"""H3 issiqlik xaritasi — toza agregatsiya (E16, `04` §2, ADR-03).

Bu modulda `SELECT` ham, HTTP ham yo'q: kirish — katakcha sanoqlari,
chiqish — ko'rsatiladigan katakchalar va ular haqidagi ogohlantirishlar.
Shu sababli butun maxfiylik va masshtab mantig'i bazasiz testlanadi.

Uchta qaror shu yerda yashaydi.

**1. Maxfiylik to'sig'i.** Katakcha `MIN_REPORTERS` (standart —
`PUBLIC_MIN_REPORTS = 3`) tadan kam **turli** foydalanuvchiga ega bo'lsa,
u xaritaga chiqmaydi. `05` §7.3 buni hodisalar uchun aytadi, lekin
issiqlik xaritasida xavf kattaroq: r9 katakcha ≈ 200 m, ya'ni yolg'iz
xabar beruvchining katakchasi amalda uning uyi. Sanoq **xabarlar** emas,
**odamlar** bo'yicha: bitta odamning o'n xabari baribir bitta uy.

Yashirilgan katakchalar jimgina yo'qolmaydi — ularning soni va ulardagi
xabarlar soni javobda qoladi (`stats` vitrinasidagi `suppressed_*` bilan
bir xil shartnoma).

**2. Logarifmik shkala.** Intensivlik `log(1+n) / log(1+max)`. Chiziqli
shkalada bitta ommaviy uzilish (masalan 300 xabar) qolgan hamma
katakchani nolga yaqin rangga bosardi va xarita «hech qayerda hech nima
yo'q» degan yolg'on taassurot berardi. Logarifm zichlik **tartibini**
ko'rsatadi, aniq nisbatini emas — issiqlik xaritasidan kutiladigani ham
shu.

**3. Zichlik yetarliligi.** `04` §2 dagi E16 chiqish mezoni — «zichlik
yetarli bo'lganda». Ko'rinadigan katakchalar `MIN_CELLS` dan kam bo'lsa,
javob `sufficient = false` bo'ladi va ogohlantirish qo'shiladi: uchta
katakchali xarita hududni emas, tasodifni ko'rsatadi.

**4. Qamrov zichlikdan boshqa narsa.** `sufficient` faqat **ko'rinadigan
katakchalar sonini** o'lchaydi, ya'ni «xaritada yetarlicha nuqta bormi»
degan savolga javob beradi. `03` §R1.2 esa boshqa savolni majburiy
qiladi: «bu hudud umuman qamralganmi». Ikkalasi ustma-ust tushmaydi —
bitta ko'chada to'plangan yigirma xabar beruvchi zich xarita beradi va
qamrovi past bo'lib qolaveradi. Shuning uchun Coverage Index bu yerga
tashqaridan (`app.stats.service.region_coverage`) uzatiladi va
xaritaning o'z ogohlantirishlariga qo'shiladi (`01` PG-S4 — «100%
vitrina indeks bilan»).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.stats.coverage import CoverageBand
from app.stats.maturity import WARNING_YOUNG

#: Intensivlik nechta pog'onaga bo'linadi (afsonaviy legenda uchun).
DEFAULT_LEVELS = 5

#: Har vitrinada majburiy dislaymer (`04` §Qat'iy qoidalar, `03` §R1.2).
DISCLAIMER_KEYS: tuple[str, ...] = (
    "stats.disclaimer.not_official",
    "stats.disclaimer.coverage",
    "heatmap.disclaimer.density",
)

#: Shu pog'onalarda vitrina ustiga «qamrov past» ogohlantirishi qo'yiladi
#: — `stats` vitrinasidagi bilan **bir xil** chegara (`service.warnings`).
LOW_COVERAGE_BANDS: frozenset[CoverageBand] = frozenset(
    {CoverageBand.NONE, CoverageBand.LOW}
)


@dataclass(frozen=True)
class CellCount:
    """Kirish qatori: katakcha, undagi xabarlar va turli xabar beruvchilar."""

    h3: str
    reports: int
    reporters: int


@dataclass(frozen=True)
class HeatCell:
    """Xaritaga chiqadigan katakcha."""

    h3: str
    reports: int
    reporters: int
    #: `0..1`, logarifmik shkala bo'yicha.
    intensity: float
    #: `1..levels` — legenda pog'onasi. Rang shu sondan tanlanadi, ya'ni
    #: mijoz shkalani o'zi qayta ixtiro qilmaydi.
    level: int


@dataclass(frozen=True)
class HeatMap:
    """Butun javobning ma'no qismi (geometriyasiz)."""

    cells: list[HeatCell]
    levels: int
    max_reports: int
    visible_reports: int
    suppressed_cells: int
    suppressed_reports: int
    sufficient: bool
    truncated: bool
    #: Hududning qamrov pog'onasi. `None` — chaqiruvchi indeksni umuman
    #: bermadi; bu holat testda taqiqlangan, chunki indekssiz vitrina
    #: `03` §R1.2 ni buzadi.
    coverage_band: CoverageBand | None = None
    #: Mintaqa yoshmi (`01` FR-S-901). Zichlik xaritasi bu pometasiz
    #: ayniqsa chalg'itadi: ikki haftalik ma'lumotdan yig'ilgan «issiq»
    #: dog' hududning odatdagi holati kabi ko'rinadi.
    is_young: bool = False

    @property
    def warnings(self) -> list[str]:
        keys = list(DISCLAIMER_KEYS)
        # Chuqurlik ogohlantirishi eng oldinda: u zichlikni ham,
        # qamrovni ham qanday o'qish kerakligini belgilaydi.
        if self.is_young:
            keys.append(WARNING_YOUNG)
        if not self.cells:
            keys.append("heatmap.warning.empty")
        elif not self.sufficient:
            keys.append("heatmap.warning.low_density")
        # Qamrov ogohlantirishi zichlikdan **keyin**, lekin maxfiylik va
        # qisqartirish izohlaridan oldin: u xaritani qanday o'qish
        # kerakligini aytadi, texnik cheklovni emas.
        if self.coverage_band in LOW_COVERAGE_BANDS:
            keys.append("stats.warning.low_coverage")
        if self.suppressed_cells:
            keys.append("heatmap.warning.suppressed")
        if self.truncated:
            keys.append("stats.warning.truncated")
        return keys


def _level(intensity: float, levels: int) -> int:
    """`(0, 1]` oralig'ini `1..levels` ga bo'ladi.

    Yuqori chegara `1.0` ham eng yuqori pog'onaga tushishi uchun natija
    kesiladi: `ceil(1.0 * 5) = 5`, lekin suzuvchi nuqta xatosi `5.0000001`
    bersa `6` chiqib ketardi.
    """
    return max(1, min(levels, math.ceil(intensity * levels)))


def build(
    rows: list[CellCount],
    *,
    min_reporters: int,
    levels: int = DEFAULT_LEVELS,
    min_cells: int,
    truncated: bool = False,
    coverage_band: CoverageBand | None = None,
    is_young: bool = False,
) -> HeatMap:
    """Sanoqlardan issiqlik xaritasini yig'adi.

    Tartib — zichlik bo'yicha kamayish, teng bo'lsa katakcha identifikatori
    bo'yicha: javob determinstik bo'lishi kerak, aks holda `ETag` bir xil
    ma'lumotda ham har safar o'zgarardi.
    """
    visible = [r for r in rows if r.reporters >= min_reporters]
    hidden = [r for r in rows if r.reporters < min_reporters]
    top = max((r.reports for r in visible), default=0)
    scale = math.log1p(top) if top > 0 else 0.0

    cells: list[HeatCell] = []
    for row in sorted(visible, key=lambda r: (-r.reports, r.h3)):
        intensity = round(math.log1p(row.reports) / scale, 4) if scale else 0.0
        cells.append(
            HeatCell(
                h3=row.h3,
                reports=row.reports,
                reporters=row.reporters,
                intensity=intensity,
                level=_level(intensity, levels),
            )
        )

    return HeatMap(
        cells=cells,
        levels=levels,
        max_reports=top,
        visible_reports=sum(r.reports for r in visible),
        suppressed_cells=len(hidden),
        suppressed_reports=sum(r.reports for r in hidden),
        sufficient=len(cells) >= min_cells,
        truncated=truncated,
        coverage_band=coverage_band,
        is_young=is_young,
    )

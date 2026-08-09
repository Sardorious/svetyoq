"""Coverage Index — hududning xabar beruvchilar bilan qamrovi (E14).

**Nima uchun majburiy** (`03` §R1.2). Kraudsorsing statistikasi qamrovsiz
o'qilsa yolg'on gapiradi: xabar kam bo'lgan hudud «tinch hudud» kabi
ko'rinadi, aslida u shunchaki qamralmagan. Indekssiz raqam nashr etish —
noto'g'ri sarlavhaga to'g'ridan-to'g'ri taklif.

**Formula validatsiya qilinmagan** — `01` §Glossariy buni ochiq aytadi
(C-11). Shuning uchun bu yerda yangi konstanta **o'ylab topilmadi**: indeks
`06` da allaqachon qaror qabul qilish uchun ishlatiladigan uchta o'lchovdan
yig'iladi va ularning chegaralari `region_config` dan keladi.

```
sufficiency = min(1, active_users_30d / A_min)          06 §5.4 to'sig'i
spread      = min(1, cell_ratio / cell_ratio_district)  06 §5.3 tarqoqligi
penetration = min(1, (active/households) / target)      [GIPOTEZA], konfiguratsiya

index = round(100 × min(mavjud komponentlar))
```

**Nima uchun eng kuchsiz komponent hal qiladi.** `06` §5.3 masshtab uchun
son va tarqoqlikni `VA` bilan bog'laydi — ya'ni birortasi yetmasa xulosa
chiqarilmaydi. Qamrov indeksi ham shunday o'qilishi kerak: 30 ta xabar
beruvchi bitta ko'chada to'plangan bo'lsa, tuman qamralgan emas.

`households` noma'lum bo'lsa `penetration` **hisobga olinmaydi**, lekin
u holda `data_quality` baribir `estimated` yoki `unknown` bo'ladi va
pog'ona quyidagi qoida bo'yicha pasayadi (`06` §3.2, §5.4 bilan bir xil
mantiq):

| `data_quality` | Pog'ona |
|---|---|
| `measured` | o'zgarmaydi |
| `estimated` | bir pog'ona pastga |
| `unknown` | eng ko'pi `low` |

Modul **toza**: bazaga ham, konfiguratsiyaga ham murojaat qilmaydi —
qiymatlar chaqiruvchidan keladi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.clustering.scale import (
    QUALITY_ESTIMATED,
    QUALITY_UNKNOWN,
    is_usable_quality,
)


class CoverageBand(StrEnum):
    """Indeksning foydalanuvchiga ko'rsatiladigan pog'onasi."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


#: Pog'ona tartibi — pasaytirish va taqqoslash uchun.
BAND_ORDER: tuple[CoverageBand, ...] = (
    CoverageBand.NONE,
    CoverageBand.LOW,
    CoverageBand.MEDIUM,
    CoverageBand.HIGH,
)

#: Indeks → pog'ona. Chegaralar `01` PRD §Metrikalar dagi «past pog'onadan
#: yuqori» maqsadi bilan mos: `medium` dan boshlab hudud «qamralgan»
#: hisoblanadi.
BAND_THRESHOLDS: tuple[tuple[int, CoverageBand], ...] = (
    (75, CoverageBand.HIGH),
    (50, CoverageBand.MEDIUM),
    (25, CoverageBand.LOW),
)

#: Pog'ona → i18n kaliti. Matn faqat katalogda (`04` §6).
BAND_KEYS: dict[CoverageBand, str] = {
    CoverageBand.NONE: "stats.coverage.none",
    CoverageBand.LOW: "stats.coverage.low",
    CoverageBand.MEDIUM: "stats.coverage.medium",
    CoverageBand.HIGH: "stats.coverage.high",
}


def _clamp01(value: float) -> float:
    return 0.0 if value < 0 else (1.0 if value > 1 else value)


def band_of(index: int) -> CoverageBand:
    for threshold, band in BAND_THRESHOLDS:
        if index >= threshold:
            return band
    return CoverageBand.NONE


def demote(band: CoverageBand, steps: int = 1) -> CoverageBand:
    position = BAND_ORDER.index(band)
    return BAND_ORDER[max(0, position - steps)]


def cap(band: CoverageBand, ceiling: CoverageBand) -> CoverageBand:
    return band if BAND_ORDER.index(band) <= BAND_ORDER.index(ceiling) else ceiling


@dataclass(frozen=True)
class CoverageInput:
    """Indeksni hisoblash uchun kerakli faktlar.

    Hammasi allaqachon mavjud manbalardan: `territory_stats` (`06` §3),
    `reports` (o'lchov) va `region_config` (chegaralar).
    """

    active_users_30d: int
    populated_cells: int
    cells_with_reports: int
    households: int | None
    data_quality: str
    #: `06` §5.4 — shu daraja uchun minimal faol foydalanuvchi soni.
    min_active: int
    #: `06` §5.3 — «to'liq tarqoqlik» deb olinadigan nisbat.
    full_spread_ratio: float
    #: Xo'jaliklarning qancha ulushi faol xabar beruvchi bo'lishi kutiladi.
    target_penetration: float


@dataclass(frozen=True)
class CoverageIndex:
    """Indeks va uni tushuntiradigan komponentlar.

    Komponentlar javobda ham qoladi: «indeks nima uchun past?» degan savolga
    javobsiz qolgan raqam ishonchsizlikni kuchaytiradi.
    """

    index: int
    band: CoverageBand
    raw_band: CoverageBand
    sufficiency: float
    spread: float | None
    penetration: float | None
    data_quality: str
    limiting_factor: str

    @property
    def message_key(self) -> str:
        return BAND_KEYS[self.band]

    @property
    def is_degraded(self) -> bool:
        """Pog'ona ma'lumot sifati tufayli pasaytirildimi."""
        return self.band is not self.raw_band


def compute(facts: CoverageInput) -> CoverageIndex:
    """`CoverageInput` → `CoverageIndex`.

    Noaniqlik har doim **pastga** qarab hal qilinadi: bo'linuvchi nol yoki
    manfiy bo'lsa komponent `0.0` bo'ladi, `None` emas. Yagona istisno —
    `households` noma'lum bo'lgan `penetration`: uni `0` deb hisoblash
    indeksni har doim nolga tushirardi va indeksni mazmunsiz qilardi.
    Uning o'rniga sifat pog'onasi pasaytiriladi.
    """
    components: dict[str, float] = {}

    sufficiency = (
        _clamp01(facts.active_users_30d / facts.min_active) if facts.min_active > 0 else 0.0
    )
    components["sufficiency"] = sufficiency

    spread: float | None = None
    if facts.populated_cells > 0 and facts.full_spread_ratio > 0:
        ratio = facts.cells_with_reports / facts.populated_cells
        spread = _clamp01(ratio / facts.full_spread_ratio)
        components["spread"] = spread

    penetration: float | None = None
    if facts.households and facts.households > 0 and facts.target_penetration > 0:
        rate = facts.active_users_30d / facts.households
        penetration = _clamp01(rate / facts.target_penetration)
        components["penetration"] = penetration

    limiting_factor = min(components, key=lambda name: components[name])
    index = round(100 * components[limiting_factor])
    raw = band_of(index)

    band = raw
    if facts.data_quality == QUALITY_ESTIMATED:
        band = demote(raw)
    elif not is_usable_quality(facts.data_quality):
        # `unknown` va noma'lum qiymat bir xil muomala ko'radi: qamrov
        # yuqori deb da'vo qilib bo'lmaydi (`06` §5.4 bilan bir xil qaror).
        # Predikat `app.clustering.scale` dan olinadi — §3.2 jadvali ikkita
        # modulda qo'lda takrorlanganda ular bir-biridan ajralib ketgan edi.
        band = cap(raw, CoverageBand.LOW)

    return CoverageIndex(
        index=index,
        band=band,
        raw_band=raw,
        sufficiency=sufficiency,
        spread=spread,
        penetration=penetration,
        data_quality=facts.data_quality or QUALITY_UNKNOWN,
        limiting_factor=limiting_factor,
    )


def unknown() -> CoverageIndex:
    """`territory_stats` qatori umuman yo'q bo'lgan hudud.

    Bu «qamrov nol» degani emas, «bilmaymiz» degani — lekin oqibati bir xil:
    hudud bo'yicha xulosa chiqarilmaydi (`06` §5.4).
    """
    return CoverageIndex(
        index=0,
        band=CoverageBand.NONE,
        raw_band=CoverageBand.NONE,
        sufficiency=0.0,
        spread=None,
        penetration=None,
        data_quality=QUALITY_UNKNOWN,
        limiting_factor="no_territory_stats",
    )

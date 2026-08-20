"""Lug'at (`01` §30 «Glossary») — paketning so'z boyligi ↔ kod.

**Nima uchun bu modul bor.** 82-run §30 ni nomzod qilib qoldirdi va
ikkita qatorni «shubhali» deb belgiladi (`DBSCAN`, `H3 8–9`). Tekshiruv
ikkalasini ham tasdiqladi, lekin asosiy topilma boshqa joyda chiqdi.

Lug'at — oddiy jadval emas. `01` §31 butun Toshkent paketini meros deb
e'lon qiladi, ya'ni §30 **butun paket qaysi so'zlar bilan yozilganini**
belgilaydi. Reyestrdagi qator yolg'on bo'lsa, uni ishlatgan har bir
hujjat o'sha yolg'onni meros qilib oladi — shuning uchun lug'atdagi
xato boshqa bo'limdagi xatodan qimmatroq.

## Asosiy topilma: lug'at belgini qo'yishni biladi va bir marta qo'yadi

`Coverage Index` qatori o'zida **ogohlantirish** olib yuradi:
«формула не валидирована (наследует C-11)». Ya'ni bo'lim uslubi ma'lum
— hal qilinmagan atama ochiq belgilanadi — va repo o'sha belgini
bajaradi: `config.py` izohi `C-11` ga havola qiladi, statistika
javoblari esa dislaymersiz chiqmaydi.

Belgi kerak bo'lgan yana ikkita qator esa uni olmagan, va ikkalasi ham
**paketning o'z keyingi hujjati** tomonidan bekor qilingan:

* **«Подтверждение»** — «достижение порога независимых источников».
  Bu aynan `05` §4.2–§4.3 ning qat'iy `min_reporters = 3` modeli, va
  `06` §1 uni ikki tomondan xato deb ataydi hamda **almashtiradi**
  (og'irlikli hisob + adaptiv chegara). Kod `06` ni bajaradi.
* **«DBSCAN»** — «алгоритм плотностной кластеризации репортов в
  инциденты». `05` §4.1 onlayn DBSCAN ni ataylab rad etadi (`ADR-02`),
  kodda inkremental biriktirish turibdi; `DBSCAN` nomli simvol repoda
  **umuman yo'q** — na `app/` da, na `tools/recluster.py` da.

Ya'ni lug'at koddan orqada qolgan emas: u **o'z paketining keyingi
hujjatlaridan** orqada qolgan. Shuning uchun hisobotning bosh xossasi —
`marks_hold`, ya'ni «bekor qilingan atama belgilanganmi».

## `UNBOUND` sinfi bo'sh — va bu, 82-rundan farqli, **yaxshi xabar**

82-run ning bo'sh `RECORDED` i bo'shliqni nomlagan edi. Bu yerda bo'sh
sinf teskari ma'noni beradi: o'nala atamaning ham repoda tayanchi bor
(jadval, ustun, simvol yoki hech bo'lmasa izoh). Ya'ni **qamrov emas,
aniqlik yiqiladi**. Sinf saqlanadi, chunki «repo eshitmagan atama»
lug'at uchun eng og'ir holat va uni o'lchaydigan joy kerak.

## Eng jim topilma: sxemada bor, hech kim to'ldirmaydi

«Махалля» — «средний уровень гео-иерархии». Sxemada haqiqatan
shunday (`mahallas` jadvali, `reports.mahalla_id`), lekin repoda
`mahallas` ga **yozadigan yo'l yo'q**: `tools/import_boundaries.py` da
`mahalla` so'zi bir marta ham uchramaydi, `tools/region_admin.py` da
ham; migratsiyalarda seed yo'q. Yagona o'quvchi — `app/geo/mahallas.py`,
va u aynan shu holat uchun `WARNING_MISSING` ni saqlaydi.

Bu 82-run ning `EX-2` topilmasini (**«Полигоны махаллей получены и
валидны»** ning birinchi yarmi bajarilmaydi) mutlaqo boshqa yo'ldan —
chiqish mezonidan emas, lug'atdan — tasdiqlaydi. Shuning uchun
`UNREACHABLE` alohida sinf: atama noto'g'ri emas, **erishib
bo'lmaydigan**.

## Teskari yo'nalish: lug'at nomlamaydigan uchta atama

Eng muhimi — **«Масштаб»**. `06` §1 ning butun mazmuni ikki savolni
ajratishdir: «Bu haqiqiymi?» (tasdiqlash) va «Bu qanchalik katta?»
(masshtab); ularni bitta chegaraga qo'shish `05` dagi xato edi.
Lug'atda esa o'sha ajratishning **faqat bekor qilingan yarmi** turibdi:
«Подтверждение» bor, «Масштаб» yo'q. Ya'ni yetishmayotgan atama va
eskirgan atama — bitta tuzatishning ikki yarmi.

## Nima ataylab tekshirilmaydi

Atamalarning **tarjimasi**. Lug'at ruscha, kod inglizcha (`Report`,
`Outage`, `layer`), foydalanuvchi matni esa UZ/RU. Nom mos kelmasligi
kamchilik emas — `i18n` kontrakti buni alohida o'lchaydi (41-run).
Bu yerda faqat **ta'rifning mazmuni** o'lchanadi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

#: Bo'limning hujjatdagi manzili.
SPEC = "01 §30"

#: Lug'at qatorlarining soni. **Aynan**: ro'yxat yopiq.
SPEC_TERMS = 10

#: Jadval sarlavhasi — ikki ustun, ya'ni har atamaga **bitta** ta'rif.
#: Uchinchi ustun (holat, manba, sana) yo'q va shuning uchun bekor
#: qilingan atamani belgilashning yagona joyi — ta'rifning o'zi.
SPEC_COLUMNS: tuple[str, ...] = ("Термин", "Определение")

#: Bo'lim ta'rif ichida ogohlantirish qo'yishni **biladi**: bu ibora
#: `Coverage Index` qatorida turibdi. Bugungi yagona belgi.
#:
#: Muhimi — ibora **qalin** yozilgan. Havola (`наследует C-11`) belgi
#: emas: u manbani ko'rsatadi, da'voni emas. Belgi — atamaning hal
#: qilinmaganini **aytadigan** jumla, va uni ajratib turadigan yagona
#: shakl — ta'kid.
MARK_EMPHASIS = "**"
MARK_PHRASE = "формула не валидирована"

#: O'sha belgining meros manbai (`01` §31 «Обязательное к прочтению»).
MARK_SOURCE = "C-11"


class Anchor(StrEnum):
    """Atama repoda **qayerga** bog'langan."""

    #: Nomni baza olib yuradi: jadval, ustun yoki ustun qiymati.
    #: Eng kuchli tayanch — uni o'chirish migratsiya talab qiladi.
    SCHEMA = "schema"
    #: Nomni kod olib yuradi: modul, sinf, funksiya yoki konstanta.
    SYMBOL = "symbol"
    #: Bajariladigan hech narsa shunday atalmaydi; atama faqat izoh,
    #: docstring yoki hujjat matnida yashaydi.
    PROSE = "prose"
    #: Repo bu nomni umuman eshitmagan. Bugun **bo'sh** — lug'atning
    #: qamrovi to'liq, yiqiladigan narsa aniqlik (yuqoridagi izoh).
    UNBOUND = "unbound"


#: Tayanch ko'rsatilishi shart bo'lgan sinflar.
ANCHOR_NEEDS_EVIDENCE: frozenset[Anchor] = frozenset(
    {Anchor.SCHEMA, Anchor.SYMBOL, Anchor.PROSE}
)


class Fidelity(StrEnum):
    """Qurilgan xulq ta'rifga **qanday** munosabatda."""

    #: Ta'rif va xulq mos keladi.
    HOLDS = "holds"
    #: Repo ta'rif nomlagandan **kamini** quradi: ta'rif diapazon
    #: beradi, kodda esa nuqta turibdi.
    NARROWER = "narrower"
    #: Repo ta'rif chiqarib tashlagan holatlarni ham **qabul qiladi**.
    WIDER = "wider"
    #: Ta'rifni paketning keyingi hujjati ochiq bekor qilgan va kod
    #: o'sha keyingi hujjatni bajaradi. Lug'at esa eski matnni saqlaydi.
    SUPERSEDED = "superseded"
    #: Ta'rif tuzilma sifatida joyida, lekin repoda uni to'ldiradigan
    #: yo'l yo'q. Xato emas — **erishib bo'lmaydigan**.
    UNREACHABLE = "unreachable"


#: Ta'rif bilan xulq orasidagi farq matn bilan izohlanishi shart
#: bo'lgan sinflar. `HOLDS` da farq yo'q va bo'lmasligi kerak.
FIDELITY_NEEDS_GAP: frozenset[Fidelity] = frozenset(
    {Fidelity.NARROWER, Fidelity.WIDER, Fidelity.SUPERSEDED, Fidelity.UNREACHABLE}
)


@dataclass(frozen=True)
class Term:
    """Lug'atning bitta qatori va uning bugungi bahosi."""

    code: str
    #: Hujjatdagi atama — **aynan**, tarjimasiz.
    term: str
    anchor: Anchor
    fidelity: Fidelity
    #: Nima uchun aynan shu baho. Keyingi o'quvchi uchun, artefakt emas.
    note: str
    #: Tayanchning dalili: `modul:simvol`. `PROSE` uchun — atamani
    #: o'zida saqlagan fayl yo'li.
    anchor_binds: tuple[str, ...] = ()
    #: Ta'rif bilan xulq orasidagi farq. `HOLDS` da bo'sh.
    gap: str = ""
    #: Ta'rifni bekor qilgan hujjat manzili. Faqat `SUPERSEDED` da.
    superseded_by: str = ""
    #: Ta'rif o'zida ogohlantirish olib yuradimi (`MARK_PHRASE`).
    marked: bool = False

    @property
    def is_precise(self) -> bool:
        return self.fidelity is Fidelity.HOLDS

    @property
    def needs_mark(self) -> bool:
        """Bekor qilingan atama belgilanishi kerak edi."""
        return self.fidelity is Fidelity.SUPERSEDED


TERMS: tuple[Term, ...] = (
    Term(
        code="G-1",
        term="Махалля",
        anchor=Anchor.SCHEMA,
        fidelity=Fidelity.UNREACHABLE,
        note=(
            "Ta'rifning ikkala yarmi ham sxemada rost: `mahallas` jadvali "
            "bor va `reports.mahalla_id` uni gerarxiyaning o'rta pog'onasiga "
            "qo'yadi (`region → district → mahalla → h3`). Yiqiladigan narsa "
            "boshqa: repoda `mahallas` ga **yozadigan yo'l yo'q**. "
            "`tools/import_boundaries.py` faqat `districts` bilan ishlaydi va "
            "unda `mahalla` so'zi bir marta ham uchramaydi; `region_admin.py` "
            "da ham; migratsiyalarda seed yo'q. Ya'ni o'rta pog'ona sxemada "
            "bor, ma'lumotda esa hech qachon paydo bo'lmaydi."
        ),
        anchor_binds=("app.geo.models:Mahalla", "app.geo.mahallas:WARNING_MISSING"),
        gap=(
            "Yagona modul atamani **yo'qligi** uchun saqlaydi: "
            "`geo.warning.mahallas_missing`. 82-run buni boshqa yo'ldan — "
            "`EX-2` chiqish mezonidan — topgan edi."
        ),
    ),
    Term(
        code="G-2",
        term="Report (отметка)",
        anchor=Anchor.SCHEMA,
        fidelity=Fidelity.WIDER,
        note=(
            "«Сообщение жителя» — `06` §2 dan oldingi dunyoning ta'rifi. "
            "Bugun `report_sources` da oltita kod bor va ularning yarmi "
            "aholi emas: `moderator` (qo'lda kiritadi), `official` (1055) "
            "va `operator_api` (Ph.3). Oxirgi ikkitasi umuman odam emas va "
            "`is_authoritative=True` bilan alohida qoidaga tushadi."
        ),
        anchor_binds=("app.reports.models:Report", "app.reports.sources:SOURCES"),
        gap=(
            "Ta'rif manbani bitta deb qabul qiladi, kod esa har xabarga "
            "og'irlik biriktiradi (`0.0`…`3.0`). Manba tushunchasi "
            "lug'atda umuman yo'q."
        ),
    ),
    Term(
        code="G-3",
        term="Outage (инцидент)",
        anchor=Anchor.SCHEMA,
        fidelity=Fidelity.WIDER,
        note=(
            "«Кластер репортов, признанный единым событием» faqat "
            "`confirmed` holatini tasvirlaydi. Kodda esa hodisa **birinchi** "
            "xabarda paydo bo'ladi va `pending` bo'lib turadi — hali hech "
            "narsa «tan olinmagan». Bundan tashqari rasmiy manbadan kelgan "
            "bitta xabar hodisani darhol `confirmed` qiladi, ya'ni «kластер» "
            "bir elementli bo'lishi mumkin; `rejected` va `merged` esa "
            "ta'rifga umuman sig'maydi."
        ),
        anchor_binds=("app.clustering.models:Outage", "app.clustering.status:OutageStatus"),
        gap=(
            "Ta'rif bitta statusni nomlaydi, status mashinasida esa beshta "
            "holat bor va ulardan uchtasi yakuniy."
        ),
    ),
    Term(
        code="G-4",
        term="Подтверждение",
        anchor=Anchor.SYMBOL,
        fidelity=Fidelity.SUPERSEDED,
        note=(
            "«Достижение порога независимых источников» — bu aynan `05` "
            "§4.2–§4.3 ning qat'iy `min_reporters = 3` modeli. `06` §1 uni "
            "ikki tomondan xato deb ataydi (kichik mahallada juda sekin, "
            "katta tumanda juda ishonchsiz) va **almashtiradi**: og'irlikli "
            "hisob (`weighted_score`) adaptiv chegaraga (`required_score`) "
            "qiyoslanadi, og'irliklar esa vaqt bilan so'nadi. Kod `06` ni "
            "bajaradi; lug'at almashtirilgan matnni saqlaydi."
        ),
        anchor_binds=(
            "app.clustering.confirmation:evaluate",
            "app.clustering.confirmation:required_score",
        ),
        gap=(
            "«Порог» endi konstanta emas, `a_local` ga bog'liq funksiya; "
            "«независимых источников» esa sanoq emas, og'irlikli yig'indi."
        ),
        superseded_by="06 §1",
    ),
    Term(
        code="G-5",
        term="Автозакрытие",
        anchor=Anchor.SYMBOL,
        fidelity=Fidelity.HOLDS,
        note=(
            "Ta'rif so'zma-so'z bajariladi: `silence >= autoclose_after` "
            "bo'lsa hodisa `resolved` ga o'tadi va sabab `autoclose` deb "
            "yoziladi. TTL konfiguratsiyada "
            "(`cluster_autoclose_after_min = 120`). Uchta yopish qoidasidan "
            "biri bo'lgani ta'rifni buzmaydi — ta'rif faqat shu qoidani "
            "nomlaydi va uni to'g'ri nomlaydi."
        ),
        anchor_binds=(
            "app.clustering.status:evaluate_status",
            "app.core.config:Settings",
        ),
    ),
    Term(
        code="G-6",
        term="Coverage Index",
        anchor=Anchor.SYMBOL,
        fidelity=Fidelity.HOLDS,
        note=(
            "Bo'limdagi **yagona belgilangan** qator, va aynan shuning "
            "uchun rost. Ogohlantirish repoda ikki joyda bajariladi: "
            "`config.py` izohi `C-11` ga havola qiladi va qiymatni `E11` ga "
            "qoldiradi; statistika javoblari esa dislaymersiz chiqmaydi "
            "(`stats.disclaimer.coverage`). Ya'ni belgi hujjat bezagi emas "
            "— u kodda kuzatiladigan xulqqa aylangan."
        ),
        anchor_binds=("app.stats.coverage:compute", "app.stats.coverage:CoverageIndex"),
        marked=True,
    ),
    Term(
        code="G-7",
        term="H3",
        anchor=Anchor.SCHEMA,
        fidelity=Fidelity.WIDER,
        note=(
            "«Разрешение 8–9» diapazon va'da qiladi. 2026-08-19 gacha kodda "
            "bitta qiymat turardi (`DEFAULT_RESOLUTION = 9`) va ta'rif "
            "`NARROWER` edi. `TZ_Podtverzhdenie_i_uvedomleniya.md` §1 buni "
            "teskarisiga o'girdi: zona endi aylana emas, **doimiy to'r**, va "
            "to'rtala daraja bir vaqtda saqlanadi — r7 (tuman), r8 (mahalla), "
            "r9 (kvartal), r10 (uy), ustiga r11 §1.1 dagi «turli manzil» ni "
            "ajratish uchun. Ya'ni repo endi ta'rif chiqarib tashlagan "
            "rezolyutsiyalarni ham yozadi. `DEFAULT_RESOLUTION` o'zgarmadi: u "
            "`h3_r9` ning egasi bo'lib qoldi, TZ darajalari esa "
            "`app.geo.pipeline:TZ_LEVELS` da."
        ),
        anchor_binds=(
            "app.geo.h3_cells:DEFAULT_RESOLUTION",
            "app.geo.pipeline:TZ_LEVELS",
            "app.reports.models:Report",
        ),
        gap="Ta'rif 8–9 deydi, sxemada 7, 8, 9, 10 va 11 bor (TZ §1, `0012`).",
    ),
    Term(
        code="G-8",
        term="DBSCAN",
        anchor=Anchor.PROSE,
        fidelity=Fidelity.SUPERSEDED,
        note=(
            "«Алгоритм плотностной кластеризации репортов в инциденты» — "
            "mahsulotning onlayn yo'li shunday ishlamaydi. `05` §4.1 to'liq "
            "DBSCAN ni ataylab rad etadi (`ADR-02`: klaster ID barqarorligi) "
            "va inkremental biriktirishni tanlaydi. `DBSCAN` nomli simvol "
            "repoda **umuman yo'q**: na `app/` da, na `tools/recluster.py` "
            "da — atama faqat izohlarda yashaydi. ⚠️ `01` buni ikki joyda "
            "aytadi: §29 C4 diagrammasi ham `Clustering Service / DBSCAN` "
            "deydi va 79-run uni `architecture.py` da qayd etgan. Ya'ni "
            "bitta katakchaning qirrasi emas, hujjatning takrorlanuvchi "
            "so'zi."
        ),
        anchor_binds=("app/clustering/geometry.py", "app/core/architecture.py"),
        gap=(
            "Oflayn DBSCAN faqat `tools/recluster.py` ning retrospektiv "
            "hisobida qoladi, ya'ni mahsulot yo'lida emas."
        ),
        superseded_by="05 §4.1",
    ),
    Term(
        code="G-9",
        term="Слой карты",
        anchor=Anchor.SCHEMA,
        fidelity=Fidelity.NARROWER,
        note=(
            "Qoidaning o'zi — «слои не смешиваются» — bajariladi va "
            "so'rovda ko'rinadi: xabar biriktirilganda `Outage.layer == "
            "layer` sharti qo'yiladi. Ro'yxat esa mos kelmaydi: ta'rif "
            "uchta qatlamni sanaydi (bot / rasmiy / issiqlik xaritasi), "
            "`OUTAGE_LAYERS` da ikkitasi bor (`crowd`, `official`). "
            "Issiqlik xaritasi qatlam emas — u alohida endpoint va "
            "`layer` ustuniga umuman tegmaydi."
        ),
        anchor_binds=(
            "app.clustering.models:OUTAGE_LAYERS",
            "app.clustering.repository:find_candidate",
        ),
        gap=(
            "Uchinchi «qatlam» boshqa turdagi narsa: qatlam hodisaning "
            "xossasi, issiqlik xaritasi esa ko'rsatish usuli."
        ),
    ),
    Term(
        code="G-10",
        term="BASELINE-TAS",
        anchor=Anchor.PROSE,
        fidelity=Fidelity.HOLDS,
        note=(
            "Yagona atama-**belgi**: u xulqni emas, qiymatning kelib "
            "chiqishini nomlaydi. Shuning uchun `PROSE` tayanchi kamchilik "
            "emas — atama o'z tabiati bo'yicha izohda yashashi kerak. Va u "
            "tirik: belgi `config.py`, `notifications/params.py` va "
            "`tools/region_admin.py` da qo'yilgan, "
            "`test_confirm_params_contract` esa uni ruxsat etilgan "
            "holatlardan biri sifatida **o'qiydi**."
        ),
        anchor_binds=("app/core/config.py", "app/notifications/params.py"),
    ),
)

TERM_BY_CODE: dict[str, Term] = {t.code: t for t in TERMS}


# --------------------------------------------------------------------------
# Teskari yo'nalish
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MissingTerm:
    """Kod tayanadigan, lug'at nomlamaydigan tushuncha."""

    code: str
    name: str
    #: Nima uchun lug'atda bo'lishi kerak edi.
    why: str
    binds: tuple[str, ...]


MISSING: tuple[MissingTerm, ...] = (
    MissingTerm(
        code="MG-1",
        name="Масштаб (scale)",
        why=(
            "`06` §1 ning butun mazmuni ikki savolni **ajratish**: «Bu "
            "haqiqiymi?» (tasdiqlash, qamrovga bog'liq) va «Bu qanchalik "
            "katta?» (masshtab, aholi va maydonga bog'liq); ularni bitta "
            "chegaraga qo'shish `05` dagi xato deb ataladi. Lug'atda esa "
            "o'sha ajratishning **faqat bekor qilingan yarmi** turibdi: "
            "`G-4` bor, masshtab yo'q. Ya'ni yetishmayotgan atama va "
            "eskirgan atama — bitta tuzatishning ikki yarmi."
        ),
        binds=("app.clustering.scale:Scale", "app.clustering.scale:SCALE_ORDER"),
    ),
    MissingTerm(
        code="MG-2",
        name="Ommaviy koordinata (jitter)",
        why=(
            "`G-9` xarita nimani ko'rsatishini ta'riflaydi, lekin "
            "ko'rsatiladigan har bir nuqta **ataylab siljitilgani** haqida "
            "lug'atda bir so'z yo'q. Bu bezak emas: `05` §3.1 siljishni "
            "deterministik qiladi (`blake2b(user_id|h3_cell)`) va "
            "`geom_exact` hech qanday javobda chiqmaydi. Maxfiylik "
            "kontrakti butun bir atamaga arziydi."
        ),
        binds=("app.geo.jitter:public_point", "app.geo.jitter:offset_for"),
    ),
    MissingTerm(
        code="MG-3",
        name="trust_score",
        why=(
            "`bot_trusted` og'irligi (`1.5`) `users.trust_score` dan kelib "
            "chiqadi, ya'ni bu qiymat hodisa tasdiqlanish-tasdiqlanmasligiga "
            "bevosita ta'sir qiladi va moderator uni qo'lda o'zgartira "
            "oladi. `G-4` tasdiqlashni ta'riflaydi va bu tushunchani "
            "nomlamaydi."
        ),
        binds=("app.admin.service:set_user_trust_score", "app.reports.sources:SOURCES"),
    ),
)


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^##\s+30\.\s+Glossary\s*$")
_NEXT_HEADING_RE = re.compile(r"^##\s+")
_ROW_RE = re.compile(r"^\|(?P<cells>.+)\|\s*$")
_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")


class GlossaryError(ValueError):
    """Hujjatdagi §30 kutilgan shaklda emas."""


@dataclass(frozen=True)
class DocRow:
    """Hujjatdagi bitta qator — reyestrning nusxasi emas, **manbasi**."""

    term: str
    definition: str

    @property
    def marked(self) -> bool:
        """Ta'rif o'zida **ta'kidlangan** ogohlantirish olib yuradimi.

        Ta'kid shart: havola qilingan har qanday ibora belgi bo'lib
        hisoblansa, `наследует` ham belgi bo'lib qolardi va shu bilan
        «hal qilinmagan» degan da'vo manbaga havola bilan
        almashtirilardi.
        """
        return f"{MARK_EMPHASIS}{MARK_PHRASE}{MARK_EMPHASIS}" in self.definition


def _cells(line: str) -> list[str]:
    match = _ROW_RE.match(line)
    if match is None:  # pragma: no cover - chaqiruvchi oldindan tekshiradi
        raise GlossaryError(f"{SPEC}: jadval qatori emas: {line!r}")
    return [cell.strip() for cell in match.group("cells").split("|")]


def parse_glossary(doc: str) -> tuple[tuple[str, ...], tuple[DocRow, ...]]:
    """`01` dan §30 jadvalini o'qiydi: sarlavha + qatorlar.

    Reyestr o'z nusxasini o'lchamasligi uchun (61-run sabog'i) hujjat
    manba sifatida qaytariladi, taqqoslash test tomonida bajariladi.
    """
    lines = doc.splitlines()
    start = next((i for i, line in enumerate(lines) if _HEADING_RE.match(line)), None)
    if start is None:
        raise GlossaryError(f"{SPEC}: «## 30. Glossary» sarlavhasi topilmadi")

    header: tuple[str, ...] | None = None
    rows: list[DocRow] = []
    for line in lines[start + 1 :]:
        if _NEXT_HEADING_RE.match(line):
            break
        if _SEPARATOR_RE.match(line):
            continue
        if not _ROW_RE.match(line):
            continue
        cells = _cells(line)
        if len(cells) != 2:
            raise GlossaryError(f"{SPEC}: qatorda {len(cells)} ustun: {line!r}")
        if header is None:
            header = (cells[0], cells[1])
            continue
        rows.append(DocRow(term=cells[0], definition=cells[1]))

    if header is None:
        raise GlossaryError(f"{SPEC}: jadval topilmadi")
    return header, tuple(rows)


# --------------------------------------------------------------------------
# Reyestrning o'z qoidalari
# --------------------------------------------------------------------------


def _check_registry() -> None:
    """Reyestr o'z-o'ziga zid bo'lsa import paytida yiqiladi.

    Bu tekshiruvlar kontrakt testining o'rnini bosmaydi — ular reyestrni
    **yozayotgan** odamga qaratilgan (`roadmap.py` bilan bir xil rol).
    """
    if len(TERMS) != SPEC_TERMS:
        raise ValueError(f"{SPEC}: {len(TERMS)} atama, kutilgani {SPEC_TERMS}")
    if len(TERM_BY_CODE) != len(TERMS):
        raise ValueError(f"{SPEC}: takrorlangan kod")

    for index, term in enumerate(TERMS, start=1):
        if term.code != f"G-{index}":
            raise ValueError(f"{SPEC}: `{term.code}` {index}-qatorda turibdi")
        if not term.note:
            raise ValueError(f"{SPEC}: `{term.code}` izohsiz")
        if term.anchor in ANCHOR_NEEDS_EVIDENCE and not term.anchor_binds:
            raise ValueError(f"{SPEC}: `{term.code}` — `{term.anchor}`, tayanch dalili yo'q")
        if term.anchor is Anchor.UNBOUND and term.anchor_binds:
            raise ValueError(f"{SPEC}: `{term.code}` — `UNBOUND`, lekin dalil ko'rsatilgan")
        # Farq — fikr emas: u nimada ekani yozilmasa, bahoni tekshirib
        # bo'lmasdi.
        if term.fidelity in FIDELITY_NEEDS_GAP and not term.gap:
            raise ValueError(f"{SPEC}: `{term.code}` — `{term.fidelity}`, farq izohlanmagan")
        if term.fidelity is Fidelity.HOLDS and term.gap:
            raise ValueError(f"{SPEC}: `{term.code}` — `HOLDS`, lekin farq ko'rsatilgan")
        # `SUPERSEDED` — «eskirgan» degan taassurot emas: bekor qilgan
        # hujjatning manzili ko'rsatilishi shart.
        if term.needs_mark and not term.superseded_by:
            raise ValueError(f"{SPEC}: `{term.code}` — `SUPERSEDED`, bekor qilgan hujjat yo'q")
        if not term.needs_mark and term.superseded_by:
            raise ValueError(f"{SPEC}: `{term.code}` — `{term.fidelity}`, manzil ortiqcha")

    for index, item in enumerate(MISSING, start=1):
        if item.code != f"MG-{index}":
            raise ValueError(f"{SPEC}: `{item.code}` {index}-o'rinda turibdi")
        if not item.binds:
            raise ValueError(f"{SPEC}: `{item.code}` dalilsiz")
        if not item.why:
            raise ValueError(f"{SPEC}: `{item.code}` izohsiz")
        if any(item.name == term.term for term in TERMS):
            raise ValueError(f"{SPEC}: `{item.code}` lug'atda allaqachon bor")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class GlossaryReport:
    """`01` §30 ning bugungi holati."""

    terms: tuple[Term, ...]
    missing: tuple[MissingTerm, ...]

    @property
    def by_anchor(self) -> dict[Anchor, tuple[str, ...]]:
        result: dict[Anchor, list[str]] = {anchor: [] for anchor in Anchor}
        for term in self.terms:
            result[term.anchor].append(term.code)
        return {anchor: tuple(codes) for anchor, codes in result.items()}

    @property
    def by_fidelity(self) -> dict[Fidelity, tuple[str, ...]]:
        result: dict[Fidelity, list[str]] = {fidelity: [] for fidelity in Fidelity}
        for term in self.terms:
            result[term.fidelity].append(term.code)
        return {fidelity: tuple(codes) for fidelity, codes in result.items()}

    @property
    def unbound(self) -> tuple[str, ...]:
        """Repo eshitmagan atamalar.

        Bugun **bo'sh**, va 82-run ning bo'sh `RECORDED` idan farqli
        o'laroq bu yaxshi xabar: lug'atning qamrovi to'liq, yiqiladigan
        narsa — aniqlik. Sinf saqlanadi, chunki bu lug'at uchun eng
        og'ir holat va uni o'lchaydigan joy kerak.
        """
        return self.by_anchor[Anchor.UNBOUND]

    @property
    def superseded(self) -> tuple[Term, ...]:
        """Paketning keyingi hujjati bekor qilgan atamalar."""
        return tuple(t for t in self.terms if t.fidelity is Fidelity.SUPERSEDED)

    @property
    def unmarked(self) -> tuple[Term, ...]:
        """Bekor qilingan, lekin belgilanmagan atamalar."""
        return tuple(t for t in self.superseded if not t.marked)

    @property
    def marked(self) -> tuple[Term, ...]:
        return tuple(t for t in self.terms if t.marked)

    @property
    def imprecise(self) -> tuple[Term, ...]:
        """Ta'rifi qurilgan xulqqa mos kelmaydigan atamalar."""
        return tuple(t for t in self.terms if not t.is_precise)

    @property
    def unreachable(self) -> tuple[Term, ...]:
        return tuple(t for t in self.terms if t.fidelity is Fidelity.UNREACHABLE)

    @property
    def marks_hold(self) -> bool:
        """Bo'limning o'z uslubi o'ziga nisbatan bajarilyaptimi.

        `Coverage Index` qatori ko'rsatadi: hal qilinmagan atama ta'rif
        ichida ochiq belgilanadi. Bugun belgi bitta, belgiga muhtoj
        qatorlar esa ikkita va ikkalasi ham belgisiz — ya'ni uslub bor,
        lekin u eng kerak joyda qo'llanmagan.
        """
        return not self.unmarked

    @property
    def accurate(self) -> bool:
        """Lug'at bugungi haqiqatni to'g'ri tasvirlaydimi.

        Uchta shart, uchtasi ham mustaqil: bekor qilingan atama
        belgilangan bo'lsin, har ta'rif qurilgan xulqqa mos kelsin va
        kod tayanadigan tushuncha nomsiz qolmasin.
        """
        return self.marks_hold and not self.imprecise and not self.missing


def evaluate() -> GlossaryReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi (`roadmap.
    evaluate` bilan bir xil sabab).
    """
    return GlossaryReport(terms=TERMS, missing=MISSING)

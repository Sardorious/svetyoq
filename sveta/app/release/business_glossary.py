"""Lug'at va ilova (`BRD` §25–§26) ↔ qurilgan mahsulot — paket yakuni.

**Nima uchun bu modul bor.** §25 — BRD ning o'z lug'ati (17 atama),
§26 — ilova: bog'liq hujjatlar (§26.1), standartlar (§26.2), diagramma
inventari (§26.3) va mahsulot egasining ochiq savollari (§26.4).
Bu BRD ning oxirgi o'qilmagan bo'limlari: shu reyestr bilan hujjatning
§8–§26 oralig'i to'liq kod bilan bog'landi.

## Birinchi topilma: `OQ-*` ro'yxati topildi — lekin u boshqa ro'yxat

`app.release.dependencies` (95-run) ochiq qoldirgan savol: «`OQ-01`
uch marta havola qilinadi va birorta hujjatda ta'riflanmagan —
`OQ-*` ro'yxati qayerda?» Ro'yxat bor ekan: BRD §26.4 sakkizta savolni
`OQ-1`…`OQ-8` deb raqamlaydi. Lekin bu **boshqa nomfazo**: `01` dagi
`OQ-01` H3-agregatsiya haqida, BRD dagi `OQ-1` — moliya modeli.
Raqamlash ham har xil (`OQ-01` ↔ `OQ-1`). Ya'ni savol yopilmadi,
aksincha aniqlashdi: `RS-*` dan keyin bu paketdagi **ikkinchi**
nomfazo to'qnashuvi (`business_environment` topilmasining egizagi).

## Ikkinchi topilma: bitta paketda ikkita lug'at va «отметка» ikki xil

`01` §30 (o'n atama, `app.core.glossary`, 83-run) va BRD §25 (o'n
yetti atama) bir tushunchani har xil ta'riflaydi: §30 da «Report
(отметка)» — sinonimlar; §25 da esa «Отметка» alohida atama («визуальное
представление сообщения **или инцидента** на карте») va «Репорт» undan
ajratilgan. Lug'atlar bir-biriga havola bermaydi. DBSCAN esa §25 da ham
bor — `05` §4.1 (ADR-02) rad etgan algoritm endi **uchinchi** hujjat
joyida «применяемый» deb tasdiqlanadi (§24.1 CLU yorlig'i, `01` §30
qatori, endi §25) — kodda inkremental biriktirish, `DBSCAN` simvoli
repoda umuman yo'q.

## Uchinchi topilma: §26.1 dagi to'qqiz hujjatning bittasi ham repoda yo'q

§26.1 «связанные документы» deb to'qqiz qatorni sanaydi — hammasi
Toshkent paketiga tegishli va birortasi bu repoda yo'q.
`business_requirements.missing_docs` (101-run, «asosi yo'q hujjatda»
sinfi) aynan shu ro'yxatning qism-to'plamiga yechiladi: §26.1 — o'sha
sinfning ota-ro'yxati. Havolalar ochilmaydigan hujjat o'z ilovasida
o'z asoslarining yo'qligini rasman e'lon qilib turibdi.

## To'rtinchi topilma: «3 часа» soni lug'atning o'zida ham eskirgan

§25 ikki qatorda («Автозакрытие», «TTL отметки») 3 soatni qotiradi;
`05` §4.4 va kod (`cluster_autoclose_after_min = 120`) — 2 soat.
Bu yangi qarama-qarshilik emas — `BR-014`/`BRL` egizagi (👤 savol
ochiq), lekin endi u BRD ning lug'at qatlamiga ham ko'chdi.
`out_of_coverage` ham shunday: §25 uni repport **statusi** deb
ta'riflaydi, kod esa qamrovdan tashqari repportni saqlamaydi — rad
etadi (`business_requirements.DOC_STATUS` topilmasining egizagi).

## Bo'sh joy: butun BRD «джиттер» so'zini bilmaydi

Mahsulotning markaziy maxfiylik mexanizmi — koordinatani deterministik
siljitish (`05` §3.1, `app.geo.jitter`) — BRD matnida **umuman**
tilga olinmaydi, lug'atda ham yo'q. `undeclared = 1` shu.

## O'qish tartibi

`TERMS` — §25 jadvalidagi tartibda, `term` katagi hujjat bilan aynan.
`DOCS`/`STANDARDS`/`DIAGRAMS`/`OQ_ROWS` — §26.1–§26.4. Baho kod dalili
(`binds`) bilan. `evaluate()` — yig'ma hisobot, `app.admin.registries`
indeksi o'qiydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.release import business_requirements as breq

#: Hujjat bo'limi. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "BRD §25–§26"

#: Bo'limlarning o'lchamlari — hujjatdan parse qilinadi.
SPEC_TERMS = 17
SPEC_DOC_ROWS = 9
SPEC_STANDARDS = 12
SPEC_DIAGRAMS = 4
SPEC_OQ_ROWS = 8

#: Birinchi topilmaning langari: `01` aynan shu ko'rinishda havola
#: qiladi, BRD §26.4 esa nol siz raqamlaydi — ikki nomfazo.
PRD_OQ_REFERENCE = "OQ-01"

#: Butun BRD tilga olmaydigan, kodda esa markaziy tushunchalar.
UNDECLARED_TERMS: tuple[str, ...] = ("джиттер (deterministik siljitish, `05` §3.1)",)


class Ground(StrEnum):
    """§25 atamasi bugungi kodga qanday tushadi."""

    #: Ta'rif kodda aynan bajariladi.
    HOLDS = "holds"
    #: Atama hujjat/reyestr qatlamida yashaydi — runtime kodi shart emas.
    DOC_LAYER = "doc_layer"
    #: Mexanizm bor, lekin ta'rifdagi son yoki shakl kodga zid.
    STALE = "stale"
    #: Ta'rif kodda mavjud bo'lmagan narsani tasdiqlaydi.
    FALSE = "false"


class StdState(StrEnum):
    """§26.2 standarti repoda qanday holatda."""

    #: Kodda izlanadigan dalili bor.
    EVIDENCED = "evidenced"
    #: Faqat e'lon — kod na tasdiqlaydi, na rad etadi.
    DECLARED = "declared"
    #: Repo holati e'longa zid.
    CONTESTED = "contested"


class OqState(StrEnum):
    """§26.4 savoli bugun qay ahvolda."""

    #: Javob yo'q, hech narsa o'zgarmagan.
    OPEN = "open"
    #: Javob yo'q, lekin kod savolni sezadi (dislaymer, reyestr).
    TOUCHED = "touched"
    #: 👤 qarori savolning «bloklaydi» qismini bekor qilgan.
    MOOT = "moot"


class BusinessGlossaryError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class TermRow:
    """§25 ning bitta qatori — `term` hujjat katagi bilan aynan."""

    term: str
    ground: Ground
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


@dataclass(frozen=True)
class DocRow:
    """§26.1 qatori — `title` hujjat katagi bilan aynan, `files` undan."""

    title: str
    files: tuple[str, ...]
    note: str
    gap: str = ""


@dataclass(frozen=True)
class StandardRow:
    """§26.2 ro'yxatining bitta nomi."""

    name: str
    state: StdState
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


@dataclass(frozen=True)
class DiagramRow:
    """§26.3 inventarining qatori. `reader` — diagrammani o'qiydigan reyestr."""

    number: int
    title: str
    section: str
    reader: str | None
    note: str
    gap: str = ""


@dataclass(frozen=True)
class OqRow:
    """§26.4 savoli — `code` va `question` hujjat kataklari bilan aynan."""

    code: str
    question: str
    blocks: str
    state: OqState
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


# --------------------------------------------------------------------------
# §25 — atamalar, hujjatdagi tartibda
# --------------------------------------------------------------------------

TERMS: tuple[TermRow, ...] = (
    TermRow(
        term="Отметка",
        ground=Ground.HOLDS,
        note=(
            "Xarita snapshotida ham repport, ham hodisa vizual "
            "ko'rsatiladi. ⚠️ `01` §30 esa «отметка» ni `Report` "
            "sinonimi deydi — ikkinchi topilma."
        ),
        binds=("app.clustering.snapshot", "web/app.js"),
    ),
    TermRow(
        term="Репорт (Report)",
        ground=Ground.HOLDS,
        note="Yagona foydalanuvchi xabari — intake shu obyektni yaratadi.",
        binds=("app.reports.intake:create_report",),
    ),
    TermRow(
        term="Инцидент (Outage)",
        ground=Ground.HOLDS,
        note="Repportlar klasteri — modellar va biriktirish xizmati.",
        binds=("app.clustering.models",),
    ),
    TermRow(
        term="Подтверждение",
        ground=Ground.HOLDS,
        note=(
            "Ikkala yo'l ham kodda: mustaqil xabarlar bo'yicha "
            "(`06` §4) va rasmiy manba orqali darhol."
        ),
        binds=("app.clustering.confirmation",),
    ),
    TermRow(
        term="Автозакрытие",
        ground=Ground.STALE,
        note=(
            "Mexanizm aynan bor (`silence >= autoclose_after` → "
            "`resolved`), lekin son eskirgan: hujjat 3 soat deydi, "
            "`05` §4.4 va kod — 120 daqiqa. `BR-014`/`BRL` egizagi."
        ),
        binds=(
            "app.clustering.status:evaluate_status",
            "app.core.config:Settings",
        ),
        gap="3 h (BRD) ≠ 120 daq (`05` §4.4 + kod) — 👤 `BR-014` bilan bitta.",
    ),
    TermRow(
        term="Махалля",
        ground=Ground.HOLDS,
        note="Geomodelning o'rta darajasi — `ST_Contains` biriktirishi.",
        binds=("app.geo.pipeline:find_mahalla_id",),
    ),
    TermRow(
        term="H3",
        ground=Ground.HOLDS,
        note="Uchinchi daraja — quvurda ham, issiqlik xaritasida ham.",
        binds=("app.geo.h3_cells",),
    ),
    TermRow(
        term="Coverage Index",
        ground=Ground.HOLDS,
        note="Zichlik ko'rsatkichi `app.stats.coverage` da hisoblanadi.",
        binds=("app.stats.coverage",),
    ),
    TermRow(
        term="Confidence",
        ground=Ground.HOLDS,
        note=(
            "0–100 baho `06` §6 bo'yicha; 100 — rasmiy manba chegarasi "
            "(`AUTHORITATIVE_CONFIDENCE`, `BRL-03` savoli alohida ochiq)."
        ),
        binds=("app.clustering.service:AUTHORITATIVE_CONFIDENCE",),
    ),
    TermRow(
        term="DBSCAN",
        ground=Ground.FALSE,
        note=(
            "«Применяемый для сведения репортов» — qo'llanmaydi: `05` "
            "§4.1 (ADR-02) uni ataylab rad etgan, kodda inkremental "
            "biriktirish, `DBSCAN` simvoli repoda yo'q. Yolg'onning "
            "uchinchi hujjat joyi (§24.1 CLU, `01` §30, endi §25)."
        ),
        gap="Algoritm qo'llanmaydi — inkremental biriktirish (`05` §4.1).",
    ),
    TermRow(
        term="TTL отметки",
        ground=Ground.STALE,
        note=(
            "Tushuncha `autoclose_after` ning o'zi — va son ham o'sha "
            "eskirgan 3 soat («Автозакрытие» qatori bilan bitta fakt)."
        ),
        binds=("app.core.config:Settings",),
        gap="3 h (BRD) ≠ 120 daq — «Автозакрытие» bilan bitta 👤 savol.",
    ),
    TermRow(
        term="Слои карты",
        ground=Ground.HOLDS,
        note=(
            "Manba bo'yicha qatlamlar kodda: `crowd`/`official` hodisa "
            "qatlamlari va alohida issiqlik xaritasi."
        ),
        binds=("app.clustering.models:OUTAGE_LAYERS", "app.stats.heatmap"),
    ),
    TermRow(
        term="Краудсорсинг",
        ground=Ground.DOC_LAYER,
        note="Yondashuv nomi — kodda alohida referenti bo'lishi shart emas.",
    ),
    TermRow(
        term="1055",
        ground=Ground.DOC_LAYER,
        note=(
            "Tashqi voqelik (raqam va kanallar) — kodda integratsiyasi "
            "yo'q, `01` §18 reyestrida `PRESUMED` (H-4 ochiq)."
        ),
        binds=("app.release.business_interfaces",),
    ),
    TermRow(
        term="BASELINE-TAS",
        ground=Ground.DOC_LAYER,
        note=(
            "Validatsiyasiz ko'chirilgan Toshkent ko'rsatkichi — atama "
            "reyestrlar qatlamida yashaydi (`business_interfaces`)."
        ),
        binds=("app.release.business_interfaces",),
    ),
    TermRow(
        term="Фаза 0",
        ground=Ground.DOC_LAYER,
        note=(
            "Gipoteza tekshiruv bosqichi — `02` ni `phase0_plan` o'qiydi; "
            "👤 qaror (2026-08-11): kalendar amalda yuritilmaydi."
        ),
        binds=("app.release.phase0_plan",),
    ),
    TermRow(
        term="out_of_coverage",
        ground=Ground.FALSE,
        note=(
            "Hujjat buni repport **statusi** deydi; kod bunday statusni "
            "yaratmaydi — qamrovdan tashqari repport saqlanmaydi, rad "
            "etiladi (`business_requirements.DOC_STATUS` egizagi)."
        ),
        gap="Status kodda yo'q — kod saqlamaydi, rad etadi (👤 savol ochiq).",
    ),
)


# --------------------------------------------------------------------------
# §26.1 — bog'liq hujjatlar
# --------------------------------------------------------------------------

_DOC_GAP = "Repoda yo'q — havola ochilmaydi (Toshkent paketi ko'chirilmagan)."

DOCS: tuple[DocRow, ...] = (
    DocRow(
        title="`01_BRD.md` (Ташкент)",
        files=("01_BRD.md",),
        note="`BASELINE-TAS` manbasi; `BR-* (TAS)` qatorlari shu yerga yechiladi.",
        gap=_DOC_GAP,
    ),
    DocRow(
        title="`02_PRD.md`",
        files=("02_PRD.md",),
        note="`PG-5` ning asosi (`business_requirements`).",
        gap=_DOC_GAP,
    ),
    DocRow(
        title="`03_Functional_Requirements.md`",
        files=("03_Functional_Requirements.md",),
        note="`FR-304`/`FR-807` asosi.",
        gap=_DOC_GAP,
    ),
    DocRow(
        title="`04_NFR.md`",
        files=("04_NFR.md",),
        note="BRD §12 qiymatlarining manbasi — qiymatlar ko'chirilgan, hujjat yo'q.",
        gap=_DOC_GAP,
    ),
    DocRow(
        title="`06_Database.md`, `18_ERD.md`",
        files=("06_Database.md", "18_ERD.md"),
        note="Meros sxema hujjatlari — repo sxemasi `05` §2 dan quriladi.",
        gap=_DOC_GAP,
    ),
    DocRow(
        title="`07_RBAC.md`",
        files=("07_RBAC.md",),
        note="Rol modeli merosi — «8 rol ↔ 3 kod roli» topilmasining ildizi.",
        gap=_DOC_GAP,
    ),
    DocRow(
        title="`13_Risk_Register.md`",
        files=("13_Risk_Register.md",),
        note="`R-13`/`R-14` asosi.",
        gap=_DOC_GAP,
    ),
    DocRow(
        title="`21_Critical_Review.md`",
        files=("21_Critical_Review.md",),
        note="`C-02`, `C-08`…`C-11` — BRD o'zi «прямо применимы» deydi.",
        gap=_DOC_GAP,
    ),
    DocRow(
        title="`svetanet-use-cases.md`",
        files=("svetanet-use-cases.md",),
        note="`UC-1`…`UC-5` asosi.",
        gap=_DOC_GAP,
    ),
)


# --------------------------------------------------------------------------
# §26.2 — standartlar
# --------------------------------------------------------------------------

_DECLARED = "Metodologik e'lon — kod na tasdiqlaydi, na rad etadi."

STANDARDS: tuple[StandardRow, ...] = (
    StandardRow(name="BABOK v3", state=StdState.DECLARED, note=_DECLARED),
    StandardRow(name="PMBOK 7", state=StdState.DECLARED, note=_DECLARED),
    StandardRow(name="IEEE 830-1998", state=StdState.DECLARED, note=_DECLARED),
    StandardRow(name="ISO/IEC 25010", state=StdState.DECLARED, note=_DECLARED),
    StandardRow(
        name="UML 2.5",
        state=StdState.DECLARED,
        note=(
            "E'lon qilingan, lekin §26.3 inventarida UML diagrammasi "
            "yo'q — flowchart, gantt va C4, xolos."
        ),
    ),
    StandardRow(
        name="BPMN 2.0",
        state=StdState.DECLARED,
        note=(
            "§9/§10 jarayonlari BPMN emas — mermaid flowchart "
            "(§26.3 ning o'zi shunday deydi)."
        ),
    ),
    StandardRow(
        name="C4 Model",
        state=StdState.EVIDENCED,
        note="§24.1 konteyner diagrammasi — `business_architecture` o'qiydi.",
        binds=("app.release.business_architecture",),
    ),
    StandardRow(
        name="OWASP ASVS",
        state=StdState.CONTESTED,
        note=(
            "SEC reyestri (71-run): NFR-S-01 MFA «Обязательно» — admin "
            "auth bitta omil; ommaviy API da rate limit yo'q (👤)."
        ),
        binds=("app.admin.security",),
        gap="MFA yo'q va ommaviy API rate limitsiz — ASVS da'vosiga zid (👤).",
    ),
    StandardRow(
        name="WCAG 2.1 AA",
        state=StdState.DECLARED,
        note="Veb bor, lekin a11y auditi o'tkazilmagan — da'vo tekshirilmagan.",
    ),
    StandardRow(
        name="OpenAPI 3.1",
        state=StdState.EVIDENCED,
        note="`/openapi.json` prodda ham ochiq, FastAPI 3.1 chiqaradi (E15).",
        binds=("app.api.openapi", "app.main"),
    ),
    StandardRow(
        name="RFC 3339",
        state=StdState.EVIDENCED,
        note="API vaqtlari UTC/ISO — `app.core.timeutil` (63-run artefakti).",
        binds=("app.core.timeutil",),
    ),
    StandardRow(
        name="WGS 84 (EPSG:4326)",
        state=StdState.EVIDENCED,
        note="Butun geo-quvur SRID 4326 da (`05` §2/§3).",
        binds=("app.geo.pipeline",),
    ),
)


# --------------------------------------------------------------------------
# §26.3 — diagramma inventari
# --------------------------------------------------------------------------

DIAGRAMS: tuple[DiagramRow, ...] = (
    DiagramRow(
        number=1,
        title="AS-IS процесс (flowchart)",
        section="§9",
        reader=None,
        note=(
            "Hech bir reyestr o'qimaydi — BRD §9–§12 oralig'i kod bilan "
            "bog'lanmagan yagona bo'laklar (👤: paket shu holida "
            "yakunlanadimi)."
        ),
    ),
    DiagramRow(
        number=2,
        title="TO-BE процесс (flowchart)",
        section="§10",
        reader=None,
        note="§9 bilan bitta holat — o'quvchi reyestr yo'q.",
    ),
    DiagramRow(
        number=3,
        title="Дорожная карта (gantt)",
        section="§23",
        reader="app.release.business_acceptance",
        note="Gantt sanalari 106-runda qulflangan (xronologiya teskari).",
    ),
    DiagramRow(
        number=4,
        title="C4 Container Diagram",
        section="§24.1",
        reader="app.release.business_architecture",
        note="107-runda tugun darajasida o'qiladi (19 tugun).",
    ),
)


# --------------------------------------------------------------------------
# §26.4 — mahsulot egasining ochiq savollari
# --------------------------------------------------------------------------

OQ_ROWS: tuple[OqRow, ...] = (
    OqRow(
        code="OQ-1",
        question="Модель финансирования проекта",
        blocks="Все фазы после Ph.0",
        state=OqState.MOOT,
        note=(
            "👤 qaror (2026-08-11): moliyaviy tomon loyihani bloklamaydi "
            "— «блокирует» ustuni amalda bekor, savolning o'zi ochiq."
        ),
        gap="👤 2026-08-11: moliya bloklamaydi — «Блокирует» ustuni eskirgan.",
    ),
    OqRow(
        code="OQ-2",
        question="Фактическое административное деление Самарканда",
        blocks="Справочник территорий",
        state=OqState.OPEN,
        note=(
            "👤 qaror (2026-08-11) yumshatgan: OSM dan qisman qamrov "
            "OK (E17 qisman boshlanadi), lekin rasmiy bo'linish savoli "
            "ochiq."
        ),
    ),
    OqRow(
        code="OQ-3",
        question="Требования законодательства РУз к локализации хранения ПДн",
        blocks="Архитектуру хранения и резервирования",
        state=OqState.OPEN,
        note="Yuridik savol — kod javob bera olmaydi (SEC qatlami kutadi).",
    ),
    OqRow(
        code="OQ-4",
        question="Наличие публичного официального источника по региону",
        blocks="Официальный слой карты",
        state=OqState.OPEN,
        note=(
            "H-4 gipotezasi (Ph.0, odamniki) — §24.1 dagi SRC/ING "
            "`ABSENT` tugunlari bilan bitta ildiz (E18)."
        ),
    ),
    OqRow(
        code="OQ-5",
        question="Порог публикации карты — конкретное значение",
        blocks="Запуск пилота",
        state=OqState.TOUCHED,
        note=(
            "Yagona savol kod allaqachon sezadigan: uch reyestr "
            "(`business_environment`, `business_requirements`, "
            "`business_rules`) darvoza o'rnidagi dislaymerni qayd etadi."
        ),
        binds=("app.release.business_environment",),
    ),
    OqRow(
        code="OQ-6",
        question="Необходимость третьего языка интерфейса",
        blocks="Скоуп локализации",
        state=OqState.OPEN,
        note="Kod bugun UZ/RU — uchinchi til katalogda yo'q (`i18n`).",
    ),
    OqRow(
        code="OQ-7",
        question="Источник и правовой режим данных о границах махаллей",
        blocks="Ph.1",
        state=OqState.OPEN,
        note="E17 ning 👤 poligon bloki bilan bitta savol.",
    ),
    OqRow(
        code="OQ-8",
        question="Лицензия проекта (не объявлена)",
        blocks="Публикацию API и Open Data",
        state=OqState.OPEN,
        note=(
            "Hujjat halol: repoda haqiqatan LICENSE yo'q. Open Data "
            "sirti esa qurilgan (`business_interfaces` topilmasi) — "
            "litsenziyasiz e'lon qilingan API."
        ),
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessGlossaryReport:
    """BRD §25–§26 ning bugungi holati."""

    terms: tuple[TermRow, ...]
    docs: tuple[DocRow, ...]
    standards: tuple[StandardRow, ...]
    diagrams: tuple[DiagramRow, ...]
    oq: tuple[OqRow, ...]

    def __post_init__(self) -> None:
        self._check_counts()
        self._check_evidence()
        self._check_neighbors()

    # -- qorovullar --------------------------------------------------------

    def _check_counts(self) -> None:
        sizes = (
            (len(self.terms), SPEC_TERMS, "§25 atamalari"),
            (len(self.docs), SPEC_DOC_ROWS, "§26.1 qatorlari"),
            (len(self.standards), SPEC_STANDARDS, "§26.2 nomlari"),
            (len(self.diagrams), SPEC_DIAGRAMS, "§26.3 qatorlari"),
            (len(self.oq), SPEC_OQ_ROWS, "§26.4 savollari"),
        )
        for got, want, what in sizes:
            if got != want:
                raise BusinessGlossaryError(
                    f"{what} soni hujjatga mos emas: {got} != {want}"
                )
        for label, seq in (
            ("§25", tuple(t.term for t in self.terms)),
            ("§26.4", tuple(q.code for q in self.oq)),
        ):
            if len(seq) != len(set(seq)):
                raise BusinessGlossaryError(f"{label} qatorlari takrorlandi")

    def _check_evidence(self) -> None:
        for t in self.terms:
            if t.ground in (Ground.HOLDS, Ground.STALE) and not t.binds:
                raise BusinessGlossaryError(f"{t.term}: {t.ground} dalilsiz bo'lmaydi")
            if t.ground is Ground.FALSE and t.binds:
                raise BusinessGlossaryError(f"{t.term}: `FALSE` da dalil bo'lmaydi")
            if t.ground in (Ground.STALE, Ground.FALSE) and not t.gap:
                raise BusinessGlossaryError(f"{t.term}: farq bor, `gap` yozilmagan")
        for d in self.docs:
            if not d.files or not d.gap:
                raise BusinessGlossaryError(f"{d.title}: fayl yoki `gap` yo'q")
        for s in self.standards:
            if s.state is not StdState.DECLARED and not s.binds:
                raise BusinessGlossaryError(f"{s.name}: {s.state} dalilsiz bo'lmaydi")
            if s.state is StdState.CONTESTED and not s.gap:
                raise BusinessGlossaryError(f"{s.name}: farq bor, `gap` yozilmagan")
        for q in self.oq:
            if q.state is OqState.MOOT and not q.gap:
                raise BusinessGlossaryError(f"{q.code}: `MOOT` sababsiz bo'lmaydi")

    def _check_neighbors(self) -> None:
        """Qo'shni reyestrlar bilan bog'lamlar — eskirsa shu yerda yiqiladi."""
        if breq.DOC_STATUS != "out_of_coverage":
            raise BusinessGlossaryError(
                "`business_requirements.DOC_STATUS` o'zgargan — "
                "`out_of_coverage` atamasi qayta baholansin"
            )
        section_files = {f for d in self.docs for f in d.files}
        missing = breq.evaluate().missing_docs
        if not missing <= section_files:
            raise BusinessGlossaryError(
                "`business_requirements.missing_docs` §26.1 dan tashqariga "
                f"chiqdi: {sorted(missing - section_files)}"
            )
        from app.core.config import Settings

        default = Settings.model_fields["cluster_autoclose_after_min"].default
        if default != 120:
            raise BusinessGlossaryError(
                "`cluster_autoclose_after_min` endi 120 emas — «3 часа» "
                "qatorlarining `STALE` bahosi qayta ko'rilsin"
            )

    # -- kesimlar ----------------------------------------------------------

    @property
    def flagged(self) -> tuple[TermRow | DocRow | StandardRow | DiagramRow | OqRow, ...]:
        """`gap` i bo'sh bo'lmagan qatorlar — hujjat bilan kod ajragan joylar."""
        rows = (*self.terms, *self.docs, *self.standards, *self.diagrams, *self.oq)
        return tuple(r for r in rows if r.gap)

    @property
    def by_ground(self) -> dict[Ground, int]:
        result: dict[Ground, int] = {g: 0 for g in Ground}
        for t in self.terms:
            result[t.ground] += 1
        return result

    @property
    def terms_hold(self) -> bool:
        """§25 ning barcha ta'riflari kodga mos keladimi. Bugun `False`."""
        return all(t.ground in (Ground.HOLDS, Ground.DOC_LAYER) for t in self.terms)

    @property
    def any_related_doc_present(self) -> bool:
        """§26.1 dan hech bo'lmasa bitta hujjat repoda bormi. Bugun `False`."""
        return any(not d.gap for d in self.docs)

    @property
    def unread_diagrams(self) -> tuple[DiagramRow, ...]:
        """O'quvchi reyestri yo'q diagrammalar — bugun §9 va §10."""
        return tuple(d for d in self.diagrams if d.reader is None)

    @property
    def accurate(self) -> bool:
        """§25–§26 «hujjat mahsulotni to'g'ri tasvirlaydi» deb o'qilsa rostmi.

        Bugun `False`: o'n besh qator ajragan — to'rtta atama (ikkitasi
        eskirgan son, ikkitasi yolg'on tasdiq), §26.1 ning to'qqiz
        hujjati repoda yo'q, OWASP ASVS da'vosi SEC holatiga zid,
        OQ-1 ning «bloklaydi» ustuni 👤 qarori bilan bekor.
        """
        return not self.flagged


def evaluate() -> BusinessGlossaryReport:
    """Reyestrdan to'liq hisobot. Argument yo'q — 85–87, 99–107 runlar qoidasi."""
    return BusinessGlossaryReport(
        terms=TERMS,
        docs=DOCS,
        standards=STANDARDS,
        diagrams=DIAGRAMS,
        oq=OQ_ROWS,
    )

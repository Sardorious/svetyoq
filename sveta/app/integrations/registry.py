"""`01` §18 «Integrations» ↔ kodda haqiqatan bor narsa.

**Nima uchun bu modul bor.** §18 — hujjatdagi yagona joy, u yerda
«mahsulot qaysi tashqi tizimlarga bog'liq» degan savolga javob beriladi.
Oltita qator, har birida `Тип`, `Протокол`, `Описание` va — eng muhimi —
`Статус`. 69-run bu jadvalning **bitta** qatorini (geokoder) ko'rdi va
o'sha yerda to'xtadi, chunki uning mavzusi `01` §22 edi. Qolgan beshtasi
hech qachon o'qilmagan.

## `Статус` — bilim haqidagi da'vo, bajarilish haqida emas

Jadvalning oxirgi ustuni integratsiya *qurilganmi* degan savolga javob
bermaydi. U «biz bu tizim haqida nimani bilamiz» deydi: `[ДАННЫЕ]` —
tekshirilgan; `[ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ]` — mavjudligi yoki formati
tasdiqlanmagan; `[ОТКРЫТО]` — manba tanlanmagan; `[ГИПОТЕЗА]` — taxmin.

Shuning uchun §18 ni «bajarilgan / bajarilmagan» ikkiligi bilan o'qish
ikkita qatorni **teskari** joyga qo'yadi:

* «Махаллинские чаты» — `Вне системы`. Kodsizligi qarz emas, qaror; uni
  bo'shliq deb sanash ro'yxatni abadiy qizil qoldirardi (67-run ning
  `EXTERNAL`, 70-run ning `CODEBASE` sinfi).
* «Региональный канал 1055» — kodda **bor**: `report_sources` da
  `official` qatori, `06` §2.2 ning alohida qoidasi va `01` §22 uchun
  yozilgan salomatlik tekshiruvi. «Bajarilgan» tomonga yaqinroq
  ko'rinadi, aslida eng xavflisi: qaror (og'irlik `0.0`, darhol
  tasdiqlash, `layer = 'official'`) **manba topilishidan oldin** qabul
  qilingan va migratsiyada muzlatilgan.

## Ikkita o'q

`Surface` — kodda nima bor. `Warrant` — o'sha narsa hujjat e'lon qilgan
bilim darajasiga **haqlimi**. Ular takrorlanmaydi va aynan 1055 da
ajraladi: `PROVISIONED` (sozlama, seed, ogohlantirish bor; chaqiruv yo'q)
va `PRESUMED` (bularning hammasi tasdiqlanmagan manba haqida).

`PRESUMED` — defekt emas va `DEFERRED` — yutuq emas. Ular narxni
ko'rsatadi: `PRESUMED` qator tasdiqlash kelganda **qayta ko'rib
chiqilishi** kerak (og'irlik, formati, `is_authoritative`), `DEFERRED`
qator esa faqat kutadi.

## Eng jim holat — `OVERSTATED`, va u eng «sog'lom» qatorda

Jadvaldagi yagona `[ДАННЫЕ]` qatori — Telegram Bot API, `Протокол`
ustunida «HTTPS webhook». Kodda webhook **bor** (`app.bot.webhook`,
`05` §6.3), lekin `TELEGRAM_MODE` ning standart qiymati uchala joyda ham
`polling`: `Settings`, `.env.example`, `docker-compose.yml`. Ya'ni
hujjat protokolni bilim sifatida e'lon qiladi, repoga kirgan har qanday
konfiguratsiya esa **boshqa** protokolni yuboradi.

Buni hech narsa ushlamaydi. Ikkala rejim ham ishlaydi, testlar ikkalasini
ham biladi, 44-run ning parity testi `TELEGRAM_MODE` ni ko'radi va
to'g'ri deydi — u kalitning mavjudligini o'lchaydi, qiymatining hujjatga
ziddligini emas. Bu 66-run ning qoidasi bilan bir sinf: e'lon qilingan
kafolat `.env` dagi bitta son bilan bekor qilinsa, u kafolat emas.

Tuzatish **qilinmadi** — standart qiymatni `webhook` ga o'zgartirish
lokal ishlab chiqishni buzadi (webhook uchun ommaviy HTTPS manzil kerak),
ya'ni bu kod emas, hujjat yoki deploy qarori. 👤 `PROGRESS.md` ning
«Ochiq savollar» ida.

## Teskari yo'nalish: e'lon qilinmagan integratsiya

§18 to'liq bo'lishi shart — bu uning yagona vazifasi. Bugun ro'yxatda
**Overpass API** yo'q: `https://overpass-api.de/api/interpreter`,
`tools.import_boundaries` undan tuman chegaralarini oladi, ya'ni butun
E2 quvuri uchinchi tomon xizmatining ishlashiga, tezlik cheklovlariga va
ODbL litsenziyasiga bog'liq. §28 «Зависимости» dagi «Полигоны районов и
махаллей — Внешняя, данные» bu emas: u **ma'lumotni** nomlaydi va bir
martalik GeoJSON fayl bilan ham qanoatlanardi; §18 esa **tizimlarni**
nomlaydi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

#: Bu ro'yxatning hujjatdagi manzili.
SPEC = "01 §18"

#: `01` §0 ning belgilari. `[ДАННЫЕ]` — tekshirilgan bilim; qolganlari
#: turli darajadagi noaniqlik, lekin `Warrant` uchun ular bir xil:
#: hech biri koddagi qarorni oqlamaydi.
CONFIRMED_MARKER = "[ДАННЫЕ]"
UNCONFIRMED_MARKERS: frozenset[str] = frozenset(
    {"[ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ]", "[ОТКРЫТО]", "[ГИПОТЕЗА]"}
)


class Surface(StrEnum):
    """Integratsiyadan kodda nima bor."""

    #: Ishlaydigan chaqiruv yo'li bor — mahsulot bu tizim bilan gaplashadi.
    OPERATING = "operating"
    #: Sozlama, seed, ogohlantirish yoki xato kodi bor; chaqiruv yo'li yo'q.
    #: Tashqaridan `NONE` ga o'xshaydi (hech narsa yurmaydi), ichkaridan
    #: `OPERATING` ga (kalit joyida, parity testi yashil).
    PROVISIONED = "provisioned"
    #: Kodda hech narsa yo'q.
    NONE = "none"


class Warrant(StrEnum):
    """Koddagi holat hujjat e'lon qilgan bilim darajasiga haqlimi.

    `Surface` ni takrorlamaydi: birinchisi «nima bor», ikkinchisi «uni
    qo'yishga asos bormidi».
    """

    #: Status tasdiqlangan, integratsiya ishlaydi va qatorning ustunlari
    #: koddagi haqiqatni to'g'ri tasvirlaydi.
    EARNED = "earned"
    #: Status tasdiqlangan va integratsiya ishlaydi, lekin qatorning
    #: bitta ustuni jo'natiladigan konfiguratsiyaga to'g'ri kelmaydi.
    OVERSTATED = "overstated"
    #: Status tasdiqlanmagan, lekin kod allaqachon qaror qabul qilgan.
    PRESUMED = "presumed"
    #: Status tasdiqlanmagan va kodda hech narsa yo'q — to'g'ri holat.
    DEFERRED = "deferred"


# --------------------------------------------------------------------------
# §18 jadvalini parse qilish
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class IntegrationRow:
    """§18 jadvalining bitta qatori."""

    system: str
    kind: str
    protocol: str
    description: str
    status: str

    @property
    def marker(self) -> str:
        """`Статус` katakchasidagi birinchi `[…]` belgisi (backticksiz)."""
        match = _MARKER_RE.search(self.status)
        if match is None:
            raise ValueError(f"{SPEC}: `{self.system}` qatorida holat belgisi yo'q")
        return match.group(1)

    @property
    def confirmed(self) -> bool:
        return self.marker == CONFIRMED_MARKER

    def cell(self, column: str) -> str:
        """Ustun sarlavhasi bo'yicha katakcha.

        Noma'lum sarlavha uchun yagona qorovul shu yerda: `assess()` da
        takrorlanmaydi. Ikkinchi nusxa bir xil xabar bilan yiqilardi va
        birinchisini olib tashlash sezilmasdi (73-run, survivor).
        """
        try:
            return getattr(self, _COLUMN_FIELDS[column])
        except KeyError:
            raise ValueError(f"{SPEC}: `{column}` degan ustun yo'q") from None


@dataclass(frozen=True)
class IntegrationTable:
    columns: tuple[str, ...]
    rows: tuple[IntegrationRow, ...]

    def row(self, system: str) -> IntegrationRow | None:
        for item in self.rows:
            if item.system == system:
                return item
        return None


#: Hujjatdagi ustun sarlavhasi → `IntegrationRow` maydoni. Sarlavhalar
#: hujjatdan **o'qiladi** va bu ko'rsatkich orqali yechiladi; §18 dagi
#: ustunni qayta nomlash `evaluate()` ni to'xtatadi.
_COLUMN_FIELDS: dict[str, str] = {
    "Система": "system",
    "Тип": "kind",
    "Протокол": "protocol",
    "Описание": "description",
    "Статус": "status",
}

_SECTION_RE = re.compile(r"^##\s+18\.\s+Integrations\s*$", re.MULTILINE)
_NEXT_SECTION_RE = re.compile(r"^##\s+\d+\.", re.MULTILINE)
_MARKER_RE = re.compile(r"(\[[А-ЯЁ][А-ЯЁ ]*\])")
_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")


def section_text(doc: str) -> str:
    """`01` dan §18 ning matnini kesib oladi."""
    match = _SECTION_RE.search(doc)
    if match is None:
        raise ValueError(f"{SPEC}: bo'lim topilmadi")
    rest = doc[match.end() :]
    nxt = _NEXT_SECTION_RE.search(rest)
    return rest[: nxt.start()] if nxt else rest


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_table(doc: str) -> IntegrationTable:
    """§18 ning jadvalini o'qiydi.

    Qo'lda ko'chirilgan nusxa yo'q (61-run sabog'i): ustun sarlavhalari
    ham, qatorlar ham faqat hujjatdan keladi. Belgi (`[ДАННЫЕ]` va
    boshqalar) tanish ro'yxatga tushmasa — `ValueError`, chunki
    noma'lum belgi jimgina «tasdiqlanmagan» deb o'qilardi.
    """
    body = section_text(doc)
    header: tuple[str, ...] | None = None
    rows: list[IntegrationRow] = []

    for raw in body.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            if header is not None and rows:
                break
            continue
        if _SEPARATOR_RE.match(line):
            continue
        cells = _split_row(line)
        if header is None:
            header = tuple(cells)
            unknown = [name for name in header if name not in _COLUMN_FIELDS]
            if unknown:
                raise ValueError(f"{SPEC}: notanish ustun(lar): {unknown}")
            missing = [name for name in _COLUMN_FIELDS if name not in header]
            if missing:
                raise ValueError(f"{SPEC}: ustun(lar) yo'q: {missing}")
            continue
        if len(cells) != len(header):
            raise ValueError(f"{SPEC}: qatorda {len(cells)} katakcha, sarlavhada {len(header)}")
        values = dict(zip(header, cells, strict=True))
        rows.append(
            IntegrationRow(
                system=values["Система"],
                kind=values["Тип"],
                protocol=values["Протокол"],
                description=values["Описание"],
                status=values["Статус"],
            )
        )

    if header is None or not rows:
        raise ValueError(f"{SPEC}: jadval topilmadi")
    for row in rows:
        marker = row.marker
        if marker != CONFIRMED_MARKER and marker not in UNCONFIRMED_MARKERS:
            raise ValueError(f"{SPEC}: `{row.system}` da notanish belgi {marker}")
    return IntegrationTable(columns=header, rows=tuple(rows))


# --------------------------------------------------------------------------
# Reyestr: har qator uchun koddagi holat
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Assessment:
    """Bitta qatorning koddagi holati va uning asosi."""

    system: str
    surface: Surface
    warrant: Warrant
    why: str
    #: `modul:simvol` — kontrakt testi har birini haqiqiy obyektga yechadi.
    #: `Surface.NONE` da bo'sh bo'lishi **shart**: dalilsiz «yo'q» va
    #: dalilli «yo'q» bir xil ko'rinmasligi kerak.
    evidence: tuple[str, ...] = ()
    #: `OVERSTATED` uchun: qatorning qaysi ustuni haqiqatga to'g'ri
    #: kelmaydi (hujjatdagi sarlavha) va uning o'rniga nima jo'natiladi.
    overstated_column: str | None = None
    overstated_by: str | None = None


ASSESSMENTS: tuple[Assessment, ...] = (
    Assessment(
        system="Telegram Bot API",
        surface=Surface.OPERATING,
        warrant=Warrant.OVERSTATED,
        overstated_column="Протокол",
        overstated_by="TELEGRAM_MODE=polling",
        evidence=(
            "app.bot.webhook:build_router",
            "app.bot.factory:setup_webhook",
            "app.bot.factory:run_polling",
            "app.core.config:Settings",
        ),
        why=(
            "Webhook yo'li to'liq yozilgan (`05` §6.3): endpoint, `secret_token` "
            "tekshiruvi, `set_webhook` chaqiruvi. Lekin rejim konfiguratsiya "
            "kaliti bilan tanlanadi va uning standart qiymati uchala joyda ham "
            "`polling`: `Settings.telegram_mode`, `.env.example`, "
            "`docker-compose.yml`. Ya'ni hujjat protokolni **bilim** sifatida "
            "e'lon qiladi, repoga kirgan konfiguratsiya esa boshqa protokolni "
            "yuboradi. Ikkala rejim ham ishlagani uchun buni hech narsa "
            "ushlamaydi."
        ),
    ),
    Assessment(
        system="Региональный канал «1055»",
        surface=Surface.PROVISIONED,
        warrant=Warrant.PRESUMED,
        evidence=(
            "app.reports.sources:SOURCES",
            "app.reports.sources:AUTHORITATIVE_CODES",
            "app.obs.monitoring:REQUIREMENT_BY_CODE",
        ),
        why=(
            "Manbaning mavjudligi ham, formati ham tasdiqlanmagan (`01` P0-1, "
            "`02` H-4) — lekin kod u haqda **uchta qaror** qabul qilib "
            "bo'lgan: `report_sources` da `official` qatori (og'irlik `0.0`), "
            "`is_authoritative=True` (ya'ni bunday xabar hodisani darhol "
            "`confirmed` qiladi, `06` §2.2), va `layer = 'official'`. Qarorlar "
            "migratsiya `0003` ning seed ida muzlatilgan. Parsing yo'li yo'q, "
            "shuning uchun bugun ular ishlamaydi — lekin manba topilgan kunda "
            "ular **qayta ko'rib chiqilmasdan** kuchga kiradi."
        ),
    ),
    Assessment(
        system="Геокодер",
        surface=Surface.PROVISIONED,
        warrant=Warrant.PRESUMED,
        evidence=(
            "app.core.config:Settings",
            "app.obs.monitoring:REQUIREMENT_BY_CODE",
        ),
        why=(
            "69-run ning topilmasi: mahsulot manzilni koordinataga umuman "
            "o'girmaydi (bot Telegram `location` pini bilan ishlaydi), ya'ni "
            "«точка на карте» zaxira emas, yagona rejim. Shunga qaramay "
            "geokoder `GEOCODER_PROVIDER`/`GEOCODER_API_KEY` sozlamalarida, "
            "`01` §16 ning `GEOCODER_UNAVAILABLE` xato kodida va "
            "`geocoding_failure_alert` talabida yashaydi. 44-run ning parity "
            "testi ikkala sozlamani ko'radi va to'g'ri deydi — ikkala tomon "
            "ham mavjud bo'lmagan quyi tizimni tasvirlayotganini u ko'rmaydi."
        ),
    ),
    Assessment(
        system="Источник полигонов махаллей",
        surface=Surface.NONE,
        warrant=Warrant.DEFERRED,
        why=(
            "Manba ham, litsenziya ham tanlanmagan (OQ-02), va kodda haqiqatan "
            "hech narsa yo'q. `tools/import_boundaries.py` bu qator emas: u "
            "**tuman** chegaralarini Overpass dan oladi, fayldan mahalla "
            "poligonlarini emas. `mahallas` jadvali bor va bo'sh — lekin "
            "jadval integratsiya emas, u qabul qiladigan idish."
        ),
    ),
    Assessment(
        system="Региональный оператор сети",
        surface=Surface.PROVISIONED,
        warrant=Warrant.PRESUMED,
        evidence=(
            "app.reports.sources:SOURCES",
            "app.reports.sources:AUTHORITATIVE_CODES",
        ),
        why=(
            "Ph.3 taxmini, «Не начато» — lekin `report_sources` da "
            "`operator_api` qatori allaqachon bor va u `is_authoritative=True`. "
            "1055 bilan bir xil sinf, bitta farq bilan: 1055 ni hech bo'lmasa "
            "`02` H-4 tekshiradi, operator API si esa uchinchi fazaning "
            "gipotezasi va uning og'irligi bugun hech kimning rejasida "
            "qayta ko'rib chiqilmaydi."
        ),
    ),
    Assessment(
        system="Махаллинские чаты",
        surface=Surface.NONE,
        warrant=Warrant.DEFERRED,
        why=(
            "`Тип` ustunining o'zi javob beradi: «Организационный», protokoli "
            "«Вне системы». Bu integratsiya emas, sovuq startning kanali — "
            "odam mahalla chatiga botning havolasini tashlaydi. Kodsizligi "
            "qarz emas va uni bo'shliq deb sanash ro'yxatni abadiy qizil "
            "qoldirardi (67-run ning `EXTERNAL` sinfi)."
        ),
    ),
)

ASSESSMENT_BY_SYSTEM: dict[str, Assessment] = {a.system: a for a in ASSESSMENTS}


# --------------------------------------------------------------------------
# Teskari yo'nalish: §18 da yo'q, kodda bor
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class UndeclaredIntegration:
    """Kod tarmoqqa chiqadi, §18 esa bu tizimni nomlamaydi."""

    system: str
    endpoint: str
    #: `modul:simvol` — chaqiruvni ko'taradigan joy.
    evidence: tuple[str, ...]
    why: str


UNDECLARED: tuple[UndeclaredIntegration, ...] = (
    UndeclaredIntegration(
        system="Overpass API",
        endpoint="https://overpass-api.de/api/interpreter",
        evidence=(
            "app.geo.osm:OVERPASS_DEFAULT_URL",
            "app.geo.osm:build_query",
            "app.geo.osm:parse_boundaries",
        ),
        why=(
            "Tuman chegaralari tizimga **faqat** shu yo'l bilan kiradi "
            "(`05` §5.1): `tools.import_boundaries survey/stage` uchinchi "
            "tomon xizmatiga HTTPS so'rov yuboradi. Ya'ni E2 ning butun quvuri "
            "o'sha xizmatning ishlashiga, tezlik cheklovlariga va OSM ning "
            "ODbL litsenziyasiga bog'liq. §28 dagi «Полигоны районов и "
            "махаллей — Внешняя, данные» buning o'rnini bosmaydi: u "
            "**ma'lumotni** nomlaydi va bir martalik GeoJSON fayl bilan ham "
            "qanoatlanardi, §18 esa **tizimlarni** nomlaydi."
        ),
    ),
)


# --------------------------------------------------------------------------
# Baholash
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    row: IntegrationRow
    assessment: Assessment

    @property
    def system(self) -> str:
        return self.row.system

    @property
    def surface(self) -> Surface:
        return self.assessment.surface

    @property
    def warrant(self) -> Warrant:
        return self.assessment.warrant

    @property
    def ahead_of_knowledge(self) -> bool:
        """Kod tasdiqlanmagan tizim haqida qaror qabul qilganmi."""
        return self.warrant is Warrant.PRESUMED


def assess(row: IntegrationRow, assessment: Assessment) -> Finding:
    """Bitta qatorni baholaydi va ikkala o'qning izchilligini talab qiladi.

    Qoidalar hujjatdan kelib chiqadi, reyestrdan emas: `Warrant`
    `Статус` belgisi bilan `Surface` ning **kesishmasi** bo'lishi shart,
    aks holda reyestrga istalgan holatni qo'lda yozib qo'yish mumkin
    bo'lardi.
    """
    if assessment.system != row.system:
        raise ValueError(f"{SPEC}: `{row.system}` uchun `{assessment.system}` bahosi berildi")

    if assessment.surface is Surface.NONE:
        if assessment.evidence:
            raise ValueError(f"{SPEC}: `{row.system}` — `NONE`, lekin dalil ko'rsatilgan")
    elif not assessment.evidence:
        raise ValueError(f"{SPEC}: `{row.system}` — `{assessment.surface}`, dalil yo'q")

    if not assessment.why.strip():
        raise ValueError(f"{SPEC}: `{row.system}` uchun izoh yo'q")

    warrant = assessment.warrant
    if row.confirmed:
        if warrant not in (Warrant.EARNED, Warrant.OVERSTATED):
            raise ValueError(
                f"{SPEC}: `{row.system}` — `{row.marker}`, lekin `{warrant}` "
                "faqat tasdiqlanmagan qatorda bo'ladi"
            )
        if assessment.surface is not Surface.OPERATING:
            raise ValueError(
                f"{SPEC}: `{row.system}` — `{row.marker}`, lekin integratsiya ishlamaydi"
            )
    else:
        if warrant in (Warrant.EARNED, Warrant.OVERSTATED):
            raise ValueError(
                f"{SPEC}: `{row.system}` — `{row.marker}`, lekin `{warrant}` "
                "faqat tasdiqlangan qatorda bo'ladi"
            )
        expected = Warrant.DEFERRED if assessment.surface is Surface.NONE else Warrant.PRESUMED
        if warrant is not expected:
            raise ValueError(
                f"{SPEC}: `{row.system}` — `{assessment.surface}` + `{row.marker}` "
                f"`{expected}` beradi, reyestrda `{warrant}`"
            )

    if warrant is Warrant.OVERSTATED:
        if not assessment.overstated_column or not assessment.overstated_by:
            raise ValueError(f"{SPEC}: `{row.system}` — `OVERSTATED`, lekin ustun ko'rsatilmagan")
        if not row.cell(assessment.overstated_column):
            raise ValueError(
                f"{SPEC}: `{row.system}` — `{assessment.overstated_column}` katakchasi bo'sh"
            )
    elif assessment.overstated_column or assessment.overstated_by:
        raise ValueError(f"{SPEC}: `{row.system}` — `{warrant}`, lekin ustun ko'rsatilgan")

    return Finding(row=row, assessment=assessment)


@dataclass(frozen=True)
class Report:
    findings: tuple[Finding, ...]
    undeclared: tuple[UndeclaredIntegration, ...]

    def by_surface(self, surface: Surface) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.surface is surface)

    def by_warrant(self, warrant: Warrant) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.warrant is warrant)

    @property
    def counts(self) -> dict[str, int]:
        return {w.value: len(self.by_warrant(w)) for w in Warrant}

    @property
    def presumed(self) -> tuple[Finding, ...]:
        return self.by_warrant(Warrant.PRESUMED)

    @property
    def accurate(self) -> bool:
        """§18 bugungi kodni to'g'ri tasvirlaydimi.

        Uchta shart, uchalasi ham mustaqil: e'lon qilinmagan tizim
        bo'lmasligi (ro'yxat **to'liq**), `OVERSTATED` bo'lmasligi
        (ustunlar **rost**) va `PRESUMED` bo'lmasligi (kod bilimdan
        oldinda **yugurmagan**). Bugun `False` va uchala sabab ham
        mavjud.

        `DEFERRED` bu yerda yo'qlik emas: tasdiqlanmagan tizim uchun
        kodsizlik — to'g'ri holat, va uni sanash ro'yxatni abadiy
        qizil qoldirardi.
        """
        return not self.undeclared and not self.by_warrant(Warrant.OVERSTATED) and not self.presumed


def build_report(doc: str) -> Report:
    """Hujjat matni → to'liq hisobot.

    Reyestrda bo'lmagan qator ham, jadvalda bo'lmagan baho ham
    `ValueError`: §18 ga yangi tizim qo'shilsa, kimdir uni **ataylab**
    baholashi kerak bo'ladi.
    """
    table = parse_table(doc)
    findings: list[Finding] = []
    for row in table.rows:
        assessment = ASSESSMENT_BY_SYSTEM.get(row.system)
        if assessment is None:
            raise ValueError(f"{SPEC}: `{row.system}` baholanmagan")
        findings.append(assess(row, assessment))

    declared = {row.system for row in table.rows}
    orphans = sorted(system for system in ASSESSMENT_BY_SYSTEM if system not in declared)
    if orphans:
        raise ValueError(f"{SPEC}: jadvalda yo'q tizim(lar) baholangan: {orphans}")

    return Report(findings=tuple(findings), undeclared=UNDECLARED)

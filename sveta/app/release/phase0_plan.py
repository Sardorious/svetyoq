"""Faza 0 validatsiya rejasi (`02_Phase0_Validation_Plan_Samarqand.md`).

`01` 99-run bilan yopildi; bu modul paketning **ikkinchi** hujjatini kod
bilan bog'laydi. `02` boshqa janr: u mahsulotni emas, mahsulot ochilishi
kerakmi degan savolni tavsiflaydi — sakkiz gipoteza, yetti metod,
go/no-go matritsasi. `roadmap.py` (82-run) `01` §24 dagi `P0-*`
vazifalarini o'lchagan; `02` o'sha vazifalarning **to'liq rejasi** va u
`P0-*` bilan §12 trassirovkasi orqali bog'lanadi — bu modul nusxa emas,
boshqa hujjatning boshqa savoli.

## Asosiy topilma: reja taqiqlagan narsa — repo o'zi

`PH0-OS-01`: «Har qanday kod yozish yoki migratsiya — byudjet
majburiyatidan oldin ishlab chiqish taqiqlanadi (BRD §22)». Repo esa
butun mahsulotni o'z ichiga oladi: `app/`, o'nta migratsiya, yuzdan
ortiq test fayli. Bu kod defekti emas — `04_Epic_Roadmap_Solo` qurishni ochiq
buyuradi — lekin paketning ikki hujjati bir-biriga qarama-qarshi
buyruq beradi va bu ziddiyat shu paytgacha hech qayerda qayd
etilmagan edi. 👤 Qaror odamniki: yo `02`/BRD §22 dagi taqiq
«mintaqaviy ochilish» ga toraytiriladi, yo `04` ning muqaddimasi
istisnoni nomlaydi.

## Ikkinchi topilma: mahsulot beshta gipotezani oldindan hal qilib bo'lgan

Faza 0 ning mantiqi — avval o'lchov, keyin qurilish. Qurilgan mahsulot
esa sakkiz gipotezadan beshtasiga allaqachon javob tanlagan:

* `H-1` (talab bor) — butun intake quvuri shu taxminga qurilgan;
* `H-2` (Telegram yetadi) — kirish nuqtasi faqat bot;
* `H-3` (UZ asosiy) — `i18n.DEFAULT_LANGUAGE = "uz"` moduldagi konstanta;
* `H-5` (mahalla chegaralari olinadi) — uch bosqichli geomodel sxemada
  (`app/geo/mahallas.py`, `0002`), haqiqiy poligonlar esa 👤 (E17);
* `H-7` (≥3 xabar zichligi) — `confirm.min_users = 3` gipotezaning
  chegarasini mahsulot konstantasi qilib qo'ygan.

`H-6` esa **teskari** hal qilingan: mahsulot geokoder chaqiruv sathisiz,
«xaritada nuqta» asosiy kirish usuli — ya'ni H-6 ning rad etish
tarmog'i qurilgan (`P0-5` ning `FORECLOSED` bahosi bilan bir dalil,
boshqa savol). Ochiq qolganlari faqat `H-4` (E18 kutadi) va `H-8`
(yuridik, `security.py` da 👤).

Bu «reja noto'g'ri» degani emas. Bu rejaning o'lchovi endi **erkin
emas** degani: rad etish chiqsa, mahsulot qayta quriladi, o'lchovchi
esa buni biladi — `PH0-R-08` (tasdiqlash tarafkashligi) aynan shu
holatni o'zining eng jiddiy riski deb yozadi.

## Uchinchi topilma: RACI ning o'nta qatoridan oltitasi konventsiyani buzadi

RACI qoidasi — har qatorda **aynan bitta** `A`. Hujjatda esa:
«Chegaralarni tasdiqlash» da `A` **ikkita** (PO va Homiy — ikki
javobgar amalda nol javobgar), `M-1`–`M-5` qatorlarida esa `A` **umuman
yo'q** — beshta o'lchov ishining javobgari belgilanmagan. Toza qatorlar
faqat to'rttasi (M-6, M-7, hisobot, qaror). Bu jadval o'zi
`PH0-R-06`/`PH0-R-08` ni ko'taradigan hujjatda — 👤 savol: `A`
ustunini kim to'ldiradi?

## Kalendar — repo o'lchay olmaydigan qatlam

Chegaralar 2026-09-01 gacha tasdiqlanishi shart (§0.2), o'lchov oynasi
2026-09-01 → 2026-10-20, qaror 2026-10-20. Bularning birortasi kodda
tekshirilmaydi — sanalar odamning taqvimida. Modul ularni **e'lon**
sifatida saqlaydi, test esa hujjat ichidagi uchta nusxaning (sarlavha,
§2 diagrammasi, §5.1 gantt) bir-biriga mosligini o'lchaydi.

## Nima qilinmadi va nima uchun

Hech narsa tuzatilmadi: gipoteza chegaralari pre-registration qoidasi
bilan muzlatilgan (§0.2 — tavsiya emas, qoida), RACI va OS-01
ziddiyatlari odam qarori. Modul o'lchaydi, tahrirlamaydi (75–77,
82–87, 98, 99-runlar bilan bir xil qoida).

Modul `app/release/` da yashaydi va `app.*` dan hech narsa import
qilmaydi: reyestr sof e'lon, qurilgan sathni **test** o'lchaydi.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

#: Hujjat. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "02 (Faza 0 rejasi)"

#: Hujjatning fayl nomi — meros ro'yxatidagi `02_PRD.md` bilan prefiks
#: to'qnashuvida aynan shu nom qatnashadi (`nfr_appendix`, 99-run).
DOC_NAME = "02_Phase0_Validation_Plan_Samarqand.md"

#: O'lchov oynasi — hujjat sarlavhasidan, aynan.
MEASUREMENT_WINDOW = ("2026-09-01", "2026-10-20")

#: go / no-go sanasi. Hujjatda uch joyda: sarlavha, §2 diagrammasi,
#: §5.1 gantt bosqichi. Test uchalasining tengligini o'lchaydi.
DECISION_DATE = "2026-10-20"

#: §0.2: barcha chegaralar shu sanagacha homiy tomonidan tasdiqlanadi.
PRE_REGISTRATION_DEADLINE = "2026-09-01"

#: §0.1 ishonchlilik belgilari — BRD §0 dan meros, tartibi hujjatdagidek.
CONFIDENCE_MARKS = ("MA'LUMOT", "BASELINE-TAS", "BAHO", "GIPOTEZA")

#: §7: M-7 (tashqi) siz jami mehnat bahosi, odam-kunda.
TOTAL_EFFORT_DAYS = 110

#: §7 dagi «Tahlil va hisobot» qatori — metod emas, lekin yig'indiga kiradi.
ANALYSIS_DAYS = 12

#: §7 yig'indisining epistemik belgisi — hujjatdagidek.
EFFORT_MARKER = "BAHO"

#: §5.2: kritik yo'l — aynan shu ikki metod, hujjatdagi tartibda.
CRITICAL_PATH = ("M-7", "M-6")

#: §5.3 asimmetrik qaror qoidasi qamraydigan gipotezalar.
ASYMMETRIC_HYPOTHESES = ("H-1", "H-7")

#: §6: to'ldirilmagan rol — «Faza 0 ning eng zaif nuqtasi».
VACANT_ROLE = "Mahalla koordinatori"

#: §6 RACI jadvalida `A` **ikki marta** uchraydigan qatorlar. RACI
#: konventsiyasida javobgar yagona bo'ladi; ro'yxat yopiq va test uni
#: jadvalning o'zidan qayta hisoblaydi.
DUAL_ACCOUNTABLE_ROWS = ("Chegaralarni tasdiqlash",)

#: §6 RACI jadvalida `A` **umuman yo'q** qatorlar — beshta o'lchov
#: ishining javobgari belgilanmagan. Ro'yxat yopiq, test qayta sanaydi.
UNACCOUNTABLE_ROWS = (
    "M-1 Desk research",
    "M-2 Kanal monitoringi",
    "M-3 Intervyular",
    "M-4 So'rov",
    "M-5 Geoaudit",
)

#: §10: hujjat o'zi «eng jiddiy» deb ataydigan risk.
MOST_SERIOUS_RISK = "PH0-R-08"

#: H-6 nazorat sinovi to'plami: 60 + 60 + 60 + 20 manzil.
ADDRESS_PROBE_SIZE = 200
ADDRESS_PROBE_PARTS = (60, 60, 60, 20)

#: Ilova D: yo'q `21_Critical_Review.md` dan meros zamechanielar.
#: To'plam `nfr_appendix.REMARKS` bilan aynan bir xil bo'lishi kerak —
#: tenglikni test ikkala moduldan hisoblaydi.
INHERITED_REMARK_CODES = ("C-04", "C-05", "C-06", "C-09", "C-10", "C-11")

#: Ilova D: Faza 0 yopishga urinadigan zamechanielar va vositasi.
FAZA0_CLOSES = {"C-06": "M-3", "C-09": "M-7"}

#: O'lchov oynasi ochilganmi. Sana kodda hisoblanmaydi (test
#: deterministik bo'lsin); qiymatni oyna ochilganda odam yangilaydi.
WINDOW_OPENED = False


class Phase0PlanError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


class Gate(StrEnum):
    """Gipotezaning §2 dagi vazni."""

    #: Rad etilishi no-go yoki skoupning tub qayta ko'rilishi.
    BLOCKING = "blocking"
    #: Rad etilishi funksionallikni degradatsiya qiladi, to'xtatmaydi.
    SCOPE = "scope"


class Result(StrEnum):
    """Gipotezaning bugungi o'lchov natijasi (§9 kartochka maqomlari)."""

    CONFIRMED = "tasdiqlandi"
    REJECTED = "rad etildi"
    UNDETERMINED = "aniqlanmadi"
    #: O'lchov boshlanmagan — bugun sakkizalasining holati.
    UNTESTED = "o'lchanmagan"


class Posture(StrEnum):
    """Qurilgan mahsulot gipotezaga nisbatan qanday turibdi."""

    #: Repo neytral — natijani kutadi.
    OPEN = "open"
    #: Mahsulot tasdiqlangan tarmoqni qurib bo'lgan.
    PRESUMES_CONFIRMED = "presumes_confirmed"
    #: Mahsulot rad etish tarmog'ini qurgan.
    PRESUMES_REJECTED = "presumes_rejected"


class Likelihood(StrEnum):
    """§10 «Ehtimol» ustuni — hujjat so'zlari bilan."""

    HIGH = "Yuqori"
    MEDIUM = "O'rta"


class Impact(StrEnum):
    """§10 «Ta'sir» ustuni — hujjat so'zlari bilan."""

    CRITICAL = "Kritik"
    HIGH = "Yuqori"
    MEDIUM = "O'rta"
    LOW = "Past"


class Outcome(StrEnum):
    """§8.1 qaror matritsasining chap ustuni."""

    GO = "GO"
    CONDITIONAL_GO = "SHARTLI GO"
    DEFER = "KECHIKTIRISH"
    NO_GO = "NO-GO"


@dataclass(frozen=True)
class Hypothesis:
    """§3 ning bitta gipotezasi va uning bugungi holati."""

    code: str
    #: §3 sarlavhasidan — aynan.
    title: str
    gate: Gate
    #: §3 «Metod» qatoridagi tartibda.
    methods: tuple[str, ...]
    #: Tasdiqlash chegarasining kalit bo'lagi — hujjat qatorida aynan bor.
    confirm: str
    #: Rad etish chegarasining kalit bo'lagi — hujjat qatorida aynan bor.
    reject: str
    #: Bugungi natija. O'lchov oynasi ochilmagan — sakkizalasida bitta.
    result: Result
    #: Mahsulotning gipotezaga nisbatan holati.
    posture: Posture
    #: §12 trassirovkasining PRD ustunidagi identifikatorlar.
    prd_refs: tuple[str, ...] = ()
    #: Dalil: `modul:simvol`, `modul` yoki fayl yo'li.
    binds: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class Method:
    """§4 ning bitta tadqiqot metodi."""

    code: str
    #: «Nimani ta'minlaydi» qatoridagi gipotezalar, hujjat tartibida.
    serves: tuple[str, ...]
    #: «qisman» deb belgilangan qism (M-2 ning H-1 i).
    partial: tuple[str, ...] = ()
    #: «Chiqish artefakti» qatorining kalit bo'lagi — aynan.
    artifact: str = ""
    #: §7 dagi mehnat bahosi; `None` — tashqi xizmat (M-7).
    effort_days: int | None = None


@dataclass(frozen=True)
class ExitCriterion:
    """§8.2 chiqish mezonlari jadvalining bitta qatori."""

    code: str
    #: Mezon matnining kalit bo'lagi — hujjat qatorida aynan bor.
    fragment: str
    #: «BRD/PRD manbasi» ustuni — aynan.
    trace: tuple[str, ...]
    #: «Holati» ustuni: hujjatda hammasi ☐. Belgilash odamning ishi.
    checked: bool = False
    #: PH0-EXIT-8: tadqiqot emas, homiy qarori.
    sponsor_dependent: bool = False


@dataclass(frozen=True)
class Risk:
    """§10 ning bitta tadqiqot riski."""

    code: str
    likelihood: Likelihood
    impact: Impact
    #: «Kamaytirish» ustunining kalit bo'lagi — aynan.
    mitigation: str = ""


@dataclass(frozen=True)
class OutOfScope:
    """§1.3 ning bitta qatori — Faza 0 nimani qilmaydi."""

    code: str
    #: «Sabab» ustunining kalit bo'lagi — aynan.
    reason: str
    #: Qator bilan repo holati orasidagi ziddiyat. Bo'sh — ziddiyat yo'q.
    tension: str = ""


@dataclass(frozen=True)
class Decision:
    """§8.1 qaror matritsasining bitta qatori."""

    outcome: Outcome
    #: Shart ustunida nomlangan gipotezalar — qatorda uchrash tartibida.
    hypotheses: tuple[str, ...]
    #: Shart matnining kalit bo'lagi — aynan.
    fragment: str = ""


# --------------------------------------------------------------------------
# §3 — gipotezalar, hujjatdagi tartibda
# --------------------------------------------------------------------------

HYPOTHESES: tuple[Hypothesis, ...] = (
    Hypothesis(
        code="H-1",
        title="Uzilishlar keskinligi talabni yaratadi",
        gate=Gate.BLOCKING,
        methods=("M-1", "M-3", "M-2"),
        confirm="≥2 rejalashtirilmagan uzilish/oy",
        reject="<0,5 uzilish/oy",
        result=Result.UNTESTED,
        posture=Posture.PRESUMES_CONFIRMED,
        prd_refs=("AS-S1", "P0-2", "RS-05"),
        binds=("app.reports.intake",),
        note=(
            "Butun intake quvuri talab bor degan taxminga qurilgan. "
            "Mavsumiylik kritik: o'lchov oynasi isitish cho'qqisidan "
            "oldin, shuning uchun §5.3 asimmetrik qoidasi H-1 ga "
            "qo'llanadi — tasdiqlash oson, rad etish ikki manba talab "
            "qiladi."
        ),
    ),
    Hypothesis(
        code="H-2",
        title="Telegram qamrovi Toshkentnikiga qiyoslanadi",
        gate=Gate.BLOCKING,
        methods=("M-1", "M-3", "M-4"),
        confirm="≥70%",
        reject="<45%",
        result=Result.UNTESTED,
        posture=Posture.PRESUMES_CONFIRMED,
        prd_refs=("AS-S5",),
        binds=("app.bot.handlers",),
        note=(
            "Kirish nuqtasi faqat bot — Telegram-first qaror qurilgan. "
            "H-2 ning o'z xavfi tanlanmada: Telegram orqali so'rov "
            "100% Telegram foydalanuvchisini beradi, shuning uchun "
            "M-4 ning ≥50% i oflayn."
        ),
    ),
    Hypothesis(
        code="H-3",
        title="O'zbek tili — sukut bo'yicha til; uchinchi tilga ehtiyoj yo'q",
        gate=Gate.BLOCKING,
        methods=("M-3", "M-4", "M-1"),
        confirm="UZ ≥60%",
        reject="UZ <40%",
        result=Result.UNTESTED,
        posture=Posture.PRESUMES_CONFIRMED,
        prd_refs=("AS-S2", "P0-3"),
        binds=("app.core.i18n:DEFAULT_LANGUAGE",),
        note=(
            "`DEFAULT_LANGUAGE = \"uz\"` — gipotezaning javobi modul "
            "konstantasi bo'lib qo'yilgan. Hujjat o'zi ogohlantiradi: "
            "BG-4 dagi «≥70% UZ-sessiya» foydalanish, Faza 0 esa "
            "afzallikni o'lchaydi — ikkisi bir narsa emas."
        ),
    ),
    Hypothesis(
        code="H-4",
        title="Mintaqa bo'yicha rasmiy ommaviy oqim mavjud",
        gate=Gate.SCOPE,
        methods=("M-2",),
        confirm="≥20 e'lon/oy",
        reject="<5 e'lon/oy",
        result=Result.UNTESTED,
        posture=Posture.OPEN,
        prd_refs=("P0-1", "RS-09"),
        note=(
            "Sakkiz gipotezadan repo chinakam kutayotgan birinchisi: "
            "E18 (rasmiy manba parsingi) aynan H-4 natijasiga qarab "
            "yoziladi yoki yozilmaydi. Rad etilsa UC-5 v1 dan chiqadi "
            "— mahsulot faqat kraudsorsing bilan ishlaydi."
        ),
    ),
    Hypothesis(
        code="H-5",
        title="Mahalla chegaralari olinadi yoki oqilona muddatda raqamlashtiriladi",
        gate=Gate.BLOCKING,
        methods=("M-5",),
        confirm="≥80%",
        reject="<50%",
        result=Result.UNTESTED,
        posture=Posture.PRESUMES_CONFIRMED,
        prd_refs=("P0-4", "RS-02"),
        binds=("app.geo.mahallas",),
        note=(
            "Uch bosqichli geomodel sxemada qurilgan (`0002`), ya'ni "
            "tasdiqlangan tarmoq tayyor; haqiqiy poligonlar esa 👤 "
            "(E17). Rad etilsa `FR-S-802` bo'yicha tuman darajasiga "
            "degradatsiya — o'sha yo'l ham sxemada bor."
        ),
    ),
    Hypothesis(
        code="H-6",
        title="Geokoder Samarqand manzillarini qoplaydi",
        gate=Gate.SCOPE,
        methods=("M-5",),
        confirm="≥85%",
        reject="<60%",
        result=Result.UNTESTED,
        posture=Posture.PRESUMES_REJECTED,
        prd_refs=("P0-5", "RS-04", "R-13"),
        binds=("app.bot.handlers:on_location",),
        note=(
            "Teskari hal qilingan gipoteza: rad etish tarmog'i — "
            "«xaritada nuqta ko'rsatish» — mahsulotning asosiy kirish "
            "usuli bo'lib qurilgan, manzil qidiruvi yo'q. Geokoder "
            "chaqiruv sathining yo'qligini `01` §18/§22/§26 "
            "reyestrlarining tripwire testlari sakkiz fayllik yopiq "
            "ro'yxat bilan qulflaydi (73–97-runlar)."
        ),
    ),
    Hypothesis(
        code="H-7",
        title="Sovuq start mahalla aktivi orqali yengib o'tiladi",
        gate=Gate.BLOCKING,
        methods=("M-6",),
        confirm="≥3 mustaqil xabar",
        reject="<20%",
        result=Result.UNTESTED,
        posture=Posture.PRESUMES_CONFIRMED,
        prd_refs=("P0-6", "AS-S4", "RS-01"),
        binds=("app.clustering.params:DEFAULTS",),
        note=(
            "Chegaraning o'zi — «Toshkent tasdiqlash mantiqi bo'yicha "
            "minimal klaster» — mahsulotda `confirm.min_users = 3` "
            "konstantasi. Kritik shart: pilot oynasida uzilish "
            "bo'lmasa, bu H-7 emas, H-1 ning natijasi (§5.3)."
        ),
    ),
    Hypothesis(
        code="H-8",
        title="Huquqiy rejim ishlashga ruxsat beradi",
        gate=Gate.BLOCKING,
        methods=("M-7",),
        confirm="≤30 odam-kunlik moslashtirish",
        reject="litsenziyalash",
        result=Result.UNTESTED,
        posture=Posture.OPEN,
        prd_refs=("P0-7", "C-09", "NFR-S-04"),
        note=(
            "Butun platformaga tegishli yagona gipoteza: rad etilishi "
            "Toshkent konturiga ham ta'sir qiladi. Repo holatni qayd "
            "etadi (`security.py` dagi 👤 qator, `C-09` ochiq), "
            "xulosa esa tashqi yurist ishi (M-7, kritik yo'l)."
        ),
    ),
)

# --------------------------------------------------------------------------
# §4 + §7 — metodlar
# --------------------------------------------------------------------------

METHODS: tuple[Method, ...] = (
    Method(
        code="M-1",
        serves=("H-1", "H-2", "H-3"),
        artifact="Manbalar reestri",
        effort_days=8,
    ),
    Method(
        code="M-2",
        serves=("H-4", "H-1"),
        partial=("H-1",),
        artifact="E'lonlar korpusi",
        effort_days=10,
    ),
    Method(
        code="M-3",
        serves=("H-1", "H-2", "H-3"),
        artifact="Transkript kodlari",
        effort_days=18,
    ),
    Method(
        code="M-4",
        serves=("H-2", "H-3"),
        artifact="anketa",
        effort_days=22,
    ),
    Method(
        code="M-5",
        serves=("H-5", "H-6"),
        artifact="Poligonlar to'plami",
        effort_days=25,
    ),
    Method(
        code="M-6",
        serves=("H-7",),
        artifact="Xabarlar jurnali",
        effort_days=15,
    ),
    Method(
        code="M-7",
        serves=("H-8",),
        artifact="Yozma xulosa",
        effort_days=None,
    ),
)

# --------------------------------------------------------------------------
# §8 — qaror matritsasi va chiqish mezonlari
# --------------------------------------------------------------------------

DECISIONS: tuple[Decision, ...] = (
    Decision(
        outcome=Outcome.GO,
        hypotheses=("H-1", "H-2", "H-3", "H-5", "H-7", "H-8"),
        fragment="Barcha to'xtatuvchi gipotezalar",
    ),
    Decision(
        outcome=Outcome.CONDITIONAL_GO,
        hypotheses=("H-1", "H-2", "H-7", "H-8", "H-3", "H-5"),
        fragment="qisqartirilgan skoup bilan",
    ),
    Decision(
        outcome=Outcome.DEFER,
        hypotheses=("H-1",),
        fragment="Qishki oynada takroriy o'lchov",
    ),
    Decision(
        outcome=Outcome.NO_GO,
        hypotheses=("H-8",),
        fragment="To'liq to'xtatish",
    ),
    Decision(
        outcome=Outcome.NO_GO,
        hypotheses=("H-1", "H-7"),
        fragment="Mintaqaviy kengayish to'xtatiladi",
    ),
    Decision(
        outcome=Outcome.NO_GO,
        hypotheses=("H-2",),
        fragment="Telegram-first strategiyasi mintaqa uchun yaroqsiz",
    ),
)

EXIT_CRITERIA: tuple[ExitCriterion, ...] = (
    ExitCriterion(
        code="PH0-EXIT-1",
        fragment="H-1…H-8 tekshirilgan",
        trace=("AC-0.1",),
    ),
    ExitCriterion(
        code="PH0-EXIT-2",
        fragment="Ma'muriy bo'linishning haqiqiy holati",
        trace=("AC-0.2",),
    ),
    ExitCriterion(
        code="PH0-EXIT-3",
        fragment="raqamlashtirish mehnat hajmi",
        trace=("AC-0.3",),
    ),
    ExitCriterion(
        code="PH0-EXIT-4",
        fragment="yuridik xulosa olingan",
        trace=("AC-0.4",),
    ),
    ExitCriterion(
        code="PH0-EXIT-5",
        fragment="go / no-go qarori qabul qilingan",
        trace=("AC-0.5",),
    ),
    ExitCriterion(
        code="PH0-EXIT-6",
        fragment="Til profili gipoteza emas",
        trace=("PRD Ph.0",),
    ),
    ExitCriterion(
        code="PH0-EXIT-7",
        fragment="Pilot zichlikka erishish",
        trace=("PRD Ph.0",),
    ),
    ExitCriterion(
        code="PH0-EXIT-8",
        fragment="moliyalashtirish manbasi aniqlangan",
        trace=("PRD Ph.0", "C-04"),
        sponsor_dependent=True,
    ),
    ExitCriterion(
        code="PH0-EXIT-9",
        fragment="o'lchovga",
        trace=("BRD §21",),
    ),
)

# --------------------------------------------------------------------------
# §10 + §1.3 — risklar va skoupdan tashqari
# --------------------------------------------------------------------------

RISKS: tuple[Risk, ...] = (
    Risk("PH0-R-01", Likelihood.HIGH, Impact.HIGH, "asimmetrik qoida"),
    Risk("PH0-R-02", Likelihood.HIGH, Impact.HIGH, "oflayn ulush ≥50%"),
    Risk("PH0-R-03", Likelihood.MEDIUM, Impact.HIGH, "Aktivdan mustaqil kanal"),
    Risk("PH0-R-04", Likelihood.HIGH, Impact.HIGH, "Ikki tilli varaq"),
    Risk("PH0-R-05", Likelihood.MEDIUM, Impact.HIGH, "6 haftagacha uzaytirish"),
    Risk("PH0-R-06", Likelihood.HIGH, Impact.CRITICAL, "ish boshlanishidan oldin yopilishi shart"),
    Risk("PH0-R-07", Likelihood.MEDIUM, Impact.MEDIUM, "Eng erta ishga tushirish"),
    Risk("PH0-R-08", Likelihood.HIGH, Impact.CRITICAL, "Oldindan ro'yxatga olish"),
    Risk("PH0-R-09", Likelihood.MEDIUM, Impact.MEDIUM, "maydon tekshiruvi"),
    Risk("PH0-R-10", Likelihood.MEDIUM, Impact.LOW, "Retrospektiv tarix"),
)

OUT_OF_SCOPE: tuple[OutOfScope, ...] = (
    OutOfScope(
        code="PH0-OS-01",
        reason="ishlab chiqish taqiqlanadi",
        tension=(
            "Repo butun mahsulotni o'z ichiga oladi: `app/`, o'nta "
            "migratsiya, yuzdan ortiq test fayli. `04_Epic_Roadmap_Solo` "
            "qurishni buyuradi — paketning ikki hujjati qarama-qarshi. "
            "👤 QAROR (2026-08-11): moliyaviy tomon loyihani "
            "bloklamaydi — `04` haq, qurilish davom etadi; hujjatlar "
            "tahrirlanmagani uchun ziddiyat hujjat darajasida qoladi "
            "va shu yerda qayd etilaveradi."
        ),
    ),
    OutOfScope(code="PH0-OS-02", reason="Til profili tasdiqlanmaguncha"),
    OutOfScope(code="PH0-OS-03", reason="alohida qaror"),
    OutOfScope(code="PH0-OS-04", reason="Regressiya riski"),
    OutOfScope(code="PH0-OS-05", reason="H-4 natijasiga bog'liq"),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Phase0Report:
    """`02` ning bugungi holati."""

    hypotheses: tuple[Hypothesis, ...]
    methods: tuple[Method, ...]
    decisions: tuple[Decision, ...]
    exit_criteria: tuple[ExitCriterion, ...]
    risks: tuple[Risk, ...]
    out_of_scope: tuple[OutOfScope, ...]
    closes: dict[str, str] = field(default_factory=lambda: dict(FAZA0_CLOSES))

    def __post_init__(self) -> None:
        h_codes = [h.code for h in self.hypotheses]
        if len(set(h_codes)) != len(h_codes):
            raise Phase0PlanError("gipoteza kodlari takrorlanadi")
        m_codes = {m.code for m in self.methods}
        # Bijeksiya: H metodni nomlaydi ⇔ metod H ni ta'minlaydi.
        for hyp in self.hypotheses:
            for m_code in hyp.methods:
                if m_code not in m_codes:
                    raise Phase0PlanError(f"{hyp.code}: metod yo'q — {m_code}")
                method = next(m for m in self.methods if m.code == m_code)
                if hyp.code not in method.serves:
                    raise Phase0PlanError(
                        f"{hyp.code} ↔ {m_code}: bog'lanish bir tomonlama"
                    )
        for method in self.methods:
            if not set(method.partial) <= set(method.serves):
                raise Phase0PlanError(f"{method.code}: `partial` `serves` dan tashqarida")
            for h_code in method.serves:
                hyp = next((h for h in self.hypotheses if h.code == h_code), None)
                if hyp is None:
                    raise Phase0PlanError(f"{method.code}: gipoteza yo'q — {h_code}")
                if method.code not in hyp.methods:
                    raise Phase0PlanError(
                        f"{method.code} ↔ {h_code}: bog'lanish bir tomonlama"
                    )
        # Falsifikatsiya: har gipotezada ikkala chegara ham bor.
        for hyp in self.hypotheses:
            if not hyp.confirm or not hyp.reject:
                raise Phase0PlanError(f"{hyp.code}: chegarasi yo'q gipoteza falsifikatsiyasiz")
            if hyp.posture is not Posture.OPEN and not hyp.binds:
                raise Phase0PlanError(f"{hyp.code}: oldindan hal qilingan, dalili yo'q")
        # GO qatori aynan to'xtatuvchi to'plam bo'lishi shart.
        go = next(d for d in self.decisions if d.outcome is Outcome.GO)
        if set(go.hypotheses) != {h.code for h in self.hypotheses if h.gate is Gate.BLOCKING}:
            raise Phase0PlanError("GO sharti to'xtatuvchi to'plamga teng emas")
        # EXIT-1 belgilanishi uchun o'lchov bo'lgan bo'lishi kerak.
        first_exit = next(c for c in self.exit_criteria if c.code == "PH0-EXIT-1")
        if first_exit.checked and any(
            h.result is Result.UNTESTED for h in self.hypotheses
        ):
            raise Phase0PlanError("EXIT-1 belgilangan, gipotezalar esa o'lchanmagan")
        # Kritik risk kamaytirish yo'lisiz qolmaydi.
        for risk in self.risks:
            if risk.impact is Impact.CRITICAL and not risk.mitigation:
                raise Phase0PlanError(f"{risk.code}: kritik risk kamaytirishsiz")
        # Yopish rejasi mavjud narsalarga ishora qilsin.
        for remark, method_code in self.closes.items():
            if remark not in INHERITED_REMARK_CODES:
                raise Phase0PlanError(f"{remark}: Ilova D da yo'q zamechanie")
            if method_code not in m_codes:
                raise Phase0PlanError(f"{remark}: yopuvchi metod yo'q — {method_code}")

    # --- kesimlar ---

    @property
    def blocking(self) -> tuple[Hypothesis, ...]:
        return tuple(h for h in self.hypotheses if h.gate is Gate.BLOCKING)

    @property
    def scope_affecting(self) -> tuple[Hypothesis, ...]:
        return tuple(h for h in self.hypotheses if h.gate is Gate.SCOPE)

    @property
    def untested(self) -> tuple[Hypothesis, ...]:
        return tuple(h for h in self.hypotheses if h.result is Result.UNTESTED)

    @property
    def prejudged(self) -> tuple[Hypothesis, ...]:
        """Mahsulot allaqachon javob tanlagan gipotezalar."""
        return tuple(h for h in self.hypotheses if h.posture is not Posture.OPEN)

    @property
    def unchecked_exits(self) -> tuple[ExitCriterion, ...]:
        return tuple(c for c in self.exit_criteria if not c.checked)

    @property
    def critical_risks(self) -> tuple[Risk, ...]:
        return tuple(r for r in self.risks if r.impact is Impact.CRITICAL)

    @property
    def scope_tensions(self) -> tuple[OutOfScope, ...]:
        """Repo holatiga zid keladigan skoup qatorlari."""
        return tuple(o for o in self.out_of_scope if o.tension)

    @property
    def unclosed_remarks(self) -> tuple[str, ...]:
        """Faza 0 yopishga urinmaydigan meros zamechanielari."""
        return tuple(c for c in INHERITED_REMARK_CODES if c not in self.closes)

    @property
    def effort_total(self) -> int:
        """§7 yig'indisi: metodlar (M-7 siz) + tahlil va hisobot."""
        return (
            sum(m.effort_days for m in self.methods if m.effort_days is not None)
            + ANALYSIS_DAYS
        )

    # --- yakuniy hukmlar ---

    @property
    def free_to_measure(self) -> bool:
        """O'lchov erkinmi — natija mahsulot holatiga bog'lanmaganmi.

        Bugun `False`: sakkizdan oltitasida mahsulot tomonini tanlab
        bo'lgan, ya'ni rad etish endi «qurilganini buzish» narxiga ega.
        `PH0-R-08` aynan shu sinf riski.
        """
        return not self.prejudged

    @property
    def accurate(self) -> bool:
        """`02` bugungi repoga to'g'ri kelyaptimi.

        Ikki mustaqil shart: reja taqiqlagan narsa repoda bo'lmasin
        (`PH0-OS-01`); o'lchov erkin bo'lsin. Bugun ikkalasi ham
        buzilgan — `False`.
        """
        return not self.scope_tensions and self.free_to_measure


def evaluate() -> Phase0Report:
    """Reyestrdan to'liq hisobot. Argument yo'q — javob kod tuzilishidan."""
    return Phase0Report(
        hypotheses=HYPOTHESES,
        methods=METHODS,
        decisions=DECISIONS,
        exit_criteria=EXIT_CRITERIA,
        risks=RISKS,
        out_of_scope=OUT_OF_SCOPE,
    )

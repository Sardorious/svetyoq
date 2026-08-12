"""Atrof-muhit reyestri (`BRD` §14–§17) ↔ qurilgan mahsulot.

**Nima uchun bu modul bor.** 102-run BRD §13 ni bog'ladi va «BRD ning
qolgan bo'limlari» ni keyingi nomzod deb qoldirdi. §14–§17 — hujjatning
**muhit** sathi: 10 taxmin (`A-*`), 7 cheklov, 12 risk (`RS-*`) va
10 bog'liqlik (`D-*`). §8 va §13 mahsulot *nima qilishini* aytadi;
bu to'rt bo'lim esa mahsulot *qaysi dunyoda* qurilayotganini tasvirlaydi
— taxminlar rostmi, cheklovlarga rioya qilinganmi, risk choralarining
qaysi biri repoda haqiqatan bor.

## Birinchi topilma: §15 «Технологии» cheklovi repo bilan to'qnashadi

Qator `ДАННЫЕ` maqomida stekni qotiradi — PostgreSQL 16 + PostGIS,
**Redis, Kafka**, Go/Python/Node, React + MapLibre, **Kubernetes** — va
«Отдельный стек для региона не допускается» deydi. Repo esa aynan
alohida stek: `04` va `05` ADR-05 Kafka/Redis ni chiqarib tashlaydi
(`outbox` jadvali — «Kafka o'rniga»), deploy Docker Compose + bitta
VPS, Kubernetes yo'q. Ikkala hujjat ham qonun maqomida: BRD cheklovi
`ДАННЫЕ` (fakt), ADR-05 esa qaytish shartlari bilan qayd etilgan
qaror. Ehtimol §15 Toshkent platformasini tasvirlaydi va mintaqaviy
mustaqil buildga tegishli emas — lekin buni hujjatning o'zi aytmaydi
(👤 qaysi tomon haq).

## Ikkinchi topilma: `RS-*` nomfazosi ikki hujjatda to'qnashadi

`01` §26 da **o'nta** `RS-*` qatori bor (`app.release.risks`), BRD §16
da esa **o'n ikkita** — kodlari ustma-ust tushadi, mazmuni esa siljigan:
`01` dagi `RS-07` — «нет финансирования», BRD dagi `RS-07` — Toshkent
statistikasining migratsiyasi. Amaliy zarari allaqachon ko'ringan:
👤 qarori (2026-08-11, `CLAUDE.md` §2) moliyaviy gate lar qatorida
«RS-07» ni BRD ga nisbat beradi, moliyaviy `RS-07` esa aslida `01` da.
Qaror mazmunan aniq (moliya bloklamaydi), lekin havolasi to'qnashuv
tufayli boshqa hujjatga tushgan — 👤 aniqlashtirish foydali.

## Uchinchi topilma: kritik yo'l o'z jadvaliga zid

§17 xulosasi «D-08 → D-02 → D-09; ни один из трёх не находится под
полным контролем команды» deydi. Jadvalning o'zi esa `D-09` ning
egasini «Команда» deb yozadi — da'vo bilan jadval bitta bo'limda
qarama-qarshi. Ustiga `D-09` («Ташкентская Фаза 1: инцидентная модель,
дедупликация») qurilgan mahsulotda umuman ishlamaydi: repo o'z
klasterlash va dedupini qurib bo'lgan (E5 ✅) — kritik yo'lning uchdan
biri mavjud bo'lmagan merosga ishora qiladi.

## To'rtinchi topilma: ikki «yuqori kritiklik» bog'liqlik mahsulotda o'lik

`D-04` (manzil spravochnigi) va `D-06` (geokoder) — ikkalasi «Высокая».
Qurilgan mahsulot esa manzil qidiruvisiz, faqat nuqta-kirish bilan
ishlaydi (H-6 rad tomonga qurilgan, 100-run): geokoderning
konfiguratsiya sirti bor (`geocoder_provider`), mexanizmi yo'q. Ya'ni
hujjat kritik degan narsa repo uchun shart emas — yoki repo hujjat
kutgan mahsulot emas (👤 o'sha H-6 savolining davomi).

## Beshinchi topilma: `RS-10` himoyasi bo'sh qoidaga tayanadi

Chora sifatida «BRL-14, Coverage Index, страница методологии» sanaladi.
Coverage Index va metodologiya sahifasi qurilgan; `BRL-14` esa
`business_rules` reyestrida **vacuous ABSENT** — taqiqni bajaradigan
ham, buzadigan ham sirt yo'q. Risk jadvalining birinchi tayanchi
mexanizmsiz qoidaning nomi.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi: stek o'zgartirilmadi (ADR-05 kuchda, ziddiyat
👤 ga), `RS-*` kodlari qayta nomlanmadi (ikkala hujjat ham
tahrirlanmaydi), geokoder qurilmadi (H-6 ochiq savol), kritik yo'l
jadvali tegilmadi. Modul o'lchaydi, tahrirlamaydi (75–77, 82–87,
99–102 runlar qoidasi).

Modul `app/release/` da yashaydi; runtime `app.*` modullaridan hech
narsa import qilmaydi — istisnolar qo'shni reyestrlar
(`phase0_plan` — taxmin ↔ gipoteza mosligi shu yerdan hisoblanadi;
`risks` — `RS-*` to'qnashuvi ikkala tomondan qulflanadi;
`business_rules` — `RS-10` ↔ `BRL-14` bog'lami), `acceptance` ↔
`gates` bilan bir xil naqsh.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.release import business_rules as brl
from app.release import phase0_plan as ph0
from app.release import risks as prd_risks

#: Hujjat bo'limlari. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "BRD §14–§17"

#: Jadval o'lchamlari — hujjatdan parse qilinadi va solishtiriladi.
SPEC_ASSUMPTION_ROWS = 10
SPEC_CONSTRAINT_ROWS = 7
SPEC_RISK_ROWS = 12
SPEC_DEPENDENCY_ROWS = 10

#: §17 xulosasidagi kritik yo'l — hujjatdagi tartibda.
CRITICAL_PATH: tuple[str, str, str] = ("D-08", "D-02", "D-09")

#: Kritik yo'l haqidagi da'voni buzadigan katak: `D-09` ning «Владелец»
#: ustuni. Da'vo «ни один … не находится под полным контролем команды»
#: deydi — egasi jamoaning o'zi bo'lgan qator bilan bitta bo'limda.
TEAM_OWNER = "Команда"

#: §15 «Технологии» qatorining taqiqi — aynan shu satr hujjatda bor va
#: repo aynan shu taqiqni buzadi (ADR-05, Docker Compose).
DOC_SEPARATE_STACK_BAN = "Отдельный стек для региона не допускается"

#: §15 qotirgan, repoda ataylab yo'q texnologiyalar (ADR-05, `04`).
#: Test ularning docker-compose da ham, importlarda ham yo'qligini
#: o'lchaydi — ziddiyat rostdan mavjudligining guvohi.
BANNED_TECH: tuple[str, ...] = ("Kafka", "Redis", "Kubernetes")

#: 👤 qarori (2026-08-11): moliyaviy cheklov loyihani bloklamaydi.
#: `CLAUDE.md` §2 da qayd etilgan; `CON-01` shu sanaga tayanadi.
FINANCE_WAIVER_DATE = "2026-08-11"

#: `RS-10` chorasida nomlangan, `business_rules` da vacuous ABSENT
#: bo'lgan qoida. Test ikkala tomondan qulflaydi.
RS10_EMPTY_GUARD = "BRL-14"


class Mark(StrEnum):
    """§14/§15 dagi ishonchlilik maqomi — hujjat so'zlari bilan."""

    HYPOTHESIS = "ГИПОТЕЗА"
    ESTIMATE = "ОЦЕНКА"
    BASELINE = "BASELINE-TAS"
    DATA = "ДАННЫЕ"
    DECISION = "Решение"


#: §14 da uchraydigan maqomlar — cheklovlarning `ДАННЫЕ`/`Решение` si
#: taxminlar jadvalida bo'lmaydi (test hujjatdan qayta sanaydi).
ASSUMPTION_MARKS: frozenset[Mark] = frozenset(
    {Mark.HYPOTHESIS, Mark.ESTIMATE, Mark.BASELINE}
)


class Answer(StrEnum):
    """Repo taxminga nisbatan qanday turibdi.

    `phase0_plan.Posture` bilan bir savol, boshqa jadval: gipotezaga
    bog'langan qatorlarda javob **hisoblanadi** — postura `OPEN`
    bo'lmasa, mahsulot taxminga allaqachon javob tanlagan.
    """

    #: Mahsulot javobni qurib bo'lgan — o'lchov endi erkin emas.
    PREJUDGED = "prejudged"
    #: Chinakam ochiq — natijani odam yoki Faza 0 beradi.
    OPEN = "open"


class Fit(StrEnum):
    """Repo §15 cheklovi bilan qanday yashayapti."""

    #: Cheklovga rioya qilinadi.
    HONORED = "honored"
    #: Repo cheklovni buzadi — farq `gap` da.
    BREACHED = "breached"
    #: 👤 qarori bilan chetga qo'yilgan.
    WAIVED = "waived"
    #: Kod o'lchay olmaydi — tashqi/tashkiliy masala.
    UNTESTED = "untested"


class Likelihood(StrEnum):
    """§16 «Вероятность» ustuni — hujjat so'zlari bilan."""

    LOW = "Низкая"
    MEDIUM = "Средняя"
    HIGH = "Высокая"


class Impact(StrEnum):
    """§16 «Влияние» ustuni — hujjat so'zlari bilan."""

    MEDIUM = "Среднее"
    HIGH = "Высокое"
    CRITICAL = "Критическое"


class Score(StrEnum):
    """§16 «Оценка» ustuni — hujjat so'zlari bilan."""

    LOW = "Низкая"
    MEDIUM = "Средняя"
    HIGH = "Высокая"


class Readiness(StrEnum):
    """§16 chorasining repodagi holati."""

    #: Choraning mexanizmi qurilgan va testlangan.
    READY = "ready"
    #: Bir qismi qurilgan, qolgani odam ishi yoki yo'q.
    PARTIAL = "partial"
    #: Butunlay odam/tashqi ish — kodda sirt kutilmaydi.
    HUMAN = "human"
    #: Toshkent platformasining ishi — bu repoga umuman tegmaydi.
    FOREIGN = "foreign"


class Criticality(StrEnum):
    """§17 «Критичность» ustuni — hujjat so'zlari bilan."""

    MEDIUM = "Средняя"
    HIGH = "Высокая"
    CRITICAL = "Критическая"


class Standing(StrEnum):
    """§17 bog'liqligining qurilgan mahsulotdagi o'rni."""

    #: Sirt qurilgan va ishlatilmoqda.
    LIVE = "live"
    #: Mexanizm tayyor, tashqi tomonni kutadi (token, ma'lumot).
    READY = "ready"
    #: Odam yoki tashqi tomon ishi — kod kutmaydi, jarayon kutadi.
    HUMAN = "human"
    #: Qurilgan mahsulotda shart emas — hujjat kutgan ehtiyoj yo'q.
    MOOT = "moot"


class BusinessEnvironmentError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class Assumption:
    """§14 ning bitta `A-*` qatori."""

    code: str
    summary: str
    mark: Mark
    #: «Как проверяется» katagidagi gipoteza (`H-*`) yoki bo'sh.
    hypothesis: str
    answer: Answer
    note: str
    binds: tuple[str, ...] = ()


@dataclass(frozen=True)
class Constraint:
    """§15 ning bitta qatori. Kod tartibdan, kategoriya hujjatdan."""

    code: str
    #: «Категория» katagi — hujjatdagi qalin yozuv bilan aynan.
    category: str
    mark: Mark
    fit: Fit
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


@dataclass(frozen=True)
class RiskRow:
    """§16 ning bitta `RS-*` qatori."""

    code: str
    summary: str
    likelihood: Likelihood
    impact: Impact
    score: Score
    readiness: Readiness
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


@dataclass(frozen=True)
class Dependency:
    """§17 ning bitta `D-*` qatori."""

    code: str
    summary: str
    #: «Тип» katagi — hujjat so'zlari bilan aynan.
    dep_type: str
    criticality: Criticality
    #: «Владелец» katagi — hujjat so'zlari bilan aynan.
    owner: str
    standing: Standing
    note: str
    binds: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# §14 — taxminlar, hujjatdagi tartibda
# --------------------------------------------------------------------------

ASSUMPTIONS: tuple[Assumption, ...] = (
    Assumption(
        code="A-01",
        summary="Uzilishlar muammosi servisga talab tug'diradigan darajada o'tkir",
        mark=Mark.HYPOTHESIS,
        hypothesis="H-1",
        answer=Answer.PREJUDGED,
        note=(
            "H-1 bilan bir ildiz: intake, klasterlash va butun quvur "
            "tasdiqlangan tarmoq uchun qurib bo'lingan — o'lchov endi "
            "neytral emas (100-run topilmasi)."
        ),
        binds=("app.reports.intake:create_report",),
    ),
    Assumption(
        code="A-02",
        summary="Telegram qamrovi Toshkentnikiga taqqoslanadi",
        mark=Mark.HYPOTHESIS,
        hypothesis="H-2",
        answer=Answer.PREJUDGED,
        note="Bot yagona kirish sifatida qurilgan (H-2 tasdiq tomonga).",
        binds=("app.bot.factory:create_bot",),
    ),
    Assumption(
        code="A-03",
        summary="O'zbekcha — auditoriya ko'pchiligi uchun afzal interfeys tili",
        mark=Mark.HYPOTHESIS,
        hypothesis="H-3",
        answer=Answer.PREJUDGED,
        note="`DEFAULT_LANGUAGE = 'uz'` allaqachon standart (H-3).",
        binds=("app.core.i18n:DEFAULT_LANGUAGE",),
    ),
    Assumption(
        code="A-04",
        summary="Mintaqa bo'yicha rasmiy xabarlarning ochiq oqimi mavjud",
        mark=Mark.HYPOTHESIS,
        hypothesis="H-4",
        answer=Answer.OPEN,
        note="Chinakam ochiq: E18 aynan H-4 natijasini kutadi (⬜).",
    ),
    Assumption(
        code="A-05",
        summary="Mahalla chegaralari mashina o'qiy oladigan ko'rinishda topiladi",
        mark=Mark.HYPOTHESIS,
        hypothesis="H-5",
        answer=Answer.PREJUDGED,
        note=(
            "Sxema va import mexanizmi qurib bo'lingan (H-5 tasdiq "
            "tomonga); 👤 qarori (2026-08-11): manba OSM, qamrov qisman "
            "bo'lishi mumkin — ya'ni taxminning «yoki raqamlashtiriladi» "
            "yarmi amalda yumshatilgan."
        ),
        binds=("app.geo.models:Mahalla", "tools/import_boundaries.py"),
    ),
    Assumption(
        code="A-06",
        summary="Shaharning besh tumanlik bo'linishga o'tishi rasmiylashadi",
        mark=Mark.HYPOTHESIS,
        hypothesis="",
        answer=Answer.OPEN,
        note=(
            "Yuridik tekshiruv — odam ishi. Repo natijadan qat'i nazar "
            "yashaydi: chegara versiyalash (`BR-002`) har ikki natijani "
            "ko'taradi."
        ),
        binds=("app.geo.queries:districts_for_period",),
    ),
    Assumption(
        code="A-07",
        summary="Xulq patternlari Toshkentdan ko'chiriladi",
        mark=Mark.BASELINE,
        hypothesis="",
        answer=Answer.OPEN,
        note=(
            "Hujjatning o'zi ham buni byudjet asosi sifatida taqiqlaydi; "
            "o'lchov faqat ishga tushirishdan keyin (E10–E11)."
        ),
    ),
    Assumption(
        code="A-08",
        summary="Uchinchi interfeys tiliga ehtiyoj yo'q yoki arzimas",
        mark=Mark.HYPOTHESIS,
        hypothesis="H-3",
        answer=Answer.PREJUDGED,
        note=(
            "i18n katalogi aynan UZ+RU bilan qulflangan — uchinchi til "
            "skoup o'zgarishisiz kirmaydi; javob amalda tanlangan."
        ),
        binds=("app.core.i18n:SUPPORTED_LANGUAGES",),
    ),
    Assumption(
        code="A-09",
        summary="Mavjud infratuzilma mintaqaviy konturni alohida instalyatsiyasiz ko'taradi",
        mark=Mark.ESTIMATE,
        hypothesis="",
        answer=Answer.PREJUDGED,
        note=(
            "Repo taxminning teskarisini qurgan: mustaqil instalyatsiya "
            "(Docker Compose, bitta VPS) — «alohida instalyatsiyasiz» "
            "premissasi amalda rad etilgan; `CON-05` bilan bir ildiz."
        ),
        binds=("docker-compose.yml",),
    ),
    Assumption(
        code="A-10",
        summary="Mintaqa bo'yicha volontyor-moderatorlarni jalb qilib bo'ladi",
        mark=Mark.HYPOTHESIS,
        hypothesis="",
        answer=Answer.OPEN,
        note=(
            "Odam ishi; moderatsiya navbati esa natijadan qat'i nazar "
            "qurilgan (E8 🔄)."
        ),
        binds=("app.admin.service:reject_outage", "app.clustering.service:moderate"),
    ),
)


# --------------------------------------------------------------------------
# §15 — cheklovlar, hujjatdagi tartibda
# --------------------------------------------------------------------------

CONSTRAINTS: tuple[Constraint, ...] = (
    Constraint(
        code="CON-01",
        category="Бюджет",
        mark=Mark.DATA,
        fit=Fit.WAIVED,
        note=(
            "«Birinchi tartibli cheklov» — lekin 👤 qarori "
            f"({FINANCE_WAIVER_DATE}, `CLAUDE.md` §2): moliyaviy tomon "
            "loyihani bloklamaydi, tugatish ustuvor. Hujjat "
            "tahrirlanmaydi; reyestr ziddiyatni qayd etaveradi."
        ),
        gap="Cheklov kuchda qoladi, lekin ishni to'xtatmaydi (👤).",
    ),
    Constraint(
        code="CON-02",
        category="Сроки",
        mark=Mark.DECISION,
        fit=Fit.BREACHED,
        note=(
            "«Faza 1 Faza 0 yopilmaguncha boshlanmaydi» — repo esa butun "
            "mahsulotni qurib bo'lgan, o'lchov oynasi ochilmagan "
            "(`WINDOW_OPENED = False`). `PH0-OS-01` ziddiyatining "
            "(100-run) aynan o'zi: paket hujjatlari bir-biriga qarshi "
            "buyruq beradi."
        ),
        binds=("app.release.phase0_plan:WINDOW_OPENED",),
        gap="Faza 1 ishi Faza 0 natijasisiz qilinmoqda (👤 PH0-OS-01).",
    ),
    Constraint(
        code="CON-03",
        category="Законодательство",
        mark=Mark.HYPOTHESIS,
        fit=Fit.UNTESTED,
        note=(
            "PDn va lokalizatsiya talablari tekshirilmagan (C-09) — "
            "yuridik xulosa odam ishi; kod bu cheklovni o'lchay olmaydi."
        ),
    ),
    Constraint(
        code="CON-04",
        category="Интеграции",
        mark=Mark.DATA,
        fit=Fit.HONORED,
        note=(
            "Telegram Bot API — yagona kirish kanali: intake faqat bot "
            "orqali, boshqa kirish sirti yo'q (H-2 bilan bir ildiz)."
        ),
        binds=("app.bot.factory:create_bot", "app.reports.intake:create_report"),
    ),
    Constraint(
        code="CON-05",
        category="Технологии",
        mark=Mark.DATA,
        fit=Fit.BREACHED,
        note=(
            "Qator stekni qotiradi (PostgreSQL+PostGIS, Redis, Kafka, "
            "Go/Python/Node, React+MapLibre, Kubernetes) va "
            f"«{DOC_SEPARATE_STACK_BAN}» deydi. Repo aynan alohida stek: "
            "ADR-05 Kafka/Redis ni chiqargan (`outbox` — «Kafka "
            "o'rnida»), deploy Docker Compose, Kubernetes yo'q. Ikkala "
            "hujjat ham qonun — 👤 qaysi haq (ehtimol §15 Toshkent "
            "platformasini tasvirlaydi, lekin buni hujjat aytmaydi)."
        ),
        binds=("app.notifications.models:OutboxMessage", "docker-compose.yml"),
        gap="BRD qotirgan stek ↔ ADR-05/`04` steki — ikki qonun to'qnashuvi (👤).",
    ),
    Constraint(
        code="CON-06",
        category="Данные",
        mark=Mark.DATA,
        fit=Fit.HONORED,
        note=(
            "Manzil spravochnigi yo'qligi startni cheklaydi — mahsulot "
            "shunga mos qurilgan: manzil qidiruvisiz, faqat nuqta-kirish "
            "(H-6 rad tomonga)."
        ),
        binds=("app.bot.handlers:on_location",),
    ),
    Constraint(
        code="CON-07",
        category="Организационные",
        mark=Mark.ESTIMATE,
        fit=Fit.UNTESTED,
        note=(
            "Bus factor va moderatsiya yuki — tashkiliy masala; solo "
            "ishlab chiquvchi modeli bu riskning o'zi. Kod o'lchamaydi."
        ),
    ),
)


# --------------------------------------------------------------------------
# §16 — risklar, hujjatdagi tartibda
# --------------------------------------------------------------------------

RISKS: tuple[RiskRow, ...] = (
    RiskRow(
        code="RS-01",
        summary="Talab pastligi: karta bo'sh qoladi",
        likelihood=Likelihood.MEDIUM,
        impact=Impact.CRITICAL,
        score=Score.HIGH,
        readiness=Readiness.PARTIAL,
        note=(
            "Faza 0 va no-go tayyorligi — odam ishi. «Порог публикации "
            "карты» esa qurilmagan: `BR-013`/`BRL-12` darvoza o'rniga "
            "dislaymer qurganini qayd etgan — chora ro'yxatidagi "
            "mexanizmning o'zi yo'q."
        ),
        binds=("app.stats.maturity:compute",),
        gap="Nashr darvozasi o'rniga dislaymer (`OQ-5`, 👤).",
    ),
    RiskRow(
        code="RS-02",
        summary="Mahalla chegaralari yo'q yoki noaniq",
        likelihood=Likelihood.HIGH,
        impact=Impact.HIGH,
        score=Score.HIGH,
        readiness=Readiness.PARTIAL,
        note=(
            "Fallback qurilgan: H3 panjara mahallasiz ishlaydi, biriktirish "
            "bo'sh jadvalda ham yiqilmaydi. Raqamlashtirish — 👤 "
            "(2026-08-11 qarori: OSM, qamrov qisman bo'lishi OK)."
        ),
        binds=("app.geo.pipeline:find_mahalla_id", "app.stats.heatmap:build"),
        gap="Poligonlar hali yo'q — E17 ⬜ (👤).",
    ),
    RiskRow(
        code="RS-03",
        summary="Ma'muriy islohot bo'linishni o'zgartiradi",
        likelihood=Likelihood.MEDIUM,
        impact=Impact.HIGH,
        score=Score.HIGH,
        readiness=Readiness.READY,
        note="Chegara versiyalash birinchi kundan qurilgan (`BR-002` BUILT).",
        binds=(
            "app.geo.queries:districts_for_period",
            "tests/test_stats_boundaries.py",
        ),
    ),
    RiskRow(
        code="RS-04",
        summary="Rasmiy manba yo'q; sverka funksiyasi ishlamaydi",
        likelihood=Likelihood.HIGH,
        impact=Impact.MEDIUM,
        score=Score.MEDIUM,
        readiness=Readiness.READY,
        note=(
            "Aynan chora aytganidek qurilgan: rasmiy qatlamsiz ishga "
            "tushish mumkin, qatlamlar ajratilgan, to'liqsizlik "
            "dislaymeri vitrinada."
        ),
        binds=("app.reports.sources:SOURCES", "app.stats.maturity:compute"),
    ),
    RiskRow(
        code="RS-05",
        summary="Til gipotezasi noto'g'ri: UZ standarti konversiyani pasaytiradi",
        likelihood=Likelihood.LOW,
        impact=Impact.MEDIUM,
        score=Score.LOW,
        readiness=Readiness.PARTIAL,
        note=(
            "Yengil til almashtirish qurilgan (bot menyusi, har xabarda "
            "til konteksti); A/B — Faza 0 odam ishi."
        ),
        binds=("app.bot.handlers:on_language",),
        gap="A/B o'lchovi Faza 0 bilan birga kutadi (👤).",
    ),
    RiskRow(
        code="RS-06",
        summary="PDn va lokalizatsiya talablariga nomuvofiqlik",
        likelihood=Likelihood.MEDIUM,
        impact=Impact.HIGH,
        score=Score.HIGH,
        readiness=Readiness.HUMAN,
        note="Yuridik tekshiruv va rezident hosting — butunlay odam ishi (D-08, D-10).",
    ),
    RiskRow(
        code="RS-07",
        summary="Kengayish Toshkent statistikasini migratsiyada buzadi",
        likelihood=Likelihood.MEDIUM,
        impact=Impact.HIGH,
        score=Score.HIGH,
        readiness=Readiness.FOREIGN,
        note=(
            "Toshkent platformasining ko'chirish ishi — bu repoda sirt "
            "yo'q va bo'lmaydi. Diqqat: 👤 qarori (`CLAUDE.md` §2) "
            "moliyaviy gate sifatida «RS-07» ni sanaydi — moliyaviy "
            "`RS-07` aslida `01` §26 da, BRD niki esa shu qator; "
            "nomfazo to'qnashuvining amaliy zarari (👤 aniqlashtirish)."
        ),
    ),
    RiskRow(
        code="RS-08",
        summary="Ikkinchi mintaqaga moderator yetishmaydi",
        likelihood=Likelihood.HIGH,
        impact=Impact.MEDIUM,
        score=Score.MEDIUM,
        readiness=Readiness.PARTIAL,
        note=(
            "Navbat va moderatsiya asboblari qurilgan (E8 🔄); "
            "prioritetlash oddiy FIFO, volontyor yig'ish — odam ishi."
        ),
        binds=("app.admin.service:merge_outage", "app.clustering.service:moderate"),
        gap="Avtomatik prioritetlash yo'q; volontyorlar 👤.",
    ),
    RiskRow(
        code="RS-09",
        summary="Moliya Faza 1 o'rtasida to'xtab qoladi",
        likelihood=Likelihood.MEDIUM,
        impact=Impact.CRITICAL,
        score=Score.HIGH,
        readiness=Readiness.READY,
        note=(
            "Chora — o'zi yetarli inkrementlar; ish tartibining o'zi "
            "shunday quriladi: har run ishlaydigan holat qoldiradi, epic "
            "xaritasi mustaqil bo'laklardan iborat (`04`, yo'l xaritasi "
            "reyestri)."
        ),
        binds=("app.release.roadmap:evaluate",),
    ),
    RiskRow(
        code="RS-10",
        summary="SMI Samarqand statistikasini Toshkent bilan noto'g'ri solishtiradi",
        likelihood=Likelihood.MEDIUM,
        impact=Impact.MEDIUM,
        score=Score.MEDIUM,
        readiness=Readiness.PARTIAL,
        note=(
            "Coverage Index va metodologiya sahifasi qurilgan. Birinchi "
            f"tayanch — `{RS10_EMPTY_GUARD}` — esa `business_rules` da "
            "vacuous ABSENT: taqiqni bajaradigan sirt ham, buzadigan "
            "sirt ham yo'q. Risk jadvalining himoyasi bo'sh qoidaga "
            "tayanadi."
        ),
        binds=(
            "app.stats.coverage:compute",
            "app.stats.methodology:build",
            "app.release.business_rules:RULES",
        ),
        gap=f"`{RS10_EMPTY_GUARD}` mexanizmsiz — himoyaning birinchi tayanchi bo'sh.",
    ),
    RiskRow(
        code="RS-11",
        summary="H3 razresheniyasi noto'g'ri tanlangan",
        likelihood=Likelihood.MEDIUM,
        impact=Impact.MEDIUM,
        score=Score.MEDIUM,
        readiness=Readiness.READY,
        note=(
            "Konfiguratsiyalanadigan razresheniya qurilgan (`BR-006`); "
            "kalibrlash asbobi tayyor (`tools/recluster.py`), haqiqiy "
            "ma'lumot E10 bilan keladi."
        ),
        binds=("app.core.config:Settings.h3_resolution", "tools/recluster.py"),
    ),
    RiskRow(
        code="RS-12",
        summary="Operator yoki hokimiyat servisni dushman deb qabul qiladi",
        likelihood=Likelihood.LOW,
        impact=Impact.HIGH,
        score=Score.MEDIUM,
        readiness=Readiness.PARTIAL,
        note=(
            "Texnik yarmi qurilgan: qatlamlar ajratilgan, metodologiya "
            "ochiq, spravochnik maqomi dislaymerda. Kooperatsiya "
            "pozitsiyasi — odam ishi."
        ),
        binds=("app.reports.sources:SOURCES", "app.stats.methodology:build"),
        gap="Munosabatlar qismi kod bilan o'lchanmaydi (👤).",
    ),
)


# --------------------------------------------------------------------------
# §17 — bog'liqliklar, hujjatdagi tartibda
# --------------------------------------------------------------------------

DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency(
        code="D-01",
        summary="Telegram Bot API",
        dep_type="Внешняя техническая",
        criticality=Criticality.CRITICAL,
        owner="Telegram",
        standing=Standing.READY,
        note="Webhook va bot to'liq qurilgan; haqiqiy token 👤 (E3-a).",
        binds=("app.bot.factory:create_bot",),
    ),
    Dependency(
        code="D-02",
        summary="Samarqand mahalla chegaralari",
        dep_type="Внешняя данные",
        criticality=Criticality.CRITICAL,
        owner="Органы махаллей / картографические источники",
        standing=Standing.READY,
        note=(
            "Sxema, import va versiyalash tayyor; ma'lumotning o'zi 👤 "
            "(OSM qarori, qisman qamrov OK — 2026-08-11)."
        ),
        binds=("tools/import_boundaries.py", "app.geo.models:Mahalla"),
    ),
    Dependency(
        code="D-03",
        summary="Shahar ma'muriy bo'linishi haqidagi rasmiy qaror",
        dep_type="Внешняя правовая",
        criticality=Criticality.HIGH,
        owner="Хокимият",
        standing=Standing.HUMAN,
        note="Versiyalash har ikki natijani ko'taradi — kod kutmaydi, jarayon kutadi.",
        binds=("app.geo.queries:districts_for_period",),
    ),
    Dependency(
        code="D-04",
        summary="Mintaqa manzil spravochnigi",
        dep_type="Внешняя данные",
        criticality=Criticality.HIGH,
        owner="Открытые/государственные источники",
        standing=Standing.MOOT,
        note=(
            "Qurilgan mahsulot manzil qidiruvisiz ishlaydi (nuqta-kirish, "
            "H-6 rad tomonga) — «yuqori kritiklik» repo uchun o'lik "
            "(👤 H-6 savolining davomi)."
        ),
    ),
    Dependency(
        code="D-05",
        summary="Rasmiy xabarlarning ochiq kanallari",
        dep_type="Внешняя данные",
        criticality=Criticality.MEDIUM,
        owner="1055 / оператор сети",
        standing=Standing.HUMAN,
        note="E18 ⬜ — H-4 natijasi va manba kelishuvi 👤; parsing quriladi keyin.",
    ),
    Dependency(
        code="D-06",
        summary="Samarqandni qoplaydigan geokoder",
        dep_type="Внешняя техническая",
        criticality=Criticality.HIGH,
        owner="Поставщик геосервисов",
        standing=Standing.MOOT,
        note=(
            "Konfiguratsiya sirti bor (`geocoder_provider`), mexanizm "
            "yo'q va kerak emas: kirish faqat nuqta bilan. D-04 bilan "
            "bir juft — hujjat kutgan mahsulot boshqa edi."
        ),
        binds=("app.core.config:Settings.geocoder_provider",),
    ),
    Dependency(
        code="D-07",
        summary="Karta tayllari (MapLibre)",
        dep_type="Внешняя техническая",
        criticality=Criticality.MEDIUM,
        owner="Поставщик тайлов",
        standing=Standing.LIVE,
        note="👤 ADR-08 hal (2026-08-11): manba OSM; env va deploy tayyor.",
        binds=("app.core.config:Settings.map_tile_url", "web/"),
    ),
    Dependency(
        code="D-08",
        summary="PDn va lokalizatsiya bo'yicha yuridik xulosa",
        dep_type="Внутренняя",
        criticality=Criticality.CRITICAL,
        owner="Владелец продукта",
        standing=Standing.HUMAN,
        note="Kritik yo'lning boshi; C-09 bilan bir ildiz — butunlay odam ishi.",
    ),
    Dependency(
        code="D-09",
        summary="Toshkent Faza 1 (insident modeli, dedupikatsiya)",
        dep_type="Внутренняя",
        criticality=Criticality.CRITICAL,
        owner=TEAM_OWNER,
        standing=Standing.MOOT,
        note=(
            "Repo o'z klasterlash va dedupini qurib bo'lgan (E5 ✅) — "
            "«meros» qaramlik qurilgan mahsulotda mavjud emas. Ustiga "
            "egasi «Команда» — kritik yo'l da'vosi bilan bitta bo'limda "
            "qarama-qarshi."
        ),
        binds=("app.clustering.service:assign",),
    ),
    Dependency(
        code="D-10",
        summary="RUz da rezidentlikka ega hosting",
        dep_type="Внешняя инфраструктурная",
        criticality=Criticality.HIGH,
        owner="Провайдер",
        standing=Standing.HUMAN,
        note="Deploy skripti har qanday VPS ga tayyor; provayder tanlovi 👤.",
        binds=("scripts/deploy.sh",),
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessEnvironmentReport:
    """BRD §14–§17 ning bugungi holati."""

    assumptions: tuple[Assumption, ...]
    constraints: tuple[Constraint, ...]
    risks: tuple[RiskRow, ...]
    dependencies: tuple[Dependency, ...]

    def __post_init__(self) -> None:
        self._check_codes()
        self._check_assumptions()
        self._check_constraints()
        self._check_risks()
        self._check_dependencies()
        self._check_collision()

    # -- qorovullar --------------------------------------------------------

    def _check_codes(self) -> None:
        pairs = (
            (self.assumptions, "A", SPEC_ASSUMPTION_ROWS),
            (self.constraints, "CON", SPEC_CONSTRAINT_ROWS),
            (self.risks, "RS", SPEC_RISK_ROWS),
            (self.dependencies, "D", SPEC_DEPENDENCY_ROWS),
        )
        for rows, prefix, count in pairs:
            expected = [f"{prefix}-{i:02d}" for i in range(1, count + 1)]
            if [r.code for r in rows] != expected:
                raise BusinessEnvironmentError(
                    f"{prefix}-* kodlari yoki tartibi buzilgan"
                )

    def _check_assumptions(self) -> None:
        postures = {h.code: h.posture for h in ph0.HYPOTHESES}
        for row in self.assumptions:
            if row.mark not in ASSUMPTION_MARKS:
                raise BusinessEnvironmentError(f"{row.code}: §14 da {row.mark} bo'lmaydi")
            if row.hypothesis:
                if row.hypothesis not in postures:
                    raise BusinessEnvironmentError(
                        f"{row.code}: gipoteza {row.hypothesis} `phase0_plan` da yo'q"
                    )
                derived = (
                    Answer.OPEN
                    if postures[row.hypothesis] is ph0.Posture.OPEN
                    else Answer.PREJUDGED
                )
                if row.answer is not derived:
                    raise BusinessEnvironmentError(
                        f"{row.code}: javob {row.answer}, gipoteza posturasi "
                        f"esa {derived} talab qiladi"
                    )
            if row.answer is Answer.PREJUDGED and not row.binds:
                raise BusinessEnvironmentError(f"{row.code}: `PREJUDGED` dalilsiz bo'lmaydi")

    def _check_constraints(self) -> None:
        for row in self.constraints:
            if row.fit in (Fit.BREACHED, Fit.WAIVED) and not row.gap:
                raise BusinessEnvironmentError(f"{row.code}: farq bor, `gap` yozilmagan")
            if row.fit is Fit.HONORED and not row.binds:
                raise BusinessEnvironmentError(f"{row.code}: `HONORED` dalilsiz bo'lmaydi")

    def _check_risks(self) -> None:
        for row in self.risks:
            if row.readiness is Readiness.READY and not row.binds:
                raise BusinessEnvironmentError(f"{row.code}: `READY` dalilsiz bo'lmaydi")
            if row.readiness is Readiness.PARTIAL and not row.gap:
                raise BusinessEnvironmentError(f"{row.code}: `PARTIAL` da `gap` majburiy")

    def _check_dependencies(self) -> None:
        by_code = {d.code: d for d in self.dependencies}
        for code in CRITICAL_PATH:
            if code not in by_code:
                raise BusinessEnvironmentError(f"kritik yo'lda noma'lum kod: {code}")
        for row in self.dependencies:
            if row.standing in (Standing.LIVE, Standing.READY) and not row.binds:
                raise BusinessEnvironmentError(
                    f"{row.code}: {row.standing} dalilsiz bo'lmaydi"
                )
            if row.standing is Standing.MOOT and not row.note:
                raise BusinessEnvironmentError(f"{row.code}: `MOOT` sababsiz bo'lmaydi")

    def _check_collision(self) -> None:
        ours = {r.code for r in self.risks}
        theirs = {e.code for e in prd_risks.RISKS}
        if theirs - ours:
            raise BusinessEnvironmentError(
                "`01` §26 kodlari BRD §16 dan tashqariga chiqdi — "
                "to'qnashuv topilmasi eskirgan"
            )
        vacuous = {r.code for r in brl.evaluate().vacuously_honored}
        if RS10_EMPTY_GUARD not in vacuous:
            raise BusinessEnvironmentError(
                f"{RS10_EMPTY_GUARD} endi vacuous emas — `RS-10` bahosi eskirgan"
            )

    # -- kesimlar ----------------------------------------------------------

    @property
    def prejudged(self) -> tuple[Assumption, ...]:
        """Mahsulot javobni tanlab bo'lgan taxminlar. Bugun 10 dan 6 tasi."""
        return tuple(a for a in self.assumptions if a.answer is Answer.PREJUDGED)

    @property
    def open_assumptions(self) -> tuple[Assumption, ...]:
        return tuple(a for a in self.assumptions if a.answer is Answer.OPEN)

    @property
    def breached(self) -> tuple[Constraint, ...]:
        """Repo buzayotgan cheklovlar: bugun `CON-02` (muddat) va `CON-05` (stek)."""
        return tuple(c for c in self.constraints if c.fit is Fit.BREACHED)

    @property
    def waived(self) -> tuple[Constraint, ...]:
        """👤 qarori bilan chetga qo'yilganlar: bugun faqat byudjet."""
        return tuple(c for c in self.constraints if c.fit is Fit.WAIVED)

    @property
    def by_readiness(self) -> dict[Readiness, tuple[str, ...]]:
        result: dict[Readiness, list[str]] = {r: [] for r in Readiness}
        for row in self.risks:
            result[row.readiness].append(row.code)
        return {r: tuple(codes) for r, codes in result.items()}

    @property
    def unguarded_risks(self) -> tuple[RiskRow, ...]:
        """Chorasi repoda to'liq bo'lmagan risklar (`READY` dan boshqa hammasi)."""
        return tuple(r for r in self.risks if r.readiness is not Readiness.READY)

    @property
    def moot(self) -> tuple[Dependency, ...]:
        """Qurilgan mahsulotda o'lik bog'liqliklar: `D-04`, `D-06`, `D-09`."""
        return tuple(d for d in self.dependencies if d.standing is Standing.MOOT)

    @property
    def critical_path(self) -> tuple[Dependency, ...]:
        by_code = {d.code: d for d in self.dependencies}
        return tuple(by_code[c] for c in CRITICAL_PATH)

    @property
    def critical_path_claim_holds(self) -> bool:
        """§17 da'vosi: «uchtasi ham jamoa nazoratida emas».

        Jadvalning o'zi rad etadi: `D-09` ning egasi — jamoa. Da'vo
        hisoblanadi, e'lon qilinmaydi — jadval o'zgargan kuni bu
        xususiyat ham o'zgaradi.
        """
        return all(d.owner != TEAM_OWNER for d in self.critical_path)

    @property
    def rs_collision(self) -> tuple[str, ...]:
        """Ikkala hujjatda ham band `RS-*` kodlari — bugun o'ntasi."""
        theirs = {e.code for e in prd_risks.RISKS}
        return tuple(r.code for r in self.risks if r.code in theirs)

    @property
    def accurate(self) -> bool:
        """§14–§17 «rioya qilingan muhit» deb o'qilsa rostmi. Bugun `False`:

        ikki cheklov buzilgan, kritik yo'l da'vosi jadvalga zid, o'nta
        `RS-*` kodi boshqa hujjat bilan to'qnashadi.
        """
        return (
            not self.breached
            and self.critical_path_claim_holds
            and not self.rs_collision
        )


def evaluate() -> BusinessEnvironmentReport:
    """Reyestrdan to'liq hisobot. Argument yo'q — 85–87, 99–102 runlar qoidasi."""
    return BusinessEnvironmentReport(
        assumptions=ASSUMPTIONS,
        constraints=CONSTRAINTS,
        risks=RISKS,
        dependencies=DEPENDENCIES,
    )

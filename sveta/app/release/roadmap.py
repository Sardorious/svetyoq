"""Mahsulot yo'l xaritasi (`01` §24 «Product Roadmap»).

**Nima uchun bu modul bor.** Uchta run ketma-ket bir xil joyga bordi va
uchalasi ham u yerda to'xtadi:

* **70-run** (`01` §23): Faza 0 natijasi qayerda qayd etiladi — ochiq savol;
* **75-run** (`01` §26/§27): o'n sakkiz banddan **o'n to'rttasi**
  `SCHEDULED`, ya'ni reyestrning yarmini yolg'onga chiqarib bo'lmaydi, va
  sabab bitta — Faza 0 natijasi repoda saqlanmaydi;
* **77-run** (`01` §25): beshta relizdan ikkitasining sharti
  `Gate.UNRECORDED`, sabab o'sha.

Ya'ni uchta reyestr bir xil bo'shliqqa **havola qiladi** va uning o'zi
hech qayerda o'lchanmaydi. §24 — o'sha bo'shliqning manzili: yettita
Faza 0 vazifasi, beshta chiqish mezoni va uchta keyingi faza.

## Asosiy topilma: gate yopilmagan, ortidagi mazmun esa qurilgan

Bo'limning epigrafi mahsulotning eng qat'iy rejalashtirish qoidasini
beradi: «Phase 0 — **единственный шлюз**. Бюджеты Phase 1–2 не
утверждаются до прохождения критериев выхода Phase 0.» Hujjatning o'zi
beshala mezonni ham **belgilanmagan** katakcha bilan yozadi (`- [ ]`),
ya'ni gate bugungacha yopilmagan — va bu hujjatning o'z e'tirofi.

Gate ortida esa Phase 1 turibdi va uning beshala bo'lagi ham qurilgan:
mintaqa konfiguratsiyasi va spravochniklar (E19/E2), UZ-first
(`DEFAULT_LANGUAGE`), mahalla darajasidagi Coverage Index (E14) va
dislaymerli statistika vitrinasi (23-run). Phase 2 ning uchdan biri ham
qurilgan (bildirishnoma radiusining **mexanizmi**, kalibrlanmagan
qiymati bilan).

Bu tugallanmagan ish emas va reja buzilgani ham emas — bu **reja o'z
qoidasini bugungi holatga nisbatan yolg'on qilib qo'ygani**. Shuning
uchun `gate_holds` — hisobotning bosh xossasi, `architecture.
headline_holds` bilan bir xil rol.

## `RECORDED` sinfi bo'sh — va bu bo'limning butun mazmuni

`Landing` — Faza 0 vazifasining **natijasi** repoda qayerga tushishi.
To'rtta sinfdan biri (`RECORDED`) bugun **birorta ham** band bilan
to'ldirilmagan, va bu tasodif emas: 75-, 76- va 77-runlarning uchalasi
ham aynan shu bo'shliqqa tayanib to'xtagan edi. Sinf ataylab
saqlanadi (81-run ning `Trigger.UNMEASURED` i bilan bir xil sabab) —
u bo'shliqni **nomlaydi**, va Faza 0 natijasi uchun joy paydo bo'lganda
kerak bo'ladi.

`INSTRUMENTED` esa `RECORDED` ga yaqin **emas**: repo javobni hisoblay
oladi, lekin uni hech qayerda saqlamaydi, ya'ni javob har safar qaytadan
olinadi va gate ni yopa olmaydi.

## `Bearing`: gipoteza tekshirilmasdan **qabul qilingan** bo'lsa

Ikkinchi o'q `Landing` ni takrorlamaydi. §24 ning uchinchi ustuni
«Проверяемая гипотеза» deb ataladi, ya'ni har qator **ochiq savol**
deb da'vo qiladi. Ikkita qatorda bu da'vo noto'g'ri:

* **P0-1** («Наличие официального слоя данных») — `0003` migratsiyasi
  `official` manbasini `is_authoritative=True` bilan seed qiladi, ya'ni
  rasmiy qatlam **bor** deb qabul qilingan va undan kelgan birinchi
  xabar hodisani darhol `confirmed` qiladi (`06` §2.2). 73-run buni
  `PRESUMED` deb belgilagan edi; §24 esa o'sha qarorni hali
  tekshirilmagan gipoteza deb yozadi.
* **P0-3** («языковой профиль») — `i18n.DEFAULT_LANGUAGE = "uz"` modul
  konstantasi, va `01` §7 uni MVP ko'lamiga `PG-S3` bilan kiritadi.

Uchinchi sinf — `FORECLOSED`, va u bittada: **P0-5** geokoderning
to'liqligini tekshiradi, mahsulot esa manzilni umuman geokodlamaydi
(69-run; `GEOCODER_*` sozlamasi yo'q, 75-run `RS-04` ni shu sababdan
`FORECLOSED` deb belgilagan). Bunday vazifa yiqila olmaydi: uning
gipotezasi mahsulotdan chiqarilgan.

## Teskari yo'nalish: fazalar nomlamaydigan qurilgan sirtlar

§24 uchta fazada mahsulotning bugungi **tugallangan** qismlarini
sanamaydi: ommaviy API va OpenAPI (E15), admin-panel va moderatsiya
(E8), issiqlik xaritasi (E16). Birinchi ikkitasi 77-runda `01` §25 da
ham topilgan edi — ya'ni `01` ning **ikkala** rejalashtirish bo'limi
ham ularni tushirib qoldiradi, bu esa bitta jadvalning qirrasi emas,
hujjatning tizimli bo'shlig'i.

## Nima ataylab tekshirilmaydi

Muddatlar. §24 «Сроки не проставлены намеренно» deydi va bu **qaror**;
reyestrda sana maydoni yo'q va bo'lmasligi kerak.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Bo'limning hujjatdagi manzili.
SPEC = "01 §24"

#: Faza 0 vazifalari jadvalining qatorlari soni. **Aynan**: ro'yxat yopiq.
SPEC_TASKS = 7

#: Chiqish mezonlarining soni (belgilanadigan katakchalar).
SPEC_CRITERIA = 5

#: Faza 0 dan keyingi fazalar soni. Faza 0 ning «mazmuni» — vazifalar
#: jadvalining o'zi, shuning uchun u bu ro'yxatda yo'q.
SPEC_PHASES = 3

#: Vazifalar jadvalining sarlavha qatori — ustunlar tarkibi ham kontrakt.
#: Uchinchi ustunning nomi bo'limning butun da'vosi: har qator **ochiq**
#: savol deb e'lon qilinadi.
SPEC_TASK_COLUMNS: tuple[str, ...] = ("ID", "Задача", "Проверяемая гипотеза")

#: Epigrafning birinchi jumlasi — rejalashtirishning eng qat'iy qoidasi.
HEADLINE = "Phase 0 — единственный шлюз."

#: O'sha qoidaning o'lchanadigan yarmi.
HEADLINE_CLAIM = "Бюджеты Phase 1–2 не утверждаются до прохождения критериев выхода Phase 0."

#: Muddatlar haqidagi qaror — reyestrda sana maydoni yo'qligining sababi.
NO_DATES = "Сроки не проставлены намеренно."


class Landing(StrEnum):
    """Faza 0 bandining **natijasi** repoda qayerga tushadi."""

    #: Joy bor va bugun javobni saqlaydi.
    RECORDED = "recorded"
    #: Repo javobni hisoblay oladi, lekin uni saqlamaydi — ya'ni javob
    #: har safar qaytadan olinadi va gate ni yopa olmaydi.
    INSTRUMENTED = "instrumented"
    #: Joy umuman yo'q. 75-run ning `SCHEDULED` iga sabab shu.
    UNRECORDED = "unrecorded"
    #: Repodan tashqarida va tashqarida qolishi **kerak** (67-run sabog'i).
    EXTERNAL = "external"


#: Gate ni yopa oladigan yagona sinf.
CLOSING = Landing.RECORDED

#: Dalil **talab qilinadigan** sinf. `UNRECORDED` da mexanizmning
#: yo'qligi aynan baho; `EXTERNAL` da esa dalil bo'lishi mumkin emas.
LANDING_NEEDS_EVIDENCE: frozenset[Landing] = frozenset({Landing.RECORDED, Landing.INSTRUMENTED})


class Bearing(StrEnum):
    """Repo gipotezani tekshirilishidan **oldin** nima qilgan."""

    #: Hech narsa: vazifa haqiqatan ochiq savolni hal qiladi.
    OPEN = "open"
    #: Javob allaqachon kodda qaror sifatida yozilgan — vazifa uni faqat
    #: tasdiqlashi mumkin.
    ASSUMED = "assumed"
    #: Gipotezaning predmeti mahsulotdan chiqarilgan — vazifa yiqila
    #: olmaydi.
    FORECLOSED = "foreclosed"


#: §24 ning «Проверяемая гипотеза» da'vosini **buzadigan** sinflar.
PREJUDGED: frozenset[Bearing] = frozenset({Bearing.ASSUMED, Bearing.FORECLOSED})


class Delivery(StrEnum):
    """Fazaning mazmuni bugun qurilganmi."""

    BUILT = "built"
    PARTIAL = "partial"
    ABSENT = "absent"


@dataclass(frozen=True)
class Task:
    """Faza 0 jadvalining bitta qatori.

    `code`, `task` va `hypothesis` — hujjatdagi **so'zma-so'z** kataklar
    (`code` ham: jadvalda `ID` ustuni bor). Qolgani — baho.

    `near` faqat `UNRECORDED` da to'ldiriladi va aynan **javob
    bermaydigan** eng yaqin asbobga ishora qiladi: usiz «joy yo'q»
    bahosi asbob bor joyda ham bir xil ko'rinardi.
    """

    code: str
    task: str
    hypothesis: str
    landing: Landing
    bearing: Bearing
    note: str
    landing_binds: tuple[str, ...] = ()
    bearing_binds: tuple[str, ...] = ()
    near: tuple[str, ...] = ()

    @property
    def closes_gate(self) -> bool:
        return self.landing is CLOSING

    @property
    def is_prejudged(self) -> bool:
        """Gipoteza tekshirilmasdan hal qilinganmi."""
        return self.bearing in PREJUDGED


@dataclass(frozen=True)
class Criterion:
    """«Критерии выхода Phase 0» ro'yxatining bitta bandi.

    `checked` — hujjatdagi katakchaning holati. Bugun beshalasi ham
    `False`, va kontrakt testi buni ikki tomonlama bog'laydi: hujjatda
    belgi paydo bo'lsa, repoda uni saqlaydigan joy ham paydo bo'lishi
    kerak.
    """

    code: str
    text: str
    landing: Landing
    note: str
    binds: tuple[str, ...] = ()
    near: tuple[str, ...] = ()
    checked: bool = False

    @property
    def closes_gate(self) -> bool:
        return self.landing is CLOSING


@dataclass(frozen=True)
class Phase:
    """Faza 0 dan keyingi bitta faza."""

    code: str
    title: str
    content: str
    delivery: Delivery
    note: str
    binds: tuple[str, ...] = ()

    @property
    def is_started(self) -> bool:
        """Faza mazmunidan biror narsa qurilganmi."""
        return self.delivery is not Delivery.ABSENT


@dataclass(frozen=True)
class AheadOfPlan:
    """Qurilgan, §24 ning birorta fazasi nomlamaydigan sirt."""

    code: str
    phrase: str
    #: Eng yaqin faza — yo'q bo'lsa bo'sh satr.
    nearest_phase: str
    why_not_named: str
    binds: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# Reyestr — Faza 0 vazifalari
# --------------------------------------------------------------------------

#: **Tartib ma'noli** — hujjatdagi bilan bir xil; `code` lar hujjatning
#: `ID` ustunidan olinadi (§25 dan farqli: u yerda ID ustuni yo'q edi).
TASKS: tuple[Task, ...] = (
    Task(
        code="P0-1",
        task=(
            "Полевое наблюдение: существует ли региональный канал 1055, "
            "каков формат и частота публикаций"
        ),
        hypothesis="Наличие официального слоя данных",
        landing=Landing.UNRECORDED,
        bearing=Bearing.ASSUMED,
        note=(
            "Gipoteza allaqachon qabul qilingan: `0003` migratsiyasi "
            "`official` manbasini `weight=0.0`, `is_authoritative=True` "
            "bilan seed qiladi, ya'ni undan kelgan birinchi xabar "
            "hodisani darhol `confirmed` qiladi (`06` §2.2). 73-run buni "
            "`PRESUMED` deb belgilagan. Kuzatuvning **natijasi** esa "
            "hech qayerda saqlanmaydi: kanalning bor-yo'qligi, formati "
            "va chastotasi uchun na jadval, na sozlama bor. Ustiga `01` "
            "§7 MVP ko'lamiga «Ручной разбор публикаций 1055 (**если он "
            "существует**)» qatorini kiritadi va uning yo'li ham yo'q — "
            "`app/` da rasmiy kod bilan xabar yaratadigan chaqiruv "
            "topilmaydi (76-run, `DP-4`). Shu sababdan `01` §25 ning "
            "`R2.0` sharti ham `UNRECORDED` (77-run)."
        ),
        bearing_binds=(
            "app.reports.sources:SOURCES",
            "app.reports.sources:AUTHORITATIVE_CODES",
        ),
    ),
    Task(
        code="P0-2",
        task=("Замер частоты отключений в Самарканде по доступным открытым источникам"),
        hypothesis="Востребованность продукта",
        landing=Landing.UNRECORDED,
        bearing=Bearing.OPEN,
        note=(
            "Eng yaqin asbob bor va u **boshqa to'plamni** o'lchaydi: "
            "`stats.aggregate.build` uzilishlar chastotasini bizning "
            "o'z xabarlarimizdan quradi, §24 esa mahsulotdan tashqaridagi "
            "ochiq manbalarni so'raydi. Farq shakliy emas — vazifaning "
            "butun ma'nosi mahsulot **paydo bo'lgunga qadar** talabni "
            "o'lchashda, o'z xabarlarimiz esa mahsulot ishlaganidan keyin "
            "paydo bo'ladi. Ya'ni mavjud asbob bilan javob berish "
            "aylanma bo'lardi."
        ),
        near=("app.stats.aggregate:build",),
    ),
    Task(
        code="P0-3",
        task="8–12 интервью с жителями (заменяет персоны §5)",
        hypothesis="JTBD, языковой профиль, роль махаллинских чатов",
        landing=Landing.INSTRUMENTED,
        bearing=Bearing.ASSUMED,
        note=(
            "Uchta gipotezadan bittasi (til profili) o'lchanadi: "
            "`track.bot_start` hodisasi `language_detected` atributini "
            "chiqaradi. Lekin javob **jurnalga** yoziladi, bazaga emas, "
            "ya'ni qayd etilmaydi; ustiga u nimani o'lchayotgani ochiq "
            "savol — Telegram mijozining tili yoki amaldagi til (68-run). "
            "Gipotezaning o'zi esa allaqachon hal qilingan: "
            '`DEFAULT_LANGUAGE = "uz"` modul konstantasi va `01` §7 uni '
            "`PG-S3` bilan MVP ko'lamiga kiritadi. Qolgan ikkitasi "
            "(JTBD, mahalla chatlarining roli) repodan tashqarida: "
            "`01` §18 mahalla chatlarini «Вне системы» deb yozadi "
            "(73-run, `EXTERNAL`)."
        ),
        landing_binds=("app.analytics.track:bot_start",),
        bearing_binds=("app.core.i18n:DEFAULT_LANGUAGE",),
    ),
    Task(
        code="P0-4",
        task="Получение и проверка полигонов махаллей",
        hypothesis="Реализуемость трёхуровневой модели",
        landing=Landing.INSTRUMENTED,
        bearing=Bearing.OPEN,
        note=(
            "Vazifaning ikkinchi yarmi («проверка») repoda to'liq: "
            "`geo.quality` oltita tekshiruv beradi va `SQL_PROMOTE` "
            "faqat ulardan keyin yuradi. Birinchi yarmi («получение») "
            "esa umuman yo'q: `tools/import_boundaries.py` da `mahalla` "
            "so'zi **bir marta ham** uchramaydi va tekshiruvlar "
            "`districts` ustida yuriladi, ya'ni bo'sh to'plam ustida ham "
            "«bajarilgan» ko'rinadi (77-run, `RP-1`). Natijaning o'zi "
            "ham qayd etilmaydi: sifat hisoboti ekranda chiqadi va "
            "hech qayerda qolmaydi."
        ),
        landing_binds=(
            "app.geo.quality:check_validity",
            "app.geo.quality:SQL_PROMOTE",
        ),
    ),
    Task(
        code="P0-5",
        task="Проверка полноты геокодера на адресах Самарканда",
        hypothesis="Риск R-13",
        landing=Landing.UNRECORDED,
        bearing=Bearing.FORECLOSED,
        note=(
            "Vazifa mahsulotda **yo'q** komponentni tekshiradi: bot "
            "Telegram `location` pini bilan ishlaydi va manzilni "
            "koordinataga o'giradigan chaqiruv `app/` da umuman yo'q "
            "(69-run). Sozlamalar esa saqlanib qolgan — `Settings` da "
            "`geocoder_provider`/`geocoder_api_key`, `.env.example` da "
            "`GEOCODER_*` — va ularni **hech kim o'qimaydi**: 44-run ning "
            "parity testi kalitning mavjudligini ko'radi, ikkala tomon "
            "ham mavjud bo'lmagan quyi tizimni tasvirlayotganini emas "
            "(73-run, `PRESUMED`). 75-run shu sababdan `RS-04` ni "
            "`FORECLOSED` deb belgilagan: «Вероятность: Высокая» qatori "
            "0%. Ya'ni bu vazifa yiqila olmaydi — natijasi qanday "
            "bo'lishidan qat'i nazar mahsulot o'zgarmaydi. 👤 `GEOCODER_*` "
            "hujjatda qoladimi degan savol 69- va 73-runlardan beri ochiq."
        ),
    ),
    Task(
        code="P0-6",
        task=("Пилот на 1–2 махаллях: набор ≥N репортеров через актив махалли"),
        hypothesis="Гипотеза холодного старта",
        landing=Landing.UNRECORDED,
        bearing=Bearing.OPEN,
        note=(
            "Ikkita to'siq, ikkalasi ham qatorning o'z matnida. "
            "Birinchisi — `N` hech bir hujjatda belgilanmagan; `03` §6 "
            "ning `G-4` i xuddi shu joyda `threshold=None` bilan "
            "`UNMEASURED` bo'lib turibdi (66-run). Ikkinchisi — "
            "granulyarlik: pilot mahalla darajasida, yoqish esa mintaqa "
            "darajasida (`region_admin activate`), ya'ni «1–2 махалли» "
            "uchun alohida rejim yo'q (77-run, `RP-1`)."
        ),
        near=("app.release.gates:GATES",),
    ),
    Task(
        code="P0-7",
        task="Юридическая проверка (общая с платформой)",
        hypothesis="C-09",
        landing=Landing.EXTERNAL,
        bearing=Bearing.OPEN,
        note=(
            "Huquqiy xulosa repodan tashqarida va tashqarida qolishi "
            "kerak: uni kodga yozib qo'yish tekshirilgandek ko'rsatardi "
            "(67-run ning `EXTERNAL` sabog'i). `01` §31 C-09 ni Toshkent "
            "paketidan meros ochiq izoh deb e'lon qiladi va bu yerda "
            "qayta ochilmaydi."
        ),
    ),
)

TASK_BY_CODE: dict[str, Task] = {t.code: t for t in TASKS}


# --------------------------------------------------------------------------
# Reyestr — chiqish mezonlari
# --------------------------------------------------------------------------

#: **Tartib ma'noli**; `code` lar hujjatda yo'q (ro'yxatda ID ustuni yo'q)
#: va tartibdan yasaladi: `EX-N` = N-band.
CRITERIA: tuple[Criterion, ...] = (
    Criterion(
        code="EX-1",
        text="Языковой профиль подтверждён замером, а не гипотезой",
        landing=Landing.INSTRUMENTED,
        note=(
            "O'lchov mavjud (`track.bot_start` ning `language_detected` "
            "atributi), lekin band aynan «замером, а не гипотезой» deb "
            "yozilgan va bugungi gipoteza kodda **konstanta** bo'lib "
            "turibdi (`P0-3`). Ustiga o'lchovning o'zi jurnalga tushadi "
            "va hech qayerda saqlanmaydi, ya'ni bandni yopadigan dalil "
            "keyingi restartgacha yashaydi. 👤 «Доля сессий на UZ» nima "
            "o'lchashi 68-rundan beri ochiq savol."
        ),
        binds=("app.analytics.track:bot_start",),
    ),
    Criterion(
        code="EX-2",
        text="Полигоны махаллей получены и валидны",
        landing=Landing.INSTRUMENTED,
        note=(
            "«Валидны» — repoda o'lchanadi (`geo.quality`), «получены» — "
            "yo'q: mahalla poligonlarini import qiladigan yo'l umuman "
            "yozilmagan (`P0-4`). Bandning ikkala yarmi bitta katakda "
            "turgani uchun uni «bajarilgan» deb belgilash ikkinchi "
            "yarmini ko'rinmas qiladi."
        ),
        binds=(
            "app.geo.quality:check_names",
            "app.geo.quality:check_overlap_ratio",
        ),
    ),
    Criterion(
        code="EX-3",
        text=(
            "Пилот показал достижимость плотности репортов, при которой "
            "вердикт «массовое отключение» возникает"
        ),
        landing=Landing.INSTRUMENTED,
        note=(
            "Beshtadan yagona band bo'lib, u to'liq mahsulotning ichida "
            "yotadi: «вердикт возникает» — bu `confirmation.required_score` "
            "va `scale.raw_scale` ning qarori, ya'ni zichlik chegarasi "
            "kodda hisoblanadi. Asbob ham tayyor: `tools/simulate.py` "
            "oqim yasaydi, `tools/recluster.py --sweep` esa parametrni "
            "butun o'q bo'ylab yurgizadi (64-run, E11 uchun). Yetmayotgan "
            "narsa — **ma'lumot** (E10) va natijani saqlaydigan joy."
        ),
        binds=(
            "app.clustering.confirmation:required_score",
            "app.clustering.scale:raw_scale",
            "tools.simulate:generate",
            "tools.recluster:parse_sweep",
        ),
    ),
    Criterion(
        code="EX-4",
        text=("Определён источник финансирования регионального расширения (наследует C-04)"),
        landing=Landing.EXTERNAL,
        note=(
            "Moliyalashtirish manbai repodan tashqarida. `01` §4 ning "
            "tijorat metrikalari bo'limi buni ochiq yozadi: mahsulot "
            "notijorat va moliyalashtirish manbai yo'q (C-04). Dalil "
            "taqiqlanadi — 67-run ning `EXTERNAL` sabog'i."
        ),
    ),
    Criterion(
        code="EX-5",
        text="Установлены целевые значения KPI на основе замеров, а не переносов",
        landing=Landing.UNRECORDED,
        note=(
            "`01` §4 ning o'n ikkita KPI qatoridan **birortasining** ham "
            "Target ustuni o'lchovdan kelmaydi: hammasi `[ГИПОТЕЗА]` yoki "
            "«подлежит установке после Ph.0». Bu ziddiyat emas — §4 "
            "o'zining vaqtinchaligini e'lon qiladi — lekin o'lchangan "
            "qiymatni saqlaydigan joy repoda ham yo'q: `region_config` "
            "faqat mahsulot parametrlarini saqlaydi, KPI maqsadlarini "
            "emas. `03` §11 esa **nima o'lchanishini** aytadi, maqsad "
            "qiymatini emas (67-run)."
        ),
        near=("app.release.measures:MEASURES",),
    ),
)

CRITERION_BY_CODE: dict[str, Criterion] = {c.code: c for c in CRITERIA}


# --------------------------------------------------------------------------
# Reyestr — keyingi fazalar
# --------------------------------------------------------------------------

PHASES: tuple[Phase, ...] = (
    Phase(
        code="PH-1",
        title="Phase 1 — Регион в проде",
        content=(
            "Конфигурация региона, справочники, UZ-first, Coverage Index "
            "по махаллям, витрина статистики с дисклеймером."
        ),
        delivery=Delivery.BUILT,
        note=(
            "Beshala bo'lak ham qurilgan: mintaqa konfiguratsiyasi va "
            "spravochniklar (E19/E2, `region_admin` + `regions` bbox), "
            "UZ-first (`DEFAULT_LANGUAGE`), mahalla darajasidagi Coverage "
            "Index (E14, 32-run) va yosh mintaqa dislaymeri (23-run). "
            "Ustiga mintaqa **prodda jonli** (80-run: `activate`). Ya'ni "
            "gate ortidagi mazmun gate yopilmasdan yetkazilgan."
        ),
        binds=(
            "app.geo.registry:active_regions",
            "app.core.i18n:DEFAULT_LANGUAGE",
            "app.stats.mahalla_coverage:summarize",
            "app.stats.maturity:WARNING_YOUNG",
            "tools.region_admin:cmd_activate",
        ),
    ),
    Phase(
        code="PH-2",
        title="Phase 2 — Плотность и доверие",
        content=(
            "Расширение на все махалли города, калибровка радиуса "
            "уведомлений, автоматический парсинг регионального 1055."
        ),
        delivery=Delivery.PARTIAL,
        note=(
            "Uchtadan bittasining **mexanizmi** qurilgan: obuna radiusi "
            "bo'yicha yetkazish ishlaydi (E13), lekin kalibrlash yo'q — "
            "qiymat hali ham Toshkentniki, 500 m (74-run). Qolgan "
            "ikkitasi yo'q: mahallalarga kengayish poligonlarga tayanadi "
            "(`P0-4`), 1055 avtoparsingi esa umuman yozilmagan (76-run, "
            "`DP-4`)."
        ),
        binds=("app.notifications.service:process",),
    ),
    Phase(
        code="PH-3",
        title="Phase 3 — Область и интеграция",
        content="Районы области, переговоры с региональным оператором, Open Data.",
        delivery=Delivery.ABSENT,
        note=(
            "Uchala bo'lak ham yo'q. ⚠️ «Open Data» — hujjatdagi ommaviy "
            "ma'lumotga eng yaqin ibora, va u **uchinchi** fazada turibdi, "
            "holbuki ommaviy API bilan OpenAPI allaqachon qurilgan "
            "(E15) — quyidagi `AH-1` shuning uchun bor. `01` §26 ning "
            "`RS-09` i ham operator bilan muzokarani tashqi shart deb "
            "yozadi (75-run)."
        ),
    ),
)

PHASE_BY_CODE: dict[str, Phase] = {p.code: p for p in PHASES}


# --------------------------------------------------------------------------
# Teskari yo'nalish
# --------------------------------------------------------------------------

#: Qurilgan, §24 ning birorta fazasi nomlamaydigan sirtlar.
AHEAD: tuple[AheadOfPlan, ...] = (
    AheadOfPlan(
        code="AH-1",
        phrase="Ommaviy API va OpenAPI",
        nearest_phase="Phase 3 — Область и интеграция",
        why_not_named=(
            "Eng yaqin ibora — Phase 3 ning «Open Data» si, ya'ni reja "
            "bo'yicha ochiq ma'lumot ikkita yopilmagan gate ortida "
            "turibdi. Amalda `/openapi.json` ochiq va `01` §16 API "
            "talablarini alohida bo'lim qilib beradi (E15). 77-run "
            "aynan shu sirtni `01` §25 da ham topmagan edi."
        ),
        binds=("app.main:create_app", "app.api.v1.geo:router"),
    ),
    AheadOfPlan(
        code="AH-2",
        phrase="Admin-panel, moderatsiya va audit",
        nearest_phase="",
        why_not_named=(
            "§24 ning birorta fazasi moderatsiyani nomlamaydi, holbuki "
            "`03` ning `Q-2` qarori uni ommaviy xaritadan **oldin** "
            "qo'yadi va unga o'z relizini beradi (`R0.3`). Qurilgan: "
            "rollar, moderatsiya, audit jurnali (E8). 77-run buni "
            "`01` §25 da ham topgan — ya'ni `01` ning ikkala "
            "rejalashtirish bo'limi ham uni tushirib qoldiradi."
        ),
        binds=("app.admin.roles:Permission", "app.admin.audit:record"),
    ),
    AheadOfPlan(
        code="AH-3",
        phrase="H3 issiqlik xaritasi",
        nearest_phase="Phase 2 — Плотность и доверие",
        why_not_named=(
            "«Плотность» so'zi Phase 2 ning sarlavhasida turibdi, lekin "
            "faza mazmuni zichlikni **ko'rsatadigan** sirtni emas, "
            "mahallalarga kengayishni sanaydi. Issiqlik xaritasi esa "
            "qurilgan (E16) va qamrov indeksi bilan birga chiqadi "
            "(22-run). ⚠️ `FR-S-802` va `FR-S-804` bir xil shart uchun "
            "ikki xil zaxira darajasini nomlaydi (75-run) — o'sha "
            "chalkashlikning ikkinchi uchi shu yerda."
        ),
        binds=("app.stats.heatmap:build", "app.stats.heatmap:LOW_COVERAGE_BANDS"),
    ),
)


# --------------------------------------------------------------------------
# Reyestrning o'z qoidalari
# --------------------------------------------------------------------------


def _check_registry() -> None:
    """Reyestr o'z-o'ziga zid bo'lsa import paytida yiqiladi.

    Bu tekshiruvlar kontrakt testining o'rnini bosmaydi — ular
    reyestrni **yozayotgan** odamga qaratilgan (`plan.py` bilan bir xil
    rol).
    """
    if len(TASKS) != SPEC_TASKS:
        raise ValueError(f"{SPEC}: {len(TASKS)} vazifa, kutilgani {SPEC_TASKS}")
    if len(CRITERIA) != SPEC_CRITERIA:
        raise ValueError(f"{SPEC}: {len(CRITERIA)} mezon, kutilgani {SPEC_CRITERIA}")
    if len(PHASES) != SPEC_PHASES:
        raise ValueError(f"{SPEC}: {len(PHASES)} faza, kutilgani {SPEC_PHASES}")
    if len(TASK_BY_CODE) != len(TASKS) or len(CRITERION_BY_CODE) != len(CRITERIA):
        raise ValueError(f"{SPEC}: takrorlangan kod")

    for index, task in enumerate(TASKS, start=1):
        if task.code != f"P0-{index}":
            raise ValueError(f"{SPEC}: `{task.code}` {index}-qatorda turibdi")
        if not task.note:
            raise ValueError(f"{SPEC}: `{task.code}` izohsiz")
        if task.landing in LANDING_NEEDS_EVIDENCE and not task.landing_binds:
            raise ValueError(f"{SPEC}: `{task.code}` — `{task.landing}`, dalil yo'q")
        if task.landing not in LANDING_NEEDS_EVIDENCE and task.landing_binds:
            raise ValueError(
                f"{SPEC}: `{task.code}` — `{task.landing}`, lekin dalil "
                f"ko'rsatilgan: {task.landing_binds}"
            )
        # `ASSUMED` — fikr emas: javobni **allaqachon** o'zida saqlagan
        # simvol ko'rsatilishi shart, aks holda bahoni tekshirib bo'lmasdi.
        if task.bearing is Bearing.ASSUMED and not task.bearing_binds:
            raise ValueError(f"{SPEC}: `{task.code}` — `ASSUMED`, dalilsiz")
        if task.bearing is not Bearing.ASSUMED and task.bearing_binds:
            raise ValueError(f"{SPEC}: `{task.code}` — `{task.bearing}`, qabul dalili ortiqcha")
        # `near` — «joy yo'q» bahosini yumshatmaydi, uni **aniqlashtiradi**.
        if task.near and task.landing is not Landing.UNRECORDED:
            raise ValueError(f"{SPEC}: `{task.code}` — `near` faqat `UNRECORDED` da")

    for index, criterion in enumerate(CRITERIA, start=1):
        if criterion.code != f"EX-{index}":
            raise ValueError(f"{SPEC}: `{criterion.code}` {index}-bandda turibdi")
        if not criterion.note:
            raise ValueError(f"{SPEC}: `{criterion.code}` izohsiz")
        if criterion.landing in LANDING_NEEDS_EVIDENCE and not criterion.binds:
            raise ValueError(f"{SPEC}: `{criterion.code}` — `{criterion.landing}`, dalil yo'q")
        if criterion.landing not in LANDING_NEEDS_EVIDENCE and criterion.binds:
            raise ValueError(f"{SPEC}: `{criterion.code}` — `{criterion.landing}`, dalil ortiqcha")
        if criterion.near and criterion.landing is not Landing.UNRECORDED:
            raise ValueError(f"{SPEC}: `{criterion.code}` — `near` faqat `UNRECORDED` da")
        # Belgilangan katakcha — hujjatning «bajarildi» da'vosi. Uni
        # `RECORDED` siz qabul qilish gate ni dalilsiz yopardi.
        if criterion.checked and not criterion.closes_gate:
            raise ValueError(
                f"{SPEC}: `{criterion.code}` hujjatda belgilangan, natijasi esa qayd etilmaydi"
            )

    for index, phase in enumerate(PHASES, start=1):
        if phase.code != f"PH-{index}":
            raise ValueError(f"{SPEC}: `{phase.code}` {index}-fazada turibdi")
        if not phase.note:
            raise ValueError(f"{SPEC}: `{phase.code}` izohsiz")
        if phase.is_started and not phase.binds:
            raise ValueError(f"{SPEC}: `{phase.code}` — `{phase.delivery}`, dalil yo'q")
        if not phase.is_started and phase.binds:
            raise ValueError(f"{SPEC}: `{phase.code}` — `ABSENT`, lekin dalil ko'rsatilgan")

    for item in AHEAD:
        if not item.binds:
            raise ValueError(f"{SPEC}: `{item.code}` dalilsiz")
        if not item.why_not_named:
            raise ValueError(f"{SPEC}: `{item.code}` izohsiz")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RoadmapReport:
    """`01` §24 ning bugungi holati."""

    tasks: tuple[Task, ...]
    criteria: tuple[Criterion, ...]
    phases: tuple[Phase, ...]
    ahead: tuple[AheadOfPlan, ...]

    @property
    def by_landing(self) -> dict[Landing, tuple[str, ...]]:
        """Sinf → band kodlari (vazifalar va mezonlar birga)."""
        result: dict[Landing, list[str]] = {landing: [] for landing in Landing}
        for task in self.tasks:
            result[task.landing].append(task.code)
        for criterion in self.criteria:
            result[criterion.landing].append(criterion.code)
        return {landing: tuple(codes) for landing, codes in result.items()}

    @property
    def by_bearing(self) -> dict[Bearing, tuple[Task, ...]]:
        return {b: tuple(t for t in self.tasks if t.bearing is b) for b in Bearing}

    @property
    def recorded(self) -> tuple[str, ...]:
        """Natijasi repoda saqlanadigan bandlar.

        Bugun **bo'sh**, va aynan shu bo'shliq 75-, 76- va 77-runlarni
        to'xtatgan. Sinf ataylab saqlanadi.
        """
        return self.by_landing[Landing.RECORDED]

    @property
    def prejudged(self) -> tuple[Task, ...]:
        """Gipotezasi tekshirilmasdan hal qilingan vazifalar."""
        return tuple(t for t in self.tasks if t.is_prejudged)

    @property
    def unchecked(self) -> tuple[Criterion, ...]:
        """Hujjatda hali belgilanmagan chiqish mezonlari."""
        return tuple(c for c in self.criteria if not c.checked)

    @property
    def built_ahead(self) -> tuple[Phase, ...]:
        """Gate yopilmasdan turib boshlangan fazalar."""
        return tuple(p for p in self.phases if p.is_started)

    @property
    def gate_holds(self) -> bool:
        """Epigrafning da'vosi bugun bajarilyaptimi.

        «Phase 0 — единственный шлюз»: gate ortidagi mazmun gate
        yopilmasdan qurilmasligi kerak. Gate esa yopilmagan va buni
        hujjatning o'zi aytadi — beshala mezon ham belgilanmagan; repo
        tomondan ham hech narsa qayd etilmaydi (`recorded` bo'sh).
        Ya'ni bugungi yagona savol — gate ortida nima qurilgan.
        """
        if not self.unchecked and self.recorded:
            return True
        return not self.built_ahead

    @property
    def accurate(self) -> bool:
        """Bo'lim bugungi haqiqatni to'g'ri tasvirlaydimi.

        Uchta shart: epigrafning qoidasi bajarilsin, «проверяемая
        гипотеза» da'vosi har qatorda rost bo'lsin va fazalar
        nomlamaydigan qurilgan sirt qolmasin.
        """
        return self.gate_holds and not self.prejudged and not self.ahead


def evaluate() -> RoadmapReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi (`plan.evaluate`
    bilan bir xil sabab).
    """
    return RoadmapReport(tasks=TASKS, criteria=CRITERIA, phases=PHASES, ahead=AHEAD)

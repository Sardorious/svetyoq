"""User Flow, Business Process, UX va UI talablari (`01` §11–§14) ↔ qurilgan sirt.

**Nima uchun bu modul oxirgi bo'lib yozildi.** 92-run §11–§14 ni «umuman
bog'lanmagan» deb topgan, 93-run esa uni ataylab kechiktirgan: o'sha kunlarda
repoda **yurgizilmagan** qatlam turardi (`test_user_stories_contract.py`,
89-run yozgan modul + 90/91-run yozgan testlar) va yana bittasini qo'shish
xatoni ikki barobar arzon qilardi. 97-run o'sha to'siqni oldi — fayl birinchi
yurgizishda 69/69 o'tdi. Ya'ni bu bo'limlar navbatning oxirida turgani
uchun emas, **shart bajarilmagani uchun** kutgan.

## Bu bo'limlar qolganlardan nimasi bilan farq qiladi

Paketning boshqa bo'limlari serverga qaraydi: jadval, formula, endpoint,
xato kodi. §11–§14 esa **mijozga** qaraydi — ekran, tugma, shakl, rang,
ekran kengligi. Va aynan shu yerda repo eng kar: 96-run oxirida `web/` ni
o'qiydigan **to'rtta** test bor edi va to'rttasi ham uni `read_text()` +
regex bilan o'qiydi (`test_i18n_key_contract`, `test_map_api`,
`test_notification_channels_contract`, `test_region_acceptance_contract`).

Buning narxi o'lchandi: 94, 95 va 96-runlar `web/` da **oltita** defekt
topdi va **birortasi ham** matn qatlamida ko'rinmasdi —

* `#heat-legend` `.legend` ning **ichida** turgani (94-run): tuzilma,
  ya'ni ota-bola munosabati. `display: none` ni matnda ko'rish mumkin,
  kimga tegishini esa mumkin emas.
* bitta argumentli `banner()` ga uch mustaqil manba yozgani (95-run):
  chaqiruv grafi.
* `#heat` kalitchasining brauzer tiklagan holati `heatOn = false` bilan
  ajralib ketgani (95-run): ikki fayl orasidagi boshlang'ich holat.
* `tiles` uyasi `baseStyle()` da bir marta qo'yilib, `applyStrings()` da
  qayta hisoblanmagani (96-run): qaysi funksiya qaysi tikda chaqiriladi.

Har birida hujjatning **harfi** bajarilgan edi. Shuning uchun bu
reyestrning uchinchi o'qi «talab bajarildimi» emas — **«uni repo umuman
ko'ra oladimi va qanday chuqurlikda»** (`Witness`).

## Uchta o'q

1. `Surface` — talab nomlagan narsa qurilganmi (§13/§14 ning qatori,
   §11 ning tuguni).
2. `Witness` — o'sha narsani repo qanday chuqurlikda ko'radi:
   xatti-harakat testi, tuzilma o'quvchisi, matn regexi, hech narsa,
   yoki faqat odam ko'zi.
3. `Voice` — talab paketda **necha marta** aytilgan. §11–§14 ning eng
   ko'zga ko'rinadigan xossasi shu: ular boshqa bo'limlarni qayta
   aytadi va nusxalar bir-biriga bog'lanmagan.

Uchalasi mustaqil. `REALIZED` + `UNWATCHED` — bugungi `web/` ning
normasi. `ABSENT` + `HUMAN` — 3G, kontrast, satr uzunligi. `REALIZED` +
`CONFLICTED` — eng yomoni: kod ikkita nusxadan birini tanlagan va
tanlagani hech qayerda yozilmagan.

## §11 — diagramma **graf**, ro'yxat emas

Bu bo'lim paketda yagona: uning artefakti jadval emas, o'n beshta tugun
va o'n sakkizta yoy. Shuning uchun undan boshqa bo'limlardan
olinmaydigan savol chiqadi — **yo'l**: tugun qurilgani yetmaydi, unga
**yetib borish** kerak.

Ikkita tugun qurilmagan va ikkalasi ham yo'lni uzadi:

* `I` «Ввод адреса» — sirtsiz. Geokoder paketda uch joyda bor
  (`GEOCODER_PROVIDER`/`GEOCODER_API_KEY` sozlamalari, `01` §16 ning
  `GEOCODER_UNAVAILABLE` xato kodi, `01` §18 ning integratsiya qatori va
  `geocoding_failure_alert`), chaqiruvchi kod esa **yo'q**. Ya'ni
  `H -- Нет --> I` yoyi bilan birga «geolokatsiya bermagan
  foydalanuvchi» butun tarmog'i o'lik: bot bunday xabarni umuman qabul
  qilmaydi.
* `N` «Предложить подписку» — **erishiladigan, taklif qilinmaydigan**.
  Obuna menyuda bor (`Action.SUBSCRIPTIONS`), verdiktdan keyin esa
  `on_location` faqat asosiy menyuni va disklameyerni yuboradi. Ya'ni
  `L --> N` va `M --> N` yoylari hech qachon o'tilmaydi, `O` ga esa
  yetib boriladi — diagramma bo'ylab yurgan foydalanuvchi obunani
  **hech qachon ko'rmaydi**, holbuki E13 ning butun mexanizmi tayyor.

Ikkinchisi qimmatroq: birinchisida yo'q narsa qurilmagan, ikkinchisida
**qurilgan narsa ulanmagan** va buni hech narsa ko'rsatmaydi — obuna
oqimining o'z testi bor (`test_bot_subscription_keyboard`) va u yashil,
chunki u tugmani tekshiradi, tugmaning **taklif qilinishini** emas.

## §12 — beshinchi nusxa va bitta yetishmayotgan yoy

§12 ning TO-BE diagrammasi mahsulotning butun zanjirini qayta aytadi va
undagi har bir qadam boshqa joyda allaqachon yozilgan (`01` §11, `05`
§4.4, `06` §4). 92-run buni «takror (beshinchi marta)» deb qayd etgan.

Nusxaning o'zi defekt emas — **son aytilmagani** uni saqlab qoladi:
«Порог независимых источников достигнут?» chegarani nomlamaydi, ya'ni
raqamli drift mumkin emas. Lekin bitta yoy yetishmaydi va u kodda bor:
outbox ikkita mavzu yuboradi (`outage.confirmed`, `outage.resolved`),
§12 esa faqat birinchisini chizadi. «Завершено» statusi shu bilan
paketda **ikkinchi marta** yo'qoladi — §14 ning rang sxemasida ham u
sirtsiz (pastda).

## §13 va §14 — mavjud bo'lmagan hujjatdan meros

§13: «Наследуются UX-01…UX-12 ташкентского пакета».
§14: «Компоненты — наследуются из существующей дизайн-системы продукта».
`UX-S7`: «наследуется A11Y-01…A11Y-10».

Ya'ni yigirma ikkita nomlangan talab va **butun dizayn-tizim** paketda
yo'q manbadan meros qilinadi. Bu 86-run ning `17_OpenAPI.yaml` va
87-run ning `03_Functional_Requirements.md` topilmalari bilan bir xil
shakl, lekin o'lchanadigan qismi kattaroq: `UX-02`…`UX-11`,
`A11Y-01`…`A11Y-05`, `A11Y-07`…`A11Y-10` iboralari sakkizta hujjatning
**birortasida** ham uchramaydi. Diapazonning uchlari (`UX-01`, `UX-12`,
`A11Y-01`, `A11Y-10`) faqat epigrafning o'zida, uch sifatida turadi.

Yigirma ikkitadan **bittasi** istisno: `A11Y-06` — uni §14 nomlaydi
(«цветом **и** формой») va aynan shu bitta talab 96-run da bajarildi.
Ya'ni paket mazmunini aytgan yagona meros talabi bajarildi, qolgan yigirma
bittasi esa bajarilgan-bajarilmagani printsipial aniqlanmaydi.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi va bu qoida 75-rundan beri o'zgarmagan: reyestr
o'lchaydi, tahrirlamaydi. Xususan onboarding (`UX-S5`) yozilmadi, `CTA`
(`UX-S3`) qo'shilmadi, `/language` komandasi (`UX-S1`) qo'shilmadi va
`prefers-color-scheme` (§14 Dark Mode) qo'shilmadi — to'rttasi ham
mahsulot ishi, reyestrning ishi emas. Topilgan yangi savollar
`PROGRESS.md` ning «Ochiq savollar» ida.

Modul `app.*` dan hech narsa import qilmaydi: reyestr sof e'lon, qurilgan
sirtni **test** o'lchaydi (`ast`, DOM, CSS kaskadi va JS chaqiruv grafi
orqali).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Hujjat bo'limlari. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "01 §11–§14"

#: Sarlavhalar — aynan, hujjatdagi tartibda. Test ularni `01` dan parse
#: qiladi va tenglik talab qiladi.
SPEC_SECTIONS: tuple[str, ...] = (
    "11. User Flow",
    "12. Business Process",
    "13. UX Requirements",
    "14. UI Requirements",
)

#: §12 ning diagrammalari — AS-IS va TO-BE, aynan ikkita.
SPEC_PROCESS_DIAGRAMS = 2

#: §13 ning delta qatorlari (`UX-S1`…`UX-S7`).
SPEC_UX_ROWS = 7

#: §14 ning qatorlari — «Аспект» ustuni.
SPEC_UI_ROWS = 6

#: §13 epigrafi meros qiladigan talablar diapazoni — aynan.
INHERITED_UX_RANGE = ("UX-01", "UX-12")

#: `UX-S7` meros qiladigan talablar diapazoni — aynan.
INHERITED_A11Y_RANGE = ("A11Y-01", "A11Y-10")

#: Meros qilingan yigirma ikkitadan paketda **mazmuni aytilgan** yagonasi.
#: §14 ning «Дублирование смысла» qatori uni nomlaydi.
INHERITED_NAMED: tuple[str, ...] = ("A11Y-06",)

#: §14 ning «Компоненты» qatori meros qiladigan manba. Paketda yo'q va
#: fayl nomi ham berilmagan — 86/87-runlarning topilmalaridan **kuchsiz**
#: shakli: u yerda hech bo'lmasa fayl nomi bor edi.
INHERITED_DESIGN_SYSTEM = "существующей дизайн-системы продукта"

#: §14 ning rang sxemasi nomlaydigan statuslar — aynan va tartibda.
SPEC_STATUS_COLORS: tuple[str, ...] = (
    "Ждёт подтверждения",
    "Авария подтверждена",
    "Из официального источника (не подтв.)",
    "Завершено",
)

#: §14 ning «Основные экраны» qatori — aynan va tartibda.
SPEC_SCREENS: tuple[str, ...] = (
    "Карта",
    "Карточка инцидента",
    "Статистика по махалле",
    "Подписки",
    "Онбординг",
    "Настройки языка",
)

#: `UX-S6` ning loyihaviy kengligi, piksel.
DESIGN_WIDTH_PX = 360

#: `web/style.css` dagi mobil tarmoqning chegarasi, piksel. `UX-S6` ni
#: **qoplaydi**, lekin unga teng emas: qator 360 ni nomlaydi, kod esa 640
#: da almashadi. Ikkalasi bog'lanmagan — kimdir chegarani 320 ga
#: tushirsa, `UX-S6` jimgina buziladi.
MOBILE_BREAKPOINT_PX = 640

#: `UX-S7` ning standarti — aynan.
A11Y_STANDARD = "WCAG 2.1 AA"


class Surface(StrEnum):
    """Talab nomlagan narsa bilan repo nima qilgan.

    Besh sinf. «Bor / yo'q» ikkiligi bu bo'limlarda to'rtta turli
    holatni bitta katakka tiqib qo'yardi va ularning narxi bir xil emas:
    qurilmagan narsani yozish kerak, ulanmagan narsani esa **ulash** —
    ikkinchisi arzon va shuning uchun uni alohida ko'rish qimmat.
    """

    #: Talab aytganidek qurilgan.
    REALIZED = "realized"
    #: Talabning bir qismi qurilgan, qolgani yo'q.
    PARTIAL = "partial"
    #: Mexanizm to'liq qurilgan, lekin talab nomlagan **joyda** emas —
    #: unga yetib borish mumkin, u taklif qilinmaydi.
    REACHABLE = "reachable"
    #: Talab nomlagan narsa umuman yo'q.
    ABSENT = "absent"
    #: Qadam mahsulotdan **tashqarida** bajariladi va kod talab
    #: qilmaydi. `ABSENT` dan farqi printsipial: bu yo'qlik emas,
    #: chegara — oqim bu tugundan baribir o'tadi.
    EXTERNAL = "external"
    #: Talabning tashqi manbasi paketda yo'q — bajarilgan-bajarilmagani
    #: **printsipial** aniqlanmaydi. Yo'qlik emas, boshqa savol.
    UNGROUNDED = "ungrounded"


#: Qator «bajarilgan» hisoblanadigan sinflar. Faqat bittasi.
#: `EXTERNAL` bu yerda **yo'q**: §12–§14 ning qatorlari mahsulotga
#: qo'yilgan talab, ya'ni ularni tashqariga chiqarib bo'lmaydi.
SURFACE_KEPT: frozenset[Surface] = frozenset({Surface.REALIZED})

#: §11 ning oqimi **o'tadigan** tugun sinflari. `EXTERNAL` bu yerda
#: **bor** va aynan shu narsa uni `ABSENT` dan ajratadi: mahalla
#: chatidagi havolani odam bosadi, ya'ni oqim to'xtamaydi. `REACHABLE`
#: esa to'xtatadi — mexanizm bor, oqim unga kirmaydi.
NODE_PASSABLE: frozenset[Surface] = frozenset(
    {Surface.REALIZED, Surface.PARTIAL, Surface.EXTERNAL}
)

#: Tugun uchun «farq yozilishi shart emas» sinflari.
NODE_WHOLE: frozenset[Surface] = frozenset({Surface.REALIZED, Surface.EXTERNAL})


class Witness(StrEnum):
    """Repo talabni qanday chuqurlikda ko'radi.

    Bu o'q talabning **rostligini** emas, uni himoyalayotgan
    mexanizmning kuchini o'lchaydi. Sinflar orasida tartib bor:
    `EXERCISED` → `STRUCTURAL` → `TEXTUAL` → `UNWATCHED`.

    ⚠️ `TEXTUAL` ning `UNWATCHED` dan farqi kichik va aynan shu narsa
    94–96-runlarning oltita defektini tushuntiradi: matn regexi fayl
    **o'chirilganini** ushlaydi, ichidagi tuzilma o'zgarganini esa yo'q.
    """

    #: Talabning xulq-atvorini yurgizadigan test bor (Python tomon).
    EXERCISED = "exercised"
    #: Talab **tuzilma** sifatida o'qiladi: DOM, CSS kaskadi yoki JS
    #: chaqiruv grafi.
    STRUCTURAL = "structural"
    #: Faqat matn sifatida: `read_text()` + regex.
    TEXTUAL = "textual"
    #: Repoda hech narsa o'qimaydi.
    UNWATCHED = "unwatched"
    #: Faqat odam ko'zi tasdiqlaydi (3G, kontrast, satr uzunligi).
    HUMAN = "human"


#: Talab haqiqatan himoyalangan sinflar. `TEXTUAL` bu yerda **yo'q**.
WITNESS_LIVE: frozenset[Witness] = frozenset({Witness.EXERCISED, Witness.STRUCTURAL})


class Voice(StrEnum):
    """Talab paketda necha marta va qanday aytilgan.

    §11–§14 ning eng ko'zga ko'rinadigan xossasi — ular boshqa
    bo'limlarni qayta aytadi. Nusxaning o'zi defekt emas; defekt —
    nusxalarning bog'lanmagani.
    """

    #: Paketda bir marta aytilgan.
    SOLE = "sole"
    #: Bir nechta joyda aytilgan, nusxalar hozircha bir xil.
    MIRRORED = "mirrored"
    #: Nusxalar bir-biriga zid — kod bittasini tanlagan.
    CONFLICTED = "conflicted"
    #: Talab paketda yo'q manbaga havola qiladi.
    BORROWED = "borrowed"


#: Nusxalar drift bermaydigan sinflar.
VOICE_SAFE: frozenset[Voice] = frozenset({Voice.SOLE, Voice.MIRRORED})


class NodeKind(StrEnum):
    """§11 tugunining diagrammadagi roli."""

    #: Dunyoda ro'y beradigan hodisa — mahsulotning sirti emas.
    TRIGGER = "trigger"
    #: Shart tuguni (`{...}`).
    DECISION = "decision"
    #: Mahsulot bajaradigan qadam (`[...]`).
    STEP = "step"
    #: Oqimning oxiri.
    TERMINAL = "terminal"


#: Sirt bo'yicha baholanadigan tugun turlari. `TRIGGER` va `TERMINAL`
#: baholanmaydi: birinchisi dunyo, ikkinchisi belgi.
JUDGED_KINDS: frozenset[NodeKind] = frozenset({NodeKind.DECISION, NodeKind.STEP})


class UxRequirementsError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class FlowNode:
    """§11 diagrammasining bitta tuguni."""

    #: Mermaid dagi harf (`A`…`O`).
    key: str
    #: Yorliq — aynan, tarjimasiz.
    label: str
    kind: NodeKind
    surface: Surface
    witness: Witness
    note: str
    #: Dalil: `modul:simvol`, `web/fayl:selektor` yoki `tests/fayl.py`.
    binds: tuple[str, ...] = ()
    gap: str = ""


@dataclass(frozen=True)
class Clause:
    """§12, §13 yoki §14 ning bitta qatori."""

    code: str
    #: Qaysi bo'limning qatori (`SPEC_SECTIONS` dagi element).
    section: str
    #: Sarlavha yoki «Аспект» katagi — aynan.
    title: str
    surface: Surface
    witness: Witness
    voice: Voice
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""
    #: Talab yana qayerda aytilgan — `Voice` ning dalili.
    copies: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# §11 — graf. Yoylar hujjatdagi mermaid blokidan parse qilinadi va shu
# ro'yxatga tenglashtiriladi (`SPEC_SECTIONS` bilan bir xil qoida).
# --------------------------------------------------------------------------

#: (dan, ga) — o'n sakkizta yoy, hujjatdagi tartibda. Yorliqlar
#: (`Нет`, `Да`, `uz по умолчанию`, `смена`) bu yerda saqlanmaydi:
#: reyestr yo'lni hisoblaydi, matnni test solishtiradi.
FLOW_EDGES: tuple[tuple[str, str], ...] = (
    ("A", "B"),
    ("B", "C"),
    ("C", "D"),
    ("B", "D"),
    ("D", "E"),
    ("E", "F"),
    ("E", "F"),
    ("F", "G"),
    ("G", "H"),
    ("H", "I"),
    ("H", "J"),
    ("I", "J"),
    ("J", "K"),
    ("K", "L"),
    ("K", "M"),
    ("L", "N"),
    ("M", "N"),
    ("N", "O"),
)

FLOW_NODES: tuple[FlowNode, ...] = (
    FlowNode(
        key="A",
        label="Свет погас",
        kind=NodeKind.TRIGGER,
        surface=Surface.REALIZED,
        witness=Witness.HUMAN,
        note=(
            "Dunyoda ro'y beradigan hodisa. Mahsulotning sirti emas va "
            "shuning uchun baholanmaydi (`JUDGED_KINDS`)."
        ),
    ),
    FlowNode(
        key="B",
        label="Знает о боте?",
        kind=NodeKind.DECISION,
        surface=Surface.EXTERNAL,
        witness=Witness.HUMAN,
        note=(
            "Shart mahsulotdan **tashqarida** hal qilinadi: bot "
            "foydalanuvchining o'zi haqida bilishini bila olmaydi. "
            "Diagrammaning yagona tuguni bo'lib, u printsipial "
            "qurilmaydi — va shuning uchun uning `C` tarmog'i ham "
            "(`odam ishi`) hech qanday kod talab qilmaydi."
        ),
        gap=(
            "Tugun mahsulot oqimida turadi, lekin mahsulot uni hal "
            "qilmaydi. §11 buni ajratmaydi."
        ),
    ),
    FlowNode(
        key="C",
        label="Ссылка в чате махалли",
        kind=NodeKind.STEP,
        surface=Surface.EXTERNAL,
        witness=Witness.HUMAN,
        note=(
            "Tarqatish kanali — E10 ning (yopiq yig'ish bosqichi) ishi. "
            "Kodda hech qanday vakili yo'q va bo'lishi ham shart emas; "
            "lekin `01` §24 ning Faza 0 vazifalari orasida ham bu qadam "
            "nomlanmagan, ya'ni oqimning boshi hech kimning "
            "javobgarligida emas."
        ),
        gap="Tarqatish kanali birorta reja bandiga bog'lanmagan.",
    ),
    FlowNode(
        key="D",
        label="/start/",
        kind=NodeKind.STEP,
        surface=Surface.REALIZED,
        witness=Witness.EXERCISED,
        note=(
            "`cmd_start` `CommandStart()` ga ulangan, foydalanuvchi "
            "yaratiladi, til hal qilinadi va asosiy menyu yuboriladi."
        ),
        binds=(
            "app.bot.handlers:cmd_start",
            "app.bot.service:register_user",
            "tests/test_bot_flow_db.py",
        ),
    ),
    FlowNode(
        key="E",
        label="Язык определён?",
        kind=NodeKind.DECISION,
        surface=Surface.REALIZED,
        witness=Witness.EXERCISED,
        note=(
            "`pick_language` uch bosqichli: mijoz tegi → mintaqaning "
            "standarti → global standart. Shart qurilgan; uning "
            "**natijasi** esa `F` da diagrammadan ajraladi (pastda)."
        ),
        binds=(
            "app.core.i18n:pick_language",
            "tests/test_i18n_negotiation.py",
            "tests/test_language_contract.py",
        ),
    ),
    FlowNode(
        key="F",
        label="Главное меню на узбекском",
        kind=NodeKind.STEP,
        surface=Surface.PARTIAL,
        witness=Witness.EXERCISED,
        note=(
            "Menyu qurilgan, «на узбекском» esa kafolatlanmagan: "
            "`pick_language` da mijoz tegi mintaqaning standartidan "
            "**ustun**, ya'ni `language_code='ru'` bo'lgan samarqandlik "
            "birinchi ekranni ruscha oladi. Diagramma buning teskarisini "
            "aytadi (`E -- uz по умолчанию --> F`)."
        ),
        binds=(
            "app.bot.keyboards:main_menu",
            "app.core.i18n:pick_language",
            "app.core.i18n:DEFAULT_LANGUAGE",
        ),
        gap=(
            "Diagrammaning `uz по умолчанию` yorlig'i faqat tegi "
            "**noma'lum** foydalanuvchi uchun rost. `01` §9 `US-S1` va "
            "§13 `UX-S1` bir xil da'voni takrorlaydi — uchala nusxa ham "
            "bir xil tarzda noto'g'ri."
        ),
    ),
    FlowNode(
        key="G",
        label="Сообщить об отключении",
        kind=NodeKind.STEP,
        surface=Surface.REALIZED,
        witness=Witness.EXERCISED,
        note=(
            "`Action.OUTAGE` tugmasi oqimni boshlaydi va holatga "
            "`FLOW_REPORT` yozadi — xabar faqat shundan keyin yaratiladi "
            "(E7 ning qarori)."
        ),
        binds=(
            "app.bot.handlers:on_report_button",
            "app.bot.keyboards:Action",
            "tests/test_bot_location_routing.py",
        ),
    ),
    FlowNode(
        key="H",
        label="Геолокация передана?",
        kind=NodeKind.DECISION,
        surface=Surface.PARTIAL,
        witness=Witness.EXERCISED,
        note=(
            "`F.location` filtri «Да» tarmog'ini beradi. «Нет» tarmog'i "
            "esa `fallback` ga tushadi va u manzil so'ramaydi — ya'ni "
            "shart ikkiga bo'linadi, lekin ikkinchi tarmoq diagramma "
            "ko'rsatgan joyga bormaydi."
        ),
        binds=("app.bot.handlers:on_location", "app.bot.handlers:fallback"),
        gap="«Нет» tarmog'i `I` ga emas, `fallback` ga boradi.",
    ),
    FlowNode(
        key="I",
        label="Ввод адреса",
        kind=NodeKind.STEP,
        surface=Surface.ABSENT,
        witness=Witness.UNWATCHED,
        note=(
            "Geokoder paketda **uch joyda** bor va kodda chaqiruvchisi "
            "yo'q: `GEOCODER_PROVIDER`/`GEOCODER_API_KEY` "
            "(`Settings` + `.env.example`), `01` §16 ning "
            "`GEOCODER_UNAVAILABLE` xato kodi, `01` §18 ning "
            "integratsiya qatori va `geocoding_failure_alert`. Ya'ni "
            "sozlama ham, xato kodi ham, alert ham **hech qachon "
            "ishlamaydigan** yo'l uchun mavjud. 94-run buni "
            "«`app/geo/` da birorta ham chaqiruv joyi yo'q» deb "
            "o'lchagan."
        ),
        binds=(
            "app.core.config:Settings.geocoder_provider",
            "app.core.config:Settings.geocoder_api_key",
            "app.obs.monitoring:REQUIREMENT_BY_CODE",
        ),
        gap=(
            "Tugun sirtsiz, ya'ni `H -- Нет --> I --> J` tarmog'i "
            "butunlay o'lik. `01` §16/§18 esa uni mavjud deb yozadi."
        ),
    ),
    FlowNode(
        key="J",
        label="Привязка: район / махалля / H3",
        kind=NodeKind.STEP,
        surface=Surface.PARTIAL,
        witness=Witness.EXERCISED,
        note=(
            "Uchala biriktirishning ikkitasi ishlaydi: tuman "
            "(`districts.geom`) va H3 (`h3_r9`). Mahalla — jadval bor, "
            "poligonlar **yo'q** va ularni yuklaydigan yo'l butun "
            "daraxtda yo'q (82/85/87-runlar uch tomondan o'lchagan). "
            "Ya'ni tugunning uchdan biri ma'lumot kutmoqda, kod emas."
        ),
        binds=(
            "app.geo.pipeline:resolve",
            "app.geo.pipeline:find_mahalla_id",
            "app.geo.h3_cells:cell_of",
            "tests/test_geo_pipeline_db.py",
        ),
        gap="`mahallas` bo'sh — 👤 poligonlar (E17).",
    ),
    FlowNode(
        key="K",
        label="Есть независимые репорты рядом?",
        kind=NodeKind.DECISION,
        surface=Surface.REALIZED,
        witness=Witness.EXERCISED,
        note=(
            "`06` §4 ning butun tasdiqlash mexanizmi. Shartning o'zi "
            "diagrammada sonsiz turadi, ya'ni bu yerda drift mumkin emas."
        ),
        binds=(
            "app.clustering.confirmation:evaluate",
            "app.clustering.independence:count_independent",
            "tests/test_confirmation.py",
        ),
    ),
    FlowNode(
        key="L",
        label="Вердикт: массовое отключение",
        kind=NodeKind.STEP,
        surface=Surface.REALIZED,
        witness=Witness.EXERCISED,
        note=(
            "`render()` verdiktni matnga aylantiradi va matn katalogdan "
            "keladi (`05` §6.2)."
        ),
        binds=("app.bot.reply:render", "tests/test_bot_reply.py"),
    ),
    FlowNode(
        key="M",
        label="Вердикт: данных недостаточно",
        kind=NodeKind.STEP,
        surface=Surface.REALIZED,
        witness=Witness.EXERCISED,
        note=(
            "E7 ning butun mazmuni. ⚠️ `05` §6.2 ning "
            "`NO_OUTAGE_COVERED` verdikti esa `UX-S2` ga zid va bu "
            "ziddiyat shu tugunda emas, `UX-S2` qatorida qayd etilgan."
        ),
        binds=("app.clustering.lookup", "app.bot.reply:render", "tests/test_clustering_lookup.py"),
    ),
    FlowNode(
        key="N",
        label="Предложить подписку",
        kind=NodeKind.STEP,
        surface=Surface.REACHABLE,
        witness=Witness.UNWATCHED,
        note=(
            "Obunaning butun mexanizmi tayyor: menyu tugmasi, "
            "`_add_subscription`, radius, outbox, yetkazish. Lekin "
            "**taklif** yo'q: verdiktdan keyin `on_location` faqat "
            "`main_menu` va `app.disclaimer` ni yuboradi. Ya'ni "
            "`L --> N` va `M --> N` yoylari hech qachon o'tilmaydi, "
            "`O` ga esa yetib boriladi.\n\n"
            "Bu `I` dan **boshqa** sinf va qimmatroq: u yerda yo'q "
            "narsa qurilmagan, bu yerda qurilgan narsa ulanmagan. "
            "Va uni hech narsa ko'rsatmaydi — "
            "`test_bot_subscription_keyboard` yashil, chunki u tugmani "
            "tekshiradi, tugmaning **taklif qilinishini** emas."
        ),
        binds=(
            "app.bot.handlers:on_location",
            "app.bot.handlers:_add_subscription",
            "app.bot.keyboards:subscriptions_menu",
            "tests/test_bot_subscription_keyboard.py",
        ),
        gap=(
            "Qurilgan mexanizm oqimga ulanmagan; `01` §11 uni oqimning "
            "majburiy qadami deb chizadi."
        ),
    ),
    FlowNode(
        key="O",
        label="Конец",
        kind=NodeKind.TERMINAL,
        surface=Surface.REALIZED,
        witness=Witness.EXERCISED,
        note=(
            "`state.clear()` — oqim yopiladi. ⚠️ Unga `N` dan "
            "**o'tmasdan** yetib boriladi, ya'ni oqim tugaydi va "
            "diagrammaning oxirgi qadami bajarilmaydi."
        ),
        binds=("app.bot.handlers:on_location",),
    ),
)


# --------------------------------------------------------------------------
# §12, §13, §14
# --------------------------------------------------------------------------

CLAUSES: tuple[Clause, ...] = (
    # ---------------- §12 ----------------
    Clause(
        code="BP-1",
        section="12. Business Process",
        title="AS-IS — Самарканд до запуска",
        surface=Surface.ABSENT,
        witness=Witness.HUMAN,
        voice=Voice.SOLE,
        note=(
            "Diagramma dunyoni tasvirlaydi: qo'shnidan so'rash, mahalla "
            "chati, 1055 ga qo'ng'iroq. Mahsulotda vakili bo'lishi shart "
            "emas va yo'q. Qiymati boshqa joyda: `02` ning Faza 0 "
            "validatsiyasi aynan shu holatni o'lchashi kerak va §12 "
            "unga bog'lanmagan."
        ),
        gap=(
            "AS-IS ning birorta bandi `02` ning validatsiya rejasida "
            "o'lchov sifatida nomlanmagan."
        ),
    ),
    Clause(
        code="BP-2",
        section="12. Business Process",
        title="TO-BE — репорт → кластеризация → подтверждение → уведомление",
        surface=Surface.REALIZED,
        witness=Witness.EXERCISED,
        voice=Voice.MIRRORED,
        note=(
            "Zanjirning har bir qadami qurilgan va **beshinchi marta** "
            "aytilgan (92-run sanagan): `01` §11, `05` §4.4, `06` §4 va "
            "`01` §19 uni allaqachon yozadi. Nusxa xavfsiz qoladi, "
            "chunki §12 sonni nomlamaydi — «Порог независимых "
            "источников достигнут?» chegarasiz shart, ya'ni raqamli "
            "drift mumkin emas.\n\n"
            "Ikkinchi jihat to'g'ri bajarilgan: bildirishnoma faqat "
            "`Инцидент подтверждён` dan chiqadi, `Ожидает "
            "подтверждения` esa faqat xaritaga boradi — kod aynan "
            "shunday (`OUTBOX_TOPICS`, `prepare`)."
        ),
        binds=(
            "app.clustering.confirmation:evaluate",
            "app.notifications.models:OUTBOX_TOPICS",
            "app.notifications.service:prepare",
            "app.clustering.snapshot",
            "tests/test_notifications_db.py",
        ),
        copies=("01 §11", "05 §4.4", "06 §4", "01 §19"),
        gap=(
            "Diagrammada `outage.resolved` yo'qi: outbox ikkita mavzu "
            "yuboradi, TO-BE faqat bittasini chizadi. «Завершено» "
            "statusi shu bilan paketda ikkinchi marta yo'qoladi "
            "(§14 ning rang sxemasi — `UI-3`)."
        ),
    ),
    # ---------------- §13 ----------------
    Clause(
        code="UX-S1",
        section="13. UX Requirements",
        title="Первый экран на узбекском; смена языка — одно действие с любого экрана",
        surface=Surface.PARTIAL,
        witness=Witness.EXERCISED,
        voice=Voice.CONFLICTED,
        note=(
            "Ikkala yarmi ham bajarilmagan, sabablari esa boshqa-boshqa.\n\n"
            "**Birinchi yarim:** `pick_language` da mijoz tegi mintaqaning "
            "standartidan ustun, ya'ni birinchi ekran tegi noma'lum "
            "bo'lganlar uchun o'zbekcha. Bu qaror to'g'ri bo'lishi mumkin "
            "(foydalanuvchi o'z tilini biladi), lekin u §13 ning matniga "
            "**zid** va uchala nusxa (`01` §9 `US-S1`, `01` §11 `E→F`, "
            "shu qator) bir xil tarzda noto'g'ri.\n\n"
            "**Ikkinchi yarim:** til almashtirish — **ikki** qadam "
            "(menyu tugmasi → inline tanlov), «одно действие» emas, va "
            "«с любого экрана» ham bajarilmaydi: `/language` komandasi "
            "yo'q, ya'ni oqimning o'rtasida (masalan geolokatsiya "
            "kutilayotganda) tilni almashtirish uchun oqimdan chiqish "
            "kerak. `BOT_COMMANDS` ikkitadan iborat: `/start`, `/help`."
        ),
        binds=(
            "app.core.i18n:pick_language",
            "app.bot.handlers:on_language_button",
            "app.bot.keyboards:language_choice",
            "tests/test_language_contract.py",
        ),
        copies=("01 §9 US-S1", "01 §11 E→F"),
        gap=(
            "Ikki qadam «одно действие» emas; `/language` yo'q; birinchi "
            "ekran mijoz tegiga bog'liq."
        ),
    ),
    Clause(
        code="UX-S2",
        section="13. UX Requirements",
        title="Вердикт «данных недостаточно», никогда «аварии нет»",
        surface=Surface.PARTIAL,
        witness=Witness.EXERCISED,
        voice=Voice.CONFLICTED,
        note=(
            "92-run ning asosiy topilmasi: bu — `C-5` taqiqining "
            "**uchinchi** nusxasi (`01` §9 `US-S2`, shu qator, `05` "
            "§6.2) va uchinchisi eng qat'iy yozilgan («**никогда**»). "
            "Kod esa `05` §6.2 ni bajaradi va u yerda "
            "`NO_OUTAGE_COVERED` verdikti bor — ya'ni qamralgan hududda "
            "mahsulot aynan «avariya yo'q» deydi.\n\n"
            "Ziddiyat mahsulot xatosi emas: qamrov yetarli bo'lganda "
            "«ma'lumot yetarli emas» deyish ham yolg'on bo'lardi. "
            "Tuzatiladigan joy — hujjat, va u **uchta**: qaror birdan "
            "`01` §9, `01` §13 va `05` §6.2 ga qo'llanadi."
        ),
        binds=(
            "app.clustering.lookup",
            "app.bot.reply:render",
            "tests/test_clustering_lookup.py",
        ),
        copies=("01 §9 US-S2", "05 §6.2"),
        gap=(
            "`NO_OUTAGE_COVERED` qatorning «никогда» sini buzadi. "
            "👤 Uch hujjatga birdan tegadigan qaror."
        ),
    ),
    Clause(
        code="UX-S3",
        section="13. UX Requirements",
        title="Зум уровня города; при пустой карте — объяснение и CTA",
        surface=Surface.PARTIAL,
        witness=Witness.STRUCTURAL,
        voice=Voice.SOLE,
        note=(
            "Ikkita shartdan ikkitasi bajarilgan, uchinchisi yo'q. "
            "Zum serverdan keladi (`/map/config` ning `zoom` i, "
            "mintaqaning ustuni) — ya'ni shahar darajasi sozlanadi va "
            "sahifaga qattiq yozilmagan. Bo'sh xarita tushuntirishi "
            "bannerda (`map.empty`) va 95-rundan beri uni boshqa manba "
            "**o'chira olmaydi** (`notices` uyalari).\n\n"
            "**CTA yo'q.** Banner — matn, unda havola ham, tugma ham "
            "yo'q; bo'sh xaritani ko'rgan foydalanuvchiga «botga o'ting "
            "va xabar bering» degan yo'l ko'rsatilmaydi. Bu qatorning "
            "yagona bajarilmagan qismi va u eng arzon tuzatiladigani."
        ),
        binds=(
            "web/app.js:refresh",
            "web/app.js:banner",
            "web/index.html:#banner",
            "app.api.v1.map:get_map_config",
        ),
        gap="Bo'sh xaritada CTA yo'q — banner faqat matn.",
    ),
    Clause(
        code="UX-S4",
        section="13. UX Requirements",
        title="Индекс покрытия махалли рядом с любой цифрой статистики",
        surface=Surface.PARTIAL,
        witness=Witness.STRUCTURAL,
        voice=Voice.MIRRORED,
        note=(
            "Qurilgan qism kuchli: zichlik qatlamining legendasi "
            "indeksni ko'rsatadi (`#heat-coverage`), matn serverdan "
            "kelgan i18n kaliti bo'yicha to'ldiriladi va kalit "
            "kelmasa qator **umuman ko'rsatilmaydi** — «qamrov "
            "noma'lum» degan bo'sh yorliq indeksni bor deb ko'rsatgan "
            "yolg'on bo'lardi.\n\n"
            "Bajarilmagani — «любой»: `GET /stats.csv` ustunlarida va "
            "botning javoblarida indeks yo'q, `01` §23 esa uni qabul "
            "mezoni qiladi. 94-run 360 px da butun legendaning "
            "yashirilishini aynan shu qator buzilishi sifatida topgan."
        ),
        binds=(
            "web/app.js:showCoverage",
            "web/index.html:#heat-coverage",
            "app.stats.coverage",
            "tests/test_stats_coverage.py",
        ),
        copies=("03 §R1.2", "01 §23", "01 PG-S4"),
        gap="CSV eksporti va bot javoblari indekssiz.",
    ),
    Clause(
        code="UX-S5",
        section="13. UX Requirements",
        title="Онбординг из 3 экранов: что делает продукт, зачем геолокация, что такое подписка",
        surface=Surface.ABSENT,
        witness=Witness.UNWATCHED,
        voice=Voice.SOLE,
        note=(
            "Butun daraxtda `onboarding` so'zi ham, uchta ekranning "
            "birortasi ham yo'q — na botda, na `web/` da, na i18n "
            "katalogida. Eng yaqin narsa `cmd_help` va `app.disclaimer`, "
            "lekin ular «uchta ekran» emas: `/help` — bitta matn, "
            "disklameyer esa har javobdan keyin qo'shiladi.\n\n"
            "⚠️ Ikkinchi oqibat: qator geolokatsiyaning **sababini** "
            "tushuntirishni talab qiladi va `01` §20 ning ПДн qarori "
            "aynan shunga tayanadi — ya'ni onboardingning yo'qligi "
            "maxfiylik va'dasining ham yetkazilmaganini bildiradi."
        ),
        binds=("app.bot.handlers:cmd_help",),
        gap=(
            "Uchta ekrandan bittasi ham yo'q; geolokatsiyaning sababi "
            "hech qayerda tushuntirilmaydi."
        ),
    ),
    Clause(
        code="UX-S6",
        section="13. UX Requirements",
        title="Проектная ширина 360 px; работоспособность на 3G обязательна",
        surface=Surface.PARTIAL,
        witness=Witness.STRUCTURAL,
        voice=Voice.SOLE,
        note=(
            "**360 px:** 94-run bu yerda haqiqiy defekt topdi va "
            "tuzatdi — `@media` butun `.legend` ni yashirar, "
            "`#heat-legend` esa uning **ichida** turardi, ya'ni "
            "loyihaviy kenglikda zichlik qatlami indekssiz, pometasiz "
            "va disklameyersiz chizilardi. Endi faqat statik status "
            "legendasi yashiriladi.\n\n"
            "⚠️ Lekin son bog'lanmagan: qator `360` ni nomlaydi, CSS "
            "esa `640` da almashadi (`MOBILE_BREAKPOINT_PX`). Chegara "
            "qoplaydi, ammo kimdir uni 320 ga tushirsa `UX-S6` jimgina "
            "buziladi.\n\n"
            "**3G:** bajarilmagan va bu tuzilmadan ko'rinadi — sahifa "
            "MapLibre ni `unpkg.com` dan oladi (CSS + JS, ikkita tashqi "
            "so'rov, lokal nusxa yo'q, `preconnect` yo'q). CDN "
            "yetib bo'lmasa `maplibregl` aniqlanmaydi va `boot()` ning "
            "`catch` i bannerga neytral `…` yozadi — foydalanuvchi "
            "sababsiz bo'sh sahifani ko'radi."
        ),
        binds=(
            "web/style.css:@media",
            "web/index.html:maplibre-gl.css",
            "web/index.html:maplibre-gl.js",
            "web/app.js:boot",
        ),
        gap=(
            "`360` va `640` bog'lanmagan; MapLibre tashqi CDN dan "
            "keladi, lokal zaxira yo'q."
        ),
    ),
    Clause(
        code="UX-S7",
        section="13. UX Requirements",
        title="Accessibility — WCAG 2.1 AA, наследуется A11Y-01…A11Y-10",
        surface=Surface.UNGROUNDED,
        witness=Witness.HUMAN,
        voice=Voice.BORROWED,
        note=(
            "O'nta talabdan **bittasi** paketda mazmuni bilan aytilgan: "
            "`A11Y-06` (§14 ning «Дублирование смысла» qatori) va u "
            "96-run da bajarildi. Qolgan to'qqiztasining "
            "(`A11Y-02`…`A11Y-05`, `A11Y-07`…`A11Y-10`) nomi ham "
            "sakkizta hujjatning birortasida uchramaydi; "
            "`A11Y-01` va `A11Y-10` esa faqat diapazonning uchi sifatida "
            "turadi. Ya'ni «WCAG 2.1 AA meros qilinadi» degan gap "
            "tekshirilishi mumkin bo'lgan hech narsani bermaydi.\n\n"
            "Bu 86-run ning `17_OpenAPI.yaml` va 87-run ning "
            "`03_Functional_Requirements.md` topilmalari bilan bir xil "
            "shakl. `UNGROUNDED` aynan shu holat uchun kiritildi: "
            "qatorni «bajarilmagan» deb belgilash yolg'on bo'lardi — "
            "nima bajarilishi kerakligi noma'lum."
        ),
        binds=("web/app.js:addLayers", "web/style.css:.dot"),
        copies=("01 §14 A11Y-06",),
        gap=(
            "Yigirma ikkita meros talabdan yigirma bittasi paketda "
            "ta'riflanmagan. 👤 Manba hujjat qo'shiladimi yoki talablar "
            "ko'chiriladimi."
        ),
    ),
    # ---------------- §14 ----------------
    Clause(
        code="UI-1",
        section="14. UI Requirements",
        title="Основные экраны — шесть",
        surface=Surface.PARTIAL,
        witness=Witness.STRUCTURAL,
        voice=Voice.MIRRORED,
        note=(
            "Oltitadan **to'rttasi** bor: «Карта» (`web/index.html`), "
            "«Карточка инцидента» (xaritadagi popup — ekran emas, "
            "lekin mazmuni bor), «Подписки» (`subscriptions_menu`), "
            "«Настройки языка» (`language_choice`).\n\n"
            "Yo'qlari: «Статистика по махалле» — API va CSV bor, "
            "**sahifa yo'q** (E14-a, vitrina); «Онбординг» — umuman "
            "yo'q (`UX-S5`).\n\n"
            "⚠️ Ikkitasi botda, ikkitasi vebda va §14 buni ajratmaydi: "
            "«ekran» so'zi ikki xil platformani bitta ro'yxatga "
            "qo'shadi, ya'ni «oltita ekran» qaysi mijozda "
            "sanalishi noma'lum."
        ),
        binds=(
            "web/index.html:#map",
            "web/app.js:addLayers",
            "app.bot.keyboards:subscriptions_menu",
            "app.bot.keyboards:language_choice",
            "app.stats.export",
        ),
        copies=("01 §13 UX-S5", "01 §9 US-S5"),
        gap="Statistika sahifasi va onboarding yo'q; platforma ajratilmagan.",
    ),
    Clause(
        code="UI-2",
        section="14. UI Requirements",
        title="Компоненты — наследуются из существующей дизайн-системы продукта",
        surface=Surface.UNGROUNDED,
        witness=Witness.UNWATCHED,
        voice=Voice.BORROWED,
        note=(
            "Manba nomlanmagan ham: `UX-S7` da hech bo'lmasa "
            "identifikatorlar diapazoni bor, bu yerda esa faqat "
            "«существующая дизайн-система». Repoda dizayn-tizim yo'q: "
            "`web/style.css` — 173 qatorlik mustaqil uslub, o'zining "
            "to'rtta CSS o'zgaruvchisi bilan; botda esa umuman "
            "komponent tushunchasi yo'q (matn + klaviatura).\n\n"
            "Ya'ni qator bajarilgan ham, buzilgan ham emas: u hech "
            "narsani aytmaydi. `UNGROUNDED` sinfining eng toza namunasi."
        ),
        binds=("web/style.css:root",),
        gap="Meros manbasi nomlanmagan — 👤 qator olib tashlanadimi.",
    ),
    Clause(
        code="UI-3",
        section="14. UI Requirements",
        title="Цветовая схема статусов — те же четыре статуса, что в Ташкенте",
        surface=Surface.PARTIAL,
        witness=Witness.STRUCTURAL,
        voice=Voice.CONFLICTED,
        note=(
            "To'rttadan **uchtasi** sirtda: `confirmed` (`#e2483d`), "
            "`pending` (`#e8a33d`) va `official` (`#3d6fe2`) — "
            "`web/app.js` ning `STATUS_COLOR` ifodasida va "
            "`web/style.css` ning `.dot` belgilarida.\n\n"
            "**«Завершено» sirtsiz va bu tasodif emas:** snapshot "
            "faqat `OPEN_STATUSES` ni oladi (`pending`, `confirmed`), "
            "ya'ni `resolved` hodisa xaritaga **printsipial** "
            "tushmaydi; `map.legend.resolved` degan i18n kaliti ham "
            "yo'q. Kod bu yerda to'g'ri ishlagan bo'lishi mumkin "
            "(tugagan uzilishni xaritada ko'rsatish chalg'itardi), "
            "lekin §14 to'rtta status va'da qiladi va nusxalar "
            "ziddiyatda: `05` §4.4 `resolved` ni yakuniy status deb "
            "yozadi, `01` §19 esa unga bildirishnoma yuboradi — ya'ni "
            "«Завершено» mahsulotda **bor**, faqat xaritada yo'q.\n\n"
            "⚠️ Uchinchi nozik joy: `official` — status emas, "
            "**qatlam** (`layer`), ya'ni to'rtlikning bir a'zosi boshqa "
            "o'qdan olingan. `outage-halo` qatlami buni bilmaydi: iz "
            "faqat `status` ga qaraydi, shuning uchun rasmiy e'lon ko'k "
            "nuqta + **sariq** iz bo'lib chiqadi (96-run ning ochiq "
            "savoli)."
        ),
        binds=(
            "web/app.js:addLayers",
            "web/style.css:.dot",
            "app.clustering.models:OPEN_STATUSES",
            "app.clustering.status:TERMINAL_STATUSES",
        ),
        copies=("05 §4.4", "01 §19"),
        gap=(
            "«Завершено» na xaritada, na legendada, na katalogda; "
            "`official` status o'qidan emas, qatlam o'qidan."
        ),
    ),
    Clause(
        code="UI-4",
        section="14. UI Requirements",
        title="Дублирование смысла — цвет и форма (пунктир / заливка / иконка), A11Y-06",
        surface=Surface.REALIZED,
        witness=Witness.STRUCTURAL,
        voice=Voice.SOLE,
        note=(
            "96-run da bajarildi va u paketning meros qilgan yigirma "
            "ikkita talabidan **yagona mazmuni aytilgani**. Xavf "
            "haqiqiy edi: `#e2483d` va `#e8a33d` deyteranopiyada "
            "deyarli farqsiz, ilgari esa uchala status bir xil doira "
            "edi.\n\n"
            "Uchlik **sprite siz** qurilgan va bu majburiy: ADR-08 "
            "ochiq, ya'ni `baseStyle()` bo'sh style qaytarishi mumkin "
            "va unda na ikonka atlasi, na glif serveri bor. "
            "To'ldirilgan doira — `заливка`; ichi bo'sh halqa — "
            "`пунктир` ning muqobili (MapLibre ning `circle` konturi "
            "punktir bo'la olmaydi); halqa + markaz — `иконка` "
            "(`outage-official-core`). Rang ikkala shaklda ham qoladi, "
            "faqat boshqa xossada, aks holda «rang **va** shakl» "
            "jimgina «faqat shakl» ga aylanardi. Legenda belgilari "
            "(`.dot`) xaritadagi uchlik bilan bir xil — foydalanuvchi "
            "xaritani aynan legendaga qarab o'qiydi."
        ),
        binds=(
            "web/app.js:addLayers",
            "web/style.css:.dot.confirmed",
            "web/style.css:.dot.pending",
            "web/style.css:.dot.official",
        ),
    ),
    Clause(
        code="UI-5",
        section="14. UI Requirements",
        title="Dark Mode — отдельный токен-набор, авто-переключение по prefers-color-scheme",
        surface=Surface.PARTIAL,
        witness=Witness.STRUCTURAL,
        voice=Voice.SOLE,
        note=(
            "Sahifa **doim** to'q: `--bg: #12151a`, `--text: #e9edf2` "
            "`:root` da qo'yilgan va `prefers-color-scheme` butun "
            "`web/` da bir marta ham uchramaydi. Ya'ni «авто-"
            "переключение» yo'q va yorug' tema umuman yo'q — qator "
            "ikkita talab qo'yadi, kod nolinchisini bajaradi.\n\n"
            "«Отдельный токен-набор» esa yarim: to'rtta o'zgaruvchi "
            "(`--bg`, `--panel`, `--text`, `--muted`) va uchta status "
            "rangi bor, lekin ular bitta to'plam — ikkinchisi uchun "
            "joy ochilmagan. ⚠️ Xarita ranglari bundan **tashqarida**: "
            "`HEAT_COLORS` va `STATUS_COLOR` `web/app.js` da, ya'ni "
            "tema almashtirilsa ular o'zgarmaydi va uchta rang ikki "
            "joyda takrorlanadi (`style.css` ↔ `app.js`)."
        ),
        binds=("web/style.css:root", "web/app.js:HEAT_COLORS"),
        gap=(
            "`prefers-color-scheme` yo'q; xarita ranglari token "
            "to'plamidan tashqarida va ikki faylda takrorlanadi."
        ),
    ),
    Clause(
        code="UI-6",
        section="14. UI Requirements",
        title="Типографика — узбекская латиница; проверка длины строк [ГИПОТЕЗА]",
        surface=Surface.PARTIAL,
        witness=Witness.HUMAN,
        voice=Voice.SOLE,
        note=(
            "Birinchi yarim bajarilgan va u sirtda ko'rinadi: "
            "`DEFAULT_LANGUAGE = 'uz'`, katalogning o'zbek qismi "
            "lotin yozuvida, `html lang` esa tanlangan tildan "
            "qo'yiladi (`applyStrings`).\n\n"
            "Ikkinchi yarim — `[ГИПОТЕЗА]` va u **tekshirilmagan**: "
            "«maketlar buzilmasligi» ni birorta test o'lchamaydi va "
            "o'lchashi ham qiyin (u renderga tayanadi). Qator "
            "«проверяется на реальных строках» deydi, haqiqiy satrlar "
            "esa katalogda bor — ya'ni tekshirish **mumkin**: eng "
            "uzun o'zbek satri eng uzun rus satridan qancha uzun, va "
            "u 360 px da qaysi elementga sig'maydi. Bugun bunday "
            "o'lchov yo'q.\n\n"
            "✅ 98-run ning yo'l-yo'lakay topilmasi **tuzatildi** "
            "(117-run): `web/index.html` dagi `aria-label=\"uz / ru\"` "
            "— sahifadagi oxirgi qattiq kodlangan foydalanuvchi matni "
            "(`04` §6 uni bloklovchi defekt deb ataydi) — olib "
            "tashlandi. Endi ikkala tanlagichning nomi ham katalogdan "
            "keladi (`map.language`, `map.region`) va ikkalasi ham "
            "`applyStrings` da qo'yiladi, ya'ni til almashganda "
            "yangilanadi. `#region` niki ilgari `fillRegions` da edi "
            "— u bir marta ishlaydi, ya'ni nom eski tilda qolardi "
            "(`tiles` uyasining 95-rundagi sinfi).\n\n"
            "⚠️ Shu sinfning qolgan yarmi: mintaqa **nomlari** "
            "serverda tarjima qilinadi (`_summary(r, lang)`) va "
            "`/map/config` faqat `boot()` da so'raladi — til "
            "almashganda `<option>` matnlari eski tilda qoladi. "
            "Bugun ko'rinmaydi (mintaqa bitta, tanlagich yashirin), "
            "shuning uchun o'lchandi, tuzatilmadi — 👤 savol."
        ),
        binds=(
            "app.core.i18n:DEFAULT_LANGUAGE",
            "web/app.js:applyStrings",
            "web/index.html:#lang",
        ),
        gap=(
            "Satr uzunligi gipotezasi o'lchanmaydi; mintaqa nomlari "
            "til almashganda eski tilda qoladi (`/map/config` qayta "
            "so'ralmaydi)."
        ),
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class UxRequirementsReport:
    """§11–§14 ning bugungi holati."""

    nodes: tuple[FlowNode, ...]
    clauses: tuple[Clause, ...]
    edges: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        keys = [n.key for n in self.nodes]
        if len(set(keys)) != len(keys):
            raise UxRequirementsError("tugun kalitlari takrorlanadi")
        codes = [c.code for c in self.clauses]
        if len(set(codes)) != len(codes):
            raise UxRequirementsError("qator kodlari takrorlanadi")
        # ⚠️ 87-run ning sabog'i: tip e'lon qilingan, lekin hech narsa
        # uni majburlamaydi va bitta elementli `("x")` — kortej emas,
        # **satr**. Bog'lamlarni sanaydigan har qanday tekshiruv shunda
        # jimgina yashil bo'lib qoladi.
        for item in (*self.nodes, *self.clauses):
            if not isinstance(item.binds, tuple):
                raise UxRequirementsError(f"{_code(item)}: `binds` kortej emas")
            if any(not _bind_shape(b) for b in item.binds):
                raise UxRequirementsError(f"{_code(item)}: `binds` shakli buzilgan")
        for clause in self.clauses:
            if clause.section not in SPEC_SECTIONS:
                raise UxRequirementsError(f"{clause.code}: noma'lum bo'lim {clause.section}")
            if clause.voice is Voice.SOLE and clause.copies:
                raise UxRequirementsError(f"{clause.code}: `SOLE` qator nusxa ko'rsata olmaydi")
            if clause.voice in {Voice.MIRRORED, Voice.CONFLICTED} and not clause.copies:
                raise UxRequirementsError(f"{clause.code}: nusxa e'lon qilingan, ro'yxat bo'sh")
            if clause.surface not in SURFACE_KEPT and not clause.gap:
                raise UxRequirementsError(f"{clause.code}: sirt to'liq emas, farq yozilmagan")
        for node in self.nodes:
            if node.kind in JUDGED_KINDS and node.surface not in NODE_WHOLE and not node.gap:
                raise UxRequirementsError(f"{node.key}: sirt to'liq emas, farq yozilmagan")
        known = {n.key for n in self.nodes}
        for src, dst in self.edges:
            if src not in known or dst not in known:
                raise UxRequirementsError(f"yoy noma'lum tugunga boradi: {src}→{dst}")

    # ---- §11: graf ----

    @property
    def by_kind(self) -> dict[NodeKind, tuple[str, ...]]:
        result: dict[NodeKind, list[str]] = {k: [] for k in NodeKind}
        for node in self.nodes:
            result[node.kind].append(node.key)
        return {k: tuple(keys) for k, keys in result.items()}

    @property
    def broken_nodes(self) -> tuple[FlowNode, ...]:
        """Baholanadigan tugunlardan sirti to'liq bo'lmaganlari.

        `TRIGGER` va `TERMINAL` chiqarib tashlanadi: `A` dunyoda ro'y
        beradi, `O` esa belgi. `EXTERNAL` ham chiqadi (`B`, `C`) — ular
        mahsulotdan tashqarida bajariladi, ya'ni ularning kodsizligi
        defekt emas, chegara.
        """
        return tuple(
            n for n in self.nodes if n.kind in JUDGED_KINDS and n.surface not in NODE_WHOLE
        )

    @property
    def reachable(self) -> frozenset[str]:
        """`A` dan **qurilgan** tugunlar bo'ylab yetib boriladigan to'plam.

        Hisoblanadi, e'lon qilinmaydi — va bu reyestrning boshqa
        bo'limlardan olinmaydigan yagona o'lchovi: §11 jadval emas,
        graf, ya'ni tugunning qurilgani yetmaydi, unga **yetib borish**
        kerak.

        Yo'l `NODE_PASSABLE` bo'ylab yuradi: yarim qurilgan qadam oqimni
        to'xtatmaydi (`J` da mahalla yo'q, lekin tuman bor), mahsulotdan
        tashqaridagi qadam ham to'xtatmaydi (`C` ni odam bajaradi).
        To'xtatadigan ikkita sinf: `ABSENT` (`I` — manzil kiritish yo'q)
        va `REACHABLE` (`N` — obuna taklif qilinmaydi). Ikkinchisi
        aynan shu o'lchov uchun kiritildi.
        """
        passable = {n.key for n in self.nodes if n.surface in NODE_PASSABLE}
        seen: set[str] = {"A"}
        frontier = ["A"]
        while frontier:
            current = frontier.pop()
            for src, dst in self.edges:
                if src != current or dst in seen or dst not in passable:
                    continue
                seen.add(dst)
                frontier.append(dst)
        return frozenset(seen)

    @property
    def unreachable_nodes(self) -> tuple[str, ...]:
        """Diagrammada bor, oqimda yetib bo'lmaydigan tugunlar."""
        return tuple(n.key for n in self.nodes if n.key not in self.reachable)

    @property
    def flow_completes(self) -> bool:
        """Oqim oxirigacha o'tiladimi (`O` ga yetib boriladimi).

        Bugun `False` va sabab bitta: `N` `REACHABLE`, ya'ni obuna
        taklifi hech qachon ko'rsatilmaydi va `N → O` yoyi o'tilmaydi.
        ⚠️ Amalda foydalanuvchi oqimni **tugatadi** (`state.clear()`) —
        ya'ni mahsulot §11 dan qisqaroq yo'l bilan yuradi va bu
        farqni hech narsa ko'rsatmaydi.
        """
        return "O" in self.reachable

    @property
    def dead_branches(self) -> tuple[tuple[str, str], ...]:
        """Hech qachon o'tilmaydigan yoylar."""
        reachable = self.reachable
        return tuple(
            (src, dst) for src, dst in self.edges if src not in reachable or dst not in reachable
        )

    # ---- §12–§14: qatorlar ----

    @property
    def by_section(self) -> dict[str, tuple[str, ...]]:
        result: dict[str, list[str]] = {s: [] for s in SPEC_SECTIONS}
        for clause in self.clauses:
            result[clause.section].append(clause.code)
        return {s: tuple(codes) for s, codes in result.items()}

    @property
    def by_surface(self) -> dict[Surface, tuple[str, ...]]:
        result: dict[Surface, list[str]] = {s: [] for s in Surface}
        for clause in self.clauses:
            result[clause.surface].append(clause.code)
        return {s: tuple(codes) for s, codes in result.items()}

    @property
    def by_witness(self) -> dict[Witness, tuple[str, ...]]:
        result: dict[Witness, list[str]] = {w: [] for w in Witness}
        for clause in self.clauses:
            result[clause.witness].append(clause.code)
        return {w: tuple(codes) for w, codes in result.items()}

    @property
    def by_voice(self) -> dict[Voice, tuple[str, ...]]:
        result: dict[Voice, list[str]] = {v: [] for v in Voice}
        for clause in self.clauses:
            result[clause.voice].append(clause.code)
        return {v: tuple(codes) for v, codes in result.items()}

    @property
    def unmet(self) -> tuple[Clause, ...]:
        """Talab nomlagan narsa to'liq qurilmagan."""
        return tuple(c for c in self.clauses if c.surface not in SURFACE_KEPT)

    @property
    def unwatched(self) -> tuple[Clause, ...]:
        """Repo talabni himoyalay olmaydi.

        `TEXTUAL` ham, `HUMAN` ham bu yerga tushadi va bu ataylab:
        birinchisi drift ni ko'rmaydi, ikkinchisi esa har run
        takrorlanmaydi.
        """
        return tuple(c for c in self.clauses if c.witness not in WITNESS_LIVE)

    @property
    def drifting(self) -> tuple[Clause, ...]:
        """Talab bir nechta joyda aytilgan va nusxalar zid."""
        return tuple(c for c in self.clauses if c.voice is Voice.CONFLICTED)

    @property
    def ungrounded(self) -> tuple[Clause, ...]:
        """Talab paketda yo'q manbaga havola qiladi.

        Bugun ikkitasi va ular bir xil emas: `UX-S7` hech bo'lmasa
        identifikatorlarni nomlaydi, `UI-2` esa hatto fayl nomini ham
        bermaydi.
        """
        return tuple(c for c in self.clauses if c.surface is Surface.UNGROUNDED)

    @property
    def inherited_total(self) -> int:
        """Meros qilingan nomlangan talablar soni (`UX-*` + `A11Y-*`)."""
        return _range_size(INHERITED_UX_RANGE) + _range_size(INHERITED_A11Y_RANGE)

    @property
    def inherited_named(self) -> int:
        """Ulardan mazmuni paketda aytilganlari. Bugun **bittasi**."""
        return len(INHERITED_NAMED)

    @property
    def web_clauses(self) -> tuple[Clause, ...]:
        """`web/` ga tegadigan qatorlar.

        Hisoblanadi: dalili `web/` bilan boshlanadigan har qator. Bu
        to'plamning `Witness` taqsimoti — 94–96-runlarning sabog'ining
        o'lchovi.
        """
        return tuple(c for c in self.clauses if any(b.startswith("web/") for b in c.binds))

    @property
    def web_watched_structurally(self) -> tuple[str, ...]:
        """`web/` qatorlaridan tuzilma sifatida o'qiladiganlari."""
        return tuple(c.code for c in self.web_clauses if c.witness is Witness.STRUCTURAL)

    @property
    def surfaces_hold(self) -> bool:
        """Har qator nomlagan narsa qurilganmi. Bugun `False`."""
        return not self.unmet

    @property
    def witnesses_hold(self) -> bool:
        """Har qatorni repo ko'ra oladimi. `surfaces_hold` dan mustaqil."""
        return not self.unwatched

    @property
    def voices_hold(self) -> bool:
        """Nusxalar bir-biriga zid emasmi."""
        return not self.drifting

    @property
    def accurate(self) -> bool:
        """§11–§14 bugungi haqiqatni to'g'ri tasvirlaydimi.

        To'rtta shart va to'rttasi ham **mustaqil** o'lchanadi (82-run
        ning sabog'i: birlashtirilgan shart bitta mutatsiyani
        yashiradi): qatorlar qurilgan bo'lsin; repo ularni ko'rsin;
        nusxalar zid bo'lmasin; va §11 ning oqimi oxirigacha o'tilsin.
        """
        return (
            self.surfaces_hold and self.witnesses_hold and self.voices_hold and self.flow_completes
        )


def _code(item: FlowNode | Clause) -> str:
    """Tugun uchun `key`, qator uchun `code` — xato matni uchun."""
    return item.key if isinstance(item, FlowNode) else item.code


def _bind_shape(bind: object) -> bool:
    """Dalilning shakli to'g'rimi.

    Uchta manba, uchta shakl: `app.modul` yoki `app.modul:simvol`
    (Python sirti), `web/fayl:nishon` (mijoz sirti — nishon **majburiy**,
    chunki fayl nomining o'zi 94–96-runlarning defektlarini
    ko'rsatmagan) va `tests/fayl.py` (qorovul). To'rtinchi shakl yo'q —
    shaklsiz satr dalil emas, izoh.
    """
    if not isinstance(bind, str) or not bind:
        return False
    if bind.startswith("tests/"):
        return bind.endswith(".py")
    if bind.startswith("web/"):
        return ":" in bind
    return bind.startswith("app.") and "." in bind.split(":", 1)[0]


def _range_size(bounds: tuple[str, str]) -> int:
    """`("UX-01", "UX-12")` → `12`. Diapazon **yopiq**."""
    first, last = (int(value.rsplit("-", 1)[1]) for value in bounds)
    return last - first + 1


def evaluate() -> UxRequirementsReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi (`scope`,
    `roadmap`, `success`, `functional_requirements`, `user_stories`
    bilan bir xil sabab).
    """
    return UxRequirementsReport(nodes=FLOW_NODES, clauses=CLAUSES, edges=FLOW_EDGES)

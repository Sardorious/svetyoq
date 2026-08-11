"""API talablari (`01` §16 «API Requirements») ↔ qurilgan interfeys.

**Nima uchun bu modul bor.** 85-run uchta nomzod qoldirdi va §16 ni
birinchi qatorga qo'ydi. Sabab shunchaki navbat emas: §16 paketdagi
yagona bo'lim bo'lib, u mahsulot haqida emas, **shartnoma** haqida
gapiradi. Qolgan reyestrlar «bu funksiya qurilganmi» deb so'raydi; §16
esa mijoz bilan tuzilgan kelishuvning shartlarini sanaydi — parametr
nomi, uning majburiyligi, sarlavha, autentifikatsiya usuli. Bunday
qatorning yolg'onligi funksiyaning yo'qligiday ko'rinmaydi: kod
ishlaydi, testlar yashil, va faqat integratsiya qilayotgan uchinchi
tomon hujjat aytgan parametrni yuborib `422` oladi.

E15 ning mezoni aynan shu edi — «tashqi so'rov **hujjat bo'yicha**
ishlaydi» (`04` E15). Bu modul o'sha mezonni §16 ga qo'llaydi.

## Bu fayl `test_api_surface_contract.py` bilan ustma-tush emas

48-run `05` §7.2 ni qulfladi: **qaysi yo'l bor**, qaysi metod bilan,
kimga ochiq. Bu yerdagi savol bir daraja pastda: yo'l topilgandan
keyin mijoz uni **qanday chaqiradi**. Parametrning nomi, majburiymi,
qaysi sarlavha o'qiladi, javob qaysi media turida keladi, kesh nima
bilan bo'linadi. §7.2 ning jadvalida bu ustunlar umuman yo'q.

## Asosiy topilma: ikkita hujjat bir xil narsani aytadi va ikkalasi ham noto'g'ri

§16 ning birinchi qatori parametrni **`region_id`** deb ataydi va uni
«обязателен во всех гео-запросах» deydi. `05` §7.2 ning oxirgi satri
o'sha da'voni **so'zma-so'z takrorlaydi** va manba sifatida shu
qatorga havola qiladi: «`region_id` barcha geo-so'rovlarda majburiy
(PRD §16)».

Kod esa ikkalasini ham bajarmaydi. Parametrning nomi — `region`,
qiymati — mintaqa **kodi** (`samarkand`), `uuid` emas; va u
majburiy emas: bo'sh qolsa `settings.default_region_code` ishlaydi.
O'n ikkita yo'l shunday — ommaviy sathdagi to'qqiztasi
(`/geo/*`, `/heatmap`, `/map*`, `/stats*`) va ma'muriy sathdagi
uchtasi, ya'ni istisno emas, qoida.

⚠️ **Takrorlanish xatoni tuzatmaydi, uni himoyalaydi.** Ikki hujjatni
solishtirgan o'quvchi kelishuvni ko'radi va tekshirishni to'xtatadi:
§7.2 §16 ga havola qiladi, §16 esa o'z-o'zini tasdiqlaydi. Yagona
uchinchi ovoz — kodning o'zi, va u hech kim so'ramagan joyda turibdi.
Shuning uchun `Echo` alohida o'q: qatorning **qayerda takrorlangani**
uning rostligidan mustaqil fakt va u xuddi shu tarzda o'lchanadi.

⚠️ Va uchinchi ovoz aslida bor edi: `05` §7.1 ning o'z misoli —
`GET /api/v1/map?region=samarkand`. Ya'ni **bitta hujjat** ikki
bo'limda ikki xil parametr nomini yozadi, misol esa haqiqatga mos
keladi. `Echo.SPLIT` shuni nomlaydi.

## Ikkinchi topilma: qatorning ikkinchi yarmi koddan emas, hujjatdan talab qiladi

Birinchi qatorning davomi — «отсутствие → регион по умолчанию, **что
подлежит явной фиксации в спецификации**». Bu topshiriq dasturchiga
emas, paketning o'ziga berilgan: standart mintaqaga tushish qoidasi
biror joyda yozib qo'yilishi kerak.

Mexanizm qurilgan (`settings.default_region_code`, hamma yo'lda
bir xil), qoida esa **hech qayerda yozilmagan**: paketning yettala
hujjatida «регион по умолчанию» iborasi faqat shu qatorning o'zida
uchraydi. Ya'ni talab o'zini bajarilmagan deb e'lon qiladi va buni
hech narsa ko'rsatmaydi — chunki tekshiradigan odam koddan boshlaydi,
kodda esa hammasi joyida.

## Uchinchi topilma: «наследуются без изменений» merosxo'r hujjatsiz

Bo'limning epigrafi `17_OpenAPI.yaml` ga havola qiladi va oltita
xossani undan meros qilib oladi. O'sha fayl **paketda yo'q** —
repoda ham, hujjatlar ro'yxatida ham. Ya'ni oltala xossaning ham
manbasi tekshirib bo'lmaydigan joyda, va ular orasida ikkitasi
mahsulot uchun hal qiluvchi: rate limit va idempotentlik.

* **rate limit** — ommaviy API da umuman yo'q (`app.admin.security`
  buni `rate_limit_api` sifatida allaqachon `ABSENT` deb yozgan,
  71-run). Xabar qabul qilish yo'li himoyalangan, `/api/v1` esa
  ochiq;
* **idempotentlik** — ommaviy sathda **tasodifan** bajariladi: u
  yerdagi hamma narsa `GET`, ya'ni HTTP ning o'zi kafolatlaydi.
  Ma'muriy `POST` lar (`reject`, `merge`, `block`, `trust`) esa
  `Idempotency-Key` ni o'qimaydi, ya'ni takroriy so'rov ikkinchi
  audit yozuvini qoldiradi. Xossa bor, uni ushlab turadigan mexanizm
  yo'q — `Delivery.INCIDENTAL` shuni nomlaydi;
* **версионирование** ham o'sha sinfda va sababi kutilmagan:
  `/api/v1` — konstanta emas, **sozlama** (`API_PREFIX`,
  44-running ochiq savoli). Sozlamani o'zgartirish versiya
  **qo'shmaydi**, u mavjud versiyani joyidan **ko'chiradi**: eski
  yo'l o'sha zahoti yo'qoladi va hamma mijoz bir vaqtda uziladi.
  Bu versiyalashning teskarisi.

## Teskari yo'nalish: mijoz bilishi shart bo'lgan beshta narsa §16 da yo'q

Delta jadvali «nima o'zgardi» ni sanaydi, lekin o'zgargan narsalarning
bir qismi unga tushmagan. Beshtasi mijozning kodiga bevosita ta'sir
qiladi: shartli so'rovlar (`ETag`/`304`), keshning til bo'yicha
bo'linishi (`Vary`), ma'muriy sathning autentifikatsiyasi
(`X-Admin-Token` — §16 esa OAuth/JWT deydi), JSON dan boshqa ikkita
media turi (`text/csv`, `text/plain; version=0.0.4`) va yagona xato
tanasi (`ErrorResponse`, FastAPI ning standart `422` si ataylab
almashtirilgan).

Ular «qurilmagan» emas — aksincha, qurilgan va hujjatlangan
(`/openapi.json` ularni ko'rsatadi). Bo'shliq §16 da: bo'lim o'zini
delta deb ataydi va deltaning yarmini sanamaydi.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi. Parametr `region_id` ga qayta nomlanmadi va
majburiy qilinmadi: ikkalasi ham buzuvchi o'zgarish (`/map` prodda
jonli, `web/` unga tayanadi) va ikkalasi ham hujjatning qaysi tomoni
haq ekanini talab qiladi — bu odam qarori. Modul o'lchaydi,
tahrirlamaydi (75-, 76-, 77-, 82-, 83-, 84- va 85-runlar bilan bir xil
qoida).

**Modul `app/core/` da yashaydi va `app.*` dan hech narsa import
qilmaydi.** Tabiiy joyi `app/api/` bo'lardi, lekin uni indeksga
ulaydigan `app/admin/registries.py` shunda `admin → api` importini
yasardi, `03` §Q-1 esa faqat teskarisiga ruxsat beradi
(`app.api` → `app.admin`, 79-run). Reyestr sof e'lon bo'lgani uchun
qurilgan sathni **test** o'lchaydi: `app.openapi()` va `ast` orqali.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Hujjat bo'limi. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "01 §16"

#: Delta jadvalining uzunligi. Hujjatdan parse qilinadi va reyestr bilan
#: solishtiriladi (`test_api_requirements_contract`).
SPEC_ROWS = 7

#: Delta jadvalining sarlavhasi — aynan.
SPEC_COLUMNS: tuple[str, ...] = ("Изменение", "Описание")

#: Epigrafdagi qavs ichida sanalgan meros xossalari — aynan va tartibda.
SPEC_INHERITED: tuple[str, ...] = (
    "OpenAPI 3.1",
    "REST",
    "`/api/v1`",
    "идемпотентность",
    "rate limit",
    "версионирование",
)

#: Meros manbai. **Paketda yo'q** — test buni alohida o'lchaydi va
#: `Echo.INHERITED` hukmi shundan kelib chiqadi.
INHERITED_DOC = "17_OpenAPI.yaml"

#: Hujjat nomlagan parametr va kod ochgan parametr. Ikkalasi ham
#: qo'lda emas — test birinchisini `01` §16 dan, ikkinchisini
#: `app.openapi()` dan oladi va shu ikki konstanta bilan solishtiradi.
PARAM_IN_SPEC = "region_id"
PARAM_IN_CODE = "region"

#: `PARAM_IN_CODE` ni ochadigan ommaviy yo'llar (prefikssiz). Ro'yxat
#: **to'liq**: test undan ortiq yoki kam bo'lsa yiqiladi, ya'ni yangi
#: geo-endpoint qo'shilganda bu qator qayta ko'rib chiqiladi.
REGION_PARAM_PATHS: tuple[str, ...] = (
    "/admin/digest",
    "/admin/gates",
    "/admin/outages",
    "/geo/districts",
    "/geo/mahallas",
    "/heatmap",
    "/map",
    "/map/config",
    "/map/i18n",
    "/stats",
    "/stats.csv",
    "/stats/methodology",
)

#: §16 ning beshinchi qatori ruxsat bergan tillar — aynan va tartibda.
SPEC_LANGUAGES: tuple[str, ...] = ("uz", "ru")


class Delivery(StrEnum):
    """Qurilgan interfeys qator bilan nima qilgan.

    Yetti sinf. «Bor / yo'q» ikkiligi bu bo'limda beshta turli holatni
    bitta katakka tiqib qo'yardi: nomi boshqa, kuchi boshqa, ichi
    bo'sh, ataylab yo'q va umuman tekshirib bo'lmaydigan — bularning
    hech biri bir-biriga teng emas.
    """

    #: Yozilganidek qurilgan.
    HONORED = "honored"
    #: Xulq-atvor qurilgan, lekin qator nomlagan nom yoki shakl bilan emas.
    RENAMED = "renamed"
    #: Xossa bajariladi, uni ushlab turadigan mexanizm yo'q — yon mahsulot.
    INCIDENTAL = "incidental"
    #: Sirt qurilgan, ortidagi ma'lumot hech qachon kelmaydi.
    EMPTY = "empty"
    #: Qator chetlashtiradi va u haqiqatan yo'q — talab **yo'qlik bilan** bajarilgan.
    WITHHELD = "withheld"
    #: Talab qilingan va qurilmagan.
    ABSENT = "absent"
    #: Manbasi paketdan tashqarida — repo guvoh bo'la olmaydi.
    EXTERNAL = "external"


#: Qator «bajarilgan» deb hisoblanadigan sinflar. `INCIDENTAL` bu yerda
#: **yo'q**: bugun ishlayotgan narsa ertaga birinchi `POST` bilan
#: to'xtaydi va uni hech narsa ushlab qolmaydi.
DELIVERY_KEPT: frozenset[Delivery] = frozenset({Delivery.HONORED, Delivery.WITHHELD})


class Obligation(StrEnum):
    """Qatorning modalligi qurilgan sathda kuchdami."""

    #: Qator shart qo'yadi va kod uni majburlaydi.
    BINDING = "binding"
    #: Qator «обязателен» deydi, kod esa ixtiyoriy qoldiradi.
    RELAXED = "relaxed"
    #: Qator shart qo'ymaydi — tavsif, talab emas.
    SILENT = "silent"
    #: Shart bor, lekin uni repo tekshira olmaydi.
    UNWITNESSED = "unwitnessed"


class Echo(StrEnum):
    """Qator paketning boshqa joyida qanday takrorlangan.

    Bu o'q qatorning **rostligini** o'lchamaydi — u takrorlanishning
    o'zini o'lchaydi. Sabab bosh topilmada: noto'g'ri qator ikkinchi
    hujjatda takrorlangani uchun o'n rundan beri tirik.
    """

    #: Paketda faqat shu yerda.
    SOLE = "sole"
    #: Boshqa bo'lim takrorlaydi va u bilan **kelishadi**.
    ECHOED = "echoed"
    #: Paket bu haqda ikki joyda ikki xil gapiradi.
    SPLIT = "split"
    #: Boshqa bo'lim o'sha **so'zni** boshqa narsa uchun ishlatadi.
    HOMONYM = "homonym"
    #: Manbasi paketdan tashqaridagi hujjat.
    INHERITED = "inherited"


class ApiRequirementsError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class Requirement:
    """§16 delta jadvalining bitta qatori va uning bugungi bahosi."""

    code: str
    #: «Изменение» katagi — aynan, tarjimasiz.
    change: str
    #: «Описание» katagi — aynan, tarjimasiz.
    description: str
    delivery: Delivery
    obligation: Obligation
    echo: Echo
    #: Nima uchun aynan shu baho. Keyingi o'quvchi uchun.
    note: str
    #: Dalil: `modul:simvol`. `Delivery.WITHHELD` va `EXTERNAL` da bo'sh
    #: bo'lishi mumkin — yo'qlikning dalili simvolning yo'qligi va uni
    #: test alohida o'lchaydi.
    binds: tuple[str, ...] = ()
    #: Da'vo bilan qurilgan narsa orasidagi farq.
    gap: str = ""
    #: Qator paketning **o'zidan** biror narsani yozib qo'yishni talab
    #: qiladimi (koddan emas).
    demands_spec: bool = False
    #: Talab qilgan bo'lsa — u yozilganmi. Test buni hujjatlardan
    #: qidiradi, qo'lda ishonmaydi.
    spec_written: bool = False
    #: Katakning matni ikki xil o'qilsa — ikkinchi o'qish.
    ambiguity: str = ""


@dataclass(frozen=True)
class InheritedClaim:
    """Epigrafdagi meros xossasi (`17_OpenAPI.yaml` dan)."""

    code: str
    #: Qavs ichidagi atama — aynan.
    label: str
    delivery: Delivery
    note: str
    binds: tuple[str, ...] = ()


@dataclass(frozen=True)
class UndeclaredInterface:
    """Qurilgan va §16 da nomlanmagan interfeys sharti (teskari yo'nalish)."""

    code: str
    #: Mijozning kodiga nima ta'sir qiladi.
    title: str
    why: str
    binds: tuple[str, ...]


# --------------------------------------------------------------------------
# Reyestr — `01` §16 delta jadvali, hujjatdagi tartibda
# --------------------------------------------------------------------------

REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement(
        code="A-1",
        change="Параметр `region_id`",
        description=(
            "Обязателен во всех гео-запросах; отсутствие → регион по умолчанию, "
            "что подлежит явной фиксации в спецификации"
        ),
        delivery=Delivery.RENAMED,
        obligation=Obligation.RELAXED,
        echo=Echo.SPLIT,
        demands_spec=True,
        spec_written=False,
        note=(
            "Uchta da'vo, uchtasi ham bajarilmagan. **Nomi:** hujjat "
            "`region_id` deydi, kod `region` ni ochadi va u `uuid` emas, "
            "mintaqa **kodi** (`samarkand`) — ya'ni farq imloviy emas, "
            "tipda. **Kuchi:** «обязателен» deyilgan, kod esa bo'sh "
            "qiymatni qabul qiladi va `settings.default_region_code` ga "
            "tushadi; o'n ikkala yo'lda bir xil. **Takrorlanishi:** "
            "`05` §7.2 o'sha da'voni so'zma-so'z takrorlaydi va §16 ga "
            "havola qiladi, `05` §7.1 ning misoli esa `?region=samarkand` "
            "yozadi — bitta hujjat ikki bo'limda ikki xil parametrni "
            "nomlaydi."
        ),
        binds=(
            "app.core.config:settings.default_region_code",
            "app.api.v1.map:RegionQuery",
            "app.api.v1.stats:RegionQuery",
        ),
        gap=(
            "«Обязателен» ni bajarish — buzuvchi o'zgarish: `/map` prodda "
            "jonli va `web/app.js` uni parametrsiz chaqiradi. Ya'ni "
            "tanlov ikkita va ikkalasi ham odamniki: qatorni kodga "
            "moslashtirish yoki mijozlarni ko'chirish."
        ),
    ),
    Requirement(
        code="A-2",
        change="`GET /geo/mahallas`",
        description="Новый эндпоинт: справочник махаллей с полигонами и версией",
        delivery=Delivery.EMPTY,
        obligation=Obligation.SILENT,
        echo=Echo.SOLE,
        note=(
            "Endpoint to'liq qurilgan va uchala nomlangan bo'lakni ham "
            "beradi: spravochnik (`registry`), poligonlar (`features`) "
            "va versiya (`registry.version`). Ortidagi jadval esa E17 "
            "gacha bo'sh, ya'ni javob har doim `available: false` va "
            "`count: 0`. Bu yiqilish emas — 27-run javobni ataylab "
            "**jimgina bo'sh emas** qilib qurgan (ogohlantirish va "
            "dislaymer bilan), lekin qator va'da qilgan spravochnik "
            "hozircha yo'q. `01` §16 dagi yagona qator bo'lib, uni "
            "`05` §7.2 jadvali umuman sanamaydi."
        ),
        binds=(
            "app.geo.mahallas:summarize",
            "app.geo.queries:mahalla_boundaries",
        ),
        gap="Poligonlar odam ishi (E17) — repo uni yopa olmaydi.",
    ),
    Requirement(
        code="A-3",
        change="`GET /geo/districts`",
        description="Расширен параметром `region_id` и полем `valid_from` / `valid_to`",
        delivery=Delivery.RENAMED,
        obligation=Obligation.SILENT,
        echo=Echo.ECHOED,
        note=(
            "Qatorning ikkinchi yarmi to'liq bajarilgan va u yagona "
            "joyda **ikki hujjat kelishgan**: `05` §7.2 jadvali ham "
            "«Chegaralar, `valid_from`/`valid_to` bilan» deydi, "
            "`DistrictProperties` ikkala maydonni ham beradi va `?at=` "
            "o'tmishdagi kesimni so'rashga imkon beradi. Birinchi yarmi "
            "esa `A-1` bilan bir xil taqdirda: parametr bor, nomi "
            "boshqa."
        ),
        binds=(
            "app.api.v1.geo:DistrictProperties",
            "app.geo.queries:district_boundaries",
        ),
    ),
    Requirement(
        code="A-4",
        change="Ответы статистики",
        description="Добавлено поле версии справочника границ и индекса покрытия махалли",
        delivery=Delivery.HONORED,
        obligation=Obligation.SILENT,
        echo=Echo.SOLE,
        ambiguity=(
            "«Поле версии справочника границ **и** индекса покрытия "
            "махалли» ikki xil o'qiladi. Birinchi o'qish (ikkita maydon: "
            "chegara versiyasi va mahalla qamrov indeksi) bajarilgan. "
            "Ikkinchi o'qishda «версия» ikkala otga ham tarqaladi va "
            "u bajarilmagan: `MahallaCoverageOut` da versiya maydoni "
            "yo'q — mahalla qamrovi qaysi spravochnik kesimida "
            "hisoblanganini javobdan bilib bo'lmaydi."
        ),
        note=(
            "`StatsOut` ikkala blokni ham beradi: `boundaries.version` "
            "(davrdagi eng so'nggi kesim sanasi, `versions` va "
            "`changed_in_period` bilan) va `mahallas` (qamrov indeksi, "
            "`available` bayrog'i bilan). Birinchisi haqiqiy ma'lumot "
            "beradi, ikkinchisi E17 gacha bo'sh — lekin bo'shligini "
            "o'zi aytadi, ya'ni maydon yolg'on gapirmaydi."
        ),
        binds=(
            "app.api.v1.stats:BoundariesOut",
            "app.api.v1.stats:MahallaCoverageOut",
        ),
    ),
    Requirement(
        code="A-5",
        change="`Accept-Language`",
        description="Значения `uz` и `ru`; порядок по умолчанию зависит от региона",
        delivery=Delivery.HONORED,
        obligation=Obligation.BINDING,
        echo=Echo.SOLE,
        note=(
            "Qatorning ikkala yarmi ham mexanizm bilan qurilgan. "
            "«Значения `uz` и `ru`»: `preferred()` sarlavhani `RFC 9110` "
            "§12.5.4 bo'yicha to'liq tahlil qiladi (`q`, `*`, `q=0`) va "
            "`SUPPORTED_LANGUAGES` dan tashqarisiga `None` qaytaradi. "
            "«Порядок по умолчанию зависит от региона»: `None` holatida "
            "javob `regions.default_language` da beriladi, global "
            "`DEFAULT_LANGUAGE` da emas — `get_client_language` ataylab "
            "standart tilni **bilmaydi**, chunki standart mintaqaning "
            "atributi (`01` §17). §16 bu shartni qo'yadigan yagona joy: "
            "`Accept-Language` paketning boshqa hech qaysi hujjatida "
            "uchramaydi."
        ),
        binds=(
            "app.core.i18n:preferred",
            "app.core.i18n:SUPPORTED_LANGUAGES",
            "app.geo.registry:language_for",
            "app.api.deps:get_client_language",
        ),
    ),
    Requirement(
        code="A-6",
        change="Webhook / WebSocket",
        description="Не входят в скоуп регионального запуска",
        delivery=Delivery.WITHHELD,
        obligation=Obligation.SILENT,
        echo=Echo.HOMONYM,
        note=(
            "WebSocket repoda umuman yo'q — na marshrut, na kutubxona. "
            "Webhook esa **bor** va u boshqa narsa: Telegram bizga "
            "so'rov yuboradigan kiruvchi yo'l (`05` §6.3), mijozga "
            "yuboriladigan chiquvchi hodisa emas. U bir xil FastAPI "
            "ilovasida yashaydi va shu sababdan `include_in_schema=False` "
            "bilan e'lon qilingan: `/openapi.json` da ko'rinsa, ommaviy "
            "API ni o'qigan mijoz uni o'ziga taklif deb o'qirdi. Chegara "
            "ushlanadi va uni ushlab turgan narsa aynan shu bayroq."
        ),
        binds=("app.core.config:settings.telegram_webhook_path",),
        gap=(
            "Bitta so'z ikki xil ma'noda: §16 ni o'qigan odam «webhook "
            "yo'q» deb tushunadi, `05` §6.3 esa webhook ni majburiy "
            "qiladi. Ikkalasi ham haq."
        ),
    ),
    Requirement(
        code="A-7",
        change="OAuth / JWT",
        description="Наследуются без изменений",
        delivery=Delivery.EXTERNAL,
        obligation=Obligation.UNWITNESSED,
        echo=Echo.INHERITED,
        note=(
            "«Без изменений» — nimadan? Manba `17_OpenAPI.yaml` va u "
            "paketda yo'q, ya'ni qatorni tasdiqlash ham, rad etish ham "
            "mumkin emas. Repoda qurilgan yagona autentifikatsiya — "
            "`X-Admin-Token`: muhitdagi uzun tasodifiy token, "
            "`hmac.compare_digest` bilan taqqoslanadi, aktor nomdan "
            "`uuid5` bilan olinadi. U na OAuth, na JWT; ommaviy sathda "
            "esa autentifikatsiya umuman yo'q va bu ataylab "
            "(`05` §7.3 ochiq ma'lumot)."
        ),
        binds=("app.admin.auth:HEADER_NAME",),
        gap=(
            "Qator meros deb belgilangani uchun hech kim uni qurishga "
            "majbur emas, va shu bilan birga hech kim uni yolg'on deb "
            "ham ayta olmaydi. `01` §20 ning MFA talabi shu bo'shliqqa "
            "tushadi (71-run, SEC)."
        ),
    ),
)


# --------------------------------------------------------------------------
# Epigraf — `17_OpenAPI.yaml` dan meros olinadigan oltita xossa
# --------------------------------------------------------------------------

INHERITED_CLAIMS: tuple[InheritedClaim, ...] = (
    InheritedClaim(
        code="I-1",
        label="OpenAPI 3.1",
        delivery=Delivery.HONORED,
        note=(
            "`app.openapi()` `3.1.0` chiqaradi va bu FastAPI ning "
            "versiyasidan keladi, sozlamadan emas. `customize()` sxemaga "
            "teglar, litsenziya, yagona xato sxemasi va barqaror "
            "`operationId` qo'shadi."
        ),
        binds=("app.api.openapi:customize",),
    ),
    InheritedClaim(
        code="I-2",
        label="REST",
        delivery=Delivery.HONORED,
        note=(
            "Yigirma beshta yo'l, resurs nomlari ot shaklida, o'qish "
            "`GET`, holat o'zgartirish `POST`. Shartli so'rovlar "
            "(`ETag`/`304`) va kesh sarlavhalari HTTP ning o'z "
            "vositalari bilan."
        ),
        binds=("app.api.router:api_router",),
    ),
    InheritedClaim(
        code="I-3",
        label="`/api/v1`",
        delivery=Delivery.HONORED,
        note="Barcha marshrutlar `settings.api_prefix` ostida ulanadi.",
        binds=("app.core.config:settings.api_prefix",),
    ),
    InheritedClaim(
        code="I-4",
        label="идемпотентность",
        delivery=Delivery.INCIDENTAL,
        note=(
            "Ommaviy sathda bajariladi va buni hech narsa ushlab "
            "turmaydi: u yerdagi hamma narsa `GET`, ya'ni kafolatni "
            "HTTP ning o'zi beradi. Ma'muriy `POST` lar "
            "(`reject`, `merge`, `block`, `trust`) `Idempotency-Key` "
            "ni o'qimaydi — takroriy so'rov ikkinchi `audit_log` "
            "yozuvini qoldiradi. Botdagi idempotentlik boshqa qatlamda "
            "va boshqa kalitda (`05` §6.3, `telegram_update_id`), ya'ni "
            "u bu xossani qoplamaydi."
        ),
        binds=("app.admin.audit:record",),
    ),
    InheritedClaim(
        code="I-5",
        label="rate limit",
        delivery=Delivery.ABSENT,
        note=(
            "Ommaviy API da cheklagich yo'q. `RateLimitedError` (`429`) "
            "mavjud va u faqat xabar qabul qilish yo'lida ishlaydi "
            "(`intake.check_rate_limit`, `REPORT_RATE_LIMIT_MIN`). "
            "`/api/v1` uchun yagona to'siq — `ETag`/`304` va snapshot "
            "keshi, ya'ni so'rovning **narxi** kamayadi, soni emas. "
            "71-run buni `app.admin.security:rate_limit_api` da "
            "`Posture.ABSENT` deb yozgan; bu qator o'sha topilmani "
            "ikkinchi tomondan tasdiqlaydi."
        ),
        binds=("app.core.errors:RateLimitedError",),
    ),
    InheritedClaim(
        code="I-6",
        label="версионирование",
        delivery=Delivery.INCIDENTAL,
        note=(
            "Prefiks bor, siyosat yo'q. `api_prefix` — `Settings` "
            "maydoni, ya'ni `/api/v1` **sozlama**: uni o'zgartirish "
            "yangi versiya qo'shmaydi, mavjudini ko'chiradi va eski "
            "yo'lni o'sha zahoti yo'q qiladi. Repoda ikkinchi versiya "
            "ham, eskirish sarlavhalari ham, versiyalar orasidagi "
            "muvofiqlik qoidasi ham yo'q. 44-run `API_PREFIX` ning "
            "sozlama bo'lib qolishini ochiq savol sifatida qoldirgan — "
            "bu qator uning narxini ko'rsatadi."
        ),
        binds=("app.core.config:settings.api_prefix",),
    ),
)


# --------------------------------------------------------------------------
# Teskari yo'nalish — qurilgan va §16 da nomlanmagan interfeys shartlari
# --------------------------------------------------------------------------

UNDECLARED: tuple[UndeclaredInterface, ...] = (
    UndeclaredInterface(
        code="X-1",
        title="Shartli so'rovlar: `ETag` + `If-None-Match` → `304`",
        why=(
            "Yettita javobda `ETag` bor va mijoz `If-None-Match` "
            "yuborsa tanasiz `304` oladi. Buni kutmagan mijoz `304` ni "
            "xato deb o'qiydi yoki keshni umuman ishlatmaydi — ya'ni "
            "§7.1 ning butun yuklama rejasi mijoz tomonida bekor "
            "bo'ladi."
        ),
        binds=("app.core.etag:matches", "app.core.etag:payload_etag"),
    ),
    UndeclaredInterface(
        code="X-2",
        title="`Vary: Accept-Language`",
        why=(
            "`A-5` ning keshdagi natijasi. Tarjima qilingan matn "
            "qaytaradigan javoblarda `ETag` tilga bog'liq, ya'ni "
            "`Vary` siz oraliq kesh ruscha javobni o'zbek so'roviga "
            "berib yuborardi. §16 sarlavhani nomlaydi, uning kesh "
            "oqibatini emas."
        ),
        binds=("app.api.v1.geo:get_mahallas",),
    ),
    UndeclaredInterface(
        code="X-3",
        title="`X-Admin-Token` — ma'muriy sathning yagona kaliti",
        why=(
            "O'n ikkita yo'l shu sarlavha bilan himoyalangan, §16 esa "
            "autentifikatsiya haqida faqat `A-7` da gapiradi va u yerda "
            "OAuth/JWT deyilgan. Ya'ni hujjatni o'qigan integrator "
            "mavjud bo'lmagan sxemani qidiradi."
        ),
        binds=("app.admin.auth:HEADER_NAME", "app.api.deps:get_actor"),
    ),
    UndeclaredInterface(
        code="X-4",
        title="JSON dan boshqa ikkita media turi",
        why=(
            "`/stats.csv` — `text/csv; charset=utf-8`, `/metrics` — "
            "`text/plain; version=0.0.4; charset=utf-8` (Prometheus "
            "eksporti). Ikkalasi ham §16 ning deltasida yo'q, va "
            "ikkalasida ham `/openapi.json` **noto'g'ri** media turini "
            "e'lon qiladi: sxemada `text/plain` turadi, server esa "
            "`text/csv` yuboradi. Ya'ni bu qatorni faqat §16 emas, "
            "hujjatning o'zi ham noto'g'ri yozadi — sxemadan yasalgan "
            "mijoz javobni boshqa nom bilan qabul qiladi."
        ),
        binds=("app.obs.metrics:CONTENT_TYPE",),
    ),
    UndeclaredInterface(
        code="X-5",
        title="Yagona xato tanasi (`ErrorResponse`)",
        why=(
            'FastAPI ning standart `422` si (`{"detail": [...]}`) '
            "ataylab almashtirilgan: barcha xatolar `SvetaError.to_dict` "
            "shaklida keladi va hujjat shuni yozadi. Bu — meros olingan "
            "kontraktdan chetlanish, ya'ni aynan deltaga tushishi kerak "
            "edi."
        ),
        binds=("app.api.openapi:ErrorResponse", "app.core.errors:SvetaError"),
    ),
)


# --------------------------------------------------------------------------
# Ichki tekshiruv — import paytida
# --------------------------------------------------------------------------


def _check_registry() -> None:
    codes = [r.code for r in REQUIREMENTS]
    if len(set(codes)) != len(codes):
        raise ApiRequirementsError("qator kodlari takrorlangan")
    if len(REQUIREMENTS) != SPEC_ROWS:
        raise ApiRequirementsError(f"jadval {SPEC_ROWS} qator, reyestr {len(REQUIREMENTS)}")

    for row in REQUIREMENTS:
        if not row.change or not row.description:
            raise ApiRequirementsError(f"{row.code}: katak bo'sh")
        if not row.note:
            raise ApiRequirementsError(f"{row.code}: izohsiz")
        if row.spec_written and not row.demands_spec:
            raise ApiRequirementsError(f"{row.code}: talab qilmagan narsani yozib bo'lmaydi")
        # Dalil qurilgan narsa uchun majburiy. `EXTERNAL` va `WITHHELD`
        # dan tashqari — ularda dalil **bo'lishi** mumkin (chegarani
        # ushlab turgan bayroq ham dalil), lekin talab qilinmaydi.
        if row.delivery not in {Delivery.EXTERNAL, Delivery.WITHHELD} and not row.binds:
            raise ApiRequirementsError(f"{row.code}: dalilsiz")
        # Modallik va yetkazib berish bir-biriga bog'liq: kuchsizlantirilgan
        # shart faqat qurilgan sathda bo'ladi.
        if row.obligation is Obligation.RELAXED and row.delivery in {
            Delivery.ABSENT,
            Delivery.EXTERNAL,
        }:
            raise ApiRequirementsError(f"{row.code}: qurilmagan narsa kuchsizlanmaydi")

    inherited_codes = [c.code for c in INHERITED_CLAIMS]
    if len(set(inherited_codes)) != len(inherited_codes):
        raise ApiRequirementsError("meros kodlari takrorlangan")
    if len(INHERITED_CLAIMS) != len(SPEC_INHERITED):
        raise ApiRequirementsError("epigraf va meros ro'yxati uzunligi teng emas")
    for claim, label in zip(INHERITED_CLAIMS, SPEC_INHERITED, strict=True):
        if claim.label != label:
            raise ApiRequirementsError(f"{claim.code}: epigrafdagi atama boshqa")
        if not claim.note or not claim.binds:
            raise ApiRequirementsError(f"{claim.code}: izohsiz yoki dalilsiz")

    undeclared_codes = [u.code for u in UNDECLARED]
    if len(set(undeclared_codes)) != len(undeclared_codes):
        raise ApiRequirementsError("teskari yo'nalish kodlari takrorlangan")
    for entry in UNDECLARED:
        if not entry.binds or not entry.why:
            raise ApiRequirementsError(f"{entry.code}: dalilsiz")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ApiRequirementsReport:
    """`01` §16 ning bugungi holati."""

    requirements: tuple[Requirement, ...]
    inherited: tuple[InheritedClaim, ...]
    undeclared: tuple[UndeclaredInterface, ...]

    @property
    def by_delivery(self) -> dict[Delivery, tuple[str, ...]]:
        result: dict[Delivery, list[str]] = {d: [] for d in Delivery}
        for row in self.requirements:
            result[row.delivery].append(row.code)
        for claim in self.inherited:
            result[claim.delivery].append(claim.code)
        return {d: tuple(codes) for d, codes in result.items()}

    @property
    def by_obligation(self) -> dict[Obligation, tuple[str, ...]]:
        result: dict[Obligation, list[str]] = {o: [] for o in Obligation}
        for row in self.requirements:
            result[row.obligation].append(row.code)
        return {o: tuple(codes) for o, codes in result.items()}

    @property
    def by_echo(self) -> dict[Echo, tuple[str, ...]]:
        result: dict[Echo, list[str]] = {e: [] for e in Echo}
        for row in self.requirements:
            result[row.echo].append(row.code)
        return {e: tuple(codes) for e, codes in result.items()}

    @property
    def misnamed(self) -> tuple[Requirement, ...]:
        """Hujjat bir nomni yozadi, kod boshqasini ochadi."""
        return tuple(r for r in self.requirements if r.delivery is Delivery.RENAMED)

    @property
    def relaxed(self) -> tuple[Requirement, ...]:
        """«Обязателен» deyilgan va majburlanmagan qatorlar."""
        return tuple(r for r in self.requirements if r.obligation is Obligation.RELAXED)

    @property
    def restated(self) -> tuple[Requirement, ...]:
        """Paket ikki joyda ikki xil gapiradigan qatorlar.

        Bosh topilmaning o'lchagichi. Ro'yxat bo'sh bo'lmasa, hujjatni
        hujjat bilan solishtirish yetarli emas — uchinchi ovoz kerak.
        """
        return tuple(r for r in self.requirements if r.echo is Echo.SPLIT)

    @property
    def unwritten(self) -> tuple[Requirement, ...]:
        """Paketning o'zidan talab qilingan va yozilmagan qoidalar."""
        return tuple(r for r in self.requirements if r.demands_spec and not r.spec_written)

    @property
    def ambiguous(self) -> tuple[Requirement, ...]:
        """Katagi ikki xil o'qiladigan qatorlar."""
        return tuple(r for r in self.requirements if r.ambiguity)

    @property
    def unwitnessed_inheritance(self) -> tuple[str, ...]:
        """Manbasi paketdan tashqarida bo'lgan hamma narsa.

        Delta qatori ham, epigraf xossasi ham shu yerga tushadi:
        ikkalasining ham hukmi `17_OpenAPI.yaml` ga bog'liq va u fayl
        paketda yo'q.
        """
        rows = tuple(r.code for r in self.requirements if r.echo is Echo.INHERITED)
        claims = tuple(c.code for c in self.inherited if c.delivery is not Delivery.HONORED)
        return rows + claims

    @property
    def names_hold(self) -> bool:
        """Hujjat nomlagan parametr — kod ochgan parametrmi.

        Alohida xossa, chunki uning narxi alohida: `accurate` ni
        yaxshilash uchun qilinadigan ish bilan buni tuzatish uchun
        qilinadigan ish bir xil emas (birinchisi hujjat, ikkinchisi
        buzuvchi reliz).
        """
        return not self.misnamed

    @property
    def contract_holds(self) -> bool:
        """Delta jadvalining hamma qatori bajarilganmi.

        `INCIDENTAL` bu yerda ham hisobga olinmaydi — u faqat epigrafda
        uchraydi va shartnomani ushlab turmaydi.
        """
        return all(r.delivery in DELIVERY_KEPT for r in self.requirements)

    @property
    def accurate(self) -> bool:
        """§16 bugungi interfeysni to'g'ri tasvirlaydimi.

        To'rtta shart va to'rttasi ham mustaqil: jadvalning hamma
        qatori bajarilsin; modallik kuchsizlanmasin; paket bir og'izdan
        gapirsin; va qurilgan interfeysda §16 nomlamagan shart
        qolmasin.
        """
        return (
            self.contract_holds and not self.relaxed and not self.restated and not self.undeclared
        )


def evaluate() -> ApiRequirementsReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi
    (`scope.evaluate`, `success.evaluate`, `glossary.evaluate` bilan bir
    xil sabab).
    """
    return ApiRequirementsReport(
        requirements=REQUIREMENTS,
        inherited=INHERITED_CLAIMS,
        undeclared=UNDECLARED,
    )

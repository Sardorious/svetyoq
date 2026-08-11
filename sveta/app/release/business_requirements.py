"""Biznes talablari (`BRD` §8) ↔ qurilgan mahsulot.

**Nima uchun bu modul bor.** 100-run paketning ikkinchi hujjatini
(`02`) yopdi va BRD ni keyingi nomzod deb qoldirdi. §8 — BRD ning
yadrosi: 28 ta `BR-*` qatori, yetti guruhda, har biri ustuvorlik va
manba bilan. Hujjatning o'z legendasi qat'iy: **High — запуск uchun
bloklovchi**. Ya'ni bu bo'lim shunchaki ro'yxat emas, hujjatning o'z
tili bilan aytganda ishga tushirish shartlari ro'yxati.

Ikki savol, ikkalasi mustaqil:

1. *Qator aytgan narsa repoda quriladimi?* (`Delivered`)
2. *Qatorning asosi — «Источник» katagi — repoda ochiladimi?* (`Warrant`)

## Birinchi topilma: yigirmata High qatordan o'n bittasi yozilganidek qurilmagan

Legend bo'yicha High «блокирует запуск». Bugun 20 ta High qatordan
**11 tasi** `BUILT` emas — hujjatning o'z o'lchovida ishga tushirish
o'n bir marta bloklangan. Bu baho emas, sanoq: `launch_blockers`
xossasi ro'yxatni beradi va test uni ikkala tomondan qulflaydi.

## Ikkinchi topilma: 28 qatordan 17 tasining asosi repoda yo'q hujjatda

«Источник» kataklari o'n xil belgiga tayanadi va ularning yettitasi —
`FR-*`, `C-*`, `R-*`, `UC-*`, `PG-5`, `BR-xx (TAS)`, `RBAC (TAS)` —
BRD §26.1 bo'yicha **yetti meros hujjatiga** yechiladi. Ularning
birortasi ham repoda yo'q. 99-run `01` §31 dan o'nta yo'q hujjatni
o'lchagan edi; BRD §26.1 ro'yxatga **uchta yangisini** qo'shadi
(`13_Risk_Register.md`, `21_Critical_Review.md`,
`svetanet-use-cases.md`) — sinf 10 dan 13 ga o'sdi va bu safar yo'q
hujjatlar shunchaki havola emas, 17 qatorning **asosi**.

## Uchinchi topilma: TTL bo'yicha ikki hujjat teskari gapiradi va kod tomon tanlagan

`BR-014` (va uning egizagi `BRL-04`): «закрывается через **3 ч** после
последнего сообщения». `05` §4.4 esa `autoclose_after` ni **120 daq**
deb qotiradi va kod aynan shuni bajaradi
(`cluster_autoclose_after_min = 120`). CLAUDE.md bo'yicha `05` —
qonun, ya'ni kod to'g'ri joyga qaragan; lekin BRD bilan `05` ning bu
ziddiyati shu paytgacha hech qayerda qayd etilmagan edi. Sonlarning
ikkalasi ham moduldа saqlanadi va test ikkala hujjatdan parse qiladi.

## To'rtinchi topilma: maxfiylik qatori boshqa mexanizm va boshqa son bilan bajarilgan

`BR-025`: «огрубляется до **сетки ~50 м**». Kod esa panjara emas,
deterministik jitter ishlatadi (`blake2b`, `05` §3.1) va uning radiusi
**60 m** (`jitter_max_m = 60`). Niyat bir, mexanizm va son boshqa —
`SUBSTITUTED`, chunki `05` §3.1 shunday buyurgan; BRD ning «сетка»
va «50» so'zlari paketning boshqa joyida uchramaydi.

## Beshinchi topilma: `regional_operator` roli hech qayerda yo'q

`BR-023` (va §6.1 `IS-10`) rolni nomlab chaqiradi, `Role` enumida esa
`viewer`/`moderator`/`admin` bor, geografik skoup umuman yo'q. Manba —
`07_RBAC.md`, ya'ni rol modeli ham yo'q hujjatdan meros. `ABSENT`.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi: TTL o'zgartirilmadi (`05` haq bo'lishi mumkin,
👤 savol), rol qo'shilmadi (E8 dan tashqari ish), obuna oqimga
ulanmadi (98-run topilmasi, alohida qaror). Modul o'lchaydi,
tahrirlamaydi (75–77, 82–87, 99–100 runlar qoidasi).

Modul `app/release/` da yashaydi va `app.*` dan hech narsa import
qilmaydi: reyestr sof e'lon, qurilgan sathni **test** o'lchaydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Hujjat bo'limi. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "BRD §8"

#: `BR-*` qatorlari soni. Hujjatdan parse qilinadi va solishtiriladi.
SPEC_ROWS = 28

#: Yetti kichik bo'lim — hujjatdagi nom va tartibda, qator soni bilan.
GROUP_SIZES: dict[str, int] = {
    "Geography & Territory": 6,
    "Localization": 4,
    "Reporting & Validation": 5,
    "Notification": 3,
    "Analytics & Reporting": 4,
    "Administration & Security": 4,
    "Integration": 2,
}

#: Legend e'lon qilgan ustuvorliklar — aynan.
SPEC_PRIORITIES: tuple[str, ...] = ("High", "Medium", "Low")

#: Legendda bor, jadvalda esa **bironta ham** qator ishlatmaydi.
#: Uchta darajali shkala amalda ikkita: «yaxshilash» sinfi bo'sh.
UNUSED_PRIORITY = "Low"

#: «Источник» katagi belgilarining uylari. `None` — belgi shu BRD ning
#: o'zida ochiladi (§3 `BP-*`, §4 `BG-*`); satr — §26.1 bo'yicha meros
#: hujjat nomi. O'ng ustundagi yettala faylning **birortasi repoda
#: yo'q** — test buni fayl tizimidan o'lchaydi.
SOURCE_HOME: dict[str, str | None] = {
    "BP-2": None,
    "BP-3": None,
    "BP-4": None,
    "BP-5": None,
    "BP-6": None,
    "BP-7": None,
    "BG-5": None,
    "PG-5": "02_PRD.md",
    "UC-1": "svetanet-use-cases.md",
    "UC-3": "svetanet-use-cases.md",
    "UC-4": "svetanet-use-cases.md",
    "FR-304": "03_Functional_Requirements.md",
    "FR-807": "03_Functional_Requirements.md",
    "C-09": "21_Critical_Review.md",
    "C-10": "21_Critical_Review.md",
    "C-11": "21_Critical_Review.md",
    "R-13": "13_Risk_Register.md",
    "R-14": "13_Risk_Register.md",
    "BR-08 (TAS)": "01_BRD.md",
    "BR-10 (TAS)": "01_BRD.md",
    "BR-12 (TAS)": "01_BRD.md",
    "RBAC (TAS)": "07_RBAC.md",
}

#: 99-run (`nfr_appendix.DOCS`) o'lchagan o'nlikdan **tashqaridagi**
#: meros hujjatlari — BRD §26.1 sinfga qo'shgan uchta yangi nom.
NEW_LEGACY_DOCS: frozenset[str] = frozenset(
    {"13_Risk_Register.md", "21_Critical_Review.md", "svetanet-use-cases.md"}
)

#: `BR-014` ning ikki tomoni: hujjat soati va kod daqiqasi.
#: 3 h == 180 min ≠ 120 min — ziddiyat shu ikkala konstantada turadi
#: va test ikkalasini o'z manbasidan (BRD matni, `Settings`) oladi.
DOC_AUTOCLOSE_H = 3
BUILT_AUTOCLOSE_MIN = 120

#: `BR-025` ning ikki tomoni: hujjat panjarasi va kod jitteri.
DOC_GRID_M = 50
BUILT_JITTER_MAX_M = 60

#: `BR-023` chaqirgan va repoda mavjud bo'lmagan rol nomi.
DOC_ROLE = "regional_operator"

#: `BR-005` ning ikki tomoni: hujjat saqlashni so'raydi
#: (`out_of_coverage` maqomi bilan), kod esa rad etadi
#: (`error.out_of_region`, hech narsa yozilmaydi).
DOC_STATUS = "out_of_coverage"
BUILT_ERROR = "out_of_region"


class Delivered(StrEnum):
    """Repo qator aytgan narsa bilan nima qilgan.

    87-run (`01` §8) sinflari + `ABSENT`: BRD kengroq va unda hech
    qanday shaklda qurilmagan qatorlar bor.
    """

    #: Qator aytganidek qurilgan.
    BUILT = "built"
    #: Qatorning bir qismi qurilgan, qolgani yo'q.
    PARTIAL = "partial"
    #: Niyat qurilgan, mexanizm yoki manba qator aytgani emas.
    SUBSTITUTED = "substituted"
    #: Mexanizm to'liq, uni ishga soladigan narsa hech qachon kelmaydi.
    DORMANT = "dormant"
    #: Qurilgan qoida qator aytgan qoida emas.
    FORKED = "forked"
    #: Hech qanday shaklda qurilmagan.
    ABSENT = "absent"


#: «Aytilganidek bajarilgan» — faqat bittasi.
DELIVERED_KEPT: frozenset[Delivered] = frozenset({Delivered.BUILT})


class Warrant(StrEnum):
    """Qatorning «Источник» katagi qayerda ochiladi.

    E'lon qilinmaydi, `SOURCE_HOME` dan **hisoblanadi** — qorovul
    `__post_init__` da qayta sanaydi va mos kelmasa yiqiladi.
    """

    #: Hamma manba shu paketning o'zida ochiladi.
    NATIVE = "native"
    #: Manbalarning bir qismi repoda yo'q hujjatga yechiladi.
    MIXED = "mixed"
    #: Hamma manba repoda yo'q hujjatlarda.
    FOREIGN = "foreign"


class BusinessRequirementsError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class Requirement:
    """§8 ning bitta `BR-*` qatori va uning bugungi bahosi."""

    code: str
    #: Sarlavha — hujjatdagidek, tarjimasiz.
    title: str
    #: Kichik bo'lim nomi (`GROUP_SIZES` kaliti).
    group: str
    #: «Приоритет» katagi — aynan.
    priority: str
    #: «Источник» katagi, vergul bo'yicha bo'lingan — aynan.
    sources: tuple[str, ...]
    delivered: Delivered
    warrant: Warrant
    #: Nima uchun aynan shu baho. Keyingi o'quvchi uchun.
    note: str
    #: Dalil: `modul:simvol` yoki `tests/fayl.py`.
    binds: tuple[str, ...] = ()
    #: Da'vo bilan qurilgan narsa orasidagi farq. `BUILT` da bo'sh
    #: bo'lishi mumkin, qolgan sinflarda majburiy.
    gap: str = ""


def _computed_warrant(sources: tuple[str, ...]) -> Warrant:
    homes = [SOURCE_HOME[s] for s in sources]
    if all(h is None for h in homes):
        return Warrant.NATIVE
    if all(h is not None for h in homes):
        return Warrant.FOREIGN
    return Warrant.MIXED


# --------------------------------------------------------------------------
# Reyestr — BRD §8 qatorlari, hujjatdagi tartibda
# --------------------------------------------------------------------------

REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement(
        code="BR-001",
        title="Трёхуровневая геомодель",
        group="Geography & Territory",
        priority="High",
        sources=("BP-2",),
        delivered=Delivered.PARTIAL,
        warrant=Warrant.NATIVE,
        note=(
            "Uch darajadan ikkitasi jonli: tuman (`district_id`) va H3 "
            "(`h3_r9`) har repartda to'ldiriladi. Uchinchisi — mahalla — "
            "mexanizm sifatida to'liq (`find_mahalla_id`, "
            "`reports.mahalla_id`), lekin `mahallas` jadvali bo'sh va uni "
            "to'ldiradigan yo'l daraxtda yo'q (87-run `F-2` bilan bir dalil)."
        ),
        binds=(
            "app.geo.pipeline:find_mahalla_id",
            "app.reports.models:Report.mahalla_id",
            "app.geo.models:District",
        ),
        gap="«Одновременно» uch darajadan ikkitasida ro'y beradi.",
    ),
    Requirement(
        code="BR-002",
        title="Версионирование границ",
        group="Geography & Territory",
        priority="High",
        sources=("BP-4", "R-14"),
        delivered=Delivered.BUILT,
        warrant=Warrant.MIXED,
        note=(
            "§8 ning eng puxta qurilgan qatori (87-run `F-3` bilan aynan "
            "bir sirt): `valid_from`/`valid_to`, `districts_for_period`, "
            "`?at=` kesimi — hammasi testda yuriladi."
        ),
        binds=(
            "app.geo.queries:districts_for_period",
            "app.stats.boundaries:summarize",
            "tests/test_stats_boundaries.py",
        ),
    ),
    Requirement(
        code="BR-003",
        title="Справочник махаллей",
        group="Geography & Territory",
        priority="High",
        sources=("BP-2", "BP-5"),
        delivered=Delivered.DORMANT,
        warrant=Warrant.NATIVE,
        note=(
            "Jadval, model, API (`GET /geo/mahallas`) va biriktirish bor; "
            "poligonlarni **yuklaydigan** kod yo'q — "
            "`tools/import_boundaries.py` da `mahalla` so'zi bir marta ham "
            "uchramaydi. Ustiga `name_ru` bu jadvalda `NULL` bo'la oladi, "
            "ya'ni «UZ/RU nomlar» talabi sxemaning o'zida ham yarim."
        ),
        binds=(
            "app.geo.mahallas",
            "app.geo.models:Mahalla",
            "tests/test_schema_spatial_nullability.py",
        ),
        gap="Ma'lumot yo'li yozilmagan (E17, 👤 poligonlar).",
    ),
    Requirement(
        code="BR-004",
        title="Полигон зоны покрытия",
        group="Geography & Territory",
        priority="High",
        sources=("FR-807",),
        delivered=Delivered.SUBSTITUTED,
        warrant=Warrant.FOREIGN,
        note=(
            "Qator **poligon** so'raydi, qurilgani — to'rtburchak bbox "
            "(`regions.bbox_*`, `BBox.contains`). Ustiga bbox siz yagona "
            "faol mintaqa **butun dunyoni** qamraydi (E19 gacha "
            "moslik istisnosi) — «явно заданная область» dan yiroq."
        ),
        binds=(
            "app.geo.bbox:make_bbox",
            "app.geo.registry:pick_for_point",
            "app.geo.models:Region.bbox_min_lat",
        ),
        gap="Poligon o'rniga bbox; bbox sizlik alohida teshik.",
    ),
    Requirement(
        code="BR-005",
        title="Отказ вне покрытия",
        group="Geography & Territory",
        priority="Medium",
        sources=("FR-304",),
        delivered=Delivered.FORKED,
        warrant=Warrant.FOREIGN,
        note=(
            "Qator repartni **saqlashni** buyuradi (maqom bilan), kod esa "
            "**rad etadi**: `error.out_of_region` xatosi, bazaga hech "
            "narsa yozilmaydi. Tushunarli xabar bor (i18n, UZ+RU), saqlash "
            "yo'q — maqomning o'zi ham sxemada mavjud emas."
        ),
        binds=(
            "app.core.errors:OutOfRegionError",
            "app.bot.handlers:on_location",
        ),
        gap="«Сохраняется как ...» o'rniga «rad etiladi»; maqom sxemada yo'q.",
    ),
    Requirement(
        code="BR-006",
        title="Конфигурируемое разрешение H3",
        group="Geography & Territory",
        priority="Medium",
        sources=("BP-2",),
        delivered=Delivered.FORKED,
        warrant=Warrant.NATIVE,
        note=(
            "Qator rezolyutsiyani **mintaqa darajasida** so'raydi. Kodda u "
            "global sozlama (`h3_resolution = 9`), `regions` da ustun "
            "yo'q, `reports.h3_r9` **ustun nomi** esa uni sxemada qotiradi "
            "va ikkita test literalni qulflaydi — 87-run `F-4` ning "
            "`HARDENED` topilmasi bilan aynan bir sirt."
        ),
        binds=(
            "app.core.config:Settings.h3_resolution",
            "app.reports.models:Report.h3_r9",
        ),
        gap="Mintaqaviy emas, global; sozlama emas, sxema.",
    ),
    Requirement(
        code="BR-007",
        title="UZ по умолчанию",
        group="Localization",
        priority="High",
        sources=("BP-3",),
        delivered=Delivered.BUILT,
        warrant=Warrant.NATIVE,
        note=(
            "`DEFAULT_LANGUAGE = 'uz'` va `regions.default_language` "
            "(`server_default='uz'`). Nozik joyi 87-run `F-5` da: birinchi "
            "ekran mintaqani bila olmaydi (`/start` da koordinata yo'q), "
            "standart esa mintaqadan qat'i nazar ishlaydi — natija BRD "
            "so'raganiga mos, sabab esa boshqa."
        ),
        binds=(
            "app.core.i18n:DEFAULT_LANGUAGE",
            "app.geo.models:Region.default_language",
        ),
    ),
    Requirement(
        code="BR-008",
        title="Переключение языка",
        group="Localization",
        priority="High",
        sources=("BP-3",),
        delivered=Delivered.BUILT,
        warrant=Warrant.NATIVE,
        note=(
            "Bir qadam (bot tugmasi), tanlov `users.language` da "
            "saqlanadi (`choose_language`), keyingi seanslarda o'qiladi."
        ),
        binds=(
            "app.bot.service:choose_language",
            "tests/test_language_contract.py",
        ),
    ),
    Requirement(
        code="BR-009",
        title="Двуязычные топонимы",
        group="Localization",
        priority="High",
        sources=("BP-5",),
        delivered=Delivered.PARTIAL,
        warrant=Warrant.NATIVE,
        note=(
            "Nomlar yarmi bor: tumanlarda `name_uz`/`name_ru` ikkalasi "
            "`NOT NULL`, mahallalarda `name_ru` `NULL` bo'la oladi, "
            "ko'chalar esa sxemada umuman yo'q. «Поиск работает по "
            "любому» qismi esa butunlay yo'q: toponim qidiruvining "
            "birorta sirti (endpoint, handler) repoda mavjud emas."
        ),
        binds=(
            "app.geo.models:District.name_ru",
            "app.geo.models:Mahalla.name_ru",
        ),
        gap="Qidiruv yo'q; ko'chalar yo'q; mahalla RU nomi majburiy emas.",
    ),
    Requirement(
        code="BR-010",
        title="Языковой паритет контента",
        group="Localization",
        priority="Medium",
        sources=("PG-5",),
        delivered=Delivered.BUILT,
        warrant=Warrant.FOREIGN,
        note=(
            "i18n kontrakt testlari katalog paritetini ikkala yo'nalishda "
            "qulflaydi (UZ↔RU), qattiq kodlangan matn bloklovchi defekt "
            "(CLAUDE.md). 96-run til driftini tuzatgan — sinf jonli, "
            "qorovullar ham."
        ),
        binds=(
            "tests/test_i18n_key_contract.py",
            "app.core.i18n:t",
        ),
    ),
    Requirement(
        code="BR-011",
        title="Приём репорта по геолокации",
        group="Reporting & Validation",
        priority="High",
        sources=("UC-1",),
        delivered=Delivered.BUILT,
        warrant=Warrant.FOREIGN,
        note=(
            "«Как в Ташкенте»: tugma, geolokatsiya, avtomatik biriktirish "
            "— intake quvuri qurilgan va DB testlari bilan yuriladi."
        ),
        binds=(
            "app.reports.intake:create_report",
            "tests/test_bot_flow_db.py",
        ),
    ),
    Requirement(
        code="BR-012",
        title="Региональные параметры валидации",
        group="Reporting & Validation",
        priority="High",
        sources=("BP-2", "C-10"),
        delivered=Delivered.BUILT,
        warrant=Warrant.MIXED,
        note=(
            "`06` §9 bo'yicha hamma qiymat `region_config` da mintaqa "
            "kesimida (`confirm.min_users`, radius, oyna), standartlar "
            "modul lug'atida."
        ),
        binds=(
            "app.clustering.params:from_mapping",
            "tests/test_confirm_params_contract.py",
        ),
    ),
    Requirement(
        code="BR-013",
        title="Порог публикации карты",
        group="Reporting & Validation",
        priority="High",
        sources=("BP-7",),
        delivered=Delivered.SUBSTITUTED,
        warrant=Warrant.NATIVE,
        note=(
            "Qator **darvoza** so'raydi: zichlikka yetmaguncha karta "
            "yoqilmaydi. Qurilgani — **ogohlantirish**: karta har doim "
            "chiqadi, yosh mintaqa pometasi (`maturity`) va Coverage "
            "Index yoniga qo'shiladi. Snapshot yo'lida zichlik sharti "
            "yo'q. Hujjatning o'zi ham qiymatni bilmaydi: §26.4 `OQ-5` "
            "«порог публикации — конкретное значение» ochiq savol."
        ),
        binds=(
            "app.clustering.snapshot:build_payload",
            "app.stats.maturity:compute",
        ),
        gap="Darvoza o'rniga dislaymer; chegara qiymati hujjatda ham yo'q.",
    ),
    Requirement(
        code="BR-014",
        title="Автозакрытие по TTL",
        group="Reporting & Validation",
        priority="High",
        sources=("UC-3",),
        delivered=Delivered.FORKED,
        warrant=Warrant.FOREIGN,
        note=(
            "Mexanizm bor va to'g'ri ishlaydi (`autoclose` → `resolved`), "
            "lekin son boshqa: qator (va `BRL-04`) **3 soat** deydi, `05` "
            "§4.4 esa **120 daqiqa** qotiradi va kod `05` ga ergashadi "
            "(`cluster_autoclose_after_min = 120`). Ikki hujjat bitta "
            "raqam haqida teskari gapiradi — 👤 savol; CLAUDE.md bo'yicha "
            "`05` qonun, ya'ni bugun kod emas, hujjatlar kelishmagan."
        ),
        binds=(
            "app.clustering.status:evaluate_status",
            "app.core.config:Settings.cluster_autoclose_after_min",
        ),
        gap="3 h (BRD) ≠ 120 min (`05` + kod).",
    ),
    Requirement(
        code="BR-015",
        title="Разделение слоёв",
        group="Reporting & Validation",
        priority="High",
        sources=("BR-08 (TAS)",),
        delivered=Delivered.BUILT,
        warrant=Warrant.FOREIGN,
        note=(
            "`layer = 'official'` alohida qoida bilan (`sources` "
            "reyestri), vebda alohida qatlam (`outage-official-core`), "
            "metrikalarda aralashmaydi."
        ),
        binds=(
            "app.reports.sources:SOURCES",
            "tests/test_report_sources_contract.py",
        ),
    ),
    Requirement(
        code="BR-016",
        title="Подписка на адрес",
        group="Notification",
        priority="High",
        sources=("UC-4",),
        delivered=Delivered.DORMANT,
        warrant=Warrant.FOREIGN,
        note=(
            "Butun mexanizm tayyor (obuna, outbox, renderer, sender) va "
            "**oqimga ulanmagan**: 98-run o'lchaganidek, verdiktdan keyin "
            "`on_location` obunani hech qachon taklif qilmaydi (`L→N`, "
            "`M→N` yoylari o'lik). Ustiga «адрес» amalda **nuqta + "
            "radius**: geokoder yo'q, manzil kiritish yo'li yo'q."
        ),
        binds=(
            "app.notifications.subscriptions:list_for_user",
            "tests/test_bot_subscription_keyboard.py",
        ),
        gap="Taklif oqimda yo'q; manzil o'rniga nuqta.",
    ),
    Requirement(
        code="BR-017",
        title="Региональный радиус уведомлений",
        group="Notification",
        priority="Medium",
        sources=("BP-2",),
        delivered=Delivered.BUILT,
        warrant=Warrant.NATIVE,
        note=(
            "`notify.default_radius_m` / `notify.max_radius_m` — "
            "`region_config` kalitlari, global konstanta emas (43/74-run)."
        ),
        binds=(
            "app.notifications.params:from_mapping",
            "tests/test_notify_params.py",
        ),
    ),
    Requirement(
        code="BR-018",
        title="Подписка на махаллю",
        group="Notification",
        priority="Medium",
        sources=("BP-2",),
        delivered=Delivered.ABSENT,
        warrant=Warrant.NATIVE,
        note=(
            "Obuna faqat nuqta + radius shaklida mavjud; hududga "
            "(mahalla, tuman) obuna bo'ladigan birorta sirt — jadval "
            "ustuni, handler, endpoint — repoda yo'q."
        ),
        binds=("app.notifications.models:Subscription",),
        gap="Hududiy obuna umuman qurilmagan.",
    ),
    Requirement(
        code="BR-019",
        title="Витрина по махаллям",
        group="Analytics & Reporting",
        priority="Medium",
        sources=("BG-5",),
        delivered=Delivered.DORMANT,
        warrant=Warrant.NATIVE,
        note=(
            "`mahalla_coverage` hisoblagichi va API bor; `mahallas` bo'sh "
            "bo'lgani uchun vitrina hech qachon ma'lumot ko'rmaydi — "
            "`BR-003` bilan bitta ildiz."
        ),
        binds=(
            "app.stats.mahalla_coverage",
            "tests/test_stats_mahalla_coverage.py",
        ),
        gap="Ma'lumot keladigan yo'l yo'q (E17).",
    ),
    Requirement(
        code="BR-020",
        title="Coverage Index региона",
        group="Analytics & Reporting",
        priority="High",
        sources=("BP-7", "C-11"),
        delivered=Delivered.BUILT,
        warrant=Warrant.MIXED,
        note=(
            "Indeks hisoblanadi, past zichlik ogohlantirishi vitrinada va "
            "issiqlik xaritasida (`sufficient` bayrog'i), `01` §23 qabul "
            "mezoni sifatida talab qiladi."
        ),
        binds=(
            "app.stats.coverage:compute",
            "tests/test_stats_coverage.py",
        ),
    ),
    Requirement(
        code="BR-021",
        title="Дисклеймер о статусе данных",
        group="Analytics & Reporting",
        priority="High",
        sources=("BR-12 (TAS)",),
        delivered=Delivered.BUILT,
        warrant=Warrant.FOREIGN,
        note=(
            "Yosh mintaqa pometasi (`maturity`), metodologiya sahifasi va "
            "«sообщения жителей» dislaymeri vitrinalarda; i18n orqali "
            "ikkala tilda."
        ),
        binds=(
            "app.stats.maturity:compute",
            "app.stats.methodology",
        ),
    ),
    Requirement(
        code="BR-022",
        title="Запрет межрегионального сравнения без нормализации",
        group="Analytics & Reporting",
        priority="High",
        sources=("C-11",),
        delivered=Delivered.ABSENT,
        warrant=Warrant.FOREIGN,
        note=(
            "Taqiqni bajaradigan ham, buzadigan ham sirt yo'q: har "
            "vitrina bitta mintaqa bilan chegaralangan (API `region` "
            "talab qiladi), solishtirish funksiyasi umuman qurilmagan. "
            "Qoida **bo'shliqqa tegmay** o'tadi — solishtirish paydo "
            "bo'lgan kuni uni hech narsa to'sib turmaydi."
        ),
        binds=("app.stats.service",),
        gap="Taqiq mexanizmsiz: sirt yo'qligi hisobiga «bajarilgan».",
    ),
    Requirement(
        code="BR-023",
        title="Региональный скоуп ролей",
        group="Administration & Security",
        priority="High",
        sources=("RBAC (TAS)",),
        delivered=Delivered.ABSENT,
        warrant=Warrant.FOREIGN,
        note=(
            "Rol modeli uch a'zoli (`viewer`, `moderator`, `admin`) va global — "
            "qator nomlagan rol ham, geografik chegara ham repoda yo'q. "
            "Meros manbasi (`07_RBAC.md`) ham yo'q, ya'ni model nimadan "
            "meros bo'lishi kerakligi ham noma'lum."
        ),
        binds=("app.admin.roles:Role",),
        gap="Rol yo'q, skoup yo'q, manba hujjat yo'q.",
    ),
    Requirement(
        code="BR-024",
        title="Аудит привилегированных действий",
        group="Administration & Security",
        priority="High",
        sources=("RBAC (TAS)",),
        delivered=Delivered.BUILT,
        warrant=Warrant.FOREIGN,
        note=(
            "Admin amallari va mintaqaviy spravochnik o'zgarishlari "
            "jurnalga yoziladi (`REGION_UPDATE`, 80-run `region_audit`); "
            "yozuvni o'zgartiradigan yoki o'chiradigan yo'l kodda yo'q — "
            "lekin «неизменяемо» faqat konventsiya, DB darajasida qulf "
            "(trigger, `REVOKE`) yo'q."
        ),
        binds=(
            "app.admin.audit:AuditAction",
            "tests/test_region_audit_db.py",
        ),
    ),
    Requirement(
        code="BR-025",
        title="Приватность точки",
        group="Administration & Security",
        priority="High",
        sources=("BR-10 (TAS)",),
        delivered=Delivered.SUBSTITUTED,
        warrant=Warrant.FOREIGN,
        note=(
            "Niyat bajarilgan, mexanizm boshqa: qator **~50 m panjara** "
            "so'raydi, kod esa deterministik jitter beradi (`blake2b`, "
            "radius ≤ **60 m**, `05` §3.1). `geom_exact` hech qanday "
            "javobda chiqmaydi (60-run kontrakti) — maxfiylik o'zi "
            "himoyada, lekin usul ham, son ham BRD niki emas."
        ),
        binds=(
            "app.geo.jitter:public_point",
            "tests/test_privacy_jitter_contract.py",
        ),
        gap="Panjara o'rniga jitter; 50 o'rniga 60.",
    ),
    Requirement(
        code="BR-026",
        title="Локализация хранения ПДн",
        group="Administration & Security",
        priority="High",
        sources=("C-09", "R-14"),
        delivered=Delivered.ABSENT,
        warrant=Warrant.FOREIGN,
        note=(
            "Talabning o'zi tekshirilmagan gipoteza (BRD §15 buni ochiq "
            "yozadi) va kodda hech qanday izi yo'q; `security.py` `C-09` "
            "ni 👤 maqomida ko'taradi (71/99-runlar). Yuridik xulosasiz "
            "bu qator o'lchanmaydi ham."
        ),
        binds=("app.admin.security:GUARANTEES",),
        gap="Yuridik tekshiruv yo'q (D-08, 👤); kod sirti ham yo'q.",
    ),
    Requirement(
        code="BR-027",
        title="Региональный официальный слой",
        group="Integration",
        priority="Medium",
        sources=("BP-6",),
        delivered=Delivered.DORMANT,
        warrant=Warrant.NATIVE,
        note=(
            "Qatlam mexanizmi tayyor (`official` manba qoidasi, alohida "
            "veb-qatlam), **parser yo'q** (E18 boshlanmagan) va manba "
            "identifikatsiya qilinmagan (BP-6 ning o'zi, H-4 👤). Qator "
            "o'zi shartli («при наличии») — mexanizm shartni kutmoqda."
        ),
        binds=(
            "app.reports.sources:SOURCES",
            "app.integrations.registry",
        ),
        gap="Parser va manba yo'q; qatlam bo'sh turibdi.",
    ),
    Requirement(
        code="BR-028",
        title="Геокодер региона",
        group="Integration",
        priority="Medium",
        sources=("BP-5", "R-13"),
        delivered=Delivered.PARTIAL,
        warrant=Warrant.MIXED,
        note=(
            "Qatorning «degradatsiya» yarmi — qo'lda nuqta tanlash — "
            "mahsulotning yagona yo'li bo'lib qurilgan; asosiy yarmi "
            "(manzil → koordinata) esa yo'q: sozlamalar bor, chaqiruv "
            "joyi yo'q (69-rundan beri to'qqiz reyestr o'lchagan sinf)."
        ),
        binds=(
            "app.core.config:Settings",
            "app.integrations.registry",
        ),
        gap="Faqat zaxira yo'l qurilgan; asosiy mexanizm yo'q.",
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessRequirementsReport:
    """BRD §8 ning bugungi holati."""

    requirements: tuple[Requirement, ...]

    def __post_init__(self) -> None:
        codes = [r.code for r in self.requirements]
        expected = [f"BR-{i:03d}" for i in range(1, SPEC_ROWS + 1)]
        if codes != expected:
            raise BusinessRequirementsError("kodlar BR-001…BR-028 emas yoki tartib buzilgan")
        for req in self.requirements:
            if req.group not in GROUP_SIZES:
                raise BusinessRequirementsError(f"{req.code}: noma'lum guruh {req.group!r}")
            if req.priority not in SPEC_PRIORITIES:
                raise BusinessRequirementsError(f"{req.code}: noma'lum ustuvorlik {req.priority!r}")
            if req.priority == UNUSED_PRIORITY:
                raise BusinessRequirementsError(
                    f"{req.code}: {UNUSED_PRIORITY!r} hujjatda e'lon qilingan, "
                    "lekin bironta qator ishlatmaydi — paydo bo'lsa hujjat o'zgargan"
                )
            if not req.sources:
                raise BusinessRequirementsError(f"{req.code}: manba katagi bo'sh")
            unknown = [s for s in req.sources if s not in SOURCE_HOME]
            if unknown:
                raise BusinessRequirementsError(f"{req.code}: uyi yo'q manba {unknown}")
            if req.warrant is not _computed_warrant(req.sources):
                raise BusinessRequirementsError(
                    f"{req.code}: warrant e'lon qilingan qiymati hisoblanganiga teng emas"
                )
            if not isinstance(req.binds, tuple):
                raise BusinessRequirementsError(f"{req.code}: `binds` kortej emas")
            if any(not isinstance(b, str) or "." not in b for b in req.binds):
                raise BusinessRequirementsError(f"{req.code}: `binds` shakli buzilgan")
            if req.delivered is Delivered.BUILT and not req.binds:
                raise BusinessRequirementsError(f"{req.code}: `BUILT` dalilsiz bo'lmaydi")
            if req.delivered not in DELIVERED_KEPT and not req.gap:
                raise BusinessRequirementsError(f"{req.code}: farq bor, `gap` yozilmagan")
        for group, size in GROUP_SIZES.items():
            actual = sum(1 for r in self.requirements if r.group == group)
            if actual != size:
                raise BusinessRequirementsError(f"{group}: {actual} qator, hujjatda {size}")

    @property
    def by_delivered(self) -> dict[Delivered, tuple[str, ...]]:
        result: dict[Delivered, list[str]] = {d: [] for d in Delivered}
        for req in self.requirements:
            result[req.delivered].append(req.code)
        return {d: tuple(codes) for d, codes in result.items()}

    @property
    def by_group(self) -> dict[str, tuple[str, ...]]:
        result: dict[str, list[str]] = {g: [] for g in GROUP_SIZES}
        for req in self.requirements:
            result[req.group].append(req.code)
        return {g: tuple(codes) for g, codes in result.items()}

    @property
    def by_priority(self) -> dict[str, tuple[str, ...]]:
        result: dict[str, list[str]] = {p: [] for p in SPEC_PRIORITIES}
        for req in self.requirements:
            result[req.priority].append(req.code)
        return {p: tuple(codes) for p, codes in result.items()}

    @property
    def launch_blockers(self) -> tuple[Requirement, ...]:
        """Hujjatning o'z legendasi bo'yicha ishga tushirishni to'sadiganlar.

        Legend: «High — блокирует запуск». Ya'ni High **va** yozilganidek
        qurilmagan har qator — hujjatning o'z tili bilan bloklovchi.
        Bugun 20 High qatordan 11 tasi shu yerda.
        """
        return tuple(
            r
            for r in self.requirements
            if r.priority == "High" and r.delivered not in DELIVERED_KEPT
        )

    @property
    def foreign_warranted(self) -> tuple[Requirement, ...]:
        """Asosi (qisman bo'lsa ham) repoda yo'q hujjatda yotganlar."""
        return tuple(r for r in self.requirements if r.warrant is not Warrant.NATIVE)

    @property
    def missing_docs(self) -> frozenset[str]:
        """Manba kataklari yechiladigan meros hujjatlari to'plami.

        Hisoblanadi — `SOURCE_HOME` ning `None` bo'lmagan qiymatlari
        ichidan faqat reyestr haqiqatan ishlatganlari.
        """
        return frozenset(
            home
            for r in self.requirements
            for s in r.sources
            if (home := SOURCE_HOME[s]) is not None
        )

    @property
    def mahalla_blocked(self) -> tuple[Requirement, ...]:
        """Bo'sh `mahallas` hal qiladigan qatorlar (87-run bilan bir usul)."""
        return tuple(
            r for r in self.requirements if any("mahalla" in b.lower() for b in r.binds)
        )

    @property
    def vacuously_honored(self) -> tuple[Requirement, ...]:
        """Bajaradigan sirt ham, buzadigan sirt ham yo'q qoidalar.

        Ular `ABSENT`, lekin oddiy `ABSENT` dan farq qiladi: bugun hech
        narsa buzilmayapti, sirt paydo bo'lgan kuni esa taqiqni hech
        narsa ushlab turmaydi.
        """
        return tuple(
            r
            for r in self.requirements
            if r.delivered is Delivered.ABSENT and "sirt yo'qligi" in r.gap
        )

    @property
    def delivered_hold(self) -> bool:
        """Har qator aytganidek qurilganmi. Bugun `False`: 28 dan 17 tasi emas."""
        return all(r.delivered in DELIVERED_KEPT for r in self.requirements)

    @property
    def warrants_hold(self) -> bool:
        """Har qatorning asosi repoda ochiladimi. Bugun `False`: 17 tasi ochilmaydi."""
        return not self.foreign_warranted

    @property
    def accurate(self) -> bool:
        """§8 «qurilgan» deb o'qilsa rostmi.

        Ikki shart, ikkalasi mustaqil o'lchanadi: qatorlar aytilganidek
        qurilgan bo'lsin va ularning asoslari repoda ochilsin.
        """
        return self.delivered_hold and self.warrants_hold


def evaluate() -> BusinessRequirementsReport:
    """Reyestrdan to'liq hisobot. Argument yo'q — 85–87, 99–100 runlar qoidasi."""
    return BusinessRequirementsReport(requirements=REQUIREMENTS)

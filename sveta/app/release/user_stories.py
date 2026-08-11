"""Foydalanuvchi hikoyalari (`01` §9) va stsenariylari (`01` §10) ↔ qurilgan mahsulot.

**Nima uchun bu modul bor.** 87-run uchta nomzod qoldirdi va §9/§10 ni
birinchi qatorga qo'ydi: «`Witness` o'qi tayyor va ular ham `AC` ga
o'xshash shaklda yozilgan». Bu to'g'ri chiqdi, lekin sabab boshqa
bo'lib chiqdi.

§8 ning `AC` si qatorning **ichida** turadi va o'sha qatorning o'zini
tekshiradi. §9 ning gherkin bloki esa **butun mahsulotni** tekshiradi:
`US-S2` ning `Then` i bitta funksiyani emas, foydalanuvchi ekranidagi
**sonni** nomlaydi. Shuning uchun §9 §8 dan qiyinroq — bo'lim yolg'on
bo'lsa, buni faqat ekranga qarab bilish mumkin, kod esa har joyda
to'g'ri ko'rinadi.

## Nega o'lchov birligi hikoya emas, **band**

Bitta `Then`/`And` bandi bitta va'da. Hikoya darajasidagi hukm ularni
o'rtachalab yuboradi va aynan eng qimmatli farqni yashiradi: `US-S5` da
bitta qatorda **ikkala** uchi ham bor — nomlangan va bajarilgan yarim
(chegaralar versiyasi) va nomlanmagan, almashtirilgan va bugun bo'sh
yarim (mahalla indeksi).

⚠️ Va bitta band ham har doim bitta hukmga sig'avermaydi: `US-S2` ning
birinchi `Then` i botning **ikkita** yo'lida ikkita **har xil** son
bilan bajariladi. Shuning uchun reyestrning kaliti — band emas, `va'da
× yo'l` juftligi (`promise`), va bir va'daning bir nechta bandi
bo'lishi `split_promises` da **hisoblanadi**, e'lon qilinmaydi.

## Uch o'q

1. *Va'da qurilganmi va aynan va'da qilinganidek qurilganmi?*
   (`Realized`)
2. *`Given` bugun umuman ro'y bera oladimi?* (`Reachable`)
3. *Repo bu bandni nom bilan taniydimi?* (`Named`)

Uchalasi mustaqil. `Then` mukammal qurilgan bo'lishi mumkin, lekin
uning `Given` i hech qachon ro'y bermasa, band hech qachon
tekshirilmaydi va hisobotda «bajarildi» deb ko'rinadi (§8 ning
`Witness.VACUOUS` i, boshqa tomondan).

## Asosiy topilma: va'da qilingan son bazada bor, ekranda esa boshqasi turadi

`US-S2` ning `AC` si «вердикт с числом **независимых** сообщений
**рядом** за **последний час**» deydi va uchala sifatlovchi ham
loyihada ta'riflangan:

* «независимых» — `05` §4.3 ning aniq ta'rifi
  (`COUNT(DISTINCT user_id)` + bloklanmagan + `trust_score` + akkaunt
  yoshi + minimal masofa), `count_independent` funksiyasi va
  `outages.independent_reporters` ustuni;
* «рядом» — klaster radiusi (`outages.radius_m`);
* «за последний час» — `06` §3 ning oynasi.

Bot javobi esa uchtasining **birortasini** ishlatmaydi: `CONFIRMED` da
`total_reports` (= biriktirilgan **xabarlar** soni, o'zining xabari ham
ichida, oyna — hodisaning butun umri), `PENDING` da `others`
(= `total - 1`). Ya'ni bitta va'da ikkita har xil sonni ko'rsatadi va
ikkalasi ham «mustaqil» emas. Hodisa `autoclose_after` gacha yashaydi,
demak «за последний час» oshirib ko'rsatishi mumkin.

⚠️ **Nega bu shunchaki xato emas:** to'g'ri son **bir maydon narida**
turibdi — `_situation` allaqachon `cluster_repo.get(...)` bilan
hodisani oladi va `independent_reporters` o'sha obyektda. Tanlov ongli
ko'rinadi, tanlov ekani esa na `05` §6.2 da, na `reply.py` da
yozilgan.

## Ikkinchi topilma: ziddiyat ikkala tomon ham to'g'ri bo'lganda ro'y beradi

`US-S2` ning ikkinchi yarmi: «если сообщений рядом нет, вердикт явно
сообщает, что данных недостаточно, **а не что аварии нет**».

`decide()` esa boshqa o'q bo'yicha bo'linadi — `coverage_ok` bo'lsa
`NO_OUTAGE_COVERED`, ya'ni aynan taqiqlangan gap. Bu E7 ning butun
mazmuni va u **asosli**: «qamrov bor + xabar yo'q» = «svet bor» degan
xulosa qonuniy. Lekin §9 uni taqiqlaydi, chunki §9 faqat xabarlar
sonini biladi va qamrov degan tushunchani umuman ko'rmaydi —
`05` §6.2 ning to'rtta verdiktidan ikkitasini biladi.

⚠️ Ikkala tomon ham **o'z ichida izchil** va ikkalasining ham testi
yashil, shuning uchun nomuvofiqlik hech qayerdan ko'rinmaydi.

## Uchinchi topilma: bir paket bitta bajarilmaydigan shartni ikki marta yozgan

`US-S1` ning `Given` i — «новый пользователь **с геолокацией**…
выполняет `/start`». 87-run buni `FR-S-601` uchun o'lchagan: `/start`
bilan koordinata kelmaydi. §9 o'sha shartni **so'zma-so'z**
takrorlaydi.

⚠️ 86-run ning «takrorlanish xatoni himoyalaydi» mexanizmi **uchinchi
marta**, endi bitta faylning §8 va §9 bo'limlari orasida — topish
uchun tashqi manba kerak emas edi.

## To'rtinchi topilma: repo to'qqizta banddan **bittasini** nomlaydi

Va u eng past prioritetli hikoyaning oson yarmi. `P0` ning ikkala
hikoyasi ham, `P1` niki ham — nomsiz. Nomlangani esa `P2` ning
chegaralar versiyasi haqidagi bandi.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi. Bot ko'rsatadigan son almashtirilmadi (bu
`05` §6.2 ning matniga va ikkita i18n satriga tegadi — 👤 qaror),
`NO_OUTAGE_COVERED` olib tashlanmadi (E7 ning mantig'i asosli),
mahallani tanlash yo'li qo'shilmadi (poligonlar yo'q). Modul
o'lchaydi, tahrirlamaydi (75–77, 82–87 runlar bilan bir xil qoida).

Modul `app/release/` da yashaydi — `scope`, `roadmap`, `success`,
`risks`, `functional_requirements` bilan bir joyda — va `app.*` dan
hech narsa import qilmaydi: reyestr sof e'lon, qurilgan sathni
**test** o'lchaydi (`ast`, i18n katalogi va paketning boshqa
hujjatlari orqali).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Hujjat bo'limlari. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "01 §9/§10"

#: §9 dagi hikoyalar soni — `US-S*` sarlavhalari. Hujjatdan parse
#: qilinadi va reyestr bilan solishtiriladi.
SPEC_STORIES = 5

#: Ulardan nechtasi gherkin bloki bilan yozilgan. `US-S4` da blok
#: **yo'q** — bu yagona hikoya bo'lib, uning bajarilishi haqida hujjat
#: hech narsa da'vo qilmaydi.
SPEC_GHERKIN_STORIES = 4

#: `Then`/`And` bandlari uchun reyestr qatorlari soni. Hujjatda sakkiz
#: band bor; to'qqizinchi qator — `US-S2` ning birinchi bandining
#: **ikkinchi yo'li** (`PENDING`), chunki u boshqa sonni ko'rsatadi.
SPEC_CLAUSES = 9

#: §10 dagi stsenariylar soni — `UC-S*` sarlavhalari.
SPEC_USE_CASES = 3

#: `US-S4` — gherkin bloki yozilmagan yagona hikoya.
STORY_WITHOUT_GHERKIN = "US-S4"

#: §9/§10 ning bandlari ko'taradigan katak nomlari — birlashma.
#: Bitta stsenariy hammasini ko'tarmaydi.
SPEC_FIELDS: tuple[str, ...] = (
    "Участники",
    "Предусловия",
    "Основной сценарий",
    "Альтернативный",
    "Ошибки",
    "Результат",
)

#: `US-S2` ning `AC` si talab qiladigan son va uning `05` §4.3 dagi
#: ta'rifi. Ustun ham, funksiya ham repoda bor.
PROMISED_COUNT_COLUMN = "independent_reporters"
PROMISED_COUNT_FUNCTION = "count_independent"

#: Ekranda haqiqatan turadigan ikkita son — `Situation` ning
#: maydonlari. Ikkalasi ham xabarlar soni, ikkalasi ham «mustaqil»
#: emas va ikkalasi ham bir-biriga teng emas.
SHOWN_COUNT_FIELDS: tuple[str, ...] = ("total_reports", "others")

#: Va'da qilingan oyna. Hodisa esa `autoclose_after` gacha yashaydi,
#: ya'ni ko'rsatilgan son undan uzun davrni qamrashi mumkin.
PROMISED_WINDOW_HOURS = 1

#: `US-S2` ning ikkinchi bandi taqiqlagan verdikt va uning o'rniga
#: talab qilingani — ikkalasi ham `05` §6.2 jadvalining qatori.
FORBIDDEN_VERDICT = "no_outage_covered"
REQUIRED_VERDICT = "not_enough_data"

#: §9 ko'radigan verdiktlar soni va `05` §6.2 da yozilganlari.
#: Bo'limlar orasidagi bo'shliq shu ikki sonda ko'rinadi.
VERDICTS_KNOWN_TO_SECTION_9 = 2
VERDICTS_IN_SPEC = 4

#: `US-S1` ning ikkinchi bandi talab qiladigan yo'l va repodagi
#: haqiqiy komandalar soni. Til almashtirish komanda emas — ikki
#: qadamli tugma yo'li.
BOT_COMMANDS = 2
LANGUAGE_SWITCH_STEPS = 2

#: `UC-S1` ning «Ошибки» katagi nomlagan kodlar — hujjatdagi yozilishi
#: bilan. Ular **da'vo**, artefakt emas: birinchisi kodda boshqacha
#: ataladi, ikkinchisi umuman qurilmagan.
#:
#: ⚠️ Bu yerda ular satr sifatida turishi kerak, chunki reyestr aynan
#: hujjatning so'zini qayd etadi. Koddagi nomni test `errors.py` ning
#: sinf atributlaridan `ast` bilan oladi — matn qidirmaydi (86-run ning
#: qoidasi: yozilgan kod qidirilayotgan kodga aylanadi).
DOC_ERROR_CODES: tuple[str, ...] = ("GEO_OUT_OF_COVERAGE", "GEOCODER_UNAVAILABLE")

#: Birinchisining koddagi nomi. 86-run ning `region_id` → `region`
#: renomi bilan bir xil shakl: mexanizm bor, nomi boshqa.
BUILT_ERROR_CODE = "out_of_region"

#: `US-S5` ning bajarilgan yarmi repoda nomlangan joylar. Ro'yxat
#: `ast`/matn bilan qayta hisoblanadi va tenglik talab qilinadi.
CITATION_SITES: tuple[str, ...] = (
    "app/stats/export.py",
    "tests/test_stats_export.py",
    "tests/test_stats_api_db.py",
)

#: `UC-S2` ni nomlaydigan yagona joy — 70-run ning qabul mezoni.
#: ⚠️ 88-run gacha u **`UC-S3`** deb yozilgan edi; ibora esa `UC-S2`
#: niki va `UC-S3` da beshinchi qadam umuman yo'q. `MISCITED` sinfi
#: shuning uchun saqlanadi: xato tuzatildi, shakl qaytishi mumkin.
USE_CASE_CITATION_SITE = "app/release/acceptance.py"

#: `UC-S2` ning oqimidagi qadamlar soni va ulardan nechtasi qurilgan
#: mexanizmga tayanadi. Qolgan ikkitasi (`coverage_zones` ni faollash
#: va nazorat namunasi) mavjud bo'lmagan narsaga tayanadi.
USE_CASE_2_STEPS = 5
USE_CASE_2_STEPS_BUILT = 3

#: `UC-S3` ning oqimidagi qadamlar soni. `UC-S2` dan farqli o'laroq
#: unda beshinchi qadam yo'q — 88-run ning havola xatosi aynan shu
#: yerda tug'ilgan edi.
USE_CASE_3_STEPS = 4


class Realized(StrEnum):
    """Repo va'da bilan nima qilgan.

    Besh sinf. «Bor / yo'q» ikkiligi bu bo'limda to'rtta turli holatni
    bitta katakka tiqib qo'yardi: va'da boshqa manbadan bajarilgan,
    nomi almashgan, kod aynan **teskarisini** qiladi, va sathning o'zi
    yo'q. Hech biri bir-biriga teng emas.
    """

    #: Va'da aytilganidek qurilgan.
    BUILT = "built"
    #: Qurilgan, lekin band ruxsat bermagan manba yoki sath bilan.
    SUBSTITUTED = "substituted"
    #: Mexanizm bor, hujjat uni boshqa nom bilan chaqiradi.
    RENAMED = "renamed"
    #: Kod band taqiqlagan narsani aynan bajaradi.
    INVERTED = "inverted"
    #: Va'dani bajaradigan sath repoda yo'q.
    ABSENT = "absent"


#: Band «aytilganidek bajarilgan» deb hisoblanadigan sinflar. Faqat
#: bittasi: qolgan to'rttasining har biri hujjat va kod orasida farqni
#: nomlaydi.
REALIZED_KEPT: frozenset[Realized] = frozenset({Realized.BUILT})


class Reachable(StrEnum):
    """`Given` bugun ro'y bera oladimi.

    Bu o'q bandning **rostligini** emas, uning **tekshirilishi
    mumkinligini** o'lchaydi. Ro'y bermaydigan `Given` bandni hech
    qachon yiqilmaydigan qilib qo'yadi va shuning uchun uni hech qachon
    tekshirmaydi.
    """

    #: Shart bugun bajariladi.
    REACHABLE = "reachable"
    #: Shartning bir yarmi bajariladi, ikkinchisi mexanizmsiz.
    PARTIAL = "partial"
    #: Shart bugun ro'y bera olmaydi — band mazmunsiz o'tadi.
    UNREACHABLE = "unreachable"
    #: Hikoyada gherkin bloki umuman yo'q.
    UNWRITTEN = "unwritten"


#: `Given` haqiqatan ro'y beradigan sinflar.
REACHABLE_LIVE: frozenset[Reachable] = frozenset({Reachable.REACHABLE, Reachable.PARTIAL})


class Named(StrEnum):
    """Repo bandni nom bilan taniydimi.

    Nomlash — arzon va kamdan-kam qilinadigan ish, lekin u yagona narsa
    bo'lib, uning yordamida keyingi o'quvchi kodni hujjatga qaytara
    oladi. Bugun to'qqizta banddan **bittasi** nomlangan.
    """

    #: Kod ham, test ham bandni nomlaydi.
    TESTED = "tested"
    #: Faqat izohda havola bor, test bandni yurgizmaydi.
    CITED = "cited"
    #: Repo bandni umuman nomlamaydi.
    SILENT = "silent"
    #: Havola bor, lekin u **boshqa** bandga ishora qiladi.
    #:
    #: Bugun bo'sh va shu holicha qoladi (88-run tuzatgan). Sinf
    #: saqlanadi, chunki xato shakli qaytishi mumkin: `UC-S2` va
    #: `UC-S3` yonma-yon turadi va qadamlar soni bilan farq qiladi.
    MISCITED = "miscited"


#: Repo bandni haqiqatan taniydigan sinflar.
NAMED_KNOWN: frozenset[Named] = frozenset({Named.TESTED, Named.CITED})


class UserStoriesError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class Story:
    """§9 ning bitta `US-S*` hikoyasi — sarlavha va `Given` i."""

    code: str
    #: Sarlavhadagi rol — aynan, tarjimasiz.
    role: str
    #: «(P0)» / «(P1)» / «(P2)» — aynan.
    priority: str
    #: Gherkin bloki bormi.
    gherkin: bool
    reachable: Reachable
    #: `Given` nima uchun aynan shu bahoni oladi.
    note: str
    binds: tuple[str, ...] = ()


@dataclass(frozen=True)
class Clause:
    """Bitta `Then`/`And` bandining bugungi bahosi.

    `promise` — hujjatdagi **va'da**, `code` esa reyestrning qatori.
    Ikkisi bir xil emas: bitta va'da bir nechta yo'lda boshqacha
    bajarilishi mumkin va aynan shu farq eng qimmatli
    (`split_promises`).
    """

    code: str
    story: str
    #: Qaysi va'da. Bir va'daning bir nechta qatori bo'lishi mumkin.
    promise: str
    #: Bandning hujjatdagi matni — qisqartirilgan, tarjimasiz.
    text: str
    realized: Realized
    named: Named
    #: Nima uchun aynan shu baho. Keyingi o'quvchi uchun.
    note: str
    #: Dalil: `modul:simvol` yoki `tests/fayl.py`.
    binds: tuple[str, ...] = ()
    #: Va'da bilan qurilgan narsa orasidagi farq. Bo'sh — farq yo'q.
    gap: str = ""


@dataclass(frozen=True)
class UseCase:
    """§10 ning bitta `UC-S*` stsenariysi."""

    code: str
    title: str
    #: Oqimdagi qadamlar soni — hujjatdan.
    steps: int
    realized: Realized
    reachable: Reachable
    named: Named
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


# --------------------------------------------------------------------------
# §9 — hikoyalar, hujjatdagi tartibda
# --------------------------------------------------------------------------

STORIES: tuple[Story, ...] = (
    Story(
        code="US-S1",
        role="житель Самарканда",
        priority="P0",
        gherkin=True,
        reachable=Reachable.UNREACHABLE,
        note=(
            "«Новый пользователь **с геолокацией** в Самарканде… "
            "выполняет `/start`». `/start` bilan koordinata kelmaydi va "
            "`register_user` buni ochiq yozadi — analitikaga "
            "`region=None` yuboriladi. 87-run aynan shu shartni "
            "`FR-S-601` uchun o'lchagan; §9 uni so'zma-so'z takrorlaydi, "
            "ya'ni bitta hujjat bitta bajarilmaydigan shartni ikki "
            "bo'limda yozgan."
        ),
        binds=("app.bot.service:register_user", "app.core.i18n:DEFAULT_LANGUAGE"),
    ),
    Story(
        code="US-S2",
        role="житель",
        priority="P0",
        gherkin=True,
        reachable=Reachable.REACHABLE,
        note=(
            "«Я отправил геолокацию… бот обработал репорт» — bu asosiy "
            "oqim va u to'liq qurilgan: `Action.REPORT` tugmasi, "
            "geolokatsiya handleri, `intake`, klasterlash va javob. "
            "Hikoyaning bahosi shuning uchun `Then` bandlariga bog'liq, "
            "shartga emas."
        ),
        binds=("app.bot.service:submit_report", "app.reports.intake"),
    ),
    Story(
        code="US-S3",
        role="актив махалли",
        priority="P1",
        gherkin=True,
        reachable=Reachable.UNREACHABLE,
        note=(
            "«Я **выбрал** махаллю» — botda mahallani tanlash yo'li "
            "umuman yo'q. `app/bot/` bo'ylab mahalla faqat "
            "koordinatadan chiqadi (`resolution.mahalla_id`); "
            "klaviaturalarda ham, `Action` da ham mahalla yo'q. "
            "Ustiga `mahallas` jadvali bo'sh va uni to'ldiradigan yo'l "
            "butun daraxtda yo'q — ya'ni shart ikki qatlamda "
            "bajarilmaydi."
        ),
        binds=("app.bot.keyboards:Action", "app.geo.pipeline:find_mahalla_id"),
    ),
    Story(
        code="US-S4",
        role="житель",
        priority="P1",
        gherkin=False,
        reachable=Reachable.UNWRITTEN,
        note=(
            "Yagona hikoya bo'lib, unda gherkin bloki yo'q — ya'ni "
            "hujjat uning bajarilishi haqida hech qanday tekshiriladigan "
            "da'vo qilmaydi. Mexanizm esa **bor** (E13: obuna, "
            "`notifications`, outbox), ya'ni bu yerda odatdagi shakl "
            "teskari: qurilgan narsa haqida hujjat jim."
        ),
        binds=("app.notifications.outbox", "app.bot.keyboards:Action"),
    ),
    Story(
        code="US-S5",
        role="аналитик",
        priority="P2",
        gherkin=True,
        reachable=Reachable.REACHABLE,
        note=(
            "«Период и регион выбраны» — ikkalasi ham `GET /stats.csv` "
            "ning parametrlari va ikkalasi ham ishlaydi "
            "(`?from=`/`?to=`, `?region=`). Bo'limning yagona to'liq "
            "ro'y beradigan sharti."
        ),
        binds=("app.api.v1.stats", "app.stats.export:render"),
    ),
)

STORY_CODES: tuple[str, ...] = tuple(s.code for s in STORIES)


# --------------------------------------------------------------------------
# §9 — bandlar. `US-S2` ning birinchi va'dasi ikki qator: botning ikki
# yo'li ikkita **har xil** sonni ko'rsatadi.
# --------------------------------------------------------------------------

CLAUSES: tuple[Clause, ...] = (
    Clause(
        code="C-1",
        story="US-S1",
        promise="interface-uz",
        text="весь интерфейс отображается на узбекском",
        realized=Realized.SUBSTITUTED,
        named=Named.SILENT,
        note=(
            "Ekran haqiqatan o'zbekcha chiqadi, lekin band ruxsat "
            "bergan sababdan emas. `Given` geolokatsiyani nomlaydi, "
            "amalda esa tilni Telegram tegi va `DEFAULT_LANGUAGE = 'uz'` "
            "hal qiladi. Farq ko'rinmaydi, chunki natija ustma-ust "
            "tushadi: tegi noma'lum **har kim** o'zbekcha ekran oladi — "
            "mintaqadan qat'i nazar — tegi `ru` bo'lgan samarqandlik esa "
            "ruscha, ya'ni aynan band taqiqlagan holat."
        ),
        binds=(
            "app.core.i18n:DEFAULT_LANGUAGE",
            "app.core.i18n:normalize_language",
            "app.geo.models:Region.default_language",
        ),
        gap=(
            "Til mintaqadan emas, tegdan keladi; mintaqaning standart "
            "tili sxemada bor va birinchi ekranga yetmaydi."
        ),
    ),
    Clause(
        code="C-2",
        story="US-S1",
        promise="language-one-command",
        text="переключение языка доступно одной командой",
        realized=Realized.SUBSTITUTED,
        named=Named.SILENT,
        note=(
            "Imkoniyat bor, sathi boshqa. Repoda jami ikkita komanda "
            "bor (`/start`, `/help`) va til ularning birortasi emas: "
            "almashtirish `Action.LANGUAGE` tugmasi → `lang:*` callback, "
            "ya'ni **ikki qadam**. Band na so'zma-so'z, na kengaytirilgan "
            "o'qishda bajariladi."
        ),
        binds=(
            "app.bot.keyboards:Action",
            "app.bot.handlers:on_language",
            "app.core.i18n:SUPPORTED_LANGUAGES",
        ),
        gap="«Одной командой» — komanda yo'q; ikki qadamli tugma yo'li bor.",
    ),
    Clause(
        code="C-3",
        story="US-S2",
        promise="independent-count",
        text="вердикт с числом независимых сообщений рядом за последний час (CONFIRMED)",
        realized=Realized.SUBSTITUTED,
        named=Named.SILENT,
        note=(
            "Tasdiqlangan hodisada ekranga `total_reports` tushadi — "
            "biriktirilgan **xabarlar** soni. Uchala sifatlovchi ham "
            "buziladi: xabarlar bir odamdan bir nechta bo'lishi mumkin "
            "(«независимых» emas), foydalanuvchining o'z xabari ham "
            "ichida, va oyna — hodisaning butun umri, ya'ni "
            "`autoclose_after` gacha («за последний час» emas). "
            "To'g'ri son bir maydon narida: `_situation` hodisani "
            "allaqachon oladi va `independent_reporters` o'sha obyektda."
        ),
        binds=(
            "app.bot.reply:Situation.total_reports",
            "app.bot.reply:render",
            "app.clustering.independence:count_independent",
            "app.clustering.models:Outage.independent_reporters",
        ),
        gap=(
            "Va'da `independent_reporters` ni nomlaydi, ekranda "
            "biriktirilgan xabarlar soni turadi va tanlov hech qayerda "
            "qayd etilmagan."
        ),
    ),
    Clause(
        code="C-4",
        story="US-S2",
        promise="independent-count",
        text="вердикт с числом независимых сообщений рядом за последний час (PENDING)",
        realized=Realized.SUBSTITUTED,
        named=Named.SILENT,
        note=(
            "Ikkinchi yo'lda **boshqa** son ko'rsatiladi: `others`, "
            "ya'ni `total - 1`. Bu C-3 dan yaxshiroq (o'zining xabari "
            "chiqarilgan) va baribir xabarlar soni, baribir butun umr "
            "bo'yicha. Ikkala qator ham bitta va'daga tegishli va aynan "
            "shu sabab ular alohida: bitta hukm ikkita har xil sonni "
            "bitta baho ostida yashirardi."
        ),
        binds=(
            "app.bot.reply:Situation.others",
            "app.bot.reply:decide",
            "app.clustering.models:Outage.independent_reporters",
        ),
        gap="Bitta va'da, ikkita yo'l, ikkita har xil son — ikkalasi ham «mustaqil» emas.",
    ),
    Clause(
        code="C-5",
        story="US-S2",
        promise="not-enough-data",
        text="если сообщений рядом нет — данных недостаточно, а не что аварии нет",
        realized=Realized.INVERTED,
        named=Named.SILENT,
        note=(
            "Kod aynan taqiqlangan narsani aytadi va buni ataylab "
            "qiladi: `decide()` xabarlar soni bo'yicha emas, **qamrov** "
            "bo'yicha bo'linadi — katakda faol foydalanuvchilar bo'lsa "
            "«avariya yo'q», bo'lmasa «ma'lumot yetarli emas». E7 ning "
            "mantig'i asosli; §9 esa qamrov degan tushunchani umuman "
            "ko'rmaydi va `05` §6.2 ning to'rtta verdiktidan ikkitasini "
            "biladi. Ikkala tomon o'z ichida izchil va ikkalasining ham "
            "testi yashil — shuning uchun nomuvofiqlikni hech narsa "
            "ko'rsatmaydi."
        ),
        binds=(
            "app.bot.reply:decide",
            "app.bot.reply:Verdict",
            "app.clustering.lookup:coverage",
        ),
        gap=(
            "Band ikkita verdiktni biladi, spetsifikatsiya to'rttasini "
            "yozadi; taqiqlangan javob shulardan biri."
        ),
    ),
    Clause(
        code="C-6",
        story="US-S3",
        promise="mahalla-summary",
        text="активные инциденты, число сообщений и индекс покрытия махалли",
        realized=Realized.ABSENT,
        named=Named.SILENT,
        note=(
            "Uch elementdan hech biri mahalla kesimida yig'ilmaydi. "
            "Indeks **bor** (`mahalla_coverage`), lekin `mahallas` bo'sh "
            "va bugun u `available=no` qaytaradi; faol hodisalar va "
            "xabarlar soni esa tuman va H3 kesimida hisoblanadi, mahalla "
            "kesimida hech qayerda. Botda bunday vitrina umuman yo'q — "
            "ya'ni band uchun sath ham, ma'lumot ham yetishmaydi."
        ),
        binds=(
            "app.stats.mahalla_coverage",
            "app.stats.service",
            "app.geo.pipeline:find_mahalla_id",
        ),
        gap="Sath yo'q va ma'lumot yo'q — ikkita mustaqil sabab.",
    ),
    Clause(
        code="C-7",
        story="US-S3",
        promise="crowdsource-disclaimer",
        text="присутствует дисклеймер о краудсорсинговой природе данных",
        realized=Realized.BUILT,
        named=Named.SILENT,
        note=(
            "Yagona to'liq qurilgan yarim: dislaymer har vitrinada "
            "chiqadi va matni katalogdan keladi. Baho shunga qaramay "
            "hisobotda «bajarildi» deb turolmaydi — hikoyaning `Given` i "
            "ro'y bermaydi, ya'ni band hech qachon tekshirilmaydi."
        ),
        binds=("app.stats.service", "app.core.i18n"),
        gap=(
            "Qurilgan, lekin `Given` (mahallani tanlash) ro'y bermaydi — "
            "band mazmunsiz o'tadi."
        ),
    ),
    Clause(
        code="C-8",
        story="US-S5",
        promise="per-mahalla-index",
        text="выгрузка содержит индекс покрытия по каждой махалле",
        realized=Realized.SUBSTITUTED,
        named=Named.SILENT,
        note=(
            "Eksport mahalla kesimini emas, **yig'ma** izoh qatorini "
            "yozadi (`mahalla_registry=`, `mahallas=`, `measured=`, "
            "`coverage_index=`, `coverage_band=`). Kodning o'z izohi "
            "buni ochiq tan oladi — «ustun emas, izoh» — va sabab "
            "asosli: CSV ning qatori tuman, `TOTAL` shu qatorlardan "
            "chiqadi. Natija esa qayd etilmagan: «по каждой» so'zi "
            "bajarilmagan va bugun yig'ma qiymat ham bo'sh."
        ),
        binds=(
            "app.stats.export:render",
            "app.stats.mahalla_coverage",
        ),
        gap=(
            "«По каждой» → yig'ma bitta qator; ustiga bugun "
            "`available=no`, ya'ni yig'ma qiymat ham bo'sh."
        ),
    ),
    Clause(
        code="C-9",
        story="US-S5",
        promise="boundary-version",
        text="выгрузка содержит версию справочника границ",
        realized=Realized.BUILT,
        named=Named.TESTED,
        note=(
            "Bo'limning yagona bajarilgan **va** nomlangan bandi: "
            "eksport chegaralar spravochnigining versiyasini yozadi, "
            "kod izohi bandni nom bilan keltiradi va ikkita test uni "
            "yurgizadi. To'qqizta banddan bittasi — va u eng past "
            "prioritetli hikoyaning oson yarmi."
        ),
        binds=(
            "app.stats.export:render",
            "app.stats.boundaries:summarize",
            "tests/test_stats_export.py",
            "tests/test_stats_api_db.py",
        ),
    ),
)


# --------------------------------------------------------------------------
# §10 — stsenariylar
# --------------------------------------------------------------------------

USE_CASES: tuple[UseCase, ...] = (
    UseCase(
        code="UC-S1",
        title="Репорт об отключении",
        steps=5,
        realized=Realized.RENAMED,
        reachable=Reachable.REACHABLE,
        named=Named.SILENT,
        note=(
            "Asosiy oqimning beshala qadami ham qurilgan va "
            "alternativa ham (`FR-S-802`: poligon yo'q → faqat tuman, "
            "xatosiz). Farq «Ошибки» katagida: ikkita kod nomlanadi va "
            "**noldan marta** o'sha nom bilan qurilgan. Birinchisi "
            "mavjud, lekin boshqa nom bilan (86-run ning `region_id` → "
            "`region` renomi bilan bir xil shakl); ikkinchisi umuman "
            "yo'q va uni ishlab chiqaradigan geokoder ham yo'q — "
            "`GEOCODER_*` sozlamalari o'qilmaydi."
        ),
        binds=(
            "app.core.errors:OutOfRegionError",
            "app.geo.pipeline:resolve",
            "app.bot.handlers:on_location",
        ),
        gap=(
            "Nomlangan ikkita xato kodidan bittasi boshqacha ataladi, "
            "ikkinchisining mexanizmi yo'q."
        ),
    ),
    UseCase(
        code="UC-S2",
        title="Активация региона",
        steps=5,
        realized=Realized.SUBSTITUTED,
        reachable=Reachable.PARTIAL,
        named=Named.CITED,
        note=(
            "Beshta qadamdan uchtasi qurilgan (yuklash, versiya va "
            "sana, geometriya validatsiyasi). To'rtinchisi "
            "almashtirilgan: «активация зоны покрытия» deb yozilgan, "
            "amalda `regions.is_active` almashadi — qamrov zonasi degan "
            "jadval umuman yo'q (72-run ning ochiq savoli). Beshinchisi "
            "— nazorat namunasi — mexanizmsiz va natijasi hech qayerda "
            "saqlanmaydi (70-run buni qo'lda tasdiqlanadigan mezon deb "
            "qayd etgan; §10 ni nomlaydigan yagona joy ham o'sha)."
        ),
        binds=(
            "app.geo.registry",
            "app.release.acceptance",
            "tools/region_admin.py",
        ),
        gap=(
            "Predshartning mahalla yarmi tekshirilmaydi; 4-qadam boshqa "
            "mexanizm bilan almashtirilgan; 5-qadam yo'q."
        ),
    ),
    UseCase(
        code="UC-S3",
        title="Изменение административных границ",
        steps=4,
        realized=Realized.SUBSTITUTED,
        reachable=Reachable.REACHABLE,
        named=Named.SILENT,
        note=(
            "To'rtala qadam ham qurilgan va «Результат» ning «история "
            "сохранена» qismi ham bajarilgan: eski qatorlar "
            "o'chirilmaydi, `valid_to` bilan yopiladi. «Ошибки» "
            "katagining ikkinchi yarmi esa **o'z kodimiz tomonidan** "
            "inkor qilinadi: chegaralarni yuklash asbobi promote ni "
            "quvurdagi yagona qaytarib bo'lmaydigan qadam deb ataydi va "
            "teskari komanda yo'q. Ya'ni hujjat kuchsizrog'ini "
            "(ma'lumot yo'qolmaydi) emas, kuchlirog'ini (amal "
            "qaytariladi) va'da qilgan."
        ),
        binds=(
            "app.geo.queries:districts_for_period",
            "app.stats.boundaries:summarize",
            "tools/import_boundaries.py",
        ),
        gap="«Миграция обратима» — teskari amal yo'q; saqlanadigan narsa ma'lumot, amal emas.",
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class UserStoriesReport:
    """§9/§10 ning bugungi holati."""

    stories: tuple[Story, ...]
    clauses: tuple[Clause, ...]
    use_cases: tuple[UseCase, ...]

    def __post_init__(self) -> None:
        codes = [item.code for item in (*self.stories, *self.clauses, *self.use_cases)]
        if len(set(codes)) != len(codes):
            raise UserStoriesError("qatorlarning kodlari takrorlanadi")

        # ⚠️ Tip e'lon qilingan, lekin hech narsa uni majburlamaydi:
        # bitta elementli `("x")` — kortej emas, **satr**, va u bo'ylab
        # iteratsiya harflarni beradi (87-run ning survivori).
        for item in (*self.stories, *self.clauses, *self.use_cases):
            if not isinstance(item.binds, tuple):
                raise UserStoriesError(f"{item.code}: `binds` kortej emas")
            if any(not isinstance(b, str) or "." not in b for b in item.binds):
                raise UserStoriesError(f"{item.code}: `binds` shakli buzilgan")

        known = {s.code for s in self.stories}
        for clause in self.clauses:
            if clause.story not in known:
                raise UserStoriesError(f"{clause.code}: noma'lum hikoya {clause.story}")
            if clause.realized in REALIZED_KEPT and not clause.gap:
                # Bajarilgan band farqsiz bo'lishi mumkin — lekin faqat
                # `Given` i ro'y berganda. Aks holda «bajarildi» degan
                # baho hisobotda tekshirilmagan va'dani yashiradi.
                if self.reachability[clause.story] not in REACHABLE_LIVE:
                    raise UserStoriesError(
                        f"{clause.code}: yetib bo'lmaydigan shart ostida farq yozilmagan"
                    )
            if clause.named is Named.TESTED and not any(
                b.startswith("tests/") for b in clause.binds
            ):
                # `TESTED` — eng kuchli da'vo va u dalilsiz qola olmaydi:
                # bandni yurgizadigan test **nomlanishi** kerak, aks
                # holda «nomlangan» hukmi o'zini o'zi tasdiqlardi.
                raise UserStoriesError(f"{clause.code}: `TESTED`, lekin test nomlanmagan")

        for story in self.stories:
            has_clauses = any(c.story == story.code for c in self.clauses)
            if story.gherkin is not has_clauses:
                raise UserStoriesError(f"{story.code}: gherkin bayrog'i bandlarga mos kelmaydi")
            if not story.gherkin and story.reachable is not Reachable.UNWRITTEN:
                raise UserStoriesError(f"{story.code}: gherkin yo'q, lekin shart baholangan")

    @property
    def reachability(self) -> dict[str, Reachable]:
        """`hikoya kodi → Given ning bahosi`."""
        return {s.code: s.reachable for s in self.stories}

    @property
    def by_realized(self) -> dict[Realized, tuple[str, ...]]:
        result: dict[Realized, list[str]] = {r: [] for r in Realized}
        for clause in self.clauses:
            result[clause.realized].append(clause.code)
        return {r: tuple(codes) for r, codes in result.items()}

    @property
    def by_reachable(self) -> dict[Reachable, tuple[str, ...]]:
        result: dict[Reachable, list[str]] = {r: [] for r in Reachable}
        for story in self.stories:
            result[story.reachable].append(story.code)
        return {r: tuple(codes) for r, codes in result.items()}

    @property
    def by_named(self) -> dict[Named, tuple[str, ...]]:
        result: dict[Named, list[str]] = {n: [] for n in Named}
        for clause in self.clauses:
            result[clause.named].append(clause.code)
        return {n: tuple(codes) for n, codes in result.items()}

    @property
    def by_story(self) -> dict[str, tuple[str, ...]]:
        result: dict[str, list[str]] = {s.code: [] for s in self.stories}
        for clause in self.clauses:
            result[clause.story].append(clause.code)
        return {code: tuple(codes) for code, codes in result.items()}

    @property
    def diverged(self) -> tuple[Clause, ...]:
        """Qurilgan narsa band aytgan narsa emas."""
        return tuple(c for c in self.clauses if c.realized not in REALIZED_KEPT)

    @property
    def inverted(self) -> tuple[Clause, ...]:
        """Kod band **taqiqlagan** narsani bajaradi.

        `diverged` ning eng og'ir qismi va alohida o'lchanadi:
        almashtirilgan va'dani tuzatish uchun manbani almashtirish
        yetadi, teskari bajarilganini tuzatish uchun avval ikki
        bo'limning qaysi biri haq ekanini hal qilish kerak.
        """
        return tuple(c for c in self.clauses if c.realized is Realized.INVERTED)

    @property
    def vacuous(self) -> tuple[Clause, ...]:
        """`Given` i ro'y bermaydigan hikoyaning bandlari.

        Hisoblanadi, e'lon qilinmaydi: baho hikoyaning o'qidan keladi,
        bandning o'zidan emas. Shuning uchun `US-S3` ning **bajarilgan**
        bandi ham shu yerga tushadi — u qurilgan, lekin hech qachon
        tekshirilmaydi.
        """
        reachability = self.reachability
        return tuple(c for c in self.clauses if reachability[c.story] not in REACHABLE_LIVE)

    @property
    def unnamed(self) -> tuple[Clause, ...]:
        """Repo nom bilan tanimaydigan bandlar."""
        return tuple(c for c in self.clauses if c.named not in NAMED_KNOWN)

    @property
    def split_promises(self) -> dict[str, tuple[str, ...]]:
        """Bitta va'dani bir nechta qator bilan bajaradigan joylar.

        Hisoblanadi. Bugun bitta: `US-S2` ning soni botning ikki yo'lida
        ikkita **har xil** maydondan olinadi. Bitta hukm ikkalasini
        bitta baho ostida yashirardi va farq — qaysi son ekrandagi son —
        hisobotdan yo'qolardi.
        """
        grouped: dict[str, list[str]] = {}
        for clause in self.clauses:
            grouped.setdefault(clause.promise, []).append(clause.code)
        return {promise: tuple(codes) for promise, codes in grouped.items() if len(codes) > 1}

    @property
    def blocked_by_empty_mahallas(self) -> tuple[Clause, ...]:
        """Bo'sh `mahallas` hal qiladigan bandlar.

        Hisoblanadi, e'lon qilinmaydi: dalili mahalla yo'li bo'lgan har
        band shu yerga tushadi. Ro'yxat bo'shashi uchun poligonlarni
        yuklaydigan birinchi kod yozilishi kerak (E17, 👤 H-4/H-5).
        """
        return tuple(c for c in self.clauses if any("mahalla" in b.lower() for b in c.binds))

    @property
    def realizations_touched(self) -> frozenset[Realized]:
        """Bo'sh `mahallas` nechta turli xil bajarilishga tegadi.

        Hisoblanadi. Bugun ikkita va ular bir-biriga o'xshamaydi:
        `US-S3` da sath ham yo'q (`ABSENT`), `US-S5` da esa sath bor va
        boshqa shaklda qurilgan (`SUBSTITUTED`). Poligonlar kelgan kuni
        ikkinchisi bir kunda ma'noli bo'ladi, birinchisi esa hali ham
        yozilmagan bo'lib qoladi.
        """
        return frozenset(c.realized for c in self.blocked_by_empty_mahallas)

    @property
    def unwitnessed_promises(self) -> tuple[Clause, ...]:
        """Bajarilgan **va** hech qachon tekshirilmaydigan bandlar.

        Hisoblanadi, ikkala o'qning kesishmasidan. Bugun bitta
        (`US-S3` ning dislaymeri) va u bo'limning eng chalg'ituvchi
        qatori: hisobotda ham, kodda ham hammasi joyida ko'rinadi.
        """
        reachability = self.reachability
        return tuple(
            c
            for c in self.clauses
            if c.realized in REALIZED_KEPT and reachability[c.story] not in REACHABLE_LIVE
        )

    @property
    def stories_without_gherkin(self) -> tuple[str, ...]:
        """Tekshiriladigan da'vosi yo'q hikoyalar."""
        return tuple(s.code for s in self.stories if not s.gherkin)

    @property
    def use_cases_diverged(self) -> tuple[UseCase, ...]:
        """Oqimi yozilganidek qurilmagan stsenariylar."""
        return tuple(u for u in self.use_cases if u.realized not in REALIZED_KEPT)

    @property
    def named_count(self) -> int:
        """Repo nom bilan taniydigan bandlar soni. Bugun bitta."""
        return len(self.clauses) - len(self.unnamed)

    @property
    def promises_hold(self) -> bool:
        """Har band aytilganidek bajarilganmi.

        Bugun `False`: to'qqizta banddan **yettitasi** boshqacha
        bajarilgan yoki umuman bajarilmagan. Qolgan ikkitasidan biri
        (`C-7`) esa hech qachon tekshirilmaydi — ya'ni bu o'q yolg'iz
        o'qilganda bo'limni boridan yaxshiroq ko'rsatadi.
        """
        return not self.diverged

    @property
    def preconditions_hold(self) -> bool:
        """Har `Given` bugun ro'y bera oladimi.

        `promises_hold` dan mustaqil: va'da to'g'ri bajarilgan bo'lsa
        ham shart ro'y bermasligi mumkin va aksincha.
        """
        return all(s.reachable in REACHABLE_LIVE for s in self.stories if s.gherkin)

    @property
    def naming_holds(self) -> bool:
        """Repo bandlarni nom bilan taniydimi."""
        return not self.unnamed

    @property
    def use_cases_hold(self) -> bool:
        """Stsenariylar yozilganidek qurilganmi."""
        return not self.use_cases_diverged

    @property
    def accurate(self) -> bool:
        """§9/§10 bugungi haqiqatni to'g'ri tasvirlaydimi.

        To'rtta shart va **to'rttasi ham mustaqil o'lchanadi** (82-run
        ning sabog'i: birlashtirilgan shart bitta mutatsiyani yashiradi).
        """
        return (
            self.promises_hold
            and self.preconditions_hold
            and self.naming_holds
            and self.use_cases_hold
        )


def evaluate() -> UserStoriesReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi
    (`scope.evaluate`, `roadmap.evaluate`, `success.evaluate`,
    `functional_requirements.evaluate` bilan bir xil sabab).
    """
    return UserStoriesReport(stories=STORIES, clauses=CLAUSES, use_cases=USE_CASES)

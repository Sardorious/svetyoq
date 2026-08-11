"""Funksional talablar deltasi (`01` §8) ↔ qurilgan mahsulot.

**Nima uchun bu modul bor.** 86-run uchta nomzod qoldirdi va §8 ni
birinchi qatorga qo'ydi. Sabab navbat emas: §8 paketdagi yagona bo'lim
bo'lib, u o'z tekshiruvini **o'zi bilan olib yuradi**. Qolgan
reyestrlarda talab nasr bilan yozilgan va uni qanday tekshirishni
o'quvchi o'ylab topadi; bu yerda esa har qatorning oxirgi katagi
`AC` — Given/When/Then, ya'ni bajariladigan da'vo.

Shundan ikkita savol chiqadi va ular bir-birini almashtirmaydi:

1. *Qator aytgan qoida — repo yurgizadigan qoidami?* (`Delivered`)
2. *`AC` bugun umuman bajarilishi mumkinmi?* (`Witness`)

Ikkinchisi birinchisidan mustaqil. `AC` yashil bo'lishi mumkin, chunki
uning `Given` i **hech qachon ro'y bermaydi** — shartning bajarilishi
emas, shartning yo'qligi. Bunday qator hisobotda «bajarildi» deb
ko'rinadi va uni hech narsa ko'rsatmaydi.

## Uchinchi o'q: bo'lim o'z noaniqligini o'zi e'lon qiladi

§8 ning ikkinchi belgisi — oltita qatordan **beshtasi** aniq epistemik
belgi ko'taradi: `[ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ]`, `[ГИПОТЕЗА]`, «подлежит
калибровке», «подлежит определению», «изменяемый без релиза». Paketda
bunday zichlik boshqa joyda yo'q.

Bu qimmatli, chunki tekshirilishi mumkin: agar hujjat «bu qiymat hali
tanlanmagan» desa, kodda o'sha qiymat **hali ham tanlanmagan** bo'lishi
kerak — ya'ni sozlama bo'lib qolishi, migratsiya talab qilmasligi va
testlar bilan qulflanmasligi kerak. `Openness` shuni o'lchaydi.

⚠️ **Eng yomon holat `HARDENED` — va u nazariy emas.** Qiymat
tanlansa, bu bir xato; tanlangan qiymatni **test himoyalasa**, bu
boshqa xato: kalibrlash — ya'ni hujjat Ph.0 ga rejalashtirgan ishning
o'zi — endi yashil to'plamni qizil qiladi. Kalibrlashni to'sib turgan
narsa mahsulot emas, o'z to'plamimiz bo'ladi.

## Asosiy topilma: bir paketning ikki bo'limi bitta son haqida teskari ko'rsatma beradi

`FR-S-804` aytadi: «Разрешение H3 — **подлежит калибровке**, не
фиксируется в спецификации до Ph.0». `05` §3 esa uni **spetsifikatsiyada
qotiradi**: quvur blokida `latlng_to_cell(lat, lon, 9)`.

Kod ikkinchisini bajaradi va uch qatlamda:

* `settings.h3_resolution = 9` — sozlama, ya'ni yuzaki qaraganda ochiq;
* `reports.h3_r9` — **ustun nomi**, ya'ni rezolyutsiyani o'zgartirish
  migratsiya talab qiladi va o'zgartirilmasa ustun o'z nomi bilan
  yolg'on gapiradi (r8 qiymatlari `h3_r9` da yashaydi);
* **ikkita test fayli** qiymatni literal `9` ga tenglashtiradi
  (`H3_GUARD_TESTS`): 44-run ADR-03 ni, `test_geo_h3` esa ustun
  nomini o'qigan. Uchinchisi (`H3_COUPLED_TEST`, 60-run) sonni
  `05` §3 dan **parse qiladi** va shuning uchun to'siq emas —
  u faqat kod bilan hujjatning birga o'zgarishini talab qiladi.
  Ya'ni kalibrlashni haqiqatan to'sib turgan narsa ikkita fayl.

Ya'ni Ph.0 da kalibrlash sozlamani, ustun nomini va **ikkita yashil
testni** birdan buzadi: hujjat rejalashtirgan ishning o'zi endi
o'z to'plamimizga qarshi bajariladi. Bo'shliq bo'limlar **orasida**: §8 sonni ochiq deb e'lon
qiladi, `05` §3 uni yopiq deb yozadi, va ikkalasi hech qachon
yonma-yon qo'yilmagan.

⚠️ Ustiga §8 rezolyutsiyani **oraliq** bilan beradi (`8–9`), sozlama
esa bitta butun son. Oraliqning pastki yarmi umuman ifodalanmagan.

## Ikkinchi topilma: bitta qator o'z ichida o'ziga zid

`FR-S-802` ning «Ошибки» katagi mahalla poligoni yo'qligi uchun
alohida xato kodini nomlaydi. O'sha qatorning `AC` si esa buni
**taqiqlaydi**: «при отсутствии полигона привязка выполняется
только к району **без ошибки**». Ikkala talab bitta katakdan
pastda turadi.

⚠️ Kodning **o'zi bu yerda yozilmaydi** — 75-run ning qorovuli
uni `app/` da literal sifatida ko'rsa yiqiladi va u haq: yozilgan
kod qidirilayotgan kodga aylanadi. Nom `test_functional_requirements_contract` da,
hujjatdan o'qilgan joyda qoladi (85-run ning `registries.py` dagi
yechimi bilan bir xil).

Kod `AC` ni tanlagan: `find_mahalla_id` `None` qaytaradi, hech narsa
ko'tarilmaydi, o'sha kod repoda **yo'q** (75- va 85-runlar buni ikki
tomondan o'lchagan). Tanlov to'g'ri, lekin u tanlov ekani hech
qayerda yozilmagan.

⚠️ Va `AC` ning **birinchi** yarmi bugun umuman ro'y bera olmaydi:
«Given репорт с координатами внутри известной махалли» — `mahallas`
bo'sh va uni to'ldiradigan yo'l butun daraxtda yo'q
(`tools/import_boundaries.py` da `mahalla` so'zi bir marta ham
uchramaydi; 82- va 85-runlar). Ya'ni qatorning ikkala yarmi ham
bajarilgan ko'rinadi va sabab bitta: birinchisi hech qachon
tekshirilmaydi, ikkinchisi esa **har doim** ishlaydi.

## Uchinchi topilma: `Given` moment ta'minlay olmaydigan faktni so'raydi

`FR-S-601` ning `AC` si: «Given новый пользователь **из региона
samarkand**, When он выполняет `/start`, Then первый экран на
узбекском».

`/start` bilan koordinata kelmaydi. `register_user` buni ochiq
yozadi va analitikaga `region=None` yuboradi — ya'ni «из региона
samarkand» degan fakt aynan `AC` nomlagan lahzada **mavjud emas**.
Qatorning birinchi disyunkti («чья первая геолокация попадает в
регион») shuning uchun birinchi ekranni hech qachon hal qila olmaydi;
ishlaydigan yagona disyunkt — Telegram tegi.

⚠️ Va u ham kengroq ishlaydi: `DEFAULT_LANGUAGE = "uz"`, ya'ni tegi
noma'lum bo'lgan **har kim** o'zbekcha ekran oladi (mintaqadan qat'i
nazar), tegi `ru` bo'lgan samarqandlik esa ruscha — `AC` aynan shuni
taqiqlaydi.

## To'rtinchi topilma: epigraf o'n ikkita modulni yo'q hujjatdan meros qiladi

«Модули M1–M12 наследуются из `03_Functional_Requirements.md`
ташкентского пакета без изменений, кроме перечисленного ниже».

O'sha fayl paketda **yo'q**. Bu 86-run ning `17_OpenAPI.yaml` topilmasi
bilan bir xil shakl, lekin kattaroq: u yerda oltita interfeys xossasi
edi, bu yerda mahsulotning **butun funksional sathi**.

⚠️ Ustiga nomida to'qnashuv bor: paketning o'z `03_` fayli —
`03_Development_Roadmap.md`. Repoda `03_` prefiksini ko'rgan o'quvchi
havola bajarilgan deb o'ylashi mumkin, aslida ikki xil hujjat bitta
raqamni da'vo qiladi.

§8 o'n ikki moduldan **uchtasini** nomlaydi (M6, M8, M9 — o'zgarganlari).
Qolgan to'qqiztasining na nomi, na mazmuni paketda bor: `M1`, `M2`,
`M3`, `M4`, `M5`, `M7`, `M10`, `M11`, `M12` iboralari yettala
hujjatda ham uchramaydi. Ya'ni «o'zgarishsiz meros qilinadi» degan
gapning **nimasi** meros qilinayotgani noma'lum.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi. `h3_resolution` kalibrlanmadi (Ph.0 ishi),
«Ошибки» katagidagi xato kodi qo'shilmadi (`AC` uni taqiqlaydi,
ya'ni avval hujjat hal qilinishi kerak), `/start` ga mintaqa
qo'shilmadi
(koordinata yo'q — mahsulot qarori). Modul o'lchaydi, tahrirlamaydi
(75–77, 82–86 runlar bilan bir xil qoida).

Modul `app/release/` da yashaydi — `scope`, `roadmap`, `success`,
`risks` bilan bir joyda — va `app.*` dan hech narsa import qilmaydi:
reyestr sof e'lon, qurilgan sathni **test** o'lchaydi (`ast`, sxema va
paketning boshqa hujjatlari orqali).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Hujjat bo'limi. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "01 §8"

#: Delta jadvallarining soni — `FR-S-*` sarlavhalari. Hujjatdan parse
#: qilinadi va reyestr bilan solishtiriladi.
SPEC_ROWS = 6

#: `AC` katagi bor qatorlar soni. Oltitadan **to'rtta**: `FR-S-804` va
#: `FR-S-901` da `AC` o'rniga «Параметр» turadi.
#:
#: ⚠️ Bu tasodif emas va uni ko'rish uchun ikkita o'q kerak: `AC` siz
#: qolgan ikkala qator ham aynan **noaniqlikni e'lon qilgan** qatorlar
#: (`подлежит калибровке`, `подлежит определению`). Ya'ni §8 o'zi ishonch
#: hosil qilgan har bir qator uchun tekshiruv beradi va ishonchsiz
#: qatorlarning birortasi uchun bermaydi — natijada aynan eng shubhali
#: ikkita qaror hech qachon yiqila olmaydigan holda kodga tushgan.
SPEC_AC_ROWS = 4

#: §8 o'zgargan deb sanaydigan modullar — aynan va hujjatdagi tartibda.
SPEC_MODULES: tuple[str, ...] = ("M8", "M6", "M9")

#: Epigraf meros qiladigan modullar oralig'i — aynan.
INHERITED_RANGE = ("M1", "M12")

#: Meros manbai. **Paketda yo'q**; ustiga paketning o'z `03_` fayli
#: boshqa hujjat (`03_Development_Roadmap.md`), ya'ni prefiks
#: to'qnashuvi havolani bajarilgandek ko'rsatadi.
INHERITED_DOC = "03_Functional_Requirements.md"

#: Paketda `03_` prefiksini egallagan haqiqiy fayl.
INHERITED_DOC_HOMONYM = "03_Development_Roadmap.md"

#: Epigraf meros qilgan, lekin paket **nomlamagan** modullar. Test
#: ularning yettala hujjatda ham uchramasligini o'lchaydi.
UNNAMED_MODULES: tuple[str, ...] = ("M1", "M2", "M3", "M4", "M5", "M7", "M10", "M11", "M12")

#: §8 ning ustunlari — har `FR-S-*` jadvalining chap ustuni. Ro'yxat
#: **birlashma**: bitta qator hammasini ko'tarmaydi.
SPEC_FIELDS: tuple[str, ...] = (
    "Описание",
    "Приоритет",
    "Риск",
    "Ошибки",
    "Обоснование",
    "Параметр",
    "Статус",
    "AC",
)

#: `FR-S-804` ning soni. Hujjat uni **oraliq** bilan beradi, sozlama esa
#: bitta butun son — test ikkalasini ham hujjatdan parse qiladi.
H3_BAND = (8, 9)

#: `05` §3 qotirgan qiymat va `settings.h3_resolution` ning standarti.
#: §8 aynan shuni «не фиксируется до Ph.0» deydi.
H3_FIXED = 9

#: `HARDENED` hukmining dalili — qiymatni **literal** bilan qulflaydigan
#: test fayllari. Ro'yxat `ast` bilan qayta hisoblanadi va tenglik
#: talab qilinadi, ya'ni yangi qorovul qo'shilsa bu qator ham
#: yangilanadi.
#:
#: ⚠️ **Uchta fayl, uchta mustaqil sabab, uchta turli run.** Hech kim
#: xato qilmagan: 44-run ADR-03 ni, 60-run `05` §3 ni, `test_geo_h3`
#: esa ustun nomini o'qigan va uchalasi ham to'g'ri o'qigan. Bo'shliq
#: shundaki, §8 ning «Ph.0 gacha qotirilmaydi» talabining ularning
#: birortasida ham vakili yo'q — kechiktirilgan qaror hech qayerda
#: **kechiktirilgan** deb yozilmagan, faqat bitta hujjatning bitta
#: katagida aytilgan.
H3_GUARD_TESTS: tuple[str, ...] = (
    "test_config.py",
    "test_geo_h3.py",
)

#: To'rtinchi qorovul — va u **boshqacha**. 60-run ning kontrakti sonni
#: `05` §3 dan **parse qiladi** va kod bilan solishtiradi
#: (`settings.h3_resolution == spec_res`), ya'ni literalga emas,
#: hujjatga bog'laydi.
#:
#: ⚠️ Farq amaliy: bu fayl kalibrlashni **to'smaydi** — u faqat kod
#: bilan hujjatning birga o'zgarishini talab qiladi, aynan §8 so'ragan
#: narsani. Ya'ni uchta qorovuldan ikkitasi to'siq, bittasi bog'lam.
#: Bu ajratishsiz «testlar kalibrlashni to'sadi» degan gap juda keng
#: bo'lardi va noto'g'ri faylni ayblardi.
H3_COUPLED_TEST = "test_privacy_jitter_contract.py"

#: `FR-S-901` meros qiladigan chegara va uni beradigan talab. Talab
#: paketda **faqat shu katakda** uchraydi.
SIGNIFICANCE_THRESHOLD = 30
SIGNIFICANCE_SOURCE = "FR-901"

#: `FR-S-801` va `FR-S-803` tayanadigan ochiq savol. Paketda uch marta
#: havola qilinadi va **birorta hujjatda ta'riflanmagan** (86-run buni
#: `01` §28 tomonidan ham ko'rgan).
OPEN_QUESTION = "OQ-01"

#: Modul → uning kodi yashaydigan paketlar. Teskari yo'nalishdagi
#: qatorning yorlig'i shu jadval bo'yicha tekshiriladi: «bu M9 ning
#: o'zgarishi» degan da'vo kamida bitta bog'lami M9 ning paketida
#: turganda ma'noli. Mutatsiya buni ko'rsatdi — yorliqni almashtirish
#: hech narsani yiqitmasdi.
MODULE_PACKAGES: dict[str, tuple[str, ...]] = {
    "M8": ("app.geo", "app.api.v1.geo", "app.db"),
    "M6": ("app.bot", "app.core.i18n"),
    "M9": ("app.stats", "app.analytics", "app.jobs"),
}


class Delivered(StrEnum):
    """Repo qator aytgan qoida bilan nima qilgan.

    Besh sinf. «Bor / yo'q» ikkiligi bu bo'limda to'rtta turli holatni
    bitta katakka tiqib qo'yardi: qoida boshqa, manba boshqa,
    mexanizm bor-u ma'lumot yo'q, va qoidaning yarmi yetib
    bo'lmaydigan joyda. Hech biri bir-biriga teng emas.

    `ABSENT` sinfi **ataylab yo'q**: §8 ning oltala qatori ham biror
    tarzda qurilgan va bu faktning o'zi aytishga arziydi — bo'lim
    bajarilmagani uchun emas, **boshqacha** bajarilgani uchun
    noto'g'ri.
    """

    #: Qator aytganidek qurilgan.
    BUILT = "built"
    #: Qoidaning bir yarmi bajarilgan, ikkinchisi yetib bo'lmaydigan joyda.
    PARTIAL = "partial"
    #: Qurilgan, lekin qator ruxsat bermagan manbadan.
    SUBSTITUTED = "substituted"
    #: Mexanizm to'liq, uni ishga soladigan ma'lumot hech qachon kelmaydi.
    DORMANT = "dormant"
    #: Qurilgan qoida qator aytgan qoida emas.
    FORKED = "forked"


#: Qator «aytilganidek bajarilgan» deb hisoblanadigan sinflar. Faqat
#: bittasi: qolgan to'rttasining har biri hujjat va kod orasida
#: farqni nomlaydi.
DELIVERED_KEPT: frozenset[Delivered] = frozenset({Delivered.BUILT})


class Witness(StrEnum):
    """`AC` katagi bugun nima qila oladi.

    Bu o'q qatorning **rostligini** emas, `AC` ning **kuchini**
    o'lchaydi. Sabab ikkinchi topilmada: `Given` i ro'y bermaydigan
    `AC` hech qachon yiqilmaydi va shuning uchun hech qachon
    tekshirmaydi.
    """

    #: Repoda test bor va u `Given`/`Then` ni yurgizadi.
    EXERCISED = "exercised"
    #: Kod javob beradi, lekin `AC` ni oxirigacha yurgizadigan test yo'q.
    DERIVABLE = "derivable"
    #: `Given` bugun ro'y bera olmaydi — `AC` mazmunsiz o'tadi.
    VACUOUS = "vacuous"
    #: `Given` o'zi nomlagan lahzada mavjud bo'lmagan faktni so'raydi.
    FORECLOSED = "foreclosed"
    #: Qatorda `AC` umuman yo'q.
    UNWRITTEN = "unwritten"


#: `AC` haqiqatan tekshiruv bo'lgan sinflar.
WITNESS_LIVE: frozenset[Witness] = frozenset({Witness.EXERCISED, Witness.DERIVABLE})


class Openness(StrEnum):
    """Qator e'lon qilgan noaniqlik bilan repo nima qilgan.

    Beshta sinf va ular orasida **tartib bor**: `OPEN` → `FROZEN` →
    `HARDENED` qarorning qanchalik chuqur ko'milganini ko'rsatadi.
    """

    #: Qaror hali ochiq: qiymat sozlama, migratsiya ham, test ham to'smaydi.
    OPEN = "open"
    #: Qiymat tanlangan va tanlangani hech qayerda qayd etilmagan.
    FROZEN = "frozen"
    #: Qiymat tanlangan **va uni test himoyalaydi** — kalibrlash to'plamni qizil qiladi.
    HARDENED = "hardened"
    #: Noaniqlik tishlay olmaydi: u boshqaradigan sirtda ma'lumot yo'q.
    MOOT = "moot"
    #: Qator hech narsani ochiq deb e'lon qilmaydi.
    SETTLED = "settled"


#: Noaniqlik hali ham haqiqatan ochiq bo'lgan sinflar. `MOOT` bu yerda
#: **yo'q**: u ochiqlik emas, kechiktirilgan hisob — ma'lumot kelgan
#: kuni qaror bir kunda talab qilinadi.
OPENNESS_HELD: frozenset[Openness] = frozenset({Openness.OPEN, Openness.SETTLED})


class FunctionalRequirementsError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class Delta:
    """§8 ning bitta `FR-S-*` qatori va uning bugungi bahosi."""

    code: str
    #: Sarlavhadagi nom — aynan, tarjimasiz.
    title: str
    #: Qaysi modulning deltasi (`M8`, `M6`, `M9`).
    module: str
    #: «Приоритет» katagi — aynan.
    priority: str
    delivered: Delivered
    witness: Witness
    openness: Openness
    #: Nima uchun aynan shu baho. Keyingi o'quvchi uchun.
    note: str
    #: Dalil: `modul:simvol` yoki `tests/fayl.py`.
    binds: tuple[str, ...] = ()
    #: Da'vo bilan qurilgan narsa orasidagi farq. Bo'sh — farq yo'q.
    gap: str = ""
    #: Qator o'z ichida o'ziga zid katak ko'taradimi.
    self_contradiction: str = ""
    #: Qator qaysi belgi bilan noaniqlikni e'lon qiladi — aynan.
    marker: str = ""


@dataclass(frozen=True)
class UnnamedSurface:
    """Qurilgan va §8 nomlamagan funksional o'zgarish (teskari yo'nalish).

    Faqat §8 o'zi «o'zgargan» deb e'lon qilgan uchta modulga
    (`M6`, `M8`, `M9`) tegishli narsalar sanaladi: qolgan modullarda
    nima bo'lganini paket bilmaydi, ya'ni ular haqida hukm chiqarib
    bo'lmaydi.
    """

    code: str
    module: str
    title: str
    why: str
    binds: tuple[str, ...]


# --------------------------------------------------------------------------
# Reyestr — `01` §8 ning qatorlari, hujjatdagi tartibda
# --------------------------------------------------------------------------

DELTAS: tuple[Delta, ...] = (
    Delta(
        code="F-1",
        title="Справочник районов Самарканда",
        module="M8",
        priority="P0",
        delivered=Delivered.SUBSTITUTED,
        witness=Witness.DERIVABLE,
        openness=Openness.FROZEN,
        marker="[ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ]",
        note=(
            "Spravochnik **bor** va `AC` ning uchala shartini ham kod "
            "bajaradi: poligonlar (`districts.geom`), ikki til "
            "(`name_uz` va `name_ru` — ikkalasi ham `NOT NULL`, "
            "`mahallas` dan farqli o'laroq) va manba bilan sana "
            "(`source`, `source_ref`, `license`, `valid_from` — hammasi "
            "javobning `properties` ida). Farq **manbada**: «Риск» "
            "katagi tumanlar tarkibi va sonini tasdiqlashni talab "
            "qiladi va `01` §28 tasdiqni «Официальный акт о границах "
            "районов» deb ataydi. Repo esa ularni OSM dan oladi va "
            "`geo.quality` faqat **shaklni** tekshiradi (topologiya, "
            "nomlarning to'liqligi) — tarkibni hech narsa tekshirmaydi. "
            "Ya'ni tasdiqlanishi kerak bo'lgan narsa tasdiqlanmadi, "
            "boshqa manba bilan **almashtirildi** va buni hech kim "
            "qaror sifatida yozib qo'ymadi."
        ),
        binds=(
            "app.geo.models:District",
            "app.api.v1.geo:_feature",
            "tools/import_boundaries.py",
            "app.geo.quality",
        ),
        gap=(
            "Tarkib va son OSM dan keladi; `OQ-01` esa rasmiy aktni "
            "kutadi va o'zi birorta hujjatda ta'riflanmagan."
        ),
    ),
    Delta(
        code="F-2",
        title="Справочник махаллей",
        module="M8",
        priority="P0",
        delivered=Delivered.DORMANT,
        witness=Witness.VACUOUS,
        openness=Openness.MOOT,
        note=(
            "Mexanizm **to'liq**: `mahallas` jadvali, `find_mahalla_id`, "
            "`reports.mahalla_id`, `GET /geo/mahallas` va tasdiqlashda "
            "`mahallas_affected`. Ishga soladigan ma'lumot esa hech "
            "qachon kelmaydi — jadvalga yozadigan yo'l butun daraxtda "
            "yo'q (`tools/import_boundaries.py` da `mahalla` so'zi bir "
            "marta ham uchramaydi). Shuning uchun `AC` ning birinchi "
            "yarmi («внутри известной махалли») hech qachon "
            "tekshirilmaydi, ikkinchi yarmi esa **har doim** ishlaydi: "
            "biriktirish tumangacha boradi va to'xtaydi."
        ),
        binds=(
            "app.geo.pipeline:find_mahalla_id",
            "app.clustering.models:Report.mahalla_id",
            "app.geo.mahallas",
        ),
        self_contradiction=(
            "«Ошибки» katagi alohida xato kodini nomlaydi, "
            "o'sha qatorning `AC` si esa «без ошибки» deb talab qiladi. "
            "Kod `AC` ni tanlagan — xato kodi repoda umuman yo'q — "
            "lekin tanlov ekani hech qayerda yozilmagan."
        ),
        gap="Degradatsiya jim bajariladi; katakdagi xato kodi repoda yo'q.",
    ),
    Delta(
        code="F-3",
        title="Версионирование границ",
        module="M8",
        priority="P0",
        delivered=Delivered.BUILT,
        witness=Witness.EXERCISED,
        openness=Openness.SETTLED,
        note=(
            "Bo'limning eng puxta qatori va yagona to'liq bajarilgani. "
            "`valid_from`/`valid_to` sxemada, `districts_for_period` "
            "davr bo'yicha kesim oladi, `boundaries.summarize` versiya "
            "raqamini (eng oxirgi `valid_from`) va davr ichida "
            "chegara o'zgargan-o'zgarmaganini javobga qo'yadi, "
            "`?at=` esa o'tmishdagi kesimni so'rash imkonini beradi. "
            "`AC` ning uchala qismi ham testda yuriladi."
        ),
        binds=(
            "app.stats.boundaries:summarize",
            "app.geo.queries:districts_for_period",
            "app.api.v1.geo:_parse_at",
            "tests/test_stats_boundaries.py",
            "tests/test_geo_api_db.py",
        ),
        gap=(
            "«Обоснование» katagi `OQ-01` ga tayanadi va o'sha ochiq "
            "savol birorta hujjatda ta'riflanmagan — qator bajarilgan, "
            "asosi esa havolada osilgan."
        ),
    ),
    Delta(
        code="F-4",
        title="H3-агрегация",
        module="M8",
        priority="P1",
        delivered=Delivered.FORKED,
        witness=Witness.UNWRITTEN,
        openness=Openness.HARDENED,
        marker="подлежит калибровке",
        note=(
            "Ikkita da'vo, ikkalasi ham boshqacha bajarilgan. "
            "**Shart:** qator H3 ni «при отсутствии полигона махалли» "
            "klasterlash uchun ishlatadi, ya'ni zaxira daraja deb "
            "yozadi; kod esa `h3_r9` ni **shartsiz** ishlatadi — "
            "mahalla poligoniga tayanadigan klasterlash yo'li umuman "
            "yozilmagan, ya'ni shart hech narsani boshqarmaydi. "
            "**Son:** qator rezolyutsiyani oraliq (`8–9`) bilan beradi "
            "va uni Ph.0 gacha qotirmaslikni talab qiladi; "
            "`settings.h3_resolution` bitta butun son, standarti `9`, "
            "`reports.h3_r9` ustuni nomi uni sxemada qotiradi va "
            "60-run ning maxfiylik kontrakti `h3_resolution == 9` ni "
            "**tasdiqlaydi**, sonni `05` §3 dan parse qilib. Oraliqning "
            "pastki yarmi (`8`) hech qayerda ifodalanmagan."
        ),
        binds=(
            "app.core.config:Settings.h3_resolution",
            "app.geo.h3_cells:DEFAULT_RESOLUTION",
            "app.clustering.lookup:coverage",
            "app.geo.pipeline:find_mahalla_id",
            "tests/test_privacy_jitter_contract.py",
        ),
        gap=(
            "Kalibrlash uch joyni birdan buzadi: sozlama, ustun nomi va "
            "yashil kontrakt testi. Uchinchisi eng og'iri — Ph.0 ning "
            "ishi endi o'z to'plamimizga qarshi bajariladi."
        ),
    ),
    Delta(
        code="F-5",
        title="Язык по умолчанию",
        module="M6",
        priority="P0",
        delivered=Delivered.PARTIAL,
        witness=Witness.FORECLOSED,
        openness=Openness.OPEN,
        marker="[ГИПОТЕЗА]",
        note=(
            "Qoida ikkita disyunktdan iborat va faqat bittasi ishlaydi. "
            "**Telegram tegi** bo'yicha: `register_user` `language_code` "
            "ni `i18n.normalize` ga beradi, `uz` o'zi qoladi — bajarildi. "
            "**Geolokatsiya** bo'yicha: `/start` bilan koordinata "
            "kelmaydi, `register_user` analitikaga `region=None` "
            "yuboradi va buni izohda ochiq yozadi, ya'ni birinchi ekran "
            "mintaqani bila olmaydi. Ustiga ishlaydigan disyunkt "
            "kengroq ishlaydi: `DEFAULT_LANGUAGE = 'uz'`, ya'ni tegi "
            "noma'lum har kim o'zbekcha ekran oladi, tegi `ru` bo'lgan "
            "samarqandlik esa ruscha — `AC` aynan buni taqiqlaydi."
        ),
        binds=(
            "app.bot.service:register_user",
            "app.core.i18n:DEFAULT_LANGUAGE",
            "app.geo.models:Region.default_language",
        ),
        gap=(
            "Birinchi disyunkt `/start` lahzasida yetib bo'lmaydigan "
            "faktga tayanadi; ikkinchisi mintaqadan qat'i nazar ishlaydi."
        ),
    ),
    Delta(
        code="F-6",
        title="Дисклеймер молодого региона",
        module="M9",
        priority="P0",
        delivered=Delivered.BUILT,
        witness=Witness.UNWRITTEN,
        openness=Openness.FROZEN,
        marker="подлежит определению",
        note=(
            "Dislaymer qurilgan va yaxshi qurilgan: `maturity.compute` "
            "ikkita mustaqil shartni alohida sanaydi, sabablar javobda "
            "ochiq turadi, chegaralar javob bilan birga sayohat qiladi "
            "va kunlar pastga yaxlitlanadi. `<30` chegarasi ham aynan: "
            "`events < min_events`, `stats_min_events = 30`. "
            "Bajarilmagani — **qaror qayd etilmagani**: `N` «подлежит "
            "определению» deb yozilgan va kod uni **tanlagan** "
            "(`stats_min_history_days = 90`), tanlagani esa hech "
            "qayerda yozilmagan. Ustiga o'lchov birligi almashgan: "
            "qator **oy** da gapiradi, sozlama **kun** da, va 90 kun "
            "birorta butun oy soniga aniq teng emas."
        ),
        binds=(
            "app.stats.maturity:compute",
            "app.core.config:Settings.stats_min_history_days",
            "app.core.config:Settings.stats_min_events",
            "tests/test_stats_maturity.py",
        ),
        gap=(
            "`N` tanlangan va qayd etilmagan; `<30` esa paketda faqat "
            "shu katakda uchraydigan `FR-901` dan meros qilinadi, ya'ni "
            "sonni paketning o'zi bilan tekshirib bo'lmaydi."
        ),
    ),
)


# --------------------------------------------------------------------------
# Teskari yo'nalish — qurilgan va §8 nomlamagan o'zgarishlar
# --------------------------------------------------------------------------

UNNAMED: tuple[UnnamedSurface, ...] = (
    UnnamedSurface(
        code="X-1",
        module="M8",
        title="Mintaqa reyestri va nuqtadan mintaqani tanlash",
        why=(
            "Toshkent paketi bitta shahar uchun yozilgan; `regions` "
            "jadvali, `pick_for_point` va `GET /regions` M8 ning eng "
            "katta o'zgarishi. §8 ning M8 deltasida bu qator yo'q — "
            "uchta qatordan biri ham mintaqa tushunchasini nomlamaydi."
        ),
        binds=("app.geo.registry:pick_for_point", "app.geo.models:Region"),
    ),
    UnnamedSurface(
        code="X-2",
        module="M8",
        title="Mintaqaning standart tili sxema ustuni sifatida",
        why=(
            "§8 ning M6 deltasi tillar tartibini «параметр "
            "конфигурации» deb ataydi, amalda esa u **sxema ustuni** "
            "(`regions.default_language`, `server_default='uz'`). "
            "Ya'ni mexanizm qator aytganidan kuchliroq — mintaqa "
            "bo'yicha bo'linadi — va bu M8 ga tegadigan o'zgarish, "
            "§8 esa uni ikkala modulda ham sanamaydi."
        ),
        binds=("app.geo.models:Region.default_language", "app.core.i18n:pick_language"),
    ),
    UnnamedSurface(
        code="X-3",
        module="M9",
        title="Mahalla darajasidagi Coverage Index",
        why=(
            "§8 ning M9 deltasi faqat dislaymerdan iborat. Mahalla "
            "kesimidagi qamrov indeksi (`01` §23 uni qabul mezoni "
            "sifatida talab qiladi) shu modulning ikkinchi "
            "o'zgarishi va jadvalда yo'q."
        ),
        binds=("app.stats.mahalla_coverage", "app.jobs.refresh_coverage"),
    ),
    UnnamedSurface(
        code="X-4",
        module="M8",
        title="Chegaralarning litsenziyasi va atributsiyasi javobda",
        why=(
            "OSM ni manba qilib olish `ODbL` atributsiyasini majburiy "
            "qiladi va javobga ikkita maydon qo'shadi (`licenses`, "
            "`attribution`). Bu M8 ning huquqiy oqibati bo'lgan "
            "o'zgarishi; §8 manba haqida faqat «Риск» katagida "
            "gapiradi va litsenziyani umuman nomlamaydi."
        ),
        binds=("app.api.v1.geo:DistrictCollection", "app.geo.models:District.license"),
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FunctionalRequirementsReport:
    """§8 ning bugungi holati."""

    deltas: tuple[Delta, ...]
    unnamed: tuple[UnnamedSurface, ...]

    def __post_init__(self) -> None:
        codes = [d.code for d in self.deltas]
        if len(set(codes)) != len(codes):
            raise FunctionalRequirementsError("qator kodlari takrorlanadi")
        # ⚠️ Tip e'lon qilingan, lekin hech narsa uni majburlamaydi va
        # mutatsiya buni ko'rsatdi: bitta elementli `("x")` — kortej
        # emas, **satr**, va u bo'ylab iteratsiya harflarni beradi.
        # Har qanday «bog'lamlar sonini sanaydigan» tekshiruv shunda
        # jimgina yashil bo'lib qoladi.
        for item in (*self.deltas, *self.unnamed):
            if not isinstance(item.binds, tuple):
                raise FunctionalRequirementsError(f"{item.code}: `binds` kortej emas")
            if any(not isinstance(b, str) or "." not in b for b in item.binds):
                raise FunctionalRequirementsError(f"{item.code}: `binds` shakli buzilgan")
        for delta in self.deltas:
            if delta.module not in SPEC_MODULES:
                raise FunctionalRequirementsError(f"{delta.code}: noma'lum modul {delta.module}")
            if delta.openness is Openness.SETTLED and delta.marker:
                raise FunctionalRequirementsError(
                    f"{delta.code}: `SETTLED` qator noaniqlik belgisini ko'tara olmaydi"
                )
            if delta.openness is not Openness.SETTLED and delta.delivered is Delivered.BUILT:
                if not delta.gap:
                    raise FunctionalRequirementsError(
                        f"{delta.code}: ochiq qaror bor, farq yozilmagan"
                    )

    @property
    def by_delivered(self) -> dict[Delivered, tuple[str, ...]]:
        result: dict[Delivered, list[str]] = {d: [] for d in Delivered}
        for delta in self.deltas:
            result[delta.delivered].append(delta.code)
        return {d: tuple(codes) for d, codes in result.items()}

    @property
    def by_witness(self) -> dict[Witness, tuple[str, ...]]:
        result: dict[Witness, list[str]] = {w: [] for w in Witness}
        for delta in self.deltas:
            result[delta.witness].append(delta.code)
        return {w: tuple(codes) for w, codes in result.items()}

    @property
    def by_openness(self) -> dict[Openness, tuple[str, ...]]:
        result: dict[Openness, list[str]] = {o: [] for o in Openness}
        for delta in self.deltas:
            result[delta.openness].append(delta.code)
        return {o: tuple(codes) for o, codes in result.items()}

    @property
    def by_module(self) -> dict[str, tuple[str, ...]]:
        result: dict[str, list[str]] = {m: [] for m in SPEC_MODULES}
        for delta in self.deltas:
            result[delta.module].append(delta.code)
        return {m: tuple(codes) for m, codes in result.items()}

    @property
    def diverged(self) -> tuple[Delta, ...]:
        """Repo yurgizadigan qoida qator aytgan qoida emas."""
        return tuple(d for d in self.deltas if d.delivered not in DELIVERED_KEPT)

    @property
    def toothless(self) -> tuple[Delta, ...]:
        """`AC` bugun hech narsani tekshirmaydi."""
        return tuple(d for d in self.deltas if d.witness not in WITNESS_LIVE)

    @property
    def closed_deferrals(self) -> tuple[Delta, ...]:
        """Ochiq deb e'lon qilingan qaror jimgina yopilgan."""
        return tuple(d for d in self.deltas if d.openness not in OPENNESS_HELD)

    @property
    def defended_deferrals(self) -> tuple[Delta, ...]:
        """Yopilgan qarorni endi **test** himoyalaydi.

        `closed_deferrals` ning eng og'ir qismi va alohida o'lchanadi:
        `FROZEN` ni tuzatish uchun sozlamani o'zgartirish yetadi,
        `HARDENED` ni tuzatish uchun avval o'z testimizni tahrirlash
        kerak.
        """
        return tuple(d for d in self.deltas if d.openness is Openness.HARDENED)

    @property
    def self_contradictory(self) -> tuple[Delta, ...]:
        """Bitta qatorning ikki katagi bir-birini inkor qiladi."""
        return tuple(d for d in self.deltas if d.self_contradiction)

    @property
    def blocked_by_empty_mahallas(self) -> tuple[Delta, ...]:
        """Bo'sh `mahallas` hal qiladigan qatorlar.

        Hisoblanadi, e'lon qilinmaydi: dalili `app.geo` ning mahalla
        yo'li bo'lgan yoki izohi mahalla poligoniga tayanadigan har
        qator shu yerga tushadi. Ro'yxat bo'shashi uchun poligonlarni
        yuklaydigan birinchi kod yozilishi kerak (E17, 👤 H-4/H-5).
        """
        return tuple(d for d in self.deltas if any("mahalla" in b.lower() for b in d.binds))

    @property
    def opennesses_touched(self) -> frozenset[Openness]:
        """Bo'sh `mahallas` nechta turli xil noaniqlikka tegadi.

        Hisoblanadi. Bugun ikkita va ular bir-biriga o'xshamaydi:
        `F-2` da noaniqlik **tishlay olmaydi** (`MOOT`), `F-4` da esa
        aynan o'sha bo'shliq shartni mazmunsiz qilgani uchun hech kim
        rezolyutsiyaning qotib qolganini sezmadi (`HARDENED`).
        Poligonlar kelgan kuni ikkala qator ham bir vaqtda ma'nosini
        o'zgartiradi.
        """
        return frozenset(d.openness for d in self.blocked_by_empty_mahallas)

    @property
    def unwitnessed_deferrals(self) -> tuple[Delta, ...]:
        """`AC` si yo'q **va** qarori ochiq deb e'lon qilingan qatorlar.

        Hisoblanadi. Bugun ikkita va ular §8 ning butun `AC` siz
        to'plami: bo'lim ishonchi komil qatorga tekshiruv beradi,
        ishonchsiz qatorga bermaydi. Natijada eng shubhali ikkita
        qaror hech qachon yiqila olmaydigan holda kodga tushgan.
        """
        return tuple(
            d
            for d in self.deltas
            if d.witness is Witness.UNWRITTEN and d.openness not in OPENNESS_HELD
        )

    @property
    def modules_named(self) -> int:
        """Epigraf meros qilgan modullardan nechtasi paketda nomlangan."""
        return len(SPEC_MODULES)

    @property
    def modules_inherited(self) -> int:
        """Epigraf meros qilgan modullar soni (`M1`–`M12`)."""
        return len(SPEC_MODULES) + len(UNNAMED_MODULES)

    @property
    def inheritance_witnessed(self) -> bool:
        """Meros manbasini repo ko'ra oladimi.

        Bugun `False` va u **hech qachon** `True` bo'lmaydi, toki
        `03_Functional_Requirements.md` paketga qo'shilmasin. 86-run
        ning `17_OpenAPI.yaml` topilmasi bilan bir xil shakl.
        """
        return False

    @property
    def deltas_hold(self) -> bool:
        """Har qator aytgan qoida — repo yurgizadigan qoidami.

        Bugun `False`: oltita qatordan **to'rttasi** boshqa qoidani
        yurgizadi.
        """
        return not self.diverged

    @property
    def acceptance_holds(self) -> bool:
        """Har `AC` bugun haqiqatan tekshiruvmi.

        `deltas_hold` dan mustaqil: qoida to'g'ri bajarilgan bo'lsa
        ham `AC` mazmunsiz bo'lishi mumkin va aksincha.
        """
        return not self.toothless

    @property
    def deferrals_hold(self) -> bool:
        """Ochiq deb e'lon qilingan qaror ochiq qolganmi."""
        return not self.closed_deferrals

    @property
    def accurate(self) -> bool:
        """§8 bugungi haqiqatni to'g'ri tasvirlaydimi.

        To'rtta shart va **to'rttasi ham mustaqil o'lchanadi** (82-run
        ning sabog'i: birlashtirilgan shart bitta mutatsiyani yashiradi):
        qoidalar mos kelsin; `AC` lar tekshiruv bo'lsin; kechiktirilgan
        qarorlar kechiktirilgan qolsin; va repo qurgan o'zgarish
        jadvalda nomsiz qolmasin.
        """
        return (
            self.deltas_hold
            and self.acceptance_holds
            and self.deferrals_hold
            and not self.unnamed
        )


def evaluate() -> FunctionalRequirementsReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi
    (`scope.evaluate`, `roadmap.evaluate`, `success.evaluate` bilan bir
    xil sabab).
    """
    return FunctionalRequirementsReport(deltas=DELTAS, unnamed=UNNAMED)

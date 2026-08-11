"""Biznes qoidalari (`BRD` §13) ↔ qurilgan mahsulot.

**Nima uchun bu modul bor.** 101-run BRD §8 ni bog'ladi va §13 ni
keyingi nomzod deb qoldirdi. §13 — hujjatning **qoidalar** sathi:
15 ta `BRL-*` qatori, har biri yoki «ЕСЛИ … ТО …» sharti, yoki qat'iy
kategorik hukm («ВСЕГДА», «НИКОГДА», «ЗАПРЕЩЕНО», «НЕ хранятся»).
§8 talab *nima qurilishini* aytadi; §13 esa qurilgan narsa *qanday
xatti-harakat qilishini* buyuradi — shuning uchun bu bo'lim §8 ning
takrori emas, alohida o'lchanadigan sirt.

## Birinchi topilma: `BRL-03` taqiqlagan yagona son — aynan kodda turgan son

Qator ishonchni «до высокого, но **не предельного** значения»
ko'tarishni buyuradi, ya'ni bitta qiymatni nomlab taqiqlaydi —
shkalaning chegarasini. `app.clustering.service` da esa
`AUTHORITATIVE_CONFIDENCE = 100` va u to'g'ridan-to'g'ri qo'yiladi:
rasmiy qatlamda `confidence` formulasi umuman hisoblanmaydi
(`confidence = AUTHORITATIVE_CONFIDENCE if authoritative else
result.confidence`). `06` §2.2 rasmiy xabar «darhol `confirmed`»
qilishini aytadi va **sonni bermaydi** — ya'ni 100 ni qonun emas, kod
tanlagan, va u aynan taqiqlangan qiymatga tushgan. Qatorning ikkinchi
yarmi — «конфликт источников» bayrog'i va moderatsiyaga yo'naltirish —
repoda hech qanday shaklda yo'q: `conflict` bilan bog'liq yagona sirt
`ON CONFLICT` SQL idiomasi.

## Ikkinchi topilma: `BRL-08` statistika qatlamida buziladi

Klasterlash `06` §3 ni benuqson bajaradi: jamoaviy xabar rasmiy
qatlamdagi hodisaga biriktirilmaydi (`find_candidate` da
`Outage.layer == layer`), rasmiy manbaning og'irligi `0.0`, karta va
API har hodisaning `layer` ini ochiq beradi. Lekin
`repo.stats_rows_started_between` `layer` ni **na tanlaydi, na
filtrlaydi** — rasmiy qatlamdagi hodisa jamoaviylari bilan bitta
`outages_total` ga, bitta mediana va P90 ga, bitta tuman chelagiga
tushadi. Qator aynan shuni taqiqlaydi: «не суммируются в одной
метрике». Bu reyestrning yagona **mahsulot defekti** — qolgan
topilmalar hujjat bilan kod orasidagi farq, bu esa kodning o'z
qatlamlar qoidasini oxirigacha olib bormagani. Tuzatilmadi: `05` §7.2
statistika kesimida `layer` ni umuman eslatmaydi va qaysi tomon haq
ekani 👤 qarori.

## Uchinchi topilma: `BRL-04` — §8 dagi TTL ziddiyatining egizagi

«3 ч» bu yerda ham: `BR-014` bilan bitta raqam, bitta qarama-qarshilik
(`05` §4.4 «120 daq», kod `05` ga ergashadi). Sonlar shu paketning
`business_requirements` modulida saqlanadi va bu modul ularni
**takrorlamaydi** — import qiladi, test ikkala hujjatdan parse qiladi.

## To'rtinchi topilma: `BRL-09` ning «30» soni repoda hech qayerda yo'q

Statistik ahamiyatsizlik sinfi mavjud — lekin boshqa mexanizm va boshqa
sonlar bilan: davomiylik kesimida `MIN_SAMPLE = 5`, vitrinada Coverage
Index ogohlantirishi va `maturity` pometasi. «Случаев < 30 → помечается
как незначимая» qoidasi aynan shu ko'rinishda qurilmagan.

## Beshinchi topilma: `BRL-15` ning kirishi bor, mexanizmi yo'q

GPS aniqligi ushlanadi (`Location.horizontal_accuracy` → analitika
hodisasi `report_created.accuracy`), lekin skoringga **kirmaydi**:
`reports.weight = source.weight × user_factor` (`06` §10), aniqlik
a'zosi formulada yo'q. Ya'ni qoidaning sharti o'lchanadi, oqibati
qurilmagan.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi: TTL o'zgartirilmadi (👤 savol, `BR-014` bilan
bitta), `AUTHORITATIVE_CONFIDENCE` ga tegilmadi (`06` sonni bermaydi —
👤 savol), statistika agregatiga `layer` kesimi qo'shilmadi (`05` §7.2
dan tashqari ish), «30» soni kiritilmadi (`06` §9 konfiguratsiya
jadvalida bunday kalit yo'q — spetsifikatsiya o'zgarishi kerak).
Modul o'lchaydi, tahrirlamaydi (75–77, 82–87, 99–101 runlar qoidasi).

Modul `app/release/` da yashaydi; runtime `app.*` modullaridan hech
narsa import qilmaydi — yagona istisno qo'shni reyestr
(`business_requirements`): `Delivered` shkalasi va TTL/jitter sonlari
bitta joyda tursin (`acceptance` ↔ `gates` bilan bir xil naqsh).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.release.business_requirements import DELIVERED_KEPT, DOC_STATUS, Delivered

#: Hujjat bo'limi. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "BRD §13"

#: `BRL-*` qatorlari soni. Hujjatdan parse qilinadi va solishtiriladi.
SPEC_ROWS = 15

#: «ЕСЛИ … ТО …» shaklida bo'lmagan qatorlar — qat'iy kategorik
#: hukmlar. Test hujjatdan qayta sanaydi: qator «ЕСЛИ» bilan
#: boshlanmasa, u shu to'plamda bo'lishi shart.
CATEGORICAL_CODES: frozenset[str] = frozenset(
    {"BRL-06", "BRL-08", "BRL-11", "BRL-14"}
)

#: Rasmiy qatlam haqidagi ikki qator. Ular ziddiyat emas — bitta
#: qatlamning ikki tomoni, va ikkalasi ham buzilgan, har biri **o'z**
#: sababi bilan: `BRL-03` ishonchni taqiqlangan chegaraga qo'yadi,
#: `BRL-08` esa statistika agregatida qatlamni yo'qotadi. Test
#: ikkalasining ham `BUILT` emasligini qulflaydi.
OFFICIAL_PAIR: tuple[str, str] = ("BRL-03", "BRL-08")

#: `BRL-03` ning ikki tomoni: qator nomlab taqiqlagan «предельное
#: значение» va kod tanlagan son. Ular **teng** — ziddiyat shundan
#: iborat. `06` §2.2 sonni umuman bermaydi.
CONFIDENCE_CEILING = 100
BUILT_AUTHORITATIVE_CONFIDENCE = 100

#: `BRL-08` buzilgan joy: statistika agregatining manba so'rovi.
#: `Outage.layer` bu so'rovda na tanlanadi, na filtrlanadi.
STATS_ROWS_QUERY = "app.clustering.repository:stats_rows_started_between"

#: `BRL-09` ning ikki tomoni: hujjat soni va kod sonlari.
#: 30 hujjatda bor, kodda yo'q; 5 kodda bor, hujjatda yo'q.
DOC_MIN_CASES = 30
BUILT_MIN_SAMPLE = 5

#: «Bo'sh bajarilgan» sinfining belgisi — 101-run (`business_
#: requirements.vacuously_honored`) bilan bir idioma. Qoida bugun
#: buzilmaydi, chunki uni buzadigan sirt yo'q; sirt paydo bo'lgan kuni
#: taqiqni hech narsa ushlab turmaydi. Belgi `gap` matnida turadi va
#: test uni shu konstantadan qidiradi.
VACUOUS_MARKER = "sirt yo'qligi"


class Form(StrEnum):
    """Qatorning grammatik shakli — hujjatdan hisoblanadi."""

    #: «ЕСЛИ <shart>, ТО <oqibat>» — shartli qoida.
    CONDITIONAL = "conditional"
    #: Shartisiz qat'iy hukm («ВСЕГДА», «НИКОГДА», «ЗАПРЕЩЕНО»).
    CATEGORICAL = "categorical"


class BusinessRulesError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class Rule:
    """§13 ning bitta `BRL-*` qatori va uning bugungi bahosi."""

    code: str
    #: Qoidaning qisqa mazmuni — o'quvchi uchun, hujjat matni emas.
    summary: str
    form: Form
    delivered: Delivered
    #: §8 dagi egizak qatorlar (`business_requirements.REQUIREMENTS`
    #: kodlari). Bo'sh — qoidaning §8 da jufti yo'q degani; test
    #: e'lon qilingan har bir egizakning mavjudligini va sinflar
    #: mosligini tekshiradi.
    twins: tuple[str, ...]
    #: Nima uchun aynan shu baho. Keyingi o'quvchi uchun.
    note: str
    #: Dalil: `modul:simvol` yoki `tests/fayl.py`.
    binds: tuple[str, ...] = ()
    #: Da'vo bilan qurilgan narsa orasidagi farq. `BUILT` da bo'sh
    #: bo'lishi mumkin, qolgan sinflarda majburiy.
    gap: str = ""


# --------------------------------------------------------------------------
# Reyestr — BRD §13 qatorlari, hujjatdagi tartibda
# --------------------------------------------------------------------------

RULES: tuple[Rule, ...] = (
    Rule(
        code="BRL-01",
        summary=(
            "Qamrov ichida — tuman/mahalla/H3 ga biriktirish; "
            f"tashqarida — `{DOC_STATUS}` bilan saqlash"
        ),
        form=Form.CONDITIONAL,
        delivered=Delivered.FORKED,
        twins=("BR-001", "BR-005"),
        note=(
            "Birinchi yarmi qisman jonli: tuman va H3 har repartda "
            "to'ldiriladi, mahalla mexanizmi bo'sh jadval ustida uxlaydi "
            "(`BR-001`/`BR-003` bilan bir ildiz). Ikkinchi yarmi esa "
            "teskari qurilgan: qamrovdan tashqari repart **saqlanmaydi**, "
            f"`error.out_of_region` bilan rad etiladi — `{DOC_STATUS}` "
            "maqomi sxemada umuman yo'q (`BR-005` ning aynan o'zi)."
        ),
        binds=(
            "app.geo.pipeline:find_mahalla_id",
            "app.core.errors:OutOfRegionError",
            "app.bot.handlers:on_location",
        ),
        gap="«Сохраняется со статусом» o'rniga rad; maqom sxemada yo'q.",
    ),
    Rule(
        code="BRL-02",
        summary="Mustaqil manbalar ≥ mintaqaviy chegara (oyna ichida) → «tasdiqlangan»",
        form=Form.CONDITIONAL,
        delivered=Delivered.BUILT,
        twins=("BR-012",),
        note=(
            "`06` §4.3 sharti aynan shu qoida: og'irlangan ball, mintaqaviy "
            "`confirm.min_users`, vaqt oynasi; ikkala holat ham status "
            "mashinasida (`pending` ↔ `confirmed`) va DB testlarida yuriladi."
        ),
        binds=(
            "app.clustering.confirmation:evaluate",
            "app.clustering.status:evaluate_status",
            "tests/test_confirmation_threshold_contract.py",
        ),
    ),
    Rule(
        code="BRL-03",
        summary=(
            "Rasmiy tasdiq → uverennost yuqori (lekin maksimal emas); "
            "manbalar zid kelsa — bayroq + moderatsiya"
        ),
        form=Form.CONDITIONAL,
        delivered=Delivered.FORKED,
        twins=(),
        note=(
            "Kod boshqa modelni bajaradi va qatorning yagona aniq "
            "taqiqini buzadi: `official` manba alohida qatlamda alohida "
            "hodisa ochadi (`06` §2 «alohida qoida») va unga "
            "`AUTHORITATIVE_CONFIDENCE = 100` **to'g'ridan-to'g'ri** "
            "qo'yiladi — formula hisoblanmaydi, qiymat esa aynan "
            "taqiqlangan «предельное». `06` §2.2 sonni bermaydi, ya'ni "
            "100 ni kod tanlagan. Aholi hodisasining `confidence` iga "
            "rasmiy a'zo esa hech qachon kirmaydi (og'irlik `0.0`) — "
            "ya'ni qatlam ajratilgan, lekin ajratilgan qatlamning o'zi "
            "chegara qiymatini oladi (`OFFICIAL_PAIR`). «Конфликт "
            "источников» bayrog'i ham, moderatsiyaga yo'naltirish ham "
            "repoda yo'q."
        ),
        binds=(
            "app.reports.sources:SOURCES",
            "app.clustering.service:AUTHORITATIVE_CONFIDENCE",
            "app.clustering.confirmation:confidence",
        ),
        gap="Rasmiy qatlamda 100 (taqiqlangan chegara); konflikt bayrog'i yo'q.",
    ),
    Rule(
        code="BRL-04",
        summary="3 soat yangi xabar yo'q → avtomatik yopilish",
        form=Form.CONDITIONAL,
        delivered=Delivered.FORKED,
        twins=("BR-014",),
        note=(
            "`BR-014` ning egizagi, o'sha raqam ziddiyati: qoida **3 soat** "
            "deydi, `05` §4.4 esa `autoclose_after = 120 daq` qotiradi va "
            "kod `05` ga ergashadi. Mexanizmning o'zi to'g'ri ishlaydi "
            "(`autoclose` → `resolved`). Sonlar "
            "`business_requirements.DOC_AUTOCLOSE_H` / "
            "`BUILT_AUTOCLOSE_MIN` da — bu modul takrorlamaydi."
        ),
        binds=(
            "app.clustering.status:evaluate_status",
            "app.core.config:Settings.cluster_autoclose_after_min",
        ),
        gap="3 h (BRD) ≠ 120 min (`05` + kod) — 👤 savol, `BR-014` bilan bitta.",
    ),
    Rule(
        code="BRL-05",
        summary=(
            "«Свет вернулся» — faqat o'z otmetkasi olinadi, "
            "boshqalarniki o'z taymautigacha turadi"
        ),
        form=Form.CONDITIONAL,
        delivered=Delivered.SUBSTITUTED,
        twins=(),
        note=(
            "Niyat — bitta foydalanuvchi hodisani yopib yubormasin — "
            "bajarilgan, lekin boshqa model bilan: shaxsiy otmetka va "
            "shaxsiy taymaut degan tushunchalar sxemada yo'q. Qurilgani — "
            "mustaqil «svet keldi» xabarlarining hisoblagichi: "
            "`min_reporters` ga yetganda hodisa darhol `restored` bilan "
            "yopiladi (`05` §4.5), yetmaganda hech kimning «otmetkasi» "
            "alohida o'chirilmaydi."
        ),
        binds=(
            "app.clustering.status:evaluate_status",
            "app.reports.intake:create_report",
        ),
        gap="Shaxsiy otmetka modeli o'rniga klaster darajasidagi hisoblagich.",
    ),
    Rule(
        code="BRL-06",
        summary="Davomiylik — birinchi xabardan oxirgigacha, VA DOIM yuqori baho sifatida",
        form=Form.CATEGORICAL,
        delivered=Delivered.PARTIAL,
        twins=(),
        note=(
            "Davomiylik kesimi bor (mediana, P90, `MIN_SAMPLE`), taymer "
            "bilan yopilganlarning ulushi ochiq turadi va chegaradan "
            "oshsa ogohlantirish chiqadi — «yuqori baho» ruhi shu yerda. "
            "Lekin o'lchov birinchi→oxirgi xabar emas: `resolved_at` "
            "taymer artefaktini o'z ichiga oladi (oxirgi xabar + "
            "`autoclose_after`), va vitrinada har bir son yoniga «верхняя "
            "оценка, а не факт» belgisi qo'yilmaydi — faqat kesim "
            "darajasidagi ogohlantirish bor."
        ),
        binds=(
            "app.stats.duration:summarize",
            "tests/test_stats_duration.py",
        ),
        gap="O'lchov nuqtalari boshqa; qator darajasidagi belgi yo'q.",
    ),
    Rule(
        code="BRL-07",
        summary="Zichlik Coverage Index chegarasidan past → vitrinada ogohlantirish",
        form=Form.CONDITIONAL,
        delivered=Delivered.BUILT,
        twins=("BR-020",),
        note=(
            "Indeks hisoblanadi, `sufficient` bayrog'i vitrinada va "
            "issiqlik xaritasida, past zichlik matni i18n orqali ikkala "
            "tilda — «отсутствие участников, а не благополучие сети» "
            "aynan shu mexanizm."
        ),
        binds=(
            "app.stats.coverage:compute",
            "tests/test_stats_coverage.py",
        ),
    ),
    Rule(
        code="BRL-08",
        summary="«Aholi xabarlari» va «rasmiy manba» qatlamlari HECH QACHON aralashmaydi",
        form=Form.CATEGORICAL,
        delivered=Delivered.PARTIAL,
        twins=("BR-015",),
        note=(
            "«Единый поток» yarmi bajarilgan: `layer = 'official'` "
            "alohida qoida bilan alohida hodisa ochadi, jamoaviy xabar "
            "rasmiy hodisaga biriktirilmaydi (`find_candidate` da "
            "`Outage.layer == layer`), og'irligi `0.0`, karta va API "
            "har hodisaning `layer` ini ochiq beradi. «Одна метрика» "
            "yarmi esa buzilgan: `stats_rows_started_between` `layer` ni "
            "na tanlaydi, na filtrlaydi — rasmiy hodisa jamoaviylari "
            "bilan bitta `outages_total` ga, bitta mediana va P90 ga, "
            "bitta tuman chelagiga qo'shiladi. Reyestrning yagona "
            "mahsulot defekti; `05` §7.2 statistika kesimida `layer` ni "
            "eslatmaydi — 👤 qaysi tomon haq."
        ),
        binds=(
            "app.reports.sources:SOURCES",
            "app.clustering.repository:find_candidate",
            "app.clustering.repository:stats_rows_started_between",
            "tests/test_report_sources_contract.py",
        ),
        gap=(
            "Statistika agregati qatlamni ko'rmaydi — rasmiy va jamoaviy "
            "hodisalar bitta metrikada qo'shiladi."
        ),
    ),
    Rule(
        code="BRL-09",
        summary="Hudud/davrda holatlar < 30 → «statistik ahamiyatsiz» pometasi",
        form=Form.CONDITIONAL,
        delivered=Delivered.SUBSTITUTED,
        twins=(),
        note=(
            "Sinf bor, son va mexanizm boshqa: davomiylik kesimi "
            "`MIN_SAMPLE = 5` dan pastda `insufficient` deydi, vitrina "
            "Coverage Index ogohlantirishi va `maturity` pometasini "
            "ko'rsatadi. «30» soni repoda hech qayerda uchramaydi; "
            "`06` §9 konfiguratsiya jadvalida ham bunday kalit yo'q — "
            "qoidani so'zma-so'z qurish uchun spetsifikatsiya o'zgarishi "
            "kerak (👤)."
        ),
        binds=(
            "app.stats.duration:summarize",
            "app.stats.maturity:compute",
        ),
        gap="30 o'rniga 5; hudud kesimidagi umumiy pometa o'rniga kesim ogohlantirishlari.",
    ),
    Rule(
        code="BRL-10",
        summary="Chegaralar o'zgarsa — tarixiy statistika hodisa paytidagi kesimda",
        form=Form.CONDITIONAL,
        delivered=Delivered.BUILT,
        twins=("BR-002",),
        note=(
            "`valid_from`/`valid_to` versiyalash, `districts_for_period`, "
            "`?at=` kesimi va chegara almashinuvi kesimi — §8 dagi eng "
            "puxta qurilgan sirtning o'zi (`BR-002`)."
        ),
        binds=(
            "app.geo.queries:districts_for_period",
            "app.stats.boundaries:summarize",
            "tests/test_stats_boundaries.py",
        ),
    ),
    Rule(
        code="BRL-11",
        summary="ФИО/telefon/username saqlanmaydi; Telegram identifikatori psevdonimlashtiriladi",
        form=Form.CATEGORICAL,
        delivered=Delivered.PARTIAL,
        twins=(),
        note=(
            "Birinchi yarmi sxema darajasida rost: birorta jadvalda ФИО, "
            "telefon yoki username ustuni yo'q (test `metadata` dan "
            "o'lchaydi). Ikkinchi yarmi yo'q: `users.tg_id` xom "
            "`BigInteger` bo'lib saqlanadi, hech qanday xesh/pepper yo'q — "
            "bu `01` §20 dagi ochiq 👤 savolning aynan o'zi (hujjat "
            "tahriri yoki pepper li xesh)."
        ),
        binds=(
            "app.reports.models:User.tg_id",
            "app.admin.security:GUARANTEES",
        ),
        gap="Psevdonimlashtirish yo'q — tg_id ochiq saqlanadi (👤).",
    ),
    Rule(
        code="BRL-12",
        summary="Nashr chegarasiga yetmagan mintaqa: repart yig'iladi, karta/statistika yopiq",
        form=Form.CONDITIONAL,
        delivered=Delivered.SUBSTITUTED,
        twins=("BR-013",),
        note=(
            "`BR-013` ning egizagi: qoida **darvoza** so'raydi, qurilgani "
            "— **dislaymer**: karta har doim ochiq, yosh mintaqa pometasi "
            "va Coverage Index yoniga qo'shiladi. Chegara qiymatini "
            "hujjatning o'zi ham bilmaydi (BRD §26.4 `OQ-5`)."
        ),
        binds=(
            "app.clustering.snapshot:build_payload",
            "app.stats.maturity:compute",
        ),
        gap="Darvoza o'rniga dislaymer; chegara qiymati hujjatda ham yo'q (👤 `OQ-5`).",
    ),
    Rule(
        code="BRL-13",
        summary="Til aniqlanmagan → «Samarqand» konturida o'zbekcha",
        form=Form.CONDITIONAL,
        delivered=Delivered.BUILT,
        twins=("BR-007",),
        note=(
            "`DEFAULT_LANGUAGE = 'uz'` va `regions.default_language` "
            "(`server_default='uz'`). `BR-007` dagi nozik joy shu yerda "
            "ham amal qiladi: birinchi ekran mintaqani bila olmaydi, "
            "standart mintaqadan qat'i nazar UZ — natija qoidaga mos."
        ),
        binds=(
            "app.core.i18n:DEFAULT_LANGUAGE",
            "app.geo.models:Region.default_language",
        ),
    ),
    Rule(
        code="BRL-14",
        summary="Samarqand ↔ Toshkent solishtiruvi qamrov farqisiz TAQIQLANADI",
        form=Form.CATEGORICAL,
        delivered=Delivered.ABSENT,
        twins=("BR-022",),
        note=(
            "`BR-022` bilan bitta holat: taqiqni bajaradigan ham, "
            "buzadigan ham sirt yo'q — har vitrina bitta mintaqa bilan "
            "chegaralangan, solishtirish funksiyasi qurilmagan. Qoida "
            "bo'shliqqa tegmay o'tadi; solishtirish paydo bo'lgan kuni "
            "uni hech narsa to'sib turmaydi."
        ),
        binds=("app.stats.service",),
        gap="Taqiq mexanizmsiz: sirt yo'qligi hisobiga «bajarilgan».",
    ),
    Rule(
        code="BRL-15",
        summary="GPS aniqligi chegaradan yomon → repart og'irligi skoringda pasayadi",
        form=Form.CONDITIONAL,
        delivered=Delivered.ABSENT,
        twins=(),
        note=(
            "Kirish o'lchanadi, oqibat qurilmagan: "
            "`Location.horizontal_accuracy` bot handleridan analitika "
            "hodisasiga (`report_created.accuracy`) tushadi va shu yerda "
            "to'xtaydi. Skoring og'irligi `source.weight × user_factor` "
            "(`06` §10) — aniqlik a'zosi formulada yo'q, chegara sozlamasi "
            "ham yo'q. `06` §9 jadvalida bunday kalit yo'q — qoida "
            "spetsifikatsiya o'zgarishisiz qurilmaydi (👤)."
        ),
        binds=(
            "app.bot.handlers:on_location",
            "app.reports.sources:freeze_weight",
        ),
        gap="Aniqlik yig'iladi, lekin skoringga ta'sir qilmaydi.",
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessRulesReport:
    """BRD §13 ning bugungi holati."""

    rules: tuple[Rule, ...]

    def __post_init__(self) -> None:
        codes = [r.code for r in self.rules]
        expected = [f"BRL-{i:02d}" for i in range(1, SPEC_ROWS + 1)]
        if codes != expected:
            raise BusinessRulesError("kodlar BRL-01…BRL-15 emas yoki tartib buzilgan")
        for rule in self.rules:
            expected_form = (
                Form.CATEGORICAL if rule.code in CATEGORICAL_CODES else Form.CONDITIONAL
            )
            if rule.form is not expected_form:
                raise BusinessRulesError(
                    f"{rule.code}: shakl {rule.form} e'lon qilingan, "
                    f"{expected_form} kutilgan edi"
                )
            if not isinstance(rule.twins, tuple):
                raise BusinessRulesError(f"{rule.code}: `twins` kortej emas")
            if any(not t.startswith("BR-") for t in rule.twins):
                raise BusinessRulesError(f"{rule.code}: egizak kodi `BR-*` emas")
            if not isinstance(rule.binds, tuple):
                raise BusinessRulesError(f"{rule.code}: `binds` kortej emas")
            if any(not isinstance(b, str) or "." not in b for b in rule.binds):
                raise BusinessRulesError(f"{rule.code}: `binds` shakli buzilgan")
            if rule.delivered is Delivered.BUILT and not rule.binds:
                raise BusinessRulesError(f"{rule.code}: `BUILT` dalilsiz bo'lmaydi")
            if rule.delivered not in DELIVERED_KEPT and not rule.gap:
                raise BusinessRulesError(f"{rule.code}: farq bor, `gap` yozilmagan")
        by_code = {r.code: r for r in self.rules}
        for code in OFFICIAL_PAIR:
            if code not in by_code:
                raise BusinessRulesError(f"rasmiy qatlam juftligida {code} yo'q")
            if by_code[code].delivered in DELIVERED_KEPT:
                raise BusinessRulesError(
                    f"{code}: rasmiy qatlam juftligi `BUILT` bo'lib qolgan — "
                    "topilma yo'qolgan yoki qoida tuzatilgan"
                )

    @property
    def by_delivered(self) -> dict[Delivered, tuple[str, ...]]:
        result: dict[Delivered, list[str]] = {d: [] for d in Delivered}
        for rule in self.rules:
            result[rule.delivered].append(rule.code)
        return {d: tuple(codes) for d, codes in result.items()}

    @property
    def by_form(self) -> dict[Form, tuple[str, ...]]:
        result: dict[Form, list[str]] = {f: [] for f in Form}
        for rule in self.rules:
            result[rule.form].append(rule.code)
        return {f: tuple(codes) for f, codes in result.items()}

    @property
    def broken(self) -> tuple[Rule, ...]:
        """Yozilganidek bajarilmaydigan qoidalar. Bugun 15 dan 11 tasi."""
        return tuple(r for r in self.rules if r.delivered not in DELIVERED_KEPT)

    @property
    def categorical_built(self) -> tuple[Rule, ...]:
        """Shartsiz hukmlardan aytilganidek qurilganlari. Bugun **bo'sh**.

        To'rtala `CATEGORICAL` qator ham `BUILT` emas va bu tasodif
        emas: shartli qoidaning bajaruv nuqtasi bor — `ЕСЛИ` ni
        tekshiradigan `if`, uni qulflaydigan test. Shartsiz hukm esa
        butun tizimning xossasi: uni buzadigan yagona joy yo'q, demak
        uni ushlaydigan qorovul ham yo'q.
        """
        return tuple(
            r
            for r in self.rules
            if r.form is Form.CATEGORICAL and r.delivered in DELIVERED_KEPT
        )

    @property
    def vacuously_honored(self) -> tuple[Rule, ...]:
        """Bajaradigan sirt ham, buzadigan sirt ham yo'q qoidalar.

        Ular `ABSENT`, lekin oddiy `ABSENT` dan farq qiladi va bu farq
        muhim: bugun hech narsa buzilmayapti, ya'ni qatorni «xavfsiz»
        deb o'qish oson. Sirt paydo bo'lgan kuni esa qoidani hech
        narsa ushlab turmaydi. 101-run bilan bir idioma va bir belgi
        (`VACUOUS_MARKER`).
        """
        return tuple(
            r
            for r in self.rules
            if r.delivered is Delivered.ABSENT and VACUOUS_MARKER in r.gap
        )

    @property
    def twinned(self) -> tuple[Rule, ...]:
        """§8 da egizagi bor qoidalar — sinflar mosligini test o'lchaydi."""
        return tuple(r for r in self.rules if r.twins)

    @property
    def official_pair(self) -> tuple[Rule, Rule]:
        """Rasmiy qatlam haqidagi ikki qator — ikkalasi ham buzilgan.

        `BRL-03` ishonchni taqiqlangan chegara qiymatiga qo'yadi,
        `BRL-08` esa statistika agregatida qatlamni yo'qotadi. Ular
        bir-biriga zid emas: bitta qatlamning ikki tomoni va ikki
        alohida sabab.
        """
        by_code = {r.code: r for r in self.rules}
        left, right = OFFICIAL_PAIR
        return by_code[left], by_code[right]

    @property
    def spec_gated(self) -> tuple[Rule, ...]:
        """So'zma-so'z qurish uchun spetsifikatsiya o'zgarishi kerak bo'lganlar.

        `06` §9 konfiguratsiya jadvalida kaliti yo'q qoidalar: chegara
        qiymatini qo'yadigan joyning o'zi hujjatda mavjud emas.
        """
        return tuple(r for r in self.rules if "§9" in r.note and "yo'q" in r.note)

    @property
    def rules_hold(self) -> bool:
        """Har qoida yozilganidek bajariladimi. Bugun `False`: 15 dan 11 tasi emas."""
        return not self.broken

    @property
    def accurate(self) -> bool:
        """§13 «bajarilgan» deb o'qilsa rostmi. `rules_hold` bilan bir xil —
        §8 dagi `Warrant` o'qi bu bo'limga tegishli emas: §13 jadvalida
        «Источник» ustuni yo'q."""
        return self.rules_hold


def evaluate() -> BusinessRulesReport:
    """Reyestrdan to'liq hisobot. Argument yo'q — 85–87, 99–101 runlar qoidasi."""
    return BusinessRulesReport(rules=RULES)

"""Risk reyestri va допущения (`01` §26, §27).

**Nima uchun bu modul bor.** `01` ning oxirgi uchdan birida ikkita
jadval turadi: o'nta risk (§26) va sakkizta допущение (§27). Ular
hech qachon kod bilan solishtirilmagan — repoda «risk» so'zi
`app/release/gates.py` ning izohidan boshqa joyda uchramaydi. Ikkala
jadval ham bitta va'da beradi: har qatorning oxirgi katagida
**mitigatsiya** yoki **tekshirish usuli** nomlangan, ya'ni hujjat
«bu bilan shug'ullanilgan» deydi. Savol shu va'do haqida:
*nomlangan mitigatsiya bugun mahsulotda bormi, va u risk sodir
bo'ladigan joyga yetadimi?*

## Asosiy qaror: `Вероятность` — bashorat, va uning bir qismi allaqachon sarflangan

Reyestr `Вероятность` × `Влияние` bo'yicha o'qiladi: yuqoridan pastga,
«Высокая/Критическое» birinchi. Bu **kelajak** haqidagi tartib. Repo
esa boshqa savolga javob beradi: *shart allaqachon bajarilganmi?*

Uchta qatorda javob «ha», bittasida esa — «yo'q va endi hech qachon»:

* `RS-02` (mahalla poligonlari yo'q) 74-runda **prodda** sodir bo'ldi:
  OSM da `admin_level=8` uchun bitta obyekt bor, `mahallas` bo'sh.
* `RS-09` (rasmiy 1055 qatlami yo'q) bugungi holat: mahsulot faqat
  kraudsorsing qatlami bilan ishlaydi.
* `AS-S3` (poligonlar mashinada o'qiladigan ko'rinishda bor) —
  **rad etilgan** допущение, sababi `RS-02` bilan bir xil.
* `RS-04` (geokoder Samarqand manzillarini qoplamaydi) — mahsulot
  manzilni koordinataga **umuman** o'girmaydi (69-run), ya'ni riskning
  sharti tug'ilmaydi.

Bunday qator uchun `Вероятность` ustuni endi bashorat emas, va
mitigatsiya ustuni ham reja emas — u **bugungi xatti-harakatning
tavsifi**. Reyestrni bashorat sifatida o'qish ularni eng tinch
qatorlar qatoriga qo'yadi: «Средняя» deb yozilgan qator aslida 100%,
«Высокая» deb yozilgani esa 0%. Shuning uchun `Onset` o'qi bor va
hisobotda `spent_forecast` alohida sanaladi.

## Ikkinchi o'q: mitigatsiya **bor** va **yetadi** — bir xil narsa emas

`Cover` `Onset` ni takrorlamaydi. U bitta savolga javob beradi:
mitigatsiya riskni **qayerda** ushlaydi.

* `MECHANISED` — mexanizm bor va risk sodir bo'ladigan sirtga yetadi.
* `DISPLACED` — mexanizm bor, lekin **boshqa** sirtda. `RS-10` uchun
  Coverage Index va yosh mintaqa pometasi kodda bor, ommaviy
  sahifaning **standart** ko'rinishida esa yo'q (70-run), risk esa
  aynan tashqi o'quvchi haqida.
* `DEGENERATE` — mexanizm ishlaydi, lekin u tushadigan daraja
  ma'nosini yo'qotgan (`RS-02`, quyida).
* `INSTRUMENTED` — kod tekshirmaydi, lekin tekshiradigan **asbob**
  yozilgan va bugun yurgizsa bo'ladi (`AS-S6` ↔ `tools/recluster.py`
  sweep, 64-run).
* `SCHEDULED` — mitigatsiya odam qadami (P0-*, moliyalashtirish).
  Kodda holati **yo'q**, va bu kamchilik emas (67-run ning `EXTERNAL`
  sabog'i: tashqi qadamni mahsulot kodidan talab qilish ro'yxatni
  abadiy qizil qoldiradi).
* `NOMINAL` — mitigatsiya kelajakdagi qayta ko'rib chiqishni nomlaydi,
  mexanizm esa umuman yo'q (`RS-06` ning «пересмотр сетки снапа»).

Bitta katakda bir nechta mitigatsiya bo'lishi mumkin va ular **turli
sinfda** bo'ladi (71-run sabog'i: `;` dan keyingi ikkinchi da'vo
birinchisining orqasida yashirinadi). Shuning uchun katak `Clause`
larga bo'linadi, qatorning `cover` i esa **eng kuchli** bandi bo'yicha
olinadi: mitigatsiyalar alternativa, ya'ni risk eng yaxshi bandi
qanchalik ushlasa shunchalik ushlangan. Audit yuki esa aksincha —
`SCHEDULED` bandlar **soni** bo'yicha, va u alohida sanaladi.

## `SCHEDULED` ning tuzog'i: uni yolg'onga chiqarib bo'lmaydi

O'n sakkiz qatordan **o'ntasi** P0-* ga yoki tashqi qarorga tayanadi.
Ular kamchilik emas, lekin ularning hammasi bitta xossani baham
ko'radi: Faza 0 tekshiruvining **natijasi repoda saqlanmaydi**.
70-run buni `01` §23 ning nazorat namunasi uchun ochiq savol qilib
qo'ygan edi; §26/§27 ko'rsatadiki, bu bitta qatorning emas,
reyestrning **yarmi**ning xossasi. Ya'ni bugun hech kim
«`P0-4` bajarildimi?» degan savolga kod bilan javob bera olmaydi va
bajarilmaganini ham hech narsa ushlamaydi. `unauditable_count` shu
sonni hisobotda ochiq ko'rsatadi.

## Eng jim topilma: `RS-08` — jadvaldagi eng tinch qator

`RS-08` yagona «Вероятность: **Низкая**» qatori va uning mitigatsiyasi
jadvaldagi eng ishonchli jumla: «Язык — параметр конфигурации, откат
без релиза». Mexanizm **bor**: `regions.default_language` ustuni
(`01` §17 da Toshkent sxemasidan farq sifatida alohida sanalgan),
`tools/region_admin.py update --lang` uni relizsiz o'zgartiradi va
`i18n.pick_language()` uni hisobga oladi (28-run).

Lekin u **botga yetmaydi**, gipoteza esa botda o'lchanadi. `/start` da
koordinata yo'q, ya'ni mintaqa ham yo'q; `register_user` tilni
`intake.get_or_create_user` ga topshiradi, u esa
`i18n.normalize_language()` ni chaqiradi va uning tayanchi —
`regions.default_language` ham, `Settings.default_language` ham emas,
**modul konstantasi** `i18n.DEFAULT_LANGUAGE = "uz"`. `app/bot/` da
`pick_language` umuman chaqirilmaydi.

Oqibati: `region_admin update --lang ru` API va veb javoblarini
o'zgartiradi, bot satrlarining esa **birortasini ham** o'zgartirmaydi
— holbuki «UZ-first ухудшает конверсию» gipotezasining konversiyasi
aynan botning birinchi ekranidan boshlanadi (`01` §21 ning
`bot_start` voronkasi, `AS-S2` ning «замер» i). Ya'ni orqaga qaytarish
yo'li gipoteza sinaladigan sirtda yo'q → `DISPLACED`, `MECHANISED`
emas. Bugun hech narsa yiqilmaydi: bitta mintaqa bor va uning
standart tili baribir `uz` (`i18n/__init__.py` ning «jim defekt»
izohi bilan bir sinf).

## `RS-02`: mitigatsiya ishlaydi, tushadigan darajasi esa bitta katak

`FR-S-802` «деградация до уровня района» ni va'da qiladi va u kodda
bor: `geo.pipeline.find_mahalla_id()` poligon topilmasa `None`
qaytaradi va xabar **xatosiz** qabul qilinadi (`FR-S-802` ning AC si
aynan shuni talab qiladi; katakdagi `MAHALLA_POLYGON_MISSING` kodi
esa repoda umuman yo'q va bo'lmasligi ham to'g'ri).

Ma'nosini yo'qotadigan narsa — **daraja**. 74-run ning ADR-07 qarori
bo'yicha chegaralar OSM `admin_level=6` dan olindi, ya'ni pilot shahri
mintaqaning **bitta** `district` i. Shahar ichidagi hamma xabar bitta
`district_id` ga tushadi: `stats` da bitta bucket, `06` §5.3
tarqoqligi (`cell_ratio_district`) bitta hudud ustida, xaritada bitta
poligon. «Tuman darajasiga tushish» shahar foydalanuvchisi uchun
«hech qanday lokalizatsiya yo'q» degani. Hech narsa yiqilmaydi:
`districts` bo'sh emas, hamma so'rov to'g'ri javob beradi.

Yon effekt sifatida `FR-S-802` va `FR-S-804` bir xil shart uchun
**ikki xil** zaxira darajasini nomlaydi (tuman va H3 r8–9), va bugun
ma'nolisi ikkinchisi. Bu hujjat qarori, shuning uchun tuzatilmadi —
`PROGRESS.md` ning «Ochiq savollar» ida.

## Teskari yo'nalish: reyestrda bo'lmagan risk

§26 ning yagona maxfiylik qatori `RS-06` — **agregatdan**
reidentifikatsiya, ya'ni nozik va hali sodir bo'lmagan hodisa. Ayni
paytda qo'polrog'i allaqachon sodir bo'lgan va reyestrda yo'q: aniq
uy koordinatasi (`reports.geom_exact`) 90 kundan keyin o'chirilishi
kerak edi (`05` §3.2, §8), `purge_exact_geom` esa 73-run topgan sxema
defekti tufayli har yurishda yiqilardi; ustiga SQL jurnali standart
holatda yoqiq bo'lib, `INSERT` parametrlari bilan o'sha koordinatalar
konteyner jurnaliga tushardi (56-run). Ikkala tuzatish ham kodda bor,
lekin **prodda hali tasdiqlanmagan** (`0010` migratsiyasi va image
qayta yig'ilishi odam ishi). Reyestr bu haqda jim.

`UNDECLARED` shu qatorni saqlaydi. U hisoblanadigan qator emas —
`accurate` ni `False` qiladi va hujjatga qo'shilishi kerakligini
aytadi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Ikkala jadvalning hujjatdagi manzili.
SPEC_RISKS = "01 §26"
SPEC_ASSUMPTIONS = "01 §27"

#: Qatorlar soni. **Aynan**: ikkala ro'yxat ham yopiq.
SPEC_RISK_ROWS = 10
SPEC_ASSUMPTION_ROWS = 8

#: Mitigatsiya katagi ichida bandlarni ajratadigan belgilar. `,` va `+`
#: ham kiradi: `RS-06`/`RS-10` vergul bilan, `AS-S2` esa `+` bilan
#: yozilgan. Kontrakt testi bandlarni shu belgilar bo'yicha hujjat
#: katagiga qaytarib yig'adi.
CLAUSE_SEPARATORS = ";,+"


class Kind(StrEnum):
    """Qator qaysi jadvaldan."""

    RISK = "risk"
    ASSUMPTION = "assumption"


class Cover(StrEnum):
    """Mitigatsiya riskni **qayerda** ushlaydi.

    Yuqoridagi izohga qarang. Tartib ma'noli — `COVER_RANK` ga qarang.
    """

    #: Mexanizm bor va risk sodir bo'ladigan sirtga yetadi.
    MECHANISED = "mechanised"
    #: Mexanizm bor, lekin boshqa sirtda.
    DISPLACED = "displaced"
    #: Mexanizm ishlaydi, tushadigan darajasi ma'nosini yo'qotgan.
    DEGENERATE = "degenerate"
    #: Kod tekshirmaydi, tekshiradigan asbob bor.
    INSTRUMENTED = "instrumented"
    #: Odam qadami (P0-*, tashqi qaror). Kodda holati yo'q.
    SCHEDULED = "scheduled"
    #: Kelajakdagi qayta ko'rib chiqish nomlangan, mexanizm yo'q.
    NOMINAL = "nominal"


#: `Cover` ning **himoya kuchi** bo'yicha tartibi (kattasi kuchliroq).
#:
#: Ikkita qaror shu jadvalda:
#:
#: 1. `INSTRUMENTED` `DEGENERATE` dan **past**. `DEGENERATE` mexanizm
#:    mahsulotda ishlab turibdi va hech bo'lmasa qisman himoya beradi;
#:    `INSTRUMENTED` esa hech nimadan himoya qilmaydi — u faqat
#:    «savolga bugun javob bersa bo'ladi» deydi. Aksincha tartiblash
#:    `AS-S6` ni `RS-02` dan xavfsizroq ko'rsatardi.
#: 2. `DISPLACED` `DEGENERATE` dan **past**, garchi intuitsiya teskarisini
#:    aytsa ham («ishlaydigan mexanizm buzilganidan yaxshiroq»). Sabab
#:    o'lchov nuqtasida: `DEGENERATE` mexanizm risk sodir bo'ladigan
#:    sirtda turadi va qisman ushlaydi (`RS-02` da xabar baribir
#:    biriktiriladi, faqat qo'pol darajada), `DISPLACED` esa o'sha sirtda
#:    **umuman yo'q** — `RS-10` ning tashqi o'quvchisi Coverage Index ni
#:    ko'rmaydi, u boshqa endpointda borligi unga hech narsa bermaydi.
#:    Ya'ni «boshqa joyda ishlaydi» himoya emas, hisobotdagi tasalli.
COVER_RANK: dict[Cover, int] = {
    Cover.NOMINAL: 0,
    Cover.SCHEDULED: 1,
    Cover.INSTRUMENTED: 2,
    Cover.DISPLACED: 3,
    Cover.DEGENERATE: 4,
    Cover.MECHANISED: 5,
}

#: Hisobotda «ushlangan» deb sanaladigan yagona sinf. Qolganlarining
#: hech biri `MECHANISED` ning o'rnini bosmaydi — shu jumladan
#: `DISPLACED`: mexanizmning boshqa sirtda borligi risk sodir
#: bo'ladigan sirtni himoya qilmaydi.
COVERED = Cover.MECHANISED


class Onset(StrEnum):
    """Riskning sharti allaqachon bajarilganmi."""

    #: Tasvirlangan holat bugun rost (repoda yoki prodda).
    MATERIALISED = "materialised"
    #: Shart bor, bugun sodir bo'lishi mumkin.
    LIVE = "live"
    #: Boshqa faza kerak — bugun sodir bo'la olmaydi.
    DORMANT = "dormant"
    #: Mahsulot riskni imkonsiz qiladigan tarmoqni allaqachon tanlagan.
    FORECLOSED = "foreclosed"


#: `Вероятность` ustuni endi bashorat bo'lmagan holatlar: hodisa
#: sodir bo'lgan yoki sodir bo'la olmaydi. Ikkalasi ham ustunni
#: **sarflaydi**, faqat qarama-qarshi tomonga.
SPENT_ONSETS = (Onset.MATERIALISED, Onset.FORECLOSED)


@dataclass(frozen=True)
class Clause:
    """Mitigatsiya katagining bitta bandi.

    `text` — hujjatdagi **so'zma-so'z** bo'lak. Kontrakt testi
    bandlarni katakka qaytarib yig'adi, ya'ni matnni tahrirlash yoki
    bandni tashlab ketish testni yiqitadi.

    `binds` — bandni bajaradigan kod, `modul:simvol` ko'rinishida.
    `SCHEDULED` band uchun **bo'sh** bo'lishi shart: uning holati kodda
    yo'q va bog'lanish yozib qo'yish uni tekshirilgan ko'rsatardi.
    """

    text: str
    cover: Cover
    binds: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class Entry:
    """§26 yoki §27 ning bitta qatori.

    `phrase` — riskning yoki допущение ning hujjatdagi so'zma-so'z
    matni. `forecast` — `Вероятность` (risk) yoki `Критичность`
    (допущение) ustunining so'zi; `impact` faqat risklarda bor.
    """

    code: str
    kind: Kind
    phrase: str
    forecast: str
    onset: Onset
    clauses: tuple[Clause, ...]
    impact: str = ""
    note: str = ""

    @property
    def cover(self) -> Cover:
        """Eng kuchli bandning sinfi — mitigatsiyalar alternativa."""
        return max(self.clauses, key=lambda c: COVER_RANK[c.cover]).cover

    @property
    def is_covered(self) -> bool:
        return self.cover is COVERED

    @property
    def unauditable_clauses(self) -> tuple[Clause, ...]:
        """Kodda holati yo'q bandlar — yolg'onga chiqarib bo'lmaydi."""
        return tuple(c for c in self.clauses if c.cover is Cover.SCHEDULED)

    @property
    def forecast_is_spent(self) -> bool:
        """`Вероятность`/`Критичность` ustuni endi bashorat emasmi."""
        return self.onset in SPENT_ONSETS


@dataclass(frozen=True)
class UndeclaredRisk:
    """Repoda ko'rinadigan, §26 da esa yo'q risk (teskari yo'nalish)."""

    code: str
    phrase: str
    #: Nima uchun u §26 ning mavjud qatorlari bilan qoplanmaydi.
    why_not_covered: str
    binds: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# §26 — risklar
# --------------------------------------------------------------------------

#: **Tartib ma'noli** — hujjatdagi bilan bir xil, kontrakt testi
#: shuni qulflaydi.
RISKS: tuple[Entry, ...] = (
    Entry(
        code="RS-01",
        kind=Kind.RISK,
        phrase="Холодный старт: карта остаётся пустой, продукт бесполезен",
        forecast="Высокая",
        impact="Критическое",
        onset=Onset.LIVE,
        note=(
            "Mintaqa 74-runda prodda `activate` qilingan va ommaviy sirtlar "
            "javob beradi. E10 (yopiq yig'ish) — **kommunikatsiya** qadami, "
            "texnik to'siq emas: bo'sh xaritani bugun ham ochiq ko'rsatsa "
            "bo'ladi, buni hech narsa to'smaydi."
        ),
        clauses=(
            Clause(
                text="Пилот через актив махалли",
                cover=Cover.SCHEDULED,
                note="E10, odam ishi. Natijasi repoda qayd etilmaydi.",
            ),
            Clause(
                text="вердикт «данных недостаточно» вместо ложного «аварии нет»",
                cover=Cover.MECHANISED,
                binds=(
                    "app.clustering.lookup:AreaVerdict.NOT_ENOUGH_DATA",
                    "app.bot.reply:Verdict.NOT_ENOUGH_DATA",
                    "app.release.acceptance:insufficient_data_verdict_present",
                ),
                note=(
                    "E7. Verdikt botning javobiga ham, `01` §23 ning qabul "
                    "ro'yxatiga ham chiqadi."
                ),
            ),
        ),
    ),
    Entry(
        code="RS-02",
        kind=Kind.RISK,
        phrase="Полигоны махаллей недоступны или неточны",
        forecast="Высокая",
        impact="Высокое",
        onset=Onset.MATERIALISED,
        note=(
            "74-run prodda: OSM `survey` 8-darajada bitta obyekt topdi, "
            "`mahallas` bo'sh. Reyestr uni «Вероятность: Высокая» deb "
            "ushlab turibdi, aslida 100%."
        ),
        clauses=(
            Clause(
                text="P0-4",
                cover=Cover.SCHEDULED,
                note="Faza 0 tekshiruvi; natijasi repoda saqlanmaydi.",
            ),
            Clause(
                text="деградация до уровня района (FR-S-802)",
                cover=Cover.DEGENERATE,
                binds=(
                    "app.geo.pipeline:find_mahalla_id",
                    "app.stats.mahalla_coverage:MahallaCoverage",
                ),
                note=(
                    "Mexanizm bor va xatosiz ishlaydi, lekin ADR-07 "
                    "(`admin_level=6`) bo'yicha pilot shahri bitta "
                    "`district`: shahar ichidagi hamma xabar bitta bucketga "
                    "tushadi."
                ),
            ),
        ),
    ),
    Entry(
        code="RS-03",
        kind=Kind.RISK,
        phrase="Административная реорганизация районов ломает историю",
        forecast="Средняя",
        impact="Высокое",
        onset=Onset.DORMANT,
        note="Bugungacha bitta ham qayta tashkil etish bo'lmagan.",
        clauses=(
            Clause(
                text="Версионирование границ (FR-S-803)",
                cover=Cover.MECHANISED,
                binds=(
                    "app.geo.models:District.valid_to",
                    "app.geo.queries:districts_for_period",
                    "app.stats.boundaries:summarize",
                ),
                note=(
                    "25-run. `FR-S-803` ning ikkala AC si ham bajariladi: "
                    "davr chegaralari bo'yicha so'rov va javobdagi "
                    "`version`/`versions`."
                ),
            ),
        ),
    ),
    Entry(
        code="RS-04",
        kind=Kind.RISK,
        phrase="Геокодер не покрывает адреса Самарканда",
        forecast="Высокая",
        impact="Среднее",
        onset=Onset.FORECLOSED,
        note=(
            "69-run: mahsulot manzilni koordinataga umuman o'girmaydi — bot "
            "Telegram `location` pini bilan ishlaydi. Riskning sharti "
            "tug'ilmaydi, ya'ni «Вероятность: Высокая» 0%. `GEOCODER_*` "
            "sozlamalari saqlanib qolgan: geokoder ulansa risk qaytadi."
        ),
        clauses=(
            Clause(
                text="P0-5",
                cover=Cover.SCHEDULED,
                note="Faza 0 tekshiruvi; bugun predmeti yo'q.",
            ),
            Clause(
                text="режим «точка на карте»",
                cover=Cover.MECHANISED,
                binds=(
                    "app.bot.handlers:on_location",
                    "app.obs.monitoring:REQUIREMENTS",
                ),
                note=(
                    "Zaxira emas, **yagona** rejim. `monitoring.py` ning "
                    "`no_geocoder` bo'shlig'i shuni yozib qo'ygan."
                ),
            ),
        ),
    ),
    Entry(
        code="RS-05",
        kind=Kind.RISK,
        phrase="Частота отключений ниже порога востребованности",
        forecast="Средняя",
        impact="Критическое",
        onset=Onset.DORMANT,
        note=(
            "Javob ma'lumot to'planganidan keyin chiqadi; P0-2 esa "
            "ishga tushirishdan **oldin**, tashqi manbadan."
        ),
        clauses=(
            Clause(
                text="P0-2 до любых вложений",
                cover=Cover.SCHEDULED,
                note="Faza 0; natijasi repoda saqlanmaydi.",
            ),
        ),
    ),
    Entry(
        code="RS-06",
        kind=Kind.RISK,
        phrase="Реидентификация в малой махалле по огрублённой точке",
        forecast="Средняя",
        impact="Высокое",
        onset=Onset.DORMANT,
        note=(
            "Kichik mahallani aniqlaydigan ma'lumotning o'zi yo'q "
            "(`mahallas` bo'sh — `RS-02`). Bazaviy maxfiylik mexanizmi "
            "(jitter, r9, `geom_exact` API da yo'q) **bor** va 60-run uni "
            "qulflagan, lekin bu qator uni emas, **moslashuvchan** to'rni "
            "nomlaydi."
        ),
        clauses=(
            Clause(
                text="OQ-04",
                cover=Cover.SCHEDULED,
                note="Ochiq savol; qarori odamniki.",
            ),
            Clause(
                text="пересмотр сетки снапа для малых полигонов",
                cover=Cover.NOMINAL,
                note=(
                    "Mexanizm yo'q: `latlng_to_cell(..., 9)` uchta joyda "
                    "qat'iy (60-run), poligon o'lchamiga qarab to'rni "
                    "o'zgartiradigan kod yozilmagan."
                ),
            ),
        ),
    ),
    Entry(
        code="RS-07",
        kind=Kind.RISK,
        phrase="Нет финансирования регионального расширения",
        forecast="Высокая",
        impact="Критическое",
        onset=Onset.DORMANT,
        note="67-run ning `EXTERNAL` sinfi — mahsulot kodidan talab qilinmaydi.",
        clauses=(
            Clause(
                text="Наследует C-04",
                cover=Cover.SCHEDULED,
                note="Toshkent paketidan meros cheklov.",
            ),
            Clause(
                text="шлюз Phase 0",
                cover=Cover.SCHEDULED,
                note=(
                    "`03` §6 gate lari kodda bor (66-run), lekin bu band "
                    "moliyaviy qarorni nomlaydi, gate ning o'zini emas."
                ),
            ),
        ),
    ),
    Entry(
        code="RS-08",
        kind=Kind.RISK,
        phrase="Языковая гипотеза неверна, UZ-first ухудшает конверсию",
        forecast="Низкая",
        impact="Среднее",
        onset=Onset.LIVE,
        note=(
            "Jadvaldagi yagona «Низкая» qator. Yuqoridagi izohga qarang: "
            "orqaga qaytarish yo'li API/veb da bor, **botda yo'q**, "
            "gipoteza esa botda o'lchanadi."
        ),
        clauses=(
            Clause(
                text="Язык — параметр конфигурации, откат без релиза",
                cover=Cover.DISPLACED,
                binds=(
                    "app.geo.models:Region.default_language",
                    "app.core.i18n:pick_language",
                    "app.core.i18n:DEFAULT_LANGUAGE",
                    "app.reports.intake:get_or_create_user",
                ),
                note=(
                    "`region_admin update --lang` relizsiz ishlaydi, lekin "
                    "`app/bot/` da `pick_language` chaqirilmaydi: yangi "
                    "foydalanuvchining tili Telegram mijozining tili yoki "
                    "modul konstantasi `DEFAULT_LANGUAGE`."
                ),
            ),
        ),
    ),
    Entry(
        code="RS-09",
        kind=Kind.RISK,
        phrase="Отсутствие регионального канала 1055 лишает официального слоя",
        forecast="Средняя",
        impact="Среднее",
        onset=Onset.MATERIALISED,
        note=(
            "Bugun rasmiy qatlam yo'q. Sababi noma'lum — kanal yo'qmi yoki "
            "P0-1 hali yurgizilmaganmi (73-run ning `PRESUMED` qatori); "
            "natija bir xil."
        ),
        clauses=(
            Clause(
                text="P0-1",
                cover=Cover.SCHEDULED,
                note="Faza 0; natijasi repoda saqlanmaydi.",
            ),
            Clause(
                text="запуск только с краудсорсинговым слоем",
                cover=Cover.MECHANISED,
                binds=(
                    "app.reports.sources:SOURCES",
                    "app.reports.sources:AUTHORITATIVE_CODES",
                    "app.obs.monitoring:REQUIREMENTS",
                ),
                note=(
                    "Mahsulot rasmiy manbasiz to'liq ishlaydi. ⚠️ 73-run "
                    "ochiq savoli: `official`/`operator_api` seedi "
                    "`is_authoritative=True` bilan yozilgan, ya'ni kanal "
                    "paydo bo'lgan kuni birinchi xabar hodisani darhol "
                    "tasdiqlaydi."
                ),
            ),
        ),
    ),
    Entry(
        code="RS-10",
        kind=Kind.RISK,
        phrase="Некорректная интерпретация молодой статистики в СМИ",
        forecast="Средняя",
        impact="Высокое",
        onset=Onset.LIVE,
        note=(
            "`01` §25 ning R1 kommunikatsiya bandi aynan shu riskka "
            "havola qiladi. Ommaviy sahifa va API bugun javob beradi."
        ),
        clauses=(
            Clause(
                text="Дисклеймер молодого региона",
                cover=Cover.DISPLACED,
                binds=(
                    "app.stats.maturity:compute",
                    "app.release.acceptance:maturity_share",
                ),
                note=(
                    "23-run. Sahifada `showMaturity` `refreshHeat` dan "
                    "chaqiriladi, `heatOn` esa standart holatda `false` "
                    "(70-run) — ya'ni tashqi o'quvchi uni ko'rmaydi."
                ),
            ),
            Clause(
                text="Coverage Index",
                cover=Cover.DISPLACED,
                binds=(
                    "app.stats.coverage:CoverageIndex",
                    "app.release.acceptance:index_share",
                ),
                note=(
                    "22-run. `index_share()` bugun 3/5: `GET /api/v1/map` "
                    "va sahifaning standart ko'rinishi indekssiz."
                ),
            ),
        ),
    ),
)


# --------------------------------------------------------------------------
# §27 — допущения
# --------------------------------------------------------------------------

ASSUMPTIONS: tuple[Entry, ...] = (
    Entry(
        code="AS-S1",
        kind=Kind.ASSUMPTION,
        phrase="Отключения в Самарканде достаточно часты",
        forecast="Критическая",
        onset=Onset.DORMANT,
        note="`RS-05` ning ijobiy shakli; bir xil tekshiruv, bir xil holat.",
        clauses=(Clause(text="P0-2", cover=Cover.SCHEDULED),),
    ),
    Entry(
        code="AS-S2",
        kind=Kind.ASSUMPTION,
        phrase="Узбекский — предпочтительный язык интерфейса в регионе",
        forecast="Высокая",
        onset=Onset.LIVE,
        note=(
            "`RS-08` bilan bir juft: bu qator gipotezani **o'lchaydi**, "
            "`RS-08` esa noto'g'ri chiqsa nima qilishni aytadi."
        ),
        clauses=(
            Clause(text="P0-3", cover=Cover.SCHEDULED),
            Clause(
                text="замер",
                cover=Cover.DISPLACED,
                binds=("app.analytics.dashboards:DASHBOARDS",),
                note=(
                    "68-run: `uz_session_share` bor, lekin u Telegram "
                    "mijozining tilini sanaydi, tanlangan tilni emas "
                    "(`detected_is_not_chosen`), va «сессия» ta'rifi yo'q "
                    "(`session_is_undefined`)."
                ),
            ),
        ),
    ),
    Entry(
        code="AS-S3",
        kind=Kind.ASSUMPTION,
        phrase="Полигоны махаллей существуют в машинно-читаемом виде",
        forecast="Высокая",
        onset=Onset.MATERIALISED,
        note=(
            "Допущение **rad etilgan**: 74-run prodda OSM 8-darajada bitta "
            "obyekt topdi. `RS-02` bilan bir xil hodisa, ikki jadvalda "
            "ikki marta yozilgan va ikkalasi ham hali ochiq turibdi."
        ),
        clauses=(Clause(text="P0-4", cover=Cover.SCHEDULED),),
    ),
    Entry(
        code="AS-S4",
        kind=Kind.ASSUMPTION,
        phrase="Махаллинские чаты пригодны как канал первичного набора",
        forecast="Высокая",
        onset=Onset.DORMANT,
        note=(
            "73-run: `01` §18 da «Махаллинские чаты» — `EXTERNAL`, "
            "«Вне системы». Kod yozilmagani qarz emas, qaror."
        ),
        clauses=(Clause(text="P0-6", cover=Cover.SCHEDULED),),
    ),
    Entry(
        code="AS-S5",
        kind=Kind.ASSUMPTION,
        phrase="Telegram доминирует в регионе так же, как в столице",
        forecast="Средняя",
        onset=Onset.DORMANT,
        note=(
            "`AS-S2` bilan bitta tekshiruvni baham ko'radi (P0-3), lekin "
            "boshqa savol beradi va uni `dashboards.py` ning `uz_session_share` "
            "i ham o'lchamaydi: mahsulot faqat Telegramda yashaydi, ya'ni "
            "Telegramda bo'lmagan odam voronkaga umuman kirmaydi."
        ),
        clauses=(Clause(text="P0-3", cover=Cover.SCHEDULED),),
    ),
    Entry(
        code="AS-S6",
        kind=Kind.ASSUMPTION,
        phrase="Ташкентские параметры кластеризации применимы после перекалибровки",
        forecast="Средняя",
        onset=Onset.LIVE,
        note=(
            "Toshkent qiymatlari bugun prodda: `DEFAULTS` → "
            "`region_config` seedi. Допущение sinalmagan, lekin sinash "
            "asbobi tayyor."
        ),
        clauses=(
            Clause(
                text="Калибровка на первых данных",
                cover=Cover.INSTRUMENTED,
                binds=(
                    "tools.recluster:parse_sweep",
                    "tools.recluster:EXIT_UNSTABLE",
                    "app.clustering.params:DEFAULTS",
                ),
                note="64-run: `--sweep` + `--set`, `06` §9 kalitlari bo'yicha.",
            ),
        ),
    ),
    Entry(
        code="AS-S7",
        kind=Kind.ASSUMPTION,
        phrase="Плотность застройки махалли совместима с радиусом уведомлений",
        forecast="Средняя",
        onset=Onset.LIVE,
        note=(
            "`AS-S6` bilan bir xil so'z bilan yozilgan, lekin asbobi **yo'q**: "
            "`notify.*` kalitlari `06` §9 jadvalida emas, ya'ni "
            "`tools/recluster.py --sweep` ularni yura olmaydi. Radiusning "
            "standarti hamon Toshkentniki (74-run)."
        ),
        clauses=(
            Clause(
                text="Калибровка после накопления данных",
                cover=Cover.SCHEDULED,
                note=(
                    "Mexanizm bor (`notifications.params`, 43-run), lekin u "
                    "qiymatni **qo'llaydi**; qiymatni tanlaydigan o'lchov "
                    "yozilmagan."
                ),
            ),
        ),
    ),
    Entry(
        code="AS-S8",
        kind=Kind.ASSUMPTION,
        phrase=(
            "Инфраструктурная нагрузка региона укладывается в текущий "
            "горизонт 500 тыс."
        ),
        forecast="Средняя",
        onset=Onset.DORMANT,
        note=(
            "`05` §10 ning metrikalari mahsulot va kechikish haqida; "
            "sig'im zaxirasini o'lchaydigan ko'rsatkich yo'q, ya'ni "
            "«500 тыс.» chegarasiga yaqinlashuvni hech narsa ko'rsatmaydi."
        ),
        clauses=(
            Clause(
                text="Мониторинг",
                cover=Cover.DISPLACED,
                binds=("app.obs.monitoring:REQUIREMENTS",),
                note="Kuzatuvchanlik bor, lekin bu miqdorni kuzatmaydi.",
            ),
        ),
    ),
)


#: Ikkala jadval birgalikda — reyestrning to'liq ro'yxati.
ENTRIES: tuple[Entry, ...] = RISKS + ASSUMPTIONS

ENTRY_BY_CODE: dict[str, Entry] = {e.code: e for e in ENTRIES}


#: §26 da yo'q, repoda esa ko'rinadigan risk (teskari yo'nalish).
UNDECLARED: tuple[UndeclaredRisk, ...] = (
    UndeclaredRisk(
        code="exact_geo_retention",
        phrase=(
            "Aniq uy koordinatasi 90 kundan keyin o'chirilmaydi va "
            "konteyner jurnaliga tushadi"
        ),
        why_not_covered=(
            "§26 ning yagona maxfiylik qatori `RS-06` — agregatdan "
            "reidentifikatsiya, ya'ni **hosila** ma'lumot. Bu yerda "
            "birlamchi ma'lumotning o'zi saqlanib qoladi: `05` §3.2 va §8 "
            "`purge_exact_geom` ni talab qiladi, u esa 73-run topgan sxema "
            "defekti bilan har yurishda yiqilardi; 56-run esa SQL "
            "jurnalining standart holatda yoqiqligini topdi. Ikkala "
            "tuzatish kodda bor, prodda tasdiqlanmagan (`0010` va image "
            "qayta yig'ilishi — odam ishi)."
        ),
        binds=(
            "app.reports.queries:purge_exact_geom",
            "app.core.logging:setup_logging",
        ),
    ),
)


# --------------------------------------------------------------------------
# Reyestrning o'z tekshiruvi
# --------------------------------------------------------------------------


def _check_registry() -> None:
    """Import paytida reyestrning ichki qoidalari.

    Bu tekshiruvlar kontrakt testining o'rnini bosmaydi — ular
    reyestrning **o'z ichida** ziddiyat qolmasligini kafolatlaydi,
    ya'ni yangi qator qo'shgan odam sinfni tasodifan buzmasin.

    ⚠️ Bu yerda **qatorlar soni tekshirilmaydi**, garchi
    `SPEC_RISK_ROWS`/`SPEC_ASSUMPTION_ROWS` shu modulda tursa ham.
    Sabab: sonni bu yerda tekshirish o'lik shart bo'lardi —
    kontrakt testi ikkala ro'yxatning uzunligini **hujjatdan** olib
    solishtiradi, ya'ni u qat'iyroq va reyestr sonni o'zidan
    o'lchashi ma'nosiz (61-run ning «fayl o'z nusxasini o'lchaydi»
    sabog'i). Mutatsiya tekshiruvi buni survivor sifatida ko'rsatdi.
    """
    codes = [e.code for e in ENTRIES]
    if len(set(codes)) != len(codes):
        raise ValueError(f"reyestrda takrorlangan kod: {codes}")

    for entry in ENTRIES:
        if not entry.clauses:
            raise ValueError(f"{entry.code}: mitigatsiya bandi yo'q")
        if entry.kind is Kind.RISK and not entry.impact:
            raise ValueError(f"{entry.code}: `Влияние` ustuni bo'sh")
        if entry.kind is Kind.ASSUMPTION and entry.impact:
            raise ValueError(f"{entry.code}: §27 da `Влияние` ustuni yo'q")
        for clause in entry.clauses:
            if clause.cover is Cover.SCHEDULED and clause.binds:
                raise ValueError(
                    f"{entry.code}: `SCHEDULED` band kodga bog'lanmaydi — {clause.binds}"
                )
            if clause.cover is Cover.NOMINAL and clause.binds:
                raise ValueError(
                    f"{entry.code}: `NOMINAL` band kodga bog'lanmaydi — {clause.binds}"
                )
            if clause.cover not in (Cover.SCHEDULED, Cover.NOMINAL) and not clause.binds:
                raise ValueError(f"{entry.code}: `{clause.cover}` band bog'lanishsiz")
        # Sinfi tushuntirishsiz qolmasin: `MECHANISED` dan boshqa har
        # qanday baho o'quvchidan «nega?» degan savolni oladi va javob
        # reyestrda turishi kerak.
        if entry.cover is not COVERED and not (entry.note or any(c.note for c in entry.clauses)):
            raise ValueError(f"{entry.code}: `{entry.cover}` bahosi izohsiz")
        if entry.forecast_is_spent and not entry.note:
            raise ValueError(f"{entry.code}: `{entry.onset}` izohsiz")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RiskReport:
    """`01` §26 + §27 ning bugungi holati."""

    entries: tuple[Entry, ...]
    undeclared: tuple[UndeclaredRisk, ...]

    @property
    def covered(self) -> tuple[Entry, ...]:
        return tuple(e for e in self.entries if e.is_covered)

    @property
    def by_cover(self) -> dict[Cover, tuple[Entry, ...]]:
        return {c: tuple(e for e in self.entries if e.cover is c) for c in Cover}

    @property
    def by_onset(self) -> dict[Onset, tuple[Entry, ...]]:
        return {o: tuple(e for e in self.entries if e.onset is o) for o in Onset}

    @property
    def spent_forecast(self) -> tuple[Entry, ...]:
        """`Вероятность` ustuni endi bashorat bo'lmagan qatorlar.

        Hisobotning eng muhim ro'yxati: reyestrni yuqoridan pastga
        o'qigan odam aynan shularni **noto'g'ri joyda** ko'radi.
        """
        return tuple(e for e in self.entries if e.forecast_is_spent)

    @property
    def unauditable_count(self) -> int:
        """Kodda holati yo'q bandlar soni (`SCHEDULED`).

        Ular kamchilik emas, lekin ularning natijasi repoda
        saqlanmaydi, ya'ni bajarilgani ham, bajarilmagani ham
        tekshirilmaydi.
        """
        return sum(len(e.unauditable_clauses) for e in self.entries)

    @property
    def nominal_clauses(self) -> tuple[tuple[Entry, Clause], ...]:
        """Mexanizmsiz bandlar.

        Qatorning `cover` i eng kuchli bandi bo'yicha olinadi, ya'ni
        `NOMINAL` band kuchliroq bandning orqasida **yashirinadi**
        (`RS-06`: `OQ-04` `SCHEDULED`, «пересмотр сетки» esa
        `NOMINAL`). Bu ro'yxat aynan shuning uchun bor — 71-run ning
        «ikkinchi da'vo birinchisining orqasida yashirinadi» sabog'i.
        """
        return tuple(
            (e, c) for e in self.entries for c in e.clauses if c.cover is Cover.NOMINAL
        )

    @property
    def unauditable_entries(self) -> tuple[Entry, ...]:
        """Barcha bandlari `SCHEDULED` bo'lgan qatorlar."""
        return tuple(
            e for e in self.entries if len(e.unauditable_clauses) == len(e.clauses)
        )

    @property
    def accurate(self) -> bool:
        """Reyestr bugungi haqiqatni to'g'ri tasvirlaydimi.

        Uchta shart, va uchalasi ham bugun buzilgan: har qator
        `MECHANISED` bo'lishi, `Вероятность` ustunining hech qayerda
        sarflanmagan bo'lishi va e'lon qilinmagan riskning
        bo'lmasligi.
        """
        return (
            all(e.is_covered for e in self.entries)
            and not self.spent_forecast
            and not self.undeclared
        )


def evaluate() -> RiskReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: bu modulning hamma javobi kodning tuzilishidan
    keladi (`acceptance.Evidence.STRUCTURAL` bilan bir xil sabab —
    javobni tashqaridan berish hisobotni soxtalashtirish yo'li
    bo'lardi).
    """
    return RiskReport(entries=ENTRIES, undeclared=UNDECLARED)

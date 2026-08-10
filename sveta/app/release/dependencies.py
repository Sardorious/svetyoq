"""Bog'liqliklar reyestri (`01` §28 «Dependencies»).

**Nima uchun bu modul bor.** `01` ning oxirgi jadvallaridan biri yettita
bog'liqlikni sanaydi va har biriga **uchinchi ustun** beradi:
`Блокирует`. Bu ustun boshqa jadvallarnikidan kuchliroq da'vo — u
mitigatsiya yoki tekshirish usuli emas, **to'siq** haqida gapiradi:
«bu narsa yo'q ekan, ana u boshlanmaydi». To'siq esa tekshirilishi
mumkin bo'lgan yagona da'vo turi: yo kimdir yo'lni to'sadi, yo
to'smaydi. Shu paytgacha jadval hech qachon o'qilmagan.

## Asosiy qaror: `Блокирует` ustuni **to'rt xil narsaga** ishora qiladi

Jadval bir xil ko'rinadi, lekin uchinchi ustunning kataklari bir
sinfda emas:

* **bosqich yoki reliz** — «Весь региональный запуск», «Phase 1+»,
  «Прод-запуск», «R0» (to'rtta qator);
* **funksional talab** — `FR-804` (bitta qator);
* **ochiq savol** — `OQ-01` (bitta qator);
* **mahsulot sirti** — «Официальный слой карты» (bitta qator).

Farq bezak emas: repo ularning **hammasiga** guvoh bo'la olmaydi.
Sirt — kodda, ya'ni to'siq bor-yo'qligini ko'rsatib berish mumkin.
Bosqich — odam qarori, kodda holati yo'q va bo'lishi ham shart emas
(67-run ning `EXTERNAL` sabog'i). Talab va ochiq savol esa **manzil**
bo'lishi kerak edi, va aynan shu ikkitasi manzilsiz chiqdi.

## `FR-804` va `OQ-01` — `01` da hech qayerda yo'q

`01` §8 talablarni `FR-S-801`…`FR-S-804` deb nomlaydi, ya'ni **`S`
prefiksi bilan**; prefikssiz `FR-804` butun hujjatda **faqat shu
jadvalda** uchraydi. `FR-S-804` esa geokoderga umuman aloqasi
bo'lmagan H3-agregatsiya. `OQ-01` uch marta havola qilinadi (`FR-S-801`
ning riski, `FR-S-803` ning asosi va shu jadval) va **birorta hujjatda
ta'riflanmaydi** — `01` da ham, `02` da ham, `05`/`06` da ham, BRD da
ham yo'q.

Ikkalasi ham Toshkent paketiga havola. Bu ularni xato qilmaydi —
`01` ochiqdan-ochiq delta hujjat va meros oladi. Xato qiladigan narsa
boshqa: **to'siq da'vosini tekshirib bo'lmaydi**, chunki to'silgan
narsa bu repoda ham, bu hujjatlar to'plamida ham yo'q. Shuning uchun
`Hold.VOID` alohida sinf: u «to'siq yo'q» demaydi (bu yolg'on bo'lardi)
va «to'siq bor» ham demaydi — u da'voning **manzili** yo'qligini
aytadi. `71`- va `73`-runlarning naqshi: hujjat nomlagan narsa
mavjudligini isbotlamaydi.

## Ikkita mustaqil o'q

`Supply` — bog'liqlik ta'minlanganmi; `Hold` — u yo'q ekan, §28
nomlagan narsa haqiqatan to'xtaydimi. Ular bog'liq emas va bog'liq
bo'lmagani ko'rinadi: `DP-3` (geokoder) hech qachon ta'minlanmagan,
lekin to'sadigan narsasi yo'q; `DP-4` (1055) ham ta'minlanmagan va
to'sig'i **haqiqiy**; `DP-6` (ko'p mintaqalilik) ta'minlangan va
to'sig'i o'z ishini qilgan.

## Eng jim topilma: `DP-1` — to'sadigan yagona qator to'smaydi

Jadvalning eng kuchli qatori birinchisi: poligonlar **butun mintaqaviy
ishga tushirishni** to'sadi. Repoda esa ishga tushirish qadamining
qorovuli bor va u boshqa narsani so'raydi:
`tools.region_admin._set_active` mintaqani `bbox` siz yoqmaydi —
`bbox` bu to'rtta `float`, `update --bbox` bilan **qo'lda** yoziladi va
birorta poligon talab qilmaydi. Undan keyingi yo'lda ham to'siq yo'q:
`geo.pipeline.find_district_id` poligon topilmasa `None` qaytaradi,
`reports.district_id` esa `NULL` bo'la oladi, issiqlik xaritasi H3 da
ishlaydi. Ya'ni poligonsiz mintaqani yoqish, xabar qabul qilish va
xaritani ko'rsatish mumkin.

Haqiqatan to'xtaydigan narsa bitta va u ancha torroq: statistika
vitrinasi. `stats.aggregate.MAX_UNASSIGNED_RATIO` (0.05) biriktirilmagan
xabarlar ulushi oshsa kesimni **ishonchsiz** deb belgilaydi. Bu
to'g'ri xatti-harakat va u ataylab qilingan (`FR-S-802` ning AC si
mahalla poligoni yo'qligida xabarni **xatosiz** qabul qilishni talab
qiladi), lekin u «весь региональный запуск» emas. Shuning uchun
`Hold.LEAKY`: to'siq bor, faqat §28 aytgan joyda emas.

Bu tuzatilmaydi. `FR-S-802` qonun (`CLAUDE.md` §2), ya'ni degradatsiya
— tanlangan xatti-harakat; noto'g'ri narsa jadvalning **so'zi**.

## Teskari yo'nalish: reyestrda yo'q ikkita bog'liqlik

§28 tashqi bog'liqliklarni sanaydi, lekin mahsulot bugun **ishlab
turgan** ikkita tashqi narsani nomlamaydi:

* **Telegram Bot API** — xabar qabul qilishning yagona yo'li
  (`app/bot/`); usiz `intake.create_report` gacha hech narsa yetib
  bormaydi. Jadvalda «Внешняя, сервис» sifatida yo'q, holbuki yagona
  «сервис» qatori (geokoder) mahsulotda umuman ishlatilmaydi.
* **OSM ma'lumoti va ODbL litsenziyasi** — poligonlarning haqiqiy
  manbai (ADR-07). §28 ning yagona «правовая» qatori mahsulotda
  **yo'q** bo'lgan hujjat (rasmiy akt) haqida, mahsulot **bajarayotgan**
  huquqiy majburiyat esa jadvalda yo'q: `geo.quality.ALLOWED_LICENSES`
  faqat `ODbL` ni qabul qiladi, `districts` javobi `licenses` va
  `attribution` beradi, OpenAPI hujjatida litsenziya ko'rsatilgan.
  73-run `01` §18 da Overpass API yo'qligini topgan edi — bu o'sha
  bo'shliqning huquqiy tomoni.

## Nima ataylab tekshirilmaydi

`Тип` ustuni (`Внешняя`/`Внутренняя`, `данные`/`сервис`/`правовая`/
`техническая`) baholanmaydi — u hujjatdan **so'zma-so'z** olinadi va
kontrakt testi shuni qulflaydi. Bu tasnif tashkiliy, kodda dalili
yo'q, va unga baho qo'yish reyestrni fikrga aylantirardi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Jadvalning hujjatdagi manzili.
SPEC = "01 §28"

#: Qatorlar soni. **Aynan**: ro'yxat yopiq.
SPEC_ROWS = 7

#: Jadvalning sarlavha qatori — ustunlar tarkibi ham kontrakt.
SPEC_COLUMNS: tuple[str, ...] = ("Зависимость", "Тип", "Блокирует")


class Referent(StrEnum):
    """`Блокирует` katagi **nimaga** ishora qiladi.

    Bu baho emas, hujjatning tasnifi: bitta ustunda to'rt xil sinfdagi
    narsa turadi va repo ularning hammasiga guvoh bo'la olmaydi.
    """

    #: Bosqich yoki reliz («Phase 1+», «R0», «Прод-запуск»).
    MILESTONE = "milestone"
    #: Funksional talab (`FR-804`).
    REQUIREMENT = "requirement"
    #: Ochiq savol (`OQ-01`).
    OPEN_QUESTION = "open_question"
    #: Mahsulot sirti («Официальный слой карты»).
    SURFACE = "surface"


#: Repo guvoh bo'la oladigan sinflar. `MILESTONE` — odam qadami
#: (67-run ning `EXTERNAL` sabog'i), qolgan ikkitasi esa manzil
#: bo'lishi kerak edi va bo'lmadi.
WITNESSABLE: frozenset[Referent] = frozenset({Referent.SURFACE})


class Supply(StrEnum):
    """Bog'liqlik ta'minlanganmi."""

    #: Bor va kod undan foydalanadi.
    MET = "met"
    #: Bir qismi bor (`DP-1`: tumanlar bor, mahallalar yo'q).
    PARTIAL = "partial"
    #: Yo'q; o'rnini bosadigan narsa ham yo'q.
    UNMET = "unmet"
    #: Mahsulot undan **voz kechgan** — talab ham, iste'molchi ham yo'q.
    MOOT = "moot"


class Hold(StrEnum):
    """`Блокирует` da'vosi haqiqatan to'xtatadimi."""

    #: Repoda to'siq bor va u nomlangan narsani to'xtatadi.
    ENFORCED = "enforced"
    #: To'siq bor, lekin §28 aytgan joyda emas — torroq sirtda.
    LEAKY = "leaky"
    #: To'silgan narsaning bu hujjatlarda **manzili yo'q**.
    VOID = "void"
    #: Odam bosqichi: repoda mexanizm yo'q va bo'lishi shart emas.
    UNSTATED = "unstated"


#: Hisobotda «da'vo o'z ishini qiladi» deb sanaladigan yagona sinf.
HELD = Hold.ENFORCED

#: `Hold` ning kodda **dalili bo'lishi shart** bo'lgan sinflari.
#: `VOID` va `UNSTATED` da dalil bo'lishi mumkin emas: birinchisida
#: to'silgan narsaning manzili yo'q, ikkinchisida mexanizmning o'zi
#: repodan tashqarida. Dalil yozib qo'yish ikkalasini ham
#: tekshirilgandek ko'rsatardi (`risks.SCHEDULED` bilan bir xil qoida).
HOLD_NEEDS_EVIDENCE: frozenset[Hold] = frozenset({Hold.ENFORCED, Hold.LEAKY})


@dataclass(frozen=True)
class Row:
    """§28 ning bitta qatori.

    `phrase`, `kind` va `blocks` — hujjatdagi **so'zma-so'z** kataklar;
    kontrakt testi ularni jadvaldan parse qiladi. Qolgani — baho.

    `supply_binds` / `hold_binds` — `modul:simvol` ko'rinishidagi
    yechiladigan havolalar. `UNMET` da `supply_binds` **bo'sh**:
    ta'minlanmagan narsani ta'minlaydigan kod bo'lishi mumkin emas, va
    dalil yozib qo'yish «yo'q» ni dalilli qilardi (`integrations`
    modulining `Surface.NONE` qoidasi).
    """

    code: str
    phrase: str
    kind: str
    blocks: str
    referent: Referent
    supply: Supply
    hold: Hold
    note: str
    supply_binds: tuple[str, ...] = ()
    hold_binds: tuple[str, ...] = ()

    @property
    def is_supplied(self) -> bool:
        return self.supply is Supply.MET

    @property
    def holds(self) -> bool:
        return self.hold is HELD

    @property
    def is_witnessable(self) -> bool:
        """Repo bu qatorning to'sig'iga guvoh bo'la oladimi."""
        return self.referent in WITNESSABLE


@dataclass(frozen=True)
class UndeclaredDependency:
    """Mahsulot tayanadigan, §28 da esa yo'q narsa (teskari yo'nalish)."""

    code: str
    phrase: str
    #: Nima uchun u §28 ning mavjud qatorlari bilan qoplanmaydi.
    why_not_covered: str
    binds: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# Reyestr
# --------------------------------------------------------------------------

#: **Tartib ma'noli** — hujjatdagi bilan bir xil, kontrakt testi shuni
#: qulflaydi. `code` lar §28 da yo'q (jadvalda `ID` ustuni umuman
#: yo'q) va shuning uchun tartibdan yasaladi: `DP-N` = N-qator.
ROWS: tuple[Row, ...] = (
    Row(
        code="DP-1",
        phrase="Полигоны районов и махаллей",
        kind="Внешняя, данные",
        blocks="Весь региональный запуск",
        referent=Referent.MILESTONE,
        supply=Supply.PARTIAL,
        hold=Hold.LEAKY,
        note=(
            "Tumanlar bor (ADR-07, OSM `admin_level=6`), mahallalar yo'q "
            "(`RS-02`, 74-run). Ishga tushirish qadamining qorovuli "
            "`bbox` ni so'raydi — to'rtta `float`, `update --bbox` bilan "
            "qo'lda yoziladi va poligon talab qilmaydi. Poligonsiz "
            "mintaqani yoqish, xabar qabul qilish va H3 xaritasini "
            "ko'rsatish mumkin; haqiqatan to'xtaydigani — statistika "
            "vitrinasi (`MAX_UNASSIGNED_RATIO`), ya'ni bitta sirt."
        ),
        supply_binds=(
            "app.geo.models:District",
            "app.geo.models:BoundaryStaging",
            "tools.import_boundaries:main",
        ),
        hold_binds=(
            "tools.region_admin:_set_active",
            "app.geo.pipeline:find_district_id",
            "app.stats.aggregate:MAX_UNASSIGNED_RATIO",
        ),
    ),
    Row(
        code="DP-2",
        phrase="Официальный акт о границах районов",
        kind="Внешняя, правовая",
        blocks="OQ-01",
        referent=Referent.OPEN_QUESTION,
        supply=Supply.UNMET,
        hold=Hold.VOID,
        note=(
            "`OQ-01` `01` da uch marta havola qilinadi va **birorta "
            "hujjatda ta'riflanmaydi** (`01`, `02`, `05`, `06`, BRD). "
            "Chegaralar rasmiy aktdan emas, OSM dan olinadi. `01` "
            "`FR-S-803` ni «прямая митигация OQ-01» deb ataydi va u "
            "kodda bor (25-run), ya'ni ta'riflanmagan savolning "
            "mitigatsiyasi ishlaydi — savolning o'zi manzilsiz."
        ),
    ),
    Row(
        code="DP-3",
        phrase="Геокодер с покрытием Самарканда",
        kind="Внешняя, сервис",
        blocks="FR-804",
        referent=Referent.REQUIREMENT,
        supply=Supply.MOOT,
        hold=Hold.VOID,
        note=(
            "Mahsulot manzilni koordinataga umuman o'girmaydi (69-run, "
            "`RS-04` `FORECLOSED`): `Settings.geocoder_provider` bor, "
            "standarti bo'sh va uni **birorta modul o'qimaydi**. "
            "`FR-804` esa `01` da faqat shu jadvalda uchraydi — §8 "
            "talablari `S` prefiksi bilan, va `FR-S-804` H3-agregatsiya, "
            "geokoderga aloqasi yo'q."
        ),
        supply_binds=("app.core.config:Settings",),
    ),
    Row(
        code="DP-4",
        phrase="Наличие регионального канала 1055",
        kind="Внешняя, данные",
        blocks="Официальный слой карты",
        referent=Referent.SURFACE,
        supply=Supply.UNMET,
        hold=Hold.ENFORCED,
        note=(
            "Jadvaldagi yagona tekshiriladigan to'siq va u haqiqiy. "
            "Rasmiy qatlamning butun mexanizmi bor — `outages.layer`, "
            "`LAYER_OFFICIAL`, `AUTHORITATIVE_CODES`, `06` §2.2 ning "
            "darhol tasdiqlashi — lekin `app/` da rasmiy kod bilan "
            "xabar yaratadigan **birorta chaqiruv yo'q**: "
            "`intake.create_report` ning standarti `bot` va bot uni "
            "bosmaydi. E18 (👤 H-4) ochiq."
        ),
        hold_binds=(
            "app.reports.sources:AUTHORITATIVE_CODES",
            "app.clustering.service:LAYER_OFFICIAL",
            "app.reports.intake:create_report",
        ),
    ),
    Row(
        code="DP-5",
        phrase="Решение по финансированию",
        kind="Внутренняя",
        blocks="Phase 1+",
        referent=Referent.MILESTONE,
        supply=Supply.UNMET,
        hold=Hold.UNSTATED,
        note=(
            "Odam qarori; `01` §24 uni Faza 0 dan chiqish mezoni qilib "
            "qo'ygan. Kodda holati yo'q va bo'lishi ham shart emas "
            "(67-run ning `EXTERNAL` sabog'i)."
        ),
    ),
    Row(
        code="DP-6",
        phrase="Реализация мультирегиональности (FR-807) в платформе",
        kind="Внутренняя, техническая",
        blocks="R0",
        referent=Referent.MILESTONE,
        supply=Supply.MET,
        hold=Hold.ENFORCED,
        note=(
            "Yettitadan yagona ta'minlangan qator va yagona ichki-texnik "
            "qator: E19 (18-run) mintaqani konfiguratsiyaga aylantirdi. "
            "To'siq haqiqiy va hali ham ishlaydi — `reports.region_id` "
            "`NOT NULL`, nuqta `registry.pick_for_point` orqali "
            "mintaqaga tushadi, faol bo'lmagan mintaqa xabar qabul "
            "qilmaydi. `FR-807` `01` §3 va §7 da mazmuni bilan "
            "tushuntirilgan, ya'ni `FR-804` dan farqli o'laroq "
            "manzilsiz emas."
        ),
        supply_binds=(
            "app.geo.registry:pick_for_point",
            "app.geo.models:Region",
            "tools.region_admin:cmd_add",
        ),
        hold_binds=(
            "app.geo.pipeline:region_for_point",
            "app.reports.models:Report",
        ),
    ),
    Row(
        code="DP-7",
        phrase="Юридическое заключение по ПДн",
        kind="Внешняя",
        blocks="Прод-запуск",
        referent=Referent.MILESTONE,
        supply=Supply.UNMET,
        hold=Hold.UNSTATED,
        note=(
            "`01` §20 ochiq yozadi: «Юридическая проверка не проведена "
            "(C-09)», `P0-7` esa uni Faza 0 ga qo'yadi. Repoda "
            "maxfiylik mexanizmlari bor (jitter, `geom_exact` ni "
            "o'chirish, ustunlar oq ro'yxati), lekin ularning birortasi "
            "«прод-запуск» ni to'smaydi va huquqiy xulosaning holatini "
            "saqlamaydi."
        ),
    ),
)

ROW_BY_CODE: dict[str, Row] = {r.code: r for r in ROWS}


#: §28 da yo'q, mahsulot esa bugun tayanadigan bog'liqliklar.
UNDECLARED: tuple[UndeclaredDependency, ...] = (
    UndeclaredDependency(
        code="UD-1",
        phrase="Telegram Bot API",
        why_not_covered=(
            "Xabar qabul qilishning yagona yo'li: `app/bot/` dan boshqa "
            "hech qanday kirish nuqtasi `intake.create_report` ni "
            "chaqirmaydi (`tools/simulate.py` — sun'iy generator). §28 "
            "ning yagona «сервис» qatori esa mahsulotda umuman "
            "ishlatilmaydigan geokoder."
        ),
        binds=("app.bot.service:submit_report", "app.reports.intake:create_report"),
    ),
    UndeclaredDependency(
        code="UD-2",
        phrase="Данные OSM и лицензия ODbL",
        why_not_covered=(
            "Poligonlarning haqiqiy manbai va u bilan kelgan atributsiya "
            "majburiyati. §28 ning yagona «правовая» qatori mahsulotda "
            "yo'q hujjat haqida; mahsulot **bajarayotgan** huquqiy shart "
            "jadvalda yo'q. 73-run `01` §18 da Overpass API yo'qligini "
            "topgan edi — bu o'sha bo'shliqning huquqiy tomoni."
        ),
        binds=("app.geo.quality:ALLOWED_LICENSES", "app.geo.models:District"),
    ),
)


# --------------------------------------------------------------------------
# Reyestrning o'z qoidalari
# --------------------------------------------------------------------------


def _check_registry() -> None:
    """Reyestr o'z-o'ziga zid bo'lsa import paytida yiqiladi.

    Bu tekshiruvlar kontrakt testining o'rnini bosmaydi — ular
    reyestrni **yozayotgan** odamga qaratilgan: dalilsiz baho va
    baholanmagan dalil ikkalasi ham jimgina o'tib ketardi.
    """
    if len(ROWS) != SPEC_ROWS:
        raise ValueError(f"{SPEC}: {len(ROWS)} qator, kutilgani {SPEC_ROWS}")
    if len(ROW_BY_CODE) != len(ROWS):
        raise ValueError(f"{SPEC}: takrorlangan kod")
    for index, row in enumerate(ROWS, start=1):
        if row.code != f"DP-{index}":
            raise ValueError(f"{SPEC}: `{row.code}` {index}-qatorda turibdi")
        if not row.note:
            raise ValueError(f"{SPEC}: `{row.code}` izohsiz")
        if row.supply is Supply.UNMET and row.supply_binds:
            raise ValueError(
                f"{SPEC}: `{row.code}` — `UNMET`, lekin ta'minot dalili "
                f"ko'rsatilgan: {row.supply_binds}"
            )
        if row.supply is not Supply.UNMET and not row.supply_binds:
            raise ValueError(f"{SPEC}: `{row.code}` — `{row.supply}`, dalil yo'q")
        if row.hold in HOLD_NEEDS_EVIDENCE and not row.hold_binds:
            raise ValueError(f"{SPEC}: `{row.code}` — `{row.hold}`, dalil yo'q")
        if row.hold not in HOLD_NEEDS_EVIDENCE and row.hold_binds:
            raise ValueError(
                f"{SPEC}: `{row.code}` — `{row.hold}`, lekin dalil "
                f"ko'rsatilgan: {row.hold_binds}"
            )
        # `VOID` faqat manzilsiz havola uchun. Bosqich — manzil emas,
        # lekin u **mavjud** narsa: uni `UNSTATED` ushlaydi. Aralashib
        # ketsa hisobotdagi «manzilsiz havola» soni ma'nosini
        # yo'qotardi.
        if row.hold is Hold.VOID and row.referent is Referent.MILESTONE:
            raise ValueError(f"{SPEC}: `{row.code}` — bosqich `VOID` bo'la olmaydi")
        if row.hold is Hold.UNSTATED and row.referent is not Referent.MILESTONE:
            raise ValueError(f"{SPEC}: `{row.code}` — `UNSTATED` faqat bosqichda")
        if row.is_witnessable and row.hold in (Hold.VOID, Hold.UNSTATED):
            raise ValueError(
                f"{SPEC}: `{row.code}` — sirt haqidagi da'vo tekshiriladi, "
                f"`{row.hold}` bo'la olmaydi"
            )
    for item in UNDECLARED:
        if not item.binds:
            raise ValueError(f"{SPEC}: `{item.code}` dalilsiz")
        if not item.why_not_covered:
            raise ValueError(f"{SPEC}: `{item.code}` izohsiz")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DependencyReport:
    """`01` §28 ning bugungi holati."""

    rows: tuple[Row, ...]
    undeclared: tuple[UndeclaredDependency, ...]

    @property
    def by_supply(self) -> dict[Supply, tuple[Row, ...]]:
        return {s: tuple(r for r in self.rows if r.supply is s) for s in Supply}

    @property
    def by_hold(self) -> dict[Hold, tuple[Row, ...]]:
        return {h: tuple(r for r in self.rows if r.hold is h) for h in Hold}

    @property
    def by_referent(self) -> dict[Referent, tuple[Row, ...]]:
        return {k: tuple(r for r in self.rows if r.referent is k) for k in Referent}

    @property
    def supplied(self) -> tuple[Row, ...]:
        return tuple(r for r in self.rows if r.is_supplied)

    @property
    def dangling(self) -> tuple[Row, ...]:
        """To'silgan narsaning manzili yo'q qatorlar.

        Hisobotning eng muhim ro'yxati: bunday qatorni na yopish, na
        yolg'onga chiqarish mumkin — u har qanday holatda ham
        bajarilgandek **ko'rinadi**.
        """
        return tuple(r for r in self.rows if r.hold is Hold.VOID)

    @property
    def leaky(self) -> tuple[Row, ...]:
        """To'sig'i §28 aytgan joydan torroq sirtda bo'lgan qatorlar."""
        return tuple(r for r in self.rows if r.hold is Hold.LEAKY)

    @property
    def witnessable(self) -> tuple[Row, ...]:
        """Repo to'sig'iga guvoh bo'la oladigan qatorlar."""
        return tuple(r for r in self.rows if r.is_witnessable)

    @property
    def accurate(self) -> bool:
        """Jadval bugungi haqiqatni to'g'ri tasvirlaydimi.

        Uchta shart, va uchalasi ham bugun buzilgan: manzilsiz havola
        bo'lmasin, to'siq §28 aytgan joyda tursin va e'lon qilinmagan
        bog'liqlik bo'lmasin.
        """
        return not self.dangling and not self.leaky and not self.undeclared


def evaluate() -> DependencyReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi
    (`risks.evaluate` bilan bir xil sabab).
    """
    return DependencyReport(rows=ROWS, undeclared=UNDECLARED)

"""`01` §21 «Дашборды» — analitika qatlamining **chiqishi** kodda.

**Nima uchun bu modul bor.** 29-run `01` §21 ning *Event Tracking*
jadvalini qulfladi: o'nta hodisa, ularning atributlari, chiqish
nuqtalari. Lekin §21 ikkita blokdan iborat va ikkinchisi —
«Дашборды» — o'sha paytda ham, keyin ham tekshirilmadi. U beshta
dashboardni **nom bilan** sanaydi va bittasini «Главная метрика
запуска» deb belgilaydi.

Hodisalar jadvali «nima yoziladi» degan savolga javob beradi.
Dashboardlar ro'yxati boshqa savolga: *yozilganidan nima
o'qiladi?* Ikkinchisi birinchisidan avtomatik kelib chiqmaydi —
oqimda hamma hodisa bo'lishi va shunga qaramay dashboard **noto'g'ri
sonni** ko'rsatishi mumkin. Aynan shu ikkinchi savol hech qayerda
berilmagan edi.

Natija bitta jumlaga sig'adi: **beshta dashboarddan bugun faqat
bittasi hujjatda yozilganidek quriladi** — va u, baxtga,
ishga tushirishning asosiy metrikasi.

## Uchta holat, ikkitasi emas

67-run ning sabog'i (`app.release.measures`) shu yerda ham ishlaydi:
«quriladi / qurilmaydi» ikkiligi eng muhim farqni yo'qotardi.

* `READY` — dashboard bugun hujjatda yozilganidek quriladi;
* `DEGRADED` — grafik **chiziladi**, lekin u boshqa sonni
  ko'rsatadi yoki eng muhim savoliga javob bermaydi. Bu eng xavfli
  holat: bo'sh grafik ko'rinadi, noto'g'ri grafik esa yo'q;
* `EMPTY` — hamma hodisa joyida, lekin kesim maydoni qurilishiga
  ko'ra `None`, ya'ni grafik doim bo'sh.

## To'rtinchi tushuncha: `ACCEPTED` cheklov bo'shliq emas

Har bir `DEGRADED`/`EMPTY` dashboard uchun cheklov **sababi bilan**
yozilgan, va sabablarning biri qolganlaridan farq qiladi:
`Unblocks.ACCEPTED` — bu narx **ataylab to'langan** va uni yopish
rejasi yo'q. Voronkaning «birinchi repor» qadami aynan shunday:
hodisalarda foydalanuvchi identifikatori yo'q (`01` §20), ya'ni
birinchi xabarni N-chisidan ajratib bo'lmaydi va voronka
bosqichlar sonining nisbati sifatida o'qiladi. Buni «bo'shliq»
ro'yxatiga qo'yish uni har hisobotda yopilishi kerak bo'lgan qarz
qilib ko'rsatardi; ro'yxatdan olib tashlash esa dashboardni
xatosiz ko'rsatardi. Shuning uchun u ro'yxatda, lekin bo'shliq
emas — `measures.Coverage.EXTERNAL` bilan bir xil rolda.

## Uchta topilma

1. **«Доля сессий на UZ» boshqa sonni ko'rsatadi.** Yagona manba —
   `bot_start.language_detected`, u esa Telegram mijozining
   `language_code` i (`app.bot.service.start`), foydalanuvchi
   tanlagan til emas. Telegrami `ru` bo'lgan, lekin botda `uz` ni
   tanlagan odam bu grafikda **abadiy RU** bo'lib qoladi. Ustiga
   «сессия» mahsulotda umuman yo'q: `bot_start` har `/start` da
   chiqadi, ya'ni maxraj — startlar soni, va `/start` ni qayta
   bosmagan qaytgan foydalanuvchi grafikda ko'rinmaydi. Ikkala
   og'ish ham bir tomonga: RU tomonga.
2. **Ikkita dashboard E17 gacha bo'sh, lekin turli sababdan.**
   «Плотность репортов по махаллям» — `report_created.mahalla_id`
   qurilishiga ko'ra `None`; «Coverage Index по махаллям» —
   `MahallaCoverage.available` `False`. Birinchisi oqimdagi
   bo'shliq, ikkinchisi vitrinadagi ochiq e'tirof (27-run). H3
   issiqlik xaritasi (`app.stats.heatmap`) **o'rnini bosmaydi** va
   `near` da aynan shu sababdan turadi.
3. **Katalog izohi «to'rtta dashboard» deb yozgan edi** (29-run),
   hujjatda esa **beshta**. Hech narsa yiqilmasdi: son izohda,
   izoh esa hech qayerda o'lchanmaydi. Endi son umuman yozilmaydi —
   ro'yxat shu yerda va uni hujjat qulflaydi.

Modul **toza**: bazaga ham, `settings` ga ham tegmaydi; foydalanuvchi
matni yo'q. `app.analytics.catalogue` dan boshqa hech narsani import
qilmaydi — vitrina havolalari `modul:atribut` matni bo'lib turadi va
kontrakt testida yechiladi (`app.stats` ni import qilish bu modulni
bazaga bog'lab qo'yardi).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.analytics import catalogue

#: Bu ro'yxatning hujjatdagi manzili.
SPEC = "01 §21 «Дашборды»"


class FeedSource(StrEnum):
    """Dashboard sonni qayerdan oladi."""

    #: `01` §21 hodisalar oqimi (`app.analytics.catalogue`).
    EVENT = "event"
    #: Ommaviy vitrina (`app/stats`), `modul:atribut` ko'rinishida.
    STATS = "stats"


class Readiness(StrEnum):
    """Dashboard bugun hujjatda yozilganidek quriladimi."""

    READY = "ready"
    DEGRADED = "degraded"
    EMPTY = "empty"


class Unblocks(StrEnum):
    """Cheklovni nima ochadi — ya'ni uni yopish **narxi**."""

    #: Mahalla poligonlari (E17). Odam ishi, kod bilan yechilmaydi.
    E17 = "e17"
    #: PWA/Web Push (E20) — brauzer platformasi Telegram bermaydigan
    #: signalni beradi.
    E20 = "e20"
    #: Mahsulot qarori kerak: nima o'lchanishi hal qilinmagan.
    HUMAN = "human"
    #: Ataylab to'langan narx. Bo'shliq **emas** va rejaga tushmaydi.
    ACCEPTED = "accepted"


#: Bo'shliq deb sanaladigan cheklovlar. `ACCEPTED` kirmaydi — sabab
#: modul izohida.
GAP_UNBLOCKS: frozenset[Unblocks] = frozenset(
    {Unblocks.E17, Unblocks.E20, Unblocks.HUMAN}
)


@dataclass(frozen=True)
class Feed:
    """Dashboardning bitta kirishi.

    `attribute` — hodisaning qaysi maydoni bo'yicha kesiladi.
    `None` bo'lsa dashboard hodisani **sanaydi**, kesmaydi (voronka
    bosqichlari aynan shunday).
    """

    source: FeedSource
    ref: str
    attribute: str | None = None

    def __str__(self) -> str:
        tail = f".{self.attribute}" if self.attribute else ""
        return f"{self.source}:{self.ref}{tail}"


@dataclass(frozen=True)
class Limit:
    """Dashboard nimaga qodir emasligi, sababi va narxi bilan.

    `why` — **bir jumlada** sabab. U hisobot uchun emas, keyingi
    o'quvchi uchun: cheklovni ko'rgan odam birinchi navbatda «buni
    shunchaki qo'shib qo'ysa bo'lmaydimi?» deb so'raydi va javob shu
    yerda turishi kerak.
    """

    code: str
    unblocks: Unblocks
    why: str

    @property
    def is_gap(self) -> bool:
        return self.unblocks in GAP_UNBLOCKS


@dataclass(frozen=True)
class Dashboard:
    """`01` §21 «Дашборды» ro'yxatining bitta bandi.

    `phrase` — hujjatdagi **so'zma-so'z** matn. U bezak emas: kontrakt
    testi ro'yxatni shu matn bo'yicha hujjat bilan solishtiradi, ya'ni
    bandni qayta nomlash yoki tartibini almashtirish testni yiqitadi.
    """

    code: str
    phrase: str
    feeds: tuple[Feed, ...]
    readiness: Readiness
    limits: tuple[Limit, ...] = ()
    #: Cheklovni «yopadigan» eng yaqin mavjud manba. Bog'lanish emas,
    #: **ogohlantirish** (67-run ning `Measure.near` i bilan bir xil
    #: rolda): uni o'rniga qo'yish bo'shliqni yopmaydi, ko'rinmas
    #: qiladi.
    near: tuple[Feed, ...] = ()
    #: «Главная метрика запуска». Ro'yxatda aynan bittasi.
    main: bool = False

    @property
    def is_gap(self) -> bool:
        return any(limit.is_gap for limit in self.limits)


def _event(name: str, attribute: str | None = None) -> Feed:
    return Feed(FeedSource.EVENT, name, attribute)


def _stats(ref: str) -> Feed:
    return Feed(FeedSource.STATS, ref)


# --------------------------------------------------------------------------
# Reyestr — `01` §21 «Дашборды», aynan o'sha tartibda
# --------------------------------------------------------------------------

DASHBOARDS: tuple[Dashboard, ...] = (
    Dashboard(
        code="activation_funnel",
        phrase="Воронка активации (start → geo → первый репорт)",
        feeds=(
            _event("bot_start"),
            _event("report_submit_attempt"),
            _event("report_created"),
        ),
        readiness=Readiness.DEGRADED,
        limits=(
            Limit(
                code="no_user_dimension",
                unblocks=Unblocks.ACCEPTED,
                why=(
                    "Hodisalarda foydalanuvchi identifikatori yo'q (`01` §20), "
                    "ya'ni «birinchi repor» ni N-chisidan ajratib bo'lmaydi va "
                    "voronka bosqichlar sonining nisbati sifatida o'qiladi. "
                    "Narx ataylab to'langan — `catalogue` modul izohi."
                ),
            ),
            Limit(
                code="refusal_invisible",
                unblocks=Unblocks.E20,
                why=(
                    "`start → geo` qadamidagi eng katta tushish sababsiz "
                    "qoladi: `geo_permission_denied` Telegram kanalida "
                    "kuzatilmaydi (`observable=False`), ya'ni rad etish va "
                    "shunchaki tashlab ketish bir xil ko'rinadi."
                ),
            ),
        ),
    ),
    Dashboard(
        code="report_density_mahalla",
        phrase="плотность репортов по махаллям",
        feeds=(_event("report_created", "mahalla_id"),),
        readiness=Readiness.EMPTY,
        limits=(
            Limit(
                code="mahalla_id_is_none",
                unblocks=Unblocks.E17,
                why=(
                    "`report_created.mahalla_id` qurilishiga ko'ra `None`: "
                    "mahalla poligonlari yo'q, ya'ni kesim maydonining "
                    "yagona qiymati bor va grafik doim bo'sh."
                ),
            ),
        ),
        near=(_stats("app.stats.heatmap:HeatCell.reports"),),
    ),
    Dashboard(
        code="insufficient_data_share",
        phrase="доля вердиктов «данных недостаточно»",
        feeds=(_event("verdict_shown", "verdict_type"),),
        readiness=Readiness.READY,
        main=True,
    ),
    Dashboard(
        code="uz_session_share",
        phrase="доля сессий на UZ",
        feeds=(_event("bot_start", "language_detected"),),
        readiness=Readiness.DEGRADED,
        limits=(
            Limit(
                code="detected_is_not_chosen",
                unblocks=Unblocks.HUMAN,
                why=(
                    "`language_detected` — Telegram mijozining `language_code` i, "
                    "foydalanuvchi tanlagan til emas: botda `uz` ni tanlagan "
                    "odam bu grafikda RU bo'lib qoladi. Tanlangan til faqat "
                    "`language_changed` da ko'rinadi va u qayta kirishda "
                    "chiqmaydi."
                ),
            ),
            Limit(
                code="session_is_undefined",
                unblocks=Unblocks.HUMAN,
                why=(
                    "«Сессия» mahsulotda yo'q: `bot_start` har `/start` da "
                    "chiqadi, ya'ni maxraj — startlar soni, va `/start` ni "
                    "qayta bosmagan qaytgan foydalanuvchi umuman sanalmaydi."
                ),
            ),
        ),
        near=(_event("language_changed", "to"),),
    ),
    Dashboard(
        code="mahalla_coverage_index",
        phrase="Coverage Index по махаллям",
        feeds=(_stats("app.stats.mahalla_coverage:MahallaCoverage.bands"),),
        readiness=Readiness.EMPTY,
        limits=(
            Limit(
                code="registry_unavailable",
                unblocks=Unblocks.E17,
                why=(
                    "`MahallaCoverage.available` `False` bo'lib qoladi — "
                    "spravochnik bo'sh. Vitrina buni yashirmaydi "
                    "(`stats.warning.mahallas_missing`), lekin taqsimot "
                    "baribir bo'sh."
                ),
            ),
        ),
    ),
)

DASHBOARD_BY_CODE: dict[str, Dashboard] = {d.code: d for d in DASHBOARDS}


def _check_registry() -> None:
    """Reyestrning **jimgina** buziladigan joylari — import paytida.

    Har biri hisobotni to'g'ri **ko'rinishda** qoldiradi: kod bor,
    matn bor, faqat u hech narsani tekshirmaydi.
    """
    codes = [d.code for d in DASHBOARDS]
    duplicates = sorted({c for c in codes if codes.count(c) > 1})
    if duplicates:
        raise ValueError(f"dashboard kodi takrorlangan: {duplicates}")

    mains = [d.code for d in DASHBOARDS if d.main]
    if len(mains) != 1:
        # `01` §21 «Главная метрика запуска» ni **bitta** deb yozadi;
        # ikkitasi bo'lsa «asosiy» so'zi ma'nosini yo'qotardi, nolta
        # bo'lsa ishga tushirishning mezoni yo'qolardi.
        raise ValueError(f"«asosiy metrika» aynan bitta bo'lishi kerak: {mains}")

    for dash in DASHBOARDS:
        if not dash.phrase.strip():
            raise ValueError(f"`{dash.code}`: hujjatdagi matn bo'sh")
        if not dash.feeds:
            raise ValueError(f"`{dash.code}`: kirishsiz dashboard")

        ready = dash.readiness is Readiness.READY
        if ready and dash.limits:
            # «Quriladi» degan da'vo cheklov bilan birga — bu aynan
            # `gates.py` ogohlantirgan yumshatishning shakli.
            raise ValueError(f"`{dash.code}`: READY, lekin cheklovi bor")
        if not ready and not dash.limits:
            raise ValueError(f"`{dash.code}`: READY emas, lekin sababi yo'q")
        if ready and dash.near:
            raise ValueError(f"`{dash.code}`: READY da `near` bo'lmaydi")

        if dash.readiness is Readiness.EMPTY and not dash.is_gap:
            # Faqat `ACCEPTED` cheklov grafikni bo'shatmaydi — u uni
            # boshqacha o'qishga majbur qiladi. Bo'sh grafikning
            # sababi har doim yopilishi mumkin bo'lgan narsa.
            raise ValueError(f"`{dash.code}`: EMPTY, lekin bo'shliq sababi yo'q")

        limit_codes = [limit.code for limit in dash.limits]
        if len(set(limit_codes)) != len(limit_codes):
            raise ValueError(f"`{dash.code}`: cheklov kodi takrorlangan")
        for limit in dash.limits:
            if len(limit.why) < 40:
                # Sababsiz cheklov keyingi o'quvchiga «shunchaki
                # qo'shib qo'ysa bo'lardi» degan taassurot qoldirardi.
                raise ValueError(f"`{dash.code}`/`{limit.code}`: sabab juda qisqa")

        for feed in (*dash.feeds, *dash.near):
            _check_feed(dash.code, feed)


def _check_feed(code: str, feed: Feed) -> None:
    """Kirish haqiqiy reyestrga tushishini tekshiradi.

    Yozuv xatosi bilan kelgan havola dashboardni **boyroq** qilib
    ko'rsatardi: qator bor, nom bor, faqat u hech narsaga
    bog'lanmagan.
    """
    if feed.source is FeedSource.EVENT:
        spec = catalogue.CATALOGUE.get(feed.ref)
        if spec is None:
            raise ValueError(f"`{code}`: `01` §21 da bunday hodisa yo'q — {feed.ref}")
        if feed.attribute is not None:
            known = set(spec.attributes) | {catalogue.REGION_ATTR}
            if feed.attribute not in known:
                raise ValueError(
                    f"`{code}`: `{feed.ref}` da `{feed.attribute}` atributi yo'q"
                )
    elif ":" not in feed.ref:
        raise ValueError(f"`{code}`: vitrina havolasi `modul:atribut` bo'lishi kerak")


def _check_observability() -> None:
    """Kuzatilmaydigan hodisadan `READY` dashboard qurib bo'lmaydi.

    Alohida funksiya, chunki bu reyestrning ichki qoidasi emas —
    u `catalogue` bilan **kesishma**: `observable` bayrog'i o'sha
    yerda o'zgarsa, bu yerdagi holat jimgina yolg'onga aylanardi.
    """
    for dash in DASHBOARDS:
        if dash.readiness is not Readiness.READY:
            continue
        for feed in dash.feeds:
            if feed.source is not FeedSource.EVENT:
                continue
            if not catalogue.CATALOGUE[feed.ref].observable:
                raise ValueError(
                    f"`{dash.code}`: READY, lekin `{feed.ref}` kuzatilmaydi"
                )


_check_registry()
_check_observability()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DashboardReport:
    """Butun ro'yxatning bugungi holati.

    `measures.MeasureReport` bilan bir xil sababdan **statik**: javob
    jonli ma'lumotdan emas, kodning tuzilishidan chiqadi.
    """

    dashboards: tuple[Dashboard, ...]

    @property
    def counts(self) -> dict[str, int]:
        """Holat → nechta dashboard. Nol bo'lgani ham qoladi."""
        result = {str(r): 0 for r in Readiness}
        for dash in self.dashboards:
            result[str(dash.readiness)] += 1
        return result

    @property
    def gaps(self) -> tuple[Dashboard, ...]:
        return tuple(d for d in self.dashboards if d.is_gap)

    @property
    def main(self) -> Dashboard:
        """«Главная метрика запуска». Reyestr uni bitta qilib kafolatlaydi."""
        return next(d for d in self.dashboards if d.main)

    def blocked_by(self, unblocks: Unblocks) -> tuple[Dashboard, ...]:
        """Bitta sabab nechta dashboardni ushlab turibdi.

        Hisobotning eng foydali kesimi: E17 bitta odam ishi, lekin u
        **ikkita** dashboardni ochadi.
        """
        return tuple(
            d for d in self.dashboards if any(x.unblocks is unblocks for x in d.limits)
        )


def evaluate() -> DashboardReport:
    """`01` §21 «Дашборды», hujjatdagi tartibda."""
    return DashboardReport(dashboards=DASHBOARDS)

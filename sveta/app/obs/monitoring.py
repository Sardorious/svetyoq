"""`01` §22 «Logging & Monitoring» — kuzatuv qatlamining **talablari** kodda.

**Nima uchun bu modul bor.** `05` §10 «Kuzatuvchanlik» 47-run bilan
qulflangan: yettita metrika, to'rtta ogohlantirish, eksport formati.
`01` §22 esa boshqa hujjat va boshqa savol: u platforma stekini
**meros** deb e'lon qiladi va undan keyin to'rtta qatorlik **delta**
beradi — ya'ni «Samarqand paketi uchun qo'shimcha nima kerak». O'sha
delta hech qachon kod bilan solishtirilmagan.

Farq mazmunli. `05` §10 «bizda nima bor» ni yozadi; `01` §22 «mintaqaviy
reliz uchun nima yetishmaydi» ni. Ikkinchisi birinchisidan kelib
chiqmaydi va, ma'lum bo'lishicha, uning uchta qatoridan **bittasi ham**
`05` §10 ga sig'maydi.

Natija bitta jumlaga sig'adi: **to'rtta talabdan bittasi bajarilgan**
(metrikalarning `region` yorlig'i, 24-run), qolgan uchtasi esa uch xil
sababdan bajarilmagan — va uchala sabab ham «shunchaki yozilmagan»
emas.

## Uchta holat, «bor/yo'q» emas

66-, 67- va 68-runlarning sabog'i shu yerda ham takrorlanadi: ikkilik
holat bo'shliqning **narxini** yo'qotardi. Bu yerda narx uch xil.

* `HELD` — talab bugun bajarilgan va test bilan qulflangan;
* `CONFLICTED` — talabni bajarish **boshqa qulflangan bo'limni
  tahrirlashni** talab qiladi. Bu kod ishi emas: `05` §10 ning oxirgi
  qatori «Ogohlantirish faqat to'rttasiga» deydi va `app.obs.alerts`
  aynan to'rttani biladi. Beshinchisini qo'shish — spetsifikatsiyaga
  o'zgartirish, 66-run ning `answer_p90` bilan bir xil sinf;
* `VACUOUS` — talabni bajarish **hech narsani to'sqinliksiz** mumkin,
  lekin o'lchov bo'sh chiqadi: uning kirishi mahsulotda yo'q. Bu eng
  yashirin sinf, chunki bunday ogohlantirish yozilgach **ishlayotganday
  ko'rinadi** — grafik bor, qiymat `0`, hech qachon o't olmaydi;
* `BLOCKED` — oddiy yetishmagan ish, egasi ma'lum (odam yoki epic).

## Nima uchun `VACUOUS` `CONFLICTED` dan ustun turadi

Uchinchi qator (geokodlash) ikkala kamchilikka ham ega: u ham beshinchi
ogohlantirish, ham bo'sh o'lchov. Holat `VACUOUS` deb belgilangan va
tartib ataylab shunday: ziddiyatni **yechish mumkin** — `05` §10 ni
tahrirlash bir soatlik ish; bo'shlik esa tahrirdan keyin ham qoladi.
Holatni «yechish mumkin bo'lgani» bo'yicha qo'yish ro'yxatni
optimistikroq, ya'ni yolg'onroq qilardi.

## Geokoder — uchta joyda bor, kodda yo'q

Uchinchi qatorning bo'shligi alohida yozilishga arziydi, chunki u bitta
qatordan kattaroq. Mahsulot manzilni koordinataga **umuman
o'girmaydi**: bot Telegram ning `location` pini bilan ishlaydi
(`app.bot.service.submit_report`), ya'ni «переход в режим "точка на
карте"» — bu zaxira rejim emas, **yagona** rejim va u birinchi kundan
yoqilgan. Demak «geokodlash muvaffaqiyatsizliklari ulushi» ning
maxraji nol: ogohlantirish yozilsa, u abadiy `0/0` bo'lardi.

Shunga qaramay geokoder hujjatda ham, konfiguratsiyada ham yashaydi:
`GEOCODER_PROVIDER` va `GEOCODER_API_KEY` (`.env.example` + `Settings`),
`01` §16 dagi `GEOCODER_UNAVAILABLE` xato kodi, `01` §18 dagi tashqi
integratsiya qatori. 44-run ning parity testi ikkala sozlamani
ko'radi va **to'g'ri** deydi — u `.env.example` bilan `Settings` ning
mos kelishini tekshiradi, ikkala tomon ham mavjud bo'lmagan
quyi tizimni tasvirlayotganini esa ko'ra olmaydi. Bu parity testining
kamchiligi emas, uning chegarasi; shu yerda yoziladi, chunki boshqa
hech qayerda yozilmagan.

## `region` yorlig'i — bitta emas, doimiy talab

Birinchi qator qolgan uchtasidan tuzilishi bilan farq qiladi: u
artefakt emas, **xossa**. «Все продуктовые метрики размечены `region`»
ni bir marta bajarib qo'yib bo'lmaydi — u har yangi metrikada qaytadan
tekshirilishi kerak va aynan shunday jimgina buziladi. Shuning uchun
bu yerda `HELD` bayrog'i yetarli emas: reyestr yorliqsiz qolishi
mumkin bo'lgan oilalarni **nom bilan** sanaydi (`LABEL_EXEMPT`), va
kontrakt testi eksportning o'zini yuradi. Ro'yxatga kirmagan yangi
oila `region` siz chiqsa, test yiqiladi.

Modul **toza**: bazaga ham, `settings` ga ham tegmaydi, foydalanuvchi
matni yo'q. `app.obs.metrics` va `app.obs.alerts` dan boshqa hech
narsani import qilmaydi — qolgan havolalar `modul:simvol` matni bo'lib
turadi va kontrakt testida yechiladi (68-run ning naqshi).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.obs import alerts, metrics

#: Bu ro'yxatning hujjatdagi manzili.
SPEC = "01 §22 «Logging & Monitoring»"

#: Delta jadvalining ziddiyati qaysi bo'limga tegadi.
ALERT_CAP_SPEC = "05 §10"

#: `05` §10 ning oxirgi qatori nechta ogohlantirishga ruxsat beradi.
#: Reyestr shu sonni `app.obs.alerts` dan **o'qimaydi**, balki u bilan
#: solishtiradi: ikkalasi bir manbadan olinsa, beshinchi ogohlantirish
#: qo'shilganda ziddiyat jimgina yo'qolardi.
ALERT_CAP = 4


class Layer(StrEnum):
    """Talab kuzatuv qatlamining qaysi bo'g'iniga tegadi."""

    #: Metrika va uning yorliqlari (`05` §10 eksporti).
    METRIC = "metric"
    #: Ogohlantirish qoidasi (`app.obs.alerts`).
    ALERT = "alert"
    #: Salomatlik tekshiruvi (`app.api.v1.health`).
    HEALTHCHECK = "healthcheck"


class State(StrEnum):
    """Talab bugun bajarilganmi va bajarilmagan bo'lsa — **nima turibdi**."""

    HELD = "held"
    CONFLICTED = "conflicted"
    VACUOUS = "vacuous"
    BLOCKED = "blocked"


class Unblocks(StrEnum):
    """To'siqni nima ochadi — ya'ni uni yopish narxi."""

    #: Spetsifikatsiyaga o'zgartirish (`05` §10 ning to'rtta cheklovi).
    SPEC = "spec"
    #: Mahalla poligonlari (E17). Odam ishi.
    E17 = "e17"
    #: Rasmiy manba kelishuvi (H-4 / P0-1 → E18). Odam ishi.
    H4 = "h4"
    #: Mahsulotda umuman yo'q bo'lgan quyi tizim. Uni «yoqib»
    #: bo'lmaydi — avval yozish kerak, va yozish qarori qabul
    #: qilinmagan.
    PRODUCT = "product"


#: `HELD` bo'lmagan talabning holati shu tartibda tanlanadi: birinchi
#: mos kelgani yutadi. Tartib ataylab pessimistik — modul izohiga
#: qarang.
STATE_PRECEDENCE: tuple[State, ...] = (State.VACUOUS, State.CONFLICTED, State.BLOCKED)

#: To'siq turi → u qaysi holatni beradi.
STATE_OF_UNBLOCK: dict[Unblocks, State] = {
    Unblocks.PRODUCT: State.VACUOUS,
    Unblocks.SPEC: State.CONFLICTED,
    Unblocks.E17: State.BLOCKED,
    Unblocks.H4: State.BLOCKED,
}


@dataclass(frozen=True)
class Obstacle:
    """Talabni nima ushlab turibdi, sababi bilan.

    `why` — **bir jumlada** sabab, keyingi o'quvchi uchun: to'siqni
    ko'rgan odam birinchi navbatda «buni shunchaki qo'shib qo'ysa
    bo'lmaydimi?» deb so'raydi va javob shu yerda turishi kerak.
    """

    code: str
    unblocks: Unblocks
    why: str

    @property
    def state(self) -> State:
        return STATE_OF_UNBLOCK[self.unblocks]


@dataclass(frozen=True)
class Requirement:
    """`01` §22 delta jadvalining bitta qatori.

    `phrase` — hujjatdagi **so'zma-so'z** matn (ikkinchi ustun).
    Kontrakt testi ro'yxatni shu matn bo'yicha hujjat bilan
    solishtiradi, ya'ni qatorni qayta yozish yoki tartibini almashtirish
    testni yiqitadi.

    `threshold` — qatorda ko'rsatilgan ulush (`>10%` → `0.10`). Kontrakt
    testi uni hujjatdan parse qilib solishtiradi: son faqat nasrda
    qolib ketmasligi kerak.
    """

    code: str
    layer: Layer
    phrase: str
    threshold: float | None = None
    #: Talabni bajaradigan kod, `modul:simvol` ko'rinishida.
    binds: tuple[str, ...] = ()
    obstacles: tuple[Obstacle, ...] = ()
    #: Eng yaqin mavjud o'lchov. Bog'lanish emas, **ogohlantirish**
    #: (67-run ning `Measure.near` i bilan bir xil rolda): uni o'rniga
    #: qo'yish bo'shliqni yopmaydi, ko'rinmas qiladi.
    near: tuple[str, ...] = ()

    @property
    def state(self) -> State:
        if not self.obstacles:
            return State.HELD
        states = {obstacle.state for obstacle in self.obstacles}
        return next(s for s in STATE_PRECEDENCE if s in states)

    @property
    def is_held(self) -> bool:
        return self.state is State.HELD


# --------------------------------------------------------------------------
# Meros qilib olingan stek (§22 ning birinchi jumlasi)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class StackElement:
    """«Наследуется платформенный стек: …» ro'yxatining bitta bandi.

    Jumla delta emas, lekin u ham da'vo: meros deb e'lon qilingan
    narsaning yarmi shu repoda yozilgan. `provided_by` bo'sh bo'lsa —
    band **butunlay** platformaga tegishli va bu yerda kod yo'q.
    """

    name: str
    provided_by: tuple[str, ...] = ()

    @property
    def is_external(self) -> bool:
        return not self.provided_by


STACK: tuple[StackElement, ...] = (
    StackElement("Prometheus", ("app.obs.metrics:render", "app.api.v1.metrics:get_metrics")),
    # Grafana repoda umuman yo'q va bo'lishi ham shart emas: u
    # `/metrics` ni o'qiydi. Ro'yxatda qoladi, chunki uning yo'qligi —
    # qaror, unutish emas.
    StackElement("Grafana"),
    # Jurnal JSON bo'lib chiqadi, ya'ni yig'uvchi uni parse qila oladi;
    # yig'uvchining o'zi (ELK yoki OpenSearch) platformaniki.
    StackElement("ELK/OpenSearch", ("app.core.logging:JsonFormatter",)),
    StackElement("health-checks", ("app.api.v1.health:health", "app.api.v1.health:live")),
    StackElement("алертинг", ("app.obs.alerts:evaluate",)),
)


# --------------------------------------------------------------------------
# `region` yorlig'i — birinchi qatorning qulfi
# --------------------------------------------------------------------------

#: `region` yorlig'isiz chiqishi **mumkin** bo'lgan oilalar, sababi bilan.
#: Ro'yxat qisqa va u o'sishi kerak emas: yangi mahsulot metrikasi
#: yorliq bilan chiqadi. Kontrakt testi eksportni yurib chiqadi va shu
#: ro'yxatdan tashqaridagi yorliqsiz oilani xato deb sanaydi.
LABEL_EXEMPT: dict[str, str] = {
    metrics.HTTP_REQUESTS.name: (
        "Protsess ichidagi hisoblagich: so'rov darajasida mintaqa ma'lum "
        "emas (`/health` va `/metrics` ning o'zi hech qanday mintaqaga "
        "tegishli emas)."
    ),
    metrics.ALERT_ACTIVE.name: (
        "Ogohlantirishning o'zi mahsulot o'lchovi emas; sharti esa "
        "mintaqalar bo'yicha maksimumdan hisoblanadi (`app.obs.alerts` "
        "modul izohi), ya'ni yorliq qiymatga ega bo'lmasdi."
    ),
}

#: `05` §10 jadvalidagi yettita metrika — yorliq talabi avvalo ularga
#: tegishli. Nom bilan yozilgan, chunki «hamma» so'zi jadval o'zgarganda
#: jimgina kichrayardi.
PRODUCT_FAMILIES: tuple[str, ...] = (
    metrics.REPORTS_RECEIVED.name,
    metrics.OUTAGES_OPEN.name,
    metrics.TIME_TO_CONFIRM.name,
    metrics.SNAPSHOT_AGE.name,
    metrics.OUTBOX_LAG.name,
    metrics.GEO_UNMATCHED.name,
    metrics.NOTIFICATIONS_FAILED.name,
)


# --------------------------------------------------------------------------
# Reyestr — `01` §22 delta jadvali, aynan o'sha tartibda
# --------------------------------------------------------------------------

REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement(
        code="region_label",
        layer=Layer.METRIC,
        phrase=(
            "Все продуктовые метрики размечены `region` — иначе самаркандские "
            "данные растворятся в ташкентских"
        ),
        binds=(
            "app.obs.readings:to_samples",
            "app.obs.readings:RegionReading",
            "app.obs.collector:collect",
        ),
    ),
    Requirement(
        code="mahalla_unmatched_alert",
        layer=Layer.ALERT,
        phrase=(
            "Доля репортов без привязки к махалле >10% → дефект справочника "
            "полигонов"
        ),
        threshold=0.10,
        obstacles=(
            Obstacle(
                code="alert_cap",
                unblocks=Unblocks.SPEC,
                why=(
                    "`05` §10 ning oxirgi qatori «Ogohlantirish faqat "
                    "to'rttasiga» deydi va `app.obs.alerts.ALERTS` aynan "
                    "to'rttani biladi; beshinchisini qo'shish kod emas, "
                    "spetsifikatsiya o'zgartirishi."
                ),
            ),
            Obstacle(
                code="no_mahalla_polygons",
                unblocks=Unblocks.E17,
                why=(
                    "Mahalla spravochnigi bo'sh, ya'ni ulush birinchi kundan "
                    "100% bo'lardi: ogohlantirish yoqilgan zahoti o't olib, "
                    "E17 gacha qizil qolardi va signal berish o'rniga shovqin "
                    "qilardi."
                ),
            ),
        ),
        near=("app.obs.metrics:GEO_UNMATCHED",),
    ),
    Requirement(
        code="geocoding_failure_alert",
        layer=Layer.ALERT,
        phrase=(
            "Доля неудачных геокодирований >15% → риск R-13, переход в режим "
            "«точка на карте»"
        ),
        threshold=0.15,
        obstacles=(
            Obstacle(
                code="no_geocoder",
                unblocks=Unblocks.PRODUCT,
                why=(
                    "Mahsulot manzilni koordinataga umuman o'girmaydi — bot "
                    "Telegram `location` pini bilan ishlaydi, ya'ni «точка на "
                    "карте» zaxira emas, yagona rejim; ulushning maxraji nol "
                    "va ogohlantirish abadiy `0/0` bo'lardi."
                ),
            ),
            Obstacle(
                code="alert_cap",
                unblocks=Unblocks.SPEC,
                why=(
                    "Ziddiyat `mahalla_unmatched_alert` bilan bir xil: "
                    "`05` §10 to'rttadan ko'pini taqiqlaydi. Bu yerda u "
                    "ikkinchi darajali — tahrirdan keyin ham o'lchov bo'sh "
                    "qolaveradi."
                ),
            ),
        ),
    ),
    Requirement(
        code="source_1055_healthcheck",
        layer=Layer.HEALTHCHECK,
        phrase="Доступность источника региональных публикаций 1055",
        obstacles=(
            Obstacle(
                code="source_unconfirmed",
                unblocks=Unblocks.H4,
                why=(
                    "Manbaning **mavjudligi** tasdiqlanmagan (`02` H-4, `01` "
                    "P0-1): tekshiriladigan manzil yo'q, stub qo'yish esa "
                    "doimo qizil salomatlik beruvchi tekshiruvni yaratardi va "
                    "u birinchi haftada e'tibordan chiqarilardi."
                ),
            ),
        ),
        near=("app.api.v1.health:health",),
    ),
)

REQUIREMENT_BY_CODE: dict[str, Requirement] = {r.code: r for r in REQUIREMENTS}


def _check_registry() -> None:
    """Reyestrning **jimgina** buziladigan joylari — import paytida.

    Har biri hisobotni to'g'ri **ko'rinishda** qoldiradi: qator bor,
    matn bor, faqat u hech narsani tekshirmaydi.
    """
    codes = [r.code for r in REQUIREMENTS]
    duplicates = sorted({c for c in codes if codes.count(c) > 1})
    if duplicates:
        raise ValueError(f"talab kodi takrorlangan: {duplicates}")

    for req in REQUIREMENTS:
        if not req.phrase.strip():
            raise ValueError(f"`{req.code}`: hujjatdagi matn bo'sh")

        if req.is_held:
            if not req.binds:
                # «Bajarilgan» degan da'vo kodga havolasiz — aynan
                # `03` §6 ogohlantirgan yumshatishning shakli.
                raise ValueError(f"`{req.code}`: HELD, lekin koddagi tayanchi yo'q")
            if req.near:
                raise ValueError(f"`{req.code}`: HELD da `near` bo'lmaydi")
        elif req.binds:
            raise ValueError(f"`{req.code}`: bajarilmagan, lekin tayanchi bor")

        obstacle_codes = [o.code for o in req.obstacles]
        if len(set(obstacle_codes)) != len(obstacle_codes):
            raise ValueError(f"`{req.code}`: to'siq kodi takrorlangan")
        for obstacle in req.obstacles:
            if len(obstacle.why) < 40:
                raise ValueError(f"`{req.code}`/`{obstacle.code}`: sabab juda qisqa")

        for ref in (*req.binds, *req.near):
            if ":" not in ref:
                raise ValueError(f"`{req.code}`: havola `modul:simvol` bo'lishi kerak")


def _check_alert_cap() -> None:
    """Ziddiyatning o'zi haqiqatan mavjudligini tekshiradi.

    Alohida funksiya, chunki bu reyestrning ichki qoidasi emas — u
    `app.obs.alerts` bilan **kesishma**. Agar kimdir beshinchi
    ogohlantirishni qo'shsa, `CONFLICTED` holati jimgina yolg'onga
    aylanardi: hisobot hamon «spetsifikatsiya to'sqinlik qilyapti»
    deb ko'rsatardi, holbuki to'siq allaqachon buzilgan bo'lardi.
    """
    if len(alerts.ALERTS) != ALERT_CAP:
        raise ValueError(
            f"{ALERT_CAP_SPEC} {ALERT_CAP} ta ogohlantirishga ruxsat beradi, "
            f"`alerts.ALERTS` da {len(alerts.ALERTS)} ta"
        )
    conflicted = [
        req.code
        for req in REQUIREMENTS
        if any(o.unblocks is Unblocks.SPEC for o in req.obstacles)
    ]
    if not conflicted:
        raise ValueError("ziddiyat yo'qolgan bo'lsa, `ALERT_CAP` ham keraksiz")


def _check_label_exemptions() -> None:
    """Yorliqsiz oilalar ro'yxati haqiqiy oilalarni ataydimi.

    Yozuv xatosi bilan kelgan nom ro'yxatni **kengroq** qilib
    ko'rsatardi: qator bor, sabab bor, faqat u hech qanday oilani
    bo'shatmaydi — va haqiqiy yorliqsiz oila e'tibordan chetda
    qolardi.
    """
    for name in LABEL_EXEMPT:
        if name not in metrics.FAMILY_BY_NAME:
            raise ValueError(f"`LABEL_EXEMPT` da bunday oila yo'q — {name}")
    for name in PRODUCT_FAMILIES:
        if name not in metrics.FAMILY_BY_NAME:
            raise ValueError(f"`PRODUCT_FAMILIES` da bunday oila yo'q — {name}")
        if name in LABEL_EXEMPT:
            raise ValueError(f"`{name}` mahsulot metrikasi — u yorliqdan ozod bo'lmaydi")


_check_registry()
_check_alert_cap()
_check_label_exemptions()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MonitoringReport:
    """`01` §22 ning bugungi holati.

    `measures.MeasureReport` va `dashboards.DashboardReport` bilan bir
    xil sababdan **statik**: javob jonli ma'lumotdan emas, kodning
    tuzilishidan chiqadi — «o'lchay olamizmi?», «qiymat qanday?» emas.
    """

    requirements: tuple[Requirement, ...]

    @property
    def counts(self) -> dict[str, int]:
        """Holat → nechta talab. Nol bo'lgani ham qoladi."""
        result = {str(s): 0 for s in State}
        for req in self.requirements:
            result[str(req.state)] += 1
        return result

    @property
    def gaps(self) -> tuple[Requirement, ...]:
        """Bajarilmagan talablar, hujjatdagi tartibda."""
        return tuple(r for r in self.requirements if not r.is_held)

    def blocked_by(self, unblocks: Unblocks) -> tuple[Requirement, ...]:
        """Bitta sabab nechta talabni ushlab turibdi."""
        return tuple(
            r for r in self.requirements if any(o.unblocks is unblocks for o in r.obstacles)
        )


def evaluate() -> MonitoringReport:
    """`01` §22 delta jadvali, hujjatdagi tartibda."""
    return MonitoringReport(requirements=REQUIREMENTS)

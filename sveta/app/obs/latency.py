"""HTTP javob vaqti gistogrammasi (`03` §11 «API p95», `03` §9 Redis tetigi).

**Nima uchun bu modul bor.** Ikkita run bir xil bo'shliqni ikki xil
joydan ko'rdi va ikkalasi ham uni yozib qoldirdi:

* 67-run — `app/release/measures.py`, `api_p95`, `Coverage.ABSENT`:
  `03` §11 R2.0 bosqichida «API p95» kuzatilishi kerak, `05` §10 da esa
  javob vaqti uchun metrika yo'q;
* 79-run — `app/core/architecture.py`, `RD` tuguni,
  `Trigger.UNMEASURED`: `03` §9 ga ko'ra Redis ni **qaytaradigan
  yagona asos** — «API p95 >300 ms», ya'ni butun `ADR-05` qarori
  o'lchanmaydigan shartga tayanib turibdi.

Ikkalasi bitta gistogramma bilan yopiladi. Shuning uchun bu modul
o'lchovni `05` §10 ning yettitasiga qo'shimcha qiladi, lekin
**ogohlantirish qo'shmaydi**: §10 ning oxirgi qatori aynan to'rttaga
ruxsat beradi (`app.obs.monitoring.ALERT_CAP`) va beshinchisi
spetsifikatsiyani o'zgartirishni talab qiladi.

## Nima uchun protsess ichida — ikkinchi va oxirgi istisno

`app.obs.metrics` ning qoidasi: metrikalar protsessda emas, **bazada**
yashaydi. Yagona istisno `http_requests_total` edi (`app.obs.counters`),
sababi esa aynan shu yerda ham kuchda: HTTP javoblari hech qayerda
saqlanmaydi va saqlanmasligi ham kerak. Javob vaqti — o'sha javobning
xossasi, ya'ni uni bazadan o'qib bo'lmaydi.

## Nima uchun gistogramma, `p95` gauge emas

Bu farq protsess ichidagi hisoblagichning cheklovini **yo'q qiladi**.
`api` bir necha nusxada ishlaganda:

* har nusxaning tayyor `p95` i — o'z trafigi bo'yicha kvantil, va
  kvantillarni qo'shib ham, o'rtachalab ham bo'lmaydi; scrape qaysi
  nusxaga tushishiga qarab raqam sakrardi;
* chelaklar esa **qo'shiladi**: `sum(rate(..._bucket[5m])) by (le)` butun
  servisning taqsimotini beradi va undan `histogram_quantile` bitta
  javob chiqaradi.

Ya'ni `counters.py` ochiq yozgan cheklov («bitta scrape dagi son butun
servisniki emas») bu yerda takrorlanmaydi.

## `0.3` — chelak chegarasi, tasodifiy son emas

`03` §6 R2.0 chiqish mezoni va §9 ning Redis sharti bitta sonni
ko'rsatadi: **300 ms**. Agar `0.3` chelak chegarasi bo'lmasa,
`histogram_quantile` uni qo'shni chegaralar orasida **chiziqli
interpolyatsiya** bilan taxmin qilardi va «p95 300 ms dan kichikmi»
degan savolga taxminiy javob berardi — arxitektura qarorini qaytarish
haqidagi savolga.

Chegara ro'yxatda bo'lganda javob interpolyatsiyasiz va aniq bo'ladi:
`p95 <= 0.3` ⟺ `le="0.3"` chelagining kümülativ soni jamining 95% idan
kam emas. `share_within()` aynan shuni hisoblaydi va chegara bo'lmagan
songa **ataylab** javob bermaydi (`ValueError`) — aks holda u
interpolyatsiyani aniqlik niqobi ostida qaytarardi.

## Nima uchun `surface`, `path` emas

Ikkita sabab, ikkalasi ham `path` ga qarshi:

1. **Kardinallik.** `/outages/{id}` xom yo'l sifatida cheksiz ko'p qiymat
   beradi va har biri o'n uchta chelak bilan keladi.
2. **Savolning o'zi boshqa.** `03` §11 ning «API p95» qatori R2.0
   «Ommaviy API» bosqichida turadi, ya'ni savol ommaviy yuza haqida.
   Bugun mavjud yagona hisoblagich (`http_requests_total`) esa hamma
   narsani bitta songa qo'shadi: Telegram webhook (u eng band yo'l va
   uni tashqi iste'molchi umuman ko'rmaydi) va `/health` (liveness
   probe har necha soniyada keladi va u har doim tez) ommaviy API ning
   p95 ini o'ziga tortib, uni tizimli ravishda **yaxshi tomonga**
   yolg'on ko'rsatardi.

Shuning uchun yorliq — yopiq to'plamdagi beshta yuza. `region` yorlig'i
esa yo'q (`01` §22 talabidan ozod, sabab `app.obs.monitoring.LABEL_EXEMPT`
da): so'rov darajasida mintaqa yuzaning xossasi emas — u ba'zi
endpointlarda so'rov parametri, ba'zilarida (`/regions`, `/map/config`,
`/health`) umuman yo'q.

Modul **toza**: bazaga ham, FastAPI ga ham, `settings` ga ham bog'liq
emas — prefikslar argument sifatida keladi.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Yopiq yuzalar to'plami. Yangi yuza qo'shish — ongli qaror: kardinallik
#: shu ro'yxat bilan chegaralangan.
PUBLIC = "public"
ADMIN = "admin"
PROBE = "probe"
WEBHOOK = "webhook"
OTHER = "other"

#: Eksport tartibi qat'iy (barqaror diff).
SURFACES: tuple[str, ...] = (PUBLIC, ADMIN, PROBE, WEBHOOK, OTHER)

#: Chelak chegaralari, soniyada. `+Inf` ro'yxatda yo'q — u har doim
#: oxirgi chelak sifatida qo'shiladi.
#:
#: Ro'yxat `0.3` atrofida ataylab zich: `03` §6 ning mezoni shu yerda
#: hal bo'ladi va qo'shni chelaklar keng bo'lsa, «300 ms dan sal
#: yomonroq» bilan «ikki barobar yomon» bir xil ko'rinardi.
BUCKETS: tuple[float, ...] = (
    0.01,
    0.025,
    0.05,
    0.1,
    0.15,
    0.2,
    0.3,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)

#: `03` §6 R2.0 chiqish mezoni va `03` §9 ning Redis sharti — bitta son.
TARGET_S = 0.3

#: `03` §11 «API p95».
P95 = 0.95


def _check_buckets() -> None:
    """Import paytida: chegaralar o'sib borishi va `TARGET_S` ular ichida.

    Ikkinchisi shu modulning butun ma'nosi: `TARGET_S` chegara
    bo'lmasa, `share_within()` ishlamaydi va savolga faqat
    interpolyatsiya javob berardi.
    """
    if list(BUCKETS) != sorted(set(BUCKETS)):
        raise ValueError("chelak chegaralari o'suvchi va takrorlanmas bo'lishi kerak")
    if TARGET_S not in BUCKETS:
        raise ValueError(f"`{TARGET_S}` chelak chegarasi emas — p95 mezoni taxminiy bo'lardi")


_check_buckets()


@dataclass(frozen=True)
class Histogram:
    """Bitta yuzaning taqsimoti.

    `counts` uzunligi `len(BUCKETS) + 1`: oxirgi element — `+Inf`
    chelagi. U alohida saqlanadi, chunki «10 soniyadan sekin» —
    haqiqiy holat va uni tashlab yuborish `_count` ni `_bucket` lar
    yig'indisidan katta qilardi.
    """

    counts: tuple[int, ...]
    sum_s: float = 0.0

    def __post_init__(self) -> None:
        if len(self.counts) != len(BUCKETS) + 1:
            raise ValueError("chelaklar soni `BUCKETS` + `+Inf` ga teng bo'lishi kerak")

    @property
    def total(self) -> int:
        return sum(self.counts)

    @property
    def cumulative(self) -> tuple[int, ...]:
        """Prometheus `_bucket` qiymatlari: har chelak — «shundan tez yoki teng»."""
        running = 0
        out: list[int] = []
        for count in self.counts:
            running += count
            out.append(running)
        return tuple(out)

    def share_within(self, seconds: float) -> float | None:
        """`seconds` ichida ulgurgan so'rovlar ulushi — **aniq**, interpolyatsiyasiz.

        `seconds` chelak chegarasi bo'lishi shart. Boshqa son uchun javob
        faqat taxminiy bo'lardi va aynan shu taxmin `03` §9 ning
        qarorini imzolab qo'yardi.

        Bo'sh gistogramma uchun `None` — «hali ma'lumot yo'q». `0.0`
        qaytarish «hech biri ulgurmadi» degan yolg'on signal bo'lardi.
        """
        if seconds not in BUCKETS:
            raise ValueError(f"`{seconds}` chelak chegarasi emas — aniq javob bo'lmaydi")
        total = self.total
        if total == 0:
            return None
        return self.cumulative[BUCKETS.index(seconds)] / total

    def quantile(self, q: float) -> float | None:
        """`histogram_quantile` ning aynan o'zi (chelak ichida chiziqli).

        Prometheus dagi qiymat bilan mos kelishi muhim: hisobotdagi son
        bilan grafikdagi son bir xil bo'lmasa, ikkalasiga ham
        ishonilmaydi.

        `+Inf` chelagiga tushgan kvantil uchun oxirgi **chekli** chegara
        qaytadi (Prometheus ham shunday qiladi): yuqoridan chegaralanmagan
        chelakdan boshqa haqiqat chiqarib bo'lmaydi.
        """
        if not 0.0 < q <= 1.0:
            raise ValueError("kvantil (0, 1] oralig'ida bo'ladi")
        total = self.total
        if total == 0:
            return None
        rank = q * total
        cumulative = self.cumulative
        index = next(i for i, value in enumerate(cumulative) if value >= rank)
        if index == len(BUCKETS):
            return BUCKETS[-1]
        lower = 0.0 if index == 0 else BUCKETS[index - 1]
        upper = BUCKETS[index]
        before = cumulative[index - 1] if index else 0
        inside = cumulative[index] - before
        if inside <= 0:
            return upper
        return lower + (upper - lower) * ((rank - before) / inside)

    def meets_target(self) -> bool | None:
        """`03` §6 R2.0: «API p95 ≤300 ms» — bugun bajarilyaptimi.

        `None` — so'rov bo'lmagan. Bu «bajarildi» emas: yuklamasiz
        o'lchov mezonni yopmaydi va shu farq `gates.py` ning
        `UNMEASURED` bilan bir xil sababdan saqlanadi.
        """
        share = self.share_within(TARGET_S)
        return None if share is None else share >= P95


EMPTY = Histogram(counts=(0,) * (len(BUCKETS) + 1))


# --------------------------------------------------------------------------
# Protsess ichidagi holat
# --------------------------------------------------------------------------

#: `counters.py` bilan bir xil sabab bo'yicha qulfsiz: statistik
#: ko'rsatkich va yo'qolgan bitta o'lchov taqsimotga ta'sir qilmaydi,
#: qulf esa har so'rovga narx qo'shardi.
_counts: dict[str, list[int]] = {}
_sums: dict[str, float] = {}


def bucket_index(seconds: float) -> int:
    """`seconds` qaysi chelakka tushadi. Chegara **o'z** chelagiga kiradi (`le`)."""
    for index, edge in enumerate(BUCKETS):
        if seconds <= edge:
            return index
    return len(BUCKETS)


def observe(surface: str, seconds: float) -> None:
    """Bitta so'rovni yozib qo'yadi.

    Notanish yuza — **xato**, jimgina `other` ga tushmaydi: yopiq
    to'plam faqat shu tekshiruv tufayli yopiq qoladi.
    """
    if surface not in SURFACES:
        raise ValueError(f"notanish yuza — {surface}")
    row = _counts.get(surface)
    if row is None:
        row = [0] * (len(BUCKETS) + 1)
        _counts[surface] = row
    row[bucket_index(seconds)] += 1
    _sums[surface] = _sums.get(surface, 0.0) + seconds


def snapshot() -> dict[str, Histogram]:
    """Yuzalar kesimidagi nusxa (o'qish uchun).

    Bir marta ham so'rov ko'rmagan yuza chiqmaydi — `app.obs.metrics`
    ning `render` qoidasi bilan bir xil sabab: nol qator «shu yuza
    sekin emas» emas, «shu yuza umuman ishlatilmagan» degani.
    """
    return {
        surface: Histogram(counts=tuple(_counts[surface]), sum_s=_sums.get(surface, 0.0))
        for surface in SURFACES
        if surface in _counts
    }


def reset() -> None:
    """Faqat testlar uchun: o'lchovlar testlar orasida sizib o'tmasligi kerak."""
    _counts.clear()
    _sums.clear()


# --------------------------------------------------------------------------
# Yo'l → yuza
# --------------------------------------------------------------------------


def classify(path: str, *, api_prefix: str, webhook_path: str) -> str:
    """So'rov yo'lini beshta yuzadan biriga o'giradi.

    Tartib muhim: webhook `api_prefix` dan tashqarida yashaydi
    (`05` §6.3), `/health` esa prefiks ichida — ya'ni uni ommaviy
    yuzadan **nom bo'yicha** ajratish kerak.
    """
    if webhook_path and (path == webhook_path or path.startswith(webhook_path + "/")):
        return WEBHOOK
    if not path.startswith(api_prefix):
        return OTHER
    head = path[len(api_prefix) :].lstrip("/").split("/", 1)[0]
    if head == "health":
        return PROBE
    if head in {"admin", "metrics"}:
        return ADMIN
    return PUBLIC

#!/usr/bin/env python3
"""Sun'iy uzilish generatori (`05` §9.1, §9.2 «Ssenariy» qatlami).

```
Kirish: markaz, radius, boshlanish vaqti, davomiylik,
        hududdagi foydalanuvchilar soni, xabar berish ehtimoli
Chiqish: reports jadvaliga yozuvlar oqimi
```

Haqiqiy ma'lumot yo'q (E10 gacha), shuning uchun `05` §9 test
infratuzilmasini kodning bir qismi deb ataydi. Bu asbob uchta savolga
javob beradi: klasterlash to'g'ri yig'adimi, ikki qo'shni uzilish birlashib
ketmaydimi, kam zichlikda «ma'lumot yetarli emas» chiqadimi.

Asbob ikkiga bo'lingan:

* **Toza qism** — `OutageSpec` → `generate()` → xabarlar oqimi. Bazasiz
  ishlaydi va bazasiz testlanadi (`tests/test_simulate.py`). `preview`
  buyrug'i shu qismni yolg'iz ishga tushiradi.
* **Yozish qismi** — oqimni bot bosib o'tadigan **aynan o'sha yo'ldan**
  o'tkazadi: `geo.resolve` → `intake.create_report` → `clustering.assign`.
  Yo'lni qisqartirish generatorni foydasiz qilardi: u tekshirmoqchi
  bo'lgan narsa aynan shu zanjir.

Uchta himoya:

* **Determinizm** (`05` §9.2). `random.Random(seed)` — global `random`
  emas, `hash()` esa umuman emas (u har protsessda tasodifiylanadi).
  Bir xil `--seed` har safar bir xil oqim va bir xil `fingerprint` beradi.
* **Standart rejim — quruq yurish.** Hammasi haqiqatan hisoblanadi, lekin
  tranzaksiya oxirida bekor qilinadi; yozish uchun `--apply` kerak.
* **`--apply` haqiqiy ma'lumot ustiga yozmaydi.** Mintaqada haqiqiy odam
  yozgan xabar bo'lsa yoki bazada faol obuna bo'lsa, asbob umuman
  ishlamaydi (`EXIT_BLOCKED`).

Misollar:

    python -m tools.simulate scenarios
    python -m tools.simulate preview --scenario three_neighbours
    python -m tools.simulate run --scenario three_neighbours --region samarkand
    python -m tools.simulate run --lat 39.6547 --lon 66.9597 --radius-m 300 \\
        --at 2026-08-01T18:00 --duration-min 120 --users 20 --probability 0.4
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import sys
import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import blake2b
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.clustering import repository as cluster_repo  # noqa: E402
from app.clustering import service as clustering  # noqa: E402
from app.clustering.geometry import haversine_m  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.errors import OutOfRegionError, RateLimitedError  # noqa: E402
from app.db.session import dispose_engine, get_sessionmaker  # noqa: E402
from app.geo import pipeline as geo  # noqa: E402
from app.notifications import subscriptions as subs  # noqa: E402
from app.reports import intake  # noqa: E402
from app.reports import queries as reports_q  # noqa: E402
from tools.recluster import fingerprint, parse_moment  # noqa: E402

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_BLOCKED = 2
EXIT_USAGE = 64

#: Bir daraja kenglikning metrdagi uzunligi. Generator uchun shu aniqlik
#: yetarli: nuqtalar bir shahar ichida, xato ~0.5% dan kam.
METERS_PER_DEGREE_LAT = 111_320.0

DEFAULT_SEED = "sveta"

#: Odamlar uzilishni bir zumda emas, birinchi yarim soatda sezadi.
DEFAULT_REPORT_WINDOW_MIN = 30

#: «Svet keldi» xabarlari uzilish tugagach shu oyna ichida keladi.
RESTORE_WINDOW_MIN = 10

#: Akkaunt yoshi (`05` §4.3) — sun'iy foydalanuvchilar shu qadar «eski».
SYNTHETIC_ACCOUNT_AGE_DAYS = 30

#: Manfiy `tg_id` fazosi: Telegram identifikatorlari doim musbat, shuning
#: uchun manfiy qiymat sun'iy akkauntning ishonchli belgisi.
SYNTHETIC_TG_SPACE = 10**11

#: `min_spacing_m` bilan uy qo'yishga urinishlar soni. Doira to'lgan bo'lsa
#: cheksiz aylanmaslik uchun chegara kerak.
MAX_PLACEMENT_ATTEMPTS = 200


class SimulationError(ValueError):
    """Generator parametri yaroqsiz — CLI uchun tushunarli xato."""


class SimulationBlocked(RuntimeError):
    """Yozish xavfsiz emas — sabab bilan to'xtatiladi."""


def synthetic_tg_id(user_key: str) -> int:
    """Sun'iy akkauntning deterministik va **manfiy** `tg_id` si.

    `blake2b`, o'rnatilgan `hash()` emas: `hash()` har protsessda
    tasodifiylanadi va bir xil `--seed` ikki yurishda ikki xil akkaunt
    yaratardi — determinizm kafolati yo'qolardi.
    """
    digest = blake2b(user_key.encode(), digest_size=8).digest()
    return -(int.from_bytes(digest, "big") % SYNTHETIC_TG_SPACE) - 1


def offset_point(lat: float, lon: float, north_m: float, east_m: float) -> tuple[float, float]:
    """Nuqtani metrlarda siljitadi (kichik masofalar uchun tekis yaqinlashuv)."""
    d_lat = north_m / METERS_PER_DEGREE_LAT
    d_lon = east_m / (METERS_PER_DEGREE_LAT * math.cos(math.radians(lat)))
    return lat + d_lat, lon + d_lon


@dataclass(frozen=True)
class OutageSpec:
    """Bitta sun'iy uzilish — `05` §9.1 dagi kirish parametrlari.

    Uchta parametr §9.1 da yo'q, lekin §9.3 oltin ssenariylarisiz
    ifodalab bo'lmaydi va shuning uchun qo'shildi:

    * `reports_per_user` — 3-ssenariy («bitta foydalanuvchi 5 marta»);
    * `restore` — 6-ssenariy («`restored` xabarlari — darhol yopilish»);
    * `report_window_min` — odamlar bir vaqtda emas, oyna ichida yozadi.
    """

    name: str
    lat: float
    lon: float
    radius_m: float
    starts_at: datetime
    duration_min: int
    users: int
    report_probability: float
    reports_per_user: int = 1
    restore: bool = False
    report_window_min: int = DEFAULT_REPORT_WINDOW_MIN
    #: Uylar orasidagi eng kichik masofa. `None` — cheklovsiz (tabiiy
    #: taqsimot). `05` §4.3 xabar beruvchilarni **>= 50 m** shartida
    #: mustaqil deb sanaydi, ya'ni tasdiqlanishi kutilgan ssenariyda uylar
    #: shu masofadan yaqin bo'lsa, ssenariy tasodifan yiqilardi: RNG uchta
    #: nuqtani bir joyga tashlashi mumkin.
    min_spacing_m: float | None = None
    #: Bitta odamning ketma-ket xabarlari orasidagi tanaffus. `None` bo'lsa
    #: — rate limit + 1 daqiqa (`05` §6.3): undan tigizroq oqimni
    #: `intake.check_rate_limit` rad etardi va 3-ssenariy hech narsani
    #: tekshirmasdi.
    repeat_gap_min: float | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise SimulationError("uzilish nomi bo'sh bo'lmasligi kerak")
        if self.radius_m <= 0:
            raise SimulationError(f"{self.name}: radius musbat bo'lishi kerak")
        if self.duration_min <= 0:
            raise SimulationError(f"{self.name}: davomiylik musbat bo'lishi kerak")
        if self.users < 0:
            raise SimulationError(f"{self.name}: foydalanuvchilar soni manfiy")
        if not 0.0 <= self.report_probability <= 1.0:
            raise SimulationError(f"{self.name}: ehtimol [0, 1] oralig'ida bo'lishi kerak")
        if self.reports_per_user < 1:
            raise SimulationError(f"{self.name}: har foydalanuvchidan kamida bitta xabar")
        if self.report_window_min < 0:
            raise SimulationError(f"{self.name}: xabar oynasi manfiy")
        if self.min_spacing_m is not None and self.min_spacing_m < 0:
            raise SimulationError(f"{self.name}: uylar orasidagi masofa manfiy")
        if self.span_min > self.duration_min:
            raise SimulationError(
                f"{self.name}: xabarlar oynasi ({self.span_min:.0f} daq) davomiylikdan "
                f"({self.duration_min} daq) uzun — uzilish tugaganidan keyin "
                "yoziladigan xabar ma'nosiz"
            )

    @property
    def gap_min(self) -> float:
        return (
            self.repeat_gap_min
            if self.repeat_gap_min is not None
            else settings.report_rate_limit_min + 1
        )

    @property
    def span_min(self) -> float:
        """Eng kech xabar uzilish boshlanishidan qancha keyin bo'lishi mumkin."""
        return self.report_window_min + (self.reports_per_user - 1) * self.gap_min

    @property
    def ends_at(self) -> datetime:
        return self.starts_at + timedelta(minutes=self.duration_min)


@dataclass(frozen=True)
class SyntheticReport:
    """Oqimning bitta elementi — hali bazaga yozilmagan xabar."""

    at: datetime
    user_key: str
    lat: float
    lon: float
    kind: str
    outage_name: str

    def as_dict(self) -> dict[str, object]:
        return {
            "at": self.at.isoformat(),
            "user_key": self.user_key,
            "lat": round(self.lat, 6),
            "lon": round(self.lon, 6),
            "kind": self.kind,
            "outage": self.outage_name,
        }


def _homes(spec: OutageSpec, rng: random.Random) -> list[tuple[float, float]]:
    """Foydalanuvchilarning uy nuqtalari — doira bo'ylab **yuza bo'yicha** teng.

    `r = R·√u`, `r = R·u` emas: ikkinchisida nuqtalar markazga yig'ilib
    qolardi va hodisaning radiusi haqiqiydan doim kichik chiqardi, ya'ni
    generator klasterlashni o'zi kutgan javobga qarab surardi.

    Nuqta odamga **biriktirilgan**: bitta odamning takroriy xabarlari bir
    joydan keladi. Har xabarga yangi nuqta olinsa, 3-ssenariydagi yolg'iz
    foydalanuvchi beshta turli manzildan yozgandek ko'rinardi.

    `min_spacing_m` berilgan bo'lsa — rad etish bilan tanlash: yaqin tushgan
    nuqta qayta uriniladi. Doiraga sig'masa, jimgina kamroq uy qo'yish
    o'rniga xato beriladi (ssenariy sababsiz «tasdiqlanmadi» degan natija
    berardi).
    """
    homes: list[tuple[float, float]] = []
    for index in range(spec.users):
        for attempt in range(MAX_PLACEMENT_ATTEMPTS):
            distance = spec.radius_m * math.sqrt(rng.random())
            angle = rng.uniform(0.0, 2 * math.pi)
            home = offset_point(
                spec.lat, spec.lon, distance * math.cos(angle), distance * math.sin(angle)
            )
            if spec.min_spacing_m is None or all(
                haversine_m(home, other) >= spec.min_spacing_m for other in homes
            ):
                homes.append(home)
                break
            if attempt == MAX_PLACEMENT_ATTEMPTS - 1:
                raise SimulationError(
                    f"{spec.name}: {spec.users} ta uyni {spec.radius_m:.0f} m doiraga "
                    f"{spec.min_spacing_m:.0f} m oralab joylashtirib bo'lmadi "
                    f"({index} tasi joylashdi) — radiusni oshiring yoki sonini kamaytiring"
                )
    return homes


def generate(specs: Sequence[OutageSpec], *, seed: str = DEFAULT_SEED) -> list[SyntheticReport]:
    """Uzilishlar tavsifidan xabarlar oqimini yasaydi.

    Har uzilish **o'z** tasodifiy oqimiga ega (`seed|name`): aks holda
    ro'yxatga yangi uzilish qo'shilishi undan keyingilarining hammasini
    siljitardi va ikki ssenariyni solishtirib bo'lmasdi.
    """
    stream: list[SyntheticReport] = []
    for spec in specs:
        rng = random.Random(f"{seed}|{spec.name}")
        for index, home in enumerate(_homes(spec, rng)):
            reports_at_home = rng.random() < spec.report_probability
            first_delay = rng.uniform(0.0, spec.report_window_min)
            restore_delay = rng.uniform(0.0, RESTORE_WINDOW_MIN)
            if not reports_at_home:
                # Tasodifiy sonlar baribir olinadi: shunda ehtimol
                # o'zgarganda faqat «kim yozdi» o'zgaradi, qolgan oqim emas.
                continue
            user_key = f"{spec.name}#{index}"
            for repeat in range(spec.reports_per_user):
                moment = spec.starts_at + timedelta(
                    minutes=first_delay + repeat * spec.gap_min
                )
                stream.append(
                    SyntheticReport(
                        at=moment,
                        user_key=user_key,
                        lat=home[0],
                        lon=home[1],
                        kind=intake.KIND_OUTAGE,
                        outage_name=spec.name,
                    )
                )
            if spec.restore:
                stream.append(
                    SyntheticReport(
                        at=spec.ends_at + timedelta(minutes=restore_delay),
                        user_key=user_key,
                        lat=home[0],
                        lon=home[1],
                        kind=intake.KIND_RESTORED,
                        outage_name=spec.name,
                    )
                )
    stream.sort(key=lambda r: (r.at, r.user_key, r.kind))
    return stream


def too_close(specs: Sequence[OutageSpec]) -> list[tuple[str, str, int]]:
    """Markazlari `cluster_eps_m` dan yaqin uzilish juftliklari.

    4-ssenariy («ikki uzoq mahalla — ikki alohida hodisa») markazlar
    yetarlicha uzoq bo'lgandagina ma'noga ega. Yaqin bo'lsa klasterlash
    ularni **to'g'ri** birlashtiradi va ssenariy o'zi tekshirmoqchi
    bo'lgan narsaning teskarisini tasdiqlagandek ko'rinardi.
    """
    pairs: list[tuple[str, str, int]] = []
    for i, first in enumerate(specs):
        for second in specs[i + 1 :]:
            distance = haversine_m((first.lat, first.lon), (second.lat, second.lon))
            if distance < settings.cluster_eps_m:
                pairs.append((first.name, second.name, int(distance)))
    return pairs


def restore_out_of_window(specs: Sequence[OutageSpec]) -> list[tuple[str, int]]:
    """«Svet keldi» xabari klasterlash oynasidan tashqarida qolgan uzilishlar.

    `05` §4.2: nomzod hodisa oxirgi xabari `cluster_time_window_min` ichida
    bo'lgani. Uzilish shundan uzoq davom etsa, `restored` xabari ochiq
    hodisani **topa olmaydi** va biriktirilmagan qoladi — bu xato emas,
    lekin ssenariy «yopilish» ni tekshirmoqchi bo'lsa, u jimgina
    tekshirmasdi.

    Xato emas, ogohlantirish: haqiqiy uzilishda odamlar davomida ham yozib
    turadi, ya'ni `last_report_at` yangilanadi. Generator esa xabarlarni
    faqat boshidagi oynada beradi.
    """
    late: list[tuple[str, int]] = []
    for spec in specs:
        if not spec.restore:
            continue
        silence = spec.duration_min - spec.report_window_min
        if silence > settings.cluster_time_window_min:
            late.append((spec.name, int(silence)))
    return late


def stream_summary(stream: Sequence[SyntheticReport]) -> dict[str, object]:
    """Oqimning bazasiz xulosasi — `preview` va hisobot uchun."""
    if not stream:
        return {"reports": 0, "users": 0, "outage_reports": 0, "restored_reports": 0}
    return {
        "reports": len(stream),
        "users": len({r.user_key for r in stream}),
        "outage_reports": sum(1 for r in stream if r.kind == intake.KIND_OUTAGE),
        "restored_reports": sum(1 for r in stream if r.kind == intake.KIND_RESTORED),
        "first_at": stream[0].at.isoformat(),
        "last_at": stream[-1].at.isoformat(),
    }


# --------------------------------------------------------------------------
# Oltin ssenariylar (`05` §9.3)
# --------------------------------------------------------------------------

#: Ssenariylarning umumiy boshlang'ich nuqtasi va vaqti. Qiymat muhim emas,
#: **barqarorligi** muhim: ssenariy natijasi sana o'zgarishidan tebranmasin.
BASE_LAT, BASE_LON = 39.6547, 66.9597
BASE_AT = datetime(2026, 8, 1, 18, 0, tzinfo=timezone.utc)

#: Tasdiqlanishi kutilgan ssenariylarda uylar orasidagi eng kichik masofa —
#: `05` §4.3 dagi mustaqillik sharti bilan bir xil manbadan olinadi.
SPACING = float(settings.reporter_min_distance_m)


@dataclass(frozen=True)
class Scenario:
    """`05` §9.3 dagi bitta oltin ssenariy.

    `expect_confirmed` — kutilgan **tasdiqlangan** hodisalar soni.
    `pending` sanalmaydi: har birinchi xabar o'zi hodisa yaratadi
    (`05` §4.2), ya'ni «hodisa yaratilmaydi» ni so'zma-so'z o'lchash
    mumkin emas — mahsulot va'dasi tasdiqlash darajasida.
    """

    key: str
    title: str
    specs: tuple[OutageSpec, ...]
    expect_confirmed: int
    note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "title": self.title,
            "outages": [s.name for s in self.specs],
            "expect_confirmed": self.expect_confirmed,
            "note": self.note,
        }


def _spec(name: str, **over) -> OutageSpec:
    base: dict[str, object] = {
        "name": name,
        "lat": BASE_LAT,
        "lon": BASE_LON,
        "radius_m": 150.0,
        "starts_at": BASE_AT,
        "duration_min": 120,
        "users": 3,
        "report_probability": 1.0,
        # 30 emas, 15 daqiqa: `06` §2.1 da `time_factor` 30 daqiqada 1.0 dan
        # 0.7 ga tushadi, ya'ni oyna to'liq 30 bo'lsa uchta qo'shni
        # ssenariysining balli `W = 3.0` chegarasidan urug'ga qarab pastga
        # tushib ketardi. Ssenariy chegarani emas, **mantiqni** tekshirishi
        # kerak.
        "report_window_min": 15,
    }
    return OutageSpec(**{**base, **over})


#: Ikkinchi mahalla — 3 km sharqda, ya'ni `cluster_eps_m` (400 m) dan ancha
#: uzoq. `too_close()` buni tekshiradi.
_FAR_LAT, _FAR_LON = offset_point(BASE_LAT, BASE_LON, 0.0, 3_000.0)

SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        key="single_house",
        title="Bitta uy — hodisa tasdiqlanmaydi",
        specs=(_spec("single", users=1, radius_m=30.0),),
        expect_confirmed=0,
        note="Bitta xabar `pending` hodisa yaratadi, lekin u tasdiqlanmaydi.",
    ),
    Scenario(
        key="three_neighbours",
        title="Uch qo'shni — hodisa tasdiqlanadi",
        specs=(_spec("neighbours", users=3, radius_m=150.0, min_spacing_m=SPACING),),
        expect_confirmed=1,
        note="Uylar >= 50 m oralab qo'yiladi, aks holda `05` §4.3 ularni bitta "
        "manba deb sanardi.",
    ),
    Scenario(
        key="one_user_five_times",
        title="Bitta foydalanuvchi 5 marta — tasdiqlanmaydi",
        specs=(
            _spec(
                "repeater",
                users=1,
                radius_m=30.0,
                reports_per_user=5,
                report_window_min=5,
                duration_min=180,
            ),
        ),
        expect_confirmed=0,
        note="`06` §7: `W` foydalanuvchi bo'yicha yig'iladi, xabar bo'yicha emas.",
    ),
    Scenario(
        key="two_distant_mahallas",
        title="Ikki uzoq mahalla bir vaqtda — ikki alohida hodisa",
        specs=(
            _spec("west", users=4, radius_m=150.0, min_spacing_m=SPACING),
            _spec(
                "east",
                lat=_FAR_LAT,
                lon=_FAR_LON,
                users=4,
                radius_m=150.0,
                min_spacing_m=SPACING,
            ),
        ),
        expect_confirmed=2,
    ),
    Scenario(
        key="sparse_area",
        title="Kam zichlikdagi hudud — «ma'lumot yetarli emas»",
        specs=(_spec("sparse", users=2, radius_m=1_200.0, min_spacing_m=SPACING),),
        expect_confirmed=0,
        note="Keng hududda ikkita xabar. Ehtimol emas, **son** qotirilgan: "
        "`p = 0.17` bilan xabar beruvchilar soni urug'dan urug'ga 1 dan 5 gacha "
        "tebranardi va ssenariy tasodifan teskari natija berardi.",
    ),
    Scenario(
        key="restored_sweep",
        title="`restored` xabarlari — darhol yopilish",
        specs=(
            _spec(
                "restored",
                users=4,
                radius_m=150.0,
                min_spacing_m=SPACING,
                restore=True,
                duration_min=60,
            ),
        ),
        expect_confirmed=1,
        note="Tasdiqlangan hodisa `resolved` ga o'tadi (`05` §4.5). Davomiylik "
        "`cluster_time_window_min` dan qisqa: uzunroq bo'lsa «svet keldi» xabari "
        "nomzod topa olmasdi va hodisa ochiq qolardi.",
    ),
)

SCENARIO_BY_KEY: dict[str, Scenario] = {s.key: s for s in SCENARIOS}


# --------------------------------------------------------------------------
# Yozish qismi
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RunResult:
    """Simulyatsiya natijasi — hisobot va ssenariy testi uchun."""

    scenario: str | None
    region_code: str
    seed: str
    since: datetime
    until: datetime
    users: int
    generated: int
    written: int
    rate_limited: int
    out_of_region: int
    unassigned: int
    outages: int
    by_status: dict[str, int] = field(default_factory=dict)
    fingerprint: str = ""
    applied: bool = False
    expect_confirmed: int | None = None

    @property
    def confirmed(self) -> int:
        return self.by_status.get("confirmed", 0)

    @property
    def resolved(self) -> int:
        return self.by_status.get("resolved", 0)

    @property
    def matches_expectation(self) -> bool | None:
        """Ssenariy kutilgan natijani berdimi.

        `resolved` ham tasdiqlangan deb sanaladi: 6-ssenariyda hodisa
        avval `confirmed` bo'ladi, keyin «svet keldi» uni yopadi —
        yopilgan hodisa tasdiqlanmagan degani emas.
        """
        if self.expect_confirmed is None:
            return None
        return self.confirmed + self.resolved == self.expect_confirmed

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "region": self.region_code,
            "seed": self.seed,
            "since": self.since.isoformat(),
            "until": self.until.isoformat(),
            "users": self.users,
            "generated": self.generated,
            "written": self.written,
            "rate_limited": self.rate_limited,
            "out_of_region": self.out_of_region,
            "unassigned": self.unassigned,
            "outages": self.outages,
            "by_status": dict(sorted(self.by_status.items())),
            "expect_confirmed": self.expect_confirmed,
            "matches_expectation": self.matches_expectation,
            "fingerprint": self.fingerprint,
            "applied": self.applied,
        }


@asynccontextmanager
async def transaction(*, apply: bool) -> AsyncIterator[AsyncSession]:
    """`--apply` bo'lsa commit, aks holda **har doim** rollback (E6 dagidek).

    Ochiq nom (`_scope` emas): ssenariy testlari aynan shu kontekstda
    ishlaydi — hisob-kitob haqiqiy, natija esa bazada qolmaydi.
    """
    async with get_sessionmaker()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        if apply:
            await session.commit()
        else:
            await session.rollback()


async def ensure_writable(session: AsyncSession, region_id: uuid.UUID) -> None:
    """`--apply` xavfsizmi. Xavfsiz bo'lmasa — `SimulationBlocked`.

    Ikkita to'siq va ikkalasi ham qaytarib bo'lmaydigan zarar haqida:

    1. **Haqiqiy xabarlar.** Sun'iy va haqiqiy xabar bir mintaqada
       aralashsa, statistika, Coverage Index va E11 sozlashi buziladi.
    2. **Faol obuna.** Sun'iy hodisa `confirmed` ga o'tsa, klasterlash
       outbox ga yozadi va `process_outbox` uni haqiqiy odamga yuboradi —
       yuborilgan xabarnomani qaytarib bo'lmaydi.
    """
    real = await reports_q.count_by_real_users(session, region_id)
    if real:
        raise SimulationBlocked(
            f"mintaqada {real} ta haqiqiy xabar bor — sun'iy ma'lumotni ularga "
            "aralashtirib bo'lgach ajratib olish imkonsiz"
        )
    active = await subs.count_active(session)
    if active:
        raise SimulationBlocked(
            f"bazada {active} ta faol obuna bor — sun'iy hodisa tasdiqlansa "
            "haqiqiy odamga bildirishnoma ketardi"
        )


async def ensure_users(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    stream: Sequence[SyntheticReport],
) -> dict[str, intake.User]:
    """Oqimdagi har bir `user_key` uchun sun'iy akkaunt.

    Akkaunt eng erta xabaridan 30 kun oldin «yaratilgan»: `05` §4.3 yosh
    filtri aks holda hamma xabarni chetlab o'tardi.
    """
    earliest: dict[str, datetime] = {}
    for item in stream:
        current = earliest.get(item.user_key)
        if current is None or item.at < current:
            earliest[item.user_key] = item.at

    users: dict[str, intake.User] = {}
    for user_key, first_at in earliest.items():
        user, _ = await intake.get_or_create_user(
            session,
            tg_id=synthetic_tg_id(user_key),
            region_id=region_id,
            created_at=first_at - timedelta(days=SYNTHETIC_ACCOUNT_AGE_DAYS),
        )
        users[user_key] = user
    return users


async def run(
    session: AsyncSession,
    *,
    region: geo.RegionLike,
    stream: Sequence[SyntheticReport],
    seed: str,
    applied: bool,
    scenario: str | None = None,
    expect_confirmed: int | None = None,
) -> RunResult:
    """Oqimni bazaga o'tkazadi. Chaqiruvchi tranzaksiyani boshqaradi."""
    if not stream:
        raise SimulationError("oqim bo'sh — hech kim xabar yozmadi")

    since = stream[0].at
    until = stream[-1].at + timedelta(minutes=1)
    users = await ensure_users(session, region_id=region.id, stream=stream)

    written = rate_limited = out_of_region = unassigned = 0
    outage_ids: set[uuid.UUID] = set()

    for item in stream:
        user = users[item.user_key]
        try:
            resolution = await geo.resolve(
                session, user_id=user.id, region=region, lat=item.lat, lon=item.lon
            )
        except OutOfRegionError:
            out_of_region += 1
            continue
        try:
            await intake.check_rate_limit(session, user.id, kind=item.kind, now=item.at)
        except RateLimitedError:
            # Bot ham aynan shunday qiladi — oqimni «tuzatib» yuborish
            # generatorni haqiqiy yo'ldan uzoqlashtirardi.
            rate_limited += 1
            continue

        created = await intake.create_report(
            session,
            user=user,
            kind=item.kind,
            lat=resolution.lat,
            lon=resolution.lon,
            public_lat=resolution.public_lat,
            public_lon=resolution.public_lon,
            h3_r9=resolution.h3_r9,
            region_id=resolution.region_id,
            district_id=resolution.district_id,
            mahalla_id=resolution.mahalla_id,
            now=item.at,
        )
        written += 1

        assignment = await clustering.assign(
            session,
            clustering.ReportRef(
                id=created.id,
                user_id=created.user_id,
                kind=created.kind,
                lat=created.lat,
                lon=created.lon,
                region_id=created.region_id,
                district_id=created.district_id,
                mahalla_id=created.mahalla_id,
                created_at=created.created_at,
                source_code=created.source_code,
            ),
        )
        if assignment.outage_id is None:
            unassigned += 1
        else:
            outage_ids.add(assignment.outage_id)

    await session.flush()
    rows = await cluster_repo.fingerprint_rows(
        session, region_id=region.id, since=since, until=until
    )
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row.status] = by_status.get(row.status, 0) + 1

    return RunResult(
        scenario=scenario,
        region_code=region.code,
        seed=seed,
        since=since,
        until=until,
        users=len(users),
        generated=len(stream),
        written=written,
        rate_limited=rate_limited,
        out_of_region=out_of_region,
        unassigned=unassigned,
        outages=len(rows),
        by_status=by_status,
        fingerprint=fingerprint(rows),
        applied=applied,
        expect_confirmed=expect_confirmed,
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def specs_from_args(args: argparse.Namespace) -> tuple[tuple[OutageSpec, ...], Scenario | None]:
    """Ssenariy nomi yoki qo'lda berilgan parametrlar — bittasi shart."""
    if args.scenario:
        scenario = SCENARIO_BY_KEY.get(args.scenario)
        if scenario is None:
            known = ", ".join(sorted(SCENARIO_BY_KEY))
            raise SimulationError(f"noma'lum ssenariy: {args.scenario} (mavjud: {known})")
        return scenario.specs, scenario

    missing = [
        name
        for name in ("lat", "lon", "at", "users")
        if getattr(args, name, None) is None
    ]
    if missing:
        raise SimulationError(
            "`--scenario` berilmasa, `--lat --lon --at --users` majburiy "
            f"(yetishmayapti: {', '.join('--' + m for m in missing)})"
        )
    spec = OutageSpec(
        name=args.name,
        lat=args.lat,
        lon=args.lon,
        radius_m=args.radius_m,
        starts_at=args.at,
        duration_min=args.duration_min,
        users=args.users,
        report_probability=args.probability,
        reports_per_user=args.reports_per_user,
        restore=args.restore,
    )
    return (spec,), None


def warn(specs: Sequence[OutageSpec]) -> None:
    """Ssenariy o'zi ko'zlagan narsani tekshirmay qoladigan holatlar."""
    for first, second, distance in too_close(specs):
        print(
            f"diqqat: `{first}` va `{second}` markazlari {distance} m — "
            f"klasterlash oynasi {settings.cluster_eps_m} m, ya'ni ular bitta "
            "hodisaga birlashishi kutiladi",
            file=sys.stderr,
        )
    for name, silence in restore_out_of_window(specs):
        print(
            f"diqqat: `{name}` uzilishi oxirgi xabardan keyin {silence} daqiqa "
            f"jim turadi ({settings.cluster_time_window_min} daq oynadan uzun) — "
            "«svet keldi» xabari ochiq hodisani topa olmaydi",
            file=sys.stderr,
        )


def cmd_scenarios(args: argparse.Namespace) -> int:
    print(json.dumps([s.as_dict() for s in SCENARIOS], ensure_ascii=False, indent=2))
    return EXIT_OK


def cmd_preview(args: argparse.Namespace) -> int:
    """Bazasiz: oqimni yasaydi va ko'rsatadi (`05` §9.1 «chiqish oqimi»)."""
    specs, scenario = specs_from_args(args)
    warn(specs)
    stream = generate(specs, seed=args.seed)
    payload: dict[str, object] = {
        "scenario": scenario.key if scenario else None,
        "seed": args.seed,
        "summary": stream_summary(stream),
    }
    if args.show_reports:
        payload["reports"] = [r.as_dict() for r in stream]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return EXIT_OK


async def cmd_run(args: argparse.Namespace) -> int:
    try:
        specs, scenario = specs_from_args(args)
        stream = generate(specs, seed=args.seed)
    except SimulationError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE

    warn(specs)

    try:
        async with transaction(apply=args.apply) as session:
            region = await geo.find_region(session, args.region)
            if region is None:
                print(f"mintaqa topilmadi: {args.region}", file=sys.stderr)
                return EXIT_USAGE
            if args.apply:
                await ensure_writable(session, region.id)
            result = await run(
                session,
                region=region,
                stream=stream,
                seed=args.seed,
                applied=args.apply,
                scenario=scenario.key if scenario else None,
                expect_confirmed=scenario.expect_confirmed if scenario else None,
            )
    except SimulationBlocked as exc:
        print(f"to'xtatildi: {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    except SimulationError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE

    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    if not args.apply:
        print("\nQuruq yurish — hech narsa yozilmadi. Yozish uchun `--apply`.")
    if result.matches_expectation is False:
        print(
            f"\nssenariy `{result.scenario}`: kutilgan {result.expect_confirmed} ta "
            f"tasdiqlangan hodisa, natija {result.confirmed + result.resolved} ta",
            file=sys.stderr,
        )
        return EXIT_MISMATCH
    return EXIT_OK


def add_spec_arguments(parser: argparse.ArgumentParser) -> None:
    """`05` §9.1 dagi kirish parametrlari."""
    parser.add_argument("--scenario", help=f"oltin ssenariy: {', '.join(SCENARIO_BY_KEY)}")
    parser.add_argument("--name", default="adhoc", help="uzilish nomi (hisobotda)")
    parser.add_argument("--lat", type=float, help="markaz kengligi")
    parser.add_argument("--lon", type=float, help="markaz uzunligi")
    parser.add_argument("--radius-m", type=float, default=300.0, help="uzilish radiusi, m")
    parser.add_argument("--at", type=parse_moment, help="boshlanish vaqti (ISO)")
    parser.add_argument("--duration-min", type=int, default=120, help="davomiylik, daqiqa")
    parser.add_argument("--users", type=int, help="hududdagi foydalanuvchilar soni")
    parser.add_argument(
        "--probability", type=float, default=0.5, help="xabar berish ehtimoli [0, 1]"
    )
    parser.add_argument(
        "--reports-per-user", type=int, default=1, help="har foydalanuvchidan xabarlar soni"
    )
    parser.add_argument(
        "--restore", action="store_true", help="oxirida «svet keldi» xabarlari"
    )
    parser.add_argument("--seed", default=DEFAULT_SEED, help="determinizm urug'i")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="simulate", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("scenarios", help="oltin ssenariylar ro'yxati (`05` §9.3)")
    listing.set_defaults(func=cmd_scenarios, is_async=False)

    preview = sub.add_parser("preview", help="oqimni bazasiz yasab ko'rsatish")
    add_spec_arguments(preview)
    preview.add_argument(
        "--show-reports", action="store_true", help="har bir xabarni ham chiqarish"
    )
    preview.set_defaults(func=cmd_preview, is_async=False)

    runner = sub.add_parser("run", help="oqimni bazaga o'tkazish (standart — quruq yurish)")
    add_spec_arguments(runner)
    runner.add_argument("--region", default=settings.default_region_code, help="regions.code")
    runner.add_argument(
        "--apply", action="store_true", help="natijani yozish (standart — quruq yurish)"
    )
    runner.set_defaults(func=cmd_run, is_async=True)
    return parser


async def _main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.is_async:
            return await args.func(args)
        return args.func(args)
    except SimulationError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE
    finally:
        if args.is_async:
            await dispose_engine()


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())

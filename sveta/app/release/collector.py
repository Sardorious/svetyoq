"""Gate o'lchovlarini yig'ish (`03` §6) — modullararo ulash qatlami.

`05` §1: modul boshqa modulning jadvaliga to'g'ridan-to'g'ri murojaat
qilmaydi. Shu sababli bu yerda bitta ham `SELECT` yo'q — har bir son
o'z modulining so'rovidan olinadi (`obs/collector.py` bilan bir xil
tartib):

| Mezon | Manba |
|---|---|
| `confirmable_share` | `app.clustering.repository` |
| `map_refresh` | `app.clustering.snapshot` |
| `regions_active` | `app.geo.registry` |
| `string_parity` | `app.core.i18n` (bazasiz) |

## Nima uchun to'rttadan ko'p emas

Qolgan beshta mezon **ataylab** `None` bilan qaytadi va bu shu
running eng qimmatli natijasi: ular o'lchanmagani hujjatda emas,
kodda ko'rinadi.

* `answer_p90` — `03` §4 R1.0 chiqish mezoni ham, §11 «Nima
  o'lchanadi» jadvalining R1.0 qatori ham «Time-to-answer p90» ni
  talab qiladi, `05` §10 metrikalar jadvalida esa bunday metrika
  **yo'q**. Eng yaqini `time_to_confirm_seconds`, lekin u boshqa
  narsani o'lchaydi: hodisa qachon tasdiqlangani, foydalanuvchi
  savoliga qachon javob berilgani emas. Ikkalasini tenglashtirish
  gate ni soxta yopardi.
* `notify_delivery_p90` — `outbox_lag_seconds` navbatning yoshini
  beradi, yetkazish vaqtini emas (`sent_at − confirmed_at` hech
  qayerda hisoblanmaydi).
* `wrong_notify_measured` — o'lchov mexanizmi umuman yo'q.
* `aggregate_diff` va `coverage_index` — hisoblanadi
  (`stats.service`), lekin butun vitrinani qurishni talab qiladi;
  gate hisoboti admin sahifasining yengil so'rovi bo'lib qolishi
  uchun ular keyingi qadamga qoldirildi (`PROGRESS.md` «Ochiq
  savollar»).
* `reported_area_share` — chegarasi ham yo'q (`N` Faza 0 dan), va
  «hudud ulushi» maydon bo'yicha o'lchanishi kerak, tuman soni
  bo'yicha emas; sonni tuman soniga almashtirish jimgina boshqa
  narsani o'lchardi.

Qo'lda tasdiqlanadigan (`MANUAL`) mezonlar bu yerda umuman
hisoblanmaydi: ularning qayerda saqlanishi mahsulot qarori
(`PROGRESS.md` «Ochiq savollar»).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import repository as outages_repo
from app.clustering import snapshot as snapshot_mod
from app.core import i18n
from app.core.config import settings
from app.geo import registry
from app.release import gates


def string_parity() -> float:
    """UZ/RU string pariteti — `1.0` to'liq paritet (`03` §4 R1.0).

    Bazasiz va **so'rov paytida** hisoblanadi: kataloglar deploy bilan
    keladi, ya'ni bu son konteynerdagi haqiqiy holatni ko'rsatadi.
    Testdagi paritet tekshiruvi (`tests/test_i18n.py`) boshqa savol —
    u repoda paritet borligini aytadi, bu esa **ishga tushgan
    nusxada**.

    Maxraj — ikkala katalogning **birlashmasi**: bir tomonlama
    hisoblash (`uz` dagi kalitlar bo'yicha) `ru` da ortiqcha kalit
    qolganini ko'rmasdi.
    """
    total = len(i18n.all_keys())
    if total == 0:
        return 0.0
    missing = sum(len(i18n.missing_keys(lang)) for lang in i18n.SUPPORTED_LANGUAGES)
    languages = len(i18n.SUPPORTED_LANGUAGES)
    return max(0.0, 1.0 - missing / (total * languages))


async def _map_refresh_s(
    session: AsyncSession, region_id: uuid.UUID, now: datetime
) -> float | None:
    """Snapshot yoshi soniyada. Snapshot yo'q bo'lsa — `None`.

    **`None`, nol emas.** Snapshot umuman qurilmagan holat «xarita
    hozirgina yangilandi» degani emas; nol qaytarish G-5 ning bu
    mezonini aynan eng yomon holatda yopardi.
    """
    built = (await snapshot_mod.built_at_by_region(session)).get(region_id)
    if built is None:
        return None
    return max(0.0, (now - built).total_seconds())


async def collect(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    now: datetime | None = None,
) -> dict[str, float | None]:
    """Bitta mintaqa uchun gate o'lchovlari.

    Kalitlar `gates.CRITERION_BY_CODE` dan olinadi, ya'ni mezon kodi
    o'zgarsa bu yerda `KeyError` chiqadi — jimgina «o'lchanmagan»
    emas.
    """
    moment = now or datetime.now(timezone.utc)
    since = moment - timedelta(days=settings.coverage_window_days)

    total, confirmable = await outages_repo.confirmable_counts(
        session,
        region_id=region_id,
        since=since,
        min_reporters=gates.MIN_INDEPENDENT_REPORTS,
    )
    # Hodisa bo'lmasa ulush **noma'lum**, nol emas: bo'sh namunada
    # «zichlik yetarli emas» degan xulosa ham, teskarisi ham
    # asossiz — G-4 shunchaki o'lchanmagan bo'lib qoladi.
    share = confirmable / total if total else None

    active = await registry.active_regions(session)

    values: dict[str, float | None] = {
        "confirmable_share": share,
        "reported_area_share": None,
        "answer_p90": None,
        "map_refresh": await _map_refresh_s(session, region_id, moment),
        "string_parity": string_parity(),
        "notify_delivery_p90": None,
        "aggregate_diff": None,
        "coverage_index": None,
        "regions_active": float(len(active)),
    }
    # Har bir kalit reyestrda borligiga ishonch: `evaluate` notanish
    # kalitni xato deb hisoblaydi, lekin **yo'qolgan** kalitni emas.
    for code in values:
        gates.CRITERION_BY_CODE[code]
    return values

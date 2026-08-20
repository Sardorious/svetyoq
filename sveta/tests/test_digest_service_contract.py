"""`app/admin/digest_service.py` — ulash qatlamining kontrakti (`05` §8).

## Nega bu fayl kerak

`digest_service` — «yupqa» modul: u o'zi hech narsa hisoblamaydi, faqat
to'rtta boshqa modulning so'rovini chaqiradi va natijasini `Digest` ning
o'n uchta maydoniga **taqsimlaydi**. Aynan shu taqsimot o'lchanmagan edi.

168-run mutatsiyasi (21 mutant) buni raqam bilan ko'rsatdi: **11 tasi omon
qoldi**, ya'ni butun to'plam (4140 test) ularni sezmadi. Sabab bitta va
tarkibiy — `tests/test_daily_digest_db.py` ning fikstyurasi **bitta
mintaqa, bitta kun** quradi va faqat **hodisa** sonlarini tekshiradi:

* xabar sonlarining beshala chelagi (`total`/`outage`/`restored`/
  `unassigned`/`reporters`) o'sha fikstyurada **bir xil qiymatga** tushadi
  (`1` yoki `0`), shuning uchun ularni o'zaro almashtirish ko'rinmaydi;
* moderatsiya, bildirishnoma va outbox chelaklari umuman to'ldirilmaydi,
  ya'ni ularning **oynasi** ham, chaqiruvi ham o'lchanmaydi;
* mintaqa bitta bo'lgani uchun `mark_delivered` va `load` dagi
  `region_id` shartini olib tashlash hech qanday farq bermaydi;
* `now=` argumenti uzatiladi, lekin **natijasi tekshirilmaydi** — ichkarida
  `datetime.now()` ishlatilsa ham testlar yashil qolardi.

Bu — `svetyoq-fixture-must-separate` naqshining eng katta ko'rinishi:
shart kodda to'g'ri, uni **ajratadigan holat** fikstyurada yo'q.

## Qanday qulflanadi

Har bo'lim omon qolgan mutantning aniq sinfini yopadi:

| § | Yopilgan mutantlar | Nima ajratiladi |
|---|---|---|
| 1 | M04, M05, M06 | beshala xabar chelagi **turli** songa ega |
| 2 | M07 | moderatsiya oynasi `[start, end)` |
| 3 | M10 | bildirishnoma oynasi `[start, end)` |
| 4 | M08 | `outbox_pending` haqiqatan so'raladi |
| 5 | M14, M18 | `now=` argumenti bazaga yozilgan qiymatni belgilaydi |
| 6 | M17, M19 | `mark_delivered` va `load` — mintaqa bo'yicha ajratilgan |

M21 (`scalar_one_or_none` → `scalars().first()`) **ekvivalent** deb
belgilandi: `daily_digest` ning birlamchi kaliti `(region_id,
digest_date)`, ya'ni ikkinchi qator bo'lishi mumkin emas. Lekin u bekorga
turmaydi — aynan `scalar_one_or_none` M20 ni (`load` dan `digest_date`
shartini olib tashlash) `MultipleResultsFound` bilan o'ldiradi. Shuning
uchun §6 da `load` ning ikkala sharti ham alohida ajratiladi.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.admin import digest as digest_mod
from app.admin import digest_service
from app.db.session import session_scope

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
DAY = date(2026, 8, 7)
#: Toshkent (UTC+5) bo'yicha 7-avgust: `[2026-08-06 19:00Z, 2026-08-07 19:00Z)`.
INSIDE = datetime(2026, 8, 7, 6, 0, tzinfo=timezone.utc)
#: Sutkaning aynan tutashgan lahzasi — `end`, ya'ni **ertangi** kunniki.
BOUNDARY = datetime(2026, 8, 7, 19, 0, tzinfo=timezone.utc)
#: Kundan ancha keyin.
AFTER = datetime(2026, 8, 8, 6, 0, tzinfo=timezone.utc)

#: `now=` argumentining ta'sirini ajratadigan sanalar. Ikkalasi ham
#: o'tmishda: kod `datetime.now()` ga tushib qolsa, farq bir yildan katta
#: bo'ladi va tasodifan mos kelib qolishi mumkin emas.
BUILT_AT = datetime(2026, 8, 8, 3, 0, tzinfo=timezone.utc)
DELIVERED_AT = datetime(2026, 8, 8, 3, 30, tzinfo=timezone.utc)


def _digest(region_code: str, day: date = DAY) -> digest_mod.Digest:
    return digest_mod.from_payload({"date": day.isoformat(), "region": region_code})


@pytest.fixture
async def two_regions():
    """Ikkita mintaqa — «bizniki» va «qo'shni».

    Qo'shni mintaqa bu fayldagi har bir tekshiruvda **teginilmagan**
    qolishi kerak: `mark_delivered` va `load` dagi `region_id` sharti
    faqat shu bilan ajratiladi.
    """
    ours, other = uuid.uuid4(), uuid.uuid4()
    async with session_scope() as session:
        for rid, name in ((ours, "Samarqand"), (other, "Qo'shni")):
            await session.execute(
                text(
                    "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                    "VALUES (:id, :code, :name, :name, "
                    "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
                ),
                {
                    "id": rid,
                    "code": f"test-{rid.hex[:8]}",
                    "name": name,
                    "lat": LAT,
                    "lon": LON,
                },
            )
    yield ours, other
    async with session_scope() as session:
        for table in ("daily_digest", "notifications", "reports", "outages", "users"):
            await session.execute(
                text(f"DELETE FROM {table} WHERE region_id IN (:a, :b)"),
                {"a": ours, "b": other},
            )
        await session.execute(
            text("DELETE FROM regions WHERE id IN (:a, :b)"), {"a": ours, "b": other}
        )


@pytest.fixture
async def clean_audit_and_outbox():
    """`audit_log` va `outbox` da `region_id` yo'q — id bo'yicha tozalanadi.

    Ikkala jadval ham butun bazaga umumiy: bu testlar qo'ygan qatorlarni
    mintaqa bilan ajratib bo'lmaydi, shuning uchun boshlang'ich `max(id)`
    eslab qolinadi va oxirida faqat undan kattasi o'chiriladi.
    """
    async with session_scope() as session:
        marks = {
            table: (
                await session.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table}"))
            ).scalar_one()
            for table in ("audit_log", "outbox")
        }
    yield
    async with session_scope() as session:
        for table, mark in marks.items():
            await session.execute(
                text(f"DELETE FROM {table} WHERE id > :mark"), {"mark": mark}
            )


async def _user(session, region_id: uuid.UUID) -> uuid.UUID:
    uid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, is_blocked, "
            "created_at) VALUES (:id, :tg, 'uz', :region, 50, false, :created)"
        ),
        {"id": uid, "tg": -int(uid.int % 10_000_000), "region": region_id, "created": INSIDE},
    )
    return uid


async def _outage(session, region_id: uuid.UUID, *, at: datetime = INSIDE) -> uuid.UUID:
    oid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO outages (id, region_id, status, layer, centroid, radius_m, "
            "independent_reporters, confidence, started_at, last_report_at, updated_at) "
            "VALUES (:id, :region, 'confirmed', 'crowd', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 120, 3, 70, "
            ":at, :at, :at)"
        ),
        {"id": oid, "region": region_id, "lat": LAT, "lon": LON, "at": at},
    )
    return oid


async def _report(
    session,
    *,
    region_id: uuid.UUID,
    user_id: uuid.UUID,
    kind: str,
    at: datetime,
    outage_id: uuid.UUID | None,
) -> None:
    await session.execute(
        text(
            "INSERT INTO reports (id, user_id, kind, geom_exact, geom_public, h3_r9, "
            "region_id, outage_id, source, created_at) VALUES (:id, :user, :kind, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :cell, "
            ":region, :outage, 'bot', :at)"
        ),
        {
            "id": uuid.uuid4(),
            "user": user_id,
            "kind": kind,
            "lat": LAT,
            "lon": LON,
            "cell": "891e2d4d4c3ffff",
            "region": region_id,
            "outage": outage_id,
            "at": at,
        },
    )


async def _collect(region_id: uuid.UUID, day: date = DAY) -> digest_mod.Digest:
    async with session_scope() as session:
        return await digest_service.collect(
            session,
            region_id=region_id,
            region_code="test",
            period=digest_mod.period_for(day),
        )


# ---------------------------------------------------------------------------
# §1. Xabar chelaklari — har biri o'z manbasidan
# ---------------------------------------------------------------------------


async def test_every_report_bucket_gets_a_distinct_count(two_regions) -> None:
    """Beshala chelak **turli** songa ega bo'lsagina almashtirish ko'rinadi.

    Mavjud fikstyurada `total == reporters == 1` va qolganlari `0` edi;
    shu sababli `reports_total=reports.outage` (M05),
    `reporters=reports.total` (M06) va `outage` ↔ `restored` (M04)
    mutantlari butun to'plamdan o'tib ketardi.

    Bu yerda taqsimot ataylab assimetrik: `total=5`, `outage=3`,
    `restored=2`, `unassigned=1`, `reporters=4` — beshta **har xil** son,
    ya'ni har qanday juftlikni almashtirish darhol ko'rinadi.
    """
    ours, _ = two_regions
    async with session_scope() as session:
        outage = await _outage(session, ours)
        users = [await _user(session, ours) for _ in range(4)]
        # 3 ta `outage` + 2 ta `restored` = 5; ulardan bittasi biriktirilmagan.
        plan = [
            (users[0], "outage", outage),
            (users[1], "outage", outage),
            (users[2], "outage", outage),
            (users[3], "restored", outage),
            (users[0], "restored", None),
        ]
        for user_id, kind, oid in plan:
            await _report(
                session,
                region_id=ours,
                user_id=user_id,
                kind=kind,
                at=INSIDE,
                outage_id=oid,
            )

    report = await _collect(ours)

    assert report.reports_total == 5
    assert report.reports_outage == 3
    assert report.reports_restored == 2
    assert report.reports_unassigned == 1
    assert report.reporters == 4
    # Beshtasi ham har xil — ya'ni yuqoridagi tasdiqlar bir-birini
    # almashtira olmaydi. Bu tekshiruv fikstyura kelajakda «tekislanib»
    # qolsa darhol yiqiladi.
    assert len(
        {
            report.reports_total,
            report.reports_outage,
            report.reports_restored,
            report.reports_unassigned,
            report.reporters,
        }
    ) == 5


async def test_report_buckets_are_scoped_to_the_region(two_regions) -> None:
    """Qo'shni mintaqaning xabarlari bizning hisobotga tushmaydi."""
    ours, other = two_regions
    async with session_scope() as session:
        user = await _user(session, other)
        await _report(
            session, region_id=other, user_id=user, kind="outage", at=INSIDE, outage_id=None
        )

    report = await _collect(ours)

    assert report.reports_total == 0
    assert report.reporters == 0


# ---------------------------------------------------------------------------
# §2. Moderatsiya oynasi
# ---------------------------------------------------------------------------


async def _audit(session, action: str, at: datetime) -> None:
    await session.execute(
        text(
            "INSERT INTO audit_log (actor_role, action, created_at) "
            "VALUES ('moderator', :action, :at)"
        ),
        {"action": action, "at": at},
    )


async def test_moderation_counts_come_from_the_period_window(
    two_regions, clean_audit_and_outbox
) -> None:
    """`moderation` — `[period.start, period.end)`, boshqa hech narsa emas.

    `collect` audit jurnalini **davr** bilan so'raydi. Oyna qulflanmagan
    edi: `since=period.end` (M07) bo'sh lug'at qaytarardi va hisobotda
    «smena hech nima qilmadi» deb ko'rinardi — jim, ishonarli nuqson.

    Chegaraviy lahza (`period.end`) ham shu yerda: u **ertangi** kunniki.
    """
    async with session_scope() as session:
        await _audit(session, "outage.reject", INSIDE)
        await _audit(session, "outage.reject", INSIDE)
        await _audit(session, "user.block", INSIDE)
        await _audit(session, "outage.merge", BOUNDARY)
        await _audit(session, "outage.merge", AFTER)

    ours, _ = two_regions
    today = await _collect(ours)
    tomorrow = await _collect(ours, DAY + timedelta(days=1))

    assert today.moderation == {"outage.reject": 2, "user.block": 1}
    assert today.moderation_total == 3
    assert tomorrow.moderation == {"outage.merge": 2}


# ---------------------------------------------------------------------------
# §3. Bildirishnoma oynasi
# ---------------------------------------------------------------------------


async def _notification(
    session, *, region_id: uuid.UUID, user_id: uuid.UUID, outage_id: uuid.UUID,
    status: str, sent_at: datetime | None,
) -> None:
    await session.execute(
        text(
            "INSERT INTO notifications (id, user_id, outage_id, region_id, status, sent_at) "
            "VALUES (:id, :user, :outage, :region, :status, :sent)"
        ),
        {
            "id": uuid.uuid4(),
            "user": user_id,
            "outage": outage_id,
            "region": region_id,
            "status": status,
            "sent": sent_at,
        },
    )


async def test_notification_counts_come_from_the_period_window(two_regions) -> None:
    """`notifications` — `sent_at` bo'yicha `[start, end)`; `queued` sanalmaydi.

    M10 (`until=period.start`) oynani nolga siqib qo'yardi va hisobotda
    yetkazish butunlay yo'qolardi. Bu — `digest.warning.notifications_failed`
    ogohlantirishining manbai, ya'ni jimgina yo'qolishi qimmatga tushadi.
    """
    ours, _ = two_regions
    async with session_scope() as session:
        outage = await _outage(session, ours)
        rows = [
            ("sent", INSIDE),
            ("sent", INSIDE),
            ("failed", INSIDE),
            ("sent", BOUNDARY),  # ertangi kun
            ("queued", None),  # hali yuborilmagan
        ]
        for status, sent_at in rows:
            await _notification(
                session,
                region_id=ours,
                user_id=await _user(session, ours),
                outage_id=outage,
                status=status,
                sent_at=sent_at,
            )

    report = await _collect(ours)

    assert report.notifications == {"sent": 2, "failed": 1}
    assert "digest.warning.notifications_failed" in report.warnings


# ---------------------------------------------------------------------------
# §4. Navbat — «hozir» kesimi
# ---------------------------------------------------------------------------


async def _outbox_pending() -> int:
    """Yopilmagan qatorlarning bugungi soni — testning boshlang'ich nuqtasi."""
    async with session_scope() as session:
        return (
            await session.execute(
                text("SELECT count(*) FROM outbox WHERE processed_at IS NULL")
            )
        ).scalar_one()


async def test_outbox_pending_is_actually_queried(two_regions, clean_audit_and_outbox) -> None:
    """`outbox_pending` — yopilmagan qatorlar soni, doimiy nol emas.

    M08 (`outbox_pending = 0`) omon qolgandi: hech bir test bu maydonni
    noldan farqli holatda ko'rmagan. E13-a bloki aynan shu son bilan
    ko'rinadi — `jobs` konteyneri turib qolsa navbat o'sadi.

    🔴 **Farq o'lchanadi, mutlaq son emas** (181-run). `outbox` da
    `region_id` yo'q va so'rov butun jadvalni sanaydi, ya'ni bu
    testdan **oldin** yurgan boshqa fayllarning qatorlari ham shu
    songa qo'shiladi. Mutlaq `== 2` faqat yolg'iz yurganda to'g'ri
    edi: butun to'plamda son 32 ham, 47 ham bo'lardi — ya'ni test
    o'zi o'lchamoqchi bo'lgan narsani emas, **yurish tartibini**
    o'lchardi. Farq esa M08 ni baribir o'ldiradi: doimiy `0` da
    farq ham `0` bo'ladi.
    """
    before = await _outbox_pending()
    async with session_scope() as session:
        for topic, processed in (
            ("outage.confirmed", None),
            ("outage.resolved", None),
            ("outage.confirmed", INSIDE),
        ):
            await session.execute(
                text(
                    "INSERT INTO outbox (topic, payload, available_at, processed_at) "
                    "VALUES (:topic, '{}'::jsonb, :at, :processed)"
                ),
                {"topic": topic, "at": INSIDE, "processed": processed},
            )

    ours, _ = two_regions
    report = await _collect(ours)

    assert report.outbox_pending - before == 2


# ---------------------------------------------------------------------------
# §5. `now=` argumenti
# ---------------------------------------------------------------------------


async def _timestamps(region_id: uuid.UUID, day: date = DAY):
    async with session_scope() as session:
        return (
            await session.execute(
                text(
                    "SELECT built_at, delivered_at FROM daily_digest "
                    "WHERE region_id = :id AND digest_date = :day"
                ),
                {"id": region_id, "day": day},
            )
        ).one()


async def test_store_writes_the_timestamp_it_was_given(two_regions) -> None:
    """`store(now=…)` bazaga aynan o'sha lahzani yozadi.

    M14 argumentni tashlab, `datetime.now(timezone.utc)` ga o'tardi.
    Mavjud test `now=` ni uzatardi, lekin natijani o'qimasdi — shuning
    uchun mutant butun to'plamdan o'tib ketgan. Argument esa kerak:
    `jobs.daily_digest` bir yurishda bir necha kunni yig'adi va
    `built_at` yurishning yagona lahzasi bo'lishi kerak, aks holda bitta
    yurishning qatorlari turli sekundlarga tarqalardi.
    """
    ours, _ = two_regions
    async with session_scope() as session:
        assert (
            await digest_service.store(
                session, region_id=ours, digest=_digest("test"), now=BUILT_AT
            )
            is True
        )

    built_at, delivered_at = await _timestamps(ours)

    assert built_at == BUILT_AT
    assert delivered_at is None, "saqlangan, lekin yuborilmagan hisobot `NULL` qoladi"


async def test_mark_delivered_writes_the_timestamp_it_was_given(two_regions) -> None:
    """`mark_delivered(now=…)` ham aynan o'sha lahzani yozadi (M18)."""
    ours, _ = two_regions
    async with session_scope() as session:
        await digest_service.store(
            session, region_id=ours, digest=_digest("test"), now=BUILT_AT
        )
        await digest_service.mark_delivered(
            session, region_id=ours, day=DAY, now=DELIVERED_AT
        )

    built_at, delivered_at = await _timestamps(ours)

    assert delivered_at == DELIVERED_AT
    assert built_at == BUILT_AT, "yetkazish belgisi yig'ilish vaqtiga tegmaydi"


# ---------------------------------------------------------------------------
# §6. Mintaqa bo'yicha ajratish
# ---------------------------------------------------------------------------


async def test_mark_delivered_touches_only_its_own_region(two_regions) -> None:
    """Bitta mintaqaning yetkazilishi qo'shnisini yuborilgan deb belgilamaydi.

    M17 (`where` dan `region_id` olib tashlangan) butun to'plamda omon
    qolgandi: fikstyurada mintaqa bitta edi. Oqibati og'ir — vazifa
    keyingi yurishda qo'shni mintaqaning hisobotini «allaqachon
    yuborilgan» deb o'tkazib yuborardi va u hech kimga yetib bormasdi.
    """
    ours, other = two_regions
    async with session_scope() as session:
        await digest_service.store(
            session, region_id=ours, digest=_digest("ours"), now=BUILT_AT
        )
        await digest_service.store(
            session, region_id=other, digest=_digest("other"), now=BUILT_AT
        )
        await digest_service.mark_delivered(
            session, region_id=ours, day=DAY, now=DELIVERED_AT
        )

    assert (await _timestamps(ours))[1] == DELIVERED_AT
    assert (await _timestamps(other))[1] is None, "qo'shni mintaqa yuborilgan deb belgilandi"


async def test_mark_delivered_touches_only_its_own_day(two_regions) -> None:
    """Bir kunning yetkazilishi qo'shni kunga tegmaydi (M16 ning qulfi)."""
    ours, _ = two_regions
    tomorrow = DAY + timedelta(days=1)
    async with session_scope() as session:
        await digest_service.store(
            session, region_id=ours, digest=_digest("ours"), now=BUILT_AT
        )
        await digest_service.store(
            session, region_id=ours, digest=_digest("ours", tomorrow), now=BUILT_AT
        )
        await digest_service.mark_delivered(
            session, region_id=ours, day=DAY, now=DELIVERED_AT
        )

    assert (await _timestamps(ours, DAY))[1] == DELIVERED_AT
    assert (await _timestamps(ours, tomorrow))[1] is None


async def test_load_is_scoped_to_its_own_region(two_regions) -> None:
    """`load` qo'shni mintaqaning hisobotini qaytarmaydi.

    M19 (`where` dan `region_id` olib tashlangan) omon qolgandi. Bu
    `GET /api/v1/admin/digest` orqali ko'rinadigan nuqson: bitta
    mintaqaning moderatori boshqasining sonlarini ko'rardi.

    Ikkala mintaqada ham **bir xil kun** saqlanadi, ya'ni farq faqat
    `region_id` bo'yicha ajratiladi; `region_code` esa qaysi qator
    o'qilganini aniq ko'rsatadi.
    """
    ours, other = two_regions
    async with session_scope() as session:
        await digest_service.store(
            session, region_id=ours, digest=_digest("ours-code"), now=BUILT_AT
        )
        await digest_service.store(
            session, region_id=other, digest=_digest("other-code"), now=BUILT_AT
        )

    async with session_scope() as session:
        mine = await digest_service.load(session, region_id=ours, day=DAY)
        theirs = await digest_service.load(session, region_id=other, day=DAY)

    assert mine is not None and mine.region_code == "ours-code"
    assert theirs is not None and theirs.region_code == "other-code"


async def test_load_is_scoped_to_its_own_day(two_regions) -> None:
    """`load` qo'shni kunning hisobotini qaytarmaydi (M20 ning qulfi).

    M20 `scalar_one_or_none` ning `MultipleResultsFound` i tufayli
    o'lgandi — ya'ni qulf **tasodifiy** edi va `scalars().first()` ga
    o'tish uni jimgina yo'qotardi. Bu yerda kun ochiq tekshiriladi.
    """
    ours, _ = two_regions
    tomorrow = DAY + timedelta(days=1)
    async with session_scope() as session:
        await digest_service.store(
            session, region_id=ours, digest=_digest("day-one"), now=BUILT_AT
        )
        await digest_service.store(
            session, region_id=ours, digest=_digest("day-two", tomorrow), now=BUILT_AT
        )

    async with session_scope() as session:
        first = await digest_service.load(session, region_id=ours, day=DAY)
        second = await digest_service.load(session, region_id=ours, day=tomorrow)

    assert first is not None and first.region_code == "day-one"
    assert second is not None and second.region_code == "day-two"

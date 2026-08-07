#!/usr/bin/env python3
"""Retrospektiv qayta hisoblash (E6, `05` §9.2, `06` §12.13).

Parametrlar (`06` §9) haqiqiy ma'lumotsiz sozlanmagan. E11 da ular
o'zgaradi va savol tug'iladi: **o'sha paytda nima bo'lardi?** Bu asbob
tarixiy xabarlarni o'zgartirmasdan, ulardan yig'ilgan xulosani —
hodisalarni — qaytadan quradi.

```
xabarlar (o'zgarmaydi)
  → oynadagi hodisalar o'chiriladi
  → xabarlar (created_at, id) tartibida qaytadan `clustering.assign` ga beriladi
  → oxirida har bir hodisa `--to` paytiga qarab qayta baholanadi (autoclose)
```

Ikkita kafolat:

* **Determinizm** (`05` §9.2 regressiya qatlami). Tartib qat'iy, jitter
  allaqachon yozilgan, hisob-kitob toza funksiyalarda — shuning uchun bir
  xil kirish har safar bir xil chiqish beradi. `fingerprint` buni
  o'lchaydigan barmoq izini beradi.
* **Xavfsizlik.** Standart rejim — **quruq yurish**: hammasi haqiqatan
  hisoblanadi, lekin tranzaksiya oxirida bekor qilinadi. Yozish uchun
  `--apply` kerak. Bildirishnoma yuborilgan hodisa bor bo'lsa asbob umuman
  ishlamaydi: foydalanuvchi ko'rgan faktni tarixdan o'chirib bo'lmaydi.

Misollar:

    python -m tools.recluster --region samarkand --from 2026-08-01 --to 2026-08-08
    python -m tools.recluster --region samarkand --from 2026-08-01 --to 2026-08-08 --apply
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.clustering import repository as cluster_repo  # noqa: E402
from app.clustering import service as clustering  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.session import dispose_engine, get_sessionmaker  # noqa: E402
from app.geo import pipeline as geo  # noqa: E402
from app.notifications import queries as notify_q  # noqa: E402
from app.reports import queries as reports_q  # noqa: E402

EXIT_OK = 0
EXIT_BLOCKED = 2
EXIT_USAGE = 64


@dataclass(frozen=True)
class Result:
    """Qayta hisoblash natijasi — hisobot va regressiya sinovi uchun."""

    region_code: str
    since: datetime
    until: datetime
    reports: int
    detached: int
    deleted_outages: int
    created_outages: int
    unassigned: int
    #: `geom_exact` i `NULL` ga o'tgan xabarlar (`05` §3.2) — ular uchun
    #: qayta hisoblash jitterlangan nuqta bilan, ya'ni qo'polroq bajarildi.
    degraded_reports: int
    fingerprint: str
    applied: bool

    @property
    def degraded_ratio(self) -> float:
        return self.degraded_reports / self.reports if self.reports else 0.0

    @property
    def warning(self) -> str | None:
        """Aniqligi pasaygan davr haqida ogohlantirish.

        Jimgina o'tkazib yuborish eng xavfli variant bo'lardi: natija
        onlayn tarixdan farq qiladi va sababi hisobotda ko'rinmasdi.
        """
        if not self.degraded_reports:
            return None
        return (
            f"diqqat: {self.degraded_reports} ta xabar ({self.degraded_ratio:.0%}) "
            "faqat jitterlangan nuqta bilan hisoblandi — `geom_exact` 90 kundan "
            "keyin NULL ga o'tadi (05 §3.2). Bu davrda markaz va radius qo'polroq."
        )

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["since"] = self.since.isoformat()
        data["until"] = self.until.isoformat()
        data["degraded_ratio"] = round(self.degraded_ratio, 4)
        data["warning"] = self.warning
        return data


class ReclusterBlocked(RuntimeError):
    """Qayta hisoblash xavfsiz emas — sabab bilan to'xtatiladi."""


@asynccontextmanager
async def _scope(*, apply: bool) -> AsyncIterator[AsyncSession]:
    """Tranzaksiya: `--apply` bo'lsa commit, aks holda **har doim** rollback.

    Quruq yurish ham haqiqiy hisob-kitobni bajaradi — «nima bo'lardi»
    degan savolga taxmin bilan emas, natija bilan javob beriladi.
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


def fingerprint(rows: list[cluster_repo.OutageFingerprintRow]) -> str:
    """Natijaning barqaror barmoq izi (`05` §9.2).

    `uuid` va vaqt tamg'alari emas, **mazmun** hashlanadi: status, markaz,
    radius, ishonch, masshtab va og'irlikli ball. Ikki yurish bir xil izni
    bersa — algoritm determinik.
    """
    payload = [
        [
            r.started_at.isoformat(),
            r.status,
            f"{r.lat:.7f}",
            f"{r.lon:.7f}",
            r.radius_m,
            r.confidence,
            r.scale,
            f"{r.weighted_score:.1f}",
        ]
        for r in rows
    ]
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.blake2b(blob, digest_size=16).hexdigest()


async def recluster(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    region_code: str,
    since: datetime,
    until: datetime,
    applied: bool,
) -> Result:
    """Oynani qaytadan klasterlaydi. Chaqiruvchi tranzaksiyani boshqaradi."""
    doomed = await cluster_repo.outage_ids_started_in(
        session, region_id=region_id, since=since, until=until
    )
    notified = await notify_q.count_for_outages(session, doomed)
    if notified:
        raise ReclusterBlocked(
            f"oynadagi {notified} ta bildirishnoma hodisaga bog'langan — "
            "yuborilgan xabarnoma tarixdan o'chirilmaydi"
        )

    rows = await reports_q.reports_for_replay(
        session, region_id=region_id, since=since, until=until
    )
    detached = await reports_q.detach_window(
        session, region_id=region_id, since=since, until=until
    )
    deleted = await cluster_repo.delete_outages(session, doomed)

    created: set[uuid.UUID] = set()
    unassigned = 0
    for row in rows:
        assignment = await clustering.assign(
            session,
            clustering.ReportRef(
                id=row.id,
                user_id=row.user_id,
                kind=row.kind,
                lat=row.lat,
                lon=row.lon,
                region_id=row.region_id,
                district_id=row.district_id,
                mahalla_id=row.mahalla_id,
                created_at=row.created_at,
                source_code=row.source_code,
            ),
        )
        if assignment.outage_id is None:
            unassigned += 1
        elif assignment.created:
            created.add(assignment.outage_id)

    # Oxirgi qadam — oyna oxiridagi holat: jim qolgan hodisalar `autoclose`
    # bo'yicha yopiladi (`05` §4.4). Onlaynda buni fon vazifasi qiladi.
    for outage_id in await cluster_repo.outage_ids_started_in(
        session, region_id=region_id, since=since, until=until
    ):
        await clustering.evaluate(session, outage_id, now=until)

    await session.flush()
    rows_out = await cluster_repo.fingerprint_rows(
        session, region_id=region_id, since=since, until=until
    )
    return Result(
        region_code=region_code,
        since=since,
        until=until,
        reports=len(rows),
        detached=detached,
        deleted_outages=deleted,
        created_outages=len(created),
        unassigned=unassigned,
        degraded_reports=sum(1 for r in rows if not r.has_exact),
        fingerprint=fingerprint(rows_out),
        applied=applied,
    )


def parse_moment(value: str) -> datetime:
    """`YYYY-MM-DD` yoki to'liq ISO vaqt. Zona ko'rsatilmasa — UTC."""
    moment = datetime.fromisoformat(value)
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


async def cmd_recluster(args: argparse.Namespace) -> int:
    since, until = args.since, args.until
    if until <= since:
        print("`--to` `--from` dan katta bo'lishi kerak", file=sys.stderr)
        return EXIT_USAGE

    try:
        async with _scope(apply=args.apply) as session:
            region = await geo.find_region(session, args.region)
            if region is None:
                print(f"mintaqa topilmadi: {args.region}", file=sys.stderr)
                return EXIT_USAGE
            result = await recluster(
                session,
                region_id=region.id,
                region_code=region.code,
                since=since,
                until=until,
                applied=args.apply,
            )
    except ReclusterBlocked as exc:
        print(f"to'xtatildi: {exc}", file=sys.stderr)
        return EXIT_BLOCKED

    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    if result.warning:
        print(f"\n{result.warning}", file=sys.stderr)
    if not args.apply:
        print("\nQuruq yurish — hech narsa yozilmadi. Yozish uchun `--apply`.")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="recluster", description=__doc__)
    parser.add_argument("--region", default=settings.default_region_code, help="regions.code")
    parser.add_argument(
        "--from", dest="since", type=parse_moment, required=True, help="oyna boshi (ISO)"
    )
    parser.add_argument(
        "--to", dest="until", type=parse_moment, required=True, help="oyna oxiri (ISO, kirmaydi)"
    )
    parser.add_argument(
        "--apply", action="store_true", help="natijani yozish (standart — quruq yurish)"
    )
    parser.set_defaults(func=cmd_recluster)
    return parser


async def _main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return await args.func(args)
    finally:
        await dispose_engine()


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())

"""TZ §7 sozlamalarini `region_config` ga qo'yadi va jurnalga yozadi.

**Nima uchun asbob, migratsiya emas.** §7: «Отсутствие настройки при
запуске = ошибка запуска, а не подстановка значения из кода». Agar
migratsiya qiymatlarni jimgina to'ldirsa, sozlamaning yo'qligi hech
qachon ko'rinmasdi va §7 ning butun ma'nosi yo'qolardi. Shuning uchun
qiymat qo'yish — **ko'rinadigan qadam**: odam buyruqni yozadi, chiqishda
har bir kalitni va uning `ПРИДУМАНО` belgisini ko'radi.

Har yozuv `config_journal` ga ham tushadi (T-2, ТС-219): eski qiymat
o'chmaydi, yangi qator qo'shiladi.

```
python -m tools.seed_tz_config --region samarkand --dry-run
python -m tools.seed_tz_config --region samarkand --changed-by "N"
```

`--dry-run` hech narsa yozmaydi va farqni ko'rsatadi: qaysi kalit yangi,
qaysinisi allaqachon boshqa qiymatda. Mavjud qiymat **ustidan
yozilmaydi** — buning uchun `--overwrite` kerak, va o'shanda ham eskisi
jurnalda qoladi.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from app.core.tzconfig import origins, starting_values
from app.db.session import session_scope
from app.geo.models import ConfigJournal, Region, RegionConfig


@dataclass(frozen=True)
class Change:
    key: str
    old: Any
    new: Any
    origin: str

    @property
    def is_new(self) -> bool:
        return self.old is None

    @property
    def differs(self) -> bool:
        return self.old != self.new


async def plan(session, region_id) -> list[Change]:
    """Nima o'zgaradi. Yozmaydi."""
    rows = await session.execute(
        select(RegionConfig.key, RegionConfig.value).where(RegionConfig.region_id == region_id)
    )
    current: dict[str, Any] = {key: value for key, value in rows.all()}
    marks = origins()
    return [
        Change(key=key, old=current.get(key), new=value, origin=str(marks[key]))
        for key, value in starting_values().items()
    ]


async def apply(session, region_id, changes: list[Change], *, changed_by: str, overwrite: bool):
    """Yozadi va jurnalga qo'shadi. Yozilgan kalitlar sonini qaytaradi."""
    written = 0
    for change in changes:
        if not change.is_new and not overwrite:
            continue
        if not change.is_new and not change.differs:
            continue
        row = await session.get(RegionConfig, {"region_id": region_id, "key": change.key})
        if row is None:
            session.add(
                RegionConfig(
                    region_id=region_id,
                    key=change.key,
                    value=change.new,
                    origin=change.origin,
                )
            )
        else:
            row.value = change.new
            row.origin = change.origin
        session.add(
            ConfigJournal(
                region_id=region_id,
                key=change.key,
                value=change.new,
                origin=change.origin,
                changed_by=changed_by,
                note="TZ §7 boshlang'ich qiymati",
            )
        )
        written += 1
    return written


async def run(region_code: str, *, dry_run: bool, changed_by: str, overwrite: bool) -> int:
    async with session_scope() as session:
        region = (
            await session.execute(select(Region).where(Region.code == region_code))
        ).scalar_one_or_none()
        if region is None:
            print(f"mintaqa topilmadi: {region_code}")
            return 1

        changes = await plan(session, region.id)
        for change in changes:
            state = "yangi" if change.is_new else ("boshqa" if change.differs else "bir xil")
            print(f"  {change.key:38} {json.dumps(change.new):>10}  [{change.origin}] {state}")

        if dry_run:
            print(f"\n--dry-run: {sum(1 for c in changes if c.is_new)} yangi kalit")
            return 0

        written = await apply(
            session, region.id, changes, changed_by=changed_by, overwrite=overwrite
        )
        print(f"\nyozildi: {written} kalit ({region_code})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="TZ §7 sozlamalarini qo'yadi")
    parser.add_argument("--region", required=True, help="mintaqa kodi, masalan `samarkand`")
    parser.add_argument("--dry-run", action="store_true", help="hech narsa yozmaydi")
    parser.add_argument("--changed-by", default="seed_tz_config", help="jurnaldagi muallif")
    parser.add_argument(
        "--overwrite", action="store_true", help="mavjud qiymatni ham qayta yozadi"
    )
    args = parser.parse_args()
    return asyncio.run(
        run(
            args.region,
            dry_run=args.dry_run,
            changed_by=args.changed_by,
            overwrite=args.overwrite,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

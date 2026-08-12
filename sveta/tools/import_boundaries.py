#!/usr/bin/env python3
"""OSM → PostGIS chegara importi (`05` §5).

```
Overpass API so'rovi
  → GeoJSON
  → ST_MakeValid, ST_Multi
  → sifat tekshiruvi
  → staging jadvaliga yuklash
  → qo'lda ko'rish (vizual)
  → districts ga ko'chirish (yangi valid_from bilan)
```

Uchta buyruq — quvurdagi «qo'lda ko'rish» qadamini saqlab qolish uchun ataylab
ajratilgan:

* `survey`  — `admin_level` 4..10 ni sanaydi va nomlarni ko'rsatadi.
              **Qaysi daraja shahar tumanlari ekanini odam tanlaydi** (ADR-07).
* `stage`   — tanlangan darajani `boundary_staging` ga yuklaydi va sifat
              hisobotini chiqaradi. `districts` ga tegmaydi.
* `promote` — tekshiruvdan o'tgan partiyani `districts` ga ko'chiradi:
              eski qatorlar `valid_to` bilan yopiladi, o'chirilmaydi.

Misollar:

    python -m tools.import_boundaries survey --region samarkand
    python -m tools.import_boundaries stage --region samarkand \\
        --admin-level 8 --reference-level 6
    python -m tools.import_boundaries promote --batch <uuid>
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.admin import audit  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.session import dispose_engine, session_scope  # noqa: E402
from app.geo import osm, quality  # noqa: E402
from app.geo.models import Region  # noqa: E402

EXIT_OK = 0
EXIT_BLOCKED = 2
EXIT_USAGE = 64


# --- Overpass ----------------------------------------------------------------


class OverpassError(RuntimeError):
    """Overpass so'rovi bajarilmadi.

    `httpx.HTTPStatusError` ni to'g'ridan-to'g'ri chiqarib yuborish
    traceback beradi va nima qilish kerakligini aytmaydi. Bu asbob
    operator qo'lida ishlaydi, ya'ni xato **o'qiladigan** bo'lishi kerak.
    """


async def _overpass(query: str, url: str) -> dict[str, Any]:
    """So'rovni yuboradi. Sarlavhalar `app.geo.osm` dan (`OVERPASS_HEADERS`).

    `User-Agent` siz `overpass-api.de` **`406 Not Acceptable`** qaytaradi —
    so'rovning o'zi to'g'ri bo'lsa ham (74-run, prodda topildi).
    """
    async with httpx.AsyncClient(timeout=osm.OVERPASS_TIMEOUT_S + 30) as client:
        try:
            response = await client.post(url, data={"data": query}, headers=osm.OVERPASS_HEADERS)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            hint = ""
            if status in (406, 403, 429):
                hint = (
                    " Overpass mijozni rad etdi. Tekshiring: `User-Agent`"
                    f" ({osm.OVERPASS_USER_AGENT!r}), tezlik cheklovi (bir necha"
                    " daqiqadan keyin qayta urinib ko'ring) yoki boshqa oyna"
                    " (`--overpass-url`)."
                )
            raise OverpassError(f"Overpass {status} — {url}.{hint}") from exc
        except httpx.HTTPError as exc:
            raise OverpassError(f"Overpass ga ulanib bo'lmadi: {exc}") from exc


def _read_cache(cache: Path | None) -> dict[str, Any] | None:
    """Saqlangan javobni o'qiydi (sinxron — CLI asboblari uchun yetarli)."""
    if cache is None or not cache.exists():
        return None
    print(f"# javob fayldan o'qildi: {cache}")
    return json.loads(cache.read_text(encoding="utf-8"))


def _write_cache(cache: Path | None, payload: dict[str, Any]) -> None:
    """Javobni faylga saqlaydi (sinxron — CLI asboblari uchun yetarli)."""
    if cache is None:
        return
    cache.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"# javob saqlandi: {cache}")


async def _load_payload(query: str, url: str, cache: Path | None) -> dict[str, Any]:
    """So'rovni bajaradi yoki oldin saqlangan javobni o'qiydi.

    Overpass sekin va cheklangan — takroriy ishga tushirishda `--from-file`
    bilan bir marta olingan javobni qayta ishlatish mumkin.

    Fayl bilan ishlash alohida sinxron yordamchilarga chiqarildi: `ASYNC240`
    async funksiya ichida `pathlib` bloklovchi chaqiruvlarini taqiqlaydi.
    """
    cached = _read_cache(cache)
    if cached is not None:
        return cached
    payload = await _overpass(query, url)
    _write_cache(cache, payload)
    return payload


async def _resolve_bbox(args: argparse.Namespace) -> str:
    """Overpass so'rovi uchun bbox: `--bbox` yoki `regions` qatoridan.

    E19 gacha bbox koddagi lug'atdan olinardi (`REGION_BBOX`), ya'ni yangi
    shahar importi deploy talab qilardi. Endi u mintaqa qatorida
    (`0005` migratsiya) va u yerga `tools/region_admin.py add` yozadi —
    import zanjiri kodga tegmasdan yakunlanadi.
    """
    if args.bbox:
        return args.bbox
    async with session_scope() as session:
        region = (
            await session.execute(select(Region).where(Region.code == args.region))
        ).scalar_one_or_none()
    box = region.bbox if region is not None else None
    if box is None:
        raise SystemExit(
            f"'{args.region}' uchun bbox yo'q. "
            f"--bbox 'min_lat,min_lon,max_lat,max_lon' bering yoki mintaqani "
            f"`python -m tools.region_admin add --code {args.region} --bbox …` "
            f"bilan yarating."
        )
    return box.as_overpass()


# --- survey ------------------------------------------------------------------


async def cmd_survey(args: argparse.Namespace) -> int:
    bbox = await _resolve_bbox(args)
    query = osm.survey_query(bbox)
    print(f"# bbox: {bbox}\n{query}")
    payload = await _load_payload(query, args.overpass_url, args.cache)
    boundaries = osm.parse_boundaries(payload)

    if not boundaries:
        print("Hech narsa topilmadi. bbox yoki hudud kodini tekshiring.")
        return EXIT_BLOCKED

    summary = osm.summarize_levels(boundaries)
    print("\nadmin_level | soni | nomlar")
    print("-" * 72)
    for level in sorted(summary):
        names = summary[level]
        shown = ", ".join(names[:8]) + ("…" if len(names) > 8 else "")
        print(f"{level:>11} | {len(names):>4} | {shown}")

    # `--reference-ref` id talab qiladi, jadval esa faqat nomlarni ko'rsatadi —
    # id ni boshqa joydan qidirishga majbur qilmaslik uchun shu yerda beriladi.
    print("\nrelation id lari (`stage --reference-ref` uchun):")
    for boundary in sorted(boundaries, key=lambda b: (b.admin_level, b.display_name)):
        print(f"  {boundary.admin_level:>2}  {boundary.source_ref:>12}  {boundary.display_name}")

    print(
        "\nQaysi daraja shahar tumanlariga mos kelishini O'ZINGIZ tanlang "
        "(ADR-07) va `stage --admin-level N` bilan davom eting."
    )
    return EXIT_OK


# --- stage -------------------------------------------------------------------

_INSERT = text(
    """
    INSERT INTO boundary_staging (
      id, batch_id, region_code, admin_level, source, source_ref, license,
      name_uz, name_ru, raw_tags, geom, status
    )
    VALUES (
      gen_random_uuid(), :batch_id, :region_code, :admin_level, 'osm', :source_ref, 'ODbL',
      :name_uz, :name_ru, CAST(:raw_tags AS jsonb),
      ST_Multi(ST_CollectionExtract(
        ST_BuildArea(ST_Node(ST_GeomFromText(:wkt, 4326))), 3)),
      :status
    )
    ON CONFLICT (batch_id, source_ref) DO NOTHING
    """
)


async def _stage_boundaries(session, batch_id, region_code, boundaries, status) -> int:
    staged = 0
    for boundary in boundaries:
        wkt = osm.lines_to_wkt(boundary)
        if wkt is None:
            print(f"  ! {boundary.source_ref}: geometriya yo'q, o'tkazib yuborildi")
            continue
        await session.execute(
            _INSERT,
            {
                "batch_id": batch_id,
                "region_code": region_code,
                "admin_level": boundary.admin_level,
                "source_ref": boundary.source_ref,
                "name_uz": boundary.name_uz,
                "name_ru": boundary.name_ru,
                "raw_tags": json.dumps(boundary.tags, ensure_ascii=False),
                "wkt": wkt,
                "status": status,
            },
        )
        staged += 1
    return staged


async def _run_quality(
    session,
    batch_id: uuid.UUID,
    rows: list[dict],
    *,
    degenerate: bool = False,
) -> quality.QualityReport:
    report = quality.QualityReport()

    await session.execute(text(quality.SQL_MAKE_VALID), {"batch_id": batch_id})
    await session.execute(text(quality.SQL_MARK_VALID), {"batch_id": batch_id})

    counts = (await session.execute(text(quality.SQL_COUNT_INVALID), {"batch_id": batch_id})).one()
    report.add(quality.check_validity(total=counts.total, invalid=counts.invalid))

    unclosed = (
        await session.execute(text(quality.SQL_COUNT_UNCLOSED), {"batch_id": batch_id})
    ).scalar_one()
    report.add(quality.check_closed_rings(total=counts.total, unclosed=unclosed))

    overlap = (
        await session.execute(text(quality.SQL_OVERLAP_AREA), {"batch_id": batch_id})
    ).scalar_one()
    total_area = (
        await session.execute(text(quality.SQL_TOTAL_AREA), {"batch_id": batch_id})
    ).scalar_one()
    report.add(quality.check_overlap_ratio(float(overlap), float(total_area)))

    if degenerate:
        report.add(quality.check_coverage_ratio(0.0, None, degenerate=True))
    else:
        coverage = (
            await session.execute(text(quality.SQL_COVERED_AREA), {"batch_id": batch_id})
        ).one_or_none()
        if coverage is None:
            report.add(quality.check_coverage_ratio(0.0, None))
        else:
            report.add(
                quality.check_coverage_ratio(
                    float(coverage.covered_area), float(coverage.reference_area) or None
                )
            )

    report.add(quality.check_names(rows))
    report.add(quality.check_license(["ODbL"] * len(rows)))
    return report


async def cmd_stage(args: argparse.Namespace) -> int:
    bbox = await _resolve_bbox(args)
    batch_id = uuid.uuid4()

    query = osm.fetch_query(bbox, args.admin_level)
    print(f"# bbox: {bbox}\n{query}")
    payload = await _load_payload(query, args.overpass_url, args.cache)
    boundaries = [b for b in osm.parse_boundaries(payload) if b.admin_level == args.admin_level]
    if not boundaries:
        print(f"admin_level={args.admin_level} bo'yicha hech narsa topilmadi.")
        return EXIT_BLOCKED

    reference: list[osm.OsmBoundary] = []
    ref_cache = args.cache.with_suffix(".ref.json") if args.cache else None
    if args.reference_ref:
        # Etalon id bo'yicha: bbox hududni ajrata olmaydi (`osm.relation_query`).
        ref_payload = await _load_payload(
            osm.relation_query(args.reference_ref), args.overpass_url, ref_cache
        )
        reference = osm.parse_boundaries(ref_payload)
    elif args.reference_level:
        ref_query = osm.fetch_query(bbox, args.reference_level)
        ref_payload = await _load_payload(ref_query, args.overpass_url, ref_cache)
        reference = [
            b for b in osm.parse_boundaries(ref_payload) if b.admin_level == args.reference_level
        ]

    # Etalon staged to'plamining ichida bo'lsa, qoplash o'lchovi ma'nosiz —
    # va `boundary_staging` ning `UNIQUE (batch_id, source_ref)` i tufayli
    # etalon qatorlari `ON CONFLICT DO NOTHING` bilan **jimgina** tushib
    # qolardi (118-run defekti): natijada tekshiruv «etalon berilmagan»
    # deb bloklardi. Endi holat nomlanadi va etalon umuman yozilmaydi.
    # Shart **tenglik**, qism-to'plam emas: etalon staged larning biri bo'lishi
    # (masalan «Samarqand shahri» oltita tumandan biri) normal va o'lchov
    # o'sha holda ham haqiqiy — birlashma shaharni qoplaydimi. Ma'nosiz
    # bo'ladigan yagona holat — staged to'plami etalonning **aynan o'zi**.
    staged_refs = {b.source_ref for b in boundaries}
    reference_refs = {b.source_ref for b in reference}
    degenerate = bool(reference_refs) and reference_refs == staged_refs
    if degenerate:
        reference = []

    async with session_scope() as session:
        staged = await _stage_boundaries(
            session, batch_id, args.region, boundaries, quality.STATUS_STAGED
        )
        if reference:
            await _stage_boundaries(
                session, batch_id, args.region, reference, quality.STATUS_REFERENCE
            )
        report = await _run_quality(
            session, batch_id, [b.to_row() for b in boundaries], degenerate=degenerate
        )

    print(f"\nbatch_id: {batch_id}")
    print(f"staging ga yozildi: {staged} ta poligon")
    print("\nSifat hisoboti (05 §5.3):")
    for line in report.as_lines():
        print("  " + line)

    if report.ok:
        print(
            "\nHammasi joyida. Poligonlarni ko'z bilan tekshiring, keyin:\n"
            f"  python -m tools.import_boundaries promote --batch {batch_id} "
            f"--region {args.region}"
        )
        return EXIT_OK

    print("\nIMPORT BLOKLANDI — yuqoridagi [BLOK] qatorlarini tuzating.")
    return EXIT_BLOCKED


# --- promote -----------------------------------------------------------------


async def cmd_promote(args: argparse.Namespace) -> int:
    async with session_scope() as session:
        region = (
            await session.execute(
                text("SELECT id, code FROM regions WHERE code = :code"), {"code": args.region}
            )
        ).one_or_none()
        if region is None:
            print(f"regions da '{args.region}' yo'q. Avval hududni qo'shing.")
            return EXIT_BLOCKED

        rows = (
            await session.execute(
                text(
                    "SELECT source_ref, name_uz, name_ru FROM boundary_staging "
                    "WHERE batch_id = :batch_id AND status = 'staged'"
                ),
                {"batch_id": args.batch},
            )
        ).mappings().all()
        if not rows:
            print("Bu partiyada ko'chiriladigan qator yo'q.")
            return EXIT_BLOCKED

        names = quality.check_names([dict(r) for r in rows])
        if names.is_blocker:
            print(f"[BLOK] {names.name}: {names.detail}")
            print("Nomlarni boundary_staging da to'ldiring va qayta urinib ko'ring.")
            return EXIT_BLOCKED

        if args.dry_run:
            print(f"[dry-run] {len(rows)} ta tuman ko'chirilar edi.")
            return EXIT_OK

        await session.execute(text(quality.SQL_CLOSE_CURRENT), {"region_id": region.id})
        await session.execute(
            text(quality.SQL_PROMOTE), {"region_id": region.id, "batch_id": args.batch}
        )
        await session.execute(text(quality.SQL_MARK_PROMOTED), {"batch_id": args.batch})
        # BR-024: spravochnik ustidagi amal jurnalda qoladi. Bu quvurdagi
        # **yagona qaytarib bo'lmaydigan** qadam — eski qatorlar `valid_to`
        # bilan yopiladi, ya'ni `05` §5 versiyalash chizig'i shu yerda
        # uziladi. `before`/`after` — partiya va qatorlar soni: chegara
        # geometriyasining o'zi `districts` da tarixi bilan turadi
        # (BR-002), jurnal esa «qachon, kim, qaysi partiya» ga javob
        # beradi — aks holda yozuv butun spravochnik nusxasi bo'lardi.
        await audit.record(
            session,
            actor=audit.cli_actor(),
            action=audit.AuditAction.BOUNDARIES_PROMOTE,
            object_id=region.id,
            after={
                "batch_id": str(args.batch),
                "districts": len(rows),
                "region_code": region.code,
            },
        )

    print(f"{len(rows)} ta tuman districts ga ko'chirildi. Eski qatorlar valid_to bilan yopildi.")
    return EXIT_OK


# --- CLI ---------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="import_boundaries", description=__doc__)
    parser.add_argument(
        "--overpass-url", default=osm.OVERPASS_DEFAULT_URL, help="Overpass API manzili"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--region", default=settings.default_region_code, help="regions.code")
        p.add_argument("--bbox", default="", help="min_lat,min_lon,max_lat,max_lon")
        p.add_argument("--cache", type=Path, default=None, help="Overpass javobini saqlash fayli")

    p_survey = sub.add_parser("survey", help="admin_level 4..10 ni sanash (ADR-07)")
    common(p_survey)
    p_survey.set_defaults(func=cmd_survey)

    p_stage = sub.add_parser("stage", help="tanlangan darajani staging ga yuklash")
    common(p_stage)
    p_stage.add_argument("--admin-level", type=int, required=True)
    ref = p_stage.add_mutually_exclusive_group()
    ref.add_argument(
        "--reference-level",
        type=int,
        default=None,
        help="shahar chegarasi darajasi — qoplashni o'lchash uchun (05 §5.3)",
    )
    ref.add_argument(
        "--reference-ref",
        default="",
        help=(
            "etalon relation id ('r17544823' yoki '17544823') — bbox hududni "
            "ajrata olmaganda (05 §5.3)"
        ),
    )
    p_stage.set_defaults(func=cmd_stage)

    p_promote = sub.add_parser("promote", help="partiyani districts ga ko'chirish")
    p_promote.add_argument("--region", default=settings.default_region_code)
    p_promote.add_argument("--batch", type=uuid.UUID, required=True)
    p_promote.add_argument("--dry-run", action="store_true")
    p_promote.set_defaults(func=cmd_promote)

    return parser


async def _main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return await args.func(args)
    except OverpassError as exc:
        print(f"[BLOK] {exc}")
        return EXIT_BLOCKED
    finally:
        await dispose_engine()


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())

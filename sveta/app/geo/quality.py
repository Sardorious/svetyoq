"""Chegara importining sifat mezonlari (`05` §5.3).

| Tekshiruv | Shart |
|---|---|
| Geometriya haqiqiyligi | `ST_IsValid` — yo'q bo'lsa `ST_MakeValid`, keyin qayta tekshirish |
| Yopiqlik | Har bir poligon yopiq halqa |
| Ustma-ustlik | Qo'shni tumanlar kesishmasi < umumiy maydonning 1% |
| Bo'shliq | Tumanlar birlashmasi shahar chegarasining ≥98% ini qoplaydi |
| Nom to'liqligi | `name:uz` va `name:ru` — bo'lmasa qo'lda to'ldiriladi |
| Litsenziya | ODbL atributsiyasi saytda ko'rsatiladi |

**Bo'shliq tekshiruvi eng muhimi.** Qoplanmagan joydan kelgan xabar
`district_id = NULL` bo'ladi va statistikadan sezilmasdan tushib qoladi.

Geometriya tekshiruvlari PostGIS da bajariladi (`checks_sql`), nom va
litsenziya tekshiruvlari — toza funksiyalar (`check_names`, `check_license`),
shuning uchun ular bazasiz testlanadi.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

#: Qo'shni tumanlar kesishmasining maksimal ulushi (`05` §5.3).
MAX_OVERLAP_RATIO = 0.01

#: Tumanlar birlashmasi qoplashi kerak bo'lgan minimal ulush (`05` §5.3).
MIN_COVERAGE_RATIO = 0.98

#: Ruxsat etilgan litsenziyalar. OSM — ODbL, atributsiya majburiy.
ALLOWED_LICENSES: tuple[str, ...] = ("ODbL",)


@dataclass
class CheckResult:
    """Bitta tekshiruv natijasi."""

    name: str
    passed: bool
    blocking: bool
    detail: str = ""

    @property
    def is_blocker(self) -> bool:
        return self.blocking and not self.passed


@dataclass
class QualityReport:
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, check: CheckResult) -> None:
        self.checks.append(check)

    @property
    def blockers(self) -> list[CheckResult]:
        return [c for c in self.checks if c.is_blocker]

    @property
    def ok(self) -> bool:
        return not self.blockers

    def as_lines(self) -> list[str]:
        out = []
        for c in self.checks:
            mark = "OK  " if c.passed else ("BLOK" if c.blocking else "OGOH")
            out.append(f"[{mark}] {c.name}: {c.detail}")
        return out


def check_names(rows: Iterable[dict]) -> CheckResult:
    """`name:uz` va `name:ru` to'liqligi.

    Bo'sh nom — bloklovchi: nomsiz tuman bot javobida «None tumanida» bo'lib
    chiqadi, bu i18n qoidasini ham buzadi.
    """
    missing: list[str] = []
    for row in rows:
        ref = str(row.get("source_ref") or row.get("id") or "?")
        if not (row.get("name_uz") or "").strip():
            missing.append(f"{ref}:name_uz")
        if not (row.get("name_ru") or "").strip():
            missing.append(f"{ref}:name_ru")
    if missing:
        shown = ", ".join(missing[:10]) + ("…" if len(missing) > 10 else "")
        detail = f"{len(missing)} ta yetishmaydi: {shown}"
    else:
        detail = "hammasi to'liq"
    return CheckResult(name="Nom to'liqligi", passed=not missing, blocking=True, detail=detail)


def check_license(licenses: Sequence[str]) -> CheckResult:
    unknown = sorted({lic for lic in licenses if lic not in ALLOWED_LICENSES})
    return CheckResult(
        name="Litsenziya",
        passed=not unknown,
        blocking=True,
        detail="ODbL" if not unknown else f"noma'lum: {', '.join(unknown)}",
    )


def check_overlap_ratio(overlap_area: float, total_area: float) -> CheckResult:
    ratio = (overlap_area / total_area) if total_area else 0.0
    return CheckResult(
        name="Ustma-ustlik",
        passed=ratio < MAX_OVERLAP_RATIO,
        blocking=True,
        detail=f"{ratio:.4%} (chegara {MAX_OVERLAP_RATIO:.0%})",
    )


def check_coverage_ratio(covered_area: float, reference_area: float | None) -> CheckResult:
    if not reference_area:
        return CheckResult(
            name="Bo'shliq (qoplash)",
            passed=False,
            blocking=True,
            detail="shahar chegarasi berilmagan — tekshirib bo'lmadi",
        )
    ratio = covered_area / reference_area
    return CheckResult(
        name="Bo'shliq (qoplash)",
        passed=ratio >= MIN_COVERAGE_RATIO,
        blocking=True,
        detail=f"{ratio:.2%} (kerak ≥{MIN_COVERAGE_RATIO:.0%})",
    )


def check_validity(total: int, invalid: int) -> CheckResult:
    return CheckResult(
        name="Geometriya haqiqiyligi",
        passed=invalid == 0,
        blocking=True,
        detail=f"{total - invalid}/{total} haqiqiy"
        + ("" if invalid == 0 else f", {invalid} ta ST_MakeValid dan keyin ham yaroqsiz"),
    )


def check_closed_rings(total: int, unclosed: int) -> CheckResult:
    return CheckResult(
        name="Yopiqlik",
        passed=unclosed == 0,
        blocking=True,
        detail=f"{total - unclosed}/{total} yopiq halqa",
    )


# --- PostGIS so'rovlari (staging ustida) -------------------------------------

#: `boundary_staging.status` qiymatlari.
#: `reference` — shahar chegarasi (qoplashni o'lchash uchun), u `districts` ga
#: hech qachon ko'chirilmaydi.
STATUS_STAGED = "staged"
STATUS_REFERENCE = "reference"
STATUS_PROMOTED = "promoted"

#: Yaroqsiz geometriyalarni tuzatish. `ST_MakeValid` poligonni kolleksiyaga
#: aylantirishi mumkin — `ST_CollectionExtract(..., 3)` faqat poligonlarni oladi.
SQL_MAKE_VALID = """
UPDATE boundary_staging
   SET geom = ST_Multi(ST_CollectionExtract(ST_MakeValid(geom), 3))
 WHERE batch_id = :batch_id AND NOT ST_IsValid(geom)
"""

SQL_MARK_VALID = """
UPDATE boundary_staging
   SET is_valid_geom = ST_IsValid(geom),
       area_m2 = ST_Area(geom::geography)::bigint
 WHERE batch_id = :batch_id
"""

SQL_COUNT_INVALID = """
SELECT count(*) FILTER (WHERE NOT is_valid_geom) AS invalid, count(*) AS total
  FROM boundary_staging
 WHERE batch_id = :batch_id AND status = 'staged'
"""

SQL_COUNT_UNCLOSED = """
SELECT count(*) AS unclosed
  FROM boundary_staging
 WHERE batch_id = :batch_id AND status = 'staged'
   AND NOT ST_IsClosed(ST_ExteriorRing(ST_GeometryN(ST_Multi(geom), 1)))
"""

SQL_OVERLAP_AREA = """
SELECT COALESCE(SUM(ST_Area(ST_Intersection(a.geom, b.geom)::geography)), 0) AS overlap_area
  FROM boundary_staging a
  JOIN boundary_staging b
    ON a.batch_id = b.batch_id AND a.id < b.id AND ST_Intersects(a.geom, b.geom)
 WHERE a.batch_id = :batch_id AND a.status = 'staged' AND b.status = 'staged'
"""

SQL_TOTAL_AREA = """
SELECT COALESCE(SUM(ST_Area(geom::geography)), 0) AS total_area
  FROM boundary_staging
 WHERE batch_id = :batch_id AND status = 'staged'
"""

#: Qoplash: tumanlar birlashmasining shahar chegarasi bilan kesishmasi.
SQL_COVERED_AREA = """
WITH districts_union AS (
  SELECT ST_Union(geom) AS g FROM boundary_staging
   WHERE batch_id = :batch_id AND status = 'staged'
), reference AS (
  SELECT ST_Union(geom) AS g FROM boundary_staging
   WHERE batch_id = :batch_id AND status = 'reference'
)
SELECT
  COALESCE(ST_Area(ST_Intersection(d.g, r.g)::geography), 0) AS covered_area,
  COALESCE(ST_Area(r.g::geography), 0) AS reference_area
FROM districts_union d, reference r
"""

#: Staging dan `districts` ga ko'chirish. Eski qatorlar `valid_to` bilan
#: yopiladi — o'chirilmaydi va tahrirlanmaydi (`05` §2.1).
SQL_CLOSE_CURRENT = """
UPDATE districts
   SET valid_to = now()
 WHERE region_id = :region_id AND valid_to IS NULL
"""

SQL_PROMOTE = """
INSERT INTO districts (
  id, region_id, code, name_uz, name_ru, geom,
  valid_from, valid_to, source, source_ref, license, imported_at
)
SELECT gen_random_uuid(), :region_id, s.source_ref, s.name_uz, s.name_ru, s.geom,
       now(), NULL, s.source, s.source_ref, s.license, now()
  FROM boundary_staging s
 WHERE s.batch_id = :batch_id AND s.status = 'staged'
"""

SQL_MARK_PROMOTED = """
UPDATE boundary_staging
   SET status = 'promoted'
 WHERE batch_id = :batch_id AND status = 'staged'
"""

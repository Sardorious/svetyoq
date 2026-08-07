"""Onlayn klasterlash: xabarni hodisaga biriktirish va qayta baholash.

```python
def assign(report):
    cand = <ochiq hodisalar orasidan eng yaqini, eps va time_window ichida>
    if cand:
        attach(report, cand.id)
        recompute_centroid_and_radius(cand.id)   # inkremental
    else:
        o = create_outage(report, status='pending')
        attach(report, o.id)
    evaluate_status(report.outage_id)
```

Geometriya va biriktirish — `05` §4.2. Tasdiqlash sharti, `confidence` va
masshtab — `06` (u `05` §4.2–§4.3 dagi qat'iy `min_reporters = 3` ni
almashtiradi). `outages.independent_reporters` baribir to'ldiriladi: u endi
qaror mezoni emas, lekin audit va E11 sozlashi uchun qiymatli.

Modul chegarasi: bu yerda `outages` bilan ishlanadi; `reports`/`users` ga
`app.reports.queries`, `territory_stats`/`region_config` ga `app.geo.queries`
orqali murojaat qilinadi (`05` §1).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import repository as repo
from app.clustering.confirmation import ConfirmationResult, Evidence
from app.clustering.confirmation import evaluate as evaluate_confirmation
from app.clustering.geometry import Point, centroid_step, clamp_radius, grow_radius
from app.clustering.independence import ReporterPoint, count_independent
from app.clustering.models import Outage
from app.clustering.params import Params
from app.clustering.params import from_mapping as params_from_mapping
from app.clustering.scale import Scale, TerritoryFacts, apply_deescalation, estimate_households
from app.clustering.scale import decide as decide_scale
from app.clustering.status import (
    OutageStatus,
    StatusDecision,
    StatusInput,
    assert_transition,
    evaluate_status,
    is_open,
)
from app.core.config import settings
from app.core.errors import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.geo import queries as geo_q
from app.reports import queries as reports_q
from app.reports.sources import DEFAULT_SOURCE_CODE, is_authoritative

log = get_logger(__name__)

KIND_OUTAGE = "outage"
KIND_RESTORED = "restored"

LAYER_CROWD = "crowd"
LAYER_OFFICIAL = "official"

#: `06` §2.2 — rasmiy e'lon kraudsorsing bali bilan «ovoz berishga» qo'yilmaydi.
#: Interfeysda u to'liq ishonch bilan ko'rsatiladi.
AUTHORITATIVE_CONFIDENCE = 100


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ReportRef:
    """Klasterlashga kerak bo'lgan xabar atributlari.

    ORM obyekti emas, neytral tuzilma — shunda `app.reports` modeli bu
    modulga sizib kirmaydi.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    kind: str
    lat: float
    lon: float
    region_id: uuid.UUID
    district_id: uuid.UUID | None = None
    mahalla_id: uuid.UUID | None = None
    created_at: datetime | None = None
    source_code: str = DEFAULT_SOURCE_CODE

    @property
    def point(self) -> Point:
        return self.lat, self.lon

    @property
    def at(self) -> datetime:
        return self.created_at or _utcnow()

    @property
    def layer(self) -> str:
        """`06` §3: jamoaviy va rasmiy qatlamlar aralashtirilmaydi."""
        return LAYER_OFFICIAL if is_authoritative(self.source_code) else LAYER_CROWD


@dataclass(frozen=True)
class Assignment:
    """`assign` natijasi."""

    outage_id: uuid.UUID | None
    created: bool
    status: str | None
    reason: str

    @property
    def attached(self) -> bool:
        return self.outage_id is not None


async def assign(session: AsyncSession, report: ReportRef) -> Assignment:
    """Xabarni mavjud hodisaga biriktiradi yoki yangisini yaratadi."""
    now = report.at
    candidate = await repo.find_candidate(
        session,
        region_id=report.region_id,
        lat=report.lat,
        lon=report.lon,
        eps_m=settings.cluster_eps_m,
        time_window_min=settings.cluster_time_window_min,
        now=now,
        layer=report.layer,
    )

    if candidate is None:
        if report.kind == KIND_RESTORED:
            # "Svet keldi" xabari yangi uzilish yaratmaydi — yopadigan narsa
            # yo'q bo'lsa, u shunchaki biriktirilmagan qoladi (`05` §4.5).
            log.info("cluster.restored_without_outage", extra={"report_id": str(report.id)})
            return Assignment(
                outage_id=None, created=False, status=None, reason="no_open_outage"
            )
        outage = await repo.create_outage(
            session,
            region_id=report.region_id,
            district_id=report.district_id,
            mahalla_id=report.mahalla_id,
            lat=report.lat,
            lon=report.lon,
            started_at=now,
            layer=report.layer,
        )
        await reports_q.attach_to_outage(session, report.id, outage.id)
        decision = await evaluate(session, outage.id, now=now)
        return Assignment(
            outage_id=outage.id,
            created=True,
            status=str(decision.target or OutageStatus.PENDING),
            reason="created",
        )

    await _attach(session, candidate, report, now=now)
    decision = await evaluate(session, candidate.id, now=now)
    return Assignment(
        outage_id=candidate.id,
        created=False,
        status=str(decision.target or candidate.status),
        reason="attached",
    )


async def _attach(
    session: AsyncSession, candidate: repo.Candidate, report: ReportRef, *, now: datetime
) -> None:
    """Biriktirish + inkremental markaz/radius (`05` §4.2)."""
    values: dict[str, object] = {"last_report_at": now, "updated_at": now}

    if report.kind == KIND_OUTAGE:
        # Nuqta qo'shilishidan OLDINGI son — markaz o'rta arifmetik bo'lishi
        # uchun aynan shu og'irlik kerak.
        attached = await reports_q.count_attached(session, candidate.id, kind=KIND_OUTAGE)
        new_centroid = centroid_step(candidate.centroid, attached, report.point)
        radius = grow_radius(
            old_centroid=candidate.centroid,
            old_radius_m=float(candidate.radius_m),
            new_centroid=new_centroid,
            point=report.point,
        )
        radius_m, exceeded = clamp_radius(radius, settings.cluster_max_radius_m)
        if exceeded:
            # `05` §4.2: max_radius dan kattasi — moderatorga (E8).
            log.warning(
                "cluster.max_radius_exceeded",
                extra={"outage_id": str(candidate.id), "radius_m": int(radius)},
            )
        values["centroid"] = repo.geog_point(*new_centroid)
        values["radius_m"] = radius_m

    await session.execute(update(Outage).where(Outage.id == candidate.id).values(**values))
    await reports_q.attach_to_outage(session, report.id, candidate.id)


async def _independent(
    session: AsyncSession, outage_id: uuid.UUID, *, kind: str, now: datetime
) -> int:
    """`05` §4.3 — ikki bosqichli: SQL filtri + fazoviy siyraklashtirish."""
    rows = await reports_q.eligible_reporter_points(
        session,
        outage_id,
        kind=kind,
        min_trust_score=settings.reporter_min_trust_score,
        account_created_before=now - timedelta(minutes=settings.reporter_min_account_age_min),
    )
    points = [ReporterPoint(user_id=u, lat=lat, lon=lon) for u, lat, lon in rows]
    return count_independent(points, min_distance_m=settings.reporter_min_distance_m)


async def _load_params(session: AsyncSession, region_id: uuid.UUID) -> Params:
    """`06` §9 — parametrlar mintaqa kesimida bazadan."""
    return params_from_mapping(await geo_q.load_region_config(session, region_id))


async def _territory(
    session: AsyncSession, territory_id: uuid.UUID | None, *, avg_household_size: float
) -> TerritoryFacts | None:
    """`territory_stats` qatorini masshtab modulining tiliga o'giradi (`06` §3).

    `households` bo'sh bo'lsa u aholidan baholanadi (`06` §3.1). Qator umuman
    yo'q bo'lsa `None` qaytadi va bu `06` §5.4 bo'yicha masshtabni `local` ga
    bosadi.
    """
    row = await geo_q.load_territory_stats(session, territory_id)
    if row is None:
        return None
    households = row.households
    if households is None:
        households = estimate_households(
            row.population, avg_household_size=avg_household_size
        )
    return TerritoryFacts(
        households=households,
        populated_cells=row.populated_cells,
        active_users_30d=row.active_users_30d,
        data_quality=row.data_quality,
    )


async def _confirmation(
    session: AsyncSession,
    state: repo.EvaluationState,
    *,
    params: Params,
    now: datetime,
) -> ConfirmationResult:
    """`06` §2.1, §4, §6 — og'irlikli ball, chegara va `confidence`."""
    rows = await reports_q.eligible_evidence(
        session,
        state.id,
        kind=KIND_OUTAGE,
        min_trust_score=settings.reporter_min_trust_score,
        account_created_before=now - timedelta(minutes=settings.reporter_min_account_age_min),
    )
    # `06` §4.1 — denominator hodisa izi, hudud emas.
    a_local = await reports_q.active_users_near(
        session,
        lat=state.lat,
        lon=state.lon,
        radius_m=state.radius_m + settings.cluster_eps_m,
        since=now - timedelta(days=settings.coverage_window_days),
    )
    evidence = [
        Evidence(
            user_id=r.user_id,
            lat=r.lat,
            lon=r.lon,
            h3_r9=r.h3_r9,
            weight=r.weight,
            created_at=r.created_at,
            mahalla_id=r.mahalla_id,
        )
        for r in rows
    ]
    return evaluate_confirmation(
        evidence,
        a_local=a_local,
        now=now,
        params=params.confirm,
        spread_min_distance_m=params.spread_min_distance_m,
    )


async def _scale(
    session: AsyncSession,
    state: repo.EvaluationState,
    result: ConfirmationResult,
    *,
    params: Params,
) -> tuple[Scale, bool]:
    """`06` §5 — narvon, qamrov to'sig'i va deeskalatsiya cheklovi."""
    mahalla = await _territory(
        session, state.mahalla_id, avg_household_size=params.avg_household_size
    )
    district = await _territory(
        session, state.district_id, avg_household_size=params.avg_household_size
    )
    decision = decide_scale(
        w=result.weighted_score,
        cells_with_reports=result.cells_with_reports,
        mahallas_affected=result.mahallas_affected,
        mahalla=mahalla,
        district=district,
        scale_params=params.scale,
        guard_params=params.guard,
    )
    final = apply_deescalation(
        current=Scale(state.scale), proposed=decision.scale, status=state.status
    )
    return final, decision.capped


async def evaluate(
    session: AsyncSession, outage_id: uuid.UUID, *, now: datetime | None = None
) -> StatusDecision:
    """Hodisani qayta baholaydi va statusni yangilaydi (`05` §4.4 + `06` §8).

    Idempotent: bir xil holatda takroriy chaqiruv hech narsani o'zgartirmaydi
    — `05` §8 fon vazifalari uchun majburiy shart.
    """
    moment = now or _utcnow()
    state = await repo.load_evaluation_state(session, outage_id)
    if state is None or not is_open(state.status):
        return StatusDecision(target=None, reason="not_open")

    independent = await _independent(session, outage_id, kind=KIND_OUTAGE, now=moment)
    restored = await _independent(session, outage_id, kind=KIND_RESTORED, now=moment)

    params = await _load_params(session, state.region_id)
    result = await _confirmation(session, state, params=params, now=moment)
    final_scale, capped = await _scale(session, state, result, params=params)

    # `06` §2.2 — rasmiy manba `W` dan qat'i nazar darhol tasdiqlaydi.
    authoritative = state.layer == LAYER_OFFICIAL
    confirm_ready = True if authoritative else result.confirmed
    confidence = AUTHORITATIVE_CONFIDENCE if authoritative else result.confidence

    decision = evaluate_status(
        StatusInput(
            status=state.status,
            independent_reporters=independent,
            restored_reporters=restored,
            last_report_at=state.last_report_at,
            now=moment,
            confirm_ready=confirm_ready,
            confidence=confidence,
        ),
        min_reporters=settings.cluster_min_reporters,
        autoclose_after_min=settings.cluster_autoclose_after_min,
    )

    values: dict[str, object] = {
        "independent_reporters": independent,
        "weighted_score": result.weighted_score,
        "distinct_users": result.distinct_users,
        "required_score": result.required_score,
        "cells_with_reports": result.cells_with_reports,
        "confidence": confidence,
        "scale": str(final_scale),
        "scale_capped": capped,
        "updated_at": moment,
    }
    if decision.target is not None:
        target = assert_transition(state.status, str(decision.target))
        values["status"] = str(target)
        if target is OutageStatus.CONFIRMED:
            values["confirmed_at"] = moment
        elif target is OutageStatus.RESOLVED:
            values["resolved_at"] = moment
        log.info(
            "cluster.status_changed",
            extra={
                "outage_id": str(outage_id),
                "from": state.status,
                "to": str(target),
                "reason": decision.reason,
                "weighted_score": result.weighted_score,
                "required_score": result.required_score,
                "distinct_users": result.distinct_users,
                "scale": str(final_scale),
            },
        )

    await session.execute(update(Outage).where(Outage.id == outage_id).values(**values))
    return decision


#: Moderator qo'li bilan qo'yiladigan statuslar (`05` §4.4 diagrammasi).
#: `confirmed`/`resolved` bu ro'yxatda **yo'q**: ular dalildan kelib chiqadi
#: (`evaluate`), qo'lda qo'yilishi tasdiqlash logikasini chetlab o'tardi.
MODERATOR_TARGETS: frozenset[OutageStatus] = frozenset(
    {OutageStatus.REJECTED, OutageStatus.MERGED}
)


class NotModeratableError(ValidationError):
    """Moderator qo'ya olmaydigan status (`05` §4.4)."""

    code = "not_moderatable"
    message_key = "error.not_moderatable"


class MergeTargetError(ValidationError):
    """`merged_into` yaroqsiz."""

    code = "merge_target_invalid"
    message_key = "error.merge_target_invalid"


@dataclass(frozen=True)
class ModerationChange:
    """Auditga tushadigan o'zgarish kesimi (`05` §2.5)."""

    outage_id: uuid.UUID
    before: dict[str, object]
    after: dict[str, object]


async def moderate(
    session: AsyncSession,
    outage_id: uuid.UUID,
    *,
    target: OutageStatus | str,
    merged_into: uuid.UUID | None = None,
    now: datetime | None = None,
) -> ModerationChange:
    """Moderator qarorini qo'llaydi (E8, `05` §4.4).

    Modul chegarasi: `outages` ustidagi yozuv shu yerda qoladi;
    `app.admin` faqat chaqiradi va natijani auditga yozadi (`05` §1).

    Qarorlar:

    * **Faqat `rejected` va `merged`.** Qolgan o'tishlar dalilga bog'liq
      (`evaluate`), qo'lda qo'yilishi `06` ni chetlab o'tardi.
    * **Xabarlar ko'chirilmaydi.** `merged` da `reports.outage_id`
      tegilmaydi: xabar — birlamchi ma'lumot, uni ko'chirish maqsad
      hodisaning geometriyasi va `W` sini qayta hisoblashni talab qilardi,
      buni esa `05` ham, `06` ham ta'riflamaydi. «Ochiq savollar» ga yozildi.
    * **Zanjir yasalmaydi:** `merged` hodisaga birlashtirib bo'lmaydi, aks
      holda `merged_into` bo'yicha yurish tsiklga tushishi mumkin edi.
    """
    moment = now or _utcnow()
    try:
        wanted = OutageStatus(str(target))
    except ValueError as exc:
        raise NotModeratableError(target=str(target)) from exc
    if wanted not in MODERATOR_TARGETS:
        raise NotModeratableError(target=str(wanted))

    row = await repo.read_row(session, outage_id)
    if row is None:
        raise NotFoundError(outage_id=str(outage_id))

    assert_transition(row.status, str(wanted))

    values: dict[str, object] = {"status": str(wanted), "updated_at": moment}
    if wanted is OutageStatus.MERGED:
        values["merged_into"] = await _merge_target(session, row, merged_into)
    elif merged_into is not None:
        raise MergeTargetError(reason="not_applicable")

    await session.execute(update(Outage).where(Outage.id == outage_id).values(**values))
    log.info(
        "cluster.moderated",
        extra={
            "outage_id": str(outage_id),
            "from": row.status,
            "to": str(wanted),
            "merged_into": str(merged_into) if merged_into else None,
        },
    )
    return ModerationChange(
        outage_id=outage_id,
        before={"status": row.status, "merged_into": row.merged_into},
        after={"status": str(wanted), "merged_into": values.get("merged_into")},
    )


async def _merge_target(
    session: AsyncSession, row: repo.OutageRow, merged_into: uuid.UUID | None
) -> uuid.UUID:
    if merged_into is None:
        raise MergeTargetError(reason="missing")
    if merged_into == row.id:
        raise MergeTargetError(reason="self")
    target_row = await repo.read_row(session, merged_into)
    if target_row is None:
        raise MergeTargetError(reason="not_found")
    if target_row.region_id != row.region_id:
        raise MergeTargetError(reason="other_region")
    if target_row.status == str(OutageStatus.MERGED):
        raise MergeTargetError(reason="already_merged")
    return merged_into


async def evaluate_open(session: AsyncSession, *, now: datetime | None = None) -> int:
    """Barcha ochiq hodisalarni qayta baholaydi. `05` §8 `evaluate_outages`."""
    moment = now or _utcnow()
    ids = await repo.open_outage_ids(session)
    changed = 0
    for outage_id in ids:
        decision = await evaluate(session, outage_id, now=moment)
        if decision.changed:
            changed += 1
    return changed

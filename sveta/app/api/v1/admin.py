"""Admin-panel endpointlari (E8).

`05` §7.2 ommaviy endpointlarni sanaydi; admin ular ro'yxatida yo'q, lekin
§1 `api/` ni «public + admin» deb belgilaydi va §2.5 audit jadvalini
beradi. Shuning uchun bu yerdagi yo'llar `/admin/...` prefiksi ostida.

**Maxfiylik chegarasi.** `geom_exact` hech qanday javobda chiqmaydi
(`05` §7.3) — moderator ham ko'rmaydi. `tg_id` ham chiqmaydi. `user_id`
esa chiqadi: usiz bloklash amalini bajarib bo'lmaydi, va §7.3 ro'yxati
**ommaviy** API haqida (ochiq xaritada foydalanuvchini deanonimlashtirish
riski). Admin API tokensiz umuman javob bermaydi.

Javoblar matn emas, **kod va raqam** qaytaradi (`status`, `scale`, ...);
tarjima interfeys tomonida bo'ladi — shuning uchun bu yerda qattiq
kodlangan foydalanuvchi matni yo'q (`04` §6).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.admin import audit, digest_service, service
from app.admin import digest as digest_mod
from app.admin.roles import Permission
from app.api.deps import AdminActor, ClientLang, DbSession
from app.api.openapi import NOT_FOUND
from app.clustering import repository as outages_repo
from app.clustering.status import OPEN_STATUSES
from app.core import i18n
from app.core.config import settings
from app.core.errors import NotFoundError, ValidationError
from app.geo import pipeline as geo
from app.release import collector as gate_collector
from app.release import gates as gates_mod
from app.release import measures as measures_mod
from app.reports import moderation as users_mod

router = APIRouter(prefix="/admin", tags=["admin"])

_OPEN = tuple(sorted(str(s) for s in OPEN_STATUSES))


class OutageOut(BaseModel):
    id: uuid.UUID
    status: str
    layer: str
    scale: str
    lat: float
    lon: float
    radius_m: int
    confidence: int
    weighted_score: float
    distinct_users: int
    independent_reporters: int
    region_id: uuid.UUID
    district_id: uuid.UUID | None
    mahalla_id: uuid.UUID | None
    merged_into: uuid.UUID | None
    started_at: datetime
    last_report_at: datetime
    #: `05` §4.2 — radius `max_radius` ga yetgan hodisa moderator ko'rigini
    #: talab qiladi. Bayroq javobda hisoblanadi, bazada saqlanmaydi.
    needs_review: bool


def _outage_out(row: outages_repo.OutageRow) -> OutageOut:
    return OutageOut(
        id=row.id,
        status=row.status,
        layer=row.layer,
        scale=row.scale,
        lat=row.lat,
        lon=row.lon,
        radius_m=row.radius_m,
        confidence=row.confidence,
        weighted_score=row.weighted_score,
        distinct_users=row.distinct_users,
        independent_reporters=row.independent_reporters,
        region_id=row.region_id,
        district_id=row.district_id,
        mahalla_id=row.mahalla_id,
        merged_into=row.merged_into,
        started_at=row.started_at,
        last_report_at=row.last_report_at,
        needs_review=row.radius_m >= settings.cluster_max_radius_m,
    )


class UserOut(BaseModel):
    """`tg_id` ataylab yo'q (`05` §7.3)."""

    id: uuid.UUID
    language: str
    region_id: uuid.UUID | None
    trust_score: int
    is_blocked: bool
    created_at: datetime
    report_count: int


class AuditOut(BaseModel):
    id: int
    actor_id: uuid.UUID | None
    actor_role: str
    action: str
    object_id: uuid.UUID | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    created_at: datetime


class ChangeOut(BaseModel):
    """Amal natijasi — `before`/`after`, xuddi auditdagidek."""

    object_id: uuid.UUID
    before: dict[str, Any]
    after: dict[str, Any]


class RejectIn(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class MergeIn(BaseModel):
    merged_into: uuid.UUID
    reason: str | None = Field(default=None, max_length=500)


class BlockIn(BaseModel):
    blocked: bool
    reason: str | None = Field(default=None, max_length=500)


class TrustIn(BaseModel):
    score: int = Field(ge=users_mod.TRUST_MIN, le=users_mod.TRUST_MAX)
    reason: str | None = Field(default=None, max_length=500)


@router.get("/outages", response_model=list[OutageOut])
async def list_outages(
    actor: AdminActor,
    session: DbSession,
    status: Annotated[list[str] | None, Query()] = None,
    region: str | None = None,
    needs_review: bool = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[OutageOut]:
    """Moderatsiya navbati.

    Standart filtr — ochiq hodisalar (`pending`, `confirmed`): yopilgan
    hodisa ustidan qaror qabul qilinmaydi (`05` §4.4 yakuniy statuslari).
    `needs_review=true` esa `05` §4.2 dagi «`max_radius` dan kattasi
    moderatorga» qoidasini qo'llaydi.
    """
    actor.require(Permission.OUTAGE_READ)
    region_id = None
    if region is not None:
        region_id = (await geo.require_region(session, region)).id
    rows = await outages_repo.list_rows(
        session,
        statuses=tuple(status) if status else _OPEN,
        region_id=region_id,
        min_radius_m=settings.cluster_max_radius_m if needs_review else None,
        limit=limit,
        offset=offset,
    )
    return [_outage_out(row) for row in rows]


@router.get(
    "/outages/{outage_id}",
    response_model=OutageOut,
    summary="Bitta hodisaning moderator ko'rinishi",
    responses={404: NOT_FOUND},
)
# Nom `admin_` bilan boshlanadi: `operationId` funksiya nomidan yasaladi
# va ommaviy `get_outage` bilan to'qnashardi (generator jimgina buzilardi).
async def admin_get_outage(
    actor: AdminActor, session: DbSession, outage_id: uuid.UUID
) -> OutageOut:
    actor.require(Permission.OUTAGE_READ)
    row = await outages_repo.read_row(session, outage_id)
    if row is None:
        raise NotFoundError(outage_id=str(outage_id))
    return _outage_out(row)


@router.post("/outages/{outage_id}/reject", response_model=ChangeOut)
async def reject_outage(
    actor: AdminActor, session: DbSession, outage_id: uuid.UUID, body: RejectIn
) -> ChangeOut:
    change = await service.reject_outage(
        session, actor=actor, outage_id=outage_id, reason=body.reason
    )
    await session.commit()
    return ChangeOut(object_id=outage_id, before=_plain(change.before), after=_plain(change.after))


@router.post("/outages/{outage_id}/merge", response_model=ChangeOut)
async def merge_outage(
    actor: AdminActor, session: DbSession, outage_id: uuid.UUID, body: MergeIn
) -> ChangeOut:
    change = await service.merge_outage(
        session,
        actor=actor,
        outage_id=outage_id,
        merged_into=body.merged_into,
        reason=body.reason,
    )
    await session.commit()
    return ChangeOut(object_id=outage_id, before=_plain(change.before), after=_plain(change.after))


@router.get("/users/{user_id}", response_model=UserOut, responses={404: NOT_FOUND})
async def get_user(actor: AdminActor, session: DbSession, user_id: uuid.UUID) -> UserOut:
    # Foydalanuvchi kartasi bloklash qarori uchun ochiladi, shuning uchun
    # ruxsat ham o'shanikidan olinadi — `viewer` uni ko'rmaydi.
    actor.require(Permission.USER_BLOCK)
    row = await users_mod.read_user(session, user_id)
    if row is None:
        raise NotFoundError(user_id=str(user_id))
    return UserOut(
        id=row.id,
        language=row.language,
        region_id=row.region_id,
        trust_score=row.trust_score,
        is_blocked=row.is_blocked,
        created_at=row.created_at,
        report_count=row.report_count,
    )


@router.post("/users/{user_id}/block", response_model=ChangeOut)
async def block_user(
    actor: AdminActor, session: DbSession, user_id: uuid.UUID, body: BlockIn
) -> ChangeOut:
    change = await service.set_user_blocked(
        session, actor=actor, user_id=user_id, blocked=body.blocked, reason=body.reason
    )
    await session.commit()
    return ChangeOut(object_id=user_id, before=_plain(change.before), after=_plain(change.after))


@router.post("/users/{user_id}/trust", response_model=ChangeOut)
async def set_trust(
    actor: AdminActor, session: DbSession, user_id: uuid.UUID, body: TrustIn
) -> ChangeOut:
    change = await service.set_user_trust_score(
        session, actor=actor, user_id=user_id, score=body.score, reason=body.reason
    )
    await session.commit()
    return ChangeOut(object_id=user_id, before=_plain(change.before), after=_plain(change.after))


class DigestOut(BaseModel):
    """Kunlik hisobot (`05` §8). Faqat sonlar — identifikator ham, koordinata ham yo'q."""

    region: str
    date: date
    stored: bool
    payload: dict[str, Any]


@router.get(
    "/digest",
    response_model=DigestOut,
    summary="Moderator uchun kunlik hisobot",
    responses={404: NOT_FOUND},
)
async def get_digest(
    actor: AdminActor,
    session: DbSession,
    region: str | None = None,
    day: Annotated[date | None, Query(alias="date")] = None,
) -> DigestOut:
    """Saqlangan hisobotni beradi; yo'q bo'lsa — o'sha kunni joyida hisoblaydi.

    Joyida hisoblash `daily_digest` ga **yozilmaydi**: yozish huquqi fon
    vazifasiniki, aks holda API so'rovi hisobotni «yig'ilgan» deb
    belgilab, o'sha kunning yuborilishini to'sib qo'yardi. Javobdagi
    `stored` aynan shuni ajratadi.

    Tugallanmagan kun so'ralsa `422`: yarim kunning raqamlari smena
    topshirishda yolg'on taassurot beradi.
    """
    actor.require(Permission.DIGEST_READ)
    # Davr avval tekshiriladi: yaroqsiz sana bazaga umuman bormaydi.
    latest = digest_mod.last_complete_day(datetime.now(timezone.utc))
    target = day or latest
    if target > latest:
        raise ValidationError("error.day_not_complete", date=target.isoformat())

    row = await geo.require_region(session, (region or settings.default_region_code).lower())
    stored = await digest_service.load(session, region_id=row.id, day=target)
    if stored is not None:
        return DigestOut(region=row.code, date=target, stored=True, payload=stored.to_payload())

    live = await digest_service.collect(
        session,
        region_id=row.id,
        region_code=row.code,
        period=digest_mod.period_for(target),
    )
    return DigestOut(region=row.code, date=target, stored=False, payload=live.to_payload())


@router.get("/audit", response_model=list[AuditOut])
async def read_audit(
    actor: AdminActor,
    session: DbSession,
    action: str | None = None,
    object_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AuditOut]:
    """Audit jurnali (`05` §2.5). Faqat `admin` roli."""
    actor.require(Permission.AUDIT_READ)
    entries = await audit.recent(session, limit=limit, action=action, object_id=object_id)
    return [
        AuditOut(
            id=e.id,
            actor_id=e.actor_id,
            actor_role=e.actor_role,
            action=e.action,
            object_id=e.object_id,
            before=e.before,
            after=e.after,
            created_at=e.created_at,
        )
        for e in entries
    ]


def _plain(payload: dict[str, object]) -> dict[str, Any]:
    """`uuid`/`datetime` ni JSON ga tushadigan ko'rinishga o'giradi."""
    return audit.jsonable(payload)


class GateCriterionOut(BaseModel):
    code: str
    label: str
    kind: str
    unit: str
    spec: str
    threshold: float | None
    direction: str
    value: float | None
    status: str


class GateOut(BaseModel):
    code: str
    release: str
    summary: str
    blocks: str
    status: str
    criteria: list[GateCriterionOut]


class GatesOut(BaseModel):
    region: str
    #: Birinchi yopilmagan gate ning kodi. `null` — hammasi yopiq.
    #: Bu maydon **hisobotning javobi**: qolgan hammasi dalil.
    blocking_gate: str | None
    #: Nima qilib bo'lmasligi (`03` §6 «Yopilmasa» ustuni), tarjima
    #: qilingan holda. Gate lar yopiq bo'lsa — bo'sh satr.
    blocked_action: str
    closed: int
    total: int
    gates: list[GateOut]


@router.get("/gates", response_model=GatesOut, summary="Reliz gate lari (`03` §6)")
async def read_gates(
    actor: AdminActor,
    session: DbSession,
    lang: ClientLang = None,
    region: str | None = None,
) -> GatesOut:
    """Gate lar hisoboti: qaysi biri yopiq, qaysi biri o'lchanmagan.

    **Bu endpoint hech narsani bloklamaydi.** U `03` §6 jadvalini
    bugungi sonlar bilan birga ko'rsatadi, qaror esa odamniki —
    gate «avtomatik yopilmasligi» aynan §6 ning talabi.

    Matn `Accept-Language` bo'yicha tarjima qilinadi: qolgan admin
    javoblaridan farqli ravishda (ular kod qaytaradi), bu yerda
    o'quvchi interfeys emas, **qaror qabul qiladigan odam**, va u
    hisobotni ko'chirib qo'yishi mumkin.
    """
    actor.require(Permission.GATES_READ)
    row = await geo.require_region(session, (region or settings.default_region_code).lower())
    language = i18n.pick_language(client=lang, region_default=row.default_language)
    values = await gate_collector.collect(session, region_id=row.id)
    report = gates_mod.evaluate(values)
    blocking = report.blocking_gate
    return GatesOut(
        region=row.code,
        blocking_gate=blocking.gate.code if blocking else None,
        blocked_action=i18n.t(blocking.gate.blocks_key, language) if blocking else "",
        closed=report.closed_count,
        total=len(report.gates),
        gates=[
            GateOut(
                code=result.gate.code,
                release=result.gate.release,
                summary=i18n.t(result.gate.summary_key, language),
                blocks=i18n.t(result.gate.blocks_key, language),
                status=str(result.status),
                criteria=[
                    GateCriterionOut(
                        code=item.criterion.code,
                        label=i18n.t(
                            item.criterion.key,
                            language,
                            min_reports=gates_mod.MIN_INDEPENDENT_REPORTS,
                        ),
                        kind=str(item.criterion.kind),
                        unit=item.criterion.unit,
                        spec=item.criterion.spec,
                        threshold=item.criterion.threshold,
                        direction=str(item.criterion.direction),
                        value=item.value,
                        status=str(item.status),
                    )
                    for item in result.criteria
                ],
            )
            for result in report.gates
        ],
    )


class MeasureOut(BaseModel):
    code: str
    label: str
    coverage: str
    #: Bugungi manba, `manba:nom` ko'rinishida. `null` — bog'lanish yo'q.
    bound: str | None
    #: Eng yaqin mavjud o'lchovlar — **tenglashtirib bo'lmaydiganlar**.
    #: Bo'sh ro'yxat «yaqini yo'q» degani, «bog'langan» emas.
    near: list[str]


class MeasureStageOut(BaseModel):
    code: str
    label: str
    #: `03` §11 ning «Nima uchun» ustuni.
    rationale: str
    measures: list[MeasureOut]


class MeasuresOut(BaseModel):
    #: Reliz tartibidagi birinchi yopilmagan ko'rsatkichning kodi.
    #: `null` — bo'shliq yo'q. Bu maydon — hisobotning javobi.
    first_gap: str | None
    #: Uning bosqichi: undan keyingi bosqichlarni o'lchash haqida
    #: gapirishdan oldin shuni yopish kerak.
    first_gap_stage: str | None
    #: Holat kodi → nechta ko'rsatkich (`measured`, `derivable`,
    #: `absent`, `external`).
    counts: dict[str, int]
    total: int
    stages: list[MeasureStageOut]


@router.get(
    "/measures",
    response_model=MeasuresOut,
    summary="O'lchov qamrovi (`03` §11)",
)
async def read_measures(
    actor: AdminActor,
    lang: ClientLang = None,
) -> MeasuresOut:
    """`03` §11 jadvali: qaysi ko'rsatkich bugun o'lchanadi, qaysi biri yo'q.

    **Bazaga murojaat qilmaydi va sonlarni ko'rsatmaydi.** Bu hisobot
    o'lchovning natijasi haqida emas, **asbobning o'zi** haqida:
    `/gates` dagi `unmeasured` mezonning sababi shu yerda yozilgan.
    Shuning uchun u mintaqaga ham bog'liq emas — qamrov butun
    mahsulot uchun bir xil.

    `near` maydonini «deyarli bog'langan» deb o'qish mumkin emas: u
    tenglashtirish **taqiqlangan** o'lchovlarni sanaydi (masalan
    `answer_p90` ↔ `time_to_confirm_seconds`), aks holda bo'shliq
    yopilmasdan ko'rinmas bo'lardi.
    """
    actor.require(Permission.MEASURES_READ)
    language = i18n.pick_language(client=lang, region_default=settings.default_language)
    report = measures_mod.evaluate()
    gap = report.first_gap
    return MeasuresOut(
        first_gap=gap.code if gap else None,
        first_gap_stage=gap.stage if gap else None,
        counts=report.counts,
        total=len(report.measures),
        stages=[
            MeasureStageOut(
                code=stage.code,
                label=i18n.t(stage.key, language),
                rationale=i18n.t(stage.rationale_key, language),
                measures=[
                    MeasureOut(
                        code=measure.code,
                        label=i18n.t(measure.key, language),
                        coverage=str(measure.coverage),
                        bound=str(measure.bound) if measure.bound else None,
                        near=[str(b) for b in measure.near],
                    )
                    for measure in report.for_stage(stage.code)
                ],
            )
            for stage in measures_mod.STAGES
        ],
    )

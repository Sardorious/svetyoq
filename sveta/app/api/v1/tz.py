"""TZ §11/7 — tashqi signalning kirish yo'li va manbalar reyestri.

178-run qabul mantiqini qurdi va uni ataylab **ulanmagan** qoldirdi:
`app/reports/tzsensor.py` ning `INBOUND` reyestri uchala signalni ham
`built=True, wired=False` deb belgilagan edi, ya'ni «В-7 hisoblanadi»
degan da'vo bor, «В-7 ishlaydi» degani yo'q. Bu modul ikkinchi da'voni
yopadi.

## Nima uchun bu `admin` tegi ostida

`05` §7.3 ommaviy sathdan nimani **chiqarmaslikni** aytadi; bu yerda
teskari savol — kim **kiritishi** mumkin. §8 javobni beradi: rasmiy
manbani operator kiritadi, va uning har bir amali «кто и на основании
чего» bilan jurnalga tushadi. Ya'ni yo'l tokensiz bo'la olmaydi.

🔴 **Qurilmaning o'z hisob ma'lumoti hali yo'q.** Bugun `X-Admin-Token`
ishlatiladi, ya'ni datchik to'g'ridan-to'g'ri emas, **shlyuz** orqali
yozadi (shlyuz tokenni saqlaydi). Har qurilma uchun alohida kalit —
alohida qaror: u yangi jadval, aylanma (rotatsiya) tartibi va
qurilmani bloklash oqimini talab qiladi, va ularning birortasi ham TZ
da yozilmagan. Taxminiy sxema o'ylab topilmaydi; savol
`PROGRESS.md` ning «Ochiq savollar» ida 👤 belgisi bilan turadi.

🔴 **Manbasiz xabar — `422`, rad etish emas.** `Reading.__post_init__`
bo'sh `reference` da yiqiladi (§8 ning taqiqi), va bu **so'rovning
shakli** haqidagi xato: unga `Reject` sababi berish «xabar keldi, lekin
hisobga olinmadi» degan ma'noni berardi, holbuki bunday xabar umuman
yuborilmasligi kerak. Qolgan hamma narsa — kanal, katak, vaqt, takror,
holat — javobda **sabab bilan** qaytadi va jurnalga yoziladi.

🔴 **Vaqt bu yerda o'qiladi.** Т-4 hisob funksiyasi soatga
qaramasligini talab qiladi; kimdir uni baribir o'qishi kerak va o'sha
joy — sathning chekkasi. `now` bir marta olinadi va butun paket **shu
bitta** vaqtga nisbatan baholanadi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import tzpanel
from app.admin.roles import Permission
from app.admin.tzoperator import Action, Basis, Decision, Incident, Request
from app.api.deps import AdminActor, DbSession
from app.core import tzconfig
from app.core.config import settings
from app.geo import pipeline as geo
from app.geo import queries as geo_q
from app.reports import tzintake
from app.reports.tzsensor import Fact, Intake, Reading, Signal

router = APIRouter(prefix="/tz", tags=["admin"])

#: Bitta so'rovdagi xabarlar chegarasi. §7 ning sozlamasi **emas** —
#: so'rovning o'lchami, ya'ni tarmoq geometriyasi (`KEY_DIGEST_BYTES`
#: bilan bir sinf). Qabul sikli butun paketni xotirada tartiblaydi va
#: `seen`/`last` ni sikl davomida yangilab boradi, ya'ni paket qanchalik
#: katta bo'lsa, bitta tranzaksiya shunchalik uzoq turadi.
MAX_BATCH = 500


class ReadingIn(BaseModel):
    """Kirgan bitta xabar. Maydonlar `tzsensor.Reading` bilan bir xil."""

    source_id: str = Field(min_length=1, max_length=100)
    signal: Signal
    at: datetime
    #: §8: «на основании чего» — qo'ng'iroq raqami, e'lon havolasi, xat.
    reference: str = Field(min_length=1, max_length=500)
    #: `operator`/`feed` uchun majburiy; `sensor` uchun reyestrdan olinadi
    #: va bu yerda ko'rsatilgani reyestrdagi bilan solishtiriladi.
    cell: str | None = Field(default=None, max_length=64)
    #: §8: «кто». `operator` kanalida majburiy.
    actor: str | None = Field(default=None, max_length=100)
    #: `planned` uchun: ishlar qachon boshlanadi (§6.3).
    starts_at: datetime | None = None


class IntakeIn(BaseModel):
    readings: list[ReadingIn] = Field(min_length=1, max_length=MAX_BATCH)


class FactOut(BaseModel):
    """Qabul qilingan signal. `key` — Т-7 ning kaliti, jurnaldagi bilan bir xil."""

    key: str
    source_id: str
    channel: str
    signal: str
    cell: str
    at: datetime
    reference: str
    actor: str | None
    starts_at: datetime | None
    #: В-7 — kvartalni darhol yopadigan fakt.
    closes_block: bool
    #: §8 — «Проверено оператором» ga asos bo'ladigan fakt.
    verifies_outage: bool


class RejectionOut(BaseModel):
    """Qabul qilinmagan xabar va **birinchi** buzilgan qoida."""

    source_id: str
    signal: str
    at: datetime
    reason: str
    #: §8 ning odamiga ko'rinadimi (buzuq qurilma, noto'g'ri sozlama).
    to_operator: bool


class IntakeOut(BaseModel):
    region: str
    accepted: list[FactOut]
    rejected: list[RejectionOut]
    #: Yig'indilar ataylab javobda: chaqiruvchi (shlyuz yoki panel)
    #: ro'yxatni qayta sanamasin va sanoq ikki joyda ajralib ketmasin.
    to_operator: int
    closures: int
    verifications: int
    planned: int


class SourceOut(BaseModel):
    source_id: str
    channel: str
    cell: str | None
    trusted: bool
    note: str | None
    created_at: datetime


class SourceCollection(BaseModel):
    region: str
    count: int
    sources: list[SourceOut]


#: Jurnaldan bir so'rovda o'qiladigan qatorlarning chegarasi.
#: `MAX_BATCH` bilan bir sinf: javobning o'lchami, §7 sozlamasi emas.
MAX_ACTIONS = 500


class ActionIn(BaseModel):
    """Operator bosgan tugma. Maydonlar `tzoperator.Request` bilan bir xil.

    `disputed` — hodisaning bugungi holati, chaqiruvchidan keladi.
    U so'rovda turadi va bazadan o'qilmaydi: TZ ning status qatlami
    mavjud `outages` jadvaliga hali ulanmagan (DP-4), va uni shu
    yerda «taxminan» hisoblash panelda ko'rinadigan holat bilan
    ajralib ketardi — operator ko'rgan narsa va kod ko'rgan narsa
    boshqa bo'lardi.
    """

    action: Action
    incident_id: str = Field(min_length=1, max_length=100)
    #: §8: «кто».
    actor: str = Field(min_length=1, max_length=100)
    #: §8: «на основании чего» — matn.
    reference: str = Field(min_length=1, max_length=500)
    #: §8 ning taqiqi o'lchanadigan maydon.
    basis: Basis
    at: datetime
    #: Operator ko'rgan qarshi dalil akkauntlari (§2.2).
    seen: list[str] = Field(default_factory=list, max_length=MAX_ACTIONS)
    #: Hodisa bugun «спорный случай» mi.
    disputed: bool = False


class ActionOut(BaseModel):
    region: str
    incident_id: str
    action: str
    accepted: bool
    #: `none` — qabul qilindi. Sabab **javobda ham, jurnalda ham**.
    refusal: str
    key: str
    #: Qaror §2.2 ning vetosini yopadimi.
    resolves: bool
    #: «Проверено оператором» ga olib boradimi.
    confirms: bool
    #: Hodisani yopadimi.
    closes: bool


class ActionRowOut(BaseModel):
    incident_id: str
    action: str
    basis: str
    actor: str
    reference: str
    accepted: bool
    refusal: str
    seen: list[str]
    key: str
    decided_at: datetime


class ActionCollection(BaseModel):
    region: str
    count: int
    actions: list[ActionRowOut]


def _action_out(region: str, decision: Decision) -> ActionOut:
    return ActionOut(
        region=region,
        incident_id=decision.request.incident_id,
        action=decision.request.action.value,
        accepted=decision.accepted,
        refusal=decision.refusal.value,
        key=decision.key,
        resolves=decision.resolves,
        confirms=decision.confirms,
        closes=decision.closes,
    )


def _fact_out(fact: Fact) -> FactOut:
    return FactOut(
        key=fact.key,
        source_id=fact.source_id,
        channel=fact.channel.value,
        signal=fact.signal.value,
        cell=fact.cell,
        at=fact.at,
        reference=fact.reference,
        actor=fact.actor,
        starts_at=fact.starts_at,
        closes_block=fact.closes_block,
        verifies_outage=fact.verifies_outage,
    )


def _intake_out(region: str, intake: Intake) -> IntakeOut:
    return IntakeOut(
        region=region,
        accepted=[_fact_out(fact) for fact in intake.accepted],
        rejected=[
            RejectionOut(
                source_id=item.reading.source_id,
                signal=item.reading.signal.value,
                at=item.reading.at,
                reason=item.reason.value,
                to_operator=item.to_operator,
            )
            for item in intake.rejected
        ],
        to_operator=len(intake.to_operator),
        closures=len(intake.closures()),
        verifications=len(intake.verifications()),
        planned=len(intake.planned()),
    )


@router.post(
    "/readings",
    response_model=IntakeOut,
    summary="Tashqi signalni qabul qilish (TZ §11/7)",
)
async def post_readings(
    body: IntakeIn,
    session: DbSession,
    actor: AdminActor,
    region: Annotated[str, Query(description="Mintaqa kodi, masalan `samarkand`")] = "",
) -> IntakeOut:
    """Datchik, operator yoki rasmiy kanalning xabarlari.

    Javob **hech qachon** jimgina bo'sh bo'lmaydi: qabul qilinmagan har
    bir xabar sababi bilan qaytadi va o'sha sabab jurnalga ham yoziladi.
    Bu В-7 uchun muhim — kvartal yopilmagan bo'lsa, nega yopilmagani
    aytilishi kerak, aks holda qurilmaning nosozligi «sokinlik» ga
    o'xshab qolardi.
    """
    actor.require(Permission.TZ_INTAKE)
    code = region or settings.default_region_code
    row = await geo.require_region(session, code)
    params = await _params(session, row.id, code)
    now = datetime.now(timezone.utc)

    readings = tuple(
        Reading(
            source_id=item.source_id,
            signal=item.signal,
            at=item.at,
            reference=item.reference,
            cell=item.cell,
            actor=item.actor,
            starts_at=item.starts_at,
        )
        for item in body.readings
    )
    intake = await tzintake.ingest(session, row.id, readings, now=now, params=params)
    # `get_session()` commit qilmaydi (`app/db/session.py`): usiz jurnal
    # qatori jimgina yo'qolardi va Т-7 ning kaliti keyingi so'rovda
    # ikkinchi marta fakt bo'lardi.
    await session.commit()
    return _intake_out(code, intake)


@router.get(
    "/sources",
    response_model=SourceCollection,
    summary="Ro'yxatdan o'tgan tashqi manbalar (TZ §8)",
)
async def get_sources(
    session: DbSession,
    actor: AdminActor,
    region: Annotated[str, Query(description="Mintaqa kodi, masalan `samarkand`")] = "",
) -> SourceCollection:
    """«Kim yozishga haqli» — smenani qabul qilishning bir qismi.

    Bo'sh ro'yxat **odatiy** javob: reyestr `tools/` bilan to'ldiriladi
    va bo'sh reyestrda har bir xabar `unknown_source` bilan tushadi.
    """
    actor.require(Permission.TZ_SOURCE_READ)
    code = region or settings.default_region_code
    row = await geo.require_region(session, code)
    rows = await tzintake.list_sources(session, row.id)
    return SourceCollection(
        region=code,
        count=len(rows),
        sources=[
            SourceOut(
                source_id=item.source_id,
                channel=item.channel,
                cell=item.cell,
                trusted=item.trusted,
                note=item.note,
                created_at=item.created_at,
            )
            for item in rows
        ],
    )


@router.post(
    "/operator/actions",
    response_model=ActionOut,
    summary="Operatorning qarori (TZ §8)",
)
async def post_operator_action(
    body: ActionIn,
    session: DbSession,
    actor: AdminActor,
    region: Annotated[str, Query(description="Mintaqa kodi, masalan `samarkand`")] = "",
) -> ActionOut:
    """§8 ning birinchi ikkita vakolati: bahsli holat va uzilishni yopish.

    Amal rad etilsa ham javob `200` bo'ladi va sabab `refusal` da
    qaytadi. Bu `POST /readings` bilan bir xil qaror: so'rovning
    **shakli** to'g'ri (imzo bor, hodisa bor), qabul qilinmagani esa
    §8 ning mazmuniy qoidasi — va u jurnalga yozilishi kerak. `4xx`
    esa jurnalsiz o'tib ketardi, ya'ni «kim tasdiqlashni o'z fikri
    bilan o'tkazmoqchi bo'ldi» degan qator hech qachon paydo
    bo'lmasdi.
    """
    actor.require(Permission.TZ_OPERATE)
    code = region or settings.default_region_code
    row = await geo.require_region(session, code)

    request = Request(
        action=body.action,
        incident_id=body.incident_id,
        actor=body.actor,
        reference=body.reference,
        basis=body.basis,
        at=body.at,
        seen=tuple(body.seen),
    )
    incident = Incident(
        incident_id=body.incident_id,
        disputed=body.disputed,
        closed=await tzpanel.closed(session, row.id, body.incident_id),
        rebuttal_users=tuple(body.seen),
    )
    decision = await tzpanel.apply_action(session, row.id, request, incident)
    # `get_session()` commit qilmaydi: usiz §8 ning jurnali jimgina
    # yo'qolardi va Т-7 ning kaliti keyingi so'rovda qaytadan bo'sh
    # bo'lib qolardi.
    await session.commit()
    return _action_out(code, decision)


@router.get(
    "/operator/actions",
    response_model=ActionCollection,
    summary="Operator amallarining jurnali (TZ §8)",
)
async def get_operator_actions(
    session: DbSession,
    actor: AdminActor,
    region: Annotated[str, Query(description="Mintaqa kodi, masalan `samarkand`")] = "",
    incident_id: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_ACTIONS)] = 100,
) -> ActionCollection:
    """§8: «кто и на основании чего» — rad etilgan urinishlar bilan birga."""
    actor.require(Permission.TZ_ACTION_READ)
    code = region or settings.default_region_code
    row = await geo.require_region(session, code)
    rows = await tzpanel.load_actions(
        session, row.id, incident_id=incident_id, limit=limit
    )
    return ActionCollection(
        region=code,
        count=len(rows),
        actions=[
            ActionRowOut(
                incident_id=item.incident_id,
                action=item.action.value,
                basis=item.basis.value,
                actor=item.actor,
                reference=item.reference,
                accepted=item.accepted,
                refusal=item.refusal.value,
                seen=list(item.seen),
                key=item.key,
                decided_at=item.decided_at,
            )
            for item in rows
        ],
    )


async def _params(
    session: AsyncSession, region_id: uuid.UUID, code: str
) -> tzconfig.TzParams:
    """§7 sozlamalari bazadan.

    «Отсутствие настройки при запуске = ошибка запуска, а не подстановка
    значения из кода» — shuning uchun yetishmagan kalit `TzParams` da
    `ConfigMissingError` beradi va bu yerda u **mintaqa sozlanmagan**
    xatosiga o'giriladi. Sukut qiymatiga tushish §7 ni buzardi:
    qabul sozlanmagan mintaqada ham ishlab ketardi va uning chegaralari
    hech kim ko'rmagan sonlar bo'lardi.
    """
    values = await geo_q.load_region_config(session, region_id)
    try:
        return tzconfig.params_from_mapping(values)
    except tzconfig.ConfigMissingError as exc:
        raise geo.RegionNotConfiguredError(region=code, setting=str(exc)) from exc

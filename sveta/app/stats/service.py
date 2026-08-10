"""Statistika vitrinasini yig'ish (E14, `05` §7.2).

Bu qatlam faqat **ulaydi**: hodisalarni `app.clustering` dan, xabar
o'lchovlarini `app.reports` dan, hudud faktlarini `app.geo` dan oladi va
toza modullarga (`aggregate`, `coverage`) uzatadi. Bitta ham `SELECT` shu
faylda yozilmagan — `05` §1 chegarasi.

Davr qoidasi. `from`/`to` berilmasa oxirgi `STATS_DEFAULT_PERIOD_DAYS` kun
olinadi; `to` **chegarasi kirmaydi** (`[from, to)`), shunda ketma-ket
davrlar bir-birining ustiga tushmaydi va ularning yig'indisi umumiy
natijaga teng bo'ladi.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import params as cluster_params
from app.clustering import repository as repo
from app.clustering.scale import QUALITY_UNKNOWN
from app.core.config import settings
from app.core.errors import ValidationError
from app.geo import queries as geo_q
from app.reports import queries as reports_q
from app.stats import aggregate, boundaries, coverage, mahalla_coverage, maturity
from app.stats import methodology as methodology_mod


class InvalidPeriodError(ValidationError):
    """`from` >= `to`, yoki davr ruxsat etilgandan uzun."""

    code = "invalid_period"
    message_key = "error.invalid_period"


@dataclass(frozen=True)
class Period:
    start: datetime
    end: datetime

    @property
    def days(self) -> int:
        return max(1, round((self.end - self.start).total_seconds() / 86400))


@dataclass(frozen=True)
class CoverageSnapshot:
    """Mintaqaning qamrov kesimi — tumanlar bo'yicha va umumiy.

    Alohida tur kerak bo'ldi, chunki Coverage Index **statistika
    vitrinasining bir qismi emas, balki har bir vitrinaning majburiy
    hamrohi** (`03` §R1.2, `01` PG-S4). Uni faqat `build_report` ichida
    hisoblash issiqlik xaritasi kabi boshqa vitrinalarni indekssiz
    qoldirardi — aynan `03` ogohlantirgan xato: xabar kam bo'lgan hudud
    «tinch» ko'rinadi.
    """

    #: Tuman qatorlari — chaqiruvchi ularni qayta so'ramasligi uchun.
    districts: list[geo_q.DistrictRow]
    per_district: dict[uuid.UUID, coverage.CoverageIndex]
    region: coverage.CoverageIndex


@dataclass(frozen=True)
class DistrictStats:
    """Bitta tuman bo'yicha kesim + uning Coverage Index i."""

    district_id: uuid.UUID | None
    code: str
    name_uz: str
    name_ru: str
    bucket: aggregate.Bucket
    index: coverage.CoverageIndex
    #: Chegara versiyasining amal qilish davri (`01` FR-S-803). Davr
    #: ichida chegara o'zgargan bo'lsa bitta `code` ikki marta chiqadi va
    #: ularni **faqat shu ikki maydon** ajratadi; qoldiq chelakda esa
    #: versiya yo'q — `None`.
    valid_from: datetime | None = None
    valid_to: datetime | None = None

    def name(self, lang: str) -> str:
        return self.name_ru if lang == "ru" else self.name_uz


@dataclass(frozen=True)
class StatsReport:
    """Vitrinaning to'liq javobi."""

    region_code: str
    period: Period
    total: aggregate.Bucket
    districts: list[DistrictStats]
    region_index: coverage.CoverageIndex
    #: Ma'lumot chuqurligi (`01` FR-S-901). Qamrovdan alohida: indeks
    #: hududni, bu esa kuzatuv tarixini o'lchaydi.
    region_maturity: maturity.Maturity
    #: Chegaralar spravochnigining versiyasi (`01` FR-S-803 AC — «в ответе
    #: указана версия справочника»). Davrga **bog'liq**, qamrov va
    #: chuqurlikdan farqli: savol aynan «bu davr qaysi chegaralar bo'yicha
    #: hisoblangan».
    boundaries: boundaries.BoundarySet
    #: Mahalla darajasidagi qamrov (`01` §16 API deltasining to'rtinchi
    #: qatori — «индекс покрытия махалли», §21 dashboardlari). Chegaralar
    #: versiyasidan farqli, davrga bog'liq emas: qamrov «hozir» degan
    #: savolga javob beradi (`region_coverage` bilan bir xil qaror).
    mahallas: mahalla_coverage.MahallaCoverage
    #: Raqamlar qaysi usul va qaysi qiymatlar bilan hisoblangani
    #: (`03` §R1.2 «metodologiya bo'limi bilan bog'lanish»). Vitrinaning
    #: qismi, ilova emas: `01` §5 jurnalist uchun qiymatni «statistika
    #: **ochilgan metodologiya** va qamrov indeksi bilan» deb ta'riflaydi,
    #: ya'ni ikkalasi ham bitta javobda bo'lishi kerak.
    methodology: methodology_mod.Methodology
    suppressed_outages: int
    suppressed_reports: int
    unassigned_ratio: float
    reconciles: bool
    truncated: bool

    @property
    def warnings(self) -> list[str]:
        """Vitrinada majburiy ko'rsatiladigan ogohlantirishlar (i18n kalitlari).

        Dislaymer har doim birinchi: `03` §R1.2 «indeks har vitrinada» va
        `04` §Qat'iy qoidalar «rasmiy manba emas» — ikkalasi ham javobning
        ixtiyoriy qismi emas.
        """
        keys = ["stats.disclaimer.not_official", "stats.disclaimer.coverage"]
        # «Yosh mintaqa» dislaymeri qamrovdan **oldin**: u butun vitrinani
        # qanday o'qish kerakligini aytadi (`01` §23, RS-10 — yosh
        # statistikani yetuk statistika bilan yonma-yon nashr etish).
        if self.region_maturity.is_young:
            keys.append(maturity.WARNING_YOUNG)
        if self.region_index.band in (coverage.CoverageBand.NONE, coverage.CoverageBand.LOW):
            keys.append("stats.warning.low_coverage")
        # Mahalla qamrovi mintaqa qamrovidan **keyin**: u umumiy xulosani
        # emas, uning tafsilotini cheklaydi. Spravochnik yo'q bo'lsa
        # (E17 gacha — har doim) javob buni ochiq aytadi, aks holda
        # `mahallas.index = 0` «mahallalarda qamrov yo'q» deb o'qilardi.
        keys.extend(self.mahallas.warnings)
        # Chegara o'zgarishi «yosh mintaqa» bilan bir toifada: u ham butun
        # vitrinani qanday o'qish kerakligini aytadi, bitta chelakni emas
        # (`01` FR-S-803, OQ-01 mitigatsiyasi).
        if self.boundaries.changed_in_period:
            keys.append(boundaries.WARNING_CHANGED)
        if self.unassigned_ratio > aggregate.MAX_UNASSIGNED_RATIO:
            keys.append("stats.warning.unassigned")
        # Davomiylik ogohlantirishlari **mintaqa** kesimidan olinadi:
        # ular `total.duration` ni qanday o'qish kerakligini aytadi.
        # Bitta tumanning kesimi qiya bo'lsa, bu vitrinaning umumiy
        # ogohlantirishi emas — u o'sha tumanning `duration` bloki
        # ichida ko'rinadi.
        keys.extend(self.total.duration.warnings)
        if self.suppressed_outages:
            keys.append("stats.warning.suppressed")
        if self.truncated:
            keys.append("stats.warning.truncated")
        return keys


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def floor_to(moment: datetime, quantum_s: int) -> datetime:
    """Vaqtni `quantum_s` panjarasiga pastga qadaydi (epoxadan hisoblab)."""
    if quantum_s <= 0:
        return moment
    epoch = int(moment.timestamp())
    return datetime.fromtimestamp(epoch - epoch % quantum_s, tz=timezone.utc)


def resolve_period(
    start: datetime | None,
    end: datetime | None,
    *,
    now: datetime | None = None,
    quantum_s: int = 0,
) -> Period:
    """So'rov parametrlarini yopiq-ochiq oraliqqa keltiradi.

    Kelajakdagi `to` kesiladi: «ertangi kunga statistika» degan savol
    ma'noga ega emas va javobni tushunarsiz qilardi.

    **`quantum_s` nima uchun bor.** Mijoz `to` ni bermasa oraliq oxiri
    «hozir» bo'ladi, ya'ni mikrosoniyagacha aniq va har so'rovda boshqa.
    Javob mazmunidan `ETag` quriladigan endpointda (`/heatmap`) bu
    keshni butunlay o'ldiradi: ma'lumot bir xil bo'lsa ham `period.end`
    o'zgaradi → `ETag` o'zgaradi → `304` **hech qachon** chiqmaydi,
    holbuki o'sha javob `Cache-Control: max-age` bilan «shuncha vaqt
    o'zgarmaydi» deb yuboriladi. Ikkala sarlavha bir-biriga zid edi.
    Panjara aynan o'sha `max-age` ga teng olinadi, ya'ni yangi qiymat
    kesh muddati tugagandagina paydo bo'ladi.

    Mijoz `to` ni aniq bergan bo'lsa qadalmaydi: u so'ragan chegara
    javobda o'zgarishsiz qolishi kerak.
    """
    moment = now or _utcnow()
    finish = min(end or moment, moment)
    if end is None:
        finish = floor_to(finish, quantum_s)
    begin = start or finish - timedelta(days=settings.stats_default_period_days)
    if begin >= finish:
        raise InvalidPeriodError("error.invalid_period")
    if (finish - begin).days > settings.stats_max_period_days:
        raise InvalidPeriodError(
            "error.invalid_period", max_days=settings.stats_max_period_days
        )
    return Period(start=begin, end=finish)


def _coverage_input(
    stats: geo_q.TerritoryStatsRow | None,
    *,
    cells_with_reports: int,
    min_active: int,
    full_spread_ratio: float,
) -> coverage.CoverageInput | None:
    if stats is None:
        return None
    return coverage.CoverageInput(
        active_users_30d=stats.active_users_30d,
        populated_cells=stats.populated_cells,
        cells_with_reports=cells_with_reports,
        households=stats.households,
        data_quality=stats.data_quality,
        min_active=min_active,
        full_spread_ratio=full_spread_ratio,
        target_penetration=settings.stats_target_penetration,
    )


def _index_for(
    stats: geo_q.TerritoryStatsRow | None,
    *,
    cells_with_reports: int,
    params: cluster_params.Params,
    min_active: int | None = None,
    full_spread_ratio: float | None = None,
) -> coverage.CoverageIndex:
    """Hudud faktlaridan indeks. Chegaralar **daraja bo'yicha**.

    Standart qiymatlar tuman darajasiniki, chunki chaqiruvchilarning
    ko'pi shu darajada ishlaydi. Mahalla darajasi ularni ochiq
    almashtiradi: `06` §5.3 va §5.4 ikki daraja uchun **alohida**
    chegaralar beradi (`min_active_mahalla = 10` ↔ `min_active_district
    = 30`, `cell_ratio_mahalla = 0.15` ↔ `cell_ratio_district = 0.30`)
    va ularni chalkashtirish indeksni ikki baravar noto'g'ri qilardi:
    mahalla qamralmagan, tuman esa haddan tashqari qamralgan bo'lib
    ko'rinardi.
    """
    facts = _coverage_input(
        stats,
        cells_with_reports=cells_with_reports,
        min_active=params.guard.min_active_district if min_active is None else min_active,
        full_spread_ratio=(
            params.scale.cell_ratio_district
            if full_spread_ratio is None
            else full_spread_ratio
        ),
    )
    return coverage.unknown() if facts is None else coverage.compute(facts)


def region_index(
    per_district: list[coverage.CoverageIndex],
) -> coverage.CoverageIndex:
    """Mintaqa darajasidagi indeks — tumanlar bo'yicha **o'rtacha**.

    O'rtacha, maksimum emas: bitta yaxshi qamralgan tuman mintaqa
    statistikasini «ishonchli» qilib ko'rsatmasligi kerak. Pog'ona ham
    o'rtachadan qayta hisoblanadi, ya'ni u ham pastga qarab og'adi.

    `data_quality` — eng past sifat: agar bitta tuman ham `unknown` bo'lsa,
    mintaqa raqami ham to'liq emas.
    """
    if not per_district:
        return coverage.unknown()
    mean = round(sum(i.index for i in per_district) / len(per_district))
    qualities = {i.data_quality for i in per_district}
    quality = QUALITY_UNKNOWN if QUALITY_UNKNOWN in qualities else min(qualities)
    raw = coverage.band_of(mean)
    band = coverage.cap(raw, coverage.CoverageBand.LOW) if quality == QUALITY_UNKNOWN else raw
    return coverage.CoverageIndex(
        index=mean,
        band=band,
        raw_band=raw,
        sufficiency=sum(i.sufficiency for i in per_district) / len(per_district),
        spread=None,
        penetration=None,
        data_quality=quality,
        limiting_factor="region_mean",
    )


async def region_coverage(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    now: datetime | None = None,
) -> CoverageSnapshot:
    """Mintaqaning Coverage Index i — vitrinadan qat'i nazar bir xil.

    Qamrov oynasi (`COVERAGE_WINDOW_DAYS`) so'ralgan davrga **bog'liq
    emas**: indeks «hozir bu hudud qamralganmi» degan savolga javob
    beradi, «o'sha davrda qamralganmi» degan savolga emas. Aks holda bir
    yil oldingi kesimni so'ragan odam o'sha davrning qamrovini bugungi
    ma'lumot sifatida o'qib qo'yardi.
    """
    moment = now or _utcnow()
    districts = await geo_q.current_districts(session, region_id)
    territory = await geo_q.load_territory_stats_many(session, [d.id for d in districts])
    cells = await reports_q.cells_with_reports_by_district(
        session, region_id=region_id, since=moment - timedelta(days=settings.coverage_window_days)
    )
    config = await geo_q.load_region_config(session, region_id)
    params = cluster_params.from_mapping(config)

    per_district = {
        district.id: _index_for(
            territory.get(district.id),
            cells_with_reports=cells.get(district.id, 0),
            params=params,
        )
        for district in districts
    }
    return CoverageSnapshot(
        districts=districts,
        per_district=per_district,
        # Tartib `districts` bo'yicha qotirilgan: o'rtacha to'plamdan
        # olinadi, ya'ni tartib natijaga ta'sir qilmaydi, lekin
        # `dict` ustidan yurish tartibi testda ko'rinib qolmasligi uchun.
        region=region_index([per_district[d.id] for d in districts]),
    )


async def mahalla_index(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    now: datetime | None = None,
) -> mahalla_coverage.MahallaCoverage:
    """Mintaqaning mahalla darajasidagi qamrovi (`01` §16, §21).

    **Nima uchun `region_coverage` ning ichida emas.** O'sha funksiyani
    ikkala vitrina ham chaqiradi (`/stats`, `/heatmap`), mahalla kesimi
    esa faqat statistikaga tegishli: `01` §16 talabi aynan «ответы
    статистики» haqida, issiqlik xaritasi esa H3 katakchalari ustida
    quriladi va ma'muriy darajalarni umuman ko'rsatmaydi (`boundaries`
    ham shu sabab u yerga qo'shilmagan va sabab kontrakt testida
    yozilgan). Qo'shilsa, `/heatmap` har so'rovda uchta ortiqcha so'rov
    qilardi va javobiga hech qachon o'qilmaydigan blok chiqardi.

    **Bo'sh ro'yxat yakuniy javob emas.** Spravochnik E17 gacha bo'sh, ya'ni
    hozir bu funksiya har doim `missing()` qaytaradi — lekin u
    `available=False` bilan qaytaradi, `index=0` bilan emas.
    `region_has_mahallas` faqat ro'yxat bo'sh chiqqanda so'raladi
    (27-sessiyaning `GET /geo/mahallas` dagi `bool(rows) or await …`
    naqshi).
    """
    moment = now or _utcnow()
    limit = settings.stats_max_mahallas
    rows = await geo_q.current_mahallas(session, region_id, limit=limit + 1)
    if not rows:
        # Joriy kesim bo'sh. Sababi ikkita va ular bir xil emas:
        # spravochnik umuman to'ldirilmagan yoki barcha qatorlari bekor
        # qilingan. Ikkinchisi — real ma'muriy hodisa va uni
        # «spravochnik yo'q» deb ko'rsatish yolg'on bo'lardi.
        has_any = await geo_q.region_has_mahallas(session, region_id)
        return (
            mahalla_coverage.summarize([], available=True)
            if has_any
            else mahalla_coverage.missing()
        )

    truncated = len(rows) > limit
    rows = rows[:limit]

    territory = await geo_q.load_territory_stats_many(session, [m.id for m in rows])
    cells = await reports_q.cells_with_reports_by_mahalla(
        session, region_id=region_id, since=moment - timedelta(days=settings.coverage_window_days)
    )
    config = await geo_q.load_region_config(session, region_id)
    params = cluster_params.from_mapping(config)

    facts = [
        mahalla_coverage.MahallaFact(
            id=row.id,
            district_id=row.district_id,
            district_code=row.district_code,
            name_uz=row.name_uz,
            name_ru=row.name_ru,
            index=_index_for(
                territory.get(row.id),
                cells_with_reports=cells.get(row.id, 0),
                params=params,
                # Chegaralar **mahalla** darajasiniki (`06` §5.3, §5.4):
                # `min_active_district = 30` mahallaga qo'llansa har bir
                # mahalla qamralmagan bo'lib chiqardi va indeks butun
                # ma'nosini yo'qotardi.
                min_active=params.guard.min_active_mahalla,
                full_spread_ratio=params.scale.cell_ratio_mahalla,
            ),
        )
        for row in rows
    ]
    return mahalla_coverage.summarize(facts, available=True, truncated=truncated)


async def region_maturity(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    now: datetime | None = None,
) -> maturity.Maturity:
    """Mintaqaning ma'lumot chuqurligi — vitrinadan qat'i nazar bir xil.

    `region_coverage` bilan bir xil sababdan alohida funksiya: chuqurlik
    ham **har bir vitrinaning** hamrohi (`01` FR-S-901 P0, §23), ya'ni uni
    `build_report` ichida yashirish issiqlik xaritasini pometasiz
    qoldirardi.

    Davrga bog'liq emas — `region_coverage` dagidek: savol «bu mintaqa
    haqida umuman xulosa chiqarish mumkinmi», «so'ralgan davrda
    mumkinmi» emas.
    """
    return maturity.compute(
        maturity.MaturityInput(
            observed_since=await reports_q.first_report_at(session, region_id),
            events=await repo.count_confirmed_ever(session, region_id),
            now=now or _utcnow(),
            min_days=settings.stats_min_history_days,
            min_events=settings.stats_min_events,
        )
    )


def public_limits() -> methodology_mod.PublicLimits:
    """`settings` → metodologiyaning deploy darajasidagi qiymatlari.

    Alohida funksiya, chunki uni testlarning fikstyurasi ham chaqiradi.
    Ikkita nusxa bo'lsa ular ajralib ketishi mumkin edi va o'shanda
    testlar mahsulotda umuman bo'lmaydigan metodologiyani tekshirardi —
    yashil suite bilan.
    """
    return methodology_mod.PublicLimits(
        h3_resolution=settings.h3_resolution,
        min_reports=settings.public_min_reports,
        time_rounding_min=settings.public_time_rounding_min,
        coverage_window_days=settings.coverage_window_days,
        target_penetration=settings.stats_target_penetration,
        autoclose_after_min=settings.cluster_autoclose_after_min,
    )


async def region_methodology(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
) -> methodology_mod.Methodology:
    """Mintaqaning metodologiyasi — jonli `region_config` bilan (`03` §R1.2).

    **Nima uchun alohida funksiya, `region_coverage` ning ichida emas.**
    Metodologiya vitrinaning bir qismi sifatida ham (`build_report`),
    o'zi yolg'iz ham (`/stats/methodology`) so'raladi, va ikkinchi holatda
    hech qanday agregat hisoblanmaydi: metodologiyani o'qish uchun
    statistika so'rashga majbur qilish uni «qo'shimcha» ga aylantirardi.

    `settings` dan keladigan qiymatlar aynan shu yerda yig'iladi —
    `methodology` moduli toza qoladi (`coverage.py` bilan bir xil qoida).
    """
    config = await geo_q.load_region_config(session, region_id)
    return methodology_mod.build(cluster_params.from_mapping(config), public_limits())


async def build_report(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    region_code: str,
    period: Period,
    now: datetime | None = None,
) -> StatsReport:
    """Mintaqa bo'yicha to'liq statistika hisoboti."""
    moment = now or _utcnow()
    limit = settings.stats_max_outages

    rows = await repo.stats_rows_started_between(
        session,
        region_id=region_id,
        since=period.start,
        until=period.end,
        limit=limit + 1,
    )
    truncated = len(rows) > limit
    rows = rows[:limit]

    counts = await reports_q.count_attached_many(session, [r.id for r in rows])
    facts = [
        aggregate.OutageFact(
            id=row.id,
            district_id=row.district_id,
            status=row.status,
            scale=row.scale,
            confidence=row.confidence,
            started_at=row.started_at,
            resolved_at=row.resolved_at,
            report_count=counts.get(row.id, 0),
            last_report_at=row.last_report_at,
        )
        for row in rows
    ]
    agg = aggregate.build(
        facts,
        min_reports=settings.public_min_reports,
        # Taymer chegarasi klasterlashniki: davomiylik kesimi «taymer
        # bilan yopilgan» ni **o'sha** qoida bo'yicha sanashi kerak,
        # o'zining nusxasi bo'yicha emas (`05` §4.2).
        autoclose_after_min=settings.cluster_autoclose_after_min,
    )

    snapshot = await region_coverage(session, region_id=region_id, now=moment)
    depth = await region_maturity(session, region_id=region_id, now=moment)
    mahallas = await mahalla_index(session, region_id=region_id, now=moment)
    method = await region_methodology(session, region_id=region_id)

    # Vitrina **davrning** chegaralari bo'yicha quriladi, joriylari
    # bo'yicha emas (`01` FR-S-803: «применяются старые границы»).
    # `snapshot.districts` bu yerda yaramaydi: u `region_coverage` niki va
    # ataylab joriy kesim (qamrov «hozir» degan savolga javob beradi).
    versions = await geo_q.districts_for_period(
        session, region_id=region_id, start=period.start, end=period.end
    )
    boundary_set = boundaries.summarize(
        [
            boundaries.BoundaryFact(
                code=row.code,
                valid_from=row.valid_from,
                valid_to=row.valid_to,
                source=row.source,
                license=row.license,
            )
            for row in versions
        ],
        start=period.start,
        end=period.end,
    )

    buckets = {b.district_id: b for b in agg.buckets}
    out: list[DistrictStats] = []
    for district in versions:
        out.append(
            DistrictStats(
                district_id=district.id,
                code=district.code,
                name_uz=district.name_uz,
                name_ru=district.name_ru,
                bucket=buckets.pop(district.id, aggregate.Bucket(district_id=district.id)),
                # Yopilgan versiyaning qamrovi **yo'q**, nol emas:
                # `region_coverage` faqat joriy tumanlarni biladi va
                # bekor qilingan tumanning «hozirgi qamrovi» degan savol
                # ma'noga ega emas (`06` §5.4 — «ma'lumot yo'q» va
                # «qamrov nol» bir xil narsa emas).
                index=snapshot.per_district.get(district.id, coverage.unknown()),
                valid_from=district.valid_from,
                valid_to=district.valid_to,
            )
        )

    # Tumani aniqlanmagan chelaklar yo'qolmaydi — `05` §5.3. Chegara
    # o'zgargani uchun yo'q bo'lgan tumanlar endi bu yerga tushmaydi:
    # ular yuqorida, o'z nomi bilan chiqadi.
    for district_id, bucket in buckets.items():
        out.append(
            DistrictStats(
                district_id=district_id,
                code="unassigned" if district_id is None else str(district_id),
                # Nom bo'sh: bu haqiqiy tuman emas, qoldiq chelak. Uning
                # matni katalogda (`stats.unassigned`) — qattiq kodlangan
                # foydalanuvchi matni bloklovchi defekt (`04` §6).
                name_uz="",
                name_ru="",
                bucket=bucket,
                index=coverage.unknown(),
            )
        )

    return StatsReport(
        region_code=region_code,
        period=period,
        total=agg.total,
        districts=out,
        region_index=snapshot.region,
        region_maturity=depth,
        boundaries=boundary_set,
        mahallas=mahallas,
        methodology=method,
        suppressed_outages=agg.suppressed_outages,
        suppressed_reports=agg.suppressed_reports,
        unassigned_ratio=agg.unassigned_ratio,
        reconciles=agg.reconciles,
        truncated=truncated,
    )

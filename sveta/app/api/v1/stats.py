"""Statistika endpointi (`05` §7.2, E14).

`GET /api/v1/stats` — hudud, davr va davomiylik kesimida + Coverage Index
(`03` §R1.2 uchala kesimni ham talab qiladi).
`GET /api/v1/stats.csv` — o'sha javobning CSV ko'rinishi (`03` §R1.2).

Ommaviy endpoint, ya'ni `05` §7.3 to'liq kuchda: `geom_exact` ham,
`user_id` ham, koordinata ham yo'q; 3 tadan kam xabarli hodisa agregatga
kirmaydi (uning soni `suppressed_outages` da qoladi — jimgina yo'qolmaydi).

`warnings` — javobning **majburiy** qismi, ixtiyoriy bezak emas: `03` §R1.2
«har bir vitrina Coverage Index bilan birga ko'rsatiladi» va «rasmiy manba
emas» ogohlantirishi barcha yuzalarda (`04`). Interfeys ularni ko'rsatmasa,
bu bloklovchi defekt.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.analytics import track as analytics
from app.api.deps import ClientLang, DbSession
from app.api.openapi import NOT_FOUND
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.i18n import t
from app.geo import pipeline as geo
from app.geo import registry
from app.stats import aggregate, export, methodology
from app.stats import service as stats_service

router = APIRouter(tags=["public"])

RegionQuery = Annotated[str, Query(description="Mintaqa kodi, masalan `samarkand`")]
FromQuery = Annotated[datetime | None, Query(alias="from", description="Davr boshi (ISO)")]
ToQuery = Annotated[datetime | None, Query(alias="to", description="Davr oxiri (kirmaydi)")]


class CoverageOut(BaseModel):
    """Coverage Index va uni tushuntiradigan komponentlar."""

    index: int = Field(description="0–100")
    band: str
    message_key: str
    data_quality: str
    limiting_factor: str = Field(description="Indeksni cheklagan komponent nomi")
    degraded: bool = Field(description="Pog'ona ma'lumot sifati tufayli pasaytirildimi")


class MaturityOut(BaseModel):
    """Ma'lumot chuqurligi — «yosh mintaqa» pometasi (`01` FR-S-901).

    Coverage Index bilan aralashtirmang: indeks hududning **qamrovini**,
    bu esa kuzatuvning **yoshini** o'lchaydi. Ikkalasi ham vitrinada
    majburiy.
    """

    observed_since: str | None = Field(description="Mintaqadagi birinchi xabar (ISO)")
    observed_days: int
    events: int = Field(description="Butun tarixda tasdiqlangan hodisalar soni")
    is_young: bool
    message_key: str
    reason_keys: list[str]
    #: Chegaralar javobda ochiq: «yosh» so'zi nimani anglatishini mijoz
    #: o'zi ko'radi va o'ylab topmaydi.
    min_days: int
    min_events: int


class DurationOut(BaseModel):
    """Davomiylik kesimi — `03` §R1.2 ning uchinchi kesimi.

    `avg_duration_min` ni almashtirmaydi, uni **to'ldiradi**: `01` §4
    kuzatiladigan ko'rsatkich sifatida medianani va P90 ni nomi bilan
    sanaydi, ularning ikkalasi ham o'rtachadan chiqmaydi.
    """

    measured: int = Field(description="Davomiyligi o'lchangan hodisalar")
    ongoing: int = Field(description="Hali ochiq — davomiyligi noma'lum")
    timeout_closed: int = Field(description="O'lchanganlardan taymer bilan yopilganlari")
    median_min: int | None
    p90_min: int | None
    bands: dict[str, int] = Field(description="Pog'onalar bo'yicha taqsimot")
    #: Namuna kichik bo'lsa mediana ham, P90 ham `None`. Maydon uni
    #: `null` dan ajratadi: «o'lchanmadi» va «hodisa yo'q» bir xil emas.
    sufficient: bool
    min_sample: int
    warnings: list[str]


class BucketOut(BaseModel):
    outages_total: int
    by_status: dict[str, int]
    reports_total: int
    avg_duration_min: int | None
    duration: DurationOut


class BoundariesOut(BaseModel):
    """Chegaralar spravochnigining versiyasi (`01` FR-S-803 AC).

    Vitrinaning majburiy qismi: ma'muriy qayta tashkil etishdan keyin
    ikki davrning bir xil nomlari bir xil hududni anglatmaydi va buni
    javobdan bilib bo'lmasa, o'quvchi ularni to'g'ridan-to'g'ri
    taqqoslab qo'yadi.
    """

    version: str | None = Field(description="Davrdagi eng so'nggi kesim sanasi (ISO)")
    versions: int = Field(description="Davrda amal qilgan chegara versiyalari soni")
    districts: int = Field(description="Turli tumanlar soni")
    sources: list[str]
    licenses: list[str]
    changed_in_period: bool = Field(description="Davr ichida chegara o'zgardimi")


class MahallaOut(BaseModel):
    """Bitta mahallaning qamrov kesimi (`01` §21 dashboardi uchun).

    Hodisalar chelagi **yo'q** va bu ataylab: `05` §7.3 ommaviy javobda
    kichik hududning tafsilotini taqiqlaydi, `06` esa masshtab da'vosini
    qamrovga bog'laydi. Ya'ni javob «bu mahallada nechta uzilish bo'ldi»
    demaydi — u faqat «bu mahalla haqidagi raqamga qanchalik ishonish
    mumkin» degan savolga javob beradi.
    """

    mahalla_id: uuid.UUID
    district_id: uuid.UUID
    district_code: str
    name: str
    coverage: CoverageOut


class MahallaCoverageOut(BaseModel):
    """Mahalla darajasidagi qamrov (`01` §16 API deltasi, §21).

    `available` — javobning eng muhim maydoni. `mahallas` jadvali E17
    gacha bo'sh (`05` §2.1) va `total = 0`, `index = 0` bo'lgan javob
    «mahallalarda qamrov yo'q» deb o'qilardi. Aslida bu FR-S-802
    degradatsiyasi: «привязка выполняется только к району **без
    ошибки**» — ya'ni holat yaroqli, lekin u ko'rinishi shart.
    """

    available: bool = Field(description="Mintaqada mahalla spravochnigi bormi")
    total: int = Field(description="Joriy kesimdagi mahallalar soni")
    measured: int = Field(description="Ulardan `territory_stats` qatori borlari")
    coverage: CoverageOut = Field(description="O'lchanganlar bo'yicha o'rtacha indeks")
    bands: dict[str, int] = Field(description="Pog'onalar bo'yicha taqsimot")
    truncated: bool
    items: list[MahallaOut]


class DistrictOut(BaseModel):
    district_id: uuid.UUID | None
    code: str
    name: str
    stats: BucketOut
    coverage: CoverageOut
    #: Qatorning chegara versiyasi. Davr ichida chegara o'zgargan bo'lsa
    #: bitta `code` ikki marta chiqadi va ularni faqat shu ikki maydon
    #: ajratadi.
    valid_from: str | None = None
    valid_to: str | None = None


class PeriodOut(BaseModel):
    start: str
    end: str
    days: int


class MethodologyValueOut(BaseModel):
    """Ochib beriladigan bitta qiymat."""

    code: str = Field(description="Parametrning haqiqiy nomi, yorlig'i emas")
    value: str = Field(description="Kanonik matn ko'rinishi")


class MethodologySectionOut(BaseModel):
    """Metodologiyaning bitta bo'limi: matn **va** qiymatlar."""

    code: str
    spec: str = Field(description="Birlamchi manba, masalan `06 §4`")
    title: str
    body: str
    values: list[MethodologyValueOut]


class MethodologyOut(BaseModel):
    """To'liq metodologiya bo'limi (`03` §R1.2)."""

    region: str
    version: str
    title: str
    sections: list[MethodologySectionOut]


class MethodologyRefOut(BaseModel):
    """Vitrinadan metodologiyaga havola.

    `url` — nisbiy: xostni javobga yozish uni reverse-proxy sozlamasiga
    bog'lab qo'yardi, `API_PREFIX` esa sozlama bo'lgani uchun qo'lda
    yozilgan `/api/v1` birinchi o'zgarishdayoq yolg'onga aylanardi.
    """

    version: str
    url: str


class StatsOut(BaseModel):
    region: str
    period: PeriodOut
    total: BucketOut
    districts: list[DistrictOut]
    coverage: CoverageOut
    #: `01` FR-S-901 — yosh mintaqa dislaymeri uchun.
    maturity: MaturityOut
    #: `01` FR-S-803 — «в ответе указана версия справочника».
    boundaries: BoundariesOut
    #: `01` §16 — «индекс покрытия махалли». Chegaralar versiyasi bilan
    #: bitta qatorda talab qilinadi, lekin boshqa savolga javob beradi:
    #: versiya «qaysi chegaralar bo'yicha», bu esa «qaysi darajada
    #: ishonish mumkin».
    mahallas: MahallaCoverageOut
    #: `03` §R1.2 — «metodologiya bo'limi bilan bog'lanish». Havola, to'liq
    #: bo'lim emas: `/stats` javobi allaqachon katta va metodologiya har
    #: so'rovda bir xil. Muhimi — vitrinani metodologiyasiz **ko'rsatib
    #: bo'lmasligi**: `version` javobning ichida turadi, ya'ni saqlangan
    #: yoki eksport qilingan kesim keyinchalik ham usulga bog'lanadi.
    methodology: MethodologyRefOut
    suppressed_outages: int
    suppressed_reports: int
    unassigned_ratio: float
    #: Chelaklar yig'indisi umumiy natijaga tengmi (`03` §R1.2 chiqish
    #: mezoni). Har javobda ochiq chiqadi — mijoz uni tekshira oladi.
    reconciles: bool
    truncated: bool
    warnings: list[str]
    warning_texts: list[str]


def coverage_out(index) -> CoverageOut:
    """`CoverageIndex` → javob modeli.

    Ommaviy, chunki indeks **har bir vitrinada** chiqadi (`03` §R1.2) va
    ularning shakli bir xil bo'lishi kerak: `/heatmap` ham shuni
    ishlatadi.
    """
    return CoverageOut(
        index=index.index,
        band=str(index.band),
        message_key=index.message_key,
        data_quality=index.data_quality,
        limiting_factor=index.limiting_factor,
        degraded=index.is_degraded,
    )


def maturity_out(depth) -> MaturityOut:
    """`Maturity` → javob modeli.

    `coverage_out` bilan bir xil sababdan ommaviy: pometa har bir
    vitrinada bir xil shaklda chiqishi kerak (`/heatmap` ham shuni
    ishlatadi).
    """
    return MaturityOut(
        observed_since=None if depth.observed_since is None else depth.observed_since.isoformat(),
        observed_days=depth.observed_days,
        events=depth.events,
        is_young=depth.is_young,
        message_key=depth.message_key,
        reason_keys=list(depth.reason_keys),
        min_days=depth.min_days,
        min_events=depth.min_events,
    )


def boundaries_out(bset) -> BoundariesOut:
    """`BoundarySet` → javob modeli.

    `coverage_out` va `maturity_out` bilan bir xil sababdan ommaviy:
    spravochnik versiyasi ham vitrinaning majburiy hamrohi va uning
    shakli hamma joyda bir xil bo'lishi kerak.
    """
    return BoundariesOut(
        version=bset.version,
        versions=bset.versions,
        districts=bset.districts,
        sources=list(bset.sources),
        licenses=list(bset.licenses),
        changed_in_period=bset.changed_in_period,
    )


def mahallas_out(block, *, lang: str) -> MahallaCoverageOut:
    """`MahallaCoverage` → javob modeli.

    Nomi shu yerda tanlanadi, modulda emas: toza modul tilni bilmaydi va
    bilmasligi ham kerak (`04` §6 — matn faqat katalogdan, til esa
    so'rov darajasida hal qilinadi).
    """
    return MahallaCoverageOut(
        available=block.available,
        total=block.total,
        measured=block.measured,
        coverage=coverage_out(block.index),
        bands=dict(block.bands),
        truncated=block.truncated,
        items=[
            MahallaOut(
                mahalla_id=item.id,
                district_id=item.district_id,
                district_code=item.district_code,
                name=item.name(lang),
                coverage=coverage_out(item.index),
            )
            for item in block.items
        ],
    )


def duration_out(cut) -> DurationOut:
    """`DurationCut` → javob modeli.

    `coverage_out` bilan bir xil sababdan ommaviy: kesim har bir
    chelakda bir xil shaklda chiqadi.
    """
    return DurationOut(
        measured=cut.measured,
        ongoing=cut.ongoing,
        timeout_closed=cut.timeout_closed,
        median_min=cut.median_min,
        p90_min=cut.p90_min,
        bands=dict(cut.bands),
        sufficient=cut.sufficient,
        min_sample=cut.min_sample,
        warnings=list(cut.warnings),
    )


def _bucket_out(bucket: aggregate.Bucket) -> BucketOut:
    return BucketOut(
        outages_total=bucket.outages_total,
        by_status=bucket.statuses(),
        reports_total=bucket.reports_total,
        avg_duration_min=bucket.avg_duration_min,
        duration=duration_out(bucket.duration),
    )


#: Metodologiya endpointining yo'li, prefikssiz. `METHODOLOGY_PATH` alohida
#: konstanta, chunki u ikki joyda kerak: dekoratorda va havolada — ikkinchi
#: nusxa qayta nomlashda jimgina eskirib qolardi.
METHODOLOGY_PATH = "/stats/methodology"


def methodology_ref(method: methodology.Methodology, *, region: str) -> MethodologyRefOut:
    """Vitrinadan metodologiyaga havola (`03` §R1.2)."""
    return MethodologyRefOut(
        version=method.version,
        url=f"{settings.api_prefix}{METHODOLOGY_PATH}?region={region}",
    )


def methodology_out(method: methodology.Methodology, *, region: str, lang: str) -> MethodologyOut:
    """`Methodology` → javob modeli. Matn faqat katalogdan (`04` §6)."""
    return MethodologyOut(
        region=region,
        version=method.version,
        title=t(methodology.TITLE_KEY, lang),
        sections=[
            MethodologySectionOut(
                code=section.code,
                spec=section.spec,
                title=t(section.title_key, lang),
                body=t(section.body_key, lang),
                values=[
                    MethodologyValueOut(code=value.code, value=value.value)
                    for value in section.values
                ],
            )
            for section in method.sections
        ],
    )


async def _report(
    session,
    *,
    region: str,
    start: datetime | None,
    end: datetime | None,
) -> stats_service.StatsReport:
    code = region or settings.default_region_code
    row = await geo.find_region(session, code)
    if row is None:
        raise NotFoundError("error.not_found", region=code)
    period = stats_service.resolve_period(start, end)
    report = await stats_service.build_report(
        session, region_id=row.id, region_code=code, period=period
    )
    # `01` §21 `stats_viewed`. Chiqish nuqtasi bitta va u `/stats` bilan
    # `/stats.csv` uchun umumiy: ikkalasi bir xil vitrinaning ikki
    # ko'rinishi, ya'ni ularni alohida sanash «kim ko'rdi» degan savolni
    # «qaysi formatda yukladi» degan savolga almashtirardi.
    #
    # `district_id`/`mahalla_id` — `None`: endpoint butun mintaqani
    # beradi va uning kesimlari javobning **ichida**. Nol qiymat emas,
    # `None`: «filtr yo'q» va «filtr bo'sh natija berdi» bir xil emas.
    analytics.stats_viewed(
        region=report.region_code,
        district_id=None,
        mahalla_id=None,
        period=f"{report.period.start.isoformat()}/{report.period.end.isoformat()}",
    )
    return report


@router.get(
    "/stats",
    response_model=StatsOut,
    summary="Hudud/davr/davomiylik kesimi + Coverage Index",
    responses={404: NOT_FOUND},
)
async def get_stats(
    session: DbSession,
    client_lang: ClientLang,
    region: RegionQuery = "",
    date_from: FromQuery = None,
    date_to: ToQuery = None,
) -> StatsOut:
    report = await _report(session, region=region, start=date_from, end=date_to)
    # `01` §16: standart til — mintaqa atributi (`01` §17), global
    # konstanta emas. `_report` mintaqa kodini allaqachon tekshirgan.
    lang = await registry.language_for(
        session, client=client_lang, region_code=report.region_code
    )
    return StatsOut(
        region=report.region_code,
        period=PeriodOut(
            start=report.period.start.isoformat(),
            end=report.period.end.isoformat(),
            days=report.period.days,
        ),
        total=_bucket_out(report.total),
        districts=[
            DistrictOut(
                district_id=item.district_id,
                code=item.code,
                name=item.name(lang) or t("stats.unassigned", lang),
                stats=_bucket_out(item.bucket),
                coverage=coverage_out(item.index),
                valid_from=None if item.valid_from is None else item.valid_from.isoformat(),
                valid_to=None if item.valid_to is None else item.valid_to.isoformat(),
            )
            for item in report.districts
        ],
        coverage=coverage_out(report.region_index),
        maturity=maturity_out(report.region_maturity),
        boundaries=boundaries_out(report.boundaries),
        mahallas=mahallas_out(report.mahallas, lang=lang),
        methodology=methodology_ref(report.methodology, region=report.region_code),
        suppressed_outages=report.suppressed_outages,
        suppressed_reports=report.suppressed_reports,
        unassigned_ratio=round(report.unassigned_ratio, 4),
        reconciles=report.reconciles,
        truncated=report.truncated,
        warnings=report.warnings,
        warning_texts=[t(key, lang) for key in report.warnings],
    )


@router.get(
    METHODOLOGY_PATH,
    response_model=MethodologyOut,
    summary="Raqamlar qanday hisoblanadi (`03` §R1.2)",
    responses={404: NOT_FOUND},
)
async def get_methodology(
    session: DbSession,
    client_lang: ClientLang,
    region: RegionQuery = "",
) -> MethodologyOut:
    """Metodologiya bo'limi — mintaqaning **jonli** qiymatlari bilan.

    Davr parametri yo'q va bu ataylab: metodologiya kesimga emas,
    mintaqaga tegishli. Uni davrga bog'lash «o'sha davrda qanday
    hisoblangan» degan va'da bo'lardi, tarixiy qiymatlar esa hech
    qayerda saqlanmaydi — `version` aynan shu bo'shliqni ochiq
    ko'rsatadi: eski eksportdagi versiya bugungisidan farq qilsa,
    demak sozlamalar o'zgargan.
    """
    code = region or settings.default_region_code
    row = await geo.find_region(session, code)
    if row is None:
        raise NotFoundError("error.not_found", region=code)
    lang = await registry.language_for(session, client=client_lang, region_code=code)
    method = await stats_service.region_methodology(session, region_id=row.id)
    return methodology_out(method, region=code, lang=lang)


@router.get(
    "/stats.csv",
    response_class=PlainTextResponse,
    summary="O'sha kesimning CSV eksporti",
    responses={404: NOT_FOUND},
)
async def get_stats_csv(
    session: DbSession,
    client_lang: ClientLang,
    region: RegionQuery = "",
    date_from: FromQuery = None,
    date_to: ToQuery = None,
) -> PlainTextResponse:
    report = await _report(session, region=region, start=date_from, end=date_to)
    lang = await registry.language_for(
        session, client=client_lang, region_code=report.region_code
    )
    return PlainTextResponse(
        content=export.render(report, lang=lang),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{export.filename(report)}"',
        },
    )

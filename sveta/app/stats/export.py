"""Statistikaning CSV eksporti (`03` §R1.2 «tarixiy chuqurlik, eksport»).

Modul nomi `csv` emas: paket ichida shunday nom standart kutubxonani
soyalab qo'yardi va bu xatoni topish qiyin bo'lardi.

CSV **JSON javobning aynan o'zi** dan quriladi — ikkinchi so'rov ham,
ikkinchi hisoblash ham yo'q. Aks holda ikki format vaqt o'tishi bilan
ajralib ketardi va «yig'indi umumiy natijaga teng» mezoni faqat birida
bajarilardi.

Har bir qatorda Coverage Index bor: `03` §R1.2 «indeks har vitrinada»
CSV ga ham tegishli — aynan CSV jurnalist qo'liga tushadigan format.
"""

from __future__ import annotations

import csv
import io

from app.core.i18n import t
from app.stats import aggregate, duration, methodology
from app.stats.service import StatsReport

HEADER: tuple[str, ...] = (
    "district_code",
    "district_name",
    "outages_total",
    *(f"outages_{status}" for status in aggregate.REPORTED_STATUSES),
    "reports_total",
    "avg_duration_min",
    # `03` §R1.2 uchinchi kesimi. CSV — jurnalist qo'liga tushadigan
    # format, ya'ni mediana va P90 aynan shu yerda kerak: `01` §4 ularni
    # kuzatiladigan ko'rsatkich deb sanaydi. `ongoing` ustuni ular
    # nimadan hisoblanganini aytadi — ochiq hodisalar namunada yo'q.
    "median_duration_min",
    "p90_duration_min",
    "duration_measured",
    "duration_ongoing",
    "duration_timeout_closed",
    *(f"duration_{code}" for code in duration.BAND_CODES),
    "coverage_index",
    "coverage_band",
    "data_quality",
    # `01` FR-S-803: qator qaysi chegara versiyasiga tegishli. Davr
    # ichida chegara o'zgargan bo'lsa bitta `district_code` ikki marta
    # chiqadi va ularni faqat shu ikki ustun ajratadi.
    "valid_from",
    "valid_to",
)


def _duration_cells(cut: duration.DurationCut) -> list[object]:
    """Davomiylik kesimining CSV kataklari.

    Namuna yetarli bo'lmasa mediana va P90 **bo'sh** katak bo'ladi, nol
    emas: elektron jadval nolni raqam sifatida o'qiydi va «bu hududda
    uzilishlar bir zumda tugagan» degan xulosaga olib kelardi.
    """
    return [
        "" if cut.median_min is None else cut.median_min,
        "" if cut.p90_min is None else cut.p90_min,
        cut.measured,
        cut.ongoing,
        cut.timeout_closed,
        *(cut.bands[code] for code in duration.BAND_CODES),
    ]


def render(report: StatsReport, *, lang: str) -> str:
    """Hisobotni CSV matniga o'giradi (sarlavha + qatorlar + izoh)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(HEADER)

    for item in report.districts:
        statuses = item.bucket.statuses()
        name = item.name(lang) or t("stats.unassigned", lang)
        writer.writerow(
            [
                item.code,
                name,
                item.bucket.outages_total,
                *(statuses[status] for status in aggregate.REPORTED_STATUSES),
                item.bucket.reports_total,
                "" if item.bucket.avg_duration_min is None else item.bucket.avg_duration_min,
                *_duration_cells(item.bucket.duration),
                item.index.index,
                str(item.index.band),
                item.index.data_quality,
                "" if item.valid_from is None else item.valid_from.date().isoformat(),
                "" if item.valid_to is None else item.valid_to.date().isoformat(),
            ]
        )

    total = report.total.statuses()
    writer.writerow(
        [
            "TOTAL",
            t("stats.total", lang),
            report.total.outages_total,
            *(total[status] for status in aggregate.REPORTED_STATUSES),
            report.total.reports_total,
            "" if report.total.avg_duration_min is None else report.total.avg_duration_min,
            *_duration_cells(report.total.duration),
            report.region_index.index,
            str(report.region_index.band),
            report.region_index.data_quality,
            "",
            "",
        ]
    )

    # Dislaymer faylning ichida qoladi: CSV kontekstsiz ko'chiriladi va
    # ogohlantirishsiz raqam aynan `03` §R1.2 ogohlantirgan holat.
    for key in report.warnings:
        writer.writerow([f"# {t(key, lang)}"])

    # Ma'lumot chuqurligi — matn bilan **va** raqam bilan (`01` FR-S-901).
    # Ogohlantirish faqat mintaqa yosh bo'lganda chiqadi, bu ikki qator
    # esa har doim: CSV ni tahlilchi oladi va «qancha vaqtdan beri
    # kuzatilmoqda» degan savolga javobni faylning o'zidan topishi kerak.
    depth = report.region_maturity
    since = "" if depth.observed_since is None else depth.observed_since.date().isoformat()
    writer.writerow([f"# {t('stats.maturity.title', lang)}: {t(depth.message_key, lang)}"])
    writer.writerow(
        [
            f"# observed_since={since} observed_days={depth.observed_days}"
            f" confirmed_events={depth.events}"
            f" min_days={depth.min_days} min_events={depth.min_events}"
        ]
    )

    # Chegaralar spravochnigining versiyasi — `01` US-S5 AC («выгрузка
    # содержит версию справочника границ») va FR-S-803. Ustunlardagi
    # `valid_from`/`valid_to` qator darajasidagi javob, bu qator esa
    # butun fayl darajasidagi: tahlilchi eksportni yillar bo'yicha
    # taqqoslaganda birinchi navbatda shuni ko'radi.
    bounds = report.boundaries
    writer.writerow([f"# {t('stats.boundaries.title', lang)}: {bounds.version or '-'}"])
    writer.writerow(
        [
            f"# boundary_versions={bounds.versions} districts={bounds.districts}"
            f" changed_in_period={'yes' if bounds.changed_in_period else 'no'}"
            f" source={'|'.join(bounds.sources) or '-'}"
            f" license={'|'.join(bounds.licenses) or '-'}"
        ]
    )

    # Mahalla darajasidagi qamrov — `01` §16 ning to'rtinchi qatori.
    # **Ustun emas, izoh:** CSV ning qatori tuman, mahalla esa undan bir
    # daraja past va uni `district_code` ustuniga tiqish faylning
    # yig'indisini buzardi («qator = tuman» qoidasi CSV ning butun
    # ma'nosi, chunki `TOTAL` qatori shu qatorlardan chiqadi). Mahalla
    # kesimini to'liq oladigan format — JSON javobi.
    #
    # Qator **har doim** yoziladi, spravochnik bo'sh bo'lganda ham:
    # `available=no` bu holatda faylning o'zidan o'qiladi va tahlilchi
    # «tumandan pastda ma'lumot yo'q» degan xulosani taxmin qilmaydi
    # (chuqurlik qatorlari bilan bir xil qaror).
    mah = report.mahallas
    bands = " ".join(f"{name}={count}" for name, count in mah.bands.items())
    writer.writerow([f"# {t('stats.mahallas.title', lang)}: {t(mah.index.message_key, lang)}"])
    writer.writerow(
        [
            f"# mahalla_registry={'yes' if mah.available else 'no'}"
            f" mahallas={mah.total} measured={mah.measured}"
            f" coverage_index={mah.index.index} coverage_band={mah.index.band}"
            f" bands[{bands}]"
            f" truncated={'yes' if mah.truncated else 'no'}"
        ]
    )

    # Metodologiya — `03` §R1.2 ning to'rtinchi qatori. CSV aynan shu
    # qatorga muhtoj: JSON javobini o'qigan dastur havolani ochib
    # ko'radi, faylni esa odam **kontekstsiz** oladi — u qaysi usul va
    # qaysi qiymatlar bilan hisoblanganini boshqa hech qayerdan bilmaydi.
    #
    # Bo'limlar to'liq ko'chirilmaydi, faqat **versiya va qiymatlar**:
    # matn ikki tilda va uzun, CSV esa jadval. Versiya ikkita eksportni
    # solishtirish uchun yetarli — qiymatlar o'zgargan bo'lsa u
    # o'zgaradi, tarjima tuzatilgan bo'lsa o'zgarmaydi.
    method = report.methodology
    writer.writerow([f"# {t(methodology.TITLE_KEY, lang)}: {method.version}"])
    for section in method.sections:
        pairs = " ".join(f"{value.code}={value.value}" for value in section.values)
        writer.writerow([f"# {section.code} ({section.spec}) {pairs}"])
    return buffer.getvalue()


def filename(report: StatsReport) -> str:
    start = report.period.start.date().isoformat()
    end = report.period.end.date().isoformat()
    return f"sveta-stats-{report.region_code}-{start}_{end}.csv"

"""Metrika registri va matn eksporti (`05` §10).

`05` §10 yettita metrikani **nom bilan** sanaydi, lekin formatni ham,
kutubxonani ham belgilamaydi. Ikkita qaror shu yerda.

**Yangi bog'liqlik qo'shilmadi.** `04` Stek ro'yxatida `prometheus-client`
yo'q, eksport formati esa (`text/plain; version=0.0.4`) — o'ttiz qatorlik
matn generatori. Kutubxona qo'shish uning registri (protsess ichidagi
global holat) bilan birga kelardi, bu esa quyidagi qarorga zid.

**Metrikalar protsessda emas, bazada yashaydi.** Deyarli hammasi —
so'rov paytida hisoblanadigan qiymat (`outages_open`,
`snapshot_age_seconds`, `outbox_lag_seconds`, `geo_unmatched_ratio`), va
`_total` bilan tugaydiganlar ham jadvaldagi qatorlar soni. Sabab:

* `api` bir necha nusxada ishlashi mumkin — protsess ichidagi hisoblagich
  har nusxada boshqacha bo'lib, scrape qaysi nusxaga tushishiga qarab
  raqam sakrardi;
* qayta ishga tushirish hisoblagichni nolga qaytarardi, jadvaldagi qator
  esa joyida qoladi.

Yagona istisno — `http_requests_total` (`app.obs.counters`): xatolik
darajasini bazadan bilib bo'lmaydi.

Modul **toza**: bazaga ham, FastAPI ga ham bog'liq emas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Barcha metrikalar shu prefiks bilan chiqadi. `05` §10 dagi nomlar
#: prefiksdan keyin **aynan** saqlanadi, shunda hujjatdagi nom bo'yicha
#: qidirish ishlaydi.
PREFIX = "sveta_"

COUNTER = "counter"
GAUGE = "gauge"
#: Chelaklar bilan taqsimot. Oilaning namunalari `_bucket`, `_sum` va
#: `_count` qo'shimchalari bilan chiqadi (`Sample.suffix`), `# HELP` va
#: `# TYPE` esa bitta — bu Prometheus matn formatining talabi.
HISTOGRAM = "histogram"

#: Prometheus matn eksportining versiyasi — `Content-Type` da ko'rsatiladi.
CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


@dataclass(frozen=True)
class Family:
    """Bitta metrika oilasi: nom, tur va izoh (`# HELP` / `# TYPE`)."""

    name: str
    type: str
    help: str

    @property
    def full_name(self) -> str:
        return PREFIX + self.name


@dataclass(frozen=True)
class Sample:
    """Bitta o'lchov. `labels` tartibi chiqishda saqlanadi (barqaror diff).

    `suffix` faqat `HISTOGRAM` uchun (`_bucket`/`_sum`/`_count`). U
    `name` ga qo'shilmaydi, chunki namuna qaysi **oilaga** tegishli
    ekani yo'qolmasligi kerak: `LABEL_EXEMPT` va `PRODUCT_FAMILIES`
    tekshiruvlari aynan `name` bo'yicha yuradi.
    """

    name: str
    value: float
    labels: tuple[tuple[str, str], ...] = field(default=())
    suffix: str = ""


#: `05` §10 jadvali, aynan o'sha tartibda.
REPORTS_RECEIVED = Family(
    "reports_received_total", COUNTER, "Qabul qilingan xabarlar (jami, jadvaldagi qatorlar)"
)
OUTAGES_OPEN = Family("outages_open", GAUGE, "Ochiq hodisalar (pending + confirmed)")
TIME_TO_CONFIRM = Family(
    "time_to_confirm_seconds",
    GAUGE,
    "Birinchi xabardan tasdiqlashgacha o'tgan vaqt, oynadagi kvantillar",
)
TIME_TO_CONFIRM_COUNT = Family("time_to_confirm_count", GAUGE, "Oynada tasdiqlangan hodisalar soni")
SNAPSHOT_AGE = Family("snapshot_age_seconds", GAUGE, "Xarita snapshotining yoshi")
OUTBOX_LAG = Family("outbox_lag_seconds", GAUGE, "Eng eski ishlanmagan outbox qatorining yoshi")
GEO_UNMATCHED = Family(
    "geo_unmatched_ratio", GAUGE, "district_id IS NULL ulushi — poligon sifati signali"
)
NOTIFICATIONS_FAILED = Family(
    "notifications_failed_total", COUNTER, "Yuborib bo'lmagan bildirishnomalar (jami)"
)

#: `05` §10 ro'yxatida yo'q, lekin «xatolik darajasi» ogohlantirishi uchun
#: zarur: uni bazadan bilib bo'lmaydi (`app.obs.counters`).
HTTP_REQUESTS = Family(
    "http_requests_total", COUNTER, "HTTP javoblari status sinfi bo'yicha (protsess ichida)"
)

#: `05` §10 ro'yxatida yo'q. Sababi boshqa hujjatda: `03` §11 R2.0
#: «API p95» ni kuzatishni talab qiladi va `03` §9 Redis ni qaytarishning
#: yagona sharti sifatida o'sha sonni ko'rsatadi (`app.obs.latency`).
#: Metrika qo'shildi, **ogohlantirish qo'shilmadi** — `05` §10 to'rttadan
#: ko'piga ruxsat bermaydi.
HTTP_DURATION = Family(
    "http_request_duration_seconds",
    HISTOGRAM,
    "HTTP javob vaqti yuzalar bo'yicha (protsess ichida)",
)

#: Ogohlantirishning faolligi — `05` §10 ning to'rtta shartidan har biri.
ALERT_ACTIVE = Family("alert_active", GAUGE, "Ogohlantirish faol (1) yoki yo'q (0)")

FAMILIES: tuple[Family, ...] = (
    REPORTS_RECEIVED,
    OUTAGES_OPEN,
    TIME_TO_CONFIRM,
    TIME_TO_CONFIRM_COUNT,
    SNAPSHOT_AGE,
    OUTBOX_LAG,
    GEO_UNMATCHED,
    NOTIFICATIONS_FAILED,
    HTTP_REQUESTS,
    HTTP_DURATION,
    ALERT_ACTIVE,
)

FAMILY_BY_NAME: dict[str, Family] = {f.name: f for f in FAMILIES}


def _escape_help(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\n", "\\n")


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _format_value(value: float) -> str:
    """Butun qiymat kasrsiz chiqadi, qolgani — oltita xona bilan.

    `repr(float)` ba'zi qiymatlarni `1e-05` shaklida berardi; Prometheus uni
    o'qiy oladi, lekin diff va testda o'qish qiyinlashardi.
    """
    if value != value or value in (float("inf"), float("-inf")):
        # NaN/Inf — Prometheus qabul qiladigan yozuv.
        return "NaN" if value != value else ("+Inf" if value > 0 else "-Inf")
    if float(value).is_integer() and abs(value) < 1e15:
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    inner = ",".join(f'{k}="{_escape_label(v)}"' for k, v in labels)
    return "{" + inner + "}"


def render(samples: list[Sample]) -> str:
    """Prometheus matn eksporti (`0.0.4`).

    Oila tartibi `FAMILIES` bo'yicha qat'iy: bir xil holat har doim bir xil
    matn beradi, ya'ni javobni testda ham, `diff` da ham solishtirsa
    bo'ladi. O'lchovi yo'q oila umuman chiqmaydi — `# TYPE` dan keyin bo'sh
    joy qoldirish scrape da «metrika yo'qoldi» degan taassurot berardi,
    holbuki u shunchaki nolga teng emas, balki mavjud emas.
    """
    by_name: dict[str, list[Sample]] = {}
    for sample in samples:
        by_name.setdefault(sample.name, []).append(sample)

    lines: list[str] = []
    for family in FAMILIES:
        rows = by_name.get(family.name)
        if not rows:
            continue
        lines.append(f"# HELP {family.full_name} {_escape_help(family.help)}")
        lines.append(f"# TYPE {family.full_name} {family.type}")
        lines += [
            f"{family.full_name}{r.suffix}{_format_labels(r.labels)} {_format_value(r.value)}"
            for r in rows
        ]
    return "\n".join(lines) + "\n" if lines else ""

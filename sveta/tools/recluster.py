#!/usr/bin/env python3
"""Retrospektiv qayta hisoblash (E6, `05` §9.2, `06` §12.13).

Parametrlar (`06` §9) haqiqiy ma'lumotsiz sozlanmagan. E11 da ular
o'zgaradi va savol tug'iladi: **o'sha paytda nima bo'lardi?** Bu asbob
tarixiy xabarlarni o'zgartirmasdan, ulardan yig'ilgan xulosani —
hodisalarni — qaytadan quradi.

```
xabarlar (o'zgarmaydi)
  → oynadagi hodisalar o'chiriladi
  → xabarlar (created_at, id) tartibida qaytadan `clustering.assign` ga beriladi
  → oxirida har bir hodisa `--to` paytiga qarab qayta baholanadi (autoclose)
```

Ikkita kafolat:

* **Determinizm** (`05` §9.2 regressiya qatlami). Tartib qat'iy, jitter
  allaqachon yozilgan, hisob-kitob toza funksiyalarda — shuning uchun bir
  xil kirish har safar bir xil chiqish beradi. `fingerprint` buni
  o'lchaydigan barmoq izini beradi.
* **Xavfsizlik.** Standart rejim — **quruq yurish**: hammasi haqiqatan
  hisoblanadi, lekin tranzaksiya oxirida bekor qilinadi. Yozish uchun
  `--apply` kerak. Bildirishnoma yuborilgan hodisa bor bo'lsa asbob umuman
  ishlamaydi: foydalanuvchi ko'rgan faktni tarixdan o'chirib bo'lmaydi.

## Ssenariy rejimi (`--set`, `--params`) — E6 ning asosiy va'dasi

`04` §E6: «parametr o'zgarishi tarixiy ma'lumotda qayta hisoblanadi».
Joriy parametrlar bilan qayta hisoblash bu savolning faqat yarmi; ikkinchi
yarmi — **boshqa** parametrlar bilan. `06` §9 ning kalitlaridan biri
`--set confirm.min_users=4` deb berilsa, asbob oynani **ikki marta**
yurgizadi:

1. **Bazaviy** — bazadagi `region_config` bilan;
2. **Variant** — o'sha oyna, ustiga yozilgan parametrlar bilan;

va ikkalasini yonma-yon qo'yadi. Bitta yurishning o'zi «boshqacha chiqdi»
degan xulosaga yetarli emas: taqqoslash uchun ayni o'sha oynadagi bazaviy
natija kerak, aks holda farq parametrdan emas, oynani tanlashdan kelib
chiqqan bo'lishi mumkin.

Ikkala yurish ham **rollback** qilinadi, shuning uchun `--set` bilan
`--apply` ni birga berib bo'lmaydi: parametrni prodda o'zgartirish alohida
qaror va alohida asbob (`tools/region_admin.py config --set`). Tartib —
avval ssenariyni ko'r, keyin parametrni yoz, keyin `--apply` bilan
tarixni qayta qur.

## Sweep rejimi (`--sweep`) — E11 ning savoli

`04` §E11: «parametrlarni haqiqiy ma'lumotda sozlash», mezoni — «qayta
hisoblashda **barqaror** natija». Bitta ssenariy («4 da nima bo'lardi?»)
bu savolga javob bermaydi: sozlash uchun parametrning **butun o'qi**
kerak — qaysi qiymatda natija o'zgaradi, qaysi oraliqda esa umuman
qimirlamaydi.

    --sweep confirm.min_users=2,3,4,5,6

bitta bazaviy yurish va beshta variant yurishini bajaradi (jami olti
marta oyna qayta quriladi — narx qiymatlar soniga **chiziqli**), so'ng
uchta xulosa chiqaradi:

* **burilish nuqtalari** — o'qning qaysi qadamida iz o'zgardi;
* **plato** — iz o'zgarmaydigan oraliq; u yerda parametr hech narsani
  hal qilmaydi va sozlashning ma'nosi yo'q;
* **determinizm** — sweep ro'yxatida joriy (`region_config`) qiymat ham
  bo'lsa, uning izi bazaviy yurishning izi bilan solishtiriladi. Bir xil
  kirishning ikki yurishi turli iz bersa, bu E11 ning mezonini buzadi va
  asbob `EXIT_UNSTABLE` (3) bilan tugaydi — sozlashning o'zi ma'nosiz
  bo'lib qoladi, chunki o'lchov asbobi qimirlab turibdi.

Bitta yurishda **bitta** kalit sweep qilinadi. Sabab dekart ko'paytmasi:
ikkita kalit beshtadan qiymat bilan 25 ta to'liq qayta hisoblashni
beradi, va natijadagi farqni ikki sababdan qay biri keltirib chiqarganini
jadval ko'rsata olmaydi. `--set`/`--params` esa sweep bilan **birga**
beriladi va **fon** bo'lib xizmat qiladi: u bazaviyga ham, har bir
variantga ham qo'llanadi, ya'ni ustundagi farqning sababi baribir bitta
bo'lib qoladi — sweep qilinayotgan kalit.

Misollar:

    python -m tools.recluster --region samarkand --from 2026-08-01 --to 2026-08-08
    python -m tools.recluster --region samarkand --from 2026-08-01 --to 2026-08-08 --apply
    python -m tools.recluster --from 2026-08-01 --to 2026-08-08 \\
        --set confirm.min_users=4 --set confirm.coef=0.6
    python -m tools.recluster --from 2026-08-01 --to 2026-08-08 --params scenario.json
    python -m tools.recluster --from 2026-08-01 --to 2026-08-08 \\
        --sweep confirm.min_users=2,3,4,5,6
    python -m tools.recluster --from 2026-08-01 --to 2026-08-08 \\
        --set scale.coef=0.4 --sweep confirm.coef=0.4,0.5,0.6
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import uuid
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.clustering import repository as cluster_repo  # noqa: E402
from app.clustering import service as clustering  # noqa: E402
from app.clustering.params import DEFAULTS  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.session import dispose_engine, get_sessionmaker  # noqa: E402
from app.geo import pipeline as geo  # noqa: E402
from app.geo import queries as geo_q  # noqa: E402
from app.notifications import queries as notify_q  # noqa: E402
from app.reports import queries as reports_q  # noqa: E402

EXIT_OK = 0
EXIT_BLOCKED = 2
#: Sweep bazaviy qiymatni qayta yurgizdi va **boshqa** iz oldi (`05` §9.2).
#: Alohida kod kerak, chunki bu yagona holat bo'lib, unda hisobotning
#: qolgan hamma qatori to'g'ri ko'rinadi, lekin hech biriga ishonib
#: bo'lmaydi — o'lchov asbobining o'zi qimirlagan.
EXIT_UNSTABLE = 3
EXIT_USAGE = 64


class OverrideError(ValueError):
    """`--set`/`--params` da yaroqsiz parametr — ish boshlanmaydi."""


def parse_override(text: str) -> tuple[str, float]:
    """`kalit=qiymat` → `(kalit, son)`. Noto'g'ri kalit — **xato**, e'tiborsiz emas.

    Nima uchun qat'iy: `confirm.min_user=4` (bitta harf yetishmaydi) jimgina
    o'tkazib yuborilsa, asbob bazaviy yurishni ikki marta bajarib «farq yo'q»
    deb yozardi — E11 da bu parametr ta'sir qilmaydi degan noto'g'ri xulosaga
    olib kelardi. Shuning uchun kalit `06` §9 ro'yxatida bo'lishi shart.
    """
    key, sep, raw = text.partition("=")
    key, raw = key.strip(), raw.strip()
    if not sep or not key or not raw:
        raise OverrideError(f"`kalit=qiymat` kutilgan edi: {text!r}")
    return key, _override_value(key, raw)


def _override_value(key: str, raw: object) -> float:
    if key not in DEFAULTS:
        raise OverrideError(f"`06` §9 da bunday kalit yo'q: {key!r}{_hint(key)}")
    try:
        return float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise OverrideError(f"{key}: son kutilgan edi, {raw!r} keldi") from None


def _hint(key: str) -> str:
    """Yaqin kalitlarni taklif qiladi — xato ko'pincha prefiksda bo'ladi."""
    prefix = key.split(".")[0]
    near = sorted(k for k in DEFAULTS if k.startswith(prefix) or prefix in k)
    return f"; ehtimol: {', '.join(near)}" if near else ""


def coerce_overrides(values: Mapping[str, object]) -> dict[str, float]:
    """`--params` faylidagi lug'atni tekshiradi va sonlarga keltiradi."""
    return {key: _override_value(key, raw) for key, raw in values.items()}


def parse_override_args(items: Sequence[str]) -> dict[str, float]:
    """`--set` ro'yxati. Takrorlangan kalit — xato, **oxirgisi yutmaydi**.

    Sabab: `--set confirm.coef=0.6 --set confirm.coef=0.7` da odam ikkita
    ssenariyni yurgizmoqchi bo'lgan bo'lishi mumkin, jim ravishda
    bittasini tanlash esa hisobotda ko'rinmasdi.
    """
    out: dict[str, float] = {}
    for item in items:
        key, value = parse_override(item)
        if key in out:
            raise OverrideError(f"`--set {key}` ikki marta berilgan")
        out[key] = value
    return out


def load_override_file(path: Path) -> dict[str, float]:
    """`--params`: `{"confirm.min_users": 4}` ko'rinishidagi JSON obyekt."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise OverrideError(f"fayl o'qilmadi: {exc}") from None
    except json.JSONDecodeError as exc:
        raise OverrideError(f"{path}: JSON emas ({exc.msg}, {exc.lineno}-qator)") from None
    if not isinstance(raw, dict):
        raise OverrideError(f"{path}: JSON obyekt kutilgan edi, {type(raw).__name__} keldi")
    return coerce_overrides(raw)


def collect_overrides(*, params_file: Path | None, sets: Sequence[str]) -> dict[str, float]:
    """Fayl + `--set`. To'qnashuvda **buyruq qatori** ustun turadi."""
    merged = load_override_file(params_file) if params_file else {}
    merged.update(parse_override_args(sets))
    return merged


def parse_sweep(text: str) -> tuple[str, list[float]]:
    """`kalit=q1,q2,q3` → `(kalit, [q1, q2, q3])`, o'sish tartibida saralangan.

    Saralash **ataylab**: sweepning uchala xulosasi (burilish nuqtasi,
    plato, monotonlik) qiymatlar o'q bo'ylab tartiblanganini nazarda
    tutadi. `4,2,3` tartibida berilgan ro'yxatda «oldingi qiymat»
    tushunchasi ma'nosini yo'qotardi. Hech narsa yashirilmaydi: jadval
    qiymatlarni o'zi ko'rsatadi.

    Ikkitadan kam qiymat — xato: bitta qiymat bu `--set`, va u yerda
    taqqoslash allaqachon bor. Takrorlangan qiymat ham xato: jimgina
    tashlab yuborilsa, hisobotdagi qatorlar soni so'ralganidan kam
    bo'lardi.
    """
    key, sep, raw = text.partition("=")
    key, raw = key.strip(), raw.strip()
    if not sep or not key or not raw:
        raise OverrideError(f"`kalit=q1,q2,…` kutilgan edi: {text!r}")
    parts = [part.strip() for part in raw.split(",")]
    if any(not part for part in parts):
        raise OverrideError(f"{key}: bo'sh qiymat berilgan ({raw!r})")
    values = [_override_value(key, part) for part in parts]
    if len(values) < 2:
        raise OverrideError(
            f"{key}: sweep uchun kamida ikkita qiymat kerak — bitta qiymat bu `--set`"
        )
    seen = sorted({v for v in values if values.count(v) > 1})
    if seen:
        raise OverrideError(f"{key}: qiymat takrorlangan ({', '.join(_num_text(v) for v in seen)})")
    return key, sorted(values)


@dataclass(frozen=True)
class Summary:
    """Oynadagi hodisalarning mazmunli kesimi — taqqoslash uchun.

    `fingerprint` «bir xilmi?» degan savolga javob beradi, bu esa
    «nimasi bilan farq qiladi?» degan savolga. E11 da ikkalasi ham kerak:
    iz o'zgargani parametr ta'sir qilganini bildiradi, yo'nalishini esa
    faqat shu sonlar ko'rsatadi.
    """

    outages: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    by_scale: dict[str, int] = field(default_factory=dict)
    mean_confidence: float = 0.0
    mean_radius_m: float = 0.0

    @property
    def confirmed(self) -> int:
        return self.by_status.get("confirmed", 0)

    @classmethod
    def of(cls, rows: Sequence[cluster_repo.OutageFingerprintRow]) -> Summary:
        if not rows:
            return cls()
        by_status: dict[str, int] = {}
        by_scale: dict[str, int] = {}
        for r in rows:
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_scale[r.scale] = by_scale.get(r.scale, 0) + 1
        return cls(
            outages=len(rows),
            by_status=dict(sorted(by_status.items())),
            by_scale=dict(sorted(by_scale.items())),
            mean_confidence=round(sum(r.confidence for r in rows) / len(rows), 2),
            mean_radius_m=round(sum(r.radius_m for r in rows) / len(rows), 1),
        )


@dataclass(frozen=True)
class Result:
    """Qayta hisoblash natijasi — hisobot va regressiya sinovi uchun."""

    region_code: str
    since: datetime
    until: datetime
    reports: int
    detached: int
    deleted_outages: int
    created_outages: int
    unassigned: int
    #: `geom_exact` i `NULL` ga o'tgan xabarlar (`05` §3.2) — ular uchun
    #: qayta hisoblash jitterlangan nuqta bilan, ya'ni qo'polroq bajarildi.
    degraded_reports: int
    fingerprint: str
    applied: bool
    #: Natijaning mazmunli kesimi (`Summary`). Standart bo'sh — eski
    #: chaqiruvchilar va testlar uni bermasligi mumkin.
    summary: Summary = field(default_factory=Summary)

    @property
    def degraded_ratio(self) -> float:
        return self.degraded_reports / self.reports if self.reports else 0.0

    @property
    def warning(self) -> str | None:
        """Aniqligi pasaygan davr haqida ogohlantirish.

        Jimgina o'tkazib yuborish eng xavfli variant bo'lardi: natija
        onlayn tarixdan farq qiladi va sababi hisobotda ko'rinmasdi.
        """
        if not self.degraded_reports:
            return None
        return (
            f"diqqat: {self.degraded_reports} ta xabar ({self.degraded_ratio:.0%}) "
            "faqat jitterlangan nuqta bilan hisoblandi — `geom_exact` 90 kundan "
            "keyin NULL ga o'tadi (05 §3.2). Bu davrda markaz va radius qo'polroq."
        )

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["since"] = self.since.isoformat()
        data["until"] = self.until.isoformat()
        data["degraded_ratio"] = round(self.degraded_ratio, 4)
        data["warning"] = self.warning
        return data


@dataclass(frozen=True)
class Comparison:
    """Bazaviy va variant yurishlari yonma-yon (`04` §E6).

    Ikkalasi ham **bir xil oynada** va bir xil xabarlar ustida bajariladi,
    farq faqat parametrlarda — shuning uchun har qanday o'zgarish
    parametrga tegishli deb o'qilishi mumkin.
    """

    baseline: Result
    variant: Result
    overrides: dict[str, float]

    @property
    def changed(self) -> bool:
        """Iz o'zgardimi. `False` — parametr bu oynada hech narsani hal qilmagan."""
        return self.baseline.fingerprint != self.variant.fingerprint

    @property
    def delta(self) -> dict[str, float]:
        """Variant − bazaviy. Musbat son «variantda ko'proq» degani."""
        b, v = self.baseline.summary, self.variant.summary
        return {
            "outages": v.outages - b.outages,
            "confirmed": v.confirmed - b.confirmed,
            "unassigned": self.variant.unassigned - self.baseline.unassigned,
            "mean_confidence": round(v.mean_confidence - b.mean_confidence, 2),
            "mean_radius_m": round(v.mean_radius_m - b.mean_radius_m, 1),
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "overrides": dict(sorted(self.overrides.items())),
            "changed": self.changed,
            "baseline": self.baseline.as_dict(),
            "variant": self.variant.as_dict(),
            "delta": self.delta,
        }


def render_comparison(cmp: Comparison) -> str:
    """Odam o'qiydigan jadval. JSON dan tashqari, chunki ssenariyni odam baholaydi."""
    b, v = cmp.baseline.summary, cmp.variant.summary
    lines = [
        "Parametr ssenariysi (ikkala yurish ham quruq — hech narsa yozilmadi)",
        "",
        *(
            f"  {k} = {_num_text(val)}   (bazaviy: {_num_text(DEFAULTS[k])} yoki region_config)"
            for k, val in sorted(cmp.overrides.items())
        ),
        "",
        f"  {'':<18}{'bazaviy':>10}{'variant':>10}{'farq':>10}",
        _row("hodisalar", b.outages, v.outages),
        _row("tasdiqlangan", b.confirmed, v.confirmed),
        _row("biriktirilmagan", cmp.baseline.unassigned, cmp.variant.unassigned),
        _row("o'rtacha ishonch", b.mean_confidence, v.mean_confidence),
        _row("o'rtacha radius, m", b.mean_radius_m, v.mean_radius_m),
        "",
        f"  iz: {cmp.baseline.fingerprint[:12]} → {cmp.variant.fingerprint[:12]}",
    ]
    lines.append(
        "  ⚠️  natija o'zgarmadi — bu oynada parametr hech narsani hal qilmaydi"
        if not cmp.changed
        else "  natija o'zgardi"
    )
    return "\n".join(lines)


def _num_text(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


def _row(label: str, base: float, variant: float) -> str:
    diff = round(variant - base, 2)
    sign = "+" if diff > 0 else ""
    return f"  {label:<18}{_num_text(base):>10}{_num_text(variant):>10}{sign + _num_text(diff):>10}"


@dataclass(frozen=True)
class SweepPoint:
    """O'qning bitta qadami: qiymat va o'sha qiymatdagi to'liq yurish."""

    value: float
    result: Result
    #: Bazaviy yurishdan (ya'ni `region_config` + fon dan) farq qiladimi.
    changed_from_baseline: bool
    #: O'qdagi **oldingi** qadamdan farq qiladimi. Birinchi qadamda `None`:
    #: «oldingi yo'q» va «oldingisi bilan bir xil» — turli xabar.
    changed_from_previous: bool | None

    def as_dict(self) -> dict[str, object]:
        return {
            "value": self.value,
            "changed_from_baseline": self.changed_from_baseline,
            "changed_from_previous": self.changed_from_previous,
            "run": self.result.as_dict(),
        }


@dataclass(frozen=True)
class Sweep:
    """Bitta parametr bo'ylab o'q (`04` §E11).

    Bazaviy **bir marta** yurgiziladi va hamma qadam u bilan
    solishtiriladi: oyna ham, xabarlar ham bir xil, shuning uchun uni har
    qadamda takrorlash o'sha ishni bekorga qilish bo'lardi. Bazaviyning
    o'zi qayta yurgizilganda o'zgarmasligi — alohida tekshiruv
    (`stable`), va u faqat ro'yxatda joriy qiymat bo'lganda bajariladi.
    """

    key: str
    baseline: Result
    #: `region_config` (yoki `DEFAULTS`) dagi joriy qiymat — o'qda qayerda
    #: turganimizni ko'rsatadi.
    baseline_value: float
    points: list[SweepPoint]
    #: Har yurishga (bazaviysiga ham) qo'llangan `--set`/`--params` fon.
    background: dict[str, float] = field(default_factory=dict)

    @property
    def turning_points(self) -> list[float]:
        """Iz aynan shu qadamda o'zgargan qiymatlar — sozlash shu yerda."""
        return [p.value for p in self.points if p.changed_from_previous]

    @property
    def plateaus(self) -> list[tuple[float, float]]:
        """Iz o'zgarmaydigan ketma-ket oraliqlar (`(boshi, oxiri)`).

        Ikki qadamdan qisqa oraliq plato emas: har bir yakka qiymat
        o'z-o'zicha «o'zgarmagan» bo'lishi mumkin, lekin bu parametr
        ishlamayotganini ko'rsatmaydi.
        """
        out: list[tuple[float, float]] = []
        start = 0
        for idx in range(1, len(self.points) + 1):
            ends = idx == len(self.points) or self.points[idx].changed_from_previous
            if ends:
                if idx - start >= 2:
                    out.append((self.points[start].value, self.points[idx - 1].value))
                start = idx
        return out

    @property
    def confirmed_direction(self) -> str:
        """`tasdiqlangan` sonining o'q bo'ylab yo'nalishi.

        `aralash` — kutilmagan holat: chegara parametri odatda tasdiqni
        bir tomonga suradi. Bu **kuzatuv**, verdikt emas; sababi haqiqiy
        ma'lumotda (masshtab to'sig'i, qamrov) bo'lishi mumkin.
        """
        return _direction([p.result.summary.confirmed for p in self.points])

    @property
    def stable(self) -> bool | None:
        """Bazaviy qiymat qayta yurgizilganda o'sha izni berdimi.

        `None` — ro'yxatda joriy qiymat yo'q, ya'ni tekshirilmadi.
        """
        for point in self.points:
            if point.value == self.baseline_value:
                return point.result.fingerprint == self.baseline.fingerprint
        return None

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "baseline_value": self.baseline_value,
            "background": dict(sorted(self.background.items())),
            "turning_points": self.turning_points,
            "plateaus": [list(span) for span in self.plateaus],
            "confirmed_direction": self.confirmed_direction,
            "stable": self.stable,
            "baseline": self.baseline.as_dict(),
            "points": [p.as_dict() for p in self.points],
        }


def _direction(values: Sequence[float]) -> str:
    """`o'zgarmaydi` / `kamaymaydi` / `o'smaydi` / `aralash`."""
    steps = list(zip(values, values[1:], strict=False))
    up = any(b > a for a, b in steps)
    down = any(b < a for a, b in steps)
    if up and down:
        return "aralash"
    if up:
        return "kamaymaydi"
    if down:
        return "o'smaydi"
    return "o'zgarmaydi"


def render_sweep(sweep: Sweep) -> str:
    """Odam o'qiydigan o'q. Sozlash qarorini odam qabul qiladi, asbob emas."""
    b = sweep.baseline
    lines = [
        f"Parametr sweepi: {sweep.key} (hamma yurish quruq — hech narsa yozilmadi)",
        "",
    ]
    if sweep.background:
        lines.append(
            "  fon (bazaviyga ham qo'llandi): "
            + ", ".join(f"{k} = {_num_text(v)}" for k, v in sorted(sweep.background.items()))
        )
        lines.append("")
    lines += [
        f"  bazaviy: {sweep.key} = {_num_text(sweep.baseline_value)}"
        f"   hodisalar {b.summary.outages}, tasdiqlangan {b.summary.confirmed},"
        f" iz {b.fingerprint[:12]}",
        "",
        f"  {'qiymat':>10}{'hodisalar':>11}{'tasdiq.':>9}{'biriktir.siz':>13}"
        f"{'ishonch':>9}  {'iz':<12}  izoh",
    ]
    for point in sweep.points:
        lines.append(_sweep_row(point, sweep))
    lines.append("")
    lines.append(
        f"  burilish nuqtalari: {', '.join(_num_text(v) for v in sweep.turning_points)}"
        if sweep.turning_points
        else "  ⚠️  burilish nuqtasi yo'q — o'qning hech bir qadamida iz o'zgarmadi"
    )
    for start, end in sweep.plateaus:
        lines.append(
            f"  plato {_num_text(start)}…{_num_text(end)} — bu oraliqda "
            "parametr hech narsani hal qilmaydi"
        )
    lines.append(f"  tasdiqlangan soni o'q bo'ylab: {sweep.confirmed_direction}")
    lines.append(_stability_line(sweep))
    return "\n".join(lines)


def _sweep_row(point: SweepPoint, sweep: Sweep) -> str:
    s = point.result.summary
    is_baseline_value = point.value == sweep.baseline_value
    mark = " ←bazaviy" if is_baseline_value else ""
    if point.changed_from_previous is None:
        note = "boshlanish"
    elif point.changed_from_previous:
        note = "o'zgardi"
    else:
        note = "= oldingi"
    # Joriy qiymatdagi qator uchun «bazaviy bilan bir xil» — takror: u
    # aynan determinizm tekshiruvi va pastda alohida qator bilan
    # chiqariladi. Qolgan qatorlarda esa bu mustaqil xabar: qiymat
    # o'zgardi, natija esa joriy holatga qaytdi.
    if not point.changed_from_baseline and not is_baseline_value:
        note += ", bazaviy bilan bir xil"
    return (
        f"  {_num_text(point.value) + mark:>10}{s.outages:>11}{s.confirmed:>9}"
        f"{point.result.unassigned:>13}{s.mean_confidence:>9}  "
        f"{point.result.fingerprint[:12]:<12}  {note}"
    )


def _stability_line(sweep: Sweep) -> str:
    if sweep.stable is None:
        return (
            f"  ℹ️  determinizm tekshirilmadi — ro'yxatga joriy qiymatni "
            f"({_num_text(sweep.baseline_value)}) qo'shsangiz tekin tekshiriladi"
        )
    if sweep.stable:
        return (
            f"  ✅ determinizm: {_num_text(sweep.baseline_value)} qiymati "
            "qayta yurgizilganda o'sha izni berdi"
        )
    return (
        f"  ❌ BARQAROR EMAS: {_num_text(sweep.baseline_value)} qiymati bazaviy "
        "bilan bir xil, lekin izi boshqa — jadvalning qolgan qatorlariga "
        "ishonib bo'lmaydi (`05` §9.2)"
    )


class ReclusterBlocked(RuntimeError):
    """Qayta hisoblash xavfsiz emas — sabab bilan to'xtatiladi."""


@asynccontextmanager
async def _scope(*, apply: bool) -> AsyncIterator[AsyncSession]:
    """Tranzaksiya: `--apply` bo'lsa commit, aks holda **har doim** rollback.

    Quruq yurish ham haqiqiy hisob-kitobni bajaradi — «nima bo'lardi»
    degan savolga taxmin bilan emas, natija bilan javob beriladi.
    """
    async with get_sessionmaker()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        if apply:
            await session.commit()
        else:
            await session.rollback()


def fingerprint(rows: list[cluster_repo.OutageFingerprintRow]) -> str:
    """Natijaning barqaror barmoq izi (`05` §9.2).

    `uuid` va vaqt tamg'alari emas, **mazmun** hashlanadi: status, markaz,
    radius, ishonch, masshtab va og'irlikli ball. Ikki yurish bir xil izni
    bersa — algoritm determinik.
    """
    payload = [
        [
            r.started_at.isoformat(),
            r.status,
            f"{r.lat:.7f}",
            f"{r.lon:.7f}",
            r.radius_m,
            r.confidence,
            r.scale,
            f"{r.weighted_score:.1f}",
        ]
        for r in rows
    ]
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.blake2b(blob, digest_size=16).hexdigest()


async def recluster(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    region_code: str,
    since: datetime,
    until: datetime,
    applied: bool,
    overrides: Mapping[str, float] | None = None,
) -> Result:
    """Oynani qaytadan klasterlaydi. Chaqiruvchi tranzaksiyani boshqaradi.

    `overrides` berilsa, u **shu tranzaksiya ichida** `region_config` ga
    yoziladi. Parametrni `assign`/`evaluate` ga argument sifatida uzatish
    o'rniga shunday qilinadi, chunki `app.clustering` ni parametrni
    bazadan o'qishi (`_load_params`) — `06` §9 ning qoidasi; asbob uchun
    ikkinchi yo'l ochish o'sha qoidadan chetlanish bo'lardi va onlayn
    yo'l bilan ssenariy yo'li ajralib ketardi. Quruq yurishda yozuv
    rollback bilan yo'qoladi.
    """
    if overrides:
        await geo_q.override_region_config(session, region_id, dict(overrides))
    doomed = await cluster_repo.outage_ids_started_in(
        session, region_id=region_id, since=since, until=until
    )
    notified = await notify_q.count_for_outages(session, doomed)
    if notified:
        raise ReclusterBlocked(
            f"oynadagi {notified} ta bildirishnoma hodisaga bog'langan — "
            "yuborilgan xabarnoma tarixdan o'chirilmaydi"
        )

    rows = await reports_q.reports_for_replay(
        session, region_id=region_id, since=since, until=until
    )
    detached = await reports_q.detach_window(session, region_id=region_id, since=since, until=until)
    deleted = await cluster_repo.delete_outages(session, doomed)

    created: set[uuid.UUID] = set()
    unassigned = 0
    for row in rows:
        assignment = await clustering.assign(
            session,
            clustering.ReportRef(
                id=row.id,
                user_id=row.user_id,
                kind=row.kind,
                lat=row.lat,
                lon=row.lon,
                region_id=row.region_id,
                district_id=row.district_id,
                mahalla_id=row.mahalla_id,
                created_at=row.created_at,
                source_code=row.source_code,
            ),
        )
        if assignment.outage_id is None:
            unassigned += 1
        elif assignment.created:
            created.add(assignment.outage_id)

    # Oxirgi qadam — oyna oxiridagi holat: jim qolgan hodisalar `autoclose`
    # bo'yicha yopiladi (`05` §4.4). Onlaynda buni fon vazifasi qiladi.
    for outage_id in await cluster_repo.outage_ids_started_in(
        session, region_id=region_id, since=since, until=until
    ):
        await clustering.evaluate(session, outage_id, now=until)

    await session.flush()
    rows_out = await cluster_repo.fingerprint_rows(
        session, region_id=region_id, since=since, until=until
    )
    return Result(
        region_code=region_code,
        since=since,
        until=until,
        reports=len(rows),
        detached=detached,
        deleted_outages=deleted,
        created_outages=len(created),
        unassigned=unassigned,
        degraded_reports=sum(1 for r in rows if not r.has_exact),
        fingerprint=fingerprint(rows_out),
        applied=applied,
        summary=Summary.of(rows_out),
    )


def parse_moment(value: str) -> datetime:
    """`YYYY-MM-DD` yoki to'liq ISO vaqt. Zona ko'rsatilmasa — UTC."""
    moment = datetime.fromisoformat(value)
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


class _RegionMissing(RuntimeError):
    """Mintaqa kodi topilmadi — ikkala yurish ham boshlanmaydi."""


async def _one_run(
    args: argparse.Namespace, *, overrides: Mapping[str, float], apply: bool
) -> Result:
    """Bitta to'liq yurish: o'z tranzaksiyasi, o'z sessiyasi."""
    async with _scope(apply=apply) as session:
        region = await geo.find_region(session, args.region)
        if region is None:
            raise _RegionMissing(args.region)
        return await recluster(
            session,
            region_id=region.id,
            region_code=region.code,
            since=args.since,
            until=args.until,
            applied=apply,
            overrides=overrides,
        )


async def _effective_value(args: argparse.Namespace, key: str) -> float:
    """`region_config` dagi joriy qiymat, yo'q bo'lsa `DEFAULTS` (`06` §9).

    Bazaviy yurishning natijasidan uni tiklab bo'lmaydi — natija sonlar
    beradi, parametrni emas — shuning uchun alohida o'qiladi.
    """
    async with _scope(apply=False) as session:
        region = await geo.find_region(session, args.region)
        if region is None:
            raise _RegionMissing(args.region)
        config = await geo_q.load_region_config(session, region.id)
        return float(config.get(key, DEFAULTS[key]))


def assemble_points(
    values: Sequence[float], results: Sequence[Result], *, baseline: Result
) -> list[SweepPoint]:
    """Yurish natijalarini o'qqa tizadi: har qadam ikki tomonga solishtiriladi.

    Bazadan ajratilgan, chunki sweepning **hamma** xulosasi (burilish
    nuqtasi, plato, determinizm) aynan shu ikki bayroqdan chiqadi va ular
    Postgres bo'lmaganda ham tekshirilishi kerak.
    """
    points: list[SweepPoint] = []
    previous: str | None = None
    for value, result in zip(values, results, strict=True):
        points.append(
            SweepPoint(
                value=value,
                result=result,
                changed_from_baseline=result.fingerprint != baseline.fingerprint,
                changed_from_previous=None if previous is None else result.fingerprint != previous,
            )
        )
        previous = result.fingerprint
    return points


async def run_sweep(
    args: argparse.Namespace, *, key: str, values: Sequence[float], background: Mapping[str, float]
) -> Sweep:
    """Bitta bazaviy + har qiymat uchun bitta variant yurishi."""
    baseline_value = await _effective_value(args, key)
    baseline = await _one_run(args, overrides=dict(background), apply=False)
    results = [
        await _one_run(args, overrides={**background, key: value}, apply=False) for value in values
    ]
    return Sweep(
        key=key,
        baseline=baseline,
        baseline_value=baseline_value,
        points=assemble_points(values, results, baseline=baseline),
        background=dict(background),
    )


async def cmd_recluster(args: argparse.Namespace) -> int:
    if args.until <= args.since:
        print("`--to` `--from` dan katta bo'lishi kerak", file=sys.stderr)
        return EXIT_USAGE

    try:
        overrides = collect_overrides(params_file=args.params, sets=args.sets)
        sweep_key, sweep_values = parse_sweep(args.sweep) if args.sweep else (None, [])
    except OverrideError as exc:
        print(f"parametr xatosi: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if sweep_key is not None and sweep_key in overrides:
        print(
            f"`--sweep {sweep_key}` va `--set {sweep_key}` birga berilmaydi: fon "
            "har yurishda o'zgarmasligi kerak, aks holda ustundagi farqning "
            "ikkita sababi bo'lardi.",
            file=sys.stderr,
        )
        return EXIT_USAGE

    if sweep_key is not None and args.apply:
        print(
            "`--sweep` bilan `--apply` birga berilmaydi: sweep bitta emas, bir "
            "necha natijani hisoblaydi va ularning qaysi biri tarixga yozilishi "
            "kerakligini asbob hal qilmaydi. Tartib — sweepni ko'ring, keyin "
            "`python -m tools.region_admin config --set …`, keyin `--apply`.",
            file=sys.stderr,
        )
        return EXIT_USAGE

    if overrides and args.apply:
        print(
            "`--set`/`--params` bilan `--apply` birga berilmaydi: ssenariy "
            "prod konfiguratsiyasini o'zgartirmaydi. Tartib — ssenariyni "
            "ko'ring, keyin `python -m tools.region_admin config --set …`, "
            "keyin `--apply` bilan tarixni qayta quring.",
            file=sys.stderr,
        )
        return EXIT_USAGE

    sweep: Sweep | None = None
    try:
        if sweep_key is not None:
            sweep = await run_sweep(args, key=sweep_key, values=sweep_values, background=overrides)
            report: Result = sweep.baseline
            payload: dict[str, object] = sweep.as_dict()
        elif overrides:
            baseline = await _one_run(args, overrides={}, apply=False)
            variant = await _one_run(args, overrides=overrides, apply=False)
            report = variant
            payload = Comparison(baseline, variant, dict(overrides)).as_dict()
        else:
            report = await _one_run(args, overrides={}, apply=args.apply)
            payload = report.as_dict()
    except ReclusterBlocked as exc:
        print(f"to'xtatildi: {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    except _RegionMissing as exc:
        print(f"mintaqa topilmadi: {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if report.warning:
        print(f"\n{report.warning}", file=sys.stderr)
    if sweep is not None:
        print()
        print(render_sweep(sweep))
        return EXIT_OK if sweep.stable is not False else EXIT_UNSTABLE
    if overrides:
        print()
        print(render_comparison(Comparison(baseline, variant, dict(overrides))))
    elif not args.apply:
        print("\nQuruq yurish — hech narsa yozilmadi. Yozish uchun `--apply`.")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="recluster", description=__doc__)
    parser.add_argument("--region", default=settings.default_region_code, help="regions.code")
    parser.add_argument(
        "--from", dest="since", type=parse_moment, required=True, help="oyna boshi (ISO)"
    )
    parser.add_argument(
        "--to", dest="until", type=parse_moment, required=True, help="oyna oxiri (ISO, kirmaydi)"
    )
    parser.add_argument(
        "--apply", action="store_true", help="natijani yozish (standart — quruq yurish)"
    )
    parser.add_argument(
        "--set",
        dest="sets",
        action="append",
        default=[],
        metavar="KALIT=QIYMAT",
        help=f"`06` §9 parametrini almashtirish; bir necha marta berilishi mumkin "
        f"({len(DEFAULTS)} ta kalit, masalan `confirm.min_users=4`)",
    )
    parser.add_argument(
        "--params",
        type=Path,
        default=None,
        metavar="FAYL.json",
        help="o'sha parametrlar JSON obyekt sifatida; `--set` undan ustun turadi",
    )
    parser.add_argument(
        "--sweep",
        default=None,
        metavar="KALIT=Q1,Q2,…",
        help="bitta parametrni bir necha qiymatda ketma-ket yurgizish (E11); "
        "`--set`/`--params` fon bo'lib qoladi, `--apply` bilan birga berilmaydi",
    )
    parser.set_defaults(func=cmd_recluster)
    return parser


async def _main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return await args.func(args)
    finally:
        await dispose_engine()


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())

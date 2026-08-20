"""TZ §12 ning yagona hisoboti — poroglar erishuvchanmi.

§12 ni TZ **yagona majburiy** tekshiruv deb ataydi va butun §2 dan
oldinga qo'yadi. Uning ikkita yarmi bor va ular har xil manbadan
javob oladi:

| Yarmi | Savoli | Manbasi | Moduli |
|---|---|---|---|
| asosiy | §2.1 ning **odam** poroglari tarixda yig'ilganmi | tarix | `tzreach` |
| «Дополнительно» | §3 ning zona poroglari umuman yig'iladimi | reyestrlar | `tzcoverage` |

193- va 194-runlar ikkala modulni qurdi, lekin **chaqiruvchisiz**:
`grep` `app/` da ikkalasiga ham birorta murojaat topmaydi. O'lchov
asbobi chaqiruvchisiz — o'lchov emas, imkoniyat. Bu skript o'sha
chaqiruvchi: bitta buyruq, bitta hisobot, bitta chiqish kodi.

```
python -m tools.tz_check --region samarkand --since 2026-01-01 --min-episodes 10
python -m tools.tz_check --region samarkand --since 2026-01-01 --min-episodes 10 --json
```

## 🔴 Kesim sanasi javobni o'zgartirishi mumkin va buni **o'lchash** kerak

`tzreach.load()` butun tarix uchun **bitta** `account_created_before`
oladi, mahsulot esa uni har hodisada qaytadan hisoblaydi
(`now - reporter_min_account_age_min`, `clustering/service.py`).
Ya'ni tarixiy o'lchovda bu qiymatni tanlash — javobni tanlash:

* `until - yosh` (kech kesim) tarixning **boshidagi** hodisada
  mahsulot rad etgan akkauntlarni ham qabul qiladi → guvohlar
  ko'proq → poroglar **erishuvchanroq** ko'rinadi;
* `since - yosh` (erta kesim) esa aksincha — tarixning oxiridagi
  hodisada mahsulot qabul qilgan akkauntlarni rad etadi → poroglar
  **yuqoriroq** ko'rinadi.

Bittasini tanlab qo'yish §12 ni aynan o'zi so'ragan tomonga
og'dirardi: kech kesim «пороги не завышены» degan javobni jimgina
qulaylashtiradi. Shuning uchun skript o'lchovni **ikki marta**
yuritadi va ikkala javobni ham chop etadi. Ular bir xil bo'lsa —
kesim qaror qabul qilmagan, son dalil. Farq qilsa — son dalil emas,
**artefakt**, va bu `reach.cutoff_decides` topilmasi bilan
nomlanadi. Narxi — so'rovlar ikki barobar; §12 oflayn va umuman bir
marta yuritiladi («занимает день работы с выгрузкой»), shuning uchun
narx qabul qilinadi.

## 🔴 «O'lchanmadi» — «o'tdi» emas

`tzreach` bugungi bazada `UNKNOWN`/`NO_INDEPENDENT_TRUTH` qaytaradi
(mustaqil dalili bor hodisa yo'q), `tzcoverage` esa foydalanuvchisi
bor kvartal bo'lmasa `UNKNOWN` beradi. Ikkala holatda ham `levels` /
sonlar **bo'sh** — modullar sonlarni o'ylab topmaydi. Agar chiqish
kodi bunda `0` bo'lsa, «hech qanday topilma yo'q» bilan «hech narsa
o'lchanmadi» bir xil ko'rinardi — bu loyihada bir necha marta
uchragan mina (bo'sh jadval, bo'sh sukut, nol maxraj). Shuning uchun
alohida kod:

| Kod | Ma'nosi |
|---|---|
| `0` | ikkala yarmi ham o'lchandi, topilma yo'q |
| `1` | hisobot **qurilmadi** (mintaqa yo'q, sozlanmagan, argument xato) |
| `2` | o'lchandi va topilma bor — hisobotni o'qish shart |
| `3` | yarmi (yoki ikkalasi) **o'lchanmadi** |

Ustunlik `3 > 2 > 0`: «topilma bor» degan kod qolgan hamma narsa
o'lchandi degan ma'noni beradi, yarmi o'lchanmaganda esa bu ma'no
yolg'on bo'lardi.

## Nima yozilmaydi

Skript **hech narsa yozmaydi** — na bazaga, na `region_config` ga.
§12 ishlab chiqishdan **oldingi** tekshiruv: uning javobi §7 ning
sonlarini o'zgartirishi mumkin, lekin o'zgartirishni odam
`seed_tz_config` orqali qiladi va u `config_journal` da ko'rinadi.
Avtomatik tuzatish o'lchovni o'z natijasiga bog'lardi.

Matn i18n katalogidan olinmaydi va olinmasligi kerak: §12
foydalanuvchiga chiqmaydi, u ishlab chiquvchining asbobi.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import tzcoverage, tzreach
from app.clustering.service import KIND_OUTAGE
from app.clustering.tzcount import Level
from app.core import tzconfig
from app.core.config import settings
from app.db.session import session_scope
from app.geo import queries as geo_q
from app.geo.models import Region


class Status(StrEnum):
    """Hisobotning yakuniy holati. Chiqish kodi shundan olinadi."""

    #: Ikkala yarmi ham o'lchandi, topilma yo'q.
    CLEAN = "clean"
    #: O'lchandi va e'tibor talab qiladigan narsa topildi.
    FINDINGS = "findings"
    #: Kamida bitta yarmi o'lchanmadi — sonlar yo'q.
    UNMEASURED = "unmeasured"


#: Holat → chiqish kodi. `1` bu jadvalda **yo'q**: u hisobot umuman
#: qurilmagan holat, ya'ni holatning qiymati emas, uning yo'qligi.
EXIT_CODE: Mapping[Status, int] = {
    Status.CLEAN: 0,
    Status.FINDINGS: 2,
    Status.UNMEASURED: 3,
}

#: Argument yoki muhit xatosi.
EXIT_ERROR = 1


@dataclass(frozen=True)
class Finding:
    """Bitta topilma — kodi va u tegishli bo'lgan narsa.

    `code` barqaror: hisobotni skript o'qishi mumkin. `subject`
    bo'sh bo'lishi mumkin (butun mintaqaga tegishli topilmalarda).
    """

    code: str
    subject: str = ""

    def __str__(self) -> str:
        return f"{self.code}:{self.subject}" if self.subject else self.code


@dataclass(frozen=True)
class Cutoffs:
    """Akkaunt yoshi kesimining ikkita chekkasi (modul izohi, birinchi 🔴)."""

    #: Konservativ: tarix boshidan yosh chegarasi olib tashlangan.
    early: datetime
    #: Erkin: tarix oxiridan.
    late: datetime
    #: Qaysi sondan yasalgani — hisobotda ko'rinsin.
    min_account_age_min: int


def cutoffs(since: datetime, until: datetime, *, min_account_age_min: int) -> Cutoffs:
    """Oynadan ikkita kesim sanasi. Toza: bazani ko'rmaydi.

    `until <= since` — xato, `ValueError`. Teskari oyna nol hodisa
    beradi va u `NO_HISTORY` ga o'xshab ko'rinardi, ya'ni argument
    xatosi ma'lumot haqidagi xulosaga aylanardi.
    """
    if until <= since:
        raise ValueError(
            f"oyna bo'sh yoki teskari: since={since.isoformat()} until={until.isoformat()}"
        )
    if min_account_age_min < 0:
        raise ValueError(f"akkaunt yoshi manfiy bo'lolmaydi: {min_account_age_min}")
    age = timedelta(minutes=min_account_age_min)
    return Cutoffs(early=since - age, late=until - age, min_account_age_min=min_account_age_min)


@dataclass(frozen=True)
class ReachPair:
    """Bitta tarix, ikkita kesim (modul izohi, birinchi 🔴)."""

    #: `Cutoffs.early` bilan o'lchangani.
    early: tzreach.Reachability
    #: `Cutoffs.late` bilan o'lchangani.
    late: tzreach.Reachability

    @property
    def verdicts_differ(self) -> bool:
        """Kesim o'lchovning **holatini** o'zgartirdimi."""
        return self.early.verdict is not self.late.verdict

    @property
    def levels_in_dispute(self) -> tuple[Level, ...]:
        """Kesim `looks_high` ni o'zgartirgan darajalar, §2.1 tartibida.

        Faqat **ikkala** o'lchov ham darajani ko'rgan holatda
        solishtiriladi: bir tomonda daraja umuman yo'q bo'lsa, farq
        ziddiyat emas, o'lchanmaganlik.
        """
        return tuple(
            level
            for level in tzreach.LEVEL_ORDER
            if level in self.early.levels
            and level in self.late.levels
            and self.early.levels[level].looks_high != self.late.levels[level].looks_high
        )

    @property
    def measured(self) -> bool:
        """Ikkala o'lchov ham sonlar berdimi."""
        return (
            self.early.verdict is tzreach.Verdict.MEASURED
            and self.late.verdict is tzreach.Verdict.MEASURED
        )

    @property
    def cutoff_decides(self) -> bool:
        """Javob kesim sanasiga bog'liqmi — ya'ni son dalil emasmi."""
        return self.verdicts_differ or bool(self.levels_in_dispute)


@dataclass(frozen=True)
class Report:
    """§12 ning ikkala yarmi bitta obyektda."""

    region: str
    since: datetime
    until: datetime
    cuts: Cutoffs
    min_episodes: int
    reach: ReachPair
    coverage: tzcoverage.Coverage

    @property
    def coverage_measured(self) -> bool:
        return self.coverage.verdict is tzcoverage.Verdict.MEASURED

    @property
    def findings(self) -> tuple[Finding, ...]:
        """Topilmalar — barqaror tartibda (Т-3).

        **O'lchanmagan yarmidan topilma chiqmaydi.** `UNKNOWN` da
        modullar sonlarni bo'sh qoldiradi, bo'sh sonlardan xulosa
        chiqarish o'lchanmagan narsa haqida da'vo bo'lardi.
        """
        items: list[Finding] = []

        if self.reach.cutoff_decides:
            if self.reach.verdicts_differ:
                items.append(Finding("reach.cutoff_decides", "verdict"))
            items += [
                Finding("reach.cutoff_decides", level.value)
                for level in self.reach.levels_in_dispute
            ]
        if self.reach.measured:
            # Ikkala kesimda ham yuqori ko'ringan darajalar — ya'ni
            # xulosasi kesimga bog'liq bo'lmaganlari.
            both = [
                level
                for level in tzreach.LEVEL_ORDER
                if level in self.reach.early.levels
                and level in self.reach.late.levels
                and self.reach.early.levels[level].looks_high
                and self.reach.late.levels[level].looks_high
            ]
            items += [Finding("reach.level_looks_high", level.value) for level in both]

        if self.coverage_measured:
            city = self.coverage.city
            if self.coverage.looks_unreachable:
                items.append(Finding("coverage.city_mostly_unreachable"))
            if not city.reachable:
                items.append(Finding("coverage.city_unreachable"))
            if city.dead_weight > 0:
                items.append(Finding("coverage.dead_weight", str(city.dead_weight)))
            if city.minimum_decides:
                items.append(Finding("coverage.minimum_decides", "city"))
            for district in self.coverage.districts:
                if not district.reachable:
                    items.append(Finding("coverage.district_unreachable", district.district_id))
            for district in self.coverage.districts:
                if district.minimum_decides:
                    items.append(Finding("coverage.minimum_decides", district.district_id))
            for district_id in self.coverage.unknown_districts:
                items.append(Finding("coverage.unknown_district", district_id))
            for district in self.coverage.districts:
                if district.over_capacity:
                    items.append(Finding("coverage.over_capacity", district.district_id))

        return tuple(items)

    @property
    def status(self) -> Status:
        """Yakuniy holat. `UNMEASURED` `FINDINGS` dan **kuchliroq**.

        Sabab modul izohida: «topilma bor» degan javob qolgan hamma
        narsa o'lchandi degan ma'noni beradi.
        """
        if not self.reach.measured or not self.coverage_measured:
            return Status.UNMEASURED
        return Status.FINDINGS if self.findings else Status.CLEAN

    @property
    def exit_code(self) -> int:
        return EXIT_CODE[self.status]


def _share(value: float | None) -> str:
    """Ulushni matnga. `None` — o'lchanmagan, `0 %` emas."""
    return "n/a" if value is None else f"{value * 100:.0f}%"


def _reach_lines(title: str, reach: tzreach.Reachability) -> list[str]:
    """Bitta o'lchovning matni."""
    lines = [
        f"  {title}: {reach.verdict.value} ({reach.reason.value}); "
        f"hodisa {reach.episodes_seen}, mustaqil {reach.episodes_independent}"
    ]
    if not reach.levels:
        lines.append("    sonlar yo'q — o'lchanmadi")
        return lines
    for level in tzreach.LEVEL_ORDER:
        result = reach.level(level)
        if result is None:
            continue
        histogram = ", ".join(
            f"{people}→{count}" for people, count in sorted(result.people_histogram.items())
        )
        lines.append(
            f"    {level.value:8} {result.reached_in_first_window}/{result.episodes} "
            f"({_share(result.share)}) oynadan tashqari {result.window_only} "
            f"{'YUQORI' if result.looks_high else 'ok'}  [{histogram}]"
        )
    return lines


def render(report: Report) -> str:
    """Odam o'qiydigan hisobot. Toza: bazani ham, vaqtni ham ko'rmaydi."""
    coverage = report.coverage
    city = coverage.city
    lines = [
        f"TZ §12 — {report.region}",
        f"oyna: {report.since.isoformat()} … {report.until.isoformat()}",
        f"akkaunt kesimi: erta {report.cuts.early.isoformat()} / "
        f"kech {report.cuts.late.isoformat()} "
        f"({report.cuts.min_account_age_min} daqiqa)",
        f"eng kam hodisa: {report.min_episodes}",
        "",
        "§2.1 — poroglar tarixda yig'ilganmi (tzreach)",
    ]
    lines += _reach_lines("erta kesim", report.reach.early)
    lines += _reach_lines("kech kesim", report.reach.late)
    if report.reach.cutoff_decides:
        disputed = ", ".join(level.value for level in report.reach.levels_in_dispute) or "-"
        lines.append(
            f"  🔴 javob kesimga bog'liq: verdikt farqi "
            f"{report.reach.verdicts_differ}, darajalar: {disputed}"
        )

    lines += [
        "",
        "§3 — zona poroglari umuman yig'ilishi mumkinmi (tzcoverage)",
        f"  verdikt: {coverage.verdict.value} ({coverage.reason.value})",
        f"  tuman: reyestrda {city.districts_total}, foydalanuvchisi bor "
        f"{city.districts_with_users}, erishuvchan {city.districts_reachable}, "
        f"kerak {city.need} → {'ok' if city.reachable else 'ERISHILMAS'}",
        f"  o'lik og'irlik: {city.dead_weight}; "
        f"qamrov: {_share(city.coverage)}; "
        f"biriktirilmagan kvartal {coverage.blocks_unassigned}, "
        f"chegarada {coverage.blocks_straddling}",
    ]
    for district in coverage.districts:
        mark = "ok" if district.reachable else "ERISHILMAS"
        code = district.code or "?"
        lines.append(
            f"    {district.district_id} [{code}] "
            f"kvartal {district.blocks_with_users}/"
            f"{'?' if district.blocks_estimated is None else district.blocks_estimated} "
            f"kerak {district.need} (ulush {district.share_part}) "
            f"{'eng-kam-son' if district.minimum_decides else 'ulush'} "
            f"{'' if district.known else 'REYESTRDA-YO`Q '}"
            f"{'TAXMIN-XATO ' if district.over_capacity else ''}{mark}"
        )

    lines += ["", f"holat: {report.status.value} (chiqish kodi {report.exit_code})"]
    if report.findings:
        lines += [f"  - {item}" for item in report.findings]
    else:
        lines.append("  topilma yo'q")
    return "\n".join(lines)


def as_json(report: Report) -> Mapping[str, object]:
    """Mashina o'qiydigan kesim.

    Ikkala yarmi ham **o'z modulining** `summary()` idan olinadi —
    shakl chaqiruvchida takrorlanmaydi.
    """
    return {
        "region": report.region,
        "since": report.since.isoformat(),
        "until": report.until.isoformat(),
        "cutoff_early": report.cuts.early.isoformat(),
        "cutoff_late": report.cuts.late.isoformat(),
        "min_account_age_min": report.cuts.min_account_age_min,
        "min_episodes": report.min_episodes,
        "reach_early": tzreach.summary(report.reach.early),
        "reach_late": tzreach.summary(report.reach.late),
        "cutoff_decides": report.reach.cutoff_decides,
        "levels_in_dispute": [level.value for level in report.reach.levels_in_dispute],
        "coverage": tzcoverage.summary(report.coverage),
        "findings": [{"code": item.code, "subject": item.subject} for item in report.findings],
        "status": report.status.value,
        "exit_code": report.exit_code,
    }


async def collect(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    region_code: str,
    since: datetime,
    until: datetime,
    min_episodes: int,
    params: tzconfig.TzParams,
    min_trust_score: int,
    min_account_age_min: int,
) -> Report:
    """Ikkala yarmini ham o'lchaydi. Yozmaydi.

    Tarix **ikki marta** o'qiladi (modul izohi, birinchi 🔴).
    """
    cuts = cutoffs(since, until, min_account_age_min=min_account_age_min)
    pair: list[tzreach.Reachability] = []
    for cutoff in (cuts.early, cuts.late):
        episodes = await tzreach.load(
            session,
            region_id=region_id,
            since=since,
            until=until,
            kind=KIND_OUTAGE,
            min_trust_score=min_trust_score,
            account_created_before=cutoff,
        )
        pair.append(tzreach.measure(episodes, params=params, min_episodes=min_episodes))
    coverage = await tzcoverage.load(session, region_id=region_id, params=params)
    return Report(
        region=region_code,
        since=since,
        until=until,
        cuts=cuts,
        min_episodes=min_episodes,
        reach=ReachPair(early=pair[0], late=pair[1]),
        coverage=coverage,
    )


def moment(raw: str) -> datetime:
    """ISO sana/vaqt → UTC. Zonasiz qiymat UTC deb o'qiladi.

    Zonasiz qiymatni mahalliy zonada o'qish oynani mashinaga bog'lardi
    va bir xil buyruq ikki mashinada boshqa son berardi.
    """
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


async def run(
    region_code: str,
    *,
    since: datetime,
    until: datetime,
    min_episodes: int,
    as_json_output: bool,
) -> int:
    async with session_scope() as session:
        region = (
            await session.execute(select(Region).where(Region.code == region_code))
        ).scalar_one_or_none()
        if region is None:
            print(f"mintaqa topilmadi: {region_code}")
            return EXIT_ERROR

        values = await geo_q.load_region_config(session, region.id)
        try:
            params = tzconfig.params_from_mapping(values)
        except (tzconfig.ConfigMissingError, tzconfig.ConfigInvalidError) as exc:
            print(f"mintaqa sozlanmagan ({region_code}): {exc}")
            return EXIT_ERROR

        report = await collect(
            session,
            region_id=region.id,
            region_code=region_code,
            since=since,
            until=until,
            min_episodes=min_episodes,
            params=params,
            min_trust_score=settings.reporter_min_trust_score,
            min_account_age_min=settings.reporter_min_account_age_min,
        )

    if as_json_output:
        print(json.dumps(as_json(report), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render(report))
    return report.exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TZ §12 tekshiruvi (poroglar erishuvchanmi)")
    parser.add_argument("--region", required=True, help="mintaqa kodi, masalan `samarkand`")
    parser.add_argument("--since", required=True, help="oyna boshi, ISO (majburiy)")
    parser.add_argument("--until", default=None, help="oyna oxiri, ISO; sukut — hozir (UTC)")
    parser.add_argument(
        "--min-episodes",
        required=True,
        type=int,
        help="maxrajning eng kam kattaligi; sukut qiymati ataylab yo'q",
    )
    parser.add_argument("--json", action="store_true", help="mashina o'qiydigan chiqish")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.min_episodes < 1:
        print("--min-episodes kamida 1 bo'lsin")
        return EXIT_ERROR
    try:
        since = moment(args.since)
        until = moment(args.until) if args.until else datetime.now(timezone.utc)
        cutoffs(since, until, min_account_age_min=settings.reporter_min_account_age_min)
    except ValueError as exc:
        print(f"argument xato: {exc}")
        return EXIT_ERROR
    return asyncio.run(
        run(
            args.region,
            since=since,
            until=until,
            min_episodes=args.min_episodes,
            as_json_output=args.json,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

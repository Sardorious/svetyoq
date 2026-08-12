"""Qabul mezonlari va jadval (`BRD` §22–§23) ↔ qurilgan mahsulot.

**Nima uchun bu modul bor.** 105-run BRD §20–§21 ni bog'ladi va §22–§23 ni
shu runga qoldirdi (sabab o'sha runda yozilgan: §22 «метрики §21 измерены»
yakuni §21 ning o'lchanuvchanlik xaritasisiz baholanmasdi — endi xarita
bor). §22 — loyihaning **qabul** sathi: 5 ta Ph.0 va 9 ta Ph.1 mezoni,
plus muvaffaqiyat ta'rifi. §23 — **vaqt** sathi: gantt va 7 fazali jadval.

## Birinchi topilma: xronologiya teskari — mahsulot go/no-go dan oldin qurilgan

§23 gantt bo'yicha Ph.0 dala ishi 2026-09-01 da **boshlanadi**, go/no-go
qarori 2026-10-20 da, Development undan ham keyin. Repo esa bugun
(2026-08-11) butun mahsulotni o'z ichiga oladi: `app/`, o'nta migratsiya,
yuz qirqdan ortiq test fayli. Ya'ni Discovery/Development/Testing
fazalarining artefaktlari reja bo'yicha ularni ochadigan qarordan **oldin**
mavjud. Bu `02` dagi `PH0-OS-01` taqiqining egizagi (u yerda 👤 qaror bor:
`04` haq, qurilish davom etadi) — lekin §23 o'z jadvalini shu holicha
saqlaydi va hujjat sifatida bajarilmaydigan reja bo'lib qoladi.

## Ikkinchi topilma: muvaffaqiyat ta'rifi o'lchab bo'lmaydigan metrikalarga tayanadi

§22 yakuni: loyiha muvaffaqiyatli, agar AC-0.*/AC-1.* bajarilgan **va**
«метрики §21 измерены». 105-run ko'rsatganidek §21 ning uch qatori bugun
o'lchab bo'lmaydi (Time-to-answer, UZ-sessiya, moderatsiya SLA) —
`business_reporting.measurability_holds` `False`. §23 ning Support fazasi
ham chiqish mezoniga aynan shu iborani qo'yadi, ya'ni oxirgi faza ta'rifan
yopilmaydi. Muvaffaqiyat mezoni «o'lchanganlik» bo'lgan loyihada bu —
qabul sathining o'zagi (👤 savol PROGRESS da, 105-run).

## Uchinchi topilma: ikki mezon uchun solishtiradigan voqelik yo'q

`AC-1.7` Toshkent vitrinalarining migratsiyadan keyingi qiymatlarini ≤1%
farq bilan talab qiladi — lekin bu kod bazasida Toshkent merosi ham,
migratsiya ham, «tarixiy qiymat» ham yo'q: regressiyani yurgizadigan
narsaning o'zi mavjud emas. `AC-1.8` «Самарканд» skoupli rollarni talab
qiladi — kodda uch rol bor (`viewer`/`moderator`/`admin`) va ularda
mintaqa skoupi tushunchasi umuman yo'q (BRD §19 dagi 8-rol topilmasining
egizagi, 104-run): «попытка выхода за скоуп» ni ifodalab ham bo'lmaydi.

## To'rtinchi topilma: go/no-go qarorini yozadigan joy yo'q

`AC-0.5` qarorning o'zi hujjatlashtirilishini so'raydi. 75/77-runlar
ko'rsatganidek `roadmap.evaluate().recorded` bo'sh — Faza 0 ning birorta
natijasi (vazifa ham, chiqish mezoni ham) repoda saqlanmaydi. Mezon
bajarilishi uchun avval «qayd etish joyi» degan savol yechilishi kerak
(👤, `01` §23/§24 bloki bilan bitta).

## O'qish tartibi

Ikki jadval hujjatdagi tartibda: `AC_ROWS` (§22, Ph.0 keyin Ph.1),
`PHASES` (§23 fazalar jadvali). Kataklar hujjat so'zlari bilan aynan
(kontrakt test hujjatdan qayta o'qiydi), baho kod dalili (`binds`) bilan.
`evaluate()` — yig'ma hisobot, `app.admin.registries` indeksi o'qiydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.admin import roles as admin_roles
from app.release import business_reporting as brep
from app.release import phase0_plan, roadmap

#: Hujjat bo'limlari. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "BRD §22–§23"

#: Jadval o'lchamlari — hujjatdan parse qilinadi va solishtiriladi.
SPEC_AC_PH0_ROWS = 5
SPEC_AC_PH1_ROWS = 9
SPEC_PHASE_ROWS = 7

#: §23 fazalar jadvalining birinchi ustuni — hujjatdagi tartibda.
SPEC_PHASE_NAMES: tuple[str, ...] = (
    "Ph.0 Validation",
    "Discovery / Design",
    "Development",
    "Testing",
    "Pilot",
    "Production",
    "Support",
)

#: §23 gantt sanalari: eng erta boshlanish va go/no-go bosqichi.
#: Ikkalasi ham repo tarixidan **keyin** — birinchi topilmaning o'qi.
#: Nomi `PH0_` — `test_risk_register_contract` `phase0*` nomlarini
#: «natija saqlanadigan joy» sifatida qulflaydi, bu esa reja sanasi.
PH0_START_DATE = "2026-09-01"
GO_NO_GO_DATE = "2026-10-20"

#: §22 yakuni tayanadigan ibora — §21 reyestri bilan bitta manba.
#: Ataylab import: ikki modul bitta iborani ikki joyda yozmasin.
SUCCESS_CLAUSE = brep.MEASURABILITY_CLAUSE

#: Kodda mavjud rollar — `AC-1.8` bahosining langari. Rollar o'zgarsa
#: (masalan skoupli rol paydo bo'lsa) qorovul yiqiladi va baho qayta
#: ko'riladi.
EXPECTED_ROLE_SET = frozenset({"viewer", "moderator", "admin"})


class Build(StrEnum):
    """Mezon yoki faza artefaktining qurilgan mahsulotdagi holati."""

    #: Mezon so'ragan narsa to'liq ishlaydi.
    LIVE = "live"
    #: Bir qismi bor, bir qismi yo'q — farq `gap` da.
    PARTIAL = "partial"
    #: Mexanizm tayyor, natija tashqi hodisani (Ph.0, poligonlar) kutadi.
    PROVISIONED = "provisioned"
    #: Kodda hech narsa yo'q yoki mezonni ifodalab bo'lmaydi.
    ABSENT = "absent"


class BusinessAcceptanceError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class AcRow:
    """§22 ning bitta qatori — `criterion` hujjat katagi bilan aynan."""

    code: str
    criterion: str
    phase: str  # "Ph.0" | "Ph.1"
    build: Build
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


@dataclass(frozen=True)
class PhaseRow:
    """§23 fazalar jadvalining bitta qatori — kataklar hujjat bilan aynan."""

    phase: str
    question: str
    exit: str
    #: Faza chiqarishi kerak bo'lgan artefakt bugun repoda bormi.
    artifacts_exist: bool
    #: Reja bo'yicha faza go/no-go qaroridan keyinmi (ganttda `after p0f`
    #: zanjiri). Ph.0 uchun `False`.
    planned_after_go_no_go: bool
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


# --------------------------------------------------------------------------
# §22 — qabul mezonlari, hujjatdagi tartibda
# --------------------------------------------------------------------------

AC_ROWS: tuple[AcRow, ...] = (
    AcRow(
        code="AC-0.1",
        criterion=(
            "Гипотезы H-1…H-5 проверены; по каждой зафиксирован результат — "
            "подтверждена, опровергнута или не определена"
        ),
        phase="Ph.0",
        build=Build.PROVISIONED,
        note=(
            "Gipoteza reyestri kodda (`phase0_plan` — H-1…H-8 posturasi "
            "bilan), ya'ni «zafiksirovan» uchun skelet bor. Dala ishi "
            "odamniki va o'tkazilmagan — natija kataklari bo'sh."
        ),
        binds=("app.release.phase0_plan:Hypothesis",),
        gap="Ph.0 o'tkazilmagan — tekshiruv natijalari mavjud emas (👤).",
    ),
    AcRow(
        code="AC-0.2",
        criterion=(
            "Фактическое административное деление города установлено и "
            "подтверждено документально"
        ),
        phase="Ph.0",
        build=Build.PROVISIONED,
        note=(
            "«Установлено» qismiga asbob bor: OSM dan chegara importi "
            "(tumanlar yuklanadi). «Подтверждено документально» esa odam "
            "ishi — rasmiy hujjat repoda bo'lishi mumkin emas."
        ),
        binds=("tools/import_boundaries.py",),
        gap="Hujjatli tasdiq yo'q — OSM importi rasmiy manba emas (👤).",
    ),
    AcRow(
        code="AC-0.3",
        criterion=(
            "Оценена доступность границ махаллей и трудоёмкость их оцифровки"
        ),
        phase="Ph.0",
        build=Build.PROVISIONED,
        note=(
            "Bu — `02` dagi H-5 gipotezasi, reyestrda posturasi bilan "
            "turibdi. Baholashning o'zi dala ishi (E17 bloki bilan bitta)."
        ),
        binds=("app.release.phase0_plan:Hypothesis",),
        gap="Baholash o'tkazilmagan — H-5 natijasiz (👤 E17).",
    ),
    AcRow(
        code="AC-0.4",
        criterion=(
            "Получено юридическое заключение по ПДн и локализации хранения"
        ),
        phase="Ph.0",
        build=Build.ABSENT,
        note=(
            "Yuridik xulosa — tashqi hujjat; kodda uni oladigan ham, "
            "saqlaydigan ham mexanizm yo'q. Maxfiylik kafolatlari "
            "(jitter, `geom_exact` purge) bor, lekin ular «xulosa olindi» "
            "mezonini qanoatlantirmaydi."
        ),
        gap="Yuridik xulosa yo'q va uni qayd etadigan joy ham yo'q (👤).",
    ),
    AcRow(
        code="AC-0.5",
        criterion=(
            "Принято и задокументировано решение go / no-go с обоснованием"
        ),
        phase="Ph.0",
        build=Build.ABSENT,
        note=(
            "To'rtinchi topilma: qaror ham yo'q, uni yozadigan joy ham — "
            "`roadmap.evaluate().recorded` bo'sh (75/77-runlar sinfi). "
            "Birinchi topilma buni keskinlashtiradi: qaror kutilayotgan "
            "kod allaqachon qurib bo'lingan."
        ),
        gap="Qaror qayd etiladigan mexanizm yo'q; kod qarordan oldin qurilgan (👤).",
    ),
    AcRow(
        code="AC-1.1",
        criterion=(
            "Трёхуровневая геомодель реализована; репорт получает привязку "
            "ко всем трём уровням"
        ),
        phase="Ph.1",
        build=Build.LIVE,
        note=(
            "`reports` jadvalida uchala daraja bor (`region_id` majburiy, "
            "`district_id`, `mahalla_id`), biriktirish geo-quvurda "
            "(`ST_Contains`)."
        ),
        binds=("app.reports.models:Report", "app.geo.pipeline:find_mahalla_id"),
    ),
    AcRow(
        code="AC-1.2",
        criterion=(
            "Границы версионируются; тестовое изменение границ не искажает "
            "историческую витрину"
        ),
        phase="Ph.1",
        build=Build.PARTIAL,
        note=(
            "Mahalla qatlami versiyalanadi (`valid_from`/`valid_to`, "
            "`MahallaRegistry.versions`) va chegara o'zgarishlari hisobot "
            "sifatida yig'iladi. Tuman/mintaqa chegaralari esa "
            "versiyasiz — ular almashtirilsa tarixiy kesim eski geometriya "
            "haqida hech narsa bilmaydi."
        ),
        binds=("app.geo.mahallas:MahallaRegistry", "app.stats.boundaries:summarize"),
        gap="Versiyalash faqat mahalla qatlamida — tuman/mintaqa chegaralari versiyasiz.",
    ),
    AcRow(
        code="AC-1.3",
        criterion=(
            "Справочник территорий и адресов загружен, покрытие проверено "
            "выборочно"
        ),
        phase="Ph.1",
        build=Build.PROVISIONED,
        note=(
            "Yuklash mexanizmi tayyor (chegara importi, mahalla reyestri, "
            "qamrov kesimi), lekin mahalla poligonlari odamdan keladi "
            "(E17) va «адресов» spravochnigi umuman ko'zda tutilmagan."
        ),
        binds=("tools/import_boundaries.py", "app.stats.mahalla_coverage:summarize"),
        gap="Poligonlar yuklanmagan (👤 E17); manzil spravochnigi kodda yo'q.",
    ),
    AcRow(
        code="AC-1.4",
        criterion=(
            "UZ является языком по умолчанию регионального контура; паритет "
            "строк 100%"
        ),
        phase="Ph.1",
        build=Build.LIVE,
        note=(
            "Standart til `uz` (global sozlama ham, `regions."
            "default_language` ham), katalog pariteti testda qulflangan "
            "(`test_no_missing_keys`)."
        ),
        binds=("app.core.config:Settings", "app.core.i18n"),
    ),
    AcRow(
        code="AC-1.5",
        criterion=(
            "Региональные параметры валидации задаются конфигурацией, без "
            "изменения кода"
        ),
        phase="Ph.1",
        build=Build.LIVE,
        note=(
            "Mintaqa parametrlari bazadan o'qiladi (`RegionInfo`: bbox, "
            "standart til) — yangi mintaqa kod o'zgarishisiz `region_admin` "
            "asbobi bilan qo'shiladi."
        ),
        binds=("app.geo.registry:RegionInfo", "app.geo.bbox"),
    ),
    AcRow(
        code="AC-1.6",
        criterion="Порог публикации карты реализован и настроен",
        phase="Ph.1",
        build=Build.LIVE,
        note=(
            "Porog konfiguratsiyada (`public_min_reports`) va uch sirtda "
            "amal qiladi: snapshot klasterni faqat porogdan oshsa oladi, "
            "ochiq hodisa sathi ham shu chegara bilan, yetuklik kesimi "
            "chegaralarini javobda ochiq ko'rsatadi."
        ),
        binds=("app.core.config:Settings", "app.clustering.snapshot:build_payload"),
    ),
    AcRow(
        code="AC-1.7",
        criterion=(
            "Ташкентские витрины после миграции воспроизводят исторические "
            "значения с расхождением ≤1%"
        ),
        phase="Ph.1",
        build=Build.ABSENT,
        note=(
            "Uchinchi topilmaning birinchi yarmi: bu kod bazasida Toshkent "
            "merosi yo'q — na eski vitrina, na migratsiya, na «tarixiy "
            "qiymat». Regressiyani yurgizadigan voqelikning o'zi mavjud "
            "emas; mezon boshqa repo haqida yozilgan."
        ),
        gap="Toshkent merosi bu repoda yo'q — solishtiradigan juft yo'q (👤 skoup).",
    ),
    AcRow(
        code="AC-1.8",
        criterion=(
            "Роли со скоупом «Самарканд» работают; попытка выхода за скоуп "
            "отклоняется и логируется"
        ),
        phase="Ph.1",
        build=Build.ABSENT,
        note=(
            "Uchinchi topilmaning ikkinchi yarmi: kodda uch rol bor va "
            "ularda mintaqa skoupi tushunchasi yo'q (BRD §19 ning 8-rol "
            "topilmasi, 104-run) — «выход за скоуп» ni ifodalab bo'lmaydi, "
            "demak rad etib ham, loglab ham bo'lmaydi."
        ),
        gap="Rol modelida mintaqa skoupi yo'q (👤 §19 bloki bilan bitta).",
    ),
    AcRow(
        code="AC-1.9",
        criterion=(
            "Публичная карта региона включена по достижении порога, витрины "
            "сопровождаются Coverage Index"
        ),
        phase="Ph.1",
        build=Build.PARTIAL,
        note=(
            "Coverage Index vitrinada bor, porog klaster darajasida "
            "ishlaydi. Lekin «karta mintaqa bo'yicha yoqiladi» degan "
            "alohida holat yo'q: endpoint har doim ochiq, yosh mintaqa "
            "dislaymer oladi (`stats.warning.young_region`), yashirilmaydi."
        ),
        binds=("app.stats.maturity:compute", "app.stats.service:mahalla_index"),
        gap="Mintaqa darajasidagi «yoqish» hodisasi yo'q — porog faqat klaster sathida.",
    ),
)


# --------------------------------------------------------------------------
# §23 — fazalar jadvali, hujjatdagi tartibda
# --------------------------------------------------------------------------

PHASES: tuple[PhaseRow, ...] = (
    PhaseRow(
        phase="Ph.0 Validation",
        question="Стоит ли вообще запускать?",
        exit="AC-0.1…AC-0.5, решение go / no-go",
        artifacts_exist=False,
        planned_after_go_no_go=False,
        note=(
            "Reja bo'yicha birinchi faza — amalda boshlanmagan (dala ishi "
            "odamniki), natijasini yozadigan joy ham yo'q (AC-0.5)."
        ),
        gap="Faza o'tkazilmagan; chiqish natijasi qayd etilmaydi (👤).",
    ),
    PhaseRow(
        phase="Discovery / Design",
        question="Как именно устроить геомодель и интерфейс?",
        exit="Утверждённые спецификации",
        artifacts_exist=True,
        planned_after_go_no_go=True,
        note=(
            "Chiqish artefakti allaqachon bor: `05`/`06` spetsifikatsiyalari "
            "yozilgan va butun kontrakt qatlami bilan kodga bog'langan — "
            "reja bo'yicha esa faza go/no-go dan keyin ochiladi."
        ),
        binds=("../05_Technical_Design.md", "../06_Confirmation_Logic.md"),
        gap="Artefakt go/no-go dan oldin mavjud — jadval teskari (birinchi topilma).",
    ),
    PhaseRow(
        phase="Development",
        question="Реализовано ли без ущерба Ташкенту?",
        exit="AC-1.1…AC-1.5, AC-1.7",
        artifacts_exist=True,
        planned_after_go_no_go=True,
        note=(
            "Mahsulot qurib bo'lingan (`app/`, o'nta migratsiya) — reja "
            "bo'yicha bu faza eng erta 2026 kuzining oxirida boshlanardi. "
            "Fazaning savoli esa bu repoda javobsiz: Toshkent yo'q (AC-1.7)."
        ),
        binds=("app", "alembic/versions"),
        gap="Mahsulot go/no-go dan oldin qurilgan (`PH0-OS-01` egizagi, 👤 qaror bor).",
    ),
    PhaseRow(
        phase="Testing",
        question="Корректны ли данные?",
        exit="Регрессия витрин пройдена",
        artifacts_exist=True,
        planned_after_go_no_go=True,
        note=(
            "Test to'plami bor va yashil (144 fayl), lekin chiqish mezoni "
            "«ташкентских витрин» regressiyasi haqida — u AC-1.7 bilan "
            "birga bu repoda ifodalanmaydi."
        ),
        binds=("tests",),
        gap="To'plam gate dan oldin qurilgan; «регрессия витрин» esa yurgizilmaydi (AC-1.7).",
    ),
    PhaseRow(
        phase="Pilot",
        question="Набирается ли плотность?",
        exit="Достижение порога публикации",
        artifacts_exist=False,
        planned_after_go_no_go=True,
        note=(
            "Yopiq yig'ish bosqichi (E10) — odam ishi, boshlanmagan. "
            "Porogning o'zi kodda tayyor (AC-1.6) — reja bilan zid emas."
        ),
        binds=("app.stats.maturity:compute",),
    ),
    PhaseRow(
        phase="Production",
        question="Работает ли продукт публично?",
        exit="AC-1.9",
        artifacts_exist=False,
        planned_after_go_no_go=True,
        note=(
            "Ommaviy ishga tushirish (E12) bo'lmagan — reja bilan zid emas; "
            "chiqish mezoni AC-1.9 ning `PARTIAL` holatiga tayanadi."
        ),
        binds=("app.clustering.snapshot:build_payload",),
    ),
    PhaseRow(
        phase="Support",
        question="Верны ли параметры?",
        exit="Калибровка завершена, метрики §21 измерены",
        artifacts_exist=False,
        planned_after_go_no_go=True,
        note=(
            "Ikkinchi topilmaning o'qi: chiqish mezoni «метрики §21 "
            "измерены» — §21 ning uch qatori esa o'lchab bo'lmaydi "
            "(`business_reporting.measurability_holds` `False`). Oxirgi "
            "faza ta'rifan yopilmaydi. Kalibrlash asbobi tayyor (E11)."
        ),
        binds=("tools/recluster.py",),
        gap="Chiqish mezoni o'lchab bo'lmaydigan metrikalarga tayanadi (👤 105-run savoli).",
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessAcceptanceReport:
    """BRD §22–§23 ning bugungi holati."""

    acceptance: tuple[AcRow, ...]
    phases: tuple[PhaseRow, ...]

    def __post_init__(self) -> None:
        self._check_counts()
        self._check_builds()
        self._check_chronology()
        self._check_neighbors()

    # -- qorovullar --------------------------------------------------------

    def _check_counts(self) -> None:
        ph0 = tuple(r for r in self.acceptance if r.phase == "Ph.0")
        ph1 = tuple(r for r in self.acceptance if r.phase == "Ph.1")
        if len(ph0) != SPEC_AC_PH0_ROWS or len(ph1) != SPEC_AC_PH1_ROWS:
            raise BusinessAcceptanceError("§22 qatorlari soni hujjatga mos emas")
        expected = tuple(f"AC-0.{i}" for i in range(1, 6)) + tuple(
            f"AC-1.{i}" for i in range(1, 10)
        )
        if tuple(r.code for r in self.acceptance) != expected:
            raise BusinessAcceptanceError("§22 kodlari tartibi hujjatdagidan farq qildi")
        if tuple(p.phase for p in self.phases) != SPEC_PHASE_NAMES:
            raise BusinessAcceptanceError("§23 fazalar ustuni hujjatdagidan farq qildi")

    def _check_builds(self) -> None:
        for row in self.acceptance:
            if row.build in (Build.LIVE, Build.PARTIAL, Build.PROVISIONED) and not row.binds:
                raise BusinessAcceptanceError(f"{row.code}: {row.build} dalilsiz bo'lmaydi")
            if row.build is Build.ABSENT and row.binds:
                raise BusinessAcceptanceError(
                    f"{row.code}: `ABSENT` da dalil bo'lmaydi — dalil bor bo'lsa, "
                    "holat boshqa"
                )
            if row.build is not Build.LIVE and not row.gap:
                raise BusinessAcceptanceError(f"{row.code}: farq bor, `gap` yozilmagan")

    def _check_chronology(self) -> None:
        for row in self.phases:
            if row.artifacts_exist and not row.binds:
                raise BusinessAcceptanceError(f"{row.phase}: artefakt dalilsiz bo'lmaydi")
            if row.artifacts_exist and row.planned_after_go_no_go and not row.gap:
                raise BusinessAcceptanceError(
                    f"{row.phase}: gate dan oldingi artefakt — xronologiya buzilishi "
                    "`gap` siz qolmaydi"
                )
        if not self.chronology_inverted:
            raise BusinessAcceptanceError(
                "Birinchi topilma yo'qoldi: gate dan oldin qurilgan faza qolmadi — "
                "reyestr qayta ko'rilsin"
            )

    def _check_neighbors(self) -> None:
        """Qo'shni reyestrlar bilan bog'lamlar — eskirsa shu yerda yiqiladi."""
        if not any(o.code == "PH0-OS-01" for o in phase0_plan.OUT_OF_SCOPE):
            raise BusinessAcceptanceError(
                "`PH0-OS-01` yo'qoldi — xronologiya topilmasining langari eskirgan"
            )
        if brep.evaluate().measurability_holds:
            raise BusinessAcceptanceError(
                "§21 o'lchanuvchan bo'ldi — Support/muvaffaqiyat bahosi qayta ko'rilsin"
            )
        if roadmap.evaluate().recorded:
            raise BusinessAcceptanceError(
                "`roadmap.recorded` to'ldi — AC-0.5 bahosi qayta ko'rilsin"
            )
        if {r.value for r in admin_roles.Role} != EXPECTED_ROLE_SET:
            raise BusinessAcceptanceError(
                "Rollar to'plami o'zgardi — AC-1.8 bahosi qayta ko'rilsin"
            )

    # -- kesimlar ----------------------------------------------------------

    @property
    def flagged(self) -> tuple[AcRow | PhaseRow, ...]:
        """`gap` i bo'sh bo'lmagan qatorlar — hujjat bilan kod ajragan joylar."""
        return tuple(r for r in (*self.acceptance, *self.phases) if r.gap)

    @property
    def by_build(self) -> dict[Build, int]:
        result: dict[Build, int] = {b: 0 for b in Build}
        for row in self.acceptance:
            result[row.build] += 1
        return result

    @property
    def chronology_inverted(self) -> bool:
        """Gate dan keyinga rejalangan faza artefakti bugun bormi. Bugun `True`."""
        return any(p.artifacts_exist and p.planned_after_go_no_go for p in self.phases)

    @property
    def success_holds(self) -> bool:
        """§22 muvaffaqiyat ta'rifi bugun rostmi. Bugun `False`.

        Ikki shart ham yiqiladi: AC lar to'liq emas (o'nta qator `LIVE`
        emas) va «метрики §21 измерены» bajarilmaydi (105-run).
        """
        all_live = all(r.build is Build.LIVE for r in self.acceptance)
        return all_live and brep.evaluate().measurability_holds

    @property
    def accurate(self) -> bool:
        """§22–§23 «hujjat mahsulotni to'g'ri tasvirlaydi» deb o'qilsa rostmi.

        Bugun `False`: o'n besh qator ajragan — o'nta mezon `LIVE` emas,
        jadvalning uch fazasi gate dan oldin bajarib qo'yilgan, biri
        boshlanmagan, oxirgisi ta'rifan yopilmaydi.
        """
        return not self.flagged


def evaluate() -> BusinessAcceptanceReport:
    """Reyestrdan to'liq hisobot. Argument yo'q — 85–87, 99–105 runlar qoidasi."""
    return BusinessAcceptanceReport(acceptance=AC_ROWS, phases=PHASES)

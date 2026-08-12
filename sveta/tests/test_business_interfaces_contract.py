"""BRD §18–§19 reyestri (`app/release/business_interfaces.py`) ↔ hujjat ↔ kod.

To'rt manba (99–103 runlar naqshi):

1. **Hujjat** — ikki jadvalning qatorlari, tartibi va ustun qiymatlari
   (tizim nomi, yo'nalish, status; rol nomi, skoup, huquqlar) BRD dan
   parse qilinadi. «Ограничения» xatboshisi ham matndan o'qiladi.
2. **Kod** — hukmlarning tayanchi import bilan ochiladi: rol/ruxsat
   matritsasi, moderator fe'llari, ochiq vitrina, veb-akkaunt yo'qligi.
3. **Manba tuzilishi** — Overpass ning BRD §18 da yo'qligi matndan;
   veb-ro'yxatdan o'tish sirti yo'qligi fayl tizimidan.
4. **Boshqa reyestrlar** — `app.integrations.registry` (`01` §18
   egizaklari va ularning `Warrant` lari), `app.admin.security`
   («Ограничения» bandlari), `business_environment` (Kafka/Redis ↔
   `CON-05`) bilan bog'lamlar aynan tekshiriladi.

Qorovullarning o'zi ham alohida testlanadi (82-run qoidasi).
"""

from __future__ import annotations

import importlib
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.admin import security as sec
from app.admin.roles import PERMISSIONS, Permission, Role
from app.integrations import registry as intreg
from app.release import business_environment as benv
from app.release import business_interfaces as bifc

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
APP_DIR = SVETA_ROOT / "app"
BRD = REPO_ROOT / "BRD_Samarkand.md"


@pytest.fixture(scope="module")
def brd_text() -> str:
    if not BRD.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip("BRD_Samarkand.md bu muhitda yo'q")
    return BRD.read_text(encoding="utf-8")


def _section(text: str, number: int) -> str:
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## \d+\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def _table_rows(section: str, header_word: str) -> list[list[str]]:
    rows: list[list[str]] = []
    seen_header = False
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if seen_header and rows:
                break
            continue
        if re.match(r"^\|[\s:|-]+\|$", stripped):
            continue
        cells = _cells(stripped)
        if not seen_header:
            assert cells[0] == header_word, f"kutilgan sarlavha {header_word!r}"
            seen_header = True
            continue
        rows.append(cells)
    assert rows, f"{header_word} jadvali topilmadi"
    return rows


@pytest.fixture(scope="module")
def doc_integrations(brd_text: str) -> list[list[str]]:
    return _table_rows(_section(brd_text, 18), "Система")


@pytest.fixture(scope="module")
def doc_roles(brd_text: str) -> list[list[str]]:
    return _table_rows(_section(brd_text, 19), "Роль")


@pytest.fixture(scope="module")
def doc_restrictions(brd_text: str) -> str:
    section = _section(brd_text, 19)
    m = re.search(r"\*\*Ограничения:\*\*(.+)$", section, re.M)
    assert m, "«Ограничения» xatboshisi topilmadi"
    return m.group(1)


@pytest.fixture(scope="module")
def report() -> bifc.BusinessInterfacesReport:
    return bifc.evaluate()


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr: ikki jadval
# --------------------------------------------------------------------------


def test_spec_label_names_the_sections() -> None:
    assert bifc.SPEC == "BRD §18–§19"


def test_integration_rows_match_document(doc_integrations, report) -> None:
    assert len(doc_integrations) == bifc.SPEC_INTEGRATION_ROWS
    assert [r[0] for r in doc_integrations] == [i.system for i in report.integrations]


def test_integration_directions_recomputed_from_document(doc_integrations, report) -> None:
    """«Направление» katagi e'londan emas, hujjatdan olinadi."""
    for cells, row in zip(doc_integrations, report.integrations, strict=True):
        assert cells[3] == row.direction, row.system


def test_integration_statuses_verbatim_from_document(doc_integrations, report) -> None:
    """«Статус» katagi aynan saqlanadi — sinf undan hisoblanadi."""
    for cells, row in zip(doc_integrations, report.integrations, strict=True):
        assert cells[4] == row.status, row.system
        assert bifc.classify_status(cells[4]) is row.claim, row.system


def test_status_classifier_covers_every_document_cell(doc_integrations) -> None:
    """Hujjatdagi har status katagi sinfga tushadi — notanishi yo'q."""
    classes = {bifc.classify_status(cells[4]) for cells in doc_integrations}
    assert classes == {
        bifc.Claim.DATA,
        bifc.Claim.HYPOTHESIS,
        bifc.Claim.BASELINE,
        bifc.Claim.REQUIRED,
        bifc.Claim.ACTIVE,
        bifc.Claim.OUT_OF_SCOPE,
    }


def test_status_classifier_rejects_unknown_cell() -> None:
    with pytest.raises(ValueError):
        bifc.classify_status("Неведомый статус")


def test_role_rows_match_document(doc_roles, report) -> None:
    assert len(doc_roles) == bifc.SPEC_ROLE_ROWS
    assert [r[0] for r in doc_roles] == [r.name for r in report.roles]


def test_role_scopes_recomputed_from_document(doc_roles, report) -> None:
    for cells, row in zip(doc_roles, report.roles, strict=True):
        assert cells[1] == row.scope, row.name


def test_moderator_verbs_are_in_the_document_cell(doc_roles) -> None:
    """§19 moderator qatori to'rt fe'lni sanaydi — hammasi katakda bor."""
    moderator = next(c for c in doc_roles if c[0] == "Модератор региона")
    for verb in bifc.MODERATOR_VERBS:
        assert verb in moderator[2], verb


def test_restrictions_paragraph_names_all_three_locks(doc_restrictions) -> None:
    """Uchala band ham ro'yxatda — qator o'chsa shu yerda yiqiladi (104-run
    mutatsiyasi: `RESTRICTION_LOCKS` dan juftlik olib tashlangani sezilmasdi)."""
    assert [d for d, _ in bifc.RESTRICTION_LOCKS] == [
        "2FA",
        "outage.read_exact_geo",
        "Разделение обязанностей",
    ]
    for doc_item, _ in bifc.RESTRICTION_LOCKS:
        assert doc_item in doc_restrictions, doc_item


# --------------------------------------------------------------------------
# 2. Birinchi topilma: Open Data API skoupdan oldinda qurilgan
# --------------------------------------------------------------------------


def test_open_data_row_is_out_of_scope_in_the_document(doc_integrations) -> None:
    row = next(c for c in doc_integrations if c[0] == "Open Data API")
    assert "вне скоупа" in row[4]
    assert "CSV/GeoJSON" in row[2]


def test_open_data_surface_is_shipped_regardless() -> None:
    """Qator sanagan formatlar — REST, CSV, GeoJSON — hammasi jo'natiladi."""
    from app.api.v1.stats import router
    from app.stats import export

    assert router.routes
    assert callable(export.render)
    src = (APP_DIR / "clustering" / "snapshot.py").read_text(encoding="utf-8")
    assert "FeatureCollection" in src


def test_open_data_is_the_only_ahead_row(report) -> None:
    assert [r.system for r in report.ahead] == ["Open Data API"]


# --------------------------------------------------------------------------
# 3. Ikkinchi topilma: Kafka/Redis — `BASELINE-TAS` ↔ ADR-05
# --------------------------------------------------------------------------


def test_kafka_redis_marked_baseline_in_the_document(doc_integrations) -> None:
    """Hujjatning o'zi bu qatorlarni meros bilim deb belgilaydi."""
    for system in ("Kafka", "Redis"):
        row = next(c for c in doc_integrations if c[0] == system)
        assert "BASELINE-TAS" in row[4], system


def test_rejected_rows_are_exactly_the_banned_tech_subset(report) -> None:
    rejected = {r.system for r in report.rejected}
    assert rejected == {"Kafka", "Redis"}
    assert rejected < set(benv.BANNED_TECH)


def test_con05_conflict_is_shared_with_business_environment() -> None:
    """`CON-05` `business_environment` da `BREACHED` — bog'lam ikki tomonlama."""
    con05 = next(c for c in benv.CONSTRAINTS if c.code == "CON-05")
    assert con05.fit is benv.Fit.BREACHED


# --------------------------------------------------------------------------
# 4. Uchinchi topilma: sakkiz rol ↔ uch kod roli
# --------------------------------------------------------------------------


def test_code_knows_exactly_three_roles() -> None:
    assert {r.value for r in Role} == {"viewer", "moderator", "admin"}


def test_only_the_moderator_row_maps_to_a_code_role(report) -> None:
    assert report.code_roles_covered == frozenset({Role.MODERATOR})


def test_absent_roles_are_the_three_platform_roles(report) -> None:
    assert [r.name for r in report.missing_roles] == [
        "Зарегистрированный пользователь (веб)",
        "Региональный оператор",
        "Super Admin",
    ]


def test_no_web_account_surface_exists() -> None:
    """Veb-ro'yxatdan o'tish yo'q: parol maydoni ham, akkaunt jadvali ham."""
    from app.core.config import Settings

    assert not any("password" in name for name in Settings.model_fields)
    for path in APP_DIR.rglob("models.py"):
        src = path.read_text(encoding="utf-8")
        assert "web_users" not in src, path


def test_curator_substitute_is_the_cli_toolchain(report) -> None:
    curator = next(r for r in report.roles if r.name == "Куратор территорий")
    assert curator.build is bifc.RoleBuild.SUBSTITUTED
    for bind in curator.binds:
        assert (SVETA_ROOT / bind).exists(), bind


def test_analyst_substitute_is_the_public_surface(report) -> None:
    """«Аналитик» huquqlari loginsiz hammaga ochiq — vitrina rolsiz."""
    analyst = next(r for r in report.roles if r.name == "Аналитик")
    assert analyst.build is bifc.RoleBuild.SUBSTITUTED
    src = (APP_DIR / "api" / "v1" / "stats.py").read_text(encoding="utf-8")
    assert "require" not in src.replace("required", "")


# --------------------------------------------------------------------------
# 5. To'rtinchi topilma: moderator fe'llarining yarmi yo'q
# --------------------------------------------------------------------------


def test_built_verbs_resolve_to_real_permissions() -> None:
    for verb, permission in bifc.MODERATOR_BUILT_VERBS.items():
        assert verb in bifc.MODERATOR_VERBS
        assert permission in PERMISSIONS[Role.MODERATOR]


def test_missing_verbs_are_confirm_and_split(report) -> None:
    assert report.moderator_missing_verbs == ("подтверждение", "разделение")


def test_no_confirm_or_split_permission_exists() -> None:
    values = {p.value for p in Permission}
    assert not any("confirm" in v or "split" in v for v in values)


def test_no_confirm_or_split_in_admin_service() -> None:
    src = (APP_DIR / "admin" / "service.py").read_text(encoding="utf-8")
    assert "def confirm" not in src
    assert "def split" not in src


# --------------------------------------------------------------------------
# 6. «Ограничения» — `security` reyestriga bog'lam
# --------------------------------------------------------------------------


def test_restriction_locks_resolve_in_security_registry() -> None:
    by_code = {g.code: g for g in sec.GUARANTEES}
    for _, sec_code in bifc.RESTRICTION_LOCKS:
        assert sec_code in by_code, sec_code


def test_mfa_is_still_absent() -> None:
    """2FA «обязательна» — kod bir omilli. Holat o'zgarsa reyestr eskiradi."""
    mfa = next(g for g in sec.GUARANTEES if g.code == "mfa")
    assert mfa.posture is sec.Posture.ABSENT


def test_read_exact_geo_is_substituted_not_granted() -> None:
    """Huquq yo'q — o'rnida kuchliroq taqiq (hech kim ko'rmaydi)."""
    row = next(g for g in sec.GUARANTEES if g.code == "read_exact_geo")
    assert row.mechanism is sec.Mechanism.SUBSTITUTED
    assert not any("read_exact_geo" in p.value for p in Permission)


def test_separation_of_duties_holds_by_construction() -> None:
    """Moderator validatsiya parametrini o'zgartira olmaydi — ruxsatning o'zi yo'q."""
    assert not any("param" in p.value or "config" in p.value for p in Permission)


# --------------------------------------------------------------------------
# 7. Teskari yo'nalish: Overpass ikkala hujjatda ham yo'q
# --------------------------------------------------------------------------


def test_overpass_is_missing_from_brd_section_18(brd_text: str) -> None:
    assert "Overpass" not in _section(brd_text, 18)


def test_overpass_is_the_undeclared_system_in_the_prd_registry() -> None:
    assert bifc.UNDECLARED_SYSTEM in {u.system for u in intreg.UNDECLARED}


# --------------------------------------------------------------------------
# 8. `01` §18 egizaklari — bog'lam ikki tomondan
# --------------------------------------------------------------------------


def test_counterparts_resolve_in_the_prd_registry(report) -> None:
    for row in report.integrations:
        if row.counterpart:
            assert row.counterpart in intreg.ASSESSMENT_BY_SYSTEM, row.system


def test_telegram_overstatement_is_shared_with_the_prd_registry() -> None:
    """Webhook↔polling farqi ikkala reyestrda bitta topilma."""
    telegram = intreg.ASSESSMENT_BY_SYSTEM["Telegram Bot API"]
    assert telegram.warrant is intreg.Warrant.OVERSTATED
    ours = next(r for r in bifc.INTEGRATIONS if r.system == "Telegram Bot API")
    assert "polling" in ours.gap


def test_presumed_twins_stay_presumed() -> None:
    """1055 va geokoder — `01` reyestrida `PRESUMED`; o'zgarsa bu yer eskiradi."""
    for system in ("Региональный канал «1055»", "Геокодер"):
        assert intreg.ASSESSMENT_BY_SYSTEM[system].warrant is intreg.Warrant.PRESUMED


def test_every_bind_resolves() -> None:
    """Har dalil yo modul simvoli, yo repo fayli — to'qima emas."""
    rows = list(bifc.INTEGRATIONS) + list(bifc.ROLES)
    for row in rows:
        label = getattr(row, "system", None) or row.name
        for bind in row.binds:
            if bind.startswith("app.") and ":" in bind:
                mod_name, symbol = bind.split(":")
                mod = importlib.import_module(mod_name)
                target = mod
                for part in symbol.split("."):
                    if hasattr(target, part):
                        target = getattr(target, part)
                        continue
                    fields = getattr(target, "model_fields", {})
                    assert part in fields, f"{label}: {bind}"
                    break
            else:
                assert (SVETA_ROOT / bind).exists(), f"{label}: {bind}"


# --------------------------------------------------------------------------
# 9. Qorovullarning o'zi (82-run qoidasi)
# --------------------------------------------------------------------------


def _rebuild(**kwargs) -> bifc.BusinessInterfacesReport:
    base = dict(integrations=bifc.INTEGRATIONS, roles=bifc.ROLES)
    base.update(kwargs)
    return bifc.BusinessInterfacesReport(**base)


def test_guard_rejects_wrong_row_count() -> None:
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(integrations=bifc.INTEGRATIONS[1:])
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(roles=bifc.ROLES[1:])


def test_guard_rejects_live_without_evidence() -> None:
    rows = list(bifc.INTEGRATIONS)
    idx = next(i for i, r in enumerate(rows) if r.build is bifc.Build.LIVE)
    rows[idx] = replace(rows[idx], binds=())
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(integrations=tuple(rows))


def test_guard_rejects_deferred_with_evidence() -> None:
    rows = list(bifc.INTEGRATIONS)
    idx = next(i for i, r in enumerate(rows) if r.build is bifc.Build.DEFERRED)
    rows[idx] = replace(rows[idx], binds=("app.core.config:Settings",))
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(integrations=tuple(rows))


def test_guard_rejects_ahead_without_gap() -> None:
    rows = list(bifc.INTEGRATIONS)
    idx = next(i for i, r in enumerate(rows) if r.build is bifc.Build.AHEAD)
    rows[idx] = replace(rows[idx], gap="")
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(integrations=tuple(rows))


def test_guard_rejects_every_evidenced_build_without_evidence() -> None:
    """Dalil qorovulining to'rtala a'zosi ham qulf ostida (110-run M6).

    Qorovul `build in (LIVE, PROVISIONED, AHEAD, REJECTED)` to'rtligini
    tekshiradi; mutatsiya uni bitta a'zoga kuchsizlantirsa, qolgan uch
    holat dalilsiz o'tar edi — 108/109 survivorlari sinfi («bor»
    tekshirilardi, «to'liq» emas). LIVE alohida testda; qolgan uchtasi
    shu yerda.
    """
    for target in (bifc.Build.PROVISIONED, bifc.Build.AHEAD, bifc.Build.REJECTED):
        rows = list(bifc.INTEGRATIONS)
        idx = next(i for i, r in enumerate(rows) if r.build is target)
        rows[idx] = replace(rows[idx], binds=())
        with pytest.raises(bifc.BusinessInterfacesError):
            _rebuild(integrations=tuple(rows))


def test_guard_rejects_rejected_without_gap() -> None:
    """`gap` qorovulining `REJECTED` yarmi (110-run M7): AHEAD alohida testda."""
    rows = list(bifc.INTEGRATIONS)
    idx = next(i for i, r in enumerate(rows) if r.build is bifc.Build.REJECTED)
    rows[idx] = replace(rows[idx], gap="")
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(integrations=tuple(rows))


def test_guard_rejects_partial_role_without_gap() -> None:
    rows = list(bifc.ROLES)
    idx = next(i for i, r in enumerate(rows) if r.build is bifc.RoleBuild.PARTIAL)
    rows[idx] = replace(rows[idx], gap="")
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(roles=tuple(rows))


def test_guard_rejects_absent_role_with_evidence() -> None:
    rows = list(bifc.ROLES)
    idx = next(i for i, r in enumerate(rows) if r.build is bifc.RoleBuild.ABSENT)
    rows[idx] = replace(rows[idx], binds=("web/",))
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(roles=tuple(rows))


def test_guard_rejects_partial_and_substituted_without_evidence() -> None:
    """Rol qorovulining uchligi to'liq (110-run M8): BUILT dan boshqa
    ikkala a'zo ham dalilsiz kirmaydi."""
    for target in (bifc.RoleBuild.PARTIAL, bifc.RoleBuild.SUBSTITUTED):
        rows = list(bifc.ROLES)
        idx = next(i for i, r in enumerate(rows) if r.build is target)
        rows[idx] = replace(rows[idx], binds=())
        with pytest.raises(bifc.BusinessInterfacesError):
            _rebuild(roles=tuple(rows))


def test_guard_rejects_absent_role_with_code_role() -> None:
    """`ABSENT` qorovulining ikkinchi yarmi (110-run M9): kod roli ham
    bo'lmaydi — `binds` yarmi alohida testda."""
    donor = next(r.code_role for r in bifc.ROLES if r.code_role is not None)
    rows = list(bifc.ROLES)
    idx = next(i for i, r in enumerate(rows) if r.build is bifc.RoleBuild.ABSENT)
    rows[idx] = replace(rows[idx], code_role=donor)
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(roles=tuple(rows))


def test_guard_rejects_rejected_outside_adr() -> None:
    """`REJECTED` qatorlar ADR-05 to'plamidan tashqariga chiqmaydi (110-run M10).

    Qorovul `rejected <= BANNED_TECH` ni tekshiradi — o'chirilsa,
    istalgan tizimni «ADR bilan chiqarilgan» deb yozib qo'yish jimgina
    o'tar edi.
    """
    rows = list(bifc.INTEGRATIONS)
    idx = next(i for i, r in enumerate(rows) if r.build is bifc.Build.REJECTED)
    rows[idx] = replace(rows[idx], system="RabbitMQ")
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(integrations=tuple(rows))


def test_guard_rejects_unknown_counterpart() -> None:
    rows = list(bifc.INTEGRATIONS)
    rows[0] = replace(rows[0], counterpart="Неизвестная система")
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(integrations=tuple(rows))


def test_guard_rejects_unknown_status_cell() -> None:
    rows = list(bifc.INTEGRATIONS)
    rows[0] = replace(rows[0], status="Неведомый статус")
    with pytest.raises(bifc.BusinessInterfacesError):
        _rebuild(integrations=tuple(rows))


def test_guard_notices_stale_undeclared_finding(monkeypatch) -> None:
    """Overpass `01` §18 ga kirsa — teskari topilma qayta ko'riladi."""
    monkeypatch.setattr(intreg, "UNDECLARED", ())
    with pytest.raises(bifc.BusinessInterfacesError):
        bifc.evaluate()


def test_guard_notices_stale_mfa_claim(monkeypatch) -> None:
    """MFA qurilsa — §19 «Ограничения» bahosi eskiradi va yiqiladi."""
    by_code = {g.code: g for g in sec.GUARANTEES}
    fixed = replace(by_code["mfa"], posture=sec.Posture.ENFORCED)
    patched = tuple(fixed if g.code == "mfa" else g for g in sec.GUARANTEES)
    monkeypatch.setattr(sec, "GUARANTEES", patched)
    with pytest.raises(bifc.BusinessInterfacesError):
        bifc.evaluate()


# --------------------------------------------------------------------------
# 10. Hisobot va indeks
# --------------------------------------------------------------------------


def test_report_counts(report) -> None:
    assert [r.system for r in report.flagged_integrations] == [
        "Telegram Bot API",
        "Telegram-каналы официальных сообщений (регион)",
        "Геокодер",
        "Kafka",
        "Redis",
        "Open Data API",
    ]
    assert report.by_build[bifc.Build.LIVE] == (
        "Telegram Bot API",
        "Обратное геокодирование",
        "Тайловый сервис карты",
        "PostgreSQL + PostGIS",
    )
    assert report.by_build[bifc.Build.DEFERRED] == ("API оператора электросети",)
    assert [r.name for r in report.flagged_roles] == [
        "Зарегистрированный пользователь (веб)",
        "Модератор региона",
        "Региональный оператор",
        "Куратор территорий",
        "Аналитик",
        "Super Admin",
    ]
    assert report.accurate is False


def test_accurate_requires_every_conjunct() -> None:
    """`accurate` — kon'yunksiya: bitta oila tozalangani bilan rost bo'lmaydi.

    Bugun ikkala oila ham bayroqli, shuning uchun `and`→`or` mutatsiyasi
    (110-run M12, `success_holds` sinfi) hisobotning bugungi qiymatida
    ko'rinmasdi. Bu test rollarni «tuzalgan» qiladi (hammasi `BUILT`,
    dalil bilan) — integratsiya bayroqlari turibdi, `accurate` baribir
    `False` qolishi shart.
    """
    healed_roles = tuple(
        replace(
            r,
            build=bifc.RoleBuild.BUILT,
            binds=r.binds or ("app.admin.roles",),
            gap="",
        )
        for r in bifc.ROLES
    )
    healed = _rebuild(roles=healed_roles)
    assert not healed.flagged_roles
    assert healed.accurate is False


def test_flagged_families_do_not_overlap(report) -> None:
    """Indeks `flagged` i yig'indi — bu xavfsizligining o'lchovi."""
    integrations = {r.system for r in report.flagged_integrations}
    roles = {r.name for r in report.flagged_roles}
    assert not integrations & roles


def test_registry_index_entry() -> None:
    from app.admin import registries as reg

    entry = next(e for e in reg.REGISTRIES if e.code == "business_interfaces")
    assert entry.spec == bifc.SPEC
    probe = entry.probe(None)
    assert probe.total == 18
    assert probe.flagged == 12
    assert probe.undeclared == 1

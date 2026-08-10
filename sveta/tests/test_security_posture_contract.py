"""`01` §20 «Security» + BRD «Безопасность» NFR lari ↔ `app/admin/security.py`.

**Nima uchun bu fayl kerak.** §20 butun bo'limni bitta jumlaga
sig'diradi — «Наследуется полностью: RBAC, MFA…» — va shu paytgacha
o'sha jumla hech qayerda o'qilmagan. Fe'lning o'zi tuzoq: «наследуется»
kelib chiqishni bildiradi, holatni emas, va bu repo Toshkent paketining
forki emas. Ya'ni bo'limni «hammasi bor» deb o'qish uchun hech qanday
asos yo'q edi, va tekshirish uchun ham hech narsa yo'q edi.

Fayl **besh** narsani bog'laydi:

1. **Ro'yxatning tuzilishi** — nasrdagi yettita element va jadvalning
   beshta qatori hujjatdan **parse qilinadi**; reyestrda qo'lda
   ko'chirilgan nusxa yo'q (61-run sabog'i). Jadvalning uchta katagi
   `;` bilan ikkita mustaqil da'voni bir qatorga qo'ygan — qatorlar
   soni shundan hisoblanadi, ya'ni hujjatga `;` qo'shilsa fayl
   yiqiladi va yangi da'vo javobsiz qololmaydi.
2. **BRD ning «Безопасность» NFR lari** — §20 ularni «полностью»
   meros qiladi, lekin ularning matni §20 da yo'q. Ular BRD dan
   parse qilinadi.
3. **Holatlarning ta'rifi xossa sifatida** — `ENFORCED` deb yozilgan
   har qator uchun `where` **haqiqiy simvolga** yechiladi va `lock`
   **mavjud fayl** bo'ladi. Bayroqqa ishonilmaydi (69-run qoidasi).
4. **Himoyalanmagan kafolatga qulf** — §20 ning «ПДн не собираются»
   qatori bu runga qadar `UNDEFENDED` edi: da'vo rost, lekin uni
   o'lchaydigan test yo'q. Endi `users` ning ustunlari oq ro'yxat
   bilan qulflangan va §20 sanagan har uch tur ПДн alohida
   tekshiriladi.
5. **`MISSTATED` ning asosi** — «идентификатор Telegram хранится в
   псевдонимизированном виде» bajarilmasligining **sababi** kodda
   ko'rsatiladi: `tg_id` yetkazish manzili sifatida ishlatiladi.
   Sabab yo'qolsa (masalan xabar boshqa kalit bilan yuborilsa) bu
   test yiqiladi va holatni qayta ko'rish kerak bo'ladi.

**Ataylab tekshirilmaydi:** `note` va `narrower` matnlarining
**mazmuni**. Ular keyingi o'quvchi uchun sabab, artefakt emas
(70-run bilan bir xil qaror). Uzunligi esa tekshiriladi — bo'sh izoh
qatorni o'qib bo'lmaydigan qiladi.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.admin import auth, roles, security
from app.admin.security import GUARANTEES, Mechanism, Posture
from app.db.models import User

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
BRD_DOC = REPO_ROOT / "BRD_Samarkand.md"

SECURITY_SECTION = "## 20. Security"
SECURITY_SECTION_END = "## 21. Analytics"

BRD_NFR_SECTION = "| Категория | ID | Требование | Значение | Статус |"
BRD_SECURITY_CATEGORY = "Безопасность"

#: Nasrdagi ro'yxatni ochadigan so'z. Hujjat matni o'zgarsa parse
#: bo'sh qaytadi va quyidagi testlar buni ko'rsatadi.
INHERITANCE_PREFIX = "Наследуется полностью:"


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _section(doc: Path, start: str, end: str) -> str:
    text = doc.read_text(encoding="utf-8")
    assert start in text, f"{doc.name}: «{start}» topilmadi"
    body = text.split(start, 1)[1]
    assert end in body, f"{doc.name}: «{end}» topilmadi"
    return body.split(end, 1)[0]


def _security_section() -> str:
    return _section(PRD_DOC, SECURITY_SECTION, SECURITY_SECTION_END)


def prose_items() -> tuple[str, ...]:
    """§20 nasridagi «наследуется полностью: …» ro'yxati."""
    body = _security_section()
    line = next(
        (ln for ln in body.splitlines() if ln.strip().startswith(INHERITANCE_PREFIX)),
        "",
    )
    assert line, f"§20 da «{INHERITANCE_PREFIX}» qatori yo'q"
    tail = line.split(":", 1)[1].strip().rstrip(".")
    return tuple(part.strip() for part in tail.split(",") if part.strip())


def table_claims() -> dict[str, tuple[str, ...]]:
    """§20 jadvali: yorliq → `;` bilan ajratilgan da'volar.

    Jadvalning uchta katagi ikkita **mustaqil** da'voni bir qatorga
    qo'ygan (GDPR, ПДн, Геоданные). Ular reyestrda alohida qator
    bo'lishi kerak, aks holda bittasi ikkinchisining orqasida
    yashirinadi — «ПДн не собираются» rost, «псевдонимизированный вид»
    esa yo'q, va bitta qator ikkalasini ham qamrab olardi.
    """
    claims: dict[str, tuple[str, ...]] = {}
    for line in _security_section().splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 2:
            continue
        label, comment = cells
        if label in {"Пункт", ""} or set(label) <= {"-", ":"}:
            continue
        claims[label] = tuple(part.strip() for part in comment.split(";") if part.strip())
    assert claims, "§20 jadvali parse qilinmadi"
    return claims


def brd_security_nfrs() -> dict[str, str]:
    """BRD NFR jadvalining «Безопасность» qatorlari: ID → talab.

    Jadvalda kategoriya faqat **birinchi** qatorda yoziladi, keyingilari
    bo'sh katak bilan davom etadi — shuning uchun oxirgi ko'rilgan
    kategoriya eslab qolinadi.
    """
    text = BRD_DOC.read_text(encoding="utf-8")
    assert BRD_NFR_SECTION in text, "BRD da NFR jadvali topilmadi"
    body = text.split(BRD_NFR_SECTION, 1)[1]
    found: dict[str, str] = {}
    category = ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if found and stripped.startswith("#"):
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if set(cells[0]) <= {"-", ":"} and cells[0]:
            continue
        if cells[0]:
            category = cells[0]
        if category == BRD_SECURITY_CATEGORY and cells[1].startswith("NFR-"):
            found[cells[1]] = cells[2]
    assert found, "BRD da «Безопасность» NFR lari topilmadi"
    return found


# --------------------------------------------------------------------------
# 1. Ro'yxat hujjatdan keladi
# --------------------------------------------------------------------------


def test_the_prose_list_is_read_from_the_document_not_from_the_registry() -> None:
    items = prose_items()
    assert len(items) == 7, f"§20 nasrida yettita element kutilgan, {len(items)} ta topildi"
    assert "RBAC" in items
    assert any("outage.read_exact_geo" in item for item in items)


def test_every_prose_item_has_exactly_one_row() -> None:
    """Nasrdagi element atomik: ikkiga bo'linmaydi va tashlanmaydi."""
    counts = {item: 0 for item in prose_items()}
    for g in GUARANTEES:
        if g.doc_item in counts:
            counts[g.doc_item] += 1
    missing = sorted(item for item, n in counts.items() if n == 0)
    doubled = sorted(item for item, n in counts.items() if n > 1)
    assert not missing, f"javobsiz qolgan elementlar: {missing}"
    assert not doubled, f"ikki marta javob berilgan: {doubled}"


def test_each_table_cell_gets_one_row_per_semicolon_separated_claim() -> None:
    """Katakdagi ikkinchi da'vo birinchisining orqasida yashirinmaydi."""
    claims = table_claims()
    for label, parts in claims.items():
        rows = sorted(g.claim for g in GUARANTEES if g.doc_item == label)
        assert rows == list(range(len(parts))), (
            f"«{label}» katagida {len(parts)} ta da'vo bor, reyestrda {rows} — "
            "har bir `;` alohida qator talab qiladi"
        )


def test_the_table_really_contains_multi_claim_cells() -> None:
    """Yuqoridagi test bo'sh ish qilmasin.

    Agar hujjatdagi `;` lar yo'qolsa, oldingi test har qatorga bitta
    javob talab qilib **o'tib ketardi** va ikkinchi da'volarni kimdir
    jimgina o'chirgan bo'lardi.
    """
    multi = {label for label, parts in table_claims().items() if len(parts) > 1}
    assert multi >= {"GDPR", "ПДн", "Геоданные"}, (
        f"ko'p da'voli kataklar kutilgan, topilgani: {sorted(multi)}"
    )


def test_no_row_is_anchored_outside_the_documents() -> None:
    anchors = set(prose_items()) | set(table_claims())
    nfrs = set(brd_security_nfrs())
    for g in GUARANTEES:
        if g.doc_item:
            assert g.doc_item in anchors, f"{g.code}: «{g.doc_item}» hujjatda yo'q"
        if g.nfr:
            assert g.nfr in nfrs, f"{g.code}: {g.nfr} BRD da «Безопасность» qatori emas"


def test_every_inherited_security_nfr_is_answered() -> None:
    covered = {g.nfr for g in GUARANTEES if g.nfr}
    assert covered == set(brd_security_nfrs()), (
        "§20 «наследуется полностью» deydi, ya'ni BRD ning har bir "
        "«Безопасность» NFR i javob talab qiladi"
    )


def test_codes_are_unique() -> None:
    codes = [g.code for g in GUARANTEES]
    assert len(codes) == len(set(codes))


# --------------------------------------------------------------------------
# 2. Reyestrning ichki qoidalari
# --------------------------------------------------------------------------


def test_the_registry_obeys_its_own_rules() -> None:
    assert security.registry_errors() == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [("where", ""), ("lock", ""), ("note", "")],
)
def test_registry_rules_reject_a_broken_enforced_row(field: str, value: str) -> None:
    """Qoidalar tekshiruvi haqiqatan ishlaydi."""
    broken = replace(security.GUARANTEE_BY_CODE["rbac"], **{field: value})
    original = security.GUARANTEES
    try:
        security.GUARANTEES = (broken,) + tuple(g for g in original if g.code != "rbac")
        assert security.registry_errors()
    finally:
        security.GUARANTEES = original


def test_an_undefended_row_may_not_carry_a_lock() -> None:
    original = security.GUARANTEES
    fake = replace(
        security.GUARANTEE_BY_CODE["mfa"],
        posture=Posture.UNDEFENDED,
        lock="tests/test_admin_auth.py",
    )
    try:
        security.GUARANTEES = (fake,) + tuple(g for g in original if g.code != "mfa")
        assert any("UNDEFENDED" in problem for problem in security.registry_errors())
    finally:
        security.GUARANTEES = original


def test_a_named_only_row_must_explain_itself_at_length() -> None:
    """Qisqa izoh `NAMED_ONLY` da yetarli emas.

    Aynan `SUBSTITUTED` va `NAMED_ONLY` qatorlari keyingi o'quvchini
    «hujjatdagi nomni tiklaymiz» degan qarorga chaqiradi, ya'ni
    ularning izohi bir-ikki so'z bo'lolmaydi.
    """
    original = security.GUARANTEES
    fake = replace(security.GUARANTEE_BY_CODE["mfa"], note="Yo'q.")
    try:
        security.GUARANTEES = (fake,) + tuple(g for g in original if g.code != "mfa")
        assert any("izoh yetarli emas" in problem for problem in security.registry_errors())
    finally:
        security.GUARANTEES = original


def test_a_misstated_row_must_say_what_holds_instead() -> None:
    original = security.GUARANTEES
    fake = replace(security.GUARANTEE_BY_CODE["tg_id_pseudonymous"], narrower="")
    try:
        security.GUARANTEES = (fake,) + tuple(
            g for g in original if g.code != "tg_id_pseudonymous"
        )
        assert any("narrower" in problem for problem in security.registry_errors())
    finally:
        security.GUARANTEES = original


# --------------------------------------------------------------------------
# 3. `ENFORCED` — bayroq emas, dalil
# --------------------------------------------------------------------------


def _resolve(where: str) -> object:
    module_name, _, symbol = where.partition(":")
    module = __import__(module_name, fromlist=["*"])
    target: object = module
    for part in symbol.split("."):
        target = getattr(target, part)
    return target


def test_every_enforced_row_points_at_a_real_symbol() -> None:
    for g in GUARANTEES:
        if g.posture is not Posture.ENFORCED:
            continue
        assert ":" in g.where, f"{g.code}: `where` `modul:simvol` ko'rinishida bo'lishi kerak"
        assert _resolve(g.where) is not None


def test_every_lock_is_an_existing_test_file() -> None:
    for g in GUARANTEES:
        if not g.lock:
            continue
        path = SVETA_ROOT / g.lock
        assert path.is_file(), f"{g.code}: qulf fayli yo'q — {g.lock}"


def test_a_lock_is_required_for_every_guarantee_we_call_enforced() -> None:
    """`ENFORCED` ning ta'rifi — modulning o'zagi.

    Mexanizm bor, lekin uni olib tashlaganda hech narsa yiqilmasa,
    kafolat `UNDEFENDED`. Bu test o'sha ta'rifni qulflaydi.
    """
    unlocked = [g.code for g in GUARANTEES if g.posture is Posture.ENFORCED and not g.lock]
    assert not unlocked, f"qulfsiz `ENFORCED`: {unlocked}"


# --------------------------------------------------------------------------
# 4. «ПДн не собираются» — himoyalanmagan kafolatga qulf
# --------------------------------------------------------------------------


def test_users_table_carries_no_column_outside_the_allowlist() -> None:
    """§20: «Не собираются: ни ФИО, ни телефон, ни username».

    Bu — bu running asosiy qulfi. Da'vo 71-run gacha rost edi, lekin
    uni o'lchaydigan narsa yo'q edi: `username` ustunini qo'shadigan
    bitta migratsiya butun to'plamni yashil qoldirgan holda §20 ni
    yolg'onga aylantirardi.
    """
    columns = {c.name for c in User.__table__.columns}
    extra = sorted(columns - security.USERS_ALLOWED_COLUMNS)
    assert not extra, (
        f"`users` da yangi ustun(lar) paydo bo'ldi: {extra}. Agar ular ПДн "
        "bo'lmasa — `USERS_ALLOWED_COLUMNS` ga **ataylab** qo'shing va "
        "sababini yozing; ПДн bo'lsa — `01` §20 buzilgan."
    )
    assert security.USERS_ALLOWED_COLUMNS - columns == frozenset(), (
        "oq ro'yxatda modelda yo'q ustun qolgan — ro'yxat eskirgan"
    )


@pytest.mark.parametrize("kind", ["ФИО", "телефон", "username"])
def test_each_personal_data_kind_named_by_the_spec_is_absent(kind: str) -> None:
    columns = {c.name for c in User.__table__.columns}
    found = security.pdn_columns_found(columns)
    assert kind not in found, f"§20 taqiqlagan ПДн topildi: {kind} → {found.get(kind)}"


def test_the_personal_data_kinds_are_the_three_the_spec_names() -> None:
    """Ro'yxat hujjatdan: uchtasi ham §20 ning ПДн katagida yozilgan."""
    cell = " ".join(table_claims()["ПДн"])
    for kind in security.PDN_COLUMN_HINTS:
        assert kind.lower() in cell.lower(), f"«{kind}» §20 ning ПДн katagida yo'q"
    assert len(security.PDN_COLUMN_HINTS) == 3


def test_the_personal_data_detector_actually_detects() -> None:
    """Qulf bo'sh ish qilmasin: qo'shilgan ustun ko'rinadimi."""
    columns = {c.name for c in User.__table__.columns} | {"username", "phone"}
    found = security.pdn_columns_found(columns)
    assert found["username"] == ("username",)
    assert found["телефон"] == ("phone",)
    assert "ФИО" not in found


def test_the_detector_is_not_fooled_by_letter_case() -> None:
    """`Username` ham `username` — SQL da nom registrsiz.

    Bu ataylab alohida test: registr bo'yicha aniq taqqoslash
    yuqoridagi tekshiruvni **o'tkazib yuborardi** va migratsiyada
    `Username` deb yozilgan ustun ko'rinmay qolardi.
    """
    found = security.pdn_columns_found({"Username", "PHONE", "Last_Name"})
    assert set(found) == {"username", "телефон", "ФИО"}


# --------------------------------------------------------------------------
# 5. `MISSTATED` ning sababi kodda turadi
# --------------------------------------------------------------------------


def test_the_telegram_id_is_a_delivery_address_not_only_an_identifier() -> None:
    """`tg_id` ni bir tomonlama xeshlab bo'lmasligining sababi.

    Xabar `sender.send(chat_id=…)` bilan yuboriladi va qiymat
    `tg_id` dan keladi. Shu bog'lanish yo'qolsa — masalan yuborish
    boshqa kalitga o'tsa — `MISSTATED` holatining asosi ham yo'qoladi
    va uni qayta ko'rish kerak bo'ladi.
    """
    from app.notifications import service

    source = inspect.getsource(service)
    tree = ast.parse(source)
    passes_tg_id = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg != "chat_id":
                continue
            if isinstance(kw.value, ast.Attribute) and kw.value.attr == "tg_id":
                passes_tg_id = True
    assert passes_tg_id, (
        "`chat_id=…tg_id` chaqiruvi topilmadi — `tg_id` endi yetkazish "
        "manzili emas, ya'ni `tg_id_pseudonymous` holatini qayta ko'ring"
    )


def test_the_raw_telegram_id_is_still_stored_as_an_integer() -> None:
    """Pseudonim emasligining ikkinchi yarmi: ustun xesh emas."""
    column = User.__table__.columns["tg_id"]
    assert column.type.python_type is int
    assert not column.nullable


def test_the_codebase_knows_what_pseudonymisation_means() -> None:
    """Aktor identifikatori haqiqatan pseudonim — farq ataylab.

    `MISSTATED` «biz pseudonimni bilmaymiz» degani emas: bu repoda
    pseudonim bor va u ishlaydi. Shuning uchun `tg_id` ning xomligi
    bilmaslik emas, **majburiyat**.
    """
    actor = auth.Actor(name="nilufar", role=roles.Role.ADMIN)
    assert actor.id == auth.uuid.uuid5(auth.ACTOR_NAMESPACE, "nilufar")
    assert "nilufar" not in str(actor.id)


# --------------------------------------------------------------------------
# 6. Hujjatdagi sonlar
# --------------------------------------------------------------------------


def test_the_reidentification_precision_is_read_from_the_document() -> None:
    cell = " ".join(table_claims()["Геоданные"])
    match = re.search(r"точность\s+(\d+)\s*м", cell)
    assert match, "«точность N м» topilmadi"
    assert int(match.group(1)) == security.DOC_MAHALLA_PRECISION_M


def test_the_public_grid_is_coarser_than_the_risk_the_document_assumes() -> None:
    """§20 riskni 50 m ga qarab baholaydi, katakcha esa undan katta.

    Ya'ni kafolat hujjat kutganidan **kuchli**. Tekshiruv `h3` ga
    bog'liq emas — hujjatning o'z sonini o'qiydi (`05` §3.1 dagi
    «≈ 174 m»), aks holda kutubxona versiyasi testni boshqarardi.
    """
    design = (REPO_ROOT / "05_Technical_Design.md").read_text(encoding="utf-8")
    match = re.search(r"r9[^\n]*?≈\s*(\d+)\s*[mм]\b", design)
    assert match, "`05` da r9 ning qirra uzunligi topilmadi"
    assert int(match.group(1)) > security.DOC_MAHALLA_PRECISION_M


# --------------------------------------------------------------------------
# 7. Hisobot
# --------------------------------------------------------------------------


def test_the_section_is_not_trustworthy_today_and_says_why() -> None:
    report = security.evaluate()
    assert not report.trustworthy
    assert "mfa" in report.absent
    assert "rate_limit_api" in report.absent
    assert "mahalla_reid_check" in report.absent
    assert report.misstated == ("tg_id_pseudonymous",)


def test_nothing_is_undefended_after_this_run() -> None:
    """`UNDEFENDED` bo'sh bo'lishi kerak — qulflar shu run da yozildi."""
    assert security.evaluate().undefended == ()


@pytest.mark.parametrize("code", ["tg_id_pseudonymous", "mfa"])
def test_a_single_unresolved_row_is_enough_to_lose_trust(code: str) -> None:
    """`trustworthy` uchala holatni ham hisobga oladi.

    Bugungi reyestrda `ABSENT` ham bor, ya'ni «`MISSTATED` ni
    formuladan olib tashlash» hisobotning javobini o'zgartirmasdi va
    mutatsiya jimgina omon qolardi. Shuning uchun tekshiruv sun'iy
    reyestrda o'tkaziladi: bitta ochilmagan qator + faqat yashillar.
    """
    original = security.GUARANTEES
    keep = security.GUARANTEE_BY_CODE[code]
    try:
        security.GUARANTEES = (keep,) + tuple(
            g for g in original if g.posture is Posture.ENFORCED
        )
        report = security.evaluate()
        assert not report.trustworthy, f"{code} ishonchni yiqitmadi"
    finally:
        security.GUARANTEES = original


def test_an_undefended_row_alone_loses_trust() -> None:
    """`UNDEFENDED` bugun bo'sh, ya'ni uni faqat sun'iy qator o'lchaydi."""
    original = security.GUARANTEES
    fake = replace(
        security.GUARANTEE_BY_CODE["pdn_not_collected"],
        posture=Posture.UNDEFENDED,
        lock="",
    )
    try:
        security.GUARANTEES = (fake,) + tuple(
            g for g in original if g.posture is Posture.ENFORCED
        )
        assert not security.evaluate().trustworthy
    finally:
        security.GUARANTEES = original


def test_the_substituted_mechanism_is_visible_in_the_report() -> None:
    """`read_exact_geo` yashil, lekin hujjat atagan nom bilan emas.

    Hisobot buni yashirmaydi: aks holda keyingi o'quvchi
    `Permission.OUTAGE_READ_EXACT_GEO` ni «tiklaydi» va gate siz
    ruxsat eshik ochadi.
    """
    report = security.evaluate()
    assert "read_exact_geo" in report.substituted
    assert security.GUARANTEE_BY_CODE["read_exact_geo"].posture is Posture.ENFORCED


def test_the_named_permission_does_not_exist_in_the_role_matrix() -> None:
    values = {p.value for p in roles.Permission}
    assert "outage.read_exact_geo" not in values, (
        "ruxsat qo'shilgan — `read_exact_geo` qatorini qayta ko'ring: "
        "gate siz ruxsat kafolatni kuchaytirmaydi"
    )


def test_the_counts_add_up() -> None:
    report = security.evaluate()
    assert sum(report.counts.values()) == len(GUARANTEES)
    assert report.counts[Posture.ENFORCED] >= 5


def test_a_vacuous_row_is_not_counted_as_a_gap() -> None:
    """`VACUOUS` va `EXTERNAL` hisobotni yiqitmaydi (67-run sababi)."""
    original = security.GUARANTEES
    try:
        security.GUARANTEES = tuple(
            g
            for g in original
            if g.posture in (Posture.VACUOUS, Posture.EXTERNAL, Posture.ENFORCED)
        )
        assert security.evaluate().trustworthy
    finally:
        security.GUARANTEES = original


def test_mfa_is_absent_because_a_single_bearer_token_is_one_factor() -> None:
    """`ABSENT` bayroq emas: admin autentifikatsiyasi bitta sarlavha."""
    assert auth.HEADER_NAME == "X-Admin-Token"
    signature = inspect.signature(auth.authenticate)
    assert list(signature.parameters) == ["token"], (
        "`authenticate` ikkinchi omilni oldi — `mfa` qatorini qayta ko'ring"
    )
    assert security.GUARANTEE_BY_CODE["mfa"].mechanism is Mechanism.NAMED_ONLY

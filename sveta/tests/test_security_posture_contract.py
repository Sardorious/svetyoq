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

## 164-run: 8–12-bo'limlar

71-run «20 mutatsiya, 0 survivor» degan edi, lekin o'sha o'lchov
`verdict` `returncode != 0` bo'lgan davrda olingan (`pytest` ning
`rc=4` i yolg'on `KILLED` berardi; tuzatilgani 126-run). Qayta
o'lchov: **70 mutatsiya → 6 KILLED, 64 SURVIVOR**. Quyidagi
bo'limlar o'sha survivorlarning **62 tasini** qulflaydi; ikkitasi
ekvivalent (`lower()` → `casefold()` — ustun nomlari ASCII;
`GUARANTEE_BY_CODE` ni teskari tartibda qurish — kodlar noyob, ya'ni
lug'atning **mazmuni** o'zgarmaydi).

Uch sinf topildi:

* **kod sirtga chiqadi.** `Posture` ning oltala va `Mechanism` ning
  to'rttala qiymati hech qayerda o'lchanmagan edi. Ular ikki yo'l
  bilan ko'rinadi: `registry_errors()` ning «izoh yetarli emas»
  xabari (reyestrni yozayotgan odam o'qiydigan matn) va
  `SecurityReport.counts` ning kalitlari. `SPEC` esa
  `app/admin/registries.py` orqali `GET /api/v1/admin/registries` ga
  chiqadi;
* **qorovullar bir-birini soyalagan.** `registry_errors()` ning o'nta
  qoidasidan oltitasi umuman o'lchanmagan edi: mavjud
  `test_registry_rules_reject_a_broken_enforced_row` faqat
  «ro'yxat bo'sh emas» ni so'raydi, ya'ni **qaysi** qoida
  ishlaganini emas. Endi har qoida **yolg'iz** buziladi va xabar
  **butunlay** solishtiriladi (`match=` yetarli emas — u `re.search`,
  161 va 162 runlarning sabog'i);
* **reyestrning o'zi o'lchanmagan.** `where` va `lock` uchun faqat
  **mavjudlik** tekshirilardi: `rbac` ning `where` i `audit` ga,
  `lock` i boshqa mavjud test fayliga ko'chsa — jim. `spec`,
  `posture` va `mechanism` ustunlari esa umuman tekshirilmasdi.
  Qulf — literal `REGISTRY` jadvali (17 qator × to'qqiz ustun) va
  tartib.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import FrozenInstanceError, replace
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


# --------------------------------------------------------------------------
# 8. Holat va mexanizm kodlari — ular sirtga chiqadi
# --------------------------------------------------------------------------
#
# Ikkala `StrEnum` ham bugungacha faqat **o'zi orqali** tekshirilardi:
# testlar `Posture.ENFORCED` ni yozadi va uni `Posture.ENFORCED` bilan
# solishtiradi, ya'ni qiymatni istalgan matnga almashtirsa ham to'plam
# yashil qolardi. Qiymat esa ikki joyda ko'rinadi: `registry_errors()`
# ning «… uchun izoh yetarli emas» xabarida (`f"{g.mechanism}"` —
# `StrEnum` o'z **qiymatini** beradi) va `counts` ning kalitlarida.


def test_the_posture_codes_are_the_literal_strings_the_report_carries() -> None:
    assert {p.name: p.value for p in Posture} == {
        "ENFORCED": "enforced",
        "UNDEFENDED": "undefended",
        "VACUOUS": "vacuous",
        "ABSENT": "absent",
        "MISSTATED": "misstated",
        "EXTERNAL": "external",
    }


def test_the_mechanism_codes_are_the_literal_strings_the_message_prints() -> None:
    assert {m.name: m.value for m in Mechanism} == {
        "AS_WRITTEN": "as_written",
        "SUBSTITUTED": "substituted",
        "NAMED_ONLY": "named_only",
        "UNNAMED": "unnamed",
    }


def test_the_postures_run_from_trustworthy_to_untrustworthy() -> None:
    """Tartib `Posture` ning docstringida **da'vo** qilingan.

    U shunchaki bezak emas: `counts` shu tartibda quriladi, ya'ni
    hisobotni o'qiydigan odam «ishonsa bo'ladi» dan «ishonib
    bo'lmaydi» ga qarab yuradi.
    """
    assert [p.name for p in Posture] == [
        "ENFORCED",
        "UNDEFENDED",
        "VACUOUS",
        "ABSENT",
        "MISSTATED",
        "EXTERNAL",
    ]


def test_the_mechanisms_keep_their_declared_order() -> None:
    assert [m.name for m in Mechanism] == [
        "AS_WRITTEN",
        "SUBSTITUTED",
        "NAMED_ONLY",
        "UNNAMED",
    ]


def test_the_counts_are_keyed_in_posture_order() -> None:
    assert list(security.evaluate().counts) == list(Posture)


def test_the_spec_address_points_at_the_security_section_of_the_prd() -> None:
    """`SPEC` — `GET /api/v1/admin/registries` javobidagi manzil.

    `app/admin/registries.py` uni o'sha endpointga uzatadi, ya'ni
    noto'g'ri son operatorni hujjatning **boshqa** bo'limiga yuboradi.
    Tekshiruv ikki qismli: shakl `01 §<son>` va son — aynan shu fayl
    parse qiladigan sarlavhaning nomeri.
    """
    match = re.search(r"##\s*(\d+)\.", SECURITY_SECTION)
    assert match, f"«{SECURITY_SECTION}» dan bo'lim nomeri o'qilmadi"
    assert security.SPEC == f"01 §{int(match.group(1))}"


# --------------------------------------------------------------------------
# 9. Reyestrning har bir qorovuli — yolg'iz va xabari bilan
# --------------------------------------------------------------------------
#
# `test_registry_rules_reject_a_broken_enforced_row` faqat «ro'yxat
# bo'sh emas» ni so'raydi, ya'ni **qaysi** qoida ishlaganini emas —
# oltita qoidani butunlay o'chirsa ham u yashil qolardi. Quyida har
# qoida alohida buziladi va xabar **butunlay** solishtiriladi: bu
# modulda xabar mahsulot sirti, chunki reyestrni yozayotgan odam
# faqat shu matnni ko'radi.

#: `SUBSTITUTED`/`NAMED_ONLY` uchun yetarli uzunlikdagi izoh.
LONG_NOTE = "x" * 60


def _row(**overrides: object) -> security.Guarantee:
    """Bitta sun'iy qator: sukut bo'yicha **hech bir** qoidani buzmaydi."""
    fields: dict[str, object] = {
        "code": "probe",
        "spec": "01 §20",
        "posture": Posture.EXTERNAL,
        "mechanism": Mechanism.UNNAMED,
        "doc_item": "PCI DSS",
        "note": LONG_NOTE,
    }
    fields.update(overrides)
    return security.Guarantee(**fields)  # type: ignore[arg-type]


def _errors(monkeypatch: pytest.MonkeyPatch, *rows: security.Guarantee) -> tuple[str, ...]:
    monkeypatch.setattr(security, "GUARANTEES", tuple(rows))
    return security.registry_errors()


def test_the_probe_row_itself_breaks_no_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quyidagi testlar bo'sh ish qilmasin: asos toza."""
    assert _errors(monkeypatch, _row()) == ()


@pytest.mark.parametrize("note", ["", "   ", "\n\t "])
def test_a_row_whose_note_is_only_whitespace_is_reported(
    monkeypatch: pytest.MonkeyPatch, note: str
) -> None:
    assert _errors(monkeypatch, _row(note=note)) == ("probe: izoh yo'q",)


def test_a_row_without_any_anchor_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _errors(monkeypatch, _row(doc_item="", nfr="")) == (
        "probe: langar yo'q — `doc_item` ham, `nfr` ham bo'sh",
    )


@pytest.mark.parametrize(("doc_item", "nfr"), [("PCI DSS", ""), ("", "NFR-S-03")])
def test_either_anchor_alone_is_enough(
    monkeypatch: pytest.MonkeyPatch, doc_item: str, nfr: str
) -> None:
    assert _errors(monkeypatch, _row(doc_item=doc_item, nfr=nfr)) == ()


def test_a_claim_number_without_a_document_item_is_meaningless(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _errors(monkeypatch, _row(doc_item="", nfr="NFR-S-03", claim=1)) == (
        "probe: `claim` `doc_item` siz ma'nosiz",
    )


def test_a_negative_claim_number_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _errors(monkeypatch, _row(claim=-1)) == ("probe: `claim` manfiy",)


@pytest.mark.parametrize(
    ("where", "lock"),
    [
        ("", ""),
        ("app.admin.roles:PERMISSIONS", ""),
        ("", "tests/test_admin_roles.py"),
    ],
)
def test_an_enforced_row_needs_both_a_mechanism_and_a_lock(
    monkeypatch: pytest.MonkeyPatch, where: str, lock: str
) -> None:
    """Ikkalasi ham shart — **yarmi** ham `ENFORCED` emas.

    Ikkinchi va uchinchi holat aynan `and` ni `or` ga almashtirishni
    ushlaydi: mexanizm bor, qulf yo'q — bu ta'rif bo'yicha
    `UNDEFENDED`, modulning butun mavjudlik sababi.
    """
    row = _row(
        posture=Posture.ENFORCED,
        mechanism=Mechanism.AS_WRITTEN,
        where=where,
        lock=lock,
    )
    assert _errors(monkeypatch, row) == ("probe: ENFORCED uchun `where` va `lock` shart",)


def test_an_undefended_row_carrying_a_lock_is_reported_by_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _row(posture=Posture.UNDEFENDED, lock="tests/test_admin_roles.py")
    assert _errors(monkeypatch, row) == ("probe: UNDEFENDED da `lock` bo'lmaydi — u ENFORCED",)


@pytest.mark.parametrize(
    ("where", "lock"),
    [
        ("app.admin.roles:PERMISSIONS", ""),
        ("", "tests/test_admin_roles.py"),
        ("app.admin.roles:PERMISSIONS", "tests/test_admin_roles.py"),
    ],
)
def test_an_absent_row_may_carry_neither_a_mechanism_nor_a_lock(
    monkeypatch: pytest.MonkeyPatch, where: str, lock: str
) -> None:
    """`or` — `and` emas: **yarim** to'ldirilgan qator ham `ABSENT` emas."""
    row = _row(
        posture=Posture.ABSENT,
        mechanism=Mechanism.NAMED_ONLY,
        where=where,
        lock=lock,
    )
    assert _errors(monkeypatch, row) == ("probe: ABSENT da `where`/`lock` bo'lmaydi",)


@pytest.mark.parametrize("narrower", ["", "   "])
def test_a_misstated_row_needs_a_narrower_that_says_something(
    monkeypatch: pytest.MonkeyPatch, narrower: str
) -> None:
    row = _row(posture=Posture.MISSTATED, mechanism=Mechanism.NAMED_ONLY, narrower=narrower)
    assert _errors(monkeypatch, row) == ("probe: MISSTATED uchun `narrower` shart",)


def test_only_a_misstated_row_may_carry_a_narrower(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _errors(monkeypatch, _row(narrower="o'rnida shu bajariladi")) == (
        "probe: `narrower` faqat MISSTATED da",
    )


@pytest.mark.parametrize("mechanism", [Mechanism.SUBSTITUTED, Mechanism.NAMED_ONLY])
def test_both_calling_mechanisms_must_explain_themselves_at_sixty_characters(
    monkeypatch: pytest.MonkeyPatch, mechanism: Mechanism
) -> None:
    """Bo'sag'a ham, ikkala mexanizm ham qulflanadi.

    Xabar mexanizm **qiymatini** bosib chiqaradi (`StrEnum.__str__`),
    ya'ni bu test 8-bo'limdagi kod jadvalining ikkinchi yarmi.
    """
    short = _errors(monkeypatch, _row(mechanism=mechanism, note="x" * 59))
    assert short == (f"probe: {mechanism.value} uchun izoh yetarli emas",)
    assert _errors(monkeypatch, _row(mechanism=mechanism, note="x" * 60)) == ()


def test_every_broken_row_is_reported_not_only_the_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    problems = _errors(monkeypatch, _row(code="a", note=""), _row(code="b", note=""))
    assert problems == ("a: izoh yo'q", "b: izoh yo'q")


# --------------------------------------------------------------------------
# 10. Reyestrning o'zi — literal jadval
# --------------------------------------------------------------------------
#
# `where` va `lock` uchun shu paytgacha faqat **mavjudlik**
# tekshirilardi (`_resolve` yechiladimi, fayl bormi), ya'ni `rbac` ning
# mexanizmi `audit` niki bilan almashsa yoki qulf boshqa **mavjud**
# test fayliga ko'chsa — hech narsa yiqilmasdi. `spec`, `posture` va
# `mechanism` ustunlari esa umuman o'lchanmagan edi: `VACUOUS` ni
# `EXTERNAL` ga («buzish uchun narsa yo'q» → «bizning ishimiz emas»)
# almashtirish jim o'tardi, holbuki bu ikki holatning **sababi**
# butunlay boshqa.

#: (code, spec, doc_item, claim, nfr, posture, mechanism, where, lock)
REGISTRY: tuple[tuple[str, str, str, int, str, Posture, Mechanism, str, str], ...] = (
    (
        "rbac", "01 §20", "RBAC", 0, "",
        Posture.ENFORCED, Mechanism.AS_WRITTEN,
        "app.admin.roles:PERMISSIONS", "tests/test_admin_roles.py",
    ),
    (
        "mfa", "01 §20 + BRD NFR-S-01", "MFA для админ-ролей", 0, "NFR-S-01",
        Posture.ABSENT, Mechanism.NAMED_ONLY,
        "", "",
    ),
    (
        "encryption", "01 §20", "шифрование", 0, "",
        Posture.EXTERNAL, Mechanism.UNNAMED,
        "", "",
    ),
    (
        "audit", "01 §20", "аудит", 0, "",
        Posture.ENFORCED, Mechanism.AS_WRITTEN,
        "app.admin.audit:record", "tests/test_admin_audit.py",
    ),
    (
        "session_password_policy", "01 §20", "политика сессий и паролей", 0, "",
        Posture.VACUOUS, Mechanism.UNNAMED,
        "", "",
    ),
    (
        "geom_split", "01 §20", "разделение `geom_exact` / `geom_public`", 0, "",
        Posture.ENFORCED, Mechanism.AS_WRITTEN,
        "app.reports.models:Report", "tests/test_privacy_jitter_contract.py",
    ),
    (
        "read_exact_geo", "01 §20 + BRD NFR-S-02", "право `outage.read_exact_geo`", 0, "NFR-S-02",
        Posture.ENFORCED, Mechanism.SUBSTITUTED,
        "app.api.v1.outages:OutagePublic", "tests/test_api_surface_contract.py",
    ),
    (
        "pci_dss", "01 §20", "PCI DSS", 0, "",
        Posture.VACUOUS, Mechanism.UNNAMED,
        "", "",
    ),
    (
        "gdpr", "01 §20", "GDPR", 0, "",
        Posture.EXTERNAL, Mechanism.UNNAMED,
        "", "",
    ),
    (
        "data_localisation", "01 §20 + 01 NFR-S-04", "GDPR", 1, "",
        Posture.EXTERNAL, Mechanism.UNNAMED,
        "", "",
    ),
    (
        "iso_27001", "01 §20", "ISO 27001", 0, "",
        Posture.EXTERNAL, Mechanism.UNNAMED,
        "", "",
    ),
    (
        "pdn_not_collected", "01 §20", "ПДн", 0, "",
        Posture.ENFORCED, Mechanism.AS_WRITTEN,
        "app.admin.security:USERS_ALLOWED_COLUMNS", "tests/test_security_posture_contract.py",
    ),
    (
        "tg_id_pseudonymous", "01 §20", "ПДн", 1, "",
        Posture.MISSTATED, Mechanism.NAMED_ONLY,
        "app.reports.models:User.tg_id", "tests/test_api_surface_contract.py",
    ),
    (
        "geo_grid_snap", "01 §20", "Геоданные", 0, "",
        Posture.ENFORCED, Mechanism.AS_WRITTEN,
        "app.geo.jitter:public_point", "tests/test_privacy_jitter_contract.py",
    ),
    (
        "mahalla_reid_check", "01 §20 (OQ-04)", "Геоданные", 1, "",
        Posture.ABSENT, Mechanism.NAMED_ONLY,
        "", "",
    ),
    (
        "rate_limit_reports", "BRD NFR-S-03", "", 0, "NFR-S-03",
        Posture.ENFORCED, Mechanism.AS_WRITTEN,
        "app.reports.intake:check_rate_limit", "tests/test_reports_intake.py",
    ),
    (
        "rate_limit_api", "BRD NFR-S-03 + 01 §16", "", 0, "NFR-S-03",
        Posture.ABSENT, Mechanism.NAMED_ONLY,
        "", "",
    ),
)


def test_the_registry_is_exactly_these_rows_in_this_order() -> None:
    """Har ustun — alohida da'vo, ya'ni har biri alohida yiqiladi.

    Tartib ham qulflanadi: reyestr §20 ni **o'qish tartibida**
    (nasr → jadval → BRD NFR lari) yozadi va hisobotning ro'yxatlari
    shundan quriladi.
    """
    actual = tuple(
        (g.code, g.spec, g.doc_item, g.claim, g.nfr, g.posture, g.mechanism, g.where, g.lock)
        for g in GUARANTEES
    )
    assert actual == REGISTRY


# --------------------------------------------------------------------------
# 11. ПДн detektorining ishoralari
# --------------------------------------------------------------------------
#
# Uchala ro'yxatdan bugungacha faqat uchta ishora o'lchangan edi
# (`username`, `phone`, `last_name`), ya'ni qolgan o'n bittasini
# jimgina o'chirib qo'yish mumkin edi — va aynan o'sha ro'yxat
# «qanday nom bilan kirib kelgan ПДн ko'rinadi» degan savolga javob
# beradi.

PDN_HINTS: dict[str, tuple[str, ...]] = {
    "ФИО": ("name", "first_name", "last_name", "full_name", "fio", "patronymic"),
    "телефон": ("phone", "msisdn", "tel", "mobile"),
    "username": ("username", "user_name", "handle", "nickname", "login"),
}


def test_the_personal_data_hints_are_exactly_these() -> None:
    assert security.PDN_COLUMN_HINTS == PDN_HINTS


@pytest.mark.parametrize(
    ("kind", "hint"),
    [(kind, hint) for kind, hints in PDN_HINTS.items() for hint in hints],
)
def test_every_single_hint_is_detected(kind: str, hint: str) -> None:
    assert security.pdn_columns_found({hint}) == {kind: (hint,)}


def test_the_hits_come_back_sorted_not_in_hint_order() -> None:
    """`sorted` — bezak emas: xato xabari barqaror bo'lishi kerak.

    `телефон` ning ishoralari ataylab alifbo tartibida emas, ya'ni
    `sorted` tushib qolsa natija boshqa bo'ladi.
    """
    found = security.pdn_columns_found({"phone", "msisdn", "tel", "mobile"})
    assert found["телефон"] == ("mobile", "msisdn", "phone", "tel")


# --------------------------------------------------------------------------
# 12. Hisobotning shakli
# --------------------------------------------------------------------------


def test_the_report_carries_every_guarantee() -> None:
    """`guarantees` — `GET /api/v1/admin/registries` dagi `total`.

    `app/admin/registries.py: _probe_security` uni aynan shu maydondan
    oladi, ya'ni qisqargan ro'yxat operatorga «reyestrda o'n olti
    qator» deb ko'rsatardi.
    """
    assert security.evaluate().guarantees == GUARANTEES


def test_the_flagged_lists_keep_registry_order() -> None:
    """«O'qish tartibida» — `SecurityReport` ning docstringidagi da'vo."""
    report = security.evaluate()
    order = [g.code for g in GUARANTEES]
    for flagged in (report.absent, report.undefended, report.misstated, report.substituted):
        assert list(flagged) == sorted(flagged, key=order.index)


def test_a_guarantee_and_its_report_are_immutable() -> None:
    """Reyestr — o'qiladigan artefakt, ish holati emas.

    `evaluate()` `GUARANTEES` ning **o'zini** qaytaradi, ya'ni
    o'zgaruvchan qator hisobotni chaqiruvchi tomonidan jimgina
    tahrirlanadigan qilardi.
    """
    with pytest.raises(FrozenInstanceError):
        GUARANTEES[0].posture = Posture.ABSENT  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        security.evaluate().trustworthy = True  # type: ignore[misc]

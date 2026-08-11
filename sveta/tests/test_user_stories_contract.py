"""`01` §9 «User Stories» / §10 «Use Cases» ↔ `app.release.user_stories`.

**Bu fayl nimani qulflaydi.** Reyestr sof e'lon — u o'zi haqida hech
narsani isbotlamaydi (75–77, 82–87 runlar bilan bir xil shakl). Isbot
shu yerda va u **uch xil manbadan** olinadi:

1. **Hujjatning o'zi** — `01_PRD_Samarkand.md` ning §9/§10 bo'limlari:
   hikoyalar soni, prioritetlar, rollar, gherkin bloklari, bandlar
   soni, stsenariylarning sarlavhalari, qadamlari va katak nomlari.
2. **Reyestrning ichki invariantlari** — uchala o'qning taqsimoti,
   hisoblanadigan xossalar (`vacuous`, `split_promises`,
   `unwitnessed_promises`, `realizations_touched`) va
   `__post_init__` ning beshta qorovuli, ularning **har biri**
   alohida yiqitiladi.
3. **Fayl tizimi** — har `binds` yozuvi haqiqiy modul, test yoki
   asbobni ko'rsatadimi.
4. **Kodning tuzilishi (`ast`)** — §8 (91-run): «ekranda turgan son
   haqiqatan `total_reports` mi» degan savolning kod tomoni. Simvol
   **matn bilan qidirilmaydi** (86-run ning qoidasi: yozilgan kod
   qidirilayotgan kodga aylanadi) — daraxtdan olinadi.

⚠️ **Matn qidirilmaydi.** `Clause.text` hujjatdagi bandning
**qisqartirilgan** nusxasi (`C-5` da ayniqsa), shuning uchun uni
hujjatga so'zma-so'z tenglashtirish faylni o'z nusxasini o'lchashga
majbur qilardi (61-run ning sabog'i). Uning o'rniga hujjatning
`Then`/`And` **qatorlari sanaladi** va reyestrning `promise`
maydonlari bilan bijeksiya talab qilinadi; reyestrda qator ko'proq
bo'lishiga faqat `split_promises` hisoblab bergan farq qadar ruxsat
beriladi.

## `ast` qatlami — 91-run

90-run `binds` ni faqat **mavjudlik** darajasida tekshirgan edi: modul
bor, test bor, asbob bor. §8 uni yopadi — har `modul:simvol` yozuvi
daraxtdagi haqiqiy nomga yechiladi va bo'limning uchta hukmi kodning
tuzilishidan **hisoblanadi**:

* `C-3`/`C-4` — `render()` `situation` dan aynan qaysi maydonlarni
  o'qiydi (`==`, `<=` emas) va `app/bot/reply.py` da
  `independent_reporters` degan nom **umuman yo'q**;
* `C-5` — `decide()` `coverage_ok` bo'yicha bo'linadi va taqiqlangan
  verdiktni qaytaradi (nom `Verdict` ning qiymatidan olinadi, satr
  qidirilmaydi);
* `UC-S1` — `errors.py` ning **sinf atributlari** orasida
  `out_of_region` bor, `DOC_ERROR_CODES` ning ikkalasi ham yo'q.

⚠️ **Fayl 88–91-runlarning birortasida ham yurgizilmagan** — sandbox
ketma-ket to'rt marta ko'tarilmadi
(`useradd failed: No space left on device`), ya'ni na `pytest`, na
`ruff`, na mutatsiya. Har tasdiq `Read` bilan qo'lda manbaga
solishtirilgan (`reply.py` ning `Situation`/`decide`/`render` i,
`errors.py` ning oltita `code` i, `handlers.py:388-402` ning register
qatorlari, yigirma bitta bind). Ziddiyat chiqsa modul ham testsiz
yozilgan (89-run) — ayb testda bo'lishi shart emas.
👤 `cleanup-sessions.ps1`.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from app.release import user_stories as us

TESTS_DIR = Path(__file__).resolve().parent
SVETA = TESTS_DIR.parent
ROOT = SVETA.parent

PRD = ROOT / "01_PRD_Samarkand.md"

#: `**US-S1 (P0).** Как житель Самарканда, я хочу …`
STORY_RE = re.compile(r"^\*\*(US-S\d+) \((P\d)\)\.\*\* Как ([^,]+),", re.M)

#: ` ```gherkin … ``` `
GHERKIN_RE = re.compile(r"```gherkin\n(.*?)```", re.S)

#: `### UC-S1. Репорт об отключении`
USE_CASE_RE = re.compile(r"^### (UC-S\d+)\. (.+)$", re.M)

#: «Основной сценарий» katagidagi raqamlangan qadam. Raqamdan oldin
#: satr boshi yoki nuqta bo'lishi **majburiy** — aks holda «H3.» ning
#: uchligi qadam deb sanalardi.
STEP_RE = re.compile(r"(?:^|\.\s+)(\d+)\.\s")


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _section(text: str, number: int) -> str:
    """`## N.` sarlavhasidan keyingi navbatdagi `## ` gacha."""
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## \d+\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


def _doc_stories(spec9: str) -> dict[str, dict[str, str]]:
    """`US-S* → {priority, role, block}`, hujjatdagi tartibda."""
    found = list(STORY_RE.finditer(spec9))
    result: dict[str, dict[str, str]] = {}
    for index, match in enumerate(found):
        end = found[index + 1].start() if index + 1 < len(found) else len(spec9)
        result[match.group(1)] = {
            "priority": match.group(2),
            "role": match.group(3),
            "block": spec9[match.start() : end],
        }
    return result


def _gherkin(block: str) -> list[str]:
    """Blokdagi gherkin qatorlari; gherkin yo'q bo'lsa — bo'sh ro'yxat."""
    found = GHERKIN_RE.search(block)
    if found is None:
        return []
    return [line.strip() for line in found.group(1).splitlines() if line.strip()]


def _doc_use_cases(spec10: str) -> dict[str, dict[str, str]]:
    """`UC-S* → {title, <katak nomi>: <qiymat>}`."""
    found = list(USE_CASE_RE.finditer(spec10))
    result: dict[str, dict[str, str]] = {}
    for index, match in enumerate(found):
        end = found[index + 1].start() if index + 1 < len(found) else len(spec10)
        cells: dict[str, str] = {"title": match.group(2).strip()}
        for line in spec10[match.start() : end].splitlines():
            if not line.startswith("|"):
                continue
            parts = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(parts) != 2:
                continue
            key, value = parts
            if key == "Поле" or set(key) <= {"-", ":"}:
                continue
            cells[key] = value
        result[match.group(1)] = cells
    return result


@pytest.fixture(scope="module")
def spec9() -> str:
    if not PRD.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip("01_PRD_Samarkand.md bu muhitda yo'q")
    return _section(PRD.read_text(encoding="utf-8"), 9)


@pytest.fixture(scope="module")
def spec10() -> str:
    if not PRD.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip("01_PRD_Samarkand.md bu muhitda yo'q")
    return _section(PRD.read_text(encoding="utf-8"), 10)


@pytest.fixture(scope="module")
def report() -> us.UserStoriesReport:
    return us.evaluate()


# --------------------------------------------------------------------------
# Yaroqsiz reyestr qurish uchun yordamchilar
# --------------------------------------------------------------------------


def _story(**kwargs: object) -> us.Story:
    base: dict[str, object] = {
        "code": "US-X",
        "role": "rol",
        "priority": "P0",
        "gherkin": False,
        "reachable": us.Reachable.UNWRITTEN,
        "note": "izoh",
        "binds": (),
    }
    base.update(kwargs)
    return us.Story(**base)


def _clause(**kwargs: object) -> us.Clause:
    base: dict[str, object] = {
        "code": "C-X",
        "story": "US-X",
        "promise": "vada",
        "text": "matn",
        "realized": us.Realized.SUBSTITUTED,
        "named": us.Named.SILENT,
        "note": "izoh",
        "binds": (),
        "gap": "farq",
    }
    base.update(kwargs)
    return us.Clause(**base)


def _report(
    stories: tuple[us.Story, ...] = (),
    clauses: tuple[us.Clause, ...] = (),
    use_cases: tuple[us.UseCase, ...] = (),
) -> us.UserStoriesReport:
    return us.UserStoriesReport(stories=stories, clauses=clauses, use_cases=use_cases)


def _bind_targets(bind: str) -> list[Path]:
    """`binds` yozuvi ko'rsatishi mumkin bo'lgan fayllar."""
    target = bind.split(":", 1)[0]
    if target.endswith(".py"):
        return [SVETA / target]
    parts = target.split(".")
    return [SVETA.joinpath(*parts).with_suffix(".py"), SVETA.joinpath(*parts, "__init__.py")]


def _all_items() -> tuple[us.Story | us.Clause | us.UseCase, ...]:
    return (*us.STORIES, *us.CLAUSES, *us.USE_CASES)


# --------------------------------------------------------------------------
# 1. Reyestrning shakli
# --------------------------------------------------------------------------


def test_spec_constant_names_both_sections() -> None:
    assert us.SPEC == "01 §9/§10"


def test_registry_sizes_match_declared_counts() -> None:
    assert len(us.STORIES) == us.SPEC_STORIES == 5
    assert len(us.CLAUSES) == us.SPEC_CLAUSES == 9
    assert len(us.USE_CASES) == us.SPEC_USE_CASES == 3


def test_story_codes_are_document_order() -> None:
    assert us.STORY_CODES == ("US-S1", "US-S2", "US-S3", "US-S4", "US-S5")
    assert us.STORY_CODES == tuple(s.code for s in us.STORIES)


def test_clause_and_use_case_codes_are_sequential() -> None:
    assert tuple(c.code for c in us.CLAUSES) == tuple(f"C-{n}" for n in range(1, 10))
    assert tuple(u.code for u in us.USE_CASES) == ("UC-S1", "UC-S2", "UC-S3")


def test_priorities_do_not_decrease() -> None:
    """Hujjat hikoyalarni prioritet bo'yicha yozadi — tartib qulflanadi."""
    priorities = [s.priority for s in us.STORIES]
    assert priorities == sorted(priorities)
    assert priorities == ["P0", "P0", "P1", "P1", "P2"]


def test_only_one_story_has_no_gherkin() -> None:
    without = tuple(s.code for s in us.STORIES if not s.gherkin)
    assert without == (us.STORY_WITHOUT_GHERKIN,)
    assert len(us.STORIES) - len(without) == us.SPEC_GHERKIN_STORIES == 4


def test_every_row_explains_itself() -> None:
    for item in _all_items():
        assert item.note.strip(), f"{item.code}: izoh yo'q"


def test_every_row_carries_evidence() -> None:
    for item in _all_items():
        assert isinstance(item.binds, tuple), f"{item.code}: kortej emas"
        assert item.binds, f"{item.code}: dalil yo'q"


# --------------------------------------------------------------------------
# 2. Uch o'q
# --------------------------------------------------------------------------


def test_axis_membership_sets() -> None:
    assert us.REALIZED_KEPT == frozenset({us.Realized.BUILT})
    assert us.REACHABLE_LIVE == frozenset({us.Reachable.REACHABLE, us.Reachable.PARTIAL})
    assert us.NAMED_KNOWN == frozenset({us.Named.TESTED, us.Named.CITED})


def test_axes_have_expected_arity() -> None:
    assert len(us.Realized) == 5
    assert len(us.Reachable) == 4
    assert len(us.Named) == 4


def test_only_miscited_is_deliberately_unused() -> None:
    """`MISCITED` bo'sh va shu holicha qoladi — 88-run xatoni tuzatgan."""
    used_realized = {c.realized for c in us.CLAUSES} | {u.realized for u in us.USE_CASES}
    used_reachable = {s.reachable for s in us.STORIES} | {u.reachable for u in us.USE_CASES}
    used_named = {c.named for c in us.CLAUSES} | {u.named for u in us.USE_CASES}
    assert used_realized == set(us.Realized)
    assert used_reachable == set(us.Reachable)
    assert set(us.Named) - used_named == {us.Named.MISCITED}


def test_realized_distribution(report: us.UserStoriesReport) -> None:
    assert report.by_realized == {
        us.Realized.BUILT: ("C-7", "C-9"),
        us.Realized.SUBSTITUTED: ("C-1", "C-2", "C-3", "C-4", "C-8"),
        us.Realized.RENAMED: (),
        us.Realized.INVERTED: ("C-5",),
        us.Realized.ABSENT: ("C-6",),
    }


def test_reachable_distribution(report: us.UserStoriesReport) -> None:
    assert report.by_reachable == {
        us.Reachable.REACHABLE: ("US-S2", "US-S5"),
        us.Reachable.PARTIAL: (),
        us.Reachable.UNREACHABLE: ("US-S1", "US-S3"),
        us.Reachable.UNWRITTEN: ("US-S4",),
    }


def test_named_distribution(report: us.UserStoriesReport) -> None:
    assert report.by_named == {
        us.Named.TESTED: ("C-9",),
        us.Named.CITED: (),
        us.Named.SILENT: tuple(f"C-{n}" for n in range(1, 9)),
        us.Named.MISCITED: (),
    }


def test_clauses_grouped_by_story(report: us.UserStoriesReport) -> None:
    assert report.by_story == {
        "US-S1": ("C-1", "C-2"),
        "US-S2": ("C-3", "C-4", "C-5"),
        "US-S3": ("C-6", "C-7"),
        "US-S4": (),
        "US-S5": ("C-8", "C-9"),
    }


# --------------------------------------------------------------------------
# 3. Hisoblanadigan xossalar
# --------------------------------------------------------------------------


def test_seven_of_nine_clauses_diverge(report: us.UserStoriesReport) -> None:
    expected = ("C-1", "C-2", "C-3", "C-4", "C-5", "C-6", "C-8")
    assert tuple(c.code for c in report.diverged) == expected
    assert len(report.diverged) == 7


def test_inverted_is_a_strict_subset_of_diverged(report: us.UserStoriesReport) -> None:
    """Teskari bajarilgan band alohida o'lchanadi — narxi boshqa."""
    assert tuple(c.code for c in report.inverted) == ("C-5",)
    assert set(report.inverted) < set(report.diverged)


def test_vacuous_follows_the_story_axis(report: us.UserStoriesReport) -> None:
    """Baho bandning o'zidan emas, hikoyaning `Given` idan keladi."""
    assert tuple(c.code for c in report.vacuous) == ("C-1", "C-2", "C-6", "C-7")


def test_repo_names_exactly_one_clause(report: us.UserStoriesReport) -> None:
    assert tuple(c.code for c in report.unnamed) == tuple(f"C-{n}" for n in range(1, 9))
    assert report.named_count == 1


def test_split_promise_is_computed_not_declared(report: us.UserStoriesReport) -> None:
    """`US-S2` ning bitta va'dasi botning ikki yo'lida ikki xil son."""
    assert report.split_promises == {"independent-count": ("C-3", "C-4")}


def test_registry_row_surplus_equals_the_split(report: us.UserStoriesReport) -> None:
    """Reyestrda banddan ko'p qator bo'lishiga faqat bo'linish sabab."""
    promises = {c.promise for c in report.clauses}
    surplus = sum(len(codes) - 1 for codes in report.split_promises.values())
    assert len(report.clauses) - len(promises) == surplus == 1


def test_empty_mahallas_blocks_two_unlike_clauses(report: us.UserStoriesReport) -> None:
    assert tuple(c.code for c in report.blocked_by_empty_mahallas) == ("C-6", "C-8")
    assert report.realizations_touched == frozenset(
        {us.Realized.ABSENT, us.Realized.SUBSTITUTED}
    )


def test_the_built_clause_that_is_never_checked(report: us.UserStoriesReport) -> None:
    """`C-7` — qurilgan, lekin `Given` i ro'y bermaydi."""
    assert tuple(c.code for c in report.unwitnessed_promises) == ("C-7",)
    assert set(report.unwitnessed_promises) < set(report.vacuous)
    assert not set(report.unwitnessed_promises) & set(report.diverged)


def test_story_without_a_checkable_claim(report: us.UserStoriesReport) -> None:
    assert report.stories_without_gherkin == ("US-S4",)


def test_all_three_use_cases_diverge(report: us.UserStoriesReport) -> None:
    assert tuple(u.code for u in report.use_cases_diverged) == ("UC-S1", "UC-S2", "UC-S3")


def test_only_the_lived_built_clause_may_omit_a_gap() -> None:
    """`C-9` yagona farqsiz qator; qolgan sakkiztasi farqni nomlaydi."""
    assert {c.code for c in us.CLAUSES if c.gap} == {f"C-{n}" for n in range(1, 9)}
    assert all(u.gap for u in us.USE_CASES)


def test_four_conditions_are_measured_separately(report: us.UserStoriesReport) -> None:
    """82-run ning sabog'i: birlashtirilgan shart mutatsiyani yashiradi."""
    assert report.promises_hold is False
    assert report.preconditions_hold is False
    assert report.naming_holds is False
    assert report.use_cases_hold is False
    assert report.accurate is False


def test_evaluate_is_pure_and_argument_free() -> None:
    first, second = us.evaluate(), us.evaluate()
    assert first == second
    assert first.stories is us.STORIES
    assert first.clauses is us.CLAUSES
    assert first.use_cases is us.USE_CASES


# --------------------------------------------------------------------------
# 4. `__post_init__` — har qorovul alohida yiqitiladi
# --------------------------------------------------------------------------


def test_duplicate_codes_are_rejected() -> None:
    with pytest.raises(us.UserStoriesError, match="takrorlanadi"):
        _report(stories=(_story(), _story()))


def test_a_bare_string_is_not_a_tuple_of_binds() -> None:
    """87-run ning survivori: `("x")` — satr, va u bo'ylab iteratsiya harf beradi."""
    with pytest.raises(us.UserStoriesError, match="kortej emas"):
        _report(stories=(_story(binds="app.bot.service"),))


def test_bind_without_a_dot_is_rejected() -> None:
    with pytest.raises(us.UserStoriesError, match="shakli buzilgan"):
        _report(stories=(_story(binds=("nuqtasiz",)),))


def test_clause_must_belong_to_a_known_story() -> None:
    with pytest.raises(us.UserStoriesError, match="noma'lum hikoya"):
        _report(
            stories=(_story(code="US-A", gherkin=True),),
            clauses=(_clause(story="US-B"),),
        )


def test_built_clause_under_an_unreachable_given_needs_a_gap() -> None:
    """`C-7` ning qoidasi: yetib bo'lmaydigan shart ostida «bajarildi» yetmaydi."""
    story = _story(code="US-A", gherkin=True, reachable=us.Reachable.UNREACHABLE)
    with pytest.raises(us.UserStoriesError, match="farq yozilmagan"):
        _report(
            stories=(story,),
            clauses=(_clause(story="US-A", realized=us.Realized.BUILT, gap=""),),
        )


def test_built_clause_under_a_reachable_given_may_omit_the_gap() -> None:
    """`C-9` ning yo'li — qorovul faqat yetib bo'lmaydigan shartda ishlaydi."""
    story = _story(code="US-A", gherkin=True, reachable=us.Reachable.REACHABLE)
    built = _clause(story="US-A", realized=us.Realized.BUILT, gap="")
    assert _report(stories=(story,), clauses=(built,)).promises_hold is True


def test_tested_verdict_requires_a_named_test() -> None:
    story = _story(code="US-A", gherkin=True, reachable=us.Reachable.REACHABLE)
    with pytest.raises(us.UserStoriesError, match="test nomlanmagan"):
        _report(
            stories=(story,),
            clauses=(_clause(story="US-A", named=us.Named.TESTED, binds=("app.x:y",)),),
        )


def test_gherkin_flag_must_match_the_clauses() -> None:
    with pytest.raises(us.UserStoriesError, match="mos kelmaydi"):
        _report(stories=(_story(code="US-A", gherkin=True),))
    with pytest.raises(us.UserStoriesError, match="mos kelmaydi"):
        _report(
            stories=(_story(code="US-A", gherkin=False),),
            clauses=(_clause(story="US-A"),),
        )


def test_a_story_without_gherkin_cannot_be_graded() -> None:
    with pytest.raises(us.UserStoriesError, match="shart baholangan"):
        _report(stories=(_story(gherkin=False, reachable=us.Reachable.REACHABLE),))


# --------------------------------------------------------------------------
# 5. Konstantalar ↔ dalillar
# --------------------------------------------------------------------------


def _clauses_binding(needle: str) -> set[str]:
    return {c.code for c in us.CLAUSES if any(needle in b for b in c.binds)}


def test_each_shown_count_belongs_to_exactly_one_path() -> None:
    """Bitta va'da, ikkita yo'l, ikkita **har xil** son."""
    assert us.SHOWN_COUNT_FIELDS == ("total_reports", "others")
    assert _clauses_binding("total_reports") == {"C-3"}
    assert _clauses_binding("others") == {"C-4"}


def test_the_promised_count_is_bound_to_both_paths() -> None:
    assert _clauses_binding(us.PROMISED_COUNT_COLUMN) == {"C-3", "C-4"}
    assert _clauses_binding(us.PROMISED_COUNT_FUNCTION) == {"C-3"}
    assert us.PROMISED_COUNT_COLUMN not in us.SHOWN_COUNT_FIELDS


def test_the_promised_window_is_shorter_than_the_incident(report: us.UserStoriesReport) -> None:
    assert us.PROMISED_WINDOW_HOURS == 1
    assert "C-3" in {c.code for c in report.diverged}


def test_section_9_knows_fewer_verdicts_than_the_spec() -> None:
    assert us.VERDICTS_KNOWN_TO_SECTION_9 == 2
    assert us.VERDICTS_IN_SPEC == 4
    assert us.VERDICTS_KNOWN_TO_SECTION_9 < us.VERDICTS_IN_SPEC
    assert us.FORBIDDEN_VERDICT != us.REQUIRED_VERDICT


def test_language_switch_is_not_a_command() -> None:
    assert us.BOT_COMMANDS == 2
    assert us.LANGUAGE_SWITCH_STEPS > 1


def test_named_error_codes_are_claims_not_artefacts() -> None:
    """Ikkalasi ham hujjatning so'zi; bittasi kodda boshqacha ataladi."""
    assert len(us.DOC_ERROR_CODES) == 2
    assert all(code == code.upper() for code in us.DOC_ERROR_CODES)
    assert us.BUILT_ERROR_CODE.upper() not in us.DOC_ERROR_CODES


def test_use_case_step_constants_match_the_rows() -> None:
    by_code = {u.code: u for u in us.USE_CASES}
    assert by_code["UC-S2"].steps == us.USE_CASE_2_STEPS
    assert by_code["UC-S3"].steps == us.USE_CASE_3_STEPS
    assert 0 < us.USE_CASE_2_STEPS_BUILT < us.USE_CASE_2_STEPS


def test_every_bind_points_at_something_that_exists() -> None:
    for item in _all_items():
        for bind in item.binds:
            found = any(path.exists() for path in _bind_targets(bind))
            assert found, f"{item.code}: {bind} — fayl yo'q"


def test_citation_sites_are_the_evidence_of_the_named_clause() -> None:
    named = next(c for c in us.CLAUSES if c.named is us.Named.TESTED)
    resolved = {p for bind in named.binds for p in _bind_targets(bind) if p.exists()}
    for site in us.CITATION_SITES:
        assert (SVETA / site).exists(), site
        assert SVETA / site in resolved, site
    assert (SVETA / us.USE_CASE_CITATION_SITE).exists()


# --------------------------------------------------------------------------
# 6. §9 — hujjat ↔ reyestr
# --------------------------------------------------------------------------


def test_document_declares_five_stories(spec9: str) -> None:
    doc = _doc_stories(spec9)
    assert tuple(doc) == us.STORY_CODES
    assert len(doc) == us.SPEC_STORIES


def test_document_priorities_match_the_registry(spec9: str) -> None:
    doc = _doc_stories(spec9)
    assert {code: item["priority"] for code, item in doc.items()} == {
        s.code: s.priority for s in us.STORIES
    }


def test_document_roles_match_the_registry(spec9: str) -> None:
    doc = _doc_stories(spec9)
    assert {code: item["role"] for code, item in doc.items()} == {
        s.code: s.role for s in us.STORIES
    }


def test_gherkin_blocks_match_the_flag(spec9: str) -> None:
    doc = _doc_stories(spec9)
    written = {code for code, item in doc.items() if _gherkin(item["block"])}
    assert written == {s.code for s in us.STORIES if s.gherkin}
    assert us.STORY_WITHOUT_GHERKIN not in written
    assert len(written) == us.SPEC_GHERKIN_STORIES


def test_every_block_states_one_given_and_one_when(spec9: str) -> None:
    for code, item in _doc_stories(spec9).items():
        lines = _gherkin(item["block"])
        if not lines:
            continue
        assert len([ln for ln in lines if ln.startswith("Given ")]) == 1, code
        assert len([ln for ln in lines if ln.startswith("When ")]) == 1, code


def test_document_clauses_map_one_to_one_onto_promises(
    spec9: str,
    report: us.UserStoriesReport,
) -> None:
    """Matn taqqoslanmaydi — qatorlar sanaladi va va'dalar bilan bog'lanadi."""
    by_story = report.by_story
    total = 0
    for code, item in _doc_stories(spec9).items():
        lines = _gherkin(item["block"])
        promised = [ln for ln in lines if ln.startswith(("Then ", "And "))]
        total += len(promised)
        registry = {c.promise for c in us.CLAUSES if c.code in by_story[code]}
        assert len(promised) == len(registry), code
    assert total == us.SPEC_CLAUSES - 1 == len({c.promise for c in us.CLAUSES})


# --------------------------------------------------------------------------
# 7. §10 — hujjat ↔ reyestr
# --------------------------------------------------------------------------


def test_document_declares_three_use_cases(spec10: str) -> None:
    doc = _doc_use_cases(spec10)
    assert tuple(doc) == tuple(u.code for u in us.USE_CASES)
    assert len(doc) == us.SPEC_USE_CASES


def test_use_case_titles_match_the_registry(spec10: str) -> None:
    doc = _doc_use_cases(spec10)
    assert {code: item["title"] for code, item in doc.items()} == {
        u.code: u.title for u in us.USE_CASES
    }


def test_use_case_steps_are_counted_from_the_document(spec10: str) -> None:
    doc = _doc_use_cases(spec10)
    for use_case in us.USE_CASES:
        cell = doc[use_case.code]["Основной сценарий"]
        numbers = [int(n) for n in STEP_RE.findall(cell)]
        assert numbers == list(range(1, use_case.steps + 1)), use_case.code


def test_spec_fields_are_the_union_not_a_single_table(spec10: str) -> None:
    doc = _doc_use_cases(spec10)
    union: set[str] = set()
    for item in doc.values():
        union |= set(item) - {"title"}
    assert union == set(us.SPEC_FIELDS)
    assert len(us.SPEC_FIELDS) == 6
    assert len(set(doc["UC-S3"]) - {"title"}) < len(us.SPEC_FIELDS)


def test_first_use_case_names_both_error_codes(spec10: str) -> None:
    cell = _doc_use_cases(spec10)["UC-S1"]["Ошибки"]
    for code in us.DOC_ERROR_CODES:
        assert code in cell


def test_third_use_case_promises_a_reversible_migration(spec10: str) -> None:
    """Hujjat kuchsizrog'ini emas, kuchlirog'ini va'da qilgan."""
    cell = _doc_use_cases(spec10)["UC-S3"]["Ошибки"]
    assert "обратим" in cell
    reversible = next(u for u in us.USE_CASES if u.code == "UC-S3")
    assert reversible.gap
    assert reversible.realized is not us.Realized.BUILT


# --------------------------------------------------------------------------
# 8. `ast` — hukm kodning tuzilishidan
# --------------------------------------------------------------------------


def _module_path(dotted: str) -> Path:
    """`app.bot.reply` → fayl. Paket ham, modul ham bo'lishi mumkin."""
    base = SVETA.joinpath(*dotted.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.exists():
            return candidate
    raise AssertionError(f"{dotted} — modul topilmadi")


def _tree(dotted: str) -> ast.Module:
    return ast.parse(_module_path(dotted).read_text(encoding="utf-8"))


def _class(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"{name} — sinf topilmadi")


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"{name} — funksiya topilmadi")


def _assigned_names(body: list[ast.stmt]) -> tuple[str, ...]:
    """`x: T = ...` va `x = ...` chap tomonlari, tartibi saqlangan."""
    names: list[str] = []
    for node in body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, ast.Assign):
            targets = list(node.targets)
        names.extend(t.id for t in targets if isinstance(t, ast.Name))
    return tuple(names)


def _string_attributes(cls: ast.ClassDef) -> dict[str, str]:
    """Sinfning `ism = "qiymat"` atributlari. Metod ichi ko'rilmaydi."""
    found: dict[str, str] = {}
    for node in cls.body:
        if not isinstance(node, (ast.AnnAssign, ast.Assign)):
            continue
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            continue
        for name in _assigned_names([node]):
            found[name] = node.value.value
    return found


def _attributes_of(node: ast.AST, base: str) -> frozenset[str]:
    """`base.<atribut>` ko'rinishidagi murojaatlar."""
    return frozenset(
        child.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Attribute)
        and isinstance(child.value, ast.Name)
        and child.value.id == base
    )


def _identifiers(node: ast.AST) -> frozenset[str]:
    """Daraxtdagi barcha nomlar. Satrlar va izohlar **kirmaydi**."""
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.add(child.id)
        elif isinstance(child, ast.Attribute):
            names.add(child.attr)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(child.name)
        elif isinstance(child, ast.arg):
            names.add(child.arg)
        elif isinstance(child, ast.alias):
            names.add(child.asname or child.name)
        elif isinstance(child, ast.keyword) and child.arg is not None:
            names.add(child.arg)
    return frozenset(names)


def _module_symbols(dotted: str) -> frozenset[str]:
    """Modulning sathi: yuqori daraja + `Sinf.atribut` / `Sinf.metod`."""
    names: set[str] = set()
    tree = _tree(dotted)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
            names.update(f"{node.name}.{n}" for n in _assigned_names(node.body))
            names.update(
                f"{node.name}.{inner.name}"
                for inner in node.body
                if isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    names.update(_assigned_names(tree.body))
    return frozenset(names)


def _registrations(tree: ast.Module) -> list[ast.Call]:
    """`router.<...>.register(handler, *filtrlar)` chaqiruvlari."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "register"
        and node.args
    ]


def _is_command_filter(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"Command", "CommandStart"}
    )


def test_every_symbol_bind_resolves_to_a_real_symbol() -> None:
    """`modul:simvol` — mavjudlik emas, **yechilish**."""
    checked = 0
    for item in _all_items():
        for bind in item.binds:
            if ":" not in bind or bind.split(":", 1)[0].endswith(".py"):
                continue
            module, symbol = bind.split(":", 1)
            assert symbol in _module_symbols(module), f"{item.code}: {bind}"
            checked += 1
    assert checked >= len(us.CLAUSES)


def test_shown_counts_are_fields_of_the_situation_dataclass() -> None:
    fields = _assigned_names(_class(_tree("app.bot.reply"), "Situation").body)
    assert set(us.SHOWN_COUNT_FIELDS) <= set(fields)
    assert us.PROMISED_COUNT_COLUMN not in fields


def test_render_reads_exactly_the_two_shown_counts() -> None:
    """`==`, `<=` emas: yangi maydon qo'shilsa hukm eskiradi."""
    used = _attributes_of(_function(_tree("app.bot.reply"), "render"), "situation")
    assert used == {"started_at", *us.SHOWN_COUNT_FIELDS}
    assert us.PROMISED_COUNT_COLUMN not in used


def test_the_promised_count_never_reaches_the_reply_module() -> None:
    """C-3/C-4 ning butun mazmuni: to'g'ri son bu faylga umuman kelmaydi."""
    names = _identifiers(_tree("app.bot.reply"))
    assert set(us.SHOWN_COUNT_FIELDS) <= names
    assert us.PROMISED_COUNT_COLUMN not in names
    assert us.PROMISED_COUNT_FUNCTION not in names


def test_the_promised_count_exists_where_the_clause_binds_it() -> None:
    """Va u bir maydon narida turibdi — mana shu yerda."""
    assert us.PROMISED_COUNT_FUNCTION in _module_symbols("app.clustering.independence")
    outage = _class(_tree("app.clustering.models"), "Outage")
    assert us.PROMISED_COUNT_COLUMN in _assigned_names(outage.body)


def test_decide_splits_on_coverage_not_on_a_report_count() -> None:
    """C-5 ning `INVERTED` hukmi shu yerdan chiqadi."""
    used = _attributes_of(_function(_tree("app.bot.reply"), "decide"), "situation")
    assert "coverage_ok" in used
    assert us.PROMISED_COUNT_COLUMN not in used
    assert not used & {us.PROMISED_COUNT_FUNCTION}


def test_decide_returns_the_forbidden_verdict() -> None:
    """Nom `Verdict` ning **qiymatidan** olinadi — satr qidirilmaydi."""
    tree = _tree("app.bot.reply")
    values = _string_attributes(_class(tree, "Verdict"))
    forbidden = {name for name, value in values.items() if value == us.FORBIDDEN_VERDICT}
    required = {name for name, value in values.items() if value == us.REQUIRED_VERDICT}
    assert len(forbidden) == len(required) == 1
    assert not forbidden & required
    returned = _attributes_of(_function(tree, "decide"), "Verdict")
    assert forbidden <= returned
    assert required <= returned


def test_the_enum_is_wider_than_section_9_knows() -> None:
    values = _string_attributes(_class(_tree("app.bot.reply"), "Verdict"))
    assert us.VERDICTS_KNOWN_TO_SECTION_9 < us.VERDICTS_IN_SPEC < len(values)


def test_the_named_error_codes_are_not_class_attributes() -> None:
    """`UC-S1` ikkita kodni nomlaydi va noldan marta shu nom bilan qurilgan."""
    tree = _tree("app.core.errors")
    codes = {
        attributes["code"]
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        for attributes in (_string_attributes(node),)
        if "code" in attributes
    }
    assert us.BUILT_ERROR_CODE in codes
    for doc_code in us.DOC_ERROR_CODES:
        assert doc_code not in codes
        assert doc_code.lower() not in codes


def test_the_bot_registers_exactly_two_commands() -> None:
    calls = _registrations(_tree("app.bot.handlers"))
    commands = sum(1 for call in calls if any(_is_command_filter(a) for a in call.args[1:]))
    assert commands == us.BOT_COMMANDS


def test_the_language_switch_is_two_registrations_and_neither_is_a_command() -> None:
    """«Одной командой» — komanda yo'q; ikki qadamli tugma yo'li bor."""
    steps: list[str] = []
    for call in _registrations(_tree("app.bot.handlers")):
        handler = call.args[0]
        if not isinstance(handler, ast.Name) or not handler.id.startswith("on_language"):
            continue
        steps.append(handler.id)
        assert not any(_is_command_filter(a) for a in call.args[1:]), handler.id
    assert len(steps) == us.LANGUAGE_SWITCH_STEPS
    assert len(set(steps)) == len(steps)

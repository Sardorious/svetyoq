"""`06` §11 ↔ hujjatning o'zi — suiiste'mol jadvali kod bilan bog'lanadi.

**Nima uchun bu fayl `test_abuse_contract.py` dan tashqari kerak.**
34-sessiya §11 ning oltita qatorining har biri uchun **xatti-harakat**
testini yozdi va bu to'g'ri qaror edi: 33-sessiya topgan defektda simvol
ham, formula ham joyida edi, ishlamaydigani esa mexanizm edi. Lekin o'sha
faylning tayanchi — `SPEC_TABLE` — **qo'lda ko'chirilgan**: hujjatga
yettinchi qator qo'shilsa, `50 m` `80 m` ga aylansa yoki `mahalla_active`
og'irligi ko'tarilsa, `test_abuse_contract.py` ning birorta testi
**yiqilmaydi** — u o'z nusxasini o'lchaydi. Aynan shu bo'shliq 40–60
sessiyalarda `06` va `05` ning boshqa hamma bo'limi uchun yopilgan;
§11 — oxirgisi.

Shuning uchun bu yerda hujjat **o'qiladi**, ko'chirilmaydi:

1. **Jadvalning uzunligi** hujjatdan olinadi va `SPEC_TABLE` niki bilan
   solishtiriladi — ya'ni §11 ga qator qo'shilsa, 34-sessiyaning fayli
   ham «to'liq emas» deb belgilanadi. Ikkala fayl bir-birini
   almashtirmaydi: u — «himoya ishlaydimi», bu — «hujjatda yozilgani
   o'shami».
2. **Har bir qatorda kamida bitta backtickli token** bo'lishi shart va
   **har bir token kodda haqiqiy simvolga** yechilishi kerak
   (`RESOLVERS`). Egasi yo'q nasr qator — «himoya bor» degan yozuv,
   ortida esa hech narsa yo'q; 33-sessiya topgan holat aynan shu edi.
   `RESOLVERS` ro'yxatda **yo'q** token uchrasa test tushunarli xabar
   bilan yiqiladi, jimgina o'tkazib yubormaydi.
3. **Qatorlardagi sonlar** (`50 m`, `≥10 daq`, `10 daqiqada 5 km`, `2.0`)
   hujjatdan parse qilinadi va `settings` / `DEFAULT_PARAMS` /
   `SOURCE_BY_CODE` bilan solishtiriladi. Shu paytgacha ular test
   kodida literal edi.
4. **Bo'limlararo ziddiyat.** Bu — 57-sessiyaning sabog'i (`06` §8 ning
   «60 s» i `05` §8 jadvali bilan hech qachon solishtirilmagan edi).
   §11 ning uchta soni boshqa joyda **takrorlanadi**:

   | Son | §11 | Ikkinchi manba |
   |---|---|---|
   | `50` m | `spread.min_distance_m` = 50 m | `06` §9 konfiguratsiya jadvali; `05` §4.3 |
   | `10` daq | akkaunt yoshi ≥10 daq | `05` §4.3 (`now() - 10 daqiqa`) |
   | `2.0` | `mahalla_active` og'irligi | `06` §2 `INSERT` bloki |

   Ikkala nusxa mustaqil o'zgarishi mumkin va **ikkala tomondagi test
   ham yashil qolardi** — chunki har biri o'z bo'limini o'qiydi. Bu
   yerda ular bir-biriga bog'lanadi.

**Ataylab tekshirilmaydi.** Himoyalarning xatti-harakati
(`dedupe_evidence`, `spread_ok`, `velocity.penalize` ning qabul yo'lida
chaqirilishi, qamrov to'sig'i) — `test_abuse_contract.py`. Bu yerda
takrorlash tuzatish joyini noaniq qilardi (41-sessiyaning sabog'i).

**Unicode ga bog'liqlik kamaytirilgan** (53-sessiyaning sabog'i):
`≥` ham, `>=` ham qabul qilinadi; qatorlar o'zbekcha so'z bo'yicha emas,
token va son shakli bo'yicha topiladi.
"""

from __future__ import annotations

import dataclasses
import inspect
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from app.clustering import confirmation, scale
from app.clustering.params import DEFAULT_PARAMS
from app.core.config import settings
from app.db import models
from app.reports import sources

from .test_abuse_contract import SPEC_TABLE

SVETA_ROOT = Path(__file__).resolve().parents[1]
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"
DESIGN_DOC = SVETA_ROOT.parent / "05_Technical_Design.md"

SECTION_11 = "## 11. Suiiste'mol ssenariylari"
SECTION_12 = "## 12. Qo'shiladigan testlar"
SECTION_9 = "## 9. Konfiguratsiya parametrlari"
SECTION_10 = "## 10. Sxema o'zgarishlari"
SECTION_2 = "## 2. Xabar manbalari va ishonch og'irliklari"
SECTION_3 = "## 3. Hudud statistikasi"
DESIGN_4_3 = "### 4.3"
DESIGN_4_4 = "### 4.4"

#: Jadval sarlavhasi — hujjat qayta tuzilsa parser jim qolmasin.
HEADER = ("Hujum", "Himoya")

#: `≥` (U+2265) ham, `>=` ham.
GE = r"(?:≥|>=)"


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _slice(doc: Path, start: str, end: str) -> str:
    assert doc.exists(), f"hujjat topilmadi: {doc}"
    text = doc.read_text(encoding="utf-8")
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    assert end in text, f"`{end}` topilmadi — hujjat qayta tuzilgan"
    return text.split(start, 1)[1].split(end, 1)[0]


def _table(section: str, *, columns: int) -> list[tuple[str, ...]]:
    """Markdown jadvalining sarlavhasiz, ajratgichsiz qatorlari."""
    rows: list[tuple[str, ...]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = tuple(c.strip() for c in line.strip("|").split("|"))
        if len(cells) != columns:
            continue
        if set(cells[0]) <= {"-", ":"}:  # ajratgich
            continue
        rows.append(cells)
    return rows


def _rows() -> list[tuple[str, ...]]:
    """§11 jadvali `(hujum, himoya)` juftliklari sifatida (sarlavhasiz)."""
    rows = _table(_slice(CONFIRMATION_DOC, SECTION_11, SECTION_12), columns=2)
    assert rows and rows[0] == HEADER, f"§11 sarlavhasi kutilganidek emas: {rows[:1]}"
    return rows[1:]


def _tokens(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def _row_matching(pattern: str) -> tuple[str, ...]:
    """Himoya katakchasi `pattern` ga mos yagona qator."""
    hits = [row for row in _rows() if re.search(pattern, row[1])]
    assert len(hits) == 1, f"`{pattern}` uchun {len(hits)} qator topildi (1 kutilgan)"
    return hits[0]


def _one_number(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    assert match is not None, f"`{pattern}` topilmadi: {text!r}"
    return match.group(1)


# --------------------------------------------------------------------------
# Tokenlarni kodga yechish
# --------------------------------------------------------------------------


def _resolve_distinct_users() -> None:
    fields = {f.name for f in dataclasses.fields(confirmation.ConfirmationResult)}
    assert "distinct_users" in fields
    assert "distinct_users" in models.Outage.__table__.columns


def _resolve_spread_min_distance() -> None:
    # Hujjatda nuqtali kalit (`spread.min_distance_m`), kodda —
    # `06` §9 ning nomlash shartnomasi bo'yicha tekis maydon.
    assert isinstance(DEFAULT_PARAMS.spread_min_distance_m, (int, float))


def _resolve_user_factor() -> None:
    assert callable(sources.user_factor)
    assert sources.user_factor(0) < sources.user_factor(100)


def _resolve_trust_score() -> None:
    assert "trust_score" in models.User.__table__.columns


def _resolve_mahalla_active() -> None:
    assert "mahalla_active" in sources.SOURCE_BY_CODE


def _resolve_cells_with_reports() -> None:
    assert "cells_with_reports" in inspect.signature(scale.raw_scale).parameters
    assert "cells_with_reports" in models.Outage.__table__.columns


#: §11 da uchraydigan har bir backtickli token uchun «kodda bormi» dalili.
RESOLVERS: dict[str, Callable[[], None]] = {
    "distinct_users": _resolve_distinct_users,
    "spread.min_distance_m": _resolve_spread_min_distance,
    "user_factor": _resolve_user_factor,
    "trust_score": _resolve_trust_score,
    "mahalla_active": _resolve_mahalla_active,
    "cells_with_reports": _resolve_cells_with_reports,
}


# --------------------------------------------------------------------------
# Jadvalning tuzilishi
# --------------------------------------------------------------------------


def test_the_section_parses_into_six_rows() -> None:
    """§11 da oltita qator — kam ham, ortiq ham emas.

    Bu birinchi test, chunki quyidagi parametrizatsiyalar shu ro'yxatdan
    yasaladi: jadval bo'shab qolsa ular jimgina nol test yig'ardi
    (28-sessiyaning `include_router` qirrasi).
    """
    assert len(_rows()) == 6


def test_the_hand_copied_table_has_the_same_length() -> None:
    """34-sessiyaning `SPEC_TABLE` i hujjat bilan bir uzunlikda.

    Bog'lovchi test: §11 ga qator qo'shilsa `test_abuse_contract.py`
    ham «to'liq emas» deb belgilanadi, garchi uning o'z testlari yashil
    qolsa ham.
    """
    assert len(SPEC_TABLE) == len(_rows())


@pytest.mark.parametrize("attack, defence", _rows())
def test_every_row_names_at_least_one_code_token(attack: str, defence: str) -> None:
    """Har bir himoya katakchasida kamida bitta backtickli token bor.

    Faqat nasrdan iborat qator — «himoya bor» degan yozuv, ortida esa
    egasi yo'q; 33-sessiya topgan defekt shu shakl edi.
    """
    assert _tokens(defence), attack


@pytest.mark.parametrize("token", sorted({t for _, d in _rows() for t in _tokens(d)}))
def test_every_backticked_token_resolves_to_code(token: str) -> None:
    """§11 nomlagan har bir simvol kodda haqiqatan mavjud."""
    resolver = RESOLVERS.get(token)
    assert resolver is not None, (
        f"`{token}` — §11 da yangi token; unga kodda egasi bor-yo'qligini "
        "ko'rsatadigan resolver `RESOLVERS` ga qo'shilishi kerak"
    )
    resolver()


def test_the_parser_is_not_vacuous() -> None:
    """Regexlar mos kelishdan to'xtasa, test jimgina yashil qolmasin.

    `_tokens` bo'sh ro'yxat qaytarsa yuqoridagi parametrizatsiya nol
    testga aylanardi va butun fayl «o'tdi» deb ko'rinardi.
    """
    tokens = [t for _, d in _rows() for t in _tokens(d)]
    assert len(tokens) >= 6
    assert set(tokens) <= set(RESOLVERS)
    assert len(set(tokens)) == len(RESOLVERS)


# --------------------------------------------------------------------------
# Qatorlardagi sonlar — hujjatdan
# --------------------------------------------------------------------------


def test_spread_distance_comes_from_the_document() -> None:
    """«`spread.min_distance_m` = 50 m» → `DEFAULT_PARAMS`."""
    _, defence = _row_matching(r"spread\.min_distance_m")
    metres = int(_one_number(defence, r"=\s*(\d+)\s*m\b"))

    assert DEFAULT_PARAMS.spread_min_distance_m == metres


def test_account_age_comes_from_the_document() -> None:
    """«akkaunt yoshi ≥10 daq» → `settings.reporter_min_account_age_min`.

    Hujjat **quyi chegara** yozadi (`≥`), ya'ni kod undan qattiqroq
    bo'lishi mumkin — lekin yumshoqroq emas.
    """
    _, defence = _row_matching(rf"{GE}\s*\d+\s*daq")
    minutes = int(_one_number(defence, rf"{GE}\s*(\d+)\s*daq"))

    assert settings.reporter_min_account_age_min >= minutes


def test_velocity_window_and_distance_come_from_the_document() -> None:
    """«10 daqiqada 5 km sakrasa» → `settings.velocity_*`.

    Jazoning **kattaligi** (`velocity_trust_penalty`) hujjatda yo'q va
    `[GIPOTEZA]` bo'lib qoladi — bu yerda faqat chegaralar qulflanadi.
    """
    pattern = r"(\d+)\s*daqiqada\s*(\d+)\s*km"
    _, defence = _row_matching(pattern)
    match = re.search(pattern, defence)
    assert match is not None
    minutes, kilometres = int(match.group(1)), int(match.group(2))

    assert settings.velocity_window_min == minutes
    assert settings.velocity_max_distance_m == kilometres * 1000


def test_active_weight_ceiling_comes_from_the_document() -> None:
    """«`mahalla_active` og'irligi 2.0 dan oshmaydi» → registr."""
    _, defence = _row_matching(r"mahalla_active")
    ceiling = float(_one_number(defence, r"(\d+\.\d+)\s*dan oshmaydi"))

    assert sources.SOURCE_BY_CODE["mahalla_active"].weight <= ceiling
    assert sources.SOURCE_BY_CODE["mahalla_active"].weight == ceiling


# --------------------------------------------------------------------------
# Bo'limlararo ziddiyat (57-sessiyaning sabog'i)
# --------------------------------------------------------------------------


def test_section_11_agrees_with_the_configuration_table() -> None:
    """§11 dagi `50 m` — §9 konfiguratsiya jadvalidagi boshlang'ich qiymat.

    Ikkala bo'lim mustaqil tahrirlanadi; ular ajralib ketsa
    `test_confirm_params_contract.py` (§9) ham, yuqoridagi test (§11) ham
    yashil qolardi.
    """
    _, defence = _row_matching(r"spread\.min_distance_m")
    from_11 = int(_one_number(defence, r"=\s*(\d+)\s*m\b"))

    config_rows = _table(_slice(CONFIRMATION_DOC, SECTION_9, SECTION_10), columns=3)
    hits = [r for r in config_rows if "spread.min_distance_m" in r[0]]
    assert len(hits) == 1, "§9 jadvalida `spread.min_distance_m` topilmadi"
    from_9 = int(_one_number(hits[0][1], r"(\d+)"))

    assert from_11 == from_9


def test_section_11_agrees_with_the_source_registry() -> None:
    """§11 dagi `2.0` — §2 `INSERT` blokidagi og'irlik."""
    _, defence = _row_matching(r"mahalla_active")
    from_11 = float(_one_number(defence, r"(\d+\.\d+)\s*dan oshmaydi"))

    registry = _slice(CONFIRMATION_DOC, SECTION_2, SECTION_3)
    from_2 = float(_one_number(registry, r"\('mahalla_active',\s*([\d.]+)"))

    assert from_11 == from_2


def test_section_11_agrees_with_the_independent_reporter_definition() -> None:
    """§11 ning ikki soni `05` §4.3 dagi ta'rifdan ko'chirilgan.

    `05` §4.3 «mustaqil xabar beruvchi» ni ta'riflaydi va §11 ning
    ikkinchi va uchinchi qatori aynan o'sha ikki shartning qisqartmasi.
    Hujjatlar ajralib ketsa kod qaysi biriga amal qilishini hech kim
    ayta olmasdi.
    """
    definition = _slice(DESIGN_DOC, DESIGN_4_3, DESIGN_4_4)
    age_05 = int(_one_number(definition, r"now\(\)\s*-\s*(\d+)\s*daqiqa"))
    spread_05 = int(_one_number(definition, rf"masofa\s*{GE}\s*(\d+)\s*m\b"))

    _, age_row = _row_matching(rf"{GE}\s*\d+\s*daq")
    age_11 = int(_one_number(age_row, rf"{GE}\s*(\d+)\s*daq"))
    _, spread_row = _row_matching(r"spread\.min_distance_m")
    spread_11 = int(_one_number(spread_row, r"=\s*(\d+)\s*m\b"))

    assert age_11 == age_05
    assert spread_11 == spread_05
    # Va kod ikkalasiga ham amal qiladi.
    assert settings.reporter_min_account_age_min == age_05
    assert DEFAULT_PARAMS.spread_min_distance_m == spread_05

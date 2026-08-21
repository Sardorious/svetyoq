"""`06` §9 jadvali ↔ `app/clustering/params.py` kontrakti — bazasiz.

**Nima uchun bu fayl kerak.** `params.py:21` da yozilgan: «`06` §9 jadvali,
**aynan**». Bu jumlani bugungacha hech narsa ushlab turmasdi. Ayni paytda
o'sha o'n beshta son kodda **uch marta** qo'lda takrorlangan:

1. `DEFAULTS` lug'ati (`params.py:22`);
2. `ConfirmParams` / `ScaleParams` / `GuardParams` / `Params` dataklasslarining
   maydon standartlari (`min_users: int = 3`, `coef: float = 0.5`, …);
3. `06_Confirmation_Logic.md` §9 jadvalining o'zi.

Uchalasi ham odam qo'li bilan yangilanadi. To'rtta yo'nalish jim edi:

1. **Hujjatdagi qiymat o'zgarsa** — `confirm.coef` 0.5 dan 0.6 ga ko'chirilsa —
   kod eski qiymat bilan ishlayveradi. Bu eng qimmat nosozlik: tasdiqlash
   chegarasi butun mahsulotning ma'nosi (`06` §4), lekin hech qanday test
   yiqilmaydi va farq faqat ishlab chiqarishdagi verdiktlarda ko'rinadi.
2. **`DEFAULTS` ga hujjatda yo'q kalit qo'shilsa** — `06` §9 ro'yxati
   **yopiq** (`tools/region_admin.py:370` shunga tayanib noma'lum kalitni
   bloklaydi), lekin bu tomon umuman o'lchanmagan edi.
3. **Dataklass standarti `DEFAULTS` dan ajralsa** — `DEFAULT_PARAMS`
   `from_mapping()` orqali `DEFAULTS` dan quriladi, `Params()` esa maydon
   standartlaridan. Ikkalasi ham ishlatiladi (`tests/test_simulate.py:345`
   `ConfirmParams()` ni to'g'ridan-to'g'ri yasaydi), ya'ni bitta ishga
   tushirishda ikki xil chegara bo'lishi mumkin edi.
4. **`DEFAULTS` da kalit bor, `from_mapping` uni o'qimaydi** — o'lik
   konfiguratsiya. `region_admin` uni bazaga seed qiladi, odam E11 da uni
   sozlaydi va **hech narsa o'zgarmaydi**. `KeyError` chiqmaydi, chunki
   `_num` faqat o'zi so'ragan kalitlarga murojaat qiladi.

Shuning uchun jadval hujjatdan o'qiladi (40- va 45-sessiyalarning `_SPEC_ROW`
naqshi). Qo'lda yozilgan `DEFAULTS` **qoladi** — u qiymatlarni qulflaydi va
ishga tushishda hujjatni o'qish kerak emas — lekin uning o'zi manba bilan
solishtiriladi.

**Bu fayl formulalarga tegmaydi.** `required_score`, masshtab narvoni va
qamrov to'sig'ining xulq-atvori `tests/test_confirmation.py` va
`tests/test_scale.py` da allaqachon qulflangan; bu yerda faqat **sonlar
qayerdan kelgani** o'lchanadi.

Hammasi bazasiz: `app.clustering.params` toza modul, hujjat esa oddiy matn.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.clustering import params as p

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `06_Confirmation_Logic.md` repo ildizida, `sveta/` ning yonida.
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"

#: §9 jadvalining qatori: `| kalit | boshlang'ich | maqomi |`. Sarlavha
#: (`| Kalit | ... |`) va ajratgich (`|---|---|---|`) da backtick yo'q,
#: ya'ni ular birinchi ustunning filtriga tushmaydi.
_ROW = re.compile(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|\s*$")
_TICKED = re.compile(r"`([^`]+)`")

#: §9 ning «Maqomi» ustunidagi so'zlar. Noma'lum maqom — testning yiqilishi,
#: jimgina o'tkazib yuborish emas: yangi maqom paydo bo'lsa (masalan
#: E11 dan keyin `EMPIRIK`) uni shu yerda ochiq tan olish kerak.
STATUSES = frozenset({"BASELINE-TAS", "BAHO", "[TEKSHIRISH]"})

#: Jadvaldagi qatorlar va ular yoyilgandagi kalitlar soni — **aynan**,
#: «kamida» emas. §9 mahsulotning sozlanadigan sathi, u epiclar bilan
#: o'smaydi: `notify.*` va `velocity.*` ataylab tashqarida qoldirilgan
#: (`PROGRESS.md` «Ochiq savollar»). Ro'yxat o'zgarsa — bu odamning ongli
#: qarori bo'lsin, jim siljish emas.
SPEC_ROWS = 12
SPEC_KEYS = 15

#: `Params` ning ichki dataklasslari. Kalit `guruh.maydon` shaklida bo'lsa
#: qiymat shu guruhdan olinadi, aks holda `Params` ning o'zidan.
GROUPS = frozenset({"confirm", "scale", "guard"})


def _section() -> str:
    """`06` §9 ning matni."""
    assert CONFIRMATION_DOC.exists(), (
        f"`06_Confirmation_Logic.md` topilmadi: {CONFIRMATION_DOC}"
    )
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    heading = "## 9. Konfiguratsiya parametrlari"
    assert heading in text, f"`06` da «{heading}» sarlavhasi yo'q"
    start = text.index(heading)
    # `\n## ` `\n### ` ni tutmaydi (uchinchi belgi `#`, probel emas), ya'ni
    # bo'lim keyingi **birinchi darajali** sarlavhagacha cho'ziladi.
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def _expand(base: str, suffix: str) -> str:
    """`confirm.floor` + `ceil` → `confirm.ceil`.

    Jadval kalitlarni ikki xil qisqartiradi: `` `confirm.floor` / `ceil` ``
    (nuqtadan keyin) va `` `scale.mahalla_floor/ceil` `` (pastki chiziqdan
    keyin). Ikkalasida ham **oxirgi nom bo'lagi** almashadi, shuning uchun
    ajratgich sifatida `.` va `_` dan qaysi biri oxirroq bo'lsa o'sha
    olinadi.
    """
    cut = max(base.rfind("."), base.rfind("_"))
    assert cut != -1, f"`06` §9: `{base}` qisqartmani yoyish uchun juda oddiy"
    return base[: cut + 1] + suffix


def _rows() -> list[tuple[list[str], list[float], str]]:
    """§9 jadvali: (kalitlar, qiymatlar, maqom) uchliklari, qator tartibida."""
    out: list[tuple[list[str], list[float], str]] = []
    for line in _section().splitlines():
        match = _ROW.match(line)
        if not match:
            continue
        key_cell, value_cell, status_cell = (g.strip() for g in match.groups())
        tokens = _TICKED.findall(key_cell)
        if not tokens:
            # Sarlavha va ajratgich shu yerda tushib qoladi.
            continue

        parts = [p.strip() for token in tokens for p in token.split("/")]
        keys = [parts[0]] + [_expand(parts[0], p) for p in parts[1:]]

        raw_values = [v.strip() for v in value_cell.split("/")]
        assert len(raw_values) == len(keys), (
            f"`06` §9: `{parts[0]}` qatorida {len(keys)} ta kalit, "
            f"{len(raw_values)} ta qiymat — ular juftlashmaydi"
        )
        try:
            values = [float(v) for v in raw_values]
        except ValueError as exc:  # pragma: no cover - hujjat buzilganda
            raise AssertionError(
                f"`06` §9: `{parts[0]}` qatorida son bo'lmagan qiymat: {raw_values}"
            ) from exc

        status = status_cell.strip("`").strip()
        assert status in STATUSES, (
            f"`06` §9: noma'lum maqom {status!r} ({parts[0]}) — "
            "uni `STATUSES` ga qo'shing"
        )
        out.append((keys, values, status))
    return out


def _spec_params() -> dict[str, float]:
    """§9 jadvali: kalit → boshlang'ich qiymat."""
    result: dict[str, float] = {}
    for keys, values, _status in _rows():
        for key, value in zip(keys, values, strict=True):
            assert key not in result, f"`06` §9: `{key}` ikki marta uchraydi"
            result[key] = value
    return result


def _declared(key: str) -> float:
    """Dataklass maydonining standart qiymati — `DEFAULTS` dan mustaqil yo'l.

    `Params()` maydon standartlaridan quriladi, `DEFAULT_PARAMS` esa
    `from_mapping()` orqali `DEFAULTS` dan. Aynan shu ikki yo'lning
    ajralib ketishi o'lchanadi.
    """
    head, _, rest = key.partition(".")
    if head in GROUPS:
        return float(getattr(getattr(p.Params(), head), rest))
    # Tekis maydonlar: `avg_household_size`, `spread.min_distance_m`.
    return float(getattr(p.Params(), key.replace(".", "_")))


# --------------------------------------------------------------------------
# Hujjat — manba
# --------------------------------------------------------------------------


def test_defaults_match_the_confirmation_doc() -> None:
    """`params.py:21`: «`06` §9 jadvali, **aynan**» — endi shu tekshiriladi.

    Kalitlar ham, qiymatlar ham. Hujjatdagi chegara o'zgarsa yoki `DEFAULTS`
    ga hujjatda yo'q kalit qo'shilsa — shu yerda yiqiladi.
    """
    assert _spec_params() == pytest.approx(p.DEFAULTS)


def test_no_key_is_missing_from_the_code() -> None:
    """Hujjatda bor, kodda yo'q — sozlanmaydigan parametr.

    Yuqoridagi tenglik buni ham ushlaydi, lekin xato xabari ikkita to'liq
    lug'atni ko'rsatadi; bu yerda **nima yetishmayotgani** ochiq yoziladi.
    """
    missing = sorted(set(_spec_params()) - set(p.DEFAULTS))
    assert missing == [], f"`06` §9 da bor, `DEFAULTS` da yo'q: {missing}"


def test_no_key_is_invented_by_the_code() -> None:
    """Kodda bor, hujjatda yo'q — `06` §9 ro'yxati yopiq.

    `tools/region_admin.py` shu yopiqlikka tayanib noma'lum kalitni
    bloklaydi (`EXIT_USAGE`) — 212-rundan beri `DEFAULTS` dan emas,
    `known_keys()` dan, ya'ni `DEFAULTS` + `notify.*` birlashmasidan:
    asbob o'zi seed qilgan kalitni rad etardi. `notify.*` baribir
    alohida manbada (`app/notifications/params.py`) va
    `tests/test_notify_params.py` ikkala to'plamning kesishmasi
    bo'shligini tekshiradi.
    """
    extra = sorted(set(p.DEFAULTS) - set(_spec_params()))
    assert extra == [], f"`DEFAULTS` da bor, `06` §9 da yo'q: {extra}"


def test_the_scan_is_measuring_something() -> None:
    """Bo'sh to'plam bo'sh to'plamga teng (34-sessiyaning saboqi).

    Sarlavha yoki jadval shakli o'zgarsa `_spec_params()` bo'sh qaytarardi
    va yuqoridagi tenglik `DEFAULTS` bo'shab qolgan kunda yashil bo'lardi.
    """
    assert len(_rows()) == SPEC_ROWS, f"`06` §9 da {len(_rows())} qator"
    assert len(_spec_params()) == SPEC_KEYS
    assert len(p.DEFAULTS) == SPEC_KEYS
    # Uch xil qatordan bittadan tayanch: oddiy, nuqtali qisqartma,
    # pastki chiziqli qisqartma.
    spec = _spec_params()
    assert spec["confirm.min_users"] == 3
    assert spec["confirm.ceil"] == 8
    assert spec["scale.mahalla_ceil"] == 15


def test_every_row_carries_a_status() -> None:
    """«Maqomi» ustuni — qaysi son taxmin ekanining yagona yozuvi.

    `_rows()` noma'lum maqomda yiqiladi; bu test ustunning **umuman
    bo'shab qolmasligini** qulflaydi va §9 ning «hech bir qiymat empirik
    asosga ega emas» jumlasini kuzatib boradi.
    """
    statuses = {status for _keys, _values, status in _rows()}
    assert statuses <= STATUSES
    assert "BAHO" in statuses, "§9 dagi barcha qiymatlar baho — ustun bo'shab qolgan"


def test_the_section_still_says_the_values_live_in_the_database() -> None:
    """§9 ning birinchi jumlasi `DEFAULTS` ning bootstrap ekanini oqlaydi.

    Jumla yo'qolsa `params.py` ning butun izohi asossiz qoladi va
    `DEFAULTS` ni oddiy konstanta deb o'qish mumkin bo'lardi.
    """
    section = _section()
    assert "Barchasi bazada" in section
    assert "region_config" in section


# --------------------------------------------------------------------------
# Kodning ichidagi uchinchi nusxa
# --------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(p.DEFAULTS))
def test_dataclass_defaults_match_defaults(key: str) -> None:
    """Maydon standarti `DEFAULTS` bilan bir xil bo'lishi shart.

    Ikki yo'l ham ishlatiladi: `DEFAULT_PARAMS` (`DEFAULTS` orqali) va
    to'g'ridan-to'g'ri `ConfirmParams()` (`tests/test_simulate.py:345`).
    Ular ajralsa bitta ishga tushirishda ikki xil chegara bo'lardi.
    """
    assert _declared(key) == pytest.approx(p.DEFAULTS[key]), (
        f"`{key}`: dataklass standarti {_declared(key)}, "
        f"`DEFAULTS` da {p.DEFAULTS[key]}"
    )


def test_default_params_equals_a_bare_params() -> None:
    """`from_mapping()` va maydon standartlari bitta obyekt berishi kerak."""
    assert p.DEFAULT_PARAMS == p.Params()


def test_from_mapping_with_the_spec_values_changes_nothing() -> None:
    """Hujjatdagi qiymatlarni bazadan o'qish standartni takrorlaydi.

    Ya'ni yangi mintaqa seed qilinganda (`region_admin` `DEFAULTS` ni
    yozadi) xulq-atvor seed qilinmagan mintaqanikidan farq qilmaydi.
    """
    assert p.from_mapping(dict(p.DEFAULTS)) == p.DEFAULT_PARAMS


# --------------------------------------------------------------------------
# O'lik konfiguratsiya
# --------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(p.DEFAULTS))
def test_every_key_is_actually_read(key: str) -> None:
    """`DEFAULTS` dagi har bir kalit `from_mapping` ning natijasiga ta'sir qiladi.

    Kalit hujjatda ham, `DEFAULTS` da ham, bazada ham bo'lishi mumkin —
    lekin `from_mapping` uni so'ramasa, E11 dagi sozlash **hech narsani
    o'zgartirmaydi** va xato ham chiqmaydi (`_num` faqat o'zi so'ragan
    kalitlarga murojaat qiladi). Perturbatsiya shu jimlikni buzadi.
    """
    changed = p.from_mapping({key: p.DEFAULTS[key] + 1})
    assert changed != p.DEFAULT_PARAMS, (
        f"`{key}` o'zgartirildi, `Params` esa o'zgarmadi — "
        "kalit `from_mapping` da o'qilmaydi (o'lik konfiguratsiya)"
    )

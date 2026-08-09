"""`05` §10 jadvali ↔ metrika registri kontrakti — bazasiz.

**Nima uchun bu fayl kerak.** `tests/test_obs_metrics.py:14` yettita nomni
sanaydi, lekin ro'yxat **qo'lda** yozilgan va tekshiruv `required <= set(...)`,
ya'ni **qism to'plam**. Bundan uchta yo'nalish jim qoladi:

1. hujjatga **sakkizinchi** qator qo'shilsa — hech narsa yiqilmaydi, metrika
   esa hech qachon eksport qilinmaydi;
2. hujjatdagi qator **qayta nomlansa** — qo'lda yozilgan ro'yxat eski nom
   bilan o'taveradi, Prometheus esa yangi nomni topmaydi;
3. registrga hujjatda yo'q metrika **qo'shilsa** — u hech qanday sababsiz
   eksportga chiqadi.

Shuning uchun jadval hujjatdan o'qiladi (45-sessiyaning `_SPEC_ROW` naqshi),
registrdagi ortiqchasi esa **ochiq ro'yxat** bilan oqlanadi: yangi metrika
`BEYOND_SPEC` ga sabab bilan yozilmaguncha test qizil bo'ladi.

Bu fayl **ogohlantirishlar tomoniga tegmaydi** — to'rtta shart ham, uchala
sonli chegara ham `tests/test_obs_alerts.py` da allaqachon qulflangan.

Hammasi bazasiz: modul `app.obs.metrics` toza, hujjat esa oddiy matn.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.obs import metrics as m

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `05_Technical_Design.md` repo ildizida, `sveta/` ning yonida.
DESIGN_DOC = SVETA_ROOT.parent / "05_Technical_Design.md"

#: `05` §10 jadvalining qatori: `| `nom` | nima uchun |`. Sarlavha
#: (`| Metrika | ... |`) va ajratgich (`|---|---|`) backtick siz, ya'ni
#: mos kelmaydi — filtr shu bilan ishlaydi.
_SPEC_ROW = re.compile(r"^\|\s*`([a-z_]+)`\s*\|\s*(.+?)\s*\|\s*$")

#: Jadval bo'shab qolmasligining pastki chegarasi. Bugun 7 ta; chegara
#: ataylab pastroq emas, aynan 7 — §10 epiclar bilan o'smaydi, u mahsulot
#: va'dasining ro'yxati. O'zgarsa — bu ongli qaror bo'lsin.
SPEC_ROWS = 7

#: Registrda bor, `05` §10 jadvalida **yo'q** metrikalar. Har biri sabab
#: bilan; sababsiz qo'shilgan metrika testni yiqitadi.
BEYOND_SPEC: dict[str, str] = {
    "time_to_confirm_count": (
        "`time_to_confirm_seconds` kvantillarining bazasi — kvantil o'zi "
        "nechta hodisadan hisoblanganini ko'rsatmaydi"
    ),
    "http_requests_total": (
        "«xatolik darajasi» ogohlantirishi uchun; bazadan bilib bo'lmaydi "
        "(`app.obs.counters`)"
    ),
    "alert_active": "ogohlantirishning o'zi, o'lchov emas (`05` §10, to'rtta shart)",
}

#: Prometheus konvensiyasi: `_total` — faqat hisoblagichda.
_COUNTER_SUFFIX = "_total"


def _section() -> str:
    """`05` §10 ning matni."""
    assert DESIGN_DOC.exists(), f"`05_Technical_Design.md` topilmadi: {DESIGN_DOC}"
    text = DESIGN_DOC.read_text(encoding="utf-8")
    heading = "## 10. Kuzatuvchanlik"
    assert heading in text, f"`05` da «{heading}» sarlavhasi yo'q"
    start = text.index(heading)
    # `\n## ` `\n### ` ni tutmaydi (uchinchi belgi `#`, probel emas), ya'ni
    # bo'lim keyingi **birinchi darajali** sarlavhagacha cho'ziladi.
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def _spec_metrics() -> dict[str, str]:
    """`05` §10 jadvali: metrika nomi → «Nima uchun» ustuni.

    Tartib saqlanadi (`dict` Python 3.7+ da kiritilish tartibida) — uni
    `test_registry_keeps_the_documented_order` ishlatadi.
    """
    result: dict[str, str] = {}
    for line in _section().splitlines():
        match = _SPEC_ROW.match(line)
        if not match:
            continue
        name, why = match.group(1), match.group(2)
        assert name not in result, f"`05` §10 da takrorlangan metrika: {name}"
        result[name] = why
    return result


SPEC = _spec_metrics()


# --------------------------------------------------------------------------
# Parserning o'zi
# --------------------------------------------------------------------------


def test_the_spec_table_is_parsed_and_not_empty() -> None:
    """Parser jim buzilsa qolgan hamma test bo'sh to'plamda o'taverardi."""
    assert len(SPEC) == SPEC_ROWS, (
        f"`05` §10 da {len(SPEC)} ta metrika topildi, kutilgani {SPEC_ROWS} ta: "
        f"{sorted(SPEC)} — jadval o'zgargan bo'lsa `SPEC_ROWS` ni yangilang"
    )


def test_every_documented_row_explains_itself() -> None:
    """Bo'sh «Nima uchun» — metrika nima uchun borligini hech kim bilmaydi."""
    silent = [name for name, why in SPEC.items() if not why.strip("* ")]
    assert not silent, f"`05` §10 da izohsiz metrika: {silent}"


# --------------------------------------------------------------------------
# Hujjat → registr
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(SPEC))
def test_documented_metric_is_registered(name: str) -> None:
    """Har bir hujjatdagi qatorning bazasiz tayanchi."""
    assert name in m.FAMILY_BY_NAME, (
        f"`05` §10 da `{name}` bor, `app/obs/metrics.py` registrida yo'q"
    )


@pytest.mark.parametrize("name", sorted(SPEC))
def test_documented_metric_reaches_the_export(name: str) -> None:
    """Registrda bo'lishi yetmaydi — `render` uni matnga chiqarishi kerak."""
    text = m.render([m.Sample(name, 1)])
    assert f"{m.PREFIX}{name} 1" in text, f"`{name}` eksport matniga chiqmadi"
    assert f"# TYPE {m.PREFIX}{name} " in text


# --------------------------------------------------------------------------
# Registr → hujjat (teskari yo'nalish — aynan shu jim edi)
# --------------------------------------------------------------------------


def test_registry_has_nothing_undocumented_and_unexplained() -> None:
    """Hujjatda yo'q metrika faqat `BEYOND_SPEC` da sabab bilan yashaydi."""
    extra = set(m.FAMILY_BY_NAME) - set(SPEC)
    assert extra == set(BEYOND_SPEC), (
        "registr va hujjat farqi kutilganidan boshqa. "
        f"Ortiqcha va sababsiz: {sorted(extra - set(BEYOND_SPEC))}; "
        f"`BEYOND_SPEC` da bor, registrda yo'q: {sorted(set(BEYOND_SPEC) - extra)}"
    )


def test_registry_keeps_the_documented_order() -> None:
    """`metrics.py` izohi «aynan o'sha tartibda» deydi — endi bu tekshiriladi.

    Tartib eksport matnini barqaror qiladi (`render` `FAMILIES` bo'yicha
    yuradi), ya'ni javobni `diff` bilan solishtirish shu tartibga tayanadi.
    """
    in_code = [f.name for f in m.FAMILIES if f.name in SPEC]
    assert in_code == list(SPEC), (
        f"registr tartibi: {in_code}\n`05` §10 tartibi: {list(SPEC)}"
    )


# --------------------------------------------------------------------------
# Oilaning o'zi
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(m.FAMILY_BY_NAME))
def test_family_type_matches_the_name_suffix(name: str) -> None:
    """`_total` ↔ `counter` ikki tomonlama.

    Prometheus da `_total` bilan tugagan gauge — `rate()` ni yolg'on
    qiladigan nom; `_total` siz counter esa aksincha, o'sishini hech kim
    hisoblamaydi.
    """
    family = m.FAMILY_BY_NAME[name]
    assert family.type in (m.COUNTER, m.GAUGE), f"`{name}` turi noma'lum: {family.type}"
    suffixed = name.endswith(_COUNTER_SUFFIX)
    assert (family.type == m.COUNTER) == suffixed, (
        f"`{name}` turi `{family.type}`, nomi esa `{_COUNTER_SUFFIX}` bilan "
        f"{'tugaydi' if suffixed else 'tugamaydi'}"
    )


@pytest.mark.parametrize("name", sorted(m.FAMILY_BY_NAME))
def test_family_help_is_not_empty(name: str) -> None:
    """Bo'sh `# HELP` — Prometheus uchun yaroqli, odam uchun foydasiz."""
    assert m.FAMILY_BY_NAME[name].help.strip()


def test_geo_unmatched_ratio_keeps_the_documented_definition() -> None:
    """Yagona ta'rifli qator: `05` §10 uni `district_id IS NULL` deb belgilaydi.

    Ta'rif kodning `help` iga ko'chirilgan; ikkalasi ajralib ketsa, panelda
    yozilgan narsa hisoblanayotgan narsadan boshqa bo'lardi.
    """
    marker = "district_id IS NULL"
    assert marker in SPEC["geo_unmatched_ratio"], "`05` §10 ning ta'rifi o'zgargan"
    assert marker in m.GEO_UNMATCHED.help


def test_the_alert_sentence_names_only_documented_metrics() -> None:
    """§10 ning ogohlantirish jumlasi jadvaldagi nomga havola qiladi.

    Chegaralar `tests/test_obs_alerts.py` da; bu yerda faqat **nom** —
    jadvaldagi qator qayta nomlansa jumla eskirib qolardi.
    """
    sentence = next(
        line for line in _section().splitlines() if line.startswith("Ogohlantirish faqat")
    )
    named = set(re.findall(r"`([a-z_]+)`", sentence))
    assert named, "ogohlantirish jumlasida metrika nomi yo'q — jumla o'zgargan"
    assert named <= set(SPEC), f"jumlada jadvalda yo'q nom: {sorted(named - set(SPEC))}"

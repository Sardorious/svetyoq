"""i18n kalitlari: kod ↔ katalog ↔ katalog.

`CLAUDE.md` §2 va `04` §6: qattiq kodlangan foydalanuvchi matni —
**bloklovchi defekt**. Shuning uchun butun matn `app/core/i18n/locales`
dan keladi. Mavjud `tests/test_i18n.py` esa **faqat bitta yo'nalishni**
o'lchaydi: `missing_keys(lang)` — «UZ da bor, `lang` da yo'q». Uchta
boshqa yo'nalish bugungacha umuman o'lchanmagan va uchtasi ham
**xato bermaydi**.

## Nima uchun bu sinf jim buziladi

`t()` topa olmagan kalitni **kalitning o'zini** qaytaradi
(`app/core/i18n/__init__.py:189`, ataylab — ilova yiqilmasin). Ya'ni:

1. **Kod katalogda yo'q kalitni so'raydi.** Telegram xabarida
   `report.accepted.pendng` chiqadi, API javobida `"message":
   "error.day_not_complet"`. Istisno yo'q, javob `200`, testlar yashil.
   Kalit ko'p joyda **literal emas**: u `MENU_KEYS`, `MESSAGE_KEYS`,
   `BAND_KEYS`, `message_key` jadvallaridan yoki f-satrdan yig'iladi
   (`f"digest.status.{status}"`), ya'ni chaqiruv joyida ko'rinmaydi.
2. **`missing_keys()` bir tomonlama.** U `set(uz) - set(lang)` ni
   qaytaradi, ya'ni **faqat RU da** bor kalit hech qanday testda
   ko'rinmaydi va o'zbek foydalanuvchi kalitning o'zini o'qiydi —
   UZ standart til bo'lgani uchun bu yo'nalish xavfliroq.
3. **Joy egalari ajralib ketadi.** `{count}` UZ da bor, RU da yo'q
   bo'lsa — `t()` `KeyError` ni yutadi va **formatlanmagan** satr
   qaytadi, ya'ni foydalanuvchi `{count}` ni ekranda ko'radi. Teskarisi
   ham shunday: RU da ortiqcha `{foo}` chaqiruvchi bermagan argumentni
   so'raydi. Ikkalasi ham xato bermaydi.
4. **Buzilgan qavs** (`"{count"`) `str.format` da `ValueError` beradi,
   uni esa `t()` **ushlamaydi** (faqat `KeyError`/`IndexError`) —
   bu yagona shovqinli variant, lekin u bazadan emas katalogdan keladi
   va CI da hech qachon o'qilmagan.

## Nima uchun `ast`, prefiks emas

«`digest.` bilan boshlangan har bir satr — i18n kaliti» qoidasi
**yolg'on**: `app/admin/roles.py` da `"digest.read"`, `"outage.read"`,
`"outage.reject"`, `"outage.merge"` — bular ruxsatlar, va
`app/jobs/daily_digest.py` da `"digest.send_failed"`,
`"digest.not_configured"` — jurnal hodisalari. Bunday test birinchi
ishga tushishida to'qqizta yolg'on ogohlantirish berardi va uni
«noto'g'ri test» deb o'chirishardi.

`error.` esa **ajratilgan**: `app/` dagi har bir `"error.…"` literali
haqiqatan i18n kaliti (bugun 30 ta chaqiruv joyi, 16 xil kalit), ya'ni
u alohida qoida bo'lishga arziydi.

## Teskari yo'nalish (3-qatlam)

Yuqoridagi qoidalar «kod so'ragan kalit katalogda bormi» degan savolga
javob beradi. **Teskarisi ham jim buziladi:** katalogda ikkala tilda
tarjima qilingan, lekin hech qachon ko'rsatilmaydigan qator turishi
mumkin. U xato bermaydi, `test_i18n.py` ni ham, yuqoridagi
qoidalarni ham o'tadi — va odam uni «bor, demak ishlaydi» deb o'qiydi.

**Bu yerda prefiks emas, aynan tenglik ishlatiladi.** Katalogdagi
kalitga **teng** bo'lgan har bir o'zgarmas satr — murojaat; prefiks
bo'yicha o'qish esa teskari xatoni berardi: `"outage.read"` va
`"digest.read"` (ruxsatlar, `admin/roles.py`), `"outage.reject"`
(audit amali), `"digest.send_failed"` (jurnal hodisasi),
`"map.snapshot_missing"` (`clustering/snapshot.py:209`),
`"notify.default_radius_m"` (konfiguratsiya kaliti,
`notifications/params.py:53`), `"outage.confirmed"` (outbox topigi) —
bularning bittasi ham katalog kaliti emas va bittasi ham tenglik
qoidasiga tushmaydi.

**`MAP_I18N_PREFIXES` ataylab murojaat deb hisoblanmaydi.**
`get_map_i18n` katalogdan prefiks bo'yicha oladi (`api/v1/map.py:227`),
ya'ni uni yo'l deb qabul qilsak `map.*`, `stats.*`, `heatmap.*`,
`app.*`, `outage.*` — **137 dan ~56 kalit** avtomatik «tirik» bo'lardi
va qoida o'sha kalitlar uchun jimgina ma'nosini yo'qotardi. Ular
o'rniga **mijoz** o'qiladi: `web/index.html` ning `data-i18n` atributi
va `web/app.js` ning `t("…")` chaqiruvlari. Aynan shu qaror
`heatmap.cell` ni (u faqat `app.js:146` da) va `app.name` ni
(u **hech qayerda**) bir-biridan ajratadi.

Test bazasiz: katalog fayllari, `app/` manba matni va `web/` o'qiladi.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from string import Formatter

import pytest

import app as app_pkg
from app.admin import digest as admin_digest
from app.admin import registries as registries_mod
from app.bot import keyboards, reply
from app.clustering import lookup
from app.clustering.scale import Scale
from app.clustering.status import OutageStatus
from app.core.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from app.notifications import render as notify_render
from app.release import gates, measures
from app.stats import coverage, heatmap, maturity, methodology

APP_ROOT = Path(app_pkg.__file__).resolve().parent
LOCALES = APP_ROOT / "core" / "i18n" / "locales"
#: Statik veb-xarita. U Python kataloglarini import qila olmaydi va matnni
#: `/map/i18n` dan oladi — ya'ni `map.*` oilasining yagona **o'quvchisi**.
WEB_ROOT = APP_ROOT.parent / "web"

#: Skaner bo'shab qolmasligining pastki chegarasi (34-sessiyaning saboqi).
#: Bugun: 137 kalit, ~35 literal `t()` chaqiruvi, 30 ta `error.` literali,
#: 134 ta yetib boriladigan kalit, `web/` da 26 ta kalit.
MIN_KEYS = 100
MIN_LITERAL_CALLS = 25
MIN_ERROR_LITERALS = 15
MIN_REACHABLE = 125
MIN_WEB_KEYS = 20


def _catalog(lang: str) -> dict[str, str]:
    """Katalog to'g'ridan-to'g'ri fayldan.

    `app.core.i18n._catalog` **`lru_cache`** bilan o'ralgan va uning
    natijasi boshqa testlar tomonidan ham ishlatiladi. Bu yerda fayl
    qayta o'qiladi: test kesh holatiga bog'liq bo'lmasligi kerak.
    """
    return json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))


def _keys(lang: str) -> set[str]:
    return set(_catalog(lang))


def _fields(value: str) -> set[str]:
    """`str.format` joy egalari — `{count}` → `{"count"}`.

    Regex emas, `string.Formatter` — aynan `t()` ichida `value.format()`
    ishlatadigan tahlilchi. Regex `{{` ni (qochirilgan qavs) joy egasi
    deb o'qirdi.
    """
    return {name for _lit, name, _spec, _conv in Formatter().parse(value) if name}


# --------------------------------------------------------------------------
# Koddagi kalitlar
# --------------------------------------------------------------------------


def _source_files() -> list[Path]:
    return sorted(APP_ROOT.rglob("*.py"))


def _literal_t_calls() -> list[tuple[str, str]]:
    """`t("literal", …)` chaqiruvlari → `(kalit, joy)`.

    Faqat **birinchi pozitsion argument o'zgarmas satr** bo'lgan holat.
    `t(key, lang)` va `t(f"digest.status.{status}", lang)` bu yerga
    tushmaydi — ular quyidagi jadval va oila testlarida o'lchanadi.
    """
    found: list[tuple[str, str]] = []
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name != "t":
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                found.append((first.value, f"{path.name}:{node.lineno}"))
    return found


def _error_literals() -> list[tuple[str, str]]:
    """`app/` dagi har bir `"error.…"` o'zgarmas satri.

    `SvetaError.__subclasses__()` bu ishni bajara olmaydi: sinf faqat
    o'z moduli import qilinganda ko'rinadi, ya'ni test import tartibiga
    bog'liq bo'lib qolardi va **jimgina** kam o'lchardi. Ustiga u
    `ValidationError("error.day_not_complete", …)` shaklini umuman
    ko'rmasdi — kalit u yerda sinf atributi emas, chaqiruv argumenti
    (`app/api/v1/admin.py:293`).
    """
    found: list[tuple[str, str]] = []
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.startswith("error."):
                    found.append((node.value, f"{path.name}:{node.lineno}"))
    return found


#: `t()` ga kalit beradigan jadvallar — **haqiqiy obyektlar**, skaner emas.
#:
#: Bu yerda `ast` ishlatilmaydi va sabab bor: jadvalning qiymatlari
#: import paytida allaqachon hisoblangan, ya'ni ularni o'qish taxminsiz.
#: Ro'yxat qo'lda (38-sessiyaning `SEQUENTIAL_BY_DESIGN` naqshi): yangi
#: jadval qo'shgan odam uni shu yerga yozadi, aks holda uning kalitlari
#: hech qachon tekshirilmaydi.
KEY_TABLES: dict[str, tuple[str, ...]] = {
    "bot.keyboards.MENU_KEYS": tuple(keyboards.MENU_KEYS.values()),
    "bot.reply.MESSAGE_KEYS": tuple(reply.MESSAGE_KEYS.values()),
    "clustering.lookup.MESSAGE_KEYS": tuple(lookup.MESSAGE_KEYS.values()),
    "notifications.render.MESSAGE_KEYS": tuple(notify_render.MESSAGE_KEYS.values()),
    "stats.coverage.BAND_KEYS": tuple(coverage.BAND_KEYS.values()),
    "stats.heatmap.DISCLAIMER_KEYS": tuple(heatmap.DISCLAIMER_KEYS),
    "stats.maturity.MESSAGE_*": (maturity.MESSAGE_YOUNG, maturity.MESSAGE_MATURE),
    # Metodologiya bo'limlarining sarlavha va matn kalitlari
    # (`03` §R1.2). Ular `MethodologySection.title_key`/`body_key` da
    # f-satrdan yig'iladi, ya'ni skaner ularni ko'rmaydi; `SECTION_KEYS`
    # esa `SECTION_ORDER` dan chiqadi, ya'ni yangi bo'lim qo'shilishi
    # bilan bu ro'yxat o'zi kengayadi va yangi kalit darhol talab
    # qilinadi.
    "stats.methodology.SECTION_KEYS": methodology.SECTION_KEYS,
    # Reliz gate lari (`03` §6). Ikkala ro'yxat ham `GATES` reyestridan
    # chiqadi: yangi gate yoki yangi mezon qo'shilgan zahoti uning
    # kaliti talab qilinadi, chunki `t()` chaqiruvi `api/v1/admin.py`
    # da f-satr emas, **atribut** orqali beriladi (`summary_key`,
    # `blocks_key`, `Criterion.key`) va skaner uni ko'rmaydi.
    "release.gates.GATE_KEYS": gates.GATE_KEYS,
    "release.gates.CRITERION_KEYS": gates.CRITERION_KEYS,
    # O'lchov qamrovi (`03` §11). Gate lar bilan bir xil sabab:
    # `t()` ga kalit `Measure.key` / `Stage.key` atributi orqali
    # beriladi, ya'ni skaner uni ko'rmaydi.
    "release.measures.MEASURE_KEYS": measures.MEASURE_KEYS,
    "release.measures.STAGE_KEYS": measures.STAGE_KEYS,
    # Spetsifikatsiya reyestrlari indeksi. Gate lar bilan bir xil
    # sabab, kuchliroq shaklda: `Registry.key` **hisoblanadigan**
    # xususiyat (`f"registry.{code}"`), sabab kaliti esa `api/v1/
    # admin.py` da f-satrdan quriladi — ya'ni ikkala oila ham skaner
    # uchun butunlay ko'rinmas.
    "admin.registries.REGISTRY_KEYS": registries_mod.REGISTRY_KEYS,
    "admin.registries.REASON_KEYS": registries_mod.REASON_KEYS,
}


def _catalog_key_constants() -> dict[str, set[str]]:
    """`app/` dagi katalog kalitiga **teng** har bir o'zgarmas satr → joylari.

    Bu — teskari yo'nalishning asosiy skaneri va u ataylab `t()` ga
    bog'lanmaydi: kalitlarning katta qismi chaqiruv joyidan uzoqda,
    modul darajasidagi konstantada yashaydi
    (`WARNING_MISSING = "geo.warning.mahallas_missing"`,
    `geo/mahallas.py:40`), ro'yxatga qo'shiladi
    (`keys.append("digest.warning.queue")`) yoki sinf atributi bo'ladi
    (`message_key = "error.not_moderatable"`).

    **Tenglik, prefiks emas.** `"outage.read"`, `"digest.read"`,
    `"map.snapshot_missing"`, `"notify.default_radius_m"`,
    `"outage.confirmed"` — hech biri katalog kaliti emas, ya'ni bu
    qoida ularni umuman ko'rmaydi. Prefiks bo'yicha o'qish esa
    to'qqizta yolg'on «tirik» keltirib chiqarardi.
    """
    known = _keys(DEFAULT_LANGUAGE)
    found: dict[str, set[str]] = {}
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in known:
                    found.setdefault(node.value, set()).add(f"{path.name}:{node.lineno}")
    return found


#: `web/` dagi qo'shtirnoq ichidagi nuqtali identifikator.
#:
#: `data-i18n="map.title"` ham, `t("map.error")` ham shu bitta shaklga
#: tushadi, shuning uchun HTML va JS bir xil o'qiladi. Tenglik qoidasi
#: bu yerda ham amal qiladi: `app.js:193` dagi `t("outage.scale." + …)`
#: literali `"outage.scale."` — u katalog kaliti **emas** va bu to'g'ri,
#: o'sha oila `KEY_FAMILIES` da alohida sanaladi.
_WEB_TOKEN = re.compile(r"""["']([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+)["']""")


def _web_key_references() -> dict[str, set[str]]:
    """`web/` sahifasi ko'rsatadigan kalitlar → joylari.

    Nima uchun bu qatlam kerak. `map.*`, `heatmap.*` va ikkita
    `stats.*.title` kaliti Python kodida **umuman uchramaydi**: ular
    `/map/i18n` orqali statik sahifaga beriladi va u yerda
    ko'rsatiladi. Bu qatlamsiz teskari qoida 26 ta tirik kalitni
    «o'lik» deb ko'rsatardi va birinchi ishga tushishida o'chirilardi.
    """
    known = _keys(DEFAULT_LANGUAGE)
    found: dict[str, set[str]] = {}
    for path in sorted(WEB_ROOT.rglob("*")):
        if path.suffix not in {".html", ".js"}:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in _WEB_TOKEN.finditer(line):
                if match.group(1) in known:
                    found.setdefault(match.group(1), set()).add(f"{path.name}:{lineno}")
    return found


#: F-satrdan yig'iladigan kalitlar: prefiks + sanab bo'ladigan to'plam.
#:
#: **Bu testning eng qimmat qismi.** `t(f"digest.status.{status}")`
#: (`app/admin/digest.py:205`) va `f"stats.maturity.reason.{code}"`
#: (`app/stats/maturity.py:92`) statik tahlil uchun ko'rinmas: yangi
#: status yoki sabab kodi qo'shilsa, hisobotda `digest.status.<yangi>`
#: matni chiqadi va hech narsa xato bermaydi.
#:
#: `outage.scale.*` da muallif buni **allaqachon bilgan**:
#: `notifications/render.py:43` `text if text != key else scale` deb
#: yozilgan, ya'ni `t()` ning kalit qaytarishi u yerda qo'lda
#: aylanib o'tilgan. Bu yerda esa u o'lchanadi.
KEY_FAMILIES: dict[str, tuple[str, tuple[str, ...]]] = {
    "digest.status": (
        "digest.status.",
        tuple(str(s) for s in OutageStatus),
    ),
    "stats.maturity.reason": (
        "stats.maturity.reason.",
        (
            maturity.REASON_NO_HISTORY,
            maturity.REASON_SHORT_HISTORY,
            maturity.REASON_FEW_EVENTS,
        ),
    ),
    "outage.scale": (
        "outage.scale.",
        tuple(str(s) for s in Scale),
    ),
}


# --------------------------------------------------------------------------
# 1-qatlam — katalogning o'zi
# --------------------------------------------------------------------------


def test_the_two_catalogs_have_the_same_keys() -> None:
    """Ikki tomonlama — `missing_keys()` faqat bittasini ko'radi.

    `missing_keys(lang) = set(uz) - set(lang)`, ya'ni **faqat RU da**
    bor kalit hech qanday testda chiqmaydi. Uning narxi esa yuqoriroq:
    UZ — standart til (`DEFAULT_LANGUAGE`), demak o'zbek foydalanuvchi
    kalitning o'zini o'qiydi, rus foydalanuvchi esa `t()` ning UZ ga
    tushishi tufayli hech bo'lmasa **matn** ko'radi.
    """
    uz, ru = _keys("uz"), _keys("ru")
    assert sorted(uz - ru) == [], "UZ da bor, RU da yo'q"
    assert sorted(ru - uz) == [], "RU da bor, UZ da yo'q"


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_every_value_is_format_safe(lang: str) -> None:
    """Buzilgan qavs `t()` dan **o'tib ketadi**.

    `t()` `KeyError` va `IndexError` ni ushlaydi, `ValueError` ni emas —
    ya'ni `"{count"` kabi qiymat chaqiruvchini yiqitadi. Bu katalogdagi
    yagona shovqinli nosozlik va aynan shuning uchun uni bu yerda
    ushlash arzon.
    """
    for key, value in _catalog(lang).items():
        assert value.strip(), f"{lang}: {key} bo'sh"
        try:
            _fields(value)
        except ValueError as exc:  # pragma: no cover — bugun sodir bo'lmaydi
            pytest.fail(f"{lang}: {key} — formatlab bo'lmaydi ({exc})")


def test_placeholders_match_between_languages() -> None:
    """Joy egalari ikkala tilda bir xil bo'lishi shart.

    Farq ikkala tomonga ham jim: yetishmagan `{count}` — raqamsiz
    xabar; ortiqcha `{foo}` — chaqiruvchi uni bermaydi, `t()`
    `KeyError` ni yutadi va foydalanuvchi **jingalak qavsni ekranda
    ko'radi**. Bugun 18 ta kalitda joy egasi bor va ikkala katalogda
    ular aynan mos.
    """
    uz, ru = _catalog("uz"), _catalog("ru")
    mismatched = {
        key: (sorted(_fields(uz[key])), sorted(_fields(ru[key])))
        for key in sorted(set(uz) & set(ru))
        if _fields(uz[key]) != _fields(ru[key])
    }
    assert mismatched == {}, f"joy egalari mos emas (uz, ru): {mismatched}"


# --------------------------------------------------------------------------
# 2-qatlam — kod → katalog
# --------------------------------------------------------------------------


def test_every_literal_key_is_in_the_catalog() -> None:
    """`t("…")` chaqiruvidagi har bir kalit katalogda bo'lishi shart."""
    known = _keys(DEFAULT_LANGUAGE)
    missing = sorted({f"{key} ({where})" for key, where in _literal_t_calls() if key not in known})
    assert missing == [], f"`t()` katalogda yo'q kalitni so'raydi: {missing}"


def test_every_key_table_holds_catalog_keys() -> None:
    """Jadvaldan kelgan kalit chaqiruv joyida umuman ko'rinmaydi.

    `t(MENU_KEYS[Action.MAP], lang)` — bu yerda kalit yo'q, u
    `keyboards.py:53` da. Shuning uchun literal skaneri bu sinfni
    umuman ushlamaydi va jadvallar alohida o'lchanadi.
    """
    known = _keys(DEFAULT_LANGUAGE)
    missing = {
        name: sorted(key for key in keys if key not in known)
        for name, keys in KEY_TABLES.items()
        if any(key not in known for key in keys)
    }
    assert missing == {}, f"jadvalda katalogda yo'q kalit: {missing}"


def test_every_error_literal_is_in_the_catalog() -> None:
    """`error.` — i18n uchun ajratilgan prefiks.

    Xato kaliti ikki xil yo'l bilan beriladi: sinf atributi
    (`message_key = "error.not_found"`) va konstruktor argumenti
    (`ValidationError("error.day_not_complete", …)`). Ikkalasi ham
    `main.py:90` da `t(exc.message_key, …)` ga tushadi, ya'ni yozuv
    xatosi mijozga `"message": "error.…"` bo'lib qaytadi — HTTP kodi
    to'g'ri, `code` to'g'ri, faqat matn yo'q.
    """
    known = _keys(DEFAULT_LANGUAGE)
    missing = sorted({f"{key} ({where})" for key, where in _error_literals() if key not in known})
    assert missing == [], f"`error.` kaliti katalogda yo'q: {missing}"


def test_every_dynamic_family_is_complete() -> None:
    """F-satrdan yig'iladigan kalitlarning **har bir a'zosi** katalogda.

    Statik tahlil bu joylarni ko'rmaydi va shuning uchun to'plam
    manbadan olinadi: `OutageStatus`, `maturity.REASON_*`, `Scale`.
    Enumga yangi a'zo qo'shilsa test yiqiladi va aytadigan gapi aniq —
    katalogga qator qo'shilsin.
    """
    known = _keys(DEFAULT_LANGUAGE)
    missing = {
        name: sorted(f"{prefix}{item}" for item in items if f"{prefix}{item}" not in known)
        for name, (prefix, items) in KEY_FAMILIES.items()
        if any(f"{prefix}{item}" not in known for item in items)
    }
    assert missing == {}, f"dinamik oilada kalit yetishmaydi: {missing}"


def test_the_digest_shows_every_status() -> None:
    """`STATUS_ORDER` — kortej, ya'ni tushib qolgan status **jim** yo'qoladi.

    `render()` faqat shu kortej bo'yicha aylanadi (`digest.py:206`).
    Lug'at bo'lganida yetishmagan status `KeyError` berardi; kortejda
    esa hisobot shunchaki bitta qatorsiz chiqadi va uzilishlarning
    umumiy soni («Uzilishlar: N») qatorlar yig'indisiga to'g'ri
    kelmay qoladi — buni faqat qo'lda solishtirib ko'rish mumkin.
    """
    assert set(admin_digest.STATUS_ORDER) == {str(s) for s in OutageStatus}


def test_every_enum_member_has_a_key() -> None:
    """Jadval o'z domenini to'liq qoplaydi.

    Yetishmagan a'zo `KeyError` beradi (`MENU_KEYS[Action.MAP]`), ya'ni
    bu **shovqinli** nosozlik — lekin u foydalanuvchining birinchi
    xabarida chiqadi, testda emas: bugun bironta test barcha `Verdict`
    qiymatlari bo'ylab aylanmaydi.
    """
    assert set(keyboards.MENU_KEYS) == set(keyboards.Action)
    assert set(reply.MESSAGE_KEYS) == set(reply.Verdict)
    assert set(lookup.MESSAGE_KEYS) == set(lookup.AreaVerdict)
    assert set(coverage.BAND_KEYS) == set(coverage.CoverageBand)


# --------------------------------------------------------------------------
# Skanerning o'zi
# --------------------------------------------------------------------------


def test_the_scan_is_measuring_something() -> None:
    """Bo'sh to'plam bo'sh to'plamga teng (34-sessiyaning saboqi).

    `t` qayta nomlansa yoki `Constant` shakli o'zgarsa, yuqoridagi
    qoidalarning hammasi **yashil** bo'lardi va hech narsa
    tekshirilmagani ko'rinmasdi.
    """
    literals = _literal_t_calls()
    keys = {key for key, _where in literals}
    modules = {where.split(":")[0] for _key, where in literals}
    assert len(_keys(DEFAULT_LANGUAGE)) >= MIN_KEYS
    assert len(literals) >= MIN_LITERAL_CALLS, f"faqat {len(literals)} ta `t()` topildi"
    assert len(_error_literals()) >= MIN_ERROR_LITERALS
    # Uchta turli modul — skaner bitta faylga qamalib qolmasin.
    # Qator raqami **ataylab** tekshirilmaydi: f-satr ichidagi chaqiruvning
    # `lineno` si Python versiyalari orasida bir xil emas.
    assert {"handlers.py", "digest.py", "openapi.py"} <= modules
    assert {"bot.menu.title", "app.disclaimer", "digest.title"} <= keys


def test_key_tables_and_families_are_not_empty() -> None:
    """Jadval bo'shab qolsa uning qoidasi ham jimgina o'chadi."""
    for name, keys in KEY_TABLES.items():
        assert keys, f"{name} bo'sh"
        assert all(isinstance(key, str) for key in keys), f"{name} da satr emas qiymat"
    for name, (prefix, items) in KEY_FAMILIES.items():
        assert prefix.endswith("."), f"{name}: prefiks nuqta bilan tugashi shart"
        assert items, f"{name} bo'sh"


# --------------------------------------------------------------------------
# 3-qatlam — katalog → kod (teskari yo'nalish)
# --------------------------------------------------------------------------


def _reachable_keys() -> set[str]:
    """Kalitga yo'l bor deb hisoblanadigan to'rtta manba.

    `MAP_I18N_PREFIXES` bu ro'yxatda **yo'q** — sabab modul
    docstringida: u 137 dan ~56 kalitni avtomatik oqlab, qoidani
    o'sha kalitlar uchun ma'nosiz qilardi. Uning o'rniga `web/` o'qiladi.
    """
    reachable = set(_catalog_key_constants())
    reachable |= set(_web_key_references())
    for keys in KEY_TABLES.values():
        reachable |= set(keys)
    for prefix, items in KEY_FAMILIES.values():
        reachable |= {f"{prefix}{item}" for item in items}
    return reachable


#: Katalogda bor, lekin hech qayerda ko'rsatilmaydigan kalitlar → sababi.
#:
#: Ro'yxat **qo'lda** (35- va 38-sessiyalarning naqshi): yangi o'lik kalit
#: paydo bo'lsa test yiqiladi va uni bu yerga yozish — **ko'rinadigan
#: qaror**, jim o'tib ketadigan holat emas. Kalitlar bugun
#: **o'chirilmadi**: matn ikkala tilda tayyor va uchalasi ham «o'lik satr»
#: emas, **ulanmagan javob** bo'lishi mumkin — bu odamning qarori
#: (`PROGRESS.md`, «Ochiq savollar»).
KNOWN_UNREACHABLE: dict[str, str] = {
    "app.name": (
        "`/map/i18n` javobiga `app.` prefiksi orqali **tushadi**, lekin uni "
        "hech kim ko'rsatmaydi: sahifa sarlavhasi `map.title` dan olinadi "
        "(`web/app.js:52`). Ya'ni kalit tarmoqdan o'tadi va ekranga chiqmaydi — "
        "o'chirish `/map/i18n` payloadini o'zgartiradi."
    ),
    "bot.location.invalid": (
        "Yozilgan, lekin ulanmagan javob. `on_location` `F.location` filtri "
        "bilan ro'yxatdan o'tgan (`bot/handlers.py:401`), ya'ni "
        "`message.location` hech qachon `None` bo'lmaydi; hudud tashqarisi esa "
        "`error.out_of_region` bilan javob beradi. Yaroqsiz geolokatsiyaning "
        "boshqa yo'li bugun yo'q."
    ),
    "outage.scale.capped": (
        "Oila a'zosiga **o'xshaydi** va aynan shuning uchun jim: `Scale` da "
        "bunday a'zo yo'q (`local|mahalla|district`), `scale_capped` esa "
        "**mantiqiy ustun** (`clustering/models.py:108`). Qiymat bazaga "
        "yoziladi (`clustering/service.py:372`), birorta javobga chiqmaydi, "
        "ya'ni `scale_text()` ham, `web/app.js:193` ham bu kalitni hech qachon "
        "yasay olmaydi."
    ),
}


def test_no_catalog_key_is_unreachable() -> None:
    """Katalogda bor, kodda yo'q kalit — **jim** nosozlik.

    U hech qanday xatolikka olib kelmaydi: tarjima ikkala tilda joyida
    turadi, `test_i18n.py` yashil, yuqoridagi ikkala qatlam ham yashil.
    Zarari boshqa yo'nalishda: kalitni ko'rgan odam «demak bu holat
    ishlangan» deb o'qiydi — `outage.scale.capped` da aynan shunday
    (`06` §10 dagi qamrov chegarasining foydalanuvchiga ko'rinadigan
    javobi yozilgan, lekin ulanmagan).
    """
    unreachable = _keys(DEFAULT_LANGUAGE) - _reachable_keys()
    new = sorted(unreachable - set(KNOWN_UNREACHABLE))
    assert new == [], (
        "kalit katalogda bor, lekin hech qayerda ko'rsatilmaydi. Uni ulang "
        f"yoki sababi bilan `KNOWN_UNREACHABLE` ga yozing: {new}"
    )


def test_every_known_unreachable_key_is_still_unreachable() -> None:
    """Teskari qulf: ulangan kalit ro'yxatda qololmaydi.

    Usiz ro'yxat vaqt o'tishi bilan «o'chirilmaydigan istisnolar»
    to'plamiga aylanardi va o'sha nom boshqa mazmun bilan qaytganda
    jim o'tib ketardi (38-sessiyaning `SEQUENTIAL_BY_DESIGN` saboqi).
    """
    wired = sorted(set(KNOWN_UNREACHABLE) & _reachable_keys())
    assert wired == [], f"kalit endi ishlatiladi — `KNOWN_UNREACHABLE` dan o'chiring: {wired}"


def test_the_unreachable_list_has_no_stale_entries() -> None:
    """Katalogdan olib tashlangan kalit ro'yxatda qolmaydi."""
    stale = sorted(set(KNOWN_UNREACHABLE) - _keys(DEFAULT_LANGUAGE))
    assert stale == [], f"katalogda bunday kalit yo'q: {stale}"
    for key, reason in KNOWN_UNREACHABLE.items():
        assert reason.strip(), f"{key}: sabab yozilmagan"


def test_every_map_i18n_prefix_still_matches_a_key() -> None:
    """Oq ro'yxatdagi prefiks hech narsaga mos kelmasa — jim no-op.

    `heatmap.` `heat.` ga qayta nomlansa `/map/i18n` o'sha oilani
    berishdan **to'xtaydi**, sahifa esa bo'sh satrlar ko'rsatadi:
    `t()` mijoz tomonida ham topa olmagan kalitni qaytaradi
    (`web/app.js`), ya'ni xato chiqmaydi.
    """
    from app.api.v1.map import MAP_I18N_PREFIXES

    known = _keys(DEFAULT_LANGUAGE)
    empty = [p for p in MAP_I18N_PREFIXES if not any(k.startswith(p) for k in known)]
    assert empty == [], f"oq ro'yxatdagi prefiks bo'sh: {empty}"


def test_the_reverse_scan_is_measuring_something() -> None:
    """Ikkala yangi skaner ham bo'shab qololmaydi.

    `web/` skaneri eng nozigi: fayl ko'chirilsa yoki `data-i18n`
    boshqa shaklga o'tsa, `_web_key_references()` bo'shab qolardi va
    26 ta tirik kalit birdan «o'lik» bo'lib ko'rinardi — ya'ni test
    o'zi qo'riqlayotgan xatoni **o'zi** yasab berardi.
    """
    constants = _catalog_key_constants()
    web = _web_key_references()
    assert len(_reachable_keys()) >= MIN_REACHABLE
    assert len(web) >= MIN_WEB_KEYS, f"`web/` da faqat {len(web)} kalit topildi"
    # Konstanta qatlami: bu kalit `t()` chaqiruvida umuman ko'rinmaydi.
    assert "geo.warning.mahallas_missing" in constants
    assert "error.not_moderatable" in constants
    # Veb qatlami: ikkala fayl turi ham o'qilishi shart.
    assert "stats.coverage.title" in web  # index.html, `data-i18n`
    assert "heatmap.cell" in web  # app.js, `t("…", {…})`

"""`tools/region_admin.py` — bazaga bog'liq yarmi (212-run).

211-run `tools/tz_check.py` uchun shu usulni ochgan: `session_scope()`
ning o'rniga so'rovni **yozib oladigan** fikstyura qo'yiladi, ya'ni na
baza, na `requires_db` kerak. Sandboxda `requires_db` `skip` ga tushadi,
`skip` esa o'lchov emas.

`region_admin` bu usulga eng muhtoj fayl edi: 478 qator, 6 buyruq va
**birorta o'z testi yo'q**. Repodagi yagona murojaatlar — manba matnini
`grep` qiladigan yoki `build_parser()` ni chaqiradigan kontrakt
testlari, ya'ni buyruqning **ichidagi** birorta qaror o'lchanmagan.
Fayl esa E19 ning chiqish mezonini bajaradigan yagona yo'l («yangi
shahar deploysiz ishga tushadi») va BR-024 ning spravochnik tomonidagi
yagona bajaruvchisi.

Fikstyuraning xavfi ma'lum (javobni o'ylab topgan soxta baza hech
narsani o'lchamaydi), shuning uchun 211-running ikkita qoidasi shu
yerda ham: so'rovning o'zi saqlanadi va unga ham da'vo qo'yiladi,
tekshiruv esa SQL **matnidan** emas, bog'langan parametridan olinadi
(`compile(...).params`).
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import pytest
from sqlalchemy.dialects import postgresql

from app.admin import audit
from app.clustering.params import DEFAULTS
from app.core.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from app.geo.models import Region, RegionConfig
from app.notifications import params as notify_params
from tools import region_admin

pytestmark = pytest.mark.anyio

REGION_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")

#: Samarqand emas: yangi shahar qo'shish yo'li o'lchanadi.
CODE = "bukhara"
BBOX = "39.70,64.35,39.85,64.52"
#: bbox markazi — qo'lda hisoblangan, `parse_bbox` dan olinmaydi.
BBOX_CENTER = (39.775, 64.435)


# --------------------------------------------------------------------------
# Fikstyura
# --------------------------------------------------------------------------


class Recorded:
    """Bazaga qilingan har bir murojaat — chaqirilgan tartibda."""

    def __init__(self) -> None:
        self.statements: list = []
        self.added: list = []
        self.flushes = 0
        self.gets: list = []
        self.audits: list[dict] = []
        self.scopes = 0

    @property
    def regions_added(self) -> list[Region]:
        return [obj for obj in self.added if isinstance(obj, Region)]

    @property
    def config_added(self) -> list[RegionConfig]:
        return [obj for obj in self.added if isinstance(obj, RegionConfig)]

    @property
    def seeded_keys(self) -> list[str]:
        return [row.key for row in self.config_added]

    def params(self, index: int = 0) -> dict:
        """`index` -chi so'rovning **bog'langan** parametrlari.

        SQL matni emas: matn ustundan ham, qiymatdan ham mustaqil
        emas, bog'langan parametr esa ikkovini ham nomlab beradi
        (kalitning nomi ustundan yasaladi, ya'ni `Region.code` ni
        `Region.name_uz` ga almashtirgan mutant boshqa kalit bilan
        yiqiladi).
        """
        return self.statements[index].compile(dialect=postgresql.dialect()).params


class _Result:
    def __init__(self, rows: list) -> None:
        self._rows = list(rows)

    def scalar_one_or_none(self):
        assert len(self._rows) <= 1, "bir nechta qator"
        return self._rows[0] if self._rows else None

    def scalars(self) -> _Result:
        return self

    def all(self) -> list:
        return list(self._rows)


class RecordingSession:
    """`AsyncSession` ning o'rni: so'rovni yozib oladi, keyin javob beradi.

    Javob so'rovning **shakliga qarab** tanlanadi, navbat bo'yicha
    emas: navbat ikkita so'rovni almashtirgan mutantni ko'rmasdi.
    """

    def __init__(self, seen: Recorded, regions: list[Region], config: dict) -> None:
        self._seen = seen
        self._regions = regions
        self._config = dict(config)

    async def execute(self, statement):
        self._seen.statements.append(statement)
        names = tuple(d["name"] for d in statement.column_descriptions)
        if names == ("Region",):
            return _Result(self._regions)
        if names == ("key",):
            return _Result([(key,) for key in self._config])
        if names == ("key", "value"):
            return _Result(sorted(self._config.items()))
        raise AssertionError(f"kutilmagan so'rov: {names}")

    def add(self, obj) -> None:
        self._seen.added.append(obj)
        if isinstance(obj, Region) and obj.id is None:
            # `flush()` ning o'rni: `cmd_add` `region.id` ni audit
            # yozuvida ishlatadi, ya'ni identifikator kerak.
            obj.id = REGION_ID

    async def flush(self) -> None:
        self._seen.flushes += 1

    async def get(self, entity, key):
        self._seen.gets.append((entity, key))
        _, config_key = key
        if config_key not in self._config:
            return None
        return RegionConfig(region_id=key[0], key=config_key, value=self._config[config_key])


def wire(monkeypatch, *, regions=(), config=None) -> Recorded:
    """`session_scope()` va `audit.record()` ni yozib oladigan o'rinbosarlarga almashtiradi."""
    seen = Recorded()
    session = RecordingSession(seen, list(regions), config or {})

    @asynccontextmanager
    async def _scope():
        seen.scopes += 1
        yield session

    async def _record(inner, *, actor, action, object_id, before=None, after=None):
        assert inner is session, "audit yozuvi boshqa sessiyada"
        seen.audits.append(
            {
                "actor": actor,
                "action": action,
                "object_id": object_id,
                "before": before,
                "after": after,
            }
        )
        return None

    monkeypatch.setattr(region_admin, "session_scope", _scope)
    monkeypatch.setattr(region_admin.audit, "record", _record)
    return seen


def region(
    *,
    code: str = CODE,
    is_active: bool = False,
    bbox: tuple[float, float, float, float] | None = (39.70, 64.35, 39.85, 64.52),
    name_uz: str = "Buxoro",
    name_ru: str = "Бухара",
    lang: str = "uz",
) -> Region:
    """Haqiqiy `Region` — `dataclass` o'rinbosar `bbox` xossasini bermasdi."""
    row = Region(
        code=code,
        name_uz=name_uz,
        name_ru=name_ru,
        default_language=lang,
        is_active=is_active,
    )
    row.id = REGION_ID
    if bbox is not None:
        row.bbox_min_lat, row.bbox_min_lon, row.bbox_max_lat, row.bbox_max_lon = bbox
    return row


async def run(argv: list[str]) -> int:
    """`main()` ning o'rni: `asyncio.run` va `dispose_engine` siz."""
    args = region_admin.build_parser().parse_args(argv)
    return await args.func(args)


def center_of(row: Region) -> tuple[float, float]:
    """`regions.center` ifodasidan (lat, lon) — bog'langan parametrlardan."""
    params = row.center.compile(dialect=postgresql.dialect()).params
    values = [v for k, v in sorted(params.items()) if isinstance(v, float)]
    # `ST_MakePoint(lon, lat)` — tartib `_point` ning ichida
    # (`tests/test_geo_sql_expressions.py`), bu yerda esa
    # **chaqiruvchi** o'lchanadi.
    lon, lat = values[0], values[1]
    return lat, lon


# --------------------------------------------------------------------------
# 1. Fikstyuraning o'zi nimadir o'lchayotganini tekshirish
# --------------------------------------------------------------------------


async def test_the_fixture_records_a_real_statement(monkeypatch) -> None:
    """Bo'sh ro'yxat bo'sh ro'yxatga teng bo'lib qolmasin.

    Quyidagi da'volarning hammasi `seen.statements` ga tayanadi;
    fikstyura so'rovni yozib olmay qo'ysa ularning ko'pi jimgina
    yashil bo'lardi.
    """
    seen = wire(monkeypatch, regions=[region()])
    assert await run(["list", ]) == region_admin.EXIT_OK
    assert seen.scopes == 1
    assert len(seen.statements) == 1
    assert seen.statements[0].column_descriptions[0]["name"] == "Region"


async def test_list_without_regions_says_so(monkeypatch, capsys) -> None:
    """Bo'sh spravochnik — javob, sukut emas."""
    wire(monkeypatch, regions=[])
    assert await run(["list"]) == region_admin.EXIT_OK
    assert "region_admin add" in capsys.readouterr().out


# --------------------------------------------------------------------------
# 2. Kodni normallashtirish — beshala buyruqda
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["update", "--code", "  BuKhArA ", "--name-uz", "X"],
        ["activate", "--code", "  BuKhArA "],
        ["deactivate", "--code", "  BuKhArA "],
        ["config", "--code", "  BuKhArA "],
    ],
)
async def test_every_command_looks_up_the_normalised_code(monkeypatch, argv) -> None:
    """`strip().lower()` beshta joyda alohida yozilgan.

    Bittasini tushirib qoldirgan mutant faqat shu buyruqda ko'rinadi
    va qolganlari yashil qoladi — shuning uchun har biri alohida
    o'lchanadi. Tekshiruv **bog'langan parametrdan**: SQL matnida
    kod umuman ko'rinmaydi.

    Kalitning **nomi** ham qulflanadi, faqat qiymati emas: `code_1`
    ustunning nomidan yasaladi, ya'ni `Region.name_uz` ga o'tgan
    mutant bir xil qiymatni boshqa kalit bilan bog'laydi. Birinchi
    o'tishda aynan shu mutant omon qolgan edi — qoida izohda yozilib,
    da'voda bajarilmagan edi.
    """
    seen = wire(monkeypatch, regions=[region()], config={"confirm.coef": 0.5})
    await run(argv)
    assert seen.params(0) == {"code_1": CODE}


async def test_add_stores_the_normalised_code(monkeypatch) -> None:
    """Qidiruv normallashtirilib, yozuv normallashtirilmasa kod ikkiga bo'linardi."""
    seen = wire(monkeypatch, regions=[])
    argv = ["add", "--code", " BUKHARA ", "--name-uz", "Buxoro", "--name-ru", "Бухара"]
    assert await run([*argv, "--bbox", BBOX]) == region_admin.EXIT_OK
    assert seen.params(0) == {"code_1": CODE}
    assert seen.regions_added[0].code == CODE
    assert seen.audits[0]["after"]["code"] == CODE


# --------------------------------------------------------------------------
# 3. `add` — yangi mintaqa
# --------------------------------------------------------------------------


def add_argv(*extra: str) -> list[str]:
    return [
        "add",
        "--code",
        CODE,
        "--name-uz",
        "Buxoro",
        "--name-ru",
        "Бухара",
        "--bbox",
        BBOX,
        *extra,
    ]


async def test_add_creates_the_region_disabled(monkeypatch) -> None:
    """`is_active=False` — asbobning eng qimmat qarori.

    Chegaralar import qilinib tekshirilgunicha mintaqa ommaviy
    ro'yxatda ko'rinmasligi kerak; `True` qo'ygan mutant bugungacha
    hech qayerda yiqilmasdi. Audit yozuvi ham shuni takrorlaydi —
    ikkovi ajralsa jurnal yolg'on gapirardi.
    """
    seen = wire(monkeypatch, regions=[])
    assert await run(add_argv()) == region_admin.EXIT_OK
    assert seen.regions_added[0].is_active is False
    assert seen.audits[0]["after"]["is_active"] is False


async def test_add_seeds_exactly_the_known_keys(monkeypatch) -> None:
    """Seed to'plami — `seed_defaults()` ning aynan o'zi, `DEFAULTS` emas.

    Maxraj o'lchanayotgan koddan olinmaydi: kalitlar soni ikkita
    manbadan qo'lda yig'iladi, ya'ni `notify.*` ni seed dan tushirib
    qoldirgan mutant shu yerda yiqiladi.
    """
    expected = sorted({*DEFAULTS, notify_params.KEY_DEFAULT_RADIUS, notify_params.KEY_MAX_RADIUS})
    seen = wire(monkeypatch, regions=[])
    await run(add_argv())
    assert sorted(seen.seeded_keys) == expected
    assert seen.audits[0]["after"]["config_keys_seeded"] == len(expected)


async def test_add_flushes_before_seeding(monkeypatch) -> None:
    """`region.id` `flush()` dan keyin paydo bo'ladi.

    `flush()` siz `_seed_config` va audit yozuvi `None` ga bog'lanardi
    — ikkalasi ham begona mintaqaga tegishli bo'lib qolardi.
    """
    seen = wire(monkeypatch, regions=[])
    await run(add_argv())
    assert seen.flushes == 1
    assert {row.region_id for row in seen.config_added} == {REGION_ID}
    assert seen.audits[0]["object_id"] == REGION_ID


async def test_add_takes_the_centre_from_the_bbox(monkeypatch) -> None:
    """`--center` berilmasa markaz bbox dan; tartib (lat, lon)."""
    seen = wire(monkeypatch, regions=[])
    await run(add_argv())
    assert center_of(seen.regions_added[0]) == pytest.approx(BBOX_CENTER)
    assert seen.audits[0]["after"]["center"] == pytest.approx(list(BBOX_CENTER))


async def test_add_prefers_an_explicit_centre(monkeypatch) -> None:
    """Berilgan markaz bbox nikini bosadi va lat/lon almashmaydi.

    Ikkita son ataylab bir-biridan va bbox markazidan farq qiladi:
    teng qiymatlarda almashuv ko'rinmasdi.
    """
    seen = wire(monkeypatch, regions=[])
    await run(add_argv("--center", "39.81,64.42"))
    assert center_of(seen.regions_added[0]) == pytest.approx((39.81, 64.42))
    assert seen.audits[0]["after"]["center"] == pytest.approx([39.81, 64.42])


async def test_add_refuses_an_existing_code(monkeypatch, capsys) -> None:
    """Mavjud kod — `EXIT_BLOCKED`, va hech narsa yozilmaydi."""
    seen = wire(monkeypatch, regions=[region()])
    assert await run(add_argv()) == region_admin.EXIT_BLOCKED
    assert seen.added == []
    assert seen.audits == []
    assert "[BLOK]" in capsys.readouterr().out


@pytest.mark.parametrize(
    "extra",
    [
        ["--bbox", "39.70,64.35"],
        ["--bbox", "39.85,64.35,39.70,64.52"],
        ["--center", "39.81"],
        ["--center", "1000,64.42"],
        ["--center", "x,y"],
    ],
)
async def test_add_parses_the_input_before_opening_a_session(monkeypatch, extra) -> None:
    """Yaroqsiz kirish sessiya **ochilishidan oldin** to'xtatiladi.

    `session_scope()` uchun `return` — normal tugash, ya'ni `commit`.
    Tahlil sessiya ichida bo'lsa yarim bajarilgan buyruq audit
    qatorisiz saqlanib qolardi (BR-024). `cmd_add` boshidan shunday
    yozilgan; bu yerda u **o'lchanadi**.
    """
    argv = [a for a in add_argv() if a not in ("--bbox", BBOX)] if "--bbox" in extra else add_argv()
    seen = wire(monkeypatch, regions=[])
    assert await run([*argv, *extra]) == region_admin.EXIT_USAGE
    assert seen.scopes == 0


async def test_add_defaults_to_the_catalogue_language(monkeypatch) -> None:
    """Til `app.core.i18n` dan: uchinchi til qo'shilsa asbob uni o'zi qabul qiladi."""
    seen = wire(monkeypatch, regions=[])
    await run(add_argv())
    assert seen.regions_added[0].default_language == DEFAULT_LANGUAGE
    assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES


# --------------------------------------------------------------------------
# 4. `update` — o'zgarish va uning jurnali
# --------------------------------------------------------------------------


async def test_update_without_any_field_changes_nothing(monkeypatch, capsys) -> None:
    """Bo'sh buyruq — `EXIT_USAGE`, jurnalda qator yo'q."""
    seen = wire(monkeypatch, regions=[region()])
    assert await run(["update", "--code", CODE]) == region_admin.EXIT_USAGE
    assert seen.audits == []
    assert "o'zgarish yo'q" in capsys.readouterr().out


async def test_update_refuses_an_unknown_code(monkeypatch) -> None:
    seen = wire(monkeypatch, regions=[])
    assert await run(["update", "--code", CODE, "--name-uz", "X"]) == region_admin.EXIT_BLOCKED
    assert seen.audits == []


async def test_update_rejects_a_bad_bbox_before_touching_the_row(monkeypatch) -> None:
    """Boshqa maydon berilgan bo'lsa ham qator tegilmaydi.

    Ilgari `--bbox` o'z navbati kelganda tahlil qilinardi va
    `--name-uz Foo --bbox xato` nomni bazaga yozib, audit qatorini
    yozmasdan chiqib ketardi. Fayldagi izoh shuni aytadi, test esa
    endi shuni **ushlaydi**.
    """
    row = region(name_uz="Buxoro")
    seen = wire(monkeypatch, regions=[row])
    argv = ["update", "--code", CODE, "--name-uz", "Yangi", "--bbox", "1,2,3"]
    assert await run(argv) == region_admin.EXIT_USAGE
    assert row.name_uz == "Buxoro"
    assert seen.scopes == 0
    assert seen.audits == []


async def test_update_logs_the_old_value_as_before(monkeypatch) -> None:
    """`before` ↔ `after` juftligi: almashuv bugungacha jim edi.

    Har bir maydonning eski va yangi qiymati ataylab har xil, ya'ni
    juftlikni teskari yozgan mutant har birida yiqiladi.
    """
    row = region(name_uz="Buxoro", name_ru="Бухара", lang="uz")
    seen = wire(monkeypatch, regions=[row])
    argv = [
        "update",
        "--code",
        CODE,
        "--name-uz",
        "Buxoro shahri",
        "--name-ru",
        "Город Бухара",
        "--lang",
        "ru",
    ]
    assert await run(argv) == region_admin.EXIT_OK
    entry = seen.audits[0]
    assert entry["action"] is audit.AuditAction.REGION_UPDATE
    assert entry["before"] == {
        "name_uz": "Buxoro",
        "name_ru": "Бухара",
        "default_language": "uz",
    }
    assert entry["after"] == {
        "name_uz": "Buxoro shahri",
        "name_ru": "Город Бухара",
        "default_language": "ru",
    }
    assert row.name_uz == "Buxoro shahri"
    assert row.default_language == "ru"


async def test_update_logs_the_old_bbox(monkeypatch) -> None:
    """bbox — to'rtta son va ularning tartibi (min_lat, min_lon, max_lat, max_lon)."""
    row = region(bbox=(1.0, 2.0, 3.0, 4.0))
    seen = wire(monkeypatch, regions=[row])
    assert await run(["update", "--code", CODE, "--bbox", BBOX]) == region_admin.EXIT_OK
    entry = seen.audits[0]
    assert entry["before"]["bbox"] == [1.0, 2.0, 3.0, 4.0]
    assert entry["after"]["bbox"] == [39.70, 64.35, 39.85, 64.52]
    assert row.bbox_min_lat == 39.70
    assert row.bbox_max_lon == 64.52


async def test_update_does_not_read_the_old_centre(monkeypatch) -> None:
    """`before["center"]` ataylab yo'q — `WKBElement` `jsonb` ni yiqitardi.

    Qoida izohda yozilgan; uni «to'liqlik uchun» qaytarib qo'ygan
    tahrir amal bajarilgandan **keyin** yiqiladigan yozuv yasardi.
    """
    row = region()
    seen = wire(monkeypatch, regions=[row])
    assert await run(["update", "--code", CODE, "--center", "39.81,64.42"]) == region_admin.EXIT_OK
    entry = seen.audits[0]
    assert "center" not in entry["before"]
    assert entry["after"]["center"] == pytest.approx([39.81, 64.42])
    assert center_of(row) == pytest.approx((39.81, 64.42))


# --------------------------------------------------------------------------
# 5. `activate` / `deactivate`
# --------------------------------------------------------------------------


async def test_activate_blocks_a_region_without_a_bbox(monkeypatch, capsys) -> None:
    """bbox siz mintaqa nuqta bo'yicha tanlanmaydi — «faol» bo'lsa ham jim qolardi."""
    row = region(bbox=None)
    seen = wire(monkeypatch, regions=[row])
    assert await run(["activate", "--code", CODE]) == region_admin.EXIT_BLOCKED
    assert row.is_active is False
    assert seen.audits == []
    assert "bbox" in capsys.readouterr().out


async def test_deactivate_needs_no_bbox(monkeypatch) -> None:
    """Qorovul faqat yoqishda: bbox siz qolgan mintaqani o'chira olmaslik qopqon bo'lardi."""
    row = region(bbox=None, is_active=True)
    seen = wire(monkeypatch, regions=[row])
    assert await run(["deactivate", "--code", CODE]) == region_admin.EXIT_OK
    assert row.is_active is False
    assert seen.audits[0]["action"] is audit.AuditAction.REGION_DEACTIVATE


async def test_activate_and_deactivate_use_their_own_action(monkeypatch) -> None:
    """Ikkita hodisa nomi almashsa jurnal teskari tarixni ko'rsatardi."""
    off = region(is_active=False)
    seen_on = wire(monkeypatch, regions=[off])
    assert await run(["activate", "--code", CODE]) == region_admin.EXIT_OK
    assert off.is_active is True
    assert seen_on.audits[0]["action"] is audit.AuditAction.REGION_ACTIVATE
    assert seen_on.audits[0]["before"] == {"is_active": False}
    assert seen_on.audits[0]["after"] == {"is_active": True}

    on = region(is_active=True)
    seen_off = wire(monkeypatch, regions=[on])
    assert await run(["deactivate", "--code", CODE]) == region_admin.EXIT_OK
    assert on.is_active is False
    assert seen_off.audits[0]["before"] == {"is_active": True}
    assert seen_off.audits[0]["after"] == {"is_active": False}


@pytest.mark.parametrize(("command", "active"), [("activate", True), ("deactivate", False)])
async def test_repeating_the_command_writes_no_row(monkeypatch, command, active) -> None:
    """Jurnal — o'zgarishlar tarixi, buyruqlar tarixi emas.

    Qayta-qayta `activate` qilingan mintaqa haqiqiy yoqilish sanasini
    bir xil qatorlar orasida ko'mib tashlardi.
    """
    seen = wire(monkeypatch, regions=[region(is_active=active)])
    assert await run([command, "--code", CODE]) == region_admin.EXIT_OK
    assert seen.audits == []


async def test_set_active_refuses_an_unknown_code(monkeypatch) -> None:
    seen = wire(monkeypatch, regions=[])
    assert await run(["activate", "--code", CODE]) == region_admin.EXIT_BLOCKED
    assert seen.audits == []


# --------------------------------------------------------------------------
# 6. `config` — `06` §9 + `notify.*`
# --------------------------------------------------------------------------


async def test_known_keys_is_exactly_what_the_tool_seeds(monkeypatch) -> None:
    """212-running topilmasi: bitta savolga ikkita jadval javob berardi.

    Seed `seed_defaults()` dan (17 kalit), qorovul va ro'yxatdagi
    yorliq esa `DEFAULTS` dan (15) — ya'ni asbob **o'zi seed qilgan**
    ikkita `notify.*` kalitini keyin noma'lum deb rad etardi.
    """
    assert region_admin.known_keys() == frozenset(region_admin.seed_defaults())
    assert notify_params.KEY_DEFAULT_RADIUS in region_admin.known_keys()
    assert notify_params.KEY_MAX_RADIUS in region_admin.known_keys()
    assert region_admin.known_keys() - frozenset(DEFAULTS) == {
        notify_params.KEY_DEFAULT_RADIUS,
        notify_params.KEY_MAX_RADIUS,
    }


@pytest.mark.parametrize("key", sorted(region_admin.seed_defaults()))
async def test_every_seeded_key_can_be_set(monkeypatch, key) -> None:
    """Seed qilingan kalit **o'zgartirilishi** shart.

    `01` §19: obuna radiusi mintaqa uchun alohida kalibrlanadi, ya'ni
    aynan bu qiymat o'zgarishi kutilgan. Uni asbobda yopib qo'yish
    odamni qo'lda `UPDATE` ga yuborardi — `audit_log` siz (BR-024).
    """
    seen = wire(monkeypatch, regions=[region()], config={})
    argv = ["config", "--code", CODE, "--key", key, "--value", "7"]
    assert await run(argv) == region_admin.EXIT_OK
    assert seen.config_added[0].key == key
    assert seen.config_added[0].value == 7.0


async def test_config_still_refuses_a_key_from_nowhere(monkeypatch, capsys) -> None:
    """Ro'yxat kengaydi, lekin yopiq qoldi."""
    seen = wire(monkeypatch, regions=[region()], config={})
    argv = ["config", "--code", CODE, "--key", "confirm.min_user", "--value", "3"]
    assert await run(argv) == region_admin.EXIT_USAGE
    assert seen.added == []
    assert seen.audits == []
    assert "[BLOK]" in capsys.readouterr().out


@pytest.mark.parametrize("value", ["", "ha", None])
async def test_config_refuses_a_non_numeric_value(monkeypatch, value) -> None:
    """`region_config.value` — `jsonb`, ya'ni unga har narsa yozilishi mumkin."""
    seen = wire(monkeypatch, regions=[region()], config={})
    argv = ["config", "--code", CODE, "--key", "confirm.coef"]
    if value is not None:
        argv += ["--value", value]
    assert await run(argv) == region_admin.EXIT_USAGE
    assert seen.added == []
    assert seen.audits == []


async def test_config_logs_none_when_the_key_was_absent(monkeypatch) -> None:
    """`before` da `None` — «kalit yo'q edi, kod `DEFAULTS` ga tushardi».

    Uni standart qiymat bilan to'ldirish jurnal o'quvchisiga qiymat
    bazada turgan degan yolg'onni aytardi — farq aynan shunda.
    """
    seen = wire(monkeypatch, regions=[region()], config={})
    argv = ["config", "--code", CODE, "--key", "confirm.coef", "--value", "0.9"]
    assert await run(argv) == region_admin.EXIT_OK
    assert seen.audits[0]["before"] == {"confirm.coef": None}
    assert seen.audits[0]["after"] == {"confirm.coef": 0.9}
    assert seen.audits[0]["action"] is audit.AuditAction.REGION_CONFIG_SET


async def test_config_overwrites_an_existing_key_and_logs_the_old_value(monkeypatch) -> None:
    """Mavjud kalit yangilanadi, yangi qator qo'shilmaydi."""
    seen = wire(monkeypatch, regions=[region()], config={"confirm.coef": 0.5})
    argv = ["config", "--code", CODE, "--key", "confirm.coef", "--value", "0.9"]
    assert await run(argv) == region_admin.EXIT_OK
    assert seen.added == []
    assert seen.gets == [(RegionConfig, (REGION_ID, "confirm.coef"))]
    assert seen.audits[0]["before"] == {"confirm.coef": 0.5}
    assert seen.audits[0]["after"] == {"confirm.coef": 0.9}


async def test_seed_never_overwrites_an_existing_value(monkeypatch) -> None:
    """E11 da qo'lda sozlangan qiymatni asbobning jim tiklashi eng yomon holat bo'lardi."""
    seen = wire(monkeypatch, regions=[region()], config={"confirm.coef": 0.9})
    assert await run(["config", "--code", CODE, "--seed"]) == region_admin.EXIT_OK
    assert "confirm.coef" not in seen.seeded_keys
    assert len(seen.seeded_keys) == len(region_admin.seed_defaults()) - 1
    assert seen.audits[0]["after"] == {"seeded_keys": len(seen.seeded_keys)}


async def test_seed_with_nothing_missing_writes_no_row(monkeypatch, capsys) -> None:
    """Nol kalit — o'zgarish yo'q, ya'ni jurnalda ham qator yo'q."""
    full = dict.fromkeys(region_admin.seed_defaults(), 1.0)
    seen = wire(monkeypatch, regions=[region()], config=full)
    assert await run(["config", "--code", CODE, "--seed"]) == region_admin.EXIT_OK
    assert seen.added == []
    assert seen.audits == []
    assert "0 ta" in capsys.readouterr().out


async def test_seed_and_key_together_are_blocked(monkeypatch, capsys) -> None:
    """Ilgari `--seed` yutardi va `--key` jim tashlab ketilardi.

    Odam «N ta kalit qo'shildi» degan javobni va `0` chiqish kodini
    olardi, qiymat esa o'zgarmasdi — jim bajarishdan ko'ra bloklagan
    afzal (`_set_active` ning o'z qoidasi).
    """
    seen = wire(monkeypatch, regions=[region()], config={})
    argv = ["config", "--code", CODE, "--seed", "--key", "confirm.coef", "--value", "9"]
    assert await run(argv) == region_admin.EXIT_USAGE
    assert seen.added == []
    assert seen.audits == []
    assert "[BLOK]" in capsys.readouterr().out


async def test_config_listing_does_not_call_its_own_keys_unknown(monkeypatch, capsys) -> None:
    """Ro'yxatdagi yorliq ham `known_keys()` dan.

    Ilgari asbob seed qilgan `notify.*` qatorlari darhol
    «noma'lum kalit» deb chiqardi.
    """
    config = {
        "confirm.coef": 0.5,
        notify_params.KEY_DEFAULT_RADIUS: 500,
        "haqiqatan.begona": 1,
    }
    wire(monkeypatch, regions=[region()], config=config)
    assert await run(["config", "--code", CODE]) == region_admin.EXIT_OK
    lines = {
        line.split()[0]: "[noma'lum kalit]" in line
        for line in capsys.readouterr().out.splitlines()
        if line.strip()
    }
    assert lines["confirm.coef"] is False
    assert lines[notify_params.KEY_DEFAULT_RADIUS] is False
    assert lines["haqiqatan.begona"] is True


async def test_config_listing_says_when_it_is_empty(monkeypatch, capsys) -> None:
    """Bo'sh konfiguratsiya — javob, sukut emas."""
    wire(monkeypatch, regions=[region()], config={})
    assert await run(["config", "--code", CODE]) == region_admin.EXIT_OK
    assert "DEFAULTS" in capsys.readouterr().out


async def test_config_refuses_an_unknown_code(monkeypatch) -> None:
    seen = wire(monkeypatch, regions=[])
    assert await run(["config", "--code", CODE, "--seed"]) == region_admin.EXIT_BLOCKED
    assert seen.added == []
    assert seen.audits == []


# --------------------------------------------------------------------------
# 7. Audit — BR-024 ning o'zi
# --------------------------------------------------------------------------


async def test_every_mutating_command_writes_exactly_one_row(monkeypatch) -> None:
    """Har bir o'zgarish jurnalda **bitta** qator qoldiradi.

    Reyestr o'lchanayotgan koddan olinmaydi: buyruqlar va hodisa
    nomlari qo'lda yozilgan, ya'ni yangi buyruq jurnalsiz qo'shilsa
    bu jadval yangilanmaguncha u yerda ko'rinmaydi.
    """
    expected = {
        "add": audit.AuditAction.REGION_CREATE,
        "update": audit.AuditAction.REGION_UPDATE,
        "activate": audit.AuditAction.REGION_ACTIVATE,
        "deactivate": audit.AuditAction.REGION_DEACTIVATE,
        "config": audit.AuditAction.REGION_CONFIG_SET,
    }
    argv = {
        "add": add_argv(),
        "update": ["update", "--code", CODE, "--name-uz", "Yangi"],
        "activate": ["activate", "--code", CODE],
        "deactivate": ["deactivate", "--code", CODE],
        "config": ["config", "--code", CODE, "--seed"],
    }
    for command, action in expected.items():
        rows = [] if command == "add" else [region(is_active=command == "deactivate")]
        seen = wire(monkeypatch, regions=rows, config={})
        assert await run(argv[command]) == region_admin.EXIT_OK, command
        assert len(seen.audits) == 1, command
        assert seen.audits[0]["action"] is action, command
        assert seen.audits[0]["object_id"] == REGION_ID, command
        assert seen.audits[0]["actor"].id == audit.cli_actor().id, command

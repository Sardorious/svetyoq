"""`app.reports.moderation` — bazasiz kontrakt (E8, `05` §2.5, §7.3).

Nima uchun bu fayl kerak. 166-run sandboxsiz o'tdi (`VM_DISK_SPACE_INSUFFICIENT`),
ya'ni mutatsiya o'lchovi mumkin emas edi; uning o'rniga navbatdagi modullar
uchun test qatlamining qamrovi `grep` bilan sanaldi. Natija: `moderation.py`
ni **butun repoda bitta** test fayli import qiladi —
`tests/test_admin_moderation_db.py`, va u `@pytest.mark.requires_db`. Verdikt
esa (`PROGRESS.md`, 126-rundan beri) **bazasiz** to'plamda o'lchanadi. Ya'ni
bugungi holatda bu moduldagi deyarli har qanday mutatsiya jimgina omon
qolardi: `SELECT` ustunlari almashsa ham, `0..100` chegarasi bir birlikka
surilsa ham, `before`/`after` o'rin almashsa ham to'plam yashil qolardi.

Shuning uchun bu yerda baza yo'q. Sessiya — yozib boruvchi qo'g'irchoq;
tekshiriladigan narsa uchta: (1) qaysi ustunlar so'raladi va qanday tartibda,
(2) `tg_id` hech qayerda chiqmasligi (`05` §7.3), (3) qorovul, chegaralar va
audit kesimining shakli.

`test_admin_moderation_db.py` bilan takrorlanmaydi: u haqiqiy bazada
**natijani** tekshiradi (qator chindan yangilanadimi), bu yerda esa
**so'rovning o'zi** va bazagacha bo'lgan mantiq qulflanadi.
"""

from __future__ import annotations

import uuid
from dataclasses import fields
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.dialects import postgresql

from app.core.errors import NotFoundError, SvetaError, ValidationError
from app.reports import moderation

NOW = datetime(2026, 8, 19, 9, 30, tzinfo=timezone.utc)


def _sql(statement) -> str:  # noqa: ANN001
    """PostgreSQL dialektiga kompilyatsiya — ulanishsiz.

    `tests/test_geo_sql_expressions.py` dagi `compiled()` bilan bir xil usul.
    """
    return str(statement.compile(dialect=postgresql.dialect()))


class _Result:
    def __init__(self, row) -> None:  # noqa: ANN001
        self._row = row

    def first(self):  # noqa: ANN201
        return self._row


class _FakeSession:
    """`execute` chaqiruvlarini yig'adi va bitta qator qaytaradi."""

    def __init__(self, row=None) -> None:  # noqa: ANN001
        self.row = row
        self.statements: list[object] = []

    async def execute(self, statement):  # noqa: ANN001, ANN201
        self.statements.append(statement)
        return _Result(self.row)


class _ForbiddenSession:
    """Bazaga tegilmasligi kerak bo'lgan yo'llar uchun."""

    async def execute(self, statement):  # noqa: ANN001, ANN201
        raise AssertionError("bu yo'lda bazaga murojaat bo'lmasligi kerak")


def _row(
    *,
    user_id: uuid.UUID,
    region_id: uuid.UUID,
    language: str = "ru",
    trust_score: object = Decimal("42"),
    is_blocked: object = 1,
    report_count: object = Decimal("7"),
) -> tuple:
    """`read_user` o'qiydigan qator.

    Qiymatlar **ataylab** bir-biridan farq qiladi va tiplari xom: `42` va `7`
    o'rin almashsa darhol ko'rinadi, `Decimal`/`int` esa `int(...)` va
    `bool(...)` o'girishlarini qulflaydi — ularsiz `== 7` baribir rost
    bo'lardi, ya'ni tenglik bilan tekshirish yetarli emas.
    """
    return (user_id, language, region_id, trust_score, is_blocked, NOW, report_count)


# --------------------------------------------------------------------------
# 1. Chegaralar va xato turi
# --------------------------------------------------------------------------


def test_the_trust_bounds_are_the_schema_bounds() -> None:
    """`05` §2.2 — `trust_score smallint`, 0..100.

    Bu ikki son sxemadan keladi, ixtiro emas. Ular surilsa `set_trust_score`
    bazaga sxema qabul qilmaydigan qiymat yuborardi (yoki aksincha, haqiqiy
    qiymatni rad etardi) — ikkalasi ham faqat ishlatilganda ko'rinadi.
    """
    assert moderation.TRUST_MIN == 0
    assert moderation.TRUST_MAX == 100


def test_the_trust_error_is_a_client_error_with_its_own_code() -> None:
    """Noto'g'ri ball — moderatorning xatosi (422), ilovaning emas (500).

    `ValidationError` dan meros olinmasa `status_code` `SvetaError` dan
    `500` bo'lib qolardi va moderator «ichki xato» ko'rardi: xabar
    tushunarsiz, jurnal esa yolg'on signal beradi.
    """
    assert issubclass(moderation.TrustScoreError, ValidationError)
    assert moderation.TrustScoreError.status_code == 422
    assert moderation.TrustScoreError.code == "trust_score_out_of_range"
    assert moderation.TrustScoreError.message_key == "error.trust_score_out_of_range"


def test_the_trust_error_code_is_not_the_generic_one() -> None:
    """Kod va kalit `ValidationError` nikidan farq qilsin.

    Meros olingandan keyin ikkalasini yozishni unutish — sezilmaydigan
    xato: xatolik baribir 422 qaytaradi, lekin `error.validation` degan
    umumiy matn bilan, ya'ni foydalanuvchi nima noto'g'ri ekanini bilmaydi.
    """
    assert moderation.TrustScoreError.code != ValidationError.code
    assert moderation.TrustScoreError.message_key != ValidationError.message_key


# --------------------------------------------------------------------------
# 2. Maxfiylik: `tg_id` moderatorga chiqmaydi (`05` §7.3)
# --------------------------------------------------------------------------


def test_the_moderator_row_has_no_telegram_id() -> None:
    """`UserRow` — aynan yettita maydon, `tg_id` siz va shu tartibda.

    Tartib ham qulflanadi, chunki `read_user` qatorni **raqamli indeks**
    bilan o'qiydi: `language` va `region_id` o'rin almashsa ikkala qiymat
    ham matn/`uuid` bo'lgani uchun hech qanday xato chiqmasdi.
    """
    assert tuple(f.name for f in fields(moderation.UserRow)) == (
        "id",
        "language",
        "region_id",
        "trust_score",
        "is_blocked",
        "created_at",
        "report_count",
    )


async def test_the_select_never_asks_for_the_telegram_id() -> None:
    """Qulf dataclass da emas, **so'rovda**.

    `UserRow` da `tg_id` yo'qligi kifoya emas: ustunni `SELECT` ga qo'shib
    tashlab yuborish ham mumkin, u holda identifikator jurnalga, tracing ga
    va xato matniga tushib qolardi. `05` §7.3 — `tg_id` moderatsiya
    sirtidan **umuman** chiqmaydi.
    """
    session = _FakeSession(_row(user_id=uuid.uuid4(), region_id=uuid.uuid4()))
    await moderation.read_user(session, uuid.uuid4())

    sql = _sql(session.statements[0])
    assert "tg_id" not in sql


async def test_the_select_keeps_the_column_order_the_row_reads() -> None:
    """`SELECT` tartibi ↔ `row[N]` — ikkisi qo'lda yuritiladi.

    Bu `test_geo_sql_expressions.py` §5 dagi hodisa qatori qulfining
    juftligi. Bu yerda ham o'rtada faqat raqamli indeks turadi.
    """
    session = _FakeSession(_row(user_id=uuid.uuid4(), region_id=uuid.uuid4()))
    await moderation.read_user(session, uuid.uuid4())

    sql = _sql(session.statements[0])
    ordered = [
        "users.id",
        "users.language",
        "users.region_id",
        "users.trust_score",
        "users.is_blocked",
        "users.created_at",
    ]
    for name in ordered:
        assert name in sql
    positions = [sql.index(name) for name in ordered]
    assert positions == sorted(positions)


async def test_the_report_count_is_counted_over_reports() -> None:
    """Yettinchi ustun — `reports` ustidan `count`, `users` ustidan emas.

    `select_from(Report)` `select_from(User)` ga aylansa son baribir
    qaytardi (har doim `1`) va hech qanday xato chiqmasdi — moderator esa
    har bir foydalanuvchini «bitta xabar bergan» deb ko'rardi.
    """
    session = _FakeSession(_row(user_id=uuid.uuid4(), region_id=uuid.uuid4()))
    await moderation.read_user(session, uuid.uuid4())

    sql = _sql(session.statements[0]).lower()
    assert "count(" in sql
    assert "from reports" in sql


# --------------------------------------------------------------------------
# 3. `read_user` — yo'q foydalanuvchi va tiplarni o'girish
# --------------------------------------------------------------------------


async def test_a_missing_user_reads_as_none() -> None:
    """Yo'q foydalanuvchi — `None`, xato emas.

    `read_user` past qatlam: chaqiruvchi (`_require_user`) qarorni o'zi
    qabul qiladi. Shart teskarisiga o'girilsa `None` dan `UserRow`
    yasashga urinilardi.
    """
    assert await moderation.read_user(_FakeSession(None), uuid.uuid4()) is None


async def test_the_row_is_mapped_field_by_field() -> None:
    """Har bir maydon o'z indeksidan keladi va tipi o'giriladi.

    `42` (ball) va `7` (xabarlar soni) ataylab har xil; `Decimal` va `1`
    esa `int(...)`/`bool(...)` ni qulflaydi — ularsiz tenglik baribir rost
    bo'lar, lekin bazadan kelgan xom tip API javobiga chiqib ketardi.
    """
    user_id = uuid.uuid4()
    region_id = uuid.uuid4()
    session = _FakeSession(_row(user_id=user_id, region_id=region_id))

    row = await moderation.read_user(session, user_id)

    assert row is not None
    assert row.id == user_id
    assert row.language == "ru"
    assert row.region_id == region_id
    assert row.created_at == NOW
    assert row.trust_score == 42
    assert type(row.trust_score) is int
    assert row.report_count == 7
    assert type(row.report_count) is int
    assert row.is_blocked is True


async def test_a_blocked_flag_of_zero_reads_as_false() -> None:
    """`bool(...)` ning ikkinchi tomoni — `0` `False` bo'ladi.

    Bir tomonlama tekshiruv `bool(row[4])` ni `True` ga aylantirgan
    mutatsiyani sezmasdi.
    """
    session = _FakeSession(_row(user_id=uuid.uuid4(), region_id=uuid.uuid4(), is_blocked=0))
    row = await moderation.read_user(session, uuid.uuid4())

    assert row is not None
    assert row.is_blocked is False


# --------------------------------------------------------------------------
# 4. Yo'q foydalanuvchi ustida amal — yozuvgacha to'xtaydi
# --------------------------------------------------------------------------


async def test_blocking_a_missing_user_writes_nothing() -> None:
    """`NotFoundError` `UPDATE` dan **oldin** otiladi.

    Tekshiruv yozuvdan keyinga ko'chsa `UPDATE ... WHERE id = <yo'q>`
    nol qator yangilardi — xatosiz, izsiz, lekin audit yozuvi bilan.
    Shuning uchun bu yerda sanaladigan narsa — bajarilgan so'rovlar soni.
    """
    session = _FakeSession(None)
    with pytest.raises(NotFoundError):
        await moderation.set_blocked(session, uuid.uuid4(), blocked=True)
    assert len(session.statements) == 1


async def test_the_not_found_error_names_the_user() -> None:
    """Kontekstda `user_id` — matn ko'rinishida.

    `str(...)` tushib qolsa kontekstda `uuid.UUID` obyekti qolardi va
    javobni JSON ga o'girishda xato chiqardi — ya'ni 404 o'rniga 500.
    """
    user_id = uuid.uuid4()
    session = _FakeSession(None)
    with pytest.raises(NotFoundError) as excinfo:
        await moderation.set_blocked(session, user_id, blocked=True)

    assert excinfo.value.context == {"user_id": str(user_id)}
    assert isinstance(excinfo.value, SvetaError)


async def test_setting_a_score_on_a_missing_user_is_not_found() -> None:
    """To'g'ri ball + yo'q foydalanuvchi = `NotFoundError`, `UPDATE` yo'q."""
    session = _FakeSession(None)
    with pytest.raises(NotFoundError):
        await moderation.set_trust_score(session, uuid.uuid4(), score=50)
    assert len(session.statements) == 1


# --------------------------------------------------------------------------
# 5. `set_blocked` — idempotent, lekin jim emas
# --------------------------------------------------------------------------


async def test_blocking_writes_and_reports_both_sides() -> None:
    """`before` — eski qator, `after` — argument.

    Ikkisi o'rin almashsa audit teskari yozilardi va hech narsa
    yiqilmasdi: ikkala qiymat ham `bool`. Shuning uchun bu holatda ular
    **har xil**.
    """
    user_id = uuid.uuid4()
    session = _FakeSession(_row(user_id=user_id, region_id=uuid.uuid4(), is_blocked=0))

    change = await moderation.set_blocked(session, user_id, blocked=True)

    assert change.user_id == user_id
    assert change.before == {"is_blocked": False}
    assert change.after == {"is_blocked": True}

    sql = _sql(session.statements[1])
    assert sql.startswith("UPDATE users")
    assert "is_blocked" in sql
    assert "trust_score" not in sql


async def test_blocking_an_already_blocked_user_still_writes() -> None:
    """Idempotentlik — dokstringdagi qaror, ya'ni o'lchanadigan da'vo.

    «Holat o'zgarmadi, `UPDATE` qilmaymiz» degan optimallashtirish
    kiritilsa audit izi yo'qolardi: moderator amalni bajardi, jurnalda esa
    hech narsa yo'q.
    """
    user_id = uuid.uuid4()
    session = _FakeSession(_row(user_id=user_id, region_id=uuid.uuid4(), is_blocked=1))

    change = await moderation.set_blocked(session, user_id, blocked=True)

    assert len(session.statements) == 2
    assert _sql(session.statements[1]).startswith("UPDATE users")
    assert change.before == {"is_blocked": True}
    assert change.after == {"is_blocked": True}


async def test_unblocking_is_the_same_path() -> None:
    """`blocked=False` — alohida shox emas, o'sha yo'l.

    Argument o'rniga doimiy `True` yozib qo'yilsa blokdan chiqarish
    ishlamas, lekin bloklash testi baribir yashil qolardi.
    """
    user_id = uuid.uuid4()
    session = _FakeSession(_row(user_id=user_id, region_id=uuid.uuid4(), is_blocked=1))

    change = await moderation.set_blocked(session, user_id, blocked=False)

    assert change.before == {"is_blocked": True}
    assert change.after == {"is_blocked": False}


# --------------------------------------------------------------------------
# 6. `set_trust_score` — qorovul bazadan oldin turadi
# --------------------------------------------------------------------------


@pytest.mark.parametrize("score", [-1, 101, -100, 1000])
async def test_a_score_outside_the_range_never_reaches_the_database(score: int) -> None:
    """Qorovul `_require_user` dan **oldin**.

    Sessiya bu yo'lda umuman ishlatilmasligi kerak: tekshiruv `UPDATE` dan
    oldin, lekin `SELECT` dan ham oldin bo'lsin — aks holda yaroqsiz
    qiymat uchun ham baza o'qilardi va xato turi foydalanuvchiga bog'liq
    bo'lib qolardi (`NotFoundError` yoki `TrustScoreError`).
    """
    with pytest.raises(moderation.TrustScoreError):
        await moderation.set_trust_score(_ForbiddenSession(), uuid.uuid4(), score=score)


@pytest.mark.parametrize("score", [0, 100])
async def test_the_range_is_inclusive_at_both_ends(score: int) -> None:
    """`0` va `100` — yaroqli.

    `<=` ning bittasi `<` ga aylansa chegaraviy ball rad etilardi: sxema
    qabul qiladigan qiymatni ilova rad etardi va sabab moderatorga
    ko'rinmasdi.
    """
    user_id = uuid.uuid4()
    session = _FakeSession(_row(user_id=user_id, region_id=uuid.uuid4()))

    change = await moderation.set_trust_score(session, user_id, score=score)

    assert change.after == {"trust_score": score}


async def test_the_range_error_carries_the_bounds() -> None:
    """Kontekstda ball va ikkala chegara.

    Bu — moderatorga ko'rinadigan yagona son: i18n matni
    (`error.trust_score_out_of_range`) chegaralarni o'zi aytmaydi.
    """
    with pytest.raises(moderation.TrustScoreError) as excinfo:
        await moderation.set_trust_score(_ForbiddenSession(), uuid.uuid4(), score=101)

    assert excinfo.value.context == {
        "score": 101,
        "min": moderation.TRUST_MIN,
        "max": moderation.TRUST_MAX,
    }


async def test_setting_a_score_writes_the_score_column_only() -> None:
    """`before` — eski ball, `after` — yangi; `UPDATE` faqat `trust_score`.

    `42` va `77` har xil, ya'ni `before`/`after` almashuvi seziladi;
    `is_blocked` ning yo'qligi esa nusxa ko'chirishdagi eng ehtimolli
    xatoni (`set_blocked` dan qolgan ustun) qulflaydi.
    """
    user_id = uuid.uuid4()
    session = _FakeSession(_row(user_id=user_id, region_id=uuid.uuid4()))

    change = await moderation.set_trust_score(session, user_id, score=77)

    assert change.user_id == user_id
    assert change.before == {"trust_score": 42}
    assert change.after == {"trust_score": 77}

    sql = _sql(session.statements[1])
    assert sql.startswith("UPDATE users")
    assert "trust_score" in sql
    assert "is_blocked" not in sql


# --------------------------------------------------------------------------
# 7. Audit kesimining shakli
# --------------------------------------------------------------------------


def test_the_audit_slice_has_exactly_three_fields() -> None:
    """`UserChange` — `user_id`, `before`, `after`.

    `app.admin` shu uchtasini auditga yozadi (`05` §2.5). Kesimga yangi
    maydon qo'shilsa u auditda jimgina tashlanardi; `tg_id` qo'shilsa esa
    §7.3 buzilardi — shuning uchun ro'yxat aniq.
    """
    assert tuple(f.name for f in fields(moderation.UserChange)) == (
        "user_id",
        "before",
        "after",
    )


def test_both_slices_are_frozen() -> None:
    """Ikkala dataclass ham `frozen=True`.

    Auditga ketayotgan kesim yo'lda o'zgartirilmasin: `before` ni
    chaqiruvchi tomonda tuzatish audit izini yolg'onlashtirardi.
    """
    assert moderation.UserRow.__dataclass_params__.frozen is True
    assert moderation.UserChange.__dataclass_params__.frozen is True


# --------------------------------------------------------------------------
# 8. So'rovning **ichi** — 167-run mutatsiya o'lchovi bo'yicha
# --------------------------------------------------------------------------
#
# 166 bu faylni sandboxsiz yozgan, ya'ni verdikt olinmagan edi. 167-run uni
# o'lchadi: 29 mutatsiya → 23 KILLED, 6 SURVIVOR (21 %). Omon qolganlarning
# hammasi bitta sinfda: 1–7-bo'limlar `SELECT`/`UPDATE` ning **matnini**
# tekshiradi, mutatsiya esa matnni o'zgartirmaydi — u yo bog'langan
# **parametrni**, yo shartning **ichini** o'zgartiradi.


def _compiled(statement):  # noqa: ANN001, ANN202
    return statement.compile(dialect=postgresql.dialect())


def _normalised(statement) -> str:  # noqa: ANN001
    """Ko'p qatorli SQL ni bitta qatorga keltiradi — shart matni izlash uchun."""
    return " ".join(str(_compiled(statement)).split())


async def test_the_report_count_is_correlated_to_this_user() -> None:
    """`count` **shu** foydalanuvchining xabarlari ustidan.

    167-run M13: `.where(Report.user_id == User.id)` ni olib tashlash butun
    to'plamdan (3837 test) o'tardi. Sabab §2 dagi juftlik testida:
    `assert "from reports" in sql` — bog'lanish o'chirilganda ham
    kichik so'rov `FROM reports` bo'lib qolaveradi, ya'ni o'sha da'vo
    **ajratmaydi** (`svetyoq-fixture-must-separate` sinfi, endi matn
    darajasida). Natijasi jimgina: moderator har bir foydalanuvchi qarshisida
    **butun jadvaldagi** xabarlar sonini ko'rardi va bloklash qarorini
    o'zgacha qabul qilardi.
    """
    session = _FakeSession(_row(user_id=uuid.uuid4(), region_id=uuid.uuid4()))
    await moderation.read_user(session, uuid.uuid4())

    assert "WHERE reports.user_id = users.id" in _normalised(session.statements[0])


async def test_the_block_update_carries_the_flag_it_was_given() -> None:
    """Yozilayotgan qiymat — **bog'langan parametr**, matn emas.

    167-run M20: `values(is_blocked=blocked)` → `values(is_blocked=not blocked)`
    SQL matnini umuman o'zgartirmaydi (`SET is_blocked=%(is_blocked)s`),
    ya'ni matn bo'yicha yozilgan hech qanday da'vo uni ushlamaydi. Ta'siri
    esa eng og'iri: moderator bloklaganda foydalanuvchi **ochilardi**, va
    aksincha.
    """
    user_id = uuid.uuid4()
    for blocked in (True, False):
        session = _FakeSession(_row(user_id=user_id, region_id=uuid.uuid4()))
        await moderation.set_blocked(session, user_id, blocked=blocked)
        assert _compiled(session.statements[1]).params["is_blocked"] is blocked


async def test_the_trust_update_carries_the_score_it_was_given() -> None:
    """167-run M26: `values(trust_score=score)` → `values(trust_score=TRUST_MAX)`.

    Matn bir xil qoladi va `change.after` ham to'g'ri ko'rinadi (u `score`
    dan yig'iladi) — ya'ni audit «55 qo'yildi» deb yozardi, bazada esa `100`
    turardi. `55` ataylab: `TRUST_MAX` ham, `TRUST_MIN` ham, fikstyuradagi
    `42` ham emas.
    """
    user_id = uuid.uuid4()
    session = _FakeSession(_row(user_id=user_id, region_id=uuid.uuid4()))

    await moderation.set_trust_score(session, user_id, score=55)

    assert _compiled(session.statements[1]).params["trust_score"] == 55


@pytest.mark.parametrize(
    ("call", "index"),
    [
        pytest.param(lambda s, u: moderation.set_blocked(s, u, blocked=True), 1, id="block"),
        pytest.param(lambda s, u: moderation.set_trust_score(s, u, score=55), 1, id="trust"),
    ],
)
async def test_every_update_is_scoped_to_one_user(call, index) -> None:  # noqa: ANN001
    """`WHERE` siz `UPDATE` — butun jadval.

    167-run M21: `update(User).where(User.id == user_id)` dan `where` ni olib
    tashlash o'lchanmagan edi. Bu moderatorning bitta bosishi bilan
    **hamma** foydalanuvchini bloklardi (yoki hammaga bir xil ishonch bali
    qo'yardi) va `change` baribir bitta odam haqida hisobot berardi, ya'ni
    audit izida ham hech narsa ko'rinmasdi.
    """
    user_id = uuid.uuid4()
    session = _FakeSession(_row(user_id=user_id, region_id=uuid.uuid4()))

    await call(session, user_id)

    assert "WHERE users.id =" in _normalised(session.statements[index])

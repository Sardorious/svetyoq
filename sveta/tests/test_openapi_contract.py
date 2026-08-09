"""Kontrakt qatlami (`05` §9.2, E15).

`05` §9.2 test qatlamlari jadvalining oxirgi qatori: «Kontrakt — OpenAPI
sxemasi javoblar bilan mos». E15 gacha bu qatlam yo'q edi: sxema
generatsiya qilinardi, lekin uni hech kim tekshirmasdi.

Bu yerdagi testlar **butun sxema bo'yicha** aylanadi, ya'ni ertaga
qo'shiladigan endpoint ham avtomatik tekshiriladi. Aynan shu sabab
har biriga qo'lda ro'yxat yozilmagan.
"""

from __future__ import annotations

import pytest

from app.api.openapi import TAGS_METADATA
from app.core.config import settings

ERROR_REF = "#/components/schemas/ErrorResponse"

#: `05` §7.3: bu nomlar hech qanday ommaviy sxemada bo'lmaydi.
FORBIDDEN_PROPERTIES = frozenset({"geom_exact", "tg_id", "user_id", "phone", "username"})

#: Admin sxemalari `user_id` ni ko'rsatishi mumkin — bloklash uchun
#: identifikator kerak (E8 qarori). Ular alohida ro'yxatda, ya'ni istisno
#: ko'rinib turadi va tasodifan kengaymaydi.
ADMIN_SCHEMAS = frozenset({"UserOut", "AuditOut", "OutageOut", "ChangeOut"})


@pytest.fixture(scope="module")
def schema(app):
    return app.openapi()


def _operations(schema):
    for path, item in schema["paths"].items():
        for method, operation in item.items():
            if isinstance(operation, dict):
                yield path, method, operation


def test_every_operation_is_documented(schema) -> None:
    """Har operatsiyada `summary` va teg bor.

    Tegsiz endpoint `/docs` da «default» guruhida yolg'iz turadi va uning
    kimga mo'ljallangani — ommaviymi yoki adminmi — ko'rinmaydi.
    """
    undocumented = [
        f"{method.upper()} {path}"
        for path, method, op in _operations(schema)
        if not op.get("summary") or not op.get("tags")
    ]
    assert undocumented == []


def test_operation_ids_are_unique_and_pathless(schema) -> None:
    """`operationId` — generatordagi metod nomi.

    Takrorlanish generatorni jimgina buzadi (bittasi ustidan yoziladi),
    yo'lni o'z ichiga olgan nom esa yo'l o'zgarganda mijoz kodini
    o'zgartirishga majburlaydi.
    """
    ids = [op["operationId"] for _, _, op in _operations(schema)]
    assert len(ids) == len(set(ids)), sorted({i for i in ids if ids.count(i) > 1})
    assert not any("api_v1" in i for i in ids)


def test_every_tag_is_described(schema) -> None:
    used = {tag for _, _, op in _operations(schema) for tag in op["tags"]}
    described = {tag["name"] for tag in TAGS_METADATA}
    assert used <= described, sorted(used - described)


def test_all_error_responses_share_one_body(schema) -> None:
    """`4xx`/`5xx` — hamma joyda `ErrorResponse`.

    E15 gacha `422` ikki xil tana bilan kelardi: ilovaning
    `ValidationError` i uchun `{code, message_key, ...}`, FastAPI ning o'zi
    uchun `{"detail": [...]}`. Bitta status kodida ikkita shartnoma —
    mijoz uchun tuzoq.
    """
    wrong = []
    for path, method, op in _operations(schema):
        for status, body in op["responses"].items():
            if not status.startswith(("4", "5")):
                continue
            content = body.get("content", {}).get("application/json", {})
            if content.get("schema", {}).get("$ref") != ERROR_REF:
                wrong.append(f"{method.upper()} {path} → {status}")
    assert wrong == []


def test_parameterless_operations_do_not_promise_validation_errors(schema) -> None:
    """Parametri yo'q endpoint `422` va'da qilmaydi.

    Bo'lmaydigan xatoni hujjatga yozish mijozni uni ishlashga majburlaydi.
    """
    health = schema["paths"][f"{settings.api_prefix}/health"]["get"]
    assert "422" not in health["responses"]
    assert not health.get("parameters")


def test_successful_responses_have_a_schema(schema) -> None:
    """`200` javobining ichi hujjatda ko'rinadi.

    `/map` va `/geo/districts` javobni qo'lda quradi (`ETag` va `304`
    uchun), shuning uchun FastAPI ularning sxemasini o'zi chiqara olmaydi
    — model qo'lda e'lon qilinadi. Bu test o'sha e'lonni qulflaydi.
    """
    empty = []
    for path, method, op in _operations(schema):
        ok = op["responses"].get("200")
        if ok is None:
            continue
        media = ok.get("content", {})
        json_schema = media.get("application/json", {}).get("schema")
        if json_schema is None and "text/plain" in media:
            continue  # `/stats.csv`
        if not json_schema:
            empty.append(f"{method.upper()} {path}")
    assert empty == []


def test_no_public_schema_exposes_identifiers(schema) -> None:
    """`05` §7.3 — butun sxema bo'yicha maxfiylik regressiyasi.

    `tests/test_admin_api.py` `geom_exact` va `tg_id` ni tekshiradi; bu
    yerda ro'yxat kengroq va `user_id` ham kiradi — ommaviy sxemalarda u
    ham bo'lmasligi kerak.
    """
    leaked = [
        (name, prop)
        for name, model in schema["components"]["schemas"].items()
        if name not in ADMIN_SCHEMAS
        for prop in (model.get("properties") or {})
        if prop in FORBIDDEN_PROPERTIES
    ]
    assert leaked == []


def test_admin_operations_document_the_forbidden_answer(schema) -> None:
    """Panel sozlanmagan bo'lsa har so'rov `403` — bu shartnomaning bir qismi."""
    missing = [
        f"{method.upper()} {path}"
        for path, method, op in _operations(schema)
        if "admin" in op["tags"] and "403" not in op["responses"]
    ]
    assert missing == []


def test_public_operations_do_not_require_a_token(schema) -> None:
    """Ommaviy endpointda `X-Admin-Token` parametri paydo bo'lib qolmasin."""
    guarded = [
        f"{method.upper()} {path}"
        for path, method, op in _operations(schema)
        if "admin" not in op["tags"]
        for param in (op.get("parameters") or [])
        if param["name"].lower() == "x-admin-token"
    ]
    assert guarded == []


def test_disclaimer_comes_from_the_catalog(schema) -> None:
    """`03` §R1.2 — «rasmiy manba emas» hujjatda ham bor va ikkala tilda."""
    description = schema["info"]["description"]
    assert "rasmiy manba emas" in description
    assert "не официальный источник" in description
    assert "geom_exact" in description  # `05` §7.3 ro'yxati


#: Statistika vitrinalari — «hududdan qancha» degan raqamni ko'rsatadigan
#: ommaviy javoblar. `03` §R1.2 va `01` PG-S4 ular uchun Coverage Index ni
#: **majburiy** qiladi. Ro'yxat sxema nomlari bo'yicha, chunki javoblar
#: qo'lda quriladi (`ETag`) va yagona umumiy tayanch — model.
SHOWCASE_SCHEMAS = frozenset({"StatsOut", "HeatCollection"})


def test_every_statistics_showcase_carries_the_coverage_index(schema) -> None:
    """`03` §R1.2: «har bir vitrina Coverage Index bilan ko'rsatiladi».

    Nima uchun test kerak. Qamrovsiz o'qilgan kraudsorsing raqami yolg'on
    gapiradi: xabar kam bo'lgan hudud «tinch» ko'rinadi, aslida u
    qamralmagan. E16 (issiqlik xaritasi) aynan shu holatga tushgan edi —
    zichlik ko'rsatilardi, qamrov esa yo'q edi.

    Test yangi vitrinaga ham tegishli: `SHOWCASE_SCHEMAS` ga qo'shilgan
    har qanday model `coverage` maydonisiz o'tmaydi.
    """
    schemas = schema["components"]["schemas"]
    missing = [
        name
        for name in sorted(SHOWCASE_SCHEMAS)
        if "coverage" not in schemas.get(name, {}).get("properties", {})
    ]
    assert missing == []


def test_every_statistics_showcase_carries_the_maturity_note(schema) -> None:
    """`01` FR-S-901 (P0) va §23: «Дисклеймер молодого региона активен».

    Qamrov indeksi bu talabni bajarmaydi — u boshqa savolga javob beradi.
    Kecha ishga tushgan mintaqa to'liq qamralgan bo'lishi mumkin, lekin
    uning ikki haftalik kesimidan «tumanlarning ishonchliligi» chiqmaydi.
    `01` RS-10 aynan shu xatoni sanaydi: yosh statistika yetuk statistika
    bilan yonma-yon nashr etilsa, o'quvchi ikkalasini bir xil chuqurlikda
    deb o'qiydi.

    Test yangi vitrinaga ham tegishli: `SHOWCASE_SCHEMAS` ga qo'shilgan
    har qanday model `maturity` maydonisiz o'tmaydi.
    """
    schemas = schema["components"]["schemas"]
    missing = [
        name
        for name in sorted(SHOWCASE_SCHEMAS)
        if "maturity" not in schemas.get(name, {}).get("properties", {})
    ]
    assert missing == []


def test_historical_showcase_states_the_boundary_version(schema) -> None:
    """`01` FR-S-803 AC: «в ответе указана версия справочника».

    Nima uchun `SHOWCASE_SCHEMAS` emas, faqat `StatsOut`. Talab
    **davrga** bog'liq javoblarga tegishli: statistika o'tmishdagi
    kesimni ko'rsatadi va o'sha kesim qaysi chegaralar bo'yicha
    hisoblanganini bilmasdan uni boshqa davr bilan taqqoslab bo'lmaydi.
    Issiqlik xaritasi esa H3 katakchalari ustida quriladi va ma'muriy
    chegaralarga umuman bog'liq emas — u yerda versiya ko'rsatish
    javobga ma'nosiz maydon qo'shardi.

    `districts[]` dagi `valid_from`/`valid_to` alohida tekshiriladi:
    davr ichida chegara o'zgargan bo'lsa bitta `code` ikki marta chiqadi
    va faqat shu ikki maydon ularni ajratadi.
    """
    schemas = schema["components"]["schemas"]
    assert "boundaries" in schemas["StatsOut"]["properties"]
    district = schemas["DistrictOut"]["properties"]
    assert {"valid_from", "valid_to"} <= set(district)


def test_statistics_showcase_states_the_mahalla_coverage(schema) -> None:
    """`01` §16: «Ответы статистики … и индекса покрытия махалли».

    To'rtinchi qator ikkita talab beradi va ular bitta jumlada yozilgani
    uchun bittasi (chegaralar versiyasi, 25-sessiya) bajarilib, ikkinchisi
    umuman e'tibordan chetda qolgan edi. Test aynan shuni takrorlanmas
    qiladi.

    `SHOWCASE_SCHEMAS` emas, faqat `StatsOut` — `boundaries` bilan bir xil
    sabab: issiqlik xaritasi H3 katakchalari ustida quriladi va ma'muriy
    darajalarni umuman ko'rsatmaydi.

    `available` alohida tekshiriladi va bu testning eng muhim qatori:
    `mahallas` jadvali E17 gacha bo'sh, ya'ni maydonsiz javob har doim
    `total=0, index=0` bo'lardi va vitrinada «mahallalarda qamrov yo'q»
    deb o'qilardi — FR-S-802 degradatsiyasining jim o'limi.
    """
    schemas = schema["components"]["schemas"]
    assert "mahallas" in schemas["StatsOut"]["properties"]
    block = schemas["MahallaCoverageOut"]["properties"]
    assert {"available", "total", "measured", "coverage", "bands"} <= set(block)


def test_mahalla_showcase_carries_no_incident_counts(schema) -> None:
    """`05` §7.3: ommaviy javobda kichik hududning tafsiloti yo'q.

    Mahalla — eng kichik ma'muriy daraja va u yerdagi hodisalar soni
    `06` §5.4 ning qamrov to'sig'idan o'tmaydi. Shuning uchun
    `MahallaOut` faqat **qamrovni** beradi: «bu raqamga qanchalik
    ishonish mumkin», «bu yerda nima bo'ldi» emas. Chelak qo'shilsa,
    `01` OQ-04 (mahalla darajasidagi reidentifikatsiya xavfi) ochiq
    turgani holda javob unga eng yaqin ma'lumotni berardi.
    """
    fields = set(schema["components"]["schemas"]["MahallaOut"]["properties"])
    assert "coverage" in fields
    assert not fields & {"stats", "outages_total", "reports_total", "by_status"}


def test_showcase_schemas_actually_exist(schema) -> None:
    """Vitrina qayta nomlansa ro'yxat jimgina bo'shab qolmasin."""
    known = set(schema["components"]["schemas"])
    assert SHOWCASE_SCHEMAS <= known


def test_license_is_declared(schema) -> None:
    """OSM poligonlari atribut talab qiladi — hujjat buni yashirmaydi."""
    assert "ODbL" in schema["info"]["license"]["name"]


async def test_openapi_is_served_in_prod(client, monkeypatch) -> None:
    """Hujjat prodda ham ochiq, interaktiv sahifa esa yopiq.

    `04` E15 mezoni — «tashqi so'rov hujjat bo'yicha ishlaydi»; hujjatni
    prodda yopish bu mezonni bajarilmas qilardi.
    """
    monkeypatch.setattr(settings, "app_env", "prod")
    assert settings.is_prod
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Sveta.Net API"

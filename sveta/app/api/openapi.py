"""OpenAPI hujjati (E15, `05` §7.2, §9.2).

Epic ning nomi «Ommaviy API + OpenAPI», mezoni esa — «tashqi so'rov hujjat
bo'yicha ishlaydi» (`04` E15). Bu shuni anglatadiki, hujjat kodning yon
mahsuloti emas, **shartnoma**: mijoz faqat `/openapi.json` ni o'qib
integratsiya qila olishi kerak, manba kodini o'qimasdan.

Shu sababli bu yerda uchta narsa yig'iladi:

1. **Tavsif va teglar** — qaysi endpoint kimga mo'ljallangan va nima
   *chiqmaydi* (`05` §7.3). Maxfiylik shartnomasi hujjatning bir qismi:
   uni bilmagan mijoz «xabar muallifi qani?» deb so'rab yurardi.
2. **Xato sxemasi** — barcha endpointlar bitta tanani qaytaradi
   (`SvetaError.to_dict`), lekin E15 gacha u hujjatda umuman yo'q edi va
   mijoz uchun `422` ning ichi noma'lum qora quti bo'lardi.
3. **Barqaror `operationId`** — generatorlar (openapi-generator, orval va
   h.k.) metod nomini shundan yasaydi. FastAPI ning standart qiymati
   yo'lni o'z ichiga oladi (`get_map_api_v1_map_get`), ya'ni yo'l
   o'zgarganda **mijoz kodidagi metod nomi** o'zgarardi.

**Dislaymer i18n katalogidan olinadi.** `03` §R1.2 «rasmiy manba emas»
ogohlantirishini majburiy qiladi. Uni bu yerda qo'lda yozish katalogdagi
matndan ajralib ketish xavfini tug'dirardi (`04` §6), shuning uchun
sarlavhaga aynan o'sha kalit qo'yiladi.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field

from app.core.i18n import t

#: `05` §7.2 dagi endpointlar guruhlari. Tavsif — teg darajasida, chunki
#: «nima uchun bu guruh bor» savoli har endpointda takrorlanmasligi kerak.
TAGS_METADATA: list[dict[str, str]] = [
    {
        "name": "public",
        "description": (
            "Ochiq ma'lumot: hodisa tafsiloti, statistika, chegaralar. "
            "Autentifikatsiya talab qilinmaydi. `05` §7.3 cheklovlari to'liq "
            "kuchda — foydalanuvchi identifikatori va aniq koordinata "
            "hech qanday javobda chiqmaydi."
        ),
    },
    {
        "name": "map",
        "description": (
            "Xarita yetkazish (`05` §7.1). Javob oldindan yig'ilgan "
            "snapshotdan o'qiladi va `ETag` bilan keshlanadi: `If-None-Match` "
            "yuborgan mijoz o'zgarish bo'lmasa `304` oladi."
        ),
    },
    {
        "name": "regions",
        "description": (
            "Ilova ishlaydigan mintaqalar (`04` E19). Ro'yxat **bazadan** "
            "keladi, koddan emas: yangi shahar deploysiz qo'shiladi. "
            "Faqat `is_active` mintaqalar chiqadi."
        ),
    },
    {
        "name": "system",
        "description": "Salomatlik va versiya. Monitoring uchun.",
    },
    {
        "name": "admin",
        "description": (
            "Moderatsiya (`05` §2.5, §4.4). `X-Admin-Token` sarlavhasi majburiy; "
            "panel sozlanmagan bo'lsa **hamma** so'rov `403` oladi. "
            "Ommaviy emas va hujjatdagi mavjudligi ruxsat bermaydi."
        ),
    },
]


def api_description() -> str:
    """`/docs` sarlavhasidagi matn.

    Ikkala tilda ham beriladi: hujjatni o'qiydigan odam UZ yoki RU bo'lishi
    mumkin, `Accept-Language` esa statik hujjatga qo'llanmaydi.
    """
    return "\n\n".join(
        [
            f"**{t('app.disclaimer', 'uz')}**",
            f"**{t('app.disclaimer', 'ru')}**",
            (
                "Ma'lumot Telegram bot orqali kelgan foydalanuvchi xabarlaridan "
                "yig'iladi va avtomatik tasdiqlanadi (`06`). Har bir hodisada "
                "`confidence` bor — uni e'tiborsiz qoldirish tasdiqlanmagan "
                "xabarni fakt sifatida ko'rsatish degani."
            ),
            (
                "### Nima chiqmaydi (`05` §7.3)\n"
                "* aniq koordinata (`geom_exact`) — hech qanday endpointda;\n"
                "* `user_id`, `tg_id` — hech qachon;\n"
                "* 3 tadan kam xabarli hodisa — deanonimizatsiya riski;\n"
                "* 3 tadan kam **turli** xabar beruvchisi bo'lgan H3 katakcha — "
                "`/heatmap` da ko'rsatilmaydi (r9 ≈ 200 m, ya'ni yolg'iz "
                "xabar beruvchining katakchasi amalda uning uyi);\n"
                "* aniq vaqt — 5 daqiqagacha pastga yaxlitlanadi."
            ),
            (
                "### Kesh\n"
                "`/map`, `/heatmap` va `/geo/districts` `ETag` qaytaradi. "
                "`If-None-Match` bilan qayta so'rang: o'zgarish bo'lmasa `304` "
                "keladi va trafik sarflanmaydi. `/heatmap` javobi tarjima "
                "qilingan ogohlantirishlarni o'z ichiga oladi, shuning uchun u "
                "`Vary: Accept-Language` bilan keladi."
            ),
            (
                "### Litsenziya\n"
                "Tuman poligonlari OpenStreetMap dan olingan; har javobda "
                "`licenses` va `attribution` maydonlari bor va atribut "
                "ko'rsatish majburiy."
            ),
        ]
    )


class ErrorResponse(BaseModel):
    """Barcha xatoliklarning yagona tanasi (`app/core/errors.py`).

    `message` — `Accept-Language` bo'yicha tarjima qilingan matn;
    `message_key` esa **barqaror** identifikator. Mijoz shartni matn
    bo'yicha emas, kalit yoki `code` bo'yicha yozishi kerak: tarjima
    o'zgarishi mumkin, kalit — yo'q.
    """

    code: str = Field(examples=["not_found"])
    message_key: str = Field(examples=["error.not_found"])
    message: str = Field(examples=["Topilmadi"])
    context: dict[str, Any] = Field(default_factory=dict)


#: Endpoint `NotFoundError` ko'tara oladigan bo'lsa shu qiymat bilan
#: e'lon qiladi. Avtomatik qo'shilmaydi: `/health` yoki `/map/config` hech
#: qachon `404` bermaydi va uni hujjatda ko'rsatish mijozni bo'lmaydigan
#: holatni ishlashga majburlardi.
NOT_FOUND: dict[str, Any] = {"description": "Topilmadi"}

#: Faqat `admin` tegidagi endpointlarga qo'shiladi: panel sozlanmagan
#: bo'lsa **har** so'rov `403` oladi (`05` §6.3 mantig'i).
FORBIDDEN_DESCRIPTION = "Token yo'q yoki ruxsat yetarli emas"

VALIDATION_DESCRIPTION = "So'rov parametri yaroqsiz"


def unique_operation_id(route: APIRoute) -> str:
    """`operationId` = funksiya nomi.

    Yo'l qatnashmaydi, ya'ni `/api/v1/map` `/api/v2/map` ga ko'chsa ham
    generatordan chiqqan mijoz metodi `get_map` bo'lib qoladi. Nomlarning
    yagonaligini test qulflaydi (`tests/test_openapi_contract.py`) — aks
    holda ikkita bir xil `operationId` generatorni jimgina buzardi.
    """
    return route.name


def _error_ref() -> dict[str, Any]:
    return {
        "application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}
    }


def customize(app: FastAPI) -> dict[str, Any]:
    """Yig'ilgan sxemaga umumiy qismlarni qo'shadi va keshlaydi.

    FastAPI `app.openapi()` natijasini `app.openapi_schema` da keshlaydi,
    shuning uchun bu funksiya bir marta bajariladi.
    """
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=TAGS_METADATA,
    )
    schema["info"]["license"] = {
        "name": "ODbL 1.0 (chegaralar) / CC BY 4.0 (hodisalar)",
        "url": "https://opendatacommons.org/licenses/odbl/1-0/",
    }
    components = schema.setdefault("components", {}).setdefault("schemas", {})
    components["ErrorResponse"] = ErrorResponse.model_json_schema()

    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.setdefault("responses", {})
            has_input = bool(operation.get("parameters") or operation.get("requestBody"))
            if has_input:
                # FastAPI o'zi `422` ni `HTTPValidationError` (`{"detail": [...]}`)
                # bilan yozadi, ilova esa `ValidationError` uchun `ErrorResponse`
                # qaytaradi. Ikki xil tana bitta status kodida — mijoz uchun
                # tuzoq, shuning uchun `main.py` da `RequestValidationError`
                # ham `ErrorResponse` ga o'giriladi va hujjat shuni aytadi.
                responses["422"] = {
                    "description": VALIDATION_DESCRIPTION,
                    "content": _error_ref(),
                }
            elif "422" in responses:
                # Parametri yo'q endpointda validatsiya xatosi ham bo'lmaydi.
                del responses["422"]
            if "admin" in (operation.get("tags") or []):
                responses.setdefault(
                    "403", {"description": FORBIDDEN_DESCRIPTION, "content": _error_ref()}
                )
            # Marshrutda e'lon qilingan xatolarning tanasi ham bir xil bo'lsin.
            for status, body in responses.items():
                if status.startswith(("4", "5")) and not body.get("content"):
                    body["content"] = _error_ref()

    # `HTTPValidationError`/`ValidationError` endi hech qayerda ishlatilmaydi.
    for orphan in ("HTTPValidationError", "ValidationError"):
        components.pop(orphan, None)

    app.openapi_schema = schema
    return schema

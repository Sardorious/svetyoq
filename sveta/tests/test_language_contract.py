"""Standart til mintaqadan keladi — kontrakt qatlami (`01` §16, §17).

`01` §17 `regions.default_language` ni Toshkent sxemasidan farq sifatida
**alohida** sanaydi: «язык по умолчанию как атрибут региона». `01` §16
esa uni `Accept-Language` bilan bog'laydi: «порядок по умолчанию зависит
от региона».

28-sessiyagacha ustun bor edi, uni `tools/region_admin.py` yozardi,
`/regions` javobida ko'rsatardi — va **hech kim o'qimasdi**. Har javob
global `DEFAULT_LANGUAGE = "uz"` ga tushardi. Defekt bitta mintaqada
ko'rinmaydi (Samarqandning standart tili baribir `uz`), ya'ni u aynan
E19 dan keyin ochiladigan jim xato — 24- va 26-sessiyalardagi
metrikalar va indekslar bilan bir sinfdan.

Bu yerdagi testlar **butun marshrutlar jadvali bo'yicha** aylanadi:
ertaga qo'shiladigan endpoint ham avtomatik tekshiriladi.
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from fastapi.routing import APIRoute

from app.api.deps import ClientLang, get_client_language
from app.geo import registry

#: `?region=` parametrisiz til beradigan endpointlar — **sabab bilan**.
#: Ro'yxat ataylab qisqa: har yangi qator «mintaqa noma'lum» degan
#: da'voni talab qiladi va uni ko'rinadigan qiladi.
NO_REGION_PARAM: dict[str, str] = {
    "get_regions": (
        "Ro'yxatning o'zi mintaqa tanlashdan OLDIN so'raladi — "
        "«qaysi mintaqaning tili» degan savolning javobi yo'q. "
        "`DEFAULT_REGION_CODE` mintaqasining tili ishlatiladi."
    ),
}


def _routes(app) -> list[APIRoute]:
    """Barcha `APIRoute` lar, ichma-ich qo'shilgan routerlar bilan birga.

    `include_router` marshrutlarni tekis ro'yxatga qo'ymaydi — FastAPI
    ularni oraliq obyekt ichida saqlaydi. Rekursiyasiz bu test **hech
    narsani** tekshirmasdan yashil bo'lardi (aynan shunday boshlangan
    edi: bitta `/` marshruti topilgan).
    """
    found: list[APIRoute] = []
    pending = list(app.routes)
    seen: set[int] = set()
    while pending:
        route = pending.pop()
        if id(route) in seen:
            continue
        seen.add(id(route))
        if isinstance(route, APIRoute):
            found.append(route)
        # `include_router` oraliq obyekt yasaydi va haqiqiy router
        # `original_router` da qoladi; ichma-ich qo'shilgan routerlar
        # uchun bu bir necha daraja bo'lishi mumkin.
        for attr in ("routes", "original_router"):
            nested = getattr(route, attr, None)
            if nested is None:
                continue
            pending.extend(nested if isinstance(nested, list) else [nested])
    return found


def _language_aware(route: APIRoute) -> bool:
    """Endpoint mijoz tilini so'raydimi (`ClientLang` bog'liqligi)."""
    return any(
        dep.call is get_client_language for dep in route.dependant.dependencies
    )


def _query_names(route: APIRoute) -> set[str]:
    return {p.alias or p.name for p in route.dependant.query_params}


def test_the_route_table_is_actually_walked(app) -> None:
    """Rekursiya ishlayotganini isbotlaydi.

    Bu test ataylab qo'pol: `_routes()` bitta marshrutni qaytarsa,
    qolgan hamma tekshiruv **yashil** bo'lardi va hech narsani
    qulflamasdi. Aynan shunday boshlangan edi — FastAPI `include_router`
    marshrutlarini tekis ro'yxatga qo'ymaydi.
    """
    routes = _routes(app)
    assert len(routes) > 15
    language_aware = [r.name for r in routes if _language_aware(r)]
    assert "get_stats" in language_aware
    assert "get_map_config" in language_aware
    assert len(language_aware) >= 7


def test_language_aware_endpoints_accept_a_region(app) -> None:
    """Til mijozdan kelmasa, mintaqa noma'lum bo'lsa — javob tilsiz qoladi.

    Aynan shu bo'shliqda defekt tug'ilgan edi: `Lang` bog'liqligi darhol
    `"uz"` qaytarardi va endpoint mintaqani so'rashi kerakligini hech
    narsa eslatmasdi.
    """
    missing = [
        route.name
        for route in _routes(app)
        if _language_aware(route)
        and "region" not in _query_names(route)
        and route.name not in NO_REGION_PARAM
    ]
    assert missing == [], (
        "Til beradigan endpoint `?region=` ni qabul qilishi shart yoki "
        f"`NO_REGION_PARAM` da sabab bilan yozilishi kerak: {missing}"
    )


def test_exemptions_are_real_routes(app) -> None:
    """Istisno ro'yxati eskirmaydi.

    Endpoint qayta nomlansa yoki o'chirilsa, uning istisnosi jimgina
    qolib ketardi va keyingi endpoint uni tasodifan meros qilib olardi.
    """
    names = {route.name for route in _routes(app)}
    stale = sorted(set(NO_REGION_PARAM) - names)
    assert stale == []


def test_exemptions_have_a_reason(app) -> None:
    for name, reason in NO_REGION_PARAM.items():
        assert len(reason) > 40, name


def test_no_endpoint_takes_a_plain_language_string(app) -> None:
    """`ClientLang` — `str | None`, `str` emas.

    `str` bo'lganida «mijoz aytmadi» holati imzoda yo'qolardi va
    chaqiruvchi mintaqadan so'rash kerakligini bilmasdi. Bu test aynan
    o'chirilgan `Lang = Annotated[str, ...]` ning qaytib kelishini
    to'sadi.
    """
    offenders = []
    for route in _routes(app):
        if not _language_aware(route):
            continue
        hints = get_type_hints(route.endpoint, include_extras=False)
        for param in inspect.signature(route.endpoint).parameters:
            if param in {"lang", "client_lang"} and hints.get(param) is str:
                offenders.append(f"{route.name}.{param}")
    assert offenders == []


def test_language_for_is_the_single_resolver() -> None:
    """Tanlov qoidasi bitta joyda — `app.geo.registry.language_for`.

    `regions` jadvalining egasi `app.geo` (`05` §1), ya'ni `app.api` uni
    o'zi o'qiy olmaydi. Imzo shu sababli qulflanadi: `client` va
    `region_code` — ikkalasi ham nomli argument, chunki pozitsion
    chaqiruvda ularni almashtirib qo'yish jim xato bo'lardi.
    """
    sig = inspect.signature(registry.language_for)
    assert list(sig.parameters) == ["session", "client", "region_code"]
    assert sig.parameters["client"].kind is inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["region_code"].kind is inspect.Parameter.KEYWORD_ONLY


def test_the_check_catches_a_real_regression() -> None:
    """Tekshiruvning o'zi ishlayotganini isbotlaydi.

    Yuqoridagi testlar «hech narsa topilmadi» deb yashil bo'ladi va
    bunday testga ishonib bo'lmaydi — u ish bermay qolganini ham
    xuddi shunday ko'rsatardi. Shu sababli bu yerda **ataylab
    buzilgan** endpoint quriladi va tekshiruv uni ushlashi kerak.

    **`ClientLang` modul darajasida import qilinishi shart.** Bu faylda
    `from __future__ import annotations` bor, ya'ni izohlar satr bo'lib
    qoladi va FastAPI ularni funksiya **modulining** globallaridan
    yechadi. Funksiya ichidagi import u yerga tushmaydi va bog'liqlik
    jimgina yo'qoladi — test aynan shu sababli avval yashil bo'lib
    turgan edi.
    """
    from fastapi import FastAPI

    broken = FastAPI()

    @broken.get("/broken")
    async def broken_endpoint(client_lang: ClientLang) -> dict[str, str]:
        return {}

    routes = _routes(broken)
    offenders = [
        r.name
        for r in routes
        if _language_aware(r) and "region" not in _query_names(r)
    ]
    assert offenders == ["broken_endpoint"]


@pytest.mark.parametrize("name", sorted(NO_REGION_PARAM))
def test_exemption_list_is_minimal(name: str) -> None:
    """Istisnolar bitta — ro'yxat o'sib ketmasin.

    O'sish o'zi xato emas, lekin u sezilmay bo'lmasligi kerak: yangi
    qator qo'shgan odam shu testni ham yangilaydi va shunda sabab
    o'ylab topiladi.
    """
    assert name in {"get_regions"}

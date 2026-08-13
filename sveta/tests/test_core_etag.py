"""`app/core/etag.py` — kesh shartnomasi (E15).

`ETag` ikki endpointda ishlatiladi (`/map`, `/geo/districts`), shuning
uchun hisoblash `core` ga ko'chirildi. Bu testlar aynan o'sha ko'chirish
hech narsani buzmaganini va `If-None-Match` ni **RFC bo'yicha** o'qishni
qulflaydi.
"""

from __future__ import annotations

from app.clustering import snapshot
from app.core.etag import DIGEST_SIZE, matches, payload_etag


def test_etag_depends_only_on_content() -> None:
    """Kalitlar tartibi hash ga ta'sir qilmaydi."""
    assert payload_etag({"a": 1, "b": 2}) == payload_etag({"b": 2, "a": 1})


def test_different_content_gives_a_different_etag() -> None:
    assert payload_etag({"a": 1}) != payload_etag({"a": 2})


def test_etag_is_a_strong_quoted_token() -> None:
    etag = payload_etag({"a": 1})
    assert etag.startswith('"') and etag.endswith('"')
    assert not etag.startswith("W/")


def test_non_ascii_is_hashed_stably() -> None:
    """O'zbek va kirill harflari `\\uXXXX` ga aylanmaydi (`ensure_ascii=False`)."""
    first = payload_etag({"name": "Samarqand — Пастдарғом"})
    assert first == payload_etag({"name": "Samarqand — Пастдарғом"})


def test_snapshot_keeps_its_public_name(app) -> None:
    """E9 chaqiruvchilari uchun `snapshot.compute_etag` o'zgarmadi."""
    payload = snapshot.empty_payload("samarkand")
    assert snapshot.compute_etag(payload) == payload_etag(payload)


def test_the_algorithm_itself_is_locked_by_a_golden_value() -> None:
    """`ETag` — sim ustidagi shartnoma, ya'ni algoritmning **o'zi** qulflanadi.

    126-run ning mutatsiya o'lchovi ko'rsatdi: `sort_keys` dan tashqari
    hamma parametrni (`separators`, `ensure_ascii`, `DIGEST_SIZE`)
    jimgina o'zgartirsa bo'lardi — hamma test o'tardi, chunki ularning
    hech biri hash ning **qiymatini** ko'rmasdi, faqat o'zi bilan
    o'zini solishtirardi.

    Narxi ko'rinmas emas: parametr o'zgargan deploydan keyin mazmuni
    o'zgarmagan **har** javob yangi `ETag` oladi, ya'ni barcha mijozlar
    keshi bir vaqtda bekor bo'ladi va `/map` snapshoti (E9) qayta
    yuklanadi. Bu qaror bo'lishi mumkin, lekin **tasodif** bo'lmasligi
    kerak: qiymatni ataylab yangilash — shu testning bir qatori.

    Payload ataylab uchala parametrga sezgir: tartibsiz kalitlar
    (`sort_keys`), ichma-ich tuzilma (`separators`) va kirill
    (`ensure_ascii`).
    """
    assert (
        payload_etag({"b": 2, "a": [1, {"ism": "Пастдарғом"}]})
        == '"b591c425ea2383980ecc1a11f9eab730"'
    )


def test_etag_length_is_the_header_contract() -> None:
    """32 belgi (16 bayt) + ikkita qo'shtirnoq.

    `DIGEST_SIZE` ni kichraytirish testlarga ko'rinmasdi, holbuki u
    to'qnashuv ehtimolini belgilaydi: ikki xil snapshot bitta `ETag`
    olsa, mijoz eskirgan xaritani `304` bilan cheksiz saqlab qolardi.
    """
    assert len(payload_etag({"a": 1})) == 2 + 2 * DIGEST_SIZE
    assert DIGEST_SIZE == 16


def test_if_none_match_accepts_a_list() -> None:
    """Mijoz bir nechta `ETag` yuborishi mumkin (`RFC 9110` §13.1.2)."""
    etag = payload_etag({"a": 1})
    assert matches(f'"boshqa", {etag}', etag)


def test_weak_prefix_is_ignored() -> None:
    etag = payload_etag({"a": 1})
    assert matches(f"W/{etag}", etag)


def test_star_matches_anything() -> None:
    assert matches("*", payload_etag({"a": 1}))


def test_star_is_recognised_around_whitespace() -> None:
    """Sarlavha `strip` qilinadi — `RFC 9110` OWS ga ruxsat beradi.

    `strip()` siz `" * "` oddiy `ETag` sifatida o'qilardi va hech
    qachon mos kelmasdi: `*` yuboradigan mijoz har safar to'liq javob
    olardi (`304` o'rniga `200`) — sekin, lekin **jim** degradatsiya.
    """
    assert matches("  *  ", payload_etag({"a": 1}))


def test_star_only_counts_when_it_is_the_whole_header() -> None:
    """`*` ning ichkarida uchrashi «hamma narsaga mos» degani emas.

    Mutatsiya `header == "*"` ni `"*" in header` ga o'zgartirganda
    hech bir test yiqilmadi: tarkibida `*` bo'lgan **begona** `ETag`
    bilan kelgan so'rov `304` olardi, ya'ni mijoz o'zida yo'q
    javobni keshdan o'qishga urinardi.
    """
    assert not matches('"a*b"', payload_etag({"a": 1}))


def test_a_list_without_spaces_is_still_a_list() -> None:
    """`"x","y"` — vergul atrofidagi bo'shliq `RFC 9110` da ixtiyoriy.

    Mavjud testlarning hammasi `", "` yozardi, shuning uchun
    `split(",")` ni `split(", ")` ga almashtirish ko'rinmasdi: bo'shliq
    qo'ymaydigan mijoz (masalan `curl -H` bilan qo'lda yozilgan
    ro'yxat) `304` o'rniga to'liq javob olardi.
    """
    etag = payload_etag({"a": 1})
    assert matches(f'"boshqa",{etag}', etag)


def test_absent_header_never_matches() -> None:
    etag = payload_etag({"a": 1})
    assert not matches(None, etag)
    assert not matches("", etag)
    assert not matches('"boshqa"', etag)

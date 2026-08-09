"""Payload mazmunidan barqaror `ETag` (`05` §7.1).

**Nima uchun `core` da.** Funksiya E9 da `app/clustering/snapshot.py` ichida
tug'ilgan edi, lekin E15 da uni ikkinchi modul ham talab qildi:
`GET /api/v1/geo/districts` javobi ham keshlanadi, chegaralar esa
`app.geo` ning ma'lumoti. `app.geo` ning `app.clustering` ni import qilishi
`05` §1 modul chegarasini buzardi, ikkinchi nusxa esa vaqt o'tishi bilan
boshqacha hash beradigan ikkita `ETag` yaratardi (bir xil mazmunga ikki xil
javob — kesh uchun eng yomon holat).

`snapshot.compute_etag` shu funksiyaga o'tkazuvchi bo'lib qoladi: E9 nomi
va testlari o'zgarmaydi.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

#: `blake2b` digest uzunligi (bayt). 16 bayt = 32 belgi — HTTP sarlavhasi
#: uchun qisqa, to'qnashuv ehtimoli esa amaliy jihatdan nol.
DIGEST_SIZE = 16


def payload_etag(payload: Any) -> str:
    """Mazmunga bog'liq **kuchli** `ETag`.

    Kuchsiz (`W/`) emas: javob bayt darajasida bir xil quriladi, ya'ni
    `If-None-Match` ni to'liq mos kelish bo'yicha tekshirsa bo'ladi.

    `sort_keys=True` — kalitlar tartibi Python ning `dict` tartibiga
    bog'liq bo'lib qolmasligi uchun; `ensure_ascii=False` — kirill va
    o'zbek harflari hash ga o'z ko'rinishida kiradi.
    """
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return '"' + hashlib.blake2b(raw.encode("utf-8"), digest_size=DIGEST_SIZE).hexdigest() + '"'


def matches(if_none_match: str | None, etag: str) -> bool:
    """`If-None-Match` shu `ETag` ga mos keladimi (`RFC 9110` §13.1.2).

    `*` — «resurs mavjud bo'lsa yetarli». Ro'yxat vergul bilan kelishi
    mumkin, shuning uchun bitta satr bilan taqqoslash kam edi. `W/` prefiksi
    olib tashlanadi: mijoz kuchsiz shaklda qaytarsa ham javob o'zgarmagan.
    """
    if not if_none_match:
        return False
    header = if_none_match.strip()
    if header == "*":
        return True
    candidates = {part.strip().removeprefix("W/") for part in header.split(",")}
    return etag in candidates

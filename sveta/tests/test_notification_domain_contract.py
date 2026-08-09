"""Bildirishnoma domeni: topik va status ro'yxatlari bir-biriga mos.

E13 ning yo'li beshta modul orqali o'tadi va ularning **har biri**
topik yoki status haqidagi faktni o'zida takrorlaydi:

| Joy | Nimani e'lon qiladi |
|---|---|
| `notifications/events.py` | `TOPICS` — topiklarning manbai (`05` §2.4) |
| `notifications/models.py` | `OUTBOX_TOPICS`, `NOTIFICATION_STATUSES` — sxema domeni |
| `notifications/render.py` | `MESSAGE_KEYS` — topik → matn |
| `notifications/service.py` | `prepare()` dispetcheri — topik → auditoriya; `STATUS_*` |
| `clustering/service.py` | `NOTIFIABLE_TOPICS` — topikni **kim chiqaradi** |

## Nima uchun bu sinf jim buziladi

Bazada cheklov yo'q: `outbox.topic` ham, `notifications.status` ham erkin
`text` (`05` §2.4). Ya'ni ro'yxatlar ajralib ketganda `INSERT` o'tadi,
so'rov to'g'ri javob beradi, testlar yashil qoladi.

**Topik bo'yicha.** `TOPICS` ga yangi qiymat qo'shilib `render.MESSAGE_KEYS`
unutilsa — `render()` `None` qaytaradi va har bir qabul qiluvchi qatori
`skipped` ga tushadi; `prepare()` dispetcheri unutilsa — `else` tarmog'i
jurnalga bitta ogohlantirish yozadi va bo'sh ro'yxat qaytaradi. **Ikkala
holatda ham `DeliveryReport.failed == 0`**, ya'ni `report.complete` rost
bo'ladi va `process_outbox` qatorni `mark_processed` bilan **yopadi**
(`jobs/process_outbox.py:82`) — xabar butunlay yo'qoladi va navbatda ham iz
qolmaydi.

**Status bo'yicha — bu allaqachon sodir bo'lgan.** `service.py` E13 ning
yopilish xabari uchun `closed` ni kiritgan, `models.NOTIFICATION_STATUSES`
esa to'rttalik ro'yxat bo'lib qolgan edi. Drift jimgina yashadi, chunki
**bu ro'yxatni hech kim import qilmaydi**: u sxemani o'qiyotgan odam uchun
yozilgan hujjat, ya'ni uni ishlatadigan birinchi so'rov (masalan status
kesimidagi hisobot yoki `CHECK` cheklovi) `closed` qatorlarni jimgina
tashlab yuborardi. Aynan shu narx bugun `queries.status_counts_between`
da o'lchanmoqda.

## Nima uchun `ast`

Dispetcher — jadval emas, `if/elif` zanjiri (`service.prepare`), ya'ni uni
obyekt sifatida o'qib bo'lmaydi. `STATUS_*` konstantalari ham shunday:
ular modul darajasidagi oddiy nom, hech qanday to'plamga yig'ilmagan.
Qolgan hamma narsa **haqiqiy import qilingan obyektdan** o'qiladi
(41-sessiyaning qarori): qiymatlar import paytida allaqachon hisoblangan.

Test bazasiz: manba matni va import qilingan konstantalar.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.clustering.service import NOTIFIABLE_TOPICS
from app.notifications import events, models, render
from app.notifications import service as notify_service

SERVICE_SRC = Path(notify_service.__file__).resolve()

#: Skaner bo'shab qolmasligining pastki chegarasi (34-sessiyaning saboqi).
#: Bugun: 5 ta `STATUS_*`, 2 ta topik, 2 ta dispetcher tarmog'i.
MIN_STATUS_CONSTANTS = 4
MIN_TOPICS = 2


def _service_tree() -> ast.Module:
    return ast.parse(SERVICE_SRC.read_text(encoding="utf-8"))


def _status_constants() -> dict[str, str]:
    """`service.py` dagi modul darajasidagi `STATUS_* = "…"` → qiymat.

    Nima uchun `ast`, `dir(module)` emas: `dir()` import qilingan
    nomlarni ham qaytaradi, ya'ni boshqa moduldan kelgan `STATUS_*`
    shu faylniki bo'lib ko'rinardi va ro'yxat **jimgina** kengayardi.
    """
    found: dict[str, str] = {}
    for node in _service_tree().body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not target.id.startswith("STATUS_"):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            found[target.id] = node.value.value
    return found


def _dispatched_topics() -> set[str]:
    """`prepare()` da `row.topic == TOPIC_*` bilan solishtirilgan topiklar.

    Solishtiruvning **o'ng** tomoni nom bo'lishi shart: o'zgarmas satr
    (`row.topic == "outage.confirmed"`) bu yerda ataylab qo'llab
    quvvatlanmaydi — u `events.py` ni chetlab o'tgan takroriy e'lon
    bo'lardi va aynan shu fayl to'sishi kerak bo'lgan drift.
    """
    prepare = next(
        node
        for node in _service_tree().body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "prepare"
    )
    names: set[str] = set()
    for node in ast.walk(prepare):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        if not isinstance(left, ast.Attribute) or left.attr != "topic":
            continue
        for other in node.comparators:
            if isinstance(other, ast.Name) and other.id.startswith("TOPIC_"):
                names.add(other.id)
    return {getattr(events, name) for name in names}


# --------------------------------------------------------------------------
# Topiklar
# --------------------------------------------------------------------------


def test_the_schema_topic_list_matches_the_events_module() -> None:
    """Bitta fakt, ikkita e'lon — ular ajralib keta olmaydi.

    `models.OUTBOX_TOPICS` ni hech kim import qilmaydi, ya'ni u eskirsa
    hech narsa yiqilmaydi; lekin sxemani o'qiyotgan odam aynan uni
    haqiqat deb qabul qiladi.
    """
    assert tuple(models.OUTBOX_TOPICS) == tuple(events.TOPICS)


def test_every_topic_has_a_message_key() -> None:
    """Matni yo'q topik — `render()` dan `None`, qator esa `skipped`.

    Nosozlik `process_outbox` ga `failed = 0` bo'lib yetadi, ya'ni
    navbat qatori **yopiladi** va xabar hech qachon yuborilmaydi.
    """
    assert set(render.MESSAGE_KEYS) == set(events.TOPICS)


def test_every_topic_has_an_audience_branch() -> None:
    """Auditoriyasi yo'q topik `prepare()` ning `else` tarmog'iga tushadi.

    U yerda faqat `log.warning("notify.unknown_topic")` bor —
    ya'ni istisno ham, qayta urinish ham yo'q.
    """
    assert _dispatched_topics() == set(events.TOPICS)


def test_every_produced_topic_is_declared() -> None:
    """Klasterlash `events.TOPICS` dan tashqariga chiqa olmaydi.

    `NOTIFIABLE_TOPICS` — `app.clustering` dagi yagona joy, u
    `app.notifications.events` ni import qiladi (bog'liqlik bir
    tomonlama, `05` §1).
    """
    assert set(NOTIFIABLE_TOPICS.values()) <= set(events.TOPICS)


def test_every_declared_topic_is_actually_produced() -> None:
    """Teskari yo'nalish (42-sessiyaning naqshi).

    Hech kim chiqarmaydigan topik — `outage.scale.capped` bilan bir xil
    sinf: ro'yxatda turadi, uni ko'rgan odam «bu holat ishlangan» deb
    o'qiydi, va `render.MESSAGE_KEYS` da matn ham bor.
    """
    orphans = sorted(set(events.TOPICS) - set(NOTIFIABLE_TOPICS.values()))
    assert orphans == [], f"topik e'lon qilingan, lekin hech kim chiqarmaydi: {orphans}"


# --------------------------------------------------------------------------
# Statuslar
# --------------------------------------------------------------------------


def test_the_schema_status_list_matches_the_service_constants() -> None:
    """Aynan shu tenglik `closed` driftini o'tkazib yuborgan edi.

    `notifications.status` — erkin `text` (`05` §2.4), ya'ni yangi
    qiymat bazadan hech qanday qarshilik ko'rmaydi. Ro'yxat esa
    hujjat bo'lib qolgani uchun uni yangilashni unutish **hech qanday
    izsiz** o'tadi.
    """
    declared = set(models.NOTIFICATION_STATUSES)
    written = set(_status_constants().values())
    assert declared == written, (
        "`models.NOTIFICATION_STATUSES` va `service.py` dagi `STATUS_*` "
        f"ajralib ketdi: faqat sxemada {sorted(declared - written)}, "
        f"faqat kodda {sorted(written - declared)}"
    )


def test_pending_statuses_are_part_of_the_domain() -> None:
    """Domendan tashqaridagi status hech bir qatorga mos kelmaydi.

    `_pending_rows` `status IN (…)` bilan tanlaydi, ya'ni yozuv xatosi
    **bo'sh** natija beradi: xabar yuborilmaydi, xato chiqmaydi,
    `report.complete` rost bo'ladi va navbat qatori yopiladi.
    """
    assert set(notify_service.PENDING_STATUSES) <= set(models.NOTIFICATION_STATUSES)


def test_the_status_domain_has_no_duplicates() -> None:
    """Ro'yxat qo'lda yoziladi — takror qiymat uni jimgina qisqartiradi."""
    assert len(models.NOTIFICATION_STATUSES) == len(set(models.NOTIFICATION_STATUSES))
    assert len(models.OUTBOX_TOPICS) == len(set(models.OUTBOX_TOPICS))


# --------------------------------------------------------------------------
# Skanerning o'zi
# --------------------------------------------------------------------------


def test_the_scan_is_measuring_something() -> None:
    """Bo'sh to'plam bo'sh to'plamga teng (34-sessiyaning saboqi).

    `STATUS_*` konstantalari lug'atga ko'chirilsa yoki dispetcher
    `match` ga o'tsa, yuqoridagi qoidalar **yashil** bo'lardi va hech
    narsa tekshirilmagani ko'rinmasdi.
    """
    statuses = _status_constants()
    assert len(statuses) >= MIN_STATUS_CONSTANTS, f"faqat {len(statuses)} ta `STATUS_*` topildi"
    assert "STATUS_CLOSED" in statuses, "`closed` — bu faylning sababi, u yo'qolmasin"
    assert len(_dispatched_topics()) >= MIN_TOPICS
    assert len(events.TOPICS) >= MIN_TOPICS

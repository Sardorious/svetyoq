"""`01` §21 Event Tracking jadvali — kod ko'radigan ko'rinishda.

Nima uchun bu ro'yxat kodda kerak
---------------------------------

`01` §21 o'nta hodisani **nom bilan** sanaydi va ularning ustiga §21
«Дашборды» quriladi, shu jumladan ishga tushirishning **asosiy
metrikasi** — «данных недостаточно» verdiktlarining ulushi.
Dashboardlar ro'yxatining o'zi `app.analytics.dashboards` da: bu yerda
u sanalmaydi, chunki izohdagi son hech qayerda o'lchanmaydi va aynan
shu sababdan **noto'g'ri** edi (68-run: «to'rtta» → beshta).
Ro'yxat faqat hujjatda qolsa, hodisaning nomi kodda tasodifan
o'zgarganda dashboard **jimgina bo'shab qoladi**: xato yo'q, javob
to'g'ri, faqat grafik tekislanadi. Bu 24-sessiyadagi (metrikalar) va
28-sessiyadagi (mintaqa tili) defektlar bilan bir sinfdan, shuning
uchun yechim ham o'sha: jadval kodda va uni kontrakt testi qulflaydi.

Uchta qoida
-----------

1. **Har bir hodisada `region` bor.** `01` §22: «все продуктовые метрики
   размечены `region` — иначе самаркандские данные растворятся в
   ташкентских». §21 uni faqat `bot_start` uchun sanaydi, lekin §22
   qoidasi butun mahsulotga tegishli.
2. **Atributlar to'plami — aynan.** Kam ham, ortiq ham emas: iste'molchi
   uchun oqim shakli barqaror bo'lishi kerak. Qiymat `None` bo'lishi
   mumkin (masalan `mahalla_id` E17 gacha doim `None`) — bu «maydon yo'q»
   bilan bir xil emas va aynan shu farq muhim.
3. **Kuzatilmaydigan hodisa ham ro'yxatda qoladi, sabab bilan.** Ikkitasi
   Telegram kanalida umuman kuzatib bo'lmaydi (`observable=False`).
   Ularni ro'yxatdan olib tashlash «biz buni o'lchayapmiz» degan yolg'onni
   yo'q qilardi, lekin talab ham ko'rinmay qolardi — E20 (PWA) da ular
   paydo bo'ladi.

Maxfiylik
---------

Hech bir hodisada foydalanuvchi identifikatori yo'q: na `tg_id`, na
`users.id`. `01` §20: ПДн yig'ilmaydi, Telegram identifikatori
psevdonimlashtirilgan holda saqlanadi — uni jurnal oqimiga chiqarish
`users` jadvaliga to'g'ridan-to'g'ri kalit berardi. Bunga yagona narx —
odam kesimidagi voronka (`01` §21 «воронка активации») **bitta
foydalanuvchi bo'yicha** emas, bosqichlar sonining nisbati sifatida
o'qiladi; bu narx ataylab to'lanadi.

Koordinata ham yo'q. `report_created` da `h3` bor (§21 shuni sanaydi) —
u `05` §3.1 bo'yicha allaqachon psevdonimlashtirilgan shakl va ommaviy
issiqlik xaritasining o'zi shu katakchada quriladi.

Modul toza: bazaga ham, `app.core.logging` ga ham bog'liq emas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Har bir hodisaga qo'shiladigan majburiy yorliq (`01` §22).
REGION_ATTR = "region"

#: Mintaqa aniqlanmagan holat. Yo'qotib yubormaslik uchun **chelak**,
#: `None` emas: 24-sessiyaning qoidasi — tanib bo'lmagani ko'rinishi kerak.
REGION_UNKNOWN = "unknown"


@dataclass(frozen=True)
class EventSpec:
    """`01` §21 jadvalining bitta qatori.

    `attributes` — `region` dan **tashqari** maydonlar, §21 dagi tartibda.
    `observable=False` bo'lsa `reason` bo'sh bo'lmasligi shart: kuzatilmaydigan
    hodisa sababsiz qolsa, uni keyin kim va nima uchun yozmaganini hech kim
    bilmasdi.
    """

    name: str
    attributes: tuple[str, ...] = field(default_factory=tuple)
    observable: bool = True
    reason: str = ""

    def keys(self) -> frozenset[str]:
        return frozenset(self.attributes)


#: `01` §21 «Event Tracking» jadvali, so'zma-so'z va shu tartibda.
SPECS: tuple[EventSpec, ...] = (
    EventSpec("bot_start", ("language_detected",)),
    # `01` §21 da ustunlar `from` / `to`. `from` — Python kalit so'zi, ya'ni
    # uni `**kwargs` bilan uzatib bo'lmaydi; `emit()` shu sababli atributlarni
    # **lug'at** qilib oladi, kalit so'z argumenti qilib emas.
    EventSpec("language_changed", ("from", "to")),
    EventSpec("report_submit_attempt", ("geo_source",)),
    EventSpec("report_created", ("district_id", "mahalla_id", "h3", "accuracy")),
    EventSpec(
        "geo_permission_denied",
        (),
        observable=False,
        reason=(
            "Telegram geolokatsiyani rad etish haqida hech qanday signal "
            "bermaydi: foydalanuvchi tugmani bosmasa, bot uchun bu shunchaki "
            "javobsizlik. Hodisa E20 (PWA) da paydo bo'ladi — brauzerning "
            "Permissions API si rad etishni ochiq qaytaradi."
        ),
    ),
    EventSpec("verdict_shown", ("verdict_type",)),
    EventSpec("subscription_created", ("radius",)),
    EventSpec("notification_sent", ("outage_id",)),
    EventSpec(
        "notification_opened",
        ("outage_id",),
        observable=False,
        reason=(
            "Telegram Bot API o'qilganlik kvitansiyasini bermaydi. Ochilishni "
            "faqat xabar ichidagi tugma orqali bilish mumkin bo'lardi, "
            "bildirishnoma esa (`05` §6.1) tugmasiz matn. E20 (Web Push) da "
            "ochilish hodisasi platformadan keladi."
        ),
    ),
    EventSpec("stats_viewed", ("district_id", "mahalla_id", "period")),
    EventSpec("light_returned_pressed", ("outage_id",)),
)

#: Nom bo'yicha kirish.
CATALOGUE: dict[str, EventSpec] = {spec.name: spec for spec in SPECS}

#: Kod chiqaradigan hodisalar (kontrakt testi shularni qidiradi).
OBSERVABLE: tuple[str, ...] = tuple(s.name for s in SPECS if s.observable)


#: `logging.LogRecord` ning o'z maydonlari. `extra` orqali shulardan birini
#: uzatish `logging` ning o'zida `KeyError` beradi — ya'ni analitika
#: foydalanuvchi oqimini yiqitardi. Kontrakt testi to'qnashuvni taqiqlaydi.
LOGRECORD_RESERVED: frozenset[str] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)

"""`01` §19 «Notifications» ↔ kodda haqiqatan bor narsa.

**Nima uchun bu modul bor.** §19 — hujjatdagi yagona joy, u yerda
«mahsulot foydalanuvchiga qaysi yo'llar bilan xabar beradi» degan
savolga javob beriladi: oltita kanal, har birida `Статус в регионе` va
`Обоснование`, va ularning ostida bitta jumla — yetkazish qoidasi.
43-run bo'limning **oxirgi jumlasini** (radius kalibrlanadi) kodga
bog'lagan, `05` §6.1 domenini esa alohida qulflagan. Jadvalning o'zi —
oltita qator — hech qachon o'qilmagan.

## `Статус в регионе` — bitta ustunda ikki xil da'vo

Ustunda uch xil qiymat bor va ular bir turdagi gap emas:

* «MVP» va «Phase 2» — **reja**. Ular *qachon* deydi va vaqt o'tishi
  bilan rost bo'ladi.
* «Не входит» — **siyosat**. U *hech qachon* deydi va sababini
  aytadi (ПДн yo'q, narx, tasdiqlanmagan talab).

Ikkilik «qurilgan / qurilmagan» o'qish shu farqni yo'qotadi va
ro'yxatni **teskari** tartibda ko'rsatadi: uchta «Не входит» qatori
bugun 100% bajarilgan bo'lib chiqadi, «Phase 2» esa qarz bo'lib. Aslida
teskarisi xavfliroq — «Phase 2» qatori buzila **olmaydi** (kelajak
haqidagi gapni bugungi commit yolg'onga aylantirmaydi), «Не входит»
qatori esa bitta migratsiya bilan yolg'onga aylanadi va buni hech kim
sezmaydi.

Shuning uchun ikkita savol ikkita o'qga ajratildi: reja qatori uchun
«**yo'l** bormi», siyosat qatori uchun «**qorovul** bormi».

## Ikkita o'q

`Reach` — kanal bugun foydalanuvchiga yeta oladimi. Uchta holat, va
o'rtadagisi shu bo'limning asosiy topilmasi (quyida).

`Standing` — qatorning da'vosini nimadir **ushlab turibdimi**. U
`Reach` ni takrorlamaydi: `Reach` bugungi qobiliyat haqida, `Standing`
esa ertangi kun haqida — da'vo buzilganda nimadir yiqiladimi.

`BORROWED` faqat «Не входит» qatorlarida bo'la oladi va bu qoida
tasodifiy emas. Mavjudlik haqidagi da'vo kod **o'chirilganda** buziladi,
uni ushlaydigan test esa ta'rifi bo'yicha o'sha kanal haqida yozilgan.
Yo'qlik haqidagi da'vo kod **qo'shilganda** buziladi, mavjud bo'lmagan
narsa haqida esa hech kim test yozmaydi — demak qorovul, agar bor
bo'lsa, doim **birovniki**.

## Eng jim topilma — `SURFACED`, va u MVP qatorida

«In-App (веб-баннер) — MVP — Дёшево». Repoda `#banner` **bor**
(`web/index.html`, `web/app.js`), ya'ni hujjat atagan artefakt joyida
va qidiruv uni topadi. Lekin u §19 ning yukini olib yurmaydi: bannerga
faqat xarita diagnostikasi chiqadi — `map.tiles_missing`, `map.stale`,
`map.empty`, `map.error` va qamrov ogohlantirishlari. Hodisa haqidagi
bildirishnoma u yerga hech qachon tushmaydi.

Va tusha olmaydi ham. §19 ning yetkazish qoidasi «при подтверждённом
инциденте **в радиусе подписки**» deydi; obuna esa `users.tg_id` ga
bog'langan va faqat bot orqali yaratiladi
(`app.notifications.subscriptions.add` ← `app.bot.handlers`). Vebda
foydalanuvchi identifikatori yo'q va §20 ga ko'ra bo'lmaydi ham. Ya'ni
ikkinchi MVP kanali tugallanmagan ish emas — u o'zi meros qilib olgan
qoida bilan **ziddiyatda**. 👤 Qaror odamniki: qoida vebda boshqacha
o'qiladimi (masalan ko'rinib turgan hududdagi tasdiqlangan hodisa,
obunasiz) yoki qator «Phase 2» ga ko'chadimi.

## `notifications` da kanal ustuni yo'q — va `UNIQUE` uni to'sadi

`05` §2.4 `notifications` ga `UNIQUE (user_id, outage_id)` beradi va
E13 o'sha cheklovga tayanadi: outbox `at-least-once`, ya'ni takroriy
urinish bir odamga ikki marta xabar yuborardi. Bitta kanal uchun bu
aynan to'g'ri.

Ikkita kanal uchun esa u kafolat emas, **to'siq**: bir foydalanuvchi bir
hodisa haqida ikkala kanalda ham xabar ololmaydi, chunki qator bitta va
kanal ustuni yo'q. Shuning uchun §19 ning MVP i ikki kanalli bo'lsa ham,
sxema bir kanalli; Phase 2 dagi Web Push esa migratsiyasiz umuman
qo'shilmaydi. Bu bugun hech narsani yiqitmaydi — ikkinchi kanal
yo'qligi uchun — ya'ni defekt emas, **narx**, va u `SURFACED` topilmasi
bilan bir tugunda yotadi.

## Teskari yo'nalish: e'lon qilinmagan yo'l

§19 to'liq bo'lishi shart — bu uning yagona vazifasi. Bugun ro'yxatda
kunlik hisobot yo'q: `app.jobs.daily_digest` xuddi shu `Sender`
transporti bilan `DIGEST_CHAT_IDS` ga yozadi. «Telegram (in-bot)»
qatori uning o'rnini bosmaydi — auditoriya boshqa (operator chati,
obunachi emas), obuna yo'q, radius yo'q va matn hodisa haqida emas,
sutka haqida.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

#: Bu ro'yxatning hujjatdagi manzili.
SPEC = "01 §19"


class Claim(StrEnum):
    """`Статус в регионе` ustuni qanday da'vo qilyapti."""

    #: «MVP» — kanal bugun ishlaydi.
    SHIPPING = "shipping"
    #: «Phase 2» — keyinroq. Bugungi commit uni yolg'onga aylantira olmaydi.
    SCHEDULED = "scheduled"
    #: «Не входит» — hech qachon, va sababi bilan. Bitta migratsiya
    #: bilan yolg'onga aylanadi.
    EXCLUDED = "excluded"


#: Hujjatdagi status matni → `Claim`. Notanish matn `ValueError` beradi:
#: yangi status jimgina «reja» deb o'qilardi.
CLAIM_BY_STATUS: dict[str, Claim] = {
    "MVP": Claim.SHIPPING,
    "Phase 2": Claim.SCHEDULED,
    "Не входит": Claim.EXCLUDED,
}


class Reach(StrEnum):
    """Kanal bugun foydalanuvchiga yeta oladimi."""

    #: To'liq yo'l bor: hodisa qaror qiladi, manzil topiladi, transport
    #: yuboradi.
    DELIVERS = "delivers"
    #: Hujjat atagan artefakt mahsulotda **bor**, lekin §19 ning yukini
    #: olib yurmaydi. Tashqaridan `DELIVERS` ga o'xshaydi (qidiruv uni
    #: topadi), amalda `NONE` (bildirishnoma yetmaydi).
    SURFACED = "surfaced"
    #: Kanal uchun kodda hech narsa yo'q.
    NONE = "none"


class Standing(StrEnum):
    """Qatorning da'vosini nimadir ushlab turibdimi.

    `Reach` ni takrorlamaydi: `Reach` — bugungi qobiliyat, `Standing` —
    da'vo buzilganda nimadir yiqiladimi.
    """

    #: Repoda mexanizm bor va u aynan shu da'vo uchun yozilgan.
    HELD = "held"
    #: Da'vo ushlab turilibdi, lekin **boshqa** bo'limning sababi bilan
    #: yozilgan mexanizm tomonidan. O'sha sabab qayta ko'rilsa, qorovul
    #: jimgina yo'qoladi.
    BORROWED = "borrowed"
    #: Bugun rost, ertaga rostligini hech narsa kafolatlamaydi.
    UNHELD = "unheld"
    #: Kelajak fazasi haqidagi qator: ushlaydigan narsa hali yo'q va
    #: qorovul talab qilish Phase 2 kodini bugun talab qilish bo'lardi
    #: (67-run ning `EXTERNAL` sinfi).
    PREMATURE = "premature"


# --------------------------------------------------------------------------
# §19 jadvalini parse qilish
# --------------------------------------------------------------------------


#: Hujjatdagi ustun sarlavhasi → `ChannelRow` maydoni.
_COLUMN_FIELDS: dict[str, str] = {
    "Канал": "channel",
    "Статус в регионе": "status",
    "Обоснование": "rationale",
}

_SECTION_RE = re.compile(r"^##\s+19\.\s+Notifications\s*$", re.MULTILINE)
_NEXT_SECTION_RE = re.compile(r"^##\s+\d+\.", re.MULTILINE)
_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")
#: Yetkazish qoidasi paragrafidagi meros radius: «500 м Ташкента».
_BASELINE_RE = re.compile(r"(\d+)\s*м\s+Ташкента")


@dataclass(frozen=True)
class ChannelRow:
    """§19 jadvalining bitta qatori."""

    channel: str
    status: str
    rationale: str

    @property
    def claim(self) -> Claim:
        try:
            return CLAIM_BY_STATUS[self.status]
        except KeyError:
            raise ValueError(
                f"{SPEC}: `{self.channel}` da notanish status `{self.status}`"
            ) from None

    def cell(self, column: str) -> str:
        """Ustun sarlavhasi bo'yicha katakcha.

        Noma'lum sarlavha uchun yagona qorovul shu yerda (73-run ning
        survivori: ikkinchi nusxa bir xil xabar bilan yiqilardi va
        birinchisini olib tashlash sezilmasdi).
        """
        try:
            return getattr(self, _COLUMN_FIELDS[column])
        except KeyError:
            raise ValueError(f"{SPEC}: `{column}` degan ustun yo'q") from None


@dataclass(frozen=True)
class ChannelTable:
    columns: tuple[str, ...]
    rows: tuple[ChannelRow, ...]
    #: Jadvaldan keyingi yetkazish qoidasi paragrafi.
    rule_text: str
    #: «500 м Ташкента» — meros qilib olingan boshlang'ich radius.
    baseline_radius_m: int

    def row(self, channel: str) -> ChannelRow | None:
        for item in self.rows:
            if item.channel == channel:
                return item
        return None


def section_text(doc: str) -> str:
    """`01` dan §19 ning matnini kesib oladi."""
    match = _SECTION_RE.search(doc)
    if match is None:
        raise ValueError(f"{SPEC}: bo'lim topilmadi")
    rest = doc[match.end() :]
    nxt = _NEXT_SECTION_RE.search(rest)
    return rest[: nxt.start()] if nxt else rest


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_table(doc: str) -> ChannelTable:
    """§19 ning jadvalini va yetkazish qoidasini o'qiydi.

    Qo'lda ko'chirilgan nusxa yo'q (61-run sabog'i): ustun sarlavhalari
    ham, qatorlar ham, meros radius ham faqat hujjatdan keladi.
    """
    body = section_text(doc)
    header: tuple[str, ...] | None = None
    rows: list[ChannelRow] = []
    tail: list[str] = []

    for raw in body.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            if header is not None and rows:
                if line and not line.startswith("---"):
                    tail.append(line)
            continue
        if _SEPARATOR_RE.match(line):
            continue
        if tail:
            raise ValueError(f"{SPEC}: qoida paragrafidan keyin yana jadval bor")
        cells = _split_row(line)
        if header is None:
            header = tuple(cells)
            unknown = [name for name in header if name not in _COLUMN_FIELDS]
            if unknown:
                raise ValueError(f"{SPEC}: notanish ustun(lar): {unknown}")
            missing = [name for name in _COLUMN_FIELDS if name not in header]
            if missing:
                raise ValueError(f"{SPEC}: ustun(lar) yo'q: {missing}")
            continue
        if len(cells) != len(header):
            raise ValueError(f"{SPEC}: qatorda {len(cells)} katakcha, sarlavhada {len(header)}")
        values = dict(zip(header, cells, strict=True))
        rows.append(
            ChannelRow(
                channel=values["Канал"],
                status=values["Статус в регионе"],
                rationale=values["Обоснование"],
            )
        )

    if header is None or not rows:
        raise ValueError(f"{SPEC}: jadval topilmadi")
    for row in rows:
        row.claim  # noqa: B018 — notanish status shu yerda to'xtatiladi
        if not row.rationale:
            raise ValueError(f"{SPEC}: `{row.channel}` da `Обоснование` bo'sh")

    rule_text = " ".join(tail).strip()
    if not rule_text:
        raise ValueError(f"{SPEC}: yetkazish qoidasi paragrafi topilmadi")
    baseline = _BASELINE_RE.search(rule_text)
    if baseline is None:
        raise ValueError(f"{SPEC}: qoidada meros radius («N м Ташкента») topilmadi")

    return ChannelTable(
        columns=header,
        rows=tuple(rows),
        rule_text=rule_text,
        baseline_radius_m=int(baseline.group(1)),
    )


# --------------------------------------------------------------------------
# Reyestr: har qator uchun koddagi holat
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Assessment:
    """Bitta kanalning koddagi holati va uning asosi."""

    channel: str
    reach: Reach
    standing: Standing
    why: str
    #: `modul:simvol` — yetkazish yo'lini ko'taradigan joylar. `NONE` da
    #: bo'sh bo'lishi **shart**: dalilsiz «yo'q» va dalilli «yo'q» bir xil
    #: ko'rinmasligi kerak.
    evidence: tuple[str, ...] = ()
    #: `HELD`/`BORROWED` da: da'voni ushlab turgan mexanizm.
    guard: tuple[str, ...] = ()
    #: `BORROWED` da: qorovul qaysi bo'limning sababi bilan yozilgan.
    borrowed_from: str | None = None
    #: `SURFACED` da: artefakt qayerda va uning o'rniga nima olib yuradi.
    surfaced_as: str | None = None
    carries: str | None = None


ASSESSMENTS: tuple[Assessment, ...] = (
    Assessment(
        channel="Telegram (in-bot)",
        reach=Reach.DELIVERS,
        standing=Standing.HELD,
        evidence=(
            "app.clustering.service:_publish",
            "app.notifications.subscriptions:find_matching",
            "app.notifications.service:process",
            "app.bot.notifier:TelegramSender",
            "app.jobs.process_outbox:run",
        ),
        guard=(
            "tests.test_notifications_db:test_confirmed_notifies_the_subscriber",
            "tests.test_notifications_db:test_matching_uses_both_radii",
            "tests.test_notification_domain_contract:test_every_topic_has_an_audience_branch",
        ),
        why=(
            "Yagona to'liq yo'l: hodisa `confirmed` bo'lganda "
            "`clustering.service._publish` outbox ga qator qo'yadi, "
            "`notifications.service.process` radius bo'yicha obunachilarni "
            "topadi, `notifications` ga niyat yozadi va `Sender` orqali "
            "yuboradi; transport `app.bot.notifier` da (aiogram). Barcha "
            "uchala bo'g'in test bilan qulflangan — yo'l uzilsa to'plam "
            "yiqiladi."
        ),
    ),
    Assessment(
        channel="In-App (веб-баннер)",
        reach=Reach.SURFACED,
        standing=Standing.UNHELD,
        surfaced_as="web/index.html:banner",
        carries="map.tiles_missing, map.stale, map.empty, map.error, coverage warnings",
        evidence=("web/app.js:function banner", "web/index.html:id=\"banner\""),
        why=(
            "Hujjat atagan artefakt joyida: `#banner` `web/index.html` da "
            "bor va `web/app.js` uni to'ldiradi. Lekin unga faqat xarita "
            "diagnostikasi chiqadi; hodisa haqidagi bildirishnoma u yerga "
            "hech qachon tushmaydi. Tusha olmaydi ham: §19 ning qoidasi "
            "«в радиусе подписки» deydi, obuna esa `users.tg_id` ga "
            "bog'langan va faqat bot orqali yaratiladi — vebda "
            "foydalanuvchi identifikatori yo'q va §20 ga ko'ra "
            "bo'lmaydi. Ya'ni ikkinchi MVP kanali tugallanmagan ish emas, "
            "u meros qilib olgan qoida bilan ziddiyatda."
        ),
    ),
    Assessment(
        channel="Web Push (PWA)",
        reach=Reach.NONE,
        standing=Standing.PREMATURE,
        why=(
            "E20, `01` §24 Phase 2. Kodda hech narsa yo'q: service worker "
            "ham, `manifest.json` ham, VAPID kaliti ham. To'g'ri holat — "
            "kelajak fazasi haqidagi qatorni bugungi commit yolg'onga "
            "aylantira olmaydi, ya'ni ushlaydigan narsa yo'q. ⚠️ Lekin narx "
            "bor va u sxemada: `notifications` da kanal ustuni yo'q, "
            "`UNIQUE (user_id, outage_id)` esa bir hodisa uchun bitta qator "
            "beradi — ikkinchi kanal migratsiyasiz qo'shilmaydi."
        ),
    ),
    Assessment(
        channel="Email",
        reach=Reach.NONE,
        standing=Standing.BORROWED,
        borrowed_from="01 §20 «ПДн не собираются»",
        guard=("app.admin.security:USERS_ALLOWED_COLUMNS",),
        why=(
            "Kodda email yo'q va uni qo'shish uchun avval manzil kerak — "
            "`users` ga yangi ustun. O'sha ustunni 71-run ning oq ro'yxati "
            "to'sadi va test yiqiladi. Lekin ro'yxat §19 uchun emas, §20 "
            "ning ПДн qatori uchun yozilgan: qorovulning sababi «kanal "
            "ko'lamdan tashqarida» emas, «shaxsiy ma'lumot yig'ilmaydi». "
            "Hujjatning o'zi ham shu sababni keltiradi, ya'ni qator §20 ga "
            "bog'liq — va §20 ning ПДн pozitsiyasi bugun ochiq savol "
            "(`tg_id` ning psevdonimligi, 71-run)."
        ),
    ),
    Assessment(
        channel="SMS",
        reach=Reach.NONE,
        standing=Standing.BORROWED,
        borrowed_from="01 §20 «ПДн не собираются»",
        guard=("app.admin.security:USERS_ALLOWED_COLUMNS",),
        why=(
            "Hujjatning sababi narx («стоимость несовместима с "
            "некоммерческой моделью»), repodagi qorovul esa boshqa: telefon "
            "raqami ham `users` ga ustun talab qiladi va oq ro'yxat uni "
            "to'sadi. Ya'ni qator ushlab turilibdi, lekin **o'z sababi "
            "bilan emas** — narx haqida repoda hech narsa yo'q va "
            "bepul SMS-shlyuz topilsa ro'yxatdan boshqa hech narsa "
            "qarshilik qilmaydi."
        ),
    ),
    Assessment(
        channel="WhatsApp",
        reach=Reach.NONE,
        standing=Standing.BORROWED,
        borrowed_from="01 §20 «ПДн не собираются»",
        guard=("app.admin.security:USERS_ALLOWED_COLUMNS",),
        why=(
            "SMS bilan bir xil mexanizm va bir xil bo'shliq: sabab "
            "«нет подтверждённого спроса», qorovul esa telefon ustunini "
            "to'sadigan oq ro'yxat. Uchala «Не входит» qatori uchun repoda "
            "**bitta** qorovul bor va u to'rtinchi sabab bilan yozilgan — "
            "ya'ni §20 ning ПДн pozitsiyasi o'zgarsa, §19 ning uchta "
            "qatori bir vaqtda qorovulsiz qoladi va §19 buni sezmaydi."
        ),
    ),
)

ASSESSMENT_BY_CHANNEL: dict[str, Assessment] = {a.channel: a for a in ASSESSMENTS}


# --------------------------------------------------------------------------
# Yetkazish qoidasi (jadvaldan keyingi paragraf)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RuleClause:
    """Qoidaning bitta bandi va uni bajaradigan joy."""

    #: Hujjat matnidan kesik — paragrafda **so'zma-so'z** bo'lishi shart.
    quote: str
    evidence: tuple[str, ...]
    why: str


#: `01` §19 ning oxirgi paragrafi uch narsani aytadi va uchalasi ham
#: kodda alohida joyda bajariladi. Iqtiboslar hujjatdan qidiriladi:
#: paragraf qayta yozilsa test yiqiladi.
RULE_CLAUSES: tuple[RuleClause, ...] = (
    RuleClause(
        quote="при подтверждённом инциденте",
        evidence=(
            "app.clustering.service:NOTIFIABLE_TOPICS",
            "app.notifications.events:TOPIC_CONFIRMED",
        ),
        why=(
            "Outbox ga qator faqat status `confirmed` yoki `resolved` "
            "bo'lganda qo'yiladi, va `resolved` xabari faqat oldin "
            "`confirmed` bo'lgan hodisaga boradi — ya'ni tasdiqlanmagan "
            "hodisa haqida hech kimga xabar ketmaydi."
        ),
    ),
    RuleClause(
        quote="в радиусе подписки",
        evidence=("app.notifications.subscriptions:find_matching",),
        why=(
            "Obunachi hodisa markazidan `subscriptions.radius_m` ichida "
            "bo'lsa tanlanadi. Markaz — `geom_public` (jitter bilan, "
            "`05` §3.1), shuning uchun `MIN_RADIUS_M` jitterdan katta."
        ),
    ),
    RuleClause(
        quote="подлежит калибровке отдельно",
        evidence=(
            "app.notifications.params:KEY_DEFAULT_RADIUS",
            "app.notifications.params:KEY_MAX_RADIUS",
            "app.notifications.params:from_mapping",
        ),
        why=(
            "43-run: radius `region_config` da, mintaqa kesimida — ya'ni "
            "kalibrlash deploysiz va boshqa mintaqaga tarqalmasdan "
            "bajariladi. ⚠️ Mexanizm bor, **qiymat esa hali meros**: "
            "`region_config` bo'sh bo'lsa `SUBSCRIPTION_DEFAULT_RADIUS_M` "
            "ishlaydi va uning standarti — hujjat «могут не "
            "соответствовать» degan aynan o'sha Toshkent soni."
        ),
    ),
)


# --------------------------------------------------------------------------
# Teskari yo'nalish: §19 da yo'q, kodda bor
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class UndeclaredPath:
    """Mahsulot xabar yuboradi, §19 esa bu yo'lni nomlamaydi."""

    name: str
    audience: str
    evidence: tuple[str, ...]
    why: str


UNDECLARED: tuple[UndeclaredPath, ...] = (
    UndeclaredPath(
        name="Kunlik hisobot (daily digest)",
        audience="DIGEST_CHAT_IDS",
        evidence=(
            "app.jobs.daily_digest:run",
            "app.jobs.daily_digest:chat_ids",
            "app.jobs.daily_digest:deliver",
            "app.admin.digest:render",
        ),
        why=(
            "19-run ning fon vazifasi xuddi shu `Sender` transporti bilan "
            "Telegramga yozadi, lekin «Telegram (in-bot)» qatori uning "
            "o'rnini bosmaydi: auditoriya obunachi emas, operator chati; "
            "obuna ham, radius ham yo'q; matn hodisa haqida emas, sutka "
            "haqida. §19 kanallarni auditoriya bo'yicha sanaydi, transport "
            "bo'yicha emas — aks holda «Telegram» qatori har qanday "
            "yuborishni yutib yuborardi."
        ),
    ),
)


# --------------------------------------------------------------------------
# Baholash
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    row: ChannelRow
    assessment: Assessment

    @property
    def channel(self) -> str:
        return self.row.channel

    @property
    def claim(self) -> Claim:
        return self.row.claim

    @property
    def reach(self) -> Reach:
        return self.assessment.reach

    @property
    def standing(self) -> Standing:
        return self.assessment.standing

    @property
    def overstated(self) -> bool:
        """Hujjat kanalni ishlaydi deydi, amalda esa u yetkazmaydi."""
        return self.claim is Claim.SHIPPING and self.reach is not Reach.DELIVERS

    @property
    def unguarded_policy(self) -> bool:
        """«Не входит» qatori o'z sababi bilan ushlab turilmayaptimi."""
        return self.claim is Claim.EXCLUDED and self.standing is not Standing.HELD


def assess(row: ChannelRow, assessment: Assessment) -> Finding:
    """Bitta qatorni baholaydi va ikkala o'qning izchilligini talab qiladi.

    Qoidalar hujjatdan kelib chiqadi, reyestrdan emas: `Standing`
    `Статус в регионе` bilan `Reach` ning **kesishmasida** yotishi
    shart, aks holda reyestrga istalgan holatni qo'lda yozib qo'yish
    mumkin bo'lardi (73-run, survivor).
    """
    if assessment.channel != row.channel:
        raise ValueError(f"{SPEC}: `{row.channel}` uchun `{assessment.channel}` bahosi berildi")

    if not assessment.why.strip():
        raise ValueError(f"{SPEC}: `{row.channel}` uchun izoh yo'q")

    reach = assessment.reach
    standing = assessment.standing
    claim = row.claim

    # --- dalillar -----------------------------------------------------
    if reach is Reach.NONE:
        if assessment.evidence:
            raise ValueError(f"{SPEC}: `{row.channel}` — `NONE`, lekin dalil ko'rsatilgan")
    elif not assessment.evidence:
        raise ValueError(f"{SPEC}: `{row.channel}` — `{reach}`, dalil yo'q")

    if reach is Reach.SURFACED:
        if not assessment.surfaced_as or not assessment.carries:
            raise ValueError(
                f"{SPEC}: `{row.channel}` — `SURFACED`, lekin artefakt yoki "
                "uning yuki ko'rsatilmagan"
            )
    elif assessment.surfaced_as or assessment.carries:
        raise ValueError(f"{SPEC}: `{row.channel}` — `{reach}`, lekin artefakt ko'rsatilgan")

    # --- qorovul ------------------------------------------------------
    if standing in (Standing.HELD, Standing.BORROWED):
        if not assessment.guard:
            raise ValueError(f"{SPEC}: `{row.channel}` — `{standing}`, lekin qorovul yo'q")
    elif assessment.guard:
        raise ValueError(f"{SPEC}: `{row.channel}` — `{standing}`, lekin qorovul ko'rsatilgan")

    if standing is Standing.BORROWED:
        if not assessment.borrowed_from:
            raise ValueError(f"{SPEC}: `{row.channel}` — `BORROWED`, manba bo'lim ko'rsatilmagan")
        if claim is not Claim.EXCLUDED:
            raise ValueError(
                f"{SPEC}: `{row.channel}` — `BORROWED` faqat «Не входит» qatorida "
                "bo'ladi: mavjudlik da'vosi kod o'chirilganda buziladi va uni "
                "ushlaydigan test o'sha kanal haqida yozilgan bo'ladi"
            )
    elif assessment.borrowed_from:
        raise ValueError(f"{SPEC}: `{row.channel}` — `{standing}`, lekin manba bo'lim ko'rsatilgan")

    # --- da'vo ↔ holat kesishmasi -------------------------------------
    if claim is Claim.SHIPPING:
        if reach is Reach.NONE:
            raise ValueError(
                f"{SPEC}: `{row.channel}` — «MVP», lekin kanal uchun kodda hech narsa yo'q"
            )
        if standing is Standing.PREMATURE:
            raise ValueError(
                f"{SPEC}: `{row.channel}` — «MVP», ya'ni da'vo bugun rost bo'lishi kerak"
            )
    elif claim is Claim.SCHEDULED:
        if reach is not Reach.NONE:
            raise ValueError(
                f"{SPEC}: `{row.channel}` — «Phase 2», lekin kodda allaqachon bir narsa bor"
            )
        if standing is not Standing.PREMATURE:
            raise ValueError(f"{SPEC}: `{row.channel}` — «Phase 2» uchun `PREMATURE` kutiladi")
    else:
        if reach is not Reach.NONE:
            raise ValueError(
                f"{SPEC}: `{row.channel}` — «Не входит», lekin kodda bir narsa bor"
            )
        if standing is Standing.PREMATURE:
            raise ValueError(
                f"{SPEC}: `{row.channel}` — «Не входит» siyosat, kelajak fazasi emas"
            )

    # `SURFACED` «Не входит» qatorida bo'la olmaydi — lekin buning
    # uchun alohida shart yozilmaydi: yuqoridagi `reach is not
    # Reach.NONE` uni allaqachon to'sadi. Ikkinchi nusxa **o'lik**
    # bo'lardi va uni olib tashlash hech qayerda sezilmasdi (73-run
    # ning survivori aynan shu edi: ustun qorovuli ikki joyda bir xil
    # xabar bilan takrorlangan edi).

    return Finding(row=row, assessment=assessment)


@dataclass(frozen=True)
class Report:
    findings: tuple[Finding, ...]
    table: ChannelTable
    clauses: tuple[RuleClause, ...]
    undeclared: tuple[UndeclaredPath, ...]

    def by_reach(self, reach: Reach) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.reach is reach)

    def by_standing(self, standing: Standing) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.standing is standing)

    def by_claim(self, claim: Claim) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.claim is claim)

    @property
    def counts(self) -> dict[str, int]:
        return {s.value: len(self.by_standing(s)) for s in Standing}

    @property
    def delivering(self) -> tuple[Finding, ...]:
        return self.by_reach(Reach.DELIVERS)

    @property
    def overstated(self) -> tuple[Finding, ...]:
        """«MVP» deb yozilgan, lekin yetkazmaydigan kanallar."""
        return tuple(f for f in self.findings if f.overstated)

    @property
    def unguarded(self) -> tuple[Finding, ...]:
        """«Не входит» qatorlari, o'z sababi bilan ushlab turilmaganlari."""
        return tuple(f for f in self.findings if f.unguarded_policy)

    @property
    def accurate(self) -> bool:
        """§19 bugungi kodni to'g'ri tasvirlaydimi.

        Uchta mustaqil shart: e'lon qilinmagan yo'l bo'lmasligi (ro'yxat
        **to'liq**), «MVP» qatorlarining hammasi yetkazishi (reja
        **bajarilgan**) va «Не входит» qatorlarining hammasi o'z sababi
        bilan ushlab turilishi (siyosat **himoyalangan**).

        `PREMATURE` bu yerda yo'qlik emas: kelajak fazasi uchun
        kodsizlik — to'g'ri holat.
        """
        return not self.undeclared and not self.overstated and not self.unguarded


def build_report(doc: str) -> Report:
    """Hujjat matni → to'liq hisobot.

    Reyestrda bo'lmagan qator ham, jadvalda bo'lmagan baho ham
    `ValueError`: §19 ga yangi kanal qo'shilsa, kimdir uni **ataylab**
    baholashi kerak bo'ladi.
    """
    table = parse_table(doc)
    findings: list[Finding] = []
    for row in table.rows:
        assessment = ASSESSMENT_BY_CHANNEL.get(row.channel)
        if assessment is None:
            raise ValueError(f"{SPEC}: `{row.channel}` baholanmagan")
        findings.append(assess(row, assessment))

    declared = {row.channel for row in table.rows}
    orphans = sorted(name for name in ASSESSMENT_BY_CHANNEL if name not in declared)
    if orphans:
        raise ValueError(f"{SPEC}: jadvalda yo'q kanal(lar) baholangan: {orphans}")

    for clause in RULE_CLAUSES:
        if clause.quote not in table.rule_text:
            raise ValueError(f"{SPEC}: qoidada «{clause.quote}» topilmadi")
        if not clause.evidence:
            raise ValueError(f"{SPEC}: «{clause.quote}» uchun dalil yo'q")

    return Report(
        findings=tuple(findings),
        table=table,
        clauses=RULE_CLAUSES,
        undeclared=UNDECLARED,
    )

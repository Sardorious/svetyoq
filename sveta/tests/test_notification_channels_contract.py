"""`01` §19 «Notifications» ↔ kodda haqiqatan bor narsa.

**Nima uchun bu fayl kerak.** §19 — hujjatdagi yagona joy, u yerda
«mahsulot foydalanuvchiga qaysi yo'llar bilan xabar beradi» degan
savolga javob beriladi. 43-run bo'limning **oxirgi jumlasini** (radius
kalibrlanadi) kodga bog'lagan; jadvalning oltita qatori hech qachon
o'qilmagan. Jadval o'zi hech narsani yiqitmaydi — ya'ni u jimgina
eskirishi mumkin va ikkala yo'nalishda ham eskirgan.

Fayl **yettita** narsani bog'laydi:

1. **Jadval va qoida paragrafi hujjatdan parse qilinadi** — ustun
   sarlavhalari, qatorlar, statuslar va «500 м Ташкента» soni.
   Reyestrda qo'lda ko'chirilgan nusxa yo'q (61-run sabog'i).
   Parserning o'zi sun'iy hujjatlarda tekshiriladi.
2. **Ikkala o'q mustaqil va kesishmasi majburiy** — `Standing` ni
   reyestrga qo'lda yozib qo'yib bo'lmaydi: `assess()` uni `Claim`
   (hujjatdan) va `Reach` (koddan) bilan taqqoslaydi va mos kelmagan
   har qanday juftlikni `ValueError` bilan to'xtatadi.
3. **Har bir dalil yechiladi** — `modul:simvol` haqiqiy Python
   obyektiga, `yo'l/fayl:token` esa repodagi faylga va uning
   matniga. «Kodda bor» degan da'vo matn bo'lib qolmaydi.
   `Reach.NONE` da dalil **bo'lmasligi** shart.
4. **`SURFACED` haqiqatga bog'lanadi** — banner `web/` da bor, lekin
   bildirishnoma matnini olib yurmasligi test ichida o'qiladi: agar
   kimdir `notify.*` kalitini `web/app.js` ga qo'shsa, bu fayl
   yiqiladi va reyestrni yangilashni talab qiladi.
5. **`BORROWED` haqiqatga bog'lanadi** — qorovul `USERS_ALLOWED_COLUMNS`
   **bugun** manzil ustunini to'sadi; agar kimdir ro'yxatga `email`
   yoki `phone` qo'shsa, uchta «Не входит» qatori qorovulsiz qoladi va
   fayl buni aytadi.
6. **Yetkazish qoidasining uchala bandi** — iqtibos hujjatda topilishi
   va bandning dalili kodda yechilishi shart.
7. **Teskari yo'nalish** — §19 da yo'q, kodda bor kunlik hisobot.

**Ataylab tekshirilmaydi:** `Обоснование` ustunining va `why`
matnlarining **mazmuni** (70-…73-run bilan bir xil qaror), faqat
uzunligi va bir nechta kalit tokeni.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from app.admin import security
from app.notifications import channels as ch
from app.notifications.channels import Claim, Reach, Standing

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"

#: Bu qatorlarni test **nom bilan** biladi, chunki ular haqidagi da'vo
#: har birida boshqacha tekshiriladi. Ro'yxatning **uzunligi** esa
#: hujjatdan keladi, ya'ni yangi qator jimgina qo'shila olmaydi.
TELEGRAM = "Telegram (in-bot)"
IN_APP = "In-App (веб-баннер)"
WEB_PUSH = "Web Push (PWA)"
EMAIL = "Email"
SMS = "SMS"
WHATSAPP = "WhatsApp"

#: `users` ga qo'shilsa manzil paydo bo'ladigan ustun nomlari. Ro'yxat
#: qora (blocklist) va bu **ataylab**: oq ro'yxat `USERS_ALLOWED_COLUMNS`
#: da, bu yerda esa savol boshqacha — «qaysi ustun kanalni ochib
#: yuborardi».
ADDRESS_COLUMN_HINTS: tuple[str, ...] = (
    "email",
    "e_mail",
    "mail",
    "phone",
    "phone_number",
    "msisdn",
    "whatsapp",
)


@pytest.fixture(scope="module")
def prd() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def table(prd: str) -> ch.ChannelTable:
    return ch.parse_table(prd)


@pytest.fixture(scope="module")
def report(prd: str) -> ch.Report:
    return ch.build_report(prd)


# ---------------------------------------------------------------------------
# 1. Parser haqiqatan parse qiladi
# ---------------------------------------------------------------------------

SYNTHETIC = """
## 19. Notifications

| Канал | Статус в регионе | Обоснование |
|---|---|---|
| Альфа | MVP | Первый |
| Бета | Не входит | Второй |

Правило доставки: при подтверждённом инциденте в радиусе подписки.
**Радиус подлежит калибровке отдельно** — 500 м Ташкента.

---

## 20. Security
"""


def test_parser_reads_a_synthetic_table() -> None:
    parsed = ch.parse_table(SYNTHETIC)
    assert parsed.columns == ("Канал", "Статус в регионе", "Обоснование")
    assert [row.channel for row in parsed.rows] == ["Альфа", "Бета"]
    assert parsed.rows[0].claim is Claim.SHIPPING
    assert parsed.rows[1].claim is Claim.EXCLUDED
    assert parsed.baseline_radius_m == 500
    assert "в радиусе подписки" in parsed.rule_text


def test_parser_stops_at_the_next_section() -> None:
    assert "Security" not in ch.section_text(SYNTHETIC)


def test_parser_rejects_an_unknown_column() -> None:
    broken = SYNTHETIC.replace("Обоснование", "Причина")
    with pytest.raises(ValueError, match="notanish ustun"):
        ch.parse_table(broken)


def test_parser_rejects_an_unknown_status() -> None:
    broken = SYNTHETIC.replace("| Альфа | MVP |", "| Альфа | Когда-нибудь |")
    with pytest.raises(ValueError, match="notanish status"):
        ch.parse_table(broken)


def test_parser_rejects_an_empty_rationale() -> None:
    broken = SYNTHETIC.replace("| Бета | Не входит | Второй |", "| Бета | Не входит |  |")
    with pytest.raises(ValueError, match="bo'sh"):
        ch.parse_table(broken)


def test_parser_requires_the_delivery_rule() -> None:
    broken = SYNTHETIC.replace(
        "Правило доставки: при подтверждённом инциденте в радиусе подписки.\n"
        "**Радиус подлежит калибровке отдельно** — 500 м Ташкента.",
        "",
    )
    with pytest.raises(ValueError, match="qoida"):
        ch.parse_table(broken)


def test_parser_requires_the_inherited_radius() -> None:
    broken = SYNTHETIC.replace("500 м Ташкента", "радиус наследуется")
    with pytest.raises(ValueError, match="meros radius"):
        ch.parse_table(broken)


def test_parser_rejects_a_missing_section() -> None:
    with pytest.raises(ValueError, match="bo'lim topilmadi"):
        ch.parse_table("## 18. Integrations\n")


def test_unknown_column_lookup_is_guarded() -> None:
    row = ch.ChannelRow("Х", "MVP", "Причина")
    with pytest.raises(ValueError, match="degan ustun yo'q"):
        row.cell("Тип")
    assert row.cell("Канал") == "Х"


# ---------------------------------------------------------------------------
# 2. Hujjatning haqiqiy jadvali
# ---------------------------------------------------------------------------


def test_the_real_table_has_six_rows(table: ch.ChannelTable) -> None:
    assert len(table.rows) == 6
    assert [row.channel for row in table.rows] == [
        TELEGRAM,
        IN_APP,
        WEB_PUSH,
        EMAIL,
        SMS,
        WHATSAPP,
    ]


def test_the_document_declares_two_mvp_channels(report: ch.Report) -> None:
    """Bu butun faylning tayanchi: MVP **ikki** kanalli deb yozilgan."""
    shipping = report.by_claim(Claim.SHIPPING)
    assert {f.channel for f in shipping} == {TELEGRAM, IN_APP}


def test_every_row_is_assessed(report: ch.Report) -> None:
    assert len(report.findings) == 6
    assert set(ch.ASSESSMENT_BY_CHANNEL) == {f.channel for f in report.findings}


def test_an_unassessed_row_stops_the_report() -> None:
    extra = SYNTHETIC.replace(
        "| Бета | Не входит | Второй |",
        "| Бета | Не входит | Второй |\n| Гамма | MVP | Третий |",
    )
    with pytest.raises(ValueError, match="topilmadi|baholanmagan"):
        ch.build_report(extra)


def test_an_orphan_assessment_stops_the_report(prd: str) -> None:
    """Teskari tomon: jadvaldan qator yo'qolsa, uning bahosi qolib ketmasin.

    Qatorni hujjatdan olib tashlash — eng jim o'zgarish: hisobot
    qisqaradi, hamma tekshiruv yashil qoladi va reyestrda kimsasiz baho
    qoladi. Shuning uchun `build_report` uni `ValueError` bilan
    to'xtatadi.
    """
    broken = prd.replace("| WhatsApp | Не входит | Нет подтверждённого спроса |\n", "")
    assert broken != prd
    with pytest.raises(ValueError, match="jadvalda yo'q kanal"):
        ch.build_report(broken)


def test_every_why_is_written(report: ch.Report) -> None:
    for finding in report.findings:
        assert len(finding.assessment.why) > 120, finding.channel


# ---------------------------------------------------------------------------
# 3. Ikkala o'q mustaqil va kesishmasi majburiy
# ---------------------------------------------------------------------------


def _row(channel: str, status: str) -> ch.ChannelRow:
    return ch.ChannelRow(channel, status, "Причина")


def test_a_shipping_row_cannot_be_empty_in_code() -> None:
    assessment = ch.Assessment(
        channel="Х", reach=Reach.NONE, standing=Standing.UNHELD, why="izoh " * 40
    )
    with pytest.raises(ValueError, match="kodda hech narsa yo'q"):
        ch.assess(_row("Х", "MVP"), assessment)


def test_a_scheduled_row_cannot_already_deliver() -> None:
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.DELIVERS,
        standing=Standing.PREMATURE,
        evidence=("app.notifications.channels:SPEC",),
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="allaqachon bir narsa bor"):
        ch.assess(_row("Х", "Phase 2"), assessment)


def test_a_scheduled_row_must_be_premature() -> None:
    assessment = ch.Assessment(
        channel="Х", reach=Reach.NONE, standing=Standing.UNHELD, why="izoh " * 40
    )
    with pytest.raises(ValueError, match="PREMATURE"):
        ch.assess(_row("Х", "Phase 2"), assessment)


def test_an_excluded_row_cannot_be_premature() -> None:
    assessment = ch.Assessment(
        channel="Х", reach=Reach.NONE, standing=Standing.PREMATURE, why="izoh " * 40
    )
    with pytest.raises(ValueError, match="siyosat, kelajak fazasi emas"):
        ch.assess(_row("Х", "Не входит"), assessment)


def test_a_shipping_row_cannot_be_premature() -> None:
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.DELIVERS,
        standing=Standing.PREMATURE,
        evidence=("app.notifications.channels:SPEC",),
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="bugun rost bo'lishi kerak"):
        ch.assess(_row("Х", "MVP"), assessment)


def test_borrowed_is_only_available_to_a_policy_row() -> None:
    """Modulning eng nozik qoidasi, va u tasodifiy emas.

    Mavjudlik da'vosi kod **o'chirilganda** buziladi va uni ushlaydigan
    test o'sha kanal haqida yozilgan bo'ladi; yo'qlik da'vosi kod
    **qo'shilganda** buziladi va mavjud bo'lmagan narsa haqida hech kim
    test yozmaydi — demak qorovul doim birovniki.
    """
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.DELIVERS,
        standing=Standing.BORROWED,
        borrowed_from="01 §20",
        guard=("app.notifications.channels:SPEC",),
        evidence=("app.notifications.channels:SPEC",),
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="faqat «Не входит»"):
        ch.assess(_row("Х", "MVP"), assessment)


def test_borrowed_needs_a_source_section() -> None:
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.NONE,
        standing=Standing.BORROWED,
        guard=("app.notifications.channels:SPEC",),
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="manba bo'lim ko'rsatilmagan"):
        ch.assess(_row("Х", "Не входит"), assessment)


def test_a_source_section_without_borrowed_is_rejected() -> None:
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.NONE,
        standing=Standing.UNHELD,
        borrowed_from="01 §20",
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="manba bo'lim ko'rsatilgan"):
        ch.assess(_row("Х", "Не входит"), assessment)


@pytest.mark.parametrize("standing", [Standing.HELD, Standing.BORROWED])
def test_a_held_row_needs_a_guard(standing: Standing) -> None:
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.NONE,
        standing=standing,
        borrowed_from="01 §20" if standing is Standing.BORROWED else None,
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="qorovul yo'q"):
        ch.assess(_row("Х", "Не входит"), assessment)


def test_an_unheld_row_cannot_carry_a_guard() -> None:
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.NONE,
        standing=Standing.UNHELD,
        guard=("app.notifications.channels:SPEC",),
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="qorovul ko'rsatilgan"):
        ch.assess(_row("Х", "Не входит"), assessment)


def test_evidence_is_required_unless_nothing_exists() -> None:
    assessment = ch.Assessment(
        channel="Х", reach=Reach.DELIVERS, standing=Standing.UNHELD, why="izoh " * 40
    )
    with pytest.raises(ValueError, match="dalil yo'q"):
        ch.assess(_row("Х", "MVP"), assessment)


def test_nothing_means_nothing() -> None:
    """Dalilsiz «yo'q» va dalilli «yo'q» bir xil ko'rinmasligi kerak."""
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.NONE,
        standing=Standing.UNHELD,
        evidence=("app.notifications.channels:SPEC",),
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="lekin dalil ko'rsatilgan"):
        ch.assess(_row("Х", "Не входит"), assessment)


@pytest.mark.parametrize(
    ("surfaced_as", "carries"),
    [
        (None, None),
        ("web/index.html:banner", None),
        (None, "нечто"),
    ],
)
def test_surfaced_needs_the_artifact_and_its_payload(
    surfaced_as: str | None, carries: str | None
) -> None:
    """Ikkala maydon ham majburiy, **alohida**.

    Faqat ikkalasi yo'qligini o'lchash `or` ni `and` ga aylantirishni
    o'tkazib yuborardi: artefaktni ko'rsatib, uning yukini
    ko'rsatmaslik `SURFACED` ni yana tekshirib bo'lmaydigan qilardi —
    «banner bor» degan gap o'zi hech narsa demaydi.
    """
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.SURFACED,
        standing=Standing.UNHELD,
        evidence=("app.notifications.channels:SPEC",),
        surfaced_as=surfaced_as,
        carries=carries,
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="artefakt yoki"):
        ch.assess(_row("Х", "MVP"), assessment)


def test_an_artifact_without_surfaced_is_rejected() -> None:
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.DELIVERS,
        standing=Standing.UNHELD,
        evidence=("app.notifications.channels:SPEC",),
        surfaced_as="web/index.html:banner",
        carries="нечто",
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="artefakt ko'rsatilgan"):
        ch.assess(_row("Х", "MVP"), assessment)


def test_an_excluded_row_cannot_be_surfaced() -> None:
    """Bitta qoida ikkita holatni to'sadi — ikkinchi shart yozilmagan.

    `SURFACED` ham `Reach.NONE` emas, ya'ni «Не входит» qatori uchun
    uni alohida taqiqlash **o'lik** shart bo'lardi va uni olib tashlash
    hech qayerda sezilmasdi. Test shu qarorni qayd etadi: xabar
    umumiy, sabab esa aynan artefaktning mavjudligi.
    """
    assessment = ch.Assessment(
        channel="Х",
        reach=Reach.SURFACED,
        standing=Standing.UNHELD,
        evidence=("app.notifications.channels:SPEC",),
        surfaced_as="web/index.html:banner",
        carries="нечто",
        why="izoh " * 40,
    )
    with pytest.raises(ValueError, match="kodda bir narsa bor"):
        ch.assess(_row("Х", "Не входит"), assessment)


def test_a_mismatched_assessment_is_rejected() -> None:
    assessment = ch.ASSESSMENT_BY_CHANNEL[EMAIL]
    with pytest.raises(ValueError, match="bahosi berildi"):
        ch.assess(_row("Х", "Не входит"), assessment)


def test_an_empty_why_is_rejected() -> None:
    assessment = ch.Assessment(
        channel="Х", reach=Reach.NONE, standing=Standing.UNHELD, why="   "
    )
    with pytest.raises(ValueError, match="izoh yo'q"):
        ch.assess(_row("Х", "Не входит"), assessment)


# ---------------------------------------------------------------------------
# 4. Dalillar yechiladi
# ---------------------------------------------------------------------------


def _resolve(ref: str) -> object:
    """`modul:simvol` → obyekt; `yo'l/fayl:token` → faylning matni.

    Ikkinchi shakl kerak, chunki §19 ning bitta kanali umuman Python
    emas: «веб-баннер» `web/` dagi statik fayllarda yashaydi va uni
    import qilib bo'lmaydi.
    """
    head, _, tail = ref.partition(":")
    assert tail, f"dalilda `:` yo'q: {ref}"
    if "/" in head:
        path = SVETA_ROOT / head
        assert path.exists(), ref
        text = path.read_text(encoding="utf-8")
        assert tail in text, ref
        return text
    module = importlib.import_module(head)
    assert hasattr(module, tail), ref
    return getattr(module, tail)


def test_every_evidence_reference_resolves(report: ch.Report) -> None:
    seen = 0
    for finding in report.findings:
        for ref in finding.assessment.evidence:
            _resolve(ref)
            seen += 1
        for ref in finding.assessment.guard:
            _resolve(ref)
            seen += 1
    for clause in report.clauses:
        for ref in clause.evidence:
            _resolve(ref)
            seen += 1
    for entry in ch.UNDECLARED:
        for ref in entry.evidence:
            _resolve(ref)
            seen += 1
    assert seen >= 20


def test_the_resolver_actually_fails_on_a_bad_reference() -> None:
    with pytest.raises(AssertionError):
        _resolve("app.notifications.channels:NO_SUCH_SYMBOL")
    with pytest.raises(AssertionError):
        _resolve("web/app.js:no_such_token_anywhere")
    with pytest.raises(AssertionError):
        _resolve("web/no_such_file.js:x")


# ---------------------------------------------------------------------------
# 5. `DELIVERS` — Telegram yo'li haqiqatan to'liq
# ---------------------------------------------------------------------------


def test_telegram_is_the_only_delivering_channel(report: ch.Report) -> None:
    assert [f.channel for f in report.delivering] == [TELEGRAM]


def test_the_confirmed_topic_is_the_only_entry_to_the_outbox() -> None:
    from app.clustering import service as clustering_service
    from app.notifications import events

    assert set(clustering_service.NOTIFIABLE_TOPICS.values()) == set(events.TOPICS)
    assert events.TOPIC_CONFIRMED in clustering_service.NOTIFIABLE_TOPICS.values()


def test_the_transport_is_reachable_from_the_registry() -> None:
    from app.notifications.sender import Sender

    sender = _resolve("app.bot.notifier:TelegramSender")
    assert hasattr(sender, "send")
    assert hasattr(Sender, "send")


# ---------------------------------------------------------------------------
# 6. `SURFACED` — banner bor, lekin bildirishnomani olib yurmaydi
# ---------------------------------------------------------------------------


def test_the_banner_artifact_exists(report: ch.Report) -> None:
    finding = next(f for f in report.findings if f.channel == IN_APP)
    assert finding.reach is Reach.SURFACED
    _resolve(finding.assessment.surfaced_as or "")


def test_the_banner_does_not_carry_a_notification() -> None:
    """Eng jim topilmaning tripwire i.

    Banner mahsulotda bor va qidiruv uni topadi, lekin unga faqat
    xarita diagnostikasi chiqadi. Agar kimdir `notify.*` kalitini
    `web/` ga olib kirsa, bu test yiqiladi va reyestrni yangilashni
    talab qiladi — ya'ni `SURFACED` `DELIVERS` ga jimgina aylanmaydi.
    """
    web_text = "\n".join(
        (SVETA_ROOT / "web" / name).read_text(encoding="utf-8")
        for name in ("app.js", "index.html")
    )
    assert "banner" in web_text
    assert "notify." not in web_text, (
        "`web/` bildirishnoma kalitini oldi — `01` §19 ning In-App qatori "
        "endi `SURFACED` emas; reyestrni yangilang"
    )


def test_the_web_has_no_user_identity() -> None:
    """Qoidani vebda bajarib bo'lmasligining sababi.

    Obuna `users.tg_id` ga bog'langan va faqat bot orqali yaratiladi;
    vebda foydalanuvchi identifikatori yo'q va `01` §20 ga ko'ra
    bo'lmaydi. Shuning uchun «в радиусе подписки» In-App kanalida
    ma'noga ega emas.
    """
    from app.notifications.models import Subscription

    assert "user_id" in Subscription.__table__.c
    web_text = "\n".join(
        (SVETA_ROOT / "web" / name).read_text(encoding="utf-8")
        for name in ("app.js", "index.html")
    )
    for token in ("tg_id", "subscription", "user_id"):
        assert token not in web_text, f"`web/` da `{token}` paydo bo'ldi"


def test_the_notification_row_has_no_channel_column() -> None:
    """`SURFACED` topilmasining ikkinchi yarmi — sxemadagi narx.

    §19 ikki kanalli MVP e'lon qiladi, `notifications` esa bir hodisa
    uchun bitta qator beradi (`UNIQUE (user_id, outage_id)`, `05` §2.4)
    va kanal ustuni yo'q. Ya'ni ikkinchi kanal migratsiyasiz
    qo'shilmaydi. Test bugungi holatni **qayd etadi**: ustun paydo
    bo'lsa, reyestrdagi izoh eskiradi.
    """
    from app.notifications.models import Notification

    columns = set(Notification.__table__.c.keys())
    assert "channel" not in columns
    uniques = {
        tuple(sorted(col.name for col in c.columns))
        for c in Notification.__table__.constraints
        if c.__class__.__name__ == "UniqueConstraint"
    }
    assert ("outage_id", "user_id") in uniques


# ---------------------------------------------------------------------------
# 7. `BORROWED` — uchta qator, bitta qorovul, to'rtinchi sabab
# ---------------------------------------------------------------------------


def test_all_three_excluded_rows_are_borrowed(report: ch.Report) -> None:
    borrowed = report.by_standing(Standing.BORROWED)
    assert {f.channel for f in borrowed} == {EMAIL, SMS, WHATSAPP}


def test_the_three_rows_share_one_guard(report: ch.Report) -> None:
    """Topilmaning o'zi: uchta sabab, bitta mexanizm."""
    guards = {f.assessment.guard for f in report.by_standing(Standing.BORROWED)}
    assert len(guards) == 1
    assert guards == {("app.admin.security:USERS_ALLOWED_COLUMNS",)}
    sources = {f.assessment.borrowed_from for f in report.by_standing(Standing.BORROWED)}
    assert sources == {"01 §20 «ПДн не собираются»"}


def test_the_document_gives_three_different_reasons(table: ch.ChannelTable) -> None:
    """Hujjat uchta boshqa sababni keltiradi — qorovul esa to'rtinchisini."""
    rationales = {
        table.row(name).rationale  # type: ignore[union-attr]
        for name in (EMAIL, SMS, WHATSAPP)
    }
    assert len(rationales) == 3


def test_the_guard_really_blocks_an_address_column() -> None:
    """Qorovul **bugun** ishlayotganini o'lchaydi, tasvirlamaydi."""
    allowed = security.USERS_ALLOWED_COLUMNS
    leaked = sorted(name for name in ADDRESS_COLUMN_HINTS if name in allowed)
    assert leaked == [], (
        f"`users` ga manzil ustuni ruxsat etildi: {leaked} — `01` §19 ning "
        "uchta «Не входит» qatori endi qorovulsiz"
    )


def test_the_users_table_carries_no_address_column() -> None:
    from app.reports.models import User

    columns = set(User.__table__.c.keys())
    assert columns & set(ADDRESS_COLUMN_HINTS) == set()
    assert columns <= set(security.USERS_ALLOWED_COLUMNS)


def test_no_transport_for_the_excluded_channels() -> None:
    """Kodda email/SMS/WhatsApp transporti umuman yo'q.

    Reyestrning o'zi chetlab o'tiladi: u kanallarni **nomlaydi** va
    o'zini topib yiqilardi. Chetlab o'tish bitta fayl bilan cheklangan
    va ro'yxat bo'sh emasligi quyida o'lchanadi, aks holda skanerni
    butunlay o'chirib qo'yish sezilmasdi.
    """
    app_root = SVETA_ROOT / "app"
    tokens = ("smtplib", "aiosmtplib", "sendgrid", "twilio", "whatsapp")
    scanned = 0
    hits: list[str] = []
    for path in sorted(app_root.rglob("*.py")):
        if path.name == "channels.py" and path.parent.name == "notifications":
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8").lower()
        hits.extend(f"{path.name}:{token}" for token in tokens if token in text)
    assert scanned > 50, "skaner hech narsani ko'rmadi"
    assert hits == [], hits


# ---------------------------------------------------------------------------
# 8. `PREMATURE` — Web Push
# ---------------------------------------------------------------------------


def test_web_push_is_premature(report: ch.Report) -> None:
    finding = next(f for f in report.findings if f.channel == WEB_PUSH)
    assert finding.claim is Claim.SCHEDULED
    assert finding.reach is Reach.NONE
    assert finding.standing is Standing.PREMATURE
    assert finding.assessment.guard == ()


def test_the_product_still_has_no_service_worker() -> None:
    web = SVETA_ROOT / "web"
    assert not (web / "manifest.json").exists()
    assert not (web / "sw.js").exists()
    text = "\n".join(p.read_text(encoding="utf-8") for p in web.glob("*.js"))
    for token in ("serviceWorker", "pushManager", "vapid", "VAPID"):
        assert token not in text, token


# ---------------------------------------------------------------------------
# 9. Yetkazish qoidasi
# ---------------------------------------------------------------------------


def test_every_clause_is_quoted_from_the_document(report: ch.Report) -> None:
    assert len(report.clauses) == 3
    for clause in report.clauses:
        assert clause.quote in report.table.rule_text


def test_a_missing_quote_stops_the_report(prd: str) -> None:
    broken = prd.replace("в радиусе подписки", "в зоне обслуживания")
    with pytest.raises(ValueError, match="topilmadi"):
        ch.build_report(broken)


def test_the_radius_is_calibratable_per_region() -> None:
    from app.notifications import params

    assert params.KEY_DEFAULT_RADIUS.startswith("notify.")
    assert params.KEY_MAX_RADIUS.startswith("notify.")
    seeded = params.seed_values()
    assert set(seeded) == {params.KEY_DEFAULT_RADIUS, params.KEY_MAX_RADIUS}


def test_the_shipped_default_is_still_the_inherited_number(table: ch.ChannelTable) -> None:
    """Mexanizm bor, qiymat esa hali Toshkentniki.

    Hujjatning o'zi «могут не соответствовать» deydi, ya'ni bu son
    o'lchanmagan. `region_config` bo'sh bo'lganda aynan u ishlaydi.
    Test uni **tuzatmaydi** — E11 gacha tuzatib bo'lmaydi — lekin
    kalibrlash bo'lganda bu fayl yiqiladi va qayd etilishini talab
    qiladi.
    """
    from app.notifications.params import bootstrap

    assert bootstrap().default_radius_m == table.baseline_radius_m


# ---------------------------------------------------------------------------
# 10. Teskari yo'nalish
# ---------------------------------------------------------------------------


def test_the_daily_digest_is_not_declared(report: ch.Report, table: ch.ChannelTable) -> None:
    assert len(report.undeclared) == 1
    entry = report.undeclared[0]
    assert entry.audience == "DIGEST_CHAT_IDS"
    for row in table.rows:
        assert entry.name not in row.channel


def test_the_digest_uses_the_same_transport_but_another_audience() -> None:
    from app.jobs import daily_digest
    from app.notifications.sender import Sender

    assert daily_digest.Sender is Sender
    assert callable(daily_digest.chat_ids)
    assert daily_digest.chat_ids("1, 2") == [1, 2]


# ---------------------------------------------------------------------------
# 11. Xulosa
# ---------------------------------------------------------------------------


def test_the_section_does_not_describe_todays_code(report: ch.Report) -> None:
    """Bugungi javob: `False`, va uchala sabab ham mavjud.

    Bu test «tuzatilishi kerak» degani emas — uchala sabab ham hujjat
    yoki mahsulot qaroriga bog'liq (70-, 71-, 73-run bilan bir xil
    holat). U javobni **qayd etadi**: biror sabab yo'qolganda fayl
    yiqiladi va reyestrni yangilashni talab qiladi.
    """
    assert report.accurate is False
    assert {f.channel for f in report.overstated} == {IN_APP}
    assert {f.channel for f in report.unguarded} == {EMAIL, SMS, WHATSAPP}
    assert len(report.undeclared) == 1


def test_the_counts_are_what_the_registry_says(report: ch.Report) -> None:
    assert report.counts == {
        "held": 1,
        "borrowed": 3,
        "unheld": 1,
        "premature": 1,
    }


def test_accuracy_needs_all_three_conditions(report: ch.Report) -> None:
    """Formuladan bitta shartni olib tashlash bugungi javobni saqlamasin.

    71- va 72-run ning survivori aynan shu edi: uchta shartdan
    ikkitasini olib tashlash `accurate` ni o'zgartirmasdi, chunki
    uchinchisi baribir `False` berardi.
    """
    empty = ch.Report(findings=(), table=report.table, clauses=(), undeclared=())
    assert empty.accurate is True

    only_undeclared = ch.Report(
        findings=(), table=report.table, clauses=(), undeclared=ch.UNDECLARED
    )
    assert only_undeclared.accurate is False

    overstated_only = ch.Report(
        findings=tuple(f for f in report.findings if f.channel == IN_APP),
        table=report.table,
        clauses=(),
        undeclared=(),
    )
    assert overstated_only.accurate is False

    unguarded_only = ch.Report(
        findings=tuple(f for f in report.findings if f.channel == EMAIL),
        table=report.table,
        clauses=(),
        undeclared=(),
    )
    assert unguarded_only.accurate is False

    held_only = ch.Report(
        findings=tuple(f for f in report.findings if f.channel == TELEGRAM),
        table=report.table,
        clauses=(),
        undeclared=(),
    )
    assert held_only.accurate is True

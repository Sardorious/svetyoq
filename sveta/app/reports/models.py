"""Foydalanuvchi va xabar modellari (`05` §2.2).

Ikkita muhim qaror shu jadvalda:

1. **`district_id` yozish paytida biriktiriladi**, so'rov paytida hisoblanmaydi.
   Chegara keyinchalik o'zgarsa, tarixiy xabar o'z tumanida qoladi.
2. **`geom_exact` va `geom_public` ajratilgan.** Aniq koordinata hech qachon
   API dan chiqmaydi (`05` §7.3) va 90 kundan keyin `NULL` ga o'tkaziladi
   (`05` §3.2) — shuning uchun ustun `nullable`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.db.spatial import point
from app.reports.sources import DEFAULT_SOURCE_CODE

#: `reports.kind` uchun ruxsat etilgan qiymatlar (`05` §2.2).
REPORT_KINDS: tuple[str, ...] = ("outage", "restored")


class ReportSource(Base):
    """Xabar manbai va ishonch og'irligi (`06` §2).

    Og'irliklar E11 da sozlanadi, shuning uchun ular jadvalda. Boshlang'ich
    qatorlar `app.reports.sources.SOURCES` da va migratsiya `0003` shu
    ro'yxatdan seed qiladi — ikki joyda qo'lda yozilgan ro'yxat ajralib
    ketardi.
    """

    __tablename__ = "report_sources"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    weight: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    is_authoritative: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class User(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    language: Mapped[str] = mapped_column(Text, nullable=False, server_default="uz")
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=True
    )
    trust_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="50")
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Report(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_geom_public", "geom_public", postgresql_using="gist"),
        # `05` §3.2 va §8 — `purge_exact_geom` **ataylab** mintaqasiz:
        # maxfiylik muddati butun bazaga tegishli. Shu sabab mintaqali
        # indeks qo'shilgandan keyin ham qoldirildi.
        Index("ix_reports_created_at", text("created_at DESC")),
        Index("ix_reports_outage_id", "outage_id"),
        Index("ix_reports_user_id_created_at", "user_id", text("created_at DESC")),
        # `01` NFR-S-02 — mintaqa bo'yicha filtr **indeks darajasida**.
        # `reports` ustidagi deyarli har bir so'rov «mintaqa + oyna»
        # ko'rinishida (`0008` migratsiyasida ro'yxati). Usiz ular
        # `ix_reports_created_at` ga tushib, qo'shni mintaqaning oynadagi
        # qatorlarini ham o'qirdi.
        Index("ix_reports_region_id_created_at", "region_id", text("created_at DESC")),
        # TZ §2.1 — sanash so'rovi «katak + oyna» ko'rinishida: uy
        # darajasi (r10) har bir tasdiqlash tekshiruvida o'qiladi.
        # Mintaqasiz: `h3_r10` ning o'zi mintaqani ham ajratadi, lekin
        # oyna filtri `created_at` bo'yicha kelgani uchun ikkinchi
        # ustun o'sha.
        Index("ix_reports_h3_r10_created_at", "h3_r10", text("created_at DESC")),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    # HECH QACHON ommaga chiqmaydi. 90 kundan keyin NULL ga o'tkaziladi.
    geom_exact = mapped_column(point(), nullable=True)
    geom_public = mapped_column(point(), nullable=False)
    h3_r9: Mapped[str] = mapped_column(Text, nullable=False)
    # TZ §1 — to'rt daraja bir vaqtda. Eski qatorlarda ular yo'q
    # (`geom_exact` 90 kundan keyin `NULL` ga o'tadi, ya'ni orqaga
    # to'ldirish har doim ham mumkin emas), shuning uchun `nullable`.
    # Yangi har bir xabar to'rtalasini ham to'ldiradi.
    h3_r7: Mapped[str | None] = mapped_column(Text, nullable=True)
    h3_r8: Mapped[str | None] = mapped_column(Text, nullable=True)
    h3_r10: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: §1.1 — «turli manzil» ning yaqinlashuvi (~50 m). Zona emas.
    h3_r11: Mapped[str | None] = mapped_column(Text, nullable=True)
    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    district_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("districts.id"), nullable=True
    )
    mahalla_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("mahallas.id"), nullable=True
    )
    outage_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("outages.id"), nullable=True
    )
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default="bot")
    # `06` §10. `source` (`05` §2.2) erkin matn edi; `source_code` — registrga
    # bog'langan kalit. Ikkalasi ham qoldirildi, chunki `06` §10 `ALTER TABLE
    # ADD COLUMN source_code` deydi, mavjud ustunni almashtirishni emas.
    # Standart registrdan olinadi: `get_source` noma'lum kodni o'shanga
    # tushiradi, shuning uchun ustunning standarti undan ajralib qolmasin.
    source_code: Mapped[str] = mapped_column(
        Text,
        ForeignKey("report_sources.code"),
        nullable=False,
        server_default=DEFAULT_SOURCE_CODE,
    )
    # Yozish paytida qotiriladi (`06` §10): `source.weight × user_factor`.
    # Qotirilmagan qiymat auditni imkonsiz qiladi — izoh `app.reports.sources` da.
    weight: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    # Telegram update id — idempotentlik kafolati (`05` §6.3).
    tg_update_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TzSource(Base):
    """Ro'yxatdan o'tgan tashqi manba (TZ §11/7, §8).

    `app.reports.tzsensor.Source` ning **bazadagi** ko'rinishi. Toza
    modul reyestrning shaklini va qoidalarini biladi, lekin uni
    qayerda saqlashni bilmaydi — bu jadval o'sha bo'shliqni to'ldiradi.

    **Nima uchun `report_sources` emas.** `report_sources` (`06` §2) —
    xabarning **og'irligi**: bot, veb, import. TZ ning manbasi esa
    og'irlikda qatnashmaydi umuman: В-7 bo'yicha u kvartalni **darhol**
    yopadi, ya'ni §2.1 ning porogini aylanib o'tadi. Ikkalasini bitta
    jadvalga qo'shish og'irlik ustunini datchik uchun ma'nosiz qilardi
    va «rasmiy manba — bu shunchaki og'irroq foydalanuvchi» degan
    yolg'onni sxemaga yozib qo'yardi.

    **Reyestr o'zgaradi, jurnal — yo'q.** Bu jadvalda `UPDATE` ruxsat:
    §8 ning operatori buzuq qurilmadan ishonchni olib qo'yishi kerak
    (`trusted = false`), va bu holat o'zgarishi, tarix emas. Т-2 ning
    faqat-qo'shiladigan taqiqi `tz_signals` ga tegishli.

    🔴 **Birlamchi kalit — `(region_id, source_id)`.** Dastlab u faqat
    `source_id` edi va haqiqiy bazada darhol yiqildi: ikkita mintaqada
    bir xil identifikatorli qurilma bo'lishi mumkin, `source_id` esa
    yetkazib beruvchi bergan nom — u global yagona bo'lishga va'da
    bermaydi. `region_config` (`(region_id, key)`) bilan bir xil shakl,
    va `01` NFR-S-02 ni ham qondiradi: kalitning **birinchi** ustuni
    mintaqa, ya'ni alohida indeks kerak emas.
    """

    __tablename__ = "tz_sources"
    __table_args__ = (
        # `Channel` ning uchala qiymati. Nom faqat oxirgi bo'lak:
        # konvensiya `ck_%(table_name)s_%(constraint_name)s` ni qo'shadi.
        CheckConstraint("channel IN ('sensor', 'operator', 'feed')", name="channel"),
        # `Source.__post_init__` ning aynan o'zi, faqat bazada. Datchikning
        # katagi reyestrda qotirilgan (aks holda bitta buzuq qurilma
        # shaharning istalgan kvartalini В-7 bo'yicha yopa olardi);
        # operator va kanal uchun katak **xabarda** keladi, ya'ni bu
        # yerda u bo'lmasligi shart.
        #
        # 🔴 **`cell IS NOT NULL` ni tushirib qoldirib bo'lmaydi.**
        # Birinchi variantda u yo'q edi va cheklov katagi yozilmagan
        # datchikni **qabul qilardi**: `btrim(NULL) <> ''` `NULL`
        # beradi, `NULL OR false` ham `NULL`, `CHECK` esa `NULL` ni
        # «buzilmagan» deb o'qiydi. Nosozlik faqat haqiqiy bazada
        # ko'rindi — qoida yozilgan edi, lekin hech qachon otilmasdi.
        CheckConstraint(
            "(channel = 'sensor' AND cell IS NOT NULL AND btrim(cell) <> '') "
            "OR (channel <> 'sensor' AND cell IS NULL)",
            name="cell",
        ),
    )

    # Tartib ahamiyatli: birlamchi kalitning **birinchi** ustuni mintaqa,
    # ya'ni «butun reyestrni mintaqa bo'yicha o'qish» so'rovi shu indeksga
    # tushadi va `01` NFR-S-02 uchun alohida indeks kerak emas.
    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), primary_key=True
    )
    source_id: Mapped[str] = mapped_column(Text, primary_key=True)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    #: `sensor` uchun majburiy: qurilma o'rnatilgan kvartal (r9).
    cell: Mapped[str | None] = mapped_column(Text, nullable=True)
    trusted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TzSignal(Base):
    """Kirgan har bir xabar va uning taqdiri — faqat qo'shiladi (Т-2).

    Т-2: «Журнал сообщений и настроек — только добавление. Изменение и
    удаление запрещены **на уровне базы**». `config_journal` sozlamalar
    yarmini yopgan edi, bu jadval — xabarlar yarmini.

    🔴 **Rad etilgan xabar ham yoziladi.** Uchta sabab:

    1. §8 ning operatori buzuq qurilmani **ko'rishi** kerak
       (`Rejection.to_operator`); javobda qaytarilgan va unutilgan rad
       etish hech kimga yetib bormaydi;
    2. Т-7 ning kaliti faqat qabul qilingan qatordan olinadi, lekin
       «nega qabul qilinmadi» savoliga javob boshqa hech qayerda yo'q;
    3. `accepted` va `reason` bitta qatorda turgani uchun ular
       **ajralib keta olmaydi** — buni baza cheklovi ushlab turadi.

    🔴 **`source_id` da tashqi kalit yo'q.** Reyestrda bo'lmagan manba
    ham jurnalga tushadi (`unknown_source`) — aynan o'sha qator eng
    qiziq: kimdir ro'yxatdan o'tmagan identifikator bilan yozyapti.
    `FOREIGN KEY` bilan bu qator **yozilmasdi** va hujum izsiz qolardi.
    """

    __tablename__ = "tz_signals"
    __table_args__ = (
        # Ikkita da'vo bitta qatorda: «qabul qilindi» va «sababi yo'q».
        # Ular ajralsa jurnal o'zi haqida yolg'on gapirardi.
        CheckConstraint("accepted = (reason = 'none')", name="reason"),
        # Qabul qilingan qatorning Т-7 kaliti **har doim** bor: quyidagi
        # yagona indeks aynan shunga tayanadi (`NULL` lar unga kirmaydi).
        CheckConstraint("NOT accepted OR key IS NOT NULL", name="key"),
        # Т-7 **bazada**: bitta kalit ikkinchi marta fakt bo'la olmaydi.
        # Qisman — rad etilgan takror qator o'sha kalit bilan yozilaveradi.
        #
        # 🔴 **Mintaqa kalitning ichida emas, indeksda.** `dedup_key()`
        # `(manba|signal|katak|vaqt)` dan quriladi va mintaqani bilmaydi
        # — bilishi ham shart emas, chunki manba reyestri mintaqaga
        # tegishli. Global yagona indeks esa ikkita shaharning bir xil
        # nomli qurilmasini to'qnashtirardi va ikkinchi shaharning
        # xabari sababsiz yo'qolardi. Bu haqiqiy bazada topildi:
        # bazasiz to'plamda ikkala test ham o'tardi.
        Index(
            "ix_tz_signals_region_id_key_accepted",
            "region_id",
            "key",
            unique=True,
            postgresql_where=text("accepted"),
        ),
        # Operator paneli va `seen` oynasi: mintaqa + vaqt.
        Index("ix_tz_signals_region_id_at", "region_id", text("at DESC")),
        # Manbaning oxirgi holati (`REPEAT`/`FLAPPING`): mintaqa ichida
        # har manba bo'yicha oxirgi qator.
        Index("ix_tz_signals_region_id_source_id_at", "region_id", "source_id", text("at DESC")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    #: Xabar **da'vo qilgan** identifikator, tasdiqlangani emas.
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    #: Reyestrdan; manba topilmagan bo'lsa `NULL`.
    channel: Mapped[str | None] = mapped_column(Text, nullable=True)
    signal: Mapped[str] = mapped_column(Text, nullable=False)
    #: Fakt tegishli bo'lgan kvartal. Katak qoidasi buzilgan bo'lsa `NULL`.
    cell: Mapped[str | None] = mapped_column(Text, nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: §8: «на основании чего». Bo'sh bo'la olmaydi — `Reading` da tekshiriladi.
    reference: Mapped[str] = mapped_column(Text, nullable=False)
    #: §8: «кто». `operator` kanalida majburiy.
    actor: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    #: `Reject` ning qiymati; qabul qilingan qatorda `none`.
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    #: Т-7 ning `blake2b` kaliti. Katak aniqlanmagan qatorda `NULL`.
    key: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

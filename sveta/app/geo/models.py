"""Hudud va chegara modellari (`05` §2.1).

Bu jadvallarga faqat `app.geo` moduli to'g'ridan-to'g'ri murojaat qiladi
(`05` §1). Boshqa modullar `app.geo` funksiyalari orqali ishlaydi.

**Chegara versiyalash qoidasi.** Chegara o'zgarganda eski qator `valid_to`
bilan yopiladi, yangisi qo'shiladi. Eski qator hech qachon o'chirilmaydi va
tahrirlanmaydi — aks holda tarixiy statistika siljiydi.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.db.spatial import multipolygon, point
from app.geo.bbox import BBox, make_bbox


class Region(UUIDPrimaryKeyMixin, Base):
    """Mintaqa (`05` §2.1) + E19 da qo'shilgan bbox.

    bbox ustunlari `05` §2.1 DDL sida yo'q. Ular E19 uchun qo'shildi:
    chiqish mezoni «ikkinchi mintaqa **kodsiz** ishga tushadi», bbox esa
    shu paytgacha `app/geo/bbox.py` dagi lug'atda edi. Batafsil sabab —
    `0005_region_bbox.py` migratsiyasida.
    """

    __tablename__ = "regions"
    __table_args__ = (
        # «Hammasi yoki hech biri» — yarim to'ldirilgan bbox jim yolg'on
        # bo'lardi. Matn migratsiyadagi bilan bir xil.
        CheckConstraint(
            "(bbox_min_lat IS NULL AND bbox_min_lon IS NULL"
            " AND bbox_max_lat IS NULL AND bbox_max_lon IS NULL)"
            " OR (bbox_min_lat IS NOT NULL AND bbox_min_lon IS NOT NULL"
            " AND bbox_max_lat IS NOT NULL AND bbox_max_lon IS NOT NULL"
            " AND bbox_min_lat < bbox_max_lat AND bbox_min_lon < bbox_max_lon"
            " AND bbox_min_lat >= -90 AND bbox_max_lat <= 90"
            " AND bbox_min_lon >= -180 AND bbox_max_lon <= 180)",
            # Yakuniy nom — `ck_regions_bbox_complete` (konvensiya prefiks
            # qo'shadi); migratsiyadagi nom bilan aynan bir xil bo'lishi kerak.
            name="bbox_complete",
        ),
    )

    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name_uz: Mapped[str] = mapped_column(Text, nullable=False)
    name_ru: Mapped[str] = mapped_column(Text, nullable=False)
    default_language: Mapped[str] = mapped_column(Text, nullable=False, server_default="uz")
    center = mapped_column(point(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    bbox_min_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_min_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    @property
    def bbox(self) -> BBox | None:
        """bbox to'liq to'ldirilgan bo'lsa `BBox`, aks holda `None`."""
        return make_bbox(
            self.bbox_min_lat, self.bbox_min_lon, self.bbox_max_lat, self.bbox_max_lon
        )


class District(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "districts"
    __table_args__ = (
        Index("ix_districts_geom", "geom", postgresql_using="gist"),
        # Joriy (yopilmagan) chegaralar bo'yicha qidiruv — `05` §2.1.
        Index(
            "ix_districts_region_id_current",
            "region_id",
            postgresql_where=text("valid_to IS NULL"),
        ),
    )

    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name_uz: Mapped[str] = mapped_column(Text, nullable=False)
    name_ru: Mapped[str] = mapped_column(Text, nullable=False)
    geom = mapped_column(multipolygon(), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    license: Mapped[str] = mapped_column(Text, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Mahalla(UUIDPrimaryKeyMixin, Base):
    """E17 gacha bo'sh qoladi, lekin sxema boshidan mavjud (`05` §2.1)."""

    __tablename__ = "mahallas"
    __table_args__ = (
        Index("ix_mahallas_geom", "geom", postgresql_using="gist"),
        # `01` NFR-S-02 — mintaqa filtri indeks darajasida. `mahallas` da
        # `region_id` ustuni yo'q (`05` §2.1), ya'ni `GET /geo/mahallas`
        # mintaqani faqat `district_id → districts.region_id` zanjiri
        # bilan ajratadi. Indekssiz bu zanjir E17 dan keyin har so'rovda
        # **barcha** mintaqalarning mahallalarini o'qib tashlardi —
        # `0008` tuzatgan defektning aynan o'zi, faqat birlashma orqali.
        # Qisman emas (`districts` dagi `WHERE valid_to IS NULL` dan
        # farqli): `?at=` bilan tarixiy kesim ham so'raladi va qisman
        # indeks unga tusha olmasdi.
        Index("ix_mahallas_district_id", "district_id"),
    )

    district_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("districts.id"), nullable=False
    )
    name_uz: Mapped[str] = mapped_column(Text, nullable=False)
    name_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    geom = mapped_column(multipolygon(), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)


class BoundaryStaging(UUIDPrimaryKeyMixin, Base):
    """Import staging (`05` §5.1).

    Overpass dan kelgan poligonlar avval shu yerga tushadi, sifat tekshiruvi
    (`05` §5.3) shu jadval ustida bajariladi va faqat undan keyin `districts`
    ga ko'chiriladi. Xom OSM tegleri `raw_tags` da qoladi — nom to'liqligini
    qo'lda to'ldirish uchun kerak.
    """

    __tablename__ = "boundary_staging"
    __table_args__ = (
        # `status` kalitning bir qismi: bitta partiyada bitta relation ham
        # `staged` (district nomzodi), ham `reference` (qoplash etaloni,
        # `05` §5.3) bo'lishi mumkin — Samarqandda «shahar» aynan shunday,
        # chunki 8-daraja yo'q. `0011` gacha etalon egizagi jimgina tushib
        # qolardi va import sababsiz bloklanardi.
        UniqueConstraint(
            "batch_id",
            "source_ref",
            "status",
            name="uq_boundary_staging_batch_id_source_ref_status",
        ),
        Index("ix_boundary_staging_geom", "geom", postgresql_using="gist"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    region_code: Mapped[str] = mapped_column(Text, nullable=False)
    admin_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default="osm")
    source_ref: Mapped[str] = mapped_column(Text, nullable=False)
    license: Mapped[str] = mapped_column(Text, nullable=False, server_default="ODbL")
    name_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_tags: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    geom = mapped_column(multipolygon(), nullable=False)
    is_valid_geom: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # Maydon m² da — viloyat darajasida `integer` chegarasidan oshishi mumkin.
    area_m2: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="staged")
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


#: `territory_stats.territory_level` (`06` §3).
TERRITORY_LEVELS: tuple[str, ...] = ("district", "mahalla")

# `data_quality` qiymatlari ataylab bu yerda takrorlanmaydi — yagona manba
# `app.clustering.scale.DATA_QUALITIES` (`06` §3.2). Ikki joyda qo'lda
# yozilgan ro'yxat vaqt o'tishi bilan ajralib ketardi.


class TerritoryStats(Base):
    """Hudud statistikasi (`06` §3) — adaptiv chegaralar uchun.

    `territory_id` — `districts` yoki `mahallas` ning `id` si, shuning uchun
    **FK yo'q**: bitta ustun ikki jadvalga ishora qila olmaydi. Daraja
    `territory_level` da saqlanadi va yozuvchi tomon to'g'riligini kafolatlaydi.

    `population` `NULL` bo'lishi mumkin — mahalla darajasida aholi soni
    deyarli mavjud emas (`06` §3.1). Bunday holatda `data_quality` `estimated`
    yoki `unknown` bo'ladi va masshtab da'vosi cheklanadi (`06` §3.2, §5.4).
    """

    __tablename__ = "territory_stats"
    __table_args__ = (Index("ix_territory_stats_territory_level", "territory_level"),)

    territory_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    territory_level: Mapped[str] = mapped_column(Text, nullable=False)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    households: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_km2: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    populated_cells: Mapped[int] = mapped_column(Integer, nullable=False)
    active_users_30d: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    data_quality: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RegionConfig(Base):
    """Mintaqa kesimidagi sozlanadigan parametrlar (`06` §9).

    **Nima uchun bazada, koddagi konstanta emas.** `06` §9: hech bir qiymat
    empirik asosga ega emas, ular E11 da haqiqiy ma'lumotda sozlanadi. Har
    sozlash uchun deploy qilish mumkin emas.

    Standart qiymatlar `app.clustering.params.DEFAULTS` da — ular konstanta
    emas, yangi mintaqa uchun bootstrap qiymati. Bazadagi qator har doim
    ustun turadi.
    """

    __tablename__ = "region_config"

    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), primary_key=True
    )
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    # `jsonb` — son, satr yoki obyekt bo'lishi mumkin (`06` §9 da sonlar,
    # TZ §4.1 da to'lqinlar massivi).
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    #: TZ §7 — qiymat qayerdan kelgan. Qiymat bilan **birga** chop
    #: etiladi: `invented` sonni «o'lchangan» deb o'qishni to'sadi.
    origin: Mapped[str] = mapped_column(Text, nullable=False, server_default="invented")


class ConfigJournal(Base):
    """Sozlama o'zgarishlarining jurnali — faqat qo'shiladi (TZ T-2, ТС-219).

    **Nima uchun alohida jadval.** `region_config` joriy holatni
    saqlaydi, ТС-219 esa o'zgarishdan keyin **eskisi saqlanishini** va
    chop etilishini talab qiladi. Bitta jadvalda ikkalasini qilish
    uchun har o'qishga «eng oxirgi versiya» so'rovi kerak bo'lardi;
    joriy holat esa har bir xabar yo'lida o'qiladi.

    O'zgartirish va o'chirish **bazada** to'siladi (`0012` dagi
    trigger). Ilova qatlamidagi tekshiruv T-2 ni bajarmaydi: u
    «на уровне базы» deydi, ya'ni `psql` dan qo'lda kirish ham
    to'silishi kerak.
    """

    __tablename__ = "config_journal"
    __table_args__ = (
        # Nom konvensiyadan quriladi (`ck_%(table_name)s_%(constraint_name)s`),
        # shuning uchun bu yerda faqat oxirgi bo'lagi yoziladi — aks holda
        # baza `ck_config_journal_ck_config_journal_origin` ni ko'radi.
        CheckConstraint("origin IN ('invented', 'expert', 'computed')", name="origin"),
        Index(
            "ix_config_journal_region_id_key_changed_at",
            "region_id",
            "key",
            text("changed_at DESC"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    key: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    origin: Mapped[str] = mapped_column(Text, nullable=False)
    #: Kim o'zgartirdi: admin tokeni egasi yoki asbob nomi.
    changed_by: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

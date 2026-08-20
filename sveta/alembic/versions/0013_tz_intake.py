"""TZ §11/7 ning kirish yo'li: manbalar reyestri va xabarlar jurnali.

178-run §11 navbatining oxirgi bandini **qurdi**, lekin uni tashqi
dunyoga ulamadi: `app/reports/tzsensor.py` ning `INBOUND` reyestri
uchala signalni ham `built=True, wired=False` deb belgilagan edi.
Yetishmagan ikkita narsa aynan shu migratsiyada:

**1. `tz_sources` — reyestr.** `Source` dataclass i qoidalarni biladi
(datchikning katagi qotirilgan, operator/kanalda katak xabarda keladi),
lekin manbalar ro'yxatining o'zi hech qayerda saqlanmasdi. Usiz
`classify()` ning birinchi qadami — «manba reyestrdami» — har doim
`unknown_source` berardi.

Qoidalar **bazada ham** takrorlanadi (`CHECK`): reyestrga qator faqat
ilova orqali tushmaydi, `psql` dan qo'lda ham kiritiladi va o'sha
qo'lda kiritilgan qator eng xavflisi — katagi yozilmagan datchik
shaharning istalgan kvartalini В-7 bo'yicha yopa olardi.

**2. `tz_signals` — faqat qo'shiladigan jurnal (Т-2).** Т-2 «журнал
сообщений **и** настроек» deydi; `0012` sozlamalar yarmini yopgan,
xabarlar yarmi ochiq qolgan edi. Bu yerda o'sha ikkinchi yarmi, xuddi
o'sha uch qatlamli himoya bilan: `UPDATE`/`DELETE` triggeri, `TRUNCATE`
triggeri (qator triggeri uni **ko'rmaydi**) va funksiyaning o'zi.

**Nima uchun rad etilgan xabar ham yoziladi.** §8 ning operatori buzuq
qurilma haqida bilishi kerak, `Rejection.to_operator` esa hozircha
faqat HTTP javobida qaytadi — ya'ni xabar yuborgan qurilmaning o'ziga.
Jurnalsiz «raqqosa» datchik hech kimga ko'rinmasdi.

**Т-7 baza darajasida.** `ix_tz_signals_key_accepted` — qisman yagona
indeks: bitta `blake2b` kaliti ikkinchi marta **fakt** bo'la olmaydi.
Ilova qatlamidagi `seen` to'plami bir protsess ichida ishlaydi; ikkita
ishchi bir vaqtda bir xil xabarni qabul qilsa, faqat baza to'sib
qoladi.

Revision ID: 0013
Revises: 0012
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tz_sources",
        # Birlamchi kalit — `(region_id, source_id)`, shu tartibda.
        # `source_id` yetkazib beruvchi bergan nom va u global yagona
        # bo'lishga va'da bermaydi; mintaqa birinchi turgani uchun
        # `01` NFR-S-02 ga alohida indeks ham kerak emas.
        sa.Column(
            "region_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("regions.id"),
            primary_key=True,
        ),
        sa.Column("source_id", sa.Text(), primary_key=True),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("cell", sa.Text(), nullable=True),
        sa.Column("trusted", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Faqat oxirgi bo'lak: `op.create_table` metadata konvensiyasini
        # (`ck_%(table_name)s_%(constraint_name)s`) o'zi qo'llaydi va
        # to'liq nom yozilsa baza `ck_tz_sources_ck_tz_sources_channel`
        # ni ko'rardi (172-run buni haqiqiy bazada o'lchab topgan).
        sa.CheckConstraint("channel IN ('sensor', 'operator', 'feed')", name="channel"),
        # `cell IS NOT NULL` **majburiy**: usiz `btrim(NULL) <> ''`
        # `NULL` beradi va `CHECK` `NULL` ni buzilmagan deb o'qiydi —
        # ya'ni katagi yozilmagan datchik reyestrga tushib ketardi.
        sa.CheckConstraint(
            "(channel = 'sensor' AND cell IS NOT NULL AND btrim(cell) <> '') "
            "OR (channel <> 'sensor' AND cell IS NULL)",
            name="cell",
        ),
    )

    op.create_table(
        "tz_signals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "region_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("regions.id"),
            nullable=False,
        ),
        # `tz_sources` ga tashqi kalit **ataylab yo'q**: ro'yxatdan
        # o'tmagan identifikator bilan kelgan xabar ham yozilishi kerak.
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=True),
        sa.Column("signal", sa.Text(), nullable=False),
        sa.Column("cell", sa.Text(), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reference", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("key", sa.Text(), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("accepted = (reason = 'none')", name="reason"),
        sa.CheckConstraint("NOT accepted OR key IS NOT NULL", name="key"),
    )
    op.create_index(
        "ix_tz_signals_region_id_key_accepted",
        "tz_signals",
        ["region_id", "key"],
        unique=True,
        postgresql_where=sa.text("accepted"),
    )
    op.create_index(
        "ix_tz_signals_region_id_at",
        "tz_signals",
        ["region_id", sa.text("at DESC")],
    )
    op.create_index(
        "ix_tz_signals_region_id_source_id_at",
        "tz_signals",
        ["region_id", "source_id", sa.text("at DESC")],
    )

    # Т-2: xabarlar jurnali ham faqat qo'shiladi. Funksiya alohida —
    # `config_journal` nikidan mustaqil: bittasini o'chirish ikkinchisini
    # jimgina qurolsizlantirmasin.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION tz_signals_append_only()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION
                'tz_signals is append-only (TZ T-2): % is forbidden',
                TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_tz_signals_append_only
        BEFORE UPDATE OR DELETE ON tz_signals
        FOR EACH ROW EXECUTE FUNCTION tz_signals_append_only();
        """
    )
    # Qator triggeri `TRUNCATE` ni ko'rmaydi — usiz taqiq bitta buyruq
    # bilan chetlab o'tilardi va bo'sh jadval «hech narsa o'chirilmagan»
    # ga o'xshab turardi.
    op.execute(
        """
        CREATE TRIGGER trg_tz_signals_no_truncate
        BEFORE TRUNCATE ON tz_signals
        FOR EACH STATEMENT EXECUTE FUNCTION tz_signals_append_only();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_tz_signals_no_truncate ON tz_signals")
    op.execute("DROP TRIGGER IF EXISTS trg_tz_signals_append_only ON tz_signals")
    op.execute("DROP FUNCTION IF EXISTS tz_signals_append_only()")
    op.drop_index("ix_tz_signals_region_id_source_id_at", table_name="tz_signals")
    op.drop_index("ix_tz_signals_region_id_at", table_name="tz_signals")
    op.drop_index("ix_tz_signals_region_id_key_accepted", table_name="tz_signals")
    op.drop_table("tz_signals")
    op.drop_table("tz_sources")

"""TZ §1 zonalari va §7 sozlamalari: to'rt darajali H3, kelib chiqish belgisi, jurnal.

`TZ_Podtverzhdenie_i_uvedomleniya.md` ning §11 navbatidagi **birinchi**
band: «Настройки, журнал, зоны H3 — без этого остальное придётся
переделывать». Migratsiya uchta mustaqil narsani qo'yadi.

**1. `reports` ga to'rt daraja (§1).** Bugungi sxemada faqat `h3_r9`
bor, TZ esa uy (r10), mahalla (r8) va tuman (r7) darajalarini
**bir vaqtda** talab qiladi, ustiga r11 ni — u zona emas, §1.1 dagi
«turli manzil» ning yaqinlashuvi. Ustunlar `NULL` bo'lishi mumkin va
bu ataylab: eski qatorlarni orqaga to'ldirish har doim ham mumkin
emas, chunki `geom_exact` 90 kundan keyin `purge_exact_geom` bilan
`NULL` ga o'tadi (`05` §3.2). Aniq nuqtasi tirik qolgan qatorlar shu
yerda to'ldiriladi, qolganlari `NULL` bo'lib qoladi va TZ ning
sanashiga umuman kirmaydi — bu yo'qotish emas, ular baribir eski
oynalarda.

**2. `region_config.origin` (§7 ning oxirgi qatori).** Har sozlamaning
kelib chiqishi — `ПРИДУМАНО` / `ЭКСПЕРТ` / `ПОСЧИТАНО` — qiymat bilan
**birga** saqlanadi va birga chop etiladi. Bugun hammasi `invented`;
👤 qarori (2026-08-19) bo'yicha Toshkent tarixi ishlatilmaydi, ya'ni
TZ §12 ning oldindan tekshiruvi yo'q va sonlar Samarqandning o'z
ma'lumotidan keyingina `computed` ga o'tadi. Belgi shu holatning
ko'rinadigan izi.

**3. `config_journal` — faqat qo'shiladigan jurnal (T-2, ТС-219).**
Sozlama o'zgarganda eskisi **saqlanadi**: yangi qator qo'shiladi.
Taqiq baza darajasida — `UPDATE` va `DELETE` ni qaytaruvchi trigger.
Ilova qatlamidagi tekshiruv yetarli emas: T-2 aynan «на уровне базы»
deydi, ya'ni `psql` dan qo'lda o'zgartirish ham to'silishi kerak.

Sozlamalarning **boshlang'ich qiymatlari bu yerda yozilmaydi**: §7
«отсутствие настройки при запуске = ошибка запуска» deydi, ya'ni
qiymatlar `tools/seed_tz_config.py` bilan ataylab, ko'rinadigan qadam
bilan qo'yiladi. Migratsiya jimgina to'ldirsa, sozlamaning yo'qligi
hech qachon ko'rinmasdi.

Revision ID: 0012
Revises: 0011
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

#: TZ §1 jadvali: ustun nomi → H3 rezolyutsiyasi.
LEVELS: tuple[tuple[str, int], ...] = (
    ("h3_r7", 7),
    ("h3_r8", 8),
    ("h3_r10", 10),
    ("h3_r11", 11),
)


def upgrade() -> None:
    for column, _ in LEVELS:
        op.add_column("reports", sa.Column(column, sa.Text(), nullable=True))

    # Aniq nuqtasi hali o'chirilmagan qatorlarni to'ldirish. PostGIS
    # `h3` kengaytmasini talab qilmaydi: koordinata `geom_exact` dan
    # olinadi va katak `tools/backfill_h3_levels.py` da hisoblanadi.
    # Bu yerda faqat ustun tayyorlanadi — SQL da H3 funksiyasi yo'q.

    op.create_index(
        "ix_reports_h3_r10_created_at",
        "reports",
        ["h3_r10", sa.text("created_at DESC")],
    )

    op.add_column(
        "region_config",
        sa.Column("origin", sa.Text(), nullable=False, server_default="invented"),
    )
    op.create_check_constraint(
        "ck_region_config_origin",
        "region_config",
        "origin IN ('invented', 'expert', 'computed')",
    )

    op.create_table(
        "config_journal",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "region_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("regions.id"),
            nullable=False,
        ),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("changed_by", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Faqat oxirgi bo'lak: `op.create_table` ham metadata ning
        # konvensiyasini (`ck_%(table_name)s_%(constraint_name)s`)
        # qo'llaydi. To'liq nom yozilsa baza
        # `ck_config_journal_ck_config_journal_origin` ni ko'radi —
        # 172-run buni haqiqiy bazada o'lchab topdi.
        sa.CheckConstraint("origin IN ('invented', 'expert', 'computed')", name="origin"),
    )
    op.create_index(
        "ix_config_journal_region_id_key_changed_at",
        "config_journal",
        ["region_id", "key", sa.text("changed_at DESC")],
    )

    # T-2: o'zgartirish va o'chirish **bazada** taqiqlanadi.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION config_journal_append_only()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION
                'config_journal is append-only (TZ T-2): % is forbidden',
                TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_config_journal_append_only
        BEFORE UPDATE OR DELETE ON config_journal
        FOR EACH ROW EXECUTE FUNCTION config_journal_append_only();
        """
    )
    # `TRUNCATE` ni qator triggeri **ushlamaydi** — u qatorlarni
    # ko'rmaydi. Usiz T-2 ning taqiqi bitta buyruq bilan chetlab
    # o'tilardi va bo'sh jadval «hech narsa o'chirilmagan» ga o'xshab
    # turardi.
    op.execute(
        """
        CREATE TRIGGER trg_config_journal_no_truncate
        BEFORE TRUNCATE ON config_journal
        FOR EACH STATEMENT EXECUTE FUNCTION config_journal_append_only();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_config_journal_no_truncate ON config_journal")
    op.execute("DROP TRIGGER IF EXISTS trg_config_journal_append_only ON config_journal")
    op.execute("DROP FUNCTION IF EXISTS config_journal_append_only()")
    op.drop_index("ix_config_journal_region_id_key_changed_at", table_name="config_journal")
    op.drop_table("config_journal")
    op.drop_constraint("ck_region_config_origin", "region_config", type_="check")
    op.drop_column("region_config", "origin")
    op.drop_index("ix_reports_h3_r10_created_at", table_name="reports")
    for column, _ in LEVELS:
        op.drop_column("reports", column)

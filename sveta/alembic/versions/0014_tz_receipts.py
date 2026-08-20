"""TZ Т-9 — yuborilgan bildirishnomalarning qabul qiluvchilar jurnali.

§6.4 ning oxirgi jumlasi butun bir jadval buyuradi: «Хранить список
получателей каждого уведомления, чтобы знать, кому слать исправление.»

176-run o'sha jurnalning **shaklini** yozgan edi
(`app/notifications/tzoutage.py` ning `Receipt` va `record()` i), lekin
uni hech qayerda saqlamagan: `CHANNELS` reyestrida tuzatish kanali shu
sababdan `wired=False` turardi — «Т-9 ning qabul qiluvchilar jadvali»
yo'q edi. Bu migratsiya o'sha jadvalni beradi.

**Nima uchun bu jim yo'qotish edi.** §6.4 ning talabi shartsiz: «Это не
опция.» Lekin uni bajarish uchun kerak bo'lgan yagona narsa — kimga
xabar ketganining ro'yxati — protsess xotirasida turardi. Ya'ni xato
xabar tarqalgandan keyin ilova qayta ishga tushsa, tuzatish **hech
kimga** ketmasdi va xizmatning o'zi mish-mishning manbaiga aylanardi.
Kodda hech qanday xato ko'rinmasdi: `correct()` bo'sh ro'yxat oladi va
bo'sh ro'yxat qaytaradi.

**Faqat qo'shiladi (Т-2).** Yuborilgan xabar — jurnalning fakti.
Qatorni o'chirish mumkin bo'lsa, §6.4 dan qutulishning eng oson yo'li
paydo bo'lardi: ro'yxatni o'chir, keyin «tuzatadigan hech kim yo'q»
de. Shuning uchun `tz_signals` dagi bilan bir xil uch qavatli himoya —
`UPDATE`/`DELETE` qator triggeri, `TRUNCATE` uchun alohida statement
triggeri va ularning **o'z** funksiyasi.

**Т-7 bazada.** `ix_tz_receipts_region_id_key` — yagona indeks (qisman
emas: bu yerda har qator yuborilgan xabar, ya'ni istisno yo'q). Kalitga
xabarning **turi** ham kiradi, aks holda tuzatish o'z uzilishining
kaliti bilan to'qnashardi.

Revision ID: 0014
Revises: 0013
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tz_receipts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "region_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("regions.id"),
            nullable=False,
        ),
        sa.Column("kind", sa.Text(), nullable=False),
        # `outages` ga tashqi kalit **ataylab yo'q**: jurnal hodisadan
        # uzoqroq yashashi kerak. Т-10 tasdiqlangan uzilishni o'chirishni
        # taqiqlaydi, lekin `FOREIGN KEY` boshqa har qanday tozalashda
        # qabul qiluvchilar ro'yxatini birga olib ketardi — va aynan
        # o'sha lahzada §6.4 bajarilmay qolardi.
        sa.Column("incident_id", sa.Text(), nullable=False),
        sa.Column("cell", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("address_id", sa.Text(), nullable=False),
        # Xabar ketgan paytdagi manzil nomi va tili — o'sha lahzaning
        # fakti, joriy obunadan `JOIN` bilan olinmaydi.
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("lang", sa.Text(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Faqat oxirgi bo'lak: `op.create_table` metadata konvensiyasini
        # (`ck_%(table_name)s_%(constraint_name)s`) o'zi qo'llaydi
        # (172-run buni haqiqiy bazada o'lchab topgan).
        sa.CheckConstraint(
            "kind IN ('outage', 'restored', 'planned', 'correction')", name="kind"
        ),
    )
    op.create_index(
        "ix_tz_receipts_region_id_key",
        "tz_receipts",
        ["region_id", "key"],
        unique=True,
    )
    op.create_index(
        "ix_tz_receipts_region_id_incident_id_cell_kind",
        "tz_receipts",
        ["region_id", "incident_id", "cell", "kind"],
    )
    op.create_index(
        "ix_tz_receipts_region_id_sent_at",
        "tz_receipts",
        ["region_id", sa.text("sent_at DESC")],
    )

    # Т-2. Funksiya alohida — `tz_signals` va `config_journal` nikidan
    # mustaqil: bittasini o'chirish qolganlarini jimgina qurolsizlantirmasin.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION tz_receipts_append_only()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION
                'tz_receipts is append-only (TZ T-9 and T-2): % is forbidden',
                TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_tz_receipts_append_only
        BEFORE UPDATE OR DELETE ON tz_receipts
        FOR EACH ROW EXECUTE FUNCTION tz_receipts_append_only();
        """
    )
    # Qator triggeri `TRUNCATE` ni ko'rmaydi.
    op.execute(
        """
        CREATE TRIGGER trg_tz_receipts_no_truncate
        BEFORE TRUNCATE ON tz_receipts
        FOR EACH STATEMENT EXECUTE FUNCTION tz_receipts_append_only();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_tz_receipts_no_truncate ON tz_receipts")
    op.execute("DROP TRIGGER IF EXISTS trg_tz_receipts_append_only ON tz_receipts")
    op.execute("DROP FUNCTION IF EXISTS tz_receipts_append_only()")
    op.drop_index("ix_tz_receipts_region_id_sent_at", table_name="tz_receipts")
    op.drop_index("ix_tz_receipts_region_id_incident_id_cell_kind", table_name="tz_receipts")
    op.drop_index("ix_tz_receipts_region_id_key", table_name="tz_receipts")
    op.drop_table("tz_receipts")

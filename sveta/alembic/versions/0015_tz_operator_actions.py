"""TZ §8 — operator amallarining jurnali.

§8 ning oxirgi jumlasi jadval buyuradi: «Все действия пишутся в журнал
с указанием, кто и на основании чего.» 179-run `tz_signals` bilan
tashqi **signal** ni yozib olishni bergan edi, lekin operatorning
**qarori** signal emas: signal — dalil («bu katakda svet yo'q»), qaror
— vakolat («bu hodisa tasdiqlanmadi»). Ikkalasini bitta jadvalga
qo'shish §8 ning o'zagini yo'qotardi.

**Nima uchun rad etilgan urinish ham yoziladi.** «Amal» — bosilgan
tugma, natija emas. Faqat muvaffaqiyatli qatorlarni yozish jurnalni
aynan eng qiziq qatorlardan mahrum qilardi: kim tasdiqlashni tashqi
manbasiz o'tkazmoqchi bo'lgani hech qayerda ko'rinmasdi. `CHECK
(accepted = (refusal = 'none'))` ikkala da'voni bitta qatorda ushlab
turadi.

**§8 ning taqiqi bazada.** `confirm_needs_external` — «не может
создать подтверждение по собственному мнению без внешнего источника»
ning ikkinchi qulfi. Birinchisi kodda (`tzoperator.Refusal.
OWN_JUDGEMENT`), lekin kod tahrirlanadi, cheklov esa migratsiyasiz
yo'qolmaydi.

**Faqat qo'shiladi (Т-2).** `UPDATE`/`DELETE` qator triggeri va
`TRUNCATE` uchun alohida statement triggeri, o'z funksiyasi bilan.
Sabab bu yerda eng kuchli: amal jurnali operator ustidan yagona
nazorat, va tahrirlanadigan nazorat — nazorat emas.

**`btrim(NULL)` tuzog'i.** 179-run buni haqiqiy bazada o'lchab topgan:
`btrim(NULL) <> ''` `NULL` beradi va `CHECK` `NULL` ni «buzilmagan»
deb o'qiydi. Shuning uchun `actor`/`reference` cheklovlarida `IS NOT
NULL` ochiq yozilgan, ustunlar `NOT NULL` bo'lsa ham.

Revision ID: 0015
Revises: 0014
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tz_operator_actions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "region_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("regions.id"),
            nullable=False,
        ),
        # `outages` ga tashqi kalit **ataylab yo'q** — `tz_receipts`
        # dagi bilan bir xil sabab: jurnal hodisadan uzoqroq yashaydi.
        sa.Column("incident_id", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("basis", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("reference", sa.Text(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("refusal", sa.Text(), nullable=False),
        sa.Column(
            "seen",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Faqat oxirgi bo'lak: `op.create_table` metadata konvensiyasini
        # (`ck_%(table_name)s_%(constraint_name)s`) o'zi qo'llaydi
        # (172-run buni haqiqiy bazada o'lchab topgan).
        sa.CheckConstraint("action IN ('confirm', 'reject', 'close')", name="action"),
        sa.CheckConstraint("basis IN ('external', 'judgement')", name="basis"),
        sa.CheckConstraint(
            "actor IS NOT NULL AND btrim(actor) <> ''", name="actor_not_blank"
        ),
        sa.CheckConstraint(
            "reference IS NOT NULL AND btrim(reference) <> ''",
            name="reference_not_blank",
        ),
        sa.CheckConstraint(
            "NOT (accepted AND action = 'confirm' AND basis <> 'external')",
            name="confirm_needs_external",
        ),
        sa.CheckConstraint(
            "accepted = (refusal = 'none')", name="accepted_matches_refusal"
        ),
    )
    op.create_index(
        "ix_tz_operator_actions_region_id_key",
        "tz_operator_actions",
        ["region_id", "key"],
        unique=True,
    )
    op.create_index(
        "ix_tz_operator_actions_region_id_incident_id_decided_at",
        "tz_operator_actions",
        ["region_id", "incident_id", sa.text("decided_at DESC")],
    )
    op.create_index(
        "ix_tz_operator_actions_region_id_decided_at",
        "tz_operator_actions",
        ["region_id", sa.text("decided_at DESC")],
    )

    # Т-2. Funksiya alohida — `tz_signals`, `tz_receipts` va
    # `config_journal` nikidan mustaqil: bittasini o'chirish
    # qolganlarini jimgina qurolsizlantirmasin.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION tz_operator_actions_append_only()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION
                'tz_operator_actions is append-only (TZ 8 and T-2): % is forbidden',
                TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_tz_operator_actions_append_only
        BEFORE UPDATE OR DELETE ON tz_operator_actions
        FOR EACH ROW EXECUTE FUNCTION tz_operator_actions_append_only();
        """
    )
    # Qator triggeri `TRUNCATE` ni ko'rmaydi.
    op.execute(
        """
        CREATE TRIGGER trg_tz_operator_actions_no_truncate
        BEFORE TRUNCATE ON tz_operator_actions
        FOR EACH STATEMENT EXECUTE FUNCTION tz_operator_actions_append_only();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_tz_operator_actions_no_truncate "
        "ON tz_operator_actions"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_tz_operator_actions_append_only "
        "ON tz_operator_actions"
    )
    op.execute("DROP FUNCTION IF EXISTS tz_operator_actions_append_only()")
    op.drop_index(
        "ix_tz_operator_actions_region_id_decided_at",
        table_name="tz_operator_actions",
    )
    op.drop_index(
        "ix_tz_operator_actions_region_id_incident_id_decided_at",
        table_name="tz_operator_actions",
    )
    op.drop_index(
        "ix_tz_operator_actions_region_id_key", table_name="tz_operator_actions"
    )
    op.drop_table("tz_operator_actions")

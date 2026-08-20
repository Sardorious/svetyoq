"""TZ Т-10 — tasdiqlangan uzilishni o'chirib bo'lmaydi.

§10 ning `ТС-218` bandi: «Попытка удалить подтверждённую аварию →
Отказ базы». Т-10 esa uni qoida qilib yozadi: «Подтверждённую аварию
нельзя удалить, только сменить статус».

**Nima uchun bu himoya `outages` da 182-rungacha bo'lmagan.**
`0012`…`0015` migratsiyalari Т-2 ni (jurnal faqat qo'shiladi) TZ ning
**yangi** jadvallariga qo'ydi — `config_journal`, `tz_signals`,
`tz_receipts`, `tz_operator_actions`. `outages` esa TZ dan **oldin**
(`0002`) tug'ilgan va o'sha to'lqinga tushmadi. Ya'ni loyihaning eng
qimmatli jadvali — tasdiqlangan hodisalar tarixi — yagona himoyasiz
jadval bo'lib qoldi, va buni 182-run §10 ni reyestrga aylantirgandagina
ko'rdi.

## Mezon — `confirmed_at`, joriy status emas

Eng oson yozilardigan shart `status = 'confirmed'` — va u qoidani
**bo'sh** qilardi: hodisa tasdiqlanadi, keyin `resolved` ga o'tadi va
shundan keyin bemalol o'chiriladi. Т-10 ning butun ma'nosi esa
«tasdiqlangan bo'lgan» faktida: `confirmed_at` bir marta qo'yiladi
(`app.clustering.service`) va hech qachon tozalanmaydi. Shuning uchun
qorovul aynan uni o'qiydi — `confirmed_at IS NOT NULL`. Tasdiqqa
yetmagan (`pending` va `rejected`) hodisa avvalgidek o'chiriladi:
Т-10 ular haqida emas.

## Т-3 bilan ziddiyat va uning yagona teshigi

Т-3 («пересчитать историю за 90 дней с другими настройками») va Т-10
to'g'ridan-to'g'ri qarama-qarshi: qayta hisoblash oynadagi hodisalarni
**o'chirib** qaytadan quradi (`05` §9.2, `tools/recluster.py`), va
oynada tasdiqlangan hodisa deyarli har doim bor. Qorovulni shartsiz
qilish Т-3 ni butunlay o'chirardi — **quruq yurish** ham `DELETE` ni
bajaradi (u faqat oxirida `ROLLBACK` qiladi), ya'ni hatto o'lchash ham
mumkin bo'lmasdi.

Shuning uchun teshik bitta va u **ko'rinadi**: tranzaksiya doirasidagi
`sveta.recluster` sozlamasi. Uni butun kodda **yagona** joy qo'yadi —
`app.clustering.repository.delete_outages`, ya'ni `05` §9.2 ning
asbobi. `SET LOCAL` bo'lgani uchun bayroq tranzaksiyadan tashqariga
chiqmaydi va keyingi so'rovga sizib o'tmaydi; qo'yilmagan holatda
`current_setting(..., true)` `NULL` qaytaradi va qorovul otiladi.
Yagona ekanini `tests/test_outage_delete_guard.py` ning tripwire testi
`ast` bilan ushlab turadi.

👤 **Ochiq savol** (`PROGRESS.md`): Т-10 ning **harfi** «только сменить
статус» deydi, ya'ni to'g'rirog'i qayta hisoblash ham `DELETE` emas,
alohida status (`superseded`) qo'yishi kerak edi. Bu `recluster` ning
barmoq izini, `/stats` ning agregatlarini va `merged_into` ni qayta
ko'rib chiqishni talab qiladi — bitta runga sig'maydi va mahsulot
qarori. Bugungi migratsiya harfni emas, **maqsadni** qulflaydi:
tasdiqlangan hodisa oddiy yo'l bilan yo'qolmaydi.

## `TRUNCATE` alohida

Qator triggeri `TRUNCATE` ni ko'rmaydi (`0013` buni haqiqiy bazada
o'lchab topgan), `TRUNCATE outages` esa ta'rifi bo'yicha barcha
tasdiqlangan hodisalarni yo'q qiladi. Statement triggerida qatorlarni
ajratib bo'lmaydi, shuning uchun taqiq **shartsiz** va teshigi ham
yo'q: qayta hisoblash `TRUNCATE` ni ishlatmaydi.

Revision ID: 0016
Revises: 0015
"""

from __future__ import annotations

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Funksiya ataylab alohida (`tz_operator_actions` nikidan mustaqil):
    # bittasini tushirish qolganlarini jimgina qurolsizlantirmasin.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION outages_confirmed_no_delete()
        RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'TRUNCATE' THEN
                RAISE EXCEPTION
                    'outages cannot be truncated (TZ T-10): '
                    'confirmed incidents would be lost';
            END IF;
            IF OLD.confirmed_at IS NULL THEN
                RETURN OLD;
            END IF;
            IF coalesce(current_setting('sveta.recluster', true), 'off') = 'on' THEN
                RETURN OLD;
            END IF;
            RAISE EXCEPTION
                'confirmed outage % cannot be deleted (TZ T-10): '
                'change the status instead', OLD.id;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_outages_confirmed_no_delete
        BEFORE DELETE ON outages
        FOR EACH ROW EXECUTE FUNCTION outages_confirmed_no_delete();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_outages_no_truncate
        BEFORE TRUNCATE ON outages
        FOR EACH STATEMENT EXECUTE FUNCTION outages_confirmed_no_delete();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_outages_no_truncate ON outages")
    op.execute("DROP TRIGGER IF EXISTS trg_outages_confirmed_no_delete ON outages")
    op.execute("DROP FUNCTION IF EXISTS outages_confirmed_no_delete()")

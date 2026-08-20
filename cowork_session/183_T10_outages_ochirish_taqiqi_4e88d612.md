# 183-run — TZ Т-10: `outages` ni o'chirish taqiqi (`0016`), ТС-218 yopildi

**Sessiya:** `local_4e88d612` · **Sana:** 2026-08-20 · **Epic:** TZ (yangi qonun)

---

## Nimadan boshlandi

182-run `app/release/tz_acceptance.py` ni qurdi — TZ §10 ning yigirmata
qabul bandini reyestrga aylantirdi — va bitta qatorni `UNBUILT` deb
belgiladi: **ТС-218**, «Попытка удалить подтверждённую аварию → Отказ
базы». Uning qoldirgan topshirig'i aynan shu edi.

Kod o'qishdan boshlandi. Uch fakt topildi:

1. `outages` da hech qanday trigger yo'q. `0012`…`0015` Т-2 ni («jurnal
   faqat qo'shiladi») TZ ning **yangi** jadvallariga qo'ygan —
   `config_journal`, `tz_signals`, `tz_receipts`, `tz_operator_actions`.
   `outages` esa `0002` da tug'ilgan va o'sha to'lqinga tushmagan.
   Ya'ni loyihaning eng qimmatli jadvali — tasdiqlangan hodisalar
   tarixi — yagona himoyasiz jadval bo'lib qolgan.
2. `confirmed_at` bir marta qo'yiladi (`clustering/service.py`, status
   `CONFIRMED` ga o'tganda) va **hech qachon tozalanmaydi**.
3. `app/clustering/repository.py:delete_outages` — butun kodda
   `DELETE FROM outages` ning yagona joyi, va uni faqat
   `tools/recluster.py` chaqiradi.

---

## Qaror 1 — mezon `confirmed_at`, joriy status emas

Eng oson yoziladigan shart `status = 'confirmed'` edi. U qoidani
**bo'sh** qilardi: hodisa tasdiqlanadi, keyin `resolved` ga o'tadi va
shundan keyin bemalol o'chiriladi — taqiq ikki qadamda chetlab
o'tiladi. Т-10 ning butun ma'nosi «tasdiqlangan **bo'lgan**» faktida,
va u faqat `confirmed_at` da yashaydi.

Shu sabab uchun `tests/test_outage_delete_guard.py` da alohida test bor
(`test_guard_survives_the_status_change`): hodisa `confirmed_at` bilan,
lekin statusi `resolved`. `status` shartli qorovul o'sha testdan
o'tmaydi.

Tasdiqqa yetmagan (`pending`, `rejected`) hodisa avvalgidek o'chadi —
Т-10 ular haqida emas, va qorovulni hammaga yoyish `05` §9.2 ni
sababsiz to'sardi.

---

## Qaror 2 — Т-3 bilan ziddiyat va uning yagona teshigi

Т-3 («пересчитать историю за 90 дней с другими настройками») va Т-10
to'g'ridan-to'g'ri qarama-qarshi. Uchta variant ko'rildi:

| Variant | Nega rad etildi |
|---|---|
| Shartsiz trigger, `recluster` esa tasdiqlangan hodisali oynani rad etsin | Т-3 butunlay o'ladi. **Quruq yurish ham `DELETE` ni bajaradi** (u faqat oxirida `ROLLBACK` qiladi), ya'ni o'lchash ham mumkin bo'lmasdi |
| `recluster` `DELETE` o'rniga `superseded` statusini qo'ysin — Т-10 ning **harfi** aynan shu | To'g'ri, lekin bitta runga sig'maydi: barmoq izi (`05` §9.2 determinizmi), `/stats` va `daily_digest` agregatlari, `merged_into` ning ma'nosi — hammasi qayta ko'riladi. 👤 `PROGRESS.md` ga ochiq savol bo'lib yozildi |
| **Tanlangan:** trigger + tranzaksiya doirasidagi bitta ko'rinadigan teshik | Teshik `grep` bilan topiladi, `SET LOCAL` bo'lgani uchun keyingi so'rovga sizmaydi, va uni ushlab turadigan ikkita tripwire bor |

Teshik `RECLUSTER_GUC = "sveta.recluster"` va uni **faqat**
`delete_outages` qo'yadi. Bayroq chaqiruvchida emas, funksiyaning
ichida — shunda u bitta joyda.

🔴 **`text("SET LOCAL …")` yozib bo'lmadi.** U `05` §1 ning «xom SQL ning
bitta uyi bor» qorovulini buzdi
(`tests/test_architecture_contract.py::test_raw_sql_outside_the_schema_has_exactly_one_home`
— ruxsat etilgani faqat `api/v1/health.py`). Qorovulga istisno ochish
Т-10 ning teshigini ikkinchi marta kengaytirish bo'lardi, shuning uchun
`select(func.set_config(RECLUSTER_GUC, "on", True))` — bazada bir xil
narsa, lekin ifoda sifatida.

---

## 🔴 Qorovul o'n ikkita teardown ni yiqitdi — va bu to'g'ri edi

Birinchi to'liq yurishda `test_clustering_service_db`, `test_metrics_api_db`,
`test_stats_api_db` va `test_recluster_db` **teardown da** yiqildi:

```
ERROR at teardown … [SQL: DELETE FROM outages WHERE region_id = $1]
```

O'n ikkita `requires_db` fayli teardown da aynan shu qatorni yozardi.
Ya'ni teardown ham «tasdiqlangan hodisani o'chirish» — qorovul
ishladi.

Tuzatishning ikki yo'li bor edi va tanlov muhim:

* fikstyuralarga bayroqni **qo'lda** qo'ydirish → teshik o'n ikki joyga
  ko'chadi, keyin uni kimdir mahsulot kodiga nusxalashi vaqt masalasi;
* **tanlangan:** `tests/conftest.py` ga `purge_outages(session, region_id)` —
  u hodisa id larini o'qiydi va **bor** teshikdan, `delete_outages` dan
  o'tadi. Testlar mahsulot bilan bitta eshikdan yuradi, yangi eshik
  ochilmaydi.

---

## 🔴 Iflos baza to'qqizta soxta xato berdi

Birinchi yurish (teardown hali tuzatilmagan) bazada mintaqalar,
hodisalar va xabarlarni qoldirdi. Keyingi tekshiruvlar o'sha bazada
qilindi va **butunlay boshqa** sabablarga o'xshab ko'rindi: `NOW`
konstantasi 2026-08-06/07 da qotgan (vaqt bombasi?), `report_sources` da
`'test'` qatori yo'q (urug'lantirish kerakmi?), `count_exact_geom_older_than`
mintaqasiz sanaydi.

Uchchalasi ham **yolg'on iz** bo'lib chiqdi. `purge_outages` dan keyin
noldan qurilgan bazada butun to'plam yashil: **4917 passed, 2 skipped**.
Xulosa yozib qo'yilsin — *0 survivor emas, «toza bazada o'lchandi»
degan gap ham da'vo*: iflos baza teskari tomonga ham yolg'on gapiradi.

---

## Qurilgani

**`alembic/versions/0016_outages_confirmed_no_delete.py`**

```
trg_outages_confirmed_no_delete   BEFORE DELETE  FOR EACH ROW
trg_outages_no_truncate           BEFORE TRUNCATE FOR EACH STATEMENT
```

Bitta funksiya, `TG_OP` bo'yicha ajraladi. `TRUNCATE` **shartsiz** —
statement triggerida qatorlarni ajratib bo'lmaydi, `TRUNCATE outages`
esa ta'rifi bo'yicha butun tasdiqlangan tarixni yo'q qiladi va qayta
hisoblash undan foydalanmaydi.

**`tests/test_outage_delete_guard.py`** — 8 test:

1. tasdiqlangan hodisa o'chmaydi (`ТС-218` ning o'zi);
2. tasdiqlanib keyin `resolved` ga o'tgani **ham** o'chmaydi;
3. `pending` va `rejected` o'chadi;
4. qayta hisoblash o'chiradi, **lekin bayroq keyingi tranzaksiyaga
   sizmaydi** (bitta testda ikkala tomon — ular bitta mexanizmning
   ikki yuzi);
5. `TRUNCATE` shartsiz rad etiladi;
6. `0016` ning `upgrade → downgrade → upgrade` i haqiqiy bazada —
   ⚠️ SQL testga **ko'chirilmaydi**, `ast` bilan migratsiyaning
   o'zidan o'qiladi (nusxa jimgina ajralib ketardi);
7. tripwire: bayroq `app/` da bitta modulda. ⚠️ Birinchi variant matn
   bo'yicha qidirdi va **reyestrning izohiga ilindi** — `tz_acceptance.py`
   bayroqni *nomlaydi*, lekin *qo'ymaydi*. Qidiruv `ast` ga ko'chirildi
   va docstring lar chiqarib tashlandi;
8. tripwire: bayroq `DELETE` dan **oldin** qo'yiladi (bu xato bazasiz
   sezilmasdi).

**Reyestr yangilandi:** ТС-218 → `BUILT`; `test_tz_acceptance.py` ning
`test_ts218_is_the_only_unbuilt_case` → `test_every_case_is_built`
(yo'nalish teskari qilindi ataylab: «bittasi qurilmagan» degan da'vo
yangi `UNBUILT` qator qo'shilganda jimgina noto'g'ri bo'lardi).
`test_an_unbuilt_case_has_no_tests_and_a_reason` endi ro'yxatda hech
qachon otilmaydi — shuning uchun qoida sun'iy band ustida ham
o'lchanadi.

---

## Yakun

* **4917 passed, 2 skipped**; `requires_db` **370** (+6) — haqiqiy
  PostGIS 3.6 da yurgizildi, `alembic upgrade head` bilan noldan
  qurilgan bazada.
* `ruff check` toza. `0016` migratsiya. Yangi sozlama yo'q, yangi i18n
  kaliti yo'q, yangi API yo'q.
* §10 reyestri: 20 banddan **20 tasi qurilgan** (edi 19), 3 tasi
  uchidan-uchiga yurilgan. `clean` hamon `False` — qolgan o'n yettitasi
  faqat o'z modulida o'lchanadi.

## 👤 Ochiq savollar (yangi)

1. Т-10 ning **harfi** «только сменить статус» deydi. Qayta hisoblash
   `DELETE` o'rniga `superseded` statusini qo'ysinmi — alohida run va
   mahsulot qarori.
2. `tools/_mut.py` va `tools/_mut84.py` — mutatsiya harnessining
   qoldig'i, mahsulot kodi emas. Agent o'chira olmaydi
   (`allow_cowork_file_delete` runni to'xtatadi). O'chirilsinmi?

## Keyingi qadam

ТС-210/ТС-212 ni uchidan-uchiga yurish (tiklanish → status →
bildirishnoma), keyin reyestrdagi qolgan `PER_MODULE` bandlar.

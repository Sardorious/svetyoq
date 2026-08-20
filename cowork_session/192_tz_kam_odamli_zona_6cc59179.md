# 192-run — TZ §2.3 ning maxraji manbaga ega bo'ldi (`2.3-source`)

**Sana:** 2026-08-20 · **Sessiya:** `local_6cc59179` · **Epic:** TZ
**👤 ulash tartibining uchinchi bandi** (190 — §3 ning maxraji, 191 — §1.1(3) ning uy katagi)

---

## 1. Qayerdan boshlandi

191-run oxirida `INDEX.md` ikkita qarzni nomlagan edi:

1. tartibning 3-bandi — TZ ni mahsulot quvuriga ulash, lekin u
   **javobsiz savolga tayanadi** (qaysi zonaning verdikti hodisani
   tasdiqlaydi — §2.1 da yozilmagan);
2. §2.3 ning maxrajini beradigan agregat so'rov (zonalar kesimida,
   N+1 siz).

Birinchisi bloklangan, ikkinchisi emas — shuning uchun bu run
ikkinchisini oldi.

**Teshikning shakli uchinchi marta bir xil.** 187-run
`from_zone_verdicts()` ning `blocks_with_users` argumentidan sukut
qiymatini olib tashlagan, 190-run so'rovni qurgan. 191-run
`tzwitness.load()` ning `active_users` argumentini **sukut qiymatisiz**
qoldirgan — ya'ni chaqiruvchi javob berishga majbur, ammo javobni
topadigan yo'l repoda umuman yo'q edi. Majburiyat bor, imkoniyat yo'q.

**Narxi o'lchandi va u jim edi.** `active_users` bo'sh bo'lsa
`threshold()` `None` ni «noma'lum» deb o'qiydi va §2.1 ning bazaviy
porogini qoldiradi — ya'ni §2.3 **umuman ishlamaydi** va TZ ning
«без этого правила частный сектор и малые махалли не подтвердят
ничего никогда» jumlasi so'zma-so'z bajarilib turadi. Qolgan hamma
zona to'g'ri ishlaydi, shuning uchun hech narsa qizarmasdi.

---

## 2. Ikkita yangi qism

### `reports.queries.zone_users` (+ `zone_users_stmt`, `ZoneUsersRow`)

Uchala darajaning maxraji **bitta** so'rovda: `UNION ALL` ostida uchta
`GROUP BY`, har birida `count(distinct user_id)`.

🔴 **Nima uchun Python da yig'ilmadi.** Xom `(user_id, r8, r9, r10)`
qatorlarini o'qib darajalarni Python da yig'ish eng qisqa yo'l edi va
u **jimgina noto'g'ri**: bitta odam bitta kvartalning ikkita uy
katagidan xabar bergan bo'lsa, kvartal darajasida u ikki marta
sanalardi. Maxraj shishar, §2.3 esa **o'chib** qolardi — ya'ni xato
aynan §2.3 ni bekor qiladigan tomonga ketardi. `count(distinct …)` ni
har daraja uchun alohida bazaga aytish yagona to'g'ri shakl.

🔴 **`IS NOT NULL` uchala darajada.** `h3_r9` `NOT NULL`, lekin `0012`
dan oldingi qatorlarda `h3_r8` va `h3_r10` bo'sh va `GROUP BY` ularni
bitta `NULL` chelakka yig'ib, **mavjud bo'lmagan zonaga** maxraj yasab
berardi.

### `app/clustering/tzactive.py` (yangi modul, ulash qatlami)

`to_counts` toza (rezolyutsiya → `Level`), `load` bazadan. `tzcount`
toza qoldi va `SPEC` konstantasi olinmadi — `tzsource`/`tzwitness`
bilan bir xil sabab.

`ActiveZones.unknown` — **javob emas, diagnostika**: darajaga
aylantirib bo'lmagan rezolyutsiya (bugun bo'sh bo'lishi kerak)
jimgina yo'qolmaydi. r11 daraja emas va u zonaga aylanib qolmasligi
kerak.

---

## 3. Yozilgan qarorlar

### 🔴 Oyna yo'q — va sabab §3 nikidan **teskari**, xulosa bir xil

TZ §2.3 «активных пользователей» deydi, §3 esa «где есть наши
пользователи» — ikki xil so'z. Oyna baribir qo'yilmadi:

1. **§7 da bunday son yo'q.** Faollikning oynasi (30 kun? 90?)
   sozlamalar jadvalida ham, matnda ham yozilmagan — kodda tanlash
   Т-1 ga to'g'ridan-to'g'ri zid.
2. **Oyna maxrajni faqat kichraytiradi.** §3 da kichik maxraj ulushni
   o'z-o'zidan bajariladigan qiladi; §2.3 da kichik maxraj qoidani
   **ishga tushiradi** va porogni `max(faollar, 2)` gacha tushiradi.
   Ya'ni ikkala bo'limda ham tor o'qish tasdiqlashni **arzonlashtiradi**.
   Keng o'qish esa §2.3 ni ishlatmaydi — porog §2.1 da qoladi. Xato
   qilinsa, qat'iyroq tomonga.

### 🔴 Filtr faqat `is_blocked` — chunki u sanoqnikidan kuchli bo'lmasligi kerak

Sanoq (`tz_evidence`) uchta to'siqdan o'tadi: `is_blocked`,
`trust_score`, akkaunt yoshi. Maxraj esa **faqat birinchisidan**.
Sabab tuzilmaviy: maxrajning filtri sanoqnikidan kuchliroq bo'lsa,
guvoh sanalib maxrajga **tushmay** qolardi, ya'ni `active_users <
have` bo'lardi va §2.3 zonaning porogini o'zi ko'rgan odamlar sonidan
**pastga** qo'yardi. Filtrlar to'plami ichma-ich bo'lgani uchun
`active_users >= have` — kafolat, tasodif emas
(`test_a_witness_is_always_inside_the_denominator`).

`is_blocked` ning o'zi qoladi: maxrajni **oshirish** ham hujum —
bo'sh zonada ochilgan akkauntlar §2.3 ni o'chirib qo'yadi.

### 🔴 Takror zonada kattasi yutadi

`GROUP BY` buni qaytarmasligi kerak. Qaytargan kunda katta maxraj
§2.3 ni **o'chiradi** (porog §2.1 da qoladi), kichigi esa porogni
tushiradi.

---

## 4. ⬜ Topilma: §2.3 «Нужно человек» ni tushiradi, «Дополнительно» ni emas

Kvartalda ikkita faol odam bo'lsa porog ikkiga tushadi va odamlar
yetadi (`have == need`), lekin §2.1 ning ikkinchi sharti — «минимум из
3 разных клеток r10» — joyida qoladi va kvartal baribir yetmaydi
(`Shortfall.SPREAD`). `block_min_cells` (3) > `sparse_floor_users` (2).

Ya'ni **kam odamli kvartal §2.3 dan keyin ham deyarli hech qachon
tasdiqlanmaydi** — ikkita odam uchta har xil uy katagidan xabar bergan
holdan tashqari. Uy darajasida bunday shart yo'q, ya'ni §2.3 aynan
o'sha yerda ishlaydi.

Bu **topilma, tuzatish emas**: §2.3 faqat «порог» haqida gapiradi,
qo'shimcha shart haqida bir og'iz ham so'z yo'q. Kodga tegilmadi,
👤 savol `PROGRESS.md` ga yozildi. Testda ochiq yozilgan
(`test_sparse_lowers_the_people_bar_but_not_the_spread_bar`), ya'ni
teshik nomlangan.

---

## 5. Yo'l-yo'lakay: xom SQL qorovuli ishladi

`UNION` ning `ORDER BY` i chiqish ustunining **nomiga** murojaat
qiladi va birinchi variant `text("resolution")` yozgan edi.
`tests/test_architecture_contract.py::test_raw_sql_outside_the_schema_
has_exactly_one_home` qizardi — u `app/` da `from sqlalchemy import
text` ning yagona uyini (`api/v1/health.py`) sanaydi.

To'g'ri javob istisnolar ro'yxatiga qo'shish emas: `column("resolution")`
xuddi shu ishni qiladi va qorovulni zaiflashtirmaydi.

---

## 6. Tekshirish

**To'plam:** butun to'plam haqiqiy bazada — **5115 passed, 2 skipped**
(PostgreSQL 18.6 + PostGIS 3, `0001…0016`); edi 5080/2. `requires_db`
398 (+10). `ruff` toza. Migratsiya, sozlama, i18n va API **yo'q**.

**Yangi testlar:** `tests/test_tz_active.py` (22, bazasiz) va
`tests/test_tz_active_db.py` (10, `requires_db`);
`test_tz_counting.MODULES` ga yangi modul (Т-1/Т-4 qorovullari).

**Mutatsiya: 13 mutant → 11 KILLED, 2 survivor.**

Uchtasi birinchi urinishda tirik qoldi va uchalasi ham tuzatildi:

| Mutant | Nima uchun tirik qoldi | Javob |
|---|---|---|
| `max(...)` → «oxirgisi yutadi» | test takrorni faqat **o'sish** tartibida berardi | ikkinchi tartib qo'shildi |
| `sorted` → yo'q (`unknown`) | `set` da bitta element | `unknown` `list` ga aylantirildi, testda ikkita qiymat teskari tartibda |
| `sorted` → yo'q (`zones`) | `to_counts` xaritani allaqachon tartiblab beradi | `ActiveZones` qo'lda yasaladigan test qo'shildi |

Qolgan ikkitasi **tan olingan**, tuzatilmagan:

* `tuple(set(unknown))` (tartiblamaydi, lekin takrorni yechadi) —
  CPython da kichik butun sonlar to'plami o'sish tartibida yuradi,
  ya'ni uni o'ldiradigan test tilning ichki tafsilotiga tayanardi;
* `.group_by(column, Report.region_id)` — so'rov bitta mintaqa bo'yicha
  filtrlangani uchun **ekvivalent mutant**, teshik emas.

---

## 7. Keyingi qadam

👤 tartibning 3-bandi — TZ ni fuqaro oqimiga ulash. U hamon **javobsiz
savolga tayanadi**: TZ §2.1 **zonani** tasdiqlaydi (r10/r9/r8),
`outages` esa klaster — qaysi zonaning verdikti hodisani tasdiqlaydi?
Uchta o'qish mumkin (markaz / istalgan zona / hodisa umuman zonaga
aylanadi) va hech biri hujjatda yozilmagan.

Ulash uchun kerak bo'lgan **uchala manba** endi bor:
`tzsource` (§3 ning maxraji), `tzwitness` (§1.1(3) ning uy katagi),
`tzactive` (§2.3 ning maxraji). Qarz qolmadi — faqat savol qoldi.

---

## 8. Sandbox

167-run retsepti ishladi: `/tmp/pg180` (18.6 + PostGIS 3),
`/tmp/mamba/envs/py311`; har run **yangi** `initdb`,
`listen_addresses='127.0.0.1'`, o'z porti. To'plam
`/sessions/…/tmp/r192` dagi nusxada (bazasiz 44 s, baza bilan 95 s);
nusxa `tar --exclude` bilan.

⚠️ **`pg_ctl start` chaqiruvlar orasida o'ladi** — `pg_ctl` +
`alembic` + `pytest` **bitta** bash chaqiruvida bo'lishi shart. Bu
run bir marta unutdi va `399 skipped` oldi: sabab «PostGIS
ko'tarilmadi» emas, server oldingi chaqiruv bilan birga o'lgani edi.

⚠️ **`/` diskda 19 MB qoldi (100 %).** `/sessions` da ~490 MB.
Keyingi run `initdb` dan oldin eski `/tmp/pgdata*` larni o'chirsin.

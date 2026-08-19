# 168-run — PostGIS sandboxda ko'tarildi; `digest_service` o'lchandi

**Sessiya:** `local_975474c8` · **Sana:** 2026-08-19 · **Epic:** E8

---

## 1. Nima qilindi (qisqacha)

1. **PostGIS sandboxda ko'tarildi** va **126-rundan beri yurgizilmagan
   298 ta `requires_db` testi birinchi marta o'tkazildi** — `298 passed`.
   Butun to'plam: **4140 passed, 1 skipped**, `ruff` toza.
   167 qoldirgan tartibning (1) bandi shu bilan **yopildi**.
2. 167 qoldirgan tartibning (3) bandi olindi: `app/admin/digest_service.py`
   mutatsiya bilan o'lchandi — **21 mutatsiya → 10 KILLED, 11 SURVIVOR (52 %)**.
3. O'n bitta survivor **butun to'plamda birma-bir** tasdiqlandi (yolg'on
   survivor yo'q), o'ntasi `tests/test_digest_service_contract.py` (11 test)
   bilan qulflandi, biri ekvivalent deb belgilandi.
4. Yakun: **4151 passed, 1 skipped**, `requires_db` **309** (+11),
   migratsiyasiz, `ruff` toza. **Mahsulot kodi tegilmadi.**

---

## 2. Muhit — ishlaydigan retsept

`/sessions` da 8.3 GB bo'sh edi (167-run kuzatgan holat saqlanib qolgan),
shuning uchun muhit `/tmp` ga emas, `/sessions/<sid>/work/` ga qurildi.

```bash
ROOT=/sessions/<sid>/work
export MAMBA_ROOT_PREFIX=$ROOT/mamba CONDA_PKGS_DIRS=$ROOT/mamba/pkgs \
       XDG_CACHE_HOME=$ROOT/cache TMPDIR=$ROOT/tmp HOME=$ROOT
micromamba create -p $ROOT/mamba/envs/py311 -c conda-forge python=3.11
micromamba install -p $ROOT/mamba/envs/py311 -c conda-forge postgis postgresql
initdb -D $ROOT/pgdata -U postgres --auth=trust -E UTF8
# postgresql.conf: listen_addresses = '127.0.0.1', port = 54329, fsync = off
pg_ctl -D $ROOT/pgdata -l $ROOT/pg.log start -w -t 60
```

Versiyalar: `postgresql 18.6`, `postgis 3.6.4` (`USE_GEOS=1 USE_PROJ=1`).
CI dagi `postgis/postgis:16-3.4` dan yangiroq, lekin `0001`…`0011`
migratsiyalari **hammasi toza o'tdi** va to'plam yashil.

### Nozik joylar (kelgusi runlar uchun)

* **Kengaytma fayllari `envs/py311/share/extension/` da**, `share/postgresql/extension/`
  da emas — `pg_config --sharedir` bilan tekshiring.
* **TCP majburiy.** `tests/conftest.py` ning `_db_reachable()` i portga
  `socket.create_connection` qiladi. Unix-soketli `DATABASE_URL` bilan
  298 test **jimgina `skip`** bo'lardi va natija yashil ko'rinardi
  (`svetyoq-requires-db-needs-tcp`).
* **Sxema `alembic upgrade head` bilan quriladi**, `create_all` bilan emas —
  `tests/test_schema_index_parity.py` aynan shunga tayanadi.
* Rol `CREATE ROLE sveta LOGIN SUPERUSER`: `0001` `CREATE EXTENSION` qiladi.
* **Mount ustida to'plam yurgizilmaydi** (`svetyoq-run-suite-on-a-local-copy`):
  `cp -r` bilan `$ROOT/repo` ga nusxa (~35 s), shundan keyin butun to'plam
  **78 s**.
* Postgres chaqiruvlar orasida yashamaydi — har `bash` chaqiruvi
  `pg_ctl start` bilan boshlanadi.
* `bash` ning **180 s** chegarasi bu runda ham urildi (`s1.json` partiyasi
  uzildi va ishchi nusxada M05 qolib ketdi — darhol tiklandi, mount dagi
  repo teginilmagan edi). Butun to'plamli mutatsiya — **ikkitadan** ortiq
  emas.

---

## 3. Mutatsiya — `app/admin/digest_service.py`

### 3.1. Nishon nega tanlandi

167-run navbatga uchinchi bandni qo'ygan edi: modulni butun repoda
faqat `tests/test_daily_digest_db.py` (`requires_db`) import qiladi.
166/167 da bu «o'lchab bo'lmaydigan» degani edi — verdikt bazasiz
to'plamda o'lchanardi. **Baza qaytgach, bu to'siq yo'qoldi** va nishon
navbatning eng tepasiga chiqdi.

### 3.2. Harness

* Ishchi nusxa `$ROOT/w1` (repo ildizidan, `svetyoq-worker-copy-from-repo-root`).
* **Har mutant oldidan baza shablondan qayta yaratiladi:**
  `DROP DATABASE sveta_test; CREATE DATABASE sveta_test TEMPLATE sveta_tpl`
  (`svetyoq-dirty-db-fakes-killed`). `TRUNCATE` dan tez va ishonchli.
* Verdikt faqat `rc == 1` da KILLED (`svetyoq-mutation-harness-rc`).
* Ikki bosqich (`svetyoq-two-stage-mutation`): tor tanlov (43 test, ~12 s)
  nomzodni topadi, **butun to'plam** (4140 test, ~78 s) tasdiqlaydi.

### 3.3. Natija

| Bosqich | KILLED | SURVIVOR |
|---|---|---|
| Tor tanlov (43 test) | 10 | 11 |
| **Butun to'plam (4140 test)** | 10 | **11** — o'n bittalasi tasdiqlandi |
| Qulfdan keyin (54 test) | **20** | 1 (ekvivalent) |

Yolg'on survivor **yo'q**: tor tanlov va butun to'plam bir xil o'n bittani
berdi.

### 3.4. 🔴 Sabab bitta va tarkibiy

`digest_service` — «yupqa» modul: u hech narsa hisoblamaydi, faqat to'rtta
boshqa modulning so'rovini chaqiradi va natijasini `Digest` ning o'n uchta
maydoniga **taqsimlaydi**. O'lchanmagani aynan shu taqsimot edi.

`tests/test_daily_digest_db.py` ning fikstyurasi **bitta mintaqa, bitta kun**
quradi va faqat **hodisa** sonlarini tekshiradi. Shundan uch sinf:

**(a) Xabar chelaklari tekislangan.** Fikstyurada `total == reporters == 1`,
qolganlari `0`. Ya'ni beshala chelakni o'zaro almashtirish ko'rinmaydi:

* **M04** — `outage` ↔ `restored` almashtirildi → SURVIVOR;
* **M05** — `reports_total = reports.outage` → SURVIVOR;
* **M06** — `reporters = reports.total` → SURVIVOR.

**(b) Uchta chelak umuman to'ldirilmagan.** `audit_log`, `notifications` va
`outbox` ga bironta test qator qo'ymagan, ya'ni ularning **oynasi** ham,
chaqiruvining o'zi ham o'lchanmagan:

* **M07** — moderatsiya oynasi `[end, end)` ga siqildi → bo'sh lug'at,
  hisobotda «smena hech nima qilmadi» deb ko'rinardi → SURVIVOR;
* **M10** — bildirishnoma oynasi `[start, start)` ga siqildi →
  `digest.warning.notifications_failed` butunlay yo'qolardi → SURVIVOR;
* **M08** — `outbox_pending = 0` doimiy → E13-a ning yagona ko'rsatkichi
  o'lardi → SURVIVOR.

**(c) Mintaqa bitta, `now=` esa o'qilmaydi.**

* **M17** — `mark_delivered` dan `region_id` sharti olib tashlandi →
  bitta mintaqaning yetkazilishi **qo'shnisini** ham yuborilgan deb
  belgilardi va u hech kimga yetib bormasdi → SURVIVOR;
* **M19** — `load` dan `region_id` olib tashlandi →
  `GET /api/v1/admin/digest` boshqa mintaqaning sonlarini ko'rsatardi →
  SURVIVOR;
* **M14**, **M18** — `store`/`mark_delivered` `now=` argumentini tashlab
  `datetime.now()` ga o'tdi. Mavjud test argumentni **uzatardi**, lekin
  natijani **o'qimasdi** → SURVIVOR.

### 3.5. O'lganlari (nima allaqachon qulflangan edi)

M01 (davr teskari), M02/M03 (`queue_now` ning `min_radius_m` i), M09
(`open_now` ↔ `queue_now`), M11 (`day` manbai), M12 (`ON CONFLICT` kaliti),
M13 (`store` ning qaytimi teskari), M15 (`digest_date` = bugun), M16
(`mark_delivered` dan kun sharti), M20 (`load` dan kun sharti).

**M20 ning o'limi tasodifiy edi:** uni `scalar_one_or_none` ning
`MultipleResultsFound` i o'ldirgan, kunni tekshiradigan tasdiq emas.

### 3.6. Ekvivalent

**M21** — `scalar_one_or_none()` → `scalars().first()`. `daily_digest` ning
birlamchi kaliti `(region_id, digest_date)`, ya'ni ikkinchi qator bo'lishi
**mumkin emas**. Lekin bu qorovul bekorga turmaydi — aynan u M20 ni
o'ldirgan, shuning uchun yangi testda `load` ning **ikkala** sharti ham
ochiq ajratildi (§6 ning ikki testi).

---

## 4. Qulf — `tests/test_digest_service_contract.py`

11 test, olti bo'lim, `requires_db`:

| § | Yopilgan | Usul |
|---|---|---|
| 1 | M04, M05, M06 | beshala chelak **turli** songa ega: `total=5`, `outage=3`, `restored=2`, `unassigned=1`, `reporters=4`; assimetriya testning **o'zida** tekshiriladi (`len({...}) == 5`), ya'ni fikstyura kelajakda tekislanib qolsa darhol yiqiladi |
| 2 | M07 | `audit_log` ga uch harakat kun ichida, ikkitasi tashqarida; chegaraviy lahza (`period.end`) **ertangi** kunniki |
| 3 | M10 | `notifications` — `sent`/`failed` kun ichida, `sent` chegarada, `queued` (`sent_at IS NULL`) sanalmaydi |
| 4 | M08 | `outbox` ga uch qator, ikkitasi yopilmagan → `outbox_pending == 2` |
| 5 | M14, M18 | `now=` bazadan **qayta o'qiladi**; sanalar o'tmishda (2026-08-08), ya'ni `datetime.now()` ga tushish bir yildan katta farq beradi |
| 6 | M17, M19 | ikkinchi (`qo'shni`) mintaqa har tekshiruvda **teginilmagan** qolishi shart; `load` uchun mintaqa ham, kun ham alohida ajratiladi |

Tozalash: `audit_log` va `outbox` da `region_id` yo'q, shuning uchun
`clean_audit_and_outbox` fikstyurasi boshlang'ich `MAX(id)` ni eslab qoladi
va oxirida faqat undan kattasini o'chiradi.

---

## 5. Qaror va rad etilgan variantlar

* **Mahsulot kodi tegilmadi.** O'n bittala survivor — **test** tuynugi,
  kod nuqsoni emas: har bir shart kodda to'g'ri yozilgan, uni ajratadigan
  holat fikstyurada yo'q edi (`svetyoq-fixture-must-separate`).
* **Mavjud `test_daily_digest_db.py` kengaytirilmadi.** Yangi fayl
  yaratildi: eski fayl «kunlik hisobot **umuman** ishlaydimi» ni
  tekshiradi, yangisi esa **ulash qatlamining** kontraktini. Ikkisini
  aralashtirsak, keyingi run qaysi tasdiq nima uchun turganini bilmasdi.
* **M21 ni qulflashga urinilmadi.** U ekvivalent, ya'ni test yozish
  bazaning birlamchi kalitini takrorlashdan boshqa narsa bermasdi.
  O'rniga uning **qorovullik roli** fayl docstringida yozib qo'yildi.
* **`pytest-xdist` o'rnatilmadi.** Ikki yadro va bitta umumiy baza —
  parallel testlar bir-birining qatorlarini ko'rardi.

---

## 6. Keyingi qadam

1. 🟢 **Baza endi bor** — navbatning «faqat `requires_db` dan chaqiriladi»
   to'sig'i yo'qoldi. Navbat: `app/bot/handlers.py` (404 qator),
   `app/geo/models.py` (251), `app/api/openapi.py` (227),
   `app/jobs/refresh_coverage.py` (201), `app/stats/export.py` (193),
   `app/clustering/lookup.py` (183), `app/bot/keyboards.py` (183),
   `app/db/session.py` (161). Oxirgi ikkitasining mazmuni **SQL da**,
   ya'ni ularni endi haqiqiy PostGIS ustida o'lchash kerak.
2. 👤 `100_sec_yozuvni_yopish_ad837191.md` hamon turibdi.
3. 👤 eski ochiq savollar o'zgarmadi (E8-b `DIGEST_CHAT_IDS`, E13-a
   `jobs` profili, `/map` javobidagi dislaymer va h.k.).

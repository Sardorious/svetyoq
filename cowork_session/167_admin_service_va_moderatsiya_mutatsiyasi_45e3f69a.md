# 167-run — sandbox qaytdi; `admin/service.py` qulflandi va `reports/moderation.py` o'lchandi

**Sana:** 2026-08-19
**Sessiya:** `local_45e3f69a-…`
**Epic:** E8 (moderatsiya) — test qatlami

---

## 1. Boshlanish holati

`INDEX.md` ning «Qayerda to'xtadik» qatori 166-runni ko'rsatardi va uch
band qoldirgan edi:

1. 🔴 sandbox tiklanganda **birinchi ish** — bazasiz to'plamni yurgizib
   164 ning (+49) va 166 ning (21) testlarini tasdiqlash; ikkalasi ham
   **o'lchanmagan da'vo** edi;
2. shundan keyin `app/reports/moderation.py` ustida haqiqiy mutatsiya
   o'lchovi (166 unga qulf yozgan, lekin verdikt olinmagan);
3. navbat o'zgarmagan: `bot/handlers.py`, `geo/models.py`, `api/openapi.py`
   va h.k.

## 2. 🟢 Sandbox tirik

Birinchi bir necha `mcp__workspace__bash` chaqiruvi `Workspace still
starting` qaytardi (`VM_DISK_SPACE_INSUFFICIENT` **emas**), keyin muhit
ko'tarildi:

```
/dev/sda1  9.6G  5.1G  4.5G  54% /
/dev/sdc   9.8G  332K  9.3G   1% /sessions
```

Ya'ni 165/166 ning bloki yopildi. `/sessions` **bo'sh** — 141-rundan beri
birinchi marta. Sabab 166 topgan `.vhdx` gipotezasi bilan mos: 👤
`reset-sandbox-vm.ps1` / `cleanup-sessions.ps1` ni yurgizgan bo'lishi
kerak (agent buni tasdiqlay olmaydi, faqat natijani ko'radi).

### Muhitni tiklash retsepti (yangi, `/tmp` emas)

`/sessions` bo'sh bo'lgani uchun bu safar hamma narsa **`/sessions` da**
qurildi, `/tmp` da emas:

```
export TMPDIR=$PWD/tmp HOME=$PWD MAMBA_ROOT_PREFIX=$PWD/mroot \
       CONDA_PKGS_DIRS=$PWD/pkgs XDG_CACHE_HOME=$PWD/cache
micromamba create -p $PWD/mroot/envs/py311 -c conda-forge python=3.11
```

Keyin `pip install` uch partiyada (bittasi ham 300 s dan oshmadi).

### 🔴 Yangi (yoki qayta tasdiqlangan) qoida — mount ustida test yurgizilmaydi

`H:` mounti ustida butun bazasiz to'plam **180 s ga sig'madi** (bash
uzildi). Repo `/sessions/.../work/repo` ga ko'chirildi (`cp -r` — 73 s,
59 MB) va o'sha yerda **44 s** da yurdi. Ya'ni ko'chirish bir marta
to'lanadi va keyin har chaqiruv 4 barobar arzon.

## 3. (1) Qoldirilgan da'volar yopildi

```
3837 passed, 1 skipped, 298 deselected in 44.63s
ruff: All checks passed!
```

Ya'ni 164 ning `test_security_posture_contract.py` dagi 8–12-bo'limlari
va 166 ning `test_moderation_users_contract.py` — **yashil**.

To'plangan (o'lchangan) sonlar:

| fayl | yig'iladigan test |
|---|---|
| `test_security_posture_contract.py` | 88 |
| `test_moderation_users_contract.py` | 26 (166 «21 test» degan — parametrizatsiyadan keyin 26) |
| `test_data_model_contract.py` | 68 |

⚠️ **Arifmetika to'liq yopilmadi.** 163 «3699» yozgan; 3699 + 49 + 26 =
3774, o'lchangani esa 3837 (yangi fayl qo'shilgunga qadar). 63 farq
qayerdan kelgani tekshirilmadi — ehtimol 164 ning «+49» i ham
parametrizatsiyadan oldingi son. **Xulosa uchun muhim emas:** to'plam
yashil, ya'ni ikkala da'vo ham tasdiqlangan; lekin «+N test» ni jurnalga
yozganda bundan keyin **yig'ilgan** (collected) son yozilsin.

## 4. Yangi nishon — `app/admin/service.py`

166 ning `grep` usuli bir qavat yuqoriga ko'chirildi va **aynan shu
tuynuk** topildi:

* `app/admin/service.py` (136 qator) ni butun repoda **bitta** test fayli
  import qiladi — `tests/test_admin_moderation_db.py`, u esa
  `@pytest.mark.requires_db`;
* qolgan barcha murojaatlar (`app/release/business_*.py`,
  `app/core/glossary.py`) — reyestrlardagi **satrlar**
  (`"app.admin.service:reject_outage"`), ya'ni mavjudlik havolasi.

Modulning butun vazifasi — uchlik: **ruxsat → o'zgarish → audit**. Uchala
bo'g'in ham bazasiz o'lchanmagan edi.

**Yozilgani:** `sveta/tests/test_admin_service_contract.py`,
**41 test** (yig'ilgan), yetti bo'lim. Baza yo'q: `session` — nishon
obyekt, to'rtta qo'shni funksiya (`clustering.moderate`,
`users.set_blocked`, `users.set_trust_score`, `audit.record`)
`monkeypatch` bilan yozib boruvchi qo'g'irchoqqa almashtiriladi.

Qulflangani:

* **ruxsat o'zgarishdan oldin** — `_viewer()` bilan to'rtala amal, qo'shni
  modullar «tegilsa yiqiladigan» qilingan (`sealed` fikstyurasi);
* **aynan qaysi ruxsat** — haqiqiy `Actor` buni ajratmaydi (`moderator`
  `OUTAGE_REJECT` va `OUTAGE_MERGE` ni birdek beradi), shuning uchun
  duck-type `_RecordingActor` so'ralgan `Permission` ni yozib oladi;
  `trust/moderator` qatori esa `USER_TRUST` ning `moderator` da
  yo'qligini haqiqiy rol bilan qulflaydi;
* **chaqiruvlar tartibi** — `["require", "moderate", "record"]`;
* **argumentlar** — `reject` da `merged_into` **uzatilmaydi**
  (`kwargs == {"target": REJECTED}`), `merge` da `outage_id` va
  `merged_into` almashmaydi (ikkalasi ham `uuid.UUID`);
* **audit** — `USER_BLOCK` ↔ `USER_UNBLOCK` ikki xil amal, `object_id`
  `merge` da **manba** hodisa;
* **`dict(change.after)` nusxasi** — `reason` qaytarilgan obyektga
  oqib ketmaydi; qoida to'rtala amalda parametrizatsiya bilan;
* `if reason:` — bo'sh satr va `None` ikkalasi ham kalit qo'shmaydi;
* **imzo** — faqat `session` pozitsion, qolgani nomli; `reason` sukut
  `None`; modulda boshqa ochiq korutina **yo'q** (ro'yxat yopiq).

## 5. `app/reports/moderation.py` — MUTATSIYA O'LCHOVI

Ikki bosqichli harness (`work/harness/`, repo **tashqarisida**;
verdikt faqat `rc==1` da KILLED). Ishchi nusxalar `work/r1`, `work/r2`.

**29 mutatsiya → 23 KILLED, 6 SURVIVOR (21 %).**

Oltalasi ham butun bazasiz to'plamda (3837 test) birma-bir tasdiqlandi —
yolg'on survivor yo'q.

### 🔴 Topilma — omon qolganlarning hammasi bitta sinfda

166 ning 1–7-bo'limlari `SELECT`/`UPDATE` ning **matnini** tekshiradi.
Omon qolgan mutatsiyalarning birortasi ham matnni o'zgartirmaydi: ular yo
**bog'langan parametrni**, yo shartning **ichini** almashtiradi.

| ID | mutatsiya | nima bo'lardi |
|---|---|---|
| M13 | kichik so'rovdan `.where(Report.user_id == User.id)` olib tashlanadi | moderator har bir foydalanuvchi qarshisida **butun jadvaldagi** xabarlar sonini ko'rardi |
| M20 | `values(is_blocked=blocked)` → `not blocked` | bloklash **ochib yuborardi**, ochish — bloklardi |
| M21 | `update(User)` dan `.where(...)` olib tashlanadi | bitta bosish bilan **hamma** foydalanuvchi bloklanardi |
| M26 | `values(trust_score=score)` → `TRUST_MAX` | har qanday tuzatish `100` yozardi, audit esa `55` deb yozardi |

M13 ning sababi alohida qimmatli: 166 da **aynan shu mutatsiyaga qarshi**
yozilgan test bor (`test_the_report_count_is_counted_over_reports`,
`assert "from reports" in sql`), lekin u **ajratmaydi** — bog'lanish
o'chirilganda ham kichik so'rov `FROM reports` bo'lib qolaveradi.
`svetyoq-fixture-must-separate` sinfining matn darajasidagi ko'rinishi.

### Ikkita EKVIVALENT

* **M14** — `.select_from(Report)` → `.select_from(User)`. Kompilyatsiya
  qilingan SQL **belgi-ba-belgi bir xil**: `.correlate(User)` `users` ni
  `FROM` dan chiqaradi, `Report` esa `WHERE` dan avtomatik keladi. Dalil
  kod o'qishdan emas, ikkala variantning kompilyatsiya natijasini
  solishtirishdan olindi. 166 ning docstringi bu mutatsiyani «xavfli» deb
  yozgan — aslida u **kuzatib bo'lmaydigan**.
* **M28** — `UserChange(user_id=user_id)` → `user_id=row.id`. `read_user`
  `User.id` ni `where User.id == user_id` bilan tanlaydi, ya'ni
  `row.id == user_id` **har doim**.

### Qulf

`tests/test_moderation_users_contract.py` ga **8-bo'lim** qo'shildi
(+5 test, fayl 26 → 31). Usul: `compile(dialect=postgresql.dialect())`
ning **`.params`** i (matn emas) va bo'shliqlari normallashtirilgan SQL
dagi shart matni (`"WHERE reports.user_id = users.id"`,
`"WHERE users.id ="`).

Qayta o'lchov: **M13, M20, M21, M26 — KILLED**; M14 va M28 — ekvivalent,
qulflanmaydi.

**Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar tegilmadi.**

## 6. Yakuniy o'lchov

```
3842 passed, 1 skipped, 298 deselected in 43.89s
ruff check .  →  All checks passed!
```

`requires_db` ning **298** testi hamon yurgizilmagan.

## 7. Keyingi qadam

1. 🟢 **Sandbox sog'lom va `/sessions` da 8.5 GB bo'sh.** Ya'ni
   `micromamba` bilan **PostGIS** ni ko'tarish endi mumkin
   (`svetyoq-postgis-in-sandbox`, `svetyoq-requires-db-needs-tcp`:
   `listen_addresses=127.0.0.1`, TCP li `DATABASE_URL` shart, aks holda
   hammasi jimgina `skip`). **298 `requires_db` testi 126-rundan beri
   yurgizilmagan** — keyingi run shuni olsin.
2. Mutatsiya navbati o'zgarmadi: `app/bot/handlers.py` (404),
   `app/geo/models.py` (251), `app/api/openapi.py` (227),
   `app/jobs/refresh_coverage.py` (201), `app/stats/export.py` (193),
   `app/clustering/lookup.py` (183), `app/bot/keyboards.py` (183),
   `app/db/session.py` (161).
3. Yangi nishon sinfi ochildi: `app/admin/digest_service.py` ni ham
   **faqat** `test_daily_digest_db.py` (`requires_db`) import qiladi —
   `moderation.py`/`admin/service.py` bilan bir xil tuynuk.
4. 👤 `100_sec_yozuvni_yopish_ad837191.md` hamon turibdi (agent o'chira
   olmaydi — `allow_cowork_file_delete` runni to'xtatadi).
5. 👤 eski ochiq savollar o'zgarmadi.

# 147-run — 145 ning raqami tasdiqlandi, obuna va fan-out qulflandi

**Sessiya:** `local_86dfa894` · **Sana:** 2026-08-13 · **Epic:** E13
(bildirishnomalar) · **Natija:** ✅ 22 mutatsiya → 15 KILLED / 7 SURVIVOR,
yettalasi qulflandi; 3733 passed, 1 skipped; `ruff` toza; mahsulot kodi
tegilmadi.

---

## 1. Nishon qayerdan olindi

146-run «147 uchun tartib» ni qoldirgan edi:

1. 👤 145 ni (`notifications/`, 10 mutatsiya) **bazasiz** to'plam bilan
   ham qayta o'lchash — uning raqami yarim;
2. `notifications/subscriptions.py` va `service.py`;
3. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi;
4. 👤 `cowork_session/` dagi nusxa juftliklari — agent o'chira olmaydi.

Bu run (1) va (2) ni bajardi. (3) keyingi runga, (4) odamga qoladi.

---

## 2. Muhit (137→147 seriyasining retsepti)

`/tmp` 146-rundan saqlanib qolgan: `micromamba` muhitlari `py311` va `pg`
joyida. Yangidan kerak bo'lgani — **baza**: `/tmp/pgdata146` yangi sandboxda
`nobody:700` bo'lib qoladi (bu bilim 143-rundan beri o'zgarmadi), shuning
uchun `initdb -D /tmp/pgdata147`, port `55147`.

```bash
export TMPDIR=/tmp HOME=/tmp/h XDG_CACHE_HOME=/tmp/cache CONDA_PKGS_DIRS=/tmp/pkgs
export MAMBA_ROOT_PREFIX=/tmp/mamba
export PATH=/tmp/mamba/envs/pg/bin:/tmp/mamba/envs/py311/bin:$PATH
export PGDATA=/tmp/pgdata147 PGPORT=55147 PGHOST=127.0.0.1
pgup() { pg_ctl -D /tmp/pgdata147 -o "-p 55147 -k /tmp -c listen_addresses=127.0.0.1" \
         -l /tmp/pg147.log start >/dev/null 2>&1; sleep 2; }
```

⚠️ **`pgup` ni HAR bash chaqiruvida qayta chaqirish shart.** Bir marta
unutildi va natija jimgina yolg'on bo'ldi: `213 passed` o'rniga
`185 passed, 28 skipped` — `conftest._db_reachable` TCP ga qaraydi va
server o'lgani uchun butun `requires_db` qismi **skip** bo'ldi. Chiqishda
xato yo'q, faqat «hammasi yashil». Bu 142-run topgan qirraning yangi
ko'rinishi.

**Uchta ishchi nusxasi** — `/tmp/w1`, `/tmp/w2`, `/tmp/w3`, **repo
ildizidan** (`rsync -a --exclude .git`), ya'ni `deploy-server` va boshqa
ildiz fayllari ham joyida (146 ning «to'liq bo'lmagan ishchi nusxasi»
saboqi). Har ishchining **o'z bazasi**: `sveta1`, `sveta2`, `sveta3`,
`sveta_tpl` shablonidan. Tiklash — `/tmp/reset147.sh N`, 0.4 s.

**Baseline har ishchida alohida** olindi (146 ning qoidasi):
`3726 passed, 1 skipped` — uchalasida ham.

---

## 3. (1) 145 ning qayta o'lchovi — sakkizala survivor haqiqiy

146 shubhalangan edi: 145 `notifications/queries.py` va `outbox.py` ni
faqat `-m requires_db` da o'lchagan, ya'ni «8 survivor» ning ba'zisi
bazasiz to'plamda o'lgan bo'lishi mumkin va o'shanda 145 qo'shgan test
ortiqcha bo'lardi.

O'sha sakkizta mutatsiya `-m "not requires_db" tests/` (3435 test) bilan
qayta yurgizildi:

| Mutatsiya | Bazasiz to'plam |
|---|---|
| `nq-since-gt` | SURVIVED |
| `nq-until-le` | SURVIVED |
| `nq-pending-not-null` | SURVIVED |
| `ob-claim-lt` | SURVIVED |
| `ob-order-id-first` | SURVIVED |
| `ob-no-limit` | SURVIVED |
| `ob-skip-locked-off` | SURVIVED |
| `ob-mark-no-guard` | SURVIVED |

**Sakkizdan sakkiztasi.** Ya'ni 145 ning «2 KILLED / 8 SURVIVOR» i butun
to'plam bo'yicha ham **to'g'ri**, qo'shilgan sakkizta test keraksiz emas.

146 ning qoidasi (`-m requires_db` — tor tanlov, verdikt butun to'plamdan)
**bekor qilinmaydi**: u shubhani asosli qilgan va `fc-drop-layer` bilan
empirik isbotlangan. Bu nishonda u natijani o'zgartirmadi, xolos.

⚠️ Birinchi partiya `bash` limitida uzildi va `outbox.py` ikkita ishchida
mutatsiyalangan qoldi — **repo tegilmadi** (146 ning nusxada ishlash
qarori aynan shu uchun). Ishchilar repo fayli bilan tiklandi, `diff`
tozalikni tasdiqladi.

---

## 4. Asbob yangiligi — ikki bosqichli o'lchov

Bu run ning asosiy tejamkorligi. Butun to'plam bitta ishchida 77 s,
uchtasi parallel — har biri 115–123 s. 22 mutatsiyani shunday o'lchash
bitta `bash` chaqiruviga (~178 s) **sig'maydi**.

Yechim:

1. **1-bosqich — tor nishon to'plami** (9 fayl: `test_notifications_db`,
   `test_notifications_outbox`, `test_notification_domain_contract`,
   `test_notification_channels_contract`, `test_geo_sql_expressions`,
   `test_bot_subscription_labels`, `test_bot_subscription_keyboard`,
   `test_notify_params`, `test_notifications_render` — 213 test, 10 s).
2. **2-bosqich — faqat SURVIVOR lar butun to'plamda** (`-x tests/`).

Nima uchun bu 144/146 ning tuzog'iga tushmaydi: tor tanlov yolg'on
**`SURVIVOR`** beradi, yolg'on **`KILLED`** bermaydi — agar tanlovning
baseline i yashil bo'lsa, undagi yiqilish faqat mutatsiyadan kelib
chiqadi. Ya'ni 1-bosqichning `KILLED` i yakuniy, `SURVIVED` i esa faqat
**nomzod** va majburiy eskalatsiya qilinadi. Narx: 22×115 s o'rniga
22×10 s + 7×115 s.

---

## 5. (2) 22 mutatsiya — natija

### `app/notifications/subscriptions.py` (12)

| ID | Nima buziladi | 1-bosqich | Butun to'plam |
|---|---|---|---|
| `sb-min-le` | `< MIN_RADIUS_M` → `<=` (200 m ning o'zi rad etiladi) | KILLED | — |
| `sb-max-ge` | `> max_radius_m` → `>=` | KILLED | — |
| `sb-limit-gt` | `>= limit` → `>` (chegaradan bitta ortiq) | KILLED | — |
| `sb-list-order` | `(created_at, id)` → `(id, created_at)` | SURVIVED | **SURVIVED** |
| `sb-list-inactive` | ro'yxatdan `is_active` filtri olinadi | KILLED | — |
| `sb-count-inactive` | sanoqdan `is_active` filtri olinadi | SURVIVED | **SURVIVED** |
| `sb-remove-any-owner` | `remove()` dan egalik sharti olinadi | KILLED | — |
| `sb-remove-no-active` | `remove()` dan `is_active` sharti olinadi | SURVIVED | **SURVIVED** |
| `sb-dwithin-no-event-r` | `radius_m + radius_m` → faqat obuna radiusi | KILLED | — |
| `sb-nearest-desc` | `DISTINCT ON` eng uzoqni qoldiradi | KILLED | — |
| `sb-latlon-swap` | `ST_Y, ST_X` → `ST_X, ST_Y` | KILLED | — |
| `sb-labels-empty` | `if not ids` → `if ids` | KILLED | — |

### `app/notifications/service.py` (10)

| ID | Nima buziladi | 1-bosqich | Butun to'plam |
|---|---|---|---|
| `sv-pending-no-failed` | `PENDING_STATUSES` dan `failed` olinadi | KILLED | — |
| `sv-complete-true` | `failed == 0` → `True` | KILLED | — |
| `sv-resolved-from-closed` | yopilish xabari `sent` emas, `closed` dan | KILLED | — |
| `sv-intents-no-filter` | `if m.user_id in allowed` olinadi | KILLED | — |
| `sv-onconflict-user-only` | kalit `(user_id, outage_id)` → `(user_id)` | KILLED | — |
| `sv-mark-sent-inverted` | `if sent_at is not None` → `is None` | SURVIVED | **SURVIVED** |
| `sv-dropped-as-failed` | bloklangan chat `failed` ga tushadi | KILLED | — |
| `sv-report-drop-dropped` | `skipped + dropped` → `skipped` | SURVIVED | **SURVIVED** |
| `sv-count-matches` | `len(values)` → `len(matches)` | SURVIVED | **SURVIVED** |
| `sv-pending-order` | `ORDER BY id` → `id DESC` | SURVIVED | **SURVIVED** |

**15 KILLED, 7 SURVIVOR** — yettalasi ham butun to'plamda tasdiqlandi,
ya'ni birortasi ham yolg'on emas.

---

## 6. Survivorlarning uch oilasi

**(a) Tartib — fikstyurada har doim bitta qator turardi.**
`list_for_user` `(created_at, id)` bo'yicha tartiblaydi, `_pending_rows`
esa `id` bo'yicha. Ikkala testda ham ro'yxatda **bitta** element bo'lgani
uchun `ORDER BY` ni birorta test ajratmasdi. Bu 143-run ning naqshining
aynan o'zi: qulf bor, uni ajratadigan **holat** yo'q.

Yangi testlar tartibni ataylab qarama-qarshi qo'yadi: `sorted([uuid4(),
uuid4()])` bilan ikkita UUID olinadi va **kattarog'iga** erta `created_at`
beriladi (`created_at` ni `add()` orqali belgilab bo'lmaydi — u
`server_default`, shuning uchun oshkora `INSERT`).

**(b) Yumshoq o'chirishning ikkinchi qirrasi.**
`remove()` `is_active = false` qo'yadi, qator jadvalda qoladi
(`notifications.subscription_id` FK). Mavjud testlar o'chirishdan keyin
**ro'yxatni** tekshirardi, lekin o'sha obunani hech qachon **qayta**
so'ramasdi:

* `remove()` dan `is_active` sharti yo'qolsa `UPDATE` nofaol qatorni ham
  topadi va bot allaqachon yo'q obuna uchun «o'chirildi» deb javob berardi;
* `count_for_user` dan filtr yo'qolsa chegaraga yetgan odam bitta obunani
  o'chirib ham yangisini qo'sha olmasdi — va bu holatdan **umuman** chiqib
  keta olmasdi, chunki qatorlar jismonan o'chmaydi.

**(c) Hisobot maydonlari — «yuborildi» tekshiriladi, «qayd» tekshirilmaydi.**
`sent_at` yozilmasa bildirishnomalar yuborilaveradi, lekin
`status_counts_between` va `05` §10 ning kunlik kesimi jimgina **nolga**
aylanadi. `DeliveryReport.skipped` faqat `prepare` ni sanasa
`planned == sent + failed + skipped` tengligi buziladi va
`notifications_skipped` metrikasi eng ko'p uchraydigan sababni (botni
bloklagan odam) ko'rsatmaydi.

`sv-count-matches` alohida turadi: `_create_intents` ning qaytargan
qiymatini **hech kim o'qimaydi** — `prepare()` uni tashlab yuboradi.
Ya'ni mutant mahsulot xulq-atvorini o'zgartirmaydi, lekin **ekvivalent
emas**: funksiyaning hujjatlangan kontrakti «yozilgan qatorlar soni».
Test uni to'g'ridan-to'g'ri o'lchaydi; qiymatning o'lik ekani
`PROGRESS.md` ning «Ochiq savollar» iga 👤 belgisi bilan yozildi.

---

## 7. Qulflar

`tests/test_notifications_db.py` ga **7 test** qo'shildi (yangi fayl
yaratilmadi — fikstyuralar shu yerda):

| Test | Qaysi survivorni qulflaydi |
|---|---|
| `test_list_is_ordered_by_creation_not_by_identifier` | `sb-list-order` |
| `test_removing_the_same_subscription_twice_is_reported` | `sb-remove-no-active` |
| `test_removed_subscription_frees_a_slot_in_the_limit` | `sb-count-inactive` |
| `test_pending_rows_are_served_oldest_identifier_first` | `sv-pending-order` |
| `test_blocked_bot_is_counted_as_skipped_in_the_report` | `sv-report-drop-dropped` |
| `test_delivery_stamps_the_moment_it_was_sent` | `sv-mark-sent-inverted` |
| `test_intent_count_is_what_was_written_not_what_matched` | `sv-count-matches` |

Qayta o'lchov: **yettalasi ham KILLED**, ya'ni 22/22.

---

## 8. O'lchovlar

| | |
|---|---|
| Butun to'plam | **3733 passed, 1 skipped** (146: 3726) |
| `-m requires_db` | **298 passed** (146: 291) |
| Bazasiz qism | **3435 passed, 1 skipped** (o'zgarmadi) |
| `ruff check app tools tests alembic` | toza |
| Migratsiya | yo'q |
| Mahsulot kodi | tegilmadi |

Yakuniy o'lchov `/tmp/w1/sveta` da olindi va `diff -r --brief` bilan repo
bilan **aynanligi** isbotlandi (`__pycache__`, `.ruff_cache` bundan
tashqari).

---

## 9. 148 uchun tartib

1. `notifications/` ning qolgan uchligi — `render.py`, `sender.py`,
   `events.py` va `bot/notifier.py` (E13 ning oxirgi o'lchanmagan qismi).
   ⚠️ `render.py` 127-runda **bazasiz** o'lchangan (12/12), lekin
   `sender.py` va `events.py` umuman o'lchanmagan.
2. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi.
3. 👤 `service._create_intents` ning o'lik qaytargan qiymati.
4. 👤 `cowork_session/` dagi nusxa juftliklari
   (`100_…_70dfe57e` ↔ `144_…_70dfe57e`, to'rtta `28_*`) — agent
   `allow_cowork_file_delete` ni chaqira olmaydi (CLAUDE.md §1).

# 131-run — «toza modul» o'rniga toza **funksiya** reyestri (statik audit)

**Sana:** 2026-08-13
**Epic:** JOBS / OBS / E14 (mutatsiya qamrovi — nishonlar navbati)
**Natija:** ⛔ kod yurgizilmadi (sandbox ko'tarilmadi) · ✅ statik audit,
nishon navbati tuzatildi · kod/test/migratsiya **tegilmadi**

---

## 1. Nima bo'ldi — sandbox umuman ko'tarilmadi

Run boshidagi birinchi `bash` chaqirig'i (repo `ls` + `INDEX.md` tepasi)
yiqildi:

```
bash failed on resume, create, and re-resume.
resume: RPC error -1: ensure user: useradd failed: exit status 1:
  useradd: /etc/passwd.80209: No space left on device
create: RPC error -1: ensure user: useradd failed: exit status 1:
  useradd: /etc/passwd.80210: No space left on device
```

Yana ikki marta urinildi (`echo ok`, `df -h`) — **aynan bir xil xato**,
faqat `/etc/passwd.NNNNN` raqami o'zgardi. Uchinchidan keyin to'xtatildi.

**Bu 130 dan sifat jihatidan boshqacha holat.** Bosqichlar:

| Run | Holat | Nima yurardi |
|---|---|---|
| 122–129 | `/` da 62 → 15 MB | `pytest` yurardi, `initdb` uchun joy yo'q → `requires_db` skip |
| 130 | `/` run o'rtasida 0 | `pytest` faqat `TMPDIR=/dev/shm/tNNN` bilan ko'tarilardi |
| **131** | foydalanuvchi yaratilmaydi | **hech narsa** — `df`, `ls` ham yo'q |

130 ning `/dev/shm` retsepti bu bosqichda **yaramaydi**: unga yetib
borish uchun ham ishlaydigan sandbox kerak. Ya'ni
`cleanup-sessions.ps1` endi `requires_db` ni emas, **butun runni**
bloklaydi — bazasiz mutatsiya seriyasi ham `pytest` talab qiladi.

Shu sababdan run `Read`/`Grep` bilan **statik audit** rejimida
o'tkazildi. Hech qanday fayl yaratilmadi va o'zgartirilmadi (holat
fayllaridan tashqari), `git` chaqirilmadi.

---

## 2. Topilma — «toza modul» noto'g'ri granularlik

124–130 runlarining nishon navbati `app/` ni **modul** kesimida
sanaydi: «bazasiz va HTTP siz modul 92 ta, o'lchangani 42 ta». Shu
hisob-kitob sababli `stats/service.py` bilan `geo/queries.py` «bazaga
tegadi» degan izoh bilan **125-rundan beri** kutmoqda.

Tekshirildi: `AsyncSession` ni import qiladigan modullar — **23 ta**
(`Grep "from sqlalchemy.ext.asyncio import AsyncSession"`). Ularning
ichida sinxron, bazasiz funksiyalar bor
(`Grep "^def [a-z_]+\("`). Ya'ni **tozalik modulning emas,
funksiyaning xossasi** — modul kesimidagi hisob ham ortiqcha sanaydi,
ham kam sanaydi.

### 2.1. Bugunoq o'lchansa bo'ladigan toza funksiyalar

Bazasiz test fayli bilan allaqachon qoplangan (test fayllari
`Grep` bilan tasdiqlandi):

| Modul | Toza funksiyalar | Bazasiz test |
|---|---|---|
| `app/stats/service.py` | `floor_to`, `resolve_period`, `_coverage_input`, `_index_for`, `region_index`, `public_limits` | `tests/test_stats_service.py` — **18 test**, `requires_db` yo'q |
| `app/clustering/snapshot.py` | `compute_etag`, `empty_payload`, `_feature` | `tests/test_map_snapshot.py` |
| `app/geo/registry.py` | `pick_for_point`, `_from_row`, `invalidate` | `tests/test_region_registry.py` |
| `app/notifications/outbox.py` | `backoff_s` | `tests/test_notifications_outbox.py` |
| `app/notifications/subscriptions.py` | `params_from_config`, `_validated_radius` | `tests/test_notify_params.py` |
| `app/geo/pipeline.py` | `validate_point` | `tests/test_geo_*`, `test_privacy_jitter_contract.py` |
| `app/reports/intake.py` | `ensure_not_blocked` | `tests/test_reports_intake.py` |
| `app/admin/audit.py` | `jsonable`, `cli_actor` | `tests/test_admin_audit.py` |
| `app/clustering/lookup.py` | `decide`, `text` | `tests/test_clustering_lookup.py` |

Xulosa: 125 dan beri turgan «servis nishoni bazaga tegadi» degan sabab
**faqat modul nomiga** tayangan edi. `stats/service.py` ning Coverage
Index yadrosi (`region_index`, `_index_for`, `resolve_period`)
bazasiz o'lchanadi.

### 2.2. Teskari tomoni og'irroq — bazasiz testi UMUMAN yo'q

Bu funksiyalar faqat `requires_db` orqali **bilvosita** ishlaydi, u esa
**121-rundan beri yurmagan** (o'n run):

| Modul | Funksiyalar | Yagona qopqoq |
|---|---|---|
| `app/obs/collector.py` | `_age_s`, `_as_uuid`, `_reading` | `tests/test_metrics_api_db.py` (`requires_db`) — butun repoda `collector.` ga murojaat qiladigan **yagona** test |
| `app/clustering/repository.py` | `_to_outage_row`, `geog_point`, `_lat_lon`, `_outage_row_columns` | — |
| `app/reports/queries.py` | `_position` | — |
| `app/bot/service.py` | `_label` | — |
| `app/notifications/subscriptions.py` | `_point`, `_lat_lon` | — |
| `app/notifications/outbox.py` | `_age_s` | — |

Eng qimmati — `collector._age_s`:

```python
def _age_s(value: datetime | None, now: datetime) -> float:
    if value is None:
        return AGE_UNKNOWN
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return max((now - aware).total_seconds(), 0.0)
```

`value.tzinfo` bo'lmasa UTC deb o'qish — 128-run (`core/timeutil.as_utc`)
va 130-run (`notifications/events._iso`) ikki marta topgan sinfning
**uchinchi nusxasi**, va bu safar u `/metrics` ning
`snapshot_age_seconds` iga chiqadi (`05` §10 ogohlantirishi).
Yonidagi `max(…, 0.0)` qisqichi va `_as_uuid` ning `if not value`
qorovuli ham hech qayerda bazasiz o'lchanmaydi.

**Qoida (131):** nishon navbatiga qo'shishdan oldin savol modul haqida
emas, funksiya haqida berilsin — «bu funksiya bazasiz chaqirilyaptimi?»
Javob «yo'q» bo'lsa, mutatsiyadan **oldin** bazasiz test kerak.

---

## 3. Statik bashorat — `app/jobs/daily_digest.py` ning bazasiz yarmi

O'lchov **emas**; 132-run buni `pytest` bilan tekshiradi. Nishon:
`chat_ids`, `deliver`; mavjud testlar — `tests/test_daily_digest.py`
(5 test: `test_chat_ids_are_parsed_and_deduplicated`,
`test_malformed_chat_id_is_skipped_not_fatal`,
`test_no_chat_ids_by_default`, `test_deliver_counts_successes`,
`test_one_broken_chat_does_not_stop_the_rest`).

**Kutilayotgan survivorlar:**

1. **`deliver` dagi `except PermanentSendError` tarmog'i hech qachon
   otilmagan.** `_Recorder` faqat `job.SendError` tashlaydi,
   `PermanentSendError` esa uning **avlodi** — butun `except
   PermanentSendError` blokini olib tashlash yetkazish sanog'ini
   umuman o'zgartirmaydi (`SendError` bloki uni ushlaydi). Farq faqat
   jurnal kalitida: `digest.chat_unreachable` ↔ `digest.send_failed`.
   Modulning o'z hujjati esa bu ikkovini ataylab ajratadi
   («`PermanentSendError` — muvaffaqiyatsizlik emas»).
2. **`chat_ids()` ning `raw is None` tarmog'i.**
   `settings.digest_chat_ids` faqat `tests/test_daily_digest_db.py`
   da patch qilinadi (`requires_db`), ya'ni bazasiz to'plam sozlamani
   konstantaga qotirib qo'yishni ko'rmaydi — 128-run ning `h3_cells`
   sinfi (sukut qiymat konstanta bilan teng bo'lgani uchun ajralmaydi).
3. **`log.warning` darajasi** (`digest.chat_id_malformed`,
   `digest.chat_unreachable`, `digest.send_failed`) — 130-run ning
   `log.error` → `log.debug` sinfi.

**Kutilayotgan ekvivalent:** bo'sh `entry` qorovuli
(`if not entry: continue`). Uni olib tashlansa `int("")` `ValueError`
beradi va o'sha `except` tarmog'i qatorni baribir tashlaydi — natija
bit-aynan bir xil, farq faqat jurnalda. Bu 126-run ning `admin/auth.py`
dagi bo'sh token qorovuli bilan bir xil holat.

**Birinchi o'tishda KILLED bo'lishi kutiladi:** `value not in result`
dedupe (test `[-100123, 456]` kutadi), `delivered += 1` ning `else`
blokida turishi (aks holda yiqilgan chat ham sanaladi), `except
ValueError` ning torayishi, `raw`/`settings` shartining teskarilanishi.

---

## 4. Nima qilinmadi va nima uchun

- **Test yozilmadi.** Yozilgan testni yurgizib bo'lmaydi, yashil
  to'plamga tekshirilmagan fayl qo'shish esa `CLAUDE.md` §2 ning «kod
  har doim ishlaydigan holatda qoldiriladi» qoidasini buzardi.
- **Mahsulot kodi tegilmadi.** Statik topilmalarning birortasi ham
  mahsulot defekti emas — hammasi test bo'shlig'i.
- **Vaqtinchalik fayl yaratilmadi** (`CLAUDE.md` §1 ning ⛔ bandi).
- **`git` chaqirilmadi.**

---

## 5. Keyingi qadam (132-run)

Sandbox tiklangach, shu tartibda:

1. `app/stats/service.py` ning bazasiz yarmini o'lchash — nishon **tor**:
   `tests/test_stats_service.py` (129 ning saboqi: keng nishon partiyani
   ~180 s limitiga uradi va mutatsiyalangan faylni repoda qoldiradi).
2. `app/obs/collector.py` ning uchala yordamchisiga **bazasiz test**
   yozish, `_age_s` ning naive tarmog'idan boshlab; keyin mutatsiya.
3. §3 dagi bashoratni o'lchov bilan tekshirish
   (`app/jobs/daily_digest.py`, nishon `tests/test_daily_digest.py`).
4. Disk bo'shagan bo'lsa — `-m requires_db` ni qayta o'lchash
   (oxirgi haqiqiy o'lchov: **121-run, 231 passed**) va `pg_ctl` ni
   **shartsiz `start`** bilan chaqirish (`EpicProgress.md` §6).

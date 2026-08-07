# 04 — E5: klasterlash (`local_b95ea26a`)

**Sana:** 2026-08-06, ~21:00–21:30 UTC
**Rejim:** `sveta-net-build` scheduled task (avtomatik run, odam yo'q)
**Natija:** 🔄 E5 kodi to'liq yozildi; CI tasdiqlashi kutilmoqda

---

## Run boshidagi holat

`INDEX.md` → «E2 kodi yozildi, sandbox yiqilgani uchun lint/test lokal
ishga tushmadi; keyingi qadam — CI, keyin E5».

`PROGRESS.md` → E1 ✅, E2 🔄, E4 🔄, qolgani ⬜. Bloklangan epic yo'q.

**Birinchi qadam:** sandboxni tekshirish.

```
mcp__workspace__bash → RPC error -1: ensure user: useradd failed: exit status 12:
                        useradd: cannot create directory /sessions/...
```

Uch marta urinildi (run boshida, o'rtasida, oxirida) — har safar bir xil xato.
**Ketma-ket ikkinchi run sandboxsiz.** Demak bu tasodif emas, muhitning
barqaror nosozligi.

**Qaror:** to'xtab qolmaslik (ko'rsatmaning §5). `ruff` va `pytest` siz ham
ishlash mumkin bo'lgan ish tanlandi — E5 klasterlash. Kod `Read`/`Write`/`Edit`
bilan yozildi, sifat nazorati — spetsifikatsiyani qatorma-qator solishtirish va
mavjud E1/E2 modullarining uslubiga qat'iy amal qilish.

---

## Nima yozildi

| Fayl | Ish |
|---|---|
| `app/clustering/geometry.py` | `haversine_m`, `centroid_step`, `grow_radius`, `clamp_radius` — toza, bazasiz |
| `app/clustering/independence.py` | `05` §4.3 ning fazoviy qismi: `>= 50 m` siyraklashtirish, `dedupe_by_user` |
| `app/clustering/status.py` | `OutageStatus`, `ALLOWED_TRANSITIONS`, `evaluate_status`, `IllegalTransitionError` |
| `app/clustering/repository.py` | `outages` bilan ishlash: `find_candidate`, `create_outage`, `load_state`, `open_outage_ids` |
| `app/clustering/service.py` | `assign()` va `evaluate()` — `05` §4.2 quvuri |
| `app/reports/queries.py` | `reports`/`users` ustidan tashqi interfeys (modul chegarasi) |
| `app/jobs/evaluate_outages.py` | `05` §8 fon vazifasi (60 s), `runner.register_jobs()` |
| `app/core/i18n/locales/{uz,ru}.json` | `error.illegal_transition` |
| `tests/test_clustering_geometry.py` | 11 test |
| `tests/test_clustering_independence.py` | 10 test |
| `tests/test_clustering_status.py` | 20 test |
| `tests/test_clustering_service_db.py` | 9 test, `@pytest.mark.requires_db` — oltin ssenariylar 1,2,3,4,6 |

**Migratsiya kerak bo'lmadi** — E5 sxemani o'zgartirmaydi.

---

## Qabul qilingan qarorlar va sabablari

### 1. Modul chegarasi: `clustering → reports`, teskarisi yo'q

`05` §1: modul boshqa modulning jadvaliga tegmaydi. Klasterlashga xabarlar
kerak, lekin `reports`/`users` — boshqa modulniki. Yechim: `app/reports/queries.py`
da tashqi interfeys, **neytral tiplar** qaytaradi (`uuid`, `float`), shuning
uchun `reports` `clustering` ni import qilmaydi va bog'liqlik bir tomonlama
qoladi.

*Rad etilgan variant:* `ReporterPoint` dataclass ini `reports` dan qaytarish —
u `clustering` da e'lon qilingan, ya'ni aylanma import bo'lardi.

### 2. Xabarlar sonini `reports` dan sanash

Inkremental markaz o'rta arifmetik bo'lishi uchun «hozirgacha nechta xabar
biriktirilgan» kerak, lekin `outages` da bunday ustun yo'q.

*Tanlandi:* har biriktirishda `COUNT(*)`. Sxema o'zgarmaydi, spetsifikatsiya
buzilmaydi.
*Rad etildi:* `outages.report_count` qo'shish — bu sxemani o'zgartirish,
qoida bo'yicha `PROGRESS.md` ning «Ochiq savollar» iga yozildi.

### 3. Radiusni konservativ o'stirish

`grow_radius` yangi doira ichida **ham eski doira, ham yangi nuqta** bo'lishini
kafolatlaydi. Aks holda markaz siljiganda allaqachon biriktirilgan xabar
doiradan chiqib ketardi va `ST_DWithin(centroid, point, radius + eps)` bo'yicha
nomzod qidirish shu xabarning qo'shnisini topmasdi — bitta uzilish ikkiga
bo'linardi.

### 4. Mustaqillik hisobi — ochko'z algoritm

«Bir-biridan >= 50 m uzoqdagi eng katta to'plam» — NP-qiyin masala. Ochko'z
yurish kichikroq natija berishi mumkin, ya'ni xato **tasdiqlashni
qiyinlashtirish** tomoniga. Suiiste'molga qarshi mexanizmda aynan shu yo'nalish
kerak. Determinizm uchun SQL tartibi qat'iy: `created_at`, keyin `user_id`.

### 5. `restored` xatti-harakati

- yangi hodisa **yaratmaydi** (nomzod yo'q bo'lsa biriktirilmagan qoladi);
- markazni **siljitmaydi** (geometriya faqat `kind='outage'` dan);
- `last_report_at` ni **yangilaydi** (bu ham faollik);
- `pending` hodisani ham yopadi — §4.5 «ochiq hodisa doirasida» deydi,
  «ochiq» = `pending` + `confirmed`. Bu §4.4 diagrammasidan kengroq, shuning
  uchun «Ochiq savollar» ga yozildi.

### 6. Qaror tartibi `evaluate_status` da

`restored` → tasdiqlash → autoclose. Sabab: §4.5 «darhol» so'zi. Agar autoclose
oldin tekshirilsa, 2 soat jim turgan va endi «svet keldi» olgan hodisa
`autoclose` sababi bilan yopilardi — jurnalda noto'g'ri sabab qolardi.

### 7. `geometry(geography)` funksiyasi, cast emas

`ST_X`/`ST_Y` faqat geometriya bilan ishlaydi. `CAST(x AS geometry(POINT,4326))`
typmod ni tekshiradi va SQLAlchemy tipi bilan nomuvofiqlik xavfi bor;
PostGIS ning `geometry(geography)` funksiyasi — o'sha castning o'zi, typmodsiz.
Xuddi shunday `geography(geometry)` yozishda.

### 8. Status ro'yxati bitta manbada

E2 da `app/clustering/models.py` da qo'lda yozilgan `OUTAGE_STATUSES` /
`OPEN_STATUSES` bor edi. Endi ular `status.py` dagi `OutageStatus` dan
olinadi — ikki joyda takrorlangan ro'yxat vaqt o'tishi bilan ajralib ketardi.

---

## Nima qilinmadi (ataylab)

- **`confidence`** — `06` ning ishi, E5b.
- **5-oltin ssenariy** («ma'lumot yetarli emas») — so'rov paytidagi verdikt,
  `05` §4.6, E7. O'lchov funksiyasi (`active_users_in_cell`) tayyor qoldirildi.
- **Moderatsiya navbatiga yozish** `max_radius` oshganda — `admin` moduli
  jadvali, E8. Hozircha `cluster.max_radius_exceeded` ogohlantirishi.
- **`tools/recluster.py`** — E6.
- **Git commit/push** — qoida bo'yicha odam `push.ps1` orqali qiladi.

---

## Keyingi run uchun

1. `.\push.ps1` → CI. U **E2 va E5 ni birga** tekshiradi (ikkalasi ham lokal
   ishga tushirilmagan). Qizil bo'lsa — birinchi ish shuni tuzatish.
2. CI yashil bo'lsa: E2 ✅, E5 ✅, keyin **E5b** — tasdiqlash va masshtab
   logikasi (`06` to'liq).
3. Sandbox uchinchi runda ham ishlamasa — bu muhit muammosi, odamga aytish
   kerak: lokal tekshiruvsiz ishlash sifatga zarar qiladi.

# 12 — E8: admin-panel (moderatsiya, rollar, audit)

**Sessiya:** `local_fb04c670` · **Sana:** 2026-08-07 · **Epic:** E8

Oldingi sessiya: [11_E7_E6_recluster](11_E7_E6_recluster_844c5fca.md).

---

## Nima qilindi

`04` §2 dagi E8 mezoni — «tashqi moderator qo'llanma bilan smena
o'tkazadi». Shuning uchun ish uchta qatlamga bo'lindi: **kim** (rollar va
tokenlar), **nima qila oladi** (moderatsiya amallari), **nima qilgani
qayerda qoladi** (audit).

| Fayl | Nima |
|---|---|
| `app/admin/roles.py` | `Role` (viewer/moderator/admin), `Permission`, ruxsat matritsasi. Toza modul |
| `app/admin/auth.py` | `ADMIN_TOKENS` → `Actor`; `hmac.compare_digest`, `uuid5` aktor identifikatori |
| `app/admin/audit.py` | `record`/`recent`, `AuditAction`, `jsonable` |
| `app/admin/service.py` | Amallar: ruxsat → o'zgarish → audit |
| `app/clustering/service.py` | `moderate()` — `rejected`/`merged`, `MODERATOR_TARGETS` |
| `app/clustering/repository.py` | `OutageRow`, `read_row`, `list_rows` (moderatsiya navbati) |
| `app/reports/moderation.py` | `users.is_blocked` va `trust_score` — `05` §1 chegarasi |
| `app/api/v1/admin.py` | 8 ta endpoint, `X-Admin-Token` |
| `app/geo/pipeline.py` | `RegionNotConfiguredError` shu yerga ko'chdi + `require_region` |

Testlar: `test_admin_roles.py`, `test_admin_auth.py`, `test_admin_api.py`,
`test_admin_audit.py` (bazasiz) va `test_admin_moderation_db.py`
(`requires_db`, 17 ta).

Natija: `ruff` yashil, `pytest -m "not requires_db"` → **381 passed** (+51),
`requires_db` **50 ta** (+17), 65 modul import qilinadi, `alembic upgrade
head --sql` toza. **Yangi migratsiya yo'q** — `audit_log` `0002` da
allaqachon bor.

---

## Qabul qilingan qarorlar va sabablari

**1. Autentifikatsiya — muhitdagi tokenlar, akkaunt tizimi emas.**
`05` da admin uchun sxema yo'q (`users` — bot foydalanuvchilari). Parol/OAuth
qatlami E8 ning maqsadini (auditlanadigan smena) oshirmaydi, lekin uni bir
necha sessiyaga cho'zardi. Format `nom:rol:token`; aktor identifikatori
nomdan `uuid5` bilan olinadi — `audit_log.actor_id` barqaror, sirdan esa
hech narsa qolmaydi. `ADMIN_TOKENS` bo'sh bo'lsa **hamma so'rov `403`**:
xuddi webhook siridagi qaror (`05` §6.3), «sir yo'q → tekshirmaymiz» ochiq
admin-panel degani.

**2. Moderator faqat `rejected` va `merged` qo'ya oladi.** `05` §4.4
diagrammasida moderator strelkalari aynan shular. `confirmed`/`resolved`
dalildan kelib chiqadi (`06` §4.3, §8) — ularni qo'lda qo'yish tasdiqlash
logikasini chetlab o'tardi va «nima uchun tasdiqlangan edi?» savolini
javobsiz qoldirardi.

**3. Birlashtirishda xabarlar ko'chirilmaydi.** `merged` da faqat `status`
va `merged_into` yoziladi; `reports.outage_id` tegilmaydi. Xabarlarni maqsad
hodisaga ko'chirish uning geometriyasi va `W` sini qayta hisoblashni talab
qilardi, buni esa `05` ham, `06` ham ta'riflamaydi. **Ochiq savolga
yozildi.**

**4. Zanjir yasalmaydi.** `merged` hodisaga birlashtirib bo'lmaydi — aks
holda `merged_into` bo'yicha yurish tsiklga tushishi mumkin edi. Shuningdek
o'ziga va boshqa mintaqaga birlashtirish rad etiladi.

**5. Alohida «moderatsiya navbati» jadvali yaratilmadi.** `05` §4.2
«`max_radius` dan kattasi — moderatorga» deydi, lekin mexanizmni
ko'rsatmaydi (E5 da bu ochiq qolgan edi). Holat `outages` da allaqachon bor,
shuning uchun navbat — **so'rov filtri** (`radius_m >= max_radius`,
`needs_review=true`), ikkinchi nusxa emas. Denormalizatsiya qilingan navbat
vaqt o'tishi bilan haqiqatdan ajralib ketardi.

**6. `user_id` admin API da chiqadi, `tg_id` va `geom_exact` — yo'q.**
`05` §7.3 ro'yxati **ommaviy** API haqida (ochiq xaritada deanonimlashtirish
riski). Bloklash amalini identifikatorsiz bajarib bo'lmaydi. `tg_id` esa
moderatorga ham kerak emas — foydalanuvchi kartasida u umuman o'qilmaydi.
Regressiya OpenAPI sxemasi bo'yicha test bilan qulflandi
(`test_no_schema_exposes_exact_location_or_telegram_id`) — yangi endpoint
qo'shilganda ham ishlaydi.

**7. `RegionNotConfiguredError` `app.bot.service` dan `app.geo.pipeline` ga
ko'chdi.** Admin API ga ham kerak bo'ldi, API ning bot ni import qilishi esa
`05` §1 chegarasini buzardi. `app.bot.service` da nom qayta eksport qilinadi
— mavjud import yo'llari buzilmasin.

**8. `trust_score` — `admin` roli, `moderator` emas.** U `06` §2.3 dagi
`user_factor` orqali tasdiqlash og'irligiga ta'sir qiladi, ya'ni bu amal
faqat tartib-intizom emas, **ma'lumot sifatiga** aralashuv.

**9. Audit ixtiyoriy emas.** Har uchala amal bir xil uch qadamdan iborat:
ruxsat → o'zgarish egasi bo'lgan modulda → `audit_log` ga `before`/`after`.
Bloklash idempotent bo'lsa ham `UPDATE` va audit yozuvi bajariladi:
«amal bajarilmadi» ni jimgina qaytarish moderator uchun chalg'ituvchi.

---

## Yo'lda topilgan defektlar

- **`log.warning(..., extra={"name": ...})` `KeyError` beradi.** `name` —
  `LogRecord` ning band maydoni. To'rtta test shu bilan yiqildi; kalit
  `actor` ga o'zgartirildi. Bu ishga tushirish paytida ham yiqilardi, ya'ni
  test uni haqiqiy defektdan ushladi.
- **`.env.example` da yangi kalit** (`ADMIN_TOKENS`) va README da
  admin-panel bo'limi — tokensiz panel jim turadi, shuning uchun uni
  hujjatsiz qoldirish operator uchun tuzoq bo'lardi.

## Sandbox

Birinchi urinishda `uv` `No space left on device` berdi: `/sessions` bo'limi
100% to'lgan edi. Yechim — cache va venv ni `/` dagi `/tmp` ga olish:

```bash
export HOME=/tmp/homme8 UV_CACHE_DIR=/tmp/uvcache8 XDG_DATA_HOME=/tmp/homme8/share
uv venv --python 3.11 /tmp/venv8 && uv pip install -e ".[dev]"
```

Eski `/tmp/venv7` yana `Permission denied` berdi — hujjatdagidek, uni
tuzatishga urinilmadi.

---

## Keyingi qadam

1. Odam: `.\push.ps1` → CI (endi **50 ta** `requires_db` testi).
2. Botni haqiqiy token bilan bir marta ishga tushirish (hali tekshirilmagan
   yagona qatlam).
3. Keyingi epic — **E9 (veb-xarita)**. U ADR-08 (tayl manbasi litsenziyasi)
   ga bog'liq: `map_snapshot` jadvali va `GET /api/v1/map` tayl manbasidan
   mustaqil, shuning uchun backend qismini ADR-08 siz ham yozish mumkin,
   frontend esa qarorni kutadi.

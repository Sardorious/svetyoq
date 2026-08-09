# Sveta.Net — backend

Elektr uzilishlari haqida jamoaviy xabar tizimi. Spetsifikatsiya: `../05_Technical_Design.md`,
`../06_Confirmation_Logic.md`. Joriy ish holati: `PROGRESS.md`.

## Ishga tushirish

```bash
cp .env.example .env      # qiymatlarni to'ldiring
docker compose up --build
curl http://localhost:8000/api/v1/health
```

`migrate` xizmati `api` dan oldin ishlaydi va `alembic upgrade head` ni bajaradi.

## Lokal ishlab chiqish

```bash
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
pytest -q
ruff check app tools tests alembic
```

## Bot (E3)

```bash
# Lokal: polling — ommaviy HTTPS manzil kerak emas
TELEGRAM_BOT_TOKEN=... TELEGRAM_MODE=polling python -m app.bot
# yoki
docker compose --profile bot up
```

Prodda bot alohida protsess emas: `TELEGRAM_MODE=webhook` bo'lganda u
`app.main` ichiga ulanadi va `TELEGRAM_WEBHOOK_PATH` da update qabul qiladi
(`05` §6.3). Webhook `TELEGRAM_WEBHOOK_SECRET` siz **ishlamaydi** — sir
sozlanmagan bo'lsa endpoint hamma so'rovni `403` bilan rad etadi.

Ikkala rejim bir vaqtda ishlamaydi: polling `delete_webhook` chaqiradi.

## Admin-panel (E8)

Moderator amallari `/api/v1/admin/...` ostida. Kirish — `X-Admin-Token`
sarlavhasi; tokenlar `ADMIN_TOKENS` da `nom:rol:token` ko'rinishida:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
ADMIN_TOKENS=aziz:moderator:<token>,nilufar:admin:<token>
```

| Rol | Nima qila oladi |
|---|---|
| `viewer` | navbat, hodisa tafsiloti va kunlik hisobotni o'qish |
| `moderator` | + `rejected`, `merged`, foydalanuvchini bloklash |
| `admin` | + `trust_score`, audit jurnali |

```bash
curl -H "X-Admin-Token: $T" 'http://localhost:8000/api/v1/admin/outages?needs_review=true'
curl -X POST -H "X-Admin-Token: $T" -H 'Content-Type: application/json' \
     -d '{"reason":"takroriy"}' \
     http://localhost:8000/api/v1/admin/outages/<id>/reject
```

`ADMIN_TOKENS` bo'sh bo'lsa **hamma so'rov `403`** — xuddi webhook siridagidek.
Moderator faqat `rejected` va `merged` qo'ya oladi: `confirmed`/`resolved`
dalildan kelib chiqadi (`06`). Har bir amal `audit_log` ga `before`/`after`
bilan tushadi (`05` §2.5).

## Veb-xarita (E9)

```bash
docker compose --profile jobs up -d      # snapshot 60 soniyada yig'iladi
curl 'http://localhost:8000/api/v1/map?region=samarkand' -i | head
python -m http.server 5173 --directory web
```

`GET /api/v1/map` hech narsa hisoblamaydi — u `map_snapshot` jadvalidan
o'qiydi (`05` §7.1). Snapshotni `build_map_snapshot` fon vazifasi to'ldiradi,
ya'ni **`jobs` konteynerisiz xarita bo'sh qoladi** (javobda `stale: true`).

`ETag` payload mazmunidan hisoblanadi: hodisalar o'zgarmasa `If-None-Match`
bilan kelgan mijoz `304` oladi.

Ommaviy javobda (`05` §7.3): `geom_exact` yo'q, `user_id`/`tg_id` yo'q,
3 tadan kam xabarli hodisa umuman ko'rinmaydi, vaqt 5 daqiqagacha
yaxlitlangan. Sahifaning o'zi — `web/` (`web/README.md`).

Xarita foni `MAP_TILE_URL` bilan sozlanadi; ADR-08 (litsenziya) hal
bo'lmagunicha u bo'sh va sahifa fon rasmisiz ochiladi.

## Issiqlik xaritasi (E16)

```bash
curl 'http://localhost:8000/api/v1/heatmap?region=samarkand' -i | head
```

Davr ichida kelgan xabarlar H3 **r9** katakchalari bo'yicha sanaladi va
GeoJSON olti burchaklar sifatida qaytadi. Sahifada — «Zichlik qatlami»
belgisi (sukut bo'yicha o'chiq).

Ikkita narsani yodda tuting:

- **Rang xabarlar sonini ko'rsatadi, uzilishlar sonini emas.** Xabar ko'p
  bo'lgan joyda shunchaki foydalanuvchi ko'p bo'lishi mumkin. Shuning
  uchun javobda `sufficient` bayrog'i va dislaymer bor.
- **Katakcha 3 tadan kam turli xabar beruvchiga ega bo'lsa ko'rinmaydi**
  (`05` §7.3). r9 ≈ 200 m, ya'ni yolg'iz xabar beruvchining katakchasi
  amalda uning uyi. Yashiringani `suppressed_cells` da sanaladi.

## Kunlik hisobot (`05` §8)

`daily_digest` fon vazifasi har kuni tugagan sutka uchun mintaqa kesimida
hisobot yig'adi: kun davomida boshlangan uzilishlar (status bo'yicha),
xabarlar va ularni yozgan odamlar soni, hozirgi moderatsiya navbati,
moderator qarorlari va bildirishnomalar. Faqat sonlar — identifikator ham,
koordinata ham yo'q.

```bash
DIGEST_CHAT_IDS=-1001234567890      # moderatorlar guruhi
curl -H "X-Admin-Token: $T" 'http://localhost:8000/api/v1/admin/digest?date=2026-08-07'
```

`DIGEST_CHAT_IDS` bo'sh bo'lsa hisobot baribir yig'iladi va saqlanadi,
lekin yuborilmaydi. Takroriy yuborishdan himoya bazada:
`daily_digest (region_id, digest_date)` — qatorni yozgan yurish yuboradi,
qolgani jim o'tadi. Kun chegarasi `DISPLAY_TIMEZONE` bo'yicha; tugallanmagan
kun so'ralsa API `422` beradi.

Vazifa `jobs` konteynerida: **`--profile jobs` siz hisobot yig'ilmaydi**
(lekin API uni so'ralganda joyida hisoblab beradi).

## Kuzatuvchanlik (`05` §10)

```bash
curl -H "X-Admin-Token: $T" http://localhost:8000/api/v1/metrics
```

Prometheus matn formati (`0.0.4`), yangi bog'liqliksiz. `05` §10 dagi
yettita metrika `sveta_` prefiksi bilan chiqadi; deyarli hammasi **so'rov
paytida bazadan** hisoblanadi, ya'ni `api` bir necha nusxada ishlaganda ham
qiymat bir xil bo'ladi va qayta ishga tushirish uni nolga qaytarmaydi.
Yagona istisno — `sveta_http_requests_total`: xatolik darajasini bazadan
bilib bo'lmaydi, u protsess ichida sanaladi.

Ogohlantirishlar `sveta_alert_active{alert="..."}` bilan chiqadi va `05`
§10 ga ko'ra **faqat to'rtta**: `snapshot_stale` (>5 daq),
`outbox_lag` (>2 daq), `geo_unmatched` (>5%), `error_rate`. Faol
bo'lmagani ham `0` bilan chiqadi — yo'qolgan namuna Prometheus da qoidani
jim qoldirardi.

Endpoint `ADMIN_TOKENS` bilan himoyalangan (`METRICS_READ` uchala rolda),
ya'ni scrape konfiguratsiyasida `X-Admin-Token` sarlavhasi ko'rsatiladi.

## Maxfiylik muddati (`05` §3.2)

`purge_exact_geom` kunlik fon vazifasi 90 kundan (`EXACT_GEOM_RETENTION_DAYS`)
eski xabarlarning `geom_exact` ustunini `NULL` qiladi. Qator
**o'chirilmaydi** — `geom_public`, `h3_r9` va `district_id` joyida qoladi,
ya'ni tarixiy statistika va `recluster.py` ishlashda davom etadi.

Vazifa ham `jobs` konteynerida: **`--profile jobs` siz muddat bajarilmaydi.**

## Obuna va bildirishnomalar (E13)

Obuna — **nuqta + radius** (manzil bo'yicha obuna geokoder tanlangandan
keyin, ADR-06). Botda: `🔔 Obunalarim` → «➕ Joy qo'shish» → geolokatsiya.

Yo'l: hodisa `confirmed` ga o'tadi → **o'sha tranzaksiyada** `outbox` ga
qator yoziladi (`05` §2.4, Kafka o'rniga) → `process_outbox` (5 s) obunachini
topadi, `notifications` ga niyat yozadi va Telegramga yuboradi.

```bash
docker compose --profile jobs up -d      # process_outbox shu konteynerda
```

**`jobs` konteynerisiz hech qanday bildirishnoma yuborilmaydi.**

Kafolatlar:

- bitta hodisa bo'yicha bir odamga bir marta — `UNIQUE (user_id, outage_id)`;
- qayta urinish eksponensial kechikish bilan (`OUTBOX_MAX_ATTEMPTS` dan keyin
  qator `outbox.dropped` bilan yopiladi);
- botni bloklagan foydalanuvchi `skipped` bo'ladi va navbatni to'smaydi;
- `outage.resolved` aynan tasdiqlanish xabarini olganlarga boradi.

Token sozlanmagan bo'lsa (`TELEGRAM_BOT_TOKEN` bo'sh) navbat va fan-out
baribir ishlaydi, faqat oxirgi qadam bajarilmaydi (`NullSender`).

## Yangi mintaqani ishga tushirish (E19)

Ikkinchi shahar **kodsiz** qo'shiladi — hech qanday deploy va hech qanday
migratsiya kerak emas:

```bash
# 1. Mintaqa qatori (o'chirilgan holda) + `06` §9 parametrlarining seedi
python -m tools.region_admin add --code bukhara \
    --name-uz Buxoro --name-ru "Бухара" --bbox 39.70,64.35,39.85,64.52

# 2. Chegaralar (bbox endi bazadan olinadi, `--bbox` shart emas)
python -m tools.import_boundaries survey --region bukhara
python -m tools.import_boundaries stage --region bukhara \
    --admin-level 8 --reference-level 6
python -m tools.import_boundaries promote --region bukhara --batch <uuid>

# 3. Yoqish — shundan keyin bot xabar qabul qiladi va u `/regions` da chiqadi
python -m tools.region_admin activate --code bukhara
python -m tools.region_admin list
```

Mintaqa ataylab **o'chirilgan** holda yaratiladi: chegara importi bir necha
bosqich va shu oraliqda shahar ommaviy ro'yxatda ko'rinmasligi kerak.
`activate` bbox siz mintaqani yoqmaydi — bunday qator nuqta bo'yicha hech
qachon tanlanmasdi va «faol» ko'rinib turib xabar qabul qilmasdi.

Xabar kelganda mintaqa **nuqtadan** aniqlanadi, `DEFAULT_REGION_CODE` dan
emas; o'sha sozlama faqat mintaqa ko'rsatilmagan o'qish so'rovlari uchun
qoladi (`/map`, `/stats`, `/heatmap`). Ro'yxat `REGION_CACHE_TTL_S`
davomida keshlanadi.

## Asboblar

```bash
# Mintaqalar (E19)
python -m tools.region_admin list
python -m tools.region_admin config --code samarkand          # `06` §9 qiymatlari
python -m tools.region_admin config --code samarkand --key confirm.min_users --value 4

# Hudud chegaralarini OSM dan olish (`05` §5)
python -m tools.import_boundaries survey --region samarkand

# Retrospektiv qayta hisoblash (E6, `05` §9.2) — standart rejim quruq yurish
python -m tools.recluster --region samarkand --from 2026-08-01 --to 2026-08-08
python -m tools.recluster --region samarkand --from 2026-08-01 --to 2026-08-08 --apply
```

`recluster` xabarlarga tegmaydi: u faqat oynadagi **hodisalarni** o'chirib,
o'sha xabarlardan qaytadan yig'adi. Bildirishnoma yuborilgan hodisa bo'lsa
asbob ishlamaydi (`exit 2`).

## Tuzilma

| Katalog | Mas'uliyat |
|---|---|
| `app/core` | konfiguratsiya, log, i18n, xatoliklar |
| `app/db` | engine, sessiya, deklarativ baza |
| `app/geo` | nuqta → hudud, H3, poligon import |
| `app/reports` | xabar qabul qilish va validatsiya |
| `app/clustering` | hodisa yig'ish, statuslar |
| `app/notifications` | obuna, outbox, yuborish |
| `app/bot` | aiogram handlerlar |
| `app/api` | FastAPI routerlar |
| `app/admin` | moderatsiya: rollar, tokenlar, audit |
| `app/stats` | statistika, Coverage Index, issiqlik xaritasi |
| `app/obs` | metrikalar va ogohlantirishlar (`05` §10) |
| `app/jobs` | fon vazifalari |
| `web/` | veb-xarita (statik: `index.html` + `app.js` + `style.css`) |

**Modul chegarasi qat'iy:** bir modul boshqasining jadvaliga to'g'ridan-to'g'ri
murojaat qilmaydi, faqat funksiya chaqiruvi orqali (`05` §1).

## Qoidalar

- Foydalanuvchiga ko'rinadigan matn faqat `app/core/i18n/locales/` dan (UZ va RU).
- `geom_exact` hech qanday API javobida chiqmaydi (`05` §7.3).
- Klasterlash parametrlari konfiguratsiyada, kodda emas (`05` §4.2).
- Sirlar `.env` da; repoda faqat `.env.example`.

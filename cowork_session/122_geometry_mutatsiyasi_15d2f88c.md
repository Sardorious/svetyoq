# 122-run — `geometry.py` mutatsiyasi: 13/13 (5 qulf + 2 ekvivalent)

**Sessiya:** `local_15d2f88c` · **Sana:** 2026-08-12 · **Epic:** E5
(`05` §4.2 — inkremental markaz va radius)

---

## 1. Nima qilinishi kerak edi

121-run qoldirgan birinchi qadam: mutatsiyasiz qolgan **mahsulot**
modullari — `clustering/geometry.py`, `stats/aggregate.py`,
`stats/heatmap.py`. Birinchisi olindi: 86 qator, to'rt funksiya
(`haversine_m`, `centroid_step`, `grow_radius`, `clamp_radius`),
bazasiz va holatsiz — ya'ni disk to'lib PostGIS ko'tarilmasa ham
to'liq o'lchanadi.

**Nishon to'plam** — modulni chaqiradigan sakkiz fayl:
`test_clustering_geometry`, `test_clustering_independence`,
`test_confirmation`, `test_reports_velocity`, `test_simulate`,
`test_map_snapshot`, `test_confirmation_threshold_contract`,
`test_abuse_contract` — **244 test**, har mutant ~12 s.

Harness — 120-runda tuzatilgan shakl (`/tmp/sv122/mut.py`):
`KILLED` faqat `rc == 1` da, `rc not in (0, 1)` → «HARNESS XATOSI»,
`--timeout` yo'q (`pytest-timeout` sandboxda o'rnatilmagan),
`finally` da fayl tiklanadi, partiya **3 mutantdan** oshmaydi,
har partiyadan keyin `cmp`.

## 2. Nazorat tajribasi

120 ning saboqi bo'yicha nazorat mutantlar bilan **bitta `main()`
yo'lidan** o'tdi:

| Nazorat | O'zgarish | Kutilgan | Chiqdi |
|---|---|---|---|
| C1 | `d_lat = lat2 - lat1` → `-(lat1 - lat2)` | `SURVIVED` | `SURVIVED` |
| C2 | `grow_radius` → `return 0.0` | `KILLED` | `KILLED` |

Ya'ni harness ikkala tomonga sezgir.

## 3. Birinchi o'tish — 13 mutatsiya, 6 KILLED, 7 SURVIVED

**Ushlanganlar:** M2 (`2 × R` ko'paytuvchisi), M3 (`cos(lat2)`
tushishi), M4 (yarim burchak `sin(d_lat/2)` → `sin(d_lat)`),
M7 (`/(n + 1)` → `/n`), M8 (longitudaning muzlashi),
M12 (`max(value, 0)` → `value`).

Ya'ni `haversine_m` ning **hisob-kitob** qismi kuchli qorovul ostida:
uning har tarmog'i qaytariladigan masofaga chiqadi (`status.py`
sinfi). Tirik qolganlarning esa deyarli hammasi — chegara, yaxlitlash
yoki hech qachon tanlanmagan tarmoq (`coverage`/`scale` sinfi).

## 4. Qulflangan beshta survivor (+6 test, mahsulot kodi tegilmadi)

**M9** — `return max(covers_old, covers_new)` → `return covers_new`.
Mavjud testlarda yangi nuqta **har doim** yutardi (`test_grow_radius_
covers_old_circle_and_new_point` da 450 ↔ 400), ya'ni `max` ning
birinchi argumenti hech qachon tanlanmagan. Tanlanmasa doira
**kichrayadi** va allaqachon biriktirilgan xabar `ST_DWithin` bo'yicha
nomzod qidiruvidan tushib qoladi — `05` §4.2 ning 1-sharti aynan
buni taqiqlaydi. Qulf: eski doira ustun bo'lgan holat (radius 1000 m,
nuqta 100 m) →
`test_grow_radius_keeps_the_old_circle_inside_when_it_dominates`.

**M10** — `haversine(new, old) + old_radius` → `old_radius`.
Markazning siljishi qo'shilmasa, 500 m siljigan doiraning **yarmi**
tashqarida qolardi. Qulf: 1000 m shimoldagi nuqta, `attached = 1`
(markaz o'rtaga ko'chadi), radius 500 → kutilgan 999.4 m →
`test_grow_radius_adds_the_centroid_shift_to_the_old_radius`.

**M11** — `if value > max_radius_m` → `>=`. **Chegaraning o'zi** hech
qachon sinalmagan edi (1234 pastda, 4200 yuqorida), `05` §4.2 esa
aynan «`max_radius` dan **kattasi** — moderatorga» deydi: mutant
bilan chegaradagi har hodisa ham bayroqlanardi va moderator navbatiga
qurilish bo'yicha ortiqcha ish tushardi. Qulf:
`clamp_radius(3000.0, 3000) == (3000, False)` →
`test_clamp_radius_at_the_limit_itself_is_not_flagged`.
121 ning «chegaraning o'zi» sinfi.

**M13** — `int(round(radius_m))` → `int(radius_m)`. Mavjud test
`1234.4` ni sinaydi, ikkala qoida ham `1234` beradi. Kesish radiusni
**har doim** kichraytiradi (1 m gacha) — bu `grow_radius` ning
konservativ o'sishiga zid, ya'ni chegaradagi xabar doiradan tashqarida
qolishi mumkin. Qulf: `1234.6 → 1235` va `1234.4 → 1234` →
`test_clamp_radius_rounds_to_the_nearest_metre`.

**M5** — `EARTH_RADIUS_M` 6 371 008.8 (IUGG o'rtacha) → 6 378 137.0
(WGS84 ekvatorial). Farq 0.11%, mahalliy testlar esa `rel=0.01`
bilan ishlaydi — ko'rmaydi. Chorak meridian `pi/2 × R` faqat
radiusga bog'liq: 10 007 557 ↔ 10 018 754 m, ya'ni **11 km** farq.
Qulf: `haversine_m((0, 0), (90, 0))` ± 1 m →
`test_haversine_uses_the_iugg_mean_radius`.

Beshala mutant qayta yurgizilib **KILLED** ekani tasdiqlandi; fayl
11 → **17 test**.

## 5. Ikkita ekvivalent mutant — ikkalasi ham empirik isbot bilan

**M1** — `math.sqrt(min(1.0, h))` → `math.sqrt(h)`. Qorovul
`math.asin` ning aniqlanish sohasi uchun yozilgan va **haqiqatan**
`h > 1` holati bor: antipodga yaqin juftlikda `h` aynan
`1.0000000000000002` — 1 dan **bitta ulp** yuqori (1.5 mln tasodifiy
juftlikda maksimum shu chiqdi). Lekin `math.sqrt` o'sha bitta ulp ni
yaxlitlab yana aynan `1.0` qaytaradi, ya'ni `asin` hech qachon
sohadan chiqmaydi; qorovul otilishi uchun `h` kamida **ikki** ulp
oshishi kerak, haversine formulasining xatosi esa unga yetmaydi.
121 ning `jitter` qutb qorovuli bilan bitta sinf — yozilgan, lekin
erishib bo'lmaydigan tarmoq; farqi shundaki, bu yerda chegarani
mahsulot hududi emas, **suzuvchi nuqta arifmetikasi** qo'yadi.
Antipod holati baribir test bilan qayd etildi
(`test_haversine_of_antipodal_points_is_half_the_circumference` —
yarim aylana `pi × R`; u yo'l-yo'lakay M5 ni ham o'ldiradi).

**M6** — `if attached <= 0` → `if attached < 0`. `attached = 0` da
mutant `(centroid × 0.0 + point) / 1.0` ni hisoblaydi — bu `point`
ning **bit-aynan o'zi** (`/1.0` aniq amal), ya'ni ikkala tarmoq bir
xil natija beradi. Tarmoqlar faqat **manfiy** `attached` da ajraladi
(`attached = -1` da `n + 1 = 0` → `ZeroDivisionError`), `attached`
esa `app/clustering/service.py:185` da
`reports_q.count_attached(...)` — SQL `COUNT`, manfiy bo'lolmaydi.

## 6. Muhit (123 o'qisin)

- ⛔ **Disk 100% to'la:** `/` — 62 MB bo'sh, `/sessions` — 0.
  Yangi `initdb` ga joy yo'q, ya'ni **`requires_db` bu runda
  yurgizilmadi**: `conftest.py` portni topolmay 231 testni jimgina
  `skip` qildi (119 ning ogohlantirishi — yashil hisobot ish
  bajarilganini bildirmaydi). 👤 `cleanup-sessions.ps1` endi
  **bloklovchi**, EpicProgress §4 ga qator qo'shildi.
- `/tmp/mamba/envs/py311` (pytest 9.1.1, ruff 0.16.2) **tirik** —
  qayta qurilmadi. `/tmp/home` va `/tmp/cache` `nobody` niki:
  `HOME=/tmp/sv122home`, `XDG_CACHE_HOME=/tmp/sv122cache`.
- Butun to'plam **besh partiyada** (30 fayldan; birinchi partiya
  95 s — eng og'iri).
- `ruff` ikki versiyada mavjud: repo versiyasi
  `/tmp/mamba/envs/py311/bin/ruff` (0.16.2, **toza**), eski
  `/tmp/sv119/ruff0.8.6` esa 23 ta `UP038`/`UP032` beradi — bu
  versiya drifti, repo defekti emas.

## 7. Yakuniy holat

- Butun to'plam: **3176 passed, 232 skipped** (DB siz). Yig'ilgan
  jami **3408** = 121 ning 3402 si + aynan **6** qulf testi.
- `ruff check app tools tests alembic` (0.16.2) — toza.
- `app/clustering/geometry.py` `cmp` bilan tekshirildi — **mahsulot
  kodi tegilmagan**.
- Migratsiya yo'q, vaqtinchalik fayl yo'q (harness `/tmp/sv122` da),
  `git` chaqirilmadi.

---

## 8. O'sha sessiyaning ikkinchi qismi — domen qatlami (👤 so'rovi)

👤 `bormitok.uz` ni serverga yo'naltirdi va serverdagi `docker ps` ni
yubordi. 👤 tasdig'i: **Telegram tokeni bor, bot polling rejimida
ishlayapti** — E3 ning «token yo'q» bloki yopiladi.

### 8.1. Uchta jim defekt (hammasi `docker ps` va kodni solishtirishdan)

1. **Sog'liq tekshiruvi hech qachon o'tmasdi.** `nginx.conf` ning
   `location = /health` i `api:8000/health` ga borardi, `deploy.sh` esa
   `127.0.0.1:${API_PORT}/health` ni so'rardi — ilovada ildiz sathida
   `/health` **yo'q**, u `/api/v1/health/live` da. Ikkalasi 404 olardi.
2. **Webhook yo'li proksi qilinmagan.** `/telegram/webhook` API
   prefiksidan tashqarida turadi, ya'ni `/api/` qoidasi uni qamramaydi:
   webhook rejimiga o'tilganda Telegram 404 olardi va bot jimgina
   ishlamay turardi.
3. **Baza internetga ochiq edi.** `${POSTGRES_PORT:-5432}:5432` —
   Docker uni `0.0.0.0` ga chiqaradi; serverdagi `docker ps` aynan
   `0.0.0.0:5432->5432` ni ko'rsatdi, parol esa standart bo'lishi
   mumkin. Endi `${POSTGRES_BIND:-127.0.0.1}:…`.

Yo'l-yo'lakay: `jobs` va `bot` ga `healthcheck: disable: true` —
rasmning HTTP healthcheck i ularni **doim `unhealthy`** deb
ko'rsatardi (ikkalasi ham HTTP server emas), ya'ni serverdagi
`(unhealthy)` yozuvi nosozlik emas edi.

### 8.2. Qurilgani

| Fayl | Nima qiladi |
|---|---|
| `deploy/nginx.locations.conf` | proksi qoidalarining **yagona manbai**: statik, `/api/` + `limit_req`, `/telegram/webhook`, tuzatilgan `/health` |
| `deploy/nginx.conf` | lokal qobiq (HTTP, 8080) — endi faqat `server` + `include` |
| `deploy/nginx.prod.conf` | prod qobiq: 80 → 443, ACME joyi redirectdan **oldin**, TLS 1.2/1.3, HSTS 30 kun |
| `deploy/docker-compose.prod.yml` | `web` ni qayta yozadi (80/443, certbot volume lari, 6 soatlik `nginx -s reload`) + `certbot` yangilash sikli |
| `scripts/init_tls.sh` | tuxum-tovuq: vaqtinchalik o'z-o'zini imzolagan sertifikat → nginx → HTTP-01 → reload |
| `tests/test_deploy_web_contract.py` | **24 test** — bu qatlam ilgari umuman testsiz edi |

Domen `nginx.prod.conf` da **ataylab qattiq yozilgan**: `envsubst`
shabloni `$uri`/`$host` kabi nginx o'zgaruvchilarini jimgina bo'shatib
yuborish xavfini olib keladi, domen esa sir emas va kamdan-kam
o'zgaradi.

### 8.3. Serverda qolgan qadamlar (👤)

```bash
cd ~/deploy && docker compose down          # eski stekni o'chirish
cd ~/svetyoq/sveta && git pull
bash scripts/init_tls.sh --email <manzil>   # sertifikat
# .env: MAP_PUBLIC_URL, TELEGRAM_WEBHOOK_URL, TELEGRAM_WEBHOOK_SECRET,
#       TELEGRAM_MODE=webhook, POSTGRES_PASSWORD (standart qolmasin)
docker compose stop bot                     # polling to'xtaydi
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml \
       --profile jobs up -d
```

**Yashil (ikkinchi qismdan keyin):** butun to'plam **3200 passed, 232
skipped**, yig'ilgan **3432** (mutatsiya qismidan keyin aynan +24),
`ruff` toza, **148** test fayli.

---

## 9. Uchinchi qism — serverdagi haqiqiy compose keldi, reja tuzatildi

👤 serverdagi `~/deploy/docker-compose.yml` ni yubordi va manzara
o'zgardi:

* serverda **bitta ko'p loyihali stek** bor — ikkiattor, droneguard
  (sayt + admin), telegram-bot-api, bgutil, utilitybot, yuksalish,
  dorilar **va** Sveta.Net ning beshta xizmati;
* **xostda nginx** allaqachon `droneguard.uz` va
  `admin.droneguard.uz` ni xizmat qilyapti (konteynerlar
  `127.0.0.1:5001` va `127.0.0.1:8765` ga chiqadi), ya'ni **80 va 443
  band**.

Demak 8-bo'limdagi konteyner-certbot yo'li **shu serverda
ishlamaydi**: TLS xostda tugatiladi. Ikkinchi tuzatish — «ikkita stek
bitta bazada» degan taxmin ham noto'g'ri: ular **ikkita alohida
Postgres volume i** bilan ishlagan (`sveta-db` → 5433,
`sveta-db-1` → 5432), ya'ni o'chirishdan oldin Samarqand importi
qaysi bazada ekanini aniqlash **shart**.

### 9.1. `deploy-server/` (repo ildizida)

| Fayl | Nima |
|---|---|
| `docker-compose.yml` | serverdagi faylning repodagi nusxasi — ilgari u faqat serverda edi va `sveta/docker-compose.yml` dan jimgina ajralib ketardi |
| `bormitok.uz.nginx.conf` | xost nginx sayti: faqat `proxy_pass 127.0.0.1:8080` |
| `README.md` | ko'chirish tartibi, jumladan bazani tekshirish retsepti |

Sveta.Net qismiga kiritilgan o'zgarishlar:

* **`sveta-web`** qo'shildi (`127.0.0.1:8080`, TLS siz) — statik `web/`
  va API bir domendan berilishi shart (CORS yoqilmagan);
* **`sveta-api` ga `api` tarmoq aliasi** — repodagi snippet
  `proxy_pass http://api:8000/...` deb yozilgan va ikkala joyda
  o'zgarishsiz ishlashi kerak; aliassiz nginx `host not found in
  upstream "api"` bilan **umuman** ko'tarilmaydi;
* **`sveta-bot` ga `profiles: ["polling"]`** — webhook bilan bir
  vaqtda ishlab qolsa nosozlik **jim** bo'ladi: Telegram update larni
  ikki iste'molchi orasida tasodifiy bo'lib beradi va jurnalda xato
  ko'rinmaydi;
* `sveta-jobs`/`sveta-bot` ga `healthcheck: disable: true`.

Kontrakt +9 test (33 ga yetdi): alias ↔ snippet bog'lanishi, snippet
nusxa emas aynan repodan ulanishi, polling profili, baza portining
bog'lanishi, xost saytining marshrutlashni takrorlamasligi.

**Yashil:** **3209 passed, 232 skipped**, yig'ilgan **3441**.

---

**Keyingi qadam — 123-run:** (1) `stats/aggregate.py` va
`stats/heatmap.py` — mutatsiyasiz qolgan oxirgi ikki mahsulot moduli;
(2) 👤 `cleanup-sessions.ps1` (endi `requires_db` ni bloklaydi);
(3) 👤 `test_recluster_db.py` izolyatsiyasi; (4) 👤 `ruff format`
savoli; (5) 👤 prod tekshiruvi (`/api/v1/regions`,
`/api/v1/geo/districts`, `/api/v1/stats`, veb-xarita 360 px va til
almashtirish).

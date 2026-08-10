# 79 — ARCH: `01` §29 «High-Level Architecture» birinchi marta kodda

**Sessiya:** `local_d44eb564-e42c-4a67-a208-7b8d2cfc6051`
**Sana:** 2026-08-10, ~16:35–17:30
**Natija:** `app/core/architecture.py` + `tests/test_architecture_contract.py`;
**2363 → 2408 passed** (+45), 1 skipped, migratsiyasiz, ruff yashil.
Odam run o'rtasida **CI yashil bo'ldi** deb xabar berdi → oltita epic ✅ ga o'tdi.

---

## Mavzu qanday tanlandi

78-run uchta nomzod qoldirgan edi: `GET /api/v1/admin/monitoring` vitrinasi,
`01` §24 «Product Roadmap», `01` §29/§30 (hech qachon o'qilmagan).

§29 tanlandi va sabab §24 ni ham, §30 ni ham chetlab o'tdi: §29 — hujjatdagi
yagona joy, u yerda mahsulot **konteynerlar** darajasida chiziladi, va o'sha
rasm bugungi kodga **mos kelmasligi mumkinligi** hech qayerda tekshirilmagan.
§24 (P0-1…P0-7) esa Faza 0 ning odam ishi — kodda o'lchanadigan tomoni deyarli
yo'q; §30 (Glossary) — atamalar lug'ati, uni qulflash foydali, lekin u §29 ning
ichida baribir tekshiriladi (tugun yorliqlari).

---

## Topilganlar

### 1. Diagrammaning o'nta tugunidan **ikkitasi umuman yo'q**

`KF` (Kafka) va `RD` (Redis). Ular unutilgan emas — `ADR-05` (`05` §11) bilan
rad etilgan va `03` §9 da qaytish sharti bilan yozilgan. Lekin §29 buni
bilmaydi va o'z xulosa jumlasida shunday deydi:

> «Единственное архитектурное следствие Самарканда: `GEO` получает третий
> уровень привязки … **Остальные контейнеры не меняются.**»

O'nta konteynerdan ikkitasi yo'q — ya'ni jumla bugun **yolg'on**. Muhimi,
u Samarqand tufayli yolg'on emas: rasm Toshkent paketidan meros olingan va
yakka ishlab chiquvchi uchun qayta chizilmagan. Bu 71- (`01` §20 «наследуется»)
va 72-runlar (`coverage_zones`) topgan tuzoqning **uchinchi** holati.

### 2. `03` §Q-1 §29 ga allaqachon javob bergan — lekin `01` buni ko'rsatmaydi

Q-1 ning sarlavhasi so'zma-so'z: «PRD §29 arxitekturasi — bu maqsad holati,
boshlang'ich holat emas». Ya'ni javob **bor** va u aniq. Faqat u `03` da
yozilgan; §29 dan kelgan o'quvchi hech qanday havola ko'rmaydi va rasmni
bajarilishi kerak bo'lgan reja deb o'qiydi. 77-run ning `01` §25 ↔ `03` §6
holati aynan takrorlandi.

Test buni qulfladi: `test_the_document_that_overrides_paragraph_29_exists`
§29 bo'limida `Q-1` **yo'qligini** tekshiradi — havola qo'shilsa qizaradi va
reyestrning asosiy da'vosi qayta ko'rib chiqiladi.

### 3. ⚠️ Eng jim topilma — rad etishning qaytish sharti tug'ilishidan o'lik

`03` §9 ning qoidasi qat'iy: «bu jadvaldagi elementni "hozir qilib qo'yaylik"
degan asos bilan ilgari surish **taqiqlanadi**; qaytish sharti — yagona asos».
Ya'ni butun qaror shartning **o'lchanishiga** tayanadi. Uchala shart ham bugun
o'lchanmaydi, lekin uch xil sababdan:

| Element | Shart | Sinf | Sabab |
|---|---|---|---|
| Kafka | `Kunlik xabar >50k` | `DERIVABLE` | `sveta_reports_received_total` — kümülativ hisoblagich, kunlik tezlik `increase()` bilan chiqadi |
| Kafka | `klaster kechikishi >30 s` | **`VOID`** | almashtirish o'lchanadigan narsani **yo'q qilgan** |
| Redis | `API p95 >300 ms` | `UNMEASURED` | gistogramma yo'q (67-run: `measures.api_p95` = `ABSENT`) |
| Mikroservislar | `Jamoa >6 dev` | `ORGANIZATIONAL` | mahsulot metrikasi emas va bo'lishi shart emas |

**`VOID` — yangi narsa.** `app.bot.service.submit_report` da `clustering.assign`
xabar yozilgan **o'sha tranzaksiyada**, sinxron chaqiriladi (`BOT→KF→CL` bitta
chaqiruvga siqilgan). Navbat yo'q — navbat kechikishi ham yo'q. Ya'ni shart
o'zi asoslayotgan komponentning **mavjudligini** o'lchaydi: Kafka bo'lmasa
qiymat doim nolga yaqin, tetik hech qachon ishlamaydi. `sveta_outbox_lag_seconds`
bor, lekin u bildirishnoma navbatini o'lchaydi (`05` §2.4), klasterlashni emas.

Redis ning tetigi esa **67-run allaqachon ko'rgan bo'shliq** — faqat u yerda u
*reliz o'lchovi* sifatida yozilgan edi. Hech kim o'sha bo'shliq bir vaqtning
o'zida Redis ni qaytaradigan yagona tetik ekanini qayd etmagan. Bu qo'shimcha
ish emas: gistogramma qo'shilsa ikkala qator birdan yopiladi.

### 4. Ikkita strelka noto'g'ri tomonga qaraydi

* **`ADM --> API`** — diagrammada admin-panel API ning **mijozi**. Kodda
  teskari: `app.api` → `app.admin`. Alohida deploy qilinadigan admin ilovasi
  yo'q, `app/admin/` — API ichidagi kutubxona. Diagrammadan o'qilgan xulosa
  («admin-panelni alohida chiqaramiz») noto'g'ri. → `REVERSED`.
* **`NT --> BOT`** — diagrammada worker botni chaqiradi. Kodda bunday import
  **yo'q va bo'lmasligi kerak**: `app.bot` → `app.notifications` importi
  allaqachon bor, teskarisi aylana yasardi (`sender.py` docstringida yozilgan).
  Ulash `app.jobs.process_outbox` da, adapter `app.bot.notifier` da.
  → `MEDIATED`.

`MEDIATED` ni `HOLDS` dan ajratish kerak edi: ikkalasi ham «ishlaydi» degani,
lekin `MEDIATED` qirrani buzish uchun **uchinchi** modulni o'zgartirish yetarli
va bu diagrammaga qarab umuman ko'rinmaydi.

### 5. O'n ikkita strelkadan **beshtasi** mavjud bo'lmagan yo'lni ko'rsatadi

`BOT→KF`, `KF→CL`, `CL→KF`, `KF→NT`, `API→RD` — hammasi rad etilgan tugun
orqali. Rasmning qariyb yarmi. → `COLLAPSED`, har biriga haqiqiy almashtirish
qirrasi biriktirilgan (`bot->clustering`, `clustering->notifications`,
`jobs->notifications`).

### 6. Chizilmagan modullar

`app/` da 14 paket, diagrammada 6 tasi.

* `SPECIFIED` (faqat `05` §1 da): `core`, `db`, `reports`, **`jobs`**.
  `jobs` jim emas: `05` §1 uni alohida konteyner deb ataydi va
  `docker-compose.yml` da u haqiqatan alohida xizmat — diagrammada esa
  planировщик **umuman yo'q**, holbuki uning ikkita strelkasi (`KF→NT`,
  `NT→BOT`) faqat shu konteyner ishlagandagina bajariladi.
* `EMERGENT` (ikkala hujjatda ham yo'q): `stats`, `obs`, `analytics`,
  `release`, `integrations`. `stats` alohida turadi — u `01` §24 Phase 1 ning
  «витрина статистики» si va §4 Success Metrics ining asosini ko'taradi, ya'ni
  **mahsulot va'dasi bor konteyner ikkala arxitektura hujjatida ham chizilmagan**.

### 7. `03` §Q-1 ning «muhim shart» i birinchi marta o'lchandi

Q-1 modulli monolitni **shart bilan** ruxsat beradi: «modul chegaralari
mikroservis chegaralari kabi qat'iy saqlanadi (bir modul boshqasining
jadvaliga to'g'ridan-to'g'ri murojaat qilmaydi)». Xuddi shu jumla `05` §1 da
va `CLAUDE.md` da ham bor — va **hech qachon o'lchanmagan**, ya'ni butun
«keyinchalik ajratish mumkin» va'dasi tekshirilmagan taxmin edi.

Mexanik shakli ikkita va ikkalasi ham bugun bajariladi:

1. Hech bir modul boshqa modulning `models` submodulini import qilmaydi —
   yagona istisno `app/db/models.py` (`Base.metadata` ni to'liq yig'ish uchun).
2. Xom SQL orqali aylanib o'tish yo'q: `models.py` dan tashqarida
   `from sqlalchemy import text` faqat bitta joyda — `api/v1/health.py`
   (`SELECT 1`).

### 8. Kichik, lekin haqiqiy: bitta shart ikki xil yozilgan

`03` §9 «**klaster** kechikishi >30 s», `03` §Q-1 «**klasterlash** kechikishi
>30 s». Bitta shart, ikkita matn — hujjatdan qidirgan odam bittasini topadi va
ikkinchisi borligini bilmaydi. `CONDITION_ALIASES` ikkalasini ham biladi;
`test_the_same_condition_is_written_two_ways` qaysi biri tuzatilsa ham qizaradi.

---

## Nima yozildi

**`app/core/architecture.py`** (~600 qator). Modul **toza**: bazaga ulanmaydi,
`settings` ni o'qimaydi, FastAPI ni bilmaydi va **`app.*` dan hech narsa
import qilmaydi** (buning o'zi test bilan qulflangan). Hujjat matnini va
kuzatilgan import grafini argument sifatida oladi — 72-run ning
`data_model.py` uslubi.

`app.core` — reyestrning yagona to'g'ri uyi: u barcha modullarni **nomlashi**
kerak, o'zi esa hech qaysisiga bog'lana olmaydi. Import grafida chiquvchi
qirrasi bo'lmagan yagona paket aynan `core` (bu ham test bilan qulflangan).

Tarkibi:

* `parse_container_diagram(doc)` — §29 ning mermaid blokini o'qiydi.
  Mermaid shakli **ma'noli** va parser uni saqlaydi: `[[…]]` navbat (Kafka),
  `[(…)]` saqlagich (Redis, Postgres), `[…]` xizmat. Ya'ni diagrammaning o'zi
  Kafka va Redis ni turli sinf deb belgilaydi — almashtirishlar ham shunday
  (navbat → `outbox` jadvali, saqlagich → sarlavha va jarayon ichidagi kesh).
  Noto'g'ri hujjat jim qolmaydi: `DiagramError`.
* `Realization` — `MODULE` / `INFRA` / `STATIC` / `DECLINED`.
* `Trigger` — `DERIVABLE` / `UNMEASURED` / `VOID` / `ORGANIZATIONAL`.
* `EdgeFidelity` — `HOLDS` / `REVERSED` / `MEDIATED` / `COLLAPSED` /
  `OUT_OF_PROCESS`.
* `Provenance` — `DIAGRAMMED` / `SPECIFIED` / `EMERGENT`.
* `check_edges(graph)` va `check_absent_edges(graph)`.

**`tests/test_architecture_contract.py`** (45 test). Uchta mustaqil qatlam:

1. **Hujjat** — diagramma parseri, sintetik rasmlar, buzilgan hujjatlar,
   `03` §9 dan so'zma-so'z iqtiboslar, `05` §1 daraxti.
2. **Kod** — import grafi `ast` bilan yig'iladi va reyestrning har bir
   `actual` da'vosi solishtiriladi.
3. **Yo'qlik** — `notifications->bot` va `admin->api` importlari
   **bo'lmasligi**. Bu turdagi da'voni hech qanday odatiy test ushlamaydi:
   import qo'shilsa hamma narsa ishlashda davom etadi va arxitektura jimgina
   bir yo'nalishga qulflanadi.

Tekshiruvchining o'zi ham sinaladi (`test_the_checker_notices_a_broken_claim`) —
aks holda u bezak bo'lardi.

---

## Sandbox

78-run ning PostGIS retsepti **qayta ishlatildi va bir joyi o'zgardi.**
`/tmp/pg` (micromamba muhiti) va `/tmp/venv78` (Python 3.12) sessiyadan
omon qoldi va o'qish uchun ochiq edi — ya'ni ~4 daqiqalik o'rnatish
takrorlanmadi. Lekin:

* `/tmp/pgdata2` **egasi `nobody`**, bu sessiya esa `blissful-busy-darwin` —
  klaster o'qib bo'lmadi. Yangi klaster: `initdb -D /tmp/pgdata79`.
* Soket katalogi ham: `-k /tmp` da `/tmp/.s.PGSQL.5432.lock` ni yaratib
  bo'lmaydi (`Permission denied`, fayl eski egaga tegishli). Yechim —
  `-k /tmp/pgsock79 -p 5433`.
* Server **har `bash` chaqiruvi oxirida o'ladi**, `setsid nohup` bilan ham.
  Ya'ni `pg_ctl start` har chaqiruv boshida qaytariladi va butun ish
  (migratsiya + pytest) **bitta chaqiruvda** bajariladi.

Retsept `EpicProgress.md` §6 da yangilandi.

---

## CI

Odam run o'rtasida yozdi: **«CI yashil bo'ldi»**. 78-run ning yagona ochiq
so'rovi shu edi — oltita epic (`E2`, `E5`, `E5b`, `E6`, `E7`, `E15`) uchun ✅
ga qolgan yagona shart CI ning o'z tasdig'i edi. Ular ✅ ga o'tkazildi.

---

## Ochiq savollar (odamga)

1. **§29 tuzatilsinmi yoki reyestr yetarlimi?** Rasmdan `KF` va `RD` ni olib
   tashlash — hujjatni to'g'ri qiladi, lekin `03` §Q-1 ning «maqsad holati»
   ma'nosini yo'qotadi. Muqobil: §29 ga bitta jumla — «amaldagi holat uchun
   `03` §Q-1 ga qarang». Reyestr ikkala yo'lda ham qizaradi va yangilanadi.
2. **`klaster kechikishi` shartini qayta yozish kerakmi?** Bugungi holida u
   hech qachon ishlamaydi. Ma'noli almashtirish — `submit_report` ning
   davomiyligi yoki `assign` ning p95 i. Bu `03` §9 ga tegish, ya'ni odam
   qarori.
3. **`api_p95` gistogrammasi.** Bitta o'lchov ikkita qatorni yopadi:
   `measures.api_p95` (67-run) va Redis ning qaytish tetigi (bu run).
4. `sveta/4wpi2gpv` (4 bayt, mazmuni `blat`) — 78-rundan beri turibdi.
   Agent o'chira olmaydi (`allow_cowork_file_delete` chaqirilmaydi).
5. `tests/test_dbg_tmp.py` — 30-sessiyadan qolgan bo'sh fayl; faylning o'zida
   `git rm` ko'rsatmasi yozilgan.

# Odam bajaradigan ishlar — qadamba-qadam

**Holat:** 2026-08-12 (117-rundan keyin) · Manba: `sveta/PROGRESS.md`
«Odam qaroriga bog'liq bloklar» + «Ochiq savollar».

Tartib **ustuvorlik bo'yicha**: A → B → C birin-ketin bajariladi
(har biri keyingisining sharti). D va E mustaqil.

---

## A. Hozir, kompyuterda (~10 daqiqa)

### A1. Kodni push qilish

Agent 117 ta run yozgan, hech biri commit qilinmagan — bu **sizning**
qadamingiz.

```powershell
cd H:\tukhaev_s\svetyoq
# Agar oldingi urinishdan qolgan bo'lsa (55-run poygasi):
Remove-Item .git\index.lock -Force -ErrorAction SilentlyContinue
.\push.ps1
```

> Commit xabari `sveta\PROGRESS.md` ning «Run jurnali» dagi eng
> yuqori qatordan yasaladi. Push davomida agent ishlab turmasin —
> aks holda `cannot rebase: You have unstaged changes` chiqadi.

### A2. C diskni tozalash

Sandbox har run `/sessions` diski to'laligidan aziyat chekadi
(117-run muhitni noldan qurishga majbur bo'ldi).

```powershell
cd H:\tukhaev_s\svetyoq
.\cleanup-sessions.ps1
```

---

## B. Serverga chiqarish (E9 + E19) — eng katta blok

Butun mahsulot shu qadamdan keyin «tirik» bo'ladi. Serverda,
repo ichidagi `sveta/` papkasidan.

### B1. `~/deploy/docker-compose.yml` ga healthcheck tuzatishini ko'chirish

⚠️ Serverdagi compose fayli **repodagidan boshqa** (loyiha nomi
`deploy`, xizmatlar `sveta-db`/`sveta-migrate`). 56-run topgan
tuzatish unga qo'lda ko'chiriladi, aks holda birinchi ko'tarilishda
`sveta-migrate` `ConnectionRefusedError` bilan yiqiladi:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U sveta -d sveta"]
  start_period: 30s
```

Sabab: `pg_isready` hostsiz unix soketga ulanadi va `initdb` paytida
ham «tayyor» deydi.

### B2. Deploy

```bash
cd ~/svetyoq/sveta       # yoki repo qayerda bo'lsa
bash scripts/deploy.sh
```

Skript o'zi qiladi: `.env` ni tekshiradi, `MAP_TILE_URL` ni OSM ga
qo'yadi (👤 ADR-08 qarori), `git pull`, `docker compose build`,
`--profile jobs` bilan `db/migrate/api/jobs/web` ni ko'taradi,
`/health` ni tekshiradi.

> `jobs` profili **majburiy**: usiz xarita snapshoti qurilmaydi
> (xarita bo'sh), bildirishnomalar yuborilmaydi, Coverage Index doim
> `unknown` bo'ladi (E13-a bloki shu bilan yopiladi).

### B3. Samarqandni sozlash

Prodda 1- va 2-qadam (mintaqa + 17 ta konfiguratsiya kaliti)
**allaqachon bajarilgan**. Qolgani — chegaralar importi.

```bash
bash scripts/bootstrap_samarkand.sh survey
```

Chiqishda OSM ning `admin_level` ro'yxati ko'rinadi. **Siz tanlaysiz**
(bu ADR-07): qaysi daraja Samarqand *shahar tumanlari*.

```bash
bash scripts/bootstrap_samarkand.sh stage 8        # tanlagan darajangiz
bash scripts/bootstrap_samarkand.sh promote <BATCH-UUID>
bash scripts/bootstrap_samarkand.sh activate
```

Agar `overpass-api.de` 504 bersa, oynani almashtiring:

```bash
OVERPASS_URL=https://overpass.kumi.systems/api/interpreter \
  bash scripts/bootstrap_samarkand.sh survey
```

> 74-run defekti (`406 Not Acceptable`, `User-Agent` yo'q edi)
> tuzatilgan — lekin konteyner **eski image** bilan turgan bo'lsa
> `docker compose build api && docker compose up -d api` qiling.

### B4. Tekshirish

```bash
docker compose ps                    # jobs konteyneri Up bo'lsin
curl -s localhost:8000/health
docker compose logs --tail=50 jobs   # endi jimlik BO'LMASLIGI kerak
```

Mintaqa faollashgach bot uni `REGION_CACHE_TTL_S` ichida o'zi ko'radi —
qayta ishga tushirish shart emas.

---

## C. `.env` ga qo'yiladigan qiymatlar (serverda)

Har biri alohida funksiyani ochadi. Agent ularni **o'ylab topa
olmaydi** — sir yoki sizning tanlovingiz.

| # | Kalit | Nima ochadi | Izoh |
|---|---|---|---|
| C1 | `ADMIN_TOKENS` | Admin-panel **va** `GET /api/v1/metrics` | Format `nom:rol:token`, token ≥ 24 belgi. Usiz hammasi `403` (ataylab) |
| C2 | `MAP_PUBLIC_URL` | Botdagi «🗺 Xarita» tugmasi | Usiz bot «hali ochilmagan» deydi. B2 dan keyin manzil ma'lum bo'ladi |
| C3 | `DIGEST_CHAT_IDS` | Kunlik hisobotning **yuborilishi** | Odatda moderatorlar guruhi. Usiz hisobot yig'iladi, lekin faqat `GET /admin/digest` orqali o'qiladi |
| C4 | `TELEGRAM_BOT_TOKEN` | ✅ allaqachon bor | Bot profili: `docker compose --profile bot up -d bot` |

Har o'zgarishdan keyin: `docker compose up -d api jobs` (yoki `bot`).

### C5. Botni haqiqiy Telegram bilan bir marta sinash (E3-a)

Sandboxda tashqi tarmoq yo'q — bu qadam **faqat sizdan**.
`/start` → til → geolokatsiya → xabar → verdikt. Kutilgan natija:
`error.region_not_configured` **chiqmasligi** kerak (B3 dan keyin).

---

## D. Brauzer tekshiruvi (E9) — hech kim hali ko'rmagan

94–96 va 117-runlarning `web/` tuzatishlarini **birorta odam
ko'rmagan** (sandboxda brauzer yo'q). B2 dan keyin xaritani oching:

1. **360 px kenglikda** (DevTools → mobil) — legenda va zichlik bloki
   xaritani yopmasin, banner uch qatorga cho'zilmasin.
2. **Til almashtiring** (UZ ↔ RU) — butun sahifa, jumladan banner,
   yangi tilga o'tsin. 117-rundan keyin tanlagichlarning ekran
   o'quvchi nomlari ham almashadi.
3. **Zichlik kalitchasi** — sahifani qayta yuklaganda **o'chirilgan**
   holatda ochilsin.
4. **`MAP_TILE_URL` bo'sh holatda** (agar sinamoqchi bo'lsangiz) —
   «Xarita foni sozlanmagan» xabari birinchi yangilanishdan keyin ham
   turishi kerak.

Nima ko'rganingizni yozib qo'ying — agent buni o'zi o'lchay olmaydi.

---

## E. Javob kutayotgan qarorlar

Bular kodni bloklamaydi (agent ularni reyestrda «ziddiyat» deb qayd
etib ishlayveradi), lekin javob bergan sari hujjat qatlami tozalanadi.

### E1. Tez javob beriladiganlar (mahsulot qarori)

| Savol | Variantlar |
|---|---|
| **Obuna taklifi oqimga ulanadimi?** Mexanizm to'liq tayyor, lekin verdiktdan keyin foydalanuvchiga taklif qilinmaydi (`01` §11 uni majburiy deb chizadi) | (a) verdikt javobiga inline tugma qo'shiladi; (b) `01` §11 dan tugun olib tashlanadi |
| **Mintaqa nomlari til almashganda eskiradi** (117-run) | (a) sahifa `/map/config` ni qayta so'rasin; (b) nomlar tilga bog'liq bo'lmasin. Bugun ko'rinmaydi — mintaqa bitta |
| **`outage-halo` rangi `official` ni bilmaydi** — rasmiy e'lon ko'k nuqta + **sariq** iz bilan chiziladi | (a) iz ham status rangiga o'tadi; (b) iz neytral rangga o'tadi |
| **To'rtinchi status «Завершено»** xaritada yo'q (`01` §14 to'rttani va'da qiladi) | (a) snapshot yopilgan hodisani ham chiqarsin (yangi rang + shakl + i18n kaliti); (b) `01` §14 «uchta faol status» deb toraytiriladi |
| **Dark Mode (`UI-5`)** — `prefers-color-scheme` umuman yo'q | (a) yorug' tema qo'shiladi; (b) qator «faqat to'q tema» ga qayta yoziladi |
| **`web/` React ga o'tkazilsinmi (E9-b)** | Hozircha build zanjirisiz statik sahifa. E14-a (statistika vitrinasi sahifasi) shu javobni kutmoqda |
| **MapLibre CDN dan keladi** (`UX-S6` 3G talabi) | (a) lokal bundle; (b) qator qayta yoziladi |

### E2. Hujjat ziddiyatlari (javob bermasa ham loyiha yuradi)

- **TTL:** BRD «3 soat», `05` §4.4 «120 daqiqa» — kod `05` ga ergashadi.
- **Meros hujjatlari:** `01` §31 va BRD §26.1 o'n uchta Toshkent
  hujjatini nomlaydi, paketda **birortasi yo'q** (17 qator asosini
  aynan shulardan oladi). Arxivga qo'shiladimi yoki «yo'q» maqomi
  doimiy deb qabul qilinadimi?
- **Arxitektura rasmi:** BRD §24 (19 tugunli mikroservis) ↔ `01` §29
  (10 tugun) ↔ repo (ataylab monolit, ADR-05). Qaysi biri qonun?
- **`RS-*` va `OQ-*` nomfazolari** `01` va BRD da to'qnashadi (bir xil
  kod, boshqa mazmun).
- **BRD §15 stek** Redis/Kafka/K8s ni majburlaydi — repo Compose+outbox.
- **§19 rol modeli:** sakkiz roldan beshtasining kodda izi yo'q.
- **BRD §1–§7 va §9–§12** reyestrsiz qoladimi (§8–§26 bog'langan).
- **OWASP ASVS darajasi** (L1/L2) tanlansa `security.py` ga kiradi.
- **`NFR-S-03` «500 ming»** — load-test kerakmi va qachon?

Javoblarni shu faylga yoki to'g'ridan-to'g'ri chatga yozing — agent
ularni `PROGRESS.md` ga ko'chiradi va kodga tushiradi.

---

## F. Uzoq muddatli (kod bilan yopilmaydi)

| Kod | Ish | Nega muhim |
|---|---|---|
| **E10-a** | Mahalla aktivi bilan kelishuv | **Eng qattiq cheklov** — yopiq yig'ish bosqichisiz E11 (parametrlarni haqiqiy ma'lumotda sozlash) va E12 (ommaviy ishga tushirish) boshlanmaydi |
| **E17** | Mahalla poligonlari | OSM qamrovi to'liq emas (👤 qaror: qisman boshlash mumkin) |
| **E18** | Rasmiy manba (elektr tarmoqlari) bilan kelishuv | Rasmiy qatlam shundan keyin to'ladi |
| **E0-e** | Huquqiy xulosa (ПДн) | E12 dan oldin |
| **ADR-06** | Geokoder tanlovi va kaliti | E13 gacha kutadi |

---

## Qisqacha: birinchi uchta qadam

1. `.\push.ps1` (va `cleanup-sessions.ps1`).
2. Serverda `bash scripts/deploy.sh` → `bash scripts/bootstrap_samarkand.sh`.
3. Xaritani brauzerda oching va botni Telegramda bir marta sinang.

Qolgani shulardan keyin ma'noga ega bo'ladi.

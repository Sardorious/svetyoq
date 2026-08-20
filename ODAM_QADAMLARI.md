# Bog'liqliklar va bajarish tartibi

> ⚠️ **ESKIRGAN QISM (2026-08-20, 189-run).** Bu fayl TZ qaroridan
> (2026-08-19) **oldin** yozilgan va shuning uchun kritik yo'lda eng
> katta texnik bandni ko'rsatmaydi: **TZ mahsulot quvuriga ulanmagan**
> — fuqaro oqimi hamon `06` ning bekor qilingan formulasi ustida
> yuradi. Ulash 2026-08-20 da birinchi navbatdagi ish deb qaror
> qilindi; tartib `sveta/PROGRESS.md` ning «Odam qaroriga bog'liq
> bloklar» bo'limida. §2 dagi odam qadamlari (push, `.env`, botni va
> xaritani sinash, E10-a) **o'z kuchida qoladi**.

**Holat:** 2026-08-13 (145-rundan keyin) · Manba: `sveta/PROGRESS.md`
«Epic holati» + «Odam qaroriga bog'liq bloklar» + «Ochiq savollar».

Bu fayl ikkita savolga javob beradi: **nima nimaga bog'liq** (§1) va
**qaysi tartibda bajariladi** (§2 — odam, §3 — agent).

---

## 0. Nima allaqachon yopilgan (endi bog'liqlik emas)

`PROGRESS.md` ning bloklar jadvali bu qatorlarni hali eski holatda
ko'rsatadi — run jurnali esa ularning yopilganini qayd etgan.
Ziddiyat chiqsa **run jurnali** haq.

| Blok | Yopilgan | Qanday |
|---|---|---|
| **ADR-08** — xarita tayl manbasi | 2026-08-11 | OSM (`tile.openstreetmap.org`), attributsiya «© OpenStreetMap contributors»; pilot uchun |
| **ADR-07** — `admin_level` | 2026-08-12 | Daraja **6**: shahar bitta `district` |
| **E0-d** — tuman poligonlari | 2026-08-12 | Prodda `batch eb3ae4b4` → oltita tuman `districts` da; sifat darvozasi o'tdi (ustma-ustlik 0.17%, qoplash 100%) |
| **E13-a** — `jobs` profili | 2026-08-12 | `deploy.sh` `--profile jobs` bilan ko'taradi; E9 + E13 + E14 + E16 ning fon vazifalari tirik |
| **E0-b** — bot tokeni | — | `sveta/.env` da |
| **E15-a** — `purge_exact_geom` | 2026-08-07 | `app/jobs/purge_exact_geom.py` |

Ya'ni **deploy bosqichi tugagan**: Samarqand prodda faol, chegaralar
haqiqiy, fon vazifalari yuradi.

---

## 1. Bog'liqliklar xaritasi

### 1.1. Kritik yo'l — ishga tushirishgacha

Faqat shu zanjir ishga tushirish sanasini belgilaydi. Qolgan hamma
narsa undan **tashqarida** va parallel bajariladi.

```
E10-b  ko'ngilli sinovchilar (odam o'zi topadi)   ← 👤 2026-08-20:
  │                                                E10-a BEKOR QILINDI
  │    shart: guruh geografik jihatdan yaqin bo'lsin (kamida bitta r8)
  └─→ E10  yopiq yig'ish bosqichi
        ├─→ E11  parametrlarni haqiqiy ma'lumotda sozlash
        │     └─→ E12  ommaviy ishga tushirish
        │           └─→ E20  PWA + Web Push
        │                 └─→ 2 ta analitika hodisasi (§21)
        └─→ E9-a  MAP_PUBLIC_URL  (ataylab E10 gacha bo'sh)
              └─→ botdagi «🗺 Xarita» tugmasi

E0-e  huquqiy xulosa (H-8) ──────────────────→ E12
```

`E9-a` ni erta to'ldirish **xato bo'lardi**: `app/bot/handlers.py`
o'sha bayroqqa qaraydi va xarita yopiq sinov tugaguncha yopiq
qolishi kerak.

### 1.2. Kritik yo'ldan tashqari — mustaqil shoxlar

Bir-biriga bog'liq emas, istalgan tartibda bajariladi.

```
E8-a  ADMIN_TOKENS ──┬─→ E8   admin-panel (hozir hamma so'rov 403)
                     └─→ OBS  GET /api/v1/metrics (u ham 403)

E8-b  DIGEST_CHAT_IDS ─→ kunlik hisobotning YUBORILISHI
                         (yig'ilishi allaqachon ishlaydi)

E3-a  botni Telegramda bir marta sinash ─→ E3 ✅ ga o'tadi

D     brauzer tekshiruvi (360 px, til, kalitcha) ─→ E9 / WEB ✅

E9-b  web/ React ga o'tsinmi? ─→ E14-a  statistika vitrinasi sahifasi
                                  (backend va CSV tayyor)

E17   mahalla darajasi ← 👤 mahalla poligonlari (OSM qamrovi qisman)
E18   rasmiy manba     ← 👤 elektr tarmoqlari bilan kelishuv
ADR-06 / E0-c  geokoder ← kechiktirilgan, hozir hech narsani bloklamaydi
```

### 1.3. Nima nimani ochadi — leverage bo'yicha

| Qadam | Vaqti | Nechta narsani ochadi |
|---|---|---|
| **E8-a** `ADMIN_TOKENS` | ~2 daqiqa | **2** (E8 + OBS metrikalari) |
| **E3-a** botni sinash | ~5 daqiqa | 1 (E3 → ✅) |
| **D** brauzer tekshiruvi | ~15 daqiqa | 1 (E9/WEB → ✅) |
| **E8-b** `DIGEST_CHAT_IDS` | ~2 daqiqa | 1 (hisobot yuborilishi) |
| **E9-b** React qarori | qaror | 1 (E14-a) |
| **E10-a** kelishuv | haftalar | **4** (E10 → E11 → E12 → E20) |

---

## 2. Odam uchun tartib

### Bosqich A — hozir, ~25 daqiqa

**A1. Push.** 145 ta run commit qilinmagan.

```powershell
cd H:\tukhaev_s\svetyoq
Remove-Item .git\index.lock -Force -ErrorAction SilentlyContinue
.\push.ps1
```

Commit xabari `sveta\PROGRESS.md` «Run jurnali» ning eng yuqori
qatoridan yasaladi. Push davomida agent ishlab turmasin.

**A2. Uchta axlat faylni o'chirish** (agent `rm` qila olmaydi):
`sveta\4hs3xo8b`, `sveta\58pozfd9`, `sveta\klc5pety` — har biri 4 bayt.
Shuningdek `cowork_session\` da ikkita nusxa:
`100_repository_va_queries_qulflandi_70dfe57e.md` (144 bilan bir xil)
va to'rtta `28_*` faylining ortiqchalari.

**A3. `.env` ga ikkita kalit** (serverda) — eng katta leverage:

| Kalit | Nima ochadi |
|---|---|
| `ADMIN_TOKENS` | Admin-panel **va** `GET /api/v1/metrics`. Format `nom:rol:token`, token ≥ 24 belgi |
| `DIGEST_CHAT_IDS` | Kunlik hisobotning yuborilishi (odatda moderatorlar guruhi) |

Keyin: `docker compose up -d api jobs`.

### Bosqich B — tekshiruv, ~20 daqiqa

**B1. Botni Telegramda sinash (E3-a).** `/start` → til → geolokatsiya
→ xabar → verdikt. Kutilgan: `error.region_not_configured`
**chiqmasligi** kerak (chegaralar 2026-08-12 da import qilingan).

**B2. Xaritani brauzerda ochish (D).** 94–96 va 117-runlarning `web/`
tuzatishlarini hali **birorta odam ko'rmagan**:

1. **360 px kenglikda** (DevTools → mobil) — legenda va zichlik bloki
   xaritani yopmasin, banner uch qatorga cho'zilmasin.
2. **Til almashtiring** (UZ ↔ RU) — butun sahifa, jumladan banner va
   tanlagichlarning ekran o'quvchi nomlari.
3. **Zichlik kalitchasi** — qayta yuklaganda **o'chirilgan** holatda
   ochilsin.
4. **`MAP_TILE_URL` bo'sh holatda** — «Xarita foni sozlanmagan» xabari
   birinchi yangilanishdan keyin ham tursin.

Nima ko'rganingizni yozib qo'ying — agent buni o'lchay olmaydi.

### Bosqich C — qarorlar (kodni bloklamaydi)

Agent ularni reyestrda «ziddiyat» deb qayd etib ishlayveradi, lekin
javob bergan sari hujjat qatlami tozalanadi.

| Savol | Variantlar |
|---|---|
| **`web/` React ga o'tsinmi (E9-b)?** | Hozircha build zanjirisiz statik sahifa. **E14-a shu javobni kutmoqda** |
| **Obuna taklifi oqimga ulanadimi?** Mexanizm tayyor, lekin verdiktdan keyin taklif qilinmaydi (`01` §11 uni majburiy deb chizadi) | (a) verdikt javobiga inline tugma; (b) `01` §11 dan tugun olib tashlanadi |
| **To'rtinchi status «Завершено»** xaritada yo'q (`01` §14 to'rttani va'da qiladi) | (a) snapshot yopilgan hodisani ham chiqarsin; (b) `01` §14 «uchta faol status» ga toraytiriladi |
| **`outage-halo` rangi `official` ni bilmaydi** — rasmiy e'lon ko'k nuqta + **sariq** iz | (a) iz status rangiga o'tadi; (b) neytral rangga |
| **Dark Mode (`UI-5`)** — `prefers-color-scheme` yo'q | (a) yorug' tema; (b) qator «faqat to'q tema» ga qayta yoziladi |
| **MapLibre CDN dan keladi** (`UX-S6` 3G talabi) | (a) lokal bundle; (b) qator qayta yoziladi |
| **Mintaqa nomlari til almashganda eskiradi** | (a) `/map/config` qayta so'ralsin; (b) nomlar tilga bog'liq bo'lmasin. Bugun ko'rinmaydi — mintaqa bitta |

### Bosqich D — uzoq muddatli (kod bilan yopilmaydi)

| Kod | Ish | Nega |
|---|---|---|
| ~~E10-a~~ | ~~Mahalla aktivi bilan kelishuv~~ | 👤 **BEKOR (2026-08-20)** — sinovchilarni odam o'zi topadi; kritik yo'lning boshi endi E10-b |
| **E0-e** | Huquqiy xulosa (ПДн, H-8) | E12 dan oldin |
| **E17** | Mahalla poligonlari | 👤 qaror: qisman qamrov bilan boshlash mumkin |
| **E18** | Rasmiy manba (elektr tarmoqlari) bilan kelishuv | Rasmiy qatlam shundan keyin to'ladi |
| **ADR-06** | Geokoder tanlovi va kaliti | Hozir hech narsani bloklamaydi |

### Hujjat ziddiyatlari (javob bermasa ham loyiha yuradi)

- **TTL:** BRD «3 soat», `05` §4.4 «120 daqiqa» — kod `05` ga ergashadi.
- **Meros hujjatlari:** `01` §31 va BRD §26.1 o'n uchta Toshkent
  hujjatini nomlaydi, paketda **birortasi yo'q**.
- **Arxitektura rasmi:** BRD §24 (19 tugunli mikroservis) ↔ `01` §29
  (10 tugun) ↔ repo (ataylab monolit, ADR-05). Qaysi biri qonun?
- **`RS-*` va `OQ-*` nomfazolari** `01` va BRD da to'qnashadi.
- **BRD §15 stek** Redis/Kafka/K8s ni majburlaydi — repo Compose+outbox.
- **§19 rol modeli:** sakkiz roldan beshtasining kodda izi yo'q.
- **BRD §1–§7 va §9–§12** reyestrsiz qoladimi (§8–§26 bog'langan).
- **OWASP ASVS darajasi** (L1/L2) tanlansa `security.py` ga kiradi.
- **`NFR-S-03` «500 ming»** — load-test kerakmi va qachon?

---

## 3. Agent uchun tartib

Odamdan mustaqil — har run bittasi olinadi.

**1. 👤 144-runni `reset` bilan QAYTA o'lchash.** 145 isbotladiki, iflos
baza har mutantga soxta `KILLED` beradi; 144 aynan shu manzarani
(46/46, 0 survivor) yozgan va uning baseline i o'lchanmagan. Bu
birinchi, chunki undan keyingi hamma o'lchov shu reyestrga tayanadi.

**2. `notifications/subscriptions.py` va `service.py`** — shu oiladagi
o'lchanmagan qolgan ikkitasi (145 `queries.py` + `outbox.py` ni oldi).

**3. 126 sanagan 92 bazasiz moduldan ~62 tasi** — hali o'lchanmagan.

**4. Reyestr epiclari** (REL, SEC, DATA, INT, SUC, SCOPE, API, FR, UX,
UX-2, WEB, ANL, OBS) — bir-biriga bog'liq emas, mutatsiya seriyasi
tugagach yoki u bloklanganda olinadi.

Bog'liqlik: **1 → 2 → 3** ketma-ket (har biri asbobning ishonchliligiga
tayanadi), **4** istalgan payt.

---

## Qisqacha

1. `.\push.ps1` + uchta axlat faylni o'chiring.
2. `.env` ga `ADMIN_TOKENS` va `DIGEST_CHAT_IDS` (~4 daqiqa, uchta
   narsani ochadi).
3. Botni Telegramda va xaritani brauzerda bir marta sinang.
4. ~~**E10-a** (mahalla aktivi bilan kelishuv)~~ — **👤 bekor qilindi
   (2026-08-20).** Ko'ngilli sinovchilarni odam o'zi topadi. Qoladigan
   yagona shart — ular **geografik jihatdan yaqin** bo'lsin (kamida
   bitta r8, ≈ 0,7 km²): TZ §2.1 uy uchun 3 kishini 20 daqiqada,
   kvartal uchun 5 kishini 30 daqiqada talab qiladi va shahar bo'ylab
   sochilgan guruh hech qachon bitta katakka tushmaydi.

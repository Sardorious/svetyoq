# 213-run — 👤 to'rtta qaror: ADR-08 yopildi (OpenFreeMap Liberty)

**Sessiya:** `local_7c9cb9b5` · **Sana:** 2026-08-21 · **Epic:** E9

> ⚠️ **Bu fayl 214-runda tiklandi.** 213-run `PROGRESS.md` va
> `EpicProgress.md` ni yangilab ulgurgan, lekin `cowork_session/` ga
> tegmasdan uzilgan — `INDEX.md` da na qator, na «Qayerda to'xtadik»
> yozuvi qolgan. Ya'ni `CLAUDE.md` da tasvirlangan 30-sessiya
> stsenariysi yana takrorlandi. Mazmun ikkita manbadan tiklandi:
> `PROGRESS.md` ning «Joriy holat» katagi va sessiyaning o'z
> transkripti (`read_transcript`). Chaqiruvlarning to'liq bayoni
> yo'q — faqat qarorlar va sabablar.
>
> ⚠️ **Sessiya 212-run bilan bitta:** `local_7c9cb9b5` da ikkala run
> ham yurgan (rejalashtirilgan vazifa sessiyani qayta ishlatgan).
> Shuning uchun `212_region_admin_olchov_7c9cb9b5.md` va bu fayl bir
> xil `Session ID` ni ko'rsatadi — bu xato emas.

---

## 1. ADR-08 — xarita foni

👤 odam OpenFreeMap Liberty ni tanladi va havolani berdi. Qaror
**2026-08-11 dagi OSM rastr qarorini almashtiradi**: OSM ning Tile
Usage Policy si ommaviy og'ir trafikni taqiqlaydi, ya'ni qiymatni E12
da baribir almashtirish kerak bo'lardi va zarar eng ko'p yuk paytida
ko'rinardi.

🔴 **Yangi manba eskisining o'rniga sig'masdi.** OpenFreeMap — tayyor
**vektor style JSON**, MapLibre ga satr bo'lib uzatiladi;
`MAP_TILE_URL` esa `{z}/{x}/{y}` shabloni va sahifa undan rastr manba
yasaydi. Eski sozlamaga qo'yilganda xarita **jimgina fonsiz** qolardi.
Shuning uchun ikkita **alohida** sozlama:

* `MAP_STYLE_URL` — stil, **ustun**;
* `MAP_TILE_URL` — rastr, muqobil.

Tanlov **serverda** (`/map/config`) hal bo'ladi, sahifada emas. Ikkovi
ham bo'sh bo'lsa sahifa fonsiz ochiladi va `map.tiles_missing`
chiqadi — degradatsiya, xato emas.

Yo'l-yo'lakay uchta jim nuqson:

1. banner `!config.tile_url` ni o'zi tekshirardi — fon **bor** xaritada
   «fon sozlanmagan» deb yozib qo'yardi (`hasBase()` ajratildi);
2. atributsiya stil yo'lida ekranga **umuman chiqmasdi** (rastrda u
   manbaning ichida yashiringan) — `attributionControl.customAttribution`
   qo'shildi; huquqiy talab aynan o'sha matnga tegishli;
3. `scripts/deploy.sh` `MAP_TILE_URL` bo'sh bo'lsa OSM ni yozardi,
   ya'ni **birinchi deploy odamning tanlovini almashtirardi**. OSM
   olib tashlandi.

Tegilgan fayllar: `app/core/config.py`, `.env.example`,
`app/api/v1/map.py` (`style_url`), `web/app.js` (`hasBase()` +
`baseStyle()`), `scripts/deploy.sh`, `web/README.md`; 8 yangi test.

👤 **qoldi:** serverdagi `.env` ga `MAP_STYLE_URL` ni yozish yoki
`deploy.sh` ni yurgizish, keyin brauzerda tekshirish.

## 2. E13-a va E8-b — kechiktirildi

👤 qarori: ikkovi ham **bloklovchi emas** va ikkovida ham kod qarzi
yo'q. Digest yig'ilaveradi va `/api/v1/admin/digest` orqali o'qiladi —
faqat Telegram ga yuborilmaydi.

## 3. Mahalla poligonlarining manbasi — o'lchandi va **yaramadi**

👤 havola berdi, run uni faraz qilmasdan **o'lchadi**. 7-qatlam
«Mahalla centre»: **20 poligon**, hammasi tarixiy o'zakda (~2×2 km,
shahar esa ~120 km²), `Description` va `id` **butunlay bo'sh** — nom
ham, identifikator ham yo'q; litsenziya e'lon qilinmagan, xizmat
anonim tahrirga ochiq. `mahallas` jadvali `name_uz` ni **talab
qiladi**, `/geo/mahallas` esa `(district_id, name_uz)` bo'yicha
sanaydi — bu ma'lumotdan jadvalni to'ldirib bo'lmaydi.

Kerak bo'lgani: **ma'muriy** chegaralar — hokimiyat reyestri yoki OSM
`admin_level=10`. Faktlar `PROGRESS.md` ning «Ochiq savollar» iga
yozildi.

## 4. Natija

**5127 passed, 410 skipped** (+8), `ruff` toza.

**Keyingi qadam (213 qoldirgani):** (1) 👤 serverdagi `.env`;
(2) mahalla poligonlarining boshqa manbasi; (3) `tools/recluster.py`
va `simulate.py` ning bazali yarmi.

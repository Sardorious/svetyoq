# `web/` — Sveta.Net veb-xaritasi (E9)

Statik sahifa: `index.html` + `app.js` + `style.css`. Build qadami yo'q —
faylni istalgan statik hostingga (yoki nginx ga) qo'yish yetarli.

## Ishga tushirish

```bash
# 1. API ishlab tursin (`docker compose up` yoki `uvicorn app.main:app`)
# 2. Sahifani xuddi shu domendan bering, yoki bazani ko'rsating:
python -m http.server 5173 --directory web
```

Boshqa domendan berilsa, `index.html` ga API manzilini qo'shing:

```html
<script>window.SVETA_API_BASE = "https://api.example.uz/api/v1";</script>
```

va API tomonida CORS ni yoqing (hozircha yoqilmagan — bir domen taxmin
qilinadi).

## Nima qayerdan keladi

| Ma'lumot | Manba |
|---|---|
| Uzilishlar | `GET /api/v1/map?region=…` — tayyor GeoJSON, `ETag` bilan |
| Matnlar (UZ/RU) | `GET /api/v1/map/i18n?locale=uz` |
| Tayl manbasi, markaz | `GET /api/v1/map/config` |
| Zichlik qatlami (E16) | `GET /api/v1/heatmap?region=…` — H3 r9 olti burchaklari |

Sahifada **qattiq kodlangan foydalanuvchi matni yo'q** (`04` §6): har bir
satr `data-i18n` kaliti orqali serverdagi katalogdan olinadi.

## Ochiq narsalar

* **ADR-08 — xarita tayl manbasi.** `MAP_TILE_URL` bo'sh bo'lsa sahifa fon
  rasmisiz, faqat uzilish nuqtalari bilan ochiladi va `map.tiles_missing`
  ogohlantirishini ko'rsatadi. Litsenziya tanlangach `.env` ga qiymat va
  `MAP_TILE_ATTRIBUTION` qo'yiladi.
* **React.** `05` §1 «React + MapLibre» deydi. Bu run React ni kiritmadi:
  u npm/vite build zanjirini talab qiladi, sandboxda esa tashqi tarmoq yo'q,
  ya'ni build ni tekshirib bo'lmasdi. Sahifa ataylab kichik — ko'chirish
  arzon. Qaror `sveta/PROGRESS.md` ning «Ochiq savollar» ida.
* **Zichlik qatlami sukut bo'yicha o'chiq.** «Zichlik qatlami» belgisi
  yoqilganda `GET /api/v1/heatmap` chaqiriladi. Rang **xabarlar** sonini
  ko'rsatadi, uzilishlar sonini emas — bu farq legendadagi dislaymerda
  yozilgan va uni olib tashlash bloklovchi defekt: xabar ko'p bo'lgan
  joyda shunchaki foydalanuvchi ko'p bo'lishi mumkin.
* **Vaqt.** `built_at` va `started_at` serverdan UTC, 5 daqiqagacha
  yaxlitlangan holda keladi (`05` §7.3); brauzer uni lokal zonada ko'rsatadi.

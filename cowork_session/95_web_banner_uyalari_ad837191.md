# 95-sessiya — `web/`: bannerning uchta manbai va yana uchta jimgina defekt

**Sana:** 2026-08-11
**Epic:** E9 (veb-xarita), yo'l-yo'lakay UX-2
**Sessiya:** `ad837191`
**Kod o'zgarishi:** `sveta/web/app.js`, `sveta/web/index.html`
**Migratsiya:** yo'q · **Yangi modul:** yo'q · **Yangi test:** yo'q ·
**Vaqtinchalik fayl:** yo'q · **Sir ko'chirilmadi** (bu sessiyada
token/kalit uchramadi)

---

## 1. Sandbox — ketma-ket **sakkizinchi** run ko'tarilmadi

`mcp__workspace__bash` uch marta aynan bir xil xato bilan yiqildi:

```
resume: RPC error -1: ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.70398: No space left on device
create: … /etc/passwd.70399: No space left on device
```

Uchinchi urinishdan keyin to'xtatildi (asbobning o'z ko'rsatmasi: «if this
keeps failing identically, stop retrying»).

Natijasi 94-run bilan bir xil: `pytest tests/test_user_stories_contract.py
-q` — 94-run ning **birinchi** qadami — bajarilmadi. Fayl endi **oltinchi**
run ketma-ket yurgizilmagan.

👤 **Odamga:** `cleanup-sessions.ps1`. Bu sakkizinchi sandboxsiz run;
sabab — C diskdagi, sessiyaga ulanmagan papka to'lib ketgani, va uni agent
o'zi tozalay olmaydi.

---

## 2. Bugungi ishning tanlovi

93-run ning sharti hali kuchda: **yurgizilmagan qatlam ustiga yangisini
qo'shmaslik.** Ya'ni `01` §11–§14 reyestri (94-run material tayyorlagan)
bugun ham **yozilmadi** — u `pytest` dan keyin yoziladi.

Uning o'rniga 94-run ochgan yo'ldan borildi. 94-run ning §9.4 bandi buni
o'zi nomlagan edi:

> ⚠️ `web/` ni o'qiydigan yangi kontrakt qatlami `style.css` ga ham
> tegishi kerak: bugungi defekt aynan CSS da edi va uni birorta test
> ko'rmasdi.

Buni tekshirish uchun avval savolni aniqlashtirish kerak edi: `web/` ni
testlar **umuman** o'qiydimi? Javob — o'qiydi, lekin faqat bitta darajada:

| Test | `web/` dan nima oladi |
|---|---|
| `test_i18n_key_contract.py` | `_WEB_TOKEN` regexi — qo'shtirnoq ichidagi nuqtali identifikator; `MIN_WEB_KEYS = 26` |
| `test_map_api.py:37` | `data-i18n="…"` va `t("map.…")` kalitlari katalogda bormi |
| `test_notification_channels_contract.py` | `_resolve("web/app.js:function banner")` — literalning **mavjudligi**; `notify.*` tokeni yo'qligi |
| `test_region_acceptance_contract.py:268` | `#heat-legend` bloki, `hidden` atributi, `var heatOn = false`, `showCoverage(`/`showMaturity(` chaqiruvlari soni |

To'rttasi ham `read_text()` + regex, ya'ni ular faylni **matn** sifatida
o'qiydi. Hech biri sahifaning **xulq-atvorini** o'lchamaydi: qaysi
funksiya qachon chaqiriladi, ikkita chaqiruv bir-birining ustiga
yozadimi, DOM holati JS holatiga mos keladimi. Aynan shu bo'shliqda
60-run sinfidagi defektlar yashaydi — hech narsa yiqilmaydi, test
qizarmaydi.

---

## 3. Avval: 94-run ning `style.css` tuzatishi to'g'rimi

94-run tuzatishni hech kim ko'rmagan holda qoldirgan edi. U qo'lda
o'qib tekshirildi va **to'g'ri**:

1. `.legend > h2`, `.legend > ul`, `.legend > .note` — **bolalar**
   selektori (`>`). `#heat-legend` ning o'z `h2` si (`index.html:54`) va
   uchala `.note` i (`:60`, `:66`, `:75`) `#heat-legend` ning bolasi,
   `.legend` ning **nabirasi** — ya'ni ular yashirilmaydi. ✅
2. `@media` blokida `#heat-legend` uchun `display` **qayta
   belgilanmagan**, ya'ni UA jadvalining `[hidden] { display: none }`
   qoidasi kuchida qoladi (`#heat-legend` ning `(1,0,0)` xosligi bu
   yerda ahamiyatsiz — u boshqa xossalarni beradi). Qatlam o'chirilganda
   blok baribir yashirin. ✅
3. `.legend` dan `background`, `padding`, `backdrop-filter` olib
   tashlangan, ya'ni `#heat-legend[hidden]` da `aside` nol o'lchamli
   bo'ladi va xaritani to'smaydi. ✅

Yo'l-yo'lakay: `_heat_legend_block()` (`test_region_acceptance_contract
.py:209`) `re.finditer(r"<div\b|</div>", …)` bilan `<div>` chuqurligini
sanaydi — `Grep` chiqishida u bir marta `<\div>` bo'lib ko'rindi va
«buzuq qorovul» shubhasi tug'ildi. `Read` bilan tekshirildi: manbada
`</div>`, ya'ni **displey artefakti**, defekt emas. Qorovul ishlaydi.

---

## 4. 🔴 Asosiy topilma: bannerning uchta manbai bir-birini o'chirardi

`banner()` bitta argument olardi va bitta DOM tugunini
(`#banner`) to'liq boshqarardi:

```js
function banner(message) {
  var el = document.getElementById("banner");
  el.textContent = message || "";
  el.hidden = !message;
}
```

Unga yozadigan **mustaqil** manba esa uchta: `baseStyle()` (tayl
manbasi), `refresh()` (snapshot holati), `refreshHeat()` (zichlikning
yetarliligi). Ya'ni oxirgi chaqiruv oldingisining xabarini **jimgina**
o'chirardi. Bundan uchta alohida defekt chiqadi.

### 4.1. `map.tiles_missing` birinchi `refresh()` dan omon qolmaydi

`baseStyle(cfg)` `cfg.tile_url` bo'sh bo'lsa `banner(t("map.tiles_missing"))`
qo'yadi. U `new maplibregl.Map({style: baseStyle(config)})` ichida,
**sinxron** bajariladi. Keyin `map.on("load")` → `refresh()` → javob
kelganda `banner(… data.features.length ? "" : …)`.

Ya'ni hodisalar bor bo'lsa banner bir necha yuz millisekunddan keyin
**bo'shatiladi**. Foydalanuvchi fonsiz kulrang xaritada nuqtalarni ko'radi
va nima uchun fon yo'qligini bilmaydi.

Bu shunchaki chekka holat emas: **ADR-08 hali ochiq** (`PROGRESS.md`,
«ADR-08 — xarita tayl manbasi», ⛔ «Endi bloklovchi»), ya'ni `MAP_TILE_URL`
bo'shligi bugungi **kutilayotgan** holat va aynan shu xabar uni
tushuntirishi kerak edi.

### 4.2. Zichlik ogohlantirishi ≥15 soniyada yo'qoladi, qatlam esa qoladi

`refreshHeat()` ning izohi qoidani **ochiq yozadi**:

> `sufficient: false` bo'lsa qatlam baribir ko'rsatiladi, lekin bannerda
> ogohlantirish chiqadi: kam ma'lumotli xaritani jimgina chizish undan
> noto'g'ri xulosa chiqarishga olib kelardi.

Amalda: `boot()` da `timer = setInterval(refresh, Math.max(config.refresh_s,
15) * 1000)`. Keyingi tik `refresh()` ni chaqiradi, u esa `banner(…)` ni
o'z hisobiga qo'yadi — hodisalar bor bo'lsa `""`. Ogohlantirish o'chadi,
`heat-fill` qatlami esa `visibility: visible` bo'lib **qoladi**.

Ya'ni ≤ `refresh_s` soniyadan keyin ekranda aynan izoh taqiqlagan holat
turadi: kam ma'lumotli zichlik xaritasi, ogohlantirishsiz. Bu 94-run va
60-run bilan **aynan bir sinf** — kodda ochiq yozilgan qoida kodning
o'zi bilan buziladi.

### 4.3. `setHeat(false)` xaritaning tushuntirishini ham o'chiradi

`setHeat(on)` ning oxiri: `if (on) refreshHeat(); else banner("");`

Zichlik qatlamini **o'chirish** — xaritaning bo'shligi haqidagi
`map.empty` xabariga hech qanday aloqasi yo'q hodisa. Lekin `banner("")`
uni ham o'chirardi va u faqat keyingi tikda qaytardi. `01` §13 `UX-S3`:
«bo'sh xarita — tushuntirish **va** CTA bilan». CTA allaqachon yo'q edi
(94-run §5.2, `split_promises`); endi ma'lum bo'ldiki, tushuntirishning
o'zi ham yo'qolishi mumkin.

### 4.4. Yo'l-yo'lakay: `reload` tugmasi noaniq, `else` esa yo'q

```js
document.getElementById("reload").addEventListener("click", function () {
  refresh();
  refreshHeat();
});
```

Ikkala so'rov parallel ketadi va ikkalasi ham bannerga yozadi — natija
**qaysi javob oldin kelishiga** bog'liq. Bu poyga, aniqlangan xulq-atvor
emas.

Ustiga, `refreshHeat()` da ogohlantirishni **tozalaydigan** shox yo'q edi:

```js
if (data.warning_texts && data.warning_texts.length && !data.sufficient) {
  banner(data.warning_texts[…]);
}
// `else` yo'q
```

Bugun buni `refresh()` ning ustiga yozishi **tasodifan** qoplaydi. Ya'ni
§4.2 dagi defekt bir vaqtning o'zida shu ikkinchisining niqobi ham edi —
uyalar joriy qilinganda `else` siz ogohlantirish **yopishib qolardi**.
Shuning uchun ikkalasi birga tuzatildi.

### 4.5. Tuzatish — uyalar

```js
var notices = { tiles: "", map: "", heat: "" };

function banner(slot, message) {
  notices[slot] = message || "";
  var text = [notices.tiles, notices.map, notices.heat]
    .filter(function (part, i, all) {
      return part && all.indexOf(part) === i;
    })
    .join(" · ");
  var el = document.getElementById("banner");
  el.textContent = text;
  el.hidden = !text;
}
```

Qarorlar va sabablari:

- **Yig'ish, ustuvorlik emas.** Uchala xabar **turli** narsa haqida, ya'ni
  birortasini tashlash aynan bugun tuzatilayotgan «jimgina yo'qotish» ni
  qaytarardi. Tartib massivda qat'iy — natija deterministik.
- **Takror satr tushib qoladi.** `filter` dagi `all.indexOf(part) === i`
  — `filter` ning uchinchi argumenti **asl** massiv, ya'ni ikkala so'rov
  ham `map.error` bergan holatda «Xato · Xato» chiqmaydi.
- **`function banner` nomi saqlandi**, faqat arity o'zgardi — sabab §5 da.
- `refreshHeat` ga `else banner("heat", "")` qo'shildi.
- `setHeat(false)` endi faqat **o'z** uyasini tozalaydi.

---

## 5. To'rtinchi defekt — `#heat` kalitchasi qayta yuklashdan keyin yolg'on gapiradi

`web/index.html:33` — `<input type="checkbox" id="heat" />`.

Brauzerlar sahifa qayta yuklanganda (F5, bfcache, «orqaga») forma
elementlarining holatini **tiklaydi**. `app.js` esa har doim
`var heatOn = false` dan boshlanadi va `setHeat()` **faqat** `change`
hodisasida chaqiriladi.

Ya'ni: foydalanuvchi zichlikni yoqadi → F5 → kalitcha «yoqilgan»
ko'rinadi, `heatOn === false`, `heat-fill` `visibility: none`,
`#heat-legend` `hidden`. Boshqaruv element o'z holatini yolg'on
ko'rsatadi va uni «to'g'rilash» uchun ikki marta bosish kerak.

**Tuzatish — `autocomplete="off"`.** Ikkita muqobil bor edi:

1. Yuklashda holatni **sinxronlash** (`setHeat(el.checked)`) — bu
   foydalanuvchining niyatini hurmat qilardi, lekin `app/release/
   acceptance.py` ning `web_default` vitrinasini (`shows_index=False`,
   `shows_maturity=False`) va `01` PG-S4 ni **ikki xil** qilardi:
   birinchi tashrifda indeks ko'rinmaydi, qaytishda ko'rinadi.
   `test_region_acceptance_contract.py:268` aynan shu da'voni o'lchaydi.
2. Tiklashni **o'chirish** — DOM allaqachon yozilgan standartga qaytadi.

Ikkinchisi tanlandi: bugungi ish defektni tuzatish, standartni
o'zgartirish emas. Birinchi variant 👤 savol sifatida qoldirildi (§7).

---

## 6. CI xavfi — qo'lda o'lchandi

`web/app.js` ni to'rtta test o'qiydi (§2), ya'ni bu 94-run ning
`style.css` idan farqli o'laroq **xavfsiz emas**. Har bir shart alohida
tekshirildi:

| Shart | Manba | Holat |
|---|---|---|
| `function banner` literali | `app/notifications/channels.py:360` — `evidence=("web/app.js:function banner", …)`, `_resolve` uni `in text` bilan qidiradi | ✅ saqlandi (nom o'zgarmadi, faqat arity) |
| `web/index.html:id="banner"` | o'sha `evidence` | ✅ tegilmadi |
| `var heatOn = false` | `test_region_acceptance_contract.py:288`, `re.search(r"\bvar\s+heatOn\s*=\s*false\b")` | ✅ `app.js:38` |
| `showCoverage(` == 2, `showMaturity(` == 2 | o'sha fayl, `:290` | ✅ 2 va 2 (e'lon + `refreshHeat` dagi chaqiruv) |
| `#heat-legend` bloki, `hidden`, `id="heat-coverage"`, `id="heat-maturity"` | o'sha fayl, `:281–285`; `_heat_legend_block` `<div` chuqurligini sanaydi | ✅ blok tegilmadi; yangi izoh `.controls` da va unda `<div` yo'q |
| `t("map.…")` kalitlari katalogda | `test_map_api.py:50` | ✅ birorta `t()` chaqiruvi o'zgarmadi, yangisi qo'shilmadi |
| `data-i18n="…"` kalitlari | `test_map_api.py:49` | ✅ qo'shilmadi, o'chirilmadi |
| `_WEB_TOKEN` + `MIN_WEB_KEYS = 26` | `test_i18n_key_contract.py:274`, `:622` | ✅ yangi izohlardagi `map.empty`, `map.error` va h.k. **backtick** ichida, qo'shtirnoqda emas; yagona yangi qo'shtirnoq — `banner("")`, `"tiles"`, `"map"`, `"heat"`, `"off"` — nuqtasiz, ya'ni regexga tushmaydi |
| `notify.*` tokeni `web/` da yo'q | `test_notification_channels_contract.py:583–586` | ✅ kirmadi |

⚠️ Bu `pytest` **emas**. Yiqilish chiqsa, u bugun ko'rilmagan joydan
keladi.

---

## 7. 👤 Yangi ochiq savollar (ikkita)

Ikkalasi ham tuzatishning **o'zi** haqida emas — tanlangan yechimning
bitta o'lchovi haqida. To'liq matni `PROGRESS.md` ning «Ochiq savollar»
bo'limida.

| Savol | Kimni bloklaydi |
|---|---|
| **Banner uyalari yig'iladimi yoki ustuvorlik bilan tanlanadimi?** Bugun yig'iladi (hech nima yo'qolmaydi), lekin banner — tor pill (`max-width: min(520px, 100% − 24px)`, markazlashgan) va uchta xabar birga chiqqanda 360 px da xaritaning ustini yopadi | E9, `01` §13 `UX-S6`, `01` §14 |
| **Zichlik kalitchasining holati qayta yuklashda saqlanadimi?** Bugun yo'q (`autocomplete="off"`). Saqlash `web_default` vitrinasining o'lchanadigan da'vosini ikki xil qiladi | E9, REL (`01` §23), `01` PG-S4 |

---

## 8. ⚠️ Ko'rilmagan qoldi

- Bugungi to'rtta tuzatish **hech kim tomonidan ko'rilmagan** — na
  `pytest`, na brauzer.
- 94-run ning `style.css` tuzatishi ham **hali ham** brauzerda
  ko'rilmagan (bugun faqat qo'lda o'qildi, §3).

👤 Xaritani ikki holatda oching:

1. **360 px kenglikda** — status legendasi yashirin, zichlik bloki
   qamrov indeksi bilan ko'rinishi kerak (94-run);
2. **`MAP_TILE_URL` bo'sh holatda** — `map.tiles_missing` birinchi
   `refresh()` dan **keyin ham** turishi kerak (bugungi §4.1).

---

## 9. 96-run uchun tartib

1. `pytest tests/test_user_stories_contract.py -q` → butun to'plam →
   `ruff check app tools tests alembic`. **Fayl oltinchi run
   yurgizilmagan** — bu hali ham birinchi qadam.
2. Mutatsiya bilan tekshirish.
3. **Shundan keyingina** `01` §11–§14 reyestri. Material:
   `94_ux2_sirt_tahlili_24f8f5cf.md` §3–§9, uning **ustiga** bugungi
   topilmalar:
   - `UX-S3` ning `split_promises` i endi ikki qatlamli — CTA yo'q
     **va** tushuntirishning o'zi ham o'chirilishi mumkin edi;
   - `UX-S6` (360 px) ga banner uyalarining ustuvorligi qo'shildi.
4. ⚠️ **Yangi qatlam `web/` ni matn sifatida emas, tuzilma sifatida
   o'qishi kerak.** Bugungi to'rtala defektning birortasi ham
   `read_text()` + regex bilan ushlanmasdi: ular funksiyalar orasidagi
   **munosabat** (kim kimning ustiga yozadi) va DOM ↔ JS holati
   mosligi haqida. Bu `web/` uchun `ast` ning analogini talab qiladi —
   yoki sodda variant: `banner(` chaqiruvlarining har biri uya nomi
   bilan ekanini va `notices` ning kalitlari to'plami bilan mos
   kelishini o'lchash.

---

## 10. Run natijasi

- **Kod:** `web/app.js` — `banner()` uyalar bilan qayta yozildi, uchta
  chaqiruv joyi va bitta `else` tuzatildi; `web/index.html` —
  `autocomplete="off"`. Boshqa fayl o'zgarmadi.
- **Migratsiya:** yo'q. **Yangi modul:** yo'q. **Yangi test:** yo'q
  (ataylab — 93-run ning sharti). **Vaqtinchalik fayl:** yo'q.
- **Sir ko'chirilmadi.**
- ⚠️ `pytest` ham, `ruff` ham yurgizilmadi — sandbox **sakkizinchi** run
  ketma-ket ko'tarilmadi.

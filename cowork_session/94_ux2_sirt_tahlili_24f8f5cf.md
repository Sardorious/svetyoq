# 94-sessiya — `01` §11–§14: sirt tahlili va topilgan defekt

**Sana:** 2026-08-11 · **Session ID:** `local_24f8f5cf` · **Epic:** UX-2
(`01` §11 User Flow, §12 Business Process, §13 UX Requirements,
§14 UI Requirements)

---

## 1. Sandbox — ketma-ket **yettinchi** run ko'tarilmadi

```
useradd failed: exit status 1: useradd: /etc/passwd.70351: No space left on device
useradd failed: exit status 1: useradd: /etc/passwd.70354: No space left on device
```

Ikkita urinish, **aynan bir xil** xato; uchinchisi qilinmadi (93-run ning
qoidasi: bir xil takrorlansa to'xta). Ya'ni 93-run qoldirgan birinchi
qadam — `pytest tests/test_user_stories_contract.py -q` → butun to'plam
→ `ruff check` — **yana bajarilmadi**. `test_user_stories_contract.py`
endi **beshinchi** run ketma-ket yurgizilmagan holda turibdi.

👤 **`cleanup-sessions.ps1`** — yettinchi eslatma.

---

## 2. Bugungi ishning tanlovi va uning sababi

93-run ikkita shart qoldirgan edi:

1. «Yana bitta yurgizilmagan qatlam qo'shilmasin» — ya'ni `01` §13
   reyestri (`UX-S1…UX-S7`) va uning testi bugun **yozilmaydi**;
   `pytest` dan **keyin** yoziladi.
2. `01` §13 — keyingi nishon, lekin faqat pytest dan keyin.

Shundan kelib chiqib bugun **kod-reyestr ham, test ham yozilmadi**.
Uning o'rniga o'sha reyestr uchun kerak bo'ladigan yagona narsa
tayyorlandi: **§11–§14 ning har bir tuguni va qatori qurilgan sirtga
solishtirildi**. Bu ish `pytest` ga bog'liq emas (u `Read`/`Grep` bilan
bajariladi) va 95-runga tayyor material qoldiradi — 90-run ning sabog'i:
reyestr yozishdagi qimmat qism e'lon emas, **hukmni qayerdan olish**
degan savol.

Chegara ochiq: bu tahlil `pytest` emas va u hech narsani qulflamaydi.
U 95-run uchun **xarita**, dalil emas.

---

## 3. §11 User Flow — o'n besh tugun

`01_PRD_Samarkand.md:355–375`, mermaid `flowchart TD`.

| Tugun | Sirt | Hukm qayerdan olinadi |
|---|---|---|
| `A` Свет погас | — | mahsulotdan tashqarida |
| `B` Знает о боте? / `C` Ссылка в чате махалли | — | marketing, kod emas |
| `D` `/start` | `handlers.cmd_start`, `router.message.register(cmd_start, CommandStart())` | `ast`: `register` chaqiruvi `CommandStart` filtri bilan (91-run ning usuli) |
| `E` Язык определён? | `service.register_user` → `is_new`; `i18n.DEFAULT_LANGUAGE = "uz"` | `ast` + konstanta |
| `F` Главное меню | `keyboards.main_menu`, `MENU_KEYS` (6 band) | `ast`: `Action` a'zolari |
| `G` Сообщить об отключении | `Action.OUTAGE` → `on_report_button` | `_action_in(Action.OUTAGE, Action.RESTORED)` |
| `H` Геолокация передана? | `location_request()` (`request_location=True`), FSM `ReportFlow.waiting_location` | `ast` |
| **`I` Ввод адреса** | ⛔ **YO'Q** | quyida §3.1 |
| `J` Привязка: район / махалля / H3 | `app/geo/pipeline.resolve()` | 60-run qulflagan |
| `K` Есть независимые репорты рядом? | `Situation.others`, `decide()` | 91-run qulflagan |
| `L` Вердикт: массовое отключение | `Verdict.CONFIRMED` / `PENDING` | `reply.py:55–63` |
| `M` Вердикт: данных недостаточно | `Verdict.NOT_ENOUGH_DATA` | `reply.py:107` |
| **`N` Предложить подписку** | ⚠️ **qisman** | quyida §3.2 |
| `O` Конец | — | — |

### 3.1. `I` «Ввод адреса» — sirt yo'q, lekin uning **atrofi** qurilgan

`app/bot/keyboards.py:102` ning docstringi buni ochiq yozadi:

> «Geolokatsiya so'rovi. Qo'lda manzil kiritish E13 dan keyin (`05` §6.3).»

Amalda: `on_report_button` FSM ni `waiting_location` ga qo'yadi, lekin
o'sha holatda **matn** kelsa uni hech kim ushlamaydi — `build_router` da
`on_location` faqat `F.location` ga ulangan (`handlers.py:401`), keyingi
qator esa `fallback`. Ya'ni foydalanuvchi manzil yozsa, javob
«tanilmagan xabar» bo'ladi va menyu qaytariladi.

⚠️ **Qiziq tomoni — geokoderning atrofi bor, o'zi yo'q.**
`geocod|GEOCODER` bo'yicha `sveta/` da 17 fayl topiladi va ularning
**birortasi ham** `app/geo/` da emas: `app/core/config.py` (sozlamalar),
`.env.example`, `app/integrations/registry.py` (`01` §18 qatori),
`app/obs/monitoring.py` (alert), `app/release/{risks,dependencies,
roadmap}.py`, `app/release/user_stories.py` va ularning testlari.
Ya'ni geokoder **reyestrlarda, sozlamalarda va alertda mavjud**, lekin
uni chaqiradigan kod yo'q.

Bu `PROGRESS.md` da allaqachon ochiq savol sifatida turibdi
(«`GEOCODER_*` sozlamalari, `GEOCODER_UNAVAILABLE` va `01` §18
integratsiya qatori hujjatda qoladimi»), lekin **§11 uni mahsulot
oqimining tuguni qilib ko'rsatadi** — ya'ni savolning og'irligi
o'zgaradi: bu endi «ortiqcha sozlama» emas, **oqimning uzilgan
tarmog'i**. 92-run `UX-S2` da aynan shu mexanizmni ko'rgan edi
(bir narsa ikkinchi hujjatda mahsulot talabiga aylanadi).

### 3.2. `N` «Предложить подписку» — erishiladi, taklif qilinmaydi

`on_location` verdiktdan keyin uchta narsa yuboradi: verdikt matni,
`main_menu(lang)` va `app.disclaimer` (`handlers.py:329–332`).
`reply.render()` esa faqat verdikt matnini qaytaradi (`reply.py:117–125`)
— hech bir shoxda obuna haqida gap yo'q.

Obuna **erishiladi** (`main_menu` da `Action.SUBSCRIPTIONS` tugmasi bor),
lekin `N` tugunining fe'li «предложить». Ya'ni bu 89-run ning
`realized` / `reachable` ajratmasi uchun tayyor misol: `reachable=True`,
`realized=False`.

---

## 4. §12 Business Process — AS-IS / TO-BE

`01:383–409`. **AS-IS** bloki o'lchanmaydi: uning tugunlari (qo'shnidan
so'rash, mahalla chati, 1055 ga qo'ng'iroq) mahsulotdan tashqarida —
reyestrda ular `gap` emas, **`out_of_scope`** deb belgilanishi kerak,
aks holda «bajarilmagan talab» bo'lib ko'rinardi.

**TO-BE** ning oltita tuguni to'liq qurilgan va hammasi allaqachon
qulflangan: klasterlash (E5, 59-run), mustaqil manbalar chegarasi
(E5b, 53-run), `confirmed` / `pending` (59-run), obunachilarga
bildirishnoma (E13, 74-run), xaritada ko'rsatish (E9), mahalla
statistikasi (E14). Ya'ni §12 dan yangi hukm chiqmaydi — u boshqa
bo'limlarning **takrori**. Takrorlanish mexanizmi **beshinchi marta**
(92-run: `C-5` uch nusxada).

---

## 5. §13 UX Requirements — yettita qator

92-run buni qisman ko'rgan edi; bugun har qatorga sirt biriktirildi.

| ID | Sirt | Holat |
|---|---|---|
| `UX-S1` | `cmd_start` + `Action.LANGUAGE` (`main_menu` ning oxirgi qatori) | ⚠️ §5.1 |
| `UX-S2` | `Verdict.NOT_ENOUGH_DATA` ↔ `NO_OUTAGE_COVERED` | ⛔ ochiq savol (uch nusxa: `01` §9, `01` §13, `05` §6.2) |
| `UX-S3` | `map.py:191` `zoom=11`; `app.js:228` `banner(t("map.empty"))` | ⚠️ §5.2 |
| `UX-S4` | `#heat-coverage` (`index.html:66`), `showCoverage` (`app.js:256`) | ⛔ **defekt topildi** — §6 |
| `UX-S5` | onboarding | ⛔ **YO'Q**: `web/` da ham, `app/bot/` da ham uchramaydi |
| `UX-S6` | 360 px + 3G | ⚠️ §6 bilan bog'liq |
| `UX-S7` | WCAG 2.1 AA, `A11Y-01…A11Y-10` | ⛔ qisman — §7 (`A11Y-06`) |

### 5.1. `UX-S1` — «Первый экран на узбекском» so'zma-so'z bajarilmaydi

`cmd_start` salomlashuvni `register_user(..., language_code=...)`
qaytargan til bilan yuboradi (`handlers.py:131–135`), `register_user` esa
Telegram mijozining `language_code` ini `get_or_create_user` ga uzatadi
(`service.py:81–83`). Ya'ni **ru lokalli mijozning birinchi ekrani rus
tilida** bo'ladi. `DEFAULT_LANGUAGE = "uz"` faqat mijoz til aytmaganda
ishlaydi.

Qurilgani hujjatdan **yaxshiroq** ko'rinadi (foydalanuvchining tilini
hurmat qiladi), lekin `01` §13 boshqa narsa yozadi. Kod o'zgartirilmadi
— 👤 savol (§8).

`UX-S1` ning ikkinchi yarmi («смена языка — одно действие») esa
`PROGRESS.md` da allaqachon ochiq: bugun til — ikki qadamli
(`Action.LANGUAGE` tugmasi → inline tanlov), `/language` komandasi yo'q
(`build_router` da faqat `CommandStart` va `Command("help")`).

### 5.2. `UX-S3` — tushuntirish bor, CTA yo'q

Zum: `map.py:191` — `zoom=11 if (found and found.bbox) else 6`, ya'ni
shahar darajasi ✅ va u serverdan keladi (`config.zoom` → `app.js:364`).

Bo'sh xarita: `app.js:228` — `banner(data.stale ? … : data.features.length
? "" : t("map.empty"))`, ya'ni **tushuntirish** chiqadi ✅. Lekin `banner()`
(`app.js:59`) faqat matn qo'yadi — havola ham, tugma ham yo'q. §13 esa
«объяснение **и CTA**» deydi. Ya'ni qator **yarim** bajarilgan va bu
reyestrda `split_promises` bo'lishi kerak (90-run ning usuli).

---

## 6. 🔴 **Bugungi asosiy topilma: mobil ekranda zichlik qatlami qamrov indeksisiz chiziladi**

Uchta mustaqil fakt bir joyga tushdi:

1. `web/index.html:42–79` — `#heat-legend` bloki `<aside class="legend">`
   ning **ichida** turadi. Qamrov indeksi (`#heat-coverage`), yosh
   mintaqa pometasi (`#heat-maturity`) va zichlik disklameyeri
   (`heatmap.disclaimer.density`) — hammasi o'sha blokda.
2. `web/style.css` (o'zgarishdan oldin) — `@media (max-width: 640px)
   { .legend { display: none; } }`.
3. Qatlamning kalitchasi `#heat` esa `.topbar` da (`index.html:32–35`)
   va u **yashirilmaydi**.

Natija: 360 px da (`UX-S6` — **loyihaviy** kenglik, ya'ni chekka holat
emas, asosiy ko'rinish) foydalanuvchi zichlik qatlamini yoqadi, rangli
olti burchaklarni ko'radi va **na shkalani, na qamrov indeksini, na
«ma'lumot yetarli emas» pometasini** ko'radi.

Bu ikkita yozilgan qoidaning teskarisi:

- `01` §13 `UX-S4`: «Индекс покрытия махалли отображается рядом с любой
  цифрой статистики, а не в FAQ»;
- `web/index.html:62–64` ning **o'z izohi**: «zichlik qatlami —
  statistika vitrinasi, ya'ni u indekssiz ko'rsatilmaydi» (`03` §R1.2,
  `01` PG-S4).

Ya'ni buzilgan narsa faqat hujjat emas, **koddagi ochiq yozilgan qoida**.
Bu 60-run ning sinfidagi defekt: hech narsa yiqilmaydi, test qizarmaydi,
buzilgani faqat kichik ekranda ko'rinadi.

### 6.1. Tuzatildi — `web/style.css`

`.legend` ni butunlay yashirish o'rniga endi faqat **statik status
legendasi** yashiriladi (uning ma'nosi nuqta bosilganda popupda matn
bilan chiqadi — `app.js:188–209`), zichlik bloki esa o'z paneli bilan
qoladi:

```css
@media (max-width: 640px) {
  .legend { background: none; padding: 0; backdrop-filter: none; }
  .legend > h2,
  .legend > ul,
  .legend > .note { display: none; }
  #heat-legend {
    margin-top: 0; padding: 12px 16px; border-top: 0;
    border-radius: 12px; background: var(--panel);
  }
}
```

Qarorlar:

- **`:has()` ishlatilmadi.** «Zichlik yopiq bo'lsa `aside` ni yashir»
  degan shart `:has()` bilan bir qatorda yozilardi, lekin `UX-S6` 3G va
  eski Android ni majburiy qiladi. Uning o'rniga `aside` dan fon va
  otstup olib tashlandi: `#heat-legend[hidden]` bo'lganda ko'rinadigan
  hech narsa qolmaydi va blok joy egallamaydi — eski xatti-harakat
  saqlanadi.
- **`.legend > .note`** — `>` ataylab: `#heat-legend` ichidagi
  `.note` lar (disklameyer, qamrov, pometa) tegilmasligi kerak.
- **Testga ta'sir yo'q.** `tests/` da `style.css` ni o'qiydigan fayl
  yo'q (`test_i18n_key_contract.py` faqat `web/index.html` va
  `web/app.js` ni o'qiydi — `data-i18n` va `t("…")`). Ya'ni bu
  o'zgarish CI ga yangi xavf qo'shmaydi; `data-i18n` kalitlari ham,
  DOM tuzilishi ham o'zgarmadi.

👤 **Ochiq qolgani:** status legendasi mobil ekranda umuman
ko'rsatilmaydigan bo'lib qoldi (avvalgidek). Uning o'rniga yig'iladigan
blok (`<details>`) qo'yiladimi — dizayn qarori, §7 bilan birga
yechilishi kerak.

---

## 7. §14 UI Requirements — oltita qator, ikkitasi bajarilmagan

`01:431–438`.

| Aspekt | Holat |
|---|---|
| Основные экраны (6 ta) | ⚠️ **4/6**: Карта ✅ (`index.html`), Карточка инцидента ✅ (popup, `app.js:188–209`), Подписки ✅ (bot, `subscriptions_menu`), Настройки языка ✅ (bot, `language_choice`). **Статистика по махалле** — vebda sahifa yo'q (faqat API + zichlik legendasi; E14-a bloki), **Онбординг** — umuman yo'q (`UX-S5`) |
| Компоненты (dizayn-tizimdan meros) | — o'lchanmaydi (tashqi tizim) |
| Цветовая схема статусов — **to'rtta** status | ⚠️ **3/4**: `--confirmed`, `--pending`, `--official` bor; **«Завершено»** uchun token ham, legenda qatori ham, `paint` shoxi ham yo'q (`style.css:10–12`, `index.html:45–47`, `app.js:162–182`) |
| **Дублирование смысла: rang **va** shakl (`A11Y-06`)** | ⛔ **bajarilmagan** — quyida |
| Dark Mode: alohida token to'plami + `prefers-color-scheme` | ⛔ **bajarilmagan**: `:root` da bitta qorong'i palitra qattiq yozilgan, `prefers-color-scheme` `web/` da **umuman uchramaydi**, yorug' to'plam yo'q |
| Типографика: uzbek lotin, satr uzunligi `[ГИПОТЕЗА]` | — tekshirilmaydi (hujjatning o'zi gipoteza deb belgilagan) |

### 7.1. `A11Y-06` — status faqat rang bilan kodlangan

`app.js:171–186` — `outage-point` qatlami:

```js
"circle-radius": 7,                       // barcha statuslar uchun bir xil
"circle-color": ["case", … "official" … "confirmed" … ],
"circle-stroke-width": 2,                 // bir xil
"circle-stroke-color": "#ffffff",         // bir xil
```

Ya'ni uchala status **faqat rang** bilan farqlanadi: radius, chegara
qalinligi va chegara rangi aynan bir xil. `style.css:73–76` dagi
legenda nuqtalari ham shunday (`.dot` — bir xil doira, faqat `background`
boshqa). §14 esa aniq talab qiladi: «Статус кодируется цветом **и**
формой (пунктир / заливка / иконка)».

Bu **tuzatilmadi**: `circle` qatlamiga shakl qo'shish `symbol` qatlamiga
o'tishni yoki `circle-stroke-dasharray` (MapLibre da `circle` uchun
yo'q) o'rniga boshqa yechim tanlashni talab qiladi — ya'ni bu §6
dagidek bir qatorli tuzatish emas, **dizayn qarori**. 👤 savol (§8).

---

## 8. 👤 Yangi ochiq savollar (beshta)

| Savol | Kimni bloklaydi |
|---|---|
| `01` §11 ning `I` «Ввод адреса» tuguni: geokoder quriladimi (E13 dan keyin, `05` §6.3 va'da qilganidek) yoki tugun oqimdan olib tashlanadimi? Bugun sozlama, `01` §18 qatori va alert bor, chaqiruvchi kod yo'q | E3, INT, `01` §11/§18 |
| `01` §13 `UX-S1` «Первый экран на узбекском»: qurilgani mijozning `language_code` ini hurmat qiladi (ru lokalda birinchi ekran ru), hujjat esa uz talab qiladi — hujjat tahrirlanadimi yoki `cmd_start` birinchi ekranni `DEFAULT_LANGUAGE` ga majburlaydimi? | E3, E4, `01` §13 |
| `01` §14 «Цветовая схема статусов» to'rtta statusni nomlaydi, xarita esa uchtasini chizadi — «Завершено» xaritaga qo'shiladimi (snapshot yopilgan hodisalarni bermaydi) yoki qator uchtaga qisqartiriladimi? | E9, `01` §14 |
| `A11Y-06` (rang **va** shakl): `outage-point` `symbol` qatlamiga o'tkaziladimi, ikonka to'plami qayerdan olinadi? `UX-S7` (WCAG 2.1 AA) shu qatorga tayanadi | E9, `01` §13/§14 |
| Dark Mode: `prefers-color-scheme` bilan yorug' token to'plami qo'shiladimi yoki `01` §14 «faqat qorong'i» deb qayta yoziladimi? Bugun palitra bitta va qattiq yozilgan | E9, `01` §14 |

Ustiga §6.1 ning kichik savoli: mobil status legendasi `<details>`
bo'lib qaytariladimi.

---

## 9. 95-run uchun tartib (o'zgarmadi + bitta qo'shimcha)

1. `pytest tests/test_user_stories_contract.py -q` → butun to'plam →
   `ruff check app tools tests alembic`. **Fayl beshinchi run
   yurgizilmagan** — bu hali ham birinchi qadam.
2. Mutatsiya bilan tekshirish.
3. **Shundan keyingina** `01` §11–§14 reyestri. Bugungi tahlil unga
   tayyor material beradi:
   - o'lchov birligi — **tugun/qator**, hikoya emas (89-run ning
     sabog'i);
   - `01` §12 AS-IS uchun `out_of_scope` holati kerak (yo'qsa u
     «bajarilmagan talab» bo'lib ko'rinadi);
   - `UX-S3` va §14 «экраны» — `split_promises` misollari;
   - `N` «Предложить подписку» — `reachable` ↔ `realized` misoli;
   - hukmlar `ast` dan (`register` chaqiruvlari, `Verdict` qiymatlari,
     `Action` a'zolari) va **`web/` dan** (`index.html` ning DOM
     tuzilishi, `app.js` ning `paint` ifodalari) olinadi — matn
     qidirilmaydi (86-run ning qoidasi).
4. ⚠️ `web/` ni o'qiydigan yangi kontrakt qatlami `style.css` ga ham
   tegishi kerak: bugungi defekt aynan CSS da edi va uni birorta test
   ko'rmasdi.

---

## 10. Run natijasi

- **Kod:** `web/style.css` — bitta media so'rovi qayta yozildi
  (`UX-S4` + `01` FR-S-901 mobil ekranda tiklandi). Boshqa fayl
  o'zgarmadi.
- **Migratsiya:** yo'q. **Yangi modul:** yo'q. **Yangi test:** yo'q
  (ataylab — 93-run ning sharti). **Vaqtinchalik fayl:** yo'q.
- **Sir ko'chirilmadi** (bu sessiyada token/kalit uchramadi).
- ⚠️ `pytest` ham, `ruff` ham **yurgizilmadi** — sandbox yettinchi run
  ketma-ket ko'tarilmadi. `style.css` ni birorta test o'qimaydi, ya'ni
  o'zgarish CI uchun xavf tug'dirmaydi, lekin uni **hech kim
  ko'rmagan** ham: 95-run xaritani 360 px da ochib tekshirishi kerak
  (yoki 👤 odam).

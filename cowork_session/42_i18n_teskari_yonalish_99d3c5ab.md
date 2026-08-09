# 42-sessiya — i18n teskari yo'nalishi: katalog → kod

**Sana:** 2026-08-09
**Epic:** E4 (ko'ndalang)
**Natija:** ✅ 41-run qoldirgan aniq topshiriq bajarildi. Katalogdagi har bir
kalitga kodda yo'l bormi degan savol o'lchandi; **uchta** ulanmagan kalit
topildi (41-run **ikkitasini** taxmin qilgan edi) va holat kontrakt testi
bilan qulflandi.
**Infratuzilma:** ⚠️ Sandbox **o'n uchinchi ketma-ket run** yiqildi
(INFRA-1). Ikki urinish, ikkalasi ham
`useradd failed: … No space left on device`. `ruff` ham, `pytest` ham
ishga tushmadi; butun run faqat fayl asboblari bilan bajarildi.

---

## 1. 41-running kodi — qo'lda audit

`tests/test_i18n_key_contract.py` ning har bir tayanchi manba bilan
solishtirildi. **Bloklovchi defekt topilmadi.**

| Tayanch | Manba | Holat |
|---|---|---|
| `keyboards.MENU_KEYS` | `bot/keyboards.py:49` | 6 kalit, `Action` 6/6 ✅ |
| `reply.MESSAGE_KEYS` | `bot/reply.py:67` | 6 kalit, `Verdict` 6/6 ✅ |
| `lookup.MESSAGE_KEYS` | `clustering/lookup.py:59` | 4 kalit, `AreaVerdict` 4/4 ✅ |
| `notify_render.MESSAGE_KEYS` | `notifications/render.py:22` | 2 kalit ✅ |
| `coverage.BAND_KEYS` | `stats/coverage.py:76` | 4 kalit, `CoverageBand` 4/4 ✅ |
| `heatmap.DISCLAIMER_KEYS` | `stats/heatmap.py:55` | 3 kalit ✅ |
| `maturity.MESSAGE_*` | `stats/maturity.py:50–51` | 2 kalit ✅ |
| `STATUS_ORDER` | `admin/digest.py:47–53` | **kortej**, 5 = `OutageStatus` 5 ✅ |
| `KEY_FAMILIES` | `OutageStatus` / `REASON_*` / `Scale` | 5 + 3 + 3, hammasi katalogda ✅ |

**Bitta sanoq xatosi — hujjatda, kodda emas.** Test docstringi `error.`
literallarini «24 ta chaqiruv joyi» deydi; `app/` da ularning soni
**30 ta** (16 xil kalit). `PROGRESS.md` ning 41-run yozuvi to'g'ri edi,
docstring esa yo'q — tuzatildi. `MIN_ERROR_LITERALS = 15` baribir
bajariladi, ya'ni zarar yo'q.

**Qirra, va u bugungi ishga olib bordi.** `Scale` da atigi **uchta**
a'zo bor (`local`, `mahalla`, `district`), katalogda esa **to'rtta**
`outage.scale.*` kaliti. 41-running `test_every_dynamic_family_is_complete`
testi oila → katalog yo'nalishida yashil, chunki u teskarisini
umuman ko'rmaydi. To'rtinchi kalit — `outage.scale.capped` — quyida.

---

## 2. O'lchov: 137 kalitning hammasi sanab chiqildi

Har bir kalit uchun manba qidirildi. Natija:

| Oila | Soni | Yo'l |
|---|---|---|
| `bot.*` | 27 | `handlers.py`, `keyboards.py`, `service.py` |
| `report.*` / `area.*` | 6 + 4 | `reply.MESSAGE_KEYS`, `lookup.MESSAGE_KEYS` |
| `notify.*` | 3 | `render.py` |
| `outage.confidence.*` | 4 | `clustering/confirmation.py:51–54` |
| `outage.scale.*` | 4 | `Scale` oilasi — **3 tasi**, biri yo'q |
| `map.*` | 17 | **faqat `web/`** (`data-i18n` + `app.js`) |
| `heatmap.*` | 9 | `web/` + `stats/heatmap.py` |
| `geo.*` | 3 | `geo/mahallas.py:40,47,52` |
| `stats.*` | 25 | `stats/*.py` konstantalari + 2 tasi `web/` da |
| `digest.*` | 17 | `admin/digest.py` |
| `error.*` | 16 | `message_key` atributlari va konstruktor argumentlari |
| `app.*` | 2 | `app.disclaimer` ✅, `app.name` ❌ |

### Uchta kalitga hech qanday yo'l yo'q

**`outage.scale.capped` — eng qimmati va butunlay yangisi.**
U dinamik oila a'zosiga **o'xshaydi** va aynan shuning uchun jim:
`Scale` da bunday a'zo yo'q, `scale_capped` esa **mantiqiy ustun**
(`clustering/models.py:108`). Qiymat bazaga yoziladi
(`clustering/service.py:372`), lekin birorta API javobiga chiqmaydi —
ya'ni `render.scale_text()` ham, `web/app.js:193` dagi
`t("outage.scale." + p.scale)` ham bu kalitni **yasay olmaydi**.
Natija: `06` §10 dagi qamrov chegarasining foydalanuvchiga ko'rinadigan
javobi ikkala tilda **yozilgan va ulanmagan**
(«Masshtabi aniqlanmagan — bu hudud bo'yicha qamrov past»).
Eng ehtimolli to'g'ri javob — o'chirish emas, **ulash**. 👤

**`bot.location.invalid` — ulanmagan javob.** `on_location`
`F.location` filtri bilan ro'yxatdan o'tgan (`bot/handlers.py:401`),
ya'ni `message.location` hech qachon `None` bo'lmaydi; hudud tashqarisi
`error.out_of_region` bilan javob beradi. Bugun yaroqsiz
geolokatsiyaning boshqa yo'li yo'q.

**`app.name` — 41-running taxminidan farqli, u tarmoqdan o'tadi.**
`/map/i18n` javobiga `app.` prefiksi orqali **tushadi**
(`api/v1/map.py:47`), lekin uni hech kim ko'rsatmaydi: sahifa sarlavhasi
`map.title` dan olinadi (`web/app.js:52`). Ya'ni «hech qayerdan
chaqirilmaydi» degani bilan «hech qayerda ko'rsatilmaydi» degani bir xil
emas, va o'chirish `/map/i18n` payloadini o'zgartiradi.

**Kod o'zgartirilmadi, kalitlar o'chirilmadi** — uchtasi ham
`PROGRESS.md` ning «Ochiq savollar» iga alohida yozildi (👤).

---

## 3. Test — `tests/test_i18n_key_contract.py`, 3-qatlam (5 ta yangi test)

### Prefiks emas, aynan tenglik

Katalog kalitiga **teng** bo'lgan har bir o'zgarmas satr murojaat deb
hisoblanadi. Prefiks bo'yicha o'qish 41-run o'lchagan yolg'onlarni
qaytarardi, faqat teskari tomonga:

| Satr | Aslida nima | Katalog kalitimi |
|---|---|---|
| `"outage.read"`, `"digest.read"` | ruxsat (`admin/roles.py`) | yo'q |
| `"outage.reject"`, `"outage.merge"` | audit amali (`admin/audit.py`) | yo'q |
| `"digest.send_failed"` va 4 ta | jurnal hodisasi (`jobs/daily_digest.py`) | yo'q |
| `"map.snapshot_missing"` | jurnal (`clustering/snapshot.py:209`) | yo'q |
| `"notify.default_radius_m"` | konfiguratsiya (`notifications/params.py:53`) | yo'q |
| `"outage.confirmed"` | outbox topigi | yo'q |

Bittasi ham tenglik qoidasiga tushmaydi.

### Skaner `t()` ga bog'lanmaydi

Kalitlarning katta qismi chaqiruv joyidan uzoqda:
modul konstantasi (`WARNING_MISSING = "geo.warning.mahallas_missing"`),
ro'yxatga qo'shish (`keys.append("digest.warning.queue")`),
sinf atributi (`message_key = "error.not_moderatable"`).

### `MAP_I18N_PREFIXES` ataylab yo'l deb hisoblanmaydi

**Testning eng muhim qarori.** Uni qabul qilish `map.*`, `stats.*`,
`heatmap.*`, `app.*`, `outage.*` — **137 dan ~56 kalitni** avtomatik
oqlab, qoidani o'sha kalitlar uchun jimgina ma'nosiz qilardi. Ya'ni bu
testni yozishning eng oson xato usuli: hamma yashil, hech narsa
o'lchanmaydi.

Uning o'rniga **mijoz** o'qiladi: `web/index.html` ning `data-i18n`
atributlari va `web/app.js` ning `t("…")` chaqiruvlari — **26 ta kalit**,
ular Python kodida umuman uchramaydi. Aynan shu qaror `heatmap.cell` ni
(faqat `app.js:146`) va `app.name` ni (hech qayerda) bir-biridan
ajratadi.

`t("outage.scale." + p.scale)` (`app.js:193`) tenglik qoidasiga
**tushmaydi** va bu to'g'ri — u oila, `KEY_FAMILIES` da sanaladi.

### Qulflar

- **`KNOWN_UNREACHABLE` — qo'lda va sabab bilan** (35/38-sessiyalarning
  naqshi). Uch tomonlama: yangi o'lik kalit paydo bo'lsa test yiqiladi;
  ro'yxatdagisi ulansa ham yiqiladi
  (`test_every_known_unreachable_key_is_still_unreachable`);
  katalogdan olib tashlangan eskirgan yozuv ham ushlanadi.
- **Oq ro'yxatning o'zi** (`test_every_map_i18n_prefix_still_matches_a_key`):
  `heatmap.` `heat.` ga qayta nomlansa `/map/i18n` o'sha oilani berishdan
  to'xtaydi va sahifa **bo'sh satrlar** ko'rsatadi — mijoz tomonidagi
  `t()` ham topa olmagan kalitni qaytaradi, ya'ni xato chiqmaydi.
- **`web/` skaneri** (≥20 kalit, `stats.coverage.title` HTML dan,
  `heatmap.cell` JS dan): fayl ko'chirilsa yoki `data-i18n` shakli
  o'zgarsa u bo'shab qolardi va 26 ta tirik kalit birdan «o'lik» bo'lib
  ko'rinardi — test o'zi qo'riqlayotgan xatoni **o'zi** yasab berardi.

---

## 4. Fayllar

| Fayl | O'zgarish |
|---|---|
| `sveta/tests/test_i18n_key_contract.py` | 3-qatlam: 2 ta skaner + 5 ta test; docstring (`24` → `30`) |
| `sveta/app/core/i18n/__init__.py` | `all_keys()` docstringi — u kalitni chaqiruvchidan yashiradi |
| `sveta/PROGRESS.md` | holat, run jurnali, «Ochiq savollar» da uchta kalit |
| `cowork_session/INDEX.md` | «Qayerda to'xtadik» |

Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik
**yo'q**, **xatti-harakat o'zgarishi ham yo'q** — faqat hujjat va
kontrakt.

---

## 5. Keyingi run uchun

⚠️ **O'n uchinchi marta** `ruff check` va `pytest -m "not requires_db"`
ishga tushmadi. **Sandbox tiklanganda birinchi ish — butun `pytest`,
yangi kod emas:** 36–42 runlarning ~82 ta testi hech qachon ishlamagan.

**Yopilgan nomzodlar, qayta ochilmasin:** i18n katalog → kod (42),
i18n kod → katalog (41), `05` §2 DDL indekslari (40), API `commit` (39),
`Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).

👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
`.\push.ps1`, va uchta i18n kaliti bo'yicha qaror
(ayniqsa `outage.scale.capped` — uni **ulash** ehtimoli yuqori).

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
Nomni tuzatish o'chirishni talab qiladi. 👤

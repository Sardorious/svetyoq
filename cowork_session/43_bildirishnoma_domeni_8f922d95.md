# 43-sessiya — bildirishnoma domeni: topik va status ro'yxatlari

**Sana:** 2026-08-09
**Epic:** E13 (ko'ndalang)
**Sessiya id:** `local_8f922d95`
**Sandbox:** ⚠️ **o'n to'rtinchi ketma-ket** yiqilish (INFRA-1) — ikki
urinish, ikkalasi ham `useradd failed: … No space left on device`. Butun
run **faqat fayl asboblari** bilan bajarildi; `ruff` ham, `pytest` ham
ishga tushmadi.

---

## 1. 42-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q

`tests/test_i18n_key_contract.py` ning 3-qatlami manba bilan
solishtirildi:

- **`WEB_ROOT` yo'li to'g'ri.** `APP_ROOT = <repo>/sveta/app`, ya'ni
  `APP_ROOT.parent / "web"` = `sveta/web/` va u yerda haqiqatan
  `index.html`, `app.js`, `style.css`, `README.md` bor. Skaner faqat
  `.html`/`.js` ni o'qiydi — ikkalasi ham joyida.
- **Ikkala tayanch kalit ham topiladi:** `stats.coverage.title` —
  `web/index.html:67` da `data-i18n` atributi; `heatmap.cell` —
  `web/app.js:146` da `t("heatmap.cell", {…})`. `_WEB_TOKEN` regexi
  ikkalasini ham bir xil shaklga tushiradi.
- **`MAP_I18N_PREFIXES` mavjud va oq ro'yxat** (`api/v1/map.py:43`):
  `map.`, `outage.scale.`, `outage.confidence.`, `app.`, `stats.`…;
  `get_map_i18n` uni `all_keys()` ga prefiks bilan qo'llaydi
  (`map.py:227`). Ya'ni 42-running «uni yo'l deb hisoblamaymiz» qarori
  hamon kuchda va `test_every_map_i18n_prefix_still_matches_a_key`
  import qiladigan nom joyida.
- **`KNOWN_UNREACHABLE` ning uchala kaliti ham katalogda bor va
  haqiqatan uch xil sinf:** `app.name` (`uz.json:2`, `ru.json:2`),
  `bot.location.invalid` (`:18`), `outage.scale.capped` (`:51`).
  `Scale` da uchta a'zo (`local|mahalla|district`, `scale.py:24–27`),
  katalogda esa to'rtta `outage.scale.*` — 42-running sanog'i aniq.
- **`Scale` bilan bog'liq qo'shimcha fakt:** `ScaleDecision.reason`
  (`scale.py:88`) yettita qiymat qaytaradi (`district_stats_unknown`,
  `mahalla_stats_unknown`, `low_district_coverage`,
  `low_mahalla_coverage`, `no_cap`, `estimated_quality`, `raw`) va
  ularning **bittasi ham** hech qayerga yozilmaydi — `clustering/
  service.py:388` dagi `"reason"` `StatusDecision` niki, `ScaleDecision`
  niki emas. Bu defekt emas (ichki qiymat), lekin `outage.scale.capped`
  ning ulanmaganligi bilan bitta manzarani to'ldiradi.

**Yopilgan nomzod, qayta ochilmasin: ustunlar pariteti.** 40-run faqat
indekslarni solishtirgan edi, shuning uchun «`05` §2 DDL ustunlari ↔
modellar» nomzodi tabiiy ko'rinardi. U **allaqachon yopiq**:
`tests/test_schema.py` `SPEC_COLUMNS` + `ADDED_BY_E19` + `ADDED_BY_06` +
uchta `SPEC_TABLES_*` ni yig'ib har bir jadval uchun **aynan tenglik**
talab qiladi (`test_columns_match_spec`), ustiga NFR-S-02 (`region_id`
bilan boshlanadigan indeks), PK lar va nullable qoidalari ham u yerda.

---

## 2. Running ishi — bildirishnoma domenidagi drift

### 2.1. Topilgan fakt

`app/notifications/models.py` da ikkita modul darajasidagi ro'yxat bor:

```python
OUTBOX_TOPICS = ("outage.confirmed", "outage.resolved")
NOTIFICATION_STATUSES = ("queued", "sent", "failed", "skipped")
```

Butun repo bo'ylab qidiruv: **ikkalasini ham hech kim import qilmaydi**
(yagona uchrash joyi — e'lonning o'zi). Ular sxemani o'qiyotgan odam
uchun yozilgan hujjat.

Va **`NOTIFICATION_STATUSES` eskirgan**: `app/notifications/service.py:56`
da `STATUS_CLOSED = "closed"` bor va u bazaga **yoziladi**
(`prepare()` `next_status = STATUS_CLOSED` beradi, `deliver()` uni
`_mark(...)` orqali ustunga yozadi). Ya'ni bugungi holatda beshta qiymat
ishlatiladi, ro'yxatda to'rttasi. `service.py` ning o'z docstringi
buni ochiq aytgan («`closed` — shu runda qo'shilgan qiymat»), lekin
ikkinchi ro'yxat yangilanmagan va hech narsa xato bermagan.

### 2.2. Nima uchun jim

`05` §2.4: `outbox.topic` ham, `notifications.status` ham erkin `text`.
Bazada `CHECK` yo'q, ya'ni har qanday satr `INSERT` dan o'tadi.

Topik tomonida narx og'irroq va u **uchta modulga** taqsimlangan:

| Yetishmasa | Nima bo'ladi |
|---|---|
| `render.MESSAGE_KEYS` | `render()` `None` qaytaradi → qator `skipped` |
| `prepare()` dispetcheri | `else` → bitta `log.warning`, bo'sh ro'yxat |

Ikkala holatda ham `DeliveryReport.failed == 0`, ya'ni
`report.complete` **rost**, va `jobs/process_outbox.py:82` qatorni
`mark_processed` bilan yopadi. Xabar yo'qoladi, navbatda iz qolmaydi,
istisno yo'q.

### 2.3. Driftning bugungi narxi — ikkita alohida oqibat

**(a) Kunlik hisobot yuborilgan bildirishnomalarni kam ko'rsatadi.**
`notifications/queries.py:status_counts_between` `status` ning **joriy**
qiymati bo'yicha guruhlaydi (`sent_at` oynasi bilan). Bitta qator ikki
marta yuboriladi: `outage.confirmed` uni `sent` qiladi,
`outage.resolved` esa **o'sha qatorni** `closed` ga o'tkazadi va
`sent_at` ni yangilaydi. `admin/digest.py:229` esa
`notifications.get("sent", 0)` ni o'qiydi — ya'ni bir kunda ham
tasdiqlangan, ham yopilgan hodisa hisobotdagi «yuborildi: N» sonidan
**butunlay tushib qoladi**. Hisobot tizim eng yaxshi ishlagan kunlarda
eng ko'p yolg'on gapiradi. Bironta test `closed` ni digest qatlamida
umuman ko'rmaydi.

**(b) `outage.resolved` ning qayta urinishi teshik.** `deliver()`
yiqilgan yuborishni `failed` ga o'tkazadi; `prepare()` esa
`TOPIC_RESOLVED` uchun **faqat `sent`** qatorlarni tanlaydi
(`service.py:187`). Ya'ni qayta urinishda o'sha qator topilmaydi →
`pending` bo'sh → `planned = 0`, `failed = 0` → `complete` → qator
yopiladi. Yopilish xabari o'sha odamlarga **hech qachon** bormaydi,
holbuki modul docstringi at-least-once ni va'da qiladi.

### 2.4. Qilingan ish

**Tuzatildi (xatti-harakat o'zgarishisiz):** `NOTIFICATION_STATUSES` ga
`"closed"` qo'shildi. Ro'yxatni hech kim import qilmagani uchun bu
o'zgarish hech qanday yo'lga tegmaydi — u faqat hujjatni haqiqatga
qaytaradi.

**Yozildi (kontrakt):**

- `models.py` — ikkala ro'yxatning **nima uchun** xavfli ekani: ular
  ikkinchi nusxa, ularni hech kim import qilmaydi, ya'ni drift jimgina
  yashaydi; `closed` ning kech qo'shilgani va uning izi.
- `queries.py` (`status_counts_between`) — kesim **joriy status**
  bo'yicha ekani va undan kelib chiqadigan kam sanoq; funksiyaning o'zi
  o'zgartirilmadi, chunki u xom kesimni qaytaradi va u yerda ma'lumot
  to'liq — chelaklarni qanday qo'shish kerakligi odamning qarori.
- `service.py` (`prepare`) — topik→auditoriya va topik→matn jadvallari
  **ikki xil modulda** ekani va ikkalasi ham jim buzilishi; hamda
  `TOPIC_RESOLVED` ning qayta urinish qirrasi ochiq qoldirilgani va
  nima uchun `failed` ni ro'yxatga shunchaki qo'shib bo'lmasligi.

**O'lchov:** yangi `tests/test_notification_domain_contract.py` — 9 ta
bazasiz test.

### 2.5. Tuzilish qarorlari

- **`ast` faqat ikkita joyda ishlatiladi va sababi bor.** Dispetcher —
  jadval emas, `if/elif` zanjiri, ya'ni uni obyekt sifatida o'qib
  bo'lmaydi; `STATUS_*` konstantalari ham modul darajasidagi oddiy
  nomlar, hech qanday to'plamga yig'ilmagan. **Qolgan hamma narsa
  haqiqiy import qilingan obyektdan** o'qiladi (41-sessiyaning qarori).
- **`dir(module)` rad etildi:** u import qilingan nomlarni ham
  qaytaradi, ya'ni boshqa moduldan kelgan `STATUS_*` shu faylniki bo'lib
  ko'rinardi va domen **jimgina** kengayardi. `ast` esa faqat shu faylda
  e'lon qilinganini ko'radi.
- **Dispetcher skaneri solishtiruvning o'ng tomonida faqat `TOPIC_*`
  nomini qabul qiladi**, o'zgarmas satrni emas: `row.topic ==
  "outage.confirmed"` `events.py` ni chetlab o'tgan uchinchi nusxa
  bo'lardi — aynan shu fayl to'sishi kerak bo'lgan drift.
- **Teskari yo'nalish alohida test** (42-sessiyaning naqshi): hech kim
  chiqarmaydigan topik `outage.scale.capped` bilan bir xil sinf —
  ro'yxatda turadi, matni bor, va uni ko'rgan odam «bu holat ishlangan»
  deb o'qiydi.
- **Producer tomonida `<=`, teskarisida `==`:** topik `events.TOPICS`
  dan tashqariga chiqa olmaydi (qat'iy), lekin kelajakda ikkinchi
  chiqaruvchi paydo bo'lishi mumkin, shuning uchun «kim chiqaradi»
  savoli `NOTIFIABLE_TOPICS` ga qattiq bog'lanmaydi.
- **Xatti-harakat o'zgartirilmadi.** Ikkala oqibat ham (kam sanoq va
  qayta urinish teshigi) foydalanuvchiga ko'rinadigan qaror talab
  qiladi, `pytest` esa o'n to'rt rundan beri ishga tushmagan — ko'r
  holda raqam yoki yuborish semantikasini o'zgartirish bu faylning
  o'zi ogohlantirayotgan xatoning aynan o'zi bo'lardi.

---

## 3. Keyingi run uchun

⚠️ **O'n to'rtinchi marta** `ruff check` va `pytest -m "not requires_db"`
ishga tushmadi. **Sandbox tiklanganda birinchi ish — butun `pytest`,
yangi kod emas:** 36–43 runlarning ~91 ta testi hech qachon ishlamagan.

**Yopilgan nomzodlar, qayta ochilmasin:** bildirishnoma domeni (43),
`05` §2 DDL **ustunlari** (allaqachon `test_schema.py` da — 43 tasdiqladi),
i18n katalog → kod (42), i18n kod → katalog (41), `05` §2 DDL
indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38),
`02` Faza 0 (34).

**👤 Odam qaroriga bog'liq:**

1. **Digest «yuborildi» soni** — `closed` chelagi `sent` ga qo'shilsinmi
   (`admin/digest.py:229`), yoki hisobotda alohida qator bo'lsinmi?
2. **`outage.resolved` qayta urinishi** — `failed` qatorlar yopilish
   xabarini olsinmi? Bitta ustun ikkala yuborishga xizmat qilgani uchun
   javob ustun qo'shishni talab qilishi mumkin.
3. Uchta i18n kaliti (42-rundan): `outage.scale.capped` (ulash ehtimoli
   yuqori), `bot.location.invalid`, `app.name`.
4. `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
   `git rm cowork_session/42_i18n_teskari_yonalish_local.md` (42-run
   xato nom bilan yaratgan bo'sh fayl), `.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
Nomni tuzatish o'chirishni talab qiladi. 👤

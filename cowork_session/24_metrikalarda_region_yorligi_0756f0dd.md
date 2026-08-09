# 24-sessiya — metrikalarda `region` yorlig'i (`01` §22 va §23 ning 6-mezoni)

**Sessiya:** `local_0756f0dd` · **Sana:** 2026-08-08 · **Sandbox:** ishladi

---

## Nima uchun aynan shu ish

23-sessiya `01` §23 ning ettita qabul mezonini kod bilan solishtirib,
ikkitasi buzilganini topgan edi. 7-mezonni («дисклеймер молодого
региона») o'sha run tuzatdi, 6-mezonni esa — «Метрики размечены
`region`» — «keyingi run uchun birinchi nomzod» deb yozib qoldirdi.
Boshqa bloklanmagan kod ishi yo'q edi (E17/E18/E20 va ikkinchi
mintaqaning haqiqiy importi odam qaroriga bog'liq), ya'ni tanlov aniq.

Talab `01` §22 da yozilgan:

> Все продуктовые метрики размечены `region` — иначе самаркандские
> данные растворятся в ташкентских.

Kodda esa `05` §10 ning **yettitasidan ikkitasi** yorliqlangan edi
(`outages_open`, `snapshot_age_seconds`). Qolgan beshtasi global:
`reports_received_total`, `geo_unmatched_ratio`,
`notifications_failed_total`, `time_to_confirm_seconds`,
`outbox_lag_seconds`.

**Nima uchun bu kosmetik emas.** Zarar bitta mintaqada ko'rinmaydi — u
aynan **E19 dan keyin** boshlanadi. Ikkinchi mintaqaning poligonlari
buzilgan bo'lsa, uning `geo_unmatched_ratio` si 30% bo'lishi mumkin,
lekin birinchi mintaqaning hajmi ostida umumiy ulush 3% bo'lib chiqadi
va 5% chegarasiga yetib bormaydi. Ya'ni ogohlantirish yo'qolmaydi —
**u jimgina noto'g'ri javob beradi**, bu esa yomonroq.

---

## Qilingan ish

### 1. `Readings` tuzilmasi qayta yig'ildi

Ilgari `Readings` ikki qavatli edi: global sonlar to'g'ridan-to'g'ri
maydonlarda, mintaqa sonlari esa `regions` ichida. Endi **hammasi**
`RegionReading` da, `Readings` da esa faqat `regions` qoldi.

Bu shakl talqinni imkonsiz qiladi: yangi metrika qo'shgan odam uni
qayerga yozishni tanlay olmaydi — mintaqasiz joy yo'q.

### 2. Beshta so'rovga `GROUP BY region_id`

| Metrika | So'rov | Manba |
|---|---|---|
| `reports_received_total` | `count_all` → `count_all_by_region` | `reports.region_id` |
| `geo_unmatched_ratio` | `unmatched_counts` → `unmatched_counts_by_region` | `reports.region_id` |
| `time_to_confirm_seconds` | `confirm_latency` → `confirm_latency_by_region` | `outages.region_id` |
| `notifications_failed_total` | `failed_total` → `failed_total_by_region` | **yangi ustun** |
| `outbox_lag_seconds` | `lag_seconds` → `lag_seconds_by_region` | `payload->>'region_id'` |

**So'rovlar soni o'zgarmadi** — yettitaligicha qoldi, faqat guruhlash
qo'shildi.

`lag_seconds` ning **mintaqasiz** varianti qoldirildi:
`process_outbox` uni jurnalga yozadi va vazifa uchun savol «navbat
qancha kechikdi», «qaysi mintaqada» emas.

### 3. `0007` — `notifications.region_id`

Yagona migratsiya talab qilgan metrika. `notifications` da mintaqa
haqida hech qanday ustun yo'q edi.

**Nima uchun `JOIN` emas.** `05` §1: modul boshqasining jadvaliga
tegmaydi. `app.notifications` `outages` ga `JOIN` qilsa, chegara
buzilardi — va aynan shu chegara `05` §2.4 dagi «payload o'zini o'zi
tushuntiradi» qaroriga asos bo'lgan. `events.py` ning izohi buni ochiq
yozadi: `process_outbox` hodisa haqidagi hech narsani `outages` dan
qayta o'qimaydi.

**Nima uchun bu kesh emas.** Bildirishnoma — o'tmish fakti: u
yuborilgan paytdagi mintaqaga tegishli. Hodisa keyinchalik
birlashtirilsa (`merged`) ham, o'sha kuni qaysi mintaqada yuborilgani
o'zgarmaydi. Ya'ni ustun `outages` dan **hosila emas**.

Backfill migratsiyada `outages` dan qilinadi va shundan keyingina
`NOT NULL` qo'yiladi (migratsiya sxema darajasida ishlaydi, modul
chegarasi unga tegishli emas). Indeks `(region_id, status)` — metrika
har scrape da aynan shu ikki ustun bo'yicha filtrlaydi va jadval
o'sib boradi.

### 4. `outbox` uchun ustun kerak bo'lmadi

`outbox.payload` da `region_id` **allaqachon bor** (`OutageEvent`).
Guruhlash `payload->>'region_id'` bo'yicha ketadi.

Ikkita ehtiyot chorasi:

- kalit `uuid` emas, **matn**: JSONB da tur kafolati yo'q va
  `uuid.UUID(...)` ni himoyasiz chaqirish bitta buzuq qator tufayli
  butun `/metrics` javobini yiqitardi;
- tanib bo'lmagan qiymat `region="unknown"` chelagiga tushadi va
  **ko'rinadi**. Uni jimgina tashlash yagona tiqilib qolgan navbatni
  metrikadan yo'qotardi — 21-sessiyaning «yo'q namuna — ogohlantirishning
  jim o'limi» qoidasi bilan bir xil sabab.

### 5. Mintaqalar ro'yxati kengaydi

`geo.region_codes()` — yangi so'rov, **faol emas mintaqalarni ham**
qaytaradi. Sabab: o'chirilgan mintaqada ham ochiq hodisa, tiqilib
qolgan outbox qatori yoki yiqilgan bildirishnoma qolishi mumkin.
Faollik faqat yangi xabar qabulini to'xtatadi, metrikadan chiqarishning
sababi emas.

Collector ro'yxatni **birlashma** sifatida yig'adi: faol mintaqalar
(hodisasi yo'q mintaqa `0` bilan chiqishi uchun) + o'lchovlarda uchragan
har qanday mintaqa.

### 6. Ogohlantirishlar — eng yomon mintaqadan

`05` §10 to'rtta shartdan ko'pini taqiqlaydi, o'lchovlar esa endi
mintaqa kesimida. Uchala o'lchovli shart mintaqalar bo'yicha
**maksimum** dan hisoblanadi (`max_snapshot_age_s` allaqachon shunday
edi, `max_outbox_lag_s` va `max_geo_unmatched_ratio` qo'shildi).

O'rtacha yoki yig'indi olish aynan `01` §22 ogohlantirgan xatoni
takrorlardi. Bu test bilan qulflandi: `0.01` va `0.30` yonma-yon
turganda ogohlantirish chiqishi kerak.

### 7. Kontrakt testi

`test_every_product_metric_carries_a_region_label` — `05` §10
jadvalidagi yettala metrikani **nom bilan** sanaydi va har birida
`region` yorlig'i borligini tekshiradi.

Defekt aynan shu bilan boshlangan edi: ikkitasi yorliqlangan, beshtasi
yo'q, va buni hech qanday test ushlamasdi. Ro'yxatga yangi metrika
qo'shgan odam endi testni ham yangilashga majbur.

Yorliqsiz qolgani ikkitasi va ikkalasi ham `05` §10 jadvalida yo'q:
`http_requests_total` (protsess hisoblagichi — mintaqa so'rov
darajasida ma'lum emas) va `alert_active` (ogohlantirishning o'zi).

---

## Qirralar

**DB testlarining fikstyurasi.** `only_our_region` `active_regions` ni
patch qilib «o'lchov faqat shu testning mintaqasini ko'rsin» deb
turgan edi. Endi collector mintaqalarni **o'lchovlardan ham** oladi,
ya'ni umumiy CI bazasidagi boshqa testlarning mintaqalari ham javobga
tushadi. Tekshiruvlar `_of(readings, region_id)` bilan o'z qatorini
tanlab oladigan bo'ldi.

**Yon foyda:** ilgari `reports_received_total` va
`notifications_failed_total` butun bazaning hisoblagichlari bo'lgani
uchun testda faqat **o'sish** ni tekshirish mumkin edi
(«before + 1»). Mintaqa kesimidan keyin aniq qiymat solishtiriladi
(`== 1`, `ratio == 1.0`) — ya'ni yorliq testlarni ham kuchaytirdi.

**`test_recluster_db.py`** `notifications` ga to'g'ridan-to'g'ri
`INSERT` qiladi — `region_id` qo'shildi, aks holda `NOT NULL` CI da
yiqilardi.

---

## Natija

- `ruff check` — yashil
- `pytest -m "not requires_db"` — **734 o'tdi, 0 yiqildi** (+3)
- `requires_db` — **164 ta** (+1)
- `alembic upgrade head --sql` — `0007` offline ishladi

**`01` §23 ning kodga tegishli mezonlari endi bajarilgan** va
`01`…`06` ning hammasi kod bilan solishtirilgan.

---

## Odamga savollar (bloklovchi emas)

1. `05` §2.4 DDL siga `notifications.region_id` yozib qo'yilsinmi?
2. `05` §10 jadvaliga «hammasi `region` bilan» qatori qo'shilsinmi?
   Talab `01` §22 da, `05` da esa yo'q — aynan shu bo'shliq defektning
   sababi bo'lgan (22-sessiya saboqi bilan bir xil).
3. Ogohlantirish qaysi mintaqada faolligini ko'rsatsinmi
   (`alert_active{alert=…,region=…}`)? Shartlar soni o'zgarmaydi,
   namunalar soni mintaqalar soniga ko'payadi.
4. `outbox` ga haqiqiy `region_id` ustuni qo'shilsinmi yoki JSONB dan
   o'qish qolsinmi (hozir `region="unknown"` chelagi bor)?

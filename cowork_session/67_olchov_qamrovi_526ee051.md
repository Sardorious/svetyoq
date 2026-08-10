# 67-sessiya — `03` §11 «Nima o'lchanadi» kodda: o'lchov qamrovi

**Sessiya:** `local_526ee051` · **Sana:** 2026-08-10 · **Blok:** REL
**Natija:** ✅ `app/release/measures.py`, `GET /api/v1/admin/measures`,
1706 passed (+52), migratsiyasiz, ruff yashil.

---

## Nima uchun aynan shu ish tanlandi

66-run ikkita nomzod qoldirgan edi: `03` §11 «Nima o'lchanadi» ↔ `05` §10
metrikalari, yoki `01` §21 analitika qatlami. Ikkinchisi **allaqachon
yozilgan** ekan (29-run, `app/analytics/catalogue.py`), ya'ni tanlov aslida
bitta edi.

Ustiga §11 — `03` dan qolgan **oxirgi** qamralmagan band. Kontrakt qatlami
(40–61 runlar) `05` va `06` ni to'liq qamragan, `03` esa qamralmagan
qolgan; 63-, 65- va 66-runlar undan uchta bajarilmagan bandni topdi. §11
ularning oxirgisi.

Bo'shliqning kattaligi: §11 yetti bosqich va o'n to'rtta ko'rsatkichni
**nom bilan** sanaydi, va ular bilan `05` §10 metrikalar reyestri
o'rtasida hech qanday bog'lanish yo'q edi. Ya'ni «R1.0 da Time-to-answer
p90 kuzatiladi» degan jumla oltmish rundan keyin ham hech qayerda
tekshirilmasdi — 66-run uning bitta uchini (G-5 mezoni uchun metrika yo'q)
tasodifan ko'rgan edi.

---

## Qarorlar

### 1. To'rtta holat, ikkitasi emas

«O'lchanadi / o'lchanmaydi» ikkiligi eng muhim narsani — bo'shliqni yopish
**narxini** — yo'qotardi:

| Holat | Ma'nosi | Narxi |
|---|---|---|
| `MEASURED` | bugun raqam bor, manbasi ko'rsatilgan | — |
| `DERIVABLE` | ma'lumot bazada yotibdi, so'rov yo'q | bitta `SELECT` |
| `ABSENT` | ma'lumotning **o'zi** yozilmaydi | ustun / hodisa / mahsulot qarori |
| `EXTERNAL` | mahsulot kodi buni hech qachon o'lchamaydi | — |

`EXTERNAL` bo'shliqqa qo'shilsa, hisobot ikkita deploy ko'rsatkichi tufayli
abadiy qizil qolardi va qolgan o'n ikkitasi ko'rinmas bo'lardi. Bu 66-run
ning `UNMEASURED` qarori bilan bir sinfdan, faqat teskari tomondan: u yerda
noaniqlikni **yaxshi** tomonga yumaloqlash taqiqlangan edi, bu yerda esa
yomon tomonga.

### 2. Hisobot statik va bazaga murojaat qilmaydi

`gates.py` «bugungi qiymat qanday?» deb so'raydi. Bu modul boshqa savolga
javob beradi: *bu ko'rsatkichni umuman o'lchay olamizmi?* Javob jonli
ma'lumotga emas, **kodning tuzilishiga** bog'liq — shuning uchun modul
bazaga ham, `settings` ga ham tegmaydi, endpoint esa `?region=` ni qabul
qilmaydi (qamrov butun mahsulot uchun bir xil).

Bu `tests/test_language_contract.py` ni qizil qildi va u yerda istisno
sabab bilan yozildi — testning o'zi «istisnolar ikkita bo'lsin» deb turadi,
ya'ni uchinchisi kelsa til qoidasining o'zi qayta ko'rib chiqiladi.

### 3. `bound` va `near` — alohida maydon

`near` bog'lanish **emas**, ogohlantirish: eng yaqin mavjud o'lchovni
tenglashtirish bo'shliqni yopmaydi, faqat ko'rinmas qiladi. Reyestr
tekshiruvi `MEASURED` qatorda `near` bo'lishini **taqiqlaydi** — aks holda
hisobotni o'qigan odam uni «deyarli bog'langan» deb o'qirdi.

Uchta xavfli juftlik:

* `answer_p90` ↔ `time_to_confirm_seconds` — ikkinchisi hodisa qachon
  **tasdiqlangani** ni o'lchaydi, foydalanuvchi savoliga qachon javob
  berilganini emas (66-run topgan);
* `matching_reports` ↔ `geo_unmatched_ratio` — nomida «unmatched» bo'lsa
  ham, u `district_id IS NULL` ni sanaydi, ya'ni **poligon sifati**;
* `notify_delivery_time` ↔ `outbox_lag_seconds` — navbatning yoshi
  yetkazish vaqti emas.

---

## Natija: o'n ikkitadan uchtasi

| Bosqich | Ko'rsatkich | Holat |
|---|---|---|
| M0–R0.3 | deploy chastotasi, quvur vaqti | `EXTERNAL` ×2 |
| Yopiq bosqich | hodisaga biriktirilgan xabarlar | `DERIVABLE` |
| Yopiq bosqich | qamralgan hudud ulushi | `ABSENT` |
| R1.0 | Time-to-answer p90 | `ABSENT` |
| R1.0 | xarita yangilanish kechikishi | ✅ `snapshot_age_seconds` |
| R1.1 | bildirishnoma yetkazish vaqti | `DERIVABLE` |
| R1.1 | obunani bekor qilish ulushi | `DERIVABLE` |
| R1.2 | agregatlar farqi | ✅ `Aggregation.reconciles` |
| R1.2 | Coverage Index taqsimoti | ✅ `MahallaCoverage.bands` |
| R2.0 | API p95 | `ABSENT` |
| R2.0 | tashqi foydalanuvchilar soni | `ABSENT` |
| Doimiy | moderatsiya SLA | `ABSENT` |
| Doimiy | avtotasdiqlash ulushi | `ABSENT` |

Birinchi bo'shliq — `matching_reports` (yopiq bosqich), ya'ni eng arzoni ham
eng erta bosqichda turibdi.

---

## Uchta yangi topilma

1. **`geo_unmatched_ratio` — nomi chalg'ituvchi.** U `05` §10 da «poligon
   sifati signali» deb ta'riflangan va aynan shu; §11 ning «hodisaga to'g'ri
   keladigan xabarlar soni» esa `reports.outage_id IS NULL` haqida.
   Ikkalasini tenglashtirish G-4 kirishini soxta yopardi. `reports.outage_id`
   nullable, ya'ni to'g'ri son bitta `COUNT(*)` bilan olinadi.

2. **Moderatsiya SLA si — `ABSENT`, `DERIVABLE` emas.** Audit jurnalida
   `outage.reject` va `outage.merge` vaqti bilan yotadi, ya'ni **qaror qabul
   qilingan** hodisalarning kutish vaqtini hisoblasa bo'ladi. Lekin SLA
   aynan qaror qabul qilinmagan navbat haqida: hodisa ko'rikka qachon
   tushgani hech qayerda saqlanmaydi (`needs_review` javob paytida
   hisoblanadi, `05` §4.2). Faqat yopilganlar bo'yicha o'lchangan SLA
   tizimli ravishda **yaxshi tomonga** yolg'on gapirardi — eng uzoq kutgan
   hodisalar namunaga umuman tushmaydi.

3. **«Avtotasdiqlash ulushi» bugun qurilishiga ko'ra `1.0`.** `05` §4.4
   status mashinasida `pending → confirmed` **faqat**
   `independent_reporters >= min_reporters` orqali o'tadi; moderator faqat
   `rejected` va `merged` qila oladi, va `AuditAction` da `outage.confirm`
   yo'q — garchi `05` §2.5 uni misol qilib keltirsa ham. Ya'ni ko'rsatkichni
   «o'lchash» tavtologiya bo'lardi. Bu kod kamchiligi emas, **hujjatlar
   orasidagi ziddiyat**.

Uchala da'vo ham **tripwire** bilan qulflandi: `05` §10 ga `answer_p90`
qo'shilgan, `AuditAction` ga `outage.confirm` kelgan yoki navbat ustuni
paydo bo'lgan kunda kontrakt testi qizil bo'ladi va qatorni `MEASURED` ga
o'tkazishni talab qiladi. Bo'shliq da'vosi jimgina eskirmaydi.

---

## Mutatsiya

**25 mutatsiya, 3 tasi bo'shliq ko'rsatdi** (hammasi tuzatildi, yakuniy
holat — 0 survivor):

1. `GAP_COVERAGES` dan `DERIVABLE` ni olib tashlash — **hech qanday test
   yiqilmadi.** `first_gap` testi o'zi bilan o'zi kelishgan edi
   («bo'shliqlar orasidagi eng erta bosqich»), ya'ni `DERIVABLE` bo'shliq
   sanalmay qolsa ham javob «to'g'ri» ko'rinardi. Yechim — holat jadvali
   testi (`is_gap` to'rtala holat uchun).
2. `MEASURED` da `near` taqiqi — parametrlangan ro'yxatda bunday qator yo'q
   edi.
3. `evaluate()` ning saralashi — reyestr allaqachon hujjat tartibida
   yozilgani uchun saralash **hech narsa qilmasdi** va isbotlanmagan edi.
   Yechim — teskari tartibdagi reyestr bilan test.

---

## Fayllar

| Fayl | Nima |
|---|---|
| `app/release/measures.py` | yangi — reyestr, `Coverage`, `Binding`, `evaluate` |
| `app/api/v1/admin.py` | `GET /admin/measures` |
| `app/admin/roles.py` | `Permission.MEASURES_READ` (admin) |
| `app/core/i18n/locales/{uz,ru}.json` | +28 kalit |
| `tests/test_release_measures.py` | yangi — reyestr, hisobot, endpoint |
| `tests/test_release_measures_contract.py` | yangi — `03` §11 hujjatdan + tripwire lar |
| `tests/test_i18n_key_contract.py` | `KEY_TABLES` ga ikkita jadval |
| `tests/test_language_contract.py` | `NO_REGION_PARAM` ga ikkinchi istisno |

---

## Odamga (👤)

1. **Moderator hodisani tasdiqlay olsinmi?** `05` §4.4 ga
   `pending → confirmed: moderator` va `AuditAction.OUTAGE_CONFIRM`
   qo'shilsa — «avtotasdiqlash ulushi» ma'noga ega bo'ladi; aks holda
   `03` §11 dan qatorni olib tashlash kerak.
2. **Navbatga tushish vaqti** uchun `outages` ga ustun (yoki alohida
   navbat jadvali) — migratsiya, ya'ni odam qarori.
3. **Ommaviy API** da iste'molchi identifikatori va javob vaqti
   gistogrammasi yo'q — R2.0 ning ikkala ko'rsatkichi ham shu bilan
   bloklangan. `answer_p90` bilan bir xil holat: `05` §10 ga yangi metrika
   kerak.

## Keyingi nomzodlar

`03` endi to'liq qamraldi. Eng arzon keyingi qadam — `matching_reports`
so'rovi (`reports.outage_id IS NOT NULL`, bitta `SELECT`, `DERIVABLE` →
`MEASURED`). Undan keyin `01` §21 «Дашборды» bo'limi: to'rtta dashboard
nomma-nom sanalgan va ular ham hech qayerda tekshirilmaydi.

## Muhit

♻️ Sandbox **to'qqizinchi** marta tekin keldi: `/tmp/sv59` butun holda
(`PYTHONPATH=/tmp/sv59` bilan `pytest` va `ruff` darhol ishladi) —
**avval `/tmp` ni qidir**.
⚠️ `/tmp` ga **yozib bo'lmaydi** (`Permission denied`); mutatsiya
ro'yxatlari `outputs/` ga yozildi.
⚠️ `ruff format --check` repo bo'ylab 86 faylni «qayta formatlash kerak»
deydi — sandboxdagi `ruff 0.16.2` CI dagidan farq qiladi. Tegilgan olti
fayl toza; qolganiga tegilmadi.

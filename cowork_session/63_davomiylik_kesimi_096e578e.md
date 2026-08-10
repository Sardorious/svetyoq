# 63-sessiya — E14: vitrinaning uchinchi kesimi (davomiylik)

**Sessiya:** `local_096e578e` · **Sana:** 2026-08-09 (UTC) · **Epic:** E14

---

## 1. Nimadan boshlandi

62-run ikkita nomzod qoldirgan edi: **E14 vitrinasi backendi** yoki E6
ustidagi sweep. E14 tanlandi.

Boshlashdan oldin `03` §R1.2 ning o'zi o'qildi va u kutilganidan aniqroq
gapirdi:

> | Statistika vitrinasi: hudud, davr, **davomiylik** kesimlarida | |

Kodda esa `app/api/v1/stats.py` ning modul izohi shunday boshlanardi:

> `GET /api/v1/stats` — **hudud va davr** kesimida + Coverage Index.

Ya'ni uchta kesimning ikkitasi bor edi. Uchinchisining o'rnida bitta son
turardi — `avg_duration_min`.

## 2. Nima uchun o'rtacha yetarli emas

Ikki mustaqil sabab, ikkalasi ham hujjatdan:

1. **O'rtacha — kesim emas.** U taqsimotni ko'rsatmaydi, aksincha uni
   bitta songa qisqartiradi.
2. **`01` §4 boshqa ikkita sonni talab qiladi.** KPI jadvalida ikkita
   qator bor:

   | KPI | Baseline (Ташкент) |
   |---|---|
   | Медианная длительность отключения | 44 мин |
   | P90 длительности | 4 ч 11 мин |

   Ikkalasi ham «не применимо как target — это **наблюдаемая величина**»
   deb belgilangan, ya'ni mahsulot ularni **o'lchay olishi** shart.
   O'rtachadan esa na mediana, na P90 chiqadi.

Ustiga, o'sha ikki bazaviy son taqsimot qanchalik qiya ekanini o'zi
ko'rsatadi: mediana 44 daqiqada, P90 esa undan **olti barobar** uzoqda.
Bunday taqsimotda o'rtacha mediananing ancha ustida yotadi va birorta
ham odatdagi uzilishni tasvirlamaydi.

`avg_duration_min` **olib tashlanmadi** — mijozlar unga tayangan
bo'lishi mumkin. U endi yolg'iz emas, xolos.

## 3. Run davomida topilgan narsa: taymer artefakti

Status mashinasini o'qiyotib (`app/clustering/status.py`) ma'lum bo'ldi:
hodisa uch xil sababdan yopiladi (`restored`, `autoclose`, `faded`) va
ulardan bittasi — **`autoclose`** — davomiylikni o'lchov bo'lishdan
to'xtatadi.

`05` §4.2 bo'yicha hodisa oxirgi xabardan `autoclose_after` (standart —
2 soat) o'tgach o'z-o'zidan yopiladi. Bunday hodisaning `resolved_at` i
kuzatuv emas: haqiqiy tiklanish oxirgi xabar bilan taymer orasidagi
qayerdadir bo'lgan va uni hech kim ko'rmagan. Agar shunday hodisalar
ko'p bo'lsa, «mediana davomiyligi» degan raqam aslida
`autoclose_after` ning aksi bo'lib qoladi — va uni o'lchov sifatida
nashr etish yolg'on bo'lardi.

**Belgi saqlanmaydi, chiqariladi.** `outages` da yopilish sababi uchun
ustun yo'q va uni qo'shish `06` §10 ning ro'yxatidan chetlashish bo'lardi.
Kerak ham emas:

```
resolved_at - last_report_at >= autoclose_after   →   taymer
```

Bu `evaluate_status` dagi shartning **aynan o'zi**. `restored` darhol
yopadi (oraliq ≈ 0), `faded` esa 45 daqiqada — ikkalasi ham chegaradan
past.

⚠️ **Chegarasi ochiq yozildi:** fon vazifasi to'xtab qolib, baholash
kechikib yurgizilsa, `restored`/`faded` ham shu oraliqqa tushib qolishi
mumkin. Ya'ni `timeout_closed` — taymer bilan yopilganlarning **yuqori**
bahosi, aniq soni emas.

## 4. Yozilgani

**`app/stats/duration.py`** — toza modul (bazasiz, konfiguratsiyasiz):

- `DurationFact` → `summarize` → `DurationCut`;
- `percentile` — PostgreSQL ning `percentile_cont` i bilan **bir xil
  usul** (`rank = p*(n-1)`, chiziqli interpolyatsiya). Tanlov ixtiyoriy
  emas: `app.clustering.queries` dagi tasdiqlash kechikishi metrikasi ham
  `percentile_cont` bilan hisoblanadi, ya'ni mahsulotda «P90» bitta
  ma'noni anglatadi;
- **uch xil hodisa — uch xil bilim:** `measured` (o'lchangan),
  `ongoing` (hali ochiq — davomiyligi yo'q) va `timeout_closed`;
- `MIN_SAMPLE = 5`: undan kam o'lchovda mediana ham, P90 ham `None`.
  Uchta qiymatdan chiqqan «P90» — eng katta qiymatning o'zi, ya'ni bitta
  hodisa haqidagi ma'lumot statistika niqobida (`05` §7.3 ning ruhi).
  Gistogramma va sanoq baribir qoladi;
- ikkita ogohlantirish: `duration_ongoing` (>20%) va `duration_timeout`
  (>50%), UZ/RU.

**Nima uchun `ongoing` alohida sanaladi.** Sabab statistik, kosmetik
emas: ochiq qolganlar aynan **eng uzun** uzilishlar. Ular namunadan
chiqib ketsa mediana pastga siljiydi va vitrina «uzilishlar qisqa»
degan xulosani sovg'a qiladi. Shuning uchun ulushi ochiq turadi va
chegaradan oshsa ogohlantirish chiqadi.

**Narvon:** `30 / 120 / 360 / 1440` daqiqa → beshta pog'ona.

| Chegara | Nima uchun |
|---|---|
| `30` | bazaviy mediana (44) dan **past** — aks holda yarmi bitta chelakda qolardi |
| `120` | standart `autoclose_after`: undan pastdagi yopilish taymer artefakti bo'lishi mumkin emas |
| `360` | bazaviy P90 (251) dan **yuqori** — oxirgi o'ndan bir o'z pog'onasida qoladi |
| `1440` | sutka: undan uzun uzilish avariya emas, uzoq ta'mirlash |

**Narvon konfiguratsiyaga bog'lanmadi** va bu ataylab qilingan qaror.
`120` `autoclose_after` ning joriy qiymatiga teng bo'lsa ham, u sozlama
o'zgarganda **siljimasligi** kerak: aks holda ikki davrning gistogrammasi
turli narvonlarda qurilib, taqqoslab bo'lmas edi. Taymerning o'zi alohida
o'lchov — `timeout_closed`.

**Ulanish:**

- `StatsRow` va `OutageFact` ga `last_report_at` (bitta mavjud so'rovga
  bitta ustun — yangi so'rov ham, yangi aylanish ham yo'q). Standart
  qiymat **berilmadi**: unutilgan maydon jimgina «taymer yo'q» degan
  javob berardi va hech qanday test yiqilmasdi;
- `Bucket.duration_facts` + `Bucket.duration`; `aggregate.build` endi
  `autoclose_after_min` ni **chaqiruvchidan** oladi (`min_reports` bilan
  bir xil chegara), `service` esa uni `settings.cluster_autoclose_after_min`
  dan beradi — vitrinada nusxa yo'q;
- `Aggregation.reconciles` endi **uchinchi kesimni ham** tekshiradi:
  o'lchangan + ochiq = chelakning umumiy soni. `03` §R1.2 mezoni kesimga
  emas, vitrinaga qo'yilgan;
- `StatsOut.total.duration` va har bir tumanda; CSV ga sakkizta ustun
  (mediana, P90, `measured`, `ongoing`, `timeout_closed`, beshta pog'ona).
  Namuna yetarli bo'lmasa mediana katagi **bo'sh**, nol emas: elektron
  jadval nolni raqam deb o'qib, «uzilishlar bir zumda tugagan» degan
  xulosaga olib kelardi;
- ogohlantirishlar **mintaqa** kesimidan: bitta tumanning kesimi qiya
  bo'lsa, bu vitrinaning umumiy ogohlantirishi emas.

## 5. Testlar

`tests/test_stats_duration.py` (43) + `test_stats_aggregate.py` (+7),
`test_stats_service.py` (+3), `test_stats_export.py` (+1),
`test_stats_api_db.py` (+2, `requires_db`).

Narvon **hujjatga bog'landi** (40–61 runlarning uslubi): `01` §4 dagi
«44 мин» va «4 ч 11 мин» testda **parse qilinadi** va ulardan uch talab
chiqadi — birinchi chegara mediananing ostida, mediana bilan P90 turli
pog'onalarda, P90 oxirgi pog'onada emas. `03` §R1.2 ning «hudud, davr,
davomiylik» qatori ham parse qilinadi: talab o'zgarsa test yiqiladi va
qolgan ikkitasi «tekshirdim» deb yolg'on gapirmaydi.

Yana bitta manba testi: `service.py` ning AST i o'qiladi va
`autoclose_after_min` ga faqat `settings.cluster_autoclose_after_min`
uzatilishi talab qilinadi. Nusxa ko'chirilgan `120` bugun to'g'ri javob
berardi va sozlama o'zgargan kunigina yolg'on bo'lib qolardi — ya'ni
hech qanday qiymat testi uni tutmaydi.

## 6. Mutatsiyalar — 16 ta, 5 tadan uch partiyada

Uchtasi **bo'shliq ko'rsatdi** (hammasi yopildi):

| Mutatsiya | Nima ochildi |
|---|---|
| `ongoing_ratio > MAX` → `>=` | taymer chegarasi uchun qat'iylik testi bor edi, ochiq hodisalar uchun yo'q. Yangi test 8 o'lchangan + 2 ochiq quradi: aynan `0.20`, va namuna `MIN_SAMPLE` dan katta — aks holda `sufficient` ogohlantirishning yo'qligini tushuntirib qo'yardi va test chegarani emas, boshqa narsani o'lchagan bo'lardi |
| `StatsReport.warnings` dan `duration.warnings` olib tashlansa | hech narsa yiqilmasdi: kesim ogohlantirishni **hisoblardi**, lekin vitrinaga chiqishi tekshirilmagan edi. Sim uzilsa javobda mediana qolardi, uni qanday o'qish kerakligi haqidagi izoh esa yo'qolardi |
| CSV sarlavhasi ↔ katak tartibi | `HEADER` va `_duration_cells` ikki xil joyda quriladi. Joy almashsa fayl baribir to'g'ri **ko'rinardi** — faqat mediana P90 deb o'qilardi. Endi qator `csv.DictReader` bilan **nomi bo'yicha** o'qiladi, va fikstyurada mediana bilan P90 ataylab **har xil** |

Qolgan 13 tasi darhol o'ldi. Har partiyadan keyin
`git status --porcelain` — repo toza qoldi (60-running qoidasi).

## 7. Natija

- `pytest -m "not requires_db"` → **1523 passed, 1 skipped** (+53)
- `requires_db` → **217** (+2)
- `ruff check app tools tests alembic` → toza
- migratsiya **yo'q**, yangi sozlama **yo'q**, yangi so'rov **yo'q**

## 8. Keyingi qadam

- **E14-a** — vitrina sahifasi. Backend endi to'liq (uchala kesim + CSV),
  qolgani interfeys; u esa **E9-b** (`web/` React ga o'tkazilsinmi) ga
  bog'liq — ikkalasi ham `PROGRESS.md` ning «Ochiq savollar» ida.
- Yoki E6 ustidagi sweep (bir necha ssenariyni ketma-ket).

**Yo'l-yo'lakay chiqqan xulosa.** Kontrakt qatlami (40–61) `05` va `06`
ni to'liq qamradi, lekin **`01` va `03` qamralmagan**: §R1.2 ning
uchinchi kesimi 15-rundan beri bajarilmagan holda «✅» ko'rinib turardi.
Ikkala hujjatda ham shunga o'xshash tekshirilmagan qatorlar bo'lishi
mumkin.

## 9. Infratuzilma

Sandbox **beshinchi marta ketma-ket** tekin keldi: `/tmp/sv59` butun
holda qolgan (104 paket, `ruff` ham), `$HOME` esa yana 100% (36 MB).
Retsept barqaror: **avval `/tmp` ni qidir**, keyin o'rnatishga urin.
👤 `cleanup-sessions.ps1` ni har run oldidan yurgizing.

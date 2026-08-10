# 60-sessiya — `05` §3 maxfiylik kontrakti (jitter, r9, `geom_exact` saqlash)

**Sana:** 2026-08-09 · **Sessiya:** `local_c01450c5-1956-491f-b604-0c3f1b2113a2`
**Epic:** E2 / E15-a (ko'ndalang) · **Natija:** ✅ yangi kontrakt fayli,
defekt topilmadi, **bitta nomuvofiqlik** ochiq savolga yozildi.

---

## 1. Qayerdan boshlandi

`EpicProgress.md` §3 ning oxirgi qatori aniq topshiriq qoldirgan edi:

> **Ochiq qolgani:** `06` §11 (34-run qisman yopgan). `05` tomonida faqat
> §3.1 (jitter) hali o'z kontrakt fayliga ega emas — §4.4/§4.5 ni 59-run
> yopdi.

Ya'ni 40–59 sessiyalarning kontrakt qatlamida `05` dan yagona bog'lanmagan
bo'lim qolgan edi. U tanlandi.

**Nima uchun bu bo'lim boshqalardan qimmatroq.** Qolgan bo'limlarning
artefakti — mahsulot xususiyati: buzilsa test yiqiladi yoki foydalanuvchi
noto'g'ri javob oladi. §3 ning artefakti — **maxfiylik kafolati**. U
buzilganda hech narsa yiqilmaydi: xarita ishlaydi, bot javob beradi,
testlar yashil. Buzilgani faqat foydalanuvchining uyi xaritada ko'ringanda
bilinadi — ya'ni amalda hech qachon.

## 2. Sandbox — 59-running retsepti ishladi

`/tmp/sv59` **butun holda qolgan** ekan (104 paket, `pytest` 9.1.1,
`h3` 4.5.0, `ruff` `/tmp/sv59/bin/ruff`), `$HOME` esa yana 100% (`/sessions`
9.8 G dan 38 M bo'sh). Hech narsa o'rnatilmadi:

```
PYTHONPATH=/tmp/sv59 TMPDIR=/tmp/tmpdir APP_ENV=test python3 -m pytest ...
PATH=$PATH:/tmp/sv59/bin ruff check app tools tests alembic
```

**Sabog'i 57-rundagidek:** avval `/tmp` da qolgan muhitni qidir, keyin
o'rnatishga urin. Ikki rundan beri bu eng arzon yo'l bo'lib chiqmoqda.

## 3. Nima yozildi — `tests/test_privacy_jitter_contract.py` (17 test)

Hujjatdan o'qiladigan beshta artefakt:

| `05` dagi joy | Artefakt | Kod |
|---|---|---|
| §3 bloki | olti qadamli quvur | `pipeline.py` modul docstringi (so'zma-so'z nusxa) |
| §3 bloki | `latlng_to_cell(lat, lon, **9**)` | `settings.h3_resolution`, `h3_cells.DEFAULT_RESOLUTION`, `reports.h3_r9` ustuni |
| §3.1 jadvali | ikkita **rad etilgan** usul | kodda izi yo'q — lekin sabablari talab |
| §3.1 tanlovi | markaz + doimiy siljitish, manba `hash(user_id, h3_cell)` | `jitter.public_point` / `offset_for` / `_unit_pair` |
| §3.2 | `90 kun`, `NULL`, fon vazifasi, `district_id`+`h3_r9` qoladi | `settings`, `purge_exact_geom_stmt`, `runner.JOBS` |

**Rad etilgan usullar bilan nima qilingan.** Ular kodda yo'q va bo'lishi
ham mumkin emas — rad etilgan variant iz qoldirmaydi. Lekin ularning
**sabablari** tanlangan usulga qo'yilgan talab, va aynan shu talab hech
qayerda o'lchanmagan edi:

* 1-qator, «o'rtacha qiymat aniq uyni beradi» → bitta foydalanuvchining
  bitta katakchadagi 200 ta xabari **bitta** ommaviy nuqta berishi shart
  (dispersiya nol, o'rtachalash yangi ma'lumot bermaydi);
* 2-qator, «aniqlik yo'qoladi» → siljitish nolga teng bo'lmasin, aks holda
  usul aynan o'sha rad etilgan variantga aylanadi va katakchadagi hamma
  foydalanuvchi bitta pikselga yig'iladi.

Ikkalasi ham endi test.

**«Doimiy (deterministik)»** AST bilan o'lchanadi: `jitter.py` da
o'rnatilgan `hash()` chaqiruvi ham, `random`/`secrets` importi ham
bo'lmasligi shart. `hash()` satrlar uchun `PYTHONHASHSEED` bilan
tasodifiylanadi — hujjatning «har doim bir xil nuqta» va'dasi shu bilan
jimgina buzilardi (`CLAUDE.md` da ham alohida yozilgan).

**«Faqat `(user_id, h3_cell)`»** ikki tomondan: xulq-atvor (bir xil juftlik
→ bir xil siljitish; boshqa foydalanuvchi yoki boshqa katakcha → boshqa)
va imzo (`_unit_pair` parametrlari **aynan** `["user_key", "cell"]` —
uchinchi kirish qo'shilsa siljitish aniq koordinatadan xabar topib qolardi).

## 4. Topilgan nomuvofiqlik — `174` m ↔ `201` m

Hujjat §3.1: «H3 r9 ≈ **174 m** o'rtacha qirra». `h3` 4.5.0 esa beradi:

| res | `average_hexagon_edge_length(res, unit="m")` |
|---|---|
| 8 | 531.4 m |
| **9** | **200.8 m** |
| 10 | 75.9 m |

`174` — H3 **v3** ning jadvalidan; h3-py 4.2 o'rtacha qirra hisobini
tuzatdi. Bir xil son `app/geo/h3_cells.py` ning modul docstringida ham bor.

**Bu defekt emas va kod o'zgartirilmadi.** Haqiqiy katakcha hujjat va'da
qilganidan **kattaroq**, ya'ni maxfiylik kuchsizlanmagan, aksincha
kuchaygan; «xarita uchun yetarli, uy uchun yetarli emas» degan xulosa
201 m da ham to'g'ri. Spetsifikatsiya — qonun (`CLAUDE.md` §2), shuning
uchun hujjatga tegilmadi va nomuvofiqlik `PROGRESS.md` ning «Ochiq
savollar» iga 👤 bilan yozildi.

**Test shuning uchun tenglik emas, tasma:** haqiqiy qirra hujjatdagi
sondan kichik bo'lmasin va uni ikki barobardan oshirmasin. Tasma vakuum
emasligi alohida test bilan isbotlangan — r8 (531 m) ham, r10 (75.9 m) ham
unga sig'maydi, ya'ni rezolyutsiya o'zgarishi baribir ushlanadi.

## 5. Mutatsiya bilan tekshirish — 18 ta

Har mutatsiya faylga yozildi, `pytest` yurgizildi, keyin `finally` da
tiklandi. **17 tasi darhol ushlandi, ikkitasi sabog' berdi:**

| Mutatsiya | Natija |
|---|---|
| doc: `latlng_to_cell(..., 9)` → `8` | 2 failed |
| doc: `**90 kundan keyin**` → `30` | 1 failed |
| doc: `WHERE valid_to IS NULL AND` olib tashlandi | 2 failed |
| doc: §3.1 jadvalining 2-qatori **o'chirildi** | 1 failed |
| doc: 2-qator qayta nomlandi (`H3` olib tashlandi) | 1 failed |
| doc: `≈ 174 m` → `≈ 74 m` | 2 failed |
| doc: manba `hash(user_id, h3_cell)` → `(user_id, lat, lon)` | 1 failed |
| code: `pipeline.py` docstringidan bitta qadam olib tashlandi | 1 failed |
| code: `blake2b` → o'rnatilgan `hash()` | 1 failed |
| code: `radius = 0.0` (siljitish yo'q) | 2 failed |
| code: markaz o'rniga aniq nuqta (`c_lat, c_lon = lat, lon`) | 2 failed |
| code: `_unit_pair` ga `salt` parametri | 1 failed |
| code: `jitter_max_m` 60 → 250 | 1 failed |
| code: `DEFAULT_RESOLUTION` 9 → 8 | 1 failed |
| muhit: `H3_RESOLUTION=10` | 1 failed |
| code: `values(geom_exact=null())` → `"POINT(0 0)"` | 2 failed |
| code: `purge_exact_geom.register()` olib tashlandi | 1 failed |
| code: `exact_geom_retention_days` 90 → 30 | 1 failed |

**Ikkita sabog':**

1. **`config.py` dagi standartni mutatsiya qilish yetmaydi** — `.env` da
   `H3_RESOLUTION=9` bor va u standartni bosadi. Ya'ni `settings` ga
   tayanadigan kontraktni tekshirish uchun mutatsiya **muhit o'zgaruvchisi**
   bilan qilinadi. (Test to'g'ri narsani — **amaldagi** qiymatni —
   tekshiradi, mutatsiya usuli noto'g'ri edi.)
2. **Birinchi urinishda jadval qatorini «qayta nomlash» ushlanmadi:** test
   faqat qatorlar **sonini** (2) va 1-qatordagi `150` ni talab qilardi,
   2-qatorning mazmuni esa bo'sh qolgan edi. Test kuchaytirildi
   (2-qatorda `H3` bo'lishi va unda kattalik **bo'lmasligi** — aynan shu
   farq ikkala rad etilgan usulni bir-biridan va tanlovdan ajratadi).

## 6. ⚠️ Yo'l-yo'lakay: mutatsiya harnessi runni deyarli buzdi

Birinchi mutatsiya to'plami bitta `bash` chaqiruvida 15 ta mutatsiyani
yurgizmoqchi bo'ldi va **120 s limitida uzildi** — `finally` bajarilmay
qoldi, `app/reports/queries.py` **mutatsiyalangan holda** qoldi
(`values(geom_exact="POINT(0 0)")`).

`git status --porcelain` uni darhol ko'rsatdi va fayl `Edit` bilan
tiklandi. Agar tekshirilmaganda repo maxfiylik defekti bilan commit ga
tayyor holatda qolardi — ya'ni tozalash `geom_exact` ni `NULL` qilish
o'rniga `POINT(0 0)` yozardi va ikkinchi yurishda `IS NOT NULL` filtri uni
umuman ko'rmasdi.

**Qoida keyingi runlarga:** mutatsiya to'plamini **5 tadan** bo'lib
yurgiz (`timeout_ms` ni ham oshir) va har to'plamdan keyin
`git status --porcelain` bilan tekshir. Uzilish `finally` ni kafolatlamaydi.

## 7. Holat

```
ruff check app tools tests alembic     → All checks passed!
pytest -m "not requires_db"            → 1415 passed, 1 skipped, 212 deselected
```

(59-run: 1398 passed → +17 yangi test.)

Vaqtinchalik fayl qoldirilmadi, `allow_cowork_file_delete` chaqirilmadi.

## 8. Keyingi qadam

`05` ning **butun** hujjati endi kod bilan bog'landi (§1–§10). `06` da
faqat §11 ning 34-run qamramagan qismi qoldi. Undan keyin kontrakt qatlami
tugaydi — keyingi runlar uchun nomzodlar `PROGRESS.md` ning «Ochiq
savollar» ida.

👤 **O'zgarmagan bloklar:** `push.ps1` (56-running logging fiksi hamon
commit qilinmagan — prodda SQL jurnali yoqiq), CI ni `NullPool` fiksi bilan
qayta yurgizish, `cleanup-sessions.ps1`.

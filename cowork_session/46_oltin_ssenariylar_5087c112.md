# 46-sessiya — oltin ssenariylar kontrakti (`05` §9.3 + `06` §12)

**Sana:** 2026-08-09
**Sessiya:** `local_5087c112-6f99-4998-b072-40d3b6be01d2`
**Epic:** E5 (klasterlash) / ko'ndalang kontrakt testi
**Sandbox:** ⚠️ **o'n yettinchi ketma-ket run yiqildi** —
`useradd failed: /etc/passwd.NNNNN: No space left on device` (INFRA-1).
`ruff check` va `pytest` yana ishga tushmadi.

---

## 1. 45-running kodi qo'lda audit qilindi — defekt yo'q

`tests/test_jobs_registry.py` ning har bir tayanchi manba bilan
solishtirildi:

- **`05` §8 jadvali** — oltita qator, chastota so'zlari aynan
  `FREQUENCY_S` dagilar (`60 s`, `5 s`, `kuniga`, `soatiga`); sarlavha
  qatori (`| Vazifa | Chastota | Ish |`) `_SPEC_ROW` regexiga tushmaydi,
  chunki nomda backtick yo'q.
- **`app/jobs/`** — aynan sakkizta fayl: oltita vazifa +
  `runner` + `__init__` (`NOT_A_JOB` bilan mos).
- **Oltala modulda** `JOB = Job(...)`, `register()` va modul nomiga teng
  `JOB.name` bor; `register_jobs()` oltalasini ham chaqiradi.
- **`INTERVAL_S`** qiymatlari `IMPLEMENTED` bilan bir xil (60/60/5/3600/
  86 400/86 400).
- **Handler imzolari:** `build_map_snapshot`, `evaluate_outages`,
  `process_outbox`, `refresh_coverage` — argumentsiz `run()`;
  `purge_exact_geom` va `daily_digest` — `_tick` o'rami (45-run aytgan
  qirra haqiqatan joyida).

Ya'ni 45-run to'g'ri yozgan, tuzatish talab qilinmadi.

## 2. Nomzod: «majburiy» so'zi hech narsani ushlab turmasdi

`CLAUDE.md` va scheduled task ko'rsatmasi bir xil jumlani takrorlaydi:
«`05` §9.3 va `06` §12 dagi oltin ssenariylar **majburiy**». Bu jumla
bugungacha faqat **docstringlarda** yashagan:

- `test_scale.py:145` — «§12.11», `test_confirmation.py:290` — «§12.8»,
  `test_area_status_db.py:1` — «§9.3 5-ssenariy», `test_simulate.py:229`
  — «`05` §9.3 oltita ssenariyni majburiy qiladi» (faqat generatorning
  kalitlarini sanaydi).

Docstring esa hech qanday tekshiruv emas. Uchta yo'nalish jim edi:

1. **Hujjatga 14-ssenariy qo'shilsa** — hech narsa yiqilmaydi, ssenariy
   hech qachon yozilmaydi.
2. **Qoplaydigan test o'chsa yoki nomi o'zgarsa** — «§12.13» havolasi
   funksiya bilan birga ketadi, qolgan testlar yashil qolaveradi.
3. **Ssenariy faqat `requires_db` testi bilan qoplansa** — sandboxda
   umuman o'lchanmaydi. Bu faraz emas: `pytest` o'n olti rundan beri
   faqat bazasiz qatlamda ishlashi mumkin edi, u ham ishlamadi.

## 3. Avval mavjud testlar qidirildi (43 va 45-sessiyaning saboqi)

Har o'n uchala ssenariy bo'yicha suite skanerlandi. Natija: **hammasi
qoplangan**, ya'ni bu safar yangi ssenariy testi yozish kerak emas edi —
yetishmagani **bog'lanish** edi. Qoplama shunday taqsimlangan:

| № | Bazasiz tayanch | Bazali tayanch |
|---|---|---|
| 1 | `test_clustering_status::test_single_report_stays_pending` | `test_clustering_service_db` |
| 2 | `…::test_three_independent_reporters_confirm` | `test_clustering_service_db` |
| 3 | `…::test_one_user_five_reports_does_not_confirm` + `test_confirmation` | `test_clustering_service_db` |
| 4 | `test_simulate::test_two_distant_mahallas_are_really_distant` | `test_clustering_service_db` |
| 5 | `test_clustering_lookup::test_uncovered_area_admits_ignorance` | `test_area_status_db` (2 ta) |
| 6 | `test_clustering_status` (2 ta) | `test_clustering_service_db` |
| 7 | `test_scale::test_example_7_…` + `test_confirmation::test_example_7_…` | — |
| 8 | `test_confirmation::test_scenario_8_…` | — |
| 9 | `test_confirmation::test_example_3_two_heavy_sources_two_people` | — |
| 10 | `test_confirmation` (2 ta) | — |
| 11 | `test_scale::test_scenario_11_…` | — |
| 12 | `test_confirmation::test_time_factor_steps` + `test_clustering_status` (2 ta) | `test_clustering_service_db` |
| 13 | `test_confirmation` + `test_recluster::test_fingerprint_is_stable…` | `test_simulate_db` |

**Qirra:** 7-ssenariy `test_scale.py` da «§7.7» deb yozilgan (`06` §7
ning ishlangan misoli), «§12.7» deb emas — ya'ni docstring bo'yicha
qidirish uni topmasdi. Aynan shuning uchun bog'lanish qo'lda va ochiq
yoziladi, matn qidiruvi bilan emas.

## 4. Qarorlar

- **Hujjat parse qilinadi, `COVERAGE` esa qo'lda qoladi** — 40 va
  45-sessiyalarning naqshi: qo'lda yozilgan ro'yxat qiymatlarni
  qulflaydi, o'zi esa manba bilan solishtiriladi.
- **Kalit so'z ham qulflanadi.** Faqat raqamlar solishtirilsa, qator
  qayta yozilib boshqa narsani anglashi mumkin edi va tenglik yashil
  qolardi. Har raqam uchun hujjat qatorida bo'lishi shart bo'lgan bo'lak
  yozilgan. **Apostrofsiz tanlandi** ataylab: hujjatlarda `'` va `'`
  aralash uchraydi va kalit so'z shu sababli yolg'on yiqilishi mumkin
  edi.
- **Raqamlash uzluksizligi — alohida test.** `06` §12 «`05` §9.3 ga
  qo'shimcha» deb boshlanadi va **7 dan** davom etadi. Butun suite dagi
  «§12.N» havolalari shu farazga tayanadi: `05` §9.3 ga yettinchi qator
  qo'shilsa har bir havola jimgina boshqa ssenariyni ko'rsatib qolardi.
- **Har ssenariyning bazasiz tayanchi majburiy.** Eng qimmat qoida:
  faqat `requires_db` bilan qoplangan ssenariy PostGIS bo'lmagan muhitda
  (bugungi holat) jimgina o'tkazib yuboriladi — `pytest` yashil,
  ssenariy tekshirilmagan. Bugun o'n uchala ssenariyning ham bazasiz
  tayanchi bor, ya'ni qoida bugundan boshlab **regressiyani** ushlaydi.
- **Bitta test ikkita ssenariyni qoplay olmaydi** — aks holda qoplama
  «bor» ko'rinardi, aslida bitta tekshiruv ikki joyda sanalgan bo'lardi.
- **`ast` ishlatilmadi:** modullar import qilinadi va funksiya obyekti
  `getattr` bilan olinadi — shunda `pytestmark` markerlari ham o'sha
  obyektdan o'qiladi. Import xavfsiz: hamma `*_db.py` modullarida faqat
  modul darajasidagi konstantalar va `pytestmark` bor, ulanish yo'q.
- **`pytest.Mark` / `MarkDecorator` turi bo'yicha tekshirilmaydi:**
  modul darajasidagi `pytestmark = pytest.mark.requires_db` —
  `MarkDecorator`, funksiya darajasidagisi — `Mark`. Ikkalasida ham
  `.name` bor, shuning uchun ro'yxat bo'lmagan hamma narsa o'raladi
  (pytest ning ichki API si versiyaga bog'liq bo'lib qolmasin).

## 5. Topilgan farq (kod o'zgartirilmadi)

`05` §9.3 ning birinchi qatori: «Bitta uy — **hodisa yaratilmaydi**».
Kod esa `pending` hodisa yaratadi va uni tasdiqlamaydi (`05` §4.2 da har
bir xabar hodisaga biriktiriladi, `pending` — ochiq status, `05` §4.4).
Bu ataylab va **uch joyda** ayni shunday o'qilgan:

- `tools/simulate.py` — `single_house` ssenariysining izohi: «Bitta
  xabar `pending` hodisa yaratadi, lekin u tasdiqlanmaydi»;
- `test_clustering_service_db.py` — testning **nomi**:
  `test_single_house_creates_pending_but_not_confirmed`;
- yangi kontrakt testidagi `note`.

`CLAUDE.md` §2 bo'yicha spetsifikatsiya — qonun, ya'ni bunday
nomuvofiqlik kodda emas, **«Ochiq savollar»** da hal qilinadi. Yozildi:
hujjat qatori aniqlashtirilsinmi yoki bugungi o'qilish yozilmagan
kelishuv bo'lib qolaversinmi. 👤

## 6. Yozildi

- **`sveta/tests/test_golden_scenarios_contract.py`** — yangi fayl,
  8 ta bazasiz test: skaner bo'shligi, raqamlash uzluksizligi, ikki
  tomonlama tenglik, kalit so'zlar, havolalarning mavjudligi, takroriy
  da'vo, bazasiz tayanch.
- Kontrakt fayl docstringida (uchala jim yo'nalish va raqamlash
  qoidasi sababi bilan).
- `PROGRESS.md`: «Joriy holat» jadvali (**45-run uni yangilamay
  qoldirgan edi** — tiklandi), run jurnaliga qator, «Ochiq savollar» ga
  1-ssenariy savoli, «Bloklangan» ga o'n yettinchi INFRA-1.

---

## Keyingi run uchun

⚠️ **O'n yettinchi marta** `ruff check` va `pytest -m "not requires_db"`
ishga tushmadi. **Sandbox tiklanganda birinchi ish — butun `pytest` va
`ruff check`, yangi kod emas:** 36–46 runlarning ~130 ta testi hech
qachon ishlamagan.

**Yopilgan nomzodlar, qayta ochilmasin:** oltin ssenariylar bog'lanishi
(46), fon vazifalari registri (45), konfiguratsiya parity (44),
bildirishnoma domeni (43), `05` §2 DDL ustunlari (43 tasdiqladi), i18n
katalog → kod (42), i18n kod → katalog (41), `05` §2 DDL indekslari
(40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).

**Ochiq nomzod (aniq topshiriq):** `05` §10 jadvali.
`tests/test_obs_metrics.py:14` yettita metrikani sanaydi, lekin ro'yxat
**qo'lda** yozilgan va tekshiruv `required <= set(...)` — ya'ni
hujjatga sakkizinchi metrika qo'shilsa hech narsa yiqilmaydi. Jadvalni
parse qilish arzon (bugungi `_numbered` va 45-sessiyaning `_SPEC_ROW`
naqshlari tayyor). **Ogohlantirishlar tomonini qayta ochmang:**
`test_obs_alerts.py` allaqachon to'rttalikni ham, uchala sonli chegarani
ham qulflaydi — u yerda qolgani prozani parse qilish bo'lardi, bu esa
mo'rt.

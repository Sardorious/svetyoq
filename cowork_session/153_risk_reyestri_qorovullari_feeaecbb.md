# 153-run — `01` §26+§27 risk reyestrining qorovullari (mutatsiya)

**Sessiya:** `local_feeaecbb` · 2026-08-13 · rejalashtirilgan
(`sveta-net-build`).

**Natija bir qatorda:** `app/release/risks.py` (956 qator) ga **43
mutatsiya → 29 KILLED, 14 SURVIVOR** (33 %); o'n to'rttalasi butun
bazasiz to'plamda birma-bir tasdiqlandi (yolg'on survivor yo'q), o'n
uchtasi qulflandi (**+13 test**, mavjud
`tests/test_risk_register_contract.py` ning yangi 8- va 9-bo'limlari),
bittasi **ekvivalent** deb isbotlandi. Mahsulot kodi, migratsiya,
konfiguratsiya **tegilmadi**. **3520 passed, 299 skipped**, `ruff` toza.

---

## 1. Nishon qanday tanlandi

152-run keyingi qadam sifatida «`app/release/` ning hali o'lchanmagan
reyestri (nishonni jurnaldan tasdiqlash shart)» ni qoldirgan edi.
151-run ning qoidasi bo'yicha ro'yxat `PROGRESS.md` ning run
jurnalidan qayta yig'ildi:

* `app/release/` da 24 modul bor;
* mutatsiya bilan **o'lchangani** — 108–116 runlarda o'nta:
  `business_architecture`, `business_glossary`, `business_environment`,
  `business_interfaces`, `business_rules`, `phase0_plan`,
  `business_requirements`, `ux_requirements`, `user_stories`,
  `nfr_appendix` (+ `gates` avvalroq);
* qolganlaridan eng kattasi — **`risks.py`, 956 qator**.

`EpicProgress.md` §4 ning navbat qatorida ham u «o'lchanmagan» ro'yxatida
turgan edi, ya'ni ikkala manba mos keldi.

⚠️ Yo'l-yo'lakay: `ls tests/ | grep risks` **bo'sh** qaytaradi — test
fayli `test_risk_register_contract.py` deb ataladi. Modulning testsizligi
haqidagi birinchi taxmin `grep -rl "release import risks" tests/` bilan
darhol rad etildi (150-run ning qoidasi: «nol import» ham `grep` bilan
tasdiqlanadi).

## 2. O'lchov qanday olindi

* Uch ishchi nusxa (`/tmp/w153_{1,2,3}`) **repo ildizidan** —
  `sveta/` + `*.md` + `deploy-server/` (147-run sabog'i: faqat `sveta/`
  ko'chirilsa collection error chiqadi).
* Har mutant **butun bazasiz to'plamda** (3507 test, ~50 s) o'lchandi —
  tor tanlov bosqichi umuman ishlatilmadi, ya'ni 144/146 ning «tor
  tanlov yolg'on survivor beradi» sinfi bu runda mumkin emas.
* Partiya: 3 ishchi × 2 mutant, `bash` ning 180 s limitiga sig'adi
  (~110 s). Hamma qatorda `restored=True`.
* Verdikt faqat `rc == 1` da `KILLED` (`/tmp/drive153.py`, 152 ning
  drayveri).

**Uch mutatsiya `rc=4` berdi** — `A5`, `A6`, `A9`. Sabab: ular import
paytidagi qorovulni **kuchaytirardi** (`SCHEDULED` o'rniga `DEGENERATE`
bog'lanishini taqiqlash), ya'ni modul import bo'lishdan yiqilardi.
Bu — memory dagi «qorovulni faqat zaiflashtir» qoidasining amaldagi
takrori. Uchalasi ham zaiflashtirish shaklida qayta yozildi
(`A5b`, `A6b`, `A9b`) va **uchalasi ham KILLED** chiqdi.

## 3. Bosh topilma — 152 ning naqshi endi SINF

Modul ikki yarimdan iborat va ular **teskari qoplangan**:

| Yarim | Qoplama |
|---|---|
| Hujjatdan parse qilinadigan **ma'lumot** — 18 qator, ID lar, so'zma-so'z matn, `Вероятность`/`Влияние` ustunlari, `COVER_RANK` ning ishlatiladigan juftliklari, `SPENT_ONSETS`, `Entry`/`RiskReport` ning oltita ro'yxati | **Zich**: 29 KILLED ning deyarli hammasi birinchi o'tishda o'ldi |
| `_check_registry()` ning **sakkizta qorovuli** | **Yarmi**: to'rttasi hech qachon otilmagan |

Mavjud to'rtta qorovul testi (`SCHEDULED`/`NOMINAL` band bog'lanishi,
`MECHANISED` band bog'lanishsizligi, izohsiz baho) sakkiztadan
to'rttasini otadi. Qolgan to'rttasi — **takrorlangan kod**, **bo'sh
mitigatsiya**, `Влияние` ustunining **ikkala yo'nalishi** va **izohsiz
sarflangan bashorat** — bugungi reyestr to'g'ri bo'lgani uchun umuman
otilmaydi, ya'ni har birini zaiflashtirish 3507 testni yashil
qoldirardi.

Bu 152 (`obs/monitoring.py`, 14 o'lchanmagan qorovul) va 149
(«ertangi kirish») bilan bir sinf. Uchinchi takror — endi navbat
tanlashning qoidasi: **modulda `_check_` ni `grep` qiling va
qorovulning nechta sharti test bilan otilishini sanang.**

## 4. Eng qimmat uchtasi

1. **Takrorlangan kod qorovulini `ENTRIES` dan `RISKS` ga toraytirish**
   (`A10`). `RS-02` ↔ `AS-S3` — bitta hodisa ikkala jadvalda yozilgan,
   ya'ni ID ni nusxalash bu yerda **tabiiy** xato. `ENTRY_BY_CODE` esa
   lug'at: takror kod ikkinchi qatorni jimgina yutadi va reyestr
   baribir o'n sakkiz qator deb ko'rsatib turaveradi.
2. **`INSTRUMENTED` bandning bog'lanish talabi** (`A7`). Qoida
   `SCHEDULED`/`NOMINAL` dan **boshqa hammasi** haqida, mavjud test esa
   faqat `MECHANISED` sinfini otadi. `AS-S6` — bugungi yagona
   `INSTRUMENTED` qator, va uning «asbob bor» degan yagona da'vosi
   dalilsiz qolardi.
3. **`RiskReport.covered` ni birorta test o'qimasdi** (`F1`). Shartni
   teskarisiga aylantirish (`if not e.is_covered`) hisobotga
   ushlanmagan o'n to'rt qatorni «ushlangan» deb yozdirardi va 3507
   test yashil qolardi.

## 5. Uch survivor ma'lumot chegarasida

* **`CLAUSE_SEPARATORS` ga belgi qo'shish** (`B6`). Mavjud test har
  belgining hujjatda **uchrashini** so'raydi — ya'ni bo'shliq yoki
  kirill harfi qo'shilsa u yashil qoladi. Ro'yxat esa `strip()` da
  ishlatiladi: ortiqcha belgi «qoplanmagan matn qoldi» tekshiruvini
  bo'shatadi va tashlab ketilgan band jimgina yo'qoladi (71-run sinfi).
  Qulf: ajratgichlar to'plami endi kataklardan **hisoblanadi**.
* **`COVER_RANK` da `INSTRUMENTED` ↔ `DISPLACED`** (`C1`). Juftlik
  bugungi reyestrda yonma-yon turmaydi, ya'ni tartib hech bir qatorning
  bahosini o'zgartirmaydi. Bu — `DISPLACED` ↔ `DEGENERATE` bilan bir xil
  **chegara qarori**; xuddi o'shanday oshkora test bilan yozildi
  (qaror izohda emas, tekshiruvda).
* **`ENTRIES` da ikkala jadvalning o'rni** (`E1`). `RISKS + ASSUMPTIONS`
  ni teskarisiga almashtirish birorta testni yiqitmasdi — qolgan hamma
  tekshiruv `RISKS` va `ASSUMPTIONS` ga **alohida** qaraydi.

## 6. Ekvivalent mutant

`unauditable_entries` dagi `len(e.unauditable_clauses) == len(e.clauses)`
→ `>=`. `unauditable_clauses` — `clauses` ning filtrlangan **qism
to'plami**, ya'ni uzunligi hech qachon kattaroq bo'la olmaydi va `>=`
aynan `==` bilan bir xil javob beradi. Qulf o'rniga xossaning o'zi
tasdiqlandi (`test_unauditable_entries_rests_on_a_subset_relation`).

## 7. Qo'shilgan testlar

`tests/test_risk_register_contract.py` ga ikkita yangi bo'lim, 13 test
(yangi fayl yaratilmadi):

**8-bo'lim — reyestrning o'z qorovullari** (`_install` yordamchisi
`_swap` ning umumiy shakli): `test_a_duplicated_code_is_rejected`,
`test_the_duplicate_check_spans_both_tables`,
`test_a_row_without_a_mitigation_clause_is_rejected`,
`test_a_risk_without_an_impact_is_rejected`,
`test_an_assumption_with_an_impact_is_rejected`,
`test_an_instrumented_clause_must_carry_a_binding`,
`test_a_spent_forecast_without_a_note_is_rejected`.

**9-bo'lim — chegara qarorlari va shakl**:
`test_the_separator_set_is_exactly_what_the_document_uses`,
`test_an_instrumented_mechanism_is_weaker_than_a_displaced_one`,
`test_entries_are_the_two_tables_in_document_order`,
`test_covered_is_exactly_the_mechanised_rows`,
`test_the_undeclared_risk_names_both_of_its_fixes`,
`test_unauditable_entries_rests_on_a_subset_relation`.

⚠️ Xabarni ham tekshirish muhim bo'lib chiqdi: bo'sh `clauses` da
qorovulsiz `Entry.cover` ning `max()` i «max() arg is an empty
sequence» bilan yiqiladi, ya'ni `pytest.raises(ValueError)` ning o'zi
mutantni **o'ldirmasdi** — `match=` shart.

## 8. Tasdiqlash

O'n to'rt survivor yangi testlar bilan qayta o'lchandi: **13 KILLED**,
`F7` (ekvivalent) SURVIVED. Butun to'plam **3520 passed, 299 skipped**,
`ruff check .` toza, `app/release/risks.py` repo nusxasi bilan
**bayt-bayt bir xil**.

`requires_db` bu runda yurgizilmadi — o'zgarish bazaga tegmaydi.

## 9. Keyingi qadam

1. `app/release/` ning qolgan o'lchanmagan reyestrlari: `roadmap.py`
   (780), `scope.py` (869), `functional_requirements.py` (860),
   `success.py` (726), `plan.py` (597), `dependencies.py` (541),
   `measures.py` (457), `acceptance.py` (580),
   `business_acceptance.py` (595), `business_reporting.py` (705),
   `collector.py` (141). Nishonni har safar jurnaldan tasdiqlash shart.
2. 152+153 ning naqshi: `_check_*` qorovuli bor **har** modulda
   «qorovulning nechta sharti test bilan otiladi» ni sanash.
3. 👤 `service._create_intents` ning qaytargan qiymatini hech kim
   o'qimaydi.
4. 👤 `cowork_session/` dagi nusxa juftliklari.

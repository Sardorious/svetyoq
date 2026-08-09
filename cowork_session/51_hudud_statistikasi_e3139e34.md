# 51-sessiya — `06` §3.1–3.2 hudud statistikasi kontrakti

**Sana:** 2026-08-09
**Sessiya:** `local_e3139e34`
**Epic:** E5 (ko'ndalang — kontrakt testlari)
**Sandbox:** ⛔ **yigirma ikkinchi ketma-ket run yiqildi** (INFRA-1)

---

## 0. Sandbox

Uchta urinish, uchalasi ham bir xil:

```
useradd failed: exit status 1: useradd: /etc/passwd.71802: No space left on device
```

Ya'ni `ruff check` ham, `pytest` ham **yana** ishga tushmadi. Butun run
faqat fayl asboblari (`Read`/`Grep`/`Glob`/`Edit`/`Write`) bilan bajarildi.
Sabab — C diskdagi sessiya papkalari; `cleanup-sessions.ps1` ni faqat odam
ishga tushira oladi. 36–51 runlarning ~270 ta testi hech qachon
ishlamagan.

---

## 1. 50-run qoldirgan nomzod TEKSHIRILDI va TASDIQLANDI

50-run keyingi nomzod sifatida `06` §3.1–3.2 ni taklif qilgan va
ogohlantirgan edi: «**avval `tests/test_scale.py` va `tests/test_confirmation.py`
ni to'liq o'qing** va bo'shliq borligini tasdiqlang — 49 va 50 aynan shu
tekshiruv tufayli bekorga ish qilmadi».

O'qildi.

**`test_confirmation.py`** — §3 ga umuman tegmaydi (`data_quality` so'zi
faylda bir marta ham yo'q; yagona `unknown` — `test_unknown_source_falls_back_to_bot`,
u `06` §2 manbalari haqida). Ya'ni bu fayl tomondan bo'shliq to'liq.

**`test_scale.py`** — §3.2 ning **xulq-atvorini** yaxshi qoplaydi:
`test_estimated_quality_demotes_one_step`, `test_estimated_mahalla_demotes_to_local`,
`test_scenario_11_unknown_quality_never_exceeds_local`,
`test_missing_territory_stats_caps_to_local`. Ya'ni 49-run rad etgan
holatga (`test_jobs_registry.py` hujjatni **parse qilar ekan**) o'xshab
ketishi mumkin edi.

**Farq shunda:** `test_scale.py` da kutilgan natijalar **qo'lda** yozilgan
va hujjatga bitta ham havola yo'q. §3.2 jadvalidagi qator o'zgarsa yoki
to'rtinchi qator qo'shilsa, test eskisi bilan yashil qolaverardi. Bu
49-ning holati emas, 50-ning holati — bo'shliq haqiqiy.

**Va tekshiruv kutilganidan ko'proq narsa topdi** (pastda §2).

## 1.1. Nima uchun bu jadval qimmat

`06` §3.2 uch qatordan iborat:

| `data_quality` | Xatti-harakat |
|---|---|
| `measured` | To'liq adaptiv formula |
| `estimated` | Adaptiv formula, lekin masshtab da'vosi bir pog'ona pasaytiriladi |
| `unknown` | Faqat qamrovga asoslangan chegara (§4.2), masshtab da'vo qilinmaydi |

Bu jadval mahsulotning eng ko'rinadigan va'dasini boshqaradi:
«tuman miqyosida uzilish» bildirishnomasi aynan shu narvondan chiqadi.
Va u **to'rt joyda qo'lda** takrorlangan edi:

| Modul | Nima qiladi |
|---|---|
| `app/clustering/scale.py` | masshtab narvoni va §5.4 to'sig'i |
| `app/stats/coverage.py` | Coverage Index pog'onasi |
| `app/stats/service.py:244` | bir nechta tumanning sifatini yig'ish |
| `app/stats/mahalla_coverage.py:144` | o'sha, mahalla darajasida |

Hujjatni **hech biri** o'qimasdi.

---

## 2. Topilgan haqiqiy defekt — ikkita modul, qarama-qarshi talqin

`territory_stats.data_quality` — **`CHECK` siz `text`** ustun
(`0003_confirmation.py:73`). Ya'ni ro'yxatdan tashqari qiymat
(`'partial'`, registr farqi `'MEASURED'`, bo'sh satr) fizik jihatdan
mumkin: qo'lda `UPDATE`, kelajakdagi migratsiya, import skripti.

Ikkala modul bu holatni **qarama-qarshi** hal qilardi:

```python
# app/clustering/scale.py — INKOR bilan
self.data_quality != QUALITY_UNKNOWN            # is_usable
district.data_quality == QUALITY_UNKNOWN        # coverage_cap

# app/stats/coverage.py:187 — RO'YXAT bilan
facts.data_quality not in (QUALITY_MEASURED, QUALITY_ESTIMATED)
```

**Oqibati.** `scale.py` da noma'lum qiymat uchta qatorning **eng ruxsat
beruvchisi** ni olardi — ya'ni `measured` ni:

- `is_usable` rost → chegara to'liq adaptiv formuladan hisoblanadi;
- `== QUALITY_ESTIMATED` yolg'on → bir pog'ona pasaytirish **qo'llanilmaydi**;
- `coverage_cap` da `== QUALITY_UNKNOWN` yolg'on → §5.4 to'sig'i ham
  **ishlamaydi**.

`coverage.py` esa xuddi shu qiymatni `low` ga tushirardi.

**Xavflisi masshtab tomonida edi** — aynan u bildirishnomani boshlaydi.
Va bu modulning **o'z yozilgan qoidasiga** zid: `coverage_cap` ning
docstringi «Kraudsorsing tizimining eng jiddiy xatosi — kam ma'lumotdan
katta xulosa chiqarish, shuning uchun noaniqlik har doim pastga qarab hal
qilinadi» deydi.

### Tuzatish

Yangi predikat `app/clustering/scale.py` da:

```python
USABLE_QUALITIES: tuple[str, ...] = (QUALITY_MEASURED, QUALITY_ESTIMATED)

def is_usable_quality(value: str) -> bool: ...
```

`is_usable` va `coverage_cap` shuni chaqiradi; `stats/coverage.py` ning
qo'lda yozilgan nusxasi ham shunga bog'landi (endi bitta predikat — bitta
talqin).

**Hujjatdagi uchala qiymat uchun xatti-harakat o'zgarmadi** —
enumeratsiya bilan tekshirildi:

| qiymat | `!= unknown` (eski) | `in (m, e)` (yangi) |
|---|---|---|
| `measured` | rost | rost |
| `estimated` | rost | rost |
| `unknown` | yolg'on | yolg'on |

Bu 50-running mezoni: «yasalgan natija **aynan bir xil**, xatti-harakat
o'zgarmadi». Faqat spetsifikatsiyada **yo'q** qiymat endi `unknown` ga
tenglashadi.

---

## 3. Yozilgan test — `tests/test_territory_stats_contract.py`

13 ta bazasiz test, parametrlangani bilan ~21 ta ishga tushish.

**§3.1 (manbalar jadvali, 5 qator):**

- jadval **yopiq** — beshta maydon, tartibi bilan;
- `households = population / avg_household_size` formulasi hujjatdan
  o'qiladi va `estimate_households` aynan shuni (yaxlitlash yo'nalishi
  bilan) hisoblashi tekshiriladi;
- «`avg_household_size` — konfiguratsiya parametri» va'dasi
  `params.DEFAULTS` ga bog'lanadi (qattiq kodlangan bo'lsa E11 dagi
  sozlash hech narsani qimirlatmasdi);
- `population = NULL → data_quality = 'unknown'` qoidasi: `households`
  noma'lum qator sifat bayrog'i `measured` bo'lsa ham formulaga
  **kiritilmaydi**;
- `populated_cells` ning zaxira yo'li (`barcha katakchalar`) →
  `refresh_coverage` hech qachon `measured` yoza olmasligi.

**§3.2 (sifat narvoni, 3 qator):**

- qatorlar `DATA_QUALITIES` bilan **tartibi bilan** teng;
- «adaptiv formula» deydigan qatorlar = `USABLE_QUALITIES`;
- qaysi qator pasaytiradi va qaysi biri da'vodan voz kechadi —
  hujjat matnidan (`pasaytiriladi` / `da'vo qilinmaydi`);
- har bir qator uchun `decide()` ning natijasi (parametrlangan,
  kalitlar hujjatdan tekshiriladi);
- ro'yxatdan tashqari to'rtta qiymat → `local`;
- `TerritoryFacts` ning standart sifati `unknown`;
- `stats/coverage.py` xuddi shu predikatni ishlatishi.

### Qarorlar

- **`SPEC_SOURCE_ROWS = 5`, `SPEC_QUALITY_ROWS = 3` aynan** (47/49/50 ning
  naqshi): jadval o'ssa bu **ko'rinadigan** qaror bo'ladi.
- **Parser ajratgichdan (`|---|`) keyin boshlanadi.** §3.2 ning sarlavhasi
  `` | `data_quality` | Xatti-harakat | `` — u ham backtick bilan yozilgan,
  ya'ni oddiy qator naqshiga tushib jadval **to'rt qatorli** bo'lib
  ko'rinardi. Birinchi yozilishida aynan shu xato bor edi va qo'lda
  tekshirishda ushlandi.
- **DDL ustunlariga tegilmadi** — `territory_stats` ustunlari
  `tests/test_schema.py` ning `SPEC_TABLES_06` ida allaqachon qulflangan
  (43-run: «`05` §2 DDL ustunlari — qayta ochilmasin»).
- **`min(qualities)` o'zgartirilmadi.** `stats/service.py:244` va
  `mahalla_coverage.py:144` alifbo tartibiga tayanadi va bugun tasodifan
  to'g'ri ishlaydi (`"estimated" < "measured"`). Sandbox yigirma ikki
  rundan beri yiqilgan — ko'r holda ikkinchi xatti-harakat o'zgarishini
  kiritish bu faylning o'zi ogohlantirayotgan xatoning aynan o'zi bo'lardi.
  «Ochiq savollar» ga 👤 bilan yozildi.
- **`CHECK` cheklovi qo'shilmadi** — yangi revizyon talab qiladi va bu
  uslub savoli (`outbox.topic`, `notifications.status` ham cheklovsiz,
  43-run). «Ochiq savollar» da 👤.

---

## 4. Qo'lda tekshiruv (sandbox yo'q)

- **Satr uzunligi 100** — eng uzun qator qayta o'raldi.
- **isort (`I`)** — `__future__` → `re`/`pathlib` → `pytest` → `app.*`;
  `app.clustering` < `app.clustering.scale` < `app.jobs` < `app.stats`;
  import ro'yxati ichida `order-by-type` (KONSTANTA → Sinf → funksiya).
- **`coverage.py` da `QUALITY_MEASURED` olib tashlandi** — grep bilan
  tekshirildi, u faqat o'sha bitta qatorda ishlatilgan edi (F401 yo'q).
  Trailing comma qo'yilgan, ya'ni ko'p qatorli import isort uchun to'g'ri.
- **`scale.py` da `QUALITY_UNKNOWN` hamon ishlatiladi** (`TerritoryFacts`
  ning standart qiymati) — o'lik nom qolmadi.
- **`decide()` ning to'rtala holati qo'lda hisoblandi** (`w=35`, 4 katakcha,
  3 mahalla; mahalla `H=460`, tuman `H=8200`): `measured` → `district`,
  `estimated` → `mahalla`, `unknown` → `local`, ro'yxatdan tashqari →
  `local`. Kirish `test_scale.py:test_district_scale_by_affected_mahallas`
  bilan bir xil, ya'ni tayanch allaqachon yashil bo'lgan.
- **Mavjud `test_scale.py` ning har bir testi** yangi predikat ostida
  qayta o'qildi — hammasi faqat hujjatdagi uchta qiymatni ishlatadi,
  ya'ni natijalari o'zgarmaydi.

---

## 5. Keyingi run uchun

⚠️ **Yigirma ikkinchi marta** `ruff check` va `pytest -m "not requires_db"`
ishga tushmadi. **Sandbox tiklanganda birinchi ish — butun `pytest` va
`ruff check`, yangi kod emas.**

**Yopilgan nomzodlar, qayta ochilmasin:** `06` §3.1–3.2 hudud statistikasi
(51), `06` §2 manba registri (50), `06` §9 konfiguratsiya jadvali (49),
`05` §8 fon vazifalari jadvali (**45 da yopilgan, 49 da tasdiqlangan**),
`05` §7.2 endpoint sathi (48), `05` §10 metrikalar jadvali (47), oltin
ssenariylar (46), fon vazifalari registri (45), konfiguratsiya parity (44),
bildirishnoma domeni (43), `05` §2 DDL **ustunlari** (43), i18n ikki
yo'nalish (41, 42), `05` §2 DDL indekslari (40), API `commit` (39),
`Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34). **Javob maydonlarini ham
qayta ochmang** — `test_openapi_contract.py` ularni qulflaydi.

**Ochiq nomzod (taklif):** `06` §5.3 ning **fazoviy shartlari** —
`MIN_CELLS_FOR_MAHALLA = 3` va `MIN_MAHALLAS_FOR_DISTRICT = 2`
(`scale.py:34,37`) izohda «`06` §5.3» deydi, lekin sonlar hujjatdan
o'qilmaydi; §5.2 chegara jadvali ham `test_scale.py` da **qo'lda**
(`(130, 5), (460, 8), …`). **Avval `tests/test_scale.py` va
`tests/test_confirmation.py` ni to'liq o'qing** va §5.2/§5.3 ni hujjat
bilan solishtiruvchi bironta yo'l yo'qligini tasdiqlang — 49, 50 va 51
aynan shu tekshiruv tufayli bekorga ish qilmadi.

**Saboqlar:**

- (48-dan) `Glob` ga **to'liq yo'l** bering — bo'sh natija «fayl yo'q»
  degani emas.
- (50-dan) `PROGRESS.md` va `INDEX.md` ning uzun qatorlarini `Grep -o`
  bilan **kichik oyna** so'rab o'qing; `Edit` qatorning **qisqa boshini**
  almashtira oladi.
- **(51, yangi)** Markdown jadvalini parse qilganda **sarlavha qatorini
  hisobga oling**: `06` §3.2 da sarlavhaning birinchi katagi ham backtick
  bilan yozilgan (`` `data_quality` ``) va oddiy qator naqshiga tushadi.
  Ajratgich (`|---|`) dan keyin boshlash — ishonchli qoida.

**👤 Odamga:** `cleanup-sessions.ps1` (sandboxning sababi),
`data_quality` ga `CHECK` (51), `min(qualities)` alifbo tartibi (51),
`06` §3.1 dagi `[TEKSHIRISH]` markeri (51),
`06` §9 jadvaliga `notify.*` / `velocity.*` qo'shilsinmi (49),
`API_PREFIX` sozlama bo'lib qolsinmi (44),
`05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
`models.py:113` dagi `source` standarti registrga bog'lansinmi (50),
`ruff check sveta` ni bir marta o'zingiz yurgizing (45),
digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43),
uchta i18n kaliti (42), `git rm sveta/tests/test_dbg_tmp.py`,
`git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
Nomni tuzatish o'chirishni talab qiladi. 👤

---

## 6. O'zgargan fayllar

| Fayl | O'zgarish |
|---|---|
| `sveta/app/clustering/scale.py` | `USABLE_QUALITIES` + `is_usable_quality`; `is_usable` va `coverage_cap` shunga bog'landi |
| `sveta/app/stats/coverage.py` | qo'lda yozilgan §3.2 nusxasi `is_usable_quality` ga almashtirildi |
| `sveta/tests/test_territory_stats_contract.py` | **yangi** — 13 ta bazasiz test |
| `sveta/PROGRESS.md` | joriy holat, run jurnali, uchta yangi ochiq savol |
| `cowork_session/51_hudud_statistikasi_e3139e34.md` | **yangi** — shu fayl |
| `cowork_session/INDEX.md` | jadval + «Qayerda to'xtadik» |

Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**.
Hujjatdagi uchta qiymat uchun **xatti-harakat o'zgarishi ham yo'q**.

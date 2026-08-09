# 49-sessiya — `06` §9 konfiguratsiya jadvali kontrakti

**Sana:** 2026-08-09
**Sessiya:** `local_72c4697c-ee53-47c2-863a-0871a3cd4093`
**Epic:** E5 (tasdiqlash/masshtab parametrlari), kontrakt qatlami
**Natija:** ✅ yangi `tests/test_confirm_params_contract.py`
**Infra:** ⚠️ sandbox **yigirmanchi ketma-ket run** yiqildi (INFRA-1)

---

## 1. Sandbox — yigirmanchi marta

Birinchi ikkita `bash` chaqiruvi bir xil xato bilan qaytdi:

```
ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.71726: No space left on device
```

Uchinchi urinish (`echo ok && df -h /`) ham aynan shunday. Asbobning o'zi
«agar bir xil takrorlansa, urinishni to'xtating» deydi — to'xtatildi.
`ruff check` va `pytest -m "not requires_db"` **yana ishga tushmadi.**

Sabab `CLAUDE.md` §3 da yozilgan: C diskdagi sessiya papkalari to'lib
ketgan, `cleanup-sessions.ps1` ni **odam** ishga tushirishi kerak.

Butun sessiya `Read` / `Grep` / `Glob` / `Write` bilan, ya'ni haqiqiy
fayl tizimida ishlandi.

---

## 2. 48-run qoldirgan nomzod tekshirildi — va **rad etildi**

48-sessiya keyingi nomzod sifatida `05` §8 (fon vazifalari jadvali) ni
taklif qilgan edi: «`FREQUENCY_S` qo'lda yozilgan». Shu bilan birga
o'sha yozuvda ogohlantirish ham bor edi: «**avval
`tests/test_jobs_registry.py` ni to'liq o'qing** va bo'shliq borligini
tasdiqlang (43 va 45-ning saboqi)».

Fayl to'liq o'qildi (247 qator). **Bo'shliq yo'q — uchala yo'nalish ham
allaqachon yopiq:**

| Yo'nalish | Qayerda qulflangan |
|---|---|
| hujjat → `IMPLEMENTED` | `test_the_implemented_table_matches_the_design_doc` (`_spec_jobs()` §8 ni **parse qiladi**) |
| `IMPLEMENTED` → registr | `test_registered_jobs_match_the_spec` |
| `app/jobs/` fayllari → registr | `test_every_job_module_is_registered` |

`FREQUENCY_S` haqiqatan qo'lda yozilgan, lekin u **lug'at emas,
tarjimon**: noma'lum chastota `assert frequency in FREQUENCY_S` da
**yiqiladi**, jimgina o'tkazib yuborilmaydi. Ya'ni u ochiq
kengaytiriladigan nuqta, jim nusxa emas.

**Xulosa:** 45-sessiya bu jadvalni o'zi bilgandan ko'proq yopgan ekan.
Nomzod yopiq ro'yxatga qo'shildi.

---

## 3. Yangi nomzod — `06` §9

### 3.1 Bo'shliq qanday topildi

`06` ning sarlavhalari ko'rib chiqildi, keyin `sveta/` bo'ylab `06 §9`
ga havolalar qidirildi. Havolalar ko'p (`params.py`, `region_admin.py`,
`0003_confirmation.py`, `models.py`, `queries.py`, `service.py`,
`README.md`), lekin **hech biri hujjatni o'qimaydi**.

`app/clustering/params.py:21` da so'zma-so'z shunday yozilgan:

```python
#: `06` §9 jadvali, aynan. Kalitlar baza qiymatlari bilan bir xil yoziladi.
DEFAULTS: dict[str, float] = { ... }
```

«**Aynan**» — bu va'da, va uni bugungacha hech narsa ushlab turmasdi.
`test_confirmation.py` faqat `from_mapping` ning **xulq-atvorini**
tekshiradi (ustunlik, yaroqsiz qiymat), qiymatlarning **kelib chiqishini**
emas. `test_notify_params.py:80` `DEFAULTS` ni import qiladi, lekin faqat
`notify.*` bilan kesishmasligini tekshiradi.

### 3.2 O'sha o'n beshta son kodda **uch marta** takrorlangan

1. `DEFAULTS` lug'ati (`params.py:22-38`);
2. dataklass maydon standartlari (`ConfirmParams.min_users: int = 3`,
   `coef: float = 0.5`, … `params.py:41-80`);
3. hujjatning o'zi.

Uchinchi nusxa alohida xavfli: `DEFAULT_PARAMS` `from_mapping()` orqali
**birinchi** nusxadan quriladi, `ConfirmParams()` esa **ikkinchisidan** —
va ikkalasi ham ishlatiladi (`tests/test_simulate.py:345` `ConfirmParams()`
ni to'g'ridan-to'g'ri yasaydi). Ular ajralsa bitta ishga tushirishda ikki
xil tasdiqlash chegarasi bo'lardi.

### 3.3 To'rtta jim yo'nalish

1. **Hujjatdagi qiymat o'zgarsa** kod eskisi bilan ishlayveradi. Eng
   qimmati: `confirm.coef` — tasdiqlash chegarasining o'zi (`06` §4),
   farq faqat ishlab chiqarishdagi verdiktlarda ko'rinardi.
2. **`DEFAULTS` ga hujjatda yo'q kalit qo'shilsa** — `06` §9 ro'yxati
   **yopiq**, `region_admin.py:370` shunga tayanib noma'lum kalitni
   `EXIT_USAGE` bilan bloklaydi. Bu tomon umuman o'lchanmagan edi.
3. **Dataklass standarti `DEFAULTS` dan ajralsa** (yuqoridagi 3.2).
4. **`DEFAULTS` da kalit bor, `from_mapping` uni o'qimaydi** — o'lik
   konfiguratsiya. `region_admin` uni bazaga seed qiladi, odam E11 da
   sozlaydi va **hech narsa o'zgarmaydi**; `KeyError` ham chiqmaydi,
   chunki `_num` faqat o'zi so'ragan kalitlarga murojaat qiladi.

---

## 4. Qarorlar

- **Parser ikki xil qisqartmani yoyadi.** §9 kalitlarni ikki uslubda
  qisqartiradi: `` `confirm.floor` / `ceil` `` (ikkita alohida backtick,
  nuqtadan keyin almashadi) va `` `scale.mahalla_floor/ceil` `` (bitta
  backtick ichida, pastki chiziqdan keyin almashadi). `_expand()`
  ajratgich sifatida `.` va `_` dan **qaysi biri oxirroq** bo'lsa o'shani
  oladi — ikkala uslub ham bitta qoida bilan yoyiladi. Shuning uchun
  12 qator → 15 kalit.
- **`SPEC_ROWS = 12` va `SPEC_KEYS = 15` — aynan, «kamida» emas**
  (47-sessiyaning naqshi). §9 — mahsulotning sozlanadigan sathi, u
  epiclar bilan o'smaydi. `notify.*` va `velocity.*` ataylab tashqarida
  (ikkalasi ham `PROGRESS.md` «Ochiq savollar» ida odam qaroriga
  qo'yilgan) — jadval o'ssa, bu ongli qaror bo'lsin.
- **Qo'lda yozilgan `DEFAULTS` o'chirilmadi.** U qiymatlarni qulflaydi va
  ishga tushishda hujjatni o'qish kerak emas (40 va 45-sessiyaning
  naqshi: qo'lda ro'yxat qoladi, lekin manba bilan solishtiriladi).
- **Maqom ustuni noma'lum so'zda yiqiladi**, jimgina o'tkazilmaydi —
  `FREQUENCY_S` naqshi. E11 dan keyin `EMPIRIK` paydo bo'lsa uni ochiq
  tan olish kerak bo'ladi.
- **`_declared()` ro'yxat emas, qoida.** To'rtinchi qo'lda yozilgan
  jadval qilmaslik uchun dataklass maydoni kalitdan **hisoblanadi**:
  `guruh.maydon` (`confirm`/`scale`/`guard`) → ichki dataklassdan,
  aks holda `key.replace(".", "_")` → `Params` ning o'zidan. Shu bitta
  qoida `avg_household_size` ni ham, `spread.min_distance_m` →
  `spread_min_distance_m` nomi o'zgarishini ham qamraydi.
- **O'lik kalit perturbatsiya bilan o'lchanadi:**
  `from_mapping({key: DEFAULTS[key] + 1}) != DEFAULT_PARAMS`. `+1`
  o'n beshala kalit uchun ham xavfsiz — `int()` kesib tashlaydigan
  qiymat yo'q (0.5→1.5, 0.35→1.35, 5.4→6.4, 3→4, 50→51).
- **Formulalarga tegilmadi.** `required_score`, masshtab narvoni va
  qamrov to'sig'ining xulq-atvori `test_confirmation.py` va
  `test_scale.py` da qulflangan; bu fayl faqat **sonlar qayerdan
  kelganini** o'lchaydi.

### Rad etilgan variantlar

- **`region_admin.seed_defaults()` ni tekshirish.** U bir qatorli
  (`{**DEFAULTS, **notify_seed_values()}`), ya'ni to'liqlik strukturaviy
  jihatdan kafolatlangan — tekshiradigan bo'shliq yo'q. Bundan tashqari
  `tools.region_admin` ni import qilish `app.db` ni tortadi va bazasiz
  testga keraksiz bog'liqlik qo'shardi (`test_region_audit.py` shuning
  uchun modulni import qilmasdan **matnini** o'qiydi).
- **`0003_confirmation.py` migratsiyasini solishtirish.** Migratsiya
  `region_config` **jadvalini** yaratadi, qiymatlarni seed qilmaydi —
  solishtiradigan nusxa yo'q.
- **`X-Admin-Token` uslubidagi takrorlanish.** 48-sessiyaning saboqi
  yodda tutildi: mavjud testlar avval qidirildi (`grep DEFAULTS
  tests/`), takrorlanadigan tekshiruv yozilmadi.

---

## 5. Yozildi

`sveta/tests/test_confirm_params_contract.py` — 10 ta test funksiyasi,
parametrlanganini hisobga olsak **38 ta ishga tushish** (8 ta oddiy +
2 × 15 ta parametrlangan). Hammasi bazasiz.

| Test | Nimani ushlaydi |
|---|---|
| `test_defaults_match_the_confirmation_doc` | hujjat ↔ `DEFAULTS`, kalit va qiymat |
| `test_no_key_is_missing_from_the_code` | hujjatda bor, kodda yo'q |
| `test_no_key_is_invented_by_the_code` | kodda bor, hujjatda yo'q (yopiq ro'yxat) |
| `test_the_scan_is_measuring_something` | 12/15, uch xil qatordan tayanch |
| `test_every_row_carries_a_status` | «Maqomi» ustuni bo'shab qolmaydi |
| `test_the_section_still_says_the_values_live_in_the_database` | §9 ning jumlasi — `DEFAULTS` ning bootstrap ekanini oqlaydi |
| `test_dataclass_defaults_match_defaults` (×15) | uchinchi nusxa ajralmaydi |
| `test_default_params_equals_a_bare_params` | ikki qurilish yo'li bitta obyekt beradi |
| `test_from_mapping_with_the_spec_values_changes_nothing` | seed qilingan mintaqa = seed qilinmagani |
| `test_every_key_is_actually_read` (×15) | o'lik konfiguratsiya |

### Qo'lda audit (sandbox yo'q)

- `_ROW` regexi sarlavha (`| Kalit | ... |`) va ajratgich (`|---|---|---|`)
  ni **backtick yo'qligi** bilan filtrlaydi — `_TICKED.findall` bo'sh
  qaytaradi va qator o'tkazib yuboriladi.
- §9 ichidagi `CREATE TABLE` bloki va bo'lim oxiridagi `---` `|` bilan
  boshlanmaydi — aralashmaydi.
- Bo'lim chegarasi `\n## ` bo'yicha; §9 da `###` kichik bo'lim yo'q,
  keyingisi `## 10. Sxema o'zgarishlari`.
- Uchala qisqartma qo'lda yoyib tekshirildi: `confirm.floor`+`ceil` →
  `confirm.ceil`; `scale.mahalla_floor`+`ceil` → `scale.mahalla_ceil`;
  `scale.district_floor`+`ceil` → `scale.district_ceil`. 12+3 = 15 =
  `len(DEFAULTS)`.
- `from_mapping` ning 15 ta kalit murojaati sanab chiqildi — hammasi bor,
  ya'ni bugun o'lik kalit yo'q.
- **Ruff:** `pyproject.toml` da `select = ["E","F","I","UP","B","ASYNC"]`,
  `line-length = 100`. Uzun qator yo'q (tekshirildi). `I` (isort)
  tufayli `from app.clustering.params import DEFAULT_PARAMS, DEFAULTS, …`
  yozilmadi — ikkita `DEFAULT…` konstantasining tartibi isort
  sozlamalariga bog'liq va sandboxsiz tasdiqlab bo'lmaydi. Uning o'rniga
  `from app.clustering import params as p` — `test_metrics_spec_contract.py`
  (`from app.obs import metrics as m`) va `test_notify_params.py` dagi
  mavjud uslub. `B905`: `zip(..., strict=True)`. `B904`: `raise … from exc`.

---

## 6. Keyingi run uchun

⚠️ **Yigirmanchi marta** `ruff check` va `pytest` ishga tushmadi.
**Sandbox tiklanganda birinchi ish — butun `pytest` va `ruff check`,
yangi kod emas:** 36–49 runlarning ~213 ta testi hech qachon ishlamagan.

**Yopilgan nomzodlar, qayta ochilmasin:** `06` §9 konfiguratsiya jadvali
(49), `05` §8 fon vazifalari jadvali (**45 da yopilgan, 49 da
tasdiqlangan**), `05` §7.2 endpoint sathi (48), `05` §10 metrikalar
jadvali (47), oltin ssenariylar bog'lanishi (46), fon vazifalari registri
(45), konfiguratsiya parity (44), bildirishnoma domeni (43), `05` §2 DDL
**ustunlari** (43), i18n katalog → kod (42), i18n kod → katalog (41),
`05` §2 DDL indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip
(38), `02` Faza 0 (34). **Javob maydonlari** — `test_openapi_contract.py`.

**Ochiq nomzod (taklif):** `06` §2 xabar manbalari va ishonch
og'irliklari jadvali (`report_sources` seedi ↔ hujjat). `06` §2.1 og'irlik
qiymatlari `reports.weight` ga qotiriladi (`06` §10), ya'ni noto'g'ri
og'irlik **qaytarib bo'lmaydigan** ma'lumot yozadi. **Avval
`tests/test_confirmation.py` va `tests/test_reports_intake.py` ni to'liq
o'qing** va bo'shliq borligini tasdiqlang — 49-run aynan shu tekshiruv
tufayli `05` §8 ni bekorga qayta yozmadi.

**Saboq (48-dan meros, hamon amal qiladi):** `Glob` ga **to'liq yo'l**
bering — `sveta/tests/*.py` «No files found» qaytaradi,
`H:\...\sveta\tests\*.py` esa 96 ta fayl beradi.

👤 **Odamga:** `cleanup-sessions.ps1` (sandboxning sababi),
`06` §9 jadvaliga `notify.*` / `velocity.*` qatorlari qo'shilsinmi
(endi `SPEC_ROWS = 12` bu qarorni ko'rinadigan qiladi),
`API_PREFIX` sozlama bo'lib qolsinmi (44),
`05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
`ruff check sveta` ni bir marta o'zingiz yurgizing (45),
digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43),
uchta i18n kaliti (42),
`git rm sveta/tests/test_dbg_tmp.py`,
`git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
Nomni tuzatish o'chirishni talab qiladi. 👤

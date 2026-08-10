# 61 — `06` §11 suiiste'mol ssenariylari kontrakti

**Sana:** 2026-08-09 · **Sessiya:** `363cf61f` · **Epic:** E5b (ko'ndalang)
**Natija:** ✅ `06` §11 hujjatdan o'qiladigan bo'ldi — kontrakt qatlami
(40–61 runlar) **tugadi**.

---

## 1. Nima uchun aynan §11

60-run `05` ning oxirgi bog'lanmagan bo'limini (§3, maxfiylik) yopdi va
`INDEX.md` ning «Qayerda to'xtadik» qatorida bitta nom qoldi: **`06` §11
ning 34-run qamramagan qismi**.

Muhim nuqta: §11 uchun test **bor** edi. 34-run
`tests/test_abuse_contract.py` ni yozgan — oltita qatorning har biri uchun
alohida **xatti-harakat** testi (`dedupe_evidence` bilan bitta odamning
yigirmata xabari, `spread_ok`, `user_factor`, `velocity.penalize` ning
qabul yo'liga ulanishi, `mahalla_active` shifti, qamrov to'sig'i). O'sha
qaror to'g'ri edi va bugun ham to'g'ri: 33-run topgan defektda ustun ham,
o'quvchi ham, formula ham joyida edi — ishlamaydigani **mexanizm** edi,
ya'ni simvolning mavjudligini tekshirish uni o'tkazib yuborardi.

Bo'shliq boshqa joyda edi. O'sha faylning tayanchi — `SPEC_TABLE` —
**qo'lda ko'chirilgan** va bu ataylab qilingan (fayl docstringi buni
oqlaydi: hujjatdan avtomatik o'qilsa test o'zini o'zi tasdiqlardi).
Natijada fayl **o'z nusxasini** o'lchaydi:

* §11 ga **yettinchi qator** qo'shilsa — `len(SPEC_TABLE) == 6` yashil;
* `50 m` **`80 m`** ga aylansa — testda `== 50` literal, yashil;
* `mahalla_active` og'irligi ko'tarilsa — testda `== 2.0` literal, yashil.

Ya'ni himoyalar ishlashini test kafolatlaydi, **hujjatda yozilgani
o'shami** degan savolga esa hech kim javob bermaydi. 49–60 runlar aynan
shu savolni `06` va `05` ning qolgan hamma bo'limi uchun yopgan.

## 2. Qaror: ikkinchi fayl, birinchisiga tegmasdan

`tests/test_abuse_scenarios_contract.py` — 22 test. Naqsh 46/58 juftligi
bilan bir xil (46 — «ssenariyning testi bormi», 58 — «ssenariy hujjat
yozganidek bajariladimi»): ikki fayl bir-birini almashtirmaydi.

Uch qatlam:

**(1) Jadvalning tuzilishi.**

| Test | Nimani ushlaydi |
|---|---|
| `test_the_section_parses_into_six_rows` | hujjat qayta tuzilsa parser jim qolmasin |
| `test_the_hand_copied_table_has_the_same_length` | **bog'lovchi** — §11 ga qator qo'shilsa 34-running fayli ham «to'liq emas» deb belgilanadi |
| `test_every_row_names_at_least_one_code_token` | faqat nasrdan iborat qator = egasi yo'q «himoya bor» yozuvi (33-run topgan shakl) |
| `test_every_backticked_token_resolves_to_code` | `RESOLVERS` — token → koddagi haqiqiy simvol |
| `test_the_parser_is_not_vacuous` | regex mos kelishdan to'xtasa parametrizatsiya nol testga aylanmasin (28-running `include_router` qirrasi) |

`RESOLVERS` dagi dalillar **ikki tomonlama** olindi, chunki bitta tomon
kam: `distinct_users` → `ConfirmationResult` maydoni **va** `outages`
ustuni; `cells_with_reports` → `raw_scale` parametri **va** ustun;
`user_factor` → monotonlik (`f(0) < f(100)`), shunchaki mavjudlik emas.

**(2) Sonlar hujjatdan parse qilinadi.** Shu paytgacha to'rttasi ham
test kodida literal edi:

| §11 dagi matn | Kod |
|---|---|
| `spread.min_distance_m` = **50 m** | `DEFAULT_PARAMS.spread_min_distance_m` |
| akkaunt yoshi **≥10 daq** | `settings.reporter_min_account_age_min` (`>=`, chunki hujjat **quyi** chegara yozadi) |
| **10 daqiqada 5 km** | `settings.velocity_window_min`, `velocity_max_distance_m` (km→m) |
| og'irligi **2.0** dan oshmaydi | `sources.SOURCE_BY_CODE["mahalla_active"].weight` |

**(3) Bo'limlararo ziddiyat — 57-running sabog'i.** O'shanda `06` §8 ning
«60 s» i `05` §8 jadvali bilan hech qachon solishtirilmagani ko'rindi.
§11 ning uchta soni ham boshqa joyda takrorlanadi va **ikkala tomondagi
test ham yashil qolardi**, chunki har biri faqat o'z bo'limini o'qiydi:

| Son | §11 | Ikkinchi manba |
|---|---|---|
| `50` m | `spread.min_distance_m` = 50 m | `06` §9 konfiguratsiya jadvali **va** `05` §4.3 («masofa >= 50 m») |
| `10` daq | akkaunt yoshi ≥10 daq | `05` §4.3 (`user.created_at < now() - 10 daqiqa`) |
| `2.0` | `mahalla_active` og'irligi | `06` §2 ning `INSERT` bloki |

Endi uchalasi bir-biriga **va** kodga bog'landi.

## 3. Ataylab tekshirilmagani

Himoyalarning xatti-harakati (`dedupe_evidence`, `spread_ok`,
`velocity.penalize` ning `intake` da chaqirilishi va `create_report` dan
**oldin** turishi, qamrov to'sig'i) — `test_abuse_contract.py` da qoladi.
Takrorlash tuzatish joyini noaniq qilardi (41-running sabog'i).

## 4. Mutatsiyalar — 17 ta, hammasi ushlandi

`CLAUDE.md` va 60-running qoidasi bo'yicha **5 tadan** bo'lib yurgizildi,
har to'plamdan keyin `git status --porcelain`. Harness asl matnni xotirada
saqlaydi va `finally` da qaytaradi (`git checkout --` ishlatilmaydi —
repo `HEAD` i eskirgan).

*Hujjat tomonidan:* `50 m`→`80 m`, `2.0`→`3.0`, `≥10 daq`→`≥20 daq`,
`5 km`→`7 km`, yettinchi qator, notanish token (`foo_guard`), qatorning
nasrga aylanishi, `06` §9 dagi `50`→`80`, `06` §2 dagi `2.0`→`2.5`,
`05` §4.3 dagi `10 daqiqa`→`15` va `50 m`→`70 m`.

*Kod tomonidan:* `reporter_min_account_age_min` `10`→`5`,
`velocity_window_min` `10`→`15`, `velocity_max_distance_m` `5000`→`3000`,
`mahalla_active` og'irligi `2.0`→`2.5`, `SPEC_TABLE` dan bitta qator
o'chirilishi.

**Bitta mutatsiya ataylab o'tkazildi va bu to'g'ri.** `params.py` dagi
dataklass maydoni `spread_min_distance_m: int = 50` → `80` bu faylni
yiqitmaydi, chunki `DEFAULT_PARAMS` `from_mapping()` orqali `DEFAULTS`
lug'atidan quriladi — dataklass standarti o'sha yo'lda umuman
ishlatilmaydi. Uni 49-run allaqachon qulflagan; tekshirildi:
mutatsiyada `test_confirm_params_contract.py` → **2 failed**. Ya'ni bu
survivor emas, **chegara**: har fayl o'z savoliga javob beradi.

## 5. Sandbox

Yana tekin keldi: 59-running `/tmp/sv59` muhiti (104 paket, `ruff` ham)
**butun holda qolgan** edi, hech narsa o'rnatilmadi. `$HOME`
(`/sessions/…`) esa yana 100% (38 MB bo'sh) — 57 va 60 ning sabog'i uchinchi
marta tasdiqlandi: **avval `/tmp` ni qidir**, keyin o'rnatishga urin.
👤 `cleanup-sessions.ps1` ni har run oldidan yurgizish kerak.

Natija: `pytest -m "not requires_db"` → **1437 passed, 1 skipped**
(212 `requires_db` deselected); `ruff check app tools tests alembic` —
toza; `ruff format --check` yangi fayl uchun toza.

## 6. Keyingi qadam

Kontrakt qatlami **tugadi** — `05` da ham, `06` da ham bog'lanmagan bo'lim
qolmadi. Keyingi run yangi funksiyaga qaytadi; bloklanmagan nomzodlar:
E6 (`tools/recluster.py` ning `requires_db` siz qismi) yoki E14 vitrinasi
backendi. 👤 tomonidagi bloklar o'zgarmadi (Telegram tokeni, mahalla
poligonlari, ADR-08, `DIGEST_CHAT_IDS`, CI ni qayta yurgizish va prodda
SQL jurnali fiksi — batafsil `PROGRESS.md`).

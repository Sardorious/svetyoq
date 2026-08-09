# 52-sessiya — `06` §5 masshtab narvoni kontrakti

**Sana:** 2026-08-09
**Sessiya:** `local_52a83926-…`
**Epic:** E5 (ko'ndalang — spetsifikatsiya ↔ kod kontrakti)
**Natija:** ✅ `tests/test_scale_ladder_contract.py` (20 ta bazasiz test
funksiyasi, 33 ta ishga tushish)
**Sandbox:** ⛔ **yigirma uchinchi ketma-ket run yiqildi** (INFRA-1)

---

## 1. Nima qilindi

`06` §5.1–5.4 (masshtab narvoni) endi hujjatdan o'qiladi. Yangi fayl:
`sveta/tests/test_scale_ladder_contract.py`. **Kod o'zgartirilmadi** — bu run
faqat o'lchash.

## 2. 51-run qoldirgan nomzod tekshirildi va TASDIQLANDI

51-run «`06` §5.2–5.3 chegara jadvali va fazoviy shartlar» ni nomzod qilib
qoldirdi va «avval `test_scale.py` va `test_confirmation.py` ni to'liq
o'qing» dedi. O'qildi:

- `tests/test_scale.py:63–77` — «`06` §5.2 chegara jadvali» sarlavhasi ostida
  ikkita `parametrize`: `[(130, 5), (460, 8), (1100, 12), (8200, 15), (16400, 15)]`
  va `[(130, 10), (460, 10), (1100, 12), (8200, 30), (16400, 30)]`. Sonlar
  hujjatdan **qo'lda ko'chirilgan**, bitta ham havola yo'q.
- `tests/test_confirmation.py` — §2.1, §4.2, §6, §7, §12 ni qoplaydi, §5 ga
  **umuman tegmaydi**. (§4.2 chegara jadvali u yerda ham qo'lda — bu keyingi
  nomzod, pastga qarang.)
- Butun `sveta/` bo'yicha `§5.2` / `§5.3` qidiruvi: 20+ havola, **hammasi
  izoh yoki docstring matni**. Birorta test hujjatni ochmaydi.

Bo'shliq haqiqiy. Nomzod kengaytirildi: §5.2–5.3 emas, **butun §5** (5.1 va
5.4 ham hech qayerdan o'qilmasdi).

## 3. Nima uchun §9 ni yopish yetarli emas edi

49-sessiya `06` §9 **konfiguratsiya jadvalini** yopdi va bu ko'p narsani
qamrab olgandek ko'rinadi: `scale.coef = 0.35`, `mahalla_floor = 5`,
`mahalla_ceil = 15`, `district_floor = 10`, `district_ceil = 30`,
`cell_ratio_mahalla = 0.15`, `cell_ratio_district = 0.30` — hammasi
hujjatdan tekshiriladi.

Lekin **§9 — bu `kalit → qiymat` ro'yxati.** U `5` va `15` borligini biladi,
ular **qayerda** turishini emas:

- `clamp(5, ceil(0.35 × sqrt(H)), 15)` da pol bilan shift o'rin almashsa §9
  testi yashil qolardi. `clamp` `ValueError` bilan yiqilgunicha hech narsa
  sezilmasdi va u ham faqat ishga tushirish paytida.
- `cell_ratio_mahalla` (0.15) bilan `cell_ratio_district` (0.30) o'rin
  almashsa narvon **teskari** ishlardi: mahalla darajasiga chiqish tuman
  darajasiga chiqishdan qiyinroq bo'lardi. §9 buni ham ko'rmasdi.
- `T_mahalla` `H_district` dan hisoblanadigan bo'lib qolsa — ham ko'rinmasdi.

## 4. Ikkita son §9 da umuman yo'q

`06` §5.3 to'rtta sonni beradi va ular **ikki xil maqomda** yashaydi:

| Son | §9 da | Kodda |
|---|---|---|
| `cell_coverage_ratio ≥ 0.15` | bor | `ScaleParams.cell_ratio_mahalla` |
| `cell_coverage_ratio ≥ 0.30` | bor | `ScaleParams.cell_ratio_district` |
| `cells_with_reports ≥ 3` | **yo'q** | `MIN_CELLS_FOR_MAHALLA` (`scale.py:34`) |
| `mahallas_affected ≥ 2` | **yo'q** | `MIN_MAHALLAS_FOR_DISTRICT` (`scale.py:37`) |

Oxirgi ikkitasiga koddagi yagona havola — izoh matni («`06` §5.3»). Izoh esa
hech narsani ushlab turmaydi, ya'ni 49-running testi ularni **printsipial
ravishda** ko'ra olmaydi. Bu 52-running asosiy topilmasi.

Bundan bitta savol chiqdi va u **kodga emas, «Ochiq savollar» ga** yozildi
(👤): bitta shartning ikkita yarmi nega har xil sozlanuvchan? E11 da nisbatni
tushirib, katakcha sonini tushira olmaslik chegarani amalda qimirlatmaydi.

## 5. Misollar jadvali — qo'lda ajratilgan ikkita narvon

`06` §5.2 ning beshta qatori **bitta ustunda** ikkita narvonni beradi:

| Hudud | `H` | Chegara | Qaysi funksiya |
|---|---|---|---|
| Kichik/O'rta/Katta mahalla | 130 / 460 / 1 100 | 5 / 8 / 12 | `mahalla_threshold` |
| O'rta/Katta tuman | 8 200 / 16 400 | 30 / 30 | `district_threshold` |

`test_scale.py` bu ajratishni **qo'lda** ikkita `parametrize` ga bo'lgan va
jadval bilan bog'lamagan. Ya'ni mahalla ro'yxatiga tuman qatorining kutilgan
qiymati yozilsa hech narsa sezilmasdi. Yangi testda funksiya `Hudud`
ustunidan aniqlanadi (`_tier_of`), ya'ni ajratish **hujjatniki**.

## 6. `(pol)` va `(shift)` izohlari — jadvalning eng qimmatli qismi

Jadval uchta qatorni izohlaydi: `**5** (pol)`, `**30** (shift)`,
`**30** (shift)`. Bu shunchaki bezak emas — u §5.2 ning butun ma'nosini
tashiydi: narvon **kichik** mahallada foydalanuvchi so'raganidek
(`3 → 5 → 10`) chiqadi va katta tumanda avtomatik ko'tariladi.

`test_clamp_annotations_mean_what_they_say` izohni ma'nosi bo'yicha o'qiydi:

- `(pol)` → natija polga teng **va** xom qiymat poldan past;
- `(shift)` → natija shiftga teng **va** xom qiymat shiftdan yuqori;
- izohsiz → `floor < natija < ceil`.

Izohsiz qator chegaraga tegib qolsa test qizaradi — chunki bu formula endi
hech narsani moslamayotganini bildiradi (hamma joyda bir xil son).

## 7. Hujjatning o'z arifmetikasi tekshiriladi

`test_example_arithmetic_is_self_consistent` `Formula` ustunini
(`0.35 × 11.4 = 4.0`) uchta songa ajratadi va ikkita mustaqil savol beradi:
`11.4` haqiqatan `sqrt(130)` mi (`abs_tol=0.1`, hujjat 1 kasrga yaxlitlagan)
va `4.0` haqiqatan `0.35 × 11.4` mi (`abs_tol=0.05`). Beshala qator o'tadi.

Sabab: hujjatdagi arifmetik xato «bu son qayerdan?» degan savolni tug'diradi
va odatda **kodni hujjatga emas, hujjatni kodga** moslashtirish bilan
tugaydi.

## 8. §5.3 bog'lovchilari — matn **va** xulq-atvor

Hujjat mahalla shartini `∧` bilan, tuman shartini ichkarida `yoki` bilan
yozgan va buni matnda alohida ta'kidlaydi («son ham, tarqoqlik ham talab
qilinadi»). Ikkalasi ham ikki tomonlama qulflandi:

- `test_mahalla_branch_is_a_conjunction` — qatorda `yoki` yo'q, `∧` roppa-rosa
  ikkita; **va** `populated_cells = 4`, `cells_with_reports = 2` holatida
  (nisbat 0.5 — yetarli, katakcha soni 2 — yetmaydi) `raw_scale` `local`
  qaytaradi. Bu «bitta transformator» holati.
- `test_district_branch_keeps_its_disjunction` — qatorda `yoki` bor; **va**
  `mahallas_affected = 1` bo'lsa ham keng qamrov (0.4 ≥ 0.30) `district`
  beradi. `VA` ga aylantirilsa bitta katta mahalladan iborat tuman hech
  qachon `district` bo'lmasdi.

Ikkala holatda ham qarama-qarshi tomon `None` bilan o'chirildi, ya'ni test
aynan bitta shoxni o'lchaydi.

## 9. §5.4 to'sig'i

Uchta qoida (`A_district < 30`, `A_mahalla < 10`, `data_quality='unknown'`)
`GuardParams` va `QUALITY_UNKNOWN` ga bog'landi, va uchalasining natijasi
**`local`** ekani alohida tekshiriladi. Sabab: `_demote` ni bu yerga ham
qo'llash `district` ni `mahalla` ga tushirardi, ya'ni katta da'vo baribir
qolardi — faqat bir pog'ona pastroq. Hujjat esa narvonni emas, **to'liq
tushishni** talab qiladi (§5.4: kam ma'lumotdan katta xulosa chiqarish
kraudsorsingning eng jiddiy xatosi).

## 10. Ataylab tekshirilmagan narsa

§5.2 jadvalining `Aholi` → `H` ustuni `estimate_households` ning natijasi
**emas**: `700 / 5.4 = 129.6` (jadvalda `130`), `6 000 / 5.4 = 1111`
(jadvalda `1 100`). Bular yaxlitlangan illyustratsiya. Bog'lash testni
asossiz qizil qilardi, shuning uchun sabab fayl docstringiga va «Ochiq
savollar» ga yozildi — keyingi run buni «drift» deb o'qib qattiqlashtirmasin.
§3.1 formulasining o'zi `test_territory_stats_contract.py` da qulflangan.

## 11. Qarorlar va rad etilganlar

- **`SPEC_TIER_ROWS = 3`, `SPEC_EXAMPLE_ROWS = 5`, `SPEC_GUARD_RULES = 3`
  aynan** (47/49/51 naqshi) — jadval o'ssa bu ko'rinadigan qaror bo'lsin.
- **Jadval parseri ajratgichdan (`|---|`) keyin boshlanadi** — 51-running
  sabog'i, o'zgartirilmadi.
- **`×` belgisi regexda `.` bilan** olinadi: hujjatda `*` ga almashtirilsa
  test sababsiz yiqilmasin. Koeffitsientning **qiymati** baribir
  solishtiriladi.
- **Rad etildi:** `06` §4.2 chegara jadvalini shu faylga qo'shish. U ham
  qo'lda (`test_confirmation.py:144`) va **aynan shu shaklga ega**
  (`adaptive_threshold`), lekin boshqa bo'lim — alohida fayl bo'ladi. Bu
  keyingi running nomzodi.
- **Rad etildi:** `MIN_CELLS_FOR_MAHALLA` ni `ScaleParams` ga ko'chirish. Bu
  hujjatga (§9 jadvaliga) tegadigan o'zgarish — «Ochiq savollar» da 👤.

## 12. Sandbox

`mcp__workspace__bash` ikki urinishda ham `useradd failed: No space left on
device` bilan yiqildi — **yigirma uchinchi ketma-ket run**. `ruff check` va
`pytest -m "not requires_db"` yana ishga tushmadi. Butun ish fayl asboblari
bilan bajarildi; yangi test qo'lda, qadamma-qadam tekshirildi (regexlar
hujjatdagi haqiqiy qatorlarga qo'lda moslandi, chegaralar qo'lda
hisoblandi, satr uzunligi `line-length = 100` ga qarab o'lchandi).

👤 `cleanup-sessions.ps1` ni ishga tushiring — 36–52 runlarning ~290 ta testi
hech qachon ishlamagan.

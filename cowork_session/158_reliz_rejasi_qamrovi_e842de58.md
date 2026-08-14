# 158-run — `01` §25 reliz rejasi: 77-running o'lchovi rad etildi

**Sessiya:** `local_e842de58` · **Sana:** 2026-08-14 · **Epic:** REL
(mutatsiya qamrovi) · **Nishon:** `sveta/app/release/plan.py` (597 qator)

---

## 1. Nishon qayerdan olindi

157-run beshta «eski-harness moduli» qoldirgan edi va ro'yxatning
birinchisi — `plan.py`. Qoida bo'yicha nishon **jurnaldan** tasdiqlandi:
`PROGRESS.md` ning 77-run qatorida so'zma-so'z «37 mutatsiya,
1 survivor tuzatildi» yozilgan. 77-run 126-rundan **oldin** bo'lgan,
ya'ni o'sha o'lchov `verdict` `returncode != 0` bo'lgan harness bilan
olingan — `pytest` ning `rc=4` i (yo'l topilmadi, plagin yo'q) yolg'on
`KILLED` berardi. Shuning uchun raqam da'vo, natija emas.

## 2. O'lchov

**50 mutatsiya → 28 KILLED, 22 SURVIVOR (44 %)**, `rc≠1` yo'q,
ekvivalent yo'q.

Qorovullar **faqat zaiflashtirildi** (`and False`): `_check_registry()`
modul import paytida yuriladi, ya'ni kuchaytirilgan qorovul butun
to'plamni collection error ga olib kelardi va bu o'lchov emas, xato
bo'lardi. Shu sababdan `SPEC_ROWS`, `COLLIDING` va
`GATE_NEEDS_EVIDENCE` ning **o'zini** mutatsiya qilib bo'lmaydi —
har uchalasi import-vaqt qorovuli bilan qulflangan.

**Ikki bosqich.** Tor tanlov (`plan` ni import qiladigan to'rt fayl:
`test_release_plan_contract`, `test_admin_registries`,
`test_roadmap_contract`, `test_scope_contract` — 231 test, 11 s)
22 nomzod berdi. Tor tanlov faqat *yolg'on survivor* berishi mumkin,
*yolg'on KILLED* emas — shuning uchun yigirma ikkalasi ham keyin butun
bazasiz to'plamda (3616 test) birma-bir tasdiqlandi. Yigirma ikkalasi
ham SURVIVED: **yolg'on survivor yo'q.**

## 3. Survivorlar — uch oila

### (a) `_check_registry` ning o'n sakkizta shartidan yettitasi hech qachon otilmagan

9-bo'lim `Alias` tarmoqlarini va dalilning **ortiqchaligi** ni otardi.
Otilmaganlari:

| Shart | Nima yashiringan bo'lardi |
|---|---|
| `len(ROWS) != SPEC_ROWS` | 1-bo'lim `len(rp.ROWS) == rp.SPEC_ROWS` ni **ma'lumot** sifatida o'qiydi; qorovulning o'zi o'lchanmagan |
| `len(ROW_BY_CODE) != len(ROWS)` | takrorlangan kod qatorni lug'atda jimgina yutardi |
| `not row.note` | izoh matni ataylab tekshirilmaydi, **borligi** esa kontrakt |
| `ship is not ABSENT and not ship_binds` | dalilsiz `BUILT`/`PARTIAL`/`CONTRADICTED` — baho beriladi, kuzatiladigan joyi ko'rsatilmaydi; 9-bo'lim faqat teskarisini (`ABSENT` + ortiqcha dalil) otardi |
| `not item.binds` | `UNPLANNED` dalilsiz |
| `not item.why_not_covered` | `UNPLANNED` izohsiz |
| `for item in UNPLANNED` sikli | `UNPLANNED[:1]` sezilmasdi — `UP-2` umuman tekshirilmasdi |

Qatorlar sikli esa **qulflangan** edi: `enumerate(ROWS[:-1])`
ushlandi, chunki 9-bo'lim `RP-5` ustida ikkita parametr yurgizadi.

### (b) Hisobotning shakli — 154/155/156/157 sinfi beshinchi marta

`by_alias`, `by_ship`, `by_gate` chelaklarini «uchragan sinflardan»
qurish bugun **bir xil** javob beradi: uchala o'qning ham to'rttala
sinfi to'la. Ertaga bir sinf bo'shab qolsa u hisobotdan **yo'qolardi**
— «bu sinfda qator yo'q» degan javob «bunday sinf yo'q» ga aylanardi.
Qulf — bitta qatorli hisobot (`RP-3`): chelaklar to'plami baribir
to'liq `Alias`/`Ship`/`Gate` bo'lishi shart.

Qolgan xossalar **o'lchangan** va bu shu oilada birinchi marta:
`accurate` ning uchala kon'yunkti ham, `and`→`or` ham, `is_shippable`,
`is_answerable`, `ANSWERABLE`, `phase_zero_bound`, `colliding` va
`unshippable` — hammasi 10-bo'lim tomonidan ushlandi.

### (c) Siyosat, lug'at va dalil kortejlari

* `collides` — `self.alias in COLLIDING` ni literal
  `self.alias is Alias.REASSIGNED` ga almashtirish bugun ekvivalent
  (to'plam bitta sinfdan iborat). Qulf — `monkeypatch` bilan to'plamni
  almashtirib xossani **qayta so'rash**.
* Uchala `StrEnum` ning qiymatlari (`Alias.SHARED`,
  `Ship.CONTRADICTED`, `Gate.UNRECORDED`) hech qayerda o'lchanmagan,
  holbuki `admin/registries.py` reyestrni vitrinaga chiqaradi.
* **Oltita** qatordan (`RP-1` ×3, `RP-2`, `RP-3`, `RP-4`) va **ikkala**
  `UNPLANNED` bandidan dalil kortejining bittadan elementi jimgina
  tushib qolardi. `test_every_bind_resolves_to_a_real_symbol` —
  mavjudlik tekshiruvi, test emas: u dalilning **yetishmasligini**
  ko'rmaydi. Bu 156/157 ning sabog'i uchinchi marta.

## 4. Qulf

Yangi fayl yaratilmadi. Mavjud `tests/test_release_plan_contract.py`
ga **11-bo'lim** qo'shildi: +12 test (51 → 63).

⚠️ **Uslub.** `pytest.raises(match=...)` shart: dalilsiz `PARTIAL` va
dalilsiz `INSTRUMENTED` bir xil «dalil yo'q» matnini beradi, mutantni
faqat sinf nomi ajratadi (`match="partial"`). `_check_with` ning
juftligi `_check_unplanned` qo'shildi. `_swap("RP-5", code=...)`
**ishlamaydi** — `_swap` ning birinchi pozitsion parametri ham `code`
deb ataladi; takrorlangan kod `replace(rp.ROWS[-1], code="RP-1")`
bilan quriladi.

## 5. Infra

To'liq to'plam **parallel yurgizilmaydi**: ikkita ishchi ikkita
yadroda birga yurganda 4+4 mutant 175 s ga sig'madi, chaqiruv uzildi
va `finally` bajarilmagani uchun **ikkala nusxada ham** mutatsiyalangan
fayl qoldi. `timeout 165 …` bilan o'rash ham xuddi shunday qoldiradi
(jarayon `SIGTERM` bilan o'ladi). Shuning uchun:

* tor tanlov bosqichi — ikkita ishchi, 12 tadan (~130 s);
* to'liq to'plamli bosqich — **ketma-ket bitta ishchi**, chaqiruviga
  **uchtadan** (3 × 41 s ≈ 125 s);
* har partiyadan keyin `diff … r158_base` bilan nusxaning tozaligi
  tekshiriladi.

`bash` chaqiruvida `timeout_ms=175000` majburiy.

## 6. Yakun

**3628 passed, 299 skipped** (+12), `requires_db` 299 (yurgizilmadi —
o'zgarish bazaga tegmaydi), migratsiyasiz, `ruff check` toza.
Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar **tegilmadi** —
yagona o'zgargan fayl `sveta/tests/test_release_plan_contract.py`.

**Keyingi qadam:** qolgan **to'rtta** eski-harness moduli —
`acceptance.py` (580, 70-run «0»), `gates.py` (563, 66-run «1»),
`dependencies.py` (541, 76-run «1»), `measures.py` (457, 67-run).
Nishonni har safar jurnaldan tasdiqlash shart.

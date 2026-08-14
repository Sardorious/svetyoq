# 149-sessiya — `notifications/channels.py`: parserning o'lchanmagan qorovullari

**Sana:** 2026-08-13
**Sessiya:** `local_e9dcc282`
**Epic:** E13 / REL (`01` §19)
**Natija:** 28 mutatsiya → **19 KILLED, 9 SURVIVOR**; to'qqizalasi butun
to'plamda tasdiqlandi (yolg'on survivor yo'q) va to'qqizalasi ham qulflandi.
Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**.

---

## 1. Nishon 148 ning rejasidan chetga chiqdi — va sabab yozib qoldiriladi

148 keyingi run uchun tartib qoldirgan edi:

> (1) 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi;
> **(2) `notifications/params.py` va `channels.py`**.

(2) bandning **birinchi yarmi eskirgan**. `PROGRESS.md` ning run jurnali
(2026-08-12, 130-run) shuni yozadi:

> mutatsiya qamrovi: uchta bazasiz modul — `app/notifications/params.py`
> **12/12**, `app/jobs/runner.py` 9/9, `app/notifications/events.py` …

Ya'ni `params.py` harness tuzatilgandan (128-run) **keyin** to'liq
o'lchangan. Buni koddan ham ko'rish mumkin edi:
`tests/test_notify_params.py` ning docstringlari mutatsiya raqamlarini
nom bilan tilga oladi — «130-run, mutatsiya M1», «M9», «M3, M12».

Shuning uchun nishon **faqat `channels.py`** ga toraytirildi. U
`EpicProgress.md` §4 ning bazasiz navbatida `sender.py` bilan yonma-yon
turadi (`sender.py` 148 da yopilgan), ya'ni navbatning boshi.

**Qoida (149): nishonni tanlashdan oldin `PROGRESS.md` ning run
jurnalida modul nomini `grep` qilish shart.** 148 ning ro'yxati
`EpicProgress.md` §4 ning navbatidan olingan, o'sha navbat esa 130 dan
keyin yangilanmagan — reja bilan jurnal orasidagi farq shu joyda
ko'rindi.

---

## 2. Nishondan oldingi `grep` (148 ning sabog'i)

`channels.py` (745 qator) ga test qatlamidan **uchta** fayl murojaat
qiladi: `test_notification_channels_contract.py` (61 test),
`test_scope_contract.py`, `test_release_plan_contract.py`. Ya'ni 148
ning «nol import» holati bu yerda **yo'q** — modul chinakam
o'lchanadi, va bashorat past survivor edi.

Bashorat noto'g'ri chiqdi, lekin **boshqa sabab bilan**: survivorlar
o'lchanmagan xatti-harakatda emas, o'lchanmagan **qorovullarda**.

---

## 3. O'lchov

**1-bosqich** — tor nishon to'plami (5 fayl, 235 test, ~10 s):
`test_notification_channels_contract.py`, `test_scope_contract.py`,
`test_release_plan_contract.py`, `test_i18n_key_contract.py`,
`test_business_interfaces_contract.py`.

**2-bosqich** — faqat survivorlar butun to'plamda (3745 test, 114–123 s
uchta ishchida parallel). To'qqizdan to'qqizi **SURVIVED** — ya'ni
1-bosqichning tor tanlovi bitta ham yolg'on survivor bermadi.

| # | Mutatsiya | Verdikt |
|---|---|---|
| M01 | `_SECTION_RE` dan `$` anchori | **SURVIVOR** |
| M02 | `_NEXT_SECTION_RE`: `^##\s+\d+\.` → `^##` | **SURVIVOR** |
| M03 | `_BASELINE_RE`: `(\d+)\s*м\s+Ташкента` → `(\d+)\s*м` | **SURVIVOR** |
| M04 | `_split_row` dan `cell.strip()` | KILLED |
| M05 | `section_text`: `rest[: nxt.start()]` → `rest` | KILLED |
| M06 | `if tail: raise` («qoidadan keyin yana jadval») | **SURVIVOR** |
| M07 | `missing` ustunlar tekshiruvi | **SURVIVOR** |
| M08 | `unknown` ustunlar tekshiruvi | KILLED |
| M09 | `len(cells) != len(header)` | **SURVIVOR** |
| M10 | `row.claim` no-op qatori | KILLED |
| M11 | `if not row.rationale` | KILLED |
| M12 | `" ".join(tail)` → `"".join(tail)` | **SURVIVOR** |
| M13 | `_SEPARATOR_RE` qatori | KILLED |
| M14 | `why.strip()` → `why` | KILLED |
| M15 | `SURFACED`: `or` → `and` (ikkala maydon) | KILLED |
| M16 | `elif surfaced_as or carries` → `and` | **SURVIVOR** |
| M17 | `standing in (HELD, BORROWED)` → `is HELD` | KILLED |
| M18 | `elif not assessment.evidence` | KILLED |
| M19 | `assessment.channel != row.channel` | KILLED |
| M20 | `overstated`: `is not DELIVERS` → `is NONE` | KILLED |
| M21 | `unguarded_policy`: `is not HELD` → `is UNHELD` | KILLED |
| M22 | `accurate` dan `not self.undeclared` | KILLED |
| M23 | `counts`: `s.value` → `s.name` | KILLED |
| M24 | `ChannelTable.row`: `==` → `!=` | KILLED |
| M25 | `if not clause.evidence` | **SURVIVOR** |
| M26 | `orphans = []` | KILLED |
| M27 | `clause.quote not in rule_text` | KILLED |
| M28 | `NONE` da dalil taqiqi | KILLED |

---

## 4. Survivorlarning sinfi — bitta va u modulning turiga xos

**Bugungi hujjat qorovulni otdirmaydi.**

`channels.py` ikki qismdan iborat: `01` §19 ni **parse qiladigan** qism
va koddagi holatni **baholaydigan** reyestr. Testlar reyestrni
zich o'lchaydi — baholash qatlamining o'n to'rtta mutatsiyasidan
o'n uchtasi o'ldi. Parser esa faqat **bugungi matnda** o'lchanadi:
har test §19 ni yoki `SYNTHETIC` ni o'qiydi va natijani tekshiradi.

Qorovullar (`missing`, «yana jadval», qator uzunligi, `$` anchori,
`" ".join`) esa hujjat **o'zgarganda** otiladi. Bugungi matn ularning
birortasini ham otdirmaydi — ya'ni ularni olib tashlash birorta
testni yiqitmasdi, va §19 ning keyingi tahriri jimgina noto'g'ri
o'qilardi.

Bu 148 ning sinfidan farq qiladi. 148 da o'lchanmagan narsa —
**ertangi xatti-harakat** (navbat qanday urinadi). 149 da —
**ertangi kirish** (hujjat qanday tahrirlanadi). Ikkalasi ham bugungi
javobda ko'rinmaydi, lekin sabab boshqa: birinchisi vaqtga bog'liq,
ikkinchisi hujjatga.

### Eng qimmat uchtasi

**M03 — meros radius o'z iborasidan uzildi.** `(\d+)\s*м\s+Ташкента`
dan «Ташкента» ni olib tashlash regexni paragrafdagi **birinchi**
metr soniga bog'laydi. Aynan shu son
`test_the_shipped_default_is_still_the_inherited_number` da
`bootstrap().default_radius_m` bilan solishtiriladi — ya'ni «obuna
radiusi hali Toshkentniki» degan **ochiq savolning** o'lchovi. Boshqa
son o'qilsa test yiqilib, «kalibrlash bo'ldi» degan yolg'on xulosani
talab qilardi.

**M07 — «notanish ustun» o'lchangan, «yo'q ustun» — yo'q.** Ikkala
tekshiruv `parse_table` da yonma-yon yozilgan va bir xil ko'rinadi,
lekin har xil xatoni ushlaydi. `missing` siz sarlavhasi qisqargan
jadval `KeyError` bilan yiqilardi — `ValueError` bilan yozilgan barcha
diagnostika chetlab o'tilardi.

**M12 — qoida paragrafi bo'shliqsiz yopishardi.** Bugun paragraf bir
qatorda, shuning uchun `" ".join` ham, `"".join` ham bir xil natija
beradi. Hujjatda qator ko'chirilishi bilan `RULE_CLAUSES` ning uchala
iqtibosi ham topilmay qolardi va `build_report` §19 ni «qoida buzilgan»
deb yiqitardi — matnning **mazmuni** o'zgarmagan holda.

### Bitta survivor xatti-harakatni emas, xabarni ushlaydi

**M09** — `len(cells) != len(header)` qorovulisiz ham
`dict(zip(header, cells, strict=True))` `ValueError` beradi, ya'ni
mutant tur bo'yicha **ekvivalent**. Farq faqat o'quvchida: `zip()
argument 2 is shorter than argument 1` hujjatni tahrirlagan odamga
hech narsa demaydi, «qatorda 2 katakcha, sarlavhada 3» esa aynan
qaysi qator buzilganini aytadi. Test shuning uchun **xabarga**
yozilgan va bu docstringda ochiq qayd etilgan.

---

## 5. Qulflar

Barchasi mavjud `tests/test_notification_channels_contract.py` ga,
yangi **12-bo'lim** sifatida (yangi fayl kerak bo'lmadi: `SYNTHETIC`
hujjati, `_row()` yordamchisi va `prd`/`table`/`report` fikstyuralari
o'sha faylda va ularni ikkinchi faylga **nusxalash** 61-run ning
taqiqiga tushardi).

| Test | Qulflaydi |
|---|---|
| `test_the_section_heading_must_end_at_the_line` | M01 |
| `test_the_section_ends_only_at_the_next_numbered_section` | M02 |
| `test_the_inherited_radius_is_read_from_its_own_phrase` | M03 |
| `test_a_second_table_after_the_rule_is_rejected` | M06 |
| `test_a_header_missing_a_column_is_rejected` | M07 |
| `test_a_ragged_row_names_both_counts` | M09 |
| `test_a_wrapped_rule_paragraph_keeps_its_words_apart` | M12 |
| `test_a_lone_artifact_field_without_surfaced_is_rejected` (2 parametr) | M16 |
| `test_a_clause_without_evidence_stops_the_report` | M25 |

**Qayta o'lchov:** to'qqizala mutant ham `KILLED`, har biri **bittadan**
test bilan (`1 failed, 244 passed`); M16 — ikkita parametr bilan
(`2 failed, 243 passed`).

---

## 6. Muhit (150 uchun retsept)

`/tmp` 147–148 dan saqlanib qolgan: `micromamba` muhitlari `py311` va
`pg` joyida. Yangidan kerak bo'lgani:

* **`/tmp/pgdata148` o'qib bo'lmaydi** — u `nobody:700`, sandbox
  foydalanuvchisi almashgan. Har run yangi `initdb -D /tmp/pgdataNNN`
  va yangi port (`55149`).
* **Ishchi nusxalar ham `nobody`** (`/tmp/x1..x3`) — yangi `/tmp/y1..y3`.
* 🔴 **Nusxa repo ILDIZIDAN olinadi, `sveta/` dan emas.** Faqat
  `sveta/` ko'chirilganda **8 ta collection error** chiqadi
  (`test_scale_ladder_contract.py`, `test_worked_examples_contract.py`
  va h.k. — ildizdagi `01`…`06` hujjatlarini o'qiydi), keyin
  `deploy-server/` ham kerak bo'ldi (`test_deploy_web_contract.py` —
  4 fail). To'liq to'plam: `sveta/` + ildizdagi `*.md` + `deploy-server/`.
* 🔴 **`pg_ctl start` HAR `bash` chaqiruvida qaytariladi** — chaqiruvlar
  orasida jarayon o'ladi (147 ning `pgup` eslatmasi kuchida).
* Uchta ishchi bitta `bash` chaqiruvi ichida `&` + `wait` bilan
  parallel yuradi. Butun to'plam yolg'iz **69 s**, uchta parallel
  ishchida **114–123 s** — ya'ni bitta chaqiruvga **uchta** to'liq
  to'plam sig'adi, ko'pi emas. `timeout_ms: 178000` oshkora beriladi.

---

## 7. O'lchovlar

* Butun to'plam: **3755 passed, 1 skipped** (148: 3745 — aynan +10)
* `-m requires_db`: **298 passed** (o'zgarmadi — yangi testlar bazasiz)
* `ruff check .`: `All checks passed!`
* Migratsiya: **yo'q** (oxirgisi `0011`)
* `diff -r` (repo ↔ ishchi nusxa): `app/` va `tests/` **aynan bir xil**,
  mutant qoldig'i yo'q
* Vaqtinchalik fayl yaratilmadi (CLAUDE.md §1 ning ⛔ qoidasi)

---

## 8. 150 uchun tartib

1. **`app/analytics/track.py` va `catalogue.py`** — `EpicProgress.md` §4
   navbatining keyingi juftligi. `track.py` ga test qatlamidan **nol**
   to'g'ridan-to'g'ri import bor (149 ning skani), ya'ni 148 ning
   sinfidagi topilma ehtimoli yuqori.
2. `app/obs/{readings,latency,monitoring}.py` va `app/stats/methodology.py`.
3. 🔴 **`EpicProgress.md` §4 ning bazasiz navbati eskirgan** — u 130-run
   sanog'ida qotib qolgan va allaqachon o'lchangan modullarni
   (`params.py`, `sender.py`, `events.py`) hali ham navbatda ko'rsatadi.
   Navbat `PROGRESS.md` ning run jurnali bo'yicha qayta yig'ilsin.
4. 👤 `service._create_intents` ning qaytargan qiymatini hech kim
   o'qimaydi (148 dan qoldi).
5. 👤 `cowork_session/` dagi nusxa juftliklari
   (`100_…_70dfe57e` ↔ `144_…_70dfe57e`, to'rtta `28_*`) — agent
   o'chira olmaydi (`mcp__cowork__allow_cowork_file_delete` taqiqlangan).

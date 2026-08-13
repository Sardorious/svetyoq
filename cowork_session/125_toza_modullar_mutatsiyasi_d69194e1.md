# 125-sessiya — qolgan to'rtta toza modulning mutatsiyasi

**Sessiya:** `local_d69194e1-16b8-43aa-a888-14df528b2e30` · **Sana:** 2026-08-12
**Natija:** ✅ `stats/boundaries.py` 15/15 · ✅ `stats/maturity.py` 15/15 ·
✅ `stats/mahalla_coverage.py` 20/20 · ✅ `geo/quality.py` 23/23 ·
73 mutatsiya (49 birinchi o'tishda KILLED, 4 yolg'on survivor, 20 qulflandi, +19 test) ·
ekvivalent mutant **yo'q** · mahsulot kodi tegilmadi ·
3248 passed / 232 skipped (3480 yig'ildi) · `ruff` toza ·
⛔ disk ketma-ket **to'rtinchi** run to'la — `requires_db` yana yurgizilmadi

---

## Nima uchun aynan shu ish

124-run ikkita xulosa qoldirgan edi: (1) 123 ning «mahsulot yadrosida
mutatsiyasiz modul qolmadi» degan yakuni **bekor** — o'lchanmagan yana
oltita toza (bazasiz, HTTP siz) modul bor; (2) ulardan ikkitasi
(`stats/duration.py`, `obs/alerts.py`) o'sha runda olindi, to'rttasi
qoldi. Qolgan to'rttasi **bazasiz**, ya'ni disk to'la bo'lsa ham
o'lchanadi — 124 ning «keyingi qadam» ro'yxatidagi birinchi band aynan
shu edi.

---

## Harness va nishon to'plami

Harness 124 nikidan ko'chirildi va o'sha qat'iy qoida bilan:
**`KILLED` faqat `rc == 1`**, `rc not in (0, 1)` — harness xatosi
(119-run ning yolg'on `KILLED` i shundan kelib chiqqan edi). Repodagi
`tools/_mut.py` hali ham `returncode != 0` bilan hukm qiladi va yana
ishlatilmadi — 👤 uni tuzatish yoki o'chirish kerak (agent
`allow_cowork_file_delete` ni chaqira olmaydi).

Nishon to'plamini tanlashda yangi qaror: **tor to'plam + survivorlarni
kengaytirilgan to'plamda qayta tekshirish**. Sabab o'lchangan: butun
nishon birlashmasi (35 fayl) bitta bash chaqiruviga sig'madi — ba'zi
kontrakt fayllari yolg'iz o'zi 20–30 s (`test_i18n_key_contract` 19 s,
`test_functional_requirements_contract` 10 s), tor to'plam esa 11–12 s
(import narxi ustunlik qiladi, testlarning o'zi 1–1.5 s). Shuning uchun:
har mutant tor to'plamda, `SURVIVED` chiqqani esa qaysi kontrakt uni
ushlashi mumkinligi aniqlanib qayta yurgiziladi. Bu **to'rtta yolg'on
survivorni** ochdi.

---

## `stats/boundaries.py` — 15 mutatsiya, 13 KILLED

Ikkala survivor ham bitta sinf: **chegaraning o'zi**.

- `f.valid_from > start` → `>=`;
- `f.valid_to < end` → `<=`.

Mahsulotdagi ma'nosi bir xil: davr boshida kuchga kirgan (yoki davr
oxirida yopilgan) kesim davr **ichida** o'zgarish emas — butun oyna
o'sha bitta rejim ostida o'tgan. `>=` bo'lsa, davri import sanasidan
boshlanadigan **har** so'rov vitrinaga «chegaralar o'zgardi»
ogohlantirishini qo'yardi. Bu yangi mintaqada (Samarqand, 2026-08-12 da
import qilingan) **birinchi kundanoq** yonardi va ogohlantirish
ma'nosini yo'qotardi.

Qulflar: `test_a_slice_opened_exactly_at_the_period_start_is_not_a_change`,
`test_a_slice_closed_exactly_at_the_period_end_is_not_a_change`.

---

## `stats/maturity.py` — 15 mutatsiya, 11 KILLED

To'rtta survivor, hammasi `days` arifmetikasi va sabablar ro'yxatida:

- `max(0, …)` qorovulining olib tashlanishi — `observed_since`
  kelajakda bo'lsa (server soati, importdagi sana) `observed_days`
  **manfiy** chiqardi;
- `max(0, …)` → `max(1, …)` — bugun boshlangan kuzatuv «1 kun» deb
  yozilardi, ya'ni o'lchov o'zi haqida bittaga ko'p da'vo qilardi;
- `events < min_events` → `<=` — chegarani aynan bajargan mintaqa yana
  bitta hodisa kutardi va javobda ochiq turgan `min_events` yolg'on
  bo'lardi;
- `elif days < min_days` → `if` — tarixsiz mintaqa «tarix yo'q» **va**
  «tarix qisqa» degan bir-birini inkor qiladigan ikki sabab olardi.

Oxirgisi qiziq: mavjud test `REASON_NO_HISTORY in result.reasons` deb
yozilgan edi, ya'ni ro'yxatning **to'liqligini** tekshirmasdi — 108-runda
topilgan «bor tekshirilardi, to'liq emas» sinfining yana bir holati.
Qulf testi endi teng solishtiradi.

---

## `stats/mahalla_coverage.py` — 20 mutatsiya, 12 KILLED

Sakkizta survivordan **ikkitasi yolg'on**: ogohlantirish kalitlarining
nomlari (`stats.warning.mahallas_missing`,
`stats.warning.mahallas_unmeasured`) `tests/test_i18n_key_contract.py`
bilan ushlanadi.

**Bu 124 ning topilmasiga to'g'ridan-to'g'ri javob.** 124 da
`obs/alerts.py` ning yettala survivori bitta sinf edi — refleksivlik:
konstantaning **qiymati** hech qayerda qayta sanalmagan. Bu yerda
o'sha sinf takrorlanmadi va sabab aniq: i18n kalitining **katalogi**
bor va uni boshqa fayl qayta sanaydi, Prometheus yorlig'iniki esa yo'q.
Ya'ni refleksivlik xavfi «konstanta tashqi shartnomaga chiqadimi va uni
boshqa fayl mustaqil qayta sanaydimi» degan savolga bog'liq — kod
uslubiga emas.

Haqiqiy oltitasi:

- `MIN_MEASURED_RATIO` ning **qiymati** (`0.5` → `0.4`) va uning qat'iy
  `<` **chegarasi** — ikkalasi ikki tomondan qulflandi (aynan yarmi →
  ogohlantirish yo'q; 2/5 → bor);
- o'rtachada `round` → kesish — kesish har doim pastga oladi, ya'ni
  mahalla indeksi tizimli kamayardi (mavjud testlarning **hammasida**
  o'rtacha butun songa tushardi, ikkala amal bir xil javob berardi);
- `min(qualities)` → `max` — aralash sifatda kuchsizrog'i emas,
  kuchlirog'i olinardi (`06` §5.4 ga zid);
- `sufficiency` ning o'rtachasi → maksimum — bitta yaxshi qamralgan
  mahalla butun kesimni ko'tarardi;
- taqsimotning `band` emas `raw_band` bo'yicha sanalishi — **eng
  qimmati**: bitta javob ichida xarita pasaytirilgan pog'onani,
  `01` §21 dashboardi esa pasaytirilmaganini ko'rsatardi, ya'ni
  degradatsiya vitrinaning bir joyida ko'rinib, ikkinchisida
  yo'qolardi.

---

## `geo/quality.py` — 23 mutatsiya, 13 KILLED

O'nta survivordan **ikkitasi yolg'on**: `ALLOWED_LICENSES`
(`test_dependencies_contract.py` uni to'g'ridan-to'g'ri sanaydi) va
`check_closed_rings` ning `unclosed == 0` sharti
(`test_release_plan_contract.py` `RP-1` uchun tekshiradi).

Haqiqiy sakkiztasining ikkitasi mahsulot xavfi bo'yicha ajralib turadi:

**1. `if not reference_area:` → `is None`.** `SQL_COVERED_AREA`
`COALESCE(ST_Area(…), 0)` bilan yozilgan, ya'ni etalon qatori
bo'lmaganda funksiyaga **`None` emas, `0.0`** keladi. `is None`
qorovuli bu holatni o'tkazib yuborardi va sifat darvozasi tushunarli
blok xabari o'rniga `ZeroDivisionError` bilan yiqilardi. Bu chekka hol
emas: 119-runda prodda aynan «shahar chegarasi berilmagan» holati
ko'rilgan edi.

**2. `is_blocker` va `blockers` ning `blocking and not passed` →
`not passed` ga kuchsizlanishi.** `05` §5.3 ikki darajani ataylab
ajratadi (bloklovchi mezon ↔ ogohlantirish). Mutant bilan
`degenerate` qoplash **ogohlantirishi** bloklovchiga aylanardi va
bitta tumanli mintaqaning importi umuman o'tmasdi — 118-run aynan
shu holatga tushgani uchun `degenerate` bayrog'i qo'shilgan edi.

Qolganlari: nomdagi `strip()` (OSM da `name:ru=" "` uchraydi va
bo'shliqdan iborat nom «to'liq» deb o'tardi), ko'p nuqtaning `> 10`
chegarasi (aynan o'nta yetishsa ro'yxat to'liq ko'rinishi kerak),
bo'sh partiyada nolga bo'linish qorovulining yo'nalishi (`1.0` bo'lsa
bo'sh import «100% ustma-ust» deb bloklanardi — sabab butunlay boshqa
joyni ko'rsatardi), `{total - invalid}/{total}` matni (almashsa hisobot
teskari o'qilardi) va `source_ref` ning `id` dan oldin turishi (qo'lda
tuzatish OSM identifikatoridan boshlanadi, ichki UUID importdagi faylda
yo'q).

---

## Yon natijalar

- **Ekvivalent mutant yo'q** — 118-runda boshlangan seriyada birinchi
  marta. To'rttala modul ham «qaror → natijada ko'rinadigan maydon»
  shaklida yozilgan, ya'ni 120-run ning qoidasi (survivor xossaning
  natijada ko'rinishiga bog'liq) bu yerda ijobiy tomondan tasdiqlandi.
- **124 ning «3452 yig'ildi» raqami hisoblangan, o'lchanmagan.** Shu
  run boshidagi haqiqiy son 3461 edi (o'lchandi: 3480 − 19 yangi test).
  Farq katta emas, lekin keyingi runlar `+N` arifmetikasiga tayanmasin
  — `--collect-only` bilan o'lchash 4 soniya.
- ⛔ **Disk — ketma-ket to'rtinchi run.** `/` da ~43 MB, `/sessions` da
  0. `requires_db` ning 232 testi yana jimgina `skip` bo'ldi; oxirgi
  haqiqiy o'lchov hamon 121-run. Endi bu blok **seriyani ham**
  to'xtatadi: toza modullar tugadi, keyingi nishon — servis/API qatlami
  (`stats/service.py`, `geo/queries.py`), ular bazaga tegadi.

---

## Keyingi qadam — 126-run

1. 👤 `cleanup-sessions.ps1` — endi ikki tomondan bloklovchi
   (`requires_db` ham, mutatsiya seriyasining davomi ham).
2. Disk bo'shagach: `-m requires_db` ni qayta o'lchash, keyin mutatsiya
   servis/API qatlamiga.
3. 👤 `tools/_mut.py` (`rc == 1` ga tuzatish yoki o'chirish).
4. 👤 `test_recluster_db.py` izolyatsiyasi; 👤 `ruff format` savoli.
5. 👤 serverda: eski `deploy` stekini o'chirish, `init_tls.sh`,
   polling → webhook; keyin prod tekshiruvi.

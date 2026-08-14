# 157-run — `01` §4 muvaffaqiyat metrikalari: 84-running o'lchovi rad etildi

**Sessiya:** `local_3fe5ca72-8c56-450b-935a-8f489fee9044`
**Sana:** 2026-08-14
**Epic:** REL (mutatsiya qamrovi)
**Nishon:** `app/release/success.py` (727 qator)

---

## 1. Nishon qanday tanlandi

156 qoldirgan tartibning (1) bandi: qolgan **oltita eski-harness
moduli** — `success.py` (726, 84-run «0»), `plan.py` (597, 77 «1»),
`acceptance.py` (580, 70 «0»), `gates.py` (563, 66 «1»),
`dependencies.py` (541, 76 «1»), `measures.py` (457, 67).

Nishon `PROGRESS.md` ning run jurnalidan **qayta tasdiqlandi** (152-run
sabog'i: `EpicProgress` §4 navbati eskiradi, nishon faqat jurnaldan
olinadi). Jurnalning **487-qatori**: 84-run `app/release/success.py` ni
yaratgan va o'sha running o'zida «18 mutatsiya, 0 survivor» deb yozgan.
O'sha o'lchov **tuzatilmagan harness** bilan olingan: verdikt
`returncode != 0` edi va `pytest` ning `rc=4` (bitta ham test yurmagan
run) `KILLED` deb o'qilardi; `verdict()` faqat **126-runda** tuzatilgan.
Ya'ni «0 survivor» — o'lchov emas, **tekshirilmagan da'vo**.

Oltitadan eng kattasi tanlandi: `success.py` (726 qator).

---

## 2. O'lchov: 61 mutatsiya → 27 KILLED, 34 SURVIVOR (56 %)

Seriyadagi eng yuqori survivor ulushi (oldingi rekord — 156 ning 60 % i
50 mutatsiyada; bu yerda mutlaq son ham, ulush ham kattaroq bazadan).
`rc=4` **yo'q**: 154 ning qoidasiga amal qilindi — qorovul faqat
zaiflashtiriladi, hech qachon kuchaytirilmaydi. `BADPATCH` ham yo'q
(har bir naqsh faylda aynan bir marta uchraydi — harness buni
tekshiradi).

**Verdikt butun bazasiz to'plamdan.** 156 dan farqli o'laroq bu run da
ikki bosqich **kerak bo'lmadi**: ishchi nusxada to'liq to'plam ~35 s da
yuradi, ya'ni `180 s` ichiga ikkita parallel ishchi bilan uch-uchtadan
sig'adi. Ya'ni **o'ttiz to'rtala survivor ham darhol to'liq to'plamda
(3590 test) o'lchandi — yolg'on survivor bo'lishi mumkin emas.**

Qulflar tasdiqlanganda esa tor tanlov ishlatildi: tor tanlov *yolg'on
survivor* berishi mumkin, *yolg'on KILLED* emas — ya'ni «qulf ishladi»
degan xulosa uchun u yetarli.

**Ekvivalent yo'q** — o'ttiz to'rttasi ham qulflandi.

---

## 3. Topilma (a): `_check_registry` ning o'nta shartidan oltitasi hech qachon otilmagan

Otilganlari to'rttasi: qator soni, `baseline` belgisi, «`SERVED`, lekin
dalil yo'q» va izohning majburiyligi.

🔴 **Eng qimmati — `undefined` qorovuli, va u yolg'on qulflangan edi.**
5-qatlamning parametrizatsiyasida `("K-9", {"reading": SERVED})` qatori
bor va u aynan shu qorovulni otadi deb o'ylangan. Aslida `K-9` da
`binds` **bo'sh**, ya'ni `reading` ni `SERVED` ga o'zgartirish
birinchi navbatda **boshqa** qorovulni («`SERVED`, lekin dalil yo'q»)
yiqitardi va `undefined` tarmog'iga navbat umuman kelmasdi. Ikkala
mutatsiya ham (`if False`, va shartni `is Reading.EXTERNAL` ga
almashtirish) tirik qoldi.

Qulf: `K-9` ga `reading=SERVED` **va** dalil beriladi — shunda faqat
`undefined` tarmog'i qoladi. `match=` shart.

Qolgan beshtasi:

* KPI **kodlarining** takrorlanishi (`KPI_BY_CODE` nusxa qatorni
  jimgina yutardi);
* KPI **nomlarining** takrorlanishi;
* `UNNAMED` kodlarining takrorlanishi;
* `UNNAMED` qatorining dalilsizligi;
* va **ikkala siklning to'liqligi**: `KPIS[:-1]` ham, `UNNAMED[:1]` ham
  sezilmasdi, ya'ni oxirgi KPI qatori va oxirgi ikkita teskari-yo'nalish
  qatori umuman o'lchanmasdi.

⚠️ **Uslub.** Nusxa kod qo'yish nusxa **nomni** ham qo'yadi va ikkala
qorovul birdan otiladi — mutantni faqat xabar ajratadi. Shuning uchun
qulflarda `pytest.raises(..., match=...)` majburiy, va buzilgan qator
ataylab bitta o'lchovda buziladi (kod nusxasi ↔ nom o'zgarishsiz).

⚠️ Uchta mutatsiya ro'yxatlarni `[:1]` ga qisqartirardi
(`codes`/`names`/`unnamed_codes`) — ular yuqoridagi uchta nusxa qulfi
bilan **birga** o'ladi, chunki nusxa juftligi 0- va 1-o'rinlarga
qo'yilgan.

---

## 4. Topilma (b): hisobotning shakli — 154/155/156 ning sinfi to'rtinchi marta

🔴 **Ikkita o'lik xossa.** `SuccessReport.by_target` va
`SuccessReport.disclaimed` ni **birorta kod o'qimasdi** — birinchisini
`{}` qilish, ikkinchisini `()` qilish sezilmasdi. Endi ikkalasi ham
reyestrning o'z qatorlariga qarshi yechiladi.

🔴 **Bitta o'lik konstanta.** `READING_BLOCKED` ham o'quvchisiz edi. U
endi `READING_ANSWERS` va «qarz» sinflari (`DERIVABLE`/`EMITTED`)
bilan birga **oltala sinfni bo'lib chiqadi**: javob bor / javob yozilishi
kerak bo'lgan kod / javob kod bilan yopilmaydi. Uch to'plam kesishmasin
va birlashmasi `Reading` ni bersin.

🔴 **O'q lug'ati «uchragan sinflardan» qurilsa bugun bir xil javob.**
Oltala `Reading` sinfi ham to'la, ya'ni `{reading: [] for reading in
Reading}` ni `setdefault` ga almashtirish sezilmasdi — va
`test_every_reading_class_is_used` **o'zining** ma'nosini yo'qotardi:
bo'sh chelak qurilmasa, bo'sh chelak qidirish bekor.

🔴 **`accurate` ning birinchi kon'yunkti.** 7-qatlamning
`test_each_condition_of_accurate_is_measured_separately` testi
`undefined` va `unnamed` yarmini ajratadi, `targets_are_answerable`
yarmini esa **yo'q**: bugun uchalasi ham buzilgan, ya'ni birinchi
kon'yunktni butunlay olib tashlash bir xil javob berardi. 154 ning
`boundaries_hold` i, 155 ning `accurate` i va 156 ning `gate_holds` i
bilan bitta sinf.

🔴 **`targets_are_answerable` ning manbai.** `not self.broken_promises`
ni `not self.promised` ga almashtirish bugun bir xil (har bir va'da
o'lchagichsiz) — va §4 tuzalgan kunda xossa yolg'on `False` qaytarardi.

🔴 **`is_broken_promise` ning ikkinchi kon'yunkti.** `and not
is_answerable` ni olib tashlash sezilmasdi: bugun sonli ikkala maqsad
ham javobsiz. (`and`→`or` esa ushlangan edi.)

🔴 **`answerable_but_disclaimed` ning birinchi yarmi.** Kesishmani
`answerable` filtri bilan emas, butun reyestrdan qurish bugun bir xil
javob beradi — ikkala `DISCLAIMED` qator ham `SERVED`.

🟡 **`READING_ANSWERS` ning kengayishi.** Mavjud test
`{"K-10","K-11"} <= served` deb so'raydi, ya'ni to'plamga `DERIVABLE`
yoki `EMITTED` qo'shilsa ham o'tardi. Endi tenglik so'raladi —
`{"K-3","K-10","K-11"}` (uchinchi `SERVED` qator `K-3` ekani ham shu
yerda qulflandi).

🟡 **Siyosat to'plami ↔ literal.** `self.reading in READING_ANSWERS` ni
`is Reading.SERVED` ga almashtirish bugun **ekvivalent** (to'plamda
bitta sinf bor). 155 ning retsepti: qulf `monkeypatch` bilan to'plamni
kengaytiradi va javob o'zgarishini talab qiladi. Bitta test ikkala
o'rinni ham yopadi (`Kpi.is_answerable` va `SuccessReport.answerable`).

---

## 5. Topilma (c): parser va matn konstantalari

🔴 **Parserning uchta qorovuli haqiqiy hujjatda hech qachon otilmaydi:**

* «jadval tugadi» sharti (`header is not None and rows`) — `and rows`
  yarmi sezilmasdi;
* katak sonining sarlavhaga mosligi;
* bo'limda jadval yo'qligi.

Uchalasi ham **sintetik hujjat** bilan qulflandi (`_synthetic()` —
sarlavha + tana + keyingi sarlavha).

🔴 **Sarlavha regexpining `$` langari.** `^##\s+4\.\s+Success Metrics\s*$`
dan `\s*$` ni olib tashlash sezilmasdi — reyestr `## 4. Success
Metrics — черновик` degan boshqa bo'limni o'lchay boshlardi.

🔴 **`_ROW_RE` ning `.+` i.** `.*` ga almashtirilsa `||` qator deb
o'qiladi va katak soni qorovuli otilib, bo'lim butunlay o'qilmay
qolardi.

🟡 **Uch matn konstantasi qisqartirilsa ham topilardi.** `in` tekshiruvi
bo'lakni ham o'tkazadi: `WARNING_PHRASE` → «Ни одна цифра»,
`COMMERCIAL_PHRASE` → «не описывает», `TAG_HYPOTHESIS` → «[Г» —
uchalasi ham hujjatda uchraydi va uchala test ham yashil qolardi. Qulf
kontekstni talab qiladi: jumla nuqta bilan tugasin
(`f"{WARNING_PHRASE}."`), kommersiya jumlasi qalin yopilish bilan
(`f"{COMMERCIAL_PHRASE}**."`), belgi esa teskari tirnoq ichida
(`f"`{TAG_HYPOTHESIS}`"`).

🟡 **Ikkita dalil kortejidan bittadan element jimgina tushib qolardi.**
`K-4` ning ikkala uchi (`User.created_at` **va** `Report.user_id`) —
`DERIVABLE` da'vosining o'zi; `U-3` ning ikkala sifat signali
(`obs.latency` **va** `obs.counters`). `test_all_binds_resolve` faqat
mavjud dalillarni yechadi, **yetishmasligini** ko'rmaydi (156-run ning
«mavjudlik tekshiruvi — test emas» sabog'i).

---

## 6. Qulflar

`tests/test_success_metrics_contract.py` ga yangi **8-qatlam** qo'shildi
(+26 test, 43 → 69). Yangi fayl **yaratilmadi**.

Yordamchi `_guard(kpis=..., unnamed=...)` — `_check_registry()` ni
almashtirilgan reyestr bilan qayta chaqiradi (modul darajasidagi
chaqiruv import paytida bo'lib bo'lgan).

Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar **tegilmadi**.

---

## 7. Infra

Sandbox **noldan** ko'tarildi (`/tmp` bo'sh edi):

* tizim `python3` — **3.10**, `app/admin/audit.py` esa `StrEnum` ni
  import qiladi → `micromamba` bilan `/tmp/mamba/envs/py311`
  (`conda-forge`, `python=3.11`), keyin `pip install` bir partiyada;
* `HOME`/`TMPDIR`/`PIP_CACHE_DIR` — `/tmp` ga; disk 67 % band, joy
  yetdi;
* ishchi nusxa **repo ildizidan** (`sveta/` + `*.md` + `deploy-server/`,
  33 MB) — `01_PRD_Samarkand.md` va boshqa hujjatlar testlarga kerak;
* ikkita parallel ishchi, har birida uchtadan mutant; `bash` chaqiruvi
  `timeout_ms=175000` bilan (standart 120 s bitta partiyani uzib
  qo'ydi — o'sha partiyaning ikkita mutanti keyin qayta o'lchandi).

---

## 8. Yakun

* **3616 passed, 299 skipped** (156: 3590 — aynan +26 qulf testi)
* `requires_db` 299 — **yurgizilmadi** (bazasiz o'zgarish, PostGIS
  ko'tarilmadi)
* migratsiyasiz, `ruff check app tools tests alembic` — toza
* vaqtinchalik fayl yo'q, repoda `success.py` tegilmagani `diff` bilan
  tasdiqlandi

**Keyingi qadam:** (1) qolgan **beshta** eski-harness moduli —
`plan.py` (597, 77-run «1»), `acceptance.py` (580, 70-run «0»),
`gates.py` (563, 66-run «1»), `dependencies.py` (541, 76-run «1»),
`measures.py` (457, 67-run); nishonni har safar jurnaldan tasdiqlash
shart; (2) 👤 `ruff format` ning versiya farqi (128 fayl); (3) 👤
`app.db`/`app.analytics` prefikslari; (4) 👤 `service._create_intents`
ning qaytargan qiymati; (5) 👤 `cowork_session/` nusxa juftliklari.

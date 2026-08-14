# 154-run — `01` §7 ko'lam reyestrining qorovullari va hisobot shakli (mutatsiya)

**Sessiya:** `local_60b5a524` · 2026-08-14 · rejalashtirilgan
(`sveta-net-build`).

**Natija bir qatorda:** `app/release/scope.py` (869 qator) ga **42
mutatsiya yozildi; uchtasi qorovulni kuchaytirgani uchun `rc=4` berdi va
hisobga olinmadi → 39 baholi: 22 KILLED, 17 SURVIVOR** (44 % — seriyadagi
eng yuqori ulush). O'n yettalasi butun bazasiz to'plamda birma-bir
tasdiqlandi (**yolg'on survivor yo'q**), o'n oltitasi qulflandi (**+25
test**, mavjud `tests/test_scope_contract.py` ning yangi 11-bo'limi),
bittasi **ekvivalent** deb isbotlandi. Mahsulot kodi, migratsiya,
konfiguratsiya **tegilmadi**. **3545 passed, 299 skipped**, `ruff` toza.

---

## 1. Nishon qanday tanlandi

153-run keyingi qadam sifatida «`app/release/` ning qolgan o'lchanmagan
reyestrlari; nishonni har safar jurnaldan tasdiqlash shart» ni qoldirgan
edi. Ro'yxat `PROGRESS.md` ning run jurnalidan qayta yig'ildi:

* `app/release/` da 24 modul bor;
* mutatsiya bilan **o'lchangani** — 106–116 runlarda o'n ikkitasi
  (`business_reporting`, `business_acceptance`, `business_architecture`,
  `business_glossary`, `business_environment`, `business_interfaces`,
  `business_rules`, `phase0_plan`, `business_requirements`,
  `ux_requirements`, `user_stories`, `nfr_appendix`), `gates` undan
  oldin, `risks` 153 da;
* qolganlaridan eng kattasi — **`scope.py`, 869 qator**.

⚠️ 153 ning ro'yxatida `business_acceptance.py` va `business_reporting.py`
ham «o'lchanmagan» deb turgan edi — jurnal ularni **107** va **106**
runlarda o'lchaganini ko'rsatdi. Ya'ni «keyingi qadam» ro'yxatining o'zi
ham manba emas; 151 ning qoidasi (nishonni jurnaldan tasdiqlash) yana bir
marta ish berdi.

`grep -rl "release import.*scope" tests/` → **`tests/test_scope_contract.py`**
(730 qator, 51 test) va `app/admin/registries.py`. Ya'ni 148 ning
«testda nol import» sinfi bu yerda yo'q: modul qoplangan, savol —
**nimasi** qoplangan.

## 2. O'lchov qanday olindi

* Uch ishchi nusxa (`/tmp/q1..q3`) **repo ildizidan** — `sveta/` +
  `*.md` + `deploy-server/` (147 sabog'i). Nom yangi: eski `/tmp/mNN`
  papkalari oldingi sessiya foydalanuvchisiniki bo'lib qoladi va
  o'chirilmaydi.
* Drayver `/tmp/drive154.py`: pristine nusxadan tiklash → **aynan bitta**
  moslikni almashtirish → `pytest` → verdikt **faqat `rc == 1` da
  KILLED**, `rc == 0` da SURVIVOR, boshqasi `BROKEN`.
* **Ikki bosqich.** Birinchi o'tish tor tanlovda (`test_scope_contract`,
  `test_admin_registries`, `test_admin_roles`, `test_api_requirements_contract`,
  `test_i18n_key_contract`, `test_architecture_contract` — 195 test, ~16 s):
  tanlovdagi `KILLED` — haqiqiy `KILLED`. Keyin **har bir survivor butun
  bazasiz to'plamda** (3520 test) qayta o'lchandi — 144/146 ning «tor
  tanlov yolg'on survivor beradi» sinfi shu bilan yopiladi. **O'n yetta
  survivorning o'n yettasi ham to'plamda tasdiqlandi.**
* Partiya: tanlovda 3 ishchi × 3 mutant (~60 s), to'plamda 3 ishchi ×
  2 mutant (~140 s) — 152 ning «butun to'plam bilan partiya 2 mutantdan
  oshmasin» qoidasi.
* Har partiyadan keyin `diff` bilan uchala nusxa ham pristine ekani
  tekshirildi.

**Uch mutatsiya `rc=4` berdi** (M11, M14, M36): `PHASE_ORDER.index(...)`
ni `>=` ga, `MVP_PHASES[-1]` ni `[0]` ga, `MVP_PHASES` tartibini
teskariga o'zgartirish. Uchalasi ham `MISDATED` hukmini **hisoblaydigan**
arifmetikaga tegadi va bugungi ma'lumot ularni ikkala tomondan qulflab
turibdi: hukm `later != (warrant is MISDATED)` tengligidan kelgani uchun
arifmetikaning istalgan siljishi import paytida `ScopeError` beradi.
Ya'ni bu qism **kuchaytirib bo'lmaydigan darajada qulflangan** — qoida
kuchida: qorovulni faqat zaiflashtir.

## 3. Bosh topilma — 152/153 sinfi uchinchi marta, va u ikkinchi yarmini ko'rsatdi

Modul yana ikki yarimdan iborat, lekin bu safar teskari qoplanish
**ikkita** o'qda:

**(a) `_check_registry` — o'n bir tarmoqdan oltitasi otilmagan.**
Mavjud `test_registry_rules_are_alive` to'qqizta patch bilan beshta
tarmoqni otadi; qolgan oltitasi bugungi o'n sakkiz qator to'g'ri
bo'lgani uchun umuman ishga tushmaydi:

| Tarmoq | Zaiflashtirilganda nima o'tib ketardi |
|---|---|
| gorizont faqat yechilgan havolada | `PROSE`/`FOREIGN` asosda osilgan `warrant_phase` — hech kim §3 bilan solishtira olmaydigan raqam |
| `MISDATED` ning **erta** tomoni | Ph.0/Ph.1 qatoriga `MISDATED` yozib qo'yish (kech tomonini mavjud parametrizatsiya otadi) |
| `ABSENT` + dalil + `HOLLOW` | «repoda hech narsasi yo'q» qator `hollow` ro'yxatiga tushardi va MVP ning bajarilmagan qatorlari bilan aralashardi |
| dalil talabi | `BUILT` dan boshqa to'rt sinf (`PARTIAL`, `DISPLACED`, `UNREACHABLE`, `EXTERNAL`) dalilsiz qolardi — aynan «repo nima qilgan» savoli qiyin bo'lgan sinflar |
| `UNLISTED` kodlarining nusxasi | teskari yo'nalish reyestri ham lug'at, nusxa kod qatorni jimgina yutadi |
| siklning `Standing` sharti | **ekvivalent** — quyida |

**(b) Yangi oila — hisobotning SHAKLI.** Bu 154 ning o'z hissasi va u
`_check_*` bilan bog'liq emas: `ScopeReport` ning xossalari
**bugungi qiymatlari to'g'ri bo'lgani uchun** o'lchanmay qolgan.

* `by_standing`/`by_presence`/`by_fence`/`by_warrant` — lug'atni
  «uchragan qiymatlardan» qurish bugun **aynan bir xil javob** beradi,
  chunki mavjud test faqat «hamma sinf to'lganmi» deb so'raydi. Bo'shliq
  yopilgan kuni kalit hisobotdan **yo'qolardi** va o'quvchi «bu sinf
  yo'q» bilan «bu sinfda qator yo'q» ni ajrata olmasdi (152 ning
  `counts` naqshi, endi to'rt nusxada).
* `boundaries_hold` dagi `and` → `or` — bugun sezilmaydi, chunki chegara
  **ikkala** tomondan buzilgan (`False or False` ham `False`). Bir tomoni
  tuzalgan kuni hisobot «chegara ushlab turibdi» derdi.
* `accurate` ning uchta shartidan **har birini** olib tashlash mavjud
  testdan o'tardi: u uchalasini **bir vaqtda** tuzatib, `clean.accurate is
  True` ni tekshiradi. Endi har shart yolg'iz buziladi.
* `standings_touched` ni butun reyestrdan hisoblash — bugun ham
  «uchchala ro'yxat», chunki bloklangan to'rt qator (`S-7`, `S-8`,
  `F-4`, `O-3`) allaqachon uchalasiga tegadi. Ya'ni **bosh topilmaning
  o'z o'lchovi** jimgina ma'nosini yo'qotardi.

**Ikki o'lik konstanta.** `PRESENCE_BUILT` va `PRESENCE_OUTSIDE` —
modulning e'lon qilingan tasnifi, lekin `grep` butun repoda **birorta
o'quvchi topmadi** (izohdan boshqa). Ular endi reyestrning o'z
qatorlariga qarshi yechiladi: `PARTIAL` `BUILT` da yo'q (aks holda
`S-1` — partial + hollow — invariantni buzadi), `EXTERNAL` ↔
`UNWITNESSED` bitta qaror (`S-8`).

## 4. Ekvivalent

`MISDATED` sikliga `standing is not Standing.IN` sharti qo'shish —
**ekvivalent**: `LATER`/`OUT` qatorida ustun yo'q, ya'ni `Warrant.NONE`,
va gorizont bilan birga `NONE` yuqoridagi qorovulda («gorizont faqat
yechilgan havolada») to'xtatiladi. Sikl u qatorga hech qachon yetmaydi.
Dalil izohda emas, testda:
`test_a_listed_row_can_never_reach_the_misdated_loop`.

## 5. Nima qulflandi

`tests/test_scope_contract.py` ning yangi **11-bo'limi** — 13 test
funksiyasi, parametrizatsiya bilan **+25 test** (51 → 76). Yangi fayl
yaratilmadi (130 ning qoidasi). Yordamchi `_check_with(monkeypatch, …)`:
reyestrni vaqtincha almashtirib `_check_registry()` ni **qayta
chaqiradi** — import paytidagi natijaga ishonmaydi.

Har o'n oltita survivor qayta o'lchandi: **o'n oltitasi ham KILLED**,
M17 (ekvivalent) kutilganidek SURVIVOR bo'lib qoldi.

## 6. O'lchovlar

* Bazasiz to'plam: **3545 passed, 299 skipped** (153 da 3520 passed).
* `-m requires_db`: **298** — bu runda yurgizilmadi, o'zgarish bazaga
  tegmaydi (test ham, modul ham `AsyncSession` ga tegmaydi).
* `ruff check .` — toza. Migratsiya yo'q. Vaqtinchalik fayl yo'q
  (drayver `/tmp` da, repoga tushmadi).

## 7. Keyingi qadam

1. `app/release/` ning qolgan o'lchanmagan reyestrlari, hajmi bo'yicha:
   `functional_requirements.py` (860), `roadmap.py` (780), `success.py`
   (726), `plan.py` (597), `acceptance.py` (580), `dependencies.py`
   (541), `measures.py` (457), `collector.py` (141). Nishonni **har
   safar jurnaldan** tasdiqlash shart.
2. 154 ning ikkinchi naqshi: `evaluate()` yoki `*Report` xossasi bor
   **har** modulda «hisobotning shakli o'lchanganmi» ni sanash — o'q
   lug'atlari, ko'p shartli xossalar, hosila ro'yxatning manbai.
3. 👤 `service._create_intents` ning qaytargan qiymati.
4. 👤 `cowork_session/` nusxa juftliklari.

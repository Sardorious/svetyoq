# 152-run — `01` §22 reyestrining qorovullari (mutatsiya qamrovi)

**Sessiya:** `local_b2e645e0` · **Sana:** 2026-08-13 · **Epic:** OBS/REL
**Nishon:** `app/obs/monitoring.py` (501 qator, hech qachon o'lchanmagan)
**Natija:** 41 mutatsiya → **22 KILLED, 19 SURVIVOR** (46 %); 19/19 qulflandi,
+22 test, mahsulot kodi tegilmadi.

---

## 1. Qayerdan boshlandi

151 qoldirgan tartibning (1) bandi: «`obs/monitoring.py` (501 qator) vaqt
yetmagani uchun 152 ning birinchi bandi». 149/150 ning qoidasi bo'yicha
nishon avval `grep` bilan tekshirildi — test qatlamidan **beshta** fayl
import qiladi (`test_logging_monitoring_contract.py`,
`test_obs_metrics.py`, `test_integrations_contract.py`,
`test_region_acceptance_contract.py`, `test_risk_register_contract.py`),
ya'ni 148 ning «nol import» sinfi bu yerda takrorlanmaydi. Nishon
o'zgartirilmadi.

## 2. Sandbox

`/sessions` yana **100 % to'la**, `/` da 659 M bo'sh — 141 ning retsepti
ishladi: `HOME`/`TMPDIR`/`XDG_CACHE_HOME` `/tmp` ga burildi va oldingi
sessiyaning `/tmp/mamba/envs/py311` muhiti **omon qolgan** (Python 3.11.15,
barcha bog'liqliklar joyida). Yangi `micromamba` o'rnatish kerak bo'lmadi.

⚠️ **Yangi qirra:** eski ishchi nusxalar (`/tmp/m1…m3`) o'tgan sessiyaning
foydalanuvchisiga tegishli va `rm -rf` ularni **o'chira olmadi** (`rsync`
`Permission denied` bilan yiqildi, `du` esa jimgina eski hajmni ko'rsatdi).
Retsept `pgdata` bilan bir xil: **har yangi sandboxda yangi nom** —
`/tmp/n1`, `/tmp/n2`, `/tmp/n3`.

Baseline: `-m "not requires_db"` → **3485 passed, 1 skipped, 298 deselected**
(41 s), ishchi nusxa repo ildizidan (`*.md` va `deploy-server` bilan,
`__pycache__` va `.git` siz — 6.6 M).

## 3. O'lchov — 147 ning ikki bosqichi

1. **Tor to'plam** (5 fayl, 169 test, ~2.7 s/mutant) — 41 mutatsiya, uch
   ishchi parallel, partiya 7 mutantdan.
2. **Butun bazasiz to'plam** (3485 test, ~58 s/mutant) — faqat survivorlar.

🔴 **Partiya hajmi qayta kalibrlandi.** Uchta ishchi **parallel** butun
to'plamni yurgizganda bitta o'tish 41 s emas, ~58–70 s bo'ladi (CPU
raqobati), ya'ni 3 mutantlik partiya 175 s limitidan oshib ketdi va
uzilgan chaqiruv ishchi nusxalarda mutant qoldirdi. Repo tegilmadi
(mutatsiya faqat `/tmp/nN` da), fayllar repodan qayta ko'chirildi.
**Yangi chegara: butun to'plam bilan partiya 2 mutantdan oshmasin.**

Ikkinchi bosqich hech bir survivorni rad etmadi: **19/19 SURVIVED** —
tor tanlov bu nishonda yolg'on bermadi.

## 4. Nima topildi

Modul ikki qismdan iborat va ular **teskari qoplangan**.

**Ma'lumot yarmi — qarzsiz.** Qatorlar, so'zma-so'z iboralar, `layer`,
`threshold`, `binds`/`near`, `STACK`, `STATE_PRECEDENCE`, `gaps`,
`blocked_by`: 22 mutatsiyadan **21 tasi birinchi o'tishda** o'ldi. Sabab —
uchala mavjud qatlam hujjatni **parse qiladi** va ro'yxat bilan
solishtiradi (61-run ning sabog'i o'z samarasini beryapti).

**Qorovullar — butunlay ochiq.** `_check_registry` (8 qorovul),
`_check_alert_cap` (3), `_check_label_exemptions` (3) import paytida
yuradi va **bugungi reyestr to'g'ri bo'lgani uchun hech qachon otilmaydi**.
Ularni zaiflashtirish butun to'plamni yashil qoldiradi:

| Mutatsiya | Nima o'tib ketardi |
|---|---|
| `codes.count(c) > 1` → `> 2` | takrorlangan talab kodi — `REQUIREMENT_BY_CODE` oxirgisini saqlaydi, birinchisiga kod orqali erishib bo'lmaydi |
| `phrase.strip()` → `phrase` | probeldan iborat matn: hujjat bilan solishtirishda «bor» ko'rinadi, hech qachon mos kelmaydi |
| `if not req.binds` → `is None` | `HELD` da'vosi kodga havolasiz (`03` §6 yumshatishi) |
| `if req.near` → `is None` | bajarilgan qatorda «eng yaqin o'lchov» — ikkiyoqlama hisobot |
| `elif req.binds` → `is None` | bajarilmagan qatorda tayanch — «yarim bajarilgan» |
| `len(set(codes)) != len(codes)` → `>` | bir xil kodli ikki to'siq `blocked_by` da ikki marta sanaladi |
| `len(why) < 40` → `< 4` | ertangi «нет данных» sabab sifatida qabul qilinadi |
| `(*binds, *near)` → `(*binds,)` | `near` ning shakli tekshirilmaydi — xato import paytida emas, kontrakt testida `AttributeError` bo'lib chiqadi |
| `len(ALERTS) != CAP` → `>` | ogohlantirish **kamayganda** cheklov endi to'sqinlik qilmaydi, reyestr esa `CONFLICTED` deb ko'rsatishda davom etadi |
| `len(ALERTS) != CAP` → `<` | **beshinchi** ogohlantirish qo'shilgan — o'sha yolg'onning ikkinchi tomoni |
| `if not conflicted` → `is None` | ziddiyatli qator yo'qolgan, `ALERT_CAP` yetim qolgan |
| `LABEL_EXEMPT` sikli → bo'sh | yozuv xatosi bilan kelgan oila nomi ro'yxatni **kengroq** ko'rsatadi va haqiqiy yorliqsiz oilani yashiradi |
| `PRODUCT_FAMILIES` sikli → bo'sh | metrika qayta nomlangan kunda `05` §10 jadvali jimgina bo'sh sanoqqa aylanadi |
| `if name in LABEL_EXEMPT` → `in ()` | **mahsulot metrikasi yorliqdan ozod qilinadi** — `01` §22 ning yagona bajarilgan qatori bo'shab qoladi |

Eng qimmat ikkitasi — `_check_alert_cap` ning `!=` si va oxirgi qator:
birinchisi hisobotni **yolg'on to'siq** bilan qoldiradi (to'siq allaqachon
buzilgan, qator hamon «spetsifikatsiya to'sqinlik qilyapti» deydi),
ikkinchisi esa `region` yorlig'i talabini — ya'ni butun modulning yagona
`HELD` qatorini — ichkaridan bo'shatadi.

**Uchta survivor qorovul emas, hisobot arifmetikasi:**

* `counts` da `+= 1` → `= 1`: bugun har holatdan **aynan bittasi** bor,
  ya'ni farq ko'rinmaydi (143 ning «shart to'g'ri, uni ajratadigan holat
  fikstyurada yo'q» naqshi);
* `counts` ni `State` o'rniga **uchragan** holatlardan qurish: bugun
  to'rtala holat ham reyestrda bor, ya'ni **bugun ekvivalent**; bo'shliq
  yopilgan kuni kalit hisobotdan yo'qolardi va grafik «nol» ni
  «o'lchanmagan» dan ajrata olmasdi;
* `STATE_OF_UNBLOCK` ning `E17 → BLOCKED` qatori: `mahalla_unmatched_alert`
  da `SPEC` to'sig'i ham bor, precedence baribir `CONFLICTED` beradi —
  farq faqat `Obstacle.state` ning o'zida ko'rinadi.

**Yana ikkitasi — hujjat manzili.** `SPEC` va `ALERT_CAP_SPEC`
konstantalari hech qachon solishtirilmagan: `01 §22` → `01 §21`
almashuvi hech qayerda ko'rinmasdi va keyingi o'quvchini boshqa
bo'limga olib borardi.

## 5. Qulflar

Yangi fayl **yaratilmadi** — `tests/test_logging_monitoring_contract.py`
ga **4-qatlam** qo'shildi (+22 test, 151 ning naqshi): reyestr
`monkeypatch` bilan almashtiriladi va tekshiruvchi **qayta chaqiriladi**
(`mon._check_registry()` va h.k.), `pytest.raises(ValueError, match=…)`
bilan. Import-vaqt invariantini test verdikti sifatida o'lchashning
yagona yo'li shu (127/150/151 sinfi).

Yordamchilar `_requirement()` / `_obstacle()` — sintetik qator quruvchi;
`_WHY` va `_SHORT_WHY` chegaraning ikki tomonida turadi va buni alohida
test tekshiradi (aks holda «qisqa sabab» testi bo'sh o'lchardi).

Qayta o'lchov: **19 dan 19 tasi KILLED**.

## 6. Bitta xato mutatsiya

`G13` ning birinchi varianti (`if name not in metrics.FAMILY_BY_NAME:` →
`if name not in ():`) qorovulni **kuchaytirardi** — har nom xato bo'lib,
import yiqilardi (`rc=4`, o'lchov emas). Qayta yozildi: siklning o'zi
bo'shatildi (`for name in PRODUCT_FAMILIES:` → `for name in ():`).
Qoida: **qorovul mutatsiyasi faqat zaiflashtirish yo'nalishida** —
kuchaytirish import xatosini beradi va verdikt o'rniga shovqin qoldiradi.

## 7. O'lchovlar

* butun bazasiz to'plam: **3507 passed, 1 skipped, 298 deselected** (+22)
* `requires_db`: **298** — yurgizilmadi (o'zgarish bazaga tegmaydi,
  `deselected` soni bilan tasdiqlangan)
* `ruff check .` — toza; migratsiya yo'q; vaqtinchalik fayl yo'q
* o'zgargan yagona kod fayli: `sveta/tests/test_logging_monitoring_contract.py`

## 8. 153 uchun tartib

1. Mutatsiya nishoni — `app/release/` ning hali o'lchanmagan reyestri.
   Nishonni **`PROGRESS.md` run jurnalidan** tasdiqlab olish shart
   (`EpicProgress` §4 navbati 130-runda qotib qolgan).
2. Bu run ning naqshini boshqa modullarga sinash: `_check_*` funksiyasi
   bor har modulda o'n barobar qarz kutiladi — qorovullar bugungi
   to'g'ri ma'lumotda **hech qachon otilmaydi**.

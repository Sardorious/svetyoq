# 204-run — kesim xulosasi: jimlik endi javob emas

**Sessiya:** `local_be3260ae` · **Sana:** 2026-08-21 · **Epic:** E14 (TZ §12
tekshiruvi, `tools/tz_check.py`)

Bu fayl — running **qisqa bayoni**: qaror, sabab va rad etilgan variantlar.
Batafsil holat `sveta/PROGRESS.md` da.

---

## Qayerdan boshlandi

203-run ikkita qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — **hamon
   bloklangan**: `/` da 71 MB, `/sessions` da 125 MB bo'sh joy.
2. `render()` ning **oxirgi** ichki f-satri — `cutoff_decides` qatori.

Ikkinchisi bloklanmagan, shu olindi. Bu 201 (`district_line`), 202
(`city_line`) va 203 (`level_line`) qilgan ishning **to'rtinchi va oxirgi**
nusxasi: shundan keyin `render()` da o'lchov haqidagi bitta ham f-satr
qolmadi (qolgani — argumentlarni qaytarib aytadigan sarlavha va yakuniy
holat qatori).

Qator butunlay o'lchanmagan edi: `grep` `javob kesimga bog'liq` iborasiga
testlarda birorta murojaat topmasdi. `levels_in_dispute` va
`verdicts_differ` modulda tekshirilgan, ularning **matni** — hech qayerda.

## Topilgan nuqsonlar

### 🔴 Qatorning yo'qligi ikki xil narsani anglatardi

Qator faqat `cutoff_decides` rost bo'lganda chiqardi. Ya'ni uning
yo'qligi ikkita **butunlay boshqa** javobni bildirardi:

| Holat | Nima bo'lgan | Odam nima o'qiydi |
|---|---|---|
| ikkala kesim ham o'lchandi, javob bir xil | o'lchangan, quvontiradigan natija | jimlik |
| ikkala kesim ham son bermadi (`UNKNOWN`) | kesimning ta'siri **umuman o'lchanmadi** | o'sha jimlik |

Ikkinchisida `verdicts_differ` yolg'on (`UNKNOWN is UNKNOWN`) va
`levels_in_dispute` bo'sh (`levels` ikkala tomonda ham bo'sh), ya'ni
`cutoff_decides` ham yolg'on — va §2.1 bo'limi **jim** qolardi. Holbuki
o'zgaradigan javobning o'zi yo'q edi.

Bu loyihaning takrorlanuvchi minasi: bo'sh gistogramma (203),
bo'sh maxraj (196), bo'sh sukut (`empty default eats the denominator`).
Har safar bir xil shakl — **o'lchovning yo'qligi o'lchangan javobga
o'xshab ko'rinadi**.

Endi qator har doim chiqadi va uchta sarlavhaning bittasini oladi:

```
  🔴 javob kesimga bog'liq: ...      # cutoff_decides
  kesim javobni o'zgartirmaydi: ...  # o'lchandi, rozi
  kesimning ta'siri o'lchanmadi: ... # ikkala tomon ham son bermadi
```

Tartib muhim va testda qulflangan: `cutoff_decides` **birinchi**
tekshiriladi, chunki «erta o'lchandi, kech o'lchanmadi» ham kesimning
qarori (javob kesim bilan yo'qoladi) va u 🔴 siz qolmasligi kerak.

### 🔴 `darajalar: -` ham ikki xil narsani anglatardi

`levels_in_dispute` faqat **ikkala** o'lchovda ham bor darajani
solishtiradi (bu to'g'ri: bir tomonda daraja yo'q bo'lsa farq ziddiyat
emas, o'lchanmaganlik). Lekin `UNKNOWN` da `levels` bo'sh, ya'ni bir tomon
o'lchanmagan bo'lsa ro'yxat **har doim** bo'sh chiqadi va eski
`... or "-"` uni «hech bir daraja qarshilik qilmadi» degan tinchlantiruvchi
javob bilan bir xil yozardi.

`NO_DISPUTED_LEVELS` (`-`, solishtirildi va rozi) va
`LEVELS_NOT_COMPARABLE` (`solishtirib bo'lmadi`) ajratildi.

### 🔴 Hisobotdagi yagona Python literali shu qatorda edi

`verdikt farqi {report.reach.verdicts_differ}` → `True` yoki `False`.
Qolgan hamma bayroq bu asbobda so'z bilan yoziladi (`DECIDER_LABEL`,
`HIGH_LABEL`, `OVER_CAPACITY_LABEL`, `CONFLICT_LABEL`) va sabab bir xil:
`False` qaysi savolga javob berayotganini aytmaydi.

Bu yerda u aldamchi ham edi: qator 🔴 bilan boshlanib
`verdikt farqi False` deb tugardi — holbuki o'sha holatda 🔴 ni
**darajalar** keltirib chiqargan bo'ladi. `DIFFER_LABEL`:
`verdikt: bir xil` ↔ `verdikt: FARQ`.

### 🔴 Haqiqiy `measure()` ziddiyatni bitta darajaga qamay olmaydi

Yangi `one_reach()` fikstyurasi shundan: `tzreach.measure()` uchala
darajani ham **birga** o'zgartiradi (`full()` da hammasi yetadi,
`short()` da hech biri), ya'ni «uy va mahalla rozi emas, kvartal rozi»
degan holatni undan yasab bo'lmaydi. Aynan o'sha holat esa ro'yxatning
`LEVEL_ORDER` tartibini va **rozi** darajaning ro'yxatga tushmasligini
o'lchaydi. `one_district`/`one_city`/`one_level` bilan bir xil sabab.

`flip(level, high=…)` da `looks_high` qo'lda berilmaydi (u `tzreach` ning
qoidasi): to'qqizta hodisadan to'rttasi yetsa porog yuqori, beshtasi yetsa
yo'q — maxraj ikkala holatda ham bir xil, ya'ni ziddiyat maxrajdan emas,
xulosadan keladi.

## Rad etilgan variantlar

* **Sababni (`Reason`) kesim qatoriga qo'shish.** Ikkala kesim ham
  `UNKNOWN` bo'lganda sabablari har xil bo'lishi mumkin
  (`no_history` ↔ `no_independent_truth`), lekin sabab **bitta
  o'lchovniki**, ya'ni uning joyi `reach_head_line()` — har kesimning o'z
  qatorida. Qatorga ko'chirish bir sonni ikki joyda haqiqat qilardi
  (202-run rad etgan `"city": {...}` bilan bir xil sabab).
* **`cutoff_decides` ni `reason` ga ham sezgir qilish.** Ikkala tomon ham
  `UNKNOWN` bo'lsa, sababi har xil bo'lsa ham, **javob** o'zgarmagan
  (ikkalasi ham «bilmayman»). Uni topilmaga aylantirish `findings` va
  `status` ni o'zgartirardi, holbuki bu §12 ning savoli emas. Qator uni
  `CUTOFF_UNMEASURED_HEAD` bilan aytadi — bu yetarli.
* **`darajalar:` bo'lagini o'lchanmagan holatda tashlab ketish.**
  Bo'lakning yo'qligi yana jimlik bo'lardi — shu runda tuzatilgan
  minaning nusxasi.

## Natija

`tools/tz_check.py`: `DIFFER_LABEL`, `CUTOFF_DECIDES_HEAD`,
`CUTOFF_STABLE_HEAD`, `CUTOFF_UNMEASURED_HEAD`, `NO_DISPUTED_LEVELS`,
`LEVELS_NOT_COMPARABLE`, `disputed_levels_text()`, `cutoff_head()`,
`cutoff_line()`; `render()` endi kesim xulosasini o'zi yasamaydi va uni
**shartsiz** qo'shadi.

`tests/test_tz_check.py`: `flip()` va `one_reach()` fikstyuralari,
o'nta test (faylda 70 → 82; parametrlar bilan +12).

**4963 passed, 409 skipped** (edi 4951/409), `ruff` toza,
migratsiya/sozlama/i18n/API yo'q. **19 mutant — 19 KILLED**, ekvivalent
yo'q.

Mutantlar: sarlavha tanlashning beshta buzilishi (shu jumladan eski
«faqat ziddiyatda chiqadi» regressiyasi va tartibning almashuvi),
daraja ro'yxatining beshtasi (ikkala bo'sh javobning birlashishi,
qorovullar tartibi, faqat birinchi darajani nomlash, ro'yxatni erta
kesimdan olish), qatorning to'rttasi, konstantalarning uchtasi
(`DIFFER_LABEL` almashuvi, ikkita bo'sh javobning tenglashishi,
ikkita sarlavhaning tenglashishi) va `render()` ning ikkitasi.

## Sandbox

`/` 100 % (71 MB), `/sessions` 99 % (125 MB) to'la; `/dev/shm` bo'sh
(512 MB) va **har bash chaqiruvida tozalanadi**. 203-run ning retsepti
o'zgarmadi: `tar` bilan `/dev/shm/w204` ga nusxa (7,6 s), muhit
`/tmp/mamba/envs/py311`, `TMPDIR=/dev/shm/t204`, **nusxa + o'lchov bitta
chaqiruvda**.

⚠️ **`ruff check .` + to'liq to'plamni bitta chaqiruvga birlashtirgan
urinish 178 s da uzildi**, holbuki alohida ikkovi 3 s + 54 s. Sabab
tekshirilmadi (ehtimol `ruff` mount ustida emas, nusxada ham sekin
kollektsiya qiladi); amaliy xulosa — ularni birlashtirmaslik.

Mutatsiya o'lchovi bu safar **bitta bosqichda** o'tdi: o'n to'qqizala
mutant `tests/test_tz_check.py` ning o'zida (0,4 s) o'ldi. Tor tanlovda
o'lgan mutant to'liq to'plamda ham o'ladi (tanlov — to'plamning qismi),
ya'ni ikkinchi bosqich kerak emas. Qoida faqat **survivor** ga tegishli:
tor tanlovdagi survivor to'liq to'plamda tasdiqlanishi shart.

## Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish (bloklangan).
2. `render()` ning **yakuniy bloki** — `holat: {status} (chiqish kodi N)`
   va topilmalar ro'yxati. Qolgan yagona o'lchanmagan shakl:
   `topilma yo'q` — inline literal (konstanta emas), yagona da'vosi
   `"topilma yo'q" in text`, ya'ni bo'lakning **borligini** o'lchaydi;
   `holat:` qatori esa chiqish kodini olib yuradi (asbobning
   mashina o'qiydigan verdikti) va uning shakli hech qayerda
   qulflanmagan.

# 62-sessiya — E6: parametr ssenariylari (`--set`) va ikki yurishni taqqoslash

**Sana:** 2026-08-09
**Sessiya:** `local_9b176a34`
**Epic:** E6 (retrospektiv qayta hisoblash) · qo'shimcha: `app/geo/queries.py`
**Natija:** `pytest -m "not requires_db"` → **1470 passed, 1 skipped**;
`requires_db` **215** (+3); `ruff check app tools tests alembic` → toza;
migratsiya **yo'q**.

---

## 1. Nima uchun aynan shu ish

61-run bilan kontrakt qatlami tugadi (`05` ham, `06` ham to'liq bog'landi) va
INDEX ning «Qayerda to'xtadik» qatori keyingi run uchun ikkita bloklanmagan
nomzod qoldirgan edi: **E6** yoki E14 vitrinasi backendi. E6 tanlandi, chunki
unda **funksional bo'shliq** bor edi, sifat bo'shlig'i emas.

`04` §E6 ning ta'rifi — «**parametr o'zgarishi** tarixiy ma'lumotda qayta
hisoblanadi». `tools/recluster.py` esa oynani faqat **joriy** parametrlar bilan
qayta hisoblardi: CLI da `--from`, `--to`, `--apply` dan boshqa hech narsa
yo'q edi. Ya'ni asbob «bugungi kod o'sha oynani qanday hisoblagan bo'lardi?»
degan savolga javob berardi, «**boshqa** parametrda nima bo'lardi?» degan
savolga esa yo'q — aynan o'sha savol uchun yozilgan bo'lsa ham (fayl
docstringi: «E11 da ular o'zgaradi va savol tug'iladi: o'sha paytda nima
bo'lardi?»).

Bu E11 ni to'g'ridan-to'g'ri bloklaydi: `04` da `E11 → E10, E6` va E11 ning
qabul mezoni «qayta hisoblashda barqaror natija». Parametr surib ko'rilmasa,
sozlashning o'zi mumkin emas.

## 2. Qanday qilindi

### 2.1 Yozish nuqtasi — `region_config`, argument emas

Parametrni `assign`/`evaluate` ga argument sifatida uzatish mumkin edi, lekin
qilinmadi. Sabab: `06` §9 ning qoidasi — **barcha qiymatlar bazada, mintaqa
kesimida**, va `app.clustering._load_params` ularni har baholashda o'zi
o'qiydi. Asbob uchun ikkinchi yo'l ochish onlayn yo'l bilan ssenariy yo'lini
ajratib yuborardi: ssenariy «boshqa kodni» sinab ko'rgan bo'lardi.

Shuning uchun override **tranzaksiya ichida** `region_config` ga yoziladi va
klasterlash uni odatdagidek bazadan o'qiydi. Quruq yurish rollback qiladi —
ssenariy prod konfiguratsiyasiga tegmaydi.

Yangi funksiya `app/geo/queries.py` da (modul chegarasi: `region_config` —
`app.geo` ning jadvali):

```python
async def override_region_config(session, region_id, values) -> int
```

U `tools/region_admin.py` dagi `_seed_config` dan **ataylab farq qiladi**:
seed mavjud kalitga tegmaydi (E11 da qo'lda sozlangan qiymatni asbob jim
tiklashi eng yomon kutilmagan holat bo'lardi), bu esa aynan uni bosadi.
`commit` shu yerda qilinmaydi — chaqiruvchining tranzaksiyasi hal qiladi.

### 2.2 Bir yurish emas, ikkita

`--set` yoki `--params` berilsa, asbob **ayni o'sha oynani ikki marta**
yurgizadi: bazaviy (bazadagi konfiguratsiya) va variant (override bilan).
Bitta yurishning o'zi yetarli emas — «boshqacha chiqdi» deb aytish uchun ayni
o'sha oynadagi bazaviy natija kerak, aks holda farq parametrdan emas, oynani
tanlashdan kelib chiqqan bo'lishi mumkin.

Ikkalasi ham rollback qilinadi → `--set` bilan `--apply` **birga berilmaydi**
(`EXIT_USAGE`). Parametrni prodda o'zgartirish alohida qaror va alohida asbob.
Tartib xabarda yozilgan: ssenariy → `region_admin config --set` → `--apply`.

### 2.3 «O'zgardimi?» va «nimasi bilan?»

Ikki xil savol, ikki xil artefakt:

- **`fingerprint`** (allaqachon bor edi) — «bir xilmi?»;
- **`Summary`** (yangi) — hodisalar soni, status va masshtab kesimi, o'rtacha
  ishonch va radius. «Nimasi bilan farq qiladi?»

`Comparison.changed` **izga** qaraydi, kesimga emas. Bu tafsilot mutatsiya
bilan aniqlandi (§4): kesim teng bo'lsa ham natija boshqacha bo'lishi mumkin —
`Summary` da koordinata yo'q, ya'ni bir xil sondagi va bir xil statusdagi
hodisalar **boshqa joyda** turgan bo'lishi mumkin. Kesimga qaraganda parametr
hodisalarni xaritada ko'chirib yuborgani hisobotda ko'rinmasdi.

Chiqish: JSON (`baseline` / `variant` / `delta` / `changed`) **va** odam
o'qiydigan jadval — ssenariyni odam baholaydi.

### 2.4 Notanish kalit — xato, e'tiborsiz emas

Eng muhim qattiqlik shu. `--set confirm.min_user=4` (bitta harf yetishmaydi)
jimgina o'tkazib yuborilsa, asbob **bazaviy yurishni ikki marta** bajarib
«farq yo'q» deb yozardi — E11 da bu «bu parametrni sozlash befoyda» degan
soxta xulosa. Shuning uchun kalit `DEFAULTS` (= `06` §9 jadvali) ro'yxatida
bo'lishi shart, xato xabarida esa yaqin kalitlar taklif qilinadi.
Shu mantiqdan: takrorlangan `--set` ham xato (oxirgisi jim yutsa, hisobotda
qaysi qiymat ishlagani ko'rinmasdi), son bo'lmagan qiymat ham.

## 3. Fayllar

| Fayl | O'zgarish |
|---|---|
| `app/geo/queries.py` | `override_region_config` (upsert, commit qilmaydi) |
| `tools/recluster.py` | `OverrideError`, `parse_override`, `parse_override_args`, `load_override_file`, `collect_overrides`, `Summary`, `Comparison`, `render_comparison`, `recluster(..., overrides=)`, `_one_run`, `--set`/`--params` |
| `tests/test_recluster_scenario.py` | **yangi**, 24 test (bazasiz) |
| `tests/test_recluster_db.py` | +3 `requires_db` test, teardownda `region_config` |
| `tools/README.md` | `## recluster.py` bo'limi (avval faqat jadval qatori bor edi) |

Migratsiya kerak emas: `region_config` allaqachon `0002` da.

## 4. Mutatsiyalar — 12 ta, ikkitasi sabab bo'ldi

Qoida (60-rundan): 5 tadan, har to'plamdan keyin `git status --porcelain`.
Bajarildi; ifloslangan fayl qolmadi.

| # | Mutatsiya | Natija |
|---|---|---|
| 1 | notanish kalit tekshiruvi olib tashlandi | ✅ |
| 2 | takrorlangan `--set` da oxirgisi yutadi | ✅ |
| 3 | `mean_confidence` — yig'indi, o'rtacha emas | ✅ |
| 4 | `changed` izni emas, **kesimni** solishtiradi | 🔴 **o'tib ketdi** → yangi test |
| 5 | fayl buyruq qatoridan ustun turadi | ✅ |
| 6 | `--set` + `--apply` to'sig'i olib tashlandi | ✅ |
| 7 | `delta` = bazaviy − variant | ✅ |
| 8 | «hech narsa o'zgarmadi» ogohlantirishi olib tashlandi | ✅ |
| 9 | `confirmed` hamma hodisani sanaydi | ✅ |
| 10 | son bo'lmagan qiymat `DEFAULTS` ga tushadi | ✅ |
| 11 | `Result` ga `summary` berilmaydi | ⚪ **chegara** (quyida) |
| 12 | `by_scale` to'ldirilmaydi | ✅ |

**4-mutatsiya — haqiqiy bo'shliq edi.** Fikstura tasodifan shunday tuzilgan
ediki, bazaviy va variant **ham** izi bilan, **ham** kesimi bilan farq qilardi
— ya'ni testlar ikkalasidan qaysi biri mezon ekanini ajratmasdi. Yangi test
(`test_changed_is_decided_by_the_fingerprint_not_by_the_summary`) aynan shu
holatni quradi: kesim **teng**, iz **har xil** → `changed is True`.

**11-mutatsiya — chegara, survivor emas.** `recluster()` dan
`summary=Summary.of(rows_out)` olib tashlansa bazasiz testlar yiqilmaydi,
chunki funksiya sessiya talab qiladi. Uni `requires_db` testi qulflaydi:
`test_overrides_reach_the_clustering_module` da `lax.summary.confirmed >= 1`
bo'sh `Summary()` bilan yiqiladi. Ya'ni qulf bor, u faqat CI da yuriladi.

## 5. Bazali testlar (CI da tekshiriladi)

| Test | Nimani isbotlaydi |
|---|---|
| `test_overrides_reach_the_clustering_module` | Ikki chekka ssenariy: `confirm.* = 1` da kamida bitta hodisa tasdiqlanadi, `= 99` da birortasi ham tasdiqlanmaydi; izlar har xil, hodisalar soni bir xil (farq faqat statusda) |
| `test_scenario_never_touches_the_stored_configuration` | Quruq ssenariydan keyin `region_config` o'zgarmagan |
| `test_empty_overrides_reproduce_the_baseline` | Bo'sh override — bazaviy yurishning o'zi (taqqoslashning nol nuqtasi) |

Chekka qiymatlar ataylab olindi: standart parametrda natija seedga bog'liq
bo'lardi va test o'zi o'lchamoqchi bo'lgan narsadan boshqa sababga ko'ra
yiqilishi mumkin edi.

## 6. Rad etilganlar

- **Parametrni `assign`/`evaluate` ga argument sifatida uzatish** — §2.1.
- **`--compare` alohida bayrog'i** — override berilgan payt taqqoslash
  **har doim** kerak, ya'ni bayroq faqat noto'g'ri ishlatish imkonini
  qo'shardi.
- **`--set` + `--apply` ni ruxsat etib, parametrni ham yozib qo'yish** —
  konfiguratsiyaning jim o'zgarishi; `region_admin` ning mas'uliyati.
- **`--set` bilan bir necha ssenariyni ketma-ket yurgizish (sweep)** —
  alohida ish; hozir bitta variant, chunki hisobotning o'qilishi shunda
  aniq qoladi.

## 7. Keyingi qadam

E6 ning `04` dagi ta'rifi endi to'liq bajarildi, lekin epic ✅ bo'lolmaydi:
`requires_db` testlari **CI da hech qachon yurmagan** (56-runda birinchi
marta yurdi va hammasi bitta sababdan yiqildi; `NullPool` tuzatishi hali
commit qilinmagan). Bloklanmagan keyingi nomzodlar o'zgarmadi: **E14
vitrinasi backendi** yoki E6 ustidagi sweep.

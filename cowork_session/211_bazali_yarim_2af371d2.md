# 211-run — bazaga bog'liq yarmi ham o'lchandi: `run()` va `collect()`

**Sessiya:** `local_2af371d2` · **Sana:** 2026-08-21 · **Epic:** E14 / TZ §12

---

## Qayerdan boshlandi

210-run uchta qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — sandboxda PostGIS
   yo'q, ko'tarish alohida running ishi;
2. `run()` ning qolgan «uchta SQL qatori» uchun test;
3. 👤 `make lint` ning `ruff format --check` qadami (119-rundan beri ochiq
   savol, odam qaroriga bog'liq).

Bloklanmagani — ikkinchisi. Boshlang'ich holat: **5045 passed, 409 skipped**,
`ruff` toza.

Sandbox 209-rundan tirik qolgan: `/tmp/mamba/envs/py311` joyida,
`micromamba` qayta yuklanmadi. `/sessions` 99 % to'la (123 MB), `/` da 3.1 GB
bo'sh — nusxa va to'plam `/tmp` da yuritildi (to'liq to'plam 59 s).

---

## 🔴 209-running xulosasi haqiqatning yarmi edi

209-run yetkazishni `run()` dan chiqarib, qolgan qismni «uchta qatorlik SQL»
deb yozgan va bu yarimni yopilgan deb hisoblagan edi. Uning sababi shunday
yozilgan:

> Sandboxda `run()` yurmaydi, ya'ni uning ichiga qo'yilgan **har qanday**
> qaror o'lchovsiz bo'ladi.

Sabab noto'g'ri nomlangan. Qaror bazaga bog'liq bo'lgani uchun emas, uni
**ajratadigan fikstyura yo'q** bo'lgani uchun o'lchovsiz edi. Uchta so'rovning
atrofida to'rtta qaror qolgan va ularning birortasi ham 5045 testda
o'lchanmasdi:

* qaysi kesim qaysi maydonga tushadi;
* oyna va sozlamaning qaysi soni `tzreach.load()` ning qaysi parametriga
  boradi;
* mintaqa **kodi** bilan qidiriladimi va hisobotga kod tushadimi;
* hisobot qurilmaganining ikkita sababi ajratilgan qoladimi.

O'lchov qanday qurildi — `session_scope()` ning o'rniga so'rovni **yozib
oladigan** fikstyura. `requires_db` **ishlatilmadi** ataylab: sandboxda u
`skip` bo'ladi, ya'ni yozilgan da'vo o'lchamaydi, faqat o'lchagandek
ko'rinadi.

Fikstyuraning xavfi ma'lum — javobni o'ylab topgan soxta baza hech narsani
o'lchamaydi. Shuning uchun ikkita qoida:

1. **So'rovning o'zi saqlanadi va unga ham da'vo qo'yiladi.**
2. **Tekshiruv SQL matnidan emas, bog'langan parametridan olinadi:**
   `statement.compile().params == {"code_1": "jizzax"}`. Kalitning nomi
   ustundan yasaladi, ya'ni `Region.name_uz` ga o'tgan mutant boshqa kalit
   bilan yiqiladi — matn qidiradigan da'vo buni ko'rmasdi.

---

## 🔴 Asosiy topilma: juftlik ro'yxatning tartibi bilan yig'ilardi

```python
pair: list[tzreach.Reachability] = []
for cutoff in (cuts.early, cuts.late):
    ...
    pair.append(tzreach.measure(...))
...
reach=ReachPair(early=pair[0], late=pair[1]),
```

Ro'yxatning tartibi bilan maydonlarning nomi orasida hech qanday bog'liqlik
yo'q edi. Almashtirgan mutant **jim** bo'lardi:

* hisobotning ikkala qatori ham to'ladi;
* `verdicts_differ` simmetrik (`early.verdict is not late.verdict`);
* `levels_in_dispute` ham simmetrik;
* ya'ni §2.1 ning butun xulosasi — «javob kesimga bog'liqmi» — o'zgarmaydi.

Faqat «erta» yorlig'i ostida kech kesimning javobi turardi. Va bu ataylab
tanlangan yorliq: modul izohining birinchi 🔴 si aytadi, kech kesim
poroglarni **erishuvchanroq** ko'rsatadi. Ya'ni almashuv §12 ni aynan o'zi
so'ragan tomonga og'dirardi — «пороги не завышены» degan xulosa jimgina
qulaylashardi.

**Tuzatish:** o'lchov o'zini yasagan kesim bilan **kalitlanadi**, o'rni bilan
emas:

```python
measured: dict[datetime, tzreach.Reachability] = {}
for cutoff in (cuts.early, cuts.late):
    ...
    measured[cutoff] = tzreach.measure(...)
...
reach=ReachPair(early=measured[cuts.early], late=measured[cuts.late]),
```

Kalit ishonchli: `cutoffs()` `until <= since` ni xato deb rad etadi, ya'ni
`early` va `late` hech qachon teng bo'lmaydi va lug'atda ikkita yozuv qoladi.

**Fikstyura ham ajratishi shart.** Ikkala kesimga bir xil tarix beradigan
fikstyurada almashuv baribir ko'rinmasdi — 203-running darsi: *fikstyura
ajratmasa, qulf yo'q*. Shuning uchun `db_half(history={...})` kesim → tarix
xaritasini oladi va soxta `tzreach.load` «qaysi kesim so'ralgan bo'lsa,
o'shaning tarixi» ni qaytaradi. Bittasida maxraj yetmaydi
(`TOO_FEW_EPISODES`), ikkinchisida yetadi.

---

## 🔴 `min_trust_score` ↔ `min_account_age_min`

Ikkovi ham `settings` dan olinadi, ikkovi ham `int`, va bir-birining o'rniga
tushganda hech narsa yiqilmasdi: birinchisi ishonch balliga, ikkinchisi kesim
sanasiga boradi — almashuv o'lchovning **ikkala** yarmini ham jimgina
siljitardi.

Fikstyurada sonlar ataylab har xil va ikkovi ham sukut qiymatdan
(`30` / `10`) farq qiladi: `TRUST = 77`, `AGE = 33`. Uchinchi son
(`EPISODES = 2`) `Invocation` dan keladi, `settings` dan emas —
`tzreach.measure` izohi buni talab qiladi («son §7 da yo'q, ya'ni uni kodda
tanlab qo'yish Т-1 ni buzardi»).

Ikkita o'qish bitta literal jadval bilan qulflandi:

```python
assert seen.reach[0] == {
    "region_id": REGION_ID, "since": SINCE, "until": UNTIL,
    "kind": KIND_OUTAGE, "min_trust_score": TRUST,
    "account_created_before": CUTS.early,
}
assert seen.reach[1] == seen.reach[0] | {"account_created_before": CUTS.late}
```

Ikkinchi qator farqni **bitta** kalitga qamaydi: ikkinchi o'qishni
birinchisining nusxasi qilgan mutant (bir xil kesim) `cutoff_decides` ni hech
qachon yondirmaydigan asbob yasardi — ikkita bir xil o'lchov har doim rozi
bo'ladi.

---

## 🔴 Ikkita rad javobi

`REGION_MISSING` va `REGION_UNCONFIGURED` izohi aytadi: «uchalasi ham bitta
satr va `EXIT_ERROR` beradi, lekin matni har xil — odam qaysi to'siqqa
urilganini `$?` dan emas, shu satrdan biladi». Ajratish o'lchanmagan edi.

Ikkita da'vo qo'shildi:

* mintaqa yo'q — sozlama **umuman o'qilmaydi**
  (`(seen.config, seen.reach, seen.coverage) == ([], [], [])`). Sozlamani
  mavjud bo'lmagan mintaqa uchun o'qigan mutant «sozlanmagan» deb javob
  berardi va odam mavjud bo'lmagan `region_config` ni qidirishga ketardi;
* sozlamaning **ikkita** nuqsoni (`ConfigMissingError` ↔ `ConfigInvalidError`)
  bir xil rad javobiga olib keladi. Bittasini tutmay qoldirgan mutant `run()`
  ni izsiz yiqitardi — odam hisobot o'rniga `traceback` olardi. Kutilgan matn
  haqiqiy istisnodan olinadi (`pytest.raises(...)` → `info.value`), qotirilgan
  satrdan emas.

---

## Yana ikkita jim chok

* **Hisobotga `id` emas, kod tushadi.** `run()` ning ikkita mintaqa qiymati
  bor: qidiruv kaliti (kod) va topilgan qatorning `id` si. `id` ni yozgan
  mutant sarlavhaga `UUID` chiqarardi — odam o'qiydigan yagona joyga.
* **§3 ning yarmi `region_config` dan kelgan sozlama bilan o'lchanadi.**
  `starting_values()` runtime da chaqirilmaydi (§7), lekin fikstyurada juda
  qulay va aynan shuning uchun xavfli: sozlamani o'qimay `starting_values()`
  ga tushgan mutant sukut qiymatli mintaqada **hech qanday** farq bermasdi.
  Shuning uchun fikstyura bitta kalitni ataylab siljitadi
  (`tz.scale.city_district_min`: 3 → 4).

---

## Natija

| | |
|---|---|
| To'plam | **5057 passed, 409 skipped** (edi 5045/409, **+12**) |
| `ruff check .` | toza |
| Migratsiya / sozlama / i18n / API | yo'q |
| Yangi test fayli | yo'q — `tests/test_tz_check.py` ga **10-bo'lim** (10 funksiya, parametrlar bilan 12) |
| Kod o'zgarishi | `tools/tz_check.py`: `collect()` ning juftligi + modul izohiga yangi bo'lim |

### Mutatsiya o'lchovi — 22 mutant, 22 KILLED

Ikkinchi o'tish (10-bo'lim `-k` bilan chiqarib tashlangan): **22 tasining
hammasi omon qoladi**. Ya'ni bu yarim shu rungacha butunlay o'lchanmagan edi
— bitta ham mutant qolgan 5045 testga ilinmaydi.

| Mutant | Nima qilingan |
|---|---|
| M1 | juftlik almashtirilgan (`early=measured[cuts.late]`) |
| M2 | o'qish tartibi teskari |
| M3 / M4 | `min_trust_score` ↔ `min_account_age_min` |
| M5 | ikkala o'qish ham `cuts.early` bilan |
| M6 / M22 | hisobotga `str(region.id)` / `code.upper()` |
| M7 | mintaqa `name_uz` bo'yicha qidiriladi |
| M8 | ikkita rad javobi bitta satrga tenglashtirilgan |
| M9 | sozlama rad javobidan **oldin** o'qiladi |
| M10 | `ConfigInvalidError` tutilmaydi |
| M11 / M20 | `min_episodes` qotirilgan (`measure` da / hisobotda) |
| M12 / M15 | `since` ↔ `until` (tarix o'qishida / hisobotda) |
| M13 | `kind="restore"` |
| M14 / M19 | sozlama sukut qiymatlar bilan to'ldiriladi / qamrov sukut sozlama bilan |
| M16 / M18 | qamrov va sozlama boshqa mintaqa uchun |
| M17 | kesimlar bir daqiqaga siljigan |
| M21 | juftlikning ikkala maydoni ham `early` |

⚠️ **Harnessning eslatmasi.** Partiya uzilganda mutant nusxada qolib ketadi
(`M16`/`M19` `ANCHOR-MISSING` berdi va nusxa iflos edi — repoda emas, faqat
`/tmp/r211` da). Sabab: `python` quvurga yozganda buferlaydi, `timeout` esa
uni oxirigacha yetkazmaydi. `python -u` va partiya boshida nusxani mountdan
qayta tiklash — ikkalasi ham shart.

---

## Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — alohida run
   (`micromamba` bilan `postgis`; `/` da 3.1 GB bo'sh joy bor, `/sessions` da
   123 MB).
2. 👤 `make lint` ning `ruff format --check` qadami hamon qizil — 119-rundan
   beri ochiq savol, odam qaroriga bog'liq.
3. `tools/` dagi qolgan asboblarning bazali yarmi shu usul bilan
   o'lchanmagan: `recluster.py`, `simulate.py`, `region_admin.py`.

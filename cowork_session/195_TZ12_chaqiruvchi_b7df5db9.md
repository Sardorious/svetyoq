# 195-run — §12 ning ikkala yarmi ham chaqiruvchiga ega bo'ldi (`tools/tz_check.py`)

**Sessiya:** `local_b7df5db9` · **Sana:** 2026-08-20 · **Epic:** TZ (yangi qonun)

---

## Qayerdan boshlandi

194 ning «keyingi qadam» i bitta bloklanmagan ishni qoldirgan edi:

> §12 ning ikkala yarmi ham endi kod: qolgan ish — `tools/` da
> ikkalasini bitta hisobotga chiqaradigan skript (`tzreach.measure` +
> `tzcoverage.summary`), u §12 ni odam yuritadigan qilardi.

Birinchi tekshiruv shu da'voni tasdiqladi va uni kuchaytirdi:

```
grep -rn "tzreach\|tzcoverage" app/ tools/   # → faqat izohlarda
```

Ikkala modulga ham `app/` da **birorta chaqiruv yo'q** edi — faqat
`app/admin/registries.py` va `app/clustering/repository.py` dagi
docstring havolalari. Chaqiruvchisiz o'lchov asbobi — o'lchov emas,
imkoniyat.

---

## 🔴 Birinchi topilma: kesim sanasi javobni tanlaydi

`tzreach.load()` ning imzosi butun tarix uchun **bitta**
`account_created_before` oladi. Mahsulot esa uni har hodisada
qaytadan hisoblaydi:

```python
# app/clustering/service.py
account_created_before=now - timedelta(minutes=settings.reporter_min_account_age_min)
```

Demak tarixiy o'lchovda bu qiymatni tanlash — javobni tanlash:

| Kesim | Tarix boshidagi hodisada | Natija |
|---|---|---|
| `until - yosh` (kech) | mahsulot **rad etgan** akkauntlarni qabul qiladi | guvohlar ko'proq → poroglar erishuvchanroq |
| `since - yosh` (erta) | tarix oxirida mahsulot qabul qilganini rad etadi | poroglar yuqoriroq |

Kech kesim §12 ni aynan o'zi so'ragan tomonga og'diradi: «пороги не
завышены» degan javob jimgina qulaylashadi.

**Rad etilgan variantlar:**

1. *Kech kesimni tanlash va izohda yozib qo'yish.* Yozilgan og'ish —
   baribir og'ish; hisobotni o'qigan odam sonni ko'radi, izohni emas.
2. *`tzreach.load()` ni har hodisa uchun o'z kesimini hisoblaydigan
   qilib qayta yozish.* To'g'ri yechim, lekin u 193-run mutatsiya
   bilan o'lchagan modulning imzosini o'zgartiradi va §12 ning
   o'lchovi bilan mahsulotning filtri orasidagi «bir xil so'rov»
   kafolatiga tegadi. Bu — alohida ish, «Ochiq savollar» ga emas,
   kelajakdagi runga.
3. **Tanlangan:** o'lchov **ikki marta** yuritiladi va ikkala javob
   ham chop etiladi. Bir xil bo'lsa — kesim qaror qabul qilmagan, son
   dalil. Farq qilsa — son dalil emas, **artefakt**, va u
   `reach.cutoff_decides` topilmasi bilan (daraja nomi bilan)
   nomlanadi. Narxi — so'rovlar ikki barobar; §12 oflayn va umuman
   bir marta yuritiladi («занимает день работы с выгрузкой»).

---

## 🔴 Ikkinchi topilma: «o'lchanmadi» — «o'tdi» emas

Bugungi bazada `tzreach` `UNKNOWN`/`NO_INDEPENDENT_TRUTH` qaytaradi
(sanoqdan mustaqil dalili bor hodisa yo'q) va `levels` bo'sh.
`tzcoverage` ham foydalanuvchisi bor kvartal bo'lmasa `UNKNOWN`
beradi.

Agar chiqish kodi bunda `0` bo'lsa, «topilma yo'q» bilan «hech narsa
o'lchanmadi» bir xil ko'rinardi — bu loyihada bir necha marta uchragan
mina (bo'sh jadval, bo'sh sukut, nol maxraj). Shuning uchun:

| Kod | Ma'nosi |
|---|---|
| `0` | ikkala yarmi ham o'lchandi, topilma yo'q |
| `1` | hisobot **qurilmadi** (mintaqa yo'q, sozlanmagan, argument xato) |
| `2` | o'lchandi va topilma bor |
| `3` | yarmi (yoki ikkalasi) **o'lchanmadi** |

Ustunlik `3 > 2 > 0` — va bu shunchaki tartib emas: «topilma bor»
degan kod qolgan hamma narsa o'lchandi degan ma'noni beradi, yarmi
o'lchanmaganda esa bu ma'no yolg'on bo'ladi.

---

## Qurilgani

* **`tools/tz_check.py`** — toza yadro + IO qobig'i:
  `cutoffs()`, `ReachPair` (`verdicts_differ`, `levels_in_dispute`,
  `measured`, `cutoff_decides`), `Report` (`findings`, `status`,
  `exit_code`), `render()`, `as_json()`, `collect()`, `run()`,
  `build_parser()`, `main()`.
* **`app/clustering/tzreach.summary()`** — `tzcoverage.summary()`
  ning juftligi. Shakl chaqiruvchida emas, **modulda** yashaydi:
  chaqiruvchi tanlagan kesim `LevelResult` ga qo'shilgan navbatdagi
  maydonni jimgina tashlab ketardi.
* **`tests/test_tz_check.py`** — 40 test.
* **`tools/README.md`** — jadvalga ikkita qator (`tz_check.py` va
  yozilmay qolgan `seed_tz_config.py`) hamda to'liq bo'lim.

Qarorlar:

- **Skript hech narsa yozmaydi.** §12 ishlab chiqishdan **oldingi**
  tekshiruv; javobi §7 ning sonlarini o'zgartirishi mumkin, lekin
  o'zgartirishni odam `seed_tz_config` orqali qiladi va u
  `config_journal` da ko'rinadi. Avtomatik tuzatish o'lchovni o'z
  natijasiga bog'lardi.
- **`--min-episodes` ning sukut qiymati yo'q** — `tzreach.measure()`
  bilan bir xil sabab, va qorovul `main()` da (`< 1` → `1`).
- **`--since` majburiy, `--until` sukut bo'yicha hozir** va hisobotda
  chop etiladi. Zonasiz sana UTC deb o'qiladi: mahalliy zonada o'qish
  bir xil buyruqni ikki mashinada boshqa oynaga aylantirardi.
- **Matn i18n dan olinmaydi** — §12 foydalanuvchiga chiqmaydi.

---

## 🔴 Uchinchi topilma: mutatsiya ikkita o'lchanmagan qorovulni ochdi

14 mutant, ikki bosqichli harness (nishon fayl → `tests/test_tz_check.py`).
Birinchi o'tishda **ikkitasi omon qoldi**:

**M10 — `findings` dagi `if self.reach.measured:` teshigi.** Uni olib
tashlagan mutant birorta testni yiqitmadi, chunki `UNKNOWN` da
`Reachability.levels` **allaqachon bo'sh** — himoyani qorovul emas,
bo'sh lug'at qilardi. Qorovulning o'zi hech qachon ishlamagan va
hech qachon o'lchanmagan. Yechim — qorovulni olib tashlash **emas**
(kelajakdagi o'zgarishdan himoya bor), balki uni **ajratish**:
verdikti `UNKNOWN`, `levels` i to'la qo'lda yig'ilgan `Reachability`.

**M12 — `summary()["levels_that_look_high"]` ni `reach.levels` bilan
almashtirish.** Fikstyurada «bir daraja yuqori, boshqasi yo'q» holati
yo'q edi: mavjud testlarda yo hammasi yuqori, yo hech biri. Ajratuvchi
fikstyura — ikkita `house_only` va ikkita `short`: uy teng bo'linadi
(Т-1 bo'yicha «ko'pchilik» emas → yuqori emas), kvartal va mahalla
esa hech qachon yig'ilmaydi.

Ikkala ajratuvchi test qo'shilgandan keyin **14 mutant — 14 KILLED**.

> ⚠️ Batafsil: birinchi urinishda M9–M12 partiyasi bazaviy holat
> **qizil** bo'lganda yurgizilgan edi (yangi test o'sha paytda
> yiqilardi) va to'rttala «KILLED» ham soxta chiqdi. Partiyadan
> oldin bazaviy holatni chop etish shart.

---

## Fikstyura haqida eslatma

§2.1 ning mahalla qatori odamlarni emas, **tasdiqlangan
kvartallarni** talab qiladi (`mahalla_min_blocks=3`), kvartal esa
beshta akkauntni va uchta r10 katagini. Ya'ni eng kichik «uchala
daraja ham yetdi» hodisasi — uchta kvartal × beshta akkaunt = **15
odam**, mahalla porogi sakkiz bo'lsa ham. Birinchi urinishdagi
sakkiz odamlik fikstyura mahallani yopmadi va «topilma yo'q» holati
umuman yasalmadi.

---

## O'lchov

- `5279 passed, 2 skipped` haqiqiy bazada (PostgreSQL 18.6 +
  PostGIS 3.6.4), `requires_db` **408** (o'zgarmadi)
- `ruff check` toza, `ruff format --check` yangi fayllarda toza
- migratsiya, yangi sozlama, i18n kaliti va API **yo'q**
- 14 mutant — 14 KILLED

Sandbox eslatmasi: `initdb` + `pg_ctl start` + `alembic upgrade head`
+ `pytest` **bitta bash chaqiruvida** bo'lishi shart (server chaqiruv
oxirida o'ladi), va `/` diskda bir vaqtda faqat bitta `pgdata` uchun
joy bor (~65 MB) — eskilarini o'chirmasa `initdb` jimgina yiqiladi va
testlar `requires_db` ni `skip` qilib «yashil» ko'rinadi.

---

## Qayerda to'xtadik

§12 **kod tomondan tugadi**. Javobi endi ma'lumotga bog'liq:
`layer='official'` li hodisa bo'lmaguncha `tz_check`
`UNKNOWN`/`NO_INDEPENDENT_TRUTH` qaytaradi va bu E10 gacha
o'zgarmaydi.

👤 savol o'zgarmadi — **qaysi zonaning verdikti hodisani
tasdiqlaydi** (ulash tartibining 3-bandi).

Keyingi bloklanmagan ish: `geo.queries._geometry_facts` ning taxminiy
qamrovi. U bazada `h3` yo'qligi uchun `ST_Area / katakcha maydoni`
bilan sanaydi, ya'ni `over_capacity` «qamrov birdan katta» emas,
**taxmin noto'g'ri** degani — va bu taxminning o'z o'lchovi yo'q.

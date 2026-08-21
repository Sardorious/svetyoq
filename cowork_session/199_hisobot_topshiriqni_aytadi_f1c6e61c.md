# 199-run — hisobot endi topshiriqni aytadi

**Sessiya:** `local_f1c6e61c` · **Sana:** 2026-08-20 · **Epic:** E14
(TZ §12, `06` §3.1/§5.3)

---

## 1. Nimadan boshlandi

198-run ikkita keyingi qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini **PostGIS li bazada** yurgizish — hamon
   bloklangan: `/` da 90 MB, `/sessions` da 126 MB bo'sh joy. Baza
   ko'tarish uchun joy yo'q (`micromamba` + `postgis` bir necha yuz MB).
2. `tz_check` hisobotida `DENOMINATOR_NOT_UPPER_BOUND` ning ikki
   sababini (`estimate` ↔ `center`) ajratish — `containment` faktda
   bor, hisobot esa ikkovini bitta yorliq bilan chiqaradi.

Ikkinchisi olindi.

---

## 2. Defekt: jurnalda ikkita hodisa, hisobotda bitta bayroq

198-run `refresh_coverage` ga **ikkita ayrim** ogohlantirish qo'ygan edi
va ularni ataylab qo'shmagan — tuzatishlari har xil joyda:

| Hodisa | Nima yetishmaydi | Ish qayerda |
|---|---|---|
| `coverage.cells_estimated` | poligonning o'zi | chegara reyestri (`districts.geom`) |
| `coverage.cells_not_upper_bound` | `overlap` sanog'i | `h3` ning eksperimental API si |

`tz_check` esa o'sha ikki holatni **bitta** yorliq (MAXRAJ-O'LCHANMAGAN)
va **bitta** topilma (`coverage.capacity_unmeasured`) bilan chiqarardi.
Oqibati: odam jurnalda ikkita qatorni ko'radi, hisobotda bitta bayroqni,
va ularni bir-biriga bog'lay olmaydi — **qaysi ishni qilish kerakligi
hisobotdan umuman o'qilmaydi**. Hisobotning vazifasi esa bayroqni
ko'rsatish emas, topshiriqni aytish.

---

## 3. Qarorlar

### 3.1. Ajratuvchi belgi — `is_counted`, `is_upper_bound_safe` emas

197-run `over_capacity` ning sababini `cellfit.is_upper_bound_safe`
bilan ajratgan edi (faqat `OVERLAP` xavfsiz). Ikkala qarzda ham u
`False`, ya'ni **o'sha belgi bu ajratmani bermaydi**. Kerakli savol —
ikkinchisi: «poligon umuman o'qildimi» (`cellfit.is_counted`).

Yangi qoida yozilmadi: ikkala funksiya ham 198-runda `cellfit` da
allaqachon bor edi va `capacity_conflict` endi ikkalasini ham chaqiradi.
`Containment` ga to'rtinchi qiymat qo'shilsa javob bitta joyda o'zgaradi.

```python
if not self.over_capacity:
    return CapacityConflict.NONE
if self.containment is None:
    return CapacityConflict.DENOMINATOR_ESTIMATED
if cellfit.is_upper_bound_safe(self.containment):
    return CapacityConflict.OUTSIDE_POLYGON
if cellfit.is_counted(self.containment):
    return CapacityConflict.DENOMINATOR_NOT_UPPER_BOUND
return CapacityConflict.DENOMINATOR_ESTIMATED
```

### 3.2. Ma'nosi noma'lum son sanoq deb o'qilmaydi

`containment is None` — `RegionFacts` da «geometriya o'qilmagan».
Uni `CENTER` tomonga tushirish qarzni `h3` ga ag'darib, chegara
reyestridagi ishni ko'rinmas qilardi. Shuning uchun `ESTIMATED`.
Holat amalda kelib chiqmasligi kerak (ikkala xarita ham bitta qatordan
quriladi), lekin tipi uni taqiqlamaydi va fikstyura yasay oladi —
shuning uchun ochiq test bor.

### 3.3. Ro'yxatlar ajratildi, holat esa bitta qoldi

`Coverage` da uchta ayrim ro'yxat: `districts_outside_polygon`,
`districts_capacity_estimated`, `districts_capacity_not_upper_bound`.
Ular qo'shilmaydi — qo'shilgan son 199-run ajratgan sababni darhol
qaytarib yo'q qilardi.

`tz_check` ning `status` iga esa bitta mantiqiy javob kerak
(«hammasi o'lchandimi»), qarzning turi emas — shuning uchun
`Coverage.has_capacity_debt`. Ikkala qarz ham `UNMEASURED` beradi.

### 3.4. Nomlar — tashqi kontrakt

Enum qiymatlari jurnalning hodisalari bilan **bir xil** atalgan
(`denominator_estimated` ↔ `coverage.cells_estimated`,
`denominator_not_upper_bound` ↔ `coverage.cells_not_upper_bound`) va
literal jadval bilan qulflangan. Matn yorliqlari ham
(MAXRAJ-BAHOLANGAN / MAXRAJ-MARKAZ-BO'YICHA). Sabab — 198-running
M7 si: testlar konstantaga murojaat qilganda ikkita nomni bitta satrga
tenglashtirish **jimgina o'tadi**, amalda esa ikkala qarz bitta filtrga
tushadi.

---

## 4. O'lchov

* **4916 passed, 409 skipped** (edi 4911/409), `ruff` toza.
  To'plam mahalliy nusxada (`/dev/shm/r199`) 55 s da yurdi.
* **14 mutant — 14 KILLED.** Nishonlar: `capacity_conflict` ning
  uchala shoxi va tartibi (M1–M4), `Coverage` ning ro'yxatlari va
  `has_capacity_debt` (M5–M7), `summary()` ning kaliti (M8),
  `tz_check` ning yorlig'i, topilmalari va `status` i (M9–M12, M14),
  enum qiymatini ikkinchisiga tenglashtirish (M13 — 198-run M7 ning
  aynan takrori, bu safar darhol KILLED).
* Migratsiya, sozlama, i18n va API o'zgarmadi.

---

## 5. Muhit

`/` va `/sessions` hamon 99 % to'la, lekin `/tmp/mamba/envs/py311`
o'z joyida va ishlaydi. To'plam `/dev/shm` dagi nusxada yurgizildi:

```
tar -cf - --exclude=.git . | (cd /dev/shm/base && tar -xf -)
export TMPDIR=$W/tmp HOME=$W PATH=/tmp/mamba/envs/py311/bin:$PATH
```

⚠️ `/dev/shm` har bash chaqiruvidan keyin tozalanadi — nusxa va testlar
**bitta** chaqiruvda bo'lishi shart. Ikkita ishchi parallel (`&` + `wait`),
mutant juftligi ~9 s.

---

## 6. Repoda qolgan asbob

`sveta/scripts/mut199.py` — mutatsiya harnessi. Har run uni noldan
yozish o'rniga endi repoda turadi; jadval repo **tashqarisidagi** JSON
dan olinadi, ya'ni fayl bir runga bog'lanmagan. Verdikt faqat `rc == 1`
da `KILLED` (`rc == 4` — yig'ish xatosi, soxta KILLED beradi).

Uni o'chirish **mumkin emas** edi: mount da `rm` `Operation not
permitted` beradi, `mcp__cowork__allow_cowork_file_delete` esa odam
tasdig'ini kutadi va rejalashtirilgan runni to'xtatadi (CLAUDE.md ⛔).
Shuning uchun fayl foydali va umumiy holga keltirildi; nomini
`mutate.py` ga o'zgartirish — 👤 odamning ishi.

---

## 7. Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish (disk).
2. `tz_check --json` tuman kesimida `capacity_conflict` ni bermaydi:
   `summary()` uchta ro'yxat beradi, tuman qatorida esa sabab faqat
   **matn** yorlig'ida qoladi — mashina o'qiydigan chiqishda u yo'q.

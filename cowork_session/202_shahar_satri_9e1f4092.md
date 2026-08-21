# 202-run — shahar satri: ulush soni va qaror yorlig'i

**Sessiya:** `local_9e1f4092` · **Sana:** 2026-08-20 · **Epic:** E14 (TZ §12
tekshiruvi, `tools/tz_check.py` + `app/clustering/tzcoverage.py`)

Bu fayl — running **qisqa bayoni**: qaror, sabab va rad etilgan variantlar.
Batafsil holat `sveta/PROGRESS.md` da.

---

## Qayerdan boshlandi

201-run ikkita qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — **hamon
   bloklangan**: sandboxda `/` da 80 MB, `/sessions` da 125 MB bo'sh joy,
   PostGIS ko'tarishga yetmaydi.
2. 👤 shahar satri «qarorni kim qabul qildi» ga javob bermaydi.

Ikkinchisi bloklanmagan, shu olindi.

## Topilgan nuqson

🔴 **Bir xil savolga ikkita daraja ikki xil to'liqlikda javob berardi.**
Tuman qatori 201-rundan beri `kerak 4 (ulush 3) qaror: eng-kam-son` deydi,
shahar satri esa faqat `kerak 3` derdi. `CityReach.share_part` na matn
hisobotida, na `tzcoverage.summary()` da bor edi — ya'ni javob faqat
topilmalar ro'yxatidagi `coverage.minimum_decides:city` bayrog'ida, **sonsiz**
qolardi. Bayroq `need != share_part` ni aytadi va ikkovining qiymatini
aytmaydi: `city_need=4` ni ko'rgan skript ulush `3` mi yoki `1` mi ekanini
bilmasdi, ya'ni §7 ning qaysi sozlamasini (`city_district_share` ↔
`city_district_min`) va **qancha** o'zgartirish kerakligini ayta olmasdi.

🔴 **Sababi — shakl chaqiruvchida.** Shahar kalitlari `summary()` ning
**ichida** yasalardi. Aynan shuning uchun `CityReach` ning maydoni chiqishga
jimgina tushmay qolgan edi: `district_summary()` bor, `city_summary()` yo'q
edi.

🔴 **`city.coverage` `--json` da umuman yo'q edi** (u faqat matnda),
`over_capacity` esa hech qayerda yo'q edi — `districts_with_users >
districts_total` ni chaqiruvchi o'zi hisoblardi, ya'ni qoida moduldan chiqib
ketardi.

## Qilingan ish

| Fayl | Nima |
|---|---|
| `app/clustering/tzcoverage.py` | `city_summary()` — 10 maydonli tekis kesim; `summary()` uni `**` bilan oladi |
| `tools/tz_check.py` | `city_line()`, `city_context_line()`, `OVER_CAPACITY_LABEL`; `render()` shahar satrlarini o'zi yasamaydi |
| `tests/test_tz_coverage.py` | `a_city()` fikstyurasi + 4 test |
| `tests/test_tz_check.py` | `one_city()`/`city_cover()` + 6 test (biri parametrlangan) |

Migratsiya, sozlama, i18n va API javoblari — **tegilmadi**. §12 ishlab
chiqishdan oldingi tekshiruv, foydalanuvchiga chiqmaydi.

**Natija:** 4941 passed, 409 skipped (edi 4929/409), `ruff check` toza,
`ruff format` to'rtala tegilgan faylda toza.

## Qabul qilingan qarorlar

1. **Kalitlar eski nomi bilan qoladi.** `city_summary()` `districts_total`,
   `city_need`, `dead_weight` nomlarini saqlaydi va faqat yetishmagan
   to'rttasini qo'shadi. Rad etilgan variant: `summary()` ga ichma-ich
   `"city": {...}` qo'shish — u bitta mapping ichida bir xil sonning ikkita
   nomini yasardi va bittasini o'qigan chaqiruvchi ikkinchisining
   yangilanganini ko'rmasdi.
2. **Yangi topilma qo'shilmadi.** `over_capacity` uchun `Finding` yaratish
   taklifi rad etildi: `coverage.unknown_district` shu holatda har doim
   yonadi va **kuchliroq** (tumanlarni nomma-nom aytadi). Qo'shilgani —
   sonning **ma'nosi** (yorliq), topilma emas. 201-run ning ⬜ qaydi shu
   sababdan faqat **qisman** yopildi.
3. **Yorliqning bo'shlig'i oldinda** (`" REYESTRDAN-KO`P"`), `CONFLICT_LABEL`
   da esa keyinda. Sabab: yorliq ulushning **ma'nosini** o'zgartiradi, ya'ni
   o'sha sonning yonida turishi kerak; bo'sh holatda qatorda ikkita bo'shliq
   qolmasligi ham shundan.
4. **Ikkinchi satr ayri funksiyada.** `city_context_line()` boshqa savolga
   javob beradi (javob qanchalik ishonchli) va uning ikkita soni `Coverage`
   niki, qolgani `CityReach` niki — shakl shu ikkovini ajratishi kerak.

## Mutatsiya o'lchovi — 16 mutant

Birinchi urinishda **ikkitasi omon qoldi**, ikkalasi ham fikstyura nuqsoni:

* **M8** (`DECIDER_LABEL[minimum_decides]` → `[reachable]`) — ikkala shahar
  fikstyurasida ham `minimum_decides == reachable` edi (birinchisida ikkovi
  `True`, ikkinchisida ikkovi `False`). «Hamma javobi bo'yicha teskari»
  ikkinchi holat — **yetarli shart emas**: ajratish kerak bo'lgan har juftlik
  uchun bittadan qarama-qarshi holat kerak. Uchinchi test qo'shildi (porogi
  yig'iladi, lekin qarorni ulush qabul qiladi — va aksincha).
* **M16** (`city_context_line(coverage)` → eski f-satr) — reyestri to'liq
  mintaqada `over_capacity` o'chiq, ya'ni eski yorliqsiz satr yangi funksiya
  bilan **belgima-belgi bir xil** chiqadi. `render` da'vosi
  `known=True/False` bo'yicha parametrlandi.

Tuzatishdan keyin: **16 mutant — 16 KILLED.**

## Muhit (o'zgarmagan sabab)

* `/` 100% to'la (80 MB), `/sessions` 99% (125 MB) → PostGIS ko'tarilmaydi,
  `ST_AsGeoJSON` yo'li **hamon o'lchanmagan**.
* Ish nusxasi `/dev/shm/w202` da (`tar` bilan, `.git` va `__pycache__` siz);
  `/dev/shm` **har bash chaqiruvida bo'shaydi**, shuning uchun nusxa+o'lchov
  bitta chaqiruvda bo'lishi shart.
* Bash chaqiruvi ~180 s da uziladi (`timeout_ms` dan qat'i nazar): to'liq
  to'plam (55 s) va 16 mutant (16 × 0.5 s + nusxa) **ikkita alohida**
  chaqiruvda yuritildi. Bittasiga birlashtirilgan urinish uzildi.

## Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish (disk kerak).
2. §12 ning **tzreach** yarmi: `_reach_lines()` ning daraja qatori
   (`{level:8} {reached}/{episodes} ({share}) oynadan tashqari {window_only}
   YUQORI/ok [histogram]`) hamon faqat `in` bilan o'lchanadi
   (`"sonlar yo'q" in text`) — shakli qulflanmagan, ya'ni ikkita maydonni
   almashtirgan mutant omon qoladi. `district_line`/`city_line` bilan bir xil
   qoidaga keltirish kerak.

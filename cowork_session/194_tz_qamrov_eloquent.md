# 194-run — TZ §12 «Дополнительно»: §3 ning poroglari erishuvchanmi

**Sessiya:** `local_eloquent-affectionate-rubin` · **Sana:** 2026-08-20
**Natija:** ✅ `app/clustering/tzcoverage.py`; 5237 passed / 2 skipped
haqiqiy bazada, `requires_db` 408 (+4), migratsiyasiz, `ruff` toza,
13 mutant → 13 KILLED.

---

## 1. Qayerdan boshlandi

193-run uchta keyingi qadam qoldirgan edi:

1. 👤 qaysi zonaning verdikti hodisani tasdiqlaydi (ulash 3-bandi) —
   **javobsiz savol**, ya'ni bloklangan;
2. §12 ning «Дополнительно» yarmi (`tzsource.BlockRegistry`) javobga
   qo'shilsin — **bloklanmagan**;
3. `tools/` da hisobot chop etadigan skript.

Ikkinchisi olindi. §10 ning yigirmala bandi `BUILT`, §11 navbati
181-runda yopilgan, ya'ni §12 — qurilmagan yagona bo'lim, va uning
asosiy yarmi (`tzreach`, odam poroglari tarixda) 193-runda qurilgan.

§12 ning oxirgi jumlasi boshqa savol beradi:

> **Дополнительно:** сколько районов и кварталов в Самарканде и в
> скольких из них есть пользователи — от этого зависит §3.

Bu savol **tarixga tayanmaydi**. `tzreach` bugun `UNKNOWN` /
`NO_INDEPENDENT_TRUTH` qaytaradi (sanoqdan mustaqil dalili bor hodisa
bazada yo'q), «Дополнительно» esa bugungi reyestrlardan hozir
o'lchanadi — ya'ni §12 dan qolgan yagona **bloklanmagan** ish shu edi.

---

## 2. Qurilgani

Yangi toza modul `app/clustering/tzcoverage.py`:

```
RegionFacts  →  measure()  →  Coverage
                              ├── districts: tuple[DistrictReach, ...]
                              └── city: CityReach

to_facts(BlockRegistry, districts=…, geometry=…) → RegionFacts
load(session, region_id=…, params=…)             → Coverage
summary(Coverage)                                → tekis kesim
```

`load()` uchta so'rovni birlashtiradi va **hech birini qayta
yozmaydi**: `tzsource.load()` (§3 ning maxraji),
`geo.queries.current_districts` (reyestr) va
`geo.queries.district_geometry_facts` (taxminiy kvartallar soni).

Testlar: `tests/test_tz_coverage.py` (72, bazasiz) va
`tests/test_tz_coverage_db.py` (4, `requires_db`).
Modul `tests/test_tz_counting.MODULES` reyestriga qo'shildi (Т-1/Т-4
qorovuli takrorlanmaydi).

---

## 3. 🔴 Shaharning porogi tumanlarning **natijasidan** yig'iladi

Eng qimmat topilma va u ko'rinmas.

`tzscale.city()` maxrajga foydalanuvchisi bor **har bir** tumanni
qo'shadi (`has_users = verdict.with_users > 0`), sanoqqa esa faqat
**tasdiqlanganini** (`confirmed = verdict.reached`). Demak ikkita
kvartalli tuman:

* shaharning maxrajini **ko'taradi**,
* sanoqqa **hech qachon** kira olmaydi (`district_block_min = 3` uni
  to'sadi — hamma kvartali tasdiqlansa ham).

O'lchov:

| Holat | maxraj | kerak | tepa chegara | verdikt |
|---|---|---|---|---|
| 3 ta uch kvartalli tuman | 3 | 3 | 3 | ✅ tasdiqlanadi |
| + 4 ta bir kvartalli tuman | 7 | 4 | 3 | ❌ tasdiqlanmaydi |

Bir xil uchta yaxshi tuman, qo'shnilarining soniga qarab ikkita
teskari verdikt — xatosiz va jurnalsiz. Shuning uchun sanoqning tepa
chegarasi `districts_reachable` (o'zi erishuvchan tumanlar),
`districts_with_users` **emas**; farqi `CityReach.dead_weight` da
nomlanadi.

Rad etilgan variant: shaharning maxrajini «foydalanuvchisi bor
tumanlar» deb qoldirish va tepa chegarani o'sha sondan olish. U
`7 >= 4` deb «erishuvchan» berardi va §12 ning butun javobini yolg'on
ijobiy qilardi. Mutatsiya bilan qulflangan
(`test_the_city_numerator_is_reachable_districts_not_districts_with_users`).

---

## 4. 🔴 Ikkita maxraj bor va ular almashtirilmaydi

| Savol | Maxraj | Manbasi |
|---|---|---|
| §3 ning porogi | foydalanuvchisi bor zonalar | `reports` |
| §12 ning qamrovi | mavjud zonalar | `geo` reyestri |

Almashtirish har ikki tomonga ham buzadi:

* qamrovni `blocks_with_users` dan hisoblash **har doim `1.0`**
  berardi — maxraj sanoqning o'zidan olingan bo'lardi va §12 ning
  «в скольких из них есть пользователи» savoli o'z javobini o'zi
  tasdiqlardi;
* §3 ning porogini `districts_total` dan hisoblash bo'sh tumanlarni
  maxrajga qo'shardi va §3 ning «Если в районе 50 кварталов, а
  пользователи есть в 12, считаем от 12» qoidasini bekor qilardi.

Uchinchi qaror: geo reyestri §3 ning maxrajini **kichraytirmaydi**
ham. `geo.queries.current_districts` faqat joriy chegara versiyasini
beradi (`valid_to IS NULL`), xabarlar esa eski `district_id` bilan
yozilgan bo'lishi mumkin. Bunday tumanni tashlab yuborish §3 ning
arifmetikasini jimgina o'zgartirardi (shaharning porogini
pasaytirardi), shuning uchun u maxrajda qoladi va `unknown_districts`
da **nomlanadi**. Bazadagi test aynan shuni o'lchaydi: `valid_to`
qo'yilgach `districts_total` 2 → 1, `districts_with_users` esa
o'zgarmaydi.

---

## 5. 🔴 Ulush erishuvchanlikni hech qachon to'smaydi

`share_need(n, share) <= n` har qanday `share <= 1` uchun, va
`tzconfig._check()` `Unit.SHARE` ni `(0, 1]` bilan qulflaydi. Ya'ni
«porog umuman yig'ilishi mumkinmi» degan savol **tuzilmaviy**
ravishda `n >= minimum` ga qisqaradi.

Shunga qaramay `need` modulda hisoblanadi, taxmin qilinmaydi:
sozlama qorovuli bo'shatilsa (`share > 1`) javob jimgina noto'g'ri
bo'lib qolmasin. Qorovulning o'zi test bilan qulflangan
(`test_the_share_alone_never_blocks_reachability`, `(0, 1]` bo'ylab
parametrlangan).

Undan chiqadigan ikkinchi kuzatuv:

| Kvartallar | ulush beradi | eng kam son | qaror |
|---|---|---|---|
| 1..5 | 1..2 | 3 | **eng kam son** |
| 6..7 | 3 | 3 | teng — bayroq `False` |
| 8+ | 4+ | 3 | ulush |

Ya'ni `0.40` kichik shaharda **umuman ishlamaydi** va qarorni faqat
mutlaq son qabul qiladi. §3 esa «Абсолютное число в настройках не
задавать, только долю и минимум» deb yozgan: mutlaq son sozlamada
emas, lekin u qaror qabul qiladi. Aynan shu — §12 ning «от этого
зависит §3» jumlasining amaliy ma'nosi.

`minimum_decides` ataylab «eng kam son javobni **o'zgartirdimi**»
degan savolga javob beradi, «son bir xilmi» degan savolga emas —
ikkinchi o'qish bayroqni diagnostikadan bezakka aylantirardi.

---

## 6. Kichikroq qarorlar

* **`need` `tzscale.share_need()` dan olinadi.** Formulani qayta
  yozish oson edi va u §12 ni foydasiz qilardi: sodda
  `ceil(0.3 * 10)` IEEE-754 da (`3.0000000000000004`) **to'rtta**
  berardi, ya'ni o'lchov mahsulot qo'llaydigan qoidadan boshqa qoida
  haqida son berardi. `tzreach` ning `evaluate_levels()` ni
  chaqirishi bilan bir xil sabab.
* **Sanaladigan narsa — kvartallar, odamlar emas.**
  `BlockUsersRow.users` ni qo'shish §3 ning birinchi jumlasi
  taqiqlagan narsani qilardi.
* **Taxminiy qamrov kesilmaydi.** `geo.queries._geometry_facts`
  bazada `h3` yo'qligi uchun `ST_Area / katakcha maydoni` bilan
  sanaydi. `over_capacity` shuning uchun «qamrov birdan katta»
  degani emas, **taxmin noto'g'ri** degani; qiymatni birgacha kesish
  nuqsonni yashirardi.
* **Geometriyasi yo'q tumanda qamrov `None`**, `0.0` emas — nol
  qaytarish o'lchanmagan qamrovni «nol qamrov» deb ko'rsatardi.
* **Foydalanuvchisiz mintaqa `UNKNOWN`**, «erishilmas» emas: §7 ning
  raqamlarini bo'sh bazadan o'zgartirish §12 ning maqsadiga
  to'g'ridan-to'g'ri zid.
* **`SPEC` konstantasi ataylab yo'q** — `tzreach` bilan bir xil
  sabab: `SPEC` li modul reyestrlar indeksida qator bo'lishi shart,
  bu modulda esa solishtiriladigan qator yo'q (u §3 ning bandlarini
  emas, reyestrlarni o'lchaydi).
* **Migratsiya, yangi sozlama, i18n kaliti va API yo'q.** §12
  foydalanuvchiga chiqmaydi — u ishlab chiqishdan **oldingi**
  tekshiruv.

---

## 7. Mutatsiya

13 mutant, ikki bosqichli harness (tor tanlov → nomzod, keyin
tasdiq); verdikt faqat `rc == 1` da `KILLED`.

Birinchi o'tishda **bittasi omon qoldi**:
`blocks_by_district` ning `counts[district] = counts.get(district, 0) + 1`
o'rniga `= 1` — ya'ni har bir tumanga bittadan kvartal. Sabab tanish:
shart to'g'ri edi, uni **ajratadigan holat fikstyurada yo'q edi** —
`blocks_by_district` ning testlari bitta kvartalli tumanlardan
iborat, qolgan hamma test esa `RegionFacts` ni qo'lda yasaydi va
ko'prikdan umuman o'tmaydi.

Mutantning narxi katta bo'lardi: `blocks_by_district` — `tzsource`
dan §3 ning maxrajiga yagona ko'prik, ya'ni sog'lom shaharning
**hamma** tumani «недостижим навсегда» bo'lib chiqar va §7 ning
raqamlari yo'qdan o'zgartirilardi.

Fikstyura ajratuvchi qilib qayta yozildi (bitta kvartalda ellik odam
↔ uchta kvartalda bittadan odam — ikkala noto'g'ri sanoqni ham bir
vaqtda o'lchaydi) va ikkinchi o'tishda **13 dan 13 tasi KILLED**.

---

## 8. Sandbox

`/tmp/pg180` + `/tmp/mamba/envs/py311` tirik. Ikkita yangi mina:

* `/tmp` ga **unix-soket** yozib bo'lmaydi —
  `could not open lock file "/tmp/.s.PGSQL.NNNNN.lock"`. Yechim:
  `unix_socket_directories` ni `pgdata` papkasiga burish.
* **Postgres chaqiruvlar orasida o'ladi.** `pg_ctl start` keyingi
  `bash` chaqiruvida yo'q — `initdb` bir marta qilinadi, lekin
  `start` + `alembic` + `pytest` **bitta** chaqiruvda bo'lishi shart.

`initdb` `/sessions/<sid>/tmp/pgdata194` ga (port `55194`), nusxa
`/sessions/<sid>/tmp/r194`, to'liq to'plam baza bilan ~95 s.
Disk: `/` da 200 MB, `/sessions` da 270 MB — juda tor.

---

## 9. Keyingi qadam

1. 👤 savol o'zgarmadi — **qaysi zonaning verdikti hodisani
   tasdiqlaydi** (TZ zonani tasdiqlaydi, `outages` esa klasterni).
   Ulash tartibining 3-bandi shunga tayanadi.
2. §12 ning ikkala yarmi ham endi kod. Qolgan ish — `tools/` da
   ikkalasini bitta hisobotga chiqaradigan skript
   (`tzreach.measure` + `tzcoverage.summary`), u §12 ni **odam
   yuritadigan** qilardi.

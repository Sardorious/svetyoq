# 85-sessiya — SCOPE: `01` §7 «Scope» ↔ kod

**Sana:** 2026-08-10 ~23:15 UTC
**Sessiya:** `local_2d39e34a-94c0-40c4-a489-684742b4b14d`
**Natija:** `app/release/scope.py` + `tests/test_scope_contract.py` (51 test),
`app/admin/registries.py` ga `scope` qatori, `registry.scope` UZ/RU kalitlari.
**2420 passed, 232 skipped** (bazasiz), ruff yashil, **31 mutatsiya / 0 survivor**.

---

## 1. Run boshi

`INDEX.md` ning «Qayerda to'xtadik» qatori 84-runni ko'rsatdi va uchta
nomzod qoldirgan edi:

1. `01` §7 «Scope» — **ogohlantirish bilan**: «ustma-tushish qulflanishi
   kerak, nusxa emas»;
2. `01` §16 «API Requirements» (`U-2` o'sha yerga olib boradi);
3. p95 ni vitrinaga chiqarish.

Birinchisi tanlandi. `EpicProgress.md` va `PROGRESS.md` ning tepasi
o'qildi; repo holati ko'rildi.

**Sandbox:** `/tmp/venv80` ishlaydi (Python 3.12, pytest 9.1.1).
PostGIS **ko'tarilmadi** — `/` da 76 MB qoldi (83-rundan beri disk 100%
to'la, `/tmp/pgdata82` boshqa foydalanuvchiniki va o'qilmaydi). Run
shuning uchun bazasiz; `requires_db` ning 232 tasi o'tkazib yuborildi.
👤 Odamga eslatma: `cleanup-sessions.ps1`.

---

## 2. Nima uchun §7 va nima uchun boshqacha savol bilan

§7 boshqa reyestrlardan farq qiladi: §24 «qachon», §25 «nima bilan»,
§4 «qanchaga» deb so'raydi, §7 esa **chegara** chizadi — uch ro'yxat
(kiradi / keyinroq / umuman kirmaydi), o'n sakkiz qator. Chegaraga
beriladigan savol ikki tomonlama: *ichkaridagi qurilganmi va
tashqaridagi qurilmay qolganmi?*

84-run ning ogohlantirishi shunday bajarildi: har MVP qatorining
«Обоснование» katagi boshqa bo'limga havola qiladi (`FR-807`, `PG-S3`,
`§17`, `PG-S4`, `PG-S2`, `P0-1`) va test o'sha havolaning **gorizontini**
`01` §3 ning o'z jadvalidan parse qiladi. Havola nimani o'lchashi bu
yerda **qayta o'lchanmaydi** — `P0-1` ni `roadmap`, `PG-S*` ni
`success`, `FR-807` ni `dependencies` o'lchaydi.

### Uch o'q

| O'q | Sinflar | Savoli |
|---|---|---|
| `Presence` | BUILT · PARTIAL · DISPLACED · UNREACHABLE · ABSENT · EXTERNAL | repo nima qilgan |
| `Fence` | HELD · CROSSED · HOLLOW · UNWITNESSED | chegara da'vosi rostmi |
| `Warrant` | ANCHORED · MISDATED · FOREIGN · PROSE · NONE | asos nimaga tayanadi |

`Presence` va `Fence` **ataylab ajratilgan**: «qurilganmi» va
«chegaradan chiqdimi» bir savol emas — `F-5` aynan shuni ko'rsatadi.

---

## 3. Topilmalar

### 3.1. Asosiy: bitta yo'q mexanizm uchala ro'yxatning ham qatorini hal qiladi

`06` §2 ning olti qatorli manba registri bor
(`app.reports.sources:SOURCES`), `intake.create_report` esa
`source_code: str = DEFAULT_SOURCE_CODE` bilan e'lon qilingan — va
**butun repoda birorta chaqiruvchi unga literal bermaydi**. AST bilan
o'lchandi: `source_code=` bo'lgan har bir chaqiruv uch shakldan biri —
mavjud qatorning maydoni (`created.source_code`), SQL natijasining
ustuni (`r[9]`) yoki funksiya ichidagi o'tkazish. Uchalasi ham manba
**tanlamaydi**. `app/api/v1/admin.py` da xabar kiritadigan endpoint ham
yo'q.

Shu bo'shliq **to'rt** qatorni hal qiladi:

| Qator | Ro'yxat | Nima bo'ladi |
|---|---|---|
| `S-7` «Ручной разбор публикаций 1055» | MVP | `official` bazada, `is_authoritative=True`, `layer='official'` qoidasi yozilgan — kirish nuqtasi yo'q → `HOLLOW` |
| `S-8` «Партнёрская схема с махаллинскими чатами» | MVP | `mahalla_active` (og'irlik 2.0) ham tanlanmaydi → sherik xabari oddiy `bot` dan farq qilmaydi |
| `F-4` «Официальная интеграция с оператором» | Future | `operator_api` `0003` da **allaqachon** seed qilingan; chegara ushlanadi, lekin **o'z sababi bilan emas** |
| `O-3` «Официальный статус источника» | Out of Scope | ushlab turgan narsa dislaymer emas, o'sha yetib bo'lmaslik |

To'rttasi **bitta kunda bir vaqtda** ma'nosini o'zgartiradi —
`source_code` ni beradigan birinchi chaqiruvchi yozilgan kuni. §7 ni
o'qigan odam uchun esa bular to'rtta mustaqil qaror.

Bu `PROGRESS.md` ning eski ochiq savolini (`official`/`operator_api`
seedi tasdiqlanmagan holda `is_authoritative=True`) boshqa tomondan
tasdiqlaydi: seed bugun **zararsiz**, va u zararsiz bo'lib qolishi
mexanizmga emas, **yo'qlikka** tayanadi.

### 3.2. Yagona `CROSSED` — `F-5`, va u eng katta

«Распространение на другие города области» — Future Release. Repo esa
**ko'plikni** qurgan: `active_regions` tuple qaytaradi, `pick_for_point`
ular orasidan tanlaydi, `for_point` koordinata bo'yicha dispetcherlik
qiladi, `tools/region_admin.py` `N`-mintaqani qo'sha oladi,
`GET /regions` ro'yxat beradi. Bitta mintaqali mahsulotga bularning
birortasi kerak emas edi.

§7 ning MVP qatori (`S-1`) faqat **birlikni** ruxsat beradi —
«активация региона конфигурацией». `03` §3 esa ko'plikni **`R3.0`** ga
qo'yadi. Bir xil ishning uchinchi hujjatda uchinchi joyga qo'yilishi:
77-run `01` §25 ↔ `03` §3 ning `R3.0` to'qnashuvini topgan, 82-run
fazalarni o'lchagan.

⚠️ Farqni sezish qiyin, chunki qurilgani **ma'lumot emas, mexanizm**:
ikkinchi mintaqa hali import qilinmagan (E19 ning to'sig'i), ya'ni
tashqi qarashda chegara buzilmagan ko'rinadi.

### 3.3. Eng jim topilma — `Warrant` o'qida

`S-6` («Подписка на адрес и уведомления», MVP = Ph.0 + Ph.1) o'zini
`PG-S2` bilan asoslaydi. `PG-S2` ning gorizonti — **Ph.2**. Ya'ni MVP
qatori o'zidan **keyinroq** keladigan maqsadga tayanadi va bunday asos
hech narsani asoslamaydi. Ustiga `PG-S2` ning mazmuni obuna haqida ham
emas: «Карта осмысленна на уровне махалли». Katak vaqt bo'yicha ham,
ma'no bo'yicha ham noto'g'ri manzilga havola qiladi.

Hukm **hisoblanadi**, e'lon qilinmaydi: gorizont `01` §3 dan parse
qilinadi, `MVP_PHASES` esa sarlavhaning (`MVP (Phase 0 + Phase 1)`)
hosilasi. 57-run ning tuzog'i shu bilan chetlab o'tildi.

### 3.4. Ikkinchi jim topilma — `O-5` ning ruxsat etilgan yarmi ham yo'q

«Гарантии времени восстановления» — Out of Scope, va chegara ushlanadi:
`outages` da bashorat maydoni yo'q, `autoclose_after` esa jimlikdan
keyin yopish qoidasi. **Lekin** `01` §3 ning User Goals i «понять,
когда **ориентировочно** вернётся свет» deb yozadi — ya'ni taxminni
**maqsad** qilib qo'yadi. Repo ikkalasini ham bermaydi va §7 buni
bo'shliq deb ko'rsatmaydi: chetlash bajarilgan, ruxsat etilgani esa
qurilmagan.

### 3.5. Uchinchi — `O-4` (SMS) ni to'sadigan qorovul boshqa bo'lim uchun yozilgan

Katakdagi sabab narx («стоимость несовместима с некоммерческой
моделью»), repodagi yagona to'siq esa
`app.admin.security:USERS_ALLOWED_COLUMNS` — telefon ustunini rad
etadigan oq ro'yxat, va u `01` §20 ning ПДн pozitsiyasi uchun yozilgan
(74-run buni `channels.py` da topgan; bu yerda boshqa yo'ldan
tasdiqlandi). Narx haqida repoda hech narsa yo'q.

### 3.6. Teskari yo'nalish — uchta qurilgan sirt uchala ro'yxatda ham yo'q

| Kod | Sirt | Izoh |
|---|---|---|
| `U-1` | Ommaviy API (`/api/v1`, OpenAPI) | E15 ✅. **To'rtinchi** hujjat: 77 — §25, 82 — §24, 84 — §4. `01` §16 undan **talab** qiladi, ya'ni paket ko'lamsiz talab qo'yadi |
| `U-2` | Moderatsiya va ma'muriy panel | E8 🔄. 77-run uni §25 da ham topmagan |
| `U-3` | H3 issiqlik xaritasi (`/heatmap`) | E16 🔄. `S-4` H3 ni **biriktirish darajasi** sifatida nomlaydi, sirt sifatida emas |

---

## 4. Ikkita eski tripwire ishladi va ikkalasi ham haq edi

1. **77-run ning `P0-*` skaneri** (`test_release_plan_contract`).
   `S-7` ning asosi `P0-1` va u reyestrda **literal** sifatida turadi,
   ya'ni skaner uni «Faza 0 natijasi saqlanadigan joy» deb o'qidi.
   82-run bu holatni allaqachon boshdan kechirgan (`roadmap.py`).
   Qoida **yumshatilmadi**: fayl ro'yxatdan chiqarildi (to'rtinchi
   istisno) va `roadmap.evaluate().recorded == ()` talabi o'z kuchida
   qoldi.
2. **75-run ning `MAHALLA_POLYGON_MISSING` qorovuli**
   (`test_risk_register_contract`). Reyestrning izohi **kod satri**
   bo'lardi (docstring emas, `note=` ichida), ya'ni qoida haq edi:
   xato kodi mahsulotda yo'q va uning nomi ham yozilmasligi kerak.
   Izoh nomsiz qayta yozildi.

Uchinchisi — **80-run ning `SPEC` tripwire i**: `SPEC` konstantasi
bo'lgan har bir modul indeksda bo'lishi shart. `registries.py` ga
`scope` qatori (`SELF_CONTAINED`, endpointsiz) va `registry.scope`
UZ/RU kalitlari qo'shildi. `_probe_scope` ning `flagged` i ikkita
sababni **birlashtiradi**, yig'maydi (`S-1` ham `HOLLOW`, ham
`FOREIGN` — yig'indi `flagged > total` bo'lib qolardi).

---

## 5. Hisob

| O'q | Taqsimot |
|---|---|
| `Presence` | BUILT 3 · PARTIAL 1 · DISPLACED 1 · UNREACHABLE 4 · ABSENT 8 · EXTERNAL 1 |
| `Fence` | HELD 12 · CROSSED 1 · HOLLOW 4 · UNWITNESSED 1 |
| `Warrant` | ANCHORED 4 · MISDATED 1 · FOREIGN 1 · PROSE 2 · NONE 10 |
| `Standing` | IN 8 · LATER 5 · OUT 5 |

`boundaries_hold` = `False` **ikkala tomondan ham** (to'rtta `HOLLOW`,
bitta `CROSSED`); `accurate` = `False`. **Hech narsa tuzatilmadi
ataylab** — modul o'lchaydi, tahrirlamaydi (75, 76, 77, 82, 83, 84
bilan bir xil qoida).

O'n besh sinfning **hammasi** ishlatilgan va test buni talab qiladi.

---

## 6. Mutatsiya

31 mutatsiya, birinchi yurishda **1 survivor**:

> `F-4` ning `presence` ini `UNREACHABLE` → `ABSENT` qilish hech
> narsani yiqitmasdi.

Bu bosh topilmaning ikkinchi yarmini o'chirib qo'yardi: `ABSENT` bu
qatorni «hali boshlanmagan» deb ko'rsatardi, holbuki uning qatori
**bugun bazada**. Yangi test qo'shildi
(`test_f4_the_operator_row_is_already_seeded`): `operator_api` ning
`is_authoritative` va `weight=0.0` i, `0003` ning `SOURCES` dan seed
qilishi, va `presence is not ABSENT`. Ikkinchi yurish — **0 survivor**.

Harness **repoda emas**, `/tmp/mut85/` da yozildi va run oxirida
o'chirildi. 84-run ning `tools/_mut84.py` tuzog'i shu bilan
takrorlanmadi; `_mut84.py` esa hali ham bo'shatilgan holda repoda
turibdi va uni odam o'chirishi kerak.

---

## 7. Qarorlar va rad etilgan variantlar

- **`PARTIAL` `PRESENCE_BUILT` ga kirmaydi.** `S-1` da uchta artefakt
  nomlangan (tuman poligonlari, mahalla poligonlari, qamrov zonasi) va
  bittasi qurilgan; qatorni «bajarildi» deb o'qish eng oson joyi shu.
- **`F-5` `Presence.BUILT` + `Fence.CROSSED`.** «Qurilgan» va
  «chegaradan chiqqan» ni bitta o'qqa siqish 76-run ning `Блокирует`
  ustunidagi xatoning aynan o'zi bo'lardi.
- **`Out of Scope` ning dalili — simvolning yo'qligi**, va bu **isbot
  emas, kuzatuv**. Test funksiyasining nomi shuni aytadi
  (`..._are_observed_absent_not_proven_absent`).
- **Absence-skanerlar reyestrning o'zini chiqarib tashlaydi**
  (`QUOTING_MODULES`): modul hujjatni **keltiradi** («стоимость»,
  `MAHALLA_POLYGON_MISSING`), ya'ni iqtibos kodning mavjudligi emas.
  84-run ning `_mut84.py` tuzog'i, teskari tomondan.
- **`note`/`gap` matnlari tekshirilmaydi** — ular keyingi o'quvchi
  uchun sabab, artefakt emas (`test_roadmap_contract` qoidasi).

---

## 8. 👤 To'rtta savol (`PROGRESS.md` da to'liq)

1. `bot` dan boshqa manba tanlaydigan yo'l qachon paydo bo'ladi?
   Eng kichik yechim — moderator uchun `POST /admin/reports`, lekin u
   `05` §7.2 ni kengaytiradi.
2. `S-6` ning asosi tuzatiladimi (katak boshqa maqsadga ko'chiriladimi
   yoki `PG-S2` ning gorizonti o'zgaradimi)?
3. `F-5` — ko'plik qayerda turadi: `01` §7 ning Future Release ida yoki
   `03` §3 ning `R3.0` ida? Bugun ziddiyat zararsiz, E19 ning to'sig'i
   olingan kunda §7 yolg'onga aylanadi.
4. §7 ga uchta qator qo'shiladimi (ommaviy API, moderatsiya, issiqlik
   xaritasi)?

Ustiga: **`sveta/tools/_mut84.py` o'chirilishi kerak** (84-rundan
qolgan, bo'shatilgan) va **`cleanup-sessions.ps1`** — disk 100% to'la,
shuning uchun ikkinchi run ketma-ket bazasiz yurdi.

---

## 9. Keyingi nomzodlar

1. **`01` §16 «API Requirements»** — `U-1` aynan o'sha yerga olib
   boradi: §16 ommaviy API dan talab qiladi, §7 esa uni ko'lamda
   umuman nomlamaydi. Yettita delta qatori bor.
2. **`01` §8 «Functional Requirements» deltasi** — `FR-S-802` va
   `FR-S-804` ning ziddiyati allaqachon ochiq savolda turibdi.
3. p95 ni vitrinaga chiqarish (84-rundan qolgan).

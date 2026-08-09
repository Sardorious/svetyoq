# 35-sessiya — BR-024: mintaqa spravochnigi o'zgarishlari audit jurnalida

**Sana:** 2026-08-08 · **Epic:** E8/E19 kesimi · **Sessiya:** `local_6ae2b8c3`

⚠️ **Sandbox oltinchi marta ketma-ket yiqildi (INFRA-1).** Ikkala urinishda
ham `useradd failed: No space left on device` — `ruff` ham, `pytest` ham
ishga tushmadi. Ko'rsatma bo'yicha ikkinchi urinishdan keyin to'xtatildi.

---

## 1. 34-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q

`tests/test_abuse_contract.py` testsiz qolgan edi. Tekshirilgani:

- **Imzolar joyida:** `confirmation.Evidence` (`user_id, lat, lon, h3_r9,
  weight, created_at, mahalla_id=None`), `confirmation.evaluate(rows, *,
  a_local, now, params, spread_min_distance_m)`, `scale.raw_scale`,
  `scale.coverage_cap`, `scale.decide`, `scale.TerritoryFacts`,
  `sources.USER_FACTOR_MIN`, `sources.SOURCE_BY_CODE`,
  `velocity.measure/is_implausible/penalize` — hammasi test
  chaqirayotgan shaklda mavjud.
- **Hisob-kitob qo'lda takrorlandi.** 5-qator: `freeze_weight(
  "mahalla_active", 100) = 2.0 × min(1.6, 100/50) = 3.2`,
  `N_req(20) = clamp(3, ceil(0.5·√20 = 2.24) = 3, 8) = 3` — ya'ni
  `weighted_score (3.2) >= required_score (3)` va sabab `min_users`
  bo'lib qoladi ✓. 6-qator: `mahalla_threshold(4000) = clamp(5, 23, 15)
  = 15`, `district_threshold(4000) = clamp(10, 23, 30) = 23`; siqilgan
  oqimda `cells_with_reports = 1 < MIN_CELLS_FOR_MAHALLA = 3` va
  `coverage_ratio(1) = 0.025 < 0.30` → `LOCAL` ✓; tarqoq oqimda
  `20/40 = 0.5 >= 0.15` va `mahallas_affected = 3 >= 2` → `DISTRICT` ✓.
- **Eng nozik joy — `min_users` ning qiymati.** 2-qator testi uchta
  akkauntni `spread` bilan to'xtatishni kutadi, lekin `evaluate` da
  tartib **avval** `distinct_users < min_users`. `DEFAULT_PARAMS.confirm
  .min_users = 3` bo'lgani uchun uchta akkaunt bu to'siqdan o'tadi va
  test haqiqatan `spread` ni o'lchaydi. `min_users` `4` ga
  o'zgartirilsa test **boshqa sabab** bilan yiqilardi — bu qulflangan
  bog'liqlik va uni bilib qo'yish kerak.
- `decide` da `capped = final is not raw` — qamrov to'sig'i testining
  `decision.capped` ✓.

## 2. `BRD_Samarkand.md` birinchi marta kod bilan solishtirildi

34-run «tekshiruv nomzodi» deb qoldirgan hujjat. §8 (BR-001…BR-028),
§11, §12 NFR, §13 BRL-01…BRL-15 ko'rildi. **Ikkita bo'shliq topildi va
ular bir xil emas:**

**(a) BR-005 / BRL-01 — `out_of_coverage`.** BRD talab qiladi: poligon
tashqarisidagi xabar **saqlanadi** («сохраняется как `out_of_coverage`»,
`FR-304` dan meros). Kodda esa `geo.region_for_point` `OutOfRegionError`
ko'taradi va xabar umuman yozilmaydi. **Lekin bu kod ishi emas:** `05`
§2 da `reports` uchun bunday status ustuni yo'q va `01` PRD bu talabni
umuman takrorlamaydi — ya'ni bajarish spetsifikatsiyadan chetlashish
bo'lardi. → «Ochiq savollar», 👤.

**(b) BR-024 — audit.** «Любое действие с региональными справочниками
логируется неизменяемо» (High, NFR-AU-01 bilan birga). `audit_log` da
esa faqat moderator harakatlari bor edi: `outage.reject`,
`outage.merge`, `user.block`, `user.unblock`, `user.trust_score`.
Spravochnikni o'zgartiradigan **hamma narsa** jurnaldan tashqarida
edi. **Va bu chetlashish emas:** `05` §2.5 `action` ustunini
`-- 'outage.confirm', 'user.block', ...` deb, ro'yxatni ochiq
qoldirib izohlaydi. → shu running ishi.

## 3. Nima uchun aynan bu bo'shliq qimmat

Eng ko'p zarar `region_admin config` da. U `06` §9 parametrlarini
o'zgartiradi — tasdiqlash chegarasi, masshtab koeffitsientlari,
bildirishnoma radiusi. `confirm.min_users` ni `1` ga tushirish bir
kechada butun mintaqaning statistikasini boshqa qiladi va bugungi kodda
bundan **hech qanday iz qolmaydi**: xato chiqmaydi, kim va qachon
qilgani ko'rinmaydi, `before` qiymat esa butunlay yo'qoladi. Ustiga
`06` §9 ning o'zi «qiymatlar E11 da sozlanadi» deydi — ya'ni bu
o'zgarish kamdan-kam emas, **rejalashtirilgan** va takrorlanadigan.

Ikkinchi o'rinda — `import_boundaries promote`: quvurdagi yagona
qaytarib bo'lmaydigan qadam (eski `districts` qatorlari `valid_to`
bilan yopiladi, `05` §5).

## 4. Qarorlar

**`SystemActor` — `Actor` emas.** CLI da `X-Admin-Token` yo'q, ya'ni
`Actor` ham yo'q. `audit_log.actor_role` esa `NOT NULL`.

- **`CLI_ROLE = "cli"` `Role` enumiga qo'shilmadi.** `roles.
  has_permission` noma'lum rolga `False` qaytaradi (xato yopiq
  tomonga), ya'ni qiymat jurnalda turadi va hech qanday eshikni
  ochmaydi. `Role.ADMIN` deb yozish qulayroq bo'lardi va aynan shuning
  uchun rad etildi: jurnal «admin qildi» deb **yolg'on** aytardi va rol
  enumiga hech kimga berilmagan qiymat kirib qolardi. Test buni
  qulflaydi: `CLI_ROLE` har bir `Permission` uchun `False`.
- **Operator nomi bazaga tushmaydi.** `actor_id = uuid5(ACTOR_NAMESPACE,
  f"cli:{name}")` — `auth` dagi «token bazada saqlanmaydi, nomdan
  `uuid5`» qarorining aynan davomi. Prefiks (`cli:`) shart: usiz bir
  xil nomli moderator va operator bitta `actor_id` olib, jurnalda
  ikkita turli odam bittaga qo'shilib ketardi.
- **Nom topilmasa `unknown`, istisno emas.** Audit yozuvining yo'qligi
  noma'lum aktordan yomonroq — o'sha holda o'zgarishning **o'zi** ham
  jurnalda ko'rinmasdi.

**Yozuv o'zgarish bilan bitta tranzaksiyada** (`session_scope()`
ichida): audit qatorisiz o'zgarish ham, o'zgarishsiz audit qatori ham
bo'lmaydi. Alohida test buni manba matnidan tekshiradi.

**`before` da nima yo'qligi ham qaror:**

- `cmd_add` da `before` **umuman yo'q** — qator endi yaratildi, ya'ni
  undan oldingi holat mavjud emas (bo'sh lug'at «hamma maydon bo'sh
  edi» degan boshqa ma'noni berardi);
- `cmd_update` da `center` ning eski qiymati **yozilmaydi**: ustundagi
  narsa — `WKBElement` va uni `jsonb` ga qo'yish yozuvni **amal
  bajarilgandan keyin** yiqitardi (`audit.jsonable` docstringi aynan
  shundan ogohlantiradi). Eski markazni olish uchun qo'shimcha
  `ST_Y/ST_X` so'rovi kerak bo'lardi — audit yozuvining narxini
  so'rovga aylantirish;
- `config --key` da `before` `None` bo'lishi mumkin va bu **qiymatli**:
  «kalit yo'q edi, kod `DEFAULTS` ga tushardi». Uni standart qiymat
  bilan to'ldirish jurnalni o'qiyotgan odamga qiymat bazada turgan
  degan yolg'onni aytardi — farq aynan shunda.

**O'zgarishsiz buyruq yozilmaydi.** Allaqachon faol mintaqani qayta
`activate` qilish jurnalga tushmaydi: jurnal — o'zgarishlar tarixi,
buyruqlar tarixi emas; aks holda haqiqiy yoqilish sanasi bir xil
qatorlar orasida ko'milib ketardi. Xuddi shu sabab bilan
`config --seed` faqat `added > 0` bo'lganda yoziladi va
`promote --dry-run` umuman yozmaydi (jurnalda hech qachon bo'lmagan
ko'chirish ko'rinardi va keyingi tergov noto'g'ri izdan borardi).

**`activate`/`deactivate` bitta yordamchida qoldi** (`_set_active`),
amal esa bayroqdan tanlanadi. Ikki nusxa yozilsa biriga audit qo'shilib
ikkinchisi unutilardi — 32-sessiyaning `LEVELS` saboqi.

**Chegara yozuvida geometriya yo'q,** faqat `batch_id` va qatorlar
soni: geometriyaning o'zi `districts` da tarixi bilan turadi (BR-002),
jurnal esa «qachon, kim, qaysi partiya» ga javob beradi. Aks holda har
bir yozuv butun spravochnikning nusxasi bo'lardi.

## 5. Ushlangan defekt — mavjud test buzilardi

`tests/test_admin_audit.py::test_actions_follow_the_object_dot_verb_convention`
har bir amalning obyektini `{"outage", "user"}` to'plami bilan
solishtiradi. Yangi amallar (`region.*`, `boundaries.promote`) uni
**yiqitardi**. Ro'yxat kengaytirildi va nima uchun u qo'lda
yozilgani izohda ochiq yozildi: bu audit qamrab oladigan obyektlar
to'plami, ya'ni yangi obyekt qo'shilishi ko'rib chiqiladigan qaror
bo'lishi kerak, jimgina kengayish emas. **Sandbox ishlaganda bu
darhol ko'rinardi** — oltita testsiz run auditni qanchalik
qimmatlashtirganining aniq o'lchovi.

## 6. Fayllar

| Fayl | O'zgarish |
|---|---|
| `app/admin/audit.py` | `CLI_ROLE`, `SystemActor`, `cli_actor()`, oltita yangi `AuditAction`, `record(actor: Actor \| SystemActor)` |
| `tools/region_admin.py` | beshta o'zgartiruvchi buyruq audit yozadi + docstringda sabab |
| `tools/import_boundaries.py` | `cmd_promote` audit yozadi |
| `tests/test_region_audit.py` | **yangi**, 13 ta bazasiz test funksiyasi (parametrlar bilan 23 ta ishga tushirish) |
| `tests/test_admin_audit.py` | obyektlar ro'yxati kengaytirildi |

Migratsiya **yo'q** (`audit_log` `0002` dan beri bor va `action` — matn),
yangi i18n kaliti **yo'q** (jurnal ichki), yangi bog'liqlik **yo'q**.

## 7. Testning tuzilishi

34-sessiyaning naqshi davom ettirildi — nosozlik rejimining o'zi
yopiladi:

- `test_the_subcommand_table_is_complete` — manbadagi `add_parser`
  ro'yxati jadval bilan **aynan** teng bo'lishi shart. Yangi buyruq
  qo'shilsa test yiqiladi, ya'ni uni avval «o'zgartiruvchi» yoki
  «o'qiydigan» deb tasniflash kerak;
- har bir o'zgartiruvchi buyruq uchun `audit.record(` **chaqirilishi**
  tekshiriladi, simvolning mavjudligi emas (33-sessiyaning defekti);
- **teskari tomon ham qulflangan:** `cmd_list` da `audit.record(`
  **bo'lmasligi** shart — aks holda har bir funksiyaga chaqiruv qo'yib
  chiqish birinchi testni o'tkazardi va jurnal o'zgarishlar tarixi
  bo'lishdan to'xtardi;
- `test_reference_actions_are_actually_used` — katalogda bor, koddan
  chaqirilmaydigan amal bo'sh jurnalning yagona sababi (29-sessiyaning
  hodisalar katalogi bilan bir naqsh).

Nomlash uslubi (`obyekt.harakat`) yangi faylda **takrorlanmadi** — u
`test_admin_audit.py` da qulflangan va ikki nusxadan biri tuzatilib
ikkinchisi unutilardi.

## 8. Keyingi run uchun

> ⚠️ **Yettinchi marta:** `ruff check` va `pytest -m "not requires_db"`.
> Endi **sakkizta** run (§19, 29, 30, 31, 32, 33, 34, 35) tekshirilmagan
> kod qoldirdi. 👤 `cleanup-sessions.ps1` — eng qimmat blok.
>
> **Yozilmagan test:** `region_admin config --key` dan keyin
> `audit_log` da qator **haqiqatan** paydo bo'lishini o'lchaydigan
> `requires_db` testi. Bugun yozilmadi, chunki uni ishga tushirib
> ko'rish imkoni yo'q edi va u CLI ning global `session_scope()` i
> bilan fikstyura sessiyasini bir joyga keltirishni talab qiladi —
> noto'g'ri yozilgan bazali test jim yashil bo'ladi.
>
> **Arxiv qirrasi:** 34-sessiya fayli `34_..._9f2ce89d.md` deb
> nomlangan, uning haqiqiy id si esa `local_61c30020`. Nomni
> tuzatish faylni o'chirishni talab qiladi (`allow_cowork_file_delete`
> — rejalashtirilgan runda **taqiqlangan**), shuning uchun shu yerda
> qayd etildi. 👤

---

## Ilova — BRD dagi qolgan talablar holati

Kod bilan solishtirilgan va **bajarilgan** deb topilganlari (qisqacha):
BR-001 (uch darajali geomodel), BR-002 (`valid_from/valid_to`), BR-006
(`region_config`), BR-007/BR-008 (28-sessiya), BR-012 (`06` §9),
BR-014 (TTL 3 soat), BR-015 (`layer`), BR-016/BR-017 (29-sessiyada
topilgan arxivlanmagan run), BR-019/BR-020 (qamrov vitrinasi), BR-021
(`stats.disclaimer.*`), BR-022 (`stats.warning.young_region`), BR-023
(`app/admin/roles.py`), BR-025 (jitter, `05` §3.1).

**Kod ishi bo'lmaganlari:** BR-003/BR-018/BR-028 — E17/E20 (mahalla
spravochnigi va geokoder) skoupida; BRL-15 (GPS aniqligi og'irlikka
ta'sir qilsin) — `05` §2 da `accuracy` ustuni yo'q va 29-sessiya buni
ataylab hodisaga qoldirgan, ya'ni «Ochiq savollar» ga tegishli;
BRL-09 ning **hudud** darajasi (`<30 holat` → ahamiyatsiz) — bugun
mintaqa darajasida bajarilgan (`app/stats/maturity.py`), tuman
darajasida yo'q, lekin `01` FR-S-901 ham mintaqa haqida gapiradi.

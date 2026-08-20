# 179-run — TZ §11/7 ning kirish yo'li: manbalar reyestri, xabarlar jurnali va `POST /tz/readings`

**Sessiya:** `local_842c68cf` · **Sana:** 2026-08-20 · **Epic:** TZ (yangi qonun)

178-run §11 navbatining oxirgi bandini **qurdi** va uni ataylab ulanmagan
qoldirdi: `app/reports/tzsensor.py` ning `INBOUND` reyestri uchala signalni
ham `built=True, wired=False` deb belgilagan edi. 178 ning «keyingi qadam» i
uchta bandni sanagan; bu run **birinchisini** bajardi — manbalar jadvali va
`POST` endpointi.

---

## 1. Nima qurildi

| Fayl | Nima |
|---|---|
| `alembic/versions/0013_tz_intake.py` | `tz_sources` reyestri, `tz_signals` jurnali, Т-2 triggerlari |
| `app/reports/models.py` | `TzSource`, `TzSignal` |
| `app/reports/tzintake.py` | baza qatlami: reyestr, `seen`/`last`, `record`, `ingest` |
| `app/api/v1/tz.py` | `POST /api/v1/tz/readings`, `GET /api/v1/tz/sources` |
| `app/admin/roles.py` | `TZ_INTAKE`, `TZ_SOURCE_READ` |
| `tests/test_tz_intake.py` | bazasiz: jurnal qatori, javob shakli, ruxsat, Т-1/Т-4 qorovullari |
| `tests/test_tz_intake_db.py` | haqiqiy bazada: Т-2, Т-7, reyestr cheklovlari, sikl xotirasi |

---

## 2. Qarorlar va sabablari

### 🔴 Rad etilgan xabar ham jurnalga yoziladi

`tz_signals` faqat faktlarni emas, **har bir kirgan xabarni** saqlaydi.
Uch sabab:

1. §8 ning operatori buzuq qurilmani ko'rishi kerak (`Rejection.to_operator`);
   HTTP javobida qaytarilgan rad etish faqat **xabar yuborgan qurilmaga**
   boradi, ya'ni hech kimga;
2. «nega В-7 ishlamadi» savolining javobi boshqa hech qayerda yo'q;
3. `accepted` va `reason` bitta qatorda tursa, ular **ajralib keta
   olmaydi** — buni `CHECK (accepted = (reason = 'none'))` ushlab turadi.

### 🔴 `tz_sources` ga tashqi kalit yo'q

Ro'yxatdan o'tmagan identifikator bilan kelgan xabar ham yozilishi shart —
aynan o'sha qator eng qiziq. `FOREIGN KEY` bilan u **yozilmasdi** va hujum
izsiz qolardi.

### 🔴 Reyestr `report_sources` ga qo'shilmadi

`report_sources` (`06` §2) — xabarning **og'irligi**. TZ ning manbasi
og'irlikda umuman qatnashmaydi: В-7 bo'yicha u kvartalni darhol yopadi,
ya'ni §2.1 ning porogini aylanib o'tadi. Bitta jadvalga qo'shish «rasmiy
manba — bu shunchaki og'irroq foydalanuvchi» degan yolg'onni sxemaga yozib
qo'yardi.

### 🔴 Endpoint `admin` tegi ostida, prefiksi `/tz`

§8 javob beradi: rasmiy manbani operator kiritadi va uning har bir amali
jurnalga tushadi — ya'ni yo'l tokensiz bo'la olmaydi. Teg `admin`, chunki
himoya **turi** shu; yo'l esa `/admin/` emas, chunki qabul moderatsiya
emas. Bu ikkita kontrakt testini ta'sir qildi (quyida).

### 🔴 Ruxsat ikkiga bo'lindi

`TZ_SOURCE_READ` (`viewer` da ham bor) va `TZ_INTAKE` (`viewer` da **yo'q**).
Bitta nom ostida bo'lganda §8 ning «operator qila oladi / qila olmaydi»
farqi umuman ifodalanmasdi.

### 👤 Rad etilgan variant: qurilmaning o'z tokeni

Har datchik uchun alohida kalit yangi jadval, aylanma tartibi va qurilmani
bloklash oqimini talab qiladi — ularning birortasi ham TZ da yozilmagan.
Taxminiy sxema **o'ylab topilmadi**: bugun `X-Admin-Token`, ya'ni qurilma
shlyuz orqali yozadi. Savol `PROGRESS.md` ning «Ochiq savollar» ida.

---

## 3. Haqiqiy baza ikkita jim nosozlikni topdi

Sandboxda PostgreSQL 16 + PostGIS 3.5 ko'tarildi (`micromamba`, yangi
prefiks `/sessions/.../tmp/pg`; eski `/tmp/mamba` `nobody` ga tegishli va
yozilmaydi). **Ikkalasi ham bazasiz to'plamda o'tib ketardi.**

### (1) `CHECK` `NULL` ni «buzilmagan» deb o'qiydi

Birinchi variant:

```sql
(channel = 'sensor' AND btrim(cell) <> '') OR (channel <> 'sensor' AND cell IS NULL)
```

`channel='sensor'`, `cell=NULL` da: `btrim(NULL) <> ''` → `NULL`,
`NULL OR false` → `NULL`, `CHECK` esa `NULL` ni qabul qiladi. Ya'ni
**katagi yozilmagan datchik reyestrga tushib ketardi** — aynan cheklov
to'sishi kerak bo'lgan qator. `cell IS NOT NULL` qo'shildi.

### (2) Т-7 ning kaliti mintaqani bilmaydi

`dedup_key()` `(manba|signal|katak|vaqt)` dan quriladi. Global yagona
indeks (`ix_tz_signals_key_accepted`) ikkita shaharning bir xil nomli
qurilmasini to'qnashtirardi va ikkinchisining xabari sababsiz yo'qolardi.
Indeks `(region_id, key)` ga aylandi.

### (3) `tz_sources` ning birlamchi kaliti

Dastlab faqat `source_id` edi — ikkinchi mintaqa uchun darhol
`duplicate key` berdi. `source_id` yetkazib beruvchi bergan nom va global
yagona bo'lishga va'da bermaydi. Kalit `(region_id, source_id)` bo'ldi
(`region_config` bilan bir xil shakl), va shu tufayli `01` NFR-S-02 uchun
alohida indeks kerak emas — mintaqa kalitning birinchi ustuni.

---

## 4. Yiqilgan qorovullar — hammasi ataylab qo'yilgan edi

Sakkizta test yiqildi va oltitasi **178- va undan oldingi runlar
tomonidan aynan shu kun uchun yozilgan** edi:

| Test | Nima qilindi |
|---|---|
| `test_the_registry_separates_built_from_wired` | `wired` endi `True`; `need` bo'sh emas — unda **qolgan** ish |
| `test_the_showcase_reports_the_intake_as_unwired` | → `..._as_wired`, verdikt `ACCURATE`, `flagged=0` |
| `test_the_sensor_intake_is_still_without_an_inbound_channel` | DP-4 **qayta o'qildi**: da'vo yolg'on emas, **chegara ko'chdi** — fakt hali `reports` ga ham, statusga ham yetib bormaydi (`official_fields`/`verified_fields` mahsulot kodida chaqirilmaydi) |
| `test_idempotency_is_incidental_not_enforced` | «ommaviy» ta'rifi yo'l prefiksidan **tegga** ko'chdi |
| `test_the_only_authentication_built_is_a_header_token` | o'sha sabab |
| `test_the_region_parameter_is_optional_everywhere` | `_params()` endi barcha metodlarni o'qiydi, `["get"]` emas |
| `test_permission_names...`, `test_viewer_reads_only` | ruxsat matritsasi |
| `test_region_id_tables_are_known`, `test_every_index_is_classified` | yangi jadvallar va indekslar |

`wired=True` ni **hech narsa ushlab turmasdi** (178 da uni `flagged=3`
ushlab turgan edi), shuning uchun yangi test qo'shildi:
`test_every_wired_signal_has_a_route_that_can_carry_it` — marshrut
haqiqatan bormi va so'rov tanasi `Signal` ning aynan o'sha to'plamini
qabul qiladimi.

### Yana bir matn-qorovul minasiga tushildi

DP-4 ning yangi testi avval regex bilan yozilgan edi va
`app/clustering/tzstatus.py` ning **izohidagi** `tzsensor.verified_fields()`
ga ilindi. `ast` ga o'girildi — xotiradagi «qorovul `ast` bilan» qoidasi
yana bir marta tasdiqlandi.

---

## 5. Natija

* **4679 passed, 1 skipped** — butun to'plam, `requires_db` ham
  (PostGIS ko'tarilgan holda); `ruff` toza.
* `0013` migratsiya haqiqiy bazada `upgrade` va `downgrade` bilan
  tekshirildi; `\d` chiqishi cheklov nomlari ikkilanmaganini,
  qisman yagona indeks va **ikkala** trigger o'rnida ekanini ko'rsatdi.
* Migratsiyasiz yangi sozlama yo'q — `.env.example` o'zgarmadi.

⚠️ **Iflos baza bitta testni yiqitadi.** Butun to'plamni **bir xil**
bazada ikkinchi marta yurgizganda
`test_digest_service_contract::test_outbox_pending_is_actually_queried`
yiqildi (`2 != 3`): u `outbox` ni **global** sanaydi va oldingi
yurishning qatorlari qoladi. Bazani `dropdb`/`createdb` +
`alembic upgrade head` bilan tiklagandan keyin to'plam yashil. Ya'ni
son to'plamning tozaligiga bog'liq, va uni «flaky» deb o'qish xato
bo'lardi.

**Keyingi qadam:** 178 qoldirgan navbatning qolgan ikkitasi —
(2) Т-9 ning jurnal jadvali (`06` §6.4 uchun oluvchilar ro'yxati),
(3) §8 operatorining paneli (`to_operator` rad etishlari ko'rinadigan
joy). Undan keyin TZ §10 ning ТС-201…ТС-220 ini uchidan-uchiga o'lchash.

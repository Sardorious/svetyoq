# 181-run — TZ §8: operatorning qarori va uning jurnali

**Sessiya:** `local_5ad29f82` · **Sana:** 2026-08-20 · **Epic:** TZ §8

179-run qoldirgan navbatning **uchinchi va oxirgi** bandi: «§8
operatorining paneli». 180-run ikkinchisini (Т-9 ning jurnali) yopgan
edi.

---

## 1. Navbatning holati: nima allaqachon bor edi

§8 operatorga **to'rt** narsani ruxsat etadi. Kodni o'qib chiqqanda
ikkitasi allaqachon ulangan ekan:

| Vakolat | Qayerda | Holat |
|---|---|---|
| «внести официальный источник» | `tzsensor.Channel.OPERATOR` + `POST /tz/readings` | 179-run |
| «отметить плановые работы» | `tzsensor.Signal.PLANNED` + o'sha endpoint | 179-run |
| «подтвердить или отклонить спорный случай» | — | **yo'q edi** |
| «закрыть аварию» | — | **yo'q edi** |

Ya'ni «panel» degan so'z ostida qolgan ish — **hodisa** haqidagi
qaror. Buni `tzstatus.is_disputed()` ning docstringi to'g'ridan-to'g'ri
aytib turardi: «Operatorning qarori §11 navbatining keyingi bandida
keladi».

---

## 2. Asosiy qaror: signal emas, qaror

Datchik va rasmiy manba **katak** haqida gapiradi («bu yerda svet
yo'q»). Operatorning qarori **hodisa** haqida («bu hodisa
tasdiqlanmadi»). Ikkalasini bitta jadvalga (`tz_signals`) qo'shish
oson edi va u §8 ning o'zagini yo'qotardi: **signal — dalil, qaror —
vakolat**. Dalilni har qanday manba beradi, qarorni faqat operator
beradi va u har doim imzolanadi.

Shu sababdan yangi toza modul `app/admin/tzoperator.py` va yangi
jadval `tz_operator_actions` (`0015`), `tz_signals` ga qo'shilmadi.

---

## 3. §8 ning taqiqi qanday o'lchanadigan bo'ldi

Hujjat: «Не может: создать подтверждение по собственному мнению **без
внешнего источника**.»

Erkin matnli «asos» maydoni bu taqiqni bajara olmaydi — unga istalgan
so'zni yozish mumkin. Shuning uchun shakl operatordan **asosning
turini** ham so'raydi:

```python
class Basis(StrEnum):
    EXTERNAL = "external"      # rasmiy e'lon, RESga qo'ng'iroq, datchik
    JUDGEMENT = "judgement"    # operatorning xabarlardan chiqargan xulosasi
```

`CONFIRM` + `JUDGEMENT` → `Refusal.OWN_JUDGEMENT`.

Bu operatorni tekshirmaydi (u yolg'on tanlashi mumkin), lekin taqiqni
**ko'rinadigan** qiladi: jurnalda «tasdiqladi, asos — o'z fikri» degan
qator hech qachon paydo bo'lmaydi, va nazoratchi uchun bu bitta
`SELECT`. Ikkinchi qulf bazada:

```sql
CHECK (NOT (accepted AND action = 'confirm' AND basis <> 'external'))
```

Kod tahrirlanadi, cheklov esa migratsiyasiz yo'qolmaydi.

🟢 **Rad etish o'z fikri bilan mumkin.** §8 faqat **tasdiqlashni**
cheklaydi. Rad etish da'vo yaratmaydi, aksincha — tasdiqlanmagan
da'voni olib tashlaydi, ya'ni taqiqning sababi unga qo'llanmaydi.
«Закрыть аварию» ni ham tashqi manba bilan cheklash mumkin edi, lekin
bu **spetsifikatsiyadan qat'iyroq** bo'lardi — bu ham chetlashish.
Savol `PROGRESS.md` ning «Ochiq savollar» iga yozildi.

---

## 4. Eng qiyin joy: rad etish qaysi statusga olib boradi

§5 jadvalida **«Отклонено» degan status yo'q**, Т-5 esa to'qqizinchini
o'ylab topishni taqiqlaydi. Uchta variant ko'rildi:

1. **Vetoni yopib narvonni erkin qoldirish.** Hodisa darhol
   «Подтверждено жителями» ga qaytardi — ya'ni operatorning
   «tasdiqlamadim» degan qarori **tasdiqlashga** aylanardi. Rad
   etilgan.
2. **«Спорно» da qoldirish.** Unda §8 ning «yopish» vakolati
   bajarilmagan bo'lardi: navbatda hodisa abadiy turardi.
3. **Narvonni «Вероятно» da to'xtatish.** Qabul qilindi.

«Вероятно» rostgo'y: xabarlar bor, tasdiq yo'q. §6.2 ga ko'ra bu
statusdan bildirishnoma ketmaydi. Tavqning o'zi §2.3 uchun yozilgan
`cap_at_likely()` — ikkinchi mexanizm yozilmadi.

Kartada esa alohida kalit `tz.card.rejected` (UZ/RU): «Вероятно» ning
oddiy hisoblagichi («1 / 3 — yana 2 ta xabar kutilmoqda») odamga
hodisa hamon tasdiqlanish yo'lida ekanini aytardi, holbuki qaror
allaqachon qabul qilingan.

🔴 **Shu yerda `tzoutage.Cause.OPERATOR` birinchi marta haqiqiy
bo'ldi.** 176-run uni yozgan va i18n matnini ham bergan edi
(«operator tekshirdi va tasdiqlamadi»), lekin uni **ishlab
chiqaradigan hech narsa yo'q edi**: `retracted` faqat «Спорно» da
hisoblanardi. Endi rad etish ham `corrects=True` beradi — §6.4 «Это не
опция» degan joy.

---

## 5. Qaror abadiy emas: `Resolution.covers()`

```python
resolved = resolution is not None and resolution.covers(rebuttals)
```

`saw` — qaror qabul qilingan lahzada sanoqda turgan qarshi dalil
akkauntlari. Yangi akkaunt paydo bo'lsa, veto **qaytadi**.

Sabab: bir marta bosilgan tugma hodisani §2.2 dan butunlay himoyalab
qo'ysa, to'suvchi uchun eng arzon yo'l operatorni **bir marta**
chalg'itish bo'lardi — tasdiqlashni soxtalashtirishdan ancha arzon.

Ro'yxat jadvalda `text[]` bo'lib saqlanadi: qaror qaysi manzarada
qabul qilinganini keyin tiklab bo'lmaydi, chunki qarshi dalillar §2.1
ning sirpanuvchi oynasidan chiqib ketadi.

---

## 6. Т-5 saqlandi

`tzoperator` `TzStatus` ni **umuman import qilmaydi** va `ast`
qorovuli buni o'lchaydi (matn qidiruvi emas — matn qidiradigan
qorovul o'z izohiga ilinadi). Ko'prik naqshi `tzsensor` nikidek:
`resolution_fields()` **lug'at** qaytaradi, `Resolution` tipini
chaqiruvchi (`tzpanel`) yasaydi. Shu tufayli `admin` va `clustering`
bir-birini import qilmaydi.

`Resolution` ning o'zi `tzstatus.py` da e'lon qilingan — `Verified`
bilan bir xil sabab: statusni tanlaydigan modul o'z kirishini o'zi
e'lon qiladi.

---

## 7. Rad etilgan urinish ham yoziladi

§8: «Все действия пишутся в журнал». **Amal** — bosilgan tugma, natija
emas. Faqat muvaffaqiyatli qatorlarni yozish jurnalni aynan eng qiziq
qatorlardan mahrum qilardi. `CHECK (accepted = (refusal = 'none'))`
ikkala da'voni bitta qatorda ushlab turadi (179-run ning naqshi).

Shu sababdan endpoint rad etishda ham `200` qaytaradi va sababni
tanada beradi: `4xx` jurnalsiz o'tib ketardi.

Statusga esa **faqat qabul qilingan** qaror ta'sir qiladi
(`resolution_for()` rad etilgan qatorni ko'rmaydi) — aks holda §8 ning
taqiqi bo'sh joyga aylanardi.

---

## 8. Yo'l-yo'lakay topilgan jim defekt (mahsulot kodida emas, testda)

Butun to'plam **haqiqiy baza bilan** yurgizilganda
`test_digest_service_contract.py::test_outbox_pending_is_actually_queried`
yiqildi: `assert report.outbox_pending == 2`, haqiqatda 32 (yoki 47 —
qaysi fayllar oldin yurganiga qarab).

Sabab: `outbox` da `region_id` yo'q va so'rov butun jadvalni sanaydi,
ya'ni bu testdan **oldin** yurgan boshqa fayllarning qatorlari ham
songa qo'shiladi. Test o'zi o'lchamoqchi bo'lgan narsani emas,
**yurish tartibini** o'lchardi.

Bu **shu running ishi emas**: yangi ikkita test fayli olib tashlanib
tekshirildi — to'plam baribir shu joyda yiqildi. Tuzatildi: mutlaq son
o'rniga **farq** o'lchanadi (`report.outbox_pending - before == 2`).
Farq M08 mutantini (`outbox_pending = 0`) baribir o'ldiradi.

---

## 9. Nima qurildi

| Fayl | Nima |
|---|---|
| `app/admin/tzoperator.py` | toza modul: `Action`/`Basis`/`Refusal`, `decide_action()`, `action_key()` (Т-7), `POWERS` reyestri |
| `app/admin/tzpanel.py` | ulash: `record`, `load_actions`, `resolution_for`, `closed`, `apply_action` |
| `app/admin/models.py` | `TzOperatorAction` + `TZ_OPERATOR_ACTIONS`/`TZ_OPERATOR_BASES` |
| `alembic/versions/0015_tz_operator_actions.py` | jadval, 6 ta `CHECK`, 3 ta indeks, Т-2 ning uch qavatli himoyasi |
| `app/clustering/tzstatus.py` | `Resolution`, `decide(resolution=)`, `Card.resolved`/`rejected`, `REJECTED_KEY`, `_signature()` |
| `app/api/v1/tz.py` | `POST` va `GET /tz/operator/actions` |
| `app/admin/roles.py` | `TZ_OPERATE` va `TZ_ACTION_READ` |
| `app/core/api_requirements.py` | yangi yo'l `REGION_PARAM_PATHS` ga |
| i18n UZ/RU | `tz.card.rejected`, `registry.tzoperator` |
| `tests/test_tz_operator.py` | 74 test, o'n bo'lim |
| `tests/test_tz_operator_db.py` | 18 test, `requires_db` |

Yangilangan kontraktlar: `test_admin_roles.py` (ruxsatlar jadvali),
`test_schema.py` (ustunlar va `region_id` jadvallari),
`test_schema_index_parity.py` (uchta yangi indeks tasnifi),
`test_digest_service_contract.py` (yuqoridagi tuzatish).

---

## 10. O'lchov

* **4808 passed, 2 skipped** — PostgreSQL 18.6 + PostGIS 3.6
  sandboxda ko'tarildi, `requires_db` ning **364** tasi ham yurgizildi.
* Tartib bo'yicha ikki marta: `-p no:randomly` va tasodifiy tartibda —
  ikkalasi ham yashil.
* `0015` haqiqiy bazada `upgrade` → `downgrade` → `upgrade`: cheklov
  nomlari ikkilanmagan, ikkala trigger ham o'rnida, `downgrade`
  funksiyani ham olib ketadi.
* `ruff check app/ tests/ tools/ alembic/` — toza.
* Yangi sozlama yo'q, ya'ni `tools/seed_tz_config.py` ni qayta
  yurgizish shart emas.

---

## 11. Ochiq savollar (👤)

1. **«Закрыть аварию» tashqi manba talab qilsinmi?** Bugun yo'q —
   §8 faqat tasdiqlashni cheklaydi va kod undan qat'iyroq emas.
2. **Datchikning o'z hisob ma'lumoti** (179-rundan qolgan): bugun
   `X-Admin-Token`, ya'ni qurilma shlyuz orqali yozadi.
3. **`disputed` bayrog'i so'rovda keladi**, bazadan o'qilmaydi — TZ
   ning status qatlami `outages` ga hali ulanmagan (DP-4). Ulangandan
   keyin bu maydon so'rovdan olib tashlanadi.

---

## 12. Keyingi qadam

§11 navbatining hammasi qurildi. Qolgani — **TZ §10 ning ТС-201…ТС-220
qabul ro'yxatini uchidan-uchiga o'lchash**: bugun har band o'z
modulining testida nomma-nom bor, lekin butun yo'l bo'ylab (xabar →
sanash → status → bildirishnoma → tuzatish) o'lchanmagan.

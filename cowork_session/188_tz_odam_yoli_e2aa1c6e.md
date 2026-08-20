# 188-run — TZ §10: kim odam va qachon (ТС-202, ТС-203, ТС-204)

**Sessiya:** `local_e2aa1c6e`
**Sana:** 2026-08-20
**Natija:** ✅ 4637 test (+24), `requires_db` 371 (o'zgarmadi), migratsiyasiz,
`ruff` toza. Mahsulot kodida **ikkita** o'zgarish: `count_rebuttals()` ning
`reporters` argumenti endi sukut qiymatisiz, `ZoneVerdict` ga `users`
maydoni qo'shildi. Yangi sozlama, i18n kaliti va API **yo'q**.

---

## 1. Qayerdan boshlandi

187-run keyingi qadam sifatida reyestrdagi qolgan olti bandni qoldirgan
edi va ulardan eng foydalisini nomlagan: ТС-202/ТС-203 — «bitta
akkauntning uchta nuqtasi va bitta r11 katagidagi uchta akkaunt
tasdiqlashda ham, qarshi dalilda ham, tiklanishda ham bir xil ishlashi
kerak». Bu uchligiga ТС-204 (oyna) qo'shildi: uning da'vosi ham
darajaning xossasi haqida, ya'ni bitta modulda tugamaydi.

Reyestrda uchchalasi **bir bosqichli** (`COUNT`) edi, ya'ni
`test_a_single_stage_case_is_never_marked_walked` bo'yicha ular
ta'rifi bo'yicha «yurilmaydigan» hisoblanardi. 185-run bu tuzoqni
allaqachon ko'rsatgan: bosqichlar ro'yxati **da'vodan** chiqadi, `path`
maydonidan emas.

## 2. Yo'l qayerdan o'tadi

§1.1 ning yaqinlashuvi (uchta turli akkaunt, uchta turli manzil,
ustma-ust tushmagan uy katagi) — TZ da bitta joyda yozilgan, lekin
**uch joyda** qo'llanadi:

* §2.1 — tasdiqlash hisobida (`tzcount.evaluate_zone`);
* §2.2 — qarshi dalil hisobida (`tzdispute.count_rebuttals`);
* §4/В-2 — tiklanish hisobida (`tzrestore.close_block`).

Uchala modul ham buni `tzcount.count_witnesses()` ni **qayta ishlatib**
qiladi (ikkinchi va uchinchisining docstringlari buni ochiq aytadi), ya'ni
da'vo modul ichida emas, ularning **orasida** yashaydi. Yo'l shundan
kelib chiqdi: `COUNT` → `DISPUTE` → `RESTORE` → `STATUS`.

Yangi fayl — `tests/test_tz_walk_count.py` (18 test):

1. ТС-202 — bitta akkaunt uchala modulda ham bitta odam
2. ТС-203 — bitta manzil uchala modulda ham bitta odam (va teskari
   qirra: «**либо** три разных указанных адреса» — bitta r11
   katagidagi uchta ko'rsatilgan manzil tasdiqlaydi)
3. ТС-204 — oyna darajaning xossasi, modulniki emas
4. Yo'lning chokidagi da'volar
5. Tripwire lar

## 3. 🔴 `reporters` sukut bo'yicha bo'sh edi

`count_rebuttals()` ning imzosi shunday edi:

```python
reporters: Iterable[str] = ()
```

`tzdispute` ning docstringidagi birinchi 🔴 qaror shundaki, uzilishni
**o'zi xabar qilgan** akkauntning keyingi «menda svet bor» i §2.2 ning
qarshi dalili emas — u §4 ning tiklanish guvohligi (В-4 tugmasi). Bo'sh
sukut qiymati bilan bu qarorni chaqiruvchi **jimgina o'chirib**
qo'yardi. Xuddi o'sha ikkita dalildan:

```
reporters=verdict.users → people=0, vetoed=False → «Подтверждено»
reporters=()            → people=2, vetoed=True  → «Спорно»
```

Ya'ni haqiqiy uzilish tiklanganda avvalgi xabar qilganlarning ikkitasi
tugmani bosishi bilan hodisa «Спорно» ga tushar, tasdiq qaytarib
olinar va §6.4 ning tuzatishi hammaga ketardi — «свет вернулся»
o'rniga. Xatosiz va jurnalsiz. Sukut qiymati olib tashlandi
(`from_zone_verdicts` ning `blocks_with_users` i va `Outage.notifies`
bilan aynan bir xil sabab), tripwire — `inspect.signature`.

## 4. 🔴 Sababi qo'shni modulda edi: `ZoneVerdict` akkauntlarni tashlardi

`reporters` ning yagona to'g'ri manbai — `Witnesses.users`. Lekin
normal yo'l (`evaluate_zone`/`evaluate_levels` → `ZoneVerdict`) uni
**qaytarmasdi**: verdikt faqat sonni (`have`) olib chiqardi.

Demak chaqiruvchi §2.2 ni to'g'ri chaqirishni **xohlasa ham** qila
olmasdi — ikkinchi marta o'zi sanashi kerak edi. Aynan shuning uchun
bo'sh sukut qiymati zararsiz ko'rinardi: uni to'ldiradigan narsa
yo'q edi. `ZoneVerdict.users` qo'shildi (kartada ko'rsatilmaydi, bu
§2.2 ning kirishi). Maydonga sukut qiymati **berilmadi**: `()` bilan
qo'lda yasalgan verdikt xuddi o'sha xatoni qaytarardi.

## 5. ⬜ В-4 akkauntni oladi, manzilni emas (👤 savol)

Yo'lda uchinchisi ham chiqdi, lekin bugun tuzatilmadi. §1.1(3) bo'yicha
bitta uy katagidagi ikkita akkauntdan sanoqqa **bittasi** kiradi.
Sanalgani «свет вернулся» ni bosganda `withdraw_points()` uning
nuqtasini olib tashlaydi — va o'sha lahzada bosilgan qo'shnisi sanoqqa
**ko'tariladi**:

```
oldin: users=('u1','u3','u4'), drops={SAME_HOME: 1}, reached=True
keyin: users=('u2','u3','u4'), drops={},             reached=True
```

Ya'ni В-4 ning birinchi yarmi («убирает точку автора») hisobga umuman
ta'sir qilmaydi. Bu — `tzcount` ning to'sishga qarshi qarorining narxi:
ustma-ust tushgan akkauntlar tashlanmaydi, bittasi qoldiriladi (aks
holda hujumchi begona uy katagi bilan akkaunt ochib haqiqiy fuqaroni
sanoqdan chiqarardi). Xuddi shu sabab teskari tomonda ham ishlaydi,
shuning uchun mahsulot kodi tegilmadi: xatti-harakat **qulflandi**
(test), qaror esa `PROGRESS.md` ning «Ochiq savollar» iga 👤 bilan
yozildi.

## 6. Mutatsiya

Yettita mutant tekshirildi — yettitasi ham KILLED, uchtasi **faqat**
yangi fayl bilan:

| # | Mutant | Verdikt | Kim o'ldirdi |
|---|---|---|---|
| M1 | `reporters` ga sukut qiymati qaytarildi | KILLED | **faqat** `test_tz_walk_count.py` |
| M2 | `ZoneVerdict.users` bo'sh berildi | KILLED | **faqat** `test_tz_walk_count.py` (3 test) |
| M3 | `close_block` uy oynasi bilan sanaydi | KILLED | **faqat** `test_tz_walk_count.py` |
| M4 | qarshi dalil har doim uy oynasi bilan | KILLED | `test_tz_dispute.py` + yangi fayl |
| M5 | §1.1(3) uy katagi tekshiruvi o'chirildi | KILLED | uchala modulning testi + yangi fayl |
| M6 | ko'rsatilgan manzil e'tiborga olinmaydi | KILLED | `test_tz_counting.py` + yangi fayl |
| M7 | `reporters` filtri ishlamaydi | KILLED | `test_tz_dispute.py`, `test_tz_walk.py` + yangi fayl |

Verdikt butun bazasiz to'plamdan olindi (mahalliy nusxada, ~42 s).
Nusxa har mutantdan keyin tiklandi; oxirgi ikki mutantda `/dev/shm`
dagi zaxira chaqiruvlar orasida yo'qoldi (mount emas, **nusxa**
ifloslandi) — nusxa o'chirildi va yakuniy to'plam toza nusxada qayta
yurgizildi.

## 7. Reyestr

`app/release/tz_acceptance.py`: ТС-202, ТС-203, ТС-204 uchun `path`
to'rt bosqichli bo'ldi, `walk="test_tz_walk_count.py"`. Hisob:
**20 banddan 20 tasi qurilgan, 17 tasi uchidan-uchiga** (edi 14),
`clean` hamon `False`. Qolgan uchtasi — ТС-218, ТС-219, ТС-220 — TZ
ning bazadagi taqig'i va sozlamalar tarafida, ya'ni ular
`SCHEMA` bosqichida bir bosqichli bo'lib qoladi va ularni yurish
uchun avval da'voni qayta o'qish kerak.

## 8. Keyingi qadam

Reyestrda qolgan uchtasi (ТС-218 — «o'chirishga urinish → bazaning
rad etishi», ТС-219 — «porogni o'zgartirish → yangi versiya, eskisi
saqlanadi, e'lon qilinadi», ТС-220 — «koddagi son-sozlama → sborka
yiqiladi») hammasi `SCHEMA` bosqichida. Ularning da'vosi bitta
modulda tugamaydi degan gumon bor: ТС-219 ning «publikatsiya» yarmi
§8 ning paneli va §7 ning jurnali orasidan o'tadi, ТС-218 ning
qorovulida esa Т-3 uchun ataylab qoldirilgan teshik bor
(`RECLUSTER_GUC`) — o'sha teshikdan `delete_outages` dan **boshqa**
yo'l o'tmasligini bugun hech nima o'lchamaydi. Shundan boshlash
kerak.

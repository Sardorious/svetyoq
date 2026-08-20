# 189-run — Т-10 teshigining kengligi (ТС-218)

**Sessiya:** `local_ba282a64` · **Sana:** 2026-08-20 · **Epic:** TZ (yangi qonun)

---

## Boshlanishi

188-run «Qayerda to'xtadik» da uchta band qoldirgan edi (ТС-218, ТС-219,
ТС-220 — hammasi `SCHEMA` bosqichida) va ТС-218 uchun aniq savol yozgan:

> ТС-218 ning qorovulida Т-3 uchun ataylab qoldirilgan teshik bor
> (`RECLUSTER_GUC`) va o'sha teshikdan
> `app.clustering.repository.delete_outages` dan **boshqa** yo'l
> o'tmasligini bugun hech nima o'lchamaydi.

Run shu savolni tekshirishdan boshlandi.

## Nima bor edi

`tests/test_outage_delete_guard.py` (183-run) bandning **o'zini**
o'lchaydi va yaxshi o'lchaydi: tasdiqlangan hodisa o'chmaydi, mezon
`confirmed_at` (joriy status emas), tasdiqqa yetmagani o'chadi,
`TRUNCATE` shartsiz rad etiladi, bayroq keyingi tranzaksiyaga sizib
o'tmaydi. Bazasiz tripwire ham bor:

```python
assert owners == ["clustering/repository.py"]   # "sveta.recluster" ni kim yozadi
```

## Topilma: tripwire faqat bitta tomonni qulflaydi

Bu tripwire **ikkinchi eshik qurilmasligini** o'lchaydi. Uch xil yo'l
undan o'tib ketadi.

### 1. 🔴 Bayroq `DELETE` dan keyin ochiq qolardi (mahsulot defekti)

`SET LOCAL` «tranzaksiya bilan o'ladi» degani, ya'ni `delete_outages`
**qaytgandan keyin** ham bayroq o'sha tranzaksiyaning qolgan hamma
so'rovi uchun Т-10 ni o'chirib turardi.

Bu nazariy emas. `tools/recluster.py:680`:

```python
deleted = await cluster_repo.delete_outages(session, doomed)

created: set[uuid.UUID] = set()
for row in rows:
    assignment = await clustering.assign(session, ...)   # o'sha tranzaksiya
```

Bugun `assign` `outages` dan hech nima o'chirmaydi (butun kodda
`delete(Outage)` bitta joyda), ya'ni defekt **hozircha zararsiz** —
lekin uni ushlaydigan narsa yo'q edi. Mavjud DB testi
(`test_recluster_may_delete_but_the_flag_does_not_leak`) **keyingi**
tranzaksiyani o'lchaydi va u har doim toza bo'ladi: `SET LOCAL` ning
ta'rifi shu. O'lchanmagani — **o'sha** tranzaksiyaning qolgan qismi.

**Tuzatildi.** Bayroq `DELETE` dan keyin darhol yopiladi:

```python
await session.execute(select(func.set_config(RECLUSTER_GUC, "on", True)))
await session.execute(update(Outage).where(...).values(merged_into=None))
result = await session.execute(delete(Outage).where(Outage.id.in_(ids)))
await session.execute(select(func.set_config(RECLUSTER_GUC, "off", True)))
```

Teshik endi ikkita ifoda kengligida.

### 2. 🟢 Bor eshikdan yurish

Yangi eshik qurish shart emas: `delete_outages` ni import qilgan
istalgan modul teshikdan o'tadi va bayroqning **nomiga umuman
tegmaydi**. Funksiyaning docstringi «ataylab shu modulda va faqat
qayta hisoblash asbobidan chaqiriladi» deb 183-rundan beri yozib
turardi — o'lchanmagan da'vo, ya'ni oddiy izoh.

Yangi qorovul chaqiruvchini `ast.Call` bilan sanaydi. Qidiruv matn
emas: reyestrning izohi (`app/release/tz_acceptance.py`)
`delete_outages` ni **nomlaydi**, lekin chaqirmaydi.

### 3. 🟢 Nomni boshqacha yasash

Mavjud tripwire `ast.Constant` ni qidiradi. `f"sveta.{name}"` yoki
`"sveta." + "recluster"` undan bemalol o'tadi — bu sinf loyihada bir
marta allaqachon o'lchangan (i18n kaliti f-satr bilan yasalganda
katalog skaneri uni ko'rmasdi).

Yangi qorovul teskari tomondan qulflaydi: PostgreSQL da GUC ni
qo'yishning yagona yo'li `set_config` (xom `SET` ni `05` §1 ning
arxitektura qorovuli allaqachon to'sadi), demak **chaqiruvni** sanash
nomni qanday yasashdan mustaqil. Ikkinchi test o'sha modul ichida ham
faqat bitta sozlama qo'yilishini tekshiradi.

### 4. ⬜ Qorovulning mezoni va status mashinasi (qulflandi, tuzatilmadi)

`0016` `confirmed_at IS NOT NULL` ni o'qiydi. Ustunni **bitta** joy
yozadi — `service.evaluate` ning `CONFIRMED` ga o'tishi
(`app/clustering/service.py:379`). Ya'ni Т-10 ning himoyasi
«tasdiqlangan» degan faktning yagona manbaiga tayanadi va bu bog'liqlik
hech qayerda yozilmagan.

Eng ehtimolli buzilish — moderator yo'li: `status='confirmed'` ni
qo'lda qo'yadigan qaror `confirmed_at` ni yozmasdi va o'sha hodisa
Т-10 dan **tashqarida** qolardi. Bugun `MODERATOR_TARGETS` buni
to'sadi (`rejected` va `merged`), lekin to'siq Т-10 sababidan emas,
`05` §4.4 sababidan qo'yilgan — ya'ni uni kengaytirish qonuniy
ko'rinadigan o'zgarish. 👤 savol `PROGRESS.md` ga yozildi.

## Rad etilgan variant: ТС-218 ni `WALKED` qilish

188-run ТС-202/203/204 ni «bir bosqichli» dan «to'rt bosqichli» ga
o'tkazgan edi va o'sha yo'l bu yerda ham vasvasa qildi: ТС-218 ni
`STATUS` + `SCHEMA` deb yozib `WALKED` ga ko'tarish.

**Qilinmadi.** Ikki sabab:

1. `STAGE_MODULES` TZ ning modullarini nomlaydi
   (`Stage.SCHEMA` → `app.core.tzconfig`), `app.clustering.repository`
   va `tools/recluster.py` esa unda umuman yo'q. Yo'lni «uzaytirish»
   uchun xaritani cho'zish kerak bo'lardi.
2. Yo'lni haqiqatan yuradigan test `requires_db` bo'lardi, bu sandboxda
   esa PostGIS ko'tarilmaydi. Yurmagan testga tayangan `WALKED` — aynan
   66–87 runlarning «tekshirilmagan da'vo» xatosi.

Reyestr hisobi shuning uchun o'zgarmadi: 20/20 qurilgan, 17 tasi
uchidan-uchiga, `clean` hamon `False`.

## Yakun

Yangi fayl `sveta/tests/test_outage_delete_reach.py` — 8 test
(6 bazasiz, 2 `requires_db`). Reyestrda ТС-218 ning `tests` tuplega
qo'shildi (`test_the_registry_finds_every_test_file_that_names_a_case`
buni birinchi yurishdayoq talab qildi — reyestrning qorovuli ishladi).

```
4643 passed, 373 skipped in 56.56s     (bazasiz, jami 5016 — +8)
ruff: All checks passed!
```

Migratsiya, yangi sozlama, i18n kaliti va API **yo'q**.

### Mutatsiyalar

| # | Mutant | Verdikt |
|---|---|---|
| M1 | `set_config(..., "off", ...)` qatori olib tashlandi | KILLED (2 fail, ikkalasi ham yangi fayl) |
| M2 | yopish `DELETE` dan **oldin** ko'chirildi | KILLED (yangi fayl) |
| M3 | `app/admin/service.py` bor eshikdan yuradi | KILLED (yangi fayl) |
| M4 | `MODERATOR_TARGETS` ga `CONFIRMED` | KILLED (yangi fayl) |

M4 ning birinchi urinishi sintaksis xatosi bilan `rc=4` berdi — bu
KILLED emas, buzilgan mutant; qayta yozildi.

### ⚠️ Yurmagan qism

Ikkita `requires_db` testi bu sandboxda **yurmadi**: PostGIS
ko'tarilmadi, `/` (9.6 G, 94 %) ham `/sessions` (9.8 G, 95 %) ham
to'la, `micromamba` ga joy yo'q. Ya'ni «bayroq tranzaksiya ichida
yopiladi» degan da'vo bugun **manba shakli** bo'yicha (`ast`)
o'lchandi, **xatti-harakat** bo'yicha emas. Baza bo'lgan runda
birinchi bo'lib shu ikki test yurgizilsin.

## Keyingi qadam

Reyestrda qolgan ikki band:

* **ТС-219** («Изменение порога в настройках → Новая версия, старая
  сохранена, **публикуется**»). Bugungi `tests` — `test_schema.py` va
  `test_schema_index_parity.py`, ya'ni faqat jadvalning shakli.
  «Publikatsiya» yarmi umuman boshqa joyda: §7 ning `config_journal` i
  bilan §8 ning paneli orasida. 188-run ham buni «bitta modulda
  tugamaydi» deb belgilagan.
* **ТС-220** («Число-настройка в коде → Сборка падает»). Ro'yxati
  yettita fayl, ya'ni har TZ moduli o'z Т-1 qorovulini olib yuradi.
  Bu yerda tekshirish arziydigan narsa — qorovul `ast` bilan
  o'lchanadimi yoki matn bilan (matn qidiradigan taqiq o'z
  docstringiga ilinadi).

# 185-run — §10 ning tiklanish o'qi tugallandi (ТС-209, ТС-211, ТС-213)

**Sessiya:** `local_6e04b23c` · **Sana:** 2026-08-20 · **Epic:** TZ (yangi qonun)

184-run qoldirgan topshiriq: «ТС-209/ТС-211/ТС-213 ni o'sha yo'lga qo'shish,
keyin reyestrdagi qolgan `PER_MODULE` bandlar».

---

## 1. Boshlanish: uchta band «yurilmaydigan» deb yozilgan edi

Reyestrda (`app/release/tz_acceptance.py`) uchchalasining yo'li bitta
bosqichdan iborat edi:

```python
path=(Stage.RESTORE,)
```

Va reyestrning o'z qorovuli buni himoya qiladi:

```python
def test_a_single_stage_case_is_never_marked_walked() -> None:
    for case in CASES:
        if case.depth is Depth.WALKED:
            assert len(case.path) > 1, case.code
```

Ya'ni ta'rifi bo'yicha ular yurilmaydi. Birinchi savol shu bo'ldi: yo'l
haqiqatan bitta bosqichdanmi?

Hujjatning matni javob berdi:

| Band | Проверка | Ожидается |
|---|---|---|
| ТС-209 | 1 человек нажал «свет вернулся» при 20 сообщавших | **Квартал не закрыт** |
| ТС-211 | Авария идёт 6 ч, ответили 3 из 4 опрошенных | Закрытие возможно, доля снижена |
| ТС-213 | Человек не ответил на опрос | **Ничего не изменилось** |

«Квартал не закрыт» va «ничего не изменилось» — bu `close_block()` ning
qaytargan qiymati haqidagi da'vo emas. Ular **natija** haqida: kartada
nima turadi va odamga nima ketadi. `Depth` ning ta'rifi to'g'ri edi,
`path` esa noto'g'ri — bosqichlar ro'yxati navbatdan emas, bandning o'z
da'vosidan chiqadi.

Uchchalasining yo'li shundan keyin:

* ТС-209 — `COUNT` → `RESTORE` → `STATUS` → `NOTIFY_RESTORED`
  (В-4 nuqtani olib tashlaydi, ya'ni sanash ham yo'lda);
* ТС-211, ТС-213 — `RESTORE` → `STATUS` → `NOTIFY_RESTORED`.

---

## 2. 🔴 Topilma: yuborish huquqi yopilmagan kvartalni to'smaydi

Yo'lni uzaytirgach ТС-209 ning ostidan 184-run qorovulining teshigi
chiqdi.

184-run `Closure.notifies` ni sukut qiymatisiz maydonga aylantirdi va
o'shanda o'lchangan savol bitta edi: **status jim turganda** («Данные
устарели») xabar ketmaydimi. ТС-209 esa teskari holat:

* hodisa **tasdiqlangan** — `notifies(TzStatus.CONFIRMED)` rost;
* kvartal esa **yopilmagan** — В-3, bitta odam yopmaydi.

Huquq bu farq haqida hech narsa bilmaydi: §6.2 uni hodisaning
**statusidan** oladi. Ya'ni `Restoration.blocks` dan to'g'ridan-to'g'ri
`Closure` yasagan chaqiruvchi svet qaytmagan kvartaldagi odamga «Свет
вернулся» yuborardi — va 184-run ning yangi qorovuli buni ko'rmasdi,
chunki huquq **rost** edi. Karta to'g'ri, huquq to'g'ri, kvartal
noto'g'ri.

Mutatsiya bilan tasdiqlandi (filtr olib tashlanganda):

```
E   AssertionError: assert (Delivery(...)) == ()
E     Left contains 2 more items, first extra item: Delivery(
E       user_id='s1', cell='b1', outcome=Outcome.SEND,
E       text_key='tz.notify.restored',
E       text_args={'address': 'Uy', 'time': '15:00', 'hours': 0, 'minutes': 50})
```

### Tuzatish

Filtr chaqiruvchining yodidan olinib `Restoration` ga chiqarildi — bu
running **yagona** mahsulot o'zgarishi:

```python
@property
def announced(self) -> tuple[BlockClosure, ...]:
    """§5: «да, **по кварталам**» — xabar chiqadigan kvartallar."""
    return tuple(block for block in self.blocks if block.closed)
```

**Rad etilgan variant:** filtrni testda (yoki har chaqiruv joyida)
qoldirish. Aynan shu 184-run tuzatgan kasallikning ko'chirmasi bo'lardi:
qoida bor, lekin u chaqiruvchining yodida turadi. Ikkinchi chaqiruv
joyi paydo bo'lishi bilan uni unutish vaqt masalasi.

**Rad etilgan variant:** `plan()` ichida `closure.closed` ni tekshirish.
`Closure` — `tzrestored` ning tipi, u `BlockClosure` ni ko'rmaydi va
ko'rmasligi kerak (`05` §1, Т-5). Yopilganlik **kirish** faktiga
aylanardi va yana chaqiruvchining yodida qolardi.

---

## 3. ТС-211 — «Восстановлено» o'qi birinchi marta yurildi

184-run ikkita o'qni yurdi: qisman tiklanish (ТС-210) va jimlik
(ТС-212). Uchinchisi — hamma kvartal yopilgan → **aniq** davomiylik →
xabar — hech qachon yurilmagan edi.

«Доля снижена» solishtirish bilan o'lchanadi: aynan o'sha javoblar
(so'ralgan 4 tadan 3 tasi javob berdi, ulardan 1 tasi «ha» → 33 %)

* hodisaning **birinchi soatida** kvartalni yopmaydi (`need_share`
  0.40, `Blocker.SHARE`);
* **oltinchi soatida** yopadi (`need_share` 0.15).

В-2 ning ikki odami: oprosning «ha» si va tugma bosgan odam — namuna
faqat chorak (§4.1), tugma esa hammada.

### 🔴 Yo'l-yo'lakay: oltinchi soat qiyalikni o'lchamaydi

`required_share(h) = max(0.40 − 0.05·h, 0.15)`. Beshinchi soatda
ifoda aynan `share_floor` ga tushadi, ya'ni ТС-211 ning verdikti
**pasayish tezligiga emas, pastki chekka** bog'liq. Band buzuq emas
(qiyalik nolga aylansa ТС-211 qizaradi), lekin «ТС-211 В-5 ning
qiyaligini qulflaydi» degan xulosa noto'g'ri bo'lardi. Qiyalik shuning
uchun o'z oralig'ida alohida qulflandi:

```python
assert required_share(0, params) == params.restore_answered_share
assert required_share(0, params) > required_share(1, params) > required_share(4, params)
assert required_share(4, params) > floor
assert required_share(5, params) == pytest.approx(floor)   # float: 0.4 − 0.25
assert required_share(6, params) == floor
```

Beshinchi soatda `pytest.approx` kerak: `0.4 - 0.05*5` `0.15000000000000002`
beradi va `max()` aynan shuni qaytaradi. Oltinchida esa `max()`
`floor` ning o'zini qaytaradi, ya'ni tenglik aniq.

---

## 4. ТС-213 — «ничего не изменилось» butun yo'lning natijasi bilan

Bandni oraliq son bilan o'lchash oson edi (`Answers.share` o'zgarmadi),
lekin da'vo shu emas. Shuning uchun yo'l ikki marta yuriladi va
**butun** natija solishtiriladi:

```python
with_silence = _restore_walk(tally_answers(replies, asked=6), ...)
without_them = _restore_walk(tally_answers(replies, asked=2), ...)
assert with_silence == without_them          # karta ham, yetkazishlar ham
```

🔴 **Yolg'iz o'zi kam.** `share` ni umuman o'qimaydigan kod ham shu
testdan o'tardi. Shuning uchun yonida majburiy qarama-qarshi holat:
jimlardan bittasi «нет» desa maxraj o'sadi (В-6) va o'sha kirishda
kvartal yopilmay qoladi — status `CONFIRMED` bo'lib qoladi,
yetkazishlar nol.

Ikkinchi qulf `tally_answers` ning o'zida: `asked` faqat
`Answers.silent` ga tegadi, `share` ga emas. Maxrajni `asked` ga
o'zgartirish (juda tabiiy xato — «40 % опрошенных») butun to'plamni
yiqitadi.

---

## 5. Mutatsiya tekshiruvi

Nusxada (`/sessions/<sid>/m1`), har mutantdan keyin fayl `r0` dan
tiklanadi, verdikt faqat `rc==1` da KILLED.

| # | Mutant | Verdikt |
|---|---|---|
| M1 | `announced` → `tuple(self.blocks)` (filtrsiz) | KILLED — **faqat** uchta yangi test |
| M2 | `required_share` da pasayish yo'q | KILLED |
| M3 | `Answers.share` maxraji `asked` | KILLED |
| M4 | В-3 ning odam sharti (`< 1`) | KILLED (eski to'plam ham) |
| M5 | `withdraw_points` nuqtani olib tashlamaydi | KILLED |

M1 ni faqat yangi testlar o'ldiradi — bu kutilgan, kod ham yangi.
M4 eski to'plam bilan ham o'ladi (`--ignore=tests/test_tz_walk_restore.py`
bilan `rc=1`), ya'ni yangi yo'l unga qo'shimcha kuch bermaydi va
bermasligi ham kerak: yo'lning qiymati modulda emas, **chokda**.

---

## 6. Natija

* `app/clustering/tzrestore.py` — `Restoration.announced` (yagona
  mahsulot o'zgarishi);
* `tests/test_tz_walk_restore.py` — uchta bo'lim, +11 test
  (ТС-209, huquq/kvartal chokining qulfi, ТС-211, В-5 qiyaligi,
  ТС-213 va uning qarama-qarshi holati);
* `app/release/tz_acceptance.py` — uchala bandning `path`/`walk`
  maydonlari va docstringdagi hisob.

To'plam **4571 passed, 371 skipped** (bazasiz; jami 4942, +11),
`requires_db` **370** o'zgarmadi, `ruff check` toza. Migratsiya,
yangi sozlama, i18n kaliti va API **yo'q**.

§10 reyestri: 20/20 qurilgan, **8** tasi uchidan-uchiga (edi 5),
12 tasi `PER_MODULE`, `clean` hamon `False`.

---

## 7. Sandbox

`/sessions` da 1.6 GB bo'sh edi — muhit o'sha yerda qurildi
(`micromamba` + `conda-forge python=3.11`, keyin `pip` bilan to'rt
partiyada). Tizim `python3` hamon **3.10**, ya'ni `StrEnum` yo'q va
repo import bo'lmaydi.

Nozik joy: `asyncpg` **kerak** — usiz 39 test yiqiladi
(`sqlalchemy.dialects.postgresql.asyncpg` import vaqtida qidiradi),
`requires_db` esa baribir `skip` bo'ladi. Va nusxa repo **ildizidan**
olinadi: `deploy-server/` bo'lmasa `test_deploy_web_contract.py`
yiqiladi (9 fail).

To'plam mount ustida emas, `/sessions/<sid>/r0` nusxasida yurgizildi —
42 s.

---

## 8. Keyingi qadam

Reyestrdagi qolgan 12 ta `PER_MODULE` band. Eng foydalisi ikkita
guruh:

* **ТС-202/ТС-203** — §1.1 ning ikkala simmetrik ko'rinishi (bitta
  odam turli nuqtadan, bitta katakdagi uch akkaunt). Ular hozir uchta
  faylda nomma-nom uchraydi, lekin himoyaning **kartaga** yetib
  borishi o'lchanmagan;
* **ТС-214…ТС-217** — ikkita bildirishnoma moduli (`tzoutage` va
  `tzrestored`) bitta yo'lda. 184-run `Stage.NOTIFY_RESTORED` ni
  aynan shular uchun ajratgan edi.

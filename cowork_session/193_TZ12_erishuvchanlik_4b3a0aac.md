# 193-run — TZ §12: poroglarning erishuvchanligi o'lchanadigan bo'ldi

**Sessiya:** `local_4b3a0aac` · **Sana:** 2026-08-20 · **Epic:** TZ

---

## Qayerdan boshlandi

192-run «keyingi qadam» qilib 👤 ulash tartibining 3-bandini
(`service.evaluate()` ni TZ ga burish) qoldirgan edi — va u
**javobsiz savolga tayanadi**: TZ §2.1 zonani tasdiqlaydi (r10/r9/r8),
`outages` esa klasterni; qaysi zonaning verdikti hodisani
tasdiqlashi hujjatda yozilmagan. Uchta o'qish mumkin va kodda birini
tanlab qo'yish §2.1 ni jimgina qayta yozish bo'lardi.

Ya'ni navbatning boshi bloklangan. Qoida bo'yicha keyingi
bloklanmagan ishga o'tildi.

## Nima tanlandi va nega

`§10` (qabul) tugagan — yigirmata banddan yigirmatasi `BUILT`,
o'n yettitasi `WALKED`, qolgan uchtasi (ТС-218/219/220) ta'rifi
bo'yicha bir bosqichli. `§11` navbati 181-runda yopilgan. Qolgan
yagona qurilmagan bo'lim — **§12, «Что проверить до начала»**:

> «в какой доле реальных аварий за первые 20 минут набиралось
> 3 человека с разных адресов в одной клетке r10? … Это
> **единственная** проверка, без которой браться за §2 не стоит.»

Butun §2 shu tekshiruvsiz qurilgan va buni loyihaning o'zi ikki
joyda ochiq yozib qo'ygan (`tzconfig.py` va `admin/registries.py`):
👤 qarori (2026-08-19) bo'yicha Toshkent tarixi ishlatilmaydi va
sonlar Samarqandning **o'z** ma'lumotidan keyin o'lchanadi.

🔴 **Qaror bajarilmas edi.** U tarixning *manbasini* almashtirgan,
savolini emas — lekin repoda javobni **biror** tarixdan
hisoblaydigan yo'l umuman yo'q edi. Ya'ni «keyin o'lchaymiz» degan
va'da uchun asbob yo'q edi va u'ni yozmasdan «keyin» hech qachon
kelmasdi. Bu run o'sha asbobni qurdi.

## Qurilgani

* `app/clustering/tzreach.py` — yangi modul (toza yadro + `load()`).
* `app/clustering/repository.reach_candidates` (+`_stmt`,
  `ReachCandidate`).
* `tests/test_tz_reach.py` (31, bazasiz), `tests/test_tz_reach_db.py`
  (6, `requires_db`).
* `test_tz_counting.MODULES` ga yangi modul (Т-1/Т-4 reyestri).
* `tzconfig.py` va `admin/registries.py` ning §12 haqidagi izohlari
  asbobga havola oldi.

## Uchta 🔴 qaror

### 1. Maxraj tasdiqlangan hodisalardan olinmaydi

Eng oson yo'l — `confirmed_at IS NOT NULL` qatorlarni olib,
qanchasida porog yig'ilganini sanash — **har doim 100 % beradi**:
tasdiqlangan hodisa ta'rifi bo'yicha porogdan o'tgan hodisa. Savol
o'z javobini o'zi tasdiqlaydigan shaklga aylanar va §12 hech qachon
«завышены» demasdi.

Shuning uchun maxrajga faqat **sanoqdan mustaqil** dalili bor
hodisalar kiradi: `outages.layer == 'official'` (RES e'loni,
datchik, operator kiritgan manba — §8 va В-7). Bunday hodisa yo'q
bo'lsa javob **`UNKNOWN` / `NO_INDEPENDENT_TRUTH`**, «erishuvchan»
emas. Bugungi bazada rasmiy qatlam bo'sh, ya'ni asbobning bugungi
halol javobi aynan shu — va u buni **aytadi**, son o'ylab topmaydi.

`reach_candidates_stmt` statusni **umuman ko'rmaydi** va buni
bazasiz qorovul qulflaydi (`confirmed_at`/`status` matnda yo'q):
filtrga jimgina qo'shilgan status o'lchovni doiraviy qilardi.

### 2. §2.3 o'lchov paytida o'chiq

§2.3 kam odamli zonada porogni ikkigacha tushiradi va u §2.1 ning
raqamlari **erishilmas bo'lishi mumkinligi uchun** yozilgan. Uni
o'lchovda yoqib qo'yish — o'lchanayotgan nosozlikni o'lchov vaqtida
yamash: deyarli har bir hodisa «yetdi» bo'lib chiqardi.
`evaluate_levels()` shu yerda `active_users` **siz** chaqiriladi va
buni `ast` qorovuli qulflaydi (chaqiruvlarning kalit so'zlari
sanaladi — matn qidiradigan qorovul o'z izohiga ilinardi).

### 3. Sanoq qayta yozilmaydi

Asbob `tzcount.evaluate_levels()` ni chaqiradi. Sanoqni bu yerda
qayta yozish oson edi va u §12 ni foydasiz qilardi: o'lchov mahsulot
qo'llaydigan qoidadan **boshqa** qoida haqida son berar, va o'sha son
bilan §7 ning raqamlari o'zgartirilardi.

## Ikkita son, bitta emas

O'lchov lahzasi — har xabarning vaqti (sanoq faqat o'shanda o'sadi).
Shundan ikkita javob chiqadi:

* `reached_in_first_window` — §12 ning to'g'ridan-to'g'ri savoli;
* `reached_ever` — kechroq bo'lsa ham yig'ildimi.

Farqi (`window_only`) amaliy: porog birinchi oynada yig'ilmasa,
lekin keyinroq muntazam yig'ilsa, §7 da o'zgarishi kerak bo'lgan
narsa **porog emas, oyna**. Bitta o'lchov (birinchi oynaning oxiri)
bu farqni umuman ko'rsatmasdi.

Uchinchi son — `people_histogram`. Ulushning o'zi kam: «0 %» ikki
xil dunyoni bildiradi — hamma joyda **ikkitadan** yig'ilgan (porogni
bittaga tushirish yetarli) va hamma joyda **bittadan** (masala
butunlay boshqa). §12 ning «набирался один-два» iborasi aynan shu
taqsimot haqida.

## Т-1: xulosa ham sonsiz

§12 ning «в большинстве случаев» i kodda `0.5` bilan emas, ikkita
**o'lchangan** sonni solishtirish bilan ifodalanadi:
`looks_high = missed > reached_in_first_window`. Tenglikda `False` —
teng bo'linish «ko'pchilik» emas. `min_episodes` esa **sukut
qiymatisiz**: son §7 da yo'q, ya'ni kodda tanlab qo'yish Т-1 ni
buzardi, sukut qiymati esa chaqiruvchini u haqda o'ylashdan xalos
qilardi (187/190/191/192 runlarning naqshi).

## 🟡 Yo'l-yo'lakay topilganlar

* **`SPEC` konstantasi olinmadi.** `SPEC` li modul
  `admin/registries.py` indeksida qator bo'lishi shart
  (`test_admin_registries.py` shuni tekshiradi), indeks esa
  **reyestrlarni** ko'rsatadi — hujjat qatorlarini kod bilan
  solishtiradiganlarni. `tzreach` da bunday qator yo'q: u §12 ning
  bandlarini emas, **tarixni** o'lchaydi. Sabab modulda yozildi.
* **`test_tz_acceptance` tripwire i ishladi:** izohda ТС-204 ni
  eslatgan edim va reyestr «bu fayl o'sha bandning testi emas» deb
  qizardi. To'g'ri javob reyestrga qator qo'shish emas — izohni
  tuzatish.
* **`starting_values()` ning kaliti to'liq** (`tz.confirm.house_users`).
  Т-3 testi avval qisqa kalit bilan yozilgan va **jimgina** o'tib
  ketgan: noma'lum kalit e'tiborsiz qoladi, ya'ni «boshqa sozlama»
  aslida o'sha sozlama edi. Testda endi kalitning mavjudligi ham
  tekshiriladi.

## Mutatsiya

To'qqizta mutant, **to'qqiztasi ham KILLED**. Bittasi
(`probe_moments` dan `sorted` olib tashlash) birinchi o'tishda
**omon qolgan**: test ikkita lahza bilan yozilgan edi va tartibsiz
to'plam tasodifan tartiblangan chiqqan. Ikkita test kuchaytirildi —
sakkizta lahza va `minutes_to_reach` ning **eng erta** lahza ekani
— shundan keyin o'ldi.

## Yakun

Butun to'plam haqiqiy bazada: **5154 passed, 2 skipped** (edi
5115/2), `requires_db` **404** (+6), `ruff` toza. Migratsiya,
sozlama, i18n va API **yo'q**.

## Keyingi qadam

1. 👤 savol o'zgarmadi: **qaysi zonaning verdikti hodisani
   tasdiqlaydi** — ulash tartibining 3-bandi shusiz bajarilmaydi.
2. §12 ning «Дополнительно» yarmi (Samarqandda nechta tuman va
   kvartal bor, nechtasida foydalanuvchi bor) allaqachon
   hisoblanadi — `tzsource.BlockRegistry`. Uni §12 ning javobiga
   qo'shish qisqa ish.
3. Asbobga chaqiruvchi yo'q: `tools/` da hisobotni chop etadigan
   skript §12 ni odam yuritadigan qilardi.

# 190-run — §3 ning maxraji manbaga ega bo'ldi (`3-source`)

**Sessiya:** `local_9f43bdd4` · **Sana:** 2026-08-20 · **Epic:** TZ (yangi qonun)

---

## Qayerdan boshlandi

189-run oxirida 👤 qaror olindi: **TZ ni mahsulot quvuriga ulash endi
birinchi navbatdagi ish**, §10 reyestrining qolgan ikki bandi
(ТС-219, ТС-220) kutadi. Tartib `PROGRESS.md` ning «Odam qaroriga
bog'liq bloklar» bo'limida beshta qadam bilan yozilgan va birinchisi —
**`3-source`**: §3 ning maxrajini to'ldiradigan so'rov.

Sabab 187-runda yozilgan: `tzscale.from_zone_verdicts()` ning
`blocks_with_users` argumenti o'shanda sukut qiymatisiz qoldirilgan
edi, ya'ni chaqiruvchi javob berishga **majbur**. Javobni
**topadigan yo'l** esa yo'q edi. Majburiyat bor, imkoniyat yo'q —
bunday holatda birinchi chaqiruvchi qo'lidagi eng yaqin ro'yxatni
(bugun xabar qilgan kvartallarni) beradi va §3 jimgina o'z-o'zidan
bajariladigan shartga aylanadi.

---

## Nima qilindi

### 1. So'rov — `reports.queries.blocks_with_users`

`app/reports/queries.py`: `BlockUsersRow` (neytral tuzilma) va
`blocks_with_users(session, *, region_id)`. So'rovning `SELECT` i
alohida funksiyada (`blocks_with_users_stmt`) — `purge_exact_geom_stmt`
bilan bir xil sabab: shakl bazasiz to'plamda ham qulflansin.

Uchta qaror sabab bilan yozildi.

**(a) Oyna YO'Q.** Qo'shni agregat so'rovlarning hammasi `since` oladi
(`active_users_*`, `cells_with_reports_*`), ya'ni uni bu yerga ham
qo'shish eng tabiiy harakat edi. §3 esa «есть пользователи» deydi —
**mavjudlik**, bugungi faollik emas. Oyna qo'yilsa maxraj «bugun
xabar qilgan kvartallar» ga qisqarardi, ya'ni sanoq ham, maxraj ham
bitta hodisadan yig'ilib, ulush har doim bajarilardi va §3 dan faqat
«не менее 3» qolardi. Bu aynan 187-run yopgan nuqsonning boshqa
qavatdagi ko'rinishi.

Mavjudlikning yagona izi — xabarning o'zi: foydalanuvchining «uy
katagi» hech qayerda saqlanmaydi (`tzcount.Witness.home_r11` ni
chaqiruvchi beradi). `geom_exact` 90 kundan keyin `NULL` ga o'tadi
(`05` §3.2), `h3_r9` esa qoladi — tarixiy mavjudlik maxfiylik
tozalashidan keyin ham o'qiladi.

**(b) Bloklangan akkaunt sanalmaydi.** Maxrajni **oshirish** —
hujum: bo'sh kvartallarda ochilgan akkauntlar tumanning porogini
ko'taradi (50 kvartalning 40 % i 12 tanikidan ikki baravar ko'p) va
tasdiqlashni abadiy uzoqlashtiradi. To'sish soxtalashtirishdan arzon
bo'lmasligi kerak — §1.1 ning ustma-ustlik qarori bilan bir xil
sabab. `trust_score` esa **filtr emas**: u dalilning og'irligi
haqida (`05` §4.3), mavjudlik haqida emas.

**(v) `DISTINCT` — odam sanaydi, xabar emas.** Son §3 ga o'zi kerak
emas («bormi» yetarli), lekin chegaradagi katakning tumanini u hal
qiladi.

### 2. Ulash qatlami — `app/clustering/tzsource.py`

Yangi modul: so'rov natijasini `from_zone_verdicts()` ning ikkita
argumentiga (`district_of`, `blocks_with_users`) aylantiradi.
`tzscale` **toza** qoldi — u bazani ko'rmaydi. Joyi va nomi mavjud
naqldan (`tzintake`, `tzreceipts`, `tzpanel`): ulash qatlami
iste'molchi paketda turadi va `SPEC` konstantasi **olmaydi** —
`SPEC` reyestr modulining belgisi va `tests/test_admin_registries.py`
uni indeksdan qidiradi.

🔴 **Bu modulning yagona qarori — chegaradagi katak.**
`from_zone_verdicts()` `district_of` ni `Mapping[str, str]` deb
oladi, ya'ni **bitta kvartal bitta tumanga** tegishli. Baza bunga
kafolat bermaydi: r9 katagi (~349 m) tuman chegarasini kesib o'tishi
mumkin va o'sha katakdagi xabarlar ikki xil `district_id` bilan
yozilgan bo'ladi (`district_id` har bir xabarga alohida
biriktiriladi). Ikkala tumanga qo'shish oson yo'l edi va u ikkita
narsani buzardi:

1. bitta ko'chadagi uzilish **ikkita** tumanning sanoqchisini
   ko'tarardi — §3 ning birinchi jumlasi aynan buni taqiqlaydi
   («сто сообщений с одной улицы не доказывают, что район без
   света»);
2. shahar darajasi tumanlarning **natijasini** sanaydi, ya'ni ikki
   marta sanalgan kvartal shaharga ham ikki marta ta'sir qilardi.

Shuning uchun: **foydalanuvchisi ko'p bo'lgan tuman yutadi**,
tenglikda identifikatori kichigi (Т-3 — bazadan kelgan tartibga
tayanish qorovulni bo'sh qilardi; tenglik nazariy emas: chegaradagi
kvartalda ikkala tomondan bittadan odam eng ehtimolli holat).
Tanlanmagan tomon yo'qolmaydi — `straddling` da qoladi.

**Tumani yo'q katak** (`district_id IS NULL`, `05` §5.3 defekti)
maxrajga ham, sanoqqa ham kirmaydi, lekin `unassigned` da qaytadi:
uning o'sishi maxrajni kamaytiradi va §3 ning ulushini
yengillashtiradi.

### 3. Reyestrning halolligi

`tzscale.RULES` ning `3-source` qatori `built=True` bo'ldi, lekin
o'rniga **yangi qator** qo'shildi:

> `3-wired` — «§3 fuqaro oqimida chaqirilmaydi — masshtab hamon
> `06` §5.3 dan», `built=False`.

`3-source` ni yashil qilib to'xtash vitrinani yolg'onga aylantirardi:
maxraj bor, hisob bor, lekin `tzscale.evaluate()` ni mahsulot quvuri
chaqirmaydi va `outages.scale` ni hamon eski narvon to'ldiradi.
`_probe_tzscale` ning verdikti shu sababdan **salbiy** bo'lib qoladi.

---

## Testlar

**`tests/test_tz_source.py`** (18 test, bazasiz) — besh bo'lim:
reyestrning shakli; chegaradagi va tumansiz kvartal; **yo'l**
(reyestrdan §3 ning verdiktigacha); so'rovning shakli; `RULES`.

Yo'lning markaziy testi — `test_the_registry_denominator_reverses_the_district_verdict`:
to'rtta kvartal tasdiqlangan, reyestrda 12 ta foydalanuvchili kvartal
→ `need = 5`, tuman **tasdiqlanmaydi**; xuddi shu dalil bo'sh maxraj
bilan → `need = 3`, tuman **tasdiqlanadi**. 187-run buni `tzscale`
ning ichida o'lchagan edi, endi u **haqiqiy manba** bilan o'lchanadi.

Yonida `test_without_the_query_the_caller_cannot_even_map_a_block_to_a_district`:
reyestrsiz `district_of` ham yo'q, ya'ni §3 umuman bo'sh natija
qaytaradi — shuning uchun `3-source` ulashning **birinchi** qadami.

**`tests/test_tz_source_db.py`** (7 test, `requires_db`) — bazasiz
to'plamda hech qachon qizarmaydigan uchta da'vo: bir yil oldingi
xabar kvartalni maxrajda qoldiradi; bloklangan akkaunt maxrajni ham,
sanoqni ham ko'tarmaydi; qo'shni mintaqa maxrajga tushmaydi. Fikstyura
ataylab **ikkita tuman va ikkita mintaqa** quradi (143-run ning
«fikstyura ajratmasa, qulf yo'q» qoidasi) va tuman identifikatorlari
`sorted()` bilan qaytariladi — tenglik qoidasi «kichigi yutadi»
deydi, ya'ni `uuid4` ning tasodifiy tartibi testni gohida o'tkazib,
gohida yiqitardi.

`tests/test_tz_counting.py` ning `MODULES` ro'yxatiga
`app/clustering/tzsource.py` qo'shildi (Т-1 va Т-4 qorovullari).

---

## O'lchov

**Butun to'plam haqiqiy bazada:** PostgreSQL 18.6 + PostGIS 3,
`alembic upgrade head` `0001…0016` — **5042 passed, 2 skipped**
(85 s). `ruff` toza. Migratsiya, yangi sozlama, yangi i18n kaliti va
yangi API **yo'q**.

189-run qoldirgan topshiriq ham bajarildi: o'sha runda yozilib,
bazasizlik sababli **yurgizilmagan** ikkita `requires_db` testi
(`test_outage_delete_reach.py` + `test_outage_delete_guard.py`, 16
test) birinchi bo'lib yurgizildi — hammasi yashil, ya'ni
`SET LOCAL` bayrog'ining tranzaksiya ichida yopilishi va
`session.begin_nested()` bilan qilingan tuzatish tasdiqlandi.

**Mutatsiya (12 mutant):** 11 KILLED, 1 ekvivalent.

| Mutant | Natija |
|---|---|
| M1 `is None` → `is not None` | KILLED |
| M2 tenglik teskari (`district > chosen`) | KILLED |
| M3 `>` → `>=` (ko'p odamli tomon) | KILLED |
| M4 `len(names) > 1` → `> 0` | KILLED |
| M5 `unassigned` jimgina tashlanadi | KILLED |
| M6 `districts` takrorlanadi | KILLED |
| M7 `blocks` ga `unassigned` qo'shiladi | KILLED |
| M8 `is_blocked` filtri yo'q | KILLED |
| M9 `count(distinct)` → `count` | KILLED |
| M10 `GROUP BY` faqat katak bo'yicha | KILLED |
| M11 mintaqa filtri yo'q | KILLED |
| M12 `join` → `outerjoin` | **SURVIVED — ekvivalent** |

M12 ekvivalentligining **ikkita mustaqil sababi** bor:
`reports.user_id` `NOT NULL` va `users` ga tashqi kalit (mos
kelmaydigan qator bo'lishi mumkin emas), hamda `LEFT JOIN` da bo'sh
tomon `users.is_blocked IS false` shartidan baribir o'tmaydi
(`NULL IS false` → `false`). Test yozilmadi: ekvivalent mutantni
«o'ldirish» uchun yozilgan test mahsulotning xatti-harakatini emas,
so'rovning yozilish uslubini o'lchagan bo'lardi.

---

## Rad etilgan variantlar

* **Mavjudlikka oyna qo'yish** (masalan «oxirgi bir yil»). §3 da ham,
  §7 da ham bunday son yo'q, ya'ni uni kodda o'ylab topish Т-1 ga zid.
  👤 savol sifatida yozildi.
* **Chegaradagi katakni ikkala tumanga qo'shish.** Yuqorida —
  §3 ning birinchi jumlasini buzardi.
* **Tumansiz katakni «noma'lum tuman» chelagiga yig'ish.** Ikkita har
  xil tumanning kvartallarini bitta porogga qo'shardi.
* **`3-source` ni yashil qilib to'xtash.** Vitrina «§3 tayyor» deb
  ko'rsatardi, holbuki uni hech kim chaqirmaydi.
* **`trust_score` bo'yicha filtr.** Past ishonchli odam ham shu
  kvartalda yashaydi; ishonch dalilning og'irligi haqida.

---

## Keyingi qadam

👤 tartibning **2-bandi**: sanash qatlami — `clustering/service.evaluate()`
`count_independent` / `evaluate_confirmation` o'rniga
`tzcount.count_witnesses()` ni oladi. `Witnesses.users` chaqiruvchiga
yetib borishi shart (188-run `ZoneVerdict.users` ni aynan shuning
uchun qo'shgan — `count_rebuttals(reporters=…)` usiz jimgina
noto'g'ri ishlaydi).

**Sandbox retsepti bu run uchun ishladi va yozib qo'yildi:**
`/tmp/pg180` (PostgreSQL 18.6 + PostGIS 3) mavjud, `/tmp/mamba/envs/py311`
da `pytest`/`sqlalchemy`/`h3` bor. Har chaqiruvda **yangi**
`initdb -D /tmp/pgd190` va `listen_addresses='127.0.0.1'`,
`port=5490` shart; `pg_ctl start` chaqiruvlar orasida **o'ladi**,
shuning uchun `start` + `alembic` + `pytest` bitta bash chaqiruvida
bo'lishi kerak. To'plam `mount` ustida emas, `/sessions/<sessiya>/tmp/`
dagi nusxada yuritildi (60 s bazasiz, 86 s baza bilan).

# 126-sessiya — harnessning o'zi va ikkita bazasiz modul

**Sessiya:** `local_4a52c32e-92fd-45e7-8403-f74dbcb8c48f` · **Sana:** 2026-08-12
**Natija:** ✅ `tools/_mut.py` ning **uchta** yolg'on verdikti tuzatildi va
qulflandi (`tests/test_mut_harness.py`, 11 test) · ✅ `app/core/etag.py`
**11/11** · ✅ `app/admin/auth.py` **11/11** · 22 mutatsiya (9 birinchi
o'tishda KILLED, 13 survivor: 12 qulflandi, 1 ekvivalent) · yolg'on
survivor yo'q · mahsulot kodi tegilmadi ·
3271 passed / 232 skipped (3503 yig'ildi, o'lchangan) · `ruff` toza ·
⛔ disk ketma-ket **beshinchi** run to'la — `requires_db` yana yurgizilmadi

---

## Nima uchun aynan shu ish

125 ning «keyingi qadam» ro'yxatidagi birinchi ikkita band 👤 odam
ishiga bog'liq edi: `cleanup-sessions.ps1` (disk) va `tools/_mut.py`.
Disk tekshirildi — `/` da **34 MB**, `/sessions` da **0**, eski
`pgdata120`/`pgdata121` esa boshqa sandbox foydalanuvchisiniki
(`Permission denied`). Ya'ni `requires_db` bugun ham yo'q va 125
qoldirgan servis/API nishoni (`stats/service.py`, `geo/queries.py` —
bazaga tegadi) yana olinmaydi.

Ikkinchi band esa aslida **odam ishi emas** edi: 125 uni «tuzatilsinmi
yoki o'chirilsinmi, agent `allow_cowork_file_delete` ni chaqira
olmaydi» deb yozgan. O'chirish — ha, agentning qo'lidan kelmaydi;
**tuzatish** esa oddiy `Edit`. Shu sababdan run ikki qismga bo'lindi:
avval asbob, keyin o'lchov.

---

## 1. Harness uch joyda yolg'on gapirardi

119-run ning butun o'lchovi shu fayl tufayli bekor bo'lgan edi
(`pytest --timeout=120` → `pytest-timeout` yo'q → `rc=4` → eski verdikt
`returncode != 0` → **bitta ham test yurmagan holda** har mutant
«KILLED»). 120–125 runlar buni `/tmp` da qayta yozilgan nusxa bilan
aylanib o'tdi, ya'ni **qarz repoda qoldi** va keyingi run yana o'sha
tuzoqqa tushishi mumkin edi.

Tuzatilgani:

1. **`verdict(rc)`** — `KILLED` faqat `rc == 1`, `rc == 0` survivor,
   qolgani (`2` uzilish, `3` ichki xato, `4` buyruq qatori, `5` test
   topilmadi) → `MutationHarnessError`. Ya'ni o'lchanmagan run endi
   `KILLED` ham, `SURVIVED` ham emas.
2. **`targets(spec)`** — `tests` maydoni bo'shliq bo'yicha bo'linadi.
   Ilgari butun satr **bitta** argument sifatida berilardi: nishon ikki
   fayldan oshgan zahoti `pytest` yo'lni topa olmay `rc=4` qaytarardi.
   Bu **birinchi partiyadayoq otildi** — beshta mutatsiyaning uchtasi
   `XATO` deb chiqdi, eski verdikt bo'lganda esa uchalasi «KILLED» deb
   yozilardi va `etag.py` bugun **8/11** o'rniga soxta «11/11» olardi.
3. **Qo'llanmagan mutatsiya endi xato.** Ilgari «manba matni topilmadi»
   va «bir necha marta uchraydi» holatlari `survivor` deb qaytarilardi,
   ya'ni **tegilmagan** kod «testlar hech narsani ushlamadi» degan
   xulosa berardi. Bu ham bugun otildi: `sort_keys=True` fayl ichida
   ikki marta uchraydi (biri — docstring), `ensure_ascii=False` ham.

Uchala qoida `tests/test_mut_harness.py` da qulflandi (11 test),
`main()` esa `XATO` larni alohida sanaydi va ularni survivor bilan
aralashtirmaydi.

**Saboq (120 ning saboqining davomi):** o'lchov asbobining o'zi
testlanmagan bo'lsa, uning bergan raqami dalil emas. 120 verdiktni
tuzatgan, lekin **testsiz** tuzatgan edi — shuning uchun tuzatish
`/tmp` dagi nusxada qoldi va repoda yana ikkita shu sinfdagi xato
yashirin turdi.

---

## 2. «Toza modullarda qarz qolmadi» — uchinchi marta tor xulosa

123 «mahsulot yadrosida mutatsiyasiz modul qolmadi» dedi → 124 uni
bekor qildi (oltita o'lchanmagan toza modul topdi) → 125 o'sha oltitani
tugatib «toza modullarda qarz qolmadi» dedi. 126 buni **sanadi**, va
sanoq yana boshqa raqam berdi.

`app/` ning har bir moduli `ast` bilan o'qildi va tranzitiv importlari
bo'yicha tasniflandi (`sqlalchemy`, `fastapi`, `aiogram`, `asyncpg`,
`starlette`, `httpx`, `alembic`, `app.db` — «iflos»):

* **92** modul toza (bazasiz, HTTP siz);
* ulardan mutatsiya bilan o'lchangani — **28** ta (16 mahsulot moduli +
  12 reyestr).

Ya'ni 125 ning xulosasi **124 sanagan ro'yxat** haqida edi, butun toza
to'plam haqida emas. Qolgan ro'yxat `EpicProgress.md` §4 ning 🟡
qatoriga yozildi — u bazadan mustaqil, ya'ni disk bloki uni to'xtatmaydi.

Bugungi ikki nishon shu ro'yxatdan tanlandi: ikkalasi ham kichik,
ikkalasi ham **tashqi shartnomani** bajaradi (kesh va autentifikatsiya),
ya'ni jim defektning narxi yuqori.

---

## 3. `app/core/etag.py` — 11 mutatsiya, 5 KILLED, 6 survivor

Survivorlar avval **kengaytirilgan** to'plamda (156 test: `map`, `geo`,
`heatmap`, `openapi`, `api_requirements`, `nfr_appendix`) qayta
yurgizildi — 125 ning usuli. Oltalasi ham omon qoldi, ya'ni **yolg'oni
yo'q**.

**Birinchi sinf — algoritmning parametrlari umuman o'lchanmagan.**
`sort_keys` dan tashqari hech biri (`separators`, `ensure_ascii`,
`DIGEST_SIZE`) testga ko'rinmasdi, chunki mavjud testlar hash ni faqat
**o'zi bilan** solishtirardi (`payload_etag(x) == payload_etag(x)`).
Narxi ko'rinmas emas: parametr o'zgargan deploydan keyin mazmuni
o'zgarmagan **har** javob yangi `ETag` oladi — barcha mijozlar keshi
bir vaqtda bekor bo'ladi va `/map` snapshoti qayta yuklanadi. Bu qaror
bo'lishi mumkin, lekin tasodif bo'lmasligi kerak. Qulf — oltin qiymat
(`"b591c425ea2383980ecc1a11f9eab730"`) hamda uzunlik shartnomasi
(`2 + 2 × DIGEST_SIZE`, to'qnashuv ehtimoli: ikki xil snapshot bitta
`ETag` olsa mijoz eskirgan xaritani `304` bilan cheksiz saqlab qolardi).

**Ikkinchi sinf — `If-None-Match` ni `RFC 9110` dan torroq o'qish.**
Uchtasi ham javobning **to'g'riligiga** tegadi:

| Mutatsiya | Nima bo'lardi |
|---|---|
| `header = if_none_match` (`strip` siz) | `" * "` tanilmasdi — `*` yuboradigan mijoz har safar `200` olardi (jim degradatsiya) |
| `"*" in header` | tarkibida `*` bo'lgan **begona** `ETag` `304` olardi — **yolg'on** kesh moslik |
| `split(", ")` | bo'shliqsiz ro'yxat (`"a","b"`) bo'linmasdi |

Oltalasi qulflandi (+5 test), keyin oltalasi ham qayta KILLED.

---

## 4. `app/admin/auth.py` — 11 mutatsiya, 4 KILLED, 7 survivor

**124 ning refleksivlik sinfi xavfsizlik qatlamida takrorlandi.**
`MIN_TOKEN_LENGTH` va `ACTOR_NAMESPACE` ni butun repo faqat
konstantaning **o'zi** orqali tekshirardi:

* `test_admin_auth`: `short = "c" * (MIN_TOKEN_LENGTH - 1)`;
* `test_security_posture_contract`: `uuid5(auth.ACTOR_NAMESPACE, …)`;
* `test_region_audit_db`: o'sha nomlar fazosini import qiladi.

Ya'ni `24 → 8` ham, nomlar fazosining almashishi ham **yashil**
qolardi. Holbuki `01` §20 kafolati (`app/admin/security.py:
session_password_policy`) aynan shu ikkovini parol siyosatining o'rnini
bosuvchi deb ataydi: «o'rnini bosgan xossalar boshqa nom ostida turadi
(`MIN_TOKEN_LENGTH`, `compare_digest`, sozlanmagan holat → `403`)».

125 «konstantaning **katalogi** bo'lsa refleksivlik xavfi yo'q» degan
qoidani chiqargan edi (i18n kalitlari `test_i18n_key_contract` bilan
qulflangani uchun omon qolgan edi). 126 uni to'ldiradi: **prozadagi
kafolat katalog emas** — `security.py` konstantani *ataydi*, lekin
qiymatini qayta sanamaydi. Xavf «konstanta tashqi shartnomaga
chiqadimi va uni **mustaqil** fayl qayta sanaydimi» savolida qoladi.

`actor_id` uchun narx aniq: u `audit_log` da **saqlanadi**. Nomlar
fazosi o'zgargan deploydan keyin o'sha moderator yangi aktor sifatida
ko'rinadi va eski yozuvlari uzilib qoladi — ya'ni «kim nima qildi»
(E8 ning butun maqsadi) faqat oxirgi deploydan beri javob beradi.
Ikkalasi absolyut qiymat bilan qulflandi.

**Vaqt bo'yicha oqish — manba matnini o'qimasdan.** `compare_digest`
ni `==` ga almashtirish ham, birinchi moslikda `return` qilish ham
javobda umuman ko'rinmaydi. Yechim — chaqiruvlarni sanash: to'rtta
yozuvli reyestrda birinchi token bilan autentifikatsiya qilinadi va
`compare_digest` **to'rt marta** chaqirilgani tekshiriladi. Mutantlarda
mos ravishda 0 va 1 chaqiruv chiqadi, ya'ni ikkala xossa ham
xulq-atvor darajasida qulflandi.

Qolgan ikki qulf: rad etish **sababi** (`missing_token` ↔
`invalid_token` — sarlavhasiz mijoz va noto'g'ri token bir xil sabab
olsa jurnal bo'yicha ikkovini ajratib bo'lmasdi) va ikki nuqta
atrofidagi bo'shliq (`aziz : moderator : …` — qo'lda tahrirlanadigan
`.env` uchun eng ehtimolli xato; `strip` siz `authenticate` **jimgina**
rad etardi).

**Ekvivalent (1 ta).** Bo'sh token qorovuli (`not name or not token` →
`not name`) — bo'sh token `len("") < MIN_TOKEN_LENGTH` tekshiruvi bilan
**to'liq soyalangan**. Empirik tasdiq: 336 kirishda (nom × rol × token ×
to'rt joylashuv) natija bit-aynan bir xil, farq faqat jurnal sababida
(`token_malformed` ↔ `token_too_short`). Birinchi urinishda taqqoslash
noto'g'ri chiqdi — ikki `exec` qilingan modulda `Actor` **har xil sinf**
bo'lgani uchun hamma natija «farq» ko'rinardi; taqqoslash
`{token: (name, role)}` shakliga keltirildi.

---

## Ogohlantirishlar

* ⚠️ **Bash chaqiruvining haqiqiy chegarasi o'zgaruvchan.** Bir
  chaqiruvda 120 s da uzildi (`timeout_ms` berilmagan) va uzilgan
  partiya **mutant faylni repoda qoldirdi** (`separators` mutanti
  `app/core/etag.py` da). Darhol `diff … .orig` bilan ko'rilib
  tiklandi. Qoida: har partiyadan keyin `diff`, kengaytirilgan
  to'plamda partiya **3 mutantdan** oshmasin va `timeout_ms` **aniq
  berilsin** (280000 ishladi).
* ⛔ Disk: `/` da 34 MB, `/sessions` da 0. Eski `pgdata*` — boshqa
  sandbox foydalanuvchisiniki. 👤 `cleanup-sessions.ps1`.

---

## Keyingi qadam — 127-run

1. 👤 `cleanup-sessions.ps1`, keyin `-m requires_db` va mutatsiya
   servis/API qatlamiga (`stats/service.py`, `geo/queries.py`).
2. Diskdan mustaqil davom: `app/bot/reply.py` (`05` §6.2 verdiktlari),
   `app/notifications/render.py`, `app/geo/osm.py`, `app/obs/metrics.py`
   (Prometheus matn eksporti), `app/admin/digest.py`.
3. 👤 `test_recluster_db.py` izolyatsiyasi; 👤 `ruff format` savoli.
4. 👤 serverda: eski `deploy` stekini o'chirish, `init_tls.sh`,
   polling → webhook; prod tekshiruvi.

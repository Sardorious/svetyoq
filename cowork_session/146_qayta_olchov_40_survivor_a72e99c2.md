# 146-run — 144 ning «0 survivor» i qayta o'lchandi: 10 KILLED, 40 SURVIVOR

**Sessiya:** `local_a72e99c2-da11-418c-b9b9-0b00a6e941ef`
**Sana:** 2026-08-13
**Epic:** E5 / E6 / E14 / E16 (mutatsiya qamrovi)
**Natija:** `clustering/repository.py` + `reports/queries.py` — 50 mutatsiya,
**10 KILLED / 40 SURVIVOR**. Qirqtasining 39 tasi yangi
`tests/test_query_boundaries_db.py` (36 test) bilan qulflandi; qolgan bittasi
(`fc-drop-layer`) allaqachon bazasiz to'plamda o'lardi.
Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**.

---

## 1. Nishon va sabab

145 qoldirgan tartibning (1) bandi: **144 ni qayta o'lchash.** 144 o'sha
ikkala faylni «46 mutatsiya → 46 KILLED, 0 survivor» deb yopgan edi, lekin
o'lchov `reset` siz olingan; 145 esa iflos baza har mutantga soxta `KILLED`
berishini isbotlagan. Ya'ni 144 ning raqami natija emas, **da'vo** edi.

Da'vo tekshirildi va **rad etildi**. 144 ning jadvalidan (o'sha faylning §4
va §5 bo'limlari) 50 mutatsiya qayta tiklandi — 144 ning 46 tasi va anker
aniqligi uchun bo'lingan bir nechtasi — va `reset` bilan qayta o'lchandi:

| O'lchov | 144 (`reset` siz) | 146 (`reset` bilan, to'liq to'plam) |
|---|---|---|
| KILLED | 46 | **10** |
| SURVIVOR | 0 | **40** |

Ya'ni bu ikkala faylning shartlaridan **80 %** i o'lchov paytida
qulflanmagan edi.

## 2. Harnessning uchta yangiligi

### 2.1. 🟢 Mutatsiya repoda emas, **nusxada** qo'llanadi

144 ikki marta repoda mutatsiyalangan fayl qoldirgan (`bash` SIGKILL beradi,
`finally` omon qolmaydi). 146 da nishon fayl `/tmp/rN/sveta/` **nusxasida**
o'zgartiriladi:

```
/tmp/r1/sveta … /tmp/r4/sveta   ← repodan `cp -r`
/tmp/rN/*.md                    ← ildizdagi hujjatlarga symlink
/tmp/mut146/ref/                ← etalon (mutatsiyadan oldin tiklash uchun)
```

Bu qaror darhol o'zini oqladi: bitta partiya `150000 ms` da uzildi va
uchala ishchida `app/reports/queries.py` mutatsiyalangan holda qoldi —
**repo esa tegilmadi**. Nusxalar `ref` dan tiklandi, run oxirida repo
fayllarining `md5` i etalon bilan bit-aynan.

### 2.2. 🟢 Uchta ishchi parallel — bitta chaqiruvda uch mutatsiya

To'liq `-m requires_db` yolg'iz 42 s, uchtasi birga 62–75 s. Har ishchining
o'z bazasi bor (`sveta_w1…w4`), har mutatsiyadan oldin u `sveta_tpl`
shablonidan qayta yaratiladi (0.2 s). To'rtta ishchi ham sinaldi —
115 s, `bash` limitiga juda yaqin, shuning uchun **uchta** qoldirildi.

### 2.3. 🔴 Yangi yolg'on sinfi: **to'liq bo'lmagan ishchi nusxasi**

Bazasiz to'plam bilan tekshirish boshlangach beshta mutatsiya `9 failed`
bilan `KILLED` chiqdi. Qorovul — son o'zi: to'qqiztasi ham har safar bir
xil edi. Mutatsiyasiz nazorat yurgizishi `9 failed` ni **mutatsiyasiz**
ham ko'rsatdi:

```
tests/test_deploy_web_contract.py — deploy-server/ topilmadi
```

`r3` va `r4` ishchilarida ildizdagi `deploy-server` symlinki qolib ketgan
edi. Ya'ni **o'sha ishchiga tushgan har qanday mutatsiya avtomatik
«KILLED»** bo'lardi. Beshtasi ham symlink qo'yilgandan keyin qayta
o'lchandi va beshtasi ham **SURVIVOR** chiqdi.

**Qoida:** ishchi nusxasi repo bilan **ildizigacha** bir xil bo'lishi kerak;
mutatsiyasiz baseline har ishchida alohida yashil bo'lmaguncha o'lchov
boshlanmaydi.

### 2.4. 🔴 `-m requires_db` — **tor tanlov**

144 ning saboqi «tor test **fayli** tanlovi yolg'on SURVIVOR beradi» edi.
146 shuni bir pog'ona yuqorida ko'rdi: `-m requires_db` ning o'zi ham tor
tanlov. `fc-drop-layer` butun `requires_db` to'plamida omon qoldi va aynan
**bazasiz** to'plamda o'ldi (`tests/test_confirmation.py` — qatlam
belgilash). Shuning uchun 146 da har survivor ikkinchi marta, bazasiz
to'plamda o'lchandi: 41 tadan bittasi shu yerda o'ldi.

**Qoida:** verdikt **butun to'plam** bo'yicha chiqariladi —
`requires_db` va bazasiz yarim birgalikda.

## 3. Nima uchun 40 survivor — «fikstyura ajratmasa, qulf yo'q»

143 ning naqshi to'liq kuchida qaytdi. Survivorlarning deyarli hammasi
uchta oilaga tushdi:

| Oila | Nechta | Nima uchun ko'rinmagan |
|---|---|---|
| yarim ochiq davr `[since, until)` ning uchlari | 17 | fikstyurada chegaraga **aynan** tushadigan qator yo'q edi |
| `ORDER BY` (tartib) | 7 | bitta qatorli fikstyurada har qanday tartib bir xil |
| `DISTINCT` (odam ↔ xabar) | 5 | har odam bittadan xabar yozardi |
| filtr/chegara (`>=` ↔ `>`, `layer`, `status`, `kind`) | 11 | shartni buzadigan qator umuman yo'q edi |

144 ning «yozuv yo'lidagi so'rov qarzsiz» bashorati shu bilan **rad
etildi**: `repository.py` ham, `queries.py` ham birlamchi yozuv yo'lida,
lekin o'nlab shart baribir qulflanmagan. To'g'ri tushuntirish boshqacha —
oxirigacha boradigan ssenariy shartning **borligini** ko'rsatadi,
**chegarasini** emas. Chegarani faqat chegarada turgan qator ko'rsatadi.

## 4. Yangi test fayli — `tests/test_query_boundaries_db.py`

36 test, hammasi so'rov funksiyasini **to'g'ridan-to'g'ri** chaqiradi (bot
yo'lidan o'tkazish qaysi shart ushlaganini yashirardi). Fikstyura
(`world`) har testga o'zining mintaqa + tuman + mahallasini beradi.

Qamrov: `find_candidate` (oyna cheti, eng yaqin nomzod, `eps`),
`find_open_at` (yopilgan hodisa, `confirmed` ustunligi, `eps`),
`load_evaluation_state` (tuman ↔ mahalla), `stats_rows_started_between`
(yarim ochiq davr, `limit`, tartib), `outage_ids_started_in`,
`fingerprint_rows`, `count_open`, `delete_outages`, va `reports/queries.py`
ning 20 ga yaqin funksiyasi.

Ikkita test birinchi urinishda **ajratmadi** va qayta yozildi:

* `fingerprint_rows` tartibi — kutilgan ro'yxat bilan solishtirish ishlamadi:
  `ORDER BY started_at` da barcha kalitlar teng bo'lganda Postgres qatorlarni
  baribir «to'g'ri» ketma-ketlikda qaytardi (ikkita ham, beshta qator bilan
  ham). Ishlagan shakl — **jismoniy tartibni o'zgartirish**: iz o'qiladi,
  bitta qator `UPDATE` bilan uyum oxiriga ko'chiriladi, iz qayta o'qiladi va
  ikkalasi solishtiriladi.
* `active_users_near` — bitta testda ikkala da'vo (oyna cheti + `DISTINCT`)
  bir-birini yashirdi: oyna ichidagi ikkinchi xabar chetdagisini keraksiz
  qilardi. Ikkita testga bo'lindi.

## 5. Yashil holat

| O'lchov | 146 | 145 |
|---|---|---|
| `-m requires_db` | **291 passed** | 255 |
| bazasiz to'plam | **3435 passed, 1 skipped** | 3435 |
| yig'indi | **3726 passed, 1 skipped** | 3690 |
| `ruff check app tools tests alembic` | toza | toza |
| migratsiya | yo'q (`0011` head) | `0011` |

⚠️ `ruff format --check` repoda **126 fayl** uchun yiqiladi — bu 146 dan
oldin ham shunday edi va CI faqat `ruff check` ni yurgizadi (`Makefile`
dagi `lint` maqsadi esa `format --check` ni ham chaqiradi, ya'ni u
allaqachon qizil). Yangi fayl `ruff format` dan o'tkazilgan.

⚠️ Bazasiz to'plam **repo mount ida 165 s da ham tugamaydi** (44 %), `/tmp`
dagi nusxada esa 41 s. Yakuniy o'lchov shu sababli nusxada olindi;
nusxaning repo bilan aynanligi `diff -r --brief` bilan isbotlangan.

## 6. Muhit

`/tmp` oldingi sandboxdan saqlanib qolgan (`micromamba` muhitlari `py311`
va `pg`). Yangi baza: `initdb -D /tmp/pgdata146`, port `55146`,
`-k /tmp -c listen_addresses=127.0.0.1`, `alembic upgrade head` (`0011`),
so'ng shablon `sveta_tpl` (`CREATE EXTENSION postgis` + `upgrade head`).
Prelude — `/tmp/sv146.sh`; server har `bash` chaqiruvi oxirida o'ladi,
shuning uchun har chaqiruv `source /tmp/sv146.sh` + `pgup` bilan boshlanadi.

## 7. Qoldirilgan qarz

1. **145 ning o'z o'lchovi ham qayta ko'rilishi kerak.** 145
   `notifications/` ni faqat `-m requires_db` da o'lchagan va 8 survivor
   topgan; §2.4 ga ko'ra bu tanlov to'liq emas. Uning 8 ta yangi testi
   zarar qilmaydi, lekin «2 KILLED / 8 survivor» raqami hali ham yarim
   o'lchov.
2. `notifications/subscriptions.py` va `service.py` — 145 ning ro'yxatidagi
   (2) band, hali o'lchanmagan.
3. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi.
4. 👤 `cowork_session/` dagi nusxa juftliklari:
   `100_repository_va_queries_qulflandi_70dfe57e.md` ↔
   `144_…_70dfe57e.md` va to'rtta `28_*` fayli. Agent fayl o'chira olmaydi
   (`allow_cowork_file_delete` taqiqlangan) — odam push dan oldin o'chirsin.
5. 👤 144 ning uchta axlat fayli (`4hs3xo8b`, `58pozfd9`, `klc5pety`)
   `sveta/` ildizida **endi yo'q** — odam o'chirgan, bu band yopildi.

`git` bu runda **chaqirilmadi**.

# 74-sessiya — `01` §19 «Notifications» kanallar jadvali kodda

**Sessiya:** `local_cca44107`
**Sana:** 2026-08-10
**Epic:** E13 (bildirishnomalar) / kontrakt qatlami — `01` §19

---

## Qayerdan boshlandi

73-run uchta nomzod qoldirgan edi: `01` §19 «Notifications» (kanallar
jadvali va «радиус подлежит калибровке» qatori), `01` §26/§27
«Risks»/«Assumptions» (hech qachon o'qilmagan), yoki
`GET /api/v1/admin/monitoring` (endi sakkizta reyestr vitrinasiz).

§19 tanlandi. Sabab: uchinchi nomzod `05` §7.2 endpoint sathini
tahrirlaydi (48-run uni qulflagan), §26/§27 esa kod bilan bog'lanishi
qiyin ro'yxatlar. §19 esa aksincha — bo'limning **oxirgi jumlasi**
allaqachon kodda (43-run: radius `region_config` da), jadvalning oltita
qatori esa hech qachon o'qilmagan.

---

## Asosiy qaror — `Статус в регионе` bitta ustunda ikki xil da'vo saqlaydi

Ustunda uch xil qiymat bor va ular bir turdagi gap emas:

* «MVP» va «Phase 2» — **reja**. Ular *qachon* deydi.
* «Не входит» — **siyosat**. U *hech qachon* deydi va sababini aytadi.

Ikkilik «qurilgan / qurilmagan» o'qish shu farqni yo'qotadi va ro'yxatni
**teskari** tartibda ko'rsatadi: uchta «Не входит» qatori bugun 100%
bajarilgan bo'lib chiqadi, «Phase 2» esa qarz bo'lib. Aslida teskarisi
xavfliroq:

* «Phase 2» qatori buzila **olmaydi** — kelajak haqidagi gapni bugungi
  commit yolg'onga aylantirmaydi;
* «Не входит» qatori bitta migratsiya bilan yolg'onga aylanadi va buni
  hech kim sezmaydi.

Shuning uchun ikkita savol ikkita o'qga ajratildi: reja qatori uchun
«**yo'l** bormi», siyosat qatori uchun «**qorovul** bormi».

### `Reach` — kanal bugun yeta oladimi

| Qiymat | Ma'nosi |
|---|---|
| `DELIVERS` | To'liq yo'l: hodisa qaror qiladi, manzil topiladi, transport yuboradi |
| `SURFACED` | Hujjat atagan artefakt mahsulotda **bor**, lekin §19 ning yukini olib yurmaydi |
| `NONE` | Kodda hech narsa yo'q |

### `Standing` — da'voni nimadir ushlab turibdimi

| Qiymat | Ma'nosi |
|---|---|
| `HELD` | Mexanizm bor va u aynan shu da'vo uchun yozilgan |
| `BORROWED` | Ushlab turilibdi, lekin **boshqa** bo'limning sababi bilan yozilgan mexanizm tomonidan |
| `UNHELD` | Bugun rost, ertaga rostligini hech narsa kafolatlamaydi |
| `PREMATURE` | Kelajak fazasi — ushlaydigan narsa hali yo'q (67-run ning `EXTERNAL` sinfi) |

**`BORROWED` faqat «Не входит» qatorida bo'la oladi**, va bu qoida
tasodifiy emas. Mavjudlik haqidagi da'vo kod **o'chirilganda** buziladi,
uni ushlaydigan test esa ta'rifi bo'yicha o'sha kanal haqida yozilgan.
Yo'qlik haqidagi da'vo kod **qo'shilganda** buziladi, mavjud bo'lmagan
narsa haqida esa hech kim test yozmaydi — demak qorovul, agar bor
bo'lsa, doim **birovniki**. `assess()` buni majburiy qiladi.

---

## Eng jim topilma — `SURFACED`, va u MVP qatorida

«In-App (веб-баннер) | MVP | Дёшево».

Repoda `#banner` **bor**: `web/index.html` da element, `web/app.js` da
`banner()` funksiyasi. Ya'ni hujjat atagan artefakt joyida va har qanday
qidiruv uni topadi. Lekin unga faqat **xarita diagnostikasi** chiqadi:
`map.tiles_missing`, `map.stale`, `map.empty`, `map.error` va qamrov
ogohlantirishlari. Hodisa haqidagi bildirishnoma u yerga hech qachon
tushmaydi.

**Va tusha olmaydi ham.** §19 ning yetkazish qoidasi «при подтверждённом
инциденте **в радиусе подписки**» deydi; obuna esa `users.tg_id` ga
bog'langan va faqat bot orqali yaratiladi
(`app.notifications.subscriptions.add` ← `app.bot`). Vebda foydalanuvchi
identifikatori yo'q va `01` §20 ga ko'ra bo'lmaydi ham.

Ya'ni ikkinchi MVP kanali **tugallanmagan ish emas** — u o'zi meros
qilib olgan qoida bilan ziddiyatda. Bu 70-run ning PG-S4 topilmasi bilan
bir sinf: tuzatishning uchala yo'li ham qulflangan hujjatni tahrirlaydi,
shuning uchun tuzatilmadi.

**Ikkinchi yarmi sxemada.** `notifications` da kanal ustuni yo'q va
`UNIQUE (user_id, outage_id)` (`05` §2.4) bir hodisa uchun bitta qator
beradi. Bitta kanal uchun bu aynan to'g'ri kafolat — outbox
`at-least-once`, ya'ni takroriy urinish bir odamga ikki marta xabar
yuborardi. Ikkita kanal uchun esa u **to'siq**: bir foydalanuvchi bir
hodisa haqida ikkala kanalda ham xabar ololmaydi, Phase 2 dagi Web Push
esa migratsiyasiz umuman qo'shilmaydi. Bugun hech narsa yiqilmaydi
(ikkinchi kanal yo'q) — ya'ni defekt emas, **narx**.

---

## `BORROWED` — uchta qator, bitta qorovul, to'rtinchi sabab

Hujjat uchta boshqa sabab keltiradi:

| Kanal | `Обоснование` |
|---|---|
| Email | Нет пользовательских email, ПДн не собираются |
| SMS | Стоимость несовместима с некоммерческой моделью |
| WhatsApp | Нет подтверждённого спроса |

Repoda esa uchalasini **bitta** mexanizm ushlab turibdi: 71-run ning
`USERS_ALLOWED_COLUMNS` oq ro'yxati. Har uchala kanal manzilni talab
qiladi (`email`, `phone`), manzil `users` ga ustun bo'lib tushadi, oq
ro'yxat esa yangi ustunni to'sadi.

Uning sababi esa **to'rtinchi** narsa: `01` §20 ning «ПДн не
собираются» qatori. Narx haqida ham, tasdiqlanmagan talab haqida ham
repoda hech narsa yo'q.

Oqibati: §20 ning ПДн pozitsiyasi qayta ko'rilsa — u bugun ochiq savol
(`tg_id` ning psevdonimligi, 71-run) — §19 ning **uchta** qatori bir
vaqtda qorovulsiz qoladi va §19 buni sezmaydi.

Test buni tasvirlamaydi, **o'lchaydi**: `USERS_ALLOWED_COLUMNS` ga
`email` yoki `phone` qo'shilsa fayl yiqiladi.

---

## Teskari yo'nalish: e'lon qilinmagan yo'l

§19 da **kunlik hisobot** yo'q. `app/jobs/daily_digest.py` xuddi shu
`Sender` transporti bilan `DIGEST_CHAT_IDS` ga yozadi (19-run).

«Telegram (in-bot)» qatori uning o'rnini bosmaydi: auditoriya obunachi
emas (operator chati), obuna ham, radius ham yo'q va matn hodisa haqida
emas, sutka haqida. §19 kanallarni **auditoriya** bo'yicha sanaydi,
transport bo'yicha emas — aks holda «Telegram» qatori har qanday
yuborishni yutib yuborardi.

---

## Yetkazish qoidasi — uchala bandi bog'landi

| Iqtibos | Kod |
|---|---|
| «при подтверждённом инциденте» | `clustering.service:NOTIFIABLE_TOPICS` |
| «в радиусе подписки» | `notifications.subscriptions:find_matching` |
| «подлежит калибровке отдельно» | `notifications.params` — `region_config` ning `notify.*` kalitlari (43-run) |

Iqtiboslar paragrafda **so'zma-so'z** qidiriladi: matn qayta yozilsa
test yiqiladi.

⚠️ **Mexanizm bor, qiymat esa hali meros.** `region_config` bo'sh
bo'lsa `SUBSCRIPTION_DEFAULT_RADIUS_M` ishlaydi va uning standarti —
hujjat «могут не соответствовать плотности застройки махаллей» degan
aynan o'sha **500 m**. Son hujjatdan parse qilinib `bootstrap()` bilan
solishtiriladi: kalibrlash bo'lganda fayl yiqiladi va qayd etilishini
talab qiladi.

---

## Hisob

| | |
|---|---|
| `HELD` | 1 (Telegram) |
| `BORROWED` | 3 (Email, SMS, WhatsApp) |
| `UNHELD` | 1 (In-App) |
| `PREMATURE` | 1 (Web Push) |
| E'lon qilinmagan yo'l | 1 (kunlik hisobot) |
| `accurate` | **`False`** |

Hech narsa tuzatilmadi **ataylab**: uchala sabab ham hujjat yoki
mahsulot qaroriga bog'liq (70-, 71-, 73-run bilan bir sinf).

---

## Mutatsiya

**26 mutatsiya, 0 survivor** (+2 nazorat: bitta ekvivalent qayta yozish
va bitta bo'sh — ikkalasi ham kutilganidek survivor).

Mutatsiyalar besh guruhda: reyestr qiymatlari, `assess()` qoidalari,
parser ichki qismlari, `01` hujjatining o'zi, va **tekshirilayotgan
kod** (`USERS_ALLOWED_COLUMNS`, `web/app.js`, `Settings`,
`NOTIFIABLE_TOPICS`, `UniqueConstraint`).

**Ikkita survivor topildi va tuzatildi:**

1. Jadvaldan qator yo'qolsa, uning bahosi reyestrda **kimsasiz**
   qolardi — `build_report` ni `orphans: list[str] = []` ga aylantirish
   sezilmasdi. Yangi test: `test_an_orphan_assessment_stops_the_report`.
2. `SURFACED` uchun `surfaced_as` va `carries` ning **alohida**
   majburiyligi o'lchanmasdi — faqat ikkalasi yo'q holat testda edi,
   ya'ni `or` ni `and` ga aylantirish o'tib ketardi. Test
   parametrlashtirildi (uchta holat).

**Bitta o'lik shart topildi va olib tashlandi:** `SURFACED` +
«Не входит» ni alohida taqiqlash. Yuqoridagi `reach is not Reach.NONE`
sharti uni allaqachon to'sadi, ya'ni ikkinchi nusxa hech qachon
bajarilmasdi va uni olib tashlash hech qayerda sezilmasdi — 73-run ning
survivori bilan aynan bir sinf (ustun qorovuli ikki joyda bir xil xabar
bilan takrorlangan edi).

---

## Natija

* `app/notifications/channels.py` — yangi modul.
* `tests/test_notification_channels_contract.py` — 61 test.
* `pytest -m "not requires_db"` → **1997 passed, 1 skipped** (+61).
* `requires_db` — 231, o'zgarmadi.
* `ruff check app tools tests alembic` — toza.
* Migratsiya yo'q.

---

## 👤 To'rtta savol

1. **In-App qatorining taqdiri.** Qoida vebda boshqacha o'qiladimi
   (ko'rinib turgan hududdagi tasdiqlangan hodisa, obunasiz), qator
   «Phase 2» ga ko'chadimi, yoki veb foydalanuvchini taniydimi (§20
   tahriri)? Kod hech birini o'zi tanlay olmaydi.
2. **`notifications` ga `channel` ustuni.** Ikkinchi kanal paydo
   bo'lganda `UNIQUE (user_id, outage_id, channel)` kerak — ya'ni
   `05` §2.4 tahriri va migratsiya.
3. **§19 uchun o'z qorovuli.** Narx va talab sabablari hujjatda qolib,
   kod faqat ПДн ga tayanadimi — yoki §19 ning o'zi uchun mexanizm
   yoziladimi?
4. **Obuna radiusining meros standarti.** 500 m Toshkentniki; oraliq
   qiymat E11 gacha qo'yiladimi?

---

## Sandbox

`/tmp/sv59` **o'n oltinchi marta ketma-ket** joyida (104 paket + `ruff`),
`$HOME` esa 100%. ⚠️ **Yangi holat:** shu run davomida `/` ham 100% ga
to'ldi va `TMPDIR=/tmp/tmpdir` ishlamay qoldi — pytest
`No usable temporary directory found` bilan yiqildi. `/tmp` da boshqa
loyihaning (Flutter/dart) qoldiqlari bor va ular `nobody` ga tegishli,
ya'ni **o'chirib bo'lmaydi** (`Permission denied`, ~2.9 GB).

Yechim: `TMPDIR=$HOME/tmpd` (`/sessions/<nom>/tmpd`). `$HOME` 100%
ko'rinsa ham unda pytest ning vaqtinchalik fayllari uchun joy yetadi.

👤 `cleanup-sessions.ps1` ni har run oldidan yurgizing.

# 19 — `daily_digest`: `05` §8 ning oxirgi fon vazifasi

**Sessiya:** `local_cd2c2d1f` · **Sana:** 2026-08-08 · **Natija:** `05` §8
jadvalidagi oltala vazifa ham kodda; 592 bazasiz test (+36), `requires_db`
135 (+7), `ruff` yashil, `0006` migratsiya offline ishladi.

---

## Nima uchun aynan shu ish

18-sessiya oxirida bloklanmagan kod ishidan ikkitasi qolgandi:
`daily_digest` va ikkinchi mintaqani haqiqiy OSM importi bilan sinash.
Ikkinchisi tarmoq talab qiladi (sandboxda yo'q), shuning uchun bu run
`daily_digest` ga ketdi.

## Spetsifikatsiya nima deydi

`05` §8 jadvalida bitta qator: «`daily_digest` | kuniga | Moderator uchun
hisobot». Boshqa hech qayerda — na mazmuni, na yetkazish kanali, na
saqlash joyi. Ya'ni bu run **to'ldirish** runi bo'ldi va har bir tanlov
`PROGRESS.md` ning «Ochiq savollar» iga sabab bilan yozildi.

## Qabul qilingan qarorlar

### 1. Jadval qo'shildi (`0006`), garchi `05` §2 da yo'q bo'lsa ham

Sabab spetsifikatsiyaning **o'z talabida**: §8 «hammasi idempotent —
takroriy ishga tushish zarar qilmaydi» deydi. Qolgan beshta vazifa uchun
bu tabiiy (`UPDATE` bir xil qatorni qayta yozadi), lekin hisobot
**yuboriladi**: konteyner qayta ko'tarilganda vazifa kechagi kunni
qaytadan hisoblab, moderatorga ikkinchi marta yozardi.

Jarayon ichidagi bayroq yordam bermaydi (qayta ishga tushirishda
yo'qoladi, ikkinchi nusxada esa umuman ishlamaydi). Ishonchli joy —
baza:

```
daily_digest (region_id, digest_date) PK, payload jsonb,
              built_at, delivered_at
```

`INSERT ... ON CONFLICT DO NOTHING ... RETURNING` — qatorni **yozgan**
yurish yuboradi, qolgani jim o'tadi.

Yon foyda: o'tgan kunni qayta hisoblab bo'lmaydi (navbat «hozir» kesimi,
hodisalar esa E6 `recluster` dan keyin o'zgargan bo'lishi mumkin), ya'ni
saqlangan qator kesh emas, **smena topshirishning hujjati**. Shu sababli
mavjud qator hech qachon yangilanmaydi.

`date`, `timestamptz` emas: qator «qaysi kun uchun» degan savolga javob
beradi.

### 2. Kun chegarasi mintaqa zonasida

Hisobot odamga mo'ljallangan, ya'ni «kecha» — uning kechasi
(`DISPLAY_TIMEZONE`, `05` §6.2 ruhi). Toshkent uchun 7-avgust =
`[2026-08-06 19:00Z, 2026-08-07 19:00Z)`. Chegara kirmaydi (`[start, end)`)
— xuddi statistika davri kabi, shunda kunlar yig'indisi umumiy natijadan
katta chiqmaydi.

**Tugallanmagan kun uchun hisobot yig'ilmaydi**: yarim kunning raqamlari
smena topshirishda yolg'on taassurot berardi. API dan bugungi kun
so'ralsa — `422` (`error.day_not_complete`).

### 3. Mazmun — olti bo'lim, «moderator nimani bilishi kerak» savolidan

| Bo'lim | Savol |
|---|---|
| `outages` | Kecha nima bo'ldi (status kesimida, `started_at` bo'yicha) |
| `reports` | Odamlar yozdimi (turli xabar beruvchilar soni), xabar hodisaga tushdimi |
| `queue` | Hozir mening ishim bormi (`05` §4.2 katta radius) |
| `moderation` | Kechagi smena qancha qaror qabul qildi (`audit_log` kesimi) |
| `notifications` | Obunachilar xabar oldimi, navbat to'planmadimi |
| `warnings` | Yuqoridagilardan kelib chiqadigan beshta signal |

Ogohlantirishlar ataylab **harakatga chaqiradigan** qilib tanlandi:
xabarsiz kun (bot o'chgan bo'lishi mumkin), navbat bo'sh emas, biriktirilmagan
xabarlar > 5% (`03` §R1.2 chegarasi), yiqilgan bildirishnoma, to'plangan
outbox (`jobs` konteyneri ishlamayapti — E13-a).

Hisobotda **faqat sonlar**: identifikator ham, koordinata ham, foydalanuvchi
nomi ham yo'q (`05` §7.3 ruhi) — u Telegram chatiga tushadi, tafsilot uchun
admin-panel bor.

### 4. Yetkazish: `DIGEST_CHAT_IDS`, bo'sh bo'lsa ham vazifa ishlaydi

Moderatorlar `users` da yo'q (ular `ADMIN_TOKENS` da, E8), ya'ni «kimga
yuborish» degan savolning bazadagi javobi yo'q. Yechim — sozlamadagi
chat identifikatorlari ro'yxati; transport `app.bot.notifier` dan
(`process_outbox` dagidek, `app.notifications` Telegramni bilmaydi).

Sozlama bo'sh bo'lsa hisobot **baribir yig'iladi va saqlanadi**, faqat
`delivered_at` `NULL` qoladi. Bu ataylab: kanal odam qaroriga bog'liq
(yangi blok **E8-b**), hisobot esa yo'q. Taxminiy chat id yozib qo'yish
mumkin emas — begona guruhga hisobot ketardi.

Bitta chatning yiqilishi qolganlarini to'xtatmaydi; hech biriga
yetkazilmasa `delivered_at` qo'yilmaydi.

### 5. Bir necha kun ko'riladi, yuboriladigan — bittasi

Interval 24 soat, ya'ni konteyner bir sutkadan ko'proq o'chib tursa
oradagi kun hisobotsiz qolardi. `DIGEST_BACKFILL_DAYS = 3` shuni
to'ldiradi, lekin **chatga faqat kechagi kun** ketadi: uch kunlik arxivni
to'kish smena topshirishga yordam bermaydi, eski kunlar API dan o'qiladi.

Ma'lum cheklov: `open_now`, `queue_now`, `outbox_pending` — o'lchov
daqiqasining kesimi, kunning emas. To'ldirilgan kunlarda ular yig'ilgan
daqiqaga tegishli bo'ladi; shuning uchun qatorda `built_at` saqlanadi.
Savol «Ochiq savollar» da.

### 6. `Permission.DIGEST_READ` uchala rolda, `viewer` da ham

Hisobot faqat sonlardan iborat, `viewer` ning maqsadi esa «smena
topshirishda xavfsiz boshlang'ich rol» (E8) — hisobot aynan shu.
Moderator harakatlari **soni** ko'rinadi, «kim nima qildi» esa
`AUDIT_READ` (faqat `admin`) da qoladi.

### 7. `GET /admin/digest` — saqlanmagan kunni joyida hisoblaydi

`jobs` konteyneri o'chirilgan bo'lsa (E13-a hali ochiq) hisobot hech
qachon yig'ilmasdi va endpoint doim bo'sh qaytarardi. Shuning uchun
saqlangan qator bo'lmasa API o'sha kunni **joyida** hisoblaydi va
javobda `stored: false` deydi. Joyida hisoblangan natija bazaga
**yozilmaydi**: yozish huquqi fon vazifasiniki, aks holda bitta API
so'rovi kunni «yig'ilgan» deb belgilab, uning yuborilishini to'sib
qo'yardi.

## Modul chegaralari (`05` §1)

Bitta ham `SELECT` `digest.py` da yozilmagan. Yangi so'rovlar o'z
modullariga qo'shildi:

| Modul | Funksiya |
|---|---|
| `app.clustering.repository` | `status_counts_started_between`, `count_open` |
| `app.reports.queries` | `daily_report_counts` (bitta so'rov, beshta agregat) |
| `app.admin.audit` | `action_counts` |
| `app.notifications.queries` | `status_counts_between`, `pending_outbox_count` |

`app/admin/digest.py` — toza (baza ham, tarmoq ham yo'q),
`app/admin/digest_service.py` — ulash, `app/jobs/daily_digest.py` —
planlovchi va transport.

## Qirralar

- **i18n katalogi tasodifan qayta tartiblandi.** Yangi kalitlarni
  qo'shishda skript butun faylni alifbo bo'yicha saralab yubordi va
  bo'limlarga bo'lingan tuzilma yo'qoldi (diff 155 qator). Fayl `git`
  da yo'q edi (E19 hali push qilinmagan), shuning uchun u `HEAD`
  versiyasidan qayta yig'ildi: eski kalitlar o'z joyida qoldi, keyingi
  epiclarning kalitlari esa prefiks bo'yicha guruhlanib oxiriga
  qo'shildi. Natija — **faqat qo'shimchalardan iborat** diff.
  **Saboq:** JSON kataloglarni skript bilan qayta yozishdan oldin
  fayl `git` da borligini tekshirish kerak.
- **`error.invalid_period` qayta ishlatilmadi.** Uning matnida
  `{max_days}` parametri bor; tugallanmagan kun holatida u yo'q va
  `t()` formatlashda yiqilib, foydalanuvchiga `{max_days}` ni ko'rsatardi.
  Alohida kalit qo'shildi — `error.day_not_complete`.
- **Davr tekshiruvi mintaqa qidiruvidan oldin.** Boshida `require_region`
  birinchi edi, ya'ni yaroqsiz sana ham bazaga so'rov yuborardi.
  Almashtirildi — arzon tekshiruv oldinda (test ham shundan bazasiz
  ishlaydi).
- **`run()` ning bazali testi barcha mintaqalarga tegib ketardi.**
  Vazifa `active_regions` bo'yicha aylanadi, ya'ni CI bazasidagi boshqa
  testlarning mintaqalariga ham qator yozib, ularning fikstyuralarini
  FK bilan to'sardi. Testda `active_regions` monkeypatch qilinadi.

## Holat

- `ruff check .` — yashil;
- `pytest -m "not requires_db"` — **592 o'tdi** (+36);
- `requires_db` — **135 ta** (+7), CI da ishlaydi;
- `alembic upgrade head --sql` — `0006` offline ishladi.

## Keyingi qadam

1. Odam: `.\push.ps1` → CI.
2. Odam qarorlari: `DIGEST_CHAT_IDS` (**E8-b**, yangi), `jobs` profili
   (**E13-a**, endi beshta vazifaga tegishli), `ADMIN_TOKENS` (E8-a).
3. Kod ishi: ikkinchi mintaqani haqiqiy OSM importi bilan uchdan-uchgacha
   sinash (`region_admin add` → `import_boundaries` → `activate`).
   E17, E18, E20 — 👤 bloki bilan.

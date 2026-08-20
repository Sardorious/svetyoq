# 180-run — Т-9 ning qabul qiluvchilar jurnali: `tz_receipts` va §6.4 ning haqiqiy tuzatishi

**Sessiya:** `local_e9805171` · **Sana:** 2026-08-20 · **Epic:** TZ (yangi qonun)

179-run uchta bandni sanab qoldirgan edi: (1) Т-9 ning jurnal jadvali,
(2) §8 operatorining paneli, (3) ТС-201…ТС-220 ni uchidan-uchiga o'lchash.
Bu run **birinchisini** bajardi.

Boshlanish nuqtasi: §6.4 («Исправление — обязательно… Это не опция»)
176-rundan beri kodda **to'liq** yozilgan edi — `tzoutage.correct()`
jurnaldan tuzatish yasaydi, `record()` jurnal qatorlarini beradi. Lekin
jurnalning o'zi hech qayerda saqlanmasdi: `Receipt` — dataclass, u
protsess xotirasida yashardi. Ya'ni ilova qayta ishga tushishi bilan
«kimga xato xabar ketgan» degan bilim yo'qolardi va majburiy tuzatish
**hech kimga** bormasdi. Kodda esa hech qanday xato ko'rinmasdi:
`correct()` bo'sh ro'yxat olardi va bo'sh ro'yxat qaytarardi.

---

## 1. Nima qurildi

| Fayl | Nima |
|---|---|
| `alembic/versions/0014_tz_receipts.py` | `tz_receipts` jadvali, uchta indeks, Т-2 triggerlari |
| `app/notifications/models.py` | `TzReceipt`, `TZ_RECEIPT_KINDS` |
| `app/notifications/tzreceipts.py` | ulash qatlami: `record`, `load_receipts`, `load_sent_keys`, `load_ledger`, `correct` |
| `app/notifications/tzoutage.py` | `record_correction()`, `Receipt.key` ning turi, `CHANNELS` da tuzatish `wired=True` |
| `app/admin/registries.py` | `_probe_tzoutage` — uchtadan **ikkitasi** ulangan |
| `tests/test_tz_receipts.py` | bazasiz: turlar to'plami, kalitning turi, tuzatishning jurnali, qorovullar |
| `tests/test_tz_receipts_db.py` | haqiqiy bazada: Т-2, Т-7, §6.4 ning idempotentligi, `Ledger` |

---

## 2. Qarorlar va sabablari

### 🔴 Jurnal faqat qo'shiladi (Т-2 ning uchta qatlami)

Т-2 «журнал **сообщений** и настроек» deydi va yuborilgan xabar aynan
shu. Qatorni o'chirish mumkin bo'lsa, §6.4 dan qutulishning eng oson
yo'li paydo bo'lardi: qabul qiluvchilar ro'yxatini o'chir, keyin
«tuzatadigan hech kim yo'q» de. `tz_signals` dagi bilan bir xil himoya —
`UPDATE`/`DELETE` qator triggeri, `TRUNCATE` uchun alohida statement
triggeri va **o'z** funksiyasi (bittasini o'chirish qolganlarini
qurolsizlantirmasin).

### 🔴 `outages` ga tashqi kalit ataylab yo'q

Jurnal hodisadan **uzoqroq** yashashi kerak. Т-10 tasdiqlangan uzilishni
o'chirishni taqiqlaydi, lekin `FOREIGN KEY` har qanday boshqa tozalashda
qabul qiluvchilar ro'yxatini birga olib ketardi — va aynan o'sha lahzada
§6.4 bajarilmay qolardi. `tz_signals.source_id` da ham xuddi shu qaror,
xuddi shu sabab bilan.

### 🔴 `label` va `lang` ko'chiriladi, `JOIN` qilinmaydi

Tuzatish yuborilayotganda odam manzilini o'chirgan yoki nomini
o'zgartirgan bo'lishi mumkin; §6.4 esa xabarni **o'sha** manzil nomi
bilan talab qiladi — tuzatishni o'qiydigan odam uni birinchi xabar bilan
solishtiradi. Til ham shundan: odam tilini almashtirgan bo'lsa ham
tuzatish tushunarli bo'lsin.

### 🔴 Т-7 bazada, mintaqa bilan

`ix_tz_receipts_region_id_key` — yagona indeks (qisman **emas**: bu
yerda har qator yuborilgan xabar, istisno yo'q). Mintaqa kalitning
ichida emas, indeksda: `delivery_key()` mintaqani bilmaydi, global
yagona indeks esa ikkita shaharning bir xil identifikatorli hodisasini
to'qnashtirardi. Bu 179-run `tz_signals` da **haqiqiy bazada** o'lchab
topgan xato — takrorlanmadi.

### 🔴 `ON CONFLICT DO NOTHING`, xato emas

To'qnashuv **normal** holat: ikkita ishchi bir vaqtda bir xil xabarni
rejalashtirgan bo'lishi mumkin. Xato ko'tarish butun paketni bekor
qilardi, ya'ni bitta takror tufayli qolgan odamlar jurnalsiz qolardi —
va aynan ular §6.4 dan tushib qolardi. Qaytgan son kirishdan kichik
bo'lishi mumkin, farq — takrorlar soni.

### 🔴 §6.4 majburiy, lekin bir marta

`tzoutage.correct()` hech qanday tekshiruvni qo'llamaydi va har doim
`SEND` qaytaradi — bu to'g'ri, §6.4 ni tekshiruvlar to'sa olmaydi.
Lekin «allaqachon tuzatilgan» tekshiruv emas, **fakt**: o'sha odam o'sha
xabarni olgan. Shuning uchun takror ulash qatlamida filtrlanadi
(jurnalda tuzatish qatori bormi), oxirgi to'siq esa bazada turadi.
Aks holda qayta ishga tushirilgan navbat butun kvartalga ikkinchi marta
«biz xato qildik» yuborardi.

---

## 3. Ulash paytida topilgan jim defekt

`Receipt.key` uchlikni (`hodisa|kvartal|manzil`) **tursiz** qaytarardi.
`plan_outage()` esa `outage_key(..., Kind.OUTAGE)` ni, ya'ni **tur
bilan** qidiradi (177-run tuzatishni uzilishdan ajratish uchun turni
kalitga ataylab qo'shgan edi).

Natija: jurnaldan qurilgan `Ledger.sent_keys` uzilish xabarini **hech
qachon** to'smasdi — Т-7 («Повторная отправка того же сообщения не
создаёт второго свидетельства») aynan eng qimmat ikkita xabar uchun
ishlamasdi va bir xil «sizda avariya» qayta-qayta ketaverardi.

Nosozlik ko'rinmasdi, chunki ikkala tomon ham **o'zicha to'g'ri** edi va
ularni bir joyda solishtiradigan test yo'q edi: 177-run ning
`test_the_journal_row_rebuilds_the_dedup_key` i aynan tursiz kalitni
qulflagan. Xossa endi turni qo'shadi; `RESTORED` — hujjatlangan yagona
istisno, chunki uning kalitini `tzrestored` yasaydi va u modul turlar
haqida umuman bilmaydi (`Kind` yuqori modulda e'lon qilingan). Istisno
**bitta joyda** — xossaning ichida — turadi.

Yangi test ikkala uchni birga o'lchaydi:
`test_a_repeated_outage_is_blocked_by_a_ledger_built_from_the_journal`.

---

## 4. Haqiqiy baza

Sandboxda PostgreSQL 18 + PostGIS 3.6 ko'tarildi (micromamba,
conda-forge; eski `/tmp/mamba/envs/py311` **boshqa foydalanuvchiga**
tegishli bo'lgani uchun unga o'rnatib bo'lmadi — Postgres alohida
prefiksga (`/tmp/pg180`) qo'yildi va Python o'sha eski muhitdan
ishlatildi).

Tekshirilgani: `upgrade` → `downgrade` → `upgrade`. Ikkalasi ham toza;
cheklov nomi **ikkilanmagan** (`ck_tz_receipts_kind`, 172-run ning
xatosi takrorlanmadi), ikkala trigger ham o'rnida, `downgrade` funksiya
va indekslarni ham olib tashlaydi.

**Yakun:** 34 yangi test (16 bazasiz + 18 `requires_db`), butun to'plam
**4718 passed, 1 skipped** (`requires_db` 345 ham yurgizildi), `ruff`
toza. Yangi sozlama yo'q, i18n kaliti yo'q (matnlar 177-runda
qo'shilgan edi).

---

## 5. 👤 Yangi ochiq savol

`test_outbox_pending_is_actually_queried` bazani toza deb o'ylaydi:
`outbox` ga uch qator qo'yib `pending == 2` ni talab qiladi. Toza
bazada butun to'plam yashil, lekin **o'sha bazada ikkinchi marta**
yurgizilsa aynan shu test yiqiladi. Bu 145-run topgan «iflos baza»
sinfining test tomonidagi ko'rinishi. Savol `PROGRESS.md` ning «Ochiq
savollar» ida; kod tegilmadi — nosozlik testda, mahsulotda emas.

---

## 6. Keyingi qadam

179 navbatining qolgani: (2) §8 operatorining paneli — rejali ishlar
e'lonini kiritish (`CHANNELS` da `PLANNED` hamon `wired=False`) va
bahsli holatni yopish; keyin (3) ТС-201…ТС-220 ni uchidan-uchiga
o'lchash.

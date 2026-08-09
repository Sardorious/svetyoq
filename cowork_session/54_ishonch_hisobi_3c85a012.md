# 54-sessiya — `06` §6 `confidence` hisobi kontrakti

**Sessiya:** `local_3c85a012-a275-4216-952e-104d46beff93` («Sveta net build»)
**Sana:** 2026-08-09
**Epic:** E5 (ko'ndalang — spetsifikatsiya ↔ kod kontrakti)
**Natija:** ✅ yangi `sveta/tests/test_confidence_contract.py`, 24 ta bazasiz
test funksiyasi. Kod o'zgartirilmadi.
**Infratuzilma:** ⚠️ sandbox **yigirma beshinchi marta ketma-ket** yiqildi
(INFRA-1, `useradd: No space left on device`) — `ruff check` va `pytest`
yana ishga tushmadi.

---

## 1. Run boshi

`CLAUDE.md` § 0 tartibi bo'yicha: `cowork_session/INDEX.md` → `PROGRESS.md`.
Sandbox birinchi chaqiruvdayoq yiqildi, shuning uchun butun run **fayl
asboblari** (`Read` / `Grep` / `Glob` / `Edit` / `Write`) bilan bajarildi.
50-sessiyaning sabog'i ishladi: `PROGRESS.md` va `INDEX.md` ning uzun
qatorlari `Grep -o` bilan `.{0,150}` oynada o'qildi.

53-sessiya keyingi run uchun **bitta ochiq nomzod** qoldirgan edi —
`06` §6 `confidence` hisobi — va uni ochishdan oldin «avval §6 ni va
`test_confirmation.py` ning §6 qismini **to'liq** o'qing» degan shart
qo'ygan edi. Shart bajarildi.

## 2. Nomzod tekshirildi va tasdiqlandi

`06_Confirmation_Logic.md:240–258` va `tests/test_confirmation.py:152–188`
yonma-yon o'qildi. 53-sessiyaning gumoni to'g'ri chiqdi: §6 ning **beshta**
artefakti ham kodda qo'lda yozilgan va hujjatga bitta ham havolasi yo'q.

| § 6 artefakti | Qayerda qo'lda yozilgan | Nima jim siljiy oladi |
|---|---|---|
| `round(100 × min(1, W / N_req) × cf × freshness)` | `confirmation.py:181–189` | `min(1, …)` tushib qolishi |
| `clamp(0.5, sqrt(A_local / 20), 1.0)` | `confirmation.py:44–47`, `171–178` | `20` bo'luvchisi — `06` §9 da **yo'q** |
| `freshness` = `1.0` / `0.85` / `0.6` (`15` / `45` daq) | `confirmation.py:41–42`; test `:156` | pog'ona qiymati yoki chegarasi |
| bandlar `40` / `70` / `90` | `confirmation.py:50–55`; test `:177–184` | bandning bir birlikka siljishi |
| «hech qachon 50% dan oshmaydi» | test `:169–171` | polning o'zgarishi |

**Eng qimmat artefakt — bandlar.** Boshqa hammasi arifmetika: xato bo'lsa son
noto'g'ri chiqadi. Bandlar esa **matnni** tanlaydi (`outage.confidence.*`).
Band bir birlikka siljisa hech qanday formula buzilmaydi — hisob to'g'ri
qoladi, faqat foydalanuvchi past ishonchda «Ehtimol, ommaviy uzilish»
o'qiydi, ya'ni tekshirilmagan hodisa tasdiqlanganday ko'rinadi. Bu — `06`
ning butun maqsadiga (`§4.3`: «kam ma'lumotdan katta xulosa chiqarmaslik»)
zid bo'lgan yagona jim nosozlik.

**`20` bo'luvchisi — ikkinchi qimmat.** 49-sessiya `06` §9 jadvalini yopdi,
lekin `20` u jadvalda **umuman yo'q**: §6 — uning yagona uyi. `20` → `200`
bo'lsa `coverage_factor` 2000 ta faol foydalanuvchigacha shiftga yetmasdi va
butun shahar polda, ya'ni «50%» da qolardi. Bu 52-sessiyaning sabog'ining
davomi: **§9 bilan yopilgan son hali kontraktda emas**, va bu yerda son
umuman §9 da emas.

## 3. Yozildi — `tests/test_confidence_contract.py`

53-sessiyaning `test_confirmation_threshold_contract.py` si tayyor naqsh
sifatida ishlatildi: bo'lim kesuvchi, kod bloki parseri, jadval parseri
(ajratgichdan keyin — 51-sessiyaning sabog'i), `clamp` shaklini o'qiydigan
regex va perturbatsiya testlari.

24 ta test funksiyasi, to'rt guruh:

1. **Formulaning shakli (7 ta).** Bo'limda `confidence = round(...)` roppa-rosa
   bitta; masshtab `100`, to'yinish `min(1, …)`, hisoblagich `W`, maxraj
   `N_req`, ikkala ko'paytuvchi ham **o'sha blokda ta'riflangan** nomlar.
   Eng kuchli test — `test_confidence_reproduces_the_documented_product`:
   qiymat hujjatdan o'qilgan beshta doimiy bo'yicha **mustaqil qayta
   hisoblanadi** va 375 ta kirish kombinatsiyasida `confidence()` bilan
   solishtiriladi (ko'paytirish tartibi bir xil, ya'ni suzuvchi nuqtada ham
   aynan teng).
2. **`coverage_factor` (6 ta).** Pol birinchi, shift oxirgi (`clamp(1.0, …,
   0.5)` `ValueError` beradi — nosozlik ishlab chiqarishda chiqardi);
   bo'luvchi `COVERAGE_DIVISOR` ga teng va **aynan shiftga tegadigan nuqta**
   (`cf(20) == 1.0`, `cf(19) < 1.0`); argument `A_local` va u §4.1 dagi
   kattalik; «50%» va'dasi bitta jumladan ikkala son bilan o'qiladi
   (`pol qiymati 0.5`, `50%`) va xulq-atvorda tekshiriladi.
3. **`freshness` (4 ta).** Ikkita pog'ona + pol; chegara **inklyuziv**
   (`freshness(15) == 1.0`, `freshness(16) < 1.0`); qiymatlar qat'iy
   kamayadi va pol noldan katta (nol pol §8 ning «so'nish» qoidasini har
   qanday eski hodisaga qo'llardi).
4. **Bandlar (7 ta).** Jadval yopiq va uzluksiz (`0…100`, teshiksiz,
   kesishmasiz); quyi chegaralar `CONFIDENCE_BANDS` ga teng va kod ro'yxati
   **kamayish** tartibida (aks holda yuqori band hech qachon qaytarilmasdi);
   `0..100` ning **har bir** qiymati o'z bandidagi kalitni oladi; hujjatdagi
   interfeys matni `uz.json` bilan solishtiriladi; kalitlar UZ va RU da bor;
   eng quyi band `pending` ni nom bilan ataydi; `06` §8 ning `confidence < 40`
   qoidasi ikkinchi bandning chegarasiga bog'landi.

### Qarorlar

- **`SPEC_BAND_ROWS = 4`, `SPEC_FRESHNESS_VALUES = 3` — aynan.** Ro'yxatlar
  yopiq: beshinchi band «matnsiz holat» degani bo'lardi.
- **Yaxlitlash `12.5 → 13` bilan qulflandi.** `1.0 / 8` dyadik, ya'ni
  `12.5` suzuvchi nuqtada aynan ifodalanadi va test tasodifga bog'liq emas.
  Yonida `round(12.5) == 12` yozilgan — `round_half_up` nima uchun
  kerakligining o'zi. Band chegaralarida (`39.5` / `69.5` / `89.5`) aynan
  ifodalanadigan kirish topilmadi, shuning uchun mexanizm tekshirildi,
  chegaraning o'zi emas.
- **Hujjat matni ↔ katalog `ASCII skeleti` bo'yicha solishtiriladi**
  (`re.sub(r"[^a-z0-9]+", "", s.lower())`). Apostrof (`'` / `ʼ` / `'`) va
  `·` ning kodlashi hujjat bilan `uz.json` o'rtasida farq qilishi mumkin va
  bu **hech kimga** ahamiyatli emas; matnning o'zi o'zgarsa skelet ham
  o'zgaradi. Bu 53-sessiyaning unicode sabog'ining davomi.
- **`×` regexda `.` bilan** (53-dan meros), `≤` esa ikkala shaklda
  (`≤` yoki `<=`) qabul qilinadi.
- **§8 dan faqat `40` olindi.** U §6 bandining chegarasi, ya'ni §6 ning
  artefakti; §8 ning qolgani (deeskalatsiya jadvali, `45` daqiqa,
  «tasdiqlangan masshtab pasaytirilmaydi») alohida bo'lim va o'z
  kontraktiga loyiq.

### Rad etilgan

- **§7 ishlangan misollar jadvalini (`conf ≈ 87`) shu faylga qo'shish.**
  U alohida bo'lim, sakkiz qator va §4, §5, §6 ni birga sinaydi — o'z
  kontrakti bo'lishi kerak. Keyingi run uchun nomzod sifatida qoldirildi.
- **`COVERAGE_DIVISOR` ni `06` §9 ga ko'chirish.** Hujjatga tegadi →
  `PROGRESS.md` «Ochiq savollar» iga 👤 bilan yozildi.
- **`test_confirmation.py` ning §6 qismini olib tashlash.** U xulq-atvor
  testi, o'z o'rnida qoladi (52- va 53-sessiyalardagi bilan bir xil qaror).
- **`05` §10 metrikalarining ishonch kesimini shu runda tekshirish.**
  Bo'lim boshqa hujjatda; «Ochiq savollar» ga 👤 bilan yozildi.

## 4. Nima ishga tushmadi

`ruff check sveta` va `pytest -m "not requires_db"` — **yigirma beshinchi
marta ketma-ket**. Sandbox har chaqiruvda `useradd: /etc/passwd.NNNNN: No
space left on device` bilan yiqiladi. Sabab — `CLAUDE.md` da yozilgan:
C diskdagi sessiya papkalari to'lgan; `cleanup-sessions.ps1` ni **odam**
ishga tushirishi kerak.

Shuning uchun yangi fayl **statik** tekshirildi: import qilinadigan har bir
nom manbada ko'zdan kechirildi (`CONFIDENCE_BANDS`, `COVERAGE_DIVISOR`,
`COVERAGE_FACTOR_MIN/MAX`, `FRESHNESS_STEPS`, `FRESHNESS_FLOOR`,
`confidence`, `confidence_key`, `coverage_factor`, `freshness`,
`LOW_CONFIDENCE_BELOW`, `SUPPORTED_LANGUAGES`), hujjatdagi barcha marker
satrlar `Grep` bilan tasdiqlandi (`## 6. \`confidence\` hisobi`,
`## 7. Ishlangan misollar`, `## 8. Qayta baholash va deeskalatsiya`,
`## 9. Konfiguratsiya parametrlari`, `### 4.1 Denominator`,
`### 4.2 Formula`), qatorlar `line-length = 100` ga sig'dirildi va
`ruff` ning `I` (import tartibi) hamda `B905` (`zip(..., strict=)`)
qoidalari qo'lda kuzatildi.

## 5. Keyingi run uchun

1. **Sandbox tiklanganda birinchi ish — butun `pytest` va `ruff check`,
   yangi kod emas.** 36–54 runlarning ~335 ta testi hech qachon
   ishlamagan.
2. **Ochiq nomzod:** `06` **§7 ishlangan misollar jadvali** (sakkiz qator:
   `A_local`, `W`, `N_req`, natija). U §4, §5 va §6 ni birga sinaydi va
   hozircha hech qayerdan o'qilmaydi; `conf ≈ 87` esa §6 ning yagona
   uchidan-uchiga misoli.
3. **Yopilgan nomzodlar, qayta ochilmasin:** `06` §6 `confidence` (54),
   `06` §4.1–4.3 (53), `06` §5.1–5.4 (52), `06` §3.1–3.2 (51), `06` §2 (50),
   `06` §9 (49), `05` §8 (45/49), `05` §7.2 (48), `05` §10 (47), oltin
   ssenariylar (46), fon vazifalari registri (45), konfiguratsiya parity
   (44), bildirishnoma domeni (43), `05` §2 DDL ustunlari (43), i18n ikki
   yo'nalish (41, 42), `05` §2 DDL indekslari (40), API `commit` (39),
   `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).

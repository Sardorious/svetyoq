# svetyoq — agent uchun doimiy qoidalar

Bu fayl har bir Cowork/Claude sessiyasi boshida o'qiladi.

## 0. Har run BOSHIDA — ishga kirishishdan oldin (majburiy)

1. **`cowork_session/INDEX.md` ni o'qi.** «Qayerda to'xtadik» qatori — qayerdan
   davom etishni ko'rsatadi. Kerak bo'lsa oxirgi sessiya faylini ham och.
2. **`sveta/EpicProgress.md` ni o'qi** — epiclar kesimi, ~15 KB, `Read` ga
   sig'adi. «Qaysi epic qanday holatda, kodi qayerda, testi qaysi, nima
   to'sqinlik qilyapti» — bir qarashda.
3. **`sveta/PROGRESS.md` ni o'qi** — texnik holatning yagona manbai (joriy epic,
   bloklar, ochiq savollar). U 300 KB dan katta va `Read` ga **sig'maydi** —
   `Grep -o` bilan kichik oyna (`.{0,150}`) so'rab o'qi.
4. Shundan keyingina yangi ishni boshla. Hech qachon nolldan taxmin qilma —
   avval qayerda to'xtaganini aniqla.

## 1. Har run OXIRIDA — majburiy

1. **Shu sessiyaning yozishmasini `cowork_session/` ga ko'chir**:
   `NN_<mavzu>_<session-id-boshi>.md`. Sessiya ro'yxati va transkriptlar
   `mcp__session_info__list_sessions` / `read_transcript` orqali olinadi.
2. **`cowork_session/INDEX.md`** jadvaliga qator qo'sh va **«Qayerda to'xtadik»**
   ni yangila.
3. **Eskirgan va keraksizini o'chir:**
   - boshqa loyihalarning sessiyalari («Continuity dev», «dorilar» va h.k.) —
     umuman qo'shilmaydi;
   - bo'sh yoki xabarsiz sessiyalar;
   - yakuniy natijasi allaqachon `PROGRESS.md` yoki keyingi sessiya faylida
     qayd etilgan, o'zidan hech qanday qaror yoki sabab qoldirmagan sessiyalar.
4. **Sirlarni ko'chirma.** Token, kalit, parol chatda uchrasa — arxivga
   `<TOKEN>` deb yoz. Haqiqiy qiymat faqat `sveta/.env` da.
5. `sveta/PROGRESS.md` ni yangila (holat jadvali, epic belgisi, run jurnali).
6. **`sveta/EpicProgress.md` ni ham yangila** — u **faqat xulosa**
   (👤 qaror, 2026-08-11): tegilgan epic holati, yangi test fayli,
   o'zgargan blok, «Xulosa» bo'limi. Run raqamlari va run bayonlari
   unga yozilmaydi. U `PROGRESS.md` ning **hosilasi**:
   ziddiyat chiqsa `PROGRESS.md` haq. Qanday yangilash — o'sha faylning
   §5 bo'limida.

### ⛔ `mcp__cowork__allow_cowork_file_delete` NI CHAQIRMA

U **odam tasdig'ini kutadi**, rejalashtirilgan runda esa odam yo'q —
chaqiruv runni butunlay to'xtatadi. 30-sessiya aynan shunday yo'qoldi:
u vaqtinchalik `tests/test_dbg_tmp.py` ni o'chirmoqchi bo'ldi va
`PROGRESS.md` ham, `INDEX.md` ham yangilanmasdan qoldi — ikkita keyingi
run `01` §16 ni «bajarilmagan» deb o'qidi va ish takrorlanishiga oz
qoldi.

Shuning uchun:

- **vaqtinchalik fayl yaratma** (debug harness, scratch test, `tmp_*`);
- yaratilib qolgan bo'lsa — mazmunini `Write`/`Edit` bilan olib tashla
  (assert siz test fayli pytest ni ifloslantiradi) va o'chirishni
  `PROGRESS.md` ning «Ochiq savollar» iga 👤 belgisi bilan yoz.

## 2. Loyihaning qolgan qoidalari

Ular `sveta-net-build` scheduled task ko'rsatmasida va
`cowork_session/02_E1_skelet_4d65f756.md` faylida to'liq yozilgan. Qisqacha:

- Bitta run = bitta epic yoki uning aniq bo'lagi; kod har doim ishlaydigan
  holatda qoldiriladi.
- Spetsifikatsiya (`05_Technical_Design.md`, `06_Confirmation_Logic.md`) —
  qonun. Yaxshiroq g'oya `PROGRESS.md` ning «Ochiq savollar» iga yoziladi,
  kodga emas.
- Stek: Python 3.11+, FastAPI, aiogram, SQLAlchemy 2.x + Alembic,
  PostgreSQL 16 + PostGIS, h3, pytest. Kafka/Redis/mikroservis YO'Q.
- i18n boshidan; qattiq kodlangan foydalanuvchi matni — bloklovchi defekt.
- **👤 Odam qarori (2026-08-11): moliyaviy tomon loyihani BLOKLAMAYDI.**
  BRD/`02` dagi moliyaviy gate lar (`BRD §22` «byudjetgacha kod taqiqlanadi»,
  `PH0-EXIT-8`, `C-04`, `RS-07`) bloklamaydigan deb o'qiladi — loyihani
  tugatish ustuvor. Hujjatlar tahrirlanmaydi; reyestrlar ziddiyatni qayd
  etaveradi, lekin ish shu sababdan to'xtatilmaydi.
- `geom_exact` hech qanday API javobida chiqmaydi.
- **Agent git commit va push QILMAYDI** — odam `push.ps1` orqali o'zi qiladi.

## 3. Papka tuzilishi

```
svetyoq/
├── CLAUDE.md              ← shu fayl
├── 01..06_*.md            ← BRD, PRD, Faza 0, roadmap, texnik dizayn, tasdiqlash
├── cowork_session/        ← sessiya arxivi (INDEX.md dan boshla)
├── sveta/                 ← kod
│   ├── PROGRESS.md        ← holatning yagona manbai (katta, Grep bilan o'qiladi)
│   └── EpicProgress.md    ← epiclar kesimi, qisqa xarita (shundan boshlang)
├── setup-git.ps1
├── cleanup-sessions.ps1   ← C diskdagi sessiya papkalarini tozalash (odam ishga tushiradi)
└── push.ps1 / push.bat
```

**Eslatma agentga:** `cleanup-sessions.ps1` ni o'zing ishga tushira olmaysan —
u C diskdagi, sessiyaga ulanmagan papka bilan ishlaydi. Sandbox
`useradd failed` xatosi bilan yiqilsa, sabab ehtimol o'sha papka to'lib
ketgani; odamga shu skriptni eslatib qo'y.

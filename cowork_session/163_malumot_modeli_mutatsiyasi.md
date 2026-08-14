# 163-run — `01` §17 ma'lumot modeli: 72-running o'lchovi rad etildi

**Sana:** 2026-08-14
**Epic:** DATA (mutatsiya qamrovi)
**Nishon:** `app/db/data_model.py` (704 qator)
**Natija:** 93 mutatsiya → 59 KILLED, **34 SURVIVOR** (37 %), 2 ekvivalent,
32 qulflandi (+22 test). 3721 passed, ruff yashil, mahsulot kodi tegilmadi.

---

## 1. Nishon qanday tanlandi

162 qoldirgan tartibning (1) bandi: «o'lchanmagan modullarni
`app/release/` dan **tashqarida** qidirish — ro'yxat `PROGRESS.md` run
jurnalidan tuziladi (`EpicProgress.md` §4 navbati 130-runda qotgan)».

Ro'yxat mexanik yig'ildi:

```bash
awk 'NR>=409 && /^\| 20/' PROGRESS.md | grep "mutatsiya" \
  | grep -o '`[a-z_0-9/]*\.py`' | tr -d '`' | sort -u > /tmp/measured.txt
```

va `find app -name '*.py'` bilan ayirma olindi. `app/release/` dan
tashqaridagi eng katta o'lchanmagan modul — `app/db/data_model.py`
(704 qator). Jurnal 72-run haqida shunday deydi:

> `22 mutatsiya, 0 survivor (3 tasi topilib tuzatildi)`

Ya'ni o'lchov `verdict` `returncode != 0` bo'lgan davrda olingan —
`pytest` ning `rc=4` i (collection error) yolg'on `KILLED` berardi.
Tuzatilgani **126-run**. Bu 155-run ochgan sinfning aynan o'zi, faqat
endi `app/release/` dan tashqarida.

**Test qatlami** oldindan `grep` bilan tekshirildi (159 sabog'i):
`data_model` ni faqat bitta test fayli import qiladi
(`tests/test_data_model_contract.py`, 46 test) va mahsulotda ikkita
iste'molchisi bor — `app/admin/registries.py`
(`GET /api/v1/admin/registries` ning `data_model` qatori) va
`app/core/architecture.py` (nasrda havola).

## 2. Metodologiya

Ikki bosqichli, 161–162 dagidek:

1. **Tor tanlov** — `tests/test_data_model_contract.py` (46 test, ~8 s)
   ishchi nusxada. U faqat *yolg'on survivor* berishi mumkin, *yolg'on
   KILLED* emas.
2. **Tasdiqlash** — o'ttiz to'rttala nomzod butun bazasiz to'plamda
   (3699 test), **ikkita parallel ishchi nusxa** (`/tmp/w163a`,
   `/tmp/w163b`, repo **ildizidan** ko'chirilgan, nusxaning
   `pyproject.toml` iga `addopts = "-m 'not requires_db'"`).
   **Bittasi ham fikrini o'zgartirmadi.**

Verdikt faqat `rc==1` da `KILLED`, `rc==0` da `SURVIVED`, boshqasi —
`ERR` va hisobga olinmaydi. `rc≠0/1` chiqmadi.

**Infra:** bitta `bash` chaqiruvida tor tanlovdan **14 mutatsiya**
(~110 s) yoki to'liq to'plamdan **6 mutatsiya** (2 yadro × 3 raund,
~145 s) sig'adi. `mcp__workspace__bash` ning **sukut** timeouti
120 s — `timeout_ms: 180000` ni ochiq berish kerak, aks holda partiya
uziladi va mutant ishchi nusxada qolib ketadi (har partiyadan keyin
`diff … /tmp/data_model.orig`).

## 3. Topilmalar

### 🔴 (a) To'qqizala `StrEnum` qiymati sezilmasdi

`Fidelity` ning beshtasi (`as_diagrammed`, `renamed`, `relocated`,
`narrowed`, `absent`) va `Reliance` ning to'rttasi (`load_bearing`,
`dormant`, `claimed_elsewhere`, `unclaimed`). Mavjud
`test_the_five_states_are_all_in_use_today` holatlarni **sanaydi**
(`report.by_fidelity(state)` bo'sh emasligini), nomini so'ramaydi.

Nega bu mahsulot sirti: qiymat ikki yo'l bilan chiqadi —
`Report.counts` ning kalitlari va `evaluate()` ning diagnostikasi
(«`{attr}` — `{verdict}`, lekin izohlanmagan»), ya'ni reyestrni
yozayotgan odam o'qiydigan yagona matn (161 bilan bir xil sabab).

### 🔴 (b) Reyestrning ikkinchi ustuni — `Reliance` — hech qachon o'lchanmagan

`_check_declared` `Fidelity` ni haqiqatga bog'laydi: manzil `metadata`
da bo'lishi shart, tipi mos bo'lishi shart, `ABSENT` uchun esa nom
sxemada **bo'lmasligi** shart. `Reliance` ni esa hech narsa
bog'lamaydi — u sxema haqidagi emas, **hujjatlar** haqidagi da'vo.

Natijada `DISTRICTS.is_city_district` ni `UNCLAIMED` dan `DORMANT` ga,
`OUTAGES.independent_reporters` ni `LOAD_BEARING` dan `DORMANT` ga
ko'chirish butun to'plamda jim o'tdi. Ya'ni 72-run ning **asosiy
qarori** — «`Reliance` `Fidelity` ni takrorlamaydi: birinchisi bugun
qayerda, ikkinchisi farqni kim sezadi» — o'lchanmagan qolgandi.

Qulf — literal `REGISTRY` jadvali (5 qator × jadval / ustun /
`Fidelity` / `Reliance` / `claimed_by`) va tartib.

### 🔴 (c) `by_reliance` har doim bo'sh ro'yxat qaytarardi

`f.reliance is reliance` → `f.fidelity is reliance`. `Fidelity` va
`Reliance` — ikki alohida `StrEnum` sinfi, ya'ni shart **har doim**
`False`. `by_fidelity` ning juftligi bor edi, `by_reliance` niki yo'q.

### 🟡 (d) `SPEC` `01 §17`→`01 §18` sezilmasdi (seriyada sakkizinchi marta)

`SPEC` `app/admin/registries.py` orqali
`GET /api/v1/admin/registries` javobiga chiqadi va `## 18. Integrations`
— **mavjud** sarlavha, ya'ni oddiy «yechiladi» tekshiruvi ikkalasini
ajratmaydi. Qulf ikki qismli: shakl `01 §<son>` **va** son — aynan
`_SECTION_RE` qidiradigan sarlavhaning nomeri.

### 🟡 (e) Parserning oltita qirrasi

* **§17 ning chegarasi — ikkala yarmi.** `_NEXT_SECTION_RE` ni
  `^###` ga o'zgartirish ham, `rest[: nxt.start()]` ni `rest` ga
  aylantirish ham sezilmasdi: bugungi hujjatda §17 dan keyin mermaid
  bloki yo'q, ya'ni javob o'zgarmasdi. Sun'iy hujjat kerak.
* **Ochko'z mermaid** (`(.*?)` → `(.*)`) — ikkita blok bittaga
  yopishardi.
* **Kardinallikning `{3,}` uzunligi** — `{2,}` da `A |{ B : label`
  chinakam sintaktik xato bo'la turib bog'lanishga aylanardi.
* **`UK` kalit belgisi** — bugungi §17 da yo'q, ya'ni regexdan olib
  tashlash hech narsani o'zgartirmasdi; hujjatga unikal kalit
  qo'shilgan kun parser butun blokni yiqitardi.
* **Kalitsiz atributning `key == ""`** (`attr.group(3) or ""`) —
  mavjud testlar faqat `PK`/`FK` ni so'raydi.
* **Blokdan tashqaridagi tushunarsiz qator** — ichkarisi qulflangan
  edi, tashqarisi yo'q.

Va «Изменения» ro'yxatining ikki qoidasi: `- ` prefiksining
**bo'shlig'i** (`-первое` qabul qilinib bitta harf kesilardi) va
ro'yxatni yopadigan **bo'sh qator**.

### 🟡 (f) Tip siyosati va uchta yechim shoxi

`TYPE_EQUIVALENTS` ning to'qqizta kalitidan beshtasi hech qachon
o'lchanmagan (`uuid`, `boolean`, `timestamptz`, `geometry`,
`geography`) — mavjud `test_narrowing_is_one_directional` faqat
to'rttasiga tegadi. Har qanday kengaytirish driftni **jimgina qabul
qiladi**: hujjat bir narsa va'da qiladi, sxema boshqasini beradi,
hisobot `AS_DIAGRAMMED` deydi.

Uchta shox: jadvalda yo'q tip `AS_DIAGRAMMED` ga aylansa hamma narsa
«mos» bo'lardi; **izohlanmagan `NARROWED`** — modulning butun mavjudlik
sababi — jimgina `AS_DIAGRAMMED` bo'lib yozilardi; manzilning yarmi
(`table` bor, `column` yo'q) va manzildagi **yo'q ustun** ham
o'lchanmagan edi.

### 🟡 (g) Hisobotning shakli

`evaluate()` kalitli (`PK`/`FK`) atributlarni butunlay tashlab ketsa
ham to'plam yashil qolardi: `sum(counts.values()) == len(findings)` —
**ichki** muvozanat, ikkala son birga kamayadi. Endi tashqi o'lchov:
`len(findings) == len(entities) + len(attributes)`.

`faithful` ning **birinchi** konyunkti (`not self.diverged`) qulflandi —
ikkinchisi va uchinchisi 72-runda allaqachon ajratilgan edi. FK
qidiruvidagi `break` ham: bitta jadvalda bitta ota-onaga ikkita FK
bo'lsa, birinchisi olinadi.

## 4. ⚪ Ekvivalent (qulflanmadi)

* `parse_change_claims` da `if idx < 0` → `if idx <= 0`.
  `section_text` qaytargan matn **har doim** sarlavha qatorining
  qoldig'i bilan boshlanadi (eng kamida `"\n"`), ya'ni
  `_CHANGES_HEADER` 0-indeksda tura olmaydi.
* `entity_to_table` da `entity.lower()` → `entity.casefold()`.
  Entity nomlari `[A-Z_][A-Z0-9_]*` bilan parse qilinadi — faqat
  ASCII, ikkala metod bir xil natija beradi.

## 5. Yakun

* **3721 passed** (+22), 1 skipped, `requires_db` 298 (yurgizilmadi —
  bazasiz o'zgarish), migratsiyasiz, `ruff check` toza.
* Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar **tegilmadi**.
* Yangi test fayli yaratilmadi — hammasi mavjud
  `tests/test_data_model_contract.py` ning yangi **8–11-bo'limlarida**.
* **155-run ochgan sinf `app/release/` dan tashqariga chiqdi:** eski
  harness bilan olingan «0 survivor» da'vosi to'qqizinchi marta rad
  etildi va bu safar reyestr moduli emas, **sxema kontrakti**.

## 6. Keyingi qadam

1. `app/release/` dan tashqaridagi qolgan o'lchanmagan modullar,
   hajmi bo'yicha: `app/admin/security.py` (576),
   `app/bot/handlers.py` (404), `app/geo/models.py` (251),
   `app/api/openapi.py` (227), `app/jobs/refresh_coverage.py` (201),
   `app/stats/export.py` (193), `app/clustering/lookup.py` (183),
   `app/bot/keyboards.py` (183), `app/db/session.py` (161),
   `app/reports/moderation.py` (134).
2. 👤 `ruff format` ning versiya farqi (128 fayl).
3. 👤 `app.db`/`app.analytics` prefikslari.
4. 👤 `service._create_intents` ning qaytargan qiymati.
5. 👤 `cowork_session/` nusxa juftliklari.

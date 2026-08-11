# 93-sessiya — mexanizm qatlamining auditi (`pytest` siz)

**Sana:** 2026-08-11 · **Sessiya:** `local_96297907-838c-4746-a30f-825699f733d5`
**Epic:** UX (`01` §9/§10) · **Kod yozilmadi, migratsiya yo'q, vaqtinchalik fayl yo'q**

---

## 1. Sharoit — sandbox ketma-ket **oltinchi** run ko'tarilmadi

```
mcp__workspace__bash → RPC error -1: ensure user: useradd failed:
    useradd: /etc/passwd.70334: No space left on device
```

Ikki urinish, ikkalasi ham **aynan bir xil** xato. Uchinchi urinish
qilinmadi (asbobning o'z ko'rsatmasi: bir xil takrorlansa to'xta).
Ya'ni `pytest` ham, `ruff` ham bugun yo'q — 89-, 90-, 91-, 92-runlar
bilan bir xil.

👤 **`cleanup-sessions.ps1`** — bu **oltinchi** ketma-ket sandboxsiz run.
`sveta/tools/_mut84.py` va `_mut.py` hali ham o'chirilmagan.

---

## 2. Nima qilinishi kerak emasdi, va nima uchun

92-run ikkita narsani ochiq yozib qoldirgan:

1. **«Yana bitta yurgizilmagan qatlam qo'shilmasin.»** Ya'ni `01` §13
   (`UX-S1…UX-S7`) reyestri — dalillari `92_qolda_yurgizish_0607dd1a.md`
   §3 da tayyor bo'lsa ham — bugun yozilmaydi. Yozilsa,
   yurgizilmagan sath **uchinchi** faylga kengayardi.
2. **Chegara:** «Bu `pytest` emas. Yiqilish chiqsa, u bugun ko'rilmagan
   **mexanizmdan** keladi (import zanjiri, `conftest.py`, marker,
   `pytest.ini`), assertning mantig'idan emas.»

Ikkinchisi — 92-run **o'zi nomlagan** yagona qolgan xavf va u
`Read`/`Grep` bilan to'liq tekshiriladi. 93-run aynan shuni qildi:
assertlarning mantig'i emas (u 92-run da hisoblangan), **fayl umuman
yig'iladimi va import qilinadimi** degan savol.

---

## 3. Audit — to'qqizta tekshiruv, hammasi toza

### 3.1. Hujjat yo'li va bo'lim regexi

| Nima | Natija |
|---|---|
| `PRD = ROOT / "01_PRD_Samarkand.md"`, `ROOT = tests/../..` | ✅ fayl shu nom bilan `H:\tukhaev_s\svetyoq\` da |
| `_section(text, 9)` → `^## 9\. ` | ✅ `01` :280 `## 9. User Stories` |
| keyingi sarlavha `^## \d+\. ` | ✅ :318 `## 10. Use Cases`, :353 `## 11. User Flow` |
| §9/§10 ichida `## <raqam>. ` bilan boshlanadigan qator | ✅ yo'q (gherkin bloklari `Given`/`When`/`Then`) |

`_section` ning offset arifmetikasi qo'lda yurgizildi: `rest[3:]` —
«## » ni tashlaydi, `rest[: nxt.start() + 3]` — uni qaytaradi, ya'ni
kesim aynan keyingi sarlavhaning boshida tugaydi.

### 3.2. `pytest` konfiguratsiyasi (`pyproject.toml` §`[tool.pytest.ini_options]`)

```toml
testpaths = ["tests"]
asyncio_mode = "auto"
markers = ["requires_db: …"]
```

- **`addopts` yo'q** → `--strict-markers` yo'q, `-W error` yo'q.
- **`filterwarnings` yo'q** → ogohlantirish testni yiqitmaydi.
- Yangi faylda marker umuman yo'q, ya'ni marker qat'iyligi ta'sir qilmaydi.

Ya'ni konfiguratsiya tomondan yiqilish sababi **yo'q**.

### 3.3. `conftest.py`

Faqat bitta hook — `pytest_collection_modifyitems`, u faqat
`requires_db` kalitini qidiradi. Yangi faylda bunday marker yo'q →
hook unga tegmaydi. `conftest` ning o'z importlari (`app.main`,
`httpx`, `sqlalchemy`, `app.clustering.params`, `app.stats.*`)
allaqachon 2500 test bilan yashil.

### 3.4. Import zanjiri

- `app/release/__init__.py` — ✅ mavjud (paket, 13 modul).
- `app/release/user_stories.py` ning importlari: `dataclasses.dataclass`,
  `enum.StrEnum` — **faqat standart kutubxona**, 3.11+ da bor.
  Import paytida na baza, na `settings`, na fayl o'qish.
- Testning importlari: `ast`, `re`, `pathlib.Path`, `pytest`,
  `app.release.user_stories` — hammasi yechiladi.

### 3.5. ⚠️ Eng qimmatli tekshiruv — `us.<KONSTANTA>` bijeksiyasi

Modul **89-run** da, testlar **90/91-run** da yozilgan va ular
hech qachon **bir marta ham** birga yurgizilmagan. Bu `AttributeError`
sinfidagi yiqilish — assertga yetmasdan, chaqiruv paytida.

Testdagi **31 ta** noyob `us.<NOM>` murojaati modulning yuqori
darajasidagi e'lonlarga solishtirildi. **Hammasi mavjud:**

| Modul qatori | Nom |
|---|---|
| :120, :124, :129, :134, :137, :144 | `SPEC`, `SPEC_STORIES`, `SPEC_GHERKIN_STORIES`, `SPEC_CLAUSES`, `SPEC_USE_CASES`, `SPEC_FIELDS` |
| :140, :447, :366, :455, :676 | `STORY_WITHOUT_GHERKIN`, `STORY_CODES`, `STORIES`, `CLAUSES`, `USE_CASES` |
| :247, :270, :296 | `REALIZED_KEPT`, `REACHABLE_LIVE`, `NAMED_KNOWN` |
| :155, :156, :161, :165 | `PROMISED_COUNT_COLUMN`, `PROMISED_COUNT_FUNCTION`, `SHOWN_COUNT_FIELDS`, `PROMISED_WINDOW_HOURS` |
| :169, :170, :174, :175 | `FORBIDDEN_VERDICT`, `REQUIRED_VERDICT`, `VERDICTS_KNOWN_TO_SECTION_9`, `VERDICTS_IN_SPEC` |
| :180, :181, :191, :195 | `BOT_COMMANDS`, `LANGUAGE_SWITCH_STEPS`, `DOC_ERROR_CODES`, `BUILT_ERROR_CODE` |
| :199, :209, :214, :215, :220 | `CITATION_SITES`, `USE_CASE_CITATION_SITE`, `USE_CASE_2_STEPS`, `USE_CASE_2_STEPS_BUILT`, `USE_CASE_3_STEPS` |

Tiplar va funksiya ham: `Realized` (:223), `Reachable` (:250),
`Named` (:273), `UserStoriesError` (:299), `Story` (:304),
`Clause` (:321), `UseCase` (:347), `UserStoriesReport` (:765),
`evaluate` (:990). **Jami 40 nom, 40 mos.**

### 3.6. `report.<xossa>` bijeksiyasi

Testdagi **21 ta** murojaat `UserStoriesReport` ning e'lonlariga
solishtirildi — hammasi bor:

`by_realized` :819 · `by_reachable` :826 · `by_named` :833 ·
`by_story` :840 · `diverged` :847 · `inverted` :852 · `vacuous` :863 ·
`unnamed` :875 · `split_promises` :880 · `blocked_by_empty_mahallas` :894 ·
`realizations_touched` :904 · `unwitnessed_promises` :916 ·
`stories_without_gherkin` :931 · `use_cases_diverged` :936 ·
`named_count` :941 · `promises_hold` :946 · `preconditions_hold` :957 ·
`naming_holds` :966 · `use_cases_hold` :971 · `accurate` :976 ·
`clauses` (maydon) :769.

### 3.7. Dataklass maydonlari ↔ test yordamchilari

`TypeError: unexpected keyword argument` o'nga yaqin testni birdan
o'chirardi. Solishtirildi:

- `_story(**)` → `code, role, priority, gherkin, reachable, note, binds`
  ↔ `Story` :307–317 — **aynan yettita, tartibi ham mos**;
- `_clause(**)` → `code, story, promise, text, realized, named, note,
  binds, gap` ↔ `Clause` :330–343 — **aynan to'qqizta**;
- `_report(stories=, clauses=, use_cases=)` ↔ `UserStoriesReport`
  :768–770 — **aynan uchta**.

### 3.8. `ruff` — konfiguratsiya bo'yicha

`select = ["E", "F", "I", "UP", "B", "ASYNC"]`, `ignore = ["UP017"]`,
`line-length = 100`.

- **`I`** — importlar `ast/re/pathlib` → `pytest` → `app.release`:
  uchta blok, to'g'ri tartibda, orasida bo'sh qator ✅
- **`B905`** (`zip(..., strict=)`) — faylda `zip(` **umuman yo'q** ✅
- **`UP038`** (`isinstance(x, (A, B))` → `A | B`) — bu shubha
  **yopildi:** aynan shu shakl `test_stats_methodology`,
  `test_abuse_scenarios_contract`, `test_privacy_jitter_contract`,
  `test_status_machine_contract`, `test_deescalation_contract`,
  `test_golden_scenarios_contract`, `test_schema_index_parity`,
  `test_api_commit_contract`, `test_transaction_boundaries`,
  `test_notifications_outbox` va `app/admin/audit.py` da bor,
  ular esa 54-rundan beri yashil ✅
- **`E501`** — 92-run tekshirgan ✅
- **`F811`** (takrorlangan e'lon) — `ruff` uni **o'zi** ushlaydi,
  ya'ni «test jimgina o'chib qolishi» xavfi lint bilan qoplangan ✅

### 3.9. 89-run ning fayllararo bog'lanishlari

| Bog'lanish | Holat |
|---|---|
| `registries.py:676` `code="user_stories"` | ✅ takrorlanmaydi |
| `registries.py:677` `spec=user_stories_mod.SPEC` | ✅ `SPEC` bor (80-run tripwire i) |
| `_check_registry()` (import paytida yiqiladi): `SELF_CONTAINED` + `probe is not None` | ✅ :679–681 |
| `entry.probe(doc)` chaqirig'i :852 ↔ `_probe_user_stories(_doc=None)` :449 | ✅ pozitsion argument qabul qilinadi |
| `USE_CASE_CITATION_SITE = "app/release/acceptance.py"` | ✅ fayl bor |
| i18n `registry.user_stories` | ✅ `uz.json:236` **va** `ru.json:236` |

---

## 4. Bitta topilma — hisob xatosi, defekt emas

**Faylda 69 ta test bor, 70 ta emas.**

```
Grep "^def test_"  →  69
```

92-run «70 nom, 70 noyob» degan edi va aynan shu son «takrorlangan
test nomi keyingisini jimgina o'chirmaydi» degan dalilning tayanchi
edi. Dalil **kuchida qoladi** (69 e'lon, 69 har xil nom, ustiga
`ruff F811`), lekin son uchta joyda noto'g'ri: `EpicProgress.md` ning
epigrafi, §2 jadvali va `INDEX.md`. Bugun uchalasi ham to'g'rilandi.

Bo'limlar bo'yicha: §1 — 11, §2 — 16, §3 — 10, §4 — 9,
§5–§7 — 12, §8 — 11. Jami 69.

---

## 5. Bugundan keyin qanday xavf qoladi

O'qib tekshirib bo'lmaydigan **ikkitasi**:

1. `evaluate()` ning haqiqiy reyestrdagi `__post_init__` qorovullari —
   92-run ularni qo'lda hisoblagan, lekin interpretator yurgizmagan;
2. muhitning o'zi (`app` paketining `sys.path` da bo'lishi —
   `PYTHONPATH=/tmp/sv59` yoki `pip install -e .`).

Ikkalasi ham faqat sandbox yoki CI bilan yopiladi.

---

## 6. Keyingi qadam — 94-run, shu tartibda

1. Sandbox tiklansa: `pytest tests/test_user_stories_contract.py -q`,
   keyin butun to'plam, keyin `ruff check app tools tests alembic`.
2. Mutatsiya (85–87-runlarning har biri 1–6 survivor topgan).
3. **Shundan keyingina** `01` §13 (`UX-S1…UX-S7`) reyestri —
   dalillar `92_qolda_yurgizish_0607dd1a.md` §3 da.

⚠️ Yana bitta yurgizilmagan qatlam qo'shilmasin.

👤 Yangi savol yo'q — 88-run ning beshtasi o'zgarishsiz ochiq
(bittasi 92-run da aniqlashtirilgan).
👤 `cleanup-sessions.ps1` — **oltinchi** ketma-ket sandboxsiz run.

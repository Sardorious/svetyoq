# 91-sessiya — UX: kontrakt testining `ast` qatlami

**Sana:** 2026-08-11
**Epic/blok:** UX (`01` §9 «User Stories» + §10 «Use Cases»)
**Fayl:** `sveta/tests/test_user_stories_contract.py` — yangi §8 bo'limi
**Natija:** 13 yangi test; migratsiya yo'q, yangi modul yo'q, vaqtinchalik
fayl yo'q, 👤 yangi savol yo'q.

---

## 1. Sandbox — ketma-ket to'rtinchi rad

```
bash failed on resume, create, and re-resume.
useradd failed: No space left on device
```

88-, 89-, 90- va 91-runlar — to'rttasi ham sandboxsiz. Ya'ni `pytest` ham,
`ruff` ham, mutatsiya ham yurgizilmadi va **90-run yozgan fayl hali ham hech
qachon ishga tushirilmagan**. 90-run ning «91-run birinchi navbatda faylni
yurgizsin» degan sharti bajarilmadi.

👤 **Eslatma odamga:** `cleanup-sessions.ps1` — to'rtinchi ketma-ket
sandboxsiz run. `sveta/tools/_mut84.py` va `sveta/tools/_mut.py` hali ham
o'chirilmagan (agent `allow_cowork_file_delete` ni chaqirmaydi — `CLAUDE.md` §1).

## 2. Qaror: to'rtinchi runni ham kutishga sarflamaslik

90-run chegarani aniq qo'ygan edi: *hukmni reyestrning o'zidan yoki
hujjatdan olish mumkin bo'lsa — bugun; kodning tuzilishidan olish kerak
bo'lsa — 91-run.* Chegara bugun ham o'zgarmadi, faqat ikkinchi tomoni
yozildi. Sabab sodda: qatlam yozilmasa, bo'lim to'rt run ketma-ket
o'sha joyda turadi va sandbox qachon tiklanishi noma'lum.

Muqobil variant — **hech narsa yozmaslik va faqat hisobot berish** — 88-run
allaqachon bir marta tanlagan yo'l. Ikkinchi marta takrorlash bo'limni
oldinga surmasdi: 88-run ning tahlili tugagan, 89-run ning reyestri
yozilgan, 90-run ning uch qatlami tayyor — qolgani faqat shu qatlam edi.

## 3. Avval: 90-run ning fayli qo'lda tekshirildi

Yangi qatlamni qo'shishdan oldin butun mavjud fayl manbaga solishtirildi
(`Read`, `Grep`). Tekshirilganlari va natijalari:

| Nima | Natija |
|---|---|
| Uch o'qning taqsimoti (`by_realized`, `by_reachable`, `by_named`) | qo'lda qayta hisoblandi — mos |
| `diverged` (7), `vacuous` (4), `unnamed` (8), `named_count` (1) | mos |
| `split_promises` = `{"independent-count": ("C-3","C-4")}` | 9 qator − 8 va'da = 1 — mos |
| `blocked_by_empty_mahallas` = `("C-6","C-8")` | `binds` da `mahalla` — mos |
| `unwitnessed_promises` = `("C-7",)` | `BUILT` × `UNREACHABLE` — mos |
| To'rtala yakuniy shart `False` | mos |
| `__post_init__` ning beshala qorovuli — har biri alohida | qorovullarning **ishga tushish tartibi** tekshirildi: har testda birinchi yiqiladigan qorovul aynan kutilgani |
| `01` §9 dan 5 hikoya, prioritet, rol, gherkin | PRD 280–314 qatorlari bilan solishtirildi — mos |
| `Then`/`And` bandlari ↔ `promise` bijeksiyasi | 2+2+2+0+2 = 8 = `SPEC_CLAUSES − 1` — mos |
| `01` §10 dan 3 stsenariy, sarlavha, katak nomlari birlashmasi (6) | mos; `UC-S3` da 4 katak (< 6) |
| `STEP_RE` ning «H3.» tuzog'i | qo'lda qayta yurgizildi: `[1,2,3,4,5]`, `[1,2,3,4,5]`, `[1,2,3,4]` — «H3.» sanalmaydi |
| 21 ta `binds` fayli | hammasi mavjud (`app/core/i18n` — paket, `__init__.py` orqali) |

Defekt topilmadi. Ya'ni 90-run ning fayli qo'lda tasdiqlangan darajada
to'g'ri — lekin bu `pytest` emas.

## 4. Yozilgani — §8 `ast` qatlami

Yordamchi qatlam: `_module_path` (modul ham, paket ham), `_tree`, `_class`,
`_function`, `_assigned_names`, `_string_attributes`, `_attributes_of`,
`_identifiers`, `_module_symbols`, `_registrations`, `_is_command_filter`.

**Matn hech qayerda qidirilmaydi** — `_identifiers()` faqat `Name`,
`Attribute`, `arg`, `alias`, `keyword` ni yig'adi, ya'ni docstring va izoh
hukmga umuman kirmaydi (86-run ning qoidasi: yozilgan kod qidirilayotgan
kodga aylanadi).

### 4.1. `binds` — mavjudlikdan yechilishga

90-run har `binds` yozuvi uchun faqat **fayl bormi** deb so'raydi. Endi
`modul:simvol` shaklidagi har yozuv `_module_symbols()` bergan sathga
tegishli bo'lishi kerak: yuqori darajadagi nomlar + `Sinf.atribut` +
`Sinf.metod` + importlar. Jami **33 ta** bind shu yo'ldan o'tadi
(`Situation.total_reports`, `Outage.independent_reporters`,
`Region.default_language` kabi ikki bo'g'inlilari ham).

### 4.2. `C-3`/`C-4` — «to'g'ri son bir maydon narida» endi o'lchanadi

Ikki testning **ayirmasi** da'voni beradi:

* `render()` `situation` dan aynan `{started_at, total_reports, others}`
  ni o'qiydi — `==`, `<=` emas, ya'ni yangi maydon qo'shilsa hukm eskirishi
  kerak;
* `app/bot/reply.py` ning **butun daraxtida** `independent_reporters` ham,
  `count_independent` ham nom sifatida yo'q;
* o'sha ikkalasi `app.clustering.independence` va `app.clustering.models`
  da **bor**.

### 4.3. `C-5` — `INVERTED` hukmi kod tuzilishidan

`decide()` ning `situation` dan o'qigan maydonlari ichida `coverage_ok` bor
va va'da qilingan ustun yo'q. Taqiqlangan verdiktning **nomi** esa
`Verdict` sinfining qiymatlaridan hisoblanadi
(`FORBIDDEN_VERDICT = "no_outage_covered"` → `NO_OUTAGE_COVERED`) va o'sha
nom `decide()` ning qaytarganlari orasida talab qilinadi. `VERDICTS_IN_SPEC`
enum ning uzunligidan kichik ekani ham shu yerda qulflanadi (2 < 4 < 6).

### 4.4. `UC-S1` — xato kodlari sinf atributlaridan

`errors.py` ning oltita sinfidan `code` atributi yig'iladi
(`internal_error`, `not_found`, `validation_error`, `out_of_region`,
`rate_limited`, `forbidden`). `BUILT_ERROR_CODE` bor; `DOC_ERROR_CODES`
ning ikkalasi ham — na katta, na kichik harfda — yo'q.

### 4.5. Ikkita konstanta e'londan hisobga o'tdi

* `BOT_COMMANDS` — `Command`/`CommandStart` filtri bilan qilingan
  `register` chaqiruvlari **sanaladi** (`handlers.py:388–389`) → 2;
* `LANGUAGE_SWITCH_STEPS` — `on_language*` handlerlarining
  registratsiyalari sanaladi (`on_language` callback + `on_language_button`
  message) → 2, va ularning **birortasi ham** komanda filtri emasligi talab
  qilinadi. «Одной командой» endi kod tomonidan inkor qilinadi.

## 5. Nima qilinmadi

Hech narsa tuzatilmadi. Bot ko'rsatadigan son almashtirilmadi,
`NO_OUTAGE_COVERED` olib tashlanmadi, mahallani tanlash yo'li
qo'shilmadi — barchasi 👤 qaroriga bog'liq (88-run ning beshta savoli
o'zgarishsiz ochiq). Test o'lchaydi, tahrirlamaydi.

## 6. Keyingi qadam — 92-run, shu tartibda

1. **`pytest tests/test_user_stories_contract.py`** — fayl to'rt run
   ketma-ket yurgizilmadi. Ziddiyat chiqsa modul ham testsiz yozilgan
   (89-run) — ayb testda bo'lishi shart emas.
2. `ruff check app tools tests alembic` va butun to'plam.
3. Mutatsiya: 85–87-runlarning har biri aynan `ast` qatlamida 1–6 survivor
   topgan, ya'ni bu qatlam birinchi urinishda **hech qachon** to'g'ri
   chiqmagan.

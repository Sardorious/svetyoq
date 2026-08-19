# 165-run — SEC: 164-running yozuvi yopildi (sandbox yo'q, sabab topildi)

**Sana:** 2026-08-19
**Sessiya:** `local_4dcb6bfb`
**Epic:** SEC (`01` §20 + BRD «Безопасность» NFR)
**Natija:** kod yozilmadi; 164-run ning yakunlanmagan hisoboti yopildi,
uning natijasi statik tekshirildi va **to'xtash sababi aniqlandi**.

---

## 1. Boshlanish: sandbox umuman ko'tarilmadi

Birinchi `mcp__workspace__bash` chaqiruvi:

```
Workspace unavailable. The isolated Linux environment failed to start
(VM_DISK_SPACE_INSUFFICIENT). You can still use file tools directly.
```

Ikkinchi urinish ham bir xil. Bu **122–140 seriyasidagi xatodan boshqa**:
o'shanda muhit ko'tarilar edi va ichida `useradd failed: No space left on
device` chiqardi, ya'ni `TMPDIR=/dev/shm/tNNN` kabi hiylalar ma'noga ega
edi. Bu safar VM ning o'zi yo'q — `df` ham, `ls` ham bajarilmaydi.

Ya'ni bu runda `pytest`, `ruff` va mutatsiya o'lchovi **mumkin emas**.
163 qoldirgan tartibning (1) bandi (`app/bot/handlers.py` va boshqa
o'lchanmagan modullar) shu sababdan olinmadi: mutatsiya verdikti
`pytest` ning `returncode` idan olinadi.

## 2. Kutilmagan topilma: 164-run yozuvsiz tugagan

`INDEX.md` ning «Qayerda to'xtadik» qatori **163** ni ko'rsatardi va
`PROGRESS.md` ning run jurnalining tepasi ham 163 (`| 2026-08-14 | DATA |`)
edi. Lekin:

* `PROGRESS.md` ning «Joriy holat» katagi **164-run** ni to'liq bayon
  qilgan (70 mutatsiya → 6 KILLED, **64 SURVIVOR**, 91 % — seriyadagi eng
  yuqori ulush);
* `tests/test_security_posture_contract.py` da 164 yozgan yangi
  bo'limlar (**8–12**, +49 test) **bor**.

Ya'ni 164 ishni bajargan, «Joriy holat» katagini yozgan va shundan keyin
to'xtagan: run jurnali qatori, SEC epic qatori, `EpicProgress.md` va
`INDEX.md` yangilanmasdan qolgan. Agar bu run buni sezmasdan «163 dan
davom etaman» desa, `app/admin/security.py` **ikkinchi marta** o'lchanardi.

## 3. Sabab: haftalik limit, sandbox emas

`mcp__session_info__list_sessions` 162-rundan (`local_7c521ce3`) keyin
**oltita** sessiya ko'rsatdi. Transkriptlar o'qildi:

| Sessiya | Nima bo'lgan |
|---|---|
| `local_0ec4912a` | 163-run (DATA) — to'liq bajarilgan |
| `local_7c72e9c0` | **164-run** — o'nga yaqin `bash`, `TaskCreate`/`TaskUpdate`, oxirgi `Edit`, keyin: **`You've hit your weekly limit · resets Aug 18, 3am (Asia/Tashkent)`** |
| `local_ea5c672a` | bo'sh — prompt va o'sha limit xabari |
| `local_6df5c1b7` | bo'sh — bir xil |
| `local_a6ddd0fb` | bo'sh — bir xil |
| `local_a89346d3` | bo'sh — bir xil |

Xulosa: 164 **haftalik foydalanish limiti** tufayli o'rtada uzildi —
`allow_cowork_file_delete` ham, sandbox ham sabab emas. Bu **yangi
bloklovchi sinf**: 30-sessiya (o'chirish tasdig'i) va 122–140 (disk)
dan farqli. Undan keyingi to'rtta rejalashtirilgan run limit tiklanmagani
uchun umuman ishlamadi — ular bo'sh, ya'ni CLAUDE.md §4.1.3 bo'yicha
arxivga qo'shilmaydi va run raqami ham berilmaydi.

**Amaliy xulosa keyingi runlarga:** yozuv (`PROGRESS.md` jurnal qatori +
`INDEX.md`) ishning **oxirida** emas, **o'lchov tugashi bilanoq**
yozilsin. 164 ning butun o'lchovi saqlanib qoldi, chunki u testni yozib
ulgurdi — lekin uni **topib olish** uchun 165 ning yarim runi ketdi.

## 4. 164 ning natijasini statik tekshirish

`pytest` yo'q, ya'ni «yashil» deb aytish mumkin emas. O'rniga fayl
ichidagi **literal jadvallar** manba bilan qo'lda solishtirildi — aynan
shular buzilsa to'plam qizil bo'lardi:

| Nima solishtirildi | Natija |
|---|---|
| §10 ning `REGISTRY` jadvali (17 qator × 9 ustun) ↔ `GUARANTEES` | ustunma-ustun mos, tartib ham mos |
| §9 ning o'nta kutilgan xabari ↔ `registry_errors()` ning literal matnlari | mos; har `_row(...)` chindan **bitta** qoidani buzadi (tekshirildi: `claim=-1` da `doc_item` bor, `MISSTATED` da `narrower` qoidasi ikki marta otilmaydi, `LONG_NOTE` uzunligi aynan 60 — `< 60` bo'sag'asining chetida) |
| §11 ning `PDN_HINTS` ↔ `PDN_COLUMN_HINTS` | aynan; o'n beshta ishora uchala tur bo'ylab **kesishmaydi**, ya'ni `test_every_single_hint_is_detected` ning «bitta kalit» kutilmasi asosli |
| §8 ning `Posture`/`Mechanism` jadvallari ↔ `StrEnum` lar | qiymatlar va tartib mos |
| §8 ning `SPEC` testi | `SECURITY_SECTION = "## 20. Security"` → `01 §20` = `security.SPEC` |
| `tests/*tmp*` | bo'sh — 164 vaqtinchalik yoki mutant fayl qoldirmagan |

**Yagona ziddiyat:** fayl docstringi `## 164-run: 8–13-bo'limlar` deb
yozgan, aslida fayl 12-bo'limda tugaydi va `PROGRESS.md` ning o'z katagi
ham «8–12» deydi. Docstring `Edit` bilan tuzatildi — ehtimol aynan shu
sarlavha 164 ning uzilgan `Edit` idan qolgan iz.

⚠️ **Tekshirilmagani:** 164 ning «3770 passed» da'vosi. Uni tasdiqlash
uchun `pytest` kerak, ya'ni bu sandbox tiklangandan keyingi **birinchi**
qadam — yangi nishon olishdan oldin.

## 5. Yon topilma: «o'n olti kafolat» aslida o'n yetti

`PROGRESS.md` ning SEC qatori 71-rundan beri «o'n olti kafolat» deb
kelgan va `test_the_report_carries_every_guarantee` ning docstringi ham
shuni takrorlaydi. Sanoq: nasrdan 7 + jadvaldan 8 + BRD NFR laridan 2 =
**17**, va 164 ning `REGISTRY` jadvali ham 17 qator. Epic qatori
tuzatildi; test docstringidagi nasr **tegilmadi** — u o'lchanadigan da'vo
emas va uni tuzatish sandboxsiz tekshirib bo'lmaydigan o'zgarish qo'shardi.

## 6. Nima o'zgardi

* `sveta/tests/test_security_posture_contract.py` — bitta satr
  (docstring: `8–13` → `8–12`);
* `sveta/PROGRESS.md` — run jurnaliga **ikkita** qator (164 va 165),
  «Joriy holat» da 165 tepaga chiqdi va 164 «Oldingi run» ga surildi,
  SEC epic qatori yangilandi;
* `sveta/EpicProgress.md` — SEC qatori, §4 ning o'lchanmagan modullar
  ro'yxatidan `admin/security.py` chiqarildi, §4 ga sandbox va haftalik
  limit bloki qo'shildi, «Oxirgi yangilanish» yangilandi;
* `cowork_session/` — shu fayl va `INDEX.md`.

Mahsulot kodi, migratsiya, konfiguratsiya va hujjatlar tegilmadi.

## 7. Keyingi qadam

1. **Sandbox tiklanganda birinchi ish:** butun bazasiz to'plamni
   yurgizish va 164 ning +49 testi yashil ekanini tasdiqlash. Faqat
   shundan keyin yangi nishon.
2. 163/164 qoldirgan tartib: `app/bot/handlers.py` (404),
   `app/geo/models.py` (251), `app/api/openapi.py` (227),
   `app/jobs/refresh_coverage.py` (201), `app/stats/export.py` (193),
   `app/clustering/lookup.py` (183), `app/bot/keyboards.py` (183),
   `app/db/session.py` (161), `app/reports/moderation.py` (134).
3. 👤 `cleanup-sessions.ps1` ni ishga tushirish va Cowork ni qayta
   ishga tushirish (sandbox VM).
4. 👤 `cowork_session/` da noto'g'ri nom bilan yaratilgan
   `100_sec_yozuvni_yopish_ad837191.md` ni o'chirish — mazmuni bu faylga
   ko'chirilgan, o'zi bo'shatilgan (`allow_cowork_file_delete`
   chaqirilmaydi, CLAUDE.md §1).
5. 👤 Ochiq qolgan savollar o'zgarmadi: `ruff format` versiya farqi,
   `app.db`/`app.analytics` prefikslari, `service._create_intents`,
   `cowork_session/` nusxa juftliklari (`100_*` ikkita, `144`/`100`
   juftligi).

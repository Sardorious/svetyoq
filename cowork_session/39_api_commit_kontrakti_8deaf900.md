# 39-sessiya — API da `commit` kontrakti

**Sana:** 2026-08-08
**Session ID:** `local_8deaf900`
**Epic:** E1 (ko'ndalang) / E8 — API tranzaksiya chegarasi
**Natija:** ✅ `get_session()` ning `commit` qilmasligi endi butun `app/` bo'ylab
o'lchanadi. ⚠️ Sandbox **o'ninchi ketma-ket run** yiqildi (INFRA-1).

---

## 0. Sandbox

Uch urinish, uchalasi ham bir xil:

```
useradd failed: /etc/passwd.NNNNN: No space left on device
```

Ya'ni `ruff check` ham, `pytest` ham **yana** ishga tushmadi. Bu §19 va
29–39 — **o'n bitta** run tekshirilmagan kod qoldirdi. 36-running 15 ta
`requires_db` testi, 37-running 9 tasi, 38-running 6 tasi va shu running
6 tasi hech qachon ishlamagan.

👤 `cleanup-sessions.ps1` — C diskdagi sessiya papkalari.

---

## 1. 38-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q

`tests/test_transaction_boundaries.py` ning har bir tayanchi manba bilan
solishtirildi.

**Skanerning `registered` to'plami ishlaydi.** `app/jobs/runner.py:44–49`
da oltita chaqiruv aynan `<modul>.register()` shaklida
(`Attribute(value=Name(...), attr="register")`), ya'ni
`node.func.value.id` to'g'ri o'qiladi va to'plam
`{evaluate_outages, build_map_snapshot, process_outbox, refresh_coverage,
purge_exact_geom, daily_digest}` bo'ladi. Chaqiruvlar `register_jobs()`
**ichida**, lekin skaner `ast.walk` bilan butun moduldan yuradi — muhim
emas. `JOBS.append(JOB)` esa `.append`, ya'ni to'plamga tushmaydi.

**Ikkala istisno ham haqiqiy.** `process_outbox.py:100` va
`daily_digest.py` da modul darajasida `JOB = Job(...)` bor, funksiya nomi
ikkalasida ham `run`, ya'ni `SEQUENTIAL_BY_DESIGN` kalitlari
(`app.jobs.process_outbox.run`, `app.jobs.daily_digest.run`) `_offenders()`
qaytaradigan nomlar bilan aynan mos.

**Offenderlar ro'yxati haqiqatan ikkita.** `NETWORK_METHODS` bo'yicha butun
`app/` qidirildi — mos keladigan chaqiruvlar faqat uch modulda:
`bot/handlers.py` (28 ta `answer`, hammasi `session_scope()` dan
**tashqarida** — 37-sessiyaning ishi), `bot/notifier.py:45`
(`send_message`, tranzaksiya yo'q), `notifications/service.py:254` va
`daily_digest.py:84` (`sender.send`, ikkalasi ham `deliver` funksiyasida,
u yerda `session_scope()` yo'q). Ya'ni `TRANSPORT_FACTORIES` orqali
topiladigan ikkita `build_sender()` — yagona natija, 38-run yozganidek.

**Bitta noaniqlik topildi va u zararsiz.** 38-sessiyaning hisoboti
`handlers.py` da **14 ta** `session_scope()` bloki deydi, bugungi manbada
esa **15 ta** (butun `app/` bo'ylab 21 ta, 7 modulda). Test `>= 10`,
`>= 18` va `>= 7` talab qiladi — hammasi bajariladi. Sanoq xatosi
hisobotda, kodda emas.

**Qirra:** `MIN_MODULES_WITH_SCOPES = 7` bugungi qiymatga **aynan teng**.
Vazifalardan biri `session_scope()` dan voz kechsa test yiqiladi — bu
ataylab shunday («skaner bo'shab qolmasin»), lekin keyingi run buni
«noto'g'ri test» deb o'qimasin.

---

## 2. Running ishi — API da `commit` invarianti

38-run «Ochiq savollar» ga qoldirgan nomzod olindi.

### Muammo

`app/db/session.py` da ikkita fabrika bor va ular **turlicha tugaydi**:

| | chiqishda | istisnoda |
|---|---|---|
| `session_scope()` | `commit` | `rollback` |
| `get_session()` (FastAPI) | **hech narsa** | **hech narsa** |

`app/api/` `session_scope()` ni umuman ishlatmaydi, ya'ni har bir
yozadigan yo'l `await session.commit()` ni **o'zi** chaqirishi shart.
Bugun sanoq to'g'ri: to'rtta o'zgartiruvchi yo'l (`reject_outage:197`,
`merge_outage:212`, `block_user:242`, `set_trust:253`) va to'rtta
`commit`.

**Lekin buni hech narsa ushlab turmaydi.** Unutilgan chaqiruv 33-, 34- va
36-sessiyalar sanagan sinfdan: **xato chiqmaydi**. Javob `200` qaytadi,
`ChangeOut` da `before`/`after` to'g'ri ko'rinadi, `audit_log` qatori ham
yoziladi — va so'rov tugashi bilan sessiya `commit` siz yopiladi. Ya'ni
moderatorning qarori ham, uning audit izi ham jimgina yo'qoladi, ekranda
esa muvaffaqiyat turadi.

### Uch qatlam, chunki uchtasi ham alohida buziladi

1. **Chaqiruv bormi.** Eng oddiy nosozlik: yangi endpoint yozgan odam
   `session_scope()` naqshiga o'rganib `commit` ni tushirib qoldiradi.
2. **Unga yetib boradigan yo'l bormi.** 36-sessiya `cmd_update` da aynan
   shu holatni topgan: `audit.record(` chaqiruvi ham, uning to'g'ri joyi
   ham bor edi, faqat erta `return` uni chetlab o'tardi. Bu yerda narx
   teskari va undan ham jimroq — erta `return` `commit` ni chetlab
   o'tadi.
3. **Qoida ma'nosini yo'qotmadimi.** Har bir funksiyaga `commit` qo'yib
   chiqish 1-qatorni o'tkazardi, shuning uchun **o'qiydigan yo'llarda
   `commit` taqiqlanadi**.

### Qarorlar

- **`raise` taqiqlanmaydi, faqat `return`.** Istisnoda so'rov `commit`
  qilmasligi **kerak** (`NotFoundError`, `ValidationError` — yozilgan
  narsa qolmasin), `return` esa muvaffaqiyat degani. Ikkalasini bir xil
  ko'rish testni har bir tekshiruvda yiqitardi va u o'chirilardi.
- **`commit` funksiya tanasining eng yuqori darajasida turishi shart.**
  `if changed: await session.commit()` birinchi ikkala testni ham
  o'tkazardi, lekin o'zgarish qilingan va shart bajarilmagan yo'lni ochiq
  qoldirardi. Shartli `commit` kerak bo'lsa test yiqiladi va bu **ko'rib
  chiqiladigan qaror** bo'ladi.
- **Skaner `app/api/` ga emas butun `app/` ga qaraydi.** Marker — yo'lning
  papkasi emas, `DbSession` bog'liqligi. `app/bot/webhook.py:45` ham
  `@router.post`, lekin sessiyasiz (u `dispatcher.feed_update` orqali
  ishlaydi va tranzaksiya `app.reports` da ochiladi) — ya'ni qoidaga
  tushmaydi va bu to'g'ri. Papkaga bog'lansa, `app/api/` dan tashqarida
  yozilgan birinchi endpoint jim o'tib ketardi.
- **Sessiya nomi parametrdan olinadi, `"session"` deb qotirilmaydi.**
  `_commit_calls` aynan o'sha nomni qidiradi, ya'ni boshqa obyektning
  `commit()` i (masalan tashqi mijoznikini) qoidaga aralashmaydi.
- **`get_session()` ning o'zi ham qulflandi.** Butun test uning hech
  narsa qilmasligiga tayanadi. U `session_scope()` kabi `commit`
  qiladigan qilib o'zgartirilsa, `test_get_session_still_does_not_commit`
  yiqiladi va aytadigan gapi aniq: bu faylning qoidalari qayta ko'rib
  chiqilsin. **Test qarorni qabul qilmaydi, faqat uni ko'rinadigan
  qiladi** — tanlov 38-sessiyada odamga qo'yilgan va ochiqligicha qoladi.

### Rad etilgan variant

**`get_session()` ni `session_scope()` kabi qilish** — hamma yo'lni bir
vaqtda tuzatardi va yangi endpoint hech narsa unutmasdi. Rad etilmadi,
**qoldirildi**: bu odamning ochiq savoli va uning narxi bor — o'sha
o'zgarish `commit` ni **yo'lning qaroridan** bog'liqlikning umumiy
xatti-harakatiga aylantiradi, ya'ni xato javob qaytargan yo'lda ham nima
`commit` bo'lishini endi yo'lning o'zi emas, `HTTPException` ning
FastAPI ichida qanday ko'tarilishi hal qiladi. Bugungi ish har ikkala
javobda ham foydali: o'zgarish qilinsa test aynan shu joyni ko'rsatadi.

### Fayllar

- **yangi** `sveta/tests/test_api_commit_contract.py` — 6 ta bazasiz
  test, `ast` skaneri.
- `sveta/app/db/session.py` — `get_session()` docstringi: nima uchun u
  `commit` qilmaydi, unutilgan chaqiruvning ko'rinishi, qoida qayerda
  o'lchanadi va ochiq savol.

Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**,
**xatti-harakat o'zgarishi ham yo'q** — faqat hujjat va kontrakt.

---

## 3. Keyingi run uchun

1. ⚠️ **Sandbox tiklanganda birinchi ish — butun `pytest`, yangi kod
   emas.** O'n bir run tekshirilmagan; 36–39 runlarning 45 ga yaqin testi
   hech qachon ishga tushmagan.
2. **Ochiq nomzod:** `05` §2 DDL ↔ koddagi indekslar farqi (hamon ochiq,
   34-rundan beri).
3. **Yopilgan nomzodlar** (qayta ochilmasin): `Fake*` ↔ haqiqiy tip
   (38-run, drift yo'q); `02` Faza 0 (34-run, kod talabi yo'q);
   API `commit` (shu run).
4. 👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
   `.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`. Nomni
tuzatish o'chirishni talab qiladi. 👤

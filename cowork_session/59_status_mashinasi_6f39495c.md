# 59-sessiya — `05` §4.4–§4.5 status mashinasi kontrakti

**Sana:** 2026-08-09
**Sessiya:** `local_6f39495c-…`
**Epic:** E5/E5b (ko'ndalang) — kontrakt qatlami, 19-fayl
**Natija:** ✅ `05` §4.4 (status mashinasi diagrammasi) va §4.5 («Svet keldi»)
endi hujjatdan o'qiladi. **Defekt topilmadi**; testlarning o'zi **11 ta
mutatsiya** bilan tekshirildi.
**Sandbox:** ✅ ishladi — `pytest -m "not requires_db"` → **1398 passed,
1 skipped, 212 deselected**; `ruff check app tools tests alembic` → toza.

---

## 1. Sandbox: muhit noldan tiklandi

56–58 sessiyalar `/tmp/sv56` muhitini qayta ishlatgan edi — bu run u **yo'q**
(sandbox toza ko'tarilgan). Tiklash tartibi, keyingi runlar uchun:

| Muammo | Yechim |
|---|---|
| `$HOME` (`/sessions/<nom>`) **100% to'la** — 12 MB bo'sh | `pip` ni butunlay `/tmp` ga olib chiqish: `--target /tmp/sv59`, **plus** `TMPDIR=/tmp/tmpdir` va `PIP_CACHE_DIR=/tmp/pipcache`. Faqat `--target` yetarli **emas**: pip yuklab olishni va yig'ishni baribir `$HOME/.cache` da qiladi va `OSError(28)` bilan yiqiladi |
| bitta `pip install` ~180 s limitiga sig'maydi | uchta partiyaga bo'lindi (test asboblari → SQLAlchemy oilasi → FastAPI/aiogram/h3). Kesh `/tmp` da qolgani uchun keyingi partiyalar tez |
| fon rejimi (`nohup … &`) ishlamaydi | har `bash` chaqiruvi tugaganda protsess o'ldiriladi — birinchi urinishda `pip` shunday yo'qoldi. Har buyruq **bitta** chaqiruvda tugashi kerak |
| interpretator 3.10, kod 3.11+ | `/tmp/sv59/sitecustomize.py` da `enum.StrEnum` va `datetime.UTC` shimi (56-sessiyanikining aynan o'zi) |

Ildiz disk (`/`) da 3.7 GB bo'sh edi, ya'ni to'lgan narsa — **faqat**
`$HOME`. 👤 `cleanup-sessions.ps1` baribir kerak.

## 2. Nima uchun aynan §4.4/§4.5

58-sessiyadan keyin `EpicProgress.md` §3 da uchta ochiq joy qoldi: `06` §11
(34-run qisman yopgan), `05` §3.1 (jitter) va **`05` §4.4/§4.5**. Oxirgisi
tanlandi, chunki uning bo'shlig'i boshqalardan **jiddiyroq**: §4.4 ning
artefakti jadval ham, formula ham emas — **mermaid diagrammasi**.

Diagramma hujjatda rasm bo'lib ko'rinadi, ya'ni uni hech kim satr-satr
o'qimaydi. Kodda esa u **uch marta** takrorlanadi:

1. `ALLOWED_TRANSITIONS` — haqiqiy qoida;
2. `app/clustering/status.py` ning **modul docstringi** — diagrammaning
   qo'lda ko'chirilgan nusxasi (ustida «`05` §4.4» deb yozilgan);
3. `OPEN_STATUSES` / `TERMINAL_STATUSES` — o'sha diagrammaning hosilasi,
   lekin alohida yozilgan.

Uchalasi bir-biridan mustaqil. Diagrammaga o'tish qo'shilsa (masalan
`resolved --> pending`, «svet yana o'chdi») hujjat o'zgaradi va **hech qanday
test yiqilmaydi**: xato faqat ish vaqtida, foydalanuvchi harakati ustida
`IllegalTransitionError` bo'lib chiqadi. Teskarisi ham yomon: koddan o'tish
olib tashlansa, diagramma mavjud bo'lmagan yo'lni va'da qilib qolaveradi.

## 3. §4.4/§4.5 dan olingan artefaktlar

| Artefakt | Qayerda edi | Endi qayerdan o'qiladi |
|---|---|---|
| 7 ta o'tish, ikkala yo'nalishda | `ALLOWED_TRANSITIONS` qo'lda | `test_transitions_match_the_diagram_exactly` |
| tugunlar to'plami | `OutageStatus` qo'lda | `test_states_match_the_enum` |
| `--> [*]` qatorlari | `TERMINAL_STATUSES` qo'lda | `test_terminal_states_come_from_the_diagram` |
| chiquvchi o'qi bor statuslar | `OPEN_STATUSES` qo'lda | `test_open_statuses_are_exactly_those_with_outgoing_edges` |
| `[*] --> pending` | `repository.create_outage` da literal | `test_initial_edge_names_the_creation_status` |
| docstringdagi nusxa | hech qayerda solishtirilmagan | `test_module_docstring_copy_matches_the_document` |
| yorliq `independent_reporters >= min_reporters` | hech qayerda | `test_confirm_edge_label_names_real_code` (+ chegara testi) |
| yorliq `moderator` (2 ta o'tish) | hech qayerda | `test_moderator_edges_are_never_taken_automatically` |
| yorliq `autoclose` (2 ta o'tish) | hech qayerda | `test_autoclose_edge_exists_for_every_open_status` |
| `reports.kind = 'restored'` | kodda **uch** nusxa | `test_restored_kind_comes_from_the_document` |
| §4.5 «2 soat» ↔ §4.2 `autoclose_after` | hech qayerda | `test_two_hours_matches_the_autoclose_parameter` |
| «ochiq hodisa doirasida … darhol `resolved`» | `test_clustering_status.py` da qisman | `test_restored_rule_covers_every_open_status`, `…_is_immediate` |
| nasr: `merged` — status, o'chirish emas | hech qayerda | `test_merged_prose_names_a_real_column` |

## 4. Uchta jim yo'nalish (nima uchun bu testlar kerak edi)

- **`OPEN_STATUSES` diagrammadan ajralishi.** U so'rovlarda ham, qisman
  indeksda ham ishlatiladi (`ix_outages_status_region_id_open`). Diagrammaga
  yangi ochiq status qo'shilsa yoki `OPEN_STATUSES` ga ortiqchasi tushsa,
  hodisa xaritada ko'rinmay qolishi yoki yopilgandan keyin ham ko'rinishi
  mumkin edi — va bu **xato bo'lib chiqmasdi**, faqat noto'g'ri javob.
- **`'restored'` literalining uch nusxasi.** `REPORT_KINDS`,
  `app/clustering/service.py:KIND_RESTORED`, `app/bot/reply.py:KIND_RESTORED`.
  Bot niki ajralsa, «Svet keldi» tugmasi ishlayotgandek ko'rinardi, lekin
  klasterlash uni oddiy xabar deb qabul qilardi — ya'ni **hodisa yopilmasdi**
  va yangi uzilish ochilardi.
- **§4.4 va §4.5 ning ziddiyati.** Diagramma `'restored'` ni **faqat**
  `confirmed --> resolved` yorlig'ida ko'rsatadi, §4.5 nasri esa «**ochiq
  hodisa** doirasida» deydi, ya'ni `pending` ni ham qamraydi. Kod §4.5 ga
  ergashadi (to'g'ri: `pending --> resolved` o'tishi diagrammada bor), lekin
  ikki bo'lim bir-biri bilan hech qachon solishtirilmagan edi.
  `test_restored_rule_covers_every_open_status` endi aynan shu ko'prikni
  qulflaydi.

## 5. Defekt topilmadi — shuning uchun 11 mutatsiya

Kod hujjatga mos chiqdi. «Yashil test» ning o'zi hech narsani isbotlamagani
uchun har tasdiq buzib ko'rildi:

| # | Mutatsiya | Yiqilgan test |
|---|---|---|
| M1 | hujjatdan `confirmed --> merged` olib tashlandi | shakl, `…match_the_diagram_exactly`, docstring nusxasi, moderator o'tishlari |
| M2 | hujjatga `resolved --> pending` qo'shildi | shakl, `…absent_from_the_diagram_are_rejected`, docstring nusxasi |
| M3 | §4.5 «2 soat» → «3 soat» | `test_two_hours_matches_the_autoclose_parameter` |
| M4 | §4.2 `autoclose_after` 120 → 90 daq | o'sha test |
| M5 | §4.5 `'restored'` → `'restore'` | `test_restored_kind_comes_from_the_document` |
| M6 | `status.py` docstringidagi yorliq o'zgartirildi | `test_module_docstring_copy_matches_the_document` |
| M7 | `OPEN_STATUSES` ga `RESOLVED` qo'shildi | ochiq statuslar + autoclose + restored qamrovi |
| M8 | `ALLOWED_TRANSITIONS` dan `pending → confirmed` olib tashlandi | `…match_the_diagram_exactly`, `…are_rejected` |
| M9 | `restored` tekshiruvi `autoclose` dan **keyinga** ko'chirildi | `test_restored_rule_is_immediate` |
| M10 | `create_outage(status="confirmed")` | `test_initial_edge_names_the_creation_status` |
| M11 | `app/bot/reply.py:KIND_RESTORED = "restored_v2"` | `test_restored_kind_comes_from_the_document` |

Har biri aynan mo'ljallangan testni yiqitdi; hujjat va kod har mutatsiyadan
keyin nusxadan tiklandi (`git status` toza, faqat yangi test fayli).

## 6. Qarorlar

- **Parsing sintaksis bo'yicha, so'z bo'yicha emas** (53-sessiyaning
  sabog'i): o'tishlar `-->` regexi bilan topiladi, statuslar `OutageStatus`
  qiymatlari bilan solishtiriladi, sonlar `\d+` bilan olinadi. Yagona
  o'zbekcha kalit — `soat` va `daq` (`test_two_hours…` da), ular hujjatning
  o'lchov birligi.
- **`SPEC_EDGES = 7` aynan.** Diagrammada 7 ta haqiqiy o'tish, 1 ta
  boshlanish, 3 ta yakun. Birinchi urinishda 8 deb yozilgan edi va test
  darhol yiqildi — ya'ni «shakl» testi o'z vazifasini birinchi daqiqadanoq
  bajardi.
- **Docstring nusxasi qulflandi, o'chirilmadi.** Muqobil — `status.py` dagi
  diagrammani olib tashlash (yagona manba qoladi). Rad etildi: docstring
  moduli o'qiyotgan odam uchun yozilgan, hujjatga havola uni almashtirmaydi.
  Buning o'rniga nusxa **hujjat bilan tenglashtiriladi**.
- **Bo'shliq normallashtiriladi.** Docstringda o'qish uchun tekislangan
  bo'shliqlar bor (`pending  --> confirmed`), hujjatda yo'q — solishtirish
  `" ".join(label.split())` dan keyin.

## 7. Rad etilgan

- **`05` §3.1 (jitter)** — u ham ochiq, lekin uning artefakti bitta formula
  va `tests/test_geo_jitter.py` uni allaqachon xulq-atvor darajasida
  o'lchaydi; §4.4 ning bo'shlig'i kattaroq edi. Keyingi runga qoldi.
- **§4.2 ning butun parametrlar jadvalini bog'lash** (`eps`, `time_window`,
  `min_reporters`, `max_radius`) — alohida ish; bu yerda faqat
  `autoclose_after` olindi, chunki u §4.5 nasrida takrorlangan.
- **§4.3 («mustaqil xabar beruvchi»)** — `tests/test_clustering_independence.py`
  da; ikkinchi joyda tekshirish tuzatish joyini noaniq qilardi
  (41-sessiyaning sabog'i).
- **Kodni «yaxshilash»** — hech narsa o'zgartirilmadi, chunki defekt yo'q.

## 8. Keyingi qadam

1. `05` §3.1 (jitter) kontrakti — `05` tomonida qolgan yagona ochiq bo'lim.
2. `06` §11 (34-run qisman yopgan).
3. 👤 O'zgarmagan bloklar: `push.ps1` → serverda `git pull` → uchala servisni
   qayta yig'ish (SQL jurnali prodda **hali yoqiq**); CI ni `NullPool`
   tuzatishidan keyin qayta yurgizish.

# 58-sessiya — `06` §12 oltin ssenariylarining mazmuni

**Sana:** 2026-08-09
**Sessiya:** `local_c160560e-…`
**Epic:** E5/E5b (ko'ndalang) — kontrakt qatlami, 18-fayl
**Natija:** ✅ `06` §12 endi nomlar darajasida emas, **bajarilish** darajasida
qulflangan. Defekt topilmadi; sakkizta mutatsiya bilan tekshirildi.
**Sandbox:** ishladi — `pytest -m "not requires_db"` → **1375 passed, 1 skipped,
212 deselected**; `ruff check app tools tests alembic` → toza.

---

## 1. Nima uchun aynan §12

57-sessiya uchta ochiq joy qoldirgan edi: `06` §11 (34-run qisman yopgan),
`06` §12 (46-run **faqat nomlarni** bog'lagan) va `05` §3.1/§4.4–4.5.
§12 tanlandi, chunki uning bo'shlig'i eng aniq o'lchanadigan edi.

46-sessiyaning `test_golden_scenarios_contract.py` bitta savolga javob
beradi: *har bir ssenariy raqamiga biriktirilgan test funksiyasi mavjudmi?*
Ssenariyning **sonlari** esa o'sha testlarga qo'lda ko'chirilgan:

```python
def test_scenario_8_dense_area_five_reports_stay_pending():
    result = run(spread_line(5), a_local=180)   # 5 va 180 — literal
    assert result.required_score == 7           # 7 — literal
```

Hujjatda `5` → `6` bo'lsa: 46-ning kalit so'zi («Zich hududda») joyida,
funksiya nomi joyida, xulq-atvor testi esa **o'z** literalini tekshiradi.
Ikkala tomon ham yashil, hujjat va kod jimgina ajraladi.

## 2. Uchta jim yo'nalish

| Yo'nalish | Nima bo'lardi |
|---|---|
| Hujjatdagi son o'zgaradi | Ikkala mavjud test ham yashil qoladi |
| §12.7 ning `scale_capped = true` i **vakuum** bo'ladi | `raw_scale` o'zi `local` bo'lsa bayroq hech narsa haqida bo'lardi, test o'zgarmasdan o'tardi |
| §12.11 ning «**hech qachon**» i bitta nuqta bilan o'lchanadi | `test_scale.py`: `w=99`, bitta sifat manbasi. «Hech qachon» va «bu holatda» — boshqa kuchdagi da'volar |

## 3. Yechim — hujjat kirish ma'lumotining manbai

`tests/test_golden_scenarios_content.py` (19 ta yurish) har bir §12
qatoridan **sonni, kod nomini va kutilgan natijani** ajratib oladi va
o'sha qiymatlar bilan `evaluate`, `decide`, `evaluate_status`,
`confidence` ni yurgizadi.

| Ssenariy | Qatordan olinadi | Nima yurgiziladi |
|---|---|---|
| §12.7 | `18`, `confirmed`, `local`, `scale_capped` | `evaluate` + `decide`; «kam qamrov» = `guard.min_active_district - 1` (§5.4 ning ta'rifi) |
| §12.8 | `5`, `chegara 7`, `pending` | `N_req == 7` beradigan `A_local` **qidiriladi** (`06` §4.2 formulasi orqali) |
| §12.9 | `ikki`, `ikki`, `pending` | Eng og'ir ikki manba `06` §2 jadvalidan **og'irligi bo'yicha** tanlanadi |
| §12.10 | `confirmed` | `confirm_ready=True` bilan bitta xabardan `confirmed`; qatlam ajratilishi |
| §12.11 | `'unknown'`, `local` | 3 × 5 × 5 × 4 = **240** kombinatsiya |
| §12.12 | `45`, `confidence`, `resolved` | `confidence` pasayishi + so'nish oynasi (oldin/keyin) |
| §12.13 | `recluster.py`, `scale` | Asbob mavjudmi va `fingerprint` o'sha maydonni hashlaydimi (AST) |

**Vakuumga qarshi uchta qo'shimcha tasdiq** — ular ssenariyning *ma'nosini*
o'lchaydi, natijasini emas:

* `test_scenario_7_cap_is_not_vacuous` — to'siq bo'lmaganda masshtab `local`
  **emas** (aks holda `scale_capped` bayrog'i bo'sh);
* `test_scenario_8_the_threshold_is_the_only_thing_missing` — chegaraga
  yetgan **o'sha** xabarlar tasdiqlaydi (aks holda `pending` sababi
  tarqoqlik yoki odam soni bo'lishi mumkin edi);
* `test_scenario_8_density_is_what_makes_it_insufficient` — siyrak hududda
  o'sha 5 ta xabar yetarli (ya'ni «zich» so'zi ishlayapti).

## 4. Mutatsiya bilan tekshirish

Hech qanday defekt topilmagani uchun testlarning o'zi tekshirildi — har
biri vaqtincha buzildi va aynan bitta test yiqilishi kuzatildi:

| Mutatsiya | Yiqilgan test |
|---|---|
| Hujjat: §12.8 «5 ta xabar» → «8 ta» | `…dense_area_keeps_it_pending` |
| Hujjat: §12.12 «45 daqiqadan» → «90» | `…resolves_after_the_documented_silence` + `…sections_agree…` |
| Hujjat: yangi §12.14 qatori | `test_every_scenario_has_a_content_test` |
| `fingerprint` dan `r.scale` olib tashlandi | `…hashes_the_named_field` |
| `coverage_cap`: `active_users_30d` sharti | `…caps_the_scale` |
| `coverage_cap`: `unknown` district sharti | `…never_exceeds_local` |
| `assign`: `find_candidate(… layer=…)` | `…crowd_outage_is_never_touched` |
| `LOW_CONFIDENCE_AFTER_MIN` 45 → 30 | `…resolves_after_the_documented_silence` |

## 5. Yo'l-yo'lakay topilgani

**57-sessiyaning bitta qaydi noto'g'ri edi.** U «`45` esa **faqat** §8 da
yashaydi» deb yozgan; aslida `45` §12.12 da ham bor. Zarari amaliy: ikkala
qator alohida tahrir qilinadi, biri o'zgarib ikkinchisi qolsa hujjatning
**o'zi ichida** ziddiyat paydo bo'lardi va kod qaysi biriga ergashgani
noaniq bo'lib qolardi. Endi `test_the_two_sections_agree_on_the_silence_window`
ikkala bo'limni solishtiradi.

**§12.12 qatori §8 ning shartini tushirib qoldiradi.** §8 yopilish uchun
ikkita shartni talab qiladi (`confidence < 40` **va** 45 daqiqa sukut),
§12.12 esa faqat sukutni eslatadi. Kod §8 ga ergashadi — to'g'ri, lekin bu
§12 ni yolg'iz o'qigan odam uchun tuzoq. Hujjat qonun bo'lgani uchun agent
uni tahrir qilmadi: savol `PROGRESS.md` ning «Ochiq savollar» ida 👤 bilan.

## 6. Rad etilgan variantlar

- **46-sessiyaning faylini kengaytirish.** U ro'yxat/nom qatlami; mazmun
  qo'shilsa fayl ikkita savolga javob berardi va tuzatish joyi noaniq
  bo'lardi (41-sessiyaning sabog'i). Ikki fayl bir-birini almashtirmaydi:
  46 — «ssenariyning testi bormi», 58 — «ssenariy hujjat yozganidek
  bajariladimi».
- **`05` §9.3 dagi 1–6 ssenariylarni ham shu yerda yurgizish.** Ular
  klasterlash quvuriga tegadi (`assign`, `find_candidate`) — bazasiz
  bajarib bo'lmaydi, bazasiz qismi esa allaqachon
  `test_clustering_status.py` da xulq-atvor sifatida bor. §12 esa `06` ning
  arifmetikasi: toza funksiyalarda yashaydi va hujjatdan yurgizib bo'ladi.
- **§12.12 qatorini hujjatda to'ldirish.** Spetsifikatsiya — qonun
  (`CLAUDE.md` §2); yaxshiroq g'oya «Ochiq savollar» ga yoziladi.
- **`06` §11 ni yopish.** 34-run qisman qilgan, qolgani `distinct_users` va
  `spread` bilan bog'liq — keyingi run uchun.

## 7. Yangi/o'zgargan fayllar

| Fayl | Nima |
|---|---|
| `tests/test_golden_scenarios_content.py` | **yangi**, 17 funksiya / 19 ishga tushish |

Kodga tegilmadi — bu run hech narsani tuzatmadi, faqat o'lchadi.

## 8. Sandbox

56-sessiyaning `/tmp/sv56` muhiti va `/tmp/wg-libs/bin/ruff` (0.16.2)
o'rnida qoldi, qayta o'rnatish kerak bo'lmadi
(`PYTHONPATH=/tmp/sv56:. python3 -m pytest`). Ildiz disk yana 100%
(13 MB bo'sh). 👤 `cleanup-sessions.ps1` ni har run oldidan yurgizish
kerakligi kuchida qolmoqda.

## 9. Run oxirida — prod jurnali (odam ko'rsatdi)

Odam 2026-08-09 13:40 (UTC) jurnalini yubordi: `sqlalchemy.engine.Engine`
har 5 soniyada `BEGIN` / `SELECT … FOR UPDATE SKIP LOCKED` / `COMMIT` ni
parametrlari bilan yozmoqda. 56-run buni tuzatgan hisoblanardi.

Uchta tekshiruv sababni bir xil nuqtaga olib keldi:

| Tekshiruv | Natija | Nima anglatadi |
|---|---|---|
| `printenv DB_ECHO LOG_LEVEL` | `false`, `INFO` | Sozlama emas |
| `grep -c engine_floor /app/app/core/logging.py` | `0` | Ishlayotgan image da fiks **yo'q** |
| `git show HEAD:…/logging.py \| grep -c engine_floor` | `0` | Fiks **commit qilinmagan** |

`git status -sb` → `main...origin/main` (repo origin bilan teng),
`HEAD` = `c184648` (08-09 18:06, JOBS fiksi). Ya'ni image o'sha commitdan
yig'ilgan: `runner.py` ning `__main__` fiksi unda **bor** (shuning uchun
`process_outbox` jurnalda ko'rinadi — fon vazifalari ishlayapti),
`logging.py` fiksi esa **yo'q**, chunki u o'sha commitdan **keyin**
yozilgan.

👤 **Tartib muhim:** `.\push.ps1` → serverda `git pull` →
`docker compose build sveta-api sveta-bot sveta-jobs` → `up -d`. Faqat
qayta yig'ish yordam bermaydi: kod serverga hali yetib bormagan. Uchala
servis ham kerak — `setup_logging(..., db_echo=...)` uchta kirish
nuqtasida (`app/main.py`, `app/bot/__main__.py`, `app/jobs/runner.py`).

**Yo'l-yo'lakay ikkinchi noto'g'ri qayd tuzatildi.** «`.\push.ps1` — 55 run
push qilinmagan» — repo aslida origin bilan **teng**. Bu qator
`EpicProgress.md` §4 da «CI 56-runda birinchi marta yurdi» qatori bilan
yonma-yon turgan va ikkisi bir-birini inkor qilardi.

`docker logs sveta-migrate` da ikkita «Context impl» bloki va bitta ham
`Running upgrade` yo'q — bu xato emas: baza allaqachon head da, konteyner
ikki marta ishga tushgan.

## 10. Keyingi qadam

`06` da ochiq qolgani — **§11** ning 34-run qamramagan qismi. `05`
tomonida §3.1 (jitter, `blake2b(user_id|h3_cell)` determinizmi) va
§4.4/§4.5 (status mashinasi diagrammasi) hali o'z kontrakt fayliga ega
emas. Eng katta blok o'zgarmadi: **55 run push qilinmagan**, CI faqat bir
marta yurgan.

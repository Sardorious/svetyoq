# 82-sessiya — mahsulot yo'l xaritasi (`app/release/roadmap.py`)

**Sessiya:** `local_c151c77f` · **Sana:** 2026-08-10
**Natija:** ✅ REL — `01` §24 «Product Roadmap» birinchi marta kodda.
**2517 passed, 1 skipped** (`requires_db` bilan birga, 231), ruff yashil,
migratsiyasiz.

---

## 1. Nima uchun aynan shu ish

81-run uchta nomzod qoldirgan edi (p95 ni vitrinaga chiqarish, `01` §30
Glossary, `01` §24 Product Roadmap). Uchinchisi tanlandi, chunki u
nomzod emas edi — **uchta reyestrning to'xtash nuqtasi** edi:

* **70-run** (`01` §23): «Faza 0 natijalari qayerda qayd etiladi» —
  ochiq savol;
* **75-run** (`01` §26/§27): o'n sakkiz banddan **o'n to'rttasi**
  `SCHEDULED`, sabab bitta — Faza 0 natijasi repoda saqlanmaydi;
* **77-run** (`01` §25): beshta relizdan ikkitasining sharti
  `Gate.UNRECORDED`, sabab o'sha.

Ya'ni uchta modul bir xil bo'shliqqa **havola qiladi** va uning o'zi
hech qachon o'lchanmagan. `01` §24 — o'sha bo'shliqning manzili.

## 2. Asosiy topilma: gate yopilmagan, ortidagi mazmun esa qurilgan

§24 ning epigrafi loyihaning eng qat'iy rejalashtirish qoidasini beradi:

> **Phase 0 — единственный шлюз.** Бюджеты Phase 1–2 не утверждаются до
> прохождения критериев выхода Phase 0.

Gate yopilmagan va buni **hujjatning o'zi** aytadi: beshala chiqish
mezoni ham `- [ ]` — belgilanmagan katakcha. Repo tomondan ham hech
narsa qayd etilmaydi.

Gate ortida esa Phase 1 turibdi va uning **beshala** bo'lagi ham
qurilgan: mintaqa konfiguratsiyasi va spravochniklar (E19/E2), UZ-first
(`DEFAULT_LANGUAGE`), mahalla darajasidagi Coverage Index (E14, 32-run),
dislaymerli statistika vitrinasi (23-run) — ustiga mintaqa **prodda
jonli** (80-run: `activate`). Phase 2 ning uchdan biri ham qurilgan
(bildirishnoma radiusining mexanizmi, kalibrlanmagan qiymati bilan).

Bu tugallanmagan ish emas va reja buzilgani ham emas: bu **reja o'z
qoidasini bugungi holatga nisbatan yolg'on qilib qo'ygani**. Shuning
uchun `gate_holds` — hisobotning bosh xossasi
(`architecture.headline_holds` bilan bir xil rol).

## 3. `RECORDED` sinfi bo'sh — va bu bo'limning butun mazmuni

`Landing` o'qi Faza 0 bandining **natijasi** qayerga tushishini aytadi:

| Sinf | Bandlar |
|---|---|
| `RECORDED` | **hech biri** |
| `INSTRUMENTED` | `P0-3`, `P0-4`, `EX-1`, `EX-2`, `EX-3` |
| `UNRECORDED` | `P0-1`, `P0-2`, `P0-5`, `P0-6`, `EX-5` |
| `EXTERNAL` | `P0-7`, `EX-4` |

Sinf ataylab saqlanadi (81-run ning bo'sh `Trigger.UNMEASURED` i bilan
bir xil sabab): u 75-, 76- va 77-runlarni to'xtatgan bo'shliqni
**nomlaydi**.

⚠️ `INSTRUMENTED` `RECORDED` ga yaqin **emas**: repo javobni hisoblay
oladi, lekin uni saqlamaydi — javob har safar qaytadan olinadi va gate
ni yopa olmaydi.

## 4. Ikkinchi o'q: «Проверяемая гипотеза» uch qatorda yolg'on

Jadvalning uchinchi ustuni **shunday ataladi**, ya'ni har qator ochiq
savol deb da'vo qiladi. `Bearing` aynan shu da'voni o'lchaydi va uchta
qatorda u noto'g'ri:

* **`P0-1`** («Наличие официального слоя данных») — `ASSUMED`. `0003`
  migratsiyasi `official` manbasini `weight=0.0`,
  `is_authoritative=True` bilan seed qiladi, ya'ni undan kelgan
  **birinchi** xabar hodisani darhol `confirmed` qiladi (`06` §2.2).
  Gipoteza tekshirilmasdan qabul qilingan (73-run: `PRESUMED`).
  Yon tomoni: `01` §7 MVP ko'lamiga «Ручной разбор публикаций 1055
  (**если он существует**)» qatorini kiritadi — va uning yo'li ham yo'q
  (76-run, `DP-4`; test buni AST siz emas, `app/reports` va `app/api`
  bo'ylab qulflaydi).
* **`P0-3`** («языковой профиль») — `ASSUMED`.
  `i18n.DEFAULT_LANGUAGE = "uz"` modul konstantasi, `01` §7 uni `PG-S3`
  bilan MVP ga kiritadi.
* **`P0-5`** («полнота геокодера») — `FORECLOSED`. Mahsulot manzilni
  umuman geokodlamaydi (69-run), ya'ni vazifa **yiqila olmaydi**:
  natijasi qanday bo'lishidan qat'i nazar mahsulot o'zgarmaydi.
  ⚠️ Sozlamalar esa joyida (`geocoder_provider`, `GEOCODER_*`) va
  ularni **hech kim o'qimaydi** — testda bu `ast.Attribute` bo'yicha
  o'lchanadi, matn bo'yicha emas (reyestrlarning izohi nomni so'zma-so'z
  keltiradi va o'quvchi emas).

## 5. Eng jim topilma: eng kuchli chiqish mezoni yarim

`EX-2` — «Полигоны махаллей **получены и валидны**». Ikkala yarmi bitta
katakda turibdi va repo faqat ikkinchisini bajaradi: `geo.quality`
oltita tekshiruv beradi va `SQL_PROMOTE` faqat ulardan keyin yuradi,
lekin `tools/import_boundaries.py` da `mahalla` so'zi **bir marta ham**
uchramaydi. Ya'ni bandni «bajarilgan» deb belgilash birinchi yarmini
ko'rinmas qiladi — va tekshiruvlar `districts` ustida yuriladi, ya'ni
bo'sh to'plam ustida ham «o'tgan» ko'rinadi (77-run, `RP-1`).

`EX-3` esa beshtadan **yagona** band bo'lib, u to'liq mahsulotning
ichida yotadi: «вердикт возникает» — `confirmation.required_score` va
`scale.raw_scale` ning qarori, asbob ham tayyor (`tools/simulate.py`,
`recluster.py --sweep`, 64-run). Yetmayotgani — ma'lumot (E10).

## 6. Teskari yo'nalish: fazalar nomlamaydigan uchta qurilgan sirt

* **`AH-1`** ommaviy API va OpenAPI (E15). Eng yaqin ibora — Phase 3
  ning «Open Data» si, ya'ni reja bo'yicha ochiq ma'lumot **ikkita
  yopilmagan gate ortida**.
* **`AH-2`** admin-panel, moderatsiya va audit (E8). §24 birorta fazada
  nomlamaydi, `03` ning `Q-2` qarori esa uni ommaviy xaritadan **oldin**
  qo'yadi.
* **`AH-3`** H3 issiqlik xaritasi (E16). «Плотность» Phase 2 ning
  sarlavhasida turibdi, mazmuni esa zichlikni ko'rsatadigan sirtni
  sanamaydi.

⚠️ `AH-1` va `AH-2` ni 77-run `01` §25 da ham topgan edi — ya'ni `01`
ning **ikkala** rejalashtirish bo'limi ham ularni tushirib qoldiradi.
Test bu ustma-tushishni qulflaydi (`plan.UNPLANNED` bilan kesishma).

## 7. Uchta eski tripwire ishladi va uchalasi ham haq edi

1. `test_geocoder_has_no_call_site` (69/73/76-run) — yangi reyestr
   geokoderni izohda nomlaydi → ro'yxatga oltinchi fayl.
2. `test_the_product_still_does_not_geocode` (69-run) — o'sha sabab.
3. ⚠️ `test_nothing_in_the_repo_records_a_phase_zero_result` (77-run) —
   **eng muhimi**. Skaner `P0-\d` satrini qidiradi, yangi reyestr esa
   yettala vazifani nom bilan sanaydi, ya'ni u «natija saqlanadigan
   joy» deb o'qildi. Bu 57-run ning tuzog'i bo'lardi: reyestrni yozish
   tripwire ni **jimgina o'chirib qo'yardi**. Shuning uchun istisno
   qo'shildi va da'vo **kuchaytirildi** — fayl ro'yxatdan chiqarildi,
   o'rniga `roadmap.evaluate().recorded == ()` talab qilinadi, ya'ni
   yangi reyestrning **o'z hukmi** eski tripwire ning o'rnini bosadi.

## 8. Fayllar

| Fayl | Nima |
|---|---|
| `app/release/roadmap.py` | **yangi** — `TASKS` (7), `CRITERIA` (5), `PHASES` (3), `AHEAD` (3); `Landing` × `Bearing`, `Delivery`; `gate_holds`, `accurate` |
| `tests/test_roadmap_contract.py` | **yangi**, 45 test — yetti qatlam |
| `app/admin/registries.py` | 14-qator: `roadmap` (`SELF_CONTAINED`, endpointsiz) |
| `app/core/i18n/locales/{uz,ru}.json` | `registry.roadmap` |
| `tests/test_integrations_contract.py` | geokoder ro'yxatiga oltinchi fayl |
| `tests/test_logging_monitoring_contract.py` | o'sha ro'yxat, ikkinchi nusxasi |
| `tests/test_release_plan_contract.py` | `P0-*` tripwire i: istisno + kuchaytirilgan da'vo |

## 9. Mutatsiya bilan tekshirish

18 mutatsiya, **1 survivor topildi va tuzatildi**: `PREJUDGED` ni
bo'shatish hech narsani yiqitmasdi, chunki `accurate` bugun birinchi
shartning o'zidan ham `False` chiqardi. Uchta yangi test qo'shildi —
har bir shartning **mustaqilligi** alohida o'lchanadi
(`test_prejudged_rows_alone_make_the_section_inaccurate`,
`test_ahead_of_plan_alone_makes_the_section_inaccurate`,
`test_three_of_seven_hypotheses_were_settled_before_the_task`).

## 10. Sandbox

`$HOME` (`/sessions`) yana **100% to'la**, `/` da esa 434 MB. Yechim
81-runnikidan arzonroq chiqdi: **80-run ning `/tmp/venv80` i saqlanib
qolgan** (Python 3.12 + hamma bog'liqlik) va `/tmp/pg` dagi PostGIS
ham. Ya'ni `pip install` ham, `micromamba` ham kerak emas edi.

⚠️ `/tmp/pgdata81` **boshqa foydalanuvchiniki** (`nobody`) — o'qib
bo'lmaydi; yangi `initdb -D /tmp/pgdata82` kerak bo'ldi (~40 MB).
Server har `bash` chaqiruvi oxirida o'ladi, shuning uchun
`pg_ctl start` + `pytest` **bitta** chaqiruvda bo'lishi shart.

👤 **Odamga:** `cleanup-sessions.ps1` ni ishga tushirish kerak —
`/sessions` to'lgani ikkinchi run ketma-ket muammo tug'diryapti.

## 11. Keyingi qadam

Nomzodlar:

1. **`01` §30 «Glossary»** — atamalar ↔ kod nomlari. Ikkita qator
   bugun shubhali: «DBSCAN» (kod inkremental biriktirish ishlatadi) va
   «H3 … разрешение 8–9» (jitter r9, 60-run ning `174 m` ↔ `201 m`
   nomuvofiqligi shu yerda).
2. **`sveta_http_request_duration_seconds` ni vitrinaga chiqarish**
   (81-run) — bugun u faqat Prometheus matnida.
3. `01` §7 «Scope» ↔ kod — bugun `P0-1` orqali unga birinchi marta
   tegildi va MVP jadvalining bitta qatori yo'lsiz chiqdi.

👤 **Ochiq savollar (odam):** Faza 0 natijalari uchun repoda joy
ochiladimi (uchta reyestr shuni kutmoqda); `P0-5` va `GEOCODER_*`
hujjatda qoladimi; `01` §24 ga ommaviy API, moderatsiya va issiqlik
xaritasi qatorlari qo'shiladimi.

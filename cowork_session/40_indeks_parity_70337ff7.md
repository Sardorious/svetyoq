# 40-sessiya — indeks parity: `05` §2 ↔ modellar ↔ migratsiyalar

**Sana:** 2026-08-09
**Sessiya id:** `local_70337ff7-a84f-4689-8ee7-392f9332bb44`
**Epic:** E1 (ko'ndalang)
**Natija:** ✅ 34-rundan beri ochiq turgan nomzod tekshirildi — **drift yo'q**;
parity endi kontrakt testi bilan ushlab turiladi.
**INFRA:** ⚠️ Sandbox **o'n birinchi marta ketma-ket** yiqildi
(`useradd failed: No space left on device`, ikki urinish) — `ruff` ham,
`pytest` ham ishga tushmadi.

---

## 1. Run boshidagi holat

`cowork_session/INDEX.md` va `sveta/PROGRESS.md` o'qildi. 39-run qoldirgan
ikkita ko'rsatma:

1. Sandbox tiklanganda **birinchi ish — butun `pytest`**, yangi kod emas.
2. Ochiq nomzod: **`05` §2 DDL ↔ koddagi indekslar farqi** (34-rundan beri).
   Yopilgan nomzodlar: `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34),
   API `commit` (39).

Sandbox ikki urinishda ham yiqildi, ya'ni 1-band bajarilmadi va run
2-bandga o'tdi.

## 2. 39-running kodi — qo'lda audit

`tests/test_api_commit_contract.py` ning har bir tayanchi manba bilan
solishtirildi.

| Tayanch | Holat |
|---|---|
| `_route_methods` — `Attribute(value=Name(id=…endswith "router"))` | ✓ `app/api/v1/*.py` ning hammasida shu shakl |
| `_session_arg` — `DbSession` / `get_session` markeri | ✓ `app/api/deps.py:14` — `Annotated[AsyncSession, Depends(get_session)]` |
| `MIN_ROUTES = 15` (izohda «23 yo'l») | ✓ haqiqatan **23**: admin 9, health 2, geo 2, map 3, metrics 1, heatmap 1, regions 1, outages 1, stats 2, webhook 1 |
| `MIN_MUTATING_ROUTES = 4` | ✓ `reject_outage:191`, `merge_outage:202`, `block_user:236`, `set_trust:247` |
| `commit` eng yuqori darajada | ✓ to'rtalasida ham, `return` esa **keyingi qatorda** |
| o'qiydigan yo'llarda `commit` yo'q | ✓ `app/api/` da boshqa `commit` yo'q |
| `get_session()` `commit`/`rollback` qilmaydi | ✓ `app/db/session.py:95`, modulda yagona |

**`app/bot/webhook.py` alohida tekshirildi:** `telegram_webhook`
`build_router()` **ichida** e'lon qilingan `@router.post` — `ast.walk`
uni topadi (ya'ni 23 yo'lning biri), lekin sessiya parametri yo'q va
qoidaga to'g'ri ravishda tushmaydi. 39-sessiyaning sanog'i **aniq**
(38-runda sanoq xatosi bo'lgan edi — bu safar yo'q).

**Qirra, keyingi run uchun:** `MIN_MUTATING_ROUTES = 4` bugungi qiymatga
**aynan teng** — 38-running `MIN_MODULES_WITH_SCOPES = 7` i bilan bir xil
holat. Bu ataylab («skaner bo'shab qolmasin») va uni «noto'g'ri test» deb
o'qish kerak emas.

**Bloklovchi defekt topilmadi.**

## 3. Nomzod: `05` §2 DDL ↔ koddagi indekslar

Nomzod 34-rundan beri turardi va oltita run uni qayta yozib, hech qachon
ochmagan.

### 3.1 O'lchov

| Tomon | Soni |
|---|---|
| `05` §2 DDL (`CREATE INDEX`) | 11 |
| Modellar (`__table_args__` da `Index(...)`) | 18 |
| Migratsiyalar (`upgrade()` da `op.create_index`) | 18 |

**Uch tomon aynan mos.** Spetsifikatsiyaning o'n bittasi ikkala tomonda
ham bor; qolgan yettitasi sababi hujjatlangan qo'shimchalar:

| Indeks | Sabab | Migratsiya |
|---|---|---|
| `ix_reports_region_id_created_at` | `01` NFR-S-02 | `0008` |
| `ix_outages_region_id_started_at` | `01` NFR-S-02 + `05` §10 | `0008` |
| `ix_outages_region_id_confirmed_at` | `05` §10 `confirm_latency_by_region` | `0008` |
| `ix_notifications_region_id_status` | `05` §10 | `0007` |
| `ix_mahallas_district_id` | `01` NFR-S-02, birlashma orqali | `0009` |
| `ix_boundary_staging_geom` | `05` §5.1 staging | `0002` |
| `ix_territory_stats_territory_level` | `06` §9 | `0003` |

Qisman shartlar ikkala tomonda **bir xil matn** bilan yozilgan
(`valid_to IS NULL`, `status IN ('pending','confirmed')`, `is_active`,
`processed_at IS NULL`, `confirmed_at IS NOT NULL`), `DESC` ifodalari ham
(`text("created_at DESC")` ↔ `sa.text("created_at DESC")`). Migratsiya
zanjiri chiziqli (`0001`→`0009`, bitta ildiz, bitta bosh) va **barcha**
`op.drop_index` chaqiruvlari faqat `downgrade()` da.

> **Toza manfiy natija — nomzod yopildi, qayta ochilmasin.**

### 3.2 Nima uchun baribir test yozildi

Holatni **hech narsa ushlab turmasdi**, va uchala nosozlik ham xato
bermaydi — 33-, 34-, 36-, 39-sessiyalar sanagan sinf:

**(a) Modelda bor, migratsiyada yo'q.** Indeks **hech qayerda**
yaratilmaydi: `tests/conftest.py` sxemani `create_all` bilan qurmaydi
(fikstyuralarda umuman sxema yaratish yo'q), test bazasi ham CI da
`alembic upgrade head` dan keladi. So'rov to'g'ri javob beradi, faqat
sekinlashadi. `0008` va `0009` migratsiyalarining izohlari aynan shu
narxni yozgan: «indeks yetishmasligi **jimgina** yashaydi».

**(b) Migratsiyada bor, modelda yo'q.** Keyingi
`alembic revision --autogenerate` metadatada yo'q indeksga
`op.drop_index(...)` yozadi va odam buni «autogenerate shunday dedi» deb
qabul qiladi — ya'ni **ishlab turgan indeks o'chiriladi**. Yo'nalish
nazariy emas: `0007`, `0008`, `0009` qo'lda yozilgan.

**(c) `05` §2 da bor, kodda yo'q.** Spetsifikatsiya — qonun
(`CLAUDE.md` §2), lekin bugungacha uni indekslar bo'yicha hech kim
o'lchamagan.

Zarar bir mintaqada, bo'sh `mahallas` da va o'nlab qatorli test bazasida
umuman ko'rinmaydi — u ommaviy uzilishda, ya'ni sistema qurilgan **yagona**
holatda chiqadi.

### 3.3 Qilingani

* **`app/db/models.py` docstringi** — kontrakt shu yerda, chunki bu modul
  `target_metadata` ning yagona to'liq manbai, ya'ni uchala tomon aynan shu
  faylda uchrashadi.
* **`tests/test_schema_index_parity.py`** — yangi, 10 ta bazasiz test,
  `ast` skaneri.

### 3.4 Tuzilish qarorlari

* **Faqat `upgrade()` o'qiladi.** `downgrade()` ni ham hisoblash bu testni
  yozishning **eng oson xato usuli** bo'lardi: har bir migratsiya o'zi
  yaratgan indeksni o'sha faylda o'chiradi, ya'ni yakuniy to'plam **bo'sh**
  chiqardi va to'rtta qoida ham yolg'on yashil bo'lib turardi.
* **Yakuniy holat zanjir bo'yicha replay qilinadi**, `creates - drops`
  bilan emas: fayl nomi faqat kelishuv, Alembic esa `down_revision` ni
  bajaradi — va `0005` da o'chirilib `0008` da qayta yaratilgan indeks
  oddiy ayirmada yo'qolardi.
* **Zanjirning chiziqliligi alohida qulflangan.** Ikkita bosh —
  `alembic upgrade head` ning xatosi, lekin bu yerda undan ham yomoni:
  replay ikkinchi shoxni **umuman o'qimasdi** va parity qoidalari yolg'on
  yashil bo'lardi.
* **`ast`, matn qidiruvi emas, va farq bu yerda amaliy:** `Index\(` regexi
  `app/stats/` dagi uchta `CoverageIndex(` chaqiruvini ham topardi;
  daraxtda esa `Name.id` aynan `"Index"` bo'lishi shart.
* **Har bir indeks tasniflanadi** (`SPEC_INDEXES` yoki `BEYOND_SPEC`,
  ikkalasi ham qo'lda — 35-sessiyaning `test_the_subcommand_table_is_complete`
  naqshi): usiz fayl indekslar **soni** o'sganini ko'rardi, ularning
  **sababini** emas.
* **`SPEC_INDEXES` jadvalining o'zi ham fakt bilan o'lchanadi**
  (38-sessiyaning naqshi): `05` dagi `CREATE INDEX` satrlari soni jadval
  bilan teng bo'lishi shart. Nom jadvalda **qo'lda** yozilgan, chunki
  spetsifikatsiyada indekslar **nomsiz** — nomni avtomatik chiqarib
  bo'lmaydi, chiqarilganda esa nom o'zgarishi jimgina o'tib ketardi
  (→ «Ochiq savollar»).
* **`op.execute("CREATE INDEX …")` taqiqlanadi** — xom SQL skanerdan
  butunlay yashirinadi va parity qoidasi jimgina teshilardi. Taqiq emas,
  **ko'rinadigan qaror**: `CONCURRENTLY` kerak bo'lsa bu fayl ham qayta
  ko'riladi.
* **Jadvalga bog'lanmagan `Index(...)` ham yiqitadi** — modul darajasidagi
  e'lon metadataga tushishi ham, tushmasligi ham mumkin va skaner uni
  jadvalga bog'lay olmasdi.

### 3.5 Ataylab o'lchanmaydi

`UNIQUE` cheklovlari va `PRIMARY KEY` o'zining indeksini yaratadi
(`reports.tg_update_id`, `notifications (user_id, outage_id)`, …). Nomi
Postgres tomonidan cheklovdan yasaladi va ikkala tomonda ham **cheklov**
sifatida e'lon qilingan, ya'ni ajralib ketishi mumkin emas.

## 4. Fayllar

| Fayl | O'zgarish |
|---|---|
| `sveta/tests/test_schema_index_parity.py` | **yangi**, 10 ta bazasiz test |
| `sveta/app/db/models.py` | docstringga indeks parity kontrakti |
| `sveta/PROGRESS.md` | holat, run jurnali, «Ochiq savollar» |

Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**,
**xatti-harakat o'zgarishi ham yo'q** — faqat hujjat va kontrakt.

## 5. Keyingi run uchun

> ⚠️ **O'n birinchi marta** `ruff check` va `pytest -m "not requires_db"`
> ishga tushmadi. **Sandbox tiklanganda birinchi ish — butun `pytest`,
> yangi kod emas:** 36–40 runlarning ~55 ta testi hech qachon ishlamagan.
>
> **Yopilgan nomzodlar, qayta ochilmasin:** `05` §2 DDL indekslari (40),
> API `commit` (39), `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).
>
> **Qirra:** `MIN_MUTATING_ROUTES = 4` (39-run) va
> `MIN_MODULES_WITH_SCOPES = 7` (38-run) bugungi qiymatlarga aynan teng —
> ataylab.
>
> 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 11-run),
> `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

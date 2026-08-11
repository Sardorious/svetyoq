# 99-run — `01` §15 (NFR deltasi) + §31 (Appendix) reyestri

**Sessiya:** `local_44d60fa3` · 2026-08-11 · rejalashtirilgan
(`sveta-net-build`).

**Natija bir qatorda:** `app/release/nfr_appendix.py` +
`tests/test_nfr_appendix_contract.py` (49 test) yozildi, indeksga
ulandi; butun to'plam **2688 passed, 232 skipped**, `requires_db`
**231 passed**, `ruff` toza, `alembic` 0001→0010 toza, **11 mutatsiya
ushlandi**. **`01` ning bog'lanmagan bo'limi qolmadi.**

---

## 1. Nima uchun aynan §15 + §31

98-run keyingi qadam sifatida shu ikkisini qoldirgan edi — `01` ning
oxirgi bog'lanmagan bo'limlari. Bitta modulga birlashtirildi, chunki
§15 birinchi jumlasidan meros bilan boshlanadi («Наследуются NFR
ташкентского пакета»), §31 esa o'sha merosning manba ro'yxati:
«delta nimaning deltasi?» degan savol ikkiga bo'linmasligi kerak.

## 2. Asosiy topilmalar

1. **§31 — «yo'q hujjat» sinfining ildiz reyestri.** 86-run
   `17_OpenAPI.yaml` ni (§16 orqali), 87-run
   `03_Functional_Requirements.md` ni (§8 orqali), 98-run dizayn-tizim
   hujjatini (`UX-S7` orqali) — har biri bittadan topgan edi. §31 esa
   o'nta meros hujjatini nomma-nom sanaydi va **o'ntasidan noli**
   repoda. Endi sinf darchama-darcha emas, ro'yxat bo'ylab o'lchanadi
   (`test_none_of_inherited_docs_exist`).
2. **Olti prefiks to'qnashuvi.** 87-run bittasini ko'rgan (`03_`).
   Ro'yxat bo'ylab qaralganda `01_`–`06_` prefikslarining **har biri**
   repoda boshqa hujjat bilan band — havola bajarilgandek ko'rinadi.
   To'qnashuvlar e'londan emas, katalogdan **hisoblanadi**
   (`test_homonyms_computed_from_filesystem`).
3. **Olti meros zamechaniedan uchtasining kodda izi yo'q**
   (`C-05` baholar, `C-06` personalar, `C-10` ML). `C-10` paketda ham
   faqat §31 qatorida uchraydi va **tishlay olmaydi** — mahsulotda ML
   sirti yo'q. «В полном объёме» meros qilingan zamechanie hech
   narsani boshqarmaydi. Guvohi borlari: `C-09` (uch modul), `C-11`
   (glossary `MARK_SOURCE`), `C-04` (risks `RS-07`, roadmap).
4. **O'n standartdan kod guvohi borlari uchta** — WCAG 2.1 AA
   (`ux_requirements`), OpenAPI 3.1 (`api_requirements` + kontrakt),
   C4 Model (`architecture`). OWASP ASVS §20 da ishora qilinadi,
   `security.py` da esa nomi ham yo'q — 👤 savol.
5. **`NFR-S-07` ning mazmuni o'qib bo'lmaydigan joyda:** availability/
   latency maqsadlari `04_NFR.md` da — ro'yxatdagi to'rtinchi yo'q
   hujjat. Repo o'z tomonini bajaradi (latency gistogrammasi bor,
   mintaqaviy SLO yo'q — qator aynan shuni so'raydi), «umumiy
   qiymatlar» esa paketdan ko'rinmas. `NFR-S-03` ham shu sinf:
   «500 тыс.» `[BASELINE-TAS]` dan, repoda yuklama asbobi yo'q.
6. **§15 ning yaxshi tomoni:** yetti qatordan to'rttasi to'liq qurilgan
   va test bilan himoyalangan: `S-01` (E19: `pick_for_point`,
   `region_admin.py`, sintetik ikkinchi mintaqa testda), `S-02`
   (`0008` migratsiyasi docstringida aynan shu qatorni nomlaydi +
   indeks pariteti + API sirt qorovuli), `S-05` (versiyalash — §8
   `F-3` bilan bitta mexanizm), `S-06` (i18n ikki tomonlama kontrakt).
7. **Nusxalar bog'landi** (57/92-runlar sinfi): `S-05` ↔ §8 `F-3` ↔
   §16 ↔ §17 (bitta qoida to'rt joyda); `S-02` ↔ `05` §7.2;
   `S-06` ↔ `CLAUDE.md` ↔ `04` §6.

## 3. Modul qurilishi

`Delivered` (BUILT / EXTERNAL / UNMEASURED / UNREADABLE — §8 dagi
`SUBSTITUTED`/`FORKED` ataylab yo'q: bu bo'limning kasali almashtirish
emas, o'qib bo'lmaydigan tayanch) × `Enforcement` (TESTED / MANUAL /
NONE) × `Baseline` (LOCAL / INHERITED / MIXED). To'rt reyestr:
`NFRS` (7), `INHERITED_DOCS` (10, olti `local_homonym`), `REMARKS`
(6, `can_bite` bilan), `STANDARDS` (10). Beshta ichki qorovul
(`TESTED` test bindsiz bo'lmaydi, `EXTERNAL` ni test himoyalay
olmaydi, o'lchab bo'lmaydigan qator `gap` siz bo'lmaydi, uxlayotgan
zamechanieda bind bo'lmaydi, kod takrorlanmaydi) — har biri alohida
testlanadi.

Probe: `total=33` (7+10+6+10), `flagged=23` (3 qator + 10 hujjat +
3 zamechanie + 7 standart), `undeclared=0`.

## 4. Rad etilgan variantlar

- **Ikki alohida modul (§15 va §31):** meros savoli ikkiga bo'linardi
  — §15 epigrafi §31 siz o'lchanmaydi.
- **`DECLARED` enforcement sinfi:** «дефект» deb e'lon qilingan ikkala
  qator (`S-02`, `S-06`) amalda test bilan ushlanadi — bo'sh sinf
  kiritilmadi; `DEFECT_ROWS` konstantasi ikkalasini hujjat bilan ikki
  tomonlama qulflaydi.
- **BPMN ni guvohli deb sanash:** `ux_requirements` §12 ning
  diagrammalarini o'qiydi, lekin BPMN **sifatida** emas — nom kodda
  uchramaydi; nuance `Standard.note` da.

## 5. Yashil yurish

| Nima | Natija |
|---|---|
| Yangi fayl | `test_nfr_appendix_contract.py` — **49 passed** |
| Butun to'plam (4 partiya) | **2688 passed, 232 skipped** (98-run: 2639 — aynan +49) |
| `-m requires_db` | **231 passed** |
| `alembic upgrade head` | 0001→0010 toza |
| `ruff check app tools tests alembic` | toza |
| Mutatsiyalar | **11/11 ushlandi** (SPEC_ROWS, homonym, mentions, marker, bind, DEFECT_ROWS, enforcement, probe, inheritance_witnessed, can_bite, tartib) |

## 6. O'zgargan fayllar

**Yangi:** `sveta/app/release/nfr_appendix.py`,
`sveta/tests/test_nfr_appendix_contract.py`.

**O'zgargan:** `sveta/app/admin/registries.py` (`nfr_appendix` qatori +
`_probe_nfr_appendix`), `sveta/app/core/i18n/locales/{uz,ru}.json`
(`registry.nfr_appendix`), `sveta/PROGRESS.md`, `sveta/EpicProgress.md`.

Migratsiya yo'q, vaqtinchalik fayl yo'q, sir ko'chirilmadi, mahsulot
kodi tegilmadi.

## 7. 👤 Uchta yangi savol

`PROGRESS.md` «Ochiq savollar» da to'liq: (1) meros hujjatlari —
qo'shish / manzil ko'rsatish / qoldirish; (2) OWASP ASVS darajasi;
(3) `NFR-S-03` uchun load-test kerakmi.

## 8. Muhit retsepti (100-run o'qisin)

```bash
export TMPDIR=/tmp                      # MAJBURIY: /sessions 100% to'la
P=/tmp/mamba/envs/py311/bin/python      # 3.11.15
PGBIN=/tmp/mamba/envs/pg/bin

# /tmp/pgdata98 BOSHQA sandbox foydalanuvchisiniki — ishlatib bo'lmaydi.
# 99-run yangisini yaratdi (xuddi shu holat takrorlansa):
#   $PGBIN/initdb -D /tmp/pgdataNN -U sveta --auth=trust
#   psql -c "CREATE DATABASE sveta;" ; psql -d sveta -c "CREATE EXTENSION postgis;"
$PGBIN/pg_ctl -D /tmp/pgdata99 -l /tmp/pg.log \
  -o "-p 55499 -k /tmp -c listen_addresses=127.0.0.1" start; sleep 4
export DATABASE_URL="postgresql+asyncpg://sveta:sveta@127.0.0.1:55499/sveta"
$P -m pytest -m requires_db -q      # pg_ctl bilan BITTA chaqiruvda!
```

Butun to'plam to'rt partiyada: `$(ls tests/test_*.py | sed -n '1,35p')`
va h.k. (chaqiruv qopqog'i ~180 s).

## 9. Keyingi qadam (100-run)

1. 👤 Brauzer tekshiruvi hali kutmoqda (360 px, `MAP_TILE_URL` bo'sh,
   til almashtirish) — 94/95/96-run tuzatishlarini hech kim ko'rmagan.
2. `01` yopildi. Yangi nomzodlar: `02_Phase0_Validation_Plan` ning
   bog'lanadigan qismlari (P0 vazifalari allaqachon `roadmap.py` da —
   qolgani bormi?) yoki `BRD_Samarkand.md` ning bog'lanmagan bo'limlari.
3. 👤 `cleanup-sessions.ps1` — `/sessions` hali ham 100% to'la.

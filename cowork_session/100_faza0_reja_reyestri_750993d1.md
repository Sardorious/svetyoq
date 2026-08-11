# 100-run — `02` Faza 0 validatsiya rejasi reyestri (PH0)

**Sessiya:** `local_750993d1-c489-4579-8553-ffcad73a5b1e` · 2026-08-11
**Turi:** rejalashtirilgan `sveta-net-build` runi (odam yo'q)

## 1. Boshlanish nuqtasi

99-run `01` ni yopdi va 100-run uchun ikkita nomzod qoldirdi:
`02_Phase0_Validation_Plan_Samarqand.md` yoki `BRD_Samarkand.md`.
`02` tanlandi — u yaxlit bitta hujjat, ichki tuzilishi kontrakt
shakliga tayyor (gipotezalar reestri, metodlar, go/no-go matritsasi)
va `roadmap.py` (82-run, `01` §24) bilan §12 trassirovkasi orqali
tabiiy bog'lanadi. BRD keyingi nomzod bo'lib qoladi.

## 2. Nima qurildi

**Yangi:** `sveta/app/release/phase0_plan.py` (reyestr, `SPEC = "02
(Faza 0 rejasi)"`) va `sveta/tests/test_phase0_plan_contract.py`
(**54 test**).

Reyestr: 8 gipoteza (`Gate` × `Result` × `Posture`), 7 metod
(`serves`/`partial`, odam-kunlar), 6 qaror qatori (`Outcome`),
9 chiqish mezoni, 10 risk (`Likelihood` × `Impact`), 5 skoup qatori
(`tension` bilan), Ilova D (6 meros zamechanie + yopish rejasi).
Olti qorovul `__post_init__` da, har biri alohida testlanadi:
H↔M bijeksiyasi, falsifikatsiya (ikkala chegara), postura dalilsiz
bo'lmasligi, GO ≡ to'xtatuvchi to'plam, EXIT-1 ↔ `UNTESTED`
ziddiyati, kritik risk kamaytirishsiz qolmasligi.

Test to'rt manbadan o'lchaydi: hujjat (sanalarning uch nusxasi
bir-biriga solishtiriladi; §2 tasnifi mermaid **o'qlaridan**
hisoblanadi; H↔M bog'lanishi hujjatning ikkala tomonidan sanaladi;
§6 RACI `A` sanog'i; §7 yig'indisi; §8 jadval kataklari; Ilova D),
kod (`DEFAULT_LANGUAGE == "uz"`, `confirm.min_users == 3`,
`on_location`, migratsiyalar katalogi), boshqa reyestrlar
(`roadmap` — yettala `P0-*` qamrovi ikkala tomonlama, `risks` —
`RS-*`/`AS-S*`, `nfr_appendix` — `NFR-S-04`, `C-09`, REMARKS
to'plamining aynan tengligi) va fayl tizimi.

Indeks: `registries.py` ga `phase0_plan` qatori + `_probe_phase0_plan`
(`total=45`, `flagged=22`, `undeclared=0`), i18n kaliti
`registry.phase0_plan` UZ+RU.

## 3. Topilmalar

1. **`PH0-OS-01` ↔ repo — hujjatlararo ziddiyat.** Reja «har qanday
   kod yozish yoki migratsiya taqiqlanadi (BRD §22)» deydi; repo esa
   butun mahsulot, `04_Epic_Roadmap_Solo` qurishni buyuradi. Shu
   paytgacha hech qayerda qayd etilmagan edi. Reyestr `scope_tensions`
   da saqlaydi, `accurate=False`; 👤 savol.
2. **O'lchov erkin emas.** 8 gipotezadan 6 tasiga mahsulot allaqachon
   javob tanlagan: H-1 (intake quvuri), H-2 (bot yagona kirish),
   H-3 (`DEFAULT_LANGUAGE="uz"`), H-5 (mahalla sxemasi `0002`),
   H-7 (`confirm.min_users=3` — hujjatdagi «≥3» ning o'zi) — tasdiq
   tomonga; H-6 — rad tomonga (nuqta-kirish qurilgan, manzil qidiruvi
   yo'q; `P0-5` ning `FORECLOSED` i bilan bir dalil). Chinakam ochiq
   faqat H-4 (E18 kutadi) va H-8 (yuridik). `Posture` enum shu uchun
   kiritildi. `PH0-R-08` (tasdiqlash tarafkashligi) — hujjatning o'zi
   bu sinfni «eng jiddiy» deb ataydi.
3. **RACI: o'n qatordan oltitasi konventsiyani buzadi.** Kutilmagan
   topilma — test yozilayotganda birinchi yurgizish ko'rsatdi:
   «Chegaralarni tasdiqlash» da `A` **ikkita** (PO va Homiy),
   `M-1`–`M-5` da esa **umuman yo'q** (birinchi taxmin faqat dual-A
   edi; jadval o'zi to'liq sanab chiqilgach beshta `A` siz qator
   chiqdi). `DUAL_ACCOUNTABLE_ROWS` + `UNACCOUNTABLE_ROWS` yopiq
   ro'yxatlar, test qayta sanaydi; 👤 savol.
4. **Ilova D ↔ `nfr_appendix.REMARKS` aynan teng** — ikki modul bitta
   yo'q hujjatning (`21_Critical_Review.md`) bitta ro'yxatini ko'radi;
   tenglik to'plam sifatida testda. Faza 0 ikkitasini yopishga urinadi:
   C-06 (M-3), C-09 (M-7) — parse qilinadi.

## 4. Kutilgan driftlar (uchta tripwire yiqildi)

1. `test_nfr_appendix_contract::test_unwitnessed_remarks_absent_from_code`
   — yangi reyestr `C-05`/`C-06`/`C-10` ni nomlaydi. `EXCLUDED` ga
   ikki fayl qo'shildi (77/82/85-runlar qoidasi: reyestr nusxa, guvoh
   emas).
2. `test_risk_register_contract::test_phase0_results_have_no_home_in_the_repository`
   — `phase0*` nomlari `app/` da paydo bo'ldi. 82-run naqshi:
   yopiq nom ro'yxati (`plan_registry_names`) + reyestrning **o'z
   hukmi** talab qilinadi (`untested == hypotheses`,
   `unchecked_exits == exit_criteria`) — natija birinchi qayd etilgan
   kuni test yana yiqiladi, tripwire semantikasi saqlanadi.
3. `test_release_plan_contract::test_nothing_in_the_repo_records_a_phase_zero_result`
   — beshinchi istisno (`quoting` ga `phase0_plan.py`), o'sha sabab:
   `P0-*` satrlari hujjat iqtibosi, natija emas; o'z hukmi qo'shildi.

**Ataylab qilinmagan drift:** modul faqat «geokoder» (k bilan)
yozuvini ishlatadi, inglizcha yozuvni emas — shuning uchun `01`
§18/§22 skanerlarining sakkiz fayllik yopiq ro'yxatlariga tegilmadi;
buni testning o'zi ham o'lchaydi (`test_h6_rejection_branch_is_built`
modul matnini regex bilan tekshiradi).

## 5. Yashil yurish

| Nima | Natija |
|---|---|
| Yangi fayl | `test_phase0_plan_contract.py` — **54 passed** |
| Butun to'plam (4 partiya, DB bilan) | **2973 passed, 1 skipped** (99-run kesimida: 2742+232 → aynan +54) |
| `-m requires_db` | **231 passed** |
| `alembic upgrade head` | 0001→0010 toza |
| `ruff check app tools tests alembic` | toza |
| Mutatsiyalar | **12/12 ushlandi** (gate, metod tartibi, chegara, EXIT checked, dual-A, A-siz ro'yxat, risk ta'siri, Ilova D, jami odam-kun, postura dalilsiz, NO-GO tartibi, probe formulasi); har biridan keyin `md5sum -c` bilan tiklanish tasdiqlandi |

## 6. O'zgargan fayllar

**Yangi:** `sveta/app/release/phase0_plan.py`,
`sveta/tests/test_phase0_plan_contract.py`.

**O'zgargan:** `sveta/app/admin/registries.py` (import + probe +
qator), `sveta/app/core/i18n/locales/{uz,ru}.json`
(`registry.phase0_plan`), `sveta/tests/test_nfr_appendix_contract.py`
(`EXCLUDED` +2), `sveta/tests/test_risk_register_contract.py` va
`sveta/tests/test_release_plan_contract.py` (istisno + o'z hukmi),
`sveta/PROGRESS.md`, `sveta/EpicProgress.md`.

Migratsiya yo'q, vaqtinchalik fayl yo'q, sir ko'chirilmadi,
mahsulot kodi tegilmadi.

## 7. 👤 Uchta savol — HAMMASI YOPILDI (o'sha kuni, odam bilan jonli)

Run tugagach odam chatga qaytdi va uchala savolga javob berdi:

1. **Moliyaviy tomon loyihani BLOKLAMAYDI** (umumiy qoida): BRD §22
   taqig'i, `PH0-EXIT-8`, `C-04`, `RS-07` bloklamaydigan deb o'qiladi;
   `04` haq, loyihani tugatish ustuvor. `CLAUDE.md` §2 ga, xotiraga va
   `PROGRESS.md` ga yozildi; `phase0_plan` OS-01 izohiga qaror kiritildi
   (ziddiyat hujjat darajasida qayd etilaveradi, `accurate=False`).
2. **RACI — «Homiy + BA»:** chegaralarni tasdiqlashda yakka `A` Homiy,
   `M-1`–`M-5` da BA/Tadqiqotchi `A/R` (M-5 da bajaruvchi
   geo-mutaxassis qoladi). `02` §6 «Tahrir (2026-08-11, 👤 qaror)»
   belgisi bilan tuzatildi; `DUAL_ACCOUNTABLE_ROWS` va
   `UNACCOUNTABLE_ROWS` bo'shatildi; test endi har qatorda aynan bitta
   javobgar borligini (`A/R` ni ham sanab) jadvaldan qayta hisoblaydi.
3. **Faza 0 kalendari amalda yuritilmaydi** — majburiyat emas, hujjat
   qatlami; sanalar tahrirlanmadi, `WINDOW_OPENED = False` turaveradi,
   o'lchovlar imkon bo'lganda o'tkaziladi.

Qarorlardan keyin: `test_phase0_plan_contract.py` 54/54, `ruff` toza.

## 8. Muhit retsepti (101-run o'qisin)

`/tmp` bu safar **bo'sh edi** (yangi sandbox) — hammasi noldan,
`EpicProgress.md` §6 retsepti ishladi:

```bash
export TMPDIR=/tmp HOME=/tmp/home CONDA_PKGS_DIRS=/tmp/pkgs \
       MAMBA_ROOT_PREFIX=/tmp/mamba XDG_CACHE_HOME=/tmp/cache
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba  # /tmp da
/tmp/bin/micromamba create -y -p /tmp/mamba/envs/py311 -c conda-forge python=3.11
/tmp/mamba/envs/py311/bin/python -m pip install -e ".[dev]"   # ~5 daq, timeout bo'lsa qayta
/tmp/bin/micromamba create -y -p /tmp/mamba/envs/pg -c conda-forge postgresql postgis
PGBIN=/tmp/mamba/envs/pg/bin
$PGBIN/initdb -D /tmp/pgdata100 -U sveta --auth=trust
$PGBIN/pg_ctl -D /tmp/pgdata100 -l /tmp/pg.log \
  -o "-p 55500 -k /tmp -c listen_addresses=127.0.0.1" start; sleep 3
$PGBIN/psql -h /tmp -p 55500 -U sveta -d postgres -c "CREATE DATABASE sveta;"
$PGBIN/psql -h /tmp -p 55500 -U sveta -d sveta -c "CREATE EXTENSION postgis;"
export DATABASE_URL="postgresql+asyncpg://sveta:sveta@127.0.0.1:55500/sveta"
# pg_ctl start va pytest — BITTA bash chaqiruvida (--die-with-parent)
```

To'plam to'rt partiyada (`sed -n '1,35p' / '36,70p' / '71,105p' /
'106,200p'`), chaqiruv qopqog'i ~175 s. `/sessions` hali ham 100%
to'la — 👤 `cleanup-sessions.ps1`.

## 9. Keyingi qadam (101-run)

1. 👤 Brauzer tekshiruvi hali kutmoqda (360 px, `MAP_TILE_URL` bo'sh,
   til almashtirish) — 94/95/96-run tuzatishlarini hech kim ko'rmagan.
2. Nomzod: `BRD_Samarkand.md` ning bog'lanmagan bo'limlari (73-run
   BR-005/BR-024 ni ko'rgan, butun hujjat reyestrsiz) — endi `02`
   naqshi tayyor; yoki 👤 savollar javobiga qarab ish.
3. 👤 Uchta yangi savol (§7).

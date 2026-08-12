# 104 — BRD §18–§19: interfeys reyestri (integratsiyalar + rollar)

**Sessiya:** `local_10af30da` (rejalashtirilgan `sveta-net-build` runi)
**Sana:** 2026-08-11
**Epic/Blok:** REL/BRD (BIFC) — paketning oltinchi hujjat bo'limi kodda

## Nima qilindi

103 INDEX ko'rsatgan nomzoddan birinchisi tanlandi: **BRD §18–§19**
(ikkinchisi — §20–§23 — 105 ga qoldi).

1. **`app/release/business_interfaces.py`** — yangi reyestr,
   `business_environment` naqshida (frozen dataclass + StrEnum +
   `__post_init__` qorovullari + hisoblanadigan kesimlar):
   - §18 — 10 integratsiya qatori: `system`/`direction`/`status`
     hujjat bilan aynan; `Claim` sinfi `classify_status()` bilan
     katakdan **hisoblanadi** (katak matni heterogen: `ДАННЫЕ`,
     `ГИПОТЕЗА`, `BASELINE-TAS`, «Требуется», «Действует», «вне
     скоупа»); `Build` — LIVE/PROVISIONED/REJECTED/DEFERRED/AHEAD.
   - §19 — 8 rol qatori: `RoleBuild` —
     BUILT/PARTIAL/SUBSTITUTED/ABSENT; moderator fe'llari
     (`MODERATOR_VERBS` ↔ `MODERATOR_BUILT_VERBS`).
   - «Ограничения» xatboshisining uch bandi **qayta o'lchanmaydi** —
     `RESTRICTION_LOCKS` bilan `app.admin.security` ga qulflanadi
     (bir haqiqat ikki reyestrda ikki marta e'lon qilinmasin).
2. **`tests/test_business_interfaces_contract.py`** — **49 test**,
   to'rt manba: hujjat (ikkala jadval ustunma-ustun, «Ограничения»
   matndan, Overpass §18 da yo'qligi matndan), kod (3 rol / 10 ruxsat,
   confirm/split yo'qligi `Permission` va `service.py` dan, veb-akkaunt
   sirti yo'qligi, `FeatureCollection`), boshqa reyestrlar
   (`integrations.registry` egizaklari `Warrant` sinxron bilan,
   `security` uch bandi, `business_environment.BANNED_TECH`), barcha
   `binds` rezolvatsiyasi; 10 guard-test.
3. Indeksga ulandi: `registry.business_interfaces` UZ+RU;
   `total=18`, `flagged=12` (6 integratsiya `gap` bilan + 6 rol
   `BUILT` emas), `undeclared=1` (Overpass).

## Topilmalar (hammasi 👤 savol, kod tahrirlanmadi)

- 🔴 **Open Data API skoup ziddiyati:** §18 «Ph.3, вне скоупа» —
  repo esa qator sanagan hamma formatni qurib bo'lgan (E15 REST,
  CSV eksport, GeoJSON snapshot). `CON-02` ning teskari ishoralisi:
  qarz emas, «ortiqcha». `Build.AHEAD` sinfi shu uchun kiritildi.
- 🟡 **Kafka/Redis qatorlari `CON-05` ni yumshatadi:** §18 ularni
  `BASELINE-TAS` deb belgilaydi — hujjatning o'z tili bilan «Toshkent
  merosi bilim», talab emas. «§15 Toshkent platformasini tasvirlaydi»
  o'qishiga hujjat **ichidan** dalil. 103 savoliga javob emas, dalil.
- 🔴 **§19: 8 rol ↔ kodda 3.** Veb-akkaunt, operator, Super Admin —
  izi yo'q (`ABSENT`); kurator va analitik — rolsiz boshqa mexanizm
  (`SUBSTITUTED`: CLI asboblar / ochiq vitrina).
- 🔴 **Moderator §19 fe'llarining yarmisiz:** «подтверждение» yo'q
  (tasdiqlash faqat avtomatik, `05` §4.4 — ma'lum `03` §11 bandi
  bilan bir ildiz) va «разделение» (split) umuman yo'q.
- «Ограничения»: 2FA — `security.mfa` `ABSENT` (NFR-S-01 qarzi);
  `outage.read_exact_geo` — huquq yo'q, o'rnida kuchliroq taqiq
  (`SUBSTITUTED`); vazifalar ajratilishi — qurilish bo'yicha.

## Rad etilgan variantlar

- §18 jadvalini modulda parse qilish (`integrations.registry` uslubi)
  — rad: BRD jadvali boshqa hujjatda va test allaqachon ikki tomonlama
  qulflaydi; `business_environment` naqshi (e'lon + hujjat-testi)
  soddaroq va boshqa BRD reyestrlari bilan bir xil.
- Kafka/Redis ni `MOOT` deb belgilash — rad: ular «o'lik ehtiyoj» emas,
  **ataylab chiqarilgan** (ADR-05, o'rnini bosuvchilari bor) — alohida
  `REJECTED` sinfi, `BANNED_TECH` ⊂ qorovuli bilan.
- «Ограничения» uchun mustaqil o'lchov — rad: `security` reyestri
  allaqachon o'lchaydi; bu yerda faqat bog'lam (`RESTRICTION_LOCKS`).

## Texnik izlar

- Kutilgan drift: ikkita «geokoder yo'q» skaneri
  (`test_integrations_contract.py`, `test_logging_monitoring_contract.py`)
  yangi faylni ushladi — **o'ninchi** reyestr sifatida izoh bilan
  allowlistga.
- Mutatsiya: 12 dan **11 ushlandi, 1 survivor** —
  `RESTRICTION_LOCKS` dan juftlik o'chirilgani sezilmasdi;
  `test_restrictions_paragraph_names_all_three_locks` ro'yxatni to'liq
  qulflaydigan qilib kuchaytirildi, qayta yurgizishda ushlandi.
- Yakuniy yashil: **3151 passed, 1 skipped** (103: 3102 — aynan +49);
  `-m requires_db` **231 passed**; `alembic` 0001→0010 toza; `ruff`
  toza; 143 test fayli.

## Muhit (105 o'qisin)

`/tmp` tirik edi: `py311` va `pg` envlar tayyor, faqat yangi
`initdb -D /tmp/pgdata104`, port **55519** (103 retsepti aynan ishladi;
`pgdata102/102b/103` — `nobody:700`, yaroqsiz). `TMPDIR=/tmp` majburiy,
`/sessions` 100% to'la (👤 `cleanup-sessions.ps1` hali kutmoqda).
Har batch chaqiruvida `pg_ctl start` + `sleep 2` — server chaqiruv
oxirida o'ladi. To'plam 4 partiyada (1–35 / 36–70 / 71–105 / 106–143).

## Keyingi qadam (105)

1. Nomzod: **BRD §20–§23** (Reporting §20 — 6 hisobot + 4 dashboard +
   7 KPI; Success Metrics §21 ↔ `01` §4 `success.py` solishtirma;
   Acceptance §22 ↔ `01` §23 / `03` §6; Timeline §23). Undan keyin
   BRD da §24 (arxitektura ↔ `01` §29/ADR) va §25–§26 qoladi.
2. 👤 ikkita yangi savol (Open Data skoup; §19 rol modeli) —
   `PROGRESS.md` «Ochiq savollar» da.
3. 👤 brauzer tekshiruvi va serverda `deploy.sh` hali kutmoqda.

# 06. Xabar manbalari va avtomatik tasdiqlash logikasi

| | |
|---|---|
| **Qamrov** | Ko'p manbadan xabar qabul qilish, ishonch og'irliklari, adaptiv tasdiqlash chegaralari, hodisa masshtabi |
| **Almashtiradi** | `05_Technical_Design.md` §4.2–§4.3 (qat'iy `min_reporters = 3`) |
| **Sana** | 2026-08-06 |

---

## 1. Muammo: qat'iy chegara nima uchun ishlamaydi

`05` hujjatida tasdiqlash chegarasi qat'iy: 3 ta mustaqil xabar. Bu ikki tomondan xato:

| Hudud | 3 ta xabar nimani anglatadi |
|---|---|
| 800 kishilik mahalla, 12 ta faol foydalanuvchi | **Kuchli signal** — faol bazaning to'rtdan biri |
| 60 000 kishilik tuman, 900 ta faol foydalanuvchi | **Shovqin** — bitta ko'chadagi transformator ham, butun tuman avariyasi ham 3 ta xabar berishi mumkin |

Qat'iy chegara birinchi holatda **juda sekin**, ikkinchisida **juda ishonchsiz**.

Foydalanuvchi so'ragan `3–5 / 5–10 / 10>` diapazonlari to'g'ri intuitsiyani ifodalaydi, lekin ular **bitta chegara emas, balki uch pog'onali masshtab narvoni**. Quyida ular aholi soni va hudud kattaligiga bog'lab formallashtirilgan.

**Asosiy ajratish:**

| Savol | Nimaga bog'liq |
|---|---|
| **Bu haqiqiymi?** (tasdiqlash) | Hodisa iziga tushgan **faol foydalanuvchilar soni** (qamrov) |
| **Bu qanchalik katta?** (masshtab) | Hududning **aholisi va maydoni**, xabarlarning fazoviy tarqoqligi |

Bu ikki savol alohida hisoblanadi. Ularni bitta chegaraga qo'shish — `05` dagi xato edi.

---

## 2. Xabar manbalari va ishonch og'irliklari

Endi xabar faqat botdan kelmaydi.

```sql
CREATE TABLE report_sources (
  code        text PRIMARY KEY,
  weight      numeric(3,1) NOT NULL,
  is_authoritative boolean NOT NULL DEFAULT false,
  description text
);

INSERT INTO report_sources (code, weight, is_authoritative, description) VALUES
  ('bot',            1.0, false, 'Telegram-bot, oddiy foydalanuvchi'),
  ('bot_trusted',    1.5, false, 'trust_score >= 80, tarixi toza'),
  ('mahalla_active', 2.0, false, 'Tasdiqlangan mahalla aktivi'),
  ('moderator',      3.0, false, 'Moderator qo''lda kiritgan'),
  ('official',       0.0, true,  'Rasmiy kanal (1055) — alohida qoida'),
  ('operator_api',   0.0, true,  'Operator API (Ph.3)');
```

### 2.1 Og'irlikli hisob

Tasdiqlash endi xabarlar sonini emas, **og'irlikli ballni** hisoblaydi:

```
W = Σ (source.weight × user_factor × time_factor)
```

| Ko'paytuvchi | Qiymat | Sabab |
|---|---|---|
| `user_factor` | `trust_score / 50`, [0.4 … 1.6] oralig'ida | Yangi va shubhali akkaunt kamroq vazn |
| `time_factor` | `1.0` (≤30 daq), `0.7` (30–60 daq), `0.4` (60–90 daq) | Eski xabar zaifroq dalil |

### 2.2 Rasmiy manba — alohida qoida

`is_authoritative = true` manbadan kelgan xabar **og'irlikli hisobga qo'shilmaydi**. U hodisani **darhol `confirmed`** qiladi, `W` qiymatidan qat'i nazar, va `layer = 'official'` qo'yadi.

Sabab: rasmiy e'lonni kraudsorsing bali bilan "ovoz berishga" qo'yish mantiqsiz. Lekin teskarisi ham to'g'ri emas — rasmiy manba **kraudsorsing hodisasini bekor qilmaydi**. Ikkalasi yonma-yon yashaydi va nomuvofiqlik qayd etiladi (bu analitik qiymat, PRD UC-5).

---

## 3. Hudud statistikasi

Adaptiv chegaralar uchun har bir hudud haqida ma'lumot kerak.

```sql
CREATE TABLE territory_stats (
  territory_id     uuid PRIMARY KEY,       -- districts yoki mahallas id
  territory_level  text NOT NULL,          -- 'district' | 'mahalla'
  population       integer,                -- NULL bo'lishi mumkin
  households       integer,                -- population / avg_household_size
  area_km2         numeric(8,2) NOT NULL,  -- ST_Area(geom::geography)/1e6
  populated_cells  integer NOT NULL,       -- aholi yashaydigan H3 r9 katakchalar
  active_users_30d integer NOT NULL DEFAULT 0,
  data_quality     text NOT NULL,          -- 'measured' | 'estimated' | 'unknown'
  updated_at       timestamptz NOT NULL DEFAULT now()
);
```

### 3.1 Ma'lumot qayerdan

| Maydon | Manba | Yo'q bo'lsa |
|---|---|---|
| `area_km2` | Poligondan hisoblanadi | Har doim mavjud |
| `populated_cells` | OSM binolari (`building=*`) → H3 r9 | Bino ma'lumoti yo'q joyda — barcha katakchalar |
| `population` | Ochiq statistika (tuman darajasi) | `NULL` → `data_quality = 'unknown'` |
| `households` | `population / avg_household_size` | `avg_household_size` — konfiguratsiya parametri `[TEKSHIRISH]` |
| `active_users_30d` | O'z ma'lumotimiz | Har doim mavjud |

**Mahalla darajasida aholi soni deyarli mavjud emas.** Shuning uchun proksi ishlatiladi:

```
households_estimated = populated_cells × avg_buildings_per_cell × avg_households_per_building
```

yoki soddaroq — tuman aholisini mahallalar orasida `populated_cells` proportsional taqsimlash. Bu **taxmin** va `data_quality = 'estimated'` bilan belgilanadi.

### 3.2 Ma'lumot sifati chegaralarga qanday ta'sir qiladi

| `data_quality` | Xatti-harakat |
|---|---|
| `measured` | To'liq adaptiv formula |
| `estimated` | Adaptiv formula, lekin masshtab da'vosi bir pog'ona pasaytiriladi |
| `unknown` | Faqat qamrovga asoslangan chegara (§4.2), masshtab da'vo qilinmaydi |

---

## 4. Tasdiqlash chegarasi

### 4.1 Denominator — hudud emas, hodisa izi

Eng muhim nuqta. Chegara **butun tumanning** faol foydalanuvchilariga bog'lanmaydi, chunki uzilish bitta ko'chani ham qamrashi mumkin. Denominator — **hodisa izi ichidagi** faol foydalanuvchilar:

```sql
-- A_local: hodisa radiusi + eps ichidagi 30 kunlik faol foydalanuvchilar
SELECT count(DISTINCT r.user_id)
FROM reports r
WHERE r.created_at > now() - interval '30 days'
  AND ST_DWithin(r.geom_public, :centroid, :radius_m + :eps);
```

### 4.2 Formula

```
N_req = clamp(3, ceil(0.5 × sqrt(A_local)), 8)
```

| `A_local` | `sqrt` | Hisob | `N_req` |
|---|---|---|---|
| 4 | 2.0 | 1.0 | **3** (pol) |
| 12 | 3.5 | 1.7 | **3** |
| 40 | 6.3 | 3.2 | **4** |
| 100 | 10.0 | 5.0 | **5** |
| 250 | 15.8 | 7.9 | **8** |
| 900 | 30.0 | 15.0 | **8** (shift) |

**Nima uchun kvadrat ildiz.** Chiziqli o'sish (masalan, faol bazaning 5%) zich hududlarda chegarani ko'tarib yuboradi va lokal uzilish hech qachon tasdiqlanmaydi. Kvadrat ildiz — sekin o'sish: qamrov 25 barobar oshganda chegara 5 barobar oshadi.

**Nima uchun 3 dan past emas.** Ikki xabar — bu tasodif yoki bitta uy. Uch — minimal mustaqil dalil. Bu qiymat qamrov qanchalik past bo'lishidan qat'i nazar pasaytirilmaydi.

**Nima uchun 8 dan yuqori emas.** Undan yuqori chegara tasdiqlashni juda sekinlashtiradi va mahsulotning 10 soniyalik va'dasini buzadi. Zich hududda ishonchni chegara emas, **masshtab narvoni** oshiradi (§5).

### 4.3 Tasdiqlash sharti

```
confirmed  ⟺  W ≥ N_req  ∧  distinct_users ≥ 3  ∧  spatial_spread_ok
```

Uchta shart birga:

| Shart | Nima uchun |
|---|---|
| `W ≥ N_req` | Og'irlikli dalil yetarli |
| `distinct_users ≥ 3` | **Og'irlik odam sonini almashtira olmaydi.** Bitta mahalla aktivi (w=2.0) + bitta moderator (w=3.0) = 5.0 ball, lekin bu ikki odam. Tasdiqlash uchun kamida uchta boshqa-boshqa odam kerak |
| `spatial_spread_ok` | Xabarlar orasidagi maksimal masofa ≥ 50 m (bitta uy emas) |

Ikkinchi shart suiiste'molga qarshi eng muhim himoya: og'irliklar tizimini "ikki ishonchli odam hamma narsani tasdiqlaydi" holatiga aylanishidan saqlaydi.

---

## 5. Masshtab narvoni (3–5 / 5–10 / 10>)

Tasdiqlangandan keyin ikkinchi savol: **hodisa qanchalik katta?** Bu foydalanuvchi so'ragan diapazonlar joylashadigan joy.

### 5.1 Pog'onalar

| Pog'ona | Ma'nosi | Xaritada |
|---|---|---|
| `local` | Bitta ko'cha / bir necha uy | Kichik nuqta |
| `mahalla` | Mahalla darajasidagi uzilish | Mahalla bo'yaladi |
| `district` | Tuman miqyosidagi ommaviy uzilish | Tuman bo'yaladi, ogohlantirish |

### 5.2 Adaptiv chegaralar

```
T_mahalla  = clamp(5,  ceil(0.35 × sqrt(H_mahalla)),  15)
T_district = clamp(10, ceil(0.35 × sqrt(H_district)), 30)
```

`H` — hududdagi xonadonlar soni. Misollar:

| Hudud | Aholi | `H` | Formula | Chegara |
|---|---|---|---|---|
| Kichik mahalla | 700 | 130 | 0.35 × 11.4 = 4.0 | **5** (pol) |
| O'rta mahalla | 2 500 | 460 | 0.35 × 21.4 = 7.5 | **8** |
| Katta mahalla | 6 000 | 1 100 | 0.35 × 33.2 = 11.6 | **12** |
| O'rta tuman | 45 000 | 8 200 | 0.35 × 90.6 = 31.7 | **30** (shift) |
| Katta tuman | 90 000 | 16 400 | 0.35 × 128 = 44.8 | **30** (shift) |

Kichik mahallada narvon aynan foydalanuvchi so'raganidek chiqadi: **3 → 5 → 10** atrofida. Katta tumanda esa chegaralar avtomatik ko'tariladi.

### 5.3 Fazoviy shart — sondan muhimroq

Faqat xabar soni yetarli emas. 12 ta xabar bitta ko'chadan kelsa — bu mahalla uzilishi emas, bu **bitta transformator**.

```
scale = local
if (W ≥ T_mahalla) ∧ (cells_with_reports ≥ 3) ∧ (cell_coverage_ratio ≥ 0.15):
    scale = mahalla
if (W ≥ T_district) ∧ (mahallas_affected ≥ 2 yoki cell_coverage_ratio ≥ 0.30):
    scale = district
```

`cell_coverage_ratio = cells_with_reports / populated_cells` — hududning qancha qismidan xabar kelgani.

**Ikki mezon — VA bog'lovchisi bilan.** Son ham, tarqoqlik ham talab qilinadi. Bu "bitta ko'chadan 30 ta xabar → butun tuman qorong'i" xatosini oldini oladi.

### 5.4 Qamrov to'sig'i — eng muhim cheklov

Masshtab da'vosi **qamrovdan oshib keta olmaydi**:

```
max_claimable_scale:
  A_district < 30       → 'local'      (tuman darajasida da'vo qilib bo'lmaydi)
  A_mahalla  < 10       → 'local'
  data_quality='unknown'→ 'local'
```

Ya'ni: tumanda atigi 20 ta faol foydalanuvchi bo'lsa, ulardan 15 tasi xabar bersa ham tizim **"tuman miqyosida uzilish" demaydi**. U aytadi: *"Tasdiqlangan uzilish. Masshtabi aniqlanmagan — bu hudud bo'yicha qamrov past."*

**Nima uchun bu shart qat'iy.** Kraudsorsing tizimining eng jiddiy xatosi — kam ma'lumotdan katta xulosa chiqarish. 15 ta xabar zich qamrovda "tuman avariyasi" bo'lishi mumkin, siyrak qamrovda esa u shunchaki "biz shu 15 kishini bilamiz" degani. Ikkalasini ajratmaslik — jurnalist tomonidan noto'g'ri sarlavha yozilishiga to'g'ridan-to'g'ri taklif.

---

## 6. `confidence` hisobi

`outages.confidence` (0–100) — foydalanuvchiga ko'rsatiladigan ishonch darajasi:

```
confidence = round(100 × min(1, W / N_req) × coverage_factor × freshness)

coverage_factor = clamp(0.5, sqrt(A_local / 20), 1.0)
freshness       = 1.0 (oxirgi xabar ≤15 daq), 0.85 (≤45 daq), 0.6 (undan eski)
```

| `confidence` | Interfeysda |
|---|---|
| 0–39 | «Tekshirilmoqda» (`pending`) |
| 40–69 | «Ehtimol, ommaviy uzilish» |
| 70–89 | «Tasdiqlangan uzilish» |
| 90–100 | «Tasdiqlangan · ko'p manba» |

`coverage_factor` ning pol qiymati 0.5 — ya'ni past qamrovda hodisa tasdiqlansa ham, `confidence` hech qachon 50% dan oshmaydi va foydalanuvchi buni ko'radi.

---

## 7. Ishlangan misollar

| # | Vaziyat | `A_local` | `W` | `N_req` | Natija |
|---|---|---|---|---|---|
| 1 | Kichik mahalla, 4 ta qo'shni xabar berdi | 15 | 4.0 | 3 | ✅ `confirmed`, `local`, conf ≈ 87 |
| 2 | Bitta odam 6 marta xabar berdi | 15 | 1.0 | 3 | ❌ `pending` (distinct_users = 1) |
| 3 | Mahalla aktivi + moderator | 15 | 5.0 | 3 | ❌ `pending` (distinct_users = 2) |
| 4 | Zich markaz, 5 ta xabar, bitta uydan | 180 | 5.0 | 7 | ❌ `pending` (spread < 50 m) |
| 5 | Zich markaz, 9 ta xabar, 4 ta katakcha | 180 | 9.0 | 7 | ✅ `confirmed`, `mahalla` |
| 6 | Rasmiy kanal e'loni | — | — | — | ✅ `confirmed`, `official`, darhol |
| 7 | 18 ta xabar, tumanda 22 faol user | 20 | 18.0 | 3 | ✅ `confirmed`, lekin `local` — qamrov to'sig'i |
| 8 | 35 ta xabar, 3 ta mahalla, tumanda 800 user | 400 | 35.0 | 8 | ✅ `confirmed`, `district` |

Misol 7 — logikaning eng muhim ishlashi: xabar ko'p, lekin qamrov past → masshtab da'vo qilinmaydi.

---

## 8. Qayta baholash va deeskalatsiya

Status va masshtab **bir marta emas**, doimiy qayta hisoblanadi (`evaluate_outages`, 60 s):

| Holat | Xatti-harakat |
|---|---|
| Yangi xabar keldi | `W`, `scale`, `confidence` qayta hisoblanadi |
| Xabarlar to'xtadi | `freshness` pasayadi → `confidence` pasayadi |
| `confidence < 40` va 45 daqiqa yangi xabar yo'q | `pending` → `resolved` (so'ndi) |
| Masshtab pasayishi | **Ruxsat etiladi**, lekin faqat `pending` da |

**Tasdiqlangan hodisaning masshtabi pasaytirilmaydi.** Sabab: foydalanuvchiga "tuman miqyosida uzilish" deb bildirishnoma yuborilgan bo'lsa, uni keyin "aslida bitta ko'cha edi" ga o'zgartirish — ishonchni yo'qotish. Xato bo'lsa, moderator qo'lda `rejected` qiladi va bu auditda qoladi.

---

## 9. Konfiguratsiya parametrlari

Barchasi bazada, mintaqa kesimida — koddagi konstanta emas.

```sql
CREATE TABLE region_config (
  region_id   uuid NOT NULL REFERENCES regions(id),
  key         text NOT NULL,
  value       jsonb NOT NULL,
  PRIMARY KEY (region_id, key)
);
```

| Kalit | Boshlang'ich | Maqomi |
|---|---|---|
| `confirm.min_users` | 3 | `BASELINE-TAS` |
| `confirm.coef` | 0.5 | `BAHO` |
| `confirm.floor` / `ceil` | 3 / 8 | `BAHO` |
| `scale.coef` | 0.35 | `BAHO` |
| `scale.mahalla_floor/ceil` | 5 / 15 | `BAHO` |
| `scale.district_floor/ceil` | 10 / 30 | `BAHO` |
| `scale.cell_ratio_mahalla` | 0.15 | `BAHO` |
| `scale.cell_ratio_district` | 0.30 | `BAHO` |
| `guard.min_active_district` | 30 | `BAHO` |
| `guard.min_active_mahalla` | 10 | `BAHO` |
| `avg_household_size` | 5.4 | `[TEKSHIRISH]` |
| `spread.min_distance_m` | 50 | `BAHO` |

**Hech bir qiymat empirik asosga ega emas.** Ular E11 da (yopiq yig'ish bosqichidan keyin) `recluster.py` orqali sozlanadi. Shuning uchun ular konfiguratsiyada — har sozlash uchun deploy qilish mumkin emas.

---

## 10. Sxema o'zgarishlari

```sql
ALTER TABLE reports ADD COLUMN source_code text NOT NULL DEFAULT 'bot'
  REFERENCES report_sources(code);
ALTER TABLE reports ADD COLUMN weight numeric(3,1);   -- yozish paytida qotiriladi

ALTER TABLE outages ADD COLUMN weighted_score  numeric(6,1) NOT NULL DEFAULT 0;
ALTER TABLE outages ADD COLUMN distinct_users  smallint     NOT NULL DEFAULT 0;
ALTER TABLE outages ADD COLUMN scale           text         NOT NULL DEFAULT 'local';
ALTER TABLE outages ADD COLUMN scale_capped    boolean      NOT NULL DEFAULT false;
ALTER TABLE outages ADD COLUMN cells_with_reports smallint  NOT NULL DEFAULT 0;
ALTER TABLE outages ADD COLUMN required_score  numeric(4,1);  -- qaror paytidagi N_req
```

**`weight` va `required_score` qotiriladi** (yozish/qaror paytidagi qiymat saqlanadi). Sabab: `trust_score` keyinchalik o'zgaradi, konfiguratsiya sozlanadi — lekin *"nima uchun bu hodisa o'sha paytda tasdiqlangan edi"* savoliga javob bera olish kerak. Qotirilmagan qiymat auditni imkonsiz qiladi.

`scale_capped = true` — masshtab qamrov to'sig'i tufayli cheklanganini bildiradi. Bu interfeysda dislaymer chiqarish uchun kerak.

---

## 11. Suiiste'mol ssenariylari

| Hujum | Himoya |
|---|---|
| Bitta odam ko'p xabar | `distinct_users` |
| Bitta uydan ko'p akkaunt | `spread.min_distance_m` = 50 m |
| Yangi akkauntlar to'dasi | `user_factor` (past `trust_score`), akkaunt yoshi ≥10 daq |
| Soxta geolokatsiya | Tezlik tekshiruvi: bir foydalanuvchi 10 daqiqada 5 km sakrasa — `trust_score` pasayadi |
| Aktiv statusini suiiste'mol | `mahalla_active` og'irligi 2.0 dan oshmaydi; `distinct_users` shartini chetlab o'tolmaydi |
| Masshtabni sun'iy ko'tarish | Fazoviy shart (`cells_with_reports`) + qamrov to'sig'i |

---

## 12. Qo'shiladigan testlar

`05` §9.3 dagi oltin ssenariylarga qo'shimcha:

7. Kam qamrovli hududda 18 ta xabar → `confirmed` + `local` + `scale_capped = true`.
8. Zich hududda 5 ta xabar → `pending` (chegara 7).
9. Ikki og'ir manba, ikki odam → `pending`.
10. Rasmiy manba → darhol `confirmed`, kraudsorsing hodisasi o'chirilmaydi.
11. `data_quality = 'unknown'` → masshtab hech qachon `local` dan oshmaydi.
12. Xabarlar to'xtaydi → `confidence` pasayadi, 45 daqiqadan keyin `resolved`.
13. Bir xil kirish `recluster.py` da bir xil `scale` beradi (determinizm).

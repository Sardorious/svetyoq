# 06 — E5b: tasdiqlash va masshtab logikasi (`06`)

| | |
|---|---|
| **Sessiya** | `local_61b5622e-d860-4e35-80b2-975fb764fa6e` |
| **Sana** | 2026-08-06, ~23:00–23:30 UTC |
| **Epic** | E5b — `06_Confirmation_Logic.md` to'liq |
| **Natija** | 🔄 kod yozildi, CI kutilmoqda; sandbox 4-marta yiqildi |

---

## 1. Run boshlanishi

Ko'rsatma tartibi bo'yicha o'qildi: `cowork_session/INDEX.md` → `sveta/PROGRESS.md`
→ `CLAUDE.md`.

`INDEX.md` dagi «Qayerda to'xtadik» aniq ko'rsatma berdi:

> Keyingi sessiyada birinchi ish — yana sandboxni tekshirish. Ishlasa: E2 + E5 ni
> lokal tozalash, keyin E5b. **Yana yiqilsa: statik reviewni takrorlamang** (u
> allaqachon qilingan), darhol odamga ayting.

Sandbox tekshirildi (ikki marta):

```
bash failed on resume, create, and re-resume.
resume: RPC error -1: ensure user: useradd failed: exit status 12:
useradd: cannot create directory /sessions/vibrant-hopeful-lovelace
```

Ketma-ket **to'rtinchi** run. Xato aynan o'sha — qayta urinish to'xtatildi.

**Qaror:** statik review takrorlanmadi. Ko'rsatma «kodni ko'r-ko'rona yozishda
davom etmang» degan edi — lekin u E2/E5 ning **allaqachon yozilgan** kodiga
tegishli edi. `sveta-net-build` ko'rsatmasining §5 esa aniq: «hech qachon to'xtab
qolma, keyingi bloklanmagan epicga o't». Shuning uchun bu run E5b ni yozdi:
`06` ning katta qismi toza (bazasiz) formulalar, ular sandboxsiz ham
to'liq testlanadigan qilib yozilishi mumkin.

---

## 2. Nima yozildi

### 2.1 Toza modullar (baza kerak emas)

| Fayl | Mazmuni |
|---|---|
| `app/clustering/formulas.py` | `clamp`, `adaptive_threshold`, `round_half_up` |
| `app/clustering/params.py` | `06` §9 parametrlari, `DEFAULTS`, `from_mapping` |
| `app/clustering/confirmation.py` | `time_factor`, `W`, `N_req`, tasdiqlash sharti, `confidence` |
| `app/clustering/scale.py` | masshtab narvoni, fazoviy shart, qamrov to'sig'i, deeskalatsiya |
| `app/reports/sources.py` | manba registri, `user_factor`, `freeze_weight` |

`adaptive_threshold` — bitta funksiya, chunki `06` §4.2 (`N_req`) va §5.2
(`T_mahalla`, `T_district`) formulalari bir xil shaklda: `clamp(floor,
ceil(coef × sqrt(x)), ceil)`. Ikki joyda qo'lda takrorlangan formula vaqt
o'tishi bilan ajralib ketardi.

### 2.2 Sxema

`0003_confirmation.py`: `report_sources` (seed `app.reports.sources.SOURCES`
dan), `territory_stats`, `region_config`; `reports.source_code` + `weight`;
`outages` ning oltita yangi ustuni.

### 2.3 Ulanish

- `app/geo/queries.py` — `load_region_config`, `load_territory_stats`
  (neytral tiplar: `app.geo` `app.clustering` ni import qilmaydi);
- `app/reports/queries.py` — `eligible_evidence`, `active_users_near`
  (`06` §4.1 `A_local`);
- `app/clustering/status.py` — `confirm_ready` va `confidence` **ixtiyoriy**
  maydonlar; berilmasa modul `05` §4.4 bo'yicha ishlaydi;
- `app/clustering/service.py` — `evaluate` endi `W`, `N_req`, `confidence`,
  `scale`, `scale_capped` ni hisoblaydi va yozadi.

### 2.4 i18n

`06` §6 bandlari va §5.1 pog'onalari UZ va RU kataloglariga qo'shildi
(`outage.confidence.*`, `outage.scale.*`). Qattiq kodlangan matn yo'q.

### 2.5 Testlar

`tests/test_confirmation.py` va `tests/test_scale.py` — `06` §7 dagi
**sakkizta ishlangan misol** va §12 dagi 8, 10, 11, 13-ssenariylar.
`tests/test_schema.py` `06` jadvallari va ustunlari bilan kengaytirildi.

---

## 3. Qabul qilingan qarorlar (spetsifikatsiya jim qolgan joylarda)

| # | Savol | Qaror | Sabab |
|---|---|---|---|
| 1 | `reports.weight` ga nima qotiriladi | `source.weight × user_factor` | `06` §10 ning o'z sababi: `trust_score` keyin o'zgaradi. Faqat manba og'irligini qotirish auditni baribir buzardi |
| 2 | `W` xabar bo'yichami, odam bo'yichami | odam bo'yicha, eng erta xabar vakil | `06` §7.2: bitta odam 6 marta → `W = 1.0`. Takroriy xabar `time_factor` ni yangilab `W` ni ko'tara olmaydi |
| 3 | 90 daqiqadan eski xabar `time_factor` i | `0.4` (oxirgi pog'ona davom etadi) | `0.0` `W` ni keskin nolga tushirardi; `06` bu diapazonni ta'riflamaydi |
| 4 | `cell_coverage_ratio` qaysi hududdan | har pog'ona o'z hududidan | `T_mahalla` `H_mahalla` ga, `T_district` `H_district` ga bog'langani bilan bir xil mantiq |
| 5 | Qamrov to'sig'i narvonmi | yo'q, so'zma-so'z `local` | `06` §5.4 uchala shartni ham `local` ga tushiradi. Odam qaroriga qo'yildi |
| 6 | Rasmiy hodisaning `confidence` i | `100` | Kraudsorsing formulasi ~0 berardi va interfeys tasdiqlangan hodisani «Tekshirilmoqda» deb ko'rsatardi |
| 7 | `05` §4.3 kirish filtrlari | saqlab qolindi | `06` faqat qat'iy `min_reporters = 3` chegarasini almashtiradi; §11 akkaunt yoshi shartini o'zi eslatadi |
| 8 | `reports.source` va `source_code` | ikkalasi ham qoldirildi | `06` §10 `ADD COLUMN` deydi, almashtirishni emas |

---

## 4. Rad etilgan variantlar

- **`user_factor` ni qaror paytida hisoblash** — `trust_score` o'zgargach eski
  hodisaning bali ham o'zgarardi, ya'ni «nima uchun o'shanda tasdiqlangan edi»
  savoliga javob yo'qolardi (`06` §10 aynan buni taqiqlaydi).
- **`W` ni mustaqil (>= 50 m) xabar beruvchilar ustida hisoblash** — `06` §4.3
  fazoviy tarqoqlikni **alohida** shart qilib beradi, filtr sifatida emas.
  Ikkalasini qo'shish shartni ikki marta qo'llagan bo'lardi.
- **`time_factor` ni `reports.weight` ga qotirish** — u qaror paytidagi yoshga
  bog'liq, yozish paytidagi emas.
- **`data_quality` ro'yxatini `app/geo/models.py` da ham e'lon qilish** —
  yagona manba `app.clustering.scale.DATA_QUALITIES`; ikki joydagi ro'yxat
  E5 da xuddi shu sababdan bittaga yig'ilgan edi.
- **`E501` va boshqa lint xatolarini yana qo'lda tekshirish** — 05-sessiyada
  qilingan; takrorlash yangi ma'lumot bermaydi. Uning o'rniga vaqt E5b ga
  sarflandi.

---

## 5. Ochiq qolgani

1. ⛔ **`cleanup-sessions.ps1`** — 4 run ketma-ket sandbox yiqildi. Bu skriptni
   faqat odam ishga tushira oladi (C diskdagi, sessiyaga ulanmagan papka).
2. **`territory_stats` bo'sh.** Jadval va o'qish yo'li tayyor, lekin uni
   to'ldiradigan asbob yo'q (`06` §3.1: OSM binolari → H3 r9 + ochiq
   statistika). Shu sababli hozir barcha hodisalar `local` bo'ladi. Bu E17/E11
   ishi va E5b ni bloklamaydi, lekin masshtab narvoni haqiqiy ma'lumotsiz
   ishlamaydi.
3. **`region_config` seed qilinmagan** — mintaqalar hali yo'q. Mintaqa
   yaratilganda `DEFAULTS` dan qatorlar yoziladigan joy kerak (E8 yoki
   `tools/`).
4. Yuqoridagi 3-jadvaldagi 1, 5, 6, 8-qarorlar odam tasdig'ini kutmoqda —
   ular `PROGRESS.md` ning «Ochiq savollar» ida ham bor.

---

## 6. Keyingi qadam

1. Odam `cleanup-sessions.ps1` ni ishga tushiradi;
2. `.\push.ps1` → CI **E2 + E5 + E5b ni birga** tekshiradi;
3. Qizil bo'lsa tuzatish; yashil bo'lsa E2, E5, E5b ✅ ga o'tadi;
4. Keyin: **E3 (bot)** — token bor, yoki **E6 (`recluster.py`)**.

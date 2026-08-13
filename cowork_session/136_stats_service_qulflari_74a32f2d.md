# 136-run — `stats/service.py`: 135 ning bashoratlari qulflandi

**Sana:** 2026-08-13 · **Sessiya:** `local_74a32f2d-cc71-47ef-84b1-3c00639f2378`
· **Epic:** E14 · **Rejim:** statik (sandbox ko'tarilmadi)

---

## 1. Sandbox — ketma-ket OLTINCHI run o'lik

`mcp__workspace__bash` ning ikkala urinishi ham aynan bir xil xato bilan
yiqildi:

```
ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.80383: No space left on device
```

Ya'ni «136 uchun tartib» ning uchala texnik bandi — (1) `pytest` +
`ruff`, (2) butun to'plam + `requires_db`, (3) `tools/_mut.py` bilan
**o'lchash** — bajarilishi mumkin emas edi. 131-rundan beri holat
o'zgarmadi: `TMPDIR=/dev/shm` yechimi ham yaramaydi, chunki unga yetib
borish uchun ham sandbox kerak.

👤 `cleanup-sessions.ps1` — ketma-ket **oltinchi** run bloklovchi.
`requires_db` ketma-ket **15-run** yurgizilmagan (oxirgisi 121-run).

## 2. Qaror: nima qilinadi va nima qilinmaydi

135 «to'rtinchi yurgizilmagan test **fayli** yozilmasin» deb qoldirgan
edi. Bu run shu chegarani buzmadi:

* **yangi fayl yaratilmadi** — o'zgargani mavjud `tests/test_stats_service.py`;
* **mahsulot kodi, migratsiya, konfiguratsiya tegilmadi**;
* qo'shilgan har tasdiq manbadagi **aniq qatorga** solishtirildi (133/134
  ning statik verifikatsiya usuli).

Sabab: 135 ning topilmalari **gipoteza** bo'lib qolsa, keyingi run ularni
qaytadan kashf qilishi kerak bo'lardi; qulflar esa sandbox tirilgan
zahoti bitta `pytest` chaqiruvi bilan tasdiqlanadi yoki rad etiladi.

## 3. Manba dalillari (o'lchov emas, o'qish)

| Da'vo | Dalil |
|---|---|
| Ikki sozlamaning qiymati teng | `config.py:156` `coverage_window_days: int = 30`; `config.py:174` `stats_default_period_days: int = 30` |
| Tasdiq refleksiv | `tests/test_stats_service.py:25` — `period.days == settings.stats_default_period_days` |
| Almashtirish nuqtasi | `service.py:205` — `begin = start or finish - timedelta(days=settings.stats_default_period_days)` |
| Kafolat faqat prozada | `service.py:307` docstring — «Qamrov oynasi so'ralgan davrga **bog'liq emas**» |
| `monkeypatch` naqshi ishlaydi | `config.py:45-50` — `model_config` da `frozen` ham, `validate_assignment` ham yo'q; repoda 15+ yashil namuna, `int` maydon uchun `test_daily_digest_db.py:201` |
| `floor_to` aware qaytaradi | `service.py:168-173` — `datetime.fromtimestamp(…, tz=timezone.utc)` |
| Mavjud tasdiqlar naive vaqtda ham o'tadi | `tick` o'sha funksiyadan olinadi (naive == naive); `18000 % 900 == 0` |
| `min()` alifbo tasodifi | `scale.py:47-49` — `"estimated" < "measured"` |
| `region_index` ning yaxlitlashi | `service.py:282` — `round(sum(…) / len(…))` |
| `"region_mean"` faqat bo'sh bo'lmagan tarmoqda | `service.py:295` ↔ `service.py:281` (`coverage.unknown()` → `no_territory_stats`) |

## 4. Qo'shilgan to'rtta qulf

1. **`test_default_period_reads_its_own_setting`** —
   `monkeypatch.setattr(settings, "stats_default_period_days", 14)`,
   `period.days == 14`, va `settings.coverage_window_days == 30` (qo'shni
   sozlama tegilmagani oshkora yoziladi). O'ladigan mutantlar: sozlamani
   qo'shnisiga almashtirish **va** `timedelta(days=30)` deb qotirib
   qo'yish (128 ning `h3_cells` sinfi).
   ⚙️ **Eski refleksiv tasdiq (`:25`) ataylab qoldirildi.** U sukut
   qiymatning o'zini emas, **sozlamaga bog'liqlikni** hujjatlaydi; yangi
   test undan qat'iy kuchli, ya'ni ikkalasi ziddiyatsiz. Absolyut `== 30`
   ga o'zgartirish rad etildi: 30 raqami spetsifikatsiyada emas,
   sozlamada yashaydi — uni testga qotirish odam sukut qiymatni
   o'zgartirgan kuni **soxta** yiqilish berardi.
2. **`tzinfo` tasdig'i** `test_quantum_makes_the_open_end_stable` ichida:
   `early.end.tzinfo == timezone.utc`. `is` emas `==` olindi — `tzinfo`
   obyektining aynanligi `fromtimestamp` ning ichki tafsiloti.
3. **`test_region_index_lowers_measured_to_estimated`** —
   `{measured, estimated}` aralashmasi: natija `estimated`, pog'ona
   `HIGH` bo'lib qoladi (sifat `unknown` emas, `cap` tegmaydi). Ikkinchi
   tasdiq muhim: usiz `min` ↔ `max` mutanti sifat maydonida ushlanardi,
   lekin `cap` tarmog'ining tegmagani o'lchanmasdi.
4. **`test_region_index_rounds_the_mean_and_averages_sufficiency`** —
   `[50, 51, 51]` (152/3 = 50.67 → **51**, kesish 50 berardi),
   `sufficiency` ning o'rtachasi `pytest.approx` bilan, va
   `limiting_factor == "region_mean"`.
   ⚙️ Fikstyura ataylab `.5` dan qochadi: `[50, 51]` (50.5) da Python ning
   bank yaxlitlashi 50 beradi va kesish bilan **farq qilmasdi**.

## 5. Nima qilinmadi va nega

* **`_index_for` / `_coverage_input`** — `tests/` da birorta murojaat
  yo'q (135 topgan). Ularni qoplash `test_stats_service.py` ga
  `geo_q.TerritoryStatsRow` va `cluster_params.Params` fikstyuralarini
  olib kirishni talab qiladi, ya'ni **yangi importlar va yangi fikstyura
  qatlami** — yurgizilmagan holda bu 133 ning riskini oshiradi. Keyingi
  runga (sandbox tirik bo'lganda) qoldirildi.
* **`resolve_period` ning chegaralari** (`begin >= finish`, `.days > max`,
  kasr kunning kesilishi, `max_days=` payloadi) — arzon, lekin ular
  **o'lchanadigan** gipoteza va uchinchi bandda `tools/_mut.py` bilan
  tekshiriladi; bugungi to'rttadan farqi shundaki, ular yiqilish riski
  emas, **qamrov** masalasi.
* **`int` ↔ `round`** `floor_to` da — to'plamda faqat butun soniyali
  moment bor; qulf `NOW` ga mikrosoniya qo'shishni talab qiladi va bu
  fayldagi boshqa testlarning `NOW` konstantasiga tegib ketardi.

## 6. Ochiq risk

⚠️⚠️ **Bu O'LCHOV EMAS.** To'rtala tasdiq ham manbaga solishtirildi,
lekin `pytest` yurmadi. Push dan oldingi majburiy navbat endi **uchta**
fayl:

```
pytest tests/test_stats_service.py tests/test_geo_sql_expressions.py \
       tests/test_obs_age_contract.py -q
ruff check tests/
```

Eng ehtimoliy yiqilish nuqtalari, ehtimollik tartibida:
`pytest.approx` ning `sufficiency` dagi ishlatilishi (float yig'indi
tartibi) → `monkeypatch.setattr` ning pydantic-settings dagi xulqi →
`tzinfo` ning `==` solishtiruvi.

Bashorat: **+4 test → 3372 passed, 232 skipped** (134 ning +29 bashorati
kuchida qolgan holda).

## 7. 137 uchun tartib

1. `pytest` (§6 dagi uchala fayl) + `ruff check tests/` — birinchi ish.
2. Butun to'plam + `requires_db`.
3. `tools/_mut.py` bilan **o'lchash**: tor nishon `tests/test_stats_service.py`,
   birinchi navbatda §5 da qoldirilgan `resolve_period` chegaralari va
   `floor_to` ning `int` ↔ `round` i.
4. `_index_for` / `_coverage_input` — fikstyura qatlami bilan.

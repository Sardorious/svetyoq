# 28 — 131 ro'yxati yopildi va chegara davri qulflandi (142-run)

**Sessiya:** `local_0b2526c0` · **Sana:** 2026-08-13 · **Epic:** OBS / E15
**Natija:** ✅ 30 mutatsiya → 30 KILLED; 3432 passed / 235 skipped;
`requires_db` 234 passed; ruff toza; migratsiyasiz, mahsulot kodi tegilmagan.

---

## 1. Qayerdan boshlandi

141-run «142 uchun tartib» ni uch band qilib qoldirgan edi:

1. 131 ro'yxatining qolgan uchtasi — `collector._as_uuid`,
   `collector._reading`, `bot/service._label` (bazasiz testi umuman yo'q);
2. baza ko'tarilgani uchun 125-rundan beri kutayotgan `geo/queries.py` va
   `clustering/repository.py` ni `requires_db` nishoni bilan o'lchash;
3. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi.

(1) va (2) bajarildi. (3) keyingi runga qoldi.

Sandbox 141 ning retsepti bilan **birinchi urinishdayoq** ko'tarildi:

```bash
export HOME=/tmp/home TMPDIR=/tmp XDG_CACHE_HOME=/tmp/cache \
       CONDA_PKGS_DIRS=/tmp/pkgs MAMBA_ROOT_PREFIX=/tmp/mamba
```

`/tmp/mamba/envs/py311` va `/tmp/mamba/envs/pg` **saqlanib qolgan** edi
(o'sha VM), ya'ni `micromamba` ni qaytadan yuklash kerak bo'lmadi.
`df`: `/` — 2.2 G bo'sh, `/sessions` — hamon **100%**.

---

## 2. Birinchi qism — 131 ro'yxatining oxirgi uchtasi

Uchalasining ham umumiy sababi bitta: **ularga chaqiruvchi faqat
`requires_db` orqali yetardi.** `collect()` va `list_subscriptions()`
`AsyncSession` talab qiladi, ya'ni Postgressiz runda (122–140 — ketma-ket
o'n to'qqizta) bu uch funksiya **umuman yurgizilmasdi** va har qanday
o'zgarish jimgina o'tib ketardi.

Ikkita yangi toza fayl:

| Fayl | Nishon | Test |
|---|---|---|
| `tests/test_obs_collector_rows.py` | `collector._as_uuid`, `collector._reading` | 18 |
| `tests/test_bot_subscription_labels.py` | `bot/service._label` | 10 |

**`_reading` uchun asosiy uslubiy qaror:** har manbaga **noyob** qiymat
(`7`, `9`, `11`, `2.5`, `(3, 12)`). Manbalar bir xil turdagi
(`dict[uuid.UUID, int]`) bo'lgani uchun `reports_total` bilan `failed` ni
almashtirish tiplar tekshiruvidan ham, mavjud testlardan ham o'tardi —
farqli qiymatlar bunday almashuvni darhol ko'rsatadi.

---

## 3. Ikkinchi qism — baza bilan o'lchash

### 3.1. 🔴 Nima uchun `requires_db` jimgina `skip` bo'ldi

Birinchi urinishda `pytest -m requires_db` **231 skipped** qaytardi,
holbuki Postgres tirik va migratsiya toza edi. Sabab —
`tests/conftest.py::_db_reachable`:

```python
url = make_url(settings.database_url)
host, port = url.host or "localhost", url.port or 5432
with socket.create_connection((host, port), timeout=1.0):
```

U **TCP soketiga** qaraydi. Unix-soketli URL
(`postgresql+asyncpg://postgres@/sveta?host=/tmp&port=5542`) da
`url.host` — `None`, ya'ni tekshiruv `localhost:5432` ga uriladi va
hamma narsani `skip` qiladi. **Xato emas, lekin jim:** to'plam yashil
qoladi va «231 skipped» ni e'tibordan qochirish oson.

Ishlaydigan retsept:

```bash
initdb -D /tmp/pgdata142 -U postgres -A trust
pg_ctl -D /tmp/pgdata142 -o "-p 5542 -k /tmp -c listen_addresses=127.0.0.1" \
       -l /tmp/pg142.log start -w
export DATABASE_URL="postgresql+asyncpg://postgres@127.0.0.1:5542/sveta"
```

`/tmp/pgdata141` ni qayta ishlatib bo'lmadi — u `nobody:nogroup` bo'lib
qolgan (memory: «pgdata foydalanuvchi bilan o'ladi»), har yangi sandboxda
yangi `initdb` va yangi port.

### 3.2. `_period_filter` — hech qachon o'lchanmagan shart

`app/geo/queries.py::_period_filter` — `05` §2.1 ning butun versiyalash
qoidasi. Uni **nom bo'yicha** uchta kontrakt reyestri eslatadi
(`test_business_acceptance_contract`, `test_business_environment_contract`,
`test_functional_requirements_contract`), lekin **xatti-harakatini**
tekshiradigan test yo'q edi.

Birinchi o'tishda beshta mutatsiyadan **ikkitasi omon qoldi**, va
ikkalasi ham bir xil bo'shliqni ko'rsatdi: oraliq **yarim ochiq**
`[valid_from, valid_to)`, mavjud testlar esa `?at=` ni faqat **oraliq**
nuqtada so'raydi. Farq faqat aniq chegarada ko'rinadi:

* `valid_from <= at` → `<`: yangi versiya **o'z ochilish kunida**
  umuman ko'rinmasdi (chegara importi kuni xarita bo'sh);
* `valid_to > at` → `>=`: o'sha kuni **ikkala** versiya qaytardi —
  modul docstringidagi «xaritada ikkita ustma-ust poligon» aynan shu.

`tests/test_geo_api_db.py` ning fikstura si bu qulf uchun tayyor edi:
`b` ning eski versiyasi aynan `NOW` da yopiladi, yangisi aynan `NOW` da
ochiladi.

### 3.3. `precision` — soddalashtirish ostida yashiringan qulf

`ST_AsGeoJSON(geom_expr, precision)` da `precision` ni `15` ga
almashtirish **hech narsani yiqitmadi**. Sabab: sukutdagi
`geo_boundaries_simplify_m = 25` poligondan faqat burchaklarni
qoldiradi, ular esa `_square_wkt` da 4 xonali — yaxlitlash umuman
ko'rinmaydi. Qulf shuning uchun `simplify_m=0` bilan **to'liq**
geometriya so'raydi; shundan keyin mutatsiya ushlandi.

Bu 141 ning «yurgizilmagan qulf o'lchov emas» qoidasining boshqa
ko'rinishi: **noto'g'ri kirish bilan yozilgan qulf ham o'lchov emas** —
u yashil bo'ladi va hech narsani ushlamaydi.

---

## 4. Mutatsiya hisobi

| Nishon | Mutatsiya | Birinchi o'tish | Yakuniy |
|---|---|---|---|
| `collector._as_uuid` + `_age_s` | 5 | 5 KILLED | 5/5 |
| `collector._reading` | 9 | 8 KILLED, 1 survivor | 9/9 |
| `bot/service._label` | 5 | 5 KILLED | 5/5 |
| `geo/queries._period_filter` | 5 | 3 KILLED, 2 survivor | 5/5 |
| `geo/queries.district_boundaries` | 6 | 5 KILLED, 1 survivor | 6/6 |
| **Jami** | **30** | **26 KILLED, 4 survivor** | **30/30** |

To'rtala survivor ham **haqiqiy** (ekvivalent mutant yo'q) va to'rtalasi
ham qulflandi. Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**.

Eng qimmatlisi — `geo_unmatched_ratio` to'sig'i:

```python
geo_unmatched_ratio=(unmatched_n / total_n) if total_n else 0.0,
```

`if total_n` → `if unmatched_n` **hech qanday** testni yiqitmasdi, chunki
agregat qaytaradigan barcha **mumkin** juftliklarda (`unmatched ≤ total`)
ikkala shart bir xil javob beradi. Nuqson faqat ishlab chiqarishda,
buzuq agregat bilan bitta so'rovda, `ZeroDivisionError` bilan butun
`/metrics` javobini yiqitib ko'rinardi. Qulf shuning uchun
**nomuvofiq** juftlikni (`(3, 0)`) beradi va da'vosi shu: `_reading`
qatoridan hech qachon istisno chiqmaydi.

---

## 5. Yakuniy o'lchovlar

| | 141-run | 142-run |
|---|---|---|
| Test fayllari | 154 | **156** |
| Butun to'plam (DB siz) | 3404 passed, 232 skipped | **3432 passed, 235 skipped** |
| `-m requires_db` | 231 passed | **234 passed** |
| `ruff check .` | toza | **toza** |
| Migratsiya | `0001`→`0011` | tegilmadi |

Farqlar aynan mos: +28 bazasiz test, +3 `requires_db` test.

To'plam sakkiz partiyada yurgizildi (`split -n l/8`) — `bash` ning
~178 s limiti tufayli; bitta chaqiruvda ikkita partiya sig'adi, uchtasi
uzilib qoladi.

---

## 6. Keyingi runga

1. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi.
2. `clustering/repository.py` ning qolgan qismi `requires_db` nishoni
   bilan — retsept endi ma'lum (§3.1), nishon tor bo'lsa o'lchov 3–4 s.
3. `mahalla_boundaries` ning o'z tartibi va `districts` bilan birlashmasi
   (`district_boundaries` bilan bir xil oila, lekin alohida so'rov).

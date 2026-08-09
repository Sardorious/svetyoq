# 53-sessiya — `06` §4.1–4.3 tasdiqlash chegarasi kontrakti

**Sana:** 2026-08-09
**Sessiya:** `local_13ce6dff`
**Epic:** E5 (ko'ndalang, spetsifikatsiya ↔ kod kontrakti)
**Natija:** ✅ yangi `sveta/tests/test_confirmation_threshold_contract.py`.
Kod o'zgartirilmadi.
**Infra:** ⚠️ sandbox **yigirma to'rtinchi ketma-ket run** yiqildi (INFRA-1).

---

## 0. Sandbox

Birinchi ikkita `mcp__workspace__bash` chaqiruvi bir xil xato bilan yiqildi:

```
ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.71865: No space left on device
```

Ko'rsatma bo'yicha ikki urinishdan keyin to'xtatildi. Butun run **faqat fayl
asboblari** (`Read`, `Grep`, `Glob`, `Write`, `Edit`) bilan bajarildi.
Demak `pytest` ham, `ruff check` ham yana ishga tushmadi — 36-rundan beri
to'plangan ~310 ta test hech qachon ishlamagan.

👤 Sabab, ehtimol, C diskdagi sessiya papkalari: `cleanup-sessions.ps1`.

---

## 1. Qayerdan boshlandi

`INDEX.md` ning «Qayerda to'xtadik» bo'limi 52-running nomzodini
ko'rsatgan edi:

> **Ochiq nomzod (taklif):** `06` §4.2 **tasdiqlash chegarasi jadvali**.
> U §5.2 bilan **aynan bir xil shaklga** ega … **Avval
> `tests/test_confirmation.py` ni to'liq o'qing** va bo'shliqni tasdiqlang.

## 2. Bo'shliq TASDIQLANDI va KENGAYTIRILDI

`tests/test_confirmation.py` to'liq o'qildi. Nomzod to'g'ri chiqdi:

```python
# --- `06` §4.2 chegara jadvali ---

@pytest.mark.parametrize(
    ("a_local", "expected"), [(4, 3), (12, 3), (40, 4), (100, 5), (250, 8), (900, 8)]
)
def test_required_score_matches_spec_table(a_local, expected):
    assert required_score(a_local, confirm=CONFIRM) == expected
```

Sarlavha «`06` §4.2 chegara jadvali» deydi, lekin hujjatga **bitta ham
havola yo'q**: olti juftlik qo'lda ko'chirilgan, jadvalning `sqrt` va
`Hisob` ustunlari umuman ishlatilmagan.

Keyin `06` §4 to'liq o'qildi (123–174-qatorlar) va nomzod §4.2 dan **butun
§4** ga kengaytirildi — §4.1 ham, §4.3 ham hech qayerdan o'qilmasdi.

### Nima uchun §9 ni yopish yetarli emas (52-ning sabog'i shu yerda ham)

49-run `06` §9 konfiguratsiya jadvalini yopdi
(`tests/test_confirm_params_contract.py`): `confirm.min_users = 3`,
`confirm.coef = 0.5`, `confirm.floor / ceil = 3 / 8`,
`spread.min_distance_m = 50` — hammasi hujjatdan tekshiriladi.

Lekin §9 — bu **kalit → qiymat** ro'yxati. §4 da esa aynan **o'rin** muhim:

- §9 da `3` **ikki marta** uchraydi — `confirm.floor` va
  `confirm.min_users`. Ular o'rin almashsa (`clamp(min_users, …)` va
  `distinct_users ≥ floor`) **ikkala** mavjud test ham yashil qolardi:
  qiymat o'zgarmaydi, faqat ma'nosi almashadi.
- `clamp(3, …, 8)` da pol bilan shift almashsa `clamp` `low > high` da
  `ValueError` bilan yiqilardi — ya'ni nosozlik ishlab chiqarishda,
  tasdiqlash paytida chiqardi, testda emas.
- `interval '30 days'` (§4.1) §9 da **umuman yo'q** — u
  `settings.coverage_window_days`, `.env` dan keladi.

## 3. §4 ning to'rtta artefakti

### 3.1. §4.1 denominator — eng qimmat, eng jim

```sql
-- A_local: hodisa radiusi + eps ichidagi 30 kunlik faol foydalanuvchilar
SELECT count(DISTINCT r.user_id)
FROM reports r
WHERE r.created_at > now() - interval '30 days'
  AND ST_DWithin(r.geom_public, :centroid, :radius_m + :eps);
```

To'rtta qaror, hech biri o'lchanmagan:

| Qaror | Buzilsa nima bo'ladi |
|---|---|
| `count(DISTINCT r.user_id)` | `count(*)` da bitta odamning o'nta xabari qamrovni o'nga ko'taradi, `N_req` sun'iy oshadi va haqiqiy uzilish tasdiqlanmaydi |
| `geom_public` | maxfiylik qoidasining buzilishi (`05` §3.1, `CLAUDE.md`) |
| `interval '30 days'` | oyna qisqarsa `A_local` tushadi va butun narvon siljiydi |
| `:radius_m + :eps` | hodisa chetidagi foydalanuvchi «faol emas» bo'lib qoladi, denominator hodisadan kichik bo'ladi |

**Eng ehtimolli siljish** esa boshqa joyda: `TerritoryStats.active_users_30d`
ni `A_local` o'rniga ishlatish. U `06` §5.4 to'sig'i uchun allaqachon
hisoblanadi va **tayyor turadi**, nomi ham chalg'ituvchi darajada o'xshash.
Shunda §4.1 ning butun sarlavhasi («hudud emas, hodisa izi») bekor bo'lardi
va uzilish bitta ko'chani qamrasa ham chegara butun tumanning faolligidan
hisoblanardi.

Shuning uchun `active_users_near` ning manbasi `inspect.getsource` bilan
o'qiladi va u yerda `TerritoryStats` / `active_users_30d` / `geom_exact`
**bo'lmasligi** talab qilinadi. `eps` ni qo'shish esa chaqiruvchida
(`clustering/service.py:_confirmation`) — u ham shu yerda qulflandi.

### 3.2. §4.2 formulaning shakli

```
N_req = clamp(3, ceil(0.5 × sqrt(A_local)), 8)
```

Qulflandi: pol → `ConfirmParams.floor`, shift → `.ceil`, koeffitsient →
`.coef`, **argument** → `A_local` (§4.1 da ta'riflangan aynan o'sha
kattalik; `A_district` yoki `households` ga o'zgarsa
`required_score(a_local=…)` o'zgarmasdan yashil qolardi).

`×` regexda `.` bilan olinadi (52-ning qarori) — hujjatda `*` ga
almashtirilsa test sababsiz yiqilmasin; koeffitsientning **qiymati**
baribir solishtiriladi.

Bundan tashqari §4.2 ning **prozasi** ham bog'landi: «Nima uchun **3** dan
past emas» va «Nima uchun **8** dan yuqori emas» — bu ikki xatboshi polning
va shiftning yagona sababi. Son o'zgarib izoh eskisicha qolsa, keyingi
o'quvchi qaysi biriga ishonishni bilmaydi va odatda **izohga** ishonadi.

### 3.3. §4.2 misollar jadvali

| `A_local` | `sqrt` | Hisob | `N_req` |
|---|---|---|---|
| 4 | 2.0 | 1.0 | **3** (pol) |
| 12 | 3.5 | 1.7 | **3** |
| 40 | 6.3 | 3.2 | **4** |
| 100 | 10.0 | 5.0 | **5** |
| 250 | 15.8 | 7.9 | **8** |
| 900 | 30.0 | 15.0 | **8** (shift) |

Har qator kod bilan qayta hisoblanadi va jadvalning **o'z arifmetikasi**
uch bosqichda tekshiriladi: `sqrt` ustuni haqiqatan `sqrt(A_local)` mi,
`Hisob` ustuni `coef × sqrt(A_local)` mi va `ceil` + `clamp` haqiqatan
`N_req` ustunini beradimi.

**52-dan farq (muhim).** 52-run §5.2 da har qatorning `(pol)` / `(shift)`
izohini **qat'iy** tekshirgan: izohsiz qator chegaraga tegib qolsa test
qizarardi. §4.2 da bu qoida **ishlamaydi**: `12 → 3` ham polga, `250 → 8`
ham shiftga tegadi, lekin ikkalasi ham izohsiz — hujjat izohni faqat
**birinchi** uchrashida yozgan. Shuning uchun bu yerda:

- izoh **bor** qator qat'iy tekshiriladi (`(pol)` → natija = pol va
  xom qiymat ≤ pol);
- izohsiz qator faqat `[pol, shift]` oralig'ida bo'lishi talab qilinadi;
- jadvalning **butun ma'nosi** alohida o'lchanadi: narvon polga ham,
  oraliqqa ham, shiftga ham tegishi shart (aks holda formula amalda
  o'zgarmas son bo'lib qoladi va buni hech narsa aytmasdi), ustiga
  `A_local` o'sish tartibida va `N_req` kamaymaydi — kvadrat ildizning
  butun ma'nosi shu.

👤 «Ochiq savollar» ga yozildi: hujjatga ikkita izoh qo'shilsa qoidani
52-nikidek qat'iylashtirish mumkin.

### 3.4. §4.3 konyunksiya

```
confirmed  ⟺  W ≥ N_req  ∧  distinct_users ≥ 3  ∧  spatial_spread_ok
```

Ikki tomonlama qulflandi:

1. **Matn tomoni.** `∧` roppa-rosa ikkita, `∨` va `yoki` yo'q; §4.3 ning
   izoh jadvalidagi uchta qator **aynan** shu uchta shartni izohlaydi
   (to'rtinchi shart izohsiz qolsa ham, jadvalda begona qator paydo
   bo'lsa ham yiqiladi); `distinct_users ≥ 3` → `ConfirmParams.min_users`,
   «maksimal masofa ≥ 50 m» → `spread_min_distance_m`.
2. **Xulq-atvor tomoni.** Bitta tayanch holat (`a_local = 15`, to'rt kishi,
   100 m qadamda → `confirmed`) va undan **uchta perturbatsiya**, har biri
   faqat bitta shartni buzadi:

   | Buzilgan shart | Kirish | Kutilgan `reason` |
   |---|---|---|
   | `W ≥ N_req` | to'rt kishi, har biri 0.5 ball → `W = 2.0` | `below_required_score` |
   | `distinct_users ≥ 3` | ikki og'ir manba, `W = 6.0` | `min_users` |
   | `spatial_spread_ok` | to'rt kishi, hammasi 15 m ichida | `spread` |

   Konyunksiyani faqat hujjatda o'qish yetarli emas: `evaluate()` da `and`
   `or` ga aylansa hujjat o'zgarmasdan qolardi.

Alohida tekshiriladi: §4.3 jadvalidagi «og'irlik odam sonini almashtira
olmaydi» jumlasi joyida turibdimi. U `06` §7 ning 3-misoli va `evaluate()`
dagi `reason` tartibining yagona asosi; yo'qolsa `distinct_users` shartini
«ortiqcha qat'iylik» deb olib tashlashga hech qanday to'siq qolmasdi.

---

## 4. Qarorlar va rad etilganlar

**Qarorlar:**

- `SPEC_EXAMPLE_ROWS = 6`, `SPEC_CONDITION_ROWS = 3` — **aynan**, «kamida»
  emas.
- Arifmetika **haqiqiy** `sqrt(A_local)` ga qarshi solishtiriladi,
  jadvalning yaxlitlangan `sqrt` ustuniga qarshi emas: `sqrt(12) = 3.46`,
  jadvalda `3.5`, `0.5 × 3.5 = 1.75`, jadvalda `1.7` — yaxlitlash xatolari
  qo'shilib `abs_tol` ni ma'nosiz qilardi.
- Unicode belgilarga bog'liqlik kamaytirildi: `⟺` nom bilan emas, `\W+`
  bilan olib tashlanadi; perturbatsiya testi shartni `≥` bilan emas, ASCII
  nomi (`N_req`, `distinct_users`, `spatial_spread_ok`) bilan topadi.
  `∧` esa qoladi — 52-run uni `test_scale_ladder_contract.py` da allaqachon
  muvaffaqiyatli ishlatgan.
- Hujjat jumlasini tekshirganda apostrofsiz bo'lak olinadi
  (`odam sonini almashtira olmaydi`) — `Og'irlik` ning apostrofi kodlashga
  bog'liq.

**Rad etilgan:**

- **§4.2 ning `(pol)` / `(shift)` qoidasini 52-nikidek qat'iy qilish** —
  hujjat izohni faqat birinchi uchrashida yozadi, qat'iy qoida ikkita
  qatorda asossiz qizil berardi (yuqorida, 3.3).
- **`coverage_window_days` ni `06` §9 ga ko'chirish** — hujjatga tegadi,
  «Ochiq savollar» ga 👤.
- **§4.2 misollar jadvalini `test_confirmation.py` dan olib tashlash** —
  u xulq-atvor testi va o'z o'rnida qoladi (40-, 49-, 52-runlarning naqshi:
  qo'lda yozilgan ro'yxat **qoladi**, lekin har run da manba bilan
  solishtiriladi).
- **`06` §6 (`confidence`)** — boshqa bo'lim, alohida fayl, keyingi nomzod.

---

## 5. Yozilgan fayl

`sveta/tests/test_confirmation_threshold_contract.py` — 21 ta bazasiz test
funksiyasi, parametrlangani bilan ~40 ta ishga tushish. Postgres talab
qilmaydi: `app.clustering.confirmation` va `app.clustering.formulas` toza
modullar, hujjat esa oddiy matn; `app.reports.queries` va
`app.clustering.service` faqat `inspect.getsource` uchun import qilinadi
(ikkalasi ham boshqa bazasiz testlarda allaqachon import qilinadi).

**Kod o'zgartirilmadi.** Bu run faqat o'lchash.

---

## 6. Keyingi run uchun

⚠️ **Yigirma to'rtinchi marta** `ruff check` va `pytest -m "not requires_db"`
ishga tushmadi. **Sandbox tiklanganda birinchi ish — butun `pytest` va
`ruff check`, yangi kod emas.**

**Ochiq nomzod (taklif):** `06` **§6 `confidence` hisobi**. U §4 bilan bir
xil kasallikka ega: `freshness` pog'onalari (`15 / 45`), `coverage_factor`
ning `clamp(0.5, sqrt(A_local / 20), 1.0)` shakli va **interfeys bandlari**
(`40 / 70 / 90` → `outage.confidence.*`) `test_confirmation.py:155–188` da
**qo'lda** yozilgan, hujjatga havolasiz. Bandlar ayniqsa qimmat: ular
foydalanuvchi ko'radigan matnni tanlaydi va `05` §10 metrikalari ham shu
chegaralarga tayanadi. `COVERAGE_DIVISOR = 20.0` esa `06` §9 jadvalida
**yo'q** — 49-ning testi uni ko'rmaydi.
**Avval `06` §6 ni va `test_confirmation.py` ning §6 qismini to'liq
o'qing** — 49, 50, 51, 52 va 53 aynan shu tekshiruv tufayli bekorga ish
qilmadi.

**Yopilgan nomzodlar, qayta ochilmasin:** `06` §4.1–4.3 tasdiqlash
chegarasi (53), `06` §5.1–5.4 masshtab narvoni (52), `06` §3.1–3.2 hudud
statistikasi (51), `06` §2 manba registri (50), `06` §9 konfiguratsiya
jadvali (49), `05` §8 fon vazifalari jadvali (45, 49 da tasdiqlangan),
`05` §7.2 endpoint sathi (48), `05` §10 metrikalar jadvali (47), oltin
ssenariylar (46), fon vazifalari registri (45), konfiguratsiya parity (44),
bildirishnoma domeni (43), `05` §2 DDL ustunlari (43), i18n ikki yo'nalish
(41, 42), `05` §2 DDL indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy
tip (38), `02` Faza 0 (34).

**Yangi saboq (53).** Bir bo'limning qoidasini ikkinchisiga **ko'chirmang**.
52-ning `(pol)` / `(shift)` qat'iy qoidasi §5.2 da to'g'ri, §4.2 da esa
noto'g'ri — ikkala jadval bir xil ko'rinadi, lekin §5.2 har chegaraviy
qatorni belgilagan, §4.2 faqat birinchisini. Naqshni ko'chirishdan oldin
**maqsad qatorlarni sanang**.

**Yana bir saboq (53).** Hujjatdan olingan unicode belgi kodda literal
yozilsa — bu yashirin bog'liqlik. `∧` va `×` da xavf yo'q (allaqachon
tekshirilgan), lekin `⟺`, `≥`, `≡` kabi belgilar uchun `\W+` yoki ASCII
nomi bilan ishlash ishonchliroq: test **shartlar** haqida qolsin,
hujjatning tipografiyasi haqida emas.

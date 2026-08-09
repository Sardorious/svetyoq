# 57-sessiya — `06` §8 deeskalatsiya kontrakti

**Sana:** 2026-08-09
**Sessiya:** `local_3ad002c7-…`
**Epic:** E5/E5b (ko'ndalang) — kontrakt qatlami, 17-fayl
**Natija:** ✅ `06` §8 endi hujjatdan o'qiladi; **bitta haqiqiy defekt topildi va
tuzatildi** (`apply_deescalation` qoidani inkor bilan yozgan edi).
**Sandbox:** ishladi — `pytest -m "not requires_db"` → **1343 passed, 1 skipped,
212 deselected**; `ruff check app tools tests alembic` → toza.

---

## 1. Nima uchun aynan §8

56-sessiya `06` §10 ni yopgach, `EpicProgress.md` §3 da uchta ochiq joy qoldi:
§11 (34-run qisman yopgan), §12 (46-run faqat nomlarni bog'lagan) va **§8** —
u haqda o'sha fayl aynan shunday yozgan edi: «deeskalatsiya taqiqi
`test_scale.py` va `test_confidence_contract.py` orqali **qisman** tegilgan,
lekin **§8 jadvalining o'zi hech qayerdan o'qilmaydi**».

§8 boshqa bo'limlardan farq qiladi: u formula bermaydi, **vaqt o'tishi bilan
nima o'zgarishini** aytadi. Uning artefaktlari — son emas, qoidalar, va aynan
shuning uchun ular jimgina buzilishi mumkin edi.

## 2. §8 dan olingan beshta artefakt

| Artefakt | Qayerda edi | Endi qayerdan o'qiladi |
|---|---|---|
| `evaluate_outages`, `60 s` (sarlavha qavsi) | `05` §8 da ham bor, lekin ikki hujjat solishtirilmagan | `test_job_name_and_interval_come_from_the_document` |
| «yangi xabar → `W`, `scale`, `confidence`» | hech qayerda | `evaluate` ning `values` lug'ati, AST bilan |
| `45` daqiqa | `status.py` da qo'lda ko'chirilgan | `test_fade_rule_thresholds_come_from_the_document` |
| «pasayish faqat `pending` da» | inkor bilan yozilgan (defekt) | `test_only_pending_may_shrink` |
| nasr: `rejected` + audit | hech qayerda | `test_prose_names_the_moderator_escape_hatch`, `…written_to_audit` |

`40` ni 53-sessiya allaqachon bog'lagan (`test_confidence_contract.py`) —
u §6 bandining chegarasi. `45` esa **faqat** §8 da yashaydi.

## 3. Topilgan defekt — qoida inkor bilan yozilgan

`06` §8, 4-qator: «Masshtab pasayishi | **Ruxsat etiladi**, lekin faqat
`pending` da».

Kod esa:

```python
if status == "confirmed" and rank(proposed) < rank(current):
    return current
```

Ya'ni **`confirmed` bo'lmagan hamma narsa** pasayishga ruxsat olardi:
`resolved`, `rejected`, `merged` ham. Ochiq statuslar ikkitagina bo'lgani
uchun natija bir xil ko'rinardi va hech qanday test yiqilmasdi —
`evaluate` yopiq hodisada `is_open` qo'riqchisida qaytadi, ya'ni funksiya
yakuniy status bilan hech qachon chaqirilmaydi. **Xato ko'rinmasdi, lekin
funksiya o'zi hujjatga zid edi**; qo'riqchi olib tashlansa yopilgan hodisaning
masshtabi jimgina kichrayardi.

Tuzatildi — qoida hujjatdagidek, **tasdiq orqali**:

```python
PENDING_STATUS = str(OutageStatus.PENDING)
...
if status != PENDING_STATUS and rank(proposed) < rank(current):
    return current
```

Tanimagan status ham endi pasaytirmaydi (konservativ tomon). Xulq-atvor
haqiqiy chaqiruv joyida **o'zgarmadi** — shuning uchun bu «tuzatish» emas,
«qoidani hujjat yozganidek yozish».

Defekt haqiqatan ushlanishini tekshirish uchun eski shart vaqtincha qaytarildi:
`test_only_pending_may_shrink` yiqildi (`status='resolved'` da `mahalla` →
`local`), keyin yangi shart tiklandi.

## 4. Ikkita yangi invariant

**`45 < autoclose`.** `evaluate_status` autoclose ni so'nishdan **oldin**
ko'radi. `cluster_autoclose_after_min` (120) `LOW_CONFIDENCE_AFTER_MIN` ga
teng yoki undan kichik bo'lsa §8 ning so'nish qatori **o'lik kodga** aylanardi
va buni bironta xulq-atvor testi ko'rsatmasdi: hamma hodisa baribir
`resolved` bo'lardi, faqat sababi boshqa. Endi qulflangan.

**So'nish sababi ≠ autoclose sababi.** §8 qavsdagi «(so'ndi)» ni alohida
holat sifatida beradi. Ikkalasi ham `resolved` qaytaradi; sabab qo'shilib
ketsa jurnal bo'yicha hodisa **nega** yopilgani aniqlanmasdi.

## 5. Rad etilgan variantlar

- **2-qatorni («xabarlar to'xtadi → `freshness` ↓ → `confidence` ↓») bu yerda
  ham tekshirish** — `test_confidence_contract.py::test_silence_lowers_confidence`
  uni allaqachon o'lchaydi. Ikkinchi joyda takrorlash tuzatish joyini noaniq
  qilardi (41-sessiyaning sabog'i). Buning o'rniga «har qatorning egasi bor»
  testi o'sha qatorni **nomlab** boshqa faylga havola qiladi.
- **`40` ni qayta bog'lash** — 53-sessiya qilgan, u §6 ning artefakti.
- **`apply_deescalation` ni `OutageStatus` qabul qiladigan qilish** —
  interfeys o'zgarishi, `06` talab qilmaydi; `PENDING_STATUS` konstantasi
  satrni status mashinasidan oladi va shu yetarli.
- **`ruff format`** — 82 fayl qayta formatlanardi (repo bo'ylab eskirgan
  formatlash), CI esa faqat `ruff check` yuradi. «Bitta run = bitta bo'lak»
  qoidasiga zid; «Ochiq savollar» ga yozildi.

## 6. Yangi/o'zgargan fayllar

| Fayl | Nima |
|---|---|
| `tests/test_deescalation_contract.py` | **yangi**, 17 funksiya / 18 ishga tushish |
| `app/clustering/scale.py` | `PENDING_STATUS`, `apply_deescalation` qoidasi va sababi |

## 7. Sandbox

56-sessiyaning `/tmp/sv56` muhiti **butun holda qoldi** — qayta o'rnatish
kerak bo'lmadi (`PYTHONPATH=/tmp/sv56:.` + o'sha `sitecustomize.py`).
Ildiz disk yana 100% (22 MB bo'sh), `pip install` imkonsiz; `ruff` esa
avvalgi runlardan qolgan `/tmp/wg-libs/bin/ruff` (0.16.2) bilan yurgizildi.
👤 `cleanup-sessions.ps1` ni har run oldidan yurgizish kerakligi kuchida
qolmoqda.

## 8. Keyingi qadam

`06` da ochiq qolgani — **§12** (46-run faqat oltin ssenariylar **nomlarini**
bog'lagan, mazmunini emas) va **§11** ning 34-run qamramagan qismi.
`05` tomonida §3.1 (jitter), §4.4/§4.5 (status mashinasi diagrammasi) hali
o'z kontrakt fayliga ega emas.

# 31-sessiya — yo'qolgan runni tiklash va testsiz kodning qo'lda auditi

**Session ID:** `local_a9f5078a-ea20-4641-80e6-d83ff6f3e6c6`
**Sana:** 2026-08-08
**Natija:** ⛔ Sandbox yiqilgan (INFRA-1, ketma-ket **ikkinchi** run) —
`ruff` ham, `pytest` ham ishga tushmadi. Kod yozilmadi; topilgan
narsalar qayd etildi, bitta test qulfi qo'shildi.

---

## 1. Run nima kutgan edi va nima topdi

29-sessiya keyingi runga ikkita aniq topshiriq qoldirgan edi:

1. **avval `ruff check` va `pytest -m "not requires_db"`** — 29- va undan
   oldingi (§19) run kodni tekshirmasdan qoldirgan;
2. bloklanmagan kod ishi — `01` §16 ning to'rtinchi qatori (mahalla
   qamrov indeksi).

Ikkalasi ham boshqacha chiqdi.

**Sandbox to'rt urinishda ham `useradd failed: No space left on
device`.** INFRA-1 ning qaytalanishi, ketma-ket ikkinchi run. Beshinchi
urinish qilinmadi — xato aynan bir xil takrorlanardi.

**`01` §16 esa allaqachon bajarilgan chiqdi.** Repoda
`app/stats/mahalla_coverage.py`, `service.mahalla_index()`,
`MahallaCoverageOut`, CSV izohlari, UZ/RU kalitlari va **ikkita kontrakt
testi** turibdi. Ya'ni 29-sessiyadan keyin yana bitta **arxivlanmagan
run** bo'lgan — 28-sessiyadan keyingisiga qo'shilib, jami ikkinchisi.

---

## 2. Yo'qolgan run topildi va sababi aniqlandi

`mcp__session_info__list_sessions` uchta oraliq sessiyani ko'rsatdi.
Ikkitasi bo'sh (`1356ae25`, `71b33228` — bittadan chaqiruv), uchinchisi
— `local_05dd60f2` — aynan §16 runi. Uning transkriptining oxiri:

```
[assistant] Now the missing tests that would have caught this, plus removing the leftover debug file.
[assistant] (called mcp__workspace__bash)
[assistant] (called ToolSearch)
[assistant] (called mcp__cowork__allow_cowork_file_delete)
```

**Sessiya o'chirish huquqini so'rab o'ldi.** `allow_cowork_file_delete`
odam tasdig'ini kutadi, rejalashtirilgan runda esa odam yo'q. Shu sabab
`PROGRESS.md` ham, `INDEX.md` ham yangilanmadi va keyingi ikki run §16 ni
«bajarilmagan» deb o'qidi.

Qilingani: 30-sessiya fayli **koddan qayta tiklandi**
([30_mahalla_qamrov_indeksi_05dd60f2.md](30_mahalla_qamrov_indeksi_05dd60f2.md)),
o'sha runda rad etilgan variantlar esa yo'qolgan — bu 29-sessiyaning
§19 ni tiklashi bilan aynan bir xil holat.

> **Yangi qoida.** Vaqtinchalik fayl yaratilmaydi. Yaratilib qolgan
> bo'lsa — mazmuni `Write` bilan olib tashlanadi va **o'chirish odamga
> qoldiriladi**. `mcp__cowork__allow_cowork_file_delete` rejalashtirilgan
> runda **chaqirilmaydi**: u runni butunlay to'xtatadi va shu bilan
> arxivni ham yo'q qiladi.

### `tests/test_dbg_tmp.py`

O'sha «leftover debug file». Mazmuni — `test_language_contract` ning
ichki funksiyalarini `print` bilan tekshiradigan, **birorta `assert` i
yo'q** harness. Test to'plamiga hech narsa qo'shmasdan uni
ifloslantirardi. Fayl bo'shatildi (izoh + odam uchun `git rm` ko'rsatmasi);
o'chirish huquqi agentda yo'q. U sinagan xatti-harakat yo'qolmadi —
`_routes` rekursiyasi 28-sessiyada `test_language_contract.py` da
allaqachon qulflangan.

---

## 3. Qo'lda audit — testsiz qolgan uchala running kodi

Sandbox ishlamagani uchun yagona mumkin bo'lgan tekshiruv. Ko'rilgani:
`app/analytics/` (29-sessiya), `app/notifications/params.py` (§19 runi),
`app/stats/mahalla_coverage.py` + `service.mahalla_index` + javob/CSV/testlar
(30-sessiya).

**Bloklovchi defekt topilmadi.** Tekshirilgani va natijasi:

| Tekshiruv | Natija |
|---|---|
| Import zanjiri (`mahalla_coverage`, `analytics`, `params`) | Barcha modul mavjud, import halqasi yo'q |
| `settings.subscription_default_radius_m` / `_max_radius_m` | `config.py` da bor |
| `params.guard.min_active_mahalla`, `params.scale.cell_ratio_mahalla` | `clustering/params.py`, `scale.py` da bor |
| `geo_q.current_mahallas`, `region_has_mahallas`, `reports_q.cells_with_reports_by_mahalla` | Hammasi bor |
| `load_territory_stats_many` mahalla `id` lari bilan ishlaydimi | ✅ `territory_stats.territory_id` generik (FK yo'q, daraja `territory_level` da) — jim bo'sh natija xavfi yo'q |
| i18n: `stats.mahallas.title`, `stats.warning.mahallas_missing`, `stats.warning.mahallas_unmeasured` | UZ va RU da bor |
| `_mean_index` ↔ `region_index` mantiqi | Bir xil (`min(qualities)`, `unknown` da `cap(LOW)`) — ataylab takrorlangan |
| `emit()` ning `extra` kalitlari ↔ `LogRecord` maydonlari | To'qnashuv yo'q; `LOGRECORD_RESERVED` `logging` nikidan kengroq |
| `analytics` chiqish nuqtalari `app/` da haqiqatan chaqirilyaptimi | O'ntadan sakkiztasi (kuzatiladiganlarning hammasi) chaqirilgan |

### Topilgan yagona bo'shliq — va u yopildi

`app/bot/service.py` oqimga `str(verdict)` uzatadi, kontrakt testi esa
`Verdict.NOT_ENOUGH_DATA.value` ni qulflagan. Bugun ikkalasi bir xil,
chunki `Verdict` — `StrEnum`. Lekin bu **tasodif**: bazaviy sinf oddiy
`Enum` ga almashtirilsa `str()` sinf nomi bilan keladi
(`Verdict.NOT_ENOUGH_DATA`) va `01` §21 ning **asosiy metrikasi**
(«доля вердиктов „данных недостаточно“») jimgina nolga tushardi —
`.value` esa o'zgarmasdi, ya'ni mavjud test buni **o'tkazib
yuborardi**. Qo'shilgani:
`tests/test_analytics_contract.py::test_verdict_reaches_the_stream_as_its_value`
— har bir verdikt uchun `str(verdict) == verdict.value`.

---

## 4. Yozib qo'yilgan bog'liqlik (kod ishi emas)

`mahalla_index` **hech qachon** `measured > 0` bermaydi, chunki
`app/jobs/refresh_coverage.py` faqat `territory_level='district'` qatorini
yozadi (docstringda ochiq: «Faqat tuman darajasi. Mahalla poligonlari E17
gacha yo'q; ular paydo bo'lganda shu vazifaga ikkinchi aylanish
qo'shiladi»).

Bugun bu ko'rinmaydi — spravochnik bo'sh, ya'ni javob `available=False`
bilan chiqadi. **E17 dan keyin esa** poligonlar paydo bo'ladi,
`available=True` bo'ladi va har bir mahalla `unknown` bo'lib qolaveradi:
`stats.warning.mahallas_unmeasured` doim yonib turadi. Ogohlantirish
to'g'ri va ko'rinadi (jim defekt emas), lekin uni o'chirish uchun E17
bilan birga `refresh_coverage` ga ikkinchi aylanish kerak. `PROGRESS.md`
«Ochiq savollar» ga yozildi.

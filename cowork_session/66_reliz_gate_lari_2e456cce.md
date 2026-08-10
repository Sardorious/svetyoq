# 66-sessiya — reliz gate lari (`03` §6) birinchi marta kodda

**Sessiya:** `local_2e456cce` · **Sana:** 2026-08-10 · **Epic:** REL (epicdan tashqari)

---

## Qayerdan boshlandi

65-run oxirida ikkita nomzod qoldirilgan edi:

> **Keyingi nomzodlar:** `03` §6 reliz gate lari (G-0…G-8 ning mashina bilan
> tekshiriladiganlari hech qayerda o'lchanmaydi) yoki `03` §11 «nima o'lchanadi»
> ↔ `05` §10 metrikalari bog'lanishi.

Birinchisi tanlandi. Sabab: `grep -rn "gate" app tools tests` **bitta ham**
mos qator bermadi. Ya'ni bu boshqa kontrakt runlaridan farq qiladi — u yerda
kod bor edi, hujjat bilan bog'lanish yo'q edi; bu yerda esa bog'lanadigan
narsaning o'zi yo'q edi.

Bu muhim, chunki `03` §4 «Yopiq yig'ish rejimi» bo'limi shunday tugaydi:

> **Xarita gate yopilmasdan ochilmaydi** — bu qat'iy qoida, muhokama predmeti emas.

va §6 G-4 haqida:

> Uni «biroz yumshatish» taklifi paydo bo'lganda — bu tasdiqlash
> tarafkashligining belgisi, texnik zarurat emas.

Loyihaning eng qat'iy qoidasi hech qayerda o'lchanmasdi.

---

## Nima yozildi

### `app/release/gates.py` — toza modul

To'qqizta gate, 18 ta mezon, `evaluate(values) → GateReport`.

Bazaga ham, `settings` ga ham, `Params` ga ham murojaat qilmaydi
(kontrakt testi buni AST bilan qulflaydi: faylda birorta `app.` importi
bo'lmasligi shart).

### `app/release/collector.py` — modullararo ulash

Bitta ham `SELECT` yo'q (`obs/collector.py` bilan bir xil tartib,
`05` §1). To'rtta o'lchov beradi:

| Mezon | Manba |
|---|---|
| `confirmable_share` | `clustering.repository.confirmable_counts` (yangi so'rov) |
| `map_refresh` | `clustering.snapshot.built_at_by_region` |
| `regions_active` | `geo.registry.active_regions` |
| `string_parity` | `core.i18n` (bazasiz) |

### `GET /api/v1/admin/gates`

Yangi `Permission.GATES_READ` — **faqat `admin`**. Metrikalar uchala rolda
ochiq, gate hisoboti esa yo'q: bu «nimani chiqarish mumkin emas» ro'yxati,
uni smena moderatori emas, qaror qabul qiladigan odam o'qiydi.

Javob **tarjima qilinadi** (qolgan admin endpointlaridan farqli — ular kod
qaytaradi): hisobotni odam ko'chirib qo'yishi mumkin. 36 ta yangi i18n
kalit UZ/RU.

---

## Uchta qaror

### 1. Uchta holat, ikkitasi emas

`CriterionStatus`: `MET` / `UNMET` / **`UNMEASURED`**.

`UNMEASURED` `MET` ga qo'shilmaydi. Gate faqat **hamma** mezoni `MET`
bo'lgandagina `CLOSED`; bittasi `UNMET` bo'lsa `BLOCKED`; qolganida
`UNKNOWN`. `UNKNOWN` ham keyingi relizni bloklaydi.

Sabab hujjatning o'zida: o'lchanmagan mezonni jimgina «muammo yo'q» deb
ko'rsatadigan hisobot — §6 ogohlantirgan yumshatishning eng arzon shakli.
Hech kim qaror qabul qilmaydi, gate esa o'z-o'zidan yopiladi.

### 2. Chegaralar literal va konfiguratsiyaga bog'lanmaydi

Bu `stats/methodology.py` ning qoidasiga **teskari**, va teskariligi
ataylab:

* metodologiyada birorta raqamli literal yo'q — u sozlamalar bilan
  **birga siljishi** kerak, aks holda vitrina yolg'on gapiradi;
* gate da hammasi literal — u siljimasligi kerak.

`p90 ≤10 s` chegarasi `settings.map_snapshot_ttl_s` ga bog'lansa, gate ni
yopish uchun `.env` da bitta sonni o'zgartirish yetarli bo'lardi. `≥50%`
`region_config` dan olinsa, E11 dagi sozlash gate ni ham «sozlab»
qo'yardi. Gate — mahsulot qarori, ishga tushirish parametri emas.

Har bir chegara `tests/test_release_gates_contract.py` da `03` dan parse
qilinadi.

### 3. Chegarasi yo'q mezon — kamchilik emas, holat

`03`:

> Qamrov: shahar hududining ≥N% ida kamida bitta xabar
> *(N Faza 0 natijalari bo'yicha belgilanadi)*

`reported_area_share.threshold = None`, ya'ni mezon **hech qachon** `MET`
bo'lmaydi — qiymat `1.0` bo'lsa ham. Chegarani «taxminan» to'ldirish gate
ning ma'nosini yo'q qilardi.

Test ikki tomonlama: hujjatda hamon `N%` turganini tekshiradi, ya'ni son
yozilgan kunda **qizil** bo'ladi va kodga chegara qo'shishni talab qiladi.

---

## Jadval qisqartma, mezon esa tafsilotda

`03` §6 ning «Mezon» ustuni — xulosa. Operativ mezon reliz tafsilotida va
u ko'proq:

| Gate | Jadval | Tafsilot |
|---|---|---|
| G-4 | «Zichlik chegarasi + qamrov chegarasi» — **2 ta** | «Yopiq yig'ish rejimi» chiqish mezoni — **4 ta** |

Faqat jadvalni kodga ko'chirish parametrlarning barqarorligini va
moderatsiya SLA sini jimgina yo'qotardi, hisobot esa to'g'ri ko'rinardi.
`test_the_pilot_exit_criteria_have_four_bullets` buni qulflaydi.

---

## Run davomida topilgani: `05` §10 da `answer_p90` metrikasi yo'q

`03` ikki joyda bir xil narsani so'raydi:

* §4 R1.0 chiqish mezoni — «javob p90 **≤10 soniyada** olinadi»;
* §11 «Nima o'lchanadi», R1.0 qatori — «Time-to-answer p90».

`05` §10 metrikalar jadvalida esa unday metrika **yo'q**. Eng yaqini
`time_to_confirm_seconds`, lekin u boshqa narsani o'lchaydi: hodisa qachon
tasdiqlangani, foydalanuvchi savoliga qachon javob berilgani emas.

Ikkalasini tenglashtirish G-5 ni **soxta yopardi**. Shuning uchun mezon
`None` bilan qoldirildi va savol odamga chiqarildi — metrikani qo'shish
`05` §10 ga o'zgartirish kiritishni talab qiladi, spetsifikatsiya esa
qonun (`CLAUDE.md` §2).

Xuddi shu sababdan `notify_delivery_p90` ham o'lchanmaydi:
`outbox_lag_seconds` navbatning **yoshini** beradi, yetkazish vaqtini emas.

---

## `confirmable_counts` — maxrajning qarori

Yangi so'rov `rejected` va `merged` ni **sanamaydi**. G-4 «kuzatilgan
uzilish hodisalari» haqida gapiradi, bu ikkitasi esa hodisa emas:
birinchisi moderator rad etgan, ikkinchisi boshqasining ichiga kirgan.

Ularni maxrajga qo'shish gate ni **pasaytirardi** — moderatsiya qanchalik
yaxshi ishlasa, zichlik shunchalik yomon ko'rinardi. To'plam
`aggregate.REPORTED_STATUSES` bilan bir xil.

Hodisa umuman bo'lmasa ulush `None` (o'lchanmagan), `0.0` emas: bo'sh
namunada «zichlik yetarli emas» degan xulosa ham asossiz.

---

## Mutatsiya

**15 mutatsiya, 1 survivor.**

Ushlangani: chegaralarning hujjatdan uzilishi (uchtasi), chegarasiz
mezonning jimgina yopilishi, `UNMEASURED` ning `CLOSED` ga qo'shilishi,
`blocking_gate` ning oxirgi gate ni qaytarishi, `≥`/`≤` ning qat'iy
bo'lib qolishi (ikkitasi), notanish kalitning jim o'tishi, mezon kodining
i18n kalitidan uzilishi, slugda chiziqcha qolishi, mezon kodining
takrorlanishi (import paytida `ValueError`), G-4 ning boshqa relizga
bog'lanishi.

**Survivor:** `confirmable_counts` dagi status to'plami `OutageStatus` ga
kengaytirilsa — `tests/test_release_gates_db.py` uni ushlaydi, lekin u
`requires_db` va sandboxda skip bo'ladi. CI da o'lchanadi.

---

## Natija

* `pytest -m "not requires_db"` → **1654 passed, 1 skipped** (+33)
* `requires_db` → **231** (+6)
* `ruff check app tools tests alembic` → toza
* migratsiya **yo'q**

Yangi fayllar: `app/release/{__init__,gates,collector}.py`,
`tests/test_release_gates{,_contract,_db}.py`.

O'zgargani: `app/admin/roles.py` (`GATES_READ`), `app/api/v1/admin.py`
(endpoint), `app/clustering/repository.py` (`confirmable_counts`),
`app/core/i18n/locales/{uz,ru}.json` (+36 kalit),
`tests/test_i18n_key_contract.py` (`KEY_TABLES` ga ikkita ro'yxat).

---

## 👤 Odamga chiqarilgan uchta savol

1. **G-4 ning `N` chegarasi** va «hudud ulushi» ning o'lchovi (maydon
   bo'yichami yoki tuman soni bo'yichami). Ikkinchisi arzonroq, lekin
   boshqa narsani o'lchaydi — proksi qo'yilmadi.
2. **Qo'lda tasdiqlanadigan 9 ta mezon qayerda qayd etiladi.** Hozircha
   ular har doim `UNMEASURED`, ya'ni hisobot G-0 ni birinchi to'siq deb
   ko'rsatadi — va bu **to'g'ri**: hech biri rasman qayd etilmagan.
3. **`answer_p90` metrikasi** (yuqorida).

---

## Keyingi nomzodlar

* `03` §11 «Nima o'lchanadi» ↔ `05` §10 metrikalari — `03` dan qolgan
  yagona bog'lanmagan band; bu run uning R1.0 qatorida allaqachon
  bo'shliq ko'rsatdi.
* `01` §21 analitika hodisalari qatlami.

---

## ♻️ Sandbox

**Sakkizinchi marta tekin keldi:** `/tmp/sv59` butun holda (104 paket +
`ruff`), `$HOME` (`/sessions/...`) yana 100% (35 MB bo'sh), ildiz `/` da
2.1 GB. Retsept barqaror — **avval `/tmp` ni qidir**.

👤 `cleanup-sessions.ps1` ni har run oldidan yurgizing.

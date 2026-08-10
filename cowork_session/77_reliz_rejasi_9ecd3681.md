# 77-sessiya — `01` §25 «Release Plan» birinchi marta kodda

**Session ID:** `local_9ecd3681`
**Sana:** 2026-08-10, ~14:30–15:40 UTC
**Epic:** REL (ko'ndalang) — `app/release/plan.py`
**Natija:** ✅ 2079 → **2130 passed** (+51), `requires_db` 231 (o'zgarmadi),
migratsiyasiz, ruff yashil.

---

## Nima uchun aynan §25

76-run uchta nomzod qoldirgan edi: `01` §25 «Release Plan»,
`GET /api/v1/admin/monitoring` (reyestrlar vitrinasi) va `01` §29/§30.
§25 tanlandi, chunki u repoda **allaqachon javobi bor** savolga
ikkinchi javob beradi: 66-run `03` §6 ning to'qqizta gate ini kodga
ko'chirgan, ya'ni «chiqishga ruxsat bormi» degan savol o'lchanadi.
§25 o'sha savolga beshta boshqa shart bilan javob beradi va ikkala
hujjat bir-biriga **hech qayerda havola qilmaydi**.

76-run ning o'zi ham §25 ni ko'rsatgan edi: `DP-1` ning «Полигоны
валидны» sharti §25 ning R0 ida **ikkinchi marta** takrorlanadi.

---

## Asosiy qaror: reliz identifikatori umumiy kalit emas

Ikkala hujjat ham `R<son>.<son>` shaklidan foydalanadi. Uchtasi
so'zma-so'z ustma-ust tushadi, **bittasigina** bir xil narsani
anglatadi:

| ID | `01` §25 | `03` §3 | Sinf |
|---|---|---|---|
| `R0` | pilot, 1–2 mahalla, yopiq doira | **yo'q** (`R0.1/0.2/0.3` — muhandislik; yopiq bosqich «reliz emas») | `FOREIGN` |
| `R1` | shahar, UZ-first, xarita, statistika | `R1.0` **va** `R1.2` (orasida `G-7`) | `SPLIT` |
| `R1.1` | obuna va bildirishnomalar | obuna va bildirishnomalar | `SHARED` |
| `R2.0` | 1055 avtoparsingi | **ommaviy API** (1055 → `R2.1`) | `REASSIGNED` |
| `R3.0` | viloyat, operator | **PWA va ko'p mintaqalilik** | `REASSIGNED` |

Bu terminologik nuqson emas, chunki **kod allaqachon tanlagan**:
`gates.GATES` ning `G-8` i `release="R3.0"` va uning mezoni
`MIN_ACTIVE_REGIONS` (ikkinchi mintaqa); `measures` ning `r20` bosqichi
«Ochiqlik» — ommaviy API. §25 dan kelgan o'quvchi «R3.0 ning gate i»
ni operator bilan muzokara deb o'qiydi va **butunlay boshqa** mezonni
ko'radi.

Shuning uchun `Alias` — baho emas, **ikkita hujjatni solishtirishdan**
chiqadigan tasnif (`dependencies.Referent` bilan bir xil rol), va
`COLLIDING` faqat `REASSIGNED` ni oladi: `SPLIT` va `FOREIGN`
o'quvchini yanglishtirmaydi (identifikatorni izlagan odam uni topmaydi
yoki ikkitasini topadi), `REASSIGNED` esa **javob beradi** va javob
noto'g'ri.

---

## Ikkita mustaqil o'q

* **`Ship`** — reliz va'da qilgan *mazmun* qurilganmi:
  `BUILT` · `PARTIAL` · `ABSENT` · `CONTRADICTED`.
* **`Gate`** — uning *sharti* qayerdan javob oladi:
  `INSTRUMENTED` · `UNRECORDED` · `UNQUANTIFIED` · `EXTERNAL`.

Mustaqilligi darhol ko'rinadi: `R1` ning mazmuni to'liq qurilgan,
sharti hech qayerda saqlanmaydi; `R0` ning sharti yagona
o'lchanadigan shart, mazmuni esa bajarib bo'lmaydi.

---

## ⚠️ Eng jim topilma: `R0` ning ikkala yarmi bitta bayroq, qarama-qarshi holatda

«Регион активен для 1–2 махаллей, **закрытый круг**».

Repoda mintaqani yoqadigan yagona narsa — `regions.is_active`, va u
**bitta bit**:

* `geo.registry.active_regions` faqat `is_active` ni oladi →
  o'chirilgan mintaqa **xabar qabul qilmaydi**;
* `jobs.build_map_snapshot` aynan o'sha ro'yxat bo'ylab yuradi →
  yoqilgan mintaqa uchun snapshot **quriladi**;
* `api.v1.map.get_map` autentifikatsiyasiz va `is_active` ni umuman
  so'ramaydi (imzosi: `session`, `region`, `if_none_match`) →
  snapshot bor bo'lsa u ommaga ochiq.

Ya'ni «регион активен» `is_active = true` ni talab qiladi, «закрытый
круг» esa uni `false` qilishni. Ikkinchi bayroq **yo'q**:
`Region.__table__` da bitta mantiqiy ustun bor.

`03` buni reliz emas, **operatsion bosqich** deb ataydi («Ommaviy
xarita **yopiq**») va qoidasini eng qat'iy shaklda yozadi: «Xarita
gate yopilmasdan ochilmaydi — bu qat'iy qoida, muhokama predmeti
emas». Bu qoidaning repoda mexanizmi **yo'q**, va 66-run buni o'z
izohida ochiq yozgan («Bu modul … xaritani yopmaydi»).

Shuning uchun `Ship.CONTRADICTED` alohida sinf: bu tugallanmagan ish
ham (`ABSENT`), qisman qurilgan narsa ham (`PARTIAL`) emas — repo
qatorni **yozilganidek bajarishga imkon bermaydi**, va tuzatish yangi
funksiya emas, **ikkinchi bayroq** talab qiladi. Bu 👤 qaror:
`05` §2.1 da ham, `01` da ham bunday ustun yo'q. Tuzatilmadi ataylab.

Qatorning ikkinchi yarmi ham shu yerda: «для 1–2 махаллей» —
yoqishning granulyarligi **mintaqa** (`region_admin` ning oltita
buyrug'i orasida mahalla darajasi yo'q), `tools/import_boundaries.py`
da `mahalla` so'zi umuman uchramaydi va `quality.SQL_PROMOTE` faqat
`districts` ga yozadi.

---

## `R0` ning sharti — beshtadan yagona javob beriladigani

«Полигоны валидны» repoda **bor**: `geo.quality` oltita tekshiruv
beradi, bir qismi `blocking=True`, va staging dan `districts` ga
ko'chirish faqat undan keyin. Ya'ni **yagona `INSTRUMENTED` shart
aynan yagona bajarib bo'lmaydigan qatorda turibdi** — hisobotda
`answerable == unshippable`.

Yon eslatma: tekshiruvlar `districts` ustida yuriladi, R0 ning
mazmuni esa mahallalar haqida — shart bo'sh to'plam ustida ham
«bajarilgan» ko'rinadi.

---

## Qolgan to'rtta shart

* `R1` — «Критерии выхода Ph.0 закрыты»: §24 ning **beshta belgisi**,
  hammasi `- [ ]`, va repoda `P0-*` natijasini saqlaydigan joy yo'q
  (75-run ning `SCHEDULED` sabog'i, tripwire bilan qulflandi) →
  `UNRECORDED`.
* `R2.0` — «P0-1 подтвердил наличие источника»: o'sha sabab →
  `UNRECORDED`.
* `R1.1` — «Накоплены данные о плотности»: o'lchov nomlangan,
  **chegara yo'q** (shartda birorta raqam yo'q). `03` §6 G-4 xuddi
  shu joyda `threshold=None` bilan to'xtaydi → `UNQUANTIFIED`.
  Mexanizm to'liq (E13), kalibrlash yo'q:
  `subscription_default_radius_m` hali ham 500 m — `01` §19 dan
  parse qilingan «500 м Ташкента» ga **teng** (74-run).
* `R3.0` — «Переговоры результативны»: repodan tashqarida va
  tashqarida qolishi kerak (67-run ning `EXTERNAL` sabog'i), shuning
  uchun `EXTERNAL` da dalil **taqiqlanadi**.

---

## Teskari yo'nalish: rejada yo'q ikkita qurilgan sirt

* **`UP-1` Ommaviy API va OpenAPI** (`03` R2.0, E15) — `01` ning
  `R2.0` o'rni band (unda 1055 turibdi), ya'ni §25 ning rejasi
  bo'yicha ommaviy API **hech qachon chiqmaydi**, holbuki u qurilgan
  va `/openapi.json` ochiq.
* **`UP-2` Admin-panel va moderatsiya** (`03` R0.3, E8) — `03` ning
  Q-2 qarori «Moderatsiya ommaviy xaritadan **oldin** quriladi»
  deydi; §25 ning eng birinchi qatori esa allaqachon mintaqani
  yoqadi. §25 ning butun matnida `api`, `модерац`, `админ`
  so'zlarining birortasi yo'q.

Simmetriya: §25 mavjud bo'lmagan ikkitasini (1055, operator) reliz
qilib qo'yadi va mavjud bo'lgan ikkitasini umuman sanamaydi.

---

## Hisob

| O'q | Qiymat |
|---|---|
| `Alias` | `FOREIGN` 1, `SPLIT` 1, `SHARED` 1, `REASSIGNED` 2 |
| `Ship` | `BUILT` 1, `PARTIAL` 2, `ABSENT` 1, `CONTRADICTED` 1 |
| `Gate` | `INSTRUMENTED` 1, `UNRECORDED` 2, `UNQUANTIFIED` 1, `EXTERNAL` 1 |
| Rejada yo'q sirt | 2 |
| `accurate` | **`False`** |

Hech narsa tuzatilmadi **ataylab** — uchala topilma ham hujjat yoki
sxema qarorini talab qiladi.

---

## Mutatsiyalar

**37 mutatsiya, 1 survivor topildi va tuzatildi.**

Survivor: `03` §3 reliz ro'yxatini **ikki marta** beradi — mermaid
gantt va «Bosh jadval» — va ular mustaqil yozilgan. Gantt dagi
`R3.0 PWA va ko'p mintaqalilik` ni o'zgartirish hech narsani
yiqitmasdi, holbuki `Alias` tasnifining butun tayanchi shu bo'lim.
57-run ning sabog'i o'z faylida: nusxalar bir-biriga bog'landi
(`test_the_two_copies_of_the_peer_map_agree`).

Yo'l-yo'lakay `PEER_SPEC` **o'lik konstanta** bo'lib qolayotgani
ko'rindi — endi undan bo'lim raqami parse qilinadi va test jadval
o'sha bo'limda ekanini tekshiradi.

O'ldirilgan mutatsiyalar orasida muhimlari: `G-8` ning `release`
driftisi, `G-4` ga chegara qo'yish, radiusni kalibrlash,
`regions` ga ikkinchi mantiqiy ustun qo'shish, `SQL_PROMOTE` ning
maqsad jadvali, `01` va `03` dagi katak tahrirlari, Faza 0
belgisini `- [x]` qilish.

---

## Fayllar

* `sveta/app/release/plan.py` — yangi (541 qator)
* `sveta/tests/test_release_plan_contract.py` — yangi (51 test)
* `sveta/app/release/__init__.py` — modul izohiga qator

Migratsiya **yo'q**, i18n kaliti **yo'q**, API o'zgarishi **yo'q**.

---

## 👤 To'rtta savol

1. **`R0` uchun ikkinchi bayroq kerakmi?** «Yig'ish yoqilgan, nashr
   o'chirilgan» holati bugun ifodalanmaydi; `03` ning eng qat'iy
   qoidasi shu sababdan mexanizmsiz. `regions` ga ustun qo'shiladimi,
   yoki qoida jarayon darajasida qoladimi?
2. **Reliz identifikatorlarining nom fazosi.** `R2.0` va `R3.0`
   ikkita hujjatda ikki xil relizni nomlaydi; kod `03` ni tanlagan.
   `01` §25 `03` ga moslanadimi, yoki §25 o'z prefiksini oladimi
   (masalan `P-R2.0`)?
3. **§25 ommaviy API ni ham, moderatsiyani ham nomlamaydi.** Reja
   kengaytiriladimi, yoki `03` §3 yagona reliz rejasi deb e'lon
   qilinadimi (o'shanda §25 «biznes bosqichlari» bo'lib qoladi)?
4. **`R1.1` ning zichlik sharti `G-4` ning `N` iga tengmi?** Ikkalasi
   ham chegarasiz va ikkalasi ham Faza 0 ga tayanadi, lekin maqsadlari
   boshqa (biri radius kalibrlash, ikkinchisi xaritani ochish).

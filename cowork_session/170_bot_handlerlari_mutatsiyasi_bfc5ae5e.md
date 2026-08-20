# 170-run — `app/bot/handlers.py` mutatsiya bilan o'lchandi

**Sessiya:** `local_bfc5ae5e` · **Sana:** 2026-08-19 · **Epic:** E3
**Natija:** 40 mutatsiya → 10 KILLED, **30 SURVIVOR (75 %)**; 28 tasi
qulflandi, 2 tasi ekvivalent. `tests/test_bot_handlers_contract.py` (45 test).
To'plam **3902 passed, 310 skipped**, `ruff` toza. Mahsulot kodi tegilmadi.

---

## 1. Nishon qayerdan olindi

169-run qoldirgan navbatning (1) bandi: `app/bot/handlers.py` — **404
qator**, navbatdagi eng katta modul va hech qachon mutatsiya bilan
o'lchanmagani. `PROGRESS.md` ning run jurnali (169, 168, 167, 165)
to'rt marta shu nomni takrorlagan, ya'ni nishon eskirgan `EpicProgress`
§4 dan emas, jurnaldan tasdiqlandi.

**PostGIS ataylab ko'tarilmadi** (169-run qoidasi). Tekshiruv arzon:

```
grep -rln "bot.handlers\|from app.bot.handlers" tests/
  → test_bot_handlers_transaction.py, test_bot_location_routing.py,
    test_bot_webhook.py, test_i18n_key_contract.py,
    test_phase0_plan_contract.py, test_transaction_boundaries.py,
    test_user_stories_contract.py
grep -c requires_db <har biri>  → 0
```

Birorta `requires_db` testi modulni chaqirmaydi, ya'ni baza verdiktga
hech narsa qo'sha olmaydi.

## 2. Muhit

Sandbox yangi edi: `/sessions` da 4.6 GB bo'sh, lekin **Python 3.10**
va bog'liqliklarsiz. `app/admin/audit.py` dagi `from enum import StrEnum`
darhol yiqildi (`StrEnum` 3.11+), `apt` da `python3.11` yo'q — shuning
uchun 168-run retsepti takrorlandi: `micromamba` (`/sessions/<sid>/work/bin`),
`conda-forge` dan `python=3.11`, keyin `pip` bilan `pyproject` ning
bog'liqliklari ikkita partiyada. Repo `rsync` bilan ildizdan
`work/base/` ga ko'chirildi (faqat `sveta/` emas —
`svetyoq-worker-copy-from-repo-root`).

Bazasiz to'plamning etaloni: **3857 passed, 310 skipped** — 169-run
raqami bilan bir xil, ya'ni nusxa to'g'ri.

## 3. O'lchov — ikki bosqichli

**Tor tanlov:** yuqoridagi yettala fayl (176 test, ~7 s/mutant),
partiya 10-11 mutant. **Tasdiq:** har bir survivor **butun bazasiz
to'plamda** (3857 test), ikkita parallel ishchi nusxada (`w1`, `w2`),
partiya 3 + 3 (~130 s). Verdikt faqat `rc == 1` da KILLED. Har partiyadan
keyin `diff` etalon fayl bilan.

Tor tanlovda o'lganlar: **M08** (`bot.start.greeting` → `bot.menu.title`),
**M17** (`request_area` → `request`), **M19** (`map.unavailable` →
`map.link`) — uchalasi `test_i18n_key_contract` yoki
`test_user_stories_contract` ning matn reyestriga tushdi; **M28**, **M30**
(`on_location` ning marshruti), **M33**–**M36** (`accepted`/`answered`
bayroqlari va `_add_subscription` dagi `listing` ning `try` ichidaligi),
**M37** (`bot.unknown` → `bot.help`).

**O'ttizala survivor to'liq to'plamda ham omon qoldi** — yolg'on
survivor yo'q.

## 4. Sabab — bitta va tarkibiy

Mavjud uchala test fayli **faqat `on_location`** ni chaqiradi va holatni
(`FLOW_KEY`, `KIND_KEY`) **qo'lda yozadi**:

```python
state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})
await handlers.on_location(message, state)
```

Ya'ni holat qanday **paydo bo'lgani** o'lchanmagan. Botning kirish
nuqtalari — `cmd_start`, `cmd_help`, `on_language`, `on_language_button`,
`on_report_button`, `on_area_button`, `on_map`, `on_subscriptions`,
`on_subscription_action`, `fallback` — hech qachon chaqirilmagan;
`build_router` esa faqat **soni** bilan tekshirilgan
(`test_router_registers_every_menu_action`: 9 va 2).

Survivorlar to'rt sinf:

**(a) Holat mashinasi (M13, M14, M15, M16, M23).** `on_report_button`
`FLOW_REPORT` o'rniga `FLOW_QUERY` yozsa xabarlar **butunlay yo'qolardi**
(har bir geolokatsiya hudud so'roviga tushardi); `set_state` yo'qolsa
ham xuddi shu; `KIND_OUTAGE` ↔ `KIND_RESTORED` almashsa «svet yo'q»
«svet keldi» ga aylanardi; `FLOW_SUBSCRIBE` `FLOW_REPORT` ga aylansa
obuna qo'shish o'rniga xabar yozilardi.

**(b) `/start` ning tarmoqlari (M05, M06, M07).** `state.clear()`,
`if is_new` ning yo'nalishi va undan keyingi `return` — uchalasi ham
o'lchanmagan: yangi foydalanuvchi til tanlash klaviaturasi ustiga
darhol menyu olardi.

**(c) Callback yo'llari (M10, M11, M12, M21, M25, M26).** Til callbacki
va obuna callbacki umuman ishga tushmagan: qorovullari
(`language_from_callback is None`, `subscription_from_callback is None`),
javob tilining manbai (so'ralgan til emas, **saqlangan** til), o'chirishdan
keyin ro'yxatning qayta yuborilishi va `text = t(exc.message_key, …)`
o'rniga **kalitning o'zi** ko'rsatilishi.

**(d) O'lchanmagan argumentlar (M01, M02, M27, M29, M31, M32).**
`_tg_id` ning `0` i (`from_user` yo'q holat), `_language_code`,
`tg_update_id` — **`05` §6.3 idempotentligining yagona manbai**, u
jimgina `None` ga aylansa takror webhook ikkinchi xabarni yozardi —
`accuracy_m` (`01` §21), `lat`/`lon` almashuvi va `KIND_KEY` ning sukuti.

Bundan tashqari **router** (M03, M04, M38, M39, M40): `fallback`
`on_location` dan oldin qo'yilsa butun geolokatsiya oqimi o'lardi va
handlerlar **soni o'zgarmasdi**; menyu filtri toraysa (`RESTORED` tushib
qolsa) tugma jimgina `fallback` ga tushardi; callback prefiksining `:`
ajratgichi yo'qolsa `langru` kabi begona `callback_data` ham handlerga
kirardi.

## 5. Qulf — `tests/test_bot_handlers_contract.py`, 45 test

**Kalit qaror (bu running yagona texnik topilmasi).** Callback
handlerlari `isinstance(callback.message, Message)` bilan qorovullangan.
Odatdagi `dataclass` fikstyura bu shartni **jimgina yiqitadi**:
handlerning yarmi bajarilmaydi, istisno chiqmaydi, test yashil qoladi.
Shuning uchun fikstyura endi haqiqiy `aiogram.types.Message` va
`CallbackQuery` ning **vorisi** — `model_construct` bilan validatsiyasiz
quriladi, `answer` esa qayd qiluvchi metod bilan almashtiriladi:

```python
class _RecordingMessage(Message):
    async def answer(self, text, reply_markup=None, **kwargs):
        harness.sent.append(Sent(text=text, markup=reply_markup))
```

`reply_markup` ham o'lchanadi (`== main_menu("uz")`, `== location_request("uz")`)
— aks holda M09 (menyusiz `/help`) omon qolardi.

Bo'limlar: (1) kim so'ralayapti, (2) menyu filtri, (3) `/start` va
`/help`, (4) til, (5) tugmalar → geolokatsiya so'rovi, (6) xarita,
(7) obuna callbacklari, (8) geolokatsiyaning argumentlari, (9) router.

Router bo'limi filtrni `FilterObject.callback.__self__` orqali
`MagicFilter` sifatida olib, `resolve(SimpleNamespace(text=…))` bilan
chaqiradi; menyu marshruti **har bir amal × har bir til** bo'yicha
parametrlangan va «aynan bitta handler» talab qilinadi.

## 6. Qayta o'lchov: 28/30

Ikkitasi omon qoldi va ikkalasi ham **ekvivalent**:

* **M22** `kind == SUBSCRIPTION_ADD` → `kind != SUBSCRIPTION_DELETE`
* **M24** `kind != SUBSCRIPTION_DELETE or subscription_id is None` → `and`

Sababi bitta: `subscription_from_callback` ning qiymatlar to'plami aynan
`{add, del}` va `del` da `uuid` **har doim** bor, ya'ni ikkala
formulirovka barcha erishiladigan kirishda teng. Bu **taxmin qilinmadi** —
`test_the_subscription_parser_has_exactly_two_kinds` uni o'lchaydi:
parser uchinchi turni qaytaradigan bo'lsa yoki `del` `uuid` siz kelsa,
test yiqiladi va handlerdagi shartlar qaytadan ko'rib chiqiladi.

## 7. Yakun va keyingi qadam

Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar **tegilmadi**;
vaqtinchalik fayl qolmadi (mutatsiya faqat `work/` dagi nusxalarda
bo'ldi, mount dagi `handlers.py` `diff` bilan tekshirildi).

Navbatning qolgani: `app/geo/models.py` (251), `app/api/openapi.py` (227),
`app/stats/export.py` (193), `app/clustering/lookup.py` (183),
`app/bot/keyboards.py` (183), `app/db/session.py` (161). Oxirgi ikkitasi
uchun avval `grep -c requires_db` bilan bazaning kerakligini tekshirish
kerak (169-run qoidasi).

👤 Ochiq savollar o'zgarmadi; `100_sec_yozuvni_yopish_ad837191.md` hamon
turibdi.

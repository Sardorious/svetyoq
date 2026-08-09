# 36-sessiya — audit qatori bazada o'lchanadi va `cmd_update` dagi teshik yopildi

**Sana:** 2026-08-08
**Sessiya id:** `local_2393e045`
**Epic:** E8/E19 (BR-024 ning davomi)
**Holat:** ✅ Kod yozildi. ⚠️ Sandbox **yettinchi ketma-ket run** yiqildi (INFRA-1).

---

## 1. Sandbox — yettinchi marta

Ikki urinish, ikkalasi ham bir xil:

```
useradd failed: exit status 1: useradd: /etc/passwd.71323: No space left on device
```

Ya'ni `ruff check` ham, `pytest -m "not requires_db"` ham yana ishga
tushmadi. **To'qqizta run** (§19, 29–36) tekshirilmagan kod qoldirdi.

Ko'rsatma bo'yicha (3-urinishdan keyin to'xtash) qo'lda auditga o'tildi.

---

## 2. 35-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q

`tests/test_region_audit.py` ning har bir tasdig'i manba bilan
solishtirildi:

| Tasdiq | Tekshirildi |
|---|---|
| `sub.add_parser("…")` regexi | `build_parser` da o'zgaruvchi haqiqatan `sub`; oltita buyruq topiladi va `MUTATING \| READ_ONLY` ga aynan teng |
| `MUTATING` funksiya nomlari | `cmd_add`, `cmd_update`, `_set_active`, `cmd_config` — hammasi mavjud va hammasida `audit.record(` bor |
| `READ_ONLY` | `cmd_list` bloki `async def cmd_list` dan `async def cmd_add` gacha; `audit.record(` yo'q |
| `audit\.record\(\s*\n?\s*session,` regexi | to'rtala joyda chaqiruv `audit.record(\n<bo'shliq>session,` shaklida — regex backtracking bilan mos keladi |
| `cmd_promote` | `args.dry_run` (321-qator) `audit.record(` (337) dan oldin; `AuditAction.BOUNDARIES_PROMOTE` joyida |
| `test_the_cli_role_grants_nothing` | `Role` — `StrEnum`, ya'ni `{str(r) for r in Role} == {"viewer","moderator","admin"}` va `"cli"` unda yo'q; `has_permission("cli", …)` → `Role("cli")` `ValueError` → `False` |
| `SystemActor` ↔ `Actor` to'qnashuvi | `uuid5(NS, "cli:sardor") != uuid5(NS, "sardor")` |
| `cli_actor()` fallback | `USER=""` → falsy → `USERNAME` → `"unknown"`; `USER="   "` → truthy → `.strip()` → `"" or "unknown"` |
| `test_actions_follow_the_object_dot_verb_convention` | obyektlar ro'yxati `{"outage","user","region","boundaries"}` ga kengaytirilgan |

**Bloklovchi defekt topilmadi.**

---

## 3. Topilgan defekt — `cmd_update` audit qatorisiz yozardi

Bu 35-running kodida emas, **undan oldingi** kodda edi va 35-run uni
o'zi bilmagan holda qamrab olishi kerak edi.

### Mexanizm

```python
async with session_scope() as session:
    ...
    if args.name_uz:
        region.name_uz = args.name_uz     # ← ORM obyekti o'zgardi
    ...
    if args.center:
        try:
            lat, lon = _parse_center(args.center)
        except BBoxError as exc:
            print(f"[BLOK] {exc}")
            return EXIT_USAGE             # ← kontekstdan NORMAL chiqish
    ...
    await audit.record(...)               # ← bu yergacha yetib bormaydi
```

`return` — kontekst menejeri uchun **istisno emas**, ya'ni
`session_scope()` `except` bo'lagiga tushmaydi va `await session.commit()`
ni bajaradi. `region` shu sessiyaning identifikatorlar xaritasida
turgani uchun `name_uz` **bazaga yoziladi**.

Natija: `region_admin update --code X --name-uz Yangi --center xato`
mintaqa nomini o'zgartiradi va `audit_log` ga hech narsa yozmaydi —
aynan BR-024 ning buzilishi.

### Nima uchun 35-running testlari buni ushlay olmaydi

`test_audit_is_written_inside_the_same_transaction` `audit.record(`
ning `session_scope()` **ichida** ekanini tekshiradi. U ichida.
`test_every_mutating_command_records_audit` chaqiruv borligini
tekshiradi. Chaqiruv bor. Ikkalasi ham yashil, xatti-harakat esa
noto'g'ri — ya'ni bu 33- va 34-sessiyalar sanagan «simvol bor, natija
yo'q» sinfining yangi ko'rinishi, faqat bu safar simvol emas,
**yetib borish yo'li** yo'q.

### Nima uchun `cmd_add` da bu yo'q

`cmd_add` `parse_bbox` va `_parse_center` ni `session_scope()`
**ochilishidan oldin** chaqiradi. Farq faqat `cmd_update` da edi.
`_set_active` va `cmd_config` da esa barcha `return EXIT_*` lar birinchi
o'zgarishdan oldin turadi (`region.bbox is None`, `key not in DEFAULTS`,
`float(args.value)`), ya'ni ular xavfsiz.

### Tuzatish

Tahlil sessiyadan oldinga ko'chirildi:

```python
try:
    box = parse_bbox(args.bbox) if args.bbox else None
    center = _parse_center(args.center) if args.center else None
except BBoxError as exc:
    print(f"[BLOK] {exc}")
    return EXIT_USAGE

async with session_scope() as session:
    ...
```

Sikl ichidagi `if args.bbox:` → `if box is not None:`, `if args.center:` →
`if center is not None:`. Xatti-harakat bir xil (bo'sh satr — «berilmagan»),
lekin xato yo'li endi tranzaksiyaga umuman kirmaydi.

**Rad etilgan variant:** `raise` bilan chiqish (istisno `rollback` ni
chaqirardi). Rad etildi, chunki `region_admin` foydalanuvchi xatosiga
istisno emas, `[BLOK]` + chiqish kodi bilan javob beradi — bu butun
asbobning naqshi va uni bitta joyda buzish keyingi buyruqni yozadigan
odamni chalg'itardi.

---

## 4. Yozilgan testlar

### 4.1. `tests/test_region_audit.py` ga umumiy invariant

```python
@pytest.mark.parametrize("validator", ("parse_bbox(", "_parse_center("))
def test_input_is_validated_before_the_transaction_opens(validator): ...
```

Har bir funksiyada: agar validator ham, `async with session_scope()` ham
bor bo'lsa — validator **oldin** turishi shart. Bu qoida `cmd_update` ga
emas, **butun modulga** yoziladi, ya'ni keyingi buyruq ham shu naqshdan
chiqa olmaydi.

Qoidaning shakli ataylab «tekshiruv qayerda» (holat), «xato qayerda»
(yo'l) emas: ikkinchisini manba matnidan o'lchab bo'lmaydi.

### 4.2. `tests/test_region_audit_db.py` — **yangi**, 15 ta `requires_db` test

35-run qoldirgan ish. Matnli testlar chaqiruv **borligini** o'lchaydi, bu
fayl chaqiruv **natija berishini**.

**Uchta tuzilish qarori:**

1. **Har bir tasdiq yangi sessiyada o'qiladi** (`_rows()` o'z
   `session_scope()` ini ochadi). O'sha sessiyadan o'qish
   identifikatorlar xaritasidan qaytishi mumkin edi, ya'ni `commit`
   bo'lmagan qator ham «bor» ko'rinardi — testning butun ma'nosi
   yo'qolardi.
2. **Buyruqlar haqiqiy parser orqali** ishga tushiriladi:
   `build_parser().parse_args(argv)` → `await args.func(args)`. Shunda
   `set_defaults(func=…)` simlari va argparse standartlari (`--seed`
   bayrog'i, `--value` ning `None` i) ham o'lchanadi. `main()`
   chaqirilmaydi: u `asyncio.run` va `dispose_engine()` qiladi va
   keyingi testlarning enginini yopib qo'yardi.
3. **Fikstyura mintaqasi `add` dan o'tmaydi**, qator to'g'ridan-to'g'ri
   SQL bilan qo'yiladi. `cmd_add` `region_config` ni seed qiladi, ya'ni
   undan keyin birorta kalit «yo'q» bo'lmasdi va `before = None` holati
   umuman tekshirilmasdi.

**Qamrab olingan qarorlar:**

| Test | Nimani qulflaydi |
|---|---|
| `config_key_leaves_a_row_after_the_commit` | qator `commit` dan omon chiqadi, `actor_role == "cli"` |
| `an_absent_key_is_recorded_as_none_not_as_the_default` | `before = {key: None}` — «kalit yo'q edi» |
| `the_second_change_shows_the_previous_value` | ikkinchi yozuvda `None` emas, eski **son** |
| `an_unknown_key_changes_nothing_and_records_nothing` | `06` §9 ro'yxati yopiq |
| `a_seed_that_adds_nothing_writes_nothing` | jurnal — o'zgarishlar tarixi |
| `listing_the_configuration_is_not_an_event` | o'qish jurnalga tushmaydi |
| `activate_records_the_transition` | `before/after` = `is_active` |
| `a_repeated_activate_is_silent` | takroriy buyruq yozilmaydi |
| `deactivate_is_a_separate_action` | bitta yordamchi, ikki xil amal |
| `update_records_only_the_changed_fields` | faqat o'zgargan maydon kesimi |
| **`a_rejected_update_leaves_neither_a_change_nor_a_row`** | **3-bo'limdagi defekt** |
| `an_update_without_arguments_is_not_an_event` | bo'sh `update` |
| `add_writes_the_creation_without_a_before` | `before is None`, `is_active is False` |
| `a_blocked_add_writes_nothing` | mavjud kod ustiga `add` |
| `the_operator_is_identified_but_never_stored` | `uuid5(NS, "cli:"+nom)`, nom bazada yo'q |

**bbox `(10.0, 10.0, 10.2, 10.2)`** ataylab okean: boshqa `requires_db`
testlari Samarqand/Toshkent/Moskva nuqtalari bilan ishlaydi va faol
mintaqa reyestriga begona qator tushib qolsa ularni buzardi. Fikstyura
teardown ida `audit_log`, `region_config`, `regions` o'chiriladi va
`registry.invalidate()` chaqiriladi.

---

## 5. Nima yozilmadi

- **Migratsiya yo'q** — `audit_log` `0002` dan beri bor.
- **Yangi i18n kaliti yo'q** — jurnal ichki oqim, CLI chiqishi operator
  uchun.
- **Yangi bog'liqlik yo'q.**
- **`out_of_coverage` (BR-005 / BRL-01) ga tegilmadi** — 35-run uni
  «Ochiq savollar» ga qo'ygan, chunki bajarish `05` §2 dan chetlashish
  bo'lardi.

---

## 6. Keyingi run uchun

> ⚠️ **Sakkizinchi marta:** `ruff check` va `pytest -m "not requires_db"`.
> Endi **to'qqizta** run (§19, 29–36) tekshirilmagan kod qoldirdi. Bu
> running defekti (3-bo'lim) qo'lda o'qish bilan topildi, lekin uni
> **hech qanday mavjud test** ushlamasdi — ya'ni sandboxning yo'qligi
> bu safar to'sqinlik qilmadi; to'sqinlik qiladigani — yangi
> yozilgan 15 ta bazali testning **hech biri hech qachon ishga
> tushirilmagani**.
>
> **`import_boundaries.py` shu runda ham ko'rildi va toza:** `cmd_stage`
> ning `session_scope` i (260-qator) ichida erta `return` yo'q,
> `cmd_promote` da esa `args.dry_run` yagona erta chiqish va u
> `SQL_CLOSE_CURRENT` dan **oldin** turadi, ya'ni o'zgarishsiz. Ya'ni
> 3-bo'limdagi naqsh butun quvurda faqat `cmd_update` da bor edi.
>
> **Bloklanmagan kod ishi nomzodi qolmadi** — lekin bu **da'vo**, isbot
> emas: 21-, 22-, 23-, 27-, 28- va shu (36-) sessiya aynan shunday
> da'vodan keyin buzilgan talab yoki defekt topgan. Eng foydali
> keyingi qadam — o'sha naqshni (kontekst menejeridan `return` bilan
> chiqish) `app/` bo'ylab qidirish: `session_scope()` ichida `return`
> bo'lgan har bir joy tekshirilishi kerak.
>
> 👤 `cleanup-sessions.ps1` (INFRA-1 — ketma-ket 7-run),
> `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi (rejalashtirilgan runda
> taqiqlangan). 👤

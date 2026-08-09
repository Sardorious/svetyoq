# 56-sessiya — `06` §10 sxema o'zgarishlari kontrakti

**Sana:** 2026-08-09 · **Epic:** E5/E5b (ko'ndalang) · **Sessiya:** `370bc693`
**Natija:** `sveta/tests/test_schema_changes_contract.py` (yangi, 13 test / 29 run)
**Testlar:** ✅ `pytest -m "not requires_db"` → **1325 passed, 1 skipped, 212 deselected**
**Qo'shimcha:** ⛔ serverdagi `docker compose up` defekti topildi va tuzatildi

---

## 1. Run boshidagi holat

`cowork_session/INDEX.md` va `sveta/EpicProgress.md` o'qildi. 55-run `06` §7
ni yopgan va sandboxni tiklagan edi (`1296 passed, 1 skipped`). 55-ning
«keyingi qadam» ustuni ikkita nomzod qoldirgan: `06` §11 (suiiste'mol) yoki
`06` §10 (`reports.weight` ni qotirish yo'li o'lchanmagan). **§10 tanlandi** —
u kattaroq yuza beradi: nafaqat nasriy da'vo, balki DDL ning o'zi.

## 2. Sandbox — birinchi ish, va u yiqildi

`ruff check` → `command not found`, `python -m pytest` → `No module named
pytest`. Sabab:

```
/dev/sda1  9.6G  9.5G  11M  100%  /
```

`/tmp` da 3.3 GB oldingi sessiyalarning qoldig'i (`/tmp/ch` 1.8 GB,
`/tmp/me` 336 MB, uchta 156 MB lik `uvcache`, uchta `venv`). **Hammasi
boshqa uid ga tegishli** (`great-focused-keller` ≠ o'sha sessiyalarning
foydalanuvchisi), shuning uchun `rm -rf` `Permission denied` beradi —
48 MB gina ozod bo'ldi, jami 59 MB. `pip install` uchun kamida ~200 MB
kerak (`sqlalchemy` + `pydantic` + `fastapi` + `aiogram` + `h3`).

`/usr/local/lib/python3.10/dist-packages` (730 MB) — bazaviy obrazning
hujjat asboblari (`cv2`, `pandas`, `onnxruntime`), root ga tegishli,
o'chirib bo'lmaydi.

**Xulosa:** 55-run ning «INFRA-1 yopildi» belgisi **bitta run ga** yetdi.
👤 `cleanup-sessions.ps1` har run oldidan kerak.

## 3. Nima uchun §10 alohida qimmat

§10 — `06` ning yagona bo'limi bo'lib, u **formula emas, DDL** beradi:
sakkizta `ALTER TABLE ... ADD COLUMN` (`reports` ga 2 ta, `outages` ga 6 ta).
Bu satrlar **uch joyda** takrorlanadi va bugungacha hech biri boshqasidan
o'qilmasdi:

| Joy | Nimani ushlaydi | Nimani ko'rmaydi |
|---|---|---|
| `tests/test_schema.py` → `ADDED_BY_06` | ustun **nomlari** | tip, `NOT NULL`, `DEFAULT`, `REFERENCES` |
| `test_schema_index_parity.py` (40-run) | indekslar | ustunlar |
| — | — | model tipi ↔ migratsiya tipi |

Uchinchi qator eng jim: test bazasi `alembic upgrade head` bilan quriladi
(`conftest.py` da `create_all` yo'q), ya'ni **migratsiyaning** tipi haqiqiy
ustunga aylanadi, ORM esa **modelnikini** ishlatadi. Ikkalasi ajralsa,
`Numeric(6,1)` bilan `SmallInteger` orasidagi farq faqat haqiqiy bazada,
overflow paytida bilinardi.

## 4. Ikkita nasriy da'vo — DDL blokidan tashqarida

55-run «son jadval ustunida emas, **nasrda** yashaydi» degan artefakt turini
topgan edi. §10 da o'shanday ikkita joy bor:

1. «**`weight` va `required_score` qotiriladi**» — bu ro'yxat DDL dagi
   **`NOT NULL` siz** ustunlar to'plamiga aynan teng bo'lishi kerak
   (qotirilgan qiymat qaror paytida yoziladi, undan oldingi qatorlarda yo'q).
   Uchinchi ustun qotirilsa yoki bulardan biri `NOT NULL` bo'lsa, nasr bilan
   DDL jimgina ajralardi: `test_schema.py:112` o'sha ikki nomni **qo'lda**
   biladi.
2. «`scale_capped = true` … interfeysda dislaymer chiqarish uchun kerak» —
   ustunning **mavjudligi** shu jumla bilan asoslanadi, §5.4 bilan emas.
   Test uni `boolean` + `DEFAULT false` ga bog'laydi (dislaymer standart
   holatda ko'rinmasligi kerak).

## 5. Nima yozildi

`sveta/tests/test_schema_changes_contract.py`:

- §10 SQL bloki parse qilinadi (`--` izohlari olib tashlanadi, `;` bo'yicha
  bo'linadi) → `SpecColumn(table, name, type, not_null, default, references)`;
- **hujjat ↔ model:** tip `postgresql.dialect()` ga kompilyatsiya qilinib
  solishtiriladi (`Numeric(6, 1)` → `numeric(6,1)`), `nullable`,
  `server_default`, `foreign_keys.target_fullname`;
- **hujjat ↔ `0003`:** migratsiya `ast` bilan o'qiladi, `op.add_column`
  to'plami ikki tomonlama tenglashtiriladi, tip/`nullable`/`server_default`
  har ustun uchun; `downgrade()` hammasini tushirishi; `create_foreign_key`
  ning to'rtta argumenti;
- **hujjat ↔ `test_schema.py`:** `ADDED_BY_06` `ast.literal_eval` bilan
  o'qilib manbaga tenglashtiriladi (import emas — matn);
- nasr: «qotiriladi» da'vosi ↔ `NULL` ruxsat etilgan ustunlar;
  `scale_capped = true` ↔ `boolean`/`false`;
- qotirish **joylari**: `create_report` da `weight = freeze_weight(...)` va
  `Report(..., weight=weight)`; `evaluate` da
  `"required_score": result.required_score`;
- `WEIGHT_DECIMALS == 1` — `numeric(3,1)` ning kasr qismidan.

**Defekt topilmadi.** Uchala tomon rozi; run holatni qulfladi.

## 6. Qarorlar va rad etilganlar

- `SPEC_STATEMENTS = 8`, `SPEC_PER_TABLE = {"reports": 2, "outages": 6}`
  **aynan** — parser bo'sh ro'yxat qaytarsa hamma solishtirish jimgina
  yashil bo'lardi, shuning uchun blok shakli alohida test.
- `_SA_TYPES` lug'ati **yopiq** (`Text`, `SmallInteger`, `Boolean`,
  `Numeric`): yangi tip paydo bo'lsa test tushunarli xato beradi, taxmin
  qilmaydi.
- `DEFAULT_SOURCE_CODE` migratsiyada **nom** bilan yozilgan, shuning uchun
  `ast.literal_eval` yetmaydi — `_literal()` o'sha bitta nomni alohida
  hal qiladi.
- **Rad etildi:** `outage.scale.capped` i18n kalitining ulanmaganini bu
  yerda ham tekshirish. Holat 41-sessiyada topilgan va
  `test_i18n_key_contract.py` ning `KNOWN_UNREACHABLE` ida sababi bilan
  turibdi; ikkinchi joyda takrorlash ikkita testni bir vaqtda qizil qilardi
  va tuzatish joyi noaniq bo'lardi.
- **Rad etildi:** `test_schema.py` dan `ADDED_BY_06` ni olib tashlab, uni
  markdowndan yasash — `test_schema.py` ni markdown o'qishga bog'lash uni
  og'irlashtirardi. Nusxa qoldi, lekin endi manba bilan solishtiriladi.
- **Rad etildi:** `from tests.test_schema import ADDED_BY_06` — repoda
  testlararo import yo'q, `ast` bilan matn o'qish xavfsizroq.
- **Rad etildi:** boshqa migratsiyalar bu ustunlarga tegmasligini tekshirish
  — `test_schema.py` ning `EXPECTED_COLUMNS` i har qanday yangi ustunni
  allaqachon ushlaydi.
- **Kod o'zgartirilmadi.**

## 7. Test o'rniga nima qilindi

`pytest` yo'qligi sababli faylning **stdlib ga tayanadigan** qismi
(hujjat parseri, migratsiya AST i, `ADDED_BY_06` o'qish, nasr regexlari,
manba matnidagi qulflar) alohida skript bilan sandboxda ishga tushirildi
va **hammasi o'tdi**. Bitta xato shu yo'l bilan topildi va tuzatildi:
`` `scale_capped = true` `` da backticklar **butun ifodani** o'raydi,
shuning uchun `` `(\w+)`\s*=\s*true `` naqshi hech narsa topmasdi →
`` `(\w+)\s*=\s*true` `` ga o'zgartirildi.

`python -m py_compile` toza; qatorlar 100 belgidan oshmaydi (`ruff`
`line-length = 100`); importlar isort guruhlariga mos.

**ORM tomoni** (`metadata.tables[...]`, `type.compile(postgresql.dialect())`)
ishga tushirilmadi — u faqat modellarni matn bo'yicha o'qib solishtirildi
(tiplar, `server_default` lar, `nullable` lar mos).

## 7-b. Run oxirida: sandbox baribir ishladi

👤 «qayta ishga tushir» dedi. Ikkinchi urinishda disk 107 MB gacha bo'shagan
edi va ikkita to'siq alohida hal qilindi:

1. **`~/.local` ga yozib bo'lmaydi** (`Errno 28`, uy katalogida kvota bor)
   — `/tmp` da yo'q. Yechim: `pip install --no-cache-dir --target /tmp/sv56`.
2. **Sandboxda faqat Python 3.10**, loyiha 3.11+ talab qiladi
   (`from enum import StrEnum`). Yechim: `/tmp/sv56/sitecustomize.py` da
   `enum.StrEnum` va `datetime.UTC` shimi — **repoga tegmaydi**.

Paketlar bosqichma-bosqich qo'shildi (`pytest`, `sqlalchemy`, `pydantic`,
`geoalchemy2`, `h3`, `httpx`, `pytest-asyncio`, `fastapi`, `aiogram`,
`alembic`, `apscheduler`, `asyncpg`); joy bo'shatish uchun `pygments` va
`__pycache__` lar o'chirildi.

**Natija:** `1325 passed, 1 skipped, 212 deselected` — 55-running 1296 tasiga
yangi faylning **29 ta ishga tushishi** qo'shildi, ya'ni bu run yozgan
hamma narsa **haqiqatan ishlaydi** va bironta eski test buzilmadi.
`ruff` uchun joy qolmadi (31 MB) — 👤 keyingi runda yoki CI da.

## 7-c. Serverdagi `docker compose up` defekti

👤 serverdan log yubordi: DB `Healthy`, lekin `sveta-migrate` `exit 1`:

```
ConnectionRefusedError: [Errno 111] Connect call failed ('172.18.0.8', 5432)
```

**Sabab — healthcheck poygasi, kodda emas.** Postgres entrypoint i `initdb`
ni va PostGIS init skriptlarini server **faqat unix soketda** turgan holda
bajaradi (`listen_addresses=''`). `pg_isready` hostsiz chaqirilganda aynan
o'sha soketga ulanadi va «accepting connections» deydi → compose konteynerni
`healthy` deb belgilaydi → `depends_on: service_healthy` ni kutayotgan
`migrate` ishga tushadi va **TCP** ga ulanib rad javobini oladi. Log dagi
vaqtlar buni tasdiqlaydi: DB 10.1 s da «healthy», `migrate` 12.5 s da
yiqilgan; volume esa o'sha runda **yangi yaratilgan** (`Created`), ya'ni bu
faqat birinchi ishga tushirishda bo'ladi.

**Tuzatildi** (`sveta/docker-compose.yml`): `pg_isready -h 127.0.0.1 …` va
`start_period: 30s`. Init paytida TCP porti yopiq, shuning uchun healthcheck
to'g'ri kutadi.

**👤 Ikkita eslatma:**

* Serverdagi `~/deploy/docker-compose.yml` — **repodagidan boshqa fayl**
  (loyiha nomi `deploy`, xizmatlar `sveta-db`/`sveta-migrate`, volume
  `deploy_sveta-pgdata`). Tuzatishni unga qo'lda ko'chirish kerak.
* Hozirgi holatni tuzatish uchun hech narsa o'chirish shart emas: DB endi
  to'liq ishga tushgan, `docker compose up -d` ni qayta yurgizish yetarli.

## 8. Keyingi qadam

1. 👤 **Serverda:** `docker compose up -d` ni qayta yurgizing; keyin
   `~/deploy/docker-compose.yml` ga healthcheck tuzatishini ko'chiring.
2. 👤 `.\push.ps1` — 26+ run push qilinmagan, CI hech qachon yurmagan.
   55-run ning `index.lock` eslatmasi hamon kuchda:
   `Remove-Item .git\index.lock -Force` → `.\push.ps1`.
3. 👤 `cleanup-sessions.ps1` — `ruff` uchun ~30 MB kerak, hozir yo'q.
4. Keyingi running birinchi ishi: `ruff check` (56-runda yurmagan).
5. Keyingi kontrakt nomzodi: `06` §11 suiiste'mol jadvali (34-run qisman
   yopgan) yoki `06` §8 qayta baholash/deeskalatsiya jadvali — u hozir
   hech qayerdan o'qilmaydi.

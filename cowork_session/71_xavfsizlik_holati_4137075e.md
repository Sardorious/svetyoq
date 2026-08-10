# 71-sessiya — SEC: `01` §20 «Security» birinchi marta kodda

**Sana:** 2026-08-10 · **Sessiya:** `local_4137075e` · **Epic:** SEC (ko'ndalang, `01` §20 + BRD «Безопасность» NFR lari)

---

## Nomzodni tanlash

70-run ikkita nomzod qoldirgan edi: `GET /api/v1/admin/monitoring`
(beshta reyestr vitrinasiz turibdi) yoki `01` §19/§20 da tegilmagan
bo'lim qolganini tekshirish.

Ikkinchisi tanlandi va tekshiruv darhol javob berdi:

* **§19 Notifications** — jadval kanallarni sanaydi (Telegram MVP,
  Web Push Phase 2, Email/SMS/WhatsApp kirmaydi) va yagona texnik
  qarori — obuna radiusi. U 14-runda (`app/notifications/`) va
  `06` orqali allaqachon qamrab olingan; yangi ma'lumot yo'q.
* **§20 Security** — hech qayerda o'qilmagan. Kodda `outage.read_exact_geo`
  degan simvol umuman uchramaydi, garchi BRD uni **NFR-S-02**,
  «Обязательно» deb belgilasa ham.

Tanlov: §20.

## Fe'lning o'zi tuzoq

§20 butun bo'limni bitta jumlaga sig'diradi:

> Наследуется полностью: RBAC, MFA для админ-ролей, шифрование, аудит,
> политика сессий и паролей, разделение `geom_exact` / `geom_public`,
> право `outage.read_exact_geo`.

«Наследуется» — **kelib chiqish**, holat emas. Toshkent paketidan
meros olingan kafolat bu repoda avtomatik ishlamaydi: bu yerda fork
emas, noldan yozilgan kod. Ya'ni «meros» amalda «qaytadan bajarilishi
kerak» degani, va bo'limni «hammasi bor» deb o'qish eng arzon xato
bo'lardi. Aynan shuning uchun bo'lim yetmish run davomida o'qilmadi:
u o'zini o'qilgandek ko'rsatib turgan edi.

## Asosiy ajratma: bajarilgan ≠ himoyalangan

Xavfsizlik kafolati mahsulot xususiyatidan shunisi bilan farq qiladi:
u **buzilganda hech narsa yiqilmaydi**. 60-run buni `05` §3 haqida
aytgan edi; §20 ga u to'liq tegishli. Shundan ikkinchi darajali, lekin
xavfliroq holat kelib chiqadi: kafolat **bugun rost**, chunki uni
buzadigan kod hali yozilmagan — lekin uni rost saqlab turadigan hech
narsa yo'q.

Shuning uchun `Posture.ENFORCED` **ikkita** shart talab qiladi:
mexanizm kodda bor **va** uni olib tashlaganda yiqiladigan test bor.
Bittasi bo'lsa — `UNDEFENDED`, va hisobotda alohida ko'rinadi.

### Topilma: «ПДн не собираются» himoyalanmagan edi

§20 jadvali: «Не собираются: ни ФИО, ни телефон, ни username».

Bugun rost — `users` da `tg_id`, `language`, `region_id`, `trust_score`,
`is_blocked`, `created_at` dan boshqa ustun yo'q. Lekin buni **birorta
test o'lchamasdi**: `username` ustunini qo'shadigan bitta migratsiya
butun to'plamni yashil qoldirgan holda §20 ni yolg'onga aylantirardi.

Endi `USERS_ALLOWED_COLUMNS` — **oq** ro'yxat (qora emas: `username`
ni taqiqlash `user_name` ni o'tkazib yuborardi), va §20 sanagan uchala
ПДн turi `PDN_COLUMN_HINTS` orqali alohida tekshiriladi, ya'ni xato
xabari «ortiqcha ustun bor» emas, «telefon kirib keldi» bo'ladi.

## Ikkinchi o'q: kafolat ≠ hujjat atagan mexanizm

`Mechanism` `Posture` ni takrorlamaydi. Hujjat ko'p joyda **nomni**
aytadi, kafolat esa boshqa mexanizm bilan ta'minlangan bo'lishi mumkin.

`outage.read_exact_geo` aynan shunday. Kafolat bugun **kuchliroq**
mexanizm bilan bajarilgan: `05` §7.3 bo'yicha `geom_exact` hech qanday
endpointdan chiqmaydi, ya'ni uni huquqi bori ham ko'rmaydi. Holat —
`ENFORCED`, mexanizm — `SUBSTITUTED`.

⚠️ Va bu qatorning izohi ogohlantirish: hujjat atagan `Permission` ni
qo'shish qatorni `AS_WRITTEN` ga ko'chiradi va **eshik ochadi** — gate
siz ruxsat xavfsizlikni oshirmaydi, faqat hisobotni yashillaydi.
70-run ning `restated_count` bilan bir sinf. Ruxsat **qo'shilmadi**, va
`test_the_named_permission_does_not_exist_in_the_role_matrix` uni
taqiqlaydi. 👤 `05` §7.3 bilan ziddiyat — 26-run ning ochiq savoli,
ochiqligicha qoladi.

## Uchinchi holat: `MISSTATED`

§20: «идентификатор Telegram хранится в псевдонимизированном виде».

`users.tg_id` — xom `bigint`, `unique`. Uni bir tomonlama xeshlab
**bo'lmaydi**, chunki u faqat identifikator emas, **yetkazish manzili**:

```python
# app/notifications/service.py:274
await sender.send(chat_id=item.tg_id, text=item.text)
```

Telegram orqali ishlaydigan mahsulot Telegram identifikatorini
pseudonimlashtirsa, foydalanuvchiga javob qaytara olmaydi.

Muhimi: kod farqni **biladi**. `app/admin/auth.py` dagi aktor haqiqatan
pseudonim (`uuid5(ACTOR_NAMESPACE, name)`) va izohi buni ataylab
tushuntiradi. Ya'ni `tg_id` ning xomligi bilmaslik emas, **majburiyat**.

Shuning uchun `ABSENT` emas, `MISSTATED`: da'vo yozilganidek bajarilishi
mumkin emas, va o'rnida torroq kafolat bajariladi — `narrower`:
identifikator tizimdan chiqmaydi (`05` §7.3, `test_api_surface_contract`,
`app/analytics/catalogue` da ham yo'q).

## Reyestr

O'n olti qator, oltita holat:

| Holat | Nechta | Qaysilar |
|---|---|---|
| `ENFORCED` | 6 | RBAC, audit, `geom_exact`/`geom_public`, `read_exact_geo`, tarmoqqa snap, repor rate limit |
| `EXTERNAL` | 4 | shifrlash, GDPR, saqlash lokalizatsiyasi, ISO 27001 |
| `ABSENT` | 3 | **MFA**, **ommaviy API da rate limit**, **mahalla reid tekshiruvi** |
| `VACUOUS` | 2 | sessiya/parol siyosati, PCI DSS |
| `MISSTATED` | 1 | `tg_id` pseudonimligi |
| `UNDEFENDED` | 0 | (qulflar shu runda yozildi) |

`VACUOUS` **xavfsiz degani emas**: parol siyosati o'rnini bosgan
xossalar boshqa nom ostida turadi (`MIN_TOKEN_LENGTH`,
`hmac.compare_digest`, sozlanmagan holat → `403`) va hujjat ularni
atamaydi. `VACUOUS` va `EXTERNAL` hisobotni yiqitmaydi (67-run sababi),
qolgan uchtasi yiqitadi — `trustworthy` ataylab qattiq.

## Ro'yxat hujjatdan keladi

61-run sabog'i: qo'lda ko'chirilgan jadval o'z nusxasini o'lchaydi.
Bu yerda `SPEC_TABLE` yo'q, langar ikki xil:

* `doc_item` — §20 nasridagi element yoki jadval yorlig'i;
* `nfr` — BRD ning «Безопасность» NFR identifikatori (§20 ularni
  «полностью» meros qiladi, lekin matni §20 da yo'q).

**Muhim tafsilot:** jadvalning uchta katagi `;` bilan **ikkita
mustaqil da'voni** bir qatorga qo'ygan — GDPR, ПДн, Геоданные. Ular
alohida qator bo'lishi kerak, aks holda ikkinchi da'vo birinchisining
orqasida yashirinadi, va aynan shunday yashiringan edi: «ПДн не
собираются» rost, «псевдонимизированный вид» esa yo'q, va bitta qator
ikkalasini ham «bajarilgan» deb ko'rsatardi. Test har katak uchun
`;` lar sonini sanaydi va shuncha qator talab qiladi.

## Sonlar

§20 riskni «в малой махалле точность **50 м**» ga qarab baholaydi.
Amaldagi ommaviy nuqta esa r9 katakchasidan quriladi — `05` «≈ 174 m»
deydi, `h3` 4.5.0 esa 200.8 m beradi (60-run ning ochiq savoli). Ya'ni
kafolat hujjat kutganidan **kuchli**, lekin ikkala son ham bir-biriga
mos emas. Test ikkalasini ham hujjatlardan parse qiladi va `h3` ga
bog'lanmaydi — aks holda kutubxona versiyasi testni boshqarardi.

## Mutatsiya

20 mutatsiya, **0 survivor** — lekin yo'l-yo'lakay **uchta survivor
topildi va tuzatildi**:

1. `trustworthy=not (absent or undefended or misstated)` →
   `not absent` **omon qoldi**: bugungi reyestrda `ABSENT` bor, ya'ni
   javob o'zgarmasdi. Tuzatildi — tekshiruv endi sun'iy reyestrda
   (bitta ochilmagan qator + faqat yashillar) o'tkaziladi.
2. `NAMED_ONLY` uchun izoh uzunligi talabi o'lchanmasdi.
3. ПДн detektori registrga bog'liq emasdi — `Username` deb yozilgan
   ustun ko'rinmay qolardi.

Beshtasi **hujjatlarga** qo'llandi (nasrdan element o'chirish, `;` ni
`.` ga almashtirish, `50 м` → `30 м`, BRD dan NFR-S-03 ni o'chirish,
ISO qatoriga `;` qo'shish) — hammasi ushlandi, ya'ni parse haqiqiy.

## Natija

* `sveta/app/admin/security.py` — yangi toza modul (bazasiz,
  `settings` siz, FastAPI siz)
* `sveta/tests/test_security_posture_contract.py` — 39 test
* **1833 passed** (+39), 1 skipped, `requires_db` 231 (o'zgarmadi)
* `ruff check` toza, migratsiyasiz

## 👤 To'rtta savol

1. **MFA.** BRD NFR-S-01 «Обязательно», amalda bitta omil
   (`X-Admin-Token`, muddatsiz, qurilmaga bog'lanmagan). Ochiq qarz
   bo'lib turadimi yoki E12 dan oldin kerakmi?
2. **`tg_id` pseudonimligi.** §20 ni «идентификатор не покидает
   систему» deb tahrirlash (bugungi haqiqat) yoki pepper li
   `tg_id_hash` ustuni qo'shish (migratsiya + sirni saqlash joyi)?
3. **Ommaviy API da rate limit.** Ilovada (middleware) yoki proxy da
   (nginx `limit_req`)? Ikkinchisi arzon, lekin `05` §7 da qayd
   etilishi kerak, aks holda joylashtirishda unutiladi.
4. **OQ-04 va «50 м».** Mahalla darajasi E17 ga bog'liq; hujjatning
   soni esa hozirdan eskirgan.

## Keyingi nomzodlar

* `01` §17 «Data Model» / §18 «Integrations» — tegilmagan bo'lim
  qolganini tekshirish (§19 va §20 bugun yopildi);
* `GET /api/v1/admin/monitoring` — endi **oltita** reyestr vitrinasiz
  turibdi (gates, measures, dashboards, acceptance, monitoring,
  security), lekin u `05` §7.2 endpoint sathini tahrirlaydi.

## ♻️ Sandbox

**O'n uchinchi** marta tekin keldi: `/tmp/sv59` butun holda (104 paket
+ `ruff`), `$HOME` yana 100%. Retsept: **avval `/tmp` ni qidir**.
👤 `cleanup-sessions.ps1` ni har run oldidan yurgizing.

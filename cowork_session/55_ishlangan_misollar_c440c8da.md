# 55-sessiya — `06` §7 ishlangan misollar jadvali kontraktga bog'landi

**Sana:** 2026-08-09
**Sessiya:** `local_c440c8da-53cb-4a14-8686-24727b4d0625`
**Epic:** E5 (ko'ndalang, hujjat ↔ kod kontrakti)
**Natija:** yangi `sveta/tests/test_worked_examples_contract.py` (28 ta bazasiz
test funksiyasi, parametrlangani bilan ~39 ta ishga tushish).
**Kod o'zgartirilmadi.**
⚠️ Sandbox **yigirma oltinchi marta ketma-ket** yiqildi (INFRA-1).

---

## 1. Boshlanish

54-sessiya `INDEX.md` ga aniq nomzod qoldirgan edi: «`06` §7 ishlangan
misollar jadvali — sakkiz qator (`A_local`, `W`, `N_req`, natija) va ular
hech qayerdan o'qilmaydi». Ko'rsatma ham berilgan edi: **avval `06` §7 ni
va `tests/test_scale.py` ni to'liq o'qing**.

O'qildi: `06` §4.1–4.3, §5.1–5.4, §6, §7, §9; `app/clustering/confirmation.py`,
`scale.py`, `formulas.py`, `params.py`; `app/reports/sources.py`;
`tests/test_scale.py`, `tests/test_confirmation.py` (§7 qismi),
`tests/test_confidence_contract.py` va `tests/test_scale_ladder_contract.py`
(naqsh uchun).

**Nomzod tasdiqlandi.** `Grep` bo'yicha §7 ga havola qiladigan yagona joylar —
`test_confirmation.py:215–284` va `test_scale.py:129`. Ikkalasi ham sakkiz
qatorni **qo'lda ko'chirgan**: hujjatga bironta ham fayl yo'li orqali
havola yo'q. 54 ning savoli («bu artefakt buzilsa qaysi test qizil bo'ladi?»)
uchun javob — **hech qaysi**.

---

## 2. Nima uchun aynan §7

`06` ning boshqa bo'limlari har biri **o'z** formulasini beradi va 49–54
sessiyalar ularni birma-bir yopdi:

| Bo'lim | Kontrakt | Sessiya |
|---|---|---|
| §2 manba registri | `test_report_sources_contract.py` | 50 |
| §3 hudud statistikasi | `test_territory_stats_contract.py` | 51 |
| §5 masshtab narvoni | `test_scale_ladder_contract.py` | 52 |
| §4 tasdiqlash chegarasi | `test_confirmation_threshold_contract.py` | 53 |
| §6 `confidence` | `test_confidence_contract.py` | 54 |
| §9 konfiguratsiya | `test_config.py` | 49 |

§7 esa ularning **birgalikdagi** natijasini e'lon qiladi — bu `06` da yagona
shunday joy. Demak bo'limlar **orasidagi** siljish faqat shu yerda ko'rinadi.
Har bir bo'lim alohida to'g'ri qolib, ularning birikmasi buzilishi mumkin,
va aynan shu holatni oltita kontrakt ham ushlamaydi.

---

## 3. Topilgan jim artefaktlar

### 3.1 `W` ustuni `bot.weight = 1.0` ga bog'langan

To'rtta qator nasrda «N ta xabar» deydi va `W` ustunida aynan `N.0` yozilgan
(4-qator `5 → 5.0`, 5-qator `9 → 9.0`, 7-qator `18 → 18.0`, 8-qator
`35 → 35.0`). Bu faqat `06` §2 registrida `bot` ning og'irligi **aynan
`1.0`** bo'lgani uchun to'g'ri.

`bot.weight` `1.5` ga o'zgarsa to'rtta qator jimgina yolg'on bo'ladi.
50-sessiyaning registr kontrakti buni ko'rmaydi (u §2 ↔ `SOURCES` ni
solishtiradi, §7 ni emas), `test_confirmation.py` ham ko'rmaydi — u `W` ni
hujjatdan emas, o'zi yasagan `Evidence` ro'yxatidan oladi.

### 3.2 3-qator — yagona ❌ bo'lib ballga ko'ra ✅ bo'ladigan qator

`Mahalla aktivi + moderator` → `W = 5.0`, `N_req = 3`. Ball yetarli, lekin
`distinct_users = 2` va shuning uchun `pending`. Bu jadvalda §4.3 ning `∧`
bog'lovchisini ko'rsatadigan **yagona** misol: qolgan ikkita ❌ qator
(`W = 1.0 < 3` va `W = 5.0 < 7`) ballga ko'ra ham yiqiladi, ya'ni ular
konyunksiya haqida hech narsa isbotlamaydi.

Bundan tashqari `5.0 = 2.0 + 3.0` — §7 registrning `bot` dan boshqa
qatorlarini (`mahalla_active`, `moderator`) faqat shu yerda ishlatadi.

### 3.3 6-qatorning uchala `—` katagi

`| 6 | Rasmiy kanal e'loni | — | — | — | ✅ confirmed, official, darhol |`

Bu bo'sh katak emas, **§2.2 ning da'vosi**: rasmiy manba og'irlikli hisobda
umuman qatnashmaydi (`official.weight = 0.0`, `is_authoritative = True`).
U yerga son yozilishi §2.2 ni bekor qilardi va buni hech narsa sezmasdi.

Shu qatorning `official` so'zi ham qirra: u **qatlam** (`outages.layer`),
pog'ona emas. Uni `Scale` ga qo'shish `rank()` tartibini siljitib §8 ning
deeskalatsiya taqiqini buzardi.

### 3.4 7- va 8-qatorlarning nasridagi `22` va `800` — eng jim artefakt

«tumanda **22** faol user» va «tumanda **800** user» —
`guard.min_active_district = 30` to'sig'ini **ikki tomondan** qamrab oladi:
`22 < 30 ≤ 800`. Ikkala son ham **nasr** ichida, ustunda emas, ya'ni ularni
hech qanday hisob o'qimaydi.

To'siq `20` ga tushirilsa 7-qator «qamrov to'sig'i» misoli bo'lishdan
to'xtaydi — u `local` emas, `mahalla` bo'lardi — lekin jadval o'zgarmagani
uchun `test_scale.py:129` (u o'z `TerritoryFacts` ini yasaydi) yashil
qolaveradi. 49-ning §9 testi `30` ni biladi, lekin uning **misolga
tegishini** bilmaydi.

### 3.5 1-qatordagi `conf ≈ 87`

`06` ning **yagona** uchidan-uchiga `confidence` qiymati. 54-sessiya §6
formulasini yopdi, lekin uni hech qanday to'liq misolga ulamadi (o'sha
sessiya faylining o'zi «§7 ning ishlangan misollari ataylab
tekshirilmaydi — ular alohida bo'lim va o'z kontraktiga loyiq» deb yozgan).

Qatorning ikkinchi qirrasi: son (`87`) va so'z (`confirmed`) **bir qatorda**
turadi, ya'ni §6 ning `70` bandi ularni bog'laydi. Band siljisa ikki artefakt
ajraladi.

### 3.6 `A_local` qiymatlari §4.2 jadvalida umuman yo'q

§7: `{15, 20, 180, 400}`. §4.2: `{4, 12, 40, 100, 250, 900}`. **Kesishmaydi.**
Ya'ni §7 chegara formulasini 53-sessiya tekshirmagan nuqtalarda sinaydi va
shu bilan birga ikkala chegarani ham (`floor = 3`, `ceil = 8`) ko'radi.

---

## 4. Yozilgan test

`sveta/tests/test_worked_examples_contract.py`, 28 ta funksiya:

* **Shakl** — sakkiz qator, `#` ustuni `1..8` tartibi bilan (hujjat «Misol 7»
  deb havola qiladi, `test_scale.py:130` ham); yagona sonsiz qator; har
  qator `confirmed` yoki `pending` deydi.
* **§4.2** — har qatorning `N_req` i `required_score(A_local)` bilan qayta
  hisoblanadi; §4.2 jadvali bilan **kesishmaslik** talab qilinadi; pol va
  shift ikkalasi ham ko'riladi.
* **§2** — «N ta xabar» × `bot.weight` = `W`; ikkita og'ir manba yig'indisi;
  rasmiy qator og'irligi `0.0` va `is_authoritative`.
* **§4.3** — ❌ qatorlarning sabab iboralari `evaluate()` ning haqiqiy
  `reason` literallariga bog'lanadi (`inspect.getsource` orqali);
  `distinct_users = 1/2` ikkalasi `min_users` dan past; `spread < 50 m` dagi
  `50` — `spread.min_distance_m` ning o'zi.
* **§5** — masshtab so'zlari `Scale` a'zolari (yoki `official`, u narvonda
  **emas**); uchala pog'ona ham uchraydi; «4 ta katakcha» va «3 ta mahalla»
  o'z minimumlaridan yuqori; `22`/`800` to'siqni qamrab oladi.
* **§6** — jadvaldagi yagona `confidence` qiymati kod bilan ham, mustaqil
  qayta hisob bilan ham tenglashtiriladi; boshqa `freshness` pog'onasi
  boshqa son berishi; bandning to'g'ri i18n kaliti; qiymat band chekkasida
  emasligi.
* **Yaxlitlik** — jadval uchala bo'limning kesimini ham saqlab qolgani.

---

## 5. Qabul qilingan qarorlar

1. **`SPEC_ROWS = 8`, `SPEC_NUMERIC_ROWS = 7` — aynan.** Qator qo'shilishi
   yoki yo'qolishi ko'rinadigan qaror bo'lsin: `#` ustunining raqami
   `test_scale.py` dan havola qilinadi, o'rtadan qator olib tashlansa
   keyingilarning raqami siljiydi.
2. **`✅`/`❌` belgilari o'qilmaydi** — hujjatning o'z `confirmed`/`pending`
   so'zlari o'qiladi va ikkisidan **aynan bittasi** talab qilinadi
   (53-sessiyaning unicode sabog'i). Xuddi shunday `—` ham literal
   yozilmaydi: katakda **raqam bor-yo'qligi** o'lchanadi.
3. **`official` narvonga qo'shilmasligi alohida qulflandi** — `Scale` ning
   uch a'zosi va `is_authoritative()` ajratildi.
4. **`reason` literallari `inspect.getsource(evaluate)` dan olinadi**, qo'lda
   yozilgan ro'yxatdan emas — hujjat mavjud bo'lmagan sababni nomlasa
   ko'rinsin.
5. **Jadval parse qilish ajratgichdan (`|---`) boshlanadi** (51-sessiyaning
   sabog'i).
6. **`confidence` misoli `last_report_age_min = 0` bilan** hisoblanadi va
   bu tanlov alohida test bilan qulflanadi: boshqa uchala `freshness`
   pog'onasi boshqa son beradi, ya'ni `87` misolning «yangi hodisa» ekanini
   ham isbotlaydi.

## 6. Rad etilgan variantlar

* **`evaluate()` ni haqiqiy `Evidence` bilan chaqirish** — bu xulq-atvor,
  uning uyi `test_confirmation.py`. 49–54 naqshi saqlanadi: xulq-atvor
  testlari o'z joyida qoladi, kontrakt fayli **sonlar qayerdan kelgani** ni
  o'lchaydi.
* **`test_confirmation.py` ning §7 qismini olib tashlash** — u qo'lda
  yozilgan xulq-atvor testi va `test_golden_scenarios_contract.py:131,166,179`
  aynan o'sha funksiya nomlariga havola qiladi. Tegilmadi.
* **§7 ning `Vaziyat` ustunini to'liq parse qilish** (masalan «bitta
  uydan» → `spread`) — nasr erkin yozilgan, naqsh mo'rt bo'lardi. Faqat
  **sonli** iboralar olindi.
* **`bot.weight` ni `06` §7 ga chiqarish** — hujjatga tegadi, 👤.
* **`22`/`800` ni §9 jadvaliga izoh qilib qo'shish** — hujjatga tegadi, 👤.

---

## 7. Sandbox — INFRA-1, 26-marta

`mcp__workspace__bash` uch marta bir xil xato bilan yiqildi:

```
useradd failed: exit status 1: useradd: /etc/passwd.NNNNN: No space left on device
```

Uchinchi urinishdan keyin to'xtatildi (ko'rsatma bo'yicha). Demak:

* yangi fayl **ishga tushirilmagan** — barcha tasdiqlar qo'lda, hujjat va
  kodni yonma-yon o'qib bajarildi (`N_req` ustunining yettala qatori,
  `confidence = 87` ning ikkala hisobi, `freshness` pog'onalari, regexlarning
  har bir qatorga mosligi shu tarzda tekshirildi);
* 36–55 runlarning ~375 ta testi hech qachon ishlamagan.

👤 **Odamga:** `cleanup-sessions.ps1` — sandboxning sababi ehtimol C
diskdagi sessiya papkalari.

---

## 8. Keyingi run uchun

**Birinchi ish — butun `pytest` va `ruff check sveta`, yangi kod emas.**

**Yopilgan nomzodlar, qayta ochilmasin:** `06` §7 ishlangan misollar (55),
§6 `confidence` (54), §4.1–4.3 chegara (53), §5.1–5.4 narvon (52),
§3.1–3.2 hudud statistikasi (51), §2 manba registri (50), §9 konfiguratsiya
(49), `05` §8 fon vazifalari (45/49), `05` §7.2 endpoint sathi (48),
`05` §10 metrikalar (47), oltin ssenariylar (46), fon vazifalari registri
(45), konfiguratsiya parity (44), bildirishnoma domeni (43), `05` §2 DDL
ustunlari (43), i18n ikki yo'nalish (41, 42), `05` §2 DDL indekslari (40),
API `commit` (39), `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).

**Ochiq nomzodlar (taklif).** `06` ning yopilmagan bo'limlari qoldi:

* **§11 suiiste'molga qarshi himoya** — `06` ning xavfsizlik bo'limi.
  Avval `06` §11 ni va `app/reports/` dagi `velocity` / `abuse` kodini
  o'qing (`test_abuse_contract.py` 34-sessiyada yozilgan — u nimani
  yopganini aniqlang, takrorlamang).
* **§10 `reports.weight` ni qotirish** — «yozish paytida qotiriladi» qoidasi
  `confirmation.py:62` izohida bor, lekin qaysi kod yo'li uni bajarishi
  o'lchanmagan.
* **§12 ssenariylar ro'yxati** — 46-sessiya nomlarni bog'lagan; qolgani
  har ssenariyning **mazmuni** hujjatdagi bilan bir xilligi.

**Saboqlar (meros):**

* `Glob` ga **to'liq yo'l** bering (48).
* `PROGRESS.md` va `INDEX.md` ni `Grep -o` bilan **kichik oyna**
  (`.{0,150}`) so'rab o'qing; `Read` ularni ko'tarmaydi, `Edit` esa
  qatorning **qisqa boshini** almashtira oladi (50).
* Markdown jadvalini ajratgichdan (`|---`) keyin parse qiling (51).
* Bir bo'limning qoidasini ikkinchisiga ko'chirmang; naqshni ko'chirishdan
  oldin **maqsad qatorlarni sanang** (53).
* Nomzod izlaganda **formulani emas, jim buziladigan artefaktni** qidiring:
  «bu buzilsa qaysi test qizil bo'ladi?» — javob «hech qaysi» bo'lsa, nomzod
  o'sha (54).
* **Yangi saboq (55):** artefakt jadval **ustunida** emas, **nasrda** ham
  yashaydi. §7 ning `22` va `800` i to'siqni belgilaydi, lekin ular hech
  qanday hisobga kirmaydi va shuning uchun eng jim artefakt bo'lib chiqdi.
  Hujjatni o'qiyotganda «bu son qaysi ustunda?» emas, «bu son **nimani
  belgilaydi**?» deb so'rang.
* **Yana bir saboq (55):** misollar jadvali — bo'limlar **orasidagi**
  siljishni ushlaydigan yagona artefakt turi. Har bo'lim alohida to'g'ri
  qolib, ularning birikmasi buzilishi mumkin; buni faqat bir necha bo'limni
  bitta chaqiruvda ishlatadigan qator ko'rsatadi.

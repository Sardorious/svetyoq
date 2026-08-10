# 64-sessiya — E6 sweep: parametrning butun o'qi (`04` §E11)

**Sana:** 2026-08-10 · **Epic:** E6 (E11 ning asbobi) · **Natija:** ✅

---

## 1. Qayerdan boshlandi

63-run ikkita nomzod qoldirgan edi: E14-a vitrina sahifasi (E9-b odam
qaroriga bog'liq) yoki **E6 ustidagi sweep**. Birinchisi bloklangan,
shuning uchun ikkinchisi olindi.

Sandbox oltinchi marta ketma-ket tekin keldi: `/tmp/sv59` butun holda
qolgan (104 paket, `ruff` ham), `$HOME` esa yana 100%. Retsept
o'zgarmadi — **avval `/tmp` ni qidir**. Bazaviy yurish: 1523 passed.

## 2. Bo'shliq

62-run `tools/recluster.py` ga `--set`/`--params` qo'shdi va «**boshqa**
parametrda nima bo'lardi?» degan savolga javob berdi. `04` §E11 esa
boshqa savol so'raydi va mezoni ham boshqacha — «qayta hisoblashda
**barqaror** natija».

Bitta ssenariy «4 da boshqacha chiqdi» deydi. Sozlash uchun bu yetarli
emas: **qayerda** boshqacha chiqishini bilish kerak — o'q bo'ylab qaysi
qadamda natija o'zgaradi va qaysi oraliqda umuman qimirlamaydi. Va eng
muhimi, o'lchov asbobining o'zi barqarormi.

## 3. Nima yozildi

`--sweep kalit=q1,q2,…` — bitta bazaviy va har qiymat uchun bitta
**to'liq** yurish (narx qiymatlar soniga chiziqli). Bazaviy bir marta
yurgiziladi: oyna ham, xabarlar ham o'zgarmaydi, uni takrorlash o'sha
ishni bekorga qilish bo'lardi.

Uchta xulosa:

| Xulosa | Nimani aytadi |
|---|---|
| **burilish nuqtalari** | iz aynan shu qadamda o'zgardi — sozlash shu yerda |
| **plato** | ikki va undan ko'p qadam bir xil iz — bu oraliqda parametr hech narsani hal qilmaydi |
| **`tasdiqlangan` yo'nalishi** | `o'smaydi` / `kamaymaydi` / `o'zgarmaydi` / **`aralash`** — oxirgisi kutilmagan holat, kuzatuv sifatida chiqariladi, verdikt emas |

**Determinizm tekin tekshiriladi.** Ro'yxatda joriy (`region_config`)
qiymat bo'lsa, uning izi bazaviy yurishning izi bilan solishtiriladi —
bu `04` §E11 mezonining o'zi. Buzilsa asbob yangi `EXIT_UNSTABLE` (3)
bilan tugaydi. Alohida kod kerak, chunki bu yagona holat bo'lib, unda
hisobotning qolgan hamma qatori to'g'ri **ko'rinadi**, lekin birortasiga
ishonib bo'lmaydi. `None` («ro'yxatda joriy qiymat yo'q — tekshirilmadi»)
`False` bilan aralashtirilmaydi: aralashsa soxta signal bo'lardi.

## 4. Qabul qilingan qarorlar va sabablari

**Bitta yurishda bitta kalit.** Ikkita kalit beshtadan qiymat bilan 25 ta
to'liq qayta hisoblash beradi, va jadval farqning ikki sababdan qay biridan
kelganini ko'rsata olmaydi.

**`--set`/`--params` — fon, va u bazaviyga ham qo'llanadi.** Agar fon faqat
variantlarga qo'llansa, har ustundagi farqning ikkita sababi bo'lardi.
Sweep kaliti fonda ham turishi — **xato** (`EXIT_USAGE`), xuddi
`--sweep` + `--apply` kabi: sweep bir necha natija beradi va qaysi biri
tarixga yozilishini asbob hal qilmaydi.

**Qiymatlar o'sish tartibida saralanadi.** Plato ham, burilish nuqtasi ham
qo'shni qadamlarni solishtiradi — ya'ni ro'yxat **o'q** bo'lishi kerak,
tartibsiz to'plam emas. Hech narsa yashirilmaydi: jadval qiymatlarni o'zi
ko'rsatadi. Takrorlangan qiymat — xato, jim dedup emas: tashlab yuborilsa
jadvaldagi qatorlar soni so'ralganidan kam bo'lardi.

**`assemble_points` bazadan ajratildi.** `run_sweep` ning o'zi
`requires_db`, sweepning esa **hamma** xulosasi ikkita bayroqdan chiqadi
(`changed_from_baseline`, `changed_from_previous`) — ular Postgressiz ham
tekshirilishi kerak. Testdagi yordamchi ham o'sha funksiyani chaqiradi:
testda takrorlangan mantiq mutatsiyani o'tkazib yuborardi.

## 5. Mutatsiyalar — 22 ta, 5 tadan to'plamda

`git status --porcelain` har to'plamdan keyin toza chiqdi (60-running
qoidasi).

**Bitta survivor, va u haqiqiy bo'shliq ko'rsatdi.** `parse_sweep` dagi
bo'sh element tekshiruvi (`3,4,` — ortiqcha vergul) **ortiqcha** ekan:
bo'sh satr sonlar tekshiruvidan ham o'tmasdi. Ya'ni shart faqat
**xabarni** yaxshilaydi — «bo'sh qiymat berilgan» deydi, «son kutilgan
edi, `''` keldi» emas, va odam kalitni emas, verguli qidirishi kerakligini
tushunadi. Test endi xabarning o'zini qulflaydi (`match="bo'sh qiymat"`),
shu bilan shart o'z o'rnini oqladi.

Qolgan 21 mutatsiya ushlandi: saralashning yo'qolishi, `>= 2` → `>= 1`
(yakka qiymat plato bo'lib qolishi), o'q chekkasidagi oxirgi platoning
yopilmasligi, determinizm verdiktining teskari o'qilishi,
`kamaymaydi`/`o'smaydi` ning joy almashishi, fonning sweepga yetib
bormasligi, `EXIT_UNSTABLE` ning yo'qolishi va h.k.

## 6. Natija

- `pytest -m "not requires_db"` → **1574 passed, 1 skipped** (+51)
- `requires_db` → **221** (+4)
- `ruff check app tools tests alembic` — toza; tegilgan uchala fayl
  `ruff format` bo'yicha ham toza qoldirildi
- Migratsiya **yo'q**, sxema o'zgarmadi

## 7. Qoldirilgan savol

👤 **`sveta/tools/_mut.py`.** Mutatsiya harnessi vaqtinchalik fayl
sifatida yaratildi, keyin ma'lum bo'ldiki agent uni o'chira olmaydi:
`allow_cowork_file_delete` odam tasdig'ini kutadi (`CLAUDE.md` §1 —
rejalashtirilgan runda chaqirilmaydi), mountdagi `rm` esa
`Operation not permitted` beradi. Tashlab ketilmadi — hujjatlashtirilgan
asbobga aylantirildi (`finally` bilan mutatsiyani **albatta** qaytaradi —
60-running sabog'i). Qaror odamda: qoldirish, `tools/mutate.py` deb
nomlab README ga qo'shish, yoki o'chirish.

## 8. Keyingi nomzodlar

- E14 vitrinasi backendi (E9-b qaroriga bog'liq emas qismi);
- `03` va `01` bo'yicha kontrakt qatlami — 63-run ko'rsatgan edi:
  `05`/`06` to'liq qamralgan, lekin `03` §R1.2 kabi talablar
  tekshirilmagan holda «✅» ko'rinishi mumkin.

"""TZ §12 ning yagona hisoboti — poroglar erishuvchanmi.

§12 ni TZ **yagona majburiy** tekshiruv deb ataydi va butun §2 dan
oldinga qo'yadi. Uning ikkita yarmi bor va ular har xil manbadan
javob oladi:

| Yarmi | Savoli | Manbasi | Moduli |
|---|---|---|---|
| asosiy | §2.1 ning **odam** poroglari tarixda yig'ilganmi | tarix | `tzreach` |
| «Дополнительно» | §3 ning zona poroglari umuman yig'iladimi | reyestrlar | `tzcoverage` |

193- va 194-runlar ikkala modulni qurdi, lekin **chaqiruvchisiz**:
`grep` `app/` da ikkalasiga ham birorta murojaat topmaydi. O'lchov
asbobi chaqiruvchisiz — o'lchov emas, imkoniyat. Bu skript o'sha
chaqiruvchi: bitta buyruq, bitta hisobot, bitta chiqish kodi.

```
python -m tools.tz_check --region samarkand --since 2026-01-01 --min-episodes 10
python -m tools.tz_check --region samarkand --since 2026-01-01 --min-episodes 10 --json
```

## 🔴 Kesim sanasi javobni o'zgartirishi mumkin va buni **o'lchash** kerak

`tzreach.load()` butun tarix uchun **bitta** `account_created_before`
oladi, mahsulot esa uni har hodisada qaytadan hisoblaydi
(`now - reporter_min_account_age_min`, `clustering/service.py`).
Ya'ni tarixiy o'lchovda bu qiymatni tanlash — javobni tanlash:

* `until - yosh` (kech kesim) tarixning **boshidagi** hodisada
  mahsulot rad etgan akkauntlarni ham qabul qiladi → guvohlar
  ko'proq → poroglar **erishuvchanroq** ko'rinadi;
* `since - yosh` (erta kesim) esa aksincha — tarixning oxiridagi
  hodisada mahsulot qabul qilgan akkauntlarni rad etadi → poroglar
  **yuqoriroq** ko'rinadi.

Bittasini tanlab qo'yish §12 ni aynan o'zi so'ragan tomonga
og'dirardi: kech kesim «пороги не завышены» degan javobni jimgina
qulaylashtiradi. Shuning uchun skript o'lchovni **ikki marta**
yuritadi va ikkala javobni ham chop etadi. Ular bir xil bo'lsa —
kesim qaror qabul qilmagan, son dalil. Farq qilsa — son dalil emas,
**artefakt**, va bu `reach.cutoff_decides` topilmasi bilan
nomlanadi. Narxi — so'rovlar ikki barobar; §12 oflayn va umuman bir
marta yuritiladi («занимает день работы с выгрузкой»), shuning uchun
narx qabul qilinadi.

## 🔴 «O'lchanmadi» — «o'tdi» emas

`tzreach` bugungi bazada `UNKNOWN`/`NO_INDEPENDENT_TRUTH` qaytaradi
(mustaqil dalili bor hodisa yo'q), `tzcoverage` esa foydalanuvchisi
bor kvartal bo'lmasa `UNKNOWN` beradi. Ikkala holatda ham `levels` /
sonlar **bo'sh** — modullar sonlarni o'ylab topmaydi. Agar chiqish
kodi bunda `0` bo'lsa, «hech qanday topilma yo'q» bilan «hech narsa
o'lchanmadi» bir xil ko'rinardi — bu loyihada bir necha marta
uchragan mina (bo'sh jadval, bo'sh sukut, nol maxraj). Shuning uchun
alohida kod:

| Kod | Ma'nosi |
|---|---|
| `0` | ikkala yarmi ham o'lchandi, topilma yo'q |
| `1` | hisobot **qurilmadi** (mintaqa yo'q, sozlanmagan, argument xato) |
| `2` | o'lchandi va topilma bor — hisobotni o'qish shart |
| `3` | yarmi (yoki ikkalasi) **o'lchanmadi** |

Ustunlik `3 > 2 > 0`: «topilma bor» degan kod qolgan hamma narsa
o'lchandi degan ma'noni beradi, yarmi o'lchanmaganda esa bu ma'no
yolg'on bo'lardi.

## Nima yozilmaydi

Skript **hech narsa yozmaydi** — na bazaga, na `region_config` ga.
§12 ishlab chiqishdan **oldingi** tekshiruv: uning javobi §7 ning
sonlarini o'zgartirishi mumkin, lekin o'zgartirishni odam
`seed_tz_config` orqali qiladi va u `config_journal` da ko'rinadi.
Avtomatik tuzatish o'lchovni o'z natijasiga bog'lardi.

## Yetkazish bazadan ajratilgan (209-run)

Skriptning yo'li to'rt qismga bo'lingan va ulardan **bittasi**
bazaga bog'liq:

| Qism | Nima qiladi | Bazaga bog'liqmi |
|---|---|---|
| `plan()` | argumentlar → `Invocation`, yoki xato | yo'q |
| `run()` | mintaqa, sozlama, `collect()` | **ha** |
| `finish()`/`deliver()` | hisobot + bayroq → matn va kod | yo'q |
| `emit()` | yagona `print` va kodni qaytarish | yo'q |

Sabab: sandboxda baza yo'q, ya'ni `run()` ning ichiga qo'yilgan har
qanday **qaror** o'lchovsiz qoladi. 208-run gacha aynan shunday edi
— `--json` bayrog'ini o'qish ham, chiqish kodini qaytarish ham
`session_scope()` dan keyingi qatorlarda turardi va butun to'plamda
o'sha ikki qatorni yuradigan birorta test yo'q edi. Endi `run()`
faqat o'qiydi va `Report | Delivery` qaytaradi; qolgan hamma narsa
toza funksiyalarda va fikstyura bilan o'lchanadi.

## 🔴 Maxrajning manbasi endi javobda (210-run)

`tzsource.BlockRegistry` §3 ning maxrajini quradi va uning izohi
chaqiruvchidan bitta narsani talab qiladi: «ular bo'sh emasligini
chaqiruvchi **ko'rishi** kerak, aks holda maxraj sababsiz
kichrayadi». 209-run gacha bu talab bajarilmagan edi. Ikkita son
(`blocks_unassigned`, `blocks_straddling`) hisobotning bitta
qatorida chop etilardi — maxrajsiz, ulushsiz va **hech qanday
topilmasiz**. Ya'ni kvartallarning yarmi tumanga tushmagan
mintaqada asbob `holat: clean (chiqish kodi 0)` deb yozardi.

Uch narsa qo'shildi: `source_line()` (ikkala sonning yonida
maxraji va ulushi), ikkita topilma (`coverage.blocks_unassigned`,
`coverage.blocks_straddling`) va `tzcoverage` tomonida
`Reason.ALL_BLOCKS_UNASSIGNED` — «kvartal yo'q» bilan «kvartal
bor, lekin biriktirilmagan» endi bitta token ostida turmaydi.

## 🔴 Bazaga bog'liq yarmi ham o'lchanadi (211-run)

209-run «sandboxda `run()` yurmaydi, ya'ni uning ichidagi har qanday
qaror o'lchovsiz bo'ladi» degan xulosa bilan yetkazishni tashqariga
chiqargan va qolgan qismni «uchta qatorlik SQL» deb yozgan edi. Xulosa
haqiqatning yarmi: o'sha uchta qator **atrofida** to'rtta qaror qolgan
edi va ularning birortasi ham hech qayerda o'lchanmasdi —

* qaysi kesim qaysi maydonga tushadi (`collect()`, yuqoridagi izoh);
* oyna va sozlamaning qaysi soni `tzreach.load()` ning qaysi
  parametriga boradi (`min_trust_score` ↔ `min_account_age_min` —
  ikkovi ham `settings` dan, ikkovi ham `int`);
* mintaqa **kodi** bilan qidiriladi va hisobotga ham kod tushadi,
  `id` emas;
* hisobot qurilmaganining ikkita sababi (mintaqa yo'q ↔ sozlanmagan)
  ajratilgan bo'lib qoladimi.

O'lchov uchun baza kerak emas va `requires_db` ham kerak emas:
`session_scope()` ning o'rniga so'rovni **yozib oladigan** fikstyura
qo'yiladi, so'rovning o'zi esa matndan emas, bog'langan
parametrlaridan tekshiriladi. Bazani soxta javob bilan almashtirish
o'zi xavfli — javobni o'ylab topgan fikstyura hech narsani
o'lchamaydi; shuning uchun so'rov saqlanadi va da'vo unga ham
qo'yiladi.

Matn i18n katalogidan olinmaydi va olinmasligi kerak: §12
foydalanuvchiga chiqmaydi, u ishlab chiquvchining asbobi.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import tzcoverage, tzreach
from app.clustering.service import KIND_OUTAGE
from app.clustering.tzcount import Level
from app.core import tzconfig
from app.core.config import settings
from app.db.session import session_scope
from app.geo import cellfit
from app.geo import queries as geo_q
from app.geo.models import Region


class Status(StrEnum):
    """Hisobotning yakuniy holati. Chiqish kodi shundan olinadi."""

    #: Ikkala yarmi ham o'lchandi, topilma yo'q.
    CLEAN = "clean"
    #: O'lchandi va e'tibor talab qiladigan narsa topildi.
    FINDINGS = "findings"
    #: Kamida bitta yarmi o'lchanmadi — sonlar yo'q.
    UNMEASURED = "unmeasured"


#: Holat → chiqish kodi. `1` bu jadvalda **yo'q**: u hisobot umuman
#: qurilmagan holat, ya'ni holatning qiymati emas, uning yo'qligi.
EXIT_CODE: Mapping[Status, int] = {
    Status.CLEAN: 0,
    Status.FINDINGS: 2,
    Status.UNMEASURED: 3,
}

#: Argument yoki muhit xatosi.
EXIT_ERROR = 1

#: Qamrov oshib ketganining sababi → matn hisobotidagi yorlig'i.
#: Uchta sabab — uchta yorliq (199-run). Birinchisida odam
#: biriktirish bilan chegara reyestrini solishtiradi; qolgan
#: ikkitasida solishtiradigan narsa yo'q, lekin **qiladigan ishi
#: har xil**: `BAHOLANGAN` da poligonning o'zi yo'q (chegara
#: reyestri), `MARKAZ-BO`YICHA` da poligon bor va `overlap` sanog'i
#: yo'q (`h3` ning eksperimental API si). Ikkovini bitta yorliq
#: bilan chiqarish odamga qaysi ishni qilish kerakligini
#: aytmasdi (`tzcoverage.CapacityConflict` jadvali).
CONFLICT_LABEL: Mapping[tzcoverage.CapacityConflict, str] = {
    tzcoverage.CapacityConflict.NONE: "",
    tzcoverage.CapacityConflict.OUTSIDE_POLYGON: "POLIGONDAN-TASHQARI ",
    tzcoverage.CapacityConflict.DENOMINATOR_ESTIMATED: "MAXRAJ-BAHOLANGAN ",
    tzcoverage.CapacityConflict.DENOMINATOR_NOT_UPPER_BOUND: "MAXRAJ-MARKAZ-BO`YICHA ",
}

#: Maxrajning **ma'nosi** → matn hisobotidagi yorlig'i (200-run).
#: `CONFLICT_LABEL` dan ayri va uni almashtirmaydi: sabab faqat
#: `over_capacity` yonganda chiqadi, ya'ni qamrovi joyida bo'lgan
#: tumanda poligon umuman o'qilmagan bo'lsa ham yorliq bo'sh qolardi
#: va `kvartal 2/4` qatori o'lchangan `50 %` dek o'qilardi. Endi
#: sonning ma'nosi **har** qatorda turadi.
#: `None` — geometriya o'qilmagan (`blocks_estimated` ham `?`).
CONTAINMENT_LABEL: Mapping[cellfit.Containment | None, str] = {
    None: "maxraj: yo`q",
    cellfit.Containment.OVERLAP: "maxraj: sanalgan",
    cellfit.Containment.CENTER: "maxraj: markazdan",
    cellfit.Containment.ESTIMATE: "maxraj: yuzadan",
}

#: `minimum_decides` → matn hisobotidagi yorlig'i (201-run).
#:
#: 🔴 Ilgari verdikt `'eng-kam-son' if … else 'ulush'` edi va o'sha
#: satrda `share_part` ning **yorlig'i** ham `ulush` bo'lgan. Qator
#: `kerak 4 (ulush 4) ulush` deb chiqardi: birinchi `ulush` — sonning
#: nomi, ikkinchisi — «qarorni kim qabul qildi» degan **boshqa**
#: savolning javobi. Bir xil so'z ikki xil savolga javob berganda
#: qatorni na odam, na `grep` ajrata oladi va verdiktni o'lchaydigan
#: har qanday da'vo (`"ulush" in text`) sonning yorlig'i tufayli
#: o'z-o'zidan bajarilardi.
#:
#: Prefiks `CONTAINMENT_LABEL` nikiga o'xshash (`maxraj:` ↔ `qaror:`):
#: qatorning har bir bo'lagi qaysi savolga javob berayotganini o'zi
#: aytadi.
DECIDER_LABEL: Mapping[bool, str] = {
    False: "qaror: ulush",
    True: "qaror: eng-kam-son",
}

#: Shahar qamrovi birdan oshib ketganining yorlig'i (202-run).
#:
#: `CityReach.over_capacity` — foydalanuvchisi bor tumanlar reyestrda
#: borlaridan ko'p, ya'ni `qamrov` **birdan katta**. Yorliqsiz
#: `qamrov: 140%` qatori o'lchangan ulushdek o'qilardi, holbuki u
#: reyestrning nuqsoni haqidagi xabar. Bo'shligi oldingi bo'lakdan
#: ajratish uchun **oldinda** (`CONFLICT_LABEL` da esa keyinda):
#: yorliq ulushning **ma'nosini** o'zgartiradi, ya'ni o'sha sonning
#: yonida turishi kerak.
OVER_CAPACITY_LABEL: Mapping[bool, str] = {
    False: "",
    True: " REYESTRDAN-KO`P",
}

#: `LevelResult.looks_high` → matn hisobotidagi yorlig'i (203-run).
#:
#: 🔴 Ilgari daraja qatori `'YUQORI' if result.looks_high else 'ok'`
#: bilan tugardi va o'sha **bir xil** `ok` hisobotning pastida
#: `district_line()` da ham chiqadi (`'ok' if district.reachable`).
#: Ikkovi ikki xil savolga javob beradi: biri «§2.1 ning porogi
#: yuqorimi», ikkinchisi «tuman §3 ning porogiga yetadimi». Bitta
#: hisobotda bir xil so'z ikki xil savolga javob berganda
#: `"ok" in text` turidagi har qanday da'vo **o'z-o'zidan**
#: bajariladi: daraja verdiktini butunlay olib tashlagan mutant ham
#: omon qoladi, chunki `ok` ni tuman qatori qoldiradi. 201-run aynan
#: shu minani `ulush` so'zida topgan edi — bu uning ikkinchi nusxasi.
#:
#: Prefiks `maxraj:`/`qaror:` bilan bir xil naqshda: qatorning har
#: bo'lagi qaysi savolga javob berayotganini o'zi aytadi.
HIGH_LABEL: Mapping[bool, str] = {
    False: "porog: ok",
    True: "porog: YUQORI",
}

#: `levels` bo'sh bo'lgandagi yagona qator (203-run).
#:
#: Konstanta, chunki `render()` dan chiqarilgan yagona da'vo shu
#: matnni butun hisobotdan qidirish edi (`"sonlar yo'q" in text`) va
#: u qatorning **borligini** o'lchardi, uning `levels` ning
#: bo'shligidan kelganini emas.
NO_LEVELS_LINE = "    sonlar yo'q — o'lchanmadi"

#: `ReachPair.verdicts_differ` → matn hisobotidagi yorlig'i (204-run).
#:
#: 🔴 Ilgari qator `verdikt farqi {report.reach.verdicts_differ}` deb
#: chiqardi, ya'ni butun hisobotdagi yagona **Python literali**:
#: `True`/`False`. Qolgan hamma bayroq bu asbobda so'z bilan yoziladi
#: (`DECIDER_LABEL`, `HIGH_LABEL`, `OVER_CAPACITY_LABEL`,
#: `CONFLICT_LABEL`) va sababi bir xil — `False` qaysi savolga javob
#: berayotganini aytmaydi. Bu yerda u aldamchi ham edi: qator 🔴 bilan
#: boshlanib `verdikt farqi False` deb tugardi, holbuki o'sha holatda
#: 🔴 ni **darajalar** keltirib chiqargan bo'ladi.
DIFFER_LABEL: Mapping[bool, str] = {
    False: "verdikt: bir xil",
    True: "verdikt: FARQ",
}

#: Kesim qatorining uchta sarlavhasi (204-run).
#:
#: 🔴 Ilgari qator **faqat** `cutoff_decides` rost bo'lganda
#: chiqardi, ya'ni uning yo'qligi ikki xil narsani anglatardi:
#: «ikkala kesim ham o'lchandi va bir xil javob berdi» (o'lchangan,
#: quvontiradigan javob) va «ikkala kesim ham son bermadi, ya'ni
#: kesimning ta'siri umuman o'lchanmadi». Ikkinchisida §2.1 bo'limi
#: **jim** qolardi va jimlik birinchisidek o'qilardi. Bu loyihada
#: bir necha marta uchragan naqsh (bo'sh gistogramma, bo'sh maxraj,
#: bo'sh sukut) — `histogram_text()` ning `-` i bilan bir xil sabab.
CUTOFF_DECIDES_HEAD = "  🔴 javob kesimga bog'liq"
CUTOFF_STABLE_HEAD = "  kesim javobni o'zgartirmaydi"
CUTOFF_UNMEASURED_HEAD = "  kesimning ta'siri o'lchanmadi"

#: Ziddiyatli daraja yo'q — lekin **solishtirildi**.
NO_DISPUTED_LEVELS = "-"

#: Darajalarni umuman solishtirib bo'lmadi (204-run).
#:
#: 🔴 Ilgari ikkala holat ham `-` berardi. `levels_in_dispute` faqat
#: **ikkala** o'lchovda ham bor darajani solishtiradi, `UNKNOWN` da
#: esa `levels` bo'sh — ya'ni bir tomon o'lchanmagan bo'lsa ro'yxat
#: har doim bo'sh chiqadi va `darajalar: -` «hech bir daraja
#: qarshilik qilmadi» degan tinchlantiruvchi javobdek o'qilardi,
#: holbuki darajalar solishtirilmagan edi.
LEVELS_NOT_COMPARABLE = "solishtirib bo'lmadi"

#: `Status` → hisobotning oxirgi qatoridagi so'z (205-run).
#:
#: 🔴 `holat:` qatori asbobning **mashina o'qiydigan verdiktini**
#: olib yuradi (chiqish kodi shundan), lekin uning yagona so'zi
#: `Status.value` — `clean` / `findings` / `unmeasured` — ya'ni
#: ichki turning nomi. 204-run hisobotdagi oxirgi Python literalini
#: (`True`/`False`) olib tashlagan edi; bu — o'sha naqshning oxirgi
#: nusxasi. Muhimi shundaki, `clean` va `unmeasured` **qarama-qarshi**
#: javoblar (biri «hammasi o'lchandi va toza», ikkinchisi «o'lchov
#: bo'lmadi»), lekin ikkovi ham bir xil zerikarli inglizcha token
#: bilan chiqadi va o'zaro farqi faqat o'quvchining diqqatiga
#: qoladi.
#:
#: Barqaror token **qoladi** (uni `grep` qiladigan skript bor deb
#: hisoblanadi, `Finding.code` bilan bir xil qoida) — uning yoniga
#: so'z qo'shiladi.
#:
#: So'zlar ataylab `NO_FINDINGS_*` / `FINDINGS_*_HEAD` bilan bitta
#: so'zni ham baham ko'rmaydi: bu qator «hammasi o'lchandimi» degan
#: savolga javob beradi, topilmalar sarlavhasi esa «bu ro'yxat
#: to'liqmi» degan **boshqa** savolga. 201- va 203-runlar bir xil
#: so'z ikki savolga javob berganda matndan bo'lak qidiradigan
#: da'vo o'z-o'zidan bajarilishini ikki marta ko'rsatgan.
STATUS_LABEL: Mapping[Status, str] = {
    Status.CLEAN: "toza",
    Status.FINDINGS: "e'tibor talab qiladi",
    Status.UNMEASURED: "o'lchov tugallanmadi",
}

#: Topilmalar bloki: to'rt holat, to'rt qator (205-run).
#:
#: 🔴 Ilgari blok ikki holatni bilardi — ro'yxat yoki `topilma yo'q`.
#: Lekin `Report.findings` **o'lchanmagan yarmidan topilma
#: chiqarmaydi** (o'sha xossaning izohi), ya'ni bo'sh ro'yxat ikki
#: xil narsani anglatardi:
#:
#: * ikkala yarmi ham o'lchandi va hech narsa topilmadi — o'lchangan,
#:   quvontiradigan javob;
#: * yarmi son bermadi, shuning uchun topiladigan narsa ham yo'q edi
#:   — o'lchovning **yo'qligi**.
#:
#: Ikkovi bir xil `topilma yo'q` qatorini berardi. Bu 204-run ning
#: kesim sarlavhasi, 203-run ning bo'sh gistogrammasi va 196-run ning
#: bo'sh maxraji bilan **bir xil mina**: o'lchovning yo'qligi
#: o'lchangan javobga o'xshab ko'rinadi.
#:
#: 🔴 Ro'yxat **bo'sh bo'lmaganda** ham shakl jim edi: o'lchanmagan
#: yarmi bor hisobotda ro'yxat faqat o'lchangan yarmidan yig'iladi,
#: ya'ni u **to'liq emas** — lekin to'liq ro'yxat bilan belgima-belgi
#: bir xil chiqardi.
#:
#: To'liqlik `Report.findings_complete` dan olinadi, `Status` dan
#: **emas**: qamrov qarzi (`has_capacity_debt`) holatni `UNMEASURED`
#: qiladi, lekin ikkala yarmi ham o'lchangan bo'ladi va ro'yxat
#: to'liq qoladi (197-, 199-runlar). Holatga qarab yozgan mutant
#: aynan o'sha fikstyurada yiqiladi.
NO_FINDINGS_LINE = "  topilma yo'q — hammasi o'lchandi"
NO_FINDINGS_UNMEASURED_LINE = "  topilma yo'q — chunki o'lchanmagan yarmi topilma bermaydi"
FINDINGS_HEAD = "  topilmalar (ro'yxat to'liq):"
FINDINGS_PARTIAL_HEAD = "  topilmalar (yarmi o'lchanmadi, ro'yxat to'liq emas):"

#: Sarlavha blokining yorliqlari (206-run).
#:
#: 🔴 Blok argumentlarni qaytarib aytadi va aynan **shu** yetti qiymat
#: `--json` da ham bor. Ikkala tomon ham ularni o'z f-satrida
#: yasardi, ya'ni bitta o'lchovning ikkita mustaqil nusxasi bor edi va
#: hech narsa ularni solishtirmasdi: matn hisobotida `erta`/`kech`
#: kesimni almashtirgan (yoki bitta maydonni tashlab ketgan) mutant
#: `--json` ni to'g'ri qoldiradi va bitta ham da'vo yiqilmaydi. Ikkita
#: haqiqat — bu asbobda eng qimmat nuqson: §12 ning javobi qaysi
#: chiqishni o'qiganingga bog'liq bo'lib qolardi.
#:
#: Yechim `Report.arguments`: yagona jadval, `as_json()` uni
#: yoyadi, sarlavha qatorlari esa undan **kalit bo'yicha** o'qiydi.
#: Shuning uchun yorliqlar ham konstanta: qator faqat qiymatni emas,
#: uning qaysi savolga javob berayotganini ham aytadi.
#:
#: Yorliqlar bir-birining bo'lagi emas va har biri hisobotda **bir
#: marta** uchraydi (`: ` bilan birga) — 201-, 203- va 206-runlar
#: ko'rsatgan mina: bir xil so'z ikki savolga javob bersa, matndan
#: bo'lak qidiradigan da'vo o'z-o'zidan bajariladi.
TITLE_HEAD = "TZ §12"
WINDOW_LABEL = "oyna"
CUTOFF_WINDOW_LABEL = "akkaunt kesimi"
MIN_EPISODES_LABEL = "eng kam hodisa"

#: Kesim juftligining ikki tomonini nomlaydigan **yagona** ikki so'z.
#:
#: 🔴 Ular ilgari uch joyda alohida yozilgan edi: sarlavha blokida
#: (`erta … / kech …`) va `render()` da ikkita `reach_lines()`
#: chaqiruvining sarlavhasi sifatida (`"erta kesim"`, `"kech kesim"`).
#: Bitta joyda so'zni almashtirgan o'zgarish hisobotni **o'zi bilan
#: ziddiyatga** solardi: tepada `erta 2025-12-22` deb yozilib,
#: pastda o'sha kesimning sonlari `kech kesim` sarlavhasi ostida
#: chiqardi. Sarlavhalar shu sababdan so'zlardan **hosila**.
EARLY_WORD = "erta"
LATE_WORD = "kech"
EARLY_TITLE = f"{EARLY_WORD} kesim"
LATE_TITLE = f"{LATE_WORD} kesim"

#: Ikkala yarmining bo'lim sarlavhalari. Har biri o'z modulini nomlaydi
#: — hisobotni o'qiyotgan odam sonning qayerdan kelganini shu qatordan
#: biladi (modul izohidagi jadval bilan bir xil juftlik).
REACH_SECTION_HEAD = "§2.1 — poroglar tarixda yig'ilganmi (tzreach)"
COVERAGE_SECTION_HEAD = "§3 — zona poroglari umuman yig'ilishi mumkinmi (tzcoverage)"

#: §3 o'lchovining verdikt qatorining yorlig'i (206-run).
#:
#: 🔴 Qator ilgari `  verdikt: {verdict} ({reason})` edi va o'sha
#: **bir xil** `verdikt:` prefiksi hisobotda yana bir marta chiqadi —
#: `DIFFER_LABEL` da (`verdikt: bir xil` / `verdikt: FARQ`). Ikkovi
#: ikki xil savolga javob beradi: bu qator «reyestrlardan o'lchov
#: chiqdimi va nega yo'q», `DIFFER_LABEL` esa «ikkita kesimning
#: verdikti bir xilmi». `DECIDER_LABEL` ning `ulush` i (201-run) va
#: `HIGH_LABEL` ning `ok` i (203-run) bilan bir xil mina, uchinchi
#: nusxasi.
#:
#: `zona` — `COVERAGE_SECTION_HEAD` ning so'zi: qator o'zi turgan
#: bo'limni nomlaydi, `reach_head_line()` ning sarlavhasi
#: (`erta kesim: …`) bilan bir xil qoidada.
COVERAGE_HEAD_LABEL = "zona"

#: Bloklarni ajratadigan **yagona** qoida (207-run).
#:
#: 🔴 Bo'sh qator ilgari uch joyda alohida yozilgan edi: `render()`
#: ichidagi `["", REACH_SECTION_HEAD]`, `["", COVERAGE_SECTION_HEAD]`
#: va `findings_lines()` ning birinchi elementi. Bittasini olib
#: tashlagan mutant hisobotni **qisman** yopishtirib qo'yardi — bir
#: bo'lim ikkinchisining davomiga o'xshab qolardi — va uni faqat
#: o'sha bo'limni nomma-nom qidiradigan da'vo ushlardi.
#:
#: Endi ajratgich bitta joyda: bloklar `report_blocks()` da,
#: ular orasidagi bo'sh qator esa shu yerda. Shuning uchun blokning
#: **ichida** bo'sh qator bo'lishi mumkin emas — aks holda
#: `text.split(BLOCK_SEPARATOR)` hisobotni boshqacha bo'laklarga
#: bo'lardi va skript blok chegarasini topa olmasdi.
BLOCK_SEPARATOR = "\n\n"


@dataclass(frozen=True)
class Finding:
    """Bitta topilma — kodi va u tegishli bo'lgan narsa.

    `code` barqaror: hisobotni skript o'qishi mumkin. `subject`
    bo'sh bo'lishi mumkin (butun mintaqaga tegishli topilmalarda).
    """

    code: str
    subject: str = ""

    def __str__(self) -> str:
        return f"{self.code}:{self.subject}" if self.subject else self.code


@dataclass(frozen=True)
class Cutoffs:
    """Akkaunt yoshi kesimining ikkita chekkasi (modul izohi, birinchi 🔴)."""

    #: Konservativ: tarix boshidan yosh chegarasi olib tashlangan.
    early: datetime
    #: Erkin: tarix oxiridan.
    late: datetime
    #: Qaysi sondan yasalgani — hisobotda ko'rinsin.
    min_account_age_min: int


def cutoffs(since: datetime, until: datetime, *, min_account_age_min: int) -> Cutoffs:
    """Oynadan ikkita kesim sanasi. Toza: bazani ko'rmaydi.

    `until <= since` — xato, `ValueError`. Teskari oyna nol hodisa
    beradi va u `NO_HISTORY` ga o'xshab ko'rinardi, ya'ni argument
    xatosi ma'lumot haqidagi xulosaga aylanardi.
    """
    if until <= since:
        raise ValueError(
            f"oyna bo'sh yoki teskari: since={since.isoformat()} until={until.isoformat()}"
        )
    if min_account_age_min < 0:
        raise ValueError(f"akkaunt yoshi manfiy bo'lolmaydi: {min_account_age_min}")
    age = timedelta(minutes=min_account_age_min)
    return Cutoffs(early=since - age, late=until - age, min_account_age_min=min_account_age_min)


@dataclass(frozen=True)
class ReachPair:
    """Bitta tarix, ikkita kesim (modul izohi, birinchi 🔴)."""

    #: `Cutoffs.early` bilan o'lchangani.
    early: tzreach.Reachability
    #: `Cutoffs.late` bilan o'lchangani.
    late: tzreach.Reachability

    @property
    def verdicts_differ(self) -> bool:
        """Kesim o'lchovning **holatini** o'zgartirdimi."""
        return self.early.verdict is not self.late.verdict

    @property
    def levels_in_dispute(self) -> tuple[Level, ...]:
        """Kesim `looks_high` ni o'zgartirgan darajalar, §2.1 tartibida.

        Faqat **ikkala** o'lchov ham darajani ko'rgan holatda
        solishtiriladi: bir tomonda daraja umuman yo'q bo'lsa, farq
        ziddiyat emas, o'lchanmaganlik.
        """
        return tuple(
            level
            for level in tzreach.LEVEL_ORDER
            if level in self.early.levels
            and level in self.late.levels
            and self.early.levels[level].looks_high != self.late.levels[level].looks_high
        )

    @property
    def measured(self) -> bool:
        """Ikkala o'lchov ham sonlar berdimi."""
        return (
            self.early.verdict is tzreach.Verdict.MEASURED
            and self.late.verdict is tzreach.Verdict.MEASURED
        )

    @property
    def cutoff_decides(self) -> bool:
        """Javob kesim sanasiga bog'liqmi — ya'ni son dalil emasmi."""
        return self.verdicts_differ or bool(self.levels_in_dispute)


@dataclass(frozen=True)
class Report:
    """§12 ning ikkala yarmi bitta obyektda."""

    region: str
    since: datetime
    until: datetime
    cuts: Cutoffs
    min_episodes: int
    reach: ReachPair
    coverage: tzcoverage.Coverage

    @property
    def arguments(self) -> Mapping[str, object]:
        """Asbobga berilgan argumentlar — ikkala chiqishning **bitta** manbai.

        Bu maydonlar o'lchov emas: ular hisobotni qurgan buyruqni
        qaytarib aytadi (mintaqa, oyna, ikkita kesim sanasi, kesim
        yasalgan daqiqa va maxrajning eng kam kattaligi). Aynan
        shuning uchun ular ikkala chiqishda ham bor — matn sarlavhasi
        odam uchun, `--json` esa skript uchun.

        🔴 Ikkovi ilgari **mustaqil** yasalardi: `render()` ning
        sarlavha bloki o'z f-satrida, `as_json()` esa o'z lug'atida.
        Bitta o'lchovning ikkita nusxasi ikkita haqiqatga ajralishi
        mumkin edi va buni hech narsa o'lchamasdi — matndagi
        `erta`/`kech` ni almashtirgan mutant `--json` ni to'g'ri
        qoldirardi. Bu `as_json()` izohidagi qoidaning uchinchi
        qo'llanishi: shakl chaqiruvchida takrorlanmaydi.

        Kalitlar `--json` ning kalitlari: jadval bitta bo'lgani uchun
        yangi argument qo'shilsa u ikkala chiqishda **birga** paydo
        bo'ladi yoki hech qaysisida.
        """
        return {
            "region": self.region,
            "since": self.since.isoformat(),
            "until": self.until.isoformat(),
            "cutoff_early": self.cuts.early.isoformat(),
            "cutoff_late": self.cuts.late.isoformat(),
            "min_account_age_min": self.cuts.min_account_age_min,
            "min_episodes": self.min_episodes,
        }

    @property
    def coverage_measured(self) -> bool:
        return self.coverage.verdict is tzcoverage.Verdict.MEASURED

    @property
    def findings_complete(self) -> bool:
        """Ikkala yarmi ham topilma bera oldimi (205-run).

        `status is UNMEASURED` bilan **bir xil emas** va aynan shu
        farq uchun alohida xossa: qamrov qarzi (`has_capacity_debt`)
        holatni `UNMEASURED` qiladi, lekin o'sha holatda ikkala
        modul ham son beradi va `findings` ikkala yarmini ham to'liq
        yig'adi (197-, 199-runlar). Ro'yxatning to'liqligini holatdan
        o'qish o'sha hisobotda «yarmi o'lchanmadi» degan yolg'on
        yozardi.

        Teskarisi ham bor: `not measured` bo'lgan tarixdan `findings`
        baribir bitta topilma chiqarishi mumkin
        (`reach.cutoff_decides:verdict` — verdiktlarning farqi
        sonlarsiz ham ko'rinadi), ya'ni ro'yxat bo'sh bo'lmasligi
        uning to'liqligini bildirmaydi.
        """
        return self.reach.measured and self.coverage_measured

    @property
    def findings(self) -> tuple[Finding, ...]:
        """Topilmalar — barqaror tartibda (Т-3).

        **O'lchanmagan yarmidan topilma chiqmaydi.** `UNKNOWN` da
        modullar sonlarni bo'sh qoldiradi, bo'sh sonlardan xulosa
        chiqarish o'lchanmagan narsa haqida da'vo bo'lardi.

        Qoida **sonning o'ziga** tegishli, bo'limga emas: `UNKNOWN`
        bo'lgan yarmida ham o'lchangan son bo'lsa, u topilma beradi.
        Bunday ikkita joy bor va ikkovi ham ataylab qorovuldan
        tashqarida: `reach.cutoff_decides:verdict` (verdiktlarning
        farqi sonlarsiz ko'rinadi) va `coverage.blocks_*`
        (`tzsource` ning to'g'ridan-to'g'ri sanog'i, quyidagi izoh).
        """
        items: list[Finding] = []

        if self.reach.cutoff_decides:
            if self.reach.verdicts_differ:
                items.append(Finding("reach.cutoff_decides", "verdict"))
            items += [
                Finding("reach.cutoff_decides", level.value)
                for level in self.reach.levels_in_dispute
            ]
        if self.reach.measured:
            # Ikkala kesimda ham yuqori ko'ringan darajalar — ya'ni
            # xulosasi kesimga bog'liq bo'lmaganlari.
            both = [
                level
                for level in tzreach.LEVEL_ORDER
                if level in self.reach.early.levels
                and level in self.reach.late.levels
                and self.reach.early.levels[level].looks_high
                and self.reach.late.levels[level].looks_high
            ]
            items += [Finding("reach.level_looks_high", level.value) for level in both]

        if self.coverage_measured:
            city = self.coverage.city
            if self.coverage.looks_unreachable:
                items.append(Finding("coverage.city_mostly_unreachable"))
            if not city.reachable:
                items.append(Finding("coverage.city_unreachable"))
            if city.dead_weight > 0:
                items.append(Finding("coverage.dead_weight", str(city.dead_weight)))
            if city.minimum_decides:
                items.append(Finding("coverage.minimum_decides", "city"))
            for district in self.coverage.districts:
                if not district.reachable:
                    items.append(Finding("coverage.district_unreachable", district.district_id))
            for district in self.coverage.districts:
                if district.minimum_decides:
                    items.append(Finding("coverage.minimum_decides", district.district_id))
            for district_id in self.coverage.unknown_districts:
                items.append(Finding("coverage.unknown_district", district_id))
            # `over_capacity` ning uchta sababi uchta alohida nom
            # bilan chiqadi (197-run, 199-run): birinchisi odam
            # tekshiradigan topilma (biriktirish ↔ chegara reyestri
            # zid), qolgan ikkitasi o'lchov qarzi. Qarzlar ham
            # bir-biridan ajratiladi, chunki tuzatishlari har xil
            # joyda: poligon yo'q (chegara reyestri) yoki `overlap`
            # sanog'i yo'q (`h3` ning eksperimental API si). Bitta
            # nom ostida qolsa, hisobot topshiriqni aytmasdi va odam
            # jurnaldagi ikkita hodisani (`coverage.cells_estimated`,
            # `coverage.cells_not_upper_bound`) bu bayroq bilan
            # solishtira olmasdi.
            for district_id in self.coverage.districts_outside_polygon:
                items.append(Finding("coverage.outside_polygon", district_id))
            for district_id in self.coverage.districts_capacity_estimated:
                items.append(Finding("coverage.capacity_estimated", district_id))
            for district_id in self.coverage.districts_capacity_not_upper_bound:
                items.append(Finding("coverage.capacity_not_upper_bound", district_id))

        # 🔴 Maxrajning **manbasi** — o'lchov qilinganidan qat'i nazar
        # (210-run). Ikkala son ham `tzsource.BlockRegistry` dan
        # to'g'ridan-to'g'ri sanoq, ya'ni ular `coverage_measured`
        # yolg'on bo'lganda ham o'lchangan bo'ladi va `UNKNOWN`
        # javobning **sababi** aynan shular bo'lishi mumkin
        # (`Reason.ALL_BLOCKS_UNASSIGNED`). Ularni yuqoridagi qorovul
        # ostiga qo'yish topilmani eng kerak bo'lgan joyda jim
        # qilardi: hisobot «foydalanuvchisi bor kvartal yo'q» deb
        # yozib, kvartallar borligini va biriktirish ishlamayotganini
        # aytmasdi. Bu qoidaning avvaldan bor nusxasi —
        # `reach.cutoff_decides:verdict`: u ham `reach.measured`
        # talab qilmaydi, chunki verdiktlarning farqi sonlarsiz ham
        # ko'rinadi.
        #
        # Ikkovi **alohida** nom oladi: biriktirilmagan kvartal
        # maxrajdan butunlay chiqib ketadi (`05` §5.3 defekti, ishi
        # chegara reyestrida yoki biriktirishda), chegaradagi katak
        # esa maxrajda **qoladi** va faqat qaysi tumanga tushgani
        # tanlangan bo'ladi — ya'ni ikkinchisining ishi umuman
        # yo'q, u r9 ning o'lchamidan kelib chiqadigan fakt.
        if self.coverage.blocks_unassigned:
            items.append(
                Finding("coverage.blocks_unassigned", str(self.coverage.blocks_unassigned))
            )
        if self.coverage.blocks_straddling:
            items.append(
                Finding("coverage.blocks_straddling", str(self.coverage.blocks_straddling))
            )

        return tuple(items)

    @property
    def status(self) -> Status:
        """Yakuniy holat. `UNMEASURED` `FINDINGS` dan **kuchliroq**.

        Sabab modul izohida: «topilma bor» degan javob qolgan hamma
        narsa o'lchandi degan ma'noni beradi.

        Shu qoidaning uchinchi holati (197-run): qamrovi oshib ketgan,
        lekin maxraji ishonchli tepa chegara **bo'lmagan** tuman ham
        `UNMEASURED` beradi. Sonlar bor, verdikt `MEASURED`, lekin
        bayroqning sababi ajratilmagan — uni `FINDINGS` deb chiqarish
        «qolgan hammasi o'lchandi» degan yolg'on da'vo bo'lardi.

        Qarzning **ikkala** turi ham bir xil kuchda (199-run): holat
        «qaysi ish qolgan» degan savolga javob bermaydi, u faqat
        «hammasi o'lchandimi» ni so'raydi. Ikkalasini bu yerda
        birlashtirish uchun `has_capacity_debt` bor — ro'yxatlar esa
        ajratilgan qoladi (`tzcoverage` izohi).
        """
        if not self.reach.measured or not self.coverage_measured:
            return Status.UNMEASURED
        if self.coverage.has_capacity_debt:
            return Status.UNMEASURED
        return Status.FINDINGS if self.findings else Status.CLEAN

    @property
    def exit_code(self) -> int:
        return EXIT_CODE[self.status]


def _share(value: float | None) -> str:
    """Ulushni matnga. `None` — o'lchanmagan, `0 %` emas."""
    return "n/a" if value is None else f"{value * 100:.0f}%"


def histogram_text(histogram: Mapping[int, int]) -> str:
    """`best_people` → hodisalar soni; §12 ning «набирался один-два» i.

    Bo'sh lug'atda `-`, `[]` emas: bo'sh qavs «guvoh umuman
    yig'ilmagan» (`{0: 8}`) bilan «gistogramma yo'q» ni ajratmasdi,
    holbuki birinchisi o'lchangan javob, ikkinchisi o'lchovning
    yo'qligi. Bu loyihada bir necha marta uchragan naqsh (bo'sh
    jadval, bo'sh maxraj, bo'sh sukut).
    """
    if not histogram:
        return "-"
    return ", ".join(f"{people}→{count}" for people, count in sorted(histogram.items()))


def reach_head_line(title: str, reach: tzreach.Reachability) -> str:
    """O'lchovning sarlavha qatori: verdikt, sababi va ikkala maxraj."""
    return (
        f"  {title}: {reach.verdict.value} ({reach.reason.value}); "
        f"hodisa {reach.episodes_seen}, mustaqil {reach.episodes_independent}"
    )


def level_line(result: tzreach.LevelResult) -> str:
    """Bitta darajaning matn qatori (203-run).

    Qator `_reach_lines()` ichidagi olti bo'lakli f-satr edi va uni
    o'lchaydigan yagona yo'l butun hisobotni yasab undan bo'lak
    qidirish bo'lardi — 201-run `district_line()` da, 202-run
    `city_line()` da tuzatgan naqshning uchinchi nusxasi.

    🔴 Sonlarning **yorlig'i yo'q edi.** `house    3/8 (44%)` —
    juftlik `district_line()` ning `kvartal 5/9` iga, foiz esa
    `city_line()` ning `qamrov: 44%` iga belgima-belgi o'xshardi,
    holbuki uchalasi boshqa narsani sanaydi. `yetdi` va `guvohlar`
    shu sababdan: qatorning har bo'lagi o'z savolini aytadi
    (`maxraj:`/`qaror:` bilan bir xil qoida).

    Chekinish (`    `) ham shu yerda: u daraja qatorlarini
    `reach_head_line()` dan ajratadi, ya'ni shaklning bir qismi.
    """
    return (
        f"    {result.level.value:8} "
        f"yetdi {result.reached_in_first_window}/{result.episodes} "
        f"({_share(result.share)}) oynadan tashqari {result.window_only} "
        f"{HIGH_LABEL[result.looks_high]} "
        f"guvohlar [{histogram_text(result.people_histogram)}]"
    )


def reach_lines(title: str, reach: tzreach.Reachability) -> list[str]:
    """Bitta o'lchovning matni: sarlavha + darajalar yoki «o'lchanmadi»."""
    lines = [reach_head_line(title, reach)]
    if not reach.levels:
        lines.append(NO_LEVELS_LINE)
        return lines
    lines += [
        level_line(result)
        for result in (reach.level(level) for level in tzreach.LEVEL_ORDER)
        if result is not None
    ]
    return lines


def disputed_levels_text(pair: ReachPair) -> str:
    """Kesim ziddiyatiga tushgan darajalar ro'yxati (204-run).

    Uchta holat, uchta javob — va aynan shu uchtasi ilgari ikkitaga
    siqilgan edi (`LEVELS_NOT_COMPARABLE` izohi):

    * ikkala o'lchov ham son berdi va darajalar rozi — `-`;
    * ikkala o'lchov ham son berdi, ba'zilari rozi emas — nomlari,
      §2.1 tartibida;
    * bittasi son bermadi — solishtirish bo'lmadi.
    """
    if not pair.measured:
        return LEVELS_NOT_COMPARABLE
    if not pair.levels_in_dispute:
        return NO_DISPUTED_LEVELS
    return ", ".join(level.value for level in pair.levels_in_dispute)


def cutoff_head(pair: ReachPair) -> str:
    """Kesim qatorining sarlavhasi — uchta holatning qaysi biri.

    Tartib muhim: `cutoff_decides` birinchi tekshiriladi, chunki
    «erta o'lchandi, kech o'lchanmadi» ham kesimning qarori (javob
    kesim bilan yo'qoladi), ya'ni u `CUTOFF_UNMEASURED_HEAD` ga
    tushmasligi kerak. `CUTOFF_UNMEASURED_HEAD` faqat **ikkala**
    tomon ham son bermagan holat.
    """
    if pair.cutoff_decides:
        return CUTOFF_DECIDES_HEAD
    return CUTOFF_STABLE_HEAD if pair.measured else CUTOFF_UNMEASURED_HEAD


def cutoff_line(pair: ReachPair) -> str:
    """§2.1 bo'limining yakuniy qatori (204-run).

    Qator `render()` ning ichidagi **oxirgi** f-satr edi va uni
    o'lchaydigan birorta da'vo yo'q edi: `grep` testlarda
    `javob kesimga bog'liq` iborasiga bitta ham murojaat topmasdi.
    201-run `district_line()` da, 202-run `city_line()` da, 203-run
    `level_line()` da tuzatgan naqshning to'rtinchi va oxirgi nusxasi.

    Sabab shu qatorda eng qimmat: butun asbob ikkita kesimni ataylab
    yonma-yon o'lchaydi, va bu qator — o'sha o'lchovning **xulosasi**.
    U jim qolsa yoki noto'g'ri holatni aytsa, hisobotning qolgan
    hamma soni to'g'ri bo'lsa ham xulosa teskari o'qiladi.

    Verdikt bo'lagining o'z **sababi** (`Reason`) bu yerda
    takrorlanmaydi: sabab bitta o'lchovniki, ya'ni uning joyi
    `reach_head_line()` — har kesimning o'z qatorida.
    """
    return (
        f"{cutoff_head(pair)}: {DIFFER_LABEL[pair.verdicts_differ]}, "
        f"darajalar: {disputed_levels_text(pair)}"
    )


def district_line(district: tzcoverage.DistrictReach) -> str:
    """Bitta tumanning matn qatori (201-run).

    Qator `render()` ning ichida **to'qqiz bo'lakli bitta f-satr**
    edi, ya'ni uning shaklini o'lchaydigan yagona yo'l butun hisobotni
    yasab undan bo'lak qidirish bo'lardi. Bunday da'volar
    (`"maxraj: yuzadan" in text`) bo'lakning **borligini** o'lchaydi
    va uning **qaysi maydondan** kelganini o'lchamaydi: ikkita
    maydonni almashtirgan mutant hisobot matnida baribir o'sha
    so'zlarni qoldiradi. Shakl shu sababdan ayri funksiyada —
    `district_summary()` bilan bir xil qoida, faqat ikkinchi tomoni
    (mashina o'qiydigani modulda, odam o'qiydigani shu yerda).

    Bo'shliq bilan boshlanadigan chekinish ham shu yerda: u
    qatorlarni shahar satridan ajratadi, ya'ni matnning shaklining
    bir qismi. Uni `render()` da qoldirish shaklni yana ikki joyga
    bo'lardi.

    `code` bo'sh bo'lsa `?` — reyestrda yo'q tumanda `[]` bo'sh
    qavs bo'lardi va u «kodi bo'sh satr» bilan «kodi umuman yo'q» ni
    ajratmasdi.
    """
    estimated = "?" if district.blocks_estimated is None else district.blocks_estimated
    return (
        f"    {district.district_id} [{district.code or '?'}] "
        f"kvartal {district.blocks_with_users}/{estimated} "
        f"({CONTAINMENT_LABEL[district.containment]}) "
        f"kerak {district.need} (ulush {district.share_part}) "
        f"{DECIDER_LABEL[district.minimum_decides]} "
        f"{'' if district.known else 'REYESTRDA-YO`Q '}"
        f"{CONFLICT_LABEL[district.capacity_conflict]}"
        f"{'ok' if district.reachable else 'ERISHILMAS'}"
    )


def city_line(city: tzcoverage.CityReach) -> str:
    """Shahar darajasining erishuvchanlik qatori (202-run).

    🔴 **Qatorda `share_part` yo'q edi.** Tuman qatori 201-rundan beri
    `kerak N (ulush M) qaror: …` deb chiqadi, shahar satri esa faqat
    `kerak N` derdi. Ya'ni bir xil savolga (`qarorni kim qabul qildi`)
    ikkita daraja ikki xil to'liqlikda javob berardi va shaharniki
    hisobotdan umuman o'qilmasdi: javob faqat topilmalar
    ro'yxatidagi `coverage.minimum_decides:city` bayrog'ida, **sonsiz**
    qolardi. Bayroq esa qaysi sozlama qarorni qabul qilganini
    (`city_district_share` ↔ `city_district_min`) ayta oladi, lekin
    uni **qancha** o'zgartirish kerakligini ayta olmaydi.

    Qator `district_line()` bilan bir xil qoidada: shakl ayri
    funksiyada, ya'ni bo'lakning **borligi** emas, uning qaysi
    maydondan kelgani o'lchanadi. Chekinish ham shu yerda.
    """
    return (
        f"  tuman: reyestrda {city.districts_total}, foydalanuvchisi bor "
        f"{city.districts_with_users}, erishuvchan {city.districts_reachable}, "
        f"kerak {city.need} (ulush {city.share_part}) "
        f"{DECIDER_LABEL[city.minimum_decides]} "
        f"→ {'ok' if city.reachable else 'ERISHILMAS'}"
    )


def city_context_line(city: tzcoverage.CityReach) -> str:
    """Shahar darajasining ikkinchi qatori — sonning konteksti.

    Birinchi qatordan ayri, chunki **boshqa savolga** javob beradi:
    `city_line()` porog yig'iladimi deydi, bu qator esa javobning
    qanchalik ishonchli ekanini deydi (o'lik og'irlik va qamrov).

    🔴 Qatorda ilgari `Coverage` ning ikkita soni ham bor edi
    (`biriktirilmagan kvartal N, chegarada M`) va argument aynan
    shuning uchun butun `Coverage` bo'lgan. Ular 210-runda `source_line()`
    ga ko'chdi: o'sha sonlar shaharning **javobi** haqida emas,
    o'lchovning **kirishi** haqida. Argument shundan keyin
    `CityReach` bo'ldi — qatorning manbasi bitta bo'lsa, uni ikkita
    manbadan o'qiyotgandek ko'rsatish keyingi o'quvchini adashtirardi.

    Qamrov yorlig'i shu yerda: `over_capacity` ulushning **ma'nosini**
    o'zgartiradi (`OVER_CAPACITY_LABEL`).
    """
    return (
        f"  o'lik og'irlik: {city.dead_weight}; "
        f"qamrov: {_share(city.coverage)}{OVER_CAPACITY_LABEL[city.over_capacity]}"
    )


def source_line(coverage: tzcoverage.Coverage) -> str:
    """§3 maxrajining **manbasi**: nechta kvartal ko'rildi va nechtasi yo'qoldi.

    🔴 Ikkita son ilgari `city_context_line()` ning oxirida turardi
    (`biriktirilmagan kvartal 3, chegarada 1`) va u yerda ikkita
    nuqsonga ega edi.

    Birinchisi — **savol boshqa**. `city_context_line()` shaharning
    javobi qanchalik ishonchli ekanini aytadi (o'lik og'irlik,
    qamrov), bu ikkita son esa o'lchovga **umuman kirmagan**
    kvartallar haqida, ya'ni javobning emas, kirishning holati. Bir
    qatorda ikkita savolga javob berish bu asbobda bir necha marta
    tuzatilgan naqsh (201-, 203-, 206-runlar).

    Ikkinchisi qimmatroq — **son maxrajsiz** edi. `biriktirilmagan
    kvartal 3` beshtadan uchtami yoki besh mingdan uchtami degan
    savolga javob bermaydi, ya'ni odam uni o'qib hech qanday qaror
    qabul qila olmasdi. Endi har ikkala son ham o'z ulushi bilan
    chiqadi va **maxraji nomlanadi**: ular har xil (`ko'rilgan` ↔
    `biriktirilgan`, `Coverage.straddling_share` izohi), ya'ni
    maxrajni aytmaslik ikkita nuqsonni bitta shkalada o'qishga
    majbur qilardi.
    """
    return (
        f"  manba: ko'rilgan {coverage.blocks_seen}, "
        f"biriktirilgan {coverage.blocks_counted}; "
        f"biriktirilmagan {coverage.blocks_unassigned} "
        f"(ko'rilgandan {_share(coverage.unassigned_share)}), "
        f"chegarada {coverage.blocks_straddling} "
        f"(biriktirilgandan {_share(coverage.straddling_share)})"
    )


def status_line(report: Report) -> str:
    """Hisobotning verdikt qatori: token, so'z va chiqish kodi (205-run).

    Uchala bo'lak ham kerak va uchalasi boshqa o'quvchi uchun:
    `Status.value` — `grep` qiladigan skript uchun barqaror token,
    `STATUS_LABEL` — odam uchun so'z (`STATUS_LABEL` izohi), chiqish
    kodi esa asbobni chaqirgan `sh` uchun. Kod matnda ham chiqadi,
    chunki hisobot faylga yozilganda `$?` yo'qoladi.
    """
    return (
        f"holat: {report.status.value} — {STATUS_LABEL[report.status]} "
        f"(chiqish kodi {report.exit_code})"
    )


def finding_line(item: Finding) -> str:
    """Bitta topilmaning qatori. Chekinish va tire — shaklning qismi."""
    return f"  - {item}"


def findings_head(report: Report) -> str:
    """Topilmalar blokining sarlavhasi — to'rt holatning qaysi biri.

    Ikkita mustaqil savol ko'paytiriladi: ro'yxat bo'shmi va u
    to'liqmi (`NO_FINDINGS_LINE` izohi). Ikkinchisi `Status` dan
    emas, `Report.findings_complete` dan olinadi.
    """
    if report.findings:
        return FINDINGS_HEAD if report.findings_complete else FINDINGS_PARTIAL_HEAD
    return NO_FINDINGS_LINE if report.findings_complete else NO_FINDINGS_UNMEASURED_LINE


def findings_lines(report: Report) -> list[str]:
    """Hisobotning yakuniy bloki: verdikt qatori + topilmalar.

    Bo'sh ro'yxatda ham sarlavha chiqadi va **shu bilan tugaydi** —
    `reach_lines()` ning `NO_LEVELS_LINE` i bilan bir xil qoida.

    Blokni oldingi blokdan ajratadigan bo'sh qator bu ro'yxatda
    **yo'q** (207-run): u `BLOCK_SEPARATOR` ning ishi va uchala
    ajratgich bitta qoidadan keladi.
    """
    lines = [status_line(report), findings_head(report)]
    lines += [finding_line(item) for item in report.findings]
    return lines


def title_line(report: Report) -> str:
    """Hisobotning birinchi qatori — qaysi tekshiruv va qaysi mintaqa."""
    return f"{TITLE_HEAD} — {report.arguments['region']}"


def window_line(report: Report) -> str:
    """Tarix oynasining ikkita chekkasi (`since` … `until`)."""
    args = report.arguments
    return f"{WINDOW_LABEL}: {args['since']} … {args['until']}"


def cutoff_window_line(report: Report) -> str:
    """Ikkita kesim sanasi va ular yasalgan daqiqa.

    So'zlar `EARLY_WORD`/`LATE_WORD` dan: §2.1 bo'limining
    sarlavhalari ham o'shalardan yasaladi, ya'ni tepadagi sana bilan
    pastdagi sonlar bir xil nomni oladi.
    """
    args = report.arguments
    return (
        f"{CUTOFF_WINDOW_LABEL}: {EARLY_WORD} {args['cutoff_early']} / "
        f"{LATE_WORD} {args['cutoff_late']} "
        f"({args['min_account_age_min']} daqiqa)"
    )


def min_episodes_line(report: Report) -> str:
    """Maxrajning eng kam kattaligi — o'lchov emas, argument."""
    return f"{MIN_EPISODES_LABEL}: {report.arguments['min_episodes']}"


def header_lines(report: Report) -> list[str]:
    """Sarlavha bloki — `--json` ning argument kalitlari bilan bir xil manbadan.

    To'rt qator yetti qiymatni ko'rsatadi va ularning hammasi
    `Report.arguments` dan keladi (o'sha xossaning izohi, 206-run).
    Blok o'lchov emas: uning vazifasi hisobotni **qaytadan yasab
    bo'ladigan** qilish — qaysi buyruq shu sonlarni chiqargani
    qog'ozda qolsin.
    """
    return [
        title_line(report),
        window_line(report),
        cutoff_window_line(report),
        min_episodes_line(report),
    ]


def coverage_head_line(coverage: tzcoverage.Coverage) -> str:
    """§3 o'lchovining sarlavha qatori — `reach_head_line()` ning juftligi.

    🔴 Qator `render()` ning ichidagi **oxirgi o'lchov f-satri** edi:
    205-run «o'lchov haqidagi birorta f-satr qolmadi» deb yozgan,
    lekin bu qator `coverage.verdict` va `coverage.reason` ni —
    ya'ni §3 ning butun yarmi haqidagi xulosani — o'lchagan va uni
    ayri funksiya sifatida hech narsa qulflamagan edi.

    🔴 Yorlig'i ham `DIFFER_LABEL` bilan bir xil so'z edi
    (`COVERAGE_HEAD_LABEL` izohi).

    Sonlar bu qatorda yo'q va bo'lmasligi kerak: §2.1 da maxrajlar
    `reach_head_line()` da turadi, chunki ular bitta o'lchovniki;
    §3 ning sonlari esa darajalarga bo'lingan va o'z qatorlarida
    (`city_line()`, `city_context_line()`, `district_line()`).
    """
    return f"  {COVERAGE_HEAD_LABEL}: {coverage.verdict.value} ({coverage.reason.value})"


def reach_block(report: Report) -> list[str]:
    """§2.1 bloki: sarlavha, ikkala kesimning qatorlari va ular haqidagi xulosa.

    `cutoff_line()` blokning **oxirgi** qatori: xulosa ikkita
    o'lchovga tegishli, ya'ni u shu blokni yopadi va §3 ni ochmaydi
    (204-run). Kesim sarlavhalari `EARLY_TITLE`/`LATE_TITLE` —
    sarlavha blokidagi sanalar bilan bir xil so'zlardan (206-run).
    """
    lines = [REACH_SECTION_HEAD]
    lines += reach_lines(EARLY_TITLE, report.reach.early)
    lines += reach_lines(LATE_TITLE, report.reach.late)
    lines.append(cutoff_line(report.reach))
    return lines


def coverage_block(report: Report) -> list[str]:
    """§3 bloki: sarlavha, verdikt, maxrajning manbasi, shahar, keyin tumanlar.

    Tartib kengdan torga: verdikt butun yarmiga, `source_line()`
    butun mintaqaning **kirishiga**, shahar qatorlari butun shaharga,
    tuman qatorlari esa bittadan tumanga tegishli. Tumanlar shu
    sababdan blokni yopadi — ular sonining o'zgarishi boshqa
    qatorlarning joyini surmaydi.

    Manba qatori verdiktdan **keyin** va shahardan **oldin** (210-run):
    u o'lchovga qancha kvartal kirgani va qanchasi yo'qolganini
    aytadi, ya'ni pastdagi hamma sonning maxrajini nomlaydi. Uni
    shahardan keyin qo'ygan mutant o'quvchiga avval javobni, keyin
    javob nimadan yasalganini ko'rsatardi.
    """
    coverage = report.coverage
    lines = [
        COVERAGE_SECTION_HEAD,
        coverage_head_line(coverage),
        source_line(coverage),
        city_line(coverage.city),
        city_context_line(coverage.city),
    ]
    lines += [district_line(district) for district in coverage.districts]
    return lines


def report_blocks(report: Report) -> list[list[str]]:
    """Hisobotning skeleti — to'rt blok, tartibda (207-run).

    🔴 Tartib `render()` ning **ichida** yozilgan edi va uni bitta
    joyda hech narsa qulflamasdi: bo'limni butunlay tashlab ketgan
    yoki ikkitasini almashtirgan mutantni faqat o'sha bo'limni
    nomma-nom qidiradigan da'volar qisman ushlardi. Bu — 201–206
    runlarning naqshining oxirgi nusxasi: shaklning bir bo'lagi
    o'lchanmagan joyda qolgan.

    To'rttasi to'rtta savolga javob beradi va shu tartibda:

    1. `header_lines()` — **qaysi buyruq** shu sonlarni chiqardi;
    2. `reach_block()` — §2.1, tarixda yig'ilganmi;
    3. `coverage_block()` — §3, umuman yig'ilishi mumkinmi;
    4. `findings_lines()` — yakuniy verdikt va topilmalar.

    Blok hech qachon **yo'qolmaydi**: o'lchanmagan yarmi ham,
    bo'sh tuman ro'yxati ham o'z qatorini chiqaradi (`NO_LEVELS_LINE`,
    `NO_FINDINGS_UNMEASURED_LINE`). Blokning yo'qligi o'quvchiga
    «bu savol berilmadi» deb ko'rinardi, holbuki javob — «o'lchanmadi».
    """
    return [
        header_lines(report),
        reach_block(report),
        coverage_block(report),
        findings_lines(report),
    ]


def render(report: Report) -> str:
    """Odam o'qiydigan hisobot. Toza: bazani ham, vaqtni ham ko'rmaydi.

    Bu funksiyada endi na f-satr, na tartib bor. Tuman qatorlari —
    `district_line()` (201-run); shahar satrlari —
    `city_line()`/`city_context_line()` (202-run); daraja qatorlari —
    `reach_lines()`/`level_line()` (203-run); kesim xulosasi —
    `cutoff_line()` (204-run); yakuniy blok — `findings_lines()`
    (205-run); sarlavha bloki — `header_lines()` va §3 ning verdikt
    qatori — `coverage_head_line()` (206-run); bloklarning tartibi —
    `report_blocks()` (207-run).

    Qolgani — bloklarni bo'sh qator bilan yopishtirish, ya'ni
    `BLOCK_SEPARATOR` ning yagona qoidasi.
    """
    return BLOCK_SEPARATOR.join(
        "\n".join(block) for block in report_blocks(report)
    )


def header_json(report: Report) -> Mapping[str, object]:
    """`--json` ning sarlavha kesimi: **qaysi buyruq** shu sonlarni chiqardi.

    `header_lines()` ning juftligi va **o'sha** jadvaldan
    (`Report.arguments`, 206-run). Kesim shu sababdan mustaqil
    funksiya emas — u jadvalning nusxasi, va nusxa bitta joyda
    yasaladi.
    """
    return dict(report.arguments)


def reach_json(report: Report) -> Mapping[str, object]:
    """`--json` ning §2.1 kesimi — `reach_block()` ning juftligi.

    To'rt kalit ikkita savolga javob beradi: ikkala kesimning
    sonlari (`tzreach.summary()` dan) va ular haqidagi xulosa
    (`cutoff_decides`, `levels_in_dispute`) — ya'ni matndagi
    `cutoff_line()` aytadigan narsa. Xulosa shu kesimda turadi va
    yakuniy kesimga ko'chmaydi: u ikkita **o'lchovga** tegishli,
    hisobotning verdiktiga emas (204-run, `cutoff_line()` blokning
    oxirgi qatori).
    """
    pair = report.reach
    return {
        "reach_early": tzreach.summary(pair.early),
        "reach_late": tzreach.summary(pair.late),
        "cutoff_decides": pair.cutoff_decides,
        "levels_in_dispute": [level.value for level in pair.levels_in_dispute],
    }


def coverage_json(report: Report) -> Mapping[str, object]:
    """`--json` ning §3 kesimi — `coverage_block()` ning juftligi.

    Bitta kalit, chunki §3 ning **butun** shakli modulniki:
    verdikt, sabab, shahar va tumanlar `tzcoverage.summary()` dan
    keladi (200-run). Bu yerda qator yasash matn hisoboti bilan
    JSON ni ikkita boshqa haqiqatga ajratardi.
    """
    return {"coverage": tzcoverage.summary(report.coverage)}


def findings_json(report: Report) -> Mapping[str, object]:
    """`--json` ning yakuniy kesimi — `findings_lines()` ning juftligi.

    Uchala kalit ham xulosa tomonida: topilmalar ro'yxati, holat
    tokeni va chiqish kodi. Kod matnda ham, JSON da ham bor va
    sababi `status_line()` niki — hisobot faylga yozilganda `$?`
    yo'qoladi.
    """
    return {
        "findings": [{"code": item.code, "subject": item.subject} for item in report.findings],
        "status": report.status.value,
        "exit_code": report.exit_code,
    }


def report_json_blocks(report: Report) -> list[Mapping[str, object]]:
    """Mashina o'qiydigan kesimning skeleti — to'rt bo'lak, `report_blocks()` tartibida.

    🔴 `as_json()` yagona yassi lug'at edi va uning kalitlari matn
    hisobotining **bloklari** bilan hech qayerda solishtirilmagan.
    207-run matn tomonini to'liq qulflagan, lekin ikkinchi chiqish
    o'sha o'lchovdan tashqarida qolgan edi: `--json` dan kalit
    tashlab ketgan mutant (`cutoff_decides`, `levels_in_dispute`)
    matn hisobotini butunlay to'g'ri qoldirardi va bitta ham da'vo
    yiqilmasdi. Hisobot ikkita chiqishga ega, ya'ni shaklning
    qulfi ham ikkita bo'lishi kerak.

    Bo'laklar bloklar bilan **bir xil tartibda** va bir xil to'rt
    savolga javob beradi (`report_blocks()` izohi). Shundan ikkita
    qoida chiqadi:

    1. **Bo'lak hech qachon bo'sh emas** — matnda bloki bor, JSON da
       kaliti yo'q savol o'quvchiga «bu savol berilmadi» degan
       yolg'on javob bo'lardi. Blokning yo'qolmasligi bilan bir xil
       qoida.
    2. **Kalit ikkita bo'lakka tegishli bo'lmaydi** — birlashtirish
       o'shanda bittasini jimgina yutardi va hisobot o'z sonini
       o'zi yo'qotardi.

    Ikkovi ham testda **literal** jadval bilan qulflanadi:
    o'lchanayotgan koddan olingan ro'yxat har doim rost javob
    berardi (`ARGUMENT_KEYS`, `BLOCK_COUNT` bilan bir xil qoida).
    """
    return [
        header_json(report),
        reach_json(report),
        coverage_json(report),
        findings_json(report),
    ]


def as_json(report: Report) -> Mapping[str, object]:
    """Mashina o'qiydigan hisobot — to'rt bo'lak bitta lug'atda.

    Ikkala yarmi ham **o'z modulining** `summary()` idan olinadi —
    shakl chaqiruvchida takrorlanmaydi. Tuman kesimi ham shu qoidadan
    keladi (200-run): `tzcoverage.summary()` ga `districts` qatorlari
    qo'shilgani uchun bu funksiyada bitta ham satr o'zgarmadi.
    Qatorni bu yerda yasash matn hisoboti bilan JSON ni ikkita
    boshqa haqiqatga ajratardi.

    Argument maydonlari ham shu qoidaga o'tdi (206-run): ular
    `Report.arguments` dan yoyiladi, matn sarlavhasi esa **o'sha**
    jadvaldan o'qiydi. Ilgari ikkovi mustaqil f-satr edi.

    Bu funksiyada endi na kalit, na tartib bor (208-run): u
    `report_json_blocks()` ni yopishtiradi, xuddi `render()` ning
    `BLOCK_SEPARATOR.join(...)` i kabi. Lug'at yassi qoladi —
    `--json` ni o'qiydigan skript uchun bo'laklar chegarasi kerak
    emas, u kalitni nomi bilan oladi; bo'laklar hisobotning
    **shakli** haqidagi qoida.
    """
    payload: dict[str, object] = {}
    for block in report_json_blocks(report):
        payload.update(block)
    return payload


@dataclass(frozen=True)
class Delivery:
    """Hisobotning `sh` ga **yetadigan** qismi: bitta matn va bitta chiqish kodi.

    🔴 209-run gacha yetkazish o'lchovdan tashqarida edi. 201–208
    runlar hisobotning ikkala chiqishini ham shakl tomonidan
    qulfladi, lekin ularning orasidagi chok — «`--json` bayrog'i
    qaysi chiqishni tanlaydi va chiqish kodi qanday qaytadi» —
    `run()` ning ichida, `session_scope()` dan **keyin** turardi.
    `run()` bazasiz chaqirilmaydi, ya'ni butun to'plamda o'sha ikki
    qatorni yuradigan birorta test yo'q edi: bayroqni teskarisiga
    burgan yoki har doim `0` qaytargan mutant 4997 testda omon
    qolardi va §12 ni skriptdan yuritgan odam **yashil** javob
    olardi.

    Ikkala maydon ham bitta obyektda va bitta joyda yasaladi
    (`deliver()`, `failure()`), chunki ular bir-birining ma'nosini
    aytadi: matn — javob, kod — o'sha javobning qisqartmasi. Ularni
    ikkita mustaqil `return` da qoldirish «bir qiymat, ikkita
    chiqish» minasining o'zi bo'lardi (206-run, `Report.arguments`).
    """

    text: str
    exit_code: int


#: Hisobot **qurilmagan** holatning uchta sababi. Uchalasi ham bitta
#: satr va `EXIT_ERROR` beradi, lekin matni har xil: odam qaysi
#: to'siqqa urilganini `$?` dan emas, shu satrdan biladi.
REGION_MISSING = "mintaqa topilmadi: {region}"
REGION_UNCONFIGURED = "mintaqa sozlanmagan ({region}): {reason}"
BAD_ARGUMENT = "argument xato: {reason}"
MIN_EPISODES_TOO_SMALL = "--min-episodes kamida 1 bo'lsin"


def failure(message: str) -> Delivery:
    """Hisobotsiz chiqish: bitta satr va `EXIT_ERROR`.

    `EXIT_CODE` jadvalidan **ataylab** o'tmaydi — `1` holatning
    qiymati emas, uning yo'qligi (modul izohidagi jadval).
    """
    return Delivery(text=message, exit_code=EXIT_ERROR)


def json_text(report: Report) -> str:
    """Mashina o'qiydigan chiqishning matni.

    `sort_keys=True` ataylab: `as_json()` bo'laklarni lug'atga
    qo'shadi, ya'ni kalitlarning tartibi bo'laklarning tartibidan
    keladi va u hisobotning shakli haqidagi qoida, chiqishning emas.
    Skript uchun barqaror alifbo tartibi `diff` ni o'qiladigan
    qiladi.
    """
    return json.dumps(as_json(report), ensure_ascii=False, indent=2, sort_keys=True)


def deliver(report: Report, *, as_json_output: bool) -> Delivery:
    """Hisobot + bayroq → yetkaziladigan chiqish.

    🔴 **Chiqish kodi bayroqdan mustaqil.** U shoxlarning ichida
    emas, shu yerda **bir marta** olinadi: `--json` javobning
    shaklini tanlaydi, javobning o'zini emas. Kodni ikkala shoxda
    alohida hisoblagan variant `--json` bilan boshqa javob
    beradigan asbob yasardi — matn hisobotini o'qigan odam va uni
    skriptdan yuritgan CI bir xil bazada ikki xil verdikt olardi.

    Shu sababdan bu funksiya `EXIT_ERROR` ni hech qachon
    qaytarmaydi: hisobot qo'lda bor, ya'ni u **qurilgan**.
    """
    text = json_text(report) if as_json_output else render(report)
    return Delivery(text=text, exit_code=report.exit_code)


def finish(outcome: Report | Delivery, *, as_json_output: bool) -> Delivery:
    """Bazadan kelgan natija → yetkaziladigan chiqish.

    `run()` ikkita narsa qaytarishi mumkin: hisobot yoki hisobot
    **qurilmaganini** aytadigan tayyor `Delivery` (mintaqa yo'q,
    sozlanmagan). Ikkinchisi shu yerda o'zgarmasdan o'tadi —
    `deliver()` esa faqat birinchisiga tegishli.

    🔴 Bu funksiya `run()` dan **ataylab** ajratilgan. Ilgari
    `deliver()` chaqiruvi `run()` ning oxirgi qatori edi, ya'ni
    «bayroq bu yerga qaysi qiymat bilan yetdi» degan savol faqat
    bazali chaqiruvda javob olardi: `as_json_output=True` ga
    qotirilgan mutant butun to'plamda omon qolardi. Endi bazaga
    bog'liq yagona funksiya `run()` va u shakl haqida hech narsa
    bilmaydi.
    """
    if isinstance(outcome, Delivery):
        return outcome
    return deliver(outcome, as_json_output=as_json_output)


def emit(delivery: Delivery) -> int:
    """Chiqishni chop etadi va kodini qaytaradi — yagona `print`.

    Skriptning butun chiqishi shu funksiyadan o'tadi (hisobot ham,
    xato satri ham). Sabab: kodni qaytarish bilan matnni chop etish
    har joyda takrorlansa, bittasini tashlab ketgan shox jimgina
    paydo bo'lardi — hisobot chop etiladi, `$?` esa `0` qoladi.
    """
    print(delivery.text)
    return delivery.exit_code


@dataclass(frozen=True)
class Invocation:
    """Argumentlardan yasalgan chaqiruv — `run()` ning yagona kirishi.

    `argparse.Namespace` bazaga bormaydigan yo'lda `run()` ga
    berilardi va shu tufayli «qaysi maydon qaysi parametrga
    tushadi» degan savol faqat bazali chaqiruvda javob olardi.
    Bu yerda u toza `plan()` ning natijasi, ya'ni o'lchanadi.
    """

    region_code: str
    since: datetime
    until: datetime
    min_episodes: int
    as_json_output: bool


def plan(
    args: argparse.Namespace,
    *,
    now: datetime,
    min_account_age_min: int,
) -> Invocation | Delivery:
    """Argumentlar → chaqiruv, yoki bazaga **bormasdan** to'xtaydigan xato.

    Toza: na soatni, na bazani ko'radi — `now` va yosh tashqaridan
    keladi. Shuning uchun «`--until` berilmasa hozir» qoidasi ham,
    oynaning to'g'riligi ham fikstyura bilan o'lchanadi.

    Tekshiruvlarning tartibi ahamiyatli: `--min-episodes` avval
    ko'riladi, chunki oynaning xatosi haqidagi xabar maxrajning
    xatosini yashirardi va odam ikkinchisini birinchisini
    tuzatgandan keyingina ko'rardi.
    """
    if args.min_episodes < 1:
        return failure(MIN_EPISODES_TOO_SMALL)
    try:
        since = moment(args.since)
        until = moment(args.until) if args.until else now
        cutoffs(since, until, min_account_age_min=min_account_age_min)
    except ValueError as exc:
        return failure(BAD_ARGUMENT.format(reason=exc))
    return Invocation(
        region_code=args.region,
        since=since,
        until=until,
        min_episodes=args.min_episodes,
        as_json_output=args.json,
    )


async def collect(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    region_code: str,
    since: datetime,
    until: datetime,
    min_episodes: int,
    params: tzconfig.TzParams,
    min_trust_score: int,
    min_account_age_min: int,
) -> Report:
    """Ikkala yarmini ham o'lchaydi. Yozmaydi.

    Tarix **ikki marta** o'qiladi (modul izohi, birinchi 🔴).

    🔴 O'lchov o'zini yasagan kesim bilan **kalitlanadi**, o'rni
    bilan emas (211-run). Ilgari ikkita natija ro'yxatga qo'yilib
    `ReachPair(early=pair[0], late=pair[1])` deb olinardi: ro'yxatning
    tartibi bilan maydonlarning nomi orasida hech qanday bog'liqlik
    yo'q edi, ya'ni ikkovini almashtirgan mutant butun to'plamda omon
    qolardi. Almashuv esa **jim** bo'lardi — hisobotning har ikkala
    qatori ham to'ldiriladi, `verdicts_differ` va `levels_in_dispute`
    ham bir xil qoladi (ikkovi ham simmetrik), faqat «erta» deb
    yozilgan qatorda kech kesimning javobi turardi. Aynan shu
    almashuv §12 ni o'zi so'ragan tomonga og'diradi: kech kesim
    poroglarni erishuvchanroq ko'rsatadi va uni «erta» yorlig'i ostida
    chop etish «пороги не завышены» degan xulosani dalilsiz
    qulaylashtirardi.

    Kalit ishonchli: `cutoffs()` `until <= since` ni xato deb rad
    etadi, ya'ni `early` va `late` hech qachon teng bo'lmaydi va
    lug'atda ikkita yozuv qoladi.
    """
    cuts = cutoffs(since, until, min_account_age_min=min_account_age_min)
    measured: dict[datetime, tzreach.Reachability] = {}
    for cutoff in (cuts.early, cuts.late):
        episodes = await tzreach.load(
            session,
            region_id=region_id,
            since=since,
            until=until,
            kind=KIND_OUTAGE,
            min_trust_score=min_trust_score,
            account_created_before=cutoff,
        )
        measured[cutoff] = tzreach.measure(episodes, params=params, min_episodes=min_episodes)
    coverage = await tzcoverage.load(session, region_id=region_id, params=params)
    return Report(
        region=region_code,
        since=since,
        until=until,
        cuts=cuts,
        min_episodes=min_episodes,
        reach=ReachPair(early=measured[cuts.early], late=measured[cuts.late]),
        coverage=coverage,
    )


def moment(raw: str) -> datetime:
    """ISO sana/vaqt → UTC. Zonasiz qiymat UTC deb o'qiladi.

    Zonasiz qiymatni mahalliy zonada o'qish oynani mashinaga bog'lardi
    va bir xil buyruq ikki mashinada boshqa son berardi.
    """
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


async def run(call: Invocation) -> Report | Delivery:
    """Bazadan o'qiydigan **yagona** qism. Shakl, tanlov va `print` bu yerda yo'q.

    Qaytaradigani ikki xil: hisobot, yoki uni qurib bo'lmaganini
    aytadigan tayyor `Delivery`. Chiqish kodi ham, `--json` bayrog'i
    ham bu funksiyaga umuman kirmaydi — shuning uchun sandboxda
    o'lchanmay qoladigan qism uchta qatorlik SQL bilan cheklandi
    (`finish()` izohi).
    """
    async with session_scope() as session:
        region = (
            await session.execute(select(Region).where(Region.code == call.region_code))
        ).scalar_one_or_none()
        if region is None:
            return failure(REGION_MISSING.format(region=call.region_code))

        values = await geo_q.load_region_config(session, region.id)
        try:
            params = tzconfig.params_from_mapping(values)
        except (tzconfig.ConfigMissingError, tzconfig.ConfigInvalidError) as exc:
            return failure(REGION_UNCONFIGURED.format(region=call.region_code, reason=exc))

        return await collect(
            session,
            region_id=region.id,
            region_code=call.region_code,
            since=call.since,
            until=call.until,
            min_episodes=call.min_episodes,
            params=params,
            min_trust_score=settings.reporter_min_trust_score,
            min_account_age_min=settings.reporter_min_account_age_min,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TZ §12 tekshiruvi (poroglar erishuvchanmi)")
    parser.add_argument("--region", required=True, help="mintaqa kodi, masalan `samarkand`")
    parser.add_argument("--since", required=True, help="oyna boshi, ISO (majburiy)")
    parser.add_argument("--until", default=None, help="oyna oxiri, ISO; sukut — hozir (UTC)")
    parser.add_argument(
        "--min-episodes",
        required=True,
        type=int,
        help="maxrajning eng kam kattaligi; sukut qiymati ataylab yo'q",
    )
    parser.add_argument("--json", action="store_true", help="mashina o'qiydigan chiqish")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Uchta qadam: argumentlarni o'qish, rejalashtirish, yurgizish.

    Soat va sozlama shu yerda o'qiladi va `plan()` ga **argument**
    bo'lib kiradi — shundan keyingi hamma narsa toza.
    """
    args = build_parser().parse_args(argv)
    outcome = plan(
        args,
        now=datetime.now(timezone.utc),
        min_account_age_min=settings.reporter_min_account_age_min,
    )
    if isinstance(outcome, Delivery):
        return emit(outcome)
    result = asyncio.run(run(outcome))
    return emit(finish(result, as_json_output=outcome.as_json_output))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

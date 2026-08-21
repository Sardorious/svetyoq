"""TZ §12 «Дополнительно» — §3 ning poroglari erishuvchanmi.

§12 ning asosiy yarmi 193-runda qurildi (`app/clustering/tzreach.py`):
u §2.1 ning **odam** poroglarini tarixda o'lchaydi. §12 ning oxirgi
jumlasi esa boshqa savol beradi va uni alohida ajratadi:

> «**Дополнительно:** сколько районов и кварталов в Самарканде и в
> скольких из них есть пользователи — от этого зависит §3.»

Bu modul aynan o'sha savolga javob beradi. Javob tarixga tayanmaydi —
u bugungi **reyestrlardan** hisoblanadi, ya'ni `tzreach` dan farqli
o'laroq Toshkent tarixi bo'lmasa ham bugun o'lchanadi.

## Nima uchun bu savol §3 uchun hayotiy

§3 ning ikkala qatorida ham ulushdan tashqari **eng kam son** bor
(«но не менее 3 кварталов», «но не менее 3 районов»). Ulush maxrajga
nisbatan o'sadi, eng kam son esa **mutlaq**. Ya'ni foydalanuvchisi bor
kvartallari uchtadan kam bo'lgan tuman §3 bo'yicha **hech qachon**
tasdiqlanmaydi — hamma kvartali tasdiqlansa ham. Bu aynan §3 ning o'zi
ogohlantirgan holat («иначе порог недостижим навсегда»), faqat u
ogohlantirishni maxraj tomonida yozgan va eng kam son tomonida
yozmagan.

## 🔴 Shaharning porogi tumanlarning **natijasidan** yig'iladi

Eng qimmat topilma shu va u ko'rinmas. `tzscale.city()` shaharning
maxrajiga foydalanuvchisi bor **har bir** tumanni qo'shadi, sanoqqa
esa faqat **tasdiqlangan** tumanni. Demak ikkita kvartali bor tuman:

* shaharning maxrajini **ko'taradi** (`has_users=True`),
* sanoqqa esa **hech qachon** kira olmaydi (`district_block_min`
  uni to'sadi).

Bunday tumanlar ko'p bo'lsa, shahar darajasi tumanlarning har biri
alohida erishuvchan ko'ringan holda ham erishilmas bo'lib qoladi.
Shuning uchun shaharning tepa chegarasi «foydalanuvchisi bor
tumanlar» emas, **o'zi erishuvchan** tumanlar soni; farqi
(`dead_weight`) — porogni ko'taradigan va uni hech qachon
to'ldirmaydigan tumanlar.

## 🔴 Ikkita maxraj bor va ular almashtirilmaydi

| Savol | Maxraj | Manbasi |
|---|---|---|
| §3 ning porogi | foydalanuvchisi bor zonalar | `reports` |
| §12 ning qamrovi | mavjud zonalar | `geo` reyestri |

Ularni almashtirish har ikki tomonga ham buzadi:

* qamrovni `blocks_with_users` dan hisoblash **har doim 100 %**
  beradi — maxraj sanoqning o'zidan olingan bo'lardi;
* §3 ning porogini `districts_total` dan hisoblash bo'sh tumanlarni
  maxrajga qo'shardi va §3 ning «считаем от 12» qoidasini bekor
  qilardi.

Shuning uchun geo reyestri bu yerda **faqat qamrovning** maxraji.
U §3 ning maxrajini hech qachon kichraytirmaydi: reyestrda yo'q,
lekin foydalanuvchisi bor tuman baribir §3 ning maxrajida qoladi va
`unknown_districts` da nomlanadi.

## 🔴 Ulush erishuvchanlikni hech qachon to'smaydi — eng kam son to'sadi

`share_need(n, share) <= n` har qanday `share <= 1` uchun, va
`tzconfig._check()` `Unit.SHARE` ni `(0, 1]` bilan qulflaydi. Ya'ni
«erishuvchanmi» degan savol tuzilmaviy ravishda `n >= minimum` ga
qisqaradi. Shunga qaramay `need` bu yerda **hisoblanadi**, taxmin
qilinmaydi: sozlama qorovuli bo'shatilsa (`share > 1`) javob jimgina
noto'g'ri bo'lib qolmasin.

Undan chiqadigan ikkinchi kuzatuv `minimum_decides` da: `0.40` va
uchta kvartal bilan ulush `n <= 5` bo'lgan **har qanday** tumanda
eng kam sondan past turadi (`n == 6..7` da ikkalasi teng, `n >= 8`
da ulush oshadi), ya'ni §3 ning ulushi kichik shaharda umuman
ishlamaydi va qarorni faqat mutlaq son qabul qiladi. §3 esa
«Абсолютное число в настройках не задавать, только долю и минимум»
deb yozgan — mutlaq son sozlamada emas, lekin u qaror qabul qiladi.

## 🔴 Qamrov birdan oshganining ikkita sababi bor va ular ajratiladi

196-run maxrajni sanaydigan qildi (`app.geo.cellfit`, `contain='overlap'`),
lekin **hamma hududda emas**: poligon o'qilmagan joyda maxraj baribir
yuzadan baholanadi. Ya'ni bitta `over_capacity` bayrog'i ikkita butunlay
boshqa narsani anglatardi — «kvartallar poligondan tashqarida» (topilma)
va «maxraj o'lchanmagan» (o'lchov qarzi). Ajratuvchi belgi — sonning
kattaligi emas, **ma'nosi** (`cellfit.Containment`), shuning uchun u
`RegionFacts.blocks_containment` da sonning yonida yuradi va
`DistrictReach.capacity_conflict` da javobga aylanadi.

## 🔴 Maxrajning **manbasi** ham nuqsonli bo'lishi mumkin

`blocks_unassigned` va `blocks_straddling` 194-rundan beri
`Coverage` da turadi, lekin ular faqat **son** edi: hisobot ularni
chop etardi, hech qanday nisbat bermasdi va hech qanday verdiktga
ta'sir qilmasdi. Uchta kvartal yo'qolgani beshtadan uchtami yoki
besh mingdan uchtami — javob hisobotdan o'qilmasdi.

Yo'qotishning ishorasi ham barqaror emas: tumandan tashlangan
kvartal uni **erishilmasroq** ko'rsatadi (`n >= minimum` da `n`
kichrayadi), butun tuman ro'yxatdan chiqib ketsa esa shahar
maxraji kichrayadi va shahar **erishuvchanroq** chiqadi. Ikkita
teskari xato bir-birini qisman bekor qiladi, ya'ni sonlarning
ko'rinishi tinch qoladi.

Shuning uchun 210-run uchta narsani qo'shdi: mustaqil maxraj
(`blocks_seen`), ikkita ulush (`unassigned_share` —
ko'rilganlardan, `straddling_share` — biriktirilganlardan) va
`Reason.ALL_BLOCKS_UNASSIGNED`. Verdiktni bu modul o'zgartirmaydi:
u faqat sonni va uning ma'nosini beradi, bayroqni esa `tz_check`
topilma qilib chiqaradi.

## Sanoq bu yerda qayta yozilmaydi

`need` `tzscale.share_need()` dan olinadi — §3 ni mahsulot qanday
hisoblasa, o'lchov ham shunday hisoblaydi. Formulani bu yerda
takrorlash oson edi va u §12 ni foydasiz qilardi: o'lchov mahsulot
qo'llaydigan qoidadan **boshqa** qoida haqida son berardi
(`tzreach` bilan bir xil sabab).

## Т-1 / Т-3 / Т-4

Modulda §7 ning soni yo'q — hammasi `TzParams` dan. Xulosa
(`looks_unreachable`) ham son bilan emas, ikkita **o'lchangan** sonni
solishtirish bilan. Soat umuman so'ralmaydi: mavjudlik vaqtga bog'liq
emas (`reports.queries.blocks_with_users` izohi).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import tzsource
from app.clustering.tzscale import share_need
from app.core.tzconfig import TzParams
from app.geo import cellfit
from app.geo import queries as geo_queries

# `SPEC` konstantasi ataylab **yo'q** — `tzreach` bilan bir xil sabab:
# `SPEC` li modul `app/admin/registries.py` indeksida qator bo'lishi
# shart, indeks esa hujjatning qatorlarini kod bilan solishtiradigan
# reyestrlarni ko'rsatadi. Bu modulda solishtiriladigan qator yo'q —
# u §3 ning bandlarini emas, **reyestrlarni** o'lchaydi, va javobi
# kodga emas, ma'lumotga bog'liq. §3 ning holati vitrinada allaqachon
# ko'rinadi (`tzscale.RULES`).


class Verdict(StrEnum):
    """O'lchovning holati."""

    #: O'lchash mumkin emas — sabab `Reason` da.
    UNKNOWN = "unknown"
    #: O'lchandi; sonlar `districts` va `city` da.
    MEASURED = "measured"


class Reason(StrEnum):
    """Nega o'lchanmadi. `MEASURED` da — `NONE`."""

    NONE = "none"
    #: Foydalanuvchisi bor kvartal umuman yo'q — §3 ning maxraji nol,
    #: ya'ni «erishuvchanmi» degan savol ma'nosiz. Bu **geo reyestri
    #: bo'shligidan boshqa** holat: chegaralar bo'lmasa ham
    #: foydalanuvchi bo'lishi mumkin.
    NO_BLOCKS_WITH_USERS = "no_blocks_with_users"
    #: Foydalanuvchisi bor kvartal **bor**, lekin ularning hech
    #: qaysisi tumanga biriktirilmagan (210-run).
    #:
    #: 🔴 Bu holat ilgari `NO_BLOCKS_WITH_USERS` bilan bir xil javob
    #: berardi va o'sha javob **yolg'on** edi: sabab «foydalanuvchisi
    #: bor kvartal yo'q» deb o'qiladi, holbuki kvartallar bor va
    #: hammasi `blocks_unassigned` da turibdi. Ya'ni ma'lumotning
    #: yo'qligi (o'lchash mumkin emas) `05` §5.3 ning defekti bilan
    #: (biriktirish ishlamayapti) bitta token ostida qolardi va
    #: hisobotni o'qigan odam geo tomonga umuman qaramasdi.
    #:
    #: Ajratuvchi belgi `Coverage.blocks_seen`: u sanoqning **o'zidan**
    #: olinmaydi (`blocks_counted + blocks_unassigned`), aks holda
    #: javob har doim «kvartal yo'q» bo'lardi — maxraj o'zi
    #: o'lchayotgan qoidadan kelib chiqardi.
    ALL_BLOCKS_UNASSIGNED = "all_blocks_unassigned"


class CapacityConflict(StrEnum):
    """Qamrov birdan oshganining **sababi** (197-run, 199-run).

    196-rungacha bayroq bitta edi va uni o'qishning ikki yo'li bor edi:
    «kvartallar poligondan tashqarida» yoki «maxraj noto'g'ri». 196-run
    maxrajni sanaydigan qildi (`app.geo.cellfit`) va bayroqni birinchi
    ma'noda o'qishga ruxsat berdi — **lekin hamma hududda emas**.
    Poligon o'qilmagan hududda maxraj baribir yuzadan baholanadi va
    mahalla o'lchamida haqiqiysidan bir necha barobar kichik chiqadi,
    ya'ni o'sha yerda bayroq eski, o'lchanmagan sababdan yonadi.

    Ikkovini bitta nom ostida qoldirish `tz_check` ni yolg'on aniqlik
    beradigan qilardi: hisobot «POLIGONDAN-TASHQARI» deb yozardi va
    odam biriktirish bilan chegara reyestrini solishtirgani ketardi,
    holbuki solishtiradigan narsa yo'q — shunchaki maxraj o'lchanmagan.

    **199-run uchinchi qiymatni qo'shdi.** 197-run ajratgan «o'lchov
    qarzi» ning o'zi ikkita **boshqa** qarzni bitta nom ostida
    yig'ardi va ularning tuzatishlari umuman har xil:

    | Qiymat | Nima yetishmaydi | Ish qayerda |
    |---|---|---|
    | `DENOMINATOR_ESTIMATED` | poligonning o'zi | chegara reyestri (`districts.geom`) |
    | `DENOMINATOR_NOT_UPPER_BOUND` | `overlap` sanog'i | `h3` ning eksperimental API si |

    Jurnal tomonida bu ajratma 198-runda allaqachon qilingan
    (`refresh_coverage` ning `coverage.cells_estimated` va
    `coverage.cells_not_upper_bound` hodisalari, ataylab **ikkita**
    hodisa). Hisobot esa ikkovini bitta yorliq bilan chiqarardi —
    ya'ni odam jurnalda ko'rgan ikkita qatorni hisobotdagi bitta
    bayroq bilan solishtira olmasdi va qaysi ishni qilish kerakligi
    hisobotdan **umuman** o'qilmasdi. Qiymatlar shu sababdan
    jurnalning hodisalari bilan bir xil atalgan.
    """

    #: Bayroq yonmagan.
    NONE = "none"
    #: Maxraj `overlap` bilan **sanalgan**, ya'ni hududning ichidagi
    #: har qanday xabarning katagi maxrajda bor
    #: (`cellfit.is_upper_bound_safe`). Shunga qaramay oshib ketgan —
    #: biriktirish (`tzsource`) bilan chegara reyestri (`geo`)
    #: bir-biriga zid. Bu **haqiqiy topilma**.
    OUTSIDE_POLYGON = "outside_polygon"
    #: Poligon umuman o'qilmagan — maxraj yuzadan baholangan
    #: (`cellfit.is_counted` `False`). Bu topilma emas, **o'lchov
    #: qarzi**, va uni yopadigan ish chegara reyestrida.
    #: `containment` ning o'zi noma'lum bo'lgan hol ham shu yerga
    #: tushadi: sonining ma'nosi yo'q son sanoq deb o'qilmaydi.
    DENOMINATOR_ESTIMATED = "denominator_estimated"
    #: Poligon o'qilgan va kataklar sanalgan, lekin faqat markazi
    #: ichkarida bo'lganlari (`center`) — chekkadagi katak maxrajga
    #: tushmagan, ya'ni son ishonchli tepa chegara emas. Bu ham
    #: **o'lchov qarzi**, lekin ishi boshqa joyda: `overlap` sanog'i
    #: `h3` ning eksperimental API sini talab qiladi.
    DENOMINATOR_NOT_UPPER_BOUND = "denominator_not_upper_bound"


@dataclass(frozen=True)
class RegionFacts:
    """O'lchovning kirishi — ikkita reyestrning kesimi.

    Uchala xarita ham **matn kalitli**: `tzscale` tumanni matn bilan
    biladi (`ZoneFact.parent_id`), `tzsource` ham matn qaytaradi.
    `uuid` ga o'tish bog'liqlik yo'nalishini teskari qilardi.
    """

    #: `geo` reyestri: tuman → kodi. §12 ning «сколько районов» i va
    #: **faqat qamrovning** maxraji.
    districts: dict[str, str]
    #: `geo` geometriyasi: tuman → poligonni qoplaydigan r9 kataklar
    #: soni. 196-rundan boshlab u **sanaladi** (`app.geo.cellfit`,
    #: `contain='overlap'`) va yuzadan baholash faqat poligon
    #: o'qilmaganda qoladi — o'shanda `refresh_coverage` jurnalga
    #: `coverage.cells_estimated` yozadi. Maydon nomi tarixiy:
    #: uni o'zgartirish `tz_check` ning chiqish formatini ham
    #: buzardi, ma'nosi esa izohda yuradi.
    #: Tumani yo'q qiymat — geometriya o'qilmagan.
    blocks_estimated: dict[str, int]
    #: Yuqoridagi son **nimani** sanagani: tuman → `cellfit.Containment`.
    #: Sukut qiymati ataylab **yo'q** — bo'sh xarita hamma hududni
    #: «o'lchanmagan» qilardi va `over_capacity` ning sababini jimgina
    #: bitta tomonga og'dirardi (`CapacityConflict` izohi). Har bir
    #: chaqiruvchi sonining ma'nosini o'zi aytadi.
    #: Tumani yo'q qiymat — geometriya o'qilmagan (`blocks_estimated`
    #: da ham yo'q).
    blocks_containment: dict[str, cellfit.Containment]
    #: `reports`: tuman → foydalanuvchisi bor kvartallar soni. §3 ning
    #: maxraji.
    blocks_with_users: dict[str, int]
    #: Tumani aniqlanmagan kvartallar (`05` §5.3). Ular hech qaysi
    #: tumanning porogiga qo'shilmaydi, ya'ni yo'qotilgan maxraj.
    blocks_unassigned: int
    #: Ikki tumanda uchragan va bittasiga biriktirilgan kvartallar.
    blocks_straddling: int


@dataclass(frozen=True)
class DistrictReach:
    """Bitta tumanning §3 bo'yicha tepa chegarasi."""

    district_id: str
    #: Reyestrdagi kodi; reyestrda yo'q tumanda bo'sh satr.
    code: str
    #: §3 ning maxraji — foydalanuvchisi bor kvartallar.
    blocks_with_users: int
    #: Reyestrdagi taxminiy umumiy kvartallar; noma'lum bo'lsa `None`.
    blocks_estimated: int | None
    #: Yuqoridagi son nimani sanagani; geometriya o'qilmagan bo'lsa
    #: `None`. `blocks_estimated` bilan **birga** yuradi: sonning
    #: ma'nosisiz `over_capacity` ning sababi aniqlanmaydi.
    containment: cellfit.Containment | None
    #: §3 ning kerakli soni (`tzscale.share_need` + eng kam son).
    need: int
    #: Faqat ulushdan kelib chiqadigan qismi — `minimum_decides` uchun.
    #: `need` dan tiklab bo'lmaydi: `max()` ikkala argumentini ham
    #: yo'qotadi, ya'ni «qaysi biri qaror qabul qildi» degan savolga
    #: javob faqat shu maydonda qoladi.
    share_part: int
    #: Geo reyestrida bormi. `False` — foydalanuvchisi bor, lekin
    #: joriy chegara versiyasi yo'q tuman.
    known: bool

    @property
    def reachable(self) -> bool:
        """Porog **umuman** yig'ilishi mumkinmi.

        Tepa chegara — foydalanuvchisi bor kvartallarning hammasi
        tasdiqlangan holat: dalilsiz kvartal tasdiqlanmaydi
        (`tzscale.from_zone_verdicts` maxrajga faqat shularni
        qo'shadi).
        """
        return self.blocks_with_users >= self.need

    @property
    def minimum_decides(self) -> bool:
        """Qarorni ulush emas, mutlaq eng kam son qabul qiladimi.

        `True` — ulushdan kelib chiqadigan son eng kam sondan oshmaydi,
        ya'ni §3 ning `40 %` i bu tumanda hech narsa qo'shmaydi.
        """
        return self.need > 0 and self.need != self.share_part

    @property
    def coverage(self) -> float | None:
        """Qamrov: foydalanuvchisi bor kvartallarning ulushi.

        Maxraj **geo** dan (modul izohi, ikkinchi 🔴). Noma'lum yoki
        nol bo'lsa `None` — `0.0` qaytarish o'lchanmagan qamrovni
        «nol qamrov» deb ko'rsatardi.
        """
        if self.blocks_estimated is None or self.blocks_estimated <= 0:
            return None
        return self.blocks_with_users / self.blocks_estimated

    @property
    def over_capacity(self) -> bool:
        """Foydalanuvchisi bor kvartallar umumiy kataklardan ko'pmi.

        Bu qamrov `100 %` dan katta degani emas, **reyestrlar mos
        kelmayapti yoki maxraj o'lchanmagan** degani. Qaysi biri —
        `capacity_conflict` da; bu yerda faqat **son** solishtiriladi,
        chunki bayroqning o'zi sababdan mustaqil bo'lishi kerak:
        sababni tekshirishni shu shartning ichiga qo'shish
        o'lchanmagan hududda bayroqni butunlay o'chirardi va nuqson
        ko'rinmay qolardi.

        Qiymat kesilmaydi — kesish nuqsonni yashirardi.
        """
        return self.blocks_estimated is not None and self.blocks_with_users > self.blocks_estimated

    @property
    def capacity_conflict(self) -> CapacityConflict:
        """`over_capacity` yongan bo'lsa — nega (197-run, 199-run).

        Ajratuvchi belgi — maxrajning **ma'nosi**, kattaligi emas:
        `overlap` bilan sanalgan maxraj hududning ichidagi har qanday
        xabarning katagini o'z ichiga oladi (`cellfit`), ya'ni oshib
        ketish faqat kvartal poligondan tashqarida bo'lgandagina
        mumkin. `center` va `estimate` da esa maxrajning o'zi
        ichkaridagi katakni yo'qotishi mumkin va bayroq o'lchov
        nuqsonidan ham yonadi.

        Qolgan ikkitasi bir-biridan **ikkinchi** savol bilan
        ajratiladi: «poligon umuman o'qildimi»
        (`cellfit.is_counted`). Ikkala qoida ham `cellfit` dan
        olinadi va bu yerda takrorlanmaydi — `Containment` ga
        to'rtinchi qiymat qo'shilsa, javob bitta joyda o'zgarsin.
        Ikkinchi savolni birinchisining ichiga solish qarzning
        sababini yo'qotardi (`CapacityConflict` jadvali).

        Ma'nosi noma'lum son (`containment is None`) `ESTIMATED` deb
        o'qiladi: `RegionFacts` da bu «geometriya o'qilmagan» degani,
        ya'ni sanoq bo'lmagan tomon. Uni sanoq deb o'qish o'lchov
        qarzini `h3` ga ag'darardi va chegara reyestridagi ishni
        ko'rinmas qilardi.
        """
        if not self.over_capacity:
            return CapacityConflict.NONE
        if self.containment is None:
            return CapacityConflict.DENOMINATOR_ESTIMATED
        if cellfit.is_upper_bound_safe(self.containment):
            return CapacityConflict.OUTSIDE_POLYGON
        if cellfit.is_counted(self.containment):
            return CapacityConflict.DENOMINATOR_NOT_UPPER_BOUND
        return CapacityConflict.DENOMINATOR_ESTIMATED


@dataclass(frozen=True)
class CityReach:
    """Shahar darajasining tepa chegarasi.

    Maxraj va sanoq **har xil to'plamdan** olinadi va bu §3 ning
    tuzilishi: `tzscale.city()` maxrajga foydalanuvchisi bor har bir
    tumanni qo'shadi, sanoqqa esa faqat tasdiqlanganini (modul izohi,
    birinchi 🔴).
    """

    #: `geo` reyestridagi joriy tumanlar — §12 ning «сколько районов» i.
    districts_total: int
    #: §3 ning maxraji — foydalanuvchisi bor tumanlar.
    districts_with_users: int
    #: Sanoqning tepa chegarasi — o'zi erishuvchan tumanlar.
    districts_reachable: int
    #: §3 ning kerakli soni.
    need: int
    #: Ulush bilan hisoblangan qismi — `minimum_decides` uchun.
    share_part: int

    @property
    def reachable(self) -> bool:
        """Shahar darajasi umuman yig'ilishi mumkinmi."""
        return self.districts_reachable >= self.need

    @property
    def minimum_decides(self) -> bool:
        """Qarorni mutlaq eng kam son qabul qiladimi."""
        return self.need > 0 and self.need != self.share_part

    @property
    def dead_weight(self) -> int:
        """Porogni ko'taradigan, lekin uni to'ldira olmaydigan tumanlar.

        Foydalanuvchisi bor, lekin o'zi hech qachon tasdiqlanmaydigan
        tumanlar. Bu son katta bo'lsa, shahar darajasi tumanlarning
        har biri alohida erishuvchan ko'ringan holda ham erishilmas.
        """
        return self.districts_with_users - self.districts_reachable

    @property
    def coverage(self) -> float | None:
        """Foydalanuvchisi bor tumanlarning ulushi. Maxraj — `geo`."""
        if self.districts_total <= 0:
            return None
        return self.districts_with_users / self.districts_total

    @property
    def over_capacity(self) -> bool:
        """Reyestrda yo'q tumanlarda foydalanuvchi bormi."""
        return self.districts_with_users > self.districts_total


@dataclass(frozen=True)
class Coverage:
    """§12 «Дополнительно» ning javobi."""

    verdict: Verdict
    reason: Reason
    #: Tuman kesimida — identifikatori bo'yicha tartiblangan (Т-3).
    #: `UNKNOWN` da ham to'ldiriladi: o'lchov bo'lmasa ham dalil
    #: ko'rinsin.
    districts: tuple[DistrictReach, ...]
    city: CityReach
    blocks_unassigned: int
    blocks_straddling: int

    @property
    def blocks_counted(self) -> int:
        """§3 ning maxrajiga **kirgan** kvartallar — hamma tuman bo'yicha.

        Son ilgari `summary()` ning ichida yig'ilardi, ya'ni matn
        hisoboti uni umuman ko'rmasdi va ikkita chiqish bitta sonni
        ikki xil joydan olardi. Bu yerda u bitta xossa — `blocks_seen`
        ham, ulushlar ham shundan hisoblanadi.
        """
        return sum(item.blocks_with_users for item in self.districts)

    @property
    def blocks_seen(self) -> int:
        """Foydalanuvchisi bor **hamma** kvartal — biriktirilgani ham, yo'g'i ham.

        🔴 O'lchovning maxraji sanoqning o'zidan olinmaydi (210-run).
        `blocks_counted` §3 ga kirgan kvartallarni sanaydi, ya'ni
        «qancha kvartal yo'qoldi» degan savolga uning o'zi javob
        berolmaydi: yo'qolganlarning hammasi maxrajdan ham
        chiqarilgan bo'lardi va nisbat har doim `0` chiqardi. Shuning
        uchun maxraj ikkala tomonning **yig'indisi**.

        `blocks_straddling` bu yerda qo'shilmaydi: chegaradagi katak
        allaqachon bitta tumanga biriktirilgan, ya'ni u
        `blocks_counted` ning **ichida** (`tzsource` izohi).
        """
        return self.blocks_counted + self.blocks_unassigned

    @property
    def unassigned_share(self) -> float | None:
        """Yo'qolgan kvartallarning ulushi. Kvartal umuman bo'lmasa — `None`.

        `None` — «o'lchanmadi», `0.0` emas: nol maxrajdan chiqqan nol
        ulush «hammasi joyida» degan yolg'on javob bo'lardi.
        """
        return None if self.blocks_seen == 0 else self.blocks_unassigned / self.blocks_seen

    @property
    def straddling_share(self) -> float | None:
        """Chegaradagi kvartallarning ulushi — maxraji **boshqa**.

        Bu son biriktirilganlarning ichidagi ulush
        (`blocks_counted`), chunki chegaradagi katak allaqachon bitta
        tumanga tushgan. `blocks_seen` ni maxraj qilish uni
        biriktirilmaganlar bilan aralashtirardi va ikkita boshqa
        nuqson bitta shkalada o'qilardi.
        """
        return None if self.blocks_counted == 0 else self.blocks_straddling / self.blocks_counted

    def district(self, district_id: str) -> DistrictReach | None:
        """Bitta tumanning natijasi; yo'q bo'lsa `None`."""
        for item in self.districts:
            if item.district_id == district_id:
                return item
        return None

    @property
    def unreachable_districts(self) -> tuple[str, ...]:
        """Porogi hech qachon yig'ilmaydigan tumanlar, tartiblangan."""
        return tuple(item.district_id for item in self.districts if not item.reachable)

    @property
    def reachable_districts(self) -> tuple[str, ...]:
        """Porogi yig'ilishi mumkin bo'lgan tumanlar, tartiblangan."""
        return tuple(item.district_id for item in self.districts if item.reachable)

    @property
    def unknown_districts(self) -> tuple[str, ...]:
        """Foydalanuvchisi bor, lekin `geo` reyestrida yo'q tumanlar.

        Ular §3 ning maxrajidan **chiqarilmaydi** (modul izohi,
        ikkinchi 🔴), lekin nomlanadi: reyestrning nuqsoni qamrovni
        birdan katta qiladi va buni ko'rish kerak.
        """
        return tuple(item.district_id for item in self.districts if not item.known)

    def _conflicting(self, conflict: CapacityConflict) -> tuple[str, ...]:
        return tuple(
            item.district_id for item in self.districts if item.capacity_conflict is conflict
        )

    @property
    def districts_outside_polygon(self) -> tuple[str, ...]:
        """Maxraji sanalgan, lekin baribir oshib ketgan tumanlar.

        **Haqiqiy topilma**: biriktirish bilan chegara reyestri zid.
        """
        return self._conflicting(CapacityConflict.OUTSIDE_POLYGON)

    @property
    def districts_capacity_estimated(self) -> tuple[str, ...]:
        """Oshib ketgan, lekin poligoni **umuman o'qilmagan** tumanlar.

        O'lchov qarzi, ishi chegara reyestrida (`CapacityConflict`
        jadvali). `districts_capacity_not_upper_bound` bilan
        **qo'shilmaydi**: qo'shilgan son qaysi ishni qilish
        kerakligini yo'qotardi.
        """
        return self._conflicting(CapacityConflict.DENOMINATOR_ESTIMATED)

    @property
    def districts_capacity_not_upper_bound(self) -> tuple[str, ...]:
        """Oshib ketgan, poligoni o'qilgan, lekin sanoq `center` bilan.

        O'lchov qarzi, ishi `h3` ning eksperimental API sida
        (`CapacityConflict` jadvali).
        """
        return self._conflicting(CapacityConflict.DENOMINATOR_NOT_UPPER_BOUND)

    @property
    def has_capacity_debt(self) -> bool:
        """Maxrajning sifati bo'yicha **birorta** qarz bormi.

        Faqat `tz_check` ning holati uchun: «hammasi o'lchandimi»
        degan savolga bitta mantiqiy javob kerak. Ro'yxatlar bu yerda
        birlashtirilmaydi — bittasini ikkinchisining ichiga solish
        199-run ajratgan sababni darhol qaytarib yo'q qilardi.
        """
        return bool(self.districts_capacity_estimated) or bool(
            self.districts_capacity_not_upper_bound
        )

    @property
    def looks_unreachable(self) -> bool:
        """§12 ning xulosasi: tumanlarning ko'pchiligi erishilmasmi.

        Sonli chegara bilan emas, ikkita **o'lchangan** sonni
        solishtirish bilan (Т-1). Tenglikda `False`: teng bo'linish
        «ko'pchilik» emas.
        """
        return len(self.unreachable_districts) > len(self.reachable_districts)


def blocks_by_district(registry: tzsource.BlockRegistry) -> dict[str, int]:
    """`tzsource` ning kvartal→tuman xaritasidan tuman kesimi.

    Sanaladigan narsa — **kvartallar**, odamlar emas: §3 ning birinchi
    jumlasi («сто сообщений с одной улицы не доказывают, что район без
    света») aynan odamlarni sanashni taqiqlaydi, va `BlockUsersRow.users`
    ni qo'shish §12 ning javobini o'sha taqiqlangan tomonga burardi.

    `BlockRegistry` chegaradagi katakni allaqachon bitta tumanga
    biriktirgan, ya'ni bu yerda ikki marta sanash mumkin emas.
    """
    counts: dict[str, int] = {}
    for district in registry.district_of.values():
        counts[district] = counts.get(district, 0) + 1
    return dict(sorted(counts.items()))


def measure(facts: RegionFacts, *, params: TzParams) -> Coverage:
    """§12 «Дополнительно» ning javobi.

    Toza funksiya: bazaga ham, soatga ham murojaat qilmaydi.
    """
    districts: list[DistrictReach] = []
    # Maxraj — §3 niki: foydalanuvchisi bor tumanlar. Geo reyestrining
    # bo'sh tumanlari bu ro'yxatga **kirmaydi** (modul izohi, 2-🔴).
    for district_id in sorted(facts.blocks_with_users):
        blocks = facts.blocks_with_users[district_id]
        share_part = share_need(blocks, share=params.district_block_share)
        item = DistrictReach(
            district_id=district_id,
            code=facts.districts.get(district_id, ""),
            blocks_with_users=blocks,
            blocks_estimated=facts.blocks_estimated.get(district_id),
            containment=facts.blocks_containment.get(district_id),
            need=max(share_part, params.district_block_min),
            share_part=share_part,
            known=district_id in facts.districts,
        )
        districts.append(item)

    with_users = len(districts)
    reachable = sum(1 for item in districts if item.reachable)
    city_share_part = share_need(with_users, share=params.city_district_share)
    city = CityReach(
        districts_total=len(facts.districts),
        districts_with_users=with_users,
        districts_reachable=reachable,
        need=max(city_share_part, params.city_district_min),
        share_part=city_share_part,
    )

    if with_users:
        reason = Reason.NONE
    elif facts.blocks_unassigned:
        # Kvartallar bor, lekin hech qaysisi tumanga tushmagan —
        # bu ma'lumotning yo'qligi emas, `05` §5.3 ning defekti
        # (`Reason.ALL_BLOCKS_UNASSIGNED` izohi).
        reason = Reason.ALL_BLOCKS_UNASSIGNED
    else:
        reason = Reason.NO_BLOCKS_WITH_USERS

    return Coverage(
        verdict=Verdict.MEASURED if with_users else Verdict.UNKNOWN,
        reason=reason,
        districts=tuple(districts),
        city=city,
        blocks_unassigned=facts.blocks_unassigned,
        blocks_straddling=facts.blocks_straddling,
    )


def to_facts(
    registry: tzsource.BlockRegistry,
    *,
    districts: Iterable[geo_queries.DistrictRow],
    geometry: Iterable[geo_queries.TerritoryGeometryFacts],
) -> RegionFacts:
    """Ikkita reyestrni `measure()` ning kirishiga aylantiradi.

    Toza: bazani ko'rmaydi, shuning uchun ikki reyestrning mos
    kelmasligi testda fikstyurasiz o'lchanadi.

    `geometry` bir marta materiallashtiriladi: undan **ikkita** xarita
    quriladi (son va sonning ma'nosi), generator esa ikkinchi o'tishda
    bo'sh bo'lardi — va bo'sh `blocks_containment` hamma hududni
    «o'lchanmagan» qilib ko'rsatardi (`RegionFacts` izohi).
    """
    geometry_rows = list(geometry)
    return RegionFacts(
        districts={str(row.id): row.code for row in districts},
        blocks_estimated={str(row.territory_id): row.covering_cells for row in geometry_rows},
        blocks_containment={str(row.territory_id): row.containment for row in geometry_rows},
        blocks_with_users=blocks_by_district(registry),
        blocks_unassigned=len(registry.unassigned),
        blocks_straddling=len(registry.straddling),
    )


async def load(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    params: TzParams,
) -> Coverage:
    """Uchta so'rov: chegaralar reyestri, geometriya va kvartallar.

    `tzsource.load()` qayta ishlatiladi — §3 ning maxraji o'lchovda
    ham, mahsulotda ham **bir xil** so'rovdan kelishi shart, aks holda
    §12 boshqa maxraj haqida son berardi (`tzreach` ning birinchi
    sababi).
    """
    registry = await tzsource.load(session, region_id=region_id)
    rows = await geo_queries.current_districts(session, region_id)
    geometry = await geo_queries.district_geometry_facts(session, region_id)
    return measure(to_facts(registry, districts=rows, geometry=geometry), params=params)


def district_summary(district: DistrictReach) -> Mapping[str, object]:
    """Bitta tumanning tekis kesimi (200-run).

    Yig'ma ro'yxatlar (`unreachable_districts`,
    `districts_capacity_*`) tumanning **nomini** beradi va sonini
    bermaydi: mashina o'qiydigan chiqishda «bu tuman porogidan qancha
    uzoq» degan savolga javob yo'q edi, u faqat matn hisobotining
    qatorida qolardi. Qator shu sababdan modulning o'zida yasaladi —
    `as_json` ning qoidasi bitta: shakl chaqiruvchida takrorlanmaydi.

    🔴 **`containment` shartsiz chiqadi.** `capacity_conflict`
    bayroqning **sababi**, ya'ni u faqat `over_capacity` yonganda
    qiymat oladi (`DistrictReach.capacity_conflict` ning birinchi
    sharti, 197-run). Demak qamrovi joyida bo'lgan tumanda poligon
    umuman o'qilmagan bo'lsa ham sabab `NONE` bo'ladi va maxrajning
    yuzadan baholangani hech qayerda ko'rinmaydi — nisbat esa
    o'lchangandek o'qiladi. Ikkalasini bitta maydonga yig'ish
    «sonning ma'nosi» va «son zid chiqdimi» degan ikki xil savolni
    birlashtirardi.

    `capacity_conflict` bu yerda **qayta hisoblanmaydi** va
    `containment` dan chiqarilmaydi: qoida `DistrictReach` da,
    kesim uni faqat ko'chiradi.
    """
    return {
        "district_id": district.district_id,
        "code": district.code,
        "known": district.known,
        "blocks_with_users": district.blocks_with_users,
        "blocks_estimated": district.blocks_estimated,
        # Sonning ma'nosi — sonining yonida (`RegionFacts` izohi).
        # `None` — geometriya umuman o'qilmagan; `0` yoki bo'sh satr
        # emas, chunki o'lchanmagan narsa qiymatga aylanmaydi.
        "containment": None if district.containment is None else district.containment.value,
        "coverage": district.coverage,
        "need": district.need,
        "share_part": district.share_part,
        "minimum_decides": district.minimum_decides,
        "reachable": district.reachable,
        "over_capacity": district.over_capacity,
        "capacity_conflict": district.capacity_conflict.value,
    }


def city_summary(city: CityReach) -> Mapping[str, object]:
    """Shahar darajasining tekis kesimi (202-run).

    🔴 **Ikkita javob kesimda umuman yo'q edi.** `share_part` va
    `minimum_decides` tuman qatorida 200-rundan beri bor, shahar
    darajasida esa yo'q: «shahar porogini kim qabul qildi — ulushmi
    yoki mutlaq eng kam sonmi» degan savolga javob faqat
    `coverage.minimum_decides:city` topilmasida qolardi, ya'ni
    **bayroq shaklida va sonsiz**. Bayroq esa `need != share_part`
    ni ko'rsatadi va ikkovining **qiymatini** ko'rsatmaydi: `kerak 4`
    ni ko'rgan skript ulush `1` mi yoki `3` mi ekanini bilmasdi, ya'ni
    §7 ning qaysi sozlamasini o'zgartirish kerakligini ayta olmasdi.

    Kalitlar `summary()` dagi tarixiy nomlarini saqlaydi
    (`districts_total`, `city_need`, `dead_weight`) — bu kesim yangi
    daraja qo'shmaydi, u faqat shaharga tegishli kalitlarni bitta
    joyga yig'adi. Ularni yangi nom bilan takrorlash bir mapping
    ichida ikkita haqiqat yasardi: bittasini o'qigan chaqiruvchi
    ikkinchisining yangilanganini ko'rmasdi.

    `coverage` va `over_capacity` ham shu yerda: birinchisi matn
    hisobotida bor edi, lekin `--json` da yo'q edi, ikkinchisi esa
    hech qayerda yo'q edi — `districts_with_users > districts_total`
    ni chaqiruvchi o'zi hisoblardi, ya'ni qoida moduldan chiqib
    ketardi.
    """
    return {
        "districts_total": city.districts_total,
        "districts_with_users": city.districts_with_users,
        "districts_reachable": city.districts_reachable,
        "city_need": city.need,
        "city_share_part": city.share_part,
        "city_minimum_decides": city.minimum_decides,
        "city_reachable": city.reachable,
        # `None` — reyestr bo'sh, ya'ni maxraj yo'q; `0.0` emas.
        "city_coverage": city.coverage,
        "city_over_capacity": city.over_capacity,
        "dead_weight": city.dead_weight,
    }


def summary(coverage: Coverage) -> Mapping[str, object]:
    """Hisobot uchun tekis kesim (`tools/` skripti va tekshiruv).

    Odam o'qiydigan matn bu yerda yasalmaydi: modul i18n katalogini
    ko'rmaydi va §12 foydalanuvchiga chiqmaydi — u ishlab chiqishdan
    **oldingi** tekshiruv.

    Tuman kesimi (`districts`) yig'ma ro'yxatlarni **almashtirmaydi**:
    ro'yxatlar savolning javobi (kimda qarz bor), qatorlar esa dalili
    (qancha va nimadan). Birini ikkinchisidan tiklab bo'lmaydi —
    `NONE` sababli tumanlar hech qaysi ro'yxatda yo'q.

    Shahar kalitlari bu yerda yasalmaydi — `city_summary()` (202-run).
    """
    return {
        "verdict": coverage.verdict.value,
        "reason": coverage.reason.value,
        **city_summary(coverage.city),
        "blocks_with_users": coverage.blocks_counted,
        "blocks_seen": coverage.blocks_seen,
        "blocks_unassigned": coverage.blocks_unassigned,
        "blocks_unassigned_share": coverage.unassigned_share,
        "blocks_straddling": coverage.blocks_straddling,
        "blocks_straddling_share": coverage.straddling_share,
        "unreachable_districts": coverage.unreachable_districts,
        "unknown_districts": coverage.unknown_districts,
        "districts_outside_polygon": coverage.districts_outside_polygon,
        "districts_capacity_estimated": coverage.districts_capacity_estimated,
        "districts_capacity_not_upper_bound": coverage.districts_capacity_not_upper_bound,
        "looks_unreachable": coverage.looks_unreachable,
        "districts": tuple(district_summary(item) for item in coverage.districts),
    }

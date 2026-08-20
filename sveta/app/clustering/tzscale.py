"""TZ §3 — masshtab: uzilish tuman miqyosidami yoki shahar miqyosida.

**Nima uchun bu modul bor.** §11 ning navbati yetti banddan iborat va
172–181 runlar yettalasini ham qurdi. §3 o'sha navbatda **umuman
yo'q**: u «Подсчёт» (2-band) ning ichida ham emas, «Восстановление»
ning ichida ham emas. Natijada 172-run §7 ning yigirma uchta
sozlamasini reyestrga yozganda `tz.scale.*` ning to'rttasi ham
yozildi, lekin ularni **o'qiydigan kod hech qachon paydo bo'lmadi**:
181-run oxirida `grep district_block_share` butun `app/` va `tests/`
bo'ylab `tzconfig.py` dan boshqa hech narsa topmaydi. Sozlama bor,
tipi bor, migratsiyasi bor, vitrinada ko'rinadi — va hech narsaga
ta'sir qilmaydi.

Buni topgan narsa — §10 ning qabul ro'yxati: ТС-208 (`app.release.
tz_acceptance`) yigirmata banddan **yagona** band bo'lib chiqdi,
uning nomeri butun `tests/` daraxtida bir marta ham uchramaydi.

## §3 nima deydi va u §2.1 dan nimasi bilan farq qiladi

> «Масштаб считается **не по числу людей, а по покрытию**. Сто
> сообщений с одной улицы не доказывают, что район без света.»

| Uroven | Shart |
|---|---|
| Tuman | tumanning **40 %** kvartali tasdiqlangan, lekin 3 tadan kam emas |
| Shahar | foydalanuvchisi bor tumanlarning **yarmi**, lekin 3 tadan kam emas |

§2.1 (`tzcount`) «zonada nechta **odam**» degan savolga javob beradi,
bu modul esa «nechta **zona**». Ikkalasini bitta funksiyaga qo'shish
aynan §3 ning birinchi jumlasi taqiqlagan narsani qilardi: bitta
kvartaldagi yuz guvoh tumanning porogini yopib yuborardi.

Shuning uchun uy/kvartal/mahalla darajasi bu yerda umuman
takrorlanmaydi — modul kvartallarning **verdiktidan** boshlaydi
(`from_zone_verdicts()`), ya'ni §2.1 ni qayta hisoblamaydi.

## Nima uchun `scale.py` bilan yonma-yon turadi

Repoda allaqachon `app/clustering/scale.py` bor va u `06` §5 ning
narvoni (`local` → `mahalla` → `district`). Ikkalasi bitta savolga
javob beradi va **har xil** javob beradi:

| | `06` §5.3 (`scale.py`) | TZ §3 (shu modul) |
|---|---|---|
| Tuman nimadan yig'iladi | ta'sirlangan **mahallalardan** | tasdiqlangan **kvartallardan** |
| Maxraj | yo'q, mutlaq son | foydalanuvchisi bor zonalar |
| Soni | `MIN_MAHALLAS_FOR_DISTRICT = 2`, kodda | §7 sozlamasida |

172-run ning 👤 qarori bo'yicha ziddiyatda TZ haq, lekin `scale.py`
bugun **mahsulotga ulangan** (`outages.scale`), bu modul esa emas.
Eski narvonni o'chirish bu running ishi emas: u `05` §7 ning javob
sxemasida, xaritada va statistikada. Holat `PROGRESS.md` ning «Ochiq
savollar» iga yozildi.

## Maxraj — faqat foydalanuvchisi bor zonalar

> «Если в районе 50 кварталов, а пользователи есть в 12, считаем от
> 12. Иначе порог недостижим навсегда.»

Bu qoidaning narxi bor va u ko'rinmas: maxraj **o'zgaruvchan**, ya'ni
bir xil hodisa foydalanuvchi qo'shilgani sayin masshtabini yo'qotishi
mumkin (5/12 — tuman, ertaga 5/14 — yo'q). Bu nuqson emas, §3 ning
o'zi: masshtab — hozirgi bilimning bahosi, tarixiy fakt emas.

Ikkita chekka holat ochiq yozildi, chunki ikkalasi ham «jimgina
to'g'ri» ko'rinadi:

* **Maxraj nol.** Foydalanuvchisi bor kvartal umuman bo'lmasa,
  «tasdiqlangan 0 tasi 0 tadan» ulush arifmetikasi bo'yicha `0 >= 0`
  beradi va tuman **tasdiqlangan** bo'lib chiqardi. Eng kam son
  (`district_block_min`) buni to'sadi, lekin sababni ko'rsatmaydi —
  shuning uchun `Shortfall.NO_ZONES` alohida.
* **Tasdiqlangan, lekin foydalanuvchisiz zona.** Mantiqan bunday
  bo'lmaydi (kvartalni tasdiqlagan odam — o'sha kvartalning
  foydalanuvchisi), lekin ma'lumot ikki xil so'rovdan kelsa
  (`confirmed` — hodisadan, `has_users` — reyestrdan) ular bir-biriga
  mos kelmasligi mumkin. Tasdiqlangan zona **har doim** maxrajga ham
  kiradi, aks holda ulush birdan katta bo'lardi.

## Ulush butun sonda solishtiriladi

`confirmed / with_users >= share` yozuvi qirrada **jimgina**
teskarilashadi: `0.3 * 10` IEEE-754 da `3.0000000000000004`, ya'ni
o'nta zonaning uchtasi «30 % emas» bo'lib qolardi. Shuning uchun
ulush `SHARE_SCALE` ga ko'paytirilib butun songa aylantiriladi va
kerakli son **yuqoriga yaxlitlangan bo'linma** bilan hisoblanadi.
`need` kartaga ham chiqadi («12 dan 5 tasi kerak»), ya'ni u baribir
butun son bo'lishi kerak edi.

## Nima uchun bu yerda status yo'q

Т-5 («статус меняется в одном месте») kuchida: masshtab —
hodisaning **kattaligi**, uning ishonchliligi emas. §5 jadvalida
«Район подтверждён» degan status yo'q va uni o'ylab topish Т-5 ni
buzardi. Modul shuning uchun `tzstatus` ni import ham qilmaydi;
natija — kartaga qo'shiladigan yorliq (`SCALE_KEYS`).

Modul **toza**: bazaga ham, soatga ham (Т-4), `settings` ga ham
murojaat qilmaydi.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from app.clustering.tzcount import Level, ZoneVerdict
from app.core.tzconfig import TzParams

#: Hujjat bo'limi. Reyestrlar vitrinasi (`app.admin.registries`) shuni o'qiydi.
SPEC = "TZ §3"

#: Ulushni butun songa aylantirish koeffitsienti. Bu **arifmetikaning
#: aniqligi**, §7 sozlamasi emas: §7 ulushlarni foizda beradi, ya'ni
#: mingdan biri barcha qiymatlarni yo'qotmasdan ifodalaydi.
SHARE_SCALE = 1000


class Scale(StrEnum):
    """§3 jadvalining ikkita qatori.

    §2.1 ning uchta darajasi (`tzcount.Level`) bu yerda takrorlanmaydi:
    ular «zonada nechta odam», bu esa «nechta zona». Bitta `StrEnum` ga
    qo'shish ikkita har xil savolni bitta o'qqa qo'yardi.
    """

    #: «Район» — kvartallar bo'yicha sanaladi, mahallalar bo'yicha emas.
    DISTRICT = "district"
    #: «Город» — tumanlar bo'yicha.
    CITY = "city"


class Shortfall(StrEnum):
    """Nega masshtab yig'ilmadi. Diagnostika, foydalanuvchiga emas."""

    NONE = "none"
    #: Foydalanuvchisi bor zona umuman yo'q — ulush ma'nosiz.
    NO_ZONES = "no_zones"
    #: Ulush yetarli, lekin eng kam son (§3 ning «не менее 3») emas.
    MINIMUM = "minimum"
    #: Eng kam son bajarilgan, ulush emas.
    SHARE = "share"


#: §5 ning kartasiga qo'shiladigan yorliq. Jadval **so'zma-so'z**:
#: `f"tz.scale.{level}"` bilan yig'ilgan kalitni katalog skaneri
#: ko'rmaydi (173-run saboqi).
SCALE_KEYS: dict[Scale, str] = {
    Scale.DISTRICT: "tz.scale.district",
    Scale.CITY: "tz.scale.city",
}


@dataclass(frozen=True)
class Rule:
    """§3 ning bitta qatori va u qurilganmi.

    Ro'yxat kodda turadi, chunki uni `app.admin.registries` o'qiydi:
    §3 ning qaysi qismi **hisoblanadi** va qaysi qismi hali kanalsiz
    turibdi — operator ko'radigan joyda yozilishi kerak.
    """

    code: str
    note: str
    built: bool


RULES: tuple[Rule, ...] = (
    Rule(
        code="3-district",
        note="Tuman: kvartallarning 40 % i, 3 tadan kam emas",
        built=True,
    ),
    Rule(
        code="3-city",
        note="Shahar: tumanlarning yarmi, 3 tadan kam emas",
        built=True,
    ),
    Rule(
        code="3-denominator",
        note="Maxraj — faqat foydalanuvchisi bor zonalar",
        built=True,
    ),
    Rule(
        code="3-source",
        note="Kvartalning «foydalanuvchisi bor» belgisi reyestrdan keladi",
        # Hisob tayyor va `from_zone_verdicts()` uni qabul qiladi,
        # lekin `has_users` ni **to'ldiradigan so'rov** yo'q: u
        # `reports`/`users` ustidan zona kesimini talab qiladi va
        # bugun bunday so'rov repoda yo'q. Shu sababdan bugun
        # `evaluate()` ni chaqiradigan mahsulot kodi ham yo'q.
        # 187-run: aynan shu qator §3 ni ulashdan oldin qurilishi
        # shart. Maxrajsiz ulangan §3 xato tomonga adashadi — ulush
        # o'z-o'zidan bajariladi va tuman yo'qdan tasdiqlanadi;
        # shuning uchun `blocks_with_users` endi sukut qiymatisiz.
        built=False,
    ),
)


@dataclass(frozen=True)
class ZoneFact:
    """Bitta zonaning masshtab uchun kerakli minimumi.

    `confirmed` — §2.1 bo'yicha tasdiqlangan (`ZoneVerdict.confirmable`,
    ya'ni §2.3 ishlagan kam odamli zona **emas**). Kam odamli
    kvartalning tumanni ko'tarishi §2.3 ning narvon cheklovini bir
    daraja yuqorida aylanib o'tish bo'lardi.
    """

    zone_id: str
    #: Qaysi kattaroq zonaga tegishli: kvartal uchun — tuman, tuman
    #: uchun — shahar. `None` bo'lishi mumkin emas: biriktirilmagan
    #: zona maxrajda ham, sanoqda ham qatnashmaydi va uni jimgina
    #: tashlash o'rniga chaqiruvchi hal qiladi.
    parent_id: str
    #: Zonada bizning foydalanuvchimiz bormi (§3 ning maxraji).
    has_users: bool
    confirmed: bool


@dataclass(frozen=True)
class ScaleVerdict:
    """Bitta kattaroq zonaning §3 bo'yicha holati."""

    level: Scale
    zone_id: str
    #: Maxraj — foydalanuvchisi bor zonalar soni.
    with_users: int
    #: Sanoq — tasdiqlangan zonalar soni.
    confirmed: int
    #: Kerakli son: ulush va eng kam sondan kattasi. Kartaga chiqadi.
    need: int
    reached: bool
    shortfall: Shortfall

    @property
    def remaining(self) -> int:
        """Karta uchun: yana nechta zona kerak."""
        return max(self.need - self.confirmed, 0)

    @property
    def key(self) -> str:
        """Yorliqning i18n kaliti."""
        return SCALE_KEYS[self.level]


def share_need(with_users: int, *, share: float) -> int:
    """Ulushdan kelib chiqadigan eng kam son — butun arifmetikada.

    Yuqoriga yaxlitlangan bo'linma: `40 %` va `12` zona uchun `4.8`
    emas, `5`. Float bo'linma qirrada teskarilashadi
    (`0.3 * 10 == 3.0000000000000004`), shuning uchun ulush avval
    `SHARE_SCALE` ga ko'paytiriladi.
    """
    scaled = round(share * SHARE_SCALE)
    return -(-scaled * with_users // SHARE_SCALE)


def _verdict(
    level: Scale,
    zone_id: str,
    facts: Iterable[ZoneFact],
    *,
    share: float,
    minimum: int,
) -> ScaleVerdict:
    """§3 ning bitta qatorini bitta kattaroq zonaga qo'llash."""
    confirmed = 0
    with_users = 0
    for fact in facts:
        if fact.confirmed:
            confirmed += 1
        # Tasdiqlangan zona har doim maxrajda: aks holda ulush birdan
        # katta bo'lardi (modul izohi, «chekka holatlar»).
        if fact.has_users or fact.confirmed:
            with_users += 1

    need = max(share_need(with_users, share=share), minimum)
    if with_users == 0:
        shortfall = Shortfall.NO_ZONES
    elif confirmed >= need:
        shortfall = Shortfall.NONE
    elif confirmed < minimum:
        shortfall = Shortfall.MINIMUM
    else:
        shortfall = Shortfall.SHARE

    return ScaleVerdict(
        level=level,
        zone_id=zone_id,
        with_users=with_users,
        confirmed=confirmed,
        need=need,
        reached=shortfall is Shortfall.NONE,
        shortfall=shortfall,
    )


def _group(facts: Iterable[ZoneFact]) -> dict[str, list[ZoneFact]]:
    """Kattaroq zona bo'yicha guruhlash. Tartib — determinizm (Т-3)."""
    groups: dict[str, list[ZoneFact]] = {}
    for fact in sorted(facts, key=lambda item: (item.parent_id, item.zone_id)):
        groups.setdefault(fact.parent_id, []).append(fact)
    return groups


def districts(
    blocks: Iterable[ZoneFact],
    *,
    params: TzParams,
) -> dict[str, ScaleVerdict]:
    """§3 ning birinchi qatori: kvartallardan tumanlar.

    Kalit — tumanning identifikatori (`ZoneFact.parent_id`).
    """
    return {
        district: _verdict(
            Scale.DISTRICT,
            district,
            group,
            share=params.district_block_share,
            minimum=params.district_block_min,
        )
        for district, group in _group(blocks).items()
    }


def city(
    district_verdicts: Mapping[str, ScaleVerdict],
    *,
    city_id: str,
    params: TzParams,
) -> ScaleVerdict:
    """§3 ning ikkinchi qatori: tumanlardan shahar.

    Maxraj yana **foydalanuvchisi bor** tumanlar: tumanning o'zi
    foydalanuvchisi bor kvartalga ega bo'lsa, u shaharning maxrajiga
    kiradi. Ya'ni bo'sh tuman shaharning porogini ko'tarmaydi.
    """
    facts = tuple(
        ZoneFact(
            zone_id=verdict.zone_id,
            parent_id=city_id,
            has_users=verdict.with_users > 0,
            confirmed=verdict.reached,
        )
        for verdict in sorted(district_verdicts.values(), key=lambda item: item.zone_id)
    )
    return _verdict(
        Scale.CITY,
        city_id,
        facts,
        share=params.city_district_share,
        minimum=params.city_district_min,
    )


@dataclass(frozen=True)
class ScaleReport:
    """Bitta hodisaning §3 bo'yicha to'liq masshtabi."""

    districts: dict[str, ScaleVerdict]
    city: ScaleVerdict

    @property
    def confirmed_districts(self) -> tuple[str, ...]:
        """Tasdiqlangan tumanlar — nomlari bo'yicha tartiblangan."""
        return tuple(sorted(zone for zone, item in self.districts.items() if item.reached))

    @property
    def largest(self) -> Scale | None:
        """Kartaga chiqadigan eng katta yorliq.

        `None` — §3 ning ikkala qatori ham yig'ilmagan. Bu **normal**
        holat: uzilishlarning aksariyati kvartal miqyosida qoladi va
        u yerda masshtab yorlig'i umuman ko'rsatilmaydi.
        """
        if self.city.reached:
            return Scale.CITY
        if self.confirmed_districts:
            return Scale.DISTRICT
        return None


def evaluate(
    blocks: Iterable[ZoneFact],
    *,
    city_id: str,
    params: TzParams,
) -> ScaleReport:
    """§3 ni to'liq: kvartallar → tumanlar → shahar.

    Tartib qat'iy va §3 ning tuzilishidan kelib chiqadi: shaharning
    sanoqchisi tumanlarning **natijasi**, ularning kvartallari emas.
    """
    by_district = districts(blocks, params=params)
    return ScaleReport(
        districts=by_district,
        city=city(by_district, city_id=city_id, params=params),
    )


def from_zone_verdicts(
    verdicts: Mapping[tuple[Level, str], ZoneVerdict],
    *,
    district_of: Mapping[str, str],
    blocks_with_users: Iterable[str],
) -> tuple[ZoneFact, ...]:
    """§2.1 ning natijasini §3 ning kirishiga aylantiradi.

    `verdicts` — `tzcount.evaluate_levels()` ning javobi. Faqat
    kvartal darajasi olinadi: §3 tumanni **kvartallar** bo'yicha
    sanaydi, mahallalar bo'yicha emas (jadvalning birinchi qatori).

    `district_of` — kvartal → tuman xaritasi. Xaritada yo'q kvartal
    **tashlanadi**: uni «noma'lum tuman» degan chelakka yig'ish
    ikkita har xil tumanning kvartallarini bitta porogga qo'shardi.

    `blocks_with_users` — foydalanuvchisi bor, lekin bugun hech narsa
    xabar qilmagan kvartallar. Aynan shular §3 ning maxraji: ular
    `verdicts` da umuman yo'q, chunki dalilsiz zona baholanmaydi.

    🔴 **Sukut qiymati ataylab yo'q** (187-run). Bo'sh sukut bilan
    argumentni **yozmagan** chaqiruvchi jimgina boshqa maxrajga
    o'tardi: «foydalanuvchisi bor kvartallar» o'rniga «bugun xabar
    qilgan kvartallar». Ikkinchisi birinchisidan har doim kichik,
    ya'ni §3 ning ulushi o'z-o'zidan bajariladigan shartga aylanardi
    va tumanning verdikti teskari bo'lib chiqardi (o'lchovi —
    `tests/test_tz_walk_scale.py`). Modul javobni o'zi topa olmaydi:
    maxraj `reports` da emas, foydalanuvchilar reyestrida. Shu sabab
    bilan `tzoutage.Outage.notifies` ham sukut qiymatisiz.

    Bo'sh ro'yxat baribir haqiqiy javob — «foydalanuvchisi bor har
    bir kvartal bugun xabar qildi» — lekin u endi **aytiladi**.
    """
    reached = {
        cell: verdict.confirmable
        for (level, cell), verdict in verdicts.items()
        if level is Level.BLOCK
    }
    cells = set(reached) | set(blocks_with_users)
    return tuple(
        ZoneFact(
            zone_id=cell,
            parent_id=district_of[cell],
            has_users=True,
            confirmed=reached.get(cell, False),
        )
        for cell in sorted(cells)
        if cell in district_of
    )

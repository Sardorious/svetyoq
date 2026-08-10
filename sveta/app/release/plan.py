"""Reliz rejasi (`01` §25 «Release Plan»).

**Nima uchun bu modul bor.** `01` ning oxirida beshta reliz sanaladi va
har biriga ikkita da'vo beriladi: *nima chiqadi* (`Содержание`) va
*qachon chiqishi mumkin* (`Условие выпуска`). 66-run `03` §6 ning
to'qqizta gate ini kodga ko'chirgan edi, ya'ni repoda «chiqishga
ruxsat bormi» degan savolning **bitta** javobi allaqachon bor. §25
o'sha savolga **ikkinchi** javob beradi va ikkalasi bir-biriga hech
qayerda havola qilmaydi: §25 ning beshta shartidan birortasi ham
`03` §6 ning gate i emas.

## Asosiy qaror: reliz identifikatori umumiy kalit **emas**

Ikkala hujjat ham `R<son>.<son>` shaklidagi identifikatorlardan
foydalanadi va ular bir xil ko'rinadi. Uchtasi so'zma-so'z ustma-ust
tushadi (`R1.1`, `R2.0`, `R3.0`), lekin **bittasigina** bir xil
narsani anglatadi:

* `R1.1` — ikkalasida ham obuna va bildirishnomalar;
* `R2.0` — `01` da regional 1055 ning avtoparsingi, `03` da esa
  **ommaviy API**; rasmiy qatlam `03` da `R2.1`;
* `R3.0` — `01` da viloyat va operator bilan integratsiya, `03` da esa
  **PWA va ko'p mintaqalilik**.

Bu terminologik nuqson emas, chunki **kod allaqachon tanlagan**:
`gates.GATES` ning `G-8` i `release="R3.0"` deb yozilgan va uning
mezoni `MIN_ACTIVE_REGIONS` — ya'ni `03` ning R3.0 i; `measures` ning
`R2.0` o'qi «Ochiqlik» deb ataladi — ya'ni `03` ning ommaviy API si.
`01` §25 dan kelgan o'quvchi «R3.0 ning gate i» ni ko'rib, uni
operator bilan muzokaralar deb o'qiydi va **butunlay boshqa** shartni
ko'radi. Shuning uchun `Alias` — baho emas, ikkita hujjatni
solishtirishdan chiqadigan tasnif.

Qolgan ikkita identifikator `03` ning xaritasida umuman yo'q: `R0`
(`03` da `R0.1`/`R0.2`/`R0.3` bor, lekin ular muhandislik relizlari;
`01` ning R0 iga mos keladigan narsa `03` da **reliz emas** —
«Yopiq yig'ish rejimi») va `R1` (`03` da `R1.0` **va** `R1.2`, ya'ni
`01` ning bitta qatori ikkita relizga bo'linadi va ular orasida `G-7`
turadi).

## Ikkita mustaqil o'q

`Ship` — reliz va'da qilgan **mazmun** repoda qurilganmi; `Gate` —
uning **sharti** kim tomonidan va qayerda yopiladi. Ular bog'liq emas
va bog'liq bo'lmagani darhol ko'rinadi: `R1` ning mazmuni to'liq
qurilgan, sharti esa hech qayerda saqlanmaydi; `R0` ning sharti
yagona o'lchanadigan shart, mazmuni esa bajarib bo'lmaydi.

## Eng jim topilma: `R0` ning ikkala yarmi bitta bayroq, qarama-qarshi holatda

«Регион активен для 1–2 махаллей, **закрытый круг**». Repoda mintaqani
yoqadigan yagona narsa bor — `regions.is_active`, va u **bitta** bit:

* `geo.registry.active_regions` faqat `is_active` ni oladi, ya'ni
  o'chirilgan mintaqa xabar **qabul qilmaydi**;
* `jobs.build_map_snapshot` ham aynan o'sha ro'yxat bo'ylab yuradi,
  ya'ni yoqilgan mintaqa uchun snapshot **quriladi**;
* `api.v1.map.get_map` esa autentifikatsiyasiz va `is_active` ni
  umuman so'ramaydi — snapshot bor bo'lsa u ommaga ochiq.

Ya'ni «регион активен» `is_active = true` ni talab qiladi, «закрытый
круг» esa xarita yopiq bo'lishini; ikkinchisi uchun `is_active` ni
o'chirish kerak, o'shanda esa xabar yig'ilmaydi. `03` buni reliz emas,
**operatsion bosqich** deb ataydi («Yopiq yig'ish rejimi»,
«Ommaviy xarita **yopiq**») va qoidasini eng qat'iy shaklda yozadi:
«Xarita gate yopilmasdan ochilmaydi — bu qat'iy qoida, muhokama
predmeti emas». Bu qoidaning repoda **mexanizmi yo'q**: 66-run ning
`gates` moduli o'z izohida ochiq yozadi — «Bu modul mezonlarni
bajarmaydi (xaritani yopmaydi)».

Shuning uchun `Ship.CONTRADICTED` alohida sinf: bu tugallanmagan ish
emas (`ABSENT`) va qisman qurilgan narsa ham emas (`PARTIAL`) — repo
qatorni yozilganidek bajarishga **imkon bermaydi**, va tuzatish yangi
funksiya emas, ikkinchi bayroq talab qiladi (yig'ish yoqilgan, nashr
o'chirilgan). Bu 👤 qaror: `05` da ham, `01` da ham bunday bayroq yo'q.

Ikkinchi yarmi ham shu qatorda: «для 1–2 махаллей». Yoqishning
granulyarligi — **mintaqa** (`region_admin activate`), mahalla emas;
va `tools/import_boundaries.py` da `mahalla` so'zi umuman uchramaydi,
`quality.SQL_PROMOTE` esa faqat `districts` ga yozadi.

## `R0` ning sharti — yagona javob beriladigan shart

«Полигоны валидны» repoda **bor**: `geo.quality` oltita tekshiruv
beradi (nom to'liqligi, litsenziya, kesishuv, qamrov, geometriya
haqiqiyligi, halqa yopiqligi), ularning bir qismi `blocking=True` va
staging dan `districts` ga ko'chirish faqat undan keyin bo'ladi.
Beshta shartdan yagona `INSTRUMENTED` shu — va u aynan yagona
bajarib bo'lmaydigan qatorda turibdi. Shuni ham eslatib qo'yish
kerak: tekshiruvlar `districts` ustida yuriladi, R0 ning mazmuni esa
mahallalar haqida, ya'ni shart bo'sh to'plam ustida ham «bajarilgan»
ko'rinadi.

## Qolgan to'rtta shart: uchtasi Faza 0 ga, bittasi muzokaraga tayanadi

75-run reyestrning 18 bandidan 14 tasini `SCHEDULED` deb topgan va
sababi bitta edi: Faza 0 natijasi repoda **saqlanmaydi**. §25 o'sha
tuzoqqa ikki marta tushadi (`R1` — «Критерии выхода Ph.0 закрыты»,
`R2.0` — «P0-1 подтвердил наличие источника»), ya'ni ikkala shart ham
bugun na yopilishi, na yolg'onga chiqarilishi mumkin →
`Gate.UNRECORDED`.

`R1.1` boshqa sinf: «Накоплены данные о плотности» — o'lchov nomlangan,
**chegara esa yo'q**. `03` §6 ning G-4 i xuddi shu joyda to'xtaydi:
«Qamrov: shahar hududining ≥N% ida kamida bitta xabar *(N Faza 0
natijalari bo'yicha belgilanadi)*», va `gates.py` uni chegarasiz
qoldirgan (`threshold=None` → `UNMEASURED`). Ikkalasi bir xil
bo'shliqning ikki nusxasi → `Gate.UNQUANTIFIED`.

`R3.0` — «Переговоры результативны». Bu repodan tashqarida va
tashqarida qolishi **kerak** (67-run ning `EXTERNAL` sabog'i):
muzokara natijasiga kodda dalil yozib qo'yish shartni tekshirilgandek
ko'rsatardi. Shuning uchun `EXTERNAL` da dalil **taqiqlanadi**.

## Teskari yo'nalish: rejada yo'q ikkita qurilgan sirt

§25 ning beshta qatori mahsulotning bugungi ikkita **tugallangan**
qismini umuman nomlamaydi, va ikkalasi ham `03` da o'z relizi bilan
turibdi:

* **Ommaviy API va OpenAPI** (`03` R2.0, E15) — `01` ning `R2.0`
  o'rni band, unda 1055 turibdi. Ya'ni `01` ning rejasi bo'yicha
  ommaviy API **hech qachon** chiqmaydi, holbuki u qurilgan va
  hujjatlashtirilgan.
* **Admin-panel va moderatsiya** (`03` R0.3, E8) — `03` ning Q-2
  qarori «Moderatsiya ommaviy xaritadan **oldin** quriladi» deydi,
  §25 ning eng birinchi qatori esa allaqachon mintaqani yoqadi.

Simmetriya aniq: §25 mavjud bo'lmagan ikkita narsani (`1055`
avtoparsingi, operator integratsiyasi) reliz qilib qo'yadi va mavjud
bo'lgan ikkitasini umuman sanamaydi.

## Nima ataylab tekshirilmaydi

`Содержание` katagining **to'liqligi** baholanmaydi — u hujjatdan
so'zma-so'z olinadi va kontrakt testi shuni qulflaydi. `Ship` bahosi
katakda nomlangan narsalarning repodagi holatiga tegishli, katak
matnining qanchalik batafsil yozilganiga emas.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Jadvalning hujjatdagi manzili.
SPEC = "01 §25"

#: `03` dagi reliz xaritasining manzili — `Alias` shu jadval bilan
#: solishtirishdan chiqadi.
PEER_SPEC = "03 §3"

#: Qatorlar soni. **Aynan**: ro'yxat yopiq.
SPEC_ROWS = 5

#: Jadvalning sarlavha qatori — ustunlar tarkibi ham kontrakt.
SPEC_COLUMNS: tuple[str, ...] = ("Релиз", "Содержание", "Условие выпуска")


class Alias(StrEnum):
    """`01` ning identifikatori `03` ning xaritasida nimani anglatadi.

    Bu baho emas, ikkita hujjatni solishtirishdan chiqadigan tasnif
    (`dependencies.Referent` bilan bir xil rol).
    """

    #: Identifikator ham, mazmuni ham bir xil.
    SHARED = "shared"
    #: Identifikator bir xil, `03` esa boshqa relizni shunday ataydi.
    REASSIGNED = "reassigned"
    #: `01` ning bitta qatori `03` ning bir nechta relizini qamraydi.
    SPLIT = "split"
    #: Identifikator `03` ning xaritasida umuman yo'q.
    FOREIGN = "foreign"


#: `03` bilan **to'qnashadigan** sinf: bir xil identifikator, boshqa
#: mazmun. `SPLIT` va `FOREIGN` — nomuvofiqlik, lekin ular o'quvchini
#: yanglishtirmaydi: identifikatorni izlagan odam uni topmaydi yoki
#: ikkitasini topadi. `REASSIGNED` esa **javob beradi**, va javob
#: noto'g'ri.
COLLIDING: frozenset[Alias] = frozenset({Alias.REASSIGNED})


class Ship(StrEnum):
    """`Содержание` katagi repoda qurilganmi."""

    #: Katakda nomlangan hamma narsa bor.
    BUILT = "built"
    #: Bir qismi bor.
    PARTIAL = "partial"
    #: Yo'q; qurilishi mumkin, hali qurilmagan.
    ABSENT = "absent"
    #: Repo qatorni **yozilganidek** bajarishga imkon bermaydi.
    CONTRADICTED = "contradicted"


class Gate(StrEnum):
    """`Условие выпуска` ning javobi qayerdan keladi."""

    #: Repo javobni hisoblaydi (hech kim unga tayanmasa ham).
    INSTRUMENTED = "instrumented"
    #: Odam qadami, natijasi **qayd etilishi kerak** edi va etilmaydi.
    UNRECORDED = "unrecorded"
    #: O'lchov nomlangan, chegara esa hech bir hujjatda yo'q.
    UNQUANTIFIED = "unquantified"
    #: Mahsulotdan tashqarida va tashqarida qolishi kerak.
    EXTERNAL = "external"


#: Reja o'z savoliga javob bera oladigan yagona sinf.
ANSWERABLE = Gate.INSTRUMENTED

#: `Gate` ning kodda **dalili bo'lishi shart** bo'lgan sinflari.
#: `UNRECORDED` va `UNQUANTIFIED` da mexanizmning yo'qligi aynan baho,
#: `EXTERNAL` da esa dalil bo'lishi **mumkin emas** (67-run sabog'i):
#: muzokara natijasiga kodda havola yozish shartni tekshirilgandek
#: ko'rsatardi.
GATE_NEEDS_EVIDENCE: frozenset[Gate] = frozenset({Gate.INSTRUMENTED})


@dataclass(frozen=True)
class Row:
    """§25 ning bitta qatori.

    `release`, `content` va `condition` — hujjatdagi **so'zma-so'z**
    kataklar; kontrakt testi ularni jadvaldan parse qiladi. Qolgani —
    baho.

    `peer` — `03` ning xaritasidagi mos reliz(lar)i; `FOREIGN` da
    bo'sh. `alias_binds` faqat `REASSIGNED` da to'ldiriladi va koddagi
    **o'sha identifikatorni ishlatayotgan** simvolga ishora qiladi:
    to'qnashuv shu bilan nazariy emas, kuzatiladigan bo'ladi.
    """

    code: str
    release: str
    content: str
    condition: str
    alias: Alias
    peer: tuple[str, ...]
    ship: Ship
    gate: Gate
    note: str
    ship_binds: tuple[str, ...] = ()
    gate_binds: tuple[str, ...] = ()
    alias_binds: tuple[str, ...] = ()

    @property
    def collides(self) -> bool:
        """Kod bu identifikatorni `03` ning ma'nosida ishlatadi."""
        return self.alias in COLLIDING

    @property
    def is_answerable(self) -> bool:
        return self.gate is ANSWERABLE

    @property
    def is_shippable(self) -> bool:
        """Qator yozilganidek bajarilishi **mumkinmi**.

        `ABSENT` va `PARTIAL` — qarz; `CONTRADICTED` esa boshqa narsa:
        qarzni to'lash yo'li ham yo'q.
        """
        return self.ship is not Ship.CONTRADICTED


@dataclass(frozen=True)
class UnplannedSurface:
    """Qurilgan, §25 da esa relizi yo'q sirt (teskari yo'nalish)."""

    code: str
    phrase: str
    #: `03` da uning relizi bor — ya'ni bo'shliq `01` ga xos.
    peer: str
    why_not_covered: str
    binds: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# Reyestr
# --------------------------------------------------------------------------

#: **Tartib ma'noli** — hujjatdagi bilan bir xil, kontrakt testi shuni
#: qulflaydi. `code` lar §25 da yo'q (jadvalda `ID` ustuni yo'q) va
#: tartibdan yasaladi: `RP-N` = N-qator.
ROWS: tuple[Row, ...] = (
    Row(
        code="RP-1",
        release="R0 (пилот)",
        content="Регион активен для 1–2 махаллей, закрытый круг",
        condition="Полигоны валидны",
        alias=Alias.FOREIGN,
        peer=(),
        ship=Ship.CONTRADICTED,
        gate=Gate.INSTRUMENTED,
        note=(
            "Qatorning ikkala yarmi bitta bayroqni qarama-qarshi "
            "holatda talab qiladi. `regions.is_active` — yagona "
            "kalit: `registry.active_regions` bo'yicha o'chirilgan "
            "mintaqa xabar qabul qilmaydi, `jobs.build_map_snapshot` "
            "esa aynan o'sha ro'yxat uchun snapshot quradi va "
            "`get_map` uni autentifikatsiyasiz beradi. «Yig'ish "
            "yoqilgan, nashr o'chirilgan» holati uchun ikkinchi "
            "bayroq kerak va u `01` da ham, `05` da ham yo'q. `03` "
            "buni reliz emas, operatsion bosqich deb ataydi va "
            "qoidasini «muhokama predmeti emas» deb yozadi — "
            "mexanizmi esa yo'q (`gates` moduli xaritani yopmaydi). "
            "Granulyarlik ham mos emas: yoqish mintaqa darajasida, "
            "mahalla poligonlarining import yo'li umuman yo'q. Sharti "
            "esa beshtadan yagona o'lchanadigani — `geo.quality` "
            "oltita tekshiruv beradi va `SQL_PROMOTE` ulardan keyin "
            "yuradi (faqat `districts` uchun)."
        ),
        ship_binds=(
            "app.geo.registry:active_regions",
            "app.jobs.build_map_snapshot:run",
            "app.api.v1.map:get_map",
            "tools.region_admin:cmd_activate",
        ),
        gate_binds=(
            "app.geo.quality:check_validity",
            "app.geo.quality:check_closed_rings",
            "app.geo.quality:SQL_PROMOTE",
        ),
    ),
    Row(
        code="RP-2",
        release="R1 (MVP)",
        content="Город целиком, UZ-first, карта, статистика",
        condition="Критерии выхода Ph.0 закрыты",
        alias=Alias.SPLIT,
        peer=("R1.0", "R1.2"),
        ship=Ship.BUILT,
        gate=Gate.UNRECORDED,
        note=(
            "Mazmunning to'rtala qismi ham repoda bor: shahar bbox "
            "bilan (E19), `DEFAULT_LANGUAGE = \"uz\"`, `/api/v1/map` "
            "va `app/stats/`. Lekin `03` ularni **ikkita** relizga "
            "ajratadi — statistika R1.2 da va uning oldida `G-7` "
            "turadi, ya'ni `01` ning bitta qatori bo'yicha ishlagan "
            "odam gate ni chetlab o'tardi. Sharti esa §24 ning beshta "
            "belgisiga havola qiladi va ularning birortasi repoda "
            "saqlanmaydi (75-run: 18 banddan 14 tasi `SCHEDULED`). "
            "⚠️ `UZ-first` ning o'zi ham to'liq emas: mintaqaning "
            "`default_language` i botga yetmaydi (75-run, `RS-08`) — "
            "lekin bu shartning emas, mexanizmning qirrasi va u "
            "o'sha yerda qayd etilgan."
        ),
        ship_binds=(
            "app.core.i18n:DEFAULT_LANGUAGE",
            "app.api.v1.map:get_map",
            "app.stats.service:region_coverage",
            "app.geo.registry:active_regions",
        ),
    ),
    Row(
        code="RP-3",
        release="R1.1",
        content="Подписки и уведомления с калиброванным радиусом",
        condition="Накоплены данные о плотности",
        alias=Alias.SHARED,
        peer=("R1.1",),
        ship=Ship.PARTIAL,
        gate=Gate.UNQUANTIFIED,
        note=(
            "Uchta ustma-tushgan identifikatordan yagonasi bir xil "
            "narsani anglatadi. Mexanizm to'liq: obuna, outbox, "
            "yetkazish, radius bo'yicha tanlash (E13). Kalibrlash esa "
            "yo'q — `subscription_default_radius_m` hali ham 500 m, "
            "ya'ni Toshkentniki (74-run). Shart chegarasiz: «данные о "
            "плотности» qancha ekani na `01` da, na `03` da yozilgan, "
            "va `03` §6 ning G-4 i xuddi shu joyda `threshold=None` "
            "bilan `UNMEASURED` bo'lib turibdi."
        ),
        ship_binds=(
            "app.notifications.service:process",
            "app.core.config:Settings",
        ),
    ),
    Row(
        code="RP-4",
        release="R2.0",
        content="Автопарсинг регионального 1055, махаллинские витрины",
        condition="P0-1 подтвердил наличие источника",
        alias=Alias.REASSIGNED,
        peer=("R2.1",),
        ship=Ship.PARTIAL,
        gate=Gate.UNRECORDED,
        note=(
            "`03` da `R2.0` — **ommaviy API**, rasmiy qatlam esa "
            "`R2.1`. Kod `03` ni tanlagan: `measures` ning `R2.0` o'qi "
            "«Ochiqlik» deb ataladi. Mazmunning ikkinchi yarmi "
            "(mahalla vitrinalari) qurilgan va bo'shligini o'zi e'lon "
            "qiladi (`WARNING_MISSING`), birinchi yarmi esa yo'q: "
            "`app/` da rasmiy kod bilan xabar yaratadigan chaqiruv "
            "yo'q (76-run, `DP-4`). Sharti `P0-1` ga tayanadi — "
            "`RP-2` bilan bir xil sabab."
        ),
        ship_binds=(
            "app.stats.mahalla_coverage:WARNING_MISSING",
            "app.reports.sources:AUTHORITATIVE_CODES",
        ),
        alias_binds=("app.release.measures:MEASURES",),
    ),
    Row(
        code="RP-5",
        release="R3.0",
        content="Область, интеграция с оператором",
        condition="Переговоры результативны",
        alias=Alias.REASSIGNED,
        peer=(),
        ship=Ship.ABSENT,
        gate=Gate.EXTERNAL,
        note=(
            "`03` da `R3.0` — PWA va ko'p mintaqalilik, va `G-8` aynan "
            "shu identifikatorga bog'langan (`MIN_ACTIVE_REGIONS`), "
            "ya'ni to'qnashuv kodda **ishlab turibdi**: §25 dan kelgan "
            "o'quvchi «R3.0 ning gate i» ni operator bilan muzokara "
            "deb o'qiydi va ikkinchi mintaqaning mezonini ko'radi. "
            "Mazmuniga mos keladigan `03` relizi **yo'q**: viloyat "
            "tumanlari va operator integratsiyasi `03` da umuman "
            "rejalashtirilmagan (E18/E19 ning ikkalasi ham boshqa "
            "narsa). Sharti — muzokara, ya'ni repodan tashqarida va "
            "tashqarida qolishi kerak."
        ),
        alias_binds=("app.release.gates:GATES",),
    ),
)

ROW_BY_CODE: dict[str, Row] = {r.code: r for r in ROWS}


#: §25 da relizi yo'q, repoda esa qurilgan sirtlar.
UNPLANNED: tuple[UnplannedSurface, ...] = (
    UnplannedSurface(
        code="UP-1",
        phrase="Ommaviy API va OpenAPI",
        peer="R2.0",
        why_not_covered=(
            "`01` ning `R2.0` o'rni band — unda 1055 turibdi, ya'ni "
            "§25 ning rejasi bo'yicha ommaviy API hech qachon "
            "chiqmaydi. Holbuki u qurilgan (E15) va hujjatlashtirilgan: "
            "`/openapi.json` ochiq, `01` §16 esa API talablarini "
            "alohida bo'lim qilib beradi."
        ),
        binds=("app.main:create_app", "app.api.v1.geo:router"),
    ),
    UnplannedSurface(
        code="UP-2",
        phrase="Admin-panel va moderatsiya",
        peer="R0.3",
        why_not_covered=(
            "`03` ning Q-2 qarori «Moderatsiya ommaviy xaritadan oldin "
            "quriladi» deydi va unga alohida reliz beradi; §25 ning eng "
            "birinchi qatori esa allaqachon mintaqani yoqadi. "
            "Moderatsiya, rollar va audit qurilgan (E8) — reja ularni "
            "birorta relizda nomlamaydi."
        ),
        binds=("app.admin.roles:Permission", "app.admin.audit:record"),
    ),
)


# --------------------------------------------------------------------------
# Reyestrning o'z qoidalari
# --------------------------------------------------------------------------


def _check_registry() -> None:
    """Reyestr o'z-o'ziga zid bo'lsa import paytida yiqiladi.

    Bu tekshiruvlar kontrakt testining o'rnini bosmaydi — ular
    reyestrni **yozayotgan** odamga qaratilgan (`dependencies` bilan
    bir xil rol).
    """
    if len(ROWS) != SPEC_ROWS:
        raise ValueError(f"{SPEC}: {len(ROWS)} qator, kutilgani {SPEC_ROWS}")
    if len(ROW_BY_CODE) != len(ROWS):
        raise ValueError(f"{SPEC}: takrorlangan kod")
    for index, row in enumerate(ROWS, start=1):
        if row.code != f"RP-{index}":
            raise ValueError(f"{SPEC}: `{row.code}` {index}-qatorda turibdi")
        if not row.note:
            raise ValueError(f"{SPEC}: `{row.code}` izohsiz")
        if row.ship is Ship.ABSENT and row.ship_binds:
            raise ValueError(
                f"{SPEC}: `{row.code}` — `ABSENT`, lekin mazmun dalili "
                f"ko'rsatilgan: {row.ship_binds}"
            )
        if row.ship is not Ship.ABSENT and not row.ship_binds:
            raise ValueError(f"{SPEC}: `{row.code}` — `{row.ship}`, dalil yo'q")
        if row.gate in GATE_NEEDS_EVIDENCE and not row.gate_binds:
            raise ValueError(f"{SPEC}: `{row.code}` — `{row.gate}`, dalil yo'q")
        if row.gate not in GATE_NEEDS_EVIDENCE and row.gate_binds:
            raise ValueError(
                f"{SPEC}: `{row.code}` — `{row.gate}`, lekin shart dalili "
                f"ko'rsatilgan: {row.gate_binds}"
            )
        # To'qnashuv — kodda **ko'rinadigan** narsa: bir xil
        # identifikatorni `03` ning ma'nosida ishlatayotgan simvol.
        # Dalilsiz `REASSIGNED` shunchaki fikr bo'lardi.
        if row.collides and not row.alias_binds:
            raise ValueError(f"{SPEC}: `{row.code}` — to'qnashuv dalilsiz")
        if not row.collides and row.alias_binds:
            raise ValueError(
                f"{SPEC}: `{row.code}` — `{row.alias}`, to'qnashuv dalili ortiqcha"
            )
        # `FOREIGN` — `03` da mos keladigan reliz yo'qligi; `SPLIT` esa
        # aynan bittadan ko'p. Aralashib ketsa hisobotdagi «ikki
        # hujjat qayerda ustma-ust tushadi» savoli ma'nosini yo'qotardi.
        if row.alias is Alias.FOREIGN and row.peer:
            raise ValueError(f"{SPEC}: `{row.code}` — `FOREIGN`, lekin mosi bor")
        if row.alias is Alias.SPLIT and len(row.peer) < 2:
            raise ValueError(f"{SPEC}: `{row.code}` — `SPLIT` bittadan ko'pini talab qiladi")
        if row.alias is Alias.SHARED and row.peer != (row.release,):
            raise ValueError(f"{SPEC}: `{row.code}` — `SHARED`, lekin mosi boshqa nomda")
        if row.alias is Alias.REASSIGNED and row.release in row.peer:
            raise ValueError(
                f"{SPEC}: `{row.code}` — `REASSIGNED`, lekin o'z nomiga mos kelyapti"
            )
    for item in UNPLANNED:
        if not item.binds:
            raise ValueError(f"{SPEC}: `{item.code}` dalilsiz")
        if not item.why_not_covered:
            raise ValueError(f"{SPEC}: `{item.code}` izohsiz")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanReport:
    """`01` §25 ning bugungi holati."""

    rows: tuple[Row, ...]
    unplanned: tuple[UnplannedSurface, ...]

    @property
    def by_alias(self) -> dict[Alias, tuple[Row, ...]]:
        return {a: tuple(r for r in self.rows if r.alias is a) for a in Alias}

    @property
    def by_ship(self) -> dict[Ship, tuple[Row, ...]]:
        return {s: tuple(r for r in self.rows if r.ship is s) for s in Ship}

    @property
    def by_gate(self) -> dict[Gate, tuple[Row, ...]]:
        return {g: tuple(r for r in self.rows if r.gate is g) for g in Gate}

    @property
    def colliding(self) -> tuple[Row, ...]:
        """Bir xil identifikator, `03` da boshqa reliz.

        Hisobotning eng muhim ro'yxati: bunday qator **javob beradi**,
        va javob noto'g'ri.
        """
        return tuple(r for r in self.rows if r.collides)

    @property
    def unshippable(self) -> tuple[Row, ...]:
        """Yozilganidek bajarib bo'lmaydigan qatorlar."""
        return tuple(r for r in self.rows if not r.is_shippable)

    @property
    def answerable(self) -> tuple[Row, ...]:
        """Sharti repoda javob topadigan qatorlar."""
        return tuple(r for r in self.rows if r.is_answerable)

    @property
    def phase_zero_bound(self) -> tuple[Row, ...]:
        """Sharti Faza 0 ning qayd etilmagan natijasiga tayanadiganlar."""
        return tuple(r for r in self.rows if r.gate is Gate.UNRECORDED)

    @property
    def accurate(self) -> bool:
        """Reja bugungi haqiqatni to'g'ri tasvirlaydimi.

        Uchta shart: identifikator to'qnashuvi bo'lmasin, har qator
        yozilganidek bajarilishi mumkin bo'lsin va rejadan tashqarida
        qurilgan sirt qolmasin.
        """
        return not self.colliding and not self.unshippable and not self.unplanned


def evaluate() -> PlanReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi
    (`dependencies.evaluate` bilan bir xil sabab).
    """
    return PlanReport(rows=ROWS, unplanned=UNPLANNED)

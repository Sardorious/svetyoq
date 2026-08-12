"""Yuqori darajali arxitektura (`BRD` §24) ↔ qurilgan mahsulot.

**Nima uchun bu modul bor.** §24 — BRD ning mahsulotni **konteynerlar**
darajasida chizadigan bo'limi: §24.1 C4 diagrammasi (19 tugun — 11
platforma, 4 ombor, 4 tashqi tizim) va §24.2 oltita arxitektura qarori.
`01` §29 uchun bunday qatlam allaqachon bor (`app.core.architecture`,
78–81-runlar); §24 esa shu paytgacha hech qayerda o'qilmagan — va u §29
bilan **bir xil sarlavha ostida boshqa mahsulotni** chizadi.

## Birinchi topilma: ikkita «High-Level Architecture» bir-biriga zid

`01` §29 o'n tugun chizadi va «архитектура наследуется без изменений,
единственное следствие — GEO» deydi. BRD §24 esa o'n to'qqiz tugun
chizadi: unda §29 umuman tilga olmagan **beshta konteyner** bor
(`S24_ONLY_CONTAINERS` — API Gateway, Territory Registry, Official
Source Ingestor, Analytics Service, Object Storage), va TERR alohida
«НОВОЕ» komponent deb e'lon qilinadi — ya'ni «faqat GEO o'zgaradi»
jumlasiga BRD ning o'zi qarshi chiqadi. Ikkala bo'lim bir-biriga
havola bermaydi; qaysi rasm «qonun» — hujjatlar javob bermaydi (👤).

## Ikkinchi topilma: chizma monolitga qarshi, qarorlar esa mos

§24.1 mikroservis topologiyasini chizadi: alohida Go-bot, API Gateway,
worker lar, Kafka shinasi, Redis kesh, Object Storage. Repo esa ataylab
monolit: ADR-05 Kafka/Redis ni chiqargan (`CON-05` savoli bilan bitta
ildiz), gateway ham, ombor ham yo'q — o'n to'qqiz tugundan oltitasi
`ABSENT`, yana yettitasi monolit moduli sifatida yashaydi. **Lekin
§24.2 dagi oltita qarordan beshtasi bajarilgan** (mintaqa
konfiguratsiya sifatida, H3, mahalla, mintaqaviy parametrlar, manba
qatlamlari). Bitta bo'limning ikki yarmi har xil aniqlikda: qarorlar
jadvali mahsulotga mos, chizma — yo'q. Chizma Toshkent paketidan meros
va forkda qayta chizilmagan (78-run «наследуется» tuzog'ining davomi).

## Uchinchi topilma: texnologiya yorliqlari yolg'on

Uch tugunning yorlig'i mavjud kodga zid: bot «Go» deb chizilgan —
aiogram/Python; web «React» — ataylab vanilla JS (`web/README`);
klasterlash «DBSCAN» worker — sinxron inkremental biriktirish
(`05` §4.1 buni ataylab tanlagan). Bular `ABSENT` emas: funksiya bor,
yorliq noto'g'ri — alohida `RESHAPED` sinfi shu uchun.

## To'rtinchi topilma: ikki va'da uchun kod umuman yo'q

`ING` (парсинг публикаций, NER) — rasmiy manba qoidasi kodda bor
(`app.reports.sources`: og'irliksiz, darhol `confirmed`), lekin uni
**avtomatik kiritadigan** hech narsa yo'q — manba qo'lda belgilanadi,
NER umuman uchramaydi. `GC` (tashqi geokoder) — konfiguratsiyada
provayder kaliti bor, klient kodi yo'q (H-6 ochiq gipoteza). Diagramma
`SRC` ni o'zi «ГИПОТЕЗА» deb belgilaydi — bu hech bo'lmaganda halol.

## O'qish tartibi

`NODES` — §24.1 tugunlari hujjatdagi tartibda (platforma, ombor,
tashqi); `label` katagi diagramma matni bilan aynan (kontrakt test
hujjatdan qayta o'qiydi). `DECISIONS` — §24.2 jadvali. Baho kod dalili
(`binds`) bilan. `evaluate()` — yig'ma hisobot, `app.admin.registries`
indeksi o'qiydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.core import architecture as prd_arch
from app.release import business_environment as benv

#: Hujjat bo'limi. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "BRD §24"

#: §24.1 diagrammasining o'lchamlari — hujjatdan parse qilinadi.
SPEC_PLATFORM_NODES = 11
SPEC_DATA_NODES = 4
SPEC_EXTERNAL_NODES = 4
SPEC_DECISION_ROWS = 6

#: §24 chizadigan, `01` §29 esa umuman tilga olmaydigan konteynerlar —
#: birinchi topilmaning langari. Test ikkala bo'limdan tekshiradi:
#: §24 da bor, §29 da yo'q.
S24_ONLY_CONTAINERS: tuple[str, ...] = (
    "API Gateway",
    "Territory Registry",
    "Official Source Ingestor",
    "Analytics Service",
    "Object Storage",
)


class Zone(StrEnum):
    """Tugun diagrammaning qaysi qismida turadi."""

    PLATFORM = "platform"
    DATA = "data"
    EXTERNAL = "external"


class Map(StrEnum):
    """§24.1 tuguni bugungi kodga qanday tushadi."""

    #: Chizilganidek bor — shakli ham, mazmuni ham mos.
    AS_DRAWN = "as_drawn"
    #: Funksiya bor, lekin alohida konteyner emas — monolit moduli.
    IN_MONOLITH = "in_monolith"
    #: Funksiya bor, lekin yorliq (til, freymvork, algoritm) kodga zid.
    RESHAPED = "reshaped"
    #: Kodda hech narsa yo'q.
    ABSENT = "absent"


class Held(StrEnum):
    """§24.2 qarori repoda amal qiladimi."""

    HONORED = "honored"
    PARTIAL = "partial"
    BREACHED = "breached"


class BusinessArchitectureError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class NodeRow:
    """§24.1 ning bitta tuguni — `label` diagramma matni bilan aynan."""

    node_id: str
    label: str
    zone: Zone
    map: Map
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


@dataclass(frozen=True)
class DecisionRow:
    """§24.2 jadvalining bitta qatori — `decision` hujjat katagi bilan aynan."""

    decision: str
    held: Held
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


# --------------------------------------------------------------------------
# §24.1 — tugunlar, diagrammadagi tartibda
# --------------------------------------------------------------------------

NODES: tuple[NodeRow, ...] = (
    NodeRow(
        node_id="BOT",
        label="Telegram Bot Service<br/>Go — приём репортов, UZ по умолчанию",
        zone=Zone.PLATFORM,
        map=Map.RESHAPED,
        note=(
            "Repport qabuli va UZ-default bor, lekin bot aiogram/Python "
            "(webhook), monolit ichida — «Go» hech qachon bo'lmagan. "
            "Uchinchi topilmaning birinchi yorlig'i."
        ),
        binds=("app.bot.factory:create_bot", "app.bot.webhook"),
        gap="«Go» yorlig'i yolg'on — bot aiogram (Python), alohida servis emas.",
    ),
    NodeRow(
        node_id="WEB",
        label="Web App<br/>React + MapLibre — карта, витрины",
        zone=Zone.PLATFORM,
        map=Map.RESHAPED,
        note=(
            "Xarita va vitrinalar bor (statik build, MapLibre), lekin React "
            "ataylab kiritilmagan (`web/README` sababi bilan yozadi) — "
            "yorliq `05` §1 dan ko'chirilgan va kod bilan tekshirilmagan."
        ),
        binds=("web/app.js", "web/index.html"),
        gap="«React» deklaratsiyasi — kod vanilla JS (ataylab, `web/README`).",
    ),
    NodeRow(
        node_id="ADM",
        label="Admin Panel<br/>React — модерация, территории",
        zone=Zone.PLATFORM,
        map=Map.IN_MONOLITH,
        note=(
            "Moderatsiya oqimi API sathida bor (admin xizmati, audit, "
            "digest), hududlar asboblarda — lekin React panel ham, umuman "
            "alohida UI ham yo'q."
        ),
        binds=("app.admin.service", "app.admin.audit"),
        gap="React panel yo'q — moderatsiya faqat API sathida.",
    ),
    NodeRow(
        node_id="GW",
        label="API Gateway<br/>rate limit, authn/z, версионирование",
        zone=Zone.PLATFORM,
        map=Map.IN_MONOLITH,
        note=(
            "Uchala funksiya monolit ichida yashaydi: rate limit intake va "
            "admin sathida, autentifikatsiya `app.admin.auth`, versiya "
            "`app.api.v1` prefiksi. Alohida gateway komponenti yo'q — "
            "§29 bu tugunni umuman chizmagan (birinchi topilma)."
        ),
        binds=("app.reports.intake:check_rate_limit", "app.admin.auth", "app.api.v1"),
        gap="Alohida gateway yo'q — uch funksiya monolit ichida tarqoq.",
    ),
    NodeRow(
        node_id="CORE",
        label="Core API<br/>инциденты, репорты, подписки",
        zone=Zone.PLATFORM,
        map=Map.IN_MONOLITH,
        note=(
            "Uchala predmet ham bor: hodisalar (`outages`), repportlar "
            "(`intake`), obunalar (`subscriptions`) — FastAPI monoliti "
            "ichida, alohida servis sifatida emas."
        ),
        binds=("app.api.router", "app.reports.intake:create_report"),
    ),
    NodeRow(
        node_id="GEO",
        label="Geo Service<br/>НОВОЕ: район → махалля → H3",
        zone=Zone.PLATFORM,
        map=Map.IN_MONOLITH,
        note=(
            "Uch darajali biriktirish to'liq bor (`ST_Contains` quvuri, "
            "H3 kataklari) — `app.geo` moduli sifatida. §29 bilan mos "
            "keladigan yagona «НОВОЕ» belgisi shu."
        ),
        binds=("app.geo.pipeline:find_mahalla_id", "app.geo.h3_cells"),
    ),
    NodeRow(
        node_id="TERR",
        label="Territory Registry<br/>НОВОЕ: версионирование границ",
        zone=Zone.PLATFORM,
        map=Map.IN_MONOLITH,
        note=(
            "Versiyalash bor, lekin faqat mahalla qatlamida "
            "(`valid_from`/`valid_to`) va alohida komponent emas — AC-1.2 "
            "ning `PARTIAL` holati bilan bitta fakt. §29 bu tugunni "
            "chizmagan, §24 esa «НОВОЕ» deydi — ikkala hujjat ham qonun."
        ),
        binds=("app.geo.mahallas:MahallaRegistry",),
        gap="Versiyalash faqat mahalla qatlamida; alohida komponent yo'q (AC-1.2).",
    ),
    NodeRow(
        node_id="CLU",
        label="Clustering Worker<br/>DBSCAN, региональные параметры",
        zone=Zone.PLATFORM,
        map=Map.RESHAPED,
        note=(
            "Mintaqaviy parametrlar rost (`region_config` dan, `06` §9), "
            "lekin algoritm DBSCAN emas — inkremental biriktirish "
            "(`05` §4.1 ataylab tanlagan) va worker ham emas: biriktirish "
            "repport tranzaksiyasida sinxron chaqiriladi."
        ),
        binds=("app.clustering.service", "app.clustering.params:from_mapping"),
        gap="«DBSCAN worker» emas — sinxron inkremental biriktirish (`05` §4.1).",
    ),
    NodeRow(
        node_id="NOT",
        label="Notification Engine<br/>подписки на точку и махаллю",
        zone=Zone.PLATFORM,
        map=Map.IN_MONOLITH,
        note=(
            "Obuna va yetkazish quvuri bor (outbox, sender), lekin obuna "
            "faqat nuqta+radius shaklida (`Subscription.geom`/`radius_m`) — "
            "«подписка на махаллю» kodda ifodalanmagan."
        ),
        binds=("app.notifications.subscriptions", "app.notifications.outbox"),
        gap="Mahalla obunasi yo'q — obuna faqat nuqta+radius.",
    ),
    NodeRow(
        node_id="ING",
        label="Official Source Ingestor<br/>парсинг публикаций, NER",
        zone=Zone.PLATFORM,
        map=Map.ABSENT,
        note=(
            "To'rtinchi topilmaning birinchi yarmi: rasmiy manba qoidasi "
            "kodda bor (`app.reports.sources` — og'irliksiz, darhol "
            "`confirmed`), lekin publikatsiyani o'qiydigan, parse "
            "qiladigan yoki NER yurgizadigan hech narsa yo'q — manba "
            "qo'lda belgilanadi."
        ),
        gap="Parser ham, NER ham yo'q — rasmiy manba qo'lda kiritiladi (H-4 ochiq).",
    ),
    NodeRow(
        node_id="STAT",
        label="Analytics Service<br/>витрины, Coverage Index",
        zone=Zone.PLATFORM,
        map=Map.IN_MONOLITH,
        note=(
            "Vitrinalar ham, Coverage Index ham bor (`app.stats`) — "
            "monolit moduli sifatida, alohida servis emas."
        ),
        binds=("app.stats.service", "app.stats.coverage"),
    ),
    NodeRow(
        node_id="PG",
        label="PostgreSQL 16 + PostGIS<br/>reports, outages, territories",
        zone=Zone.DATA,
        map=Map.AS_DRAWN,
        note=(
            "Diagrammaning kodga to'liq mos tushadigan kam sonli "
            "tugunlaridan biri: baza ham, uchala predmet jadvali ham bor."
        ),
        binds=("app.db", "alembic/versions"),
    ),
    NodeRow(
        node_id="RD",
        label="Redis<br/>кеш карты и справочников",
        zone=Zone.DATA,
        map=Map.ABSENT,
        note=(
            "ADR-05 chiqargan (`05` §11, qaytish sharti `03` §9 da) — "
            "kesh qatlami umuman yo'q. `CON-05` savoli bilan bitta ildiz; "
            "§29 dagi egizagi `app.core.architecture` da `DECLINED`."
        ),
        gap="ADR-05 rad etgan — kesh yo'q (`CON-05` bilan bitta savol, 👤).",
    ),
    NodeRow(
        node_id="KF",
        label="Kafka<br/>шина событий",
        zone=Zone.DATA,
        map=Map.ABSENT,
        note=(
            "ADR-05: o'rnida tranzaksion outbox (`app.notifications."
            "outbox`), shina yo'q. Diagrammadagi hodisa oqimining o'zagi "
            "shu tugun orqali o'tadi — usiz ING→KF→CLU zanjiri ham chizma "
            "bo'lib qoladi."
        ),
        gap="ADR-05: o'rnida tranzaksion outbox — shina yo'q (`CON-05`, 👤).",
    ),
    NodeRow(
        node_id="OBJ",
        label="Object Storage<br/>архив, выгрузки",
        zone=Zone.DATA,
        map=Map.ABSENT,
        note=(
            "Ombor yo'q: eksport so'rov vaqtida CSV yasab beradi "
            "(`app.stats.export`), hech narsa arxivlanmaydi."
        ),
        gap="Ombor yo'q — eksport so'rovda yasaladi, arxiv saqlanmaydi.",
    ),
    NodeRow(
        node_id="TG",
        label="Telegram Bot API",
        zone=Zone.EXTERNAL,
        map=Map.AS_DRAWN,
        note="Yagona kirish kanali — webhook orqali (CON-04 bilan mos).",
        binds=("app.bot.webhook",),
    ),
    NodeRow(
        node_id="GC",
        label="Геокодер",
        zone=Zone.EXTERNAL,
        map=Map.ABSENT,
        note=(
            "To'rtinchi topilmaning ikkinchi yarmi: konfiguratsiyada "
            "`geocoder_provider`/`geocoder_api_key` kalitlari bor, lekin "
            "ularni o'qiydigan klient kodi yo'q — biriktirish faqat "
            "koordinata orqali. H-6 gipotezasi ochiq."
        ),
        gap="Klient kodda yo'q — konfiguratsiyada faqat provayder kaliti (H-6).",
    ),
    NodeRow(
        node_id="TILE",
        label="Тайловый сервис",
        zone=Zone.EXTERNAL,
        map=Map.AS_DRAWN,
        note=(
            "Tashqi tayl manbasi konfiguratsiyadan keladi (`map_tile_url`) "
            "va xarita konfiguratsiya javobida ochiq uzatiladi."
        ),
        binds=("app.core.config:Settings", "web/app.js"),
    ),
    NodeRow(
        node_id="SRC",
        label="Публичные каналы об отключениях<br/>ГИПОТЕЗА: источник по региону",
        zone=Zone.EXTERNAL,
        map=Map.ABSENT,
        note=(
            "Diagramma o'zi «ГИПОТЕЗА» deb belgilaydi — H-4 tekshirilmagan "
            "(Ph.0 odamniki), oqim ulanmagan. ING `ABSENT` bo'lgani uchun "
            "ulanadigan joyning o'zi ham yo'q."
        ),
        gap="H-4 tekshirilmagan va oqim ulanmagan — diagramma o'zi gipoteza deydi.",
    ),
)


# --------------------------------------------------------------------------
# §24.2 — qarorlar, hujjatdagi tartibda
# --------------------------------------------------------------------------

DECISIONS: tuple[DecisionRow, ...] = (
    DecisionRow(
        decision="Единая платформа, регион как конфигурация",
        held=Held.HONORED,
        note=(
            "Mintaqa bazadagi konfiguratsiya obyekti (`RegionInfo`: bbox, "
            "standart til) va `region_admin` asbobi bilan kod "
            "o'zgarishisiz qo'shiladi — AC-1.5 ning `LIVE` holati."
        ),
        binds=("app.geo.registry:RegionInfo", "tools/region_admin.py"),
    ),
    DecisionRow(
        decision="Territory Registry как отдельный компонент",
        held=Held.PARTIAL,
        note=(
            "«Сквозная функция» yarmi rost: mahalla versiyalari vitrina va "
            "chegara hisobotiga ulangan. «Отдельный компонент» yarmi yo'q "
            "va tuman/mintaqa qatlamlari versiyasiz (TERR tuguni bilan "
            "bitta fakt)."
        ),
        binds=("app.geo.mahallas:MahallaRegistry", "app.stats.boundaries:summarize"),
        gap="Komponent alohida emas va versiyalash faqat mahalla qatlamida.",
    ),
    DecisionRow(
        decision="H3 как третий уровень",
        held=Held.HONORED,
        note=(
            "H3 uchinchi daraja sifatida quvurda ham, issiqlik xaritasida "
            "ham ishlaydi — agregatsiya aynan katak bo'yicha."
        ),
        binds=("app.geo.h3_cells", "app.stats.heatmap"),
    ),
    DecisionRow(
        decision="Махалля как средний уровень",
        held=Held.HONORED,
        note=(
            "Repport mahallaga `ST_Contains` bilan biriktiriladi va "
            "foydalanuvchi javoblarida mahalla nomi ko'rinadi."
        ),
        binds=("app.geo.pipeline:find_mahalla_id",),
    ),
    DecisionRow(
        decision="Региональные параметры валидации",
        held=Held.HONORED,
        note=(
            "`06` §9: barcha porog va koeffitsiyentlar `region_config` "
            "dan, kod konstantasi emas — Toshkent qiymatlari standart "
            "sifatida ko'chmaydi."
        ),
        binds=("app.clustering.params:from_mapping",),
    ),
    DecisionRow(
        decision="Разделение слоёв источников",
        held=Held.HONORED,
        note=(
            "Manba qatlamlari ajratilgan: og'irlikli fuqaro manbalari va "
            "og'irliksiz rasmiy manba (`06` §2.2), hodisada `crowd`/"
            "`official` qatlamlari alohida."
        ),
        binds=("app.reports.sources:SOURCES", "app.clustering.models:OUTAGE_LAYERS"),
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessArchitectureReport:
    """BRD §24 ning bugungi holati."""

    nodes: tuple[NodeRow, ...]
    decisions: tuple[DecisionRow, ...]

    def __post_init__(self) -> None:
        self._check_counts()
        self._check_evidence()
        self._check_neighbors()

    # -- qorovullar --------------------------------------------------------

    def _check_counts(self) -> None:
        zones = {
            Zone.PLATFORM: SPEC_PLATFORM_NODES,
            Zone.DATA: SPEC_DATA_NODES,
            Zone.EXTERNAL: SPEC_EXTERNAL_NODES,
        }
        for zone, want in zones.items():
            got = sum(1 for n in self.nodes if n.zone is zone)
            if got != want:
                raise BusinessArchitectureError(
                    f"§24.1 {zone} tugunlari soni hujjatga mos emas: {got} != {want}"
                )
        if len(self.decisions) != SPEC_DECISION_ROWS:
            raise BusinessArchitectureError("§24.2 qatorlari soni hujjatga mos emas")
        ids = tuple(n.node_id for n in self.nodes)
        if len(ids) != len(set(ids)):
            raise BusinessArchitectureError("§24.1 tugun identifikatorlari takrorlandi")

    def _check_evidence(self) -> None:
        for node in self.nodes:
            if node.map is Map.ABSENT and node.binds:
                raise BusinessArchitectureError(
                    f"{node.node_id}: `ABSENT` da dalil bo'lmaydi"
                )
            if node.map is not Map.ABSENT and not node.binds:
                raise BusinessArchitectureError(
                    f"{node.node_id}: {node.map} dalilsiz bo'lmaydi"
                )
            if node.map in (Map.RESHAPED, Map.ABSENT) and not node.gap:
                raise BusinessArchitectureError(
                    f"{node.node_id}: farq bor, `gap` yozilmagan"
                )
        for row in self.decisions:
            if not row.binds:
                raise BusinessArchitectureError(f"{row.decision}: dalilsiz bo'lmaydi")
            if row.held is not Held.HONORED and not row.gap:
                raise BusinessArchitectureError(
                    f"{row.decision}: farq bor, `gap` yozilmagan"
                )

    def _check_neighbors(self) -> None:
        """Qo'shni reyestrlar bilan bog'lamlar — eskirsa shu yerda yiqiladi."""
        declined_ids = {c.node_id for c in prd_arch.declined()}
        if not {"KF", "RD"} <= declined_ids:
            raise BusinessArchitectureError(
                "`01` §29 reyestrida Kafka/Redis `DECLINED` emas — "
                "RD/KF bahosi qayta ko'rilsin"
            )
        con05 = next(c for c in benv.CONSTRAINTS if c.code == "CON-05")
        if con05.fit is not benv.Fit.BREACHED:
            raise BusinessArchitectureError(
                "`CON-05` endi buzilmagan — stek savoli hal bo'lgan, "
                "RESHAPED/ABSENT baholari qayta ko'rilsin"
            )
        if not self.monolith_vs_diagram:
            raise BusinessArchitectureError(
                "Ikkinchi topilma yo'qoldi: monolitda yashaydigan tugun "
                "qolmadi — reyestr qayta ko'rilsin"
            )

    # -- kesimlar ----------------------------------------------------------

    @property
    def flagged(self) -> tuple[NodeRow | DecisionRow, ...]:
        """`gap` i bo'sh bo'lmagan qatorlar — hujjat bilan kod ajragan joylar."""
        return tuple(r for r in (*self.nodes, *self.decisions) if r.gap)

    @property
    def by_map(self) -> dict[Map, int]:
        result: dict[Map, int] = {m: 0 for m in Map}
        for node in self.nodes:
            result[node.map] += 1
        return result

    @property
    def monolith_vs_diagram(self) -> bool:
        """Chizma alohida servis deb ko'rsatgan funksiya monolitda yashayaptimi."""
        return any(n.map is Map.IN_MONOLITH for n in self.nodes)

    @property
    def decisions_hold(self) -> bool:
        """§24.2 qarorlari to'liq amal qiladimi. Bugun `False` (D2 `PARTIAL`)."""
        return all(d.held is Held.HONORED for d in self.decisions)

    @property
    def drawing_matches(self) -> bool:
        """§24.1 chizmasi mahsulot shaklini to'g'ri ko'rsatadimi. Bugun `False`."""
        return all(n.map is Map.AS_DRAWN for n in self.nodes)

    @property
    def accurate(self) -> bool:
        """§24 «hujjat mahsulotni to'g'ri tasvirlaydi» deb o'qilsa rostmi.

        Bugun `False`: o'n to'rt qator ajragan — oltita tugun `ABSENT`,
        uchtasining yorlig'i kodga zid, to'rt monolit tugunida va'da
        qilingan qism yetishmaydi, bitta qaror yarim bajarilgan.
        """
        return not self.flagged


def evaluate() -> BusinessArchitectureReport:
    """Reyestrdan to'liq hisobot. Argument yo'q — 85–87, 99–106 runlar qoidasi."""
    return BusinessArchitectureReport(nodes=NODES, decisions=DECISIONS)

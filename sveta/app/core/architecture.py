"""`01` §29 «High-Level Architecture» C4 Container diagrammasi ↔ haqiqiy modullar.

**Nima uchun bu modul bor.** §29 — hujjatdagi yagona joy, u yerda
mahsulot **konteynerlar** darajasida chiziladi: o'nta tugun, o'n ikkita
strelka va bitta xulosa jumlasi. Shu paytgacha bu rasm hech qayerda
o'qilmagan. `05` §1 modul chegaralarini o'z so'zlari bilan yozadi,
`03` §Q-1 esa §29 ga **to'g'ridan-to'g'ri javob beradi** — va uchala
hujjat bir-biriga bitta havola bilan ham bog'lanmagan.

Bu 77-run ning holati aynan takrorlanadi: `01` §25 ning reliz shartlari
`03` §6 ning gate lari bilan hech qayerda solishtirilmagan edi. Farq
shundaki, u yerda ikkita hujjat **bir xil savolga** ikki xil javob
berardi; bu yerda `03` §Q-1 §29 ni nomi bilan chaqiradi va uni bekor
qiladi — lekin bekor qilish faqat `03` da yozilgan, ya'ni §29 dan
kelgan o'quvchi uni ko'rmaydi.

## Diagramma bajarilmaydi, va bu safar u ikki marta noto'g'ri

72-run `01` §17 uchun aytgan gap («diagramma yiqila olmaydi») bu yerda
ham amal qiladi, lekin natijasi og'irroq. ER rasmi ustun nomlarida
adashadi; konteyner rasmi esa **mahsulotning shaklida** adashadi:

* Diagrammaning o'nta tugunidan **ikkitasi umuman yo'q** — `KF` (Kafka)
  va `RD` (Redis). Ular unutilgan emas, ular `ADR-05` bilan rad etilgan
  (`05` §11) va `03` §9 da qaytish sharti bilan birga yozilgan.
* Diagrammaning o'n ikkita strelkasidan **beshtasi** aynan shu ikki
  tugun orqali o'tadi (`BOT→KF`, `KF→CL`, `CL→KF`, `KF→NT`, `API→RD`),
  ya'ni rasmning qariyb yarmi mavjud bo'lmagan yo'lni ko'rsatadi.

Shundan keyin §29 ning xulosa jumlasi o'qiladi:

    «Единственное архитектурное следствие Самарканда: GEO получает
    третий уровень привязки … Остальные контейнеры не меняются.»

O'nta konteynerdan ikkitasi yo'q — ya'ni «остальные контейнеры не
меняются» **bugun yolg'on**. Muhimi, u Samarqand tufayli yolg'on emas:
rasm Toshkent paketidan meros olingan va yakka ishlab chiquvchi uchun
qayta chizilmagan. Bu 71- va 72-runlar topgan «наследуется» tuzog'ining
uchinchi holati — meros olingan hujjat forkda **avtomatik rost** bo'lib
tuyuladi, chunki uni hech kim qaytadan o'qimaydi.

## Birinchi o'q: `Realization` — tugun bugun nima

Rad etilgan tugunni «bajarilmagan» deb belgilash ro'yxatni abadiy
qizil qoldirardi (67-run ning `EXTERNAL`, 70-run ning `CODEBASE`
sinfi bilan bir xil sabab). `DECLINED` — qaror, qarz emas.

Ajratma to'rt qiymatli, chunki qolgan uchtasi ham «modul» emas:
`DB` — haqiqiy runtime bog'liqligi, lekin bizning kodimiz emas;
`WEB` — brauzerda ishlaydigan statik build, konteyner emas (`05` §1:
«React + MapLibre (statik build)»). Ikkalasini `MODULE` deb belgilash
«har bir tugun ortida `app/` paketi bor» degan noto'g'ri va'da berardi.

## Ikkinchi o'q: `Trigger` — rad etishning qaytish sharti o'lchanadimi

Bu o'q `Realization` ni takrorlamaydi va **eng qimmatli topilma shu
yerdan chiqadi.** `03` §9 ning qoidasi qat'iy: «bu jadvaldagi elementni
"hozir qilib qo'yaylik" degan asos bilan ilgari surish taqiqlanadi;
qaytish sharti — yagona asos». Ya'ni butun qaror **shartning
o'lchanishiga** tayanadi. Uchala shart ham bugun o'lchanmaydi, lekin
uch xil sababdan — va sabablar bir-biriga o'xshamaydi:

* **Redis · `API p95 >300 ms` → `UNMEASURED`.** `sveta_http_requests_total`
  faqat status sinfini sanaydi; javob vaqti uchun gistogramma yo'q.
  67-run buni allaqachon ko'rgan (`app/release/measures.py`, `api_p95`,
  `Coverage.ABSENT`) — lekin **reliz o'lchovi** sifatida. Hech kim
  o'sha bo'shliq bir vaqtning o'zida Redis ni qaytaradigan **yagona
  tetik** ekanini yozmagan. Bu qo'shimcha ish emas: gistogramma
  qo'shilsa ikkala qator birdan yopiladi.
* **Kafka · `klasterlash kechikishi >30 s` → `VOID`.** Shart o'lchanmaydi
  va **o'lchanishi ham mumkin emas**, chunki almashtirish o'sha
  kechikishni yo'q qilgan: `app.bot.service.submit_report` da
  `clustering.assign` xabar yozilgan **o'sha tranzaksiyada**, sinxron
  chaqiriladi. Navbat yo'q — navbatning kechikishi ham yo'q. Shart
  o'zi asoslayotgan komponentning **mavjudligini** o'lchaydi: Kafka
  bo'lmasa qiymat doim nolga yaqin, ya'ni tetik hech qachon ishlamaydi.
  Bu yagona joy emas: `sveta_outbox_lag_seconds` **bor**, lekin u
  bildirishnoma navbatini o'lchaydi (`05` §2.4), klasterlashni emas.
* **Mikroservislar · `Jamoa >6 dev` → `ORGANIZATIONAL`.** Bu mahsulot
  metrikasi emas va bo'lishi ham shart emas. Uni «o'lchanmagan» deb
  sanash boshqa ikkitasining ma'nosini suyultirardi.

Kafka ning ikkinchi yarmi (`Kunlik xabar >50k`) esa **`DERIVABLE`**:
`sveta_reports_received_total` kümülativ hisoblagich, kunlik tezlik
undan `increase()` bilan chiqadi — Prometheus o'rnatilganda. Shuning
uchun Kafka ikkita qatorda turadi: bitta sharti hisoblanadi, ikkinchisi
tug'ilishidan o'lik.

## Uchinchi o'q: `EdgeFidelity` — strelka kodda qanday ko'rinadi

Strelkalarning ikkitasi **teskari** va ikkalasi ham ma'noli:

* `ADM --> API` — diagrammada admin-panel API ning **mijozi**. Kodda
  teskari: `app.api` → `app.admin`. Ya'ni alohida admin ilovasi yo'q,
  `app/admin/` — API ichidagi kutubxona (`app/api/v1/admin.py`
  routerlari). Diagrammadan o'qilgan xulosa («admin-panelni alohida
  deploy qilamiz») noto'g'ri.
* `NT --> BOT` — diagrammada bildirishnoma workeri botni chaqiradi.
  Kodda bunday import **yo'q** va ataylab: `app.bot` obunalar ro'yxati
  uchun `app.notifications` ni import qiladi, teskari import aylana
  yasardi. Ikkalasini `app.jobs.process_outbox` ulaydi
  (`app.notifications.sender.Sender` protokoli + `app.bot.notifier`
  adapteri). Ya'ni strelka **rost**, lekin u import qirrasi emas —
  `MEDIATED`.

`MEDIATED` ni `HOLDS` dan ajratish shuning uchun kerak: ikkalasi ham
«ishlaydi» degani, lekin `MEDIATED` qirrani buzish uchun uchinchi
modulni o'zgartirish yetarli va bu diagrammaga qarab ko'rinmaydi.

`WEB --> API` — `OUT_OF_PROCESS`: `web/app.js` brauzerdan HTTP bilan
so'raydi, Python importi umuman yo'q. Uni `HOLDS` deb belgilash import
grafiga qo'shilmaydigan qirrani qo'shgandek bo'lardi.

## To'rtinchi o'q: `Provenance` — chizilmagan modullar

Teskari yo'nalish ham o'lchanadi: `app/` da o'n to'rtta paket bor,
diagrammada esa oltitasi. Rasm to'liq bo'lishi shart emas — u
illyustratsiya. Lekin ajratma foydali:

* `SPECIFIED` — `05` §1 da bor, §29 da yo'q (`core`, `db`, `reports`,
  `jobs`). Bularning ichida bittasi jim emas: **`jobs`** — `05` §1
  uni alohida konteyner deb ataydi va `docker-compose.yml` da u
  haqiqatan alohida xizmat. Diagrammada esa umuman planировщик yo'q,
  holbuki uning ikkita strelkasi (`KF→NT`, `NT→BOT`) faqat shu
  konteyner ishlagandagina bajariladi.
* `EMERGENT` — ikkala hujjatda ham yo'q (`stats`, `obs`, `analytics`,
  `release`, `integrations`). Bu qarz emas, lekin `stats` alohida
  turadi: u `01` §24 Phase 1 ning «витрина статистики» va §4 Success
  Metrics ining butun asosini ko'taradi, ya'ni mahsulot va'dasi bor
  konteyner ikkala arxitektura hujjatida ham chizilmagan.

## Modul chegarasi qoidasi — `03` §Q-1 ning «muhim shart» i

Q-1 modulli monolitni **shart bilan** ruxsat beradi: «modul chegaralari
mikroservis chegaralari kabi qat'iy saqlanadi (bir modul boshqasining
jadvaliga to'g'ridan-to'g'ri murojaat qilmaydi)». Bu jumla `05` §1 da
ham bor va shu paytgacha hech qachon **o'lchanmagan** — ya'ni butun
«keyinchalik ajratish mumkin» va'dasi tekshirilmagan taxmin edi.

Mexanik shakli ikkita: (1) hech bir modul boshqa modulning `models`
submodulini import qilmaydi — yagona istisno `app/db/models.py`, u
`Base.metadata` ni to'liq yig'ish uchun bor; (2) xom SQL orqali
aylanib o'tish yo'q. Ikkalasi ham bugun bajariladi va endi
`tests/test_architecture_contract.py` da qulflangan.

## Modul chegarasi (bu faylning o'zi)

Modul **toza**: bazaga ulanmaydi, `settings` ni o'qimaydi, FastAPI ni
bilmaydi va `app.*` dan hech narsa import qilmaydi. U hujjat matnini
va kuzatilgan import grafini **argument sifatida** oladi (72-run ning
`data_model.py` uslubi: `metadata` tashqaridan berilardi). Hech nimani
majburlamaydi — majburlash kontrakt testining ishi.

`app.core` — bu reyestrning yagona to'g'ri uyi: u barcha modullarni
nomlashi kerak, o'zi esa hech qaysisiga bog'lana olmaydi. `app.core`
import grafida chiquvchi qirrasi bo'lmagan yagona paket, ya'ni faqat
shu yerda aylana tug'ilmaydi.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Set
from dataclasses import dataclass
from enum import StrEnum

#: Diagrammaning hujjatdagi manzili.
SPEC = "01 §29"

#: §29 ni «maqsad holati» deb ataydigan va uni bekor qiladigan yagona joy.
COUNTER_SPEC = "03 §Q-1"

#: Rad etilgan tugunlarning qaytish shartlari jadvali.
DEFERRAL_SPEC = "03 §9"

#: ⚠️ Bitta shart `03` da **ikki xil** yozilgan: §9 «klaster kechikishi»,
#: §Q-1 esa «klasterlash kechikishi». Reyestr §9 ning so'zini oladi
#: (`DEFERRAL_SPEC`), lekin ikkinchisini ham biladi — aks holda hujjat
#: qaysi biri tuzatilsa ham test jimgina yashil qolardi.
CONDITION_ALIASES: dict[str, str] = {
    "klaster kechikishi >30 s": "klasterlash kechikishi >30 s",
}

#: Kafka/Redis ni rad etgan qaror (`05` §11).
DECLINE_ADR = "ADR-05"

#: §29 ning xulosa jumlasi — reyestr uni **so'zma-so'z** biladi, chunki
#: butun modulning da'vosi shu jumla bugun yolg'onligiga tayanadi.
HEADLINE_CLAIM = "Остальные контейнеры не меняются"


# --------------------------------------------------------------------------
# Diagramma parseri
# --------------------------------------------------------------------------


class Shape(StrEnum):
    """Mermaid tugunining shakli — diagrammaning o'zi bergan tasnif."""

    #: `NODE[Yorliq]` — xizmat.
    SERVICE = "service"
    #: `NODE[(Yorliq)]` — saqlagich (silindr).
    DATASTORE = "datastore"
    #: `NODE[[Yorliq]]` — navbat.
    QUEUE = "queue"


#: Shakl sintaksisi. Tartib muhim: `[[` va `[(` `[` dan **oldin** sinaladi.
_NODE_PATTERNS: tuple[tuple[str, Shape], ...] = (
    (r"^(?P<id>[A-Z][A-Za-z0-9_]*)\[\[(?P<label>.+?)\]\]$", Shape.QUEUE),
    (r"^(?P<id>[A-Z][A-Za-z0-9_]*)\[\((?P<label>.+?)\)\]$", Shape.DATASTORE),
    (r"^(?P<id>[A-Z][A-Za-z0-9_]*)\[(?P<label>.+?)\]$", Shape.SERVICE),
)

_EDGE_RE = re.compile(r"^(?P<src>[A-Z][A-Za-z0-9_]*)\s*-->\s*(?P<dst>[A-Z][A-Za-z0-9_]*)$")
_SUBGRAPH_RE = re.compile(r"^subgraph\s+(?P<id>[A-Za-z0-9_]+)")


class DiagramError(ValueError):
    """Diagrammani o'qib bo'lmadi — hujjat kutilgan shaklda emas."""


@dataclass(frozen=True)
class Node:
    """Diagrammadagi bitta tugun."""

    node_id: str
    label: str
    shape: Shape


@dataclass(frozen=True)
class Diagram:
    """`01` §29 ning C4 Container mermaid bloki, o'qilgan holda."""

    nodes: tuple[Node, ...]
    edges: tuple[tuple[str, str], ...]

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(n.node_id for n in self.nodes)

    def node(self, node_id: str) -> Node:
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        raise KeyError(node_id)


def _strip_label(raw: str) -> str:
    """`<br/>` ni bo'shliqqa aylantiradi — yorliq bitta qatorga siqiladi."""
    return re.sub(r"\s+", " ", raw.replace("<br/>", " ").replace("<br>", " ")).strip()


def parse_container_diagram(doc: str) -> Diagram:
    """§29 ning «C4 Container» mermaid blokini o'qiydi.

    Reyestr diagrammani **hujjatdan** oladi, ro'yxatni takrorlamaydi:
    aks holda rasm tahrirlanganda reyestr jimgina eskirardi. Xuddi shu
    sabab bilan noto'g'ri shakldagi hujjat jim qolmaydi — `DiagramError`.
    """
    heading = doc.find("### C4 Container")
    if heading < 0:
        raise DiagramError("«### C4 Container» sarlavhasi topilmadi")
    start = doc.find("```mermaid", heading)
    if start < 0:
        raise DiagramError("«### C4 Container» dan keyin mermaid bloki yo'q")
    end = doc.find("```", start + len("```mermaid"))
    if end < 0:
        raise DiagramError("mermaid bloki yopilmagan")

    body = doc[start + len("```mermaid") : end]
    nodes: list[Node] = []
    edges: list[tuple[str, str]] = []
    seen: set[str] = set()

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line in {"end"} or line.startswith("flowchart"):
            continue
        if _SUBGRAPH_RE.match(line):
            continue

        edge = _EDGE_RE.match(line)
        if edge is not None:
            edges.append((edge.group("src"), edge.group("dst")))
            continue

        for pattern, shape in _NODE_PATTERNS:
            m = re.match(pattern, line)
            if m is None:
                continue
            node_id = m.group("id")
            if node_id in seen:
                raise DiagramError(f"tugun ikki marta e'lon qilingan: {node_id}")
            seen.add(node_id)
            nodes.append(Node(node_id, _strip_label(m.group("label")), shape))
            break
        else:
            raise DiagramError(f"tanib bo'lmagan qator: {line!r}")

    if not nodes:
        raise DiagramError("diagrammada bitta ham tugun yo'q")
    if not edges:
        raise DiagramError("diagrammada bitta ham strelka yo'q")

    unknown = {n for edge in edges for n in edge} - seen
    if unknown:
        raise DiagramError(f"strelka e'lon qilinmagan tugunga: {sorted(unknown)}")

    return Diagram(tuple(nodes), tuple(edges))


# --------------------------------------------------------------------------
# Konteynerlar
# --------------------------------------------------------------------------


class Realization(StrEnum):
    """Diagramma tuguni bugungi repoda nima."""

    #: `app/` ichidagi Python paketi.
    MODULE = "module"
    #: Haqiqiy runtime bog'liqligi, lekin bizning kodimiz emas (Postgres).
    INFRA = "infra"
    #: Brauzerda ishlaydigan statik build — konteyner emas (`05` §1).
    STATIC = "static"
    #: Diagrammada bor, mahsulotda **ataylab** yo'q (`ADR-05`).
    DECLINED = "declined"


class Trigger(StrEnum):
    """Rad etilgan tugunning qaytish sharti (`03` §9) bugun o'lchanadimi."""

    #: O'lchov bor yoki mavjud hisoblagichdan chiqariladi.
    DERIVABLE = "derivable"
    #: O'lchov yo'q, lekin qo'shilishi mumkin (gistogramma kerak).
    UNMEASURED = "unmeasured"
    #: O'lchash **mumkin emas**: almashtirish o'lchanadigan narsani yo'q qilgan.
    VOID = "void"
    #: Mahsulot metrikasi emas — tashkiliy fakt.
    ORGANIZATIONAL = "organizational"


@dataclass(frozen=True)
class Container:
    """Diagrammaning bitta tuguni haqidagi baho."""

    node_id: str
    realization: Realization
    #: Kodda qayerda — `app/` paketi nomi (`MODULE` uchun majburiy).
    package: str | None = None
    #: Tugunni nima almashtirdi (`DECLINED` uchun majburiy).
    substitute: tuple[str, ...] = ()
    #: `03` §9 dagi qaytish sharti, so'zma-so'z (`DECLINED` uchun majburiy).
    conditions: tuple[tuple[str, Trigger], ...] = ()
    #: Nima uchun aynan shu sinf. Bo'sh bo'lmasligi kerak.
    why: str = ""


CONTAINERS: tuple[Container, ...] = (
    Container(
        "BOT",
        Realization.MODULE,
        package="bot",
        why="aiogram handlerlar va FSM — `05` §1 dagi `bot/`.",
    ),
    Container(
        "API",
        Realization.MODULE,
        package="api",
        why="FastAPI routerlar (public + admin) — `05` §1 dagi `api/`.",
    ),
    Container(
        "GEO",
        Realization.MODULE,
        package="geo",
        why=(
            "§29 ning yagona «Samarqand o'zgarishi» aynan shu tugunda: "
            "uchinchi daraja (mahalla) va spravochnik versiyalash `app/geo/` da."
        ),
    ),
    Container(
        "CL",
        Realization.MODULE,
        package="clustering",
        why=(
            "Diagramma DBSCAN deydi; kodda inkremental biriktirish (`ADR-02`), "
            "oflayn DBSCAN faqat `tools/recluster.py` da. Tugun o'sha, algoritm boshqa."
        ),
    ),
    Container(
        "NT",
        Realization.MODULE,
        package="notifications",
        why="obuna, outbox, yuborish — `05` §1 dagi `notifications/`.",
    ),
    Container(
        "ADM",
        Realization.MODULE,
        package="admin",
        why=(
            "Moderatsiya mantiqi kutubxona sifatida; alohida deploy qilinadigan "
            "admin ilovasi yo'q — routerlar `app/api/v1/admin.py` da."
        ),
    ),
    Container(
        "DB",
        Realization.INFRA,
        why=(
            "PostgreSQL 16 + PostGIS — `docker-compose.yml` dagi `db` xizmati. "
            "Bizning kodimiz emas, shuning uchun `MODULE` emas."
        ),
    ),
    Container(
        "WEB",
        Realization.STATIC,
        why=(
            "`web/` — statik build (`05` §1), brauzerda ishlaydi. Ishlab turgan "
            "konteyner emas, ya'ni `MODULE` ham, `INFRA` ham noto'g'ri bo'lardi."
        ),
    ),
    Container(
        "KF",
        Realization.DECLINED,
        substitute=(
            "app.notifications.outbox",
            "app.bot.service:submit_report",
        ),
        conditions=(
            ("Kunlik xabar >50k", Trigger.DERIVABLE),
            ("klaster kechikishi >30 s", Trigger.VOID),
        ),
        why=(
            "`ADR-05`: Kafka o'rniga Postgres outbox (`05` §2.4) va sinxron "
            "chaqiruv. Ikkinchi shart `VOID`: navbat yo'q — navbat kechikishi "
            "ham yo'q, ya'ni tetik hech qachon ishlamaydi."
        ),
    ),
    Container(
        "RD",
        Realization.DECLINED,
        substitute=(
            "app.core.etag",
            "app.geo.registry",
        ),
        conditions=(("API p95 >300 ms", Trigger.UNMEASURED),),
        why=(
            "`ADR-05`: Redis o'rniga HTTP cache-header (`ETag`/`Cache-Control`) "
            "va jarayon ichidagi kesh. Tetik o'lchanmaydi — javob vaqti uchun "
            "gistogramma yo'q (67-run: `measures.api_p95` = `ABSENT`)."
        ),
    ),
)

CONTAINER_BY_NODE: dict[str, Container] = {c.node_id: c for c in CONTAINERS}

#: `03` §9 ning uchinchi qatori — diagrammada tuguni yo'q, chunki u
#: tugun emas, butun rasmning shakli haqida. Reyestrda alohida turadi:
#: uni konteyner qilib qo'yish diagrammani buzardi, tashlab yuborish esa
#: `03` §9 ning uchta qatoridan bittasini yo'qotardi.
MICROSERVICES_CONDITION: tuple[str, Trigger] = ("Jamoa >6 dev", Trigger.ORGANIZATIONAL)


# --------------------------------------------------------------------------
# Strelkalar
# --------------------------------------------------------------------------


class EdgeFidelity(StrEnum):
    """Diagrammadagi strelka kodda qanday ko'rinadi."""

    #: Import grafida o'sha yo'nalishda bor.
    HOLDS = "holds"
    #: Import grafida **teskari** yo'nalishda bor.
    REVERSED = "reversed"
    #: Uchala modul ham bir-birini import qilmaydi; uchinchisi ulaydi.
    MEDIATED = "mediated"
    #: Rad etilgan tugun orqali o'tardi — chaqiruvga yoki jadvalga aylandi.
    COLLAPSED = "collapsed"
    #: Haqiqiy, lekin Python importi emas (brauzerdan HTTP).
    OUT_OF_PROCESS = "out_of_process"


@dataclass(frozen=True)
class Edge:
    """Diagrammaning bitta strelkasi haqidagi baho."""

    source: str
    target: str
    fidelity: EdgeFidelity
    #: Haqiqiy import qirralari, `"paket->paket"` shaklida.
    actual: tuple[str, ...] = ()
    #: `MEDIATED` da ulovchi joy.
    via: tuple[str, ...] = ()
    why: str = ""


EDGES: tuple[Edge, ...] = (
    Edge(
        "BOT",
        "GEO",
        EdgeFidelity.HOLDS,
        actual=("bot->geo",),
        why="`submit_report` mintaqani nuqtadan oladi (`geo.region_for_point`, E19).",
    ),
    Edge(
        "GEO",
        "DB",
        EdgeFidelity.HOLDS,
        actual=("geo->db",),
        why="Poligonlar va spravochniklar PostGIS da.",
    ),
    Edge(
        "BOT",
        "KF",
        EdgeFidelity.COLLAPSED,
        actual=("bot->clustering",),
        why=(
            "Kafka ga chiqish o'rniga `clustering.assign` xabar yozilgan **o'sha "
            "tranzaksiyada** chaqiriladi. Aynan shu qadam `03` §9 ning "
            "«klasterlash kechikishi» shartini `VOID` qiladi."
        ),
    ),
    Edge(
        "KF",
        "CL",
        EdgeFidelity.COLLAPSED,
        actual=("bot->clustering",),
        why="Iste'mol qadami yo'q — `BOT→KF→CL` bitta sinxron chaqiruvga siqilgan.",
    ),
    Edge(
        "CL",
        "DB",
        EdgeFidelity.HOLDS,
        actual=("clustering->db",),
        why="Hodisalar va biriktirishlar `outages` / `report_outage` da.",
    ),
    Edge(
        "CL",
        "KF",
        EdgeFidelity.COLLAPSED,
        actual=("clustering->notifications",),
        why=(
            "Hodisa chiqishi Kafka ga emas, `outbox` jadvaliga yoziladi "
            "(`05` §2.4, `ADR-05`) — o'sha tranzaksiyada, ya'ni yo'qolmaydi."
        ),
    ),
    Edge(
        "KF",
        "NT",
        EdgeFidelity.COLLAPSED,
        actual=("jobs->notifications",),
        why="Iste'molchi — `app.jobs.process_outbox`, u navbatni jadvaldan oladi.",
    ),
    Edge(
        "NT",
        "BOT",
        EdgeFidelity.MEDIATED,
        via=("app.jobs.process_outbox", "app.notifications.sender:Sender"),
        why=(
            "`app.notifications` Telegramni bilmaydi va bilmasligi kerak: "
            "`app.bot` → `app.notifications` importi allaqachon bor, teskarisi "
            "aylana yasardi. Adapter `app.bot.notifier` da, ulash `jobs` da."
        ),
    ),
    Edge(
        "API",
        "RD",
        EdgeFidelity.COLLAPSED,
        actual=(),
        why=(
            "Kesh HTTP sarlavhalariga ko'chdi (`app.core.etag`, `Cache-Control`) "
            "va jarayon ichiga (`app.geo.registry`). Tashqi saqlagich yo'q."
        ),
    ),
    Edge(
        "API",
        "DB",
        EdgeFidelity.HOLDS,
        actual=("api->db",),
        why="Ommaviy va admin endpointlar bazadan o'qiydi.",
    ),
    Edge(
        "WEB",
        "API",
        EdgeFidelity.OUT_OF_PROCESS,
        why="`web/app.js` brauzerdan `fetch` qiladi — Python importi umuman yo'q.",
    ),
    Edge(
        "ADM",
        "API",
        EdgeFidelity.REVERSED,
        actual=("api->admin",),
        why=(
            "Diagramma admin-panelni API ning mijozi qilib ko'rsatadi; kodda "
            "teskari — `app/api/v1/admin.py` `app.admin` ni import qiladi. "
            "Alohida deploy qilinadigan admin ilovasi yo'q."
        ),
    ),
)

EDGE_BY_PAIR: dict[tuple[str, str], Edge] = {(e.source, e.target): e for e in EDGES}


# --------------------------------------------------------------------------
# Chizilmagan modullar
# --------------------------------------------------------------------------


class Provenance(StrEnum):
    """Haqiqiy `app/` paketi qaysi hujjatda e'lon qilingan."""

    #: `01` §29 diagrammasida chizilgan.
    DIAGRAMMED = "diagrammed"
    #: Faqat `05` §1 daraxtida bor.
    SPECIFIED = "specified"
    #: Ikkala hujjatda ham yo'q.
    EMERGENT = "emergent"


#: `05` §1 ning daraxti, aynan o'sha ro'yxat.
SPEC_TREE: tuple[str, ...] = (
    "core",
    "db",
    "geo",
    "reports",
    "clustering",
    "notifications",
    "bot",
    "api",
    "admin",
    "jobs",
)

#: Ikkala hujjatda ham yo'q paketlar va nima uchun ular paydo bo'lgan.
EMERGENT_PACKAGES: dict[str, str] = {
    "stats": (
        "E14 — statistika va Coverage Index. `01` §24 Phase 1 ning «витрина "
        "статистики» si va §4 Success Metrics shu paketga tayanadi, ya'ni "
        "mahsulot va'dasi bor konteyner ikkala arxitektura hujjatida ham yo'q."
    ),
    "obs": "OBS — `05` §10 metrikalari va ogohlantirishlari (`01` §22).",
    "analytics": "ANL — `01` §21 mahsulot hodisalari.",
    "release": "REL — `03` §6 gate lari va `01` §25–§28 reyestrlari.",
    "integrations": "INT — `01` §18 tashqi tizimlar reyestri.",
}


def provenance(package: str) -> Provenance:
    """Paket qaysi hujjatdan kelganini aytadi."""
    for c in CONTAINERS:
        if c.package == package:
            return Provenance.DIAGRAMMED
    if package in SPEC_TREE:
        return Provenance.SPECIFIED
    return Provenance.EMERGENT


# --------------------------------------------------------------------------
# Kuzatilgan graf bilan solishtirish
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Divergence:
    """Reyestrning bitta da'vosi kuzatilgan grafga mos kelmadi."""

    edge: tuple[str, str]
    claim: EdgeFidelity
    missing: tuple[str, ...] = ()
    unexpected: tuple[str, ...] = ()

    def __str__(self) -> str:
        parts = [f"{self.edge[0]}→{self.edge[1]} ({self.claim})"]
        if self.missing:
            parts.append(f"yo'q: {', '.join(self.missing)}")
        if self.unexpected:
            parts.append(f"kutilmagan: {', '.join(self.unexpected)}")
        return "; ".join(parts)


def _pairs(graph: Mapping[str, Set[str]]) -> set[str]:
    return {f"{src}->{dst}" for src, targets in graph.items() for dst in targets}


def check_edges(graph: Mapping[str, Set[str]]) -> tuple[Divergence, ...]:
    """Reyestrning `actual` da'volarini kuzatilgan import grafiga solishtiradi.

    `graph` — `{paket: {paket, ...}}`; uni chaqiruvchi yig'adi (test
    `ast` bilan o'qiydi). Modul o'zi hech narsa skanerlamaydi: shu
    tufayli u sof qoladi va sintetik graf bilan ham sinaladi.

    `MEDIATED` va `OUT_OF_PROCESS` qirralar **atayin** tekshirilmaydi:
    ularning da'vosi «import qirrasi yo'q» degani, va u
    `check_absent_edges` da alohida o'lchanadi.
    """
    observed = _pairs(graph)
    out: list[Divergence] = []
    for edge in EDGES:
        if not edge.actual:
            continue
        missing = tuple(sorted(p for p in edge.actual if p not in observed))
        if missing:
            out.append(Divergence((edge.source, edge.target), edge.fidelity, missing=missing))
    return tuple(out)


def check_absent_edges(graph: Mapping[str, Set[str]]) -> tuple[Divergence, ...]:
    """`MEDIATED` va `REVERSED` da'volarining **yo'qligini** tekshiradi.

    `NT --> BOT` uchun da'vo ikki tomonlama: `notifications->bot` importi
    **bo'lmasligi** kerak (aylana), `ADM --> API` uchun esa
    `admin->api` bo'lmasligi kerak. Bu da'volar buzilsa arxitektura
    jimgina o'zgargan bo'ladi va hech qanday test qizarmasdi.
    """
    observed = _pairs(graph)
    out: list[Divergence] = []
    for edge in EDGES:
        if edge.fidelity not in {EdgeFidelity.MEDIATED, EdgeFidelity.REVERSED}:
            continue
        src = CONTAINER_BY_NODE[edge.source].package
        dst = CONTAINER_BY_NODE[edge.target].package
        if src is None or dst is None:
            continue
        forbidden = f"{src}->{dst}"
        if forbidden in observed:
            out.append(
                Divergence((edge.source, edge.target), edge.fidelity, unexpected=(forbidden,))
            )
    return tuple(out)


def declined() -> tuple[Container, ...]:
    """Diagrammada bor, mahsulotda ataylab yo'q tugunlar."""
    return tuple(c for c in CONTAINERS if c.realization is Realization.DECLINED)


def collapsed_edges() -> tuple[Edge, ...]:
    """Rad etilgan tugun orqali o'tgan strelkalar."""
    return tuple(e for e in EDGES if e.fidelity is EdgeFidelity.COLLAPSED)


def unreachable_triggers() -> tuple[tuple[str, str], ...]:
    """Hech qachon ishlamaydigan qaytish shartlari: `(tugun, shart)`.

    `VOID` — o'lchanadigan narsa almashtirish bilan birga yo'qolgan.
    `UNMEASURED` — o'lchov qo'shilishi mumkin, ya'ni bu ro'yxatga
    kirmaydi: u bo'shliq, tuzoq emas.
    """
    return tuple(
        (c.node_id, condition)
        for c in CONTAINERS
        for condition, trigger in c.conditions
        if trigger is Trigger.VOID
    )


def condition_wordings(condition: str) -> tuple[str, ...]:
    """Shartning hujjatdagi barcha yozilishlari (`CONDITION_ALIASES` bilan)."""
    alias = CONDITION_ALIASES.get(condition)
    return (condition,) if alias is None else (condition, alias)


def headline_holds(diagram: Diagram) -> bool:
    """§29 ning «остальные контейнеры не меняются» da'vosi bugun rostmi.

    Rost bo'lishi uchun diagrammaning `GEO` dan boshqa birorta tuguni
    o'zgarmagan bo'lishi kerak. Ikkita tugun rad etilgan — ya'ni yolg'on.
    Funksiya `False` qaytarish uchun yozilgan: uning `True` bo'lishi
    diagramma qayta chizilganini bildiradi va test buni ko'radi.
    """
    drawn = set(diagram.node_ids)
    return not any(c.node_id in drawn for c in declined())


def unassessed(diagram: Diagram) -> tuple[str, ...]:
    """Diagrammada bor, lekin reyestrda bahosi yo'q tugunlar."""
    return tuple(sorted(set(diagram.node_ids) - set(CONTAINER_BY_NODE)))


def phantom(diagram: Diagram) -> tuple[str, ...]:
    """Reyestrda bor, lekin diagrammada yo'q tugunlar."""
    return tuple(sorted(set(CONTAINER_BY_NODE) - set(diagram.node_ids)))


def packages(names: Iterable[str]) -> dict[str, Provenance]:
    """Berilgan paketlar ro'yxatini uchta sinfga ajratadi."""
    return {name: provenance(name) for name in names}

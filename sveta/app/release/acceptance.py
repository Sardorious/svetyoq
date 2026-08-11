"""Mintaqaviy relizning qabul mezonlari (`01` §23).

**Nima uchun bu modul bor.** `01` §23 ning butun mazmuni — yettita
belgilash katagi va ustidagi bitta jumla: «Общий критерий приёмки
**регионального релиза**». Shu paytgacha bu ro'yxat hujjatda qolib
kelgan. Kodda «acceptance» so'zi umuman uchramasdi, ya'ni mahsulotning
«mintaqani ommaga ochsa bo'ladimi?» degan yakuniy savoliga javob
beradigan yagona ro'yxat hech qayerda o'lchanmasdi.

## Nima uchun `gates.py` buni qoplamaydi

66-run `03` §6 ni yopgan va u ham «relizni to'xtatadigan mezonlar»
haqida. Farq **o'lchov o'qida**, mazmunda emas:

* `gates.py` — **loyiha fazasi** bo'yicha: G-0 M0 oxirida, G-5 R1.0
  oxirida. Har gate hayotda **bir marta** yopiladi va yopilgandan keyin
  qaytib ochilmaydi.
* bu modul — **mintaqa** bo'yicha. Ro'yxat Samarqand uchun bir marta
  emas, **har** yangi mintaqa uchun qaytadan yuriladi. `03` §6 G-8
  aynan shunga tayanadi: «Ikkinchi mintaqa kodsiz ishga tushdi».

Ikkalasini bitta reyestrga qo'shish ro'yxatni Samarqandning sanalariga
bog'lab qo'yardi, ya'ni ikkinchi mintaqa uchun u avtomatik «yopiq»
ko'rinardi.

## Asosiy topilma: yettitadan ikkitasigina mintaqa haqida

Hujjat yettala qatorni bitta tekis ro'yxatda beradi, go'yo ular bir
xil turdagi savol. Ular emas, va farqning oqibati bor:

* **`Scope.REGION`** — javob mintaqaning **ma'lumotiga** bog'liq
  (chegaralar yuklanganmi, nazorat namunasi biriktirilganmi). Uni har
  mintaqa uchun qaytadan o'lchash kerak.
* **`Scope.CODEBASE`** — javob **kodning tuzilishiga** bog'liq (UZ
  katalogi to'liqmi, indeks qaysi endpointlarda bor, verdikt qanday
  yozilgan, metrikalarda `region` yorlig'i bormi). Bunday qator
  birinchi mintaqada bajarilgan bo'lsa, ikkinchisida **tekinga** yashil
  bo'ladi: uni belgilash tekshiruv emas, **takrorlash**.

Bugungi hisob: `REGION` — **ikkita** (§23 ning 1- va 2-qatori),
`CODEBASE` — **beshta**. Ya'ni ikkinchi mintaqa uchun yurgizilgan
yettita bandlik ro'yxat aslida **ikkita** yangi savol beradi, qolgan
beshtasi Samarqanddan meros bo'lib o'tadi. Va bugun o'sha ikkitasining
**ikkalasi ham** o'lchanmagan (`UNMEASURED`), o'lchanadigan uchtasi esa
`CODEBASE`. Bu ro'yxatning kamchiligi emas — uni «5/7 yashil» deb
o'qish kamchilik, va aynan shu G-8 tayanadigan joyda sodir bo'ladi.

`restated_count` shu sonni hisobotda ochiq ko'rsatadi.

## `PG-S4` — vitrina reyestri va ikkita bajarilmagan qator

`01` §23 ning 4-qatori («Coverage Index отображается на всех витринах
региона») bugun **bajarilmagan**, va uni bajarilgan ko'rsatib turgan
narsa — savolning noto'g'ri qo'yilishi. «Indeks bormi?» degan savolga
`test_stats_api_db.py` ham, `test_heatmap_api.py` ham «ha» deydi:
maydon javobda bor. `01` PG-S4 esa boshqa savolni o'lchaydi —
«**100% витрин** с индексом покрытия», ya'ni ulush, mavjudlik emas.

Shuning uchun bu yerda **vitrinalar reyestri** turadi (`SHOWCASES`) va
ulush undan hisoblanadi. Bugungi holat:

| Vitrina | Indeks | Chuqurlik pometasi |
|---|---|---|
| `GET /api/v1/stats` | bor | bor |
| `GET /api/v1/heatmap` | bor | bor |
| CSV eksport | bor | bor |
| `GET /api/v1/map` | **yo'q** | **yo'q** |
| Ommaviy sahifaning **standart** ko'rinishi | **yo'q** | **yo'q** |

Oxirgi qator eng muhimi va uni topish qiyin edi: sahifada indeks
**bor** (`web/index.html`, `#heat-coverage`), lekin u `#heat-legend`
blokining ichida, blok esa `heatOn` bayrog'i bilan ochiladi va
bayroq standart holatda `false` (`web/app.js:38`). Ya'ni odam
zichlik qatlamini **qo'lda yoqmaguncha** ommaviy xaritada na qamrov
indeksi, na yosh mintaqa pometasi ko'rinadi. Xuddi shu sababdan §23
ning **7-qatori** («Дисклеймер молодого региона активен») ham
bajarilmagan: `showMaturity` o'sha `refreshHeat` dan chaqiriladi.

**Nima uchun xarita ham vitrina.** Bahsli ko'rinishi mumkin: xarita
hodisalarni ko'rsatadi, statistikani emas. Lekin u har hodisa uchun
`scale` va `confidence` ni chop etadi, va ikkalasi ham `06` §5.3/§6
bo'yicha xabar beruvchilar **zichligidan** chiqadi. `01` PG-S4 ning
nomi to'liq shunday: «**Честная** статистика с Coverage Index» —
indeks aynan zichlikdan chiqarilgan sonning halollik izohi. Zichlikka
tayangan yorliqni («tuman miqyosida uzilish») indekssiz ko'rsatish —
PG-S4 taqiqlayotgan narsaning o'zi.

**Nima uchun bu run tuzatmadi.** Har uchala yo'l ham qulflangan
kontraktni tahrirlaydi: `/map` javobiga maydon qo'shish — `05` §7.1 va
`test_openapi_contract.py`; `/map/config` ga qo'shish — o'sha; sahifaga
ikkinchi so'rov qo'shish — `05` §7.2 endpoint sathi (48-run). Bu
66-run ning `answer_p90` holati bilan bir sinf, va o'sha qaror
takrorlanadi: holat kodda qayd etiladi, tanlov odamga qoldiriladi
(`PROGRESS.md` «Ochiq savollar»).

## Uchta dalil manbai

`Evidence` `gates.CriterionKind` ni takrorlamaydi — u boshqa savolga
javob beradi. `CriterionKind` «mezonni **kim** yopadi» (mashina yoki
odam), bu yerda esa «javob **qayerdan** keladi»:

* `STRUCTURAL` — bugun, bazasiz, kodning o'zidan (katalog to'liqligi,
  vitrina reyestri, verdikt matni, metrika yorliqlari);
* `RUNTIME` — mintaqaning ma'lumotidan, ya'ni so'rov kerak;
* `MANUAL` — dalil tizimdan tashqarida (nazorat namunasining natijasi
  hech qayerda saqlanmaydi).

Farq narxni ko'rsatadi, `measures.py` dagi `DERIVABLE`/`ABSENT`
ajratmasi bilan bir xil sababdan.

Modul **toza**: bazaga ham, `settings` ga ham murojaat qilmaydi.
`STRUCTURAL` mezonlar `app.core.i18n`, `app.clustering.lookup`,
`app.obs.monitoring` va `app.stats.maturity` dan o'qiladi (hammasi
toza), `RUNTIME` mezonlar esa qiymatni chaqiruvchidan oladi.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from app.clustering import lookup
from app.core import i18n
from app.obs import monitoring
from app.release.gates import CriterionStatus
from app.stats import maturity

#: Bu ro'yxatning hujjatdagi manzili.
SPEC = "01 §23"

#: `01` §23 ning 2-qatoridagi son: «Контрольная выборка **≥50 точек**».
#: Kontrakt testi uni hujjatdan parse qilib solishtiradi.
MIN_CONTROL_SAMPLE = 50

#: `01` PG-S4 ning maqsadi: «**100%** витрин с индексом покрытия».
#: Chegara literal va `gates.py` ning qoidasi bo'yicha konfiguratsiyadan
#: **olinmaydi**: vitrina ro'yxatini sozlama bilan qisqartirish ulushni
#: yolg'ondan 100% ga chiqarardi.
REQUIRED_SHOWCASE_SHARE = 1.0

class Scope(StrEnum):
    """Mezon nimaga tegishli: mintaqaga yoki kodga.

    Yuqoridagi izohga qarang — bu modulning asosiy ajratmasi.
    `CODEBASE` mezon ikkinchi mintaqada **tekinga** bajariladi, ya'ni
    uni belgilash yangi ma'lumot bermaydi.
    """

    REGION = "region"
    CODEBASE = "codebase"


class Evidence(StrEnum):
    """Javob qayerdan keladi."""

    #: Kodning o'zidan, bazasiz, bugun.
    STRUCTURAL = "structural"
    #: Mintaqaning ma'lumotidan — so'rov kerak.
    RUNTIME = "runtime"
    #: Tizimdan tashqarida (odam qayd etadi).
    MANUAL = "manual"


# --------------------------------------------------------------------------
# Vitrina reyestri (`01` PG-S4)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Showcase:
    """Mintaqaning bitta ommaviy vitrinasi.

    `why_missing` — nima uchun indeks yo'q, **bir jumlada**. Bo'sh
    bo'lsa vitrina indeksni ko'rsatadi. Sabab reyestrda turishi shart:
    uni ko'rgan odam birinchi navbatda «shunchaki qo'shib qo'ysa
    bo'lmaydimi?» deb so'raydi.
    """

    code: str
    spec: str
    #: Kodda qayerda: `modul:simvol` yoki `fayl:selektor`.
    where: str
    shows_index: bool
    shows_maturity: bool
    why_missing: str = ""


SHOWCASES: tuple[Showcase, ...] = (
    Showcase(
        code="stats_api",
        spec="05 §7.2",
        where="app.api.v1.stats:CoverageOut",
        shows_index=True,
        shows_maturity=True,
    ),
    Showcase(
        code="heatmap_api",
        spec="05 §7.2",
        where="app.api.v1.heatmap:HeatCollection",
        shows_index=True,
        shows_maturity=True,
    ),
    Showcase(
        code="stats_export",
        spec="03 §R1.2",
        where="app.stats.export:HEADER",
        shows_index=True,
        shows_maturity=True,
    ),
    Showcase(
        code="map_api",
        spec="05 §7.1",
        where="app.api.v1.map:MapCollection",
        shows_index=False,
        shows_maturity=False,
        why_missing=(
            "javob `map_snapshot` dan o'qiladi va hisoblanmaydi; indeksni "
            "qo'shish `05` §7.1 javob sxemasini tahrirlashni talab qiladi"
        ),
    ),
    Showcase(
        code="web_default",
        spec="01 §14",
        where="web/index.html:#heat-coverage",
        shows_index=False,
        shows_maturity=False,
        why_missing=(
            "qator `#heat-legend` ichida, blok esa `heatOn` bilan ochiladi "
            "va bayroq standart holatda `false` (`web/app.js`)"
        ),
    ),
)

SHOWCASE_BY_CODE: dict[str, Showcase] = {s.code: s for s in SHOWCASES}


def index_share() -> float:
    """Qamrov indeksini ko'rsatadigan vitrinalar ulushi (`01` PG-S4)."""
    return sum(1 for s in SHOWCASES if s.shows_index) / len(SHOWCASES)


def maturity_share() -> float:
    """Yosh mintaqa pometasini ko'rsatadigan vitrinalar ulushi."""
    return sum(1 for s in SHOWCASES if s.shows_maturity) / len(SHOWCASES)


def showcases_without_index() -> tuple[Showcase, ...]:
    return tuple(s for s in SHOWCASES if not s.shows_index)


# --------------------------------------------------------------------------
# `STRUCTURAL` mezonlarning tekshiruvlari
# --------------------------------------------------------------------------


def uz_catalog_complete() -> bool:
    """§23 3-qatori: «Интерфейс на UZ полон: непереведённых строк нет».

    Faqat **katalog** haqida. Mintaqaga bog'liq matn (`regions.name_uz`,
    `districts.name_uz`, `mahallas.name_uz`) bazada yotadi va bu yerdan
    ko'rinmaydi — lekin uchalasi ham `NOT NULL` (`05` §2.1), ya'ni UZ
    tomoni sxema darajasida kafolatlangan. RU tomoni **emas**:
    `mahallas.name_ru` nullable. §23 faqat UZ ni so'raydi, shuning
    uchun bu yerda holat emas, izoh (`PROGRESS.md` «Ochiq savollar»).
    """
    return all(not i18n.missing_keys(lang) for lang in i18n.SUPPORTED_LANGUAGES)


def insufficient_data_verdict_present() -> bool:
    """§23 5-qatori: «Вердикт … сформулирован как "данных недостаточно"».

    Uchta qatlam tekshiriladi: verdikt qiymati bor, unga matn kaliti
    biriktirilgan va kalit **ikkala** katalogda mavjud. Faqat
    `AreaVerdict` a'zosini tekshirish yetarli emas — verdikt bor-u
    matnsiz qolsa foydalanuvchi bo'sh javob olardi.
    """
    verdict = lookup.AreaVerdict.NOT_ENOUGH_DATA
    key = lookup.MESSAGE_KEYS.get(verdict)
    if not key or key not in i18n.all_keys():
        return False
    return all(key not in i18n.missing_keys(lang) for lang in i18n.SUPPORTED_LANGUAGES)


def metrics_labelled_region() -> bool:
    """§23 6-qatori: «Метрики размечены `region`».

    Qatorni **qayta yozmaydi**: xuddi shu talab `01` §22 ning birinchi
    qatori va uni 69-run `app/obs/monitoring.py` da bog'lagan. Ikkinchi,
    mustaqil yozilgan tekshiruv 57-run ning holatini takrorlardi —
    ikki nusxa bir-biridan siljiydi va siljish ko'rinmaydi.
    """
    return monitoring.REQUIREMENT_BY_CODE["region_label"].is_held


def maturity_disclaimer_active() -> bool:
    """§23 7-qatori: «Дисклеймер молодого региона активен».

    «Faol» — mexanizm mavjud **va** vitrinalarda ko'rinadi. Birinchisi
    bajarilgan (`stats.maturity:WARNING_YOUNG` katalogda va
    `stats.service`/`stats.heatmap` uni chiqaradi), ikkinchisi yo'q:
    ommaviy sahifaning standart ko'rinishida pometa umuman chizilmaydi.
    """
    warning_present = maturity.WARNING_YOUNG in i18n.all_keys()
    return warning_present and maturity_share() >= REQUIRED_SHOWCASE_SHARE


#: `STRUCTURAL` mezonlarning tekshiruvlari, mezon kodi bo'yicha.
#: Reyestrdan **ajratilgan**: `Criterion` — ma'lumot, bu — xatti-harakat,
#: va ularni bitta dataklassga qo'shish reyestrni chaqiriladigan
#: qilardi (`gates.Criterion` bilan bir xil tartib).
STRUCTURAL_CHECKS = {
    "uz_interface": uz_catalog_complete,
    "coverage_index_on_showcases": lambda: index_share() >= REQUIRED_SHOWCASE_SHARE,
    "insufficient_data_verdict": insufficient_data_verdict_present,
    "metrics_region_label": metrics_labelled_region,
    "young_region_disclaimer": maturity_disclaimer_active,
}


# --------------------------------------------------------------------------
# Reyestr
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Criterion:
    """`01` §23 ning bitta belgilash katagi.

    `phrase` — hujjatdagi **so'zma-so'z** matn. Kontrakt testi ro'yxatni
    shu matn bo'yicha `01` bilan solishtiradi, ya'ni qatorni qayta
    yozish yoki tartibini almashtirish testni yiqitadi
    (`monitoring.Requirement.phrase` bilan bir xil rolda).

    `blocked_by` — mezonni **odam** ishi ushlab turgan bo'lsa, sababi.
    Bo'sh bo'lsa mezon texnik jihatdan ochiq.
    """

    code: str
    scope: Scope
    evidence: Evidence
    phrase: str
    #: Mezonni bajaradigan kod, `modul:simvol` ko'rinishida.
    binds: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()
    note: str = ""

    @property
    def is_restated(self) -> bool:
        """Ikkinchi mintaqada bu qator tekinga bajariladimi."""
        return self.scope is Scope.CODEBASE


#: `01` §23 ning to'liq ro'yxati. **Tartib ma'noli** — hujjatdagi
#: bilan bir xil, kontrakt testi shuni qulflaydi.
CRITERIA: tuple[Criterion, ...] = (
    Criterion(
        code="boundaries_loaded",
        scope=Scope.REGION,
        evidence=Evidence.RUNTIME,
        phrase="Все районы и махалли загружены, геометрия валидна, версии проставлены",
        binds=(
            "app.geo.queries:region_has_mahallas",
            "app.geo.quality:check_validity",
            "app.geo.quality:check_closed_rings",
            "app.geo.models:District.valid_from",
        ),
        blocked_by=("mahalla poligonlari olinmagan (H-5, `02` §H-5)",),
        note=(
            "Uchta shart bitta qatorda: yuklanganmi, geometriya to'g'rimi, "
            "versiya qo'yilganmi. Uchalasi uchun ham tekshiruv bor, lekin "
            "ularni mintaqa bo'yicha yurgizadigan so'rov yo'q."
        ),
    ),
    Criterion(
        code="control_sample",
        scope=Scope.REGION,
        evidence=Evidence.MANUAL,
        phrase="Контрольная выборка ≥50 точек привязывается к корректной махалле",
        note=(
            "Yagona mezon bo'lib, uning dalili tizimda umuman saqlanmaydi. "
            "`01` §10 UC-S2 uni oqimning 5-qadami deb sanaydi "
            "(«Смоук-проверка привязки на контрольных точках»), natijasi esa "
            "hech qayerda qayd etilmaydi — `03` §6 ning qo'lda tasdiqlanadigan "
            "mezonlari bilan bir xil holat."
        ),
    ),
    Criterion(
        code="uz_interface",
        scope=Scope.CODEBASE,
        evidence=Evidence.STRUCTURAL,
        phrase="Интерфейс на UZ полон: непереведённых строк нет",
        binds=("app.core.i18n:missing_keys",),
        note=(
            "Katalog to'liq (41–42 runlar qulflagan). Mintaqaga bog'liq matn "
            "bazada, lekin `name_uz` uchala jadvalda ham `NOT NULL`."
        ),
    ),
    Criterion(
        code="coverage_index_on_showcases",
        scope=Scope.CODEBASE,
        evidence=Evidence.STRUCTURAL,
        phrase="Coverage Index отображается на всех витринах региона",
        binds=("app.release.acceptance:SHOWCASES", "app.stats.coverage:CoverageIndex"),
        note=(
            "`01` PG-S4 ulushni so'raydi (100%), mavjudlikni emas — shuning "
            "uchun javob vitrina reyestridan hisoblanadi."
        ),
    ),
    Criterion(
        code="insufficient_data_verdict",
        scope=Scope.CODEBASE,
        evidence=Evidence.STRUCTURAL,
        phrase=(
            "Вердикт при отсутствии соседних репортов сформулирован "
            "как «данных недостаточно»"
        ),
        binds=(
            "app.clustering.lookup:AreaVerdict.NOT_ENOUGH_DATA",
            "app.clustering.lookup:MESSAGE_KEYS",
        ),
    ),
    Criterion(
        code="metrics_region_label",
        scope=Scope.CODEBASE,
        evidence=Evidence.STRUCTURAL,
        phrase="Метрики размечены `region`",
        binds=("app.obs.monitoring:REQUIREMENT_BY_CODE",),
        note="`01` §22 ning birinchi qatori bilan **bir xil** talab (69-run).",
    ),
    Criterion(
        code="young_region_disclaimer",
        scope=Scope.CODEBASE,
        evidence=Evidence.STRUCTURAL,
        phrase="Дисклеймер молодого региона активен",
        binds=("app.stats.maturity:WARNING_YOUNG", "app.release.acceptance:SHOWCASES"),
        note=(
            "Mexanizm bor, lekin ommaviy sahifaning standart ko'rinishida "
            "pometa chizilmaydi — 4-qator bilan bitta sababdan."
        ),
    ),
)

CRITERION_BY_CODE: dict[str, Criterion] = {c.code: c for c in CRITERIA}


def _check_registry() -> None:
    """Reyestrning o'zi izchilmi.

    Bu tekshiruvlar import paytida yuriladi: reyestr ma'lumot, ya'ni
    uning xatosi test yozilgunga qadar emas, **birinchi importda**
    ko'rinishi kerak (`gates._check_registry` bilan bir xil tartib).
    """
    codes = [c.code for c in CRITERIA]
    duplicates = sorted({code for code in codes if codes.count(code) > 1})
    if duplicates:
        raise ValueError(f"mezon kodi takrorlangan: {duplicates}")

    # `STRUCTURAL` mezonning tekshiruvisiz qolishi eng xavfli xato:
    # `evaluate` uni jimgina `UNMEASURED` deb ko'rsatardi, ya'ni
    # bugun javobi **bor** qator hisobotdan yo'qolardi.
    structural = {c.code for c in CRITERIA if c.evidence is Evidence.STRUCTURAL}
    if structural != set(STRUCTURAL_CHECKS):
        raise ValueError(
            "STRUCTURAL mezonlar va tekshiruvlar mos emas: "
            f"{sorted(structural ^ set(STRUCTURAL_CHECKS))}"
        )

    # `MANUAL` mezon `binds` bilan kelsa — o'zi bilan ziddiyat: dalil
    # tizimdan tashqarida deb e'lon qilingan qator kodga havola qilardi.
    bound_manual = [c.code for c in CRITERIA if c.evidence is Evidence.MANUAL and c.binds]
    if bound_manual:
        raise ValueError(f"MANUAL mezon `binds` bilan: {bound_manual}")

    showcase_codes = [s.code for s in SHOWCASES]
    if len(set(showcase_codes)) != len(showcase_codes):
        raise ValueError("vitrina kodi takrorlangan")

    # Indeksni ko'rsatmaydigan vitrina **sababsiz** qolmasligi kerak:
    # sababsiz bo'shliq keyingi o'quvchi uchun tasodifga o'xshaydi.
    silent = [s.code for s in SHOWCASES if not s.shows_index and not s.why_missing]
    if silent:
        raise ValueError(f"vitrina sababsiz indekssiz: {silent}")


_check_registry()


# --------------------------------------------------------------------------
# Baholash
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CriterionResult:
    """Mezon + uning bugungi holati."""

    criterion: Criterion
    status: CriterionStatus

    @property
    def is_met(self) -> bool:
        return self.status is CriterionStatus.MET


@dataclass(frozen=True)
class AcceptanceReport:
    """`01` §23 bo'yicha mintaqaning bugungi holati."""

    criteria: tuple[CriterionResult, ...]

    @property
    def is_accepted(self) -> bool:
        """Hamma mezon bajarilganmi.

        `UNMEASURED` **bajarilgan emas** — `gates.py` ning qoidasi
        (`03` §6 G-4 haqidagi «yumshatish» izohi) shu yerda ham
        amal qiladi.
        """
        return all(item.is_met for item in self.criteria)

    @property
    def met_count(self) -> int:
        return sum(1 for item in self.criteria if item.is_met)

    @property
    def unmet(self) -> tuple[CriterionResult, ...]:
        return tuple(i for i in self.criteria if i.status is CriterionStatus.UNMET)

    @property
    def unmeasured(self) -> tuple[CriterionResult, ...]:
        return tuple(i for i in self.criteria if i.status is CriterionStatus.UNMEASURED)

    @property
    def region_questions(self) -> tuple[CriterionResult, ...]:
        """Mintaqaning **o'zi** haqidagi qatorlar."""
        return tuple(i for i in self.criteria if i.criterion.scope is Scope.REGION)

    @property
    def restated_count(self) -> int:
        """Ikkinchi mintaqada tekinga bajariladigan **bajarilgan** qatorlar.

        Hisobotning eng muhim soni: u «5/7 yashil» degan xulosani
        «beshtasining hammasi Samarqanddan meros» deb o'qiydi.
        """
        return sum(1 for i in self.criteria if i.is_met and i.criterion.is_restated)


def evaluate(observations: Mapping[str, bool | None] | None = None) -> AcceptanceReport:
    """Kuzatuvlardan to'liq hisobot.

    `observations` — `{mezon kodi: bajarildimi}`, faqat `RUNTIME` va
    `MANUAL` mezonlar uchun. `STRUCTURAL` qatorlar bu yerdan
    **olinmaydi**: ularning javobi kodda va uni tashqaridan berish
    hisobotni soxtalashtirish yo'li bo'lardi.

    Notanish kalit — xato, e'tiborsiz emas (`gates.evaluate` bilan bir
    xil sabab): `control_sample` o'rniga `control_samples` yozilgan
    chaqiruv jimgina «o'lchanmagan» hisobot berardi.
    """
    values = dict(observations or {})
    unknown = sorted(set(values) - set(CRITERION_BY_CODE))
    if unknown:
        raise ValueError(f"notanish mezon kodi: {unknown}")
    structural = sorted(set(values) & set(STRUCTURAL_CHECKS))
    if structural:
        raise ValueError(f"STRUCTURAL mezon tashqaridan berilmaydi: {structural}")

    results = []
    for criterion in CRITERIA:
        if criterion.evidence is Evidence.STRUCTURAL:
            ok: bool | None = STRUCTURAL_CHECKS[criterion.code]()
        else:
            ok = values.get(criterion.code)
        if ok is None:
            status = CriterionStatus.UNMEASURED
        else:
            status = CriterionStatus.MET if ok else CriterionStatus.UNMET
        results.append(CriterionResult(criterion=criterion, status=status))
    return AcceptanceReport(criteria=tuple(results))

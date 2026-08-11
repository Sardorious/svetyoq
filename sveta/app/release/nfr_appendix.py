"""NFR deltasi va ilova (`01` §15 «Non-functional Requirements» + §31 «Appendix»).

**Nima uchun ikkala bo'lim bitta modulda.** §15 birinchi jumlasidan
meros bilan boshlanadi («Наследуются NFR ташкентского пакета
(ISO/IEC 25010). Дельта:»), §31 esa o'sha merosning **manba
ro'yxati**. Ya'ni §15 ning har qatori §31 ga suyanadi va ikkalasini
alohida o'lchash bitta savolni ikkiga bo'lardi: *delta nimaning
deltasi?*

## Asosiy topilma: meros ro'yxatining O'NTASIDAN NOLI paketda bor

86-run `17_OpenAPI.yaml` ni topdi (§16 orqali), 87-run
`03_Functional_Requirements.md` ni (§8 orqali), 98-run dizayn-tizim
hujjatini (`UX-S7` orqali) — har biri **bittadan**, har biri o'z
bo'limining darchasidan. §31 esa o'sha sinfning **ildiz reyestri**:
u meros qilinadigan o'nta hujjatni nomma-nom sanaydi va o'ntasidan
**birortasi ham** repoda yo'q. Endi bu topilma darchama-darcha emas,
ro'yxat bo'ylab o'lchanadi.

⚠️ **Olti prefiks to'qnashuvi.** 87-run bitta to'qnashuvni ko'rgan
edi (`03_` ikki hujjatni da'vo qiladi). Ro'yxat bo'ylab qaralganda
ular **oltita**: `01_`–`06_` prefikslarining har biri repoda **boshqa**
hujjat bilan band (`01_BRD.md` ↔ `01_PRD_Samarkand.md`,
`02_PRD.md` ↔ `02_Phase0_Validation_Plan_Samarqand.md` va h.k.).
Repoga qaragan o'quvchi oltala havolani ham «bajarilgan» deb o'ylashi
mumkin — fayl bor, prefiks mos, mazmun esa butunlay boshqa.

## Ikkinchi topilma: `NFR-S-07` ning mazmuni o'qib bo'lmaydigan joyda

Qator o'zi hech narsa talab qilmaydi: «целевые значения общие с
платформой, отдельного SLO для региона нет». Maqsad qiymatlari qayerda?
`04_NFR.md` da — ro'yxatdagi to'rtinchi yo'q hujjatda. Ya'ni mahsulot
availability va latency bo'yicha **nimaga** va'da berganini paketning
o'zidan bilib bo'lmaydi. Repo o'z tomonini to'g'ri bajaradi:
`app/obs/latency.py` gistogramma beradi (81-run) va mintaqaviy SLO
konstantasi hech qayerda yo'q — qator aynan shuni so'raydi. Lekin
«umumiy qiymatlar» ning o'zi ko'rinmas.

`NFR-S-03` ham shu sinfda: «500 тыс. пользователей» soni
`[BASELINE-TAS]` belgisi bilan keladi, ya'ni manbasi o'sha o'qib
bo'lmaydigan paket; repoda esa yuklama o'lchaydigan birorta asbob yo'q
(na load-test, na harness). Da'voni na tasdiqlab, na inkor qilib
bo'ladi — `UNMEASURED`.

## Uchinchi topilma: olti «ochiq zamechanie» dan uchtasining repoda izi yo'q

§31 «Обязательное к прочтению» bandi oltita ochiq zamechanieni
(`C-04`…`C-11`) **yo'q hujjatdan** «в полном объёме» meros qiladi.
Uchtasi repoda haqiqatan yashaydi: `C-09` (huquq) —
`app/admin/security.py` da 👤 qator, `C-11` (Coverage Index) —
`glossary.MARK_SOURCE` va `config.py` izohi, `C-04` (iqtisod) —
`risks.py` `RS-07` va `roadmap.py` chiqish mezoni. Qolgan uchtasi
(`C-05` baholar, `C-06` personalar, `C-10` ML metrikalari) kodda **bir
marta ham** uchramaydi.

⚠️ `C-10` alohida: u paketda ham faqat §31 ning o'sha bitta qatorida
uchraydi va tishlay olmaydi — mahsulotda ML sirti umuman yo'q.
«В полном объёме» meros qilingan zamechanie hech narsaga tegmaydi.

## To'rtinchi topilma: o'n standartdan uchtasining kod guvohi bor

§31 o'nta standartni sanaydi. Kod darajasida guvohi borlari: WCAG 2.1
AA (`ux_requirements` — `A11Y-*`, 96-run `A11Y-06` ni bajardi),
OpenAPI 3.1 (`api_requirements` + `app.openapi()` kontraktlari) va
C4 Model (`architecture.py` §29 ning diagrammasini o'qiydi). Qolgan
yettitasi (BABOK, PMBOK, IEEE 830, ISO/IEC 25010, UML 2.5, BPMN 2.0,
OWASP ASVS) `app/` da nomi bilan **bir marta ham** uchramaydi.
Bu defekt emas — BABOK kod standarti emas — lekin §20 OWASP ASVS ga
ishora qilgan mahsulotda ASVS darajasining birorta qayd etilgan
tekshiruvi yo'qligi 71-run ning `security.py` topilmalari bilan bir
qatorda turadi.

## §15 qatorlari bo'yicha

Yaxshi xabar: yettitadan **to'rttasi** to'liq qurilgan va testlar bilan
himoyalangan (`S-01` mintaqa reyestri — E19, `S-02` indekslar — `0008`
aynan shu qatorni docstringida nomlaydi, `S-05` chegara versiyalash —
§8 `F-3` bilan bir mexanizm, `S-06` i18n — ikki tomonlama kontrakt).

⚠️ `S-01` ning ichida ziddiyat bor va u bu bo'limniki emas: §15 «mintaqa
qo'shish kod o'zgarishini talab qilmaydi» deb **hozirgi** talab qo'yadi,
§7 esa mintaqaviy kengayishni Future Release ga chiqaradi (85-run
buni ochiq savol qilib yozgan). Mexanizm qurilgan va sintetik ikkinchi
mintaqa bilan testlanadi; haqiqiy ikkinchi mintaqa importi — 👤 (E19).

⚠️ `S-02` ning ikkinchi yarmi («отсутствие фильтра — дефект») ikki
sathda ushlanadi (indeks pariteti + API sirt kontrakti), lekin API dan
tashqaridagi so'rov yo'llari (`jobs`, bot servisi) uchun umumiy qorovul
yo'q — yangi yo'l filtrsiz yozilsa, uni faqat ko'z ushlaydi.

`S-04` (ma'lumotni RUz hududida saqlash) kod bilan yechilmaydi:
bu infratuzilma talabi, deploy odamniki, repo faqat qayd eta oladi —
va qayd etgan (`security.py` dagi 👤 qator, `C-09` ochiq).

## Nusxalar (57/92-runlar sinfi)

`S-05` ↔ §8 `F-3` ↔ §16 (`valid_from`/`valid_to`) ↔ §17 ER — bitta
qoida **to'rt** joyda; `S-02` ↔ `05` §7.2; `S-06` ↔ `CLAUDE.md` ↔
`04` §6. Nusxalar reyestrda ochiq bog'lanadi, test ularning
mavjudligini o'lchaydi.

## Nima qilinmadi va nima uchun

Hech narsa tuzatilmadi: yo'q hujjatlarni yozib bo'lmaydi (ular boshqa
loyihaning artefaktlari), load-test qurish `NFR-S-03` ning o'zi
so'ramagan ish (u aksincha «отдельно не рассчитывается» deydi),
ASVS auditi odam qarori. Modul o'lchaydi, tahrirlamaydi (75–77,
82–87, 98-runlar bilan bir xil qoida).

Modul `app/release/` da yashaydi va `app.*` dan hech narsa import
qilmaydi: reyestr sof e'lon, qurilgan sathni **test** o'lchaydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Hujjat bo'limlari. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "01 §15 + §31"

#: §15 jadvalining qatorlari — `NFR-S-*` identifikatorlari bilan.
SPEC_ROWS = 7

#: §15 epigrafi nomlaydigan standart. §31 ro'yxatida ham bor va kodda
#: nomi bilan uchramaydi — ya'ni epigraf standartga tayanadi, standartning
#: repodagi yagona izi esa shu ikki hujjat qatori.
EPIGRAPH_STANDARD = "ISO/IEC 25010"

#: NFR bazasi yashaydigan hujjat. Ro'yxatdagi to'rtinchi yo'q fayl;
#: paketda **faqat** §31 ning ro'yxat qatorida tilga olinadi.
BASELINE_DOC = "04_NFR.md"

#: «Обязательное к прочтению» hujjati. Repoda yo'q; undan olti ochiq
#: zamechanie «в полном объёме» meros qilinadi.
REVIEW_DOC = "21_Critical_Review.md"

#: §15 da «дефект» so'zini ko'taradigan qatorlar — aynan. Ikkalasi ham
#: qoidani e'lon bilan emas, test bilan ushlaydi (`Enforcement.TESTED`),
#: va test buni reyestr bilan ikki tomonlama qulflaydi.
DEFECT_ROWS: tuple[str, ...] = ("NFR-S-02", "NFR-S-06")


class NfrAppendixError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


class Delivered(StrEnum):
    """Repo qator aytgan narsa bilan nima qilgan.

    `SUBSTITUTED`/`FORKED` sinflari (§8 dagi) bu yerda **ataylab yo'q**:
    §15 ning birorta qatori boshqa qoida bilan almashtirilmagan.
    Bo'limning kasali boshqa — o'qib bo'lmaydigan tayanch.
    """

    #: Qurilgan va qator aytganidek.
    BUILT = "built"
    #: Kod bilan yechilmaydi: infratuzilma yoki jarayon, odam bajaradi.
    EXTERNAL = "external"
    #: Da'voni tekshiradigan mexanizm repoda umuman yo'q.
    UNMEASURED = "unmeasured"
    #: Qatorning normativ mazmuni paketda yo'q hujjatda yashaydi.
    UNREADABLE = "unreadable"


#: «Bajarilgan» deb sanaladigan yagona sinf.
DELIVERED_KEPT: frozenset[Delivered] = frozenset({Delivered.BUILT})


class Enforcement(StrEnum):
    """Qator buzilsa buni nima ko'rsatadi."""

    #: Kontrakt testi qizaradi.
    TESTED = "tested"
    #: Faqat odam yoki jarayon ushlaydi; repo holatni qayd etadi.
    MANUAL = "manual"
    #: Hech narsa — buzilish ko'rinmas o'tadi.
    NONE = "none"


class Baseline(StrEnum):
    """Qatorning normativ mazmuni qayerdan keladi."""

    #: Shu paketning o'zidan.
    LOCAL = "local"
    #: Yo'q hujjatdan (`[BASELINE-TAS]`, `04_NFR.md`, `21_Critical_Review.md`).
    INHERITED = "inherited"
    #: Talab mahalliy, tayanchi (ochiq zamechanie, son) meros.
    MIXED = "mixed"


@dataclass(frozen=True)
class Nfr:
    """§15 ning bitta qatori va uning bugungi bahosi."""

    code: str
    #: Qatorning qisqartirilgan mazmuni — tarjimasiz kalit ibora bilan.
    title: str
    delivered: Delivered
    enforcement: Enforcement
    baseline: Baseline
    #: Nima uchun aynan shu baho. Keyingi o'quvchi uchun.
    note: str
    #: Dalil: `modul:simvol`, `modul` yoki `tests/fayl.py` / fayl yo'li.
    binds: tuple[str, ...] = ()
    #: Xuddi shu qoida yana qayerlarda yozilgan (57/92-runlar sinfi).
    copies: tuple[str, ...] = ()
    #: Da'vo bilan qurilgan narsa orasidagi farq. Bo'sh — farq yo'q.
    gap: str = ""
    #: Qator ko'taradigan epistemik belgi — aynan, hujjatdagidek.
    marker: str = ""


@dataclass(frozen=True)
class InheritedDoc:
    """§31 «Наследуемые документы» ro'yxatining bitta nomi."""

    name: str
    #: Repoda o'sha prefiksni egallagan **boshqa** hujjat. Bo'sh —
    #: prefiks bo'sh, ya'ni yo'qligi hech bo'lmasa ko'rinadi.
    local_homonym: str = ""


@dataclass(frozen=True)
class Standard:
    """§31 «Стандарты» qatoridagi bitta nom."""

    name: str
    #: Kod darajasidagi guvohlar. Bo'sh — nom `app/` da uchramaydi.
    binds: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class Remark:
    """`21_Critical_Review.md` dan meros qilingan bitta ochiq zamechanie."""

    code: str
    #: §31 dagi qavs ichidagi mavzu — aynan.
    topic: str
    #: `01` da necha marta tilga olinadi (§31 ning o'zi bilan birga).
    doc_mentions: int
    #: Repodagi guvohlar. Bo'sh — kodda bir marta ham uchramaydi.
    binds: tuple[str, ...] = ()
    #: Zamechanie bugun umuman tegadigan sirt bormi. `C-10` uchun
    #: `False`: mahsulotda ML yo'q, ya'ni «в полном объёме» meros
    #: qilingan zamechanie hech narsani boshqarmaydi.
    can_bite: bool = True
    note: str = ""


# --------------------------------------------------------------------------
# §15 — delta qatorlari, hujjatdagi tartibda
# --------------------------------------------------------------------------

NFRS: tuple[Nfr, ...] = (
    Nfr(
        code="NFR-S-01",
        title="Добавление региона не требует изменения кода",
        delivered=Delivered.BUILT,
        enforcement=Enforcement.TESTED,
        baseline=Baseline.LOCAL,
        note=(
            "E19 aynan shu qatorni qurdi: mintaqa nuqtadan aniqlanadi "
            "(`pick_for_point`), bbox bazada (`0005`, ilgari lug'at "
            "edi), yangi mintaqa `tools/region_admin.py` bilan "
            "qo'shiladi — kod tegilmaydi. Test sintetik ikkinchi "
            "mintaqa (Toshkent qatori) bilan buni yurgizadi. "
            "`settings.default_region_code` sozlama bo'lib qoldi va "
            "faqat zaxira yo'lda ishlaydi."
        ),
        binds=(
            "app.geo.registry:pick_for_point",
            "app.geo.bbox:make_bbox",
            "tools/region_admin.py",
            "tests/test_region_registry.py",
        ),
        gap=(
            "Haqiqiy ikkinchi mintaqa hech qachon import qilinmagan — "
            "E19 ning 👤 sharti. Ustiga §7 mintaqaviy kengayishni "
            "Future Release ga chiqaradi, §15 esa talabni hozirgi "
            "zamonda qo'yadi (85-run ning ochiq savoli)."
        ),
    ),
    Nfr(
        code="NFR-S-02",
        title="Фильтрация по `region_id` на уровне индекса",
        delivered=Delivered.BUILT,
        enforcement=Enforcement.TESTED,
        baseline=Baseline.LOCAL,
        note=(
            "`0008` migratsiyasi docstringida aynan shu qatorni "
            "nomlaydi va uchta indeks qo'shadi; indeks pariteti "
            "kontrakti ularni sabab satri bilan qulflaydi "
            "(`NFR-S-02` sababi test faylida literal turadi). "
            "Ikkinchi yarim — «отсутствие фильтра — дефект» — API "
            "sathida umumiy qorovul bilan ushlanadi: har geo-endpoint "
            "aynan bitta `region` parametrini e'lon qilishi "
            "`app.openapi()` dan sanaladi."
        ),
        binds=(
            "alembic/versions/0008_region_indexes.py",
            "tests/test_schema_index_parity.py",
            "tests/test_api_surface_contract.py",
        ),
        copies=("05 §7.2",),
        gap=(
            "API dan tashqaridagi so'rov yo'llari (`app.jobs`, bot "
            "servisi) uchun «filtr bormi» degan umumiy qorovul yo'q — "
            "u yerda qoidani faqat ko'z ushlaydi."
        ),
    ),
    Nfr(
        code="NFR-S-03",
        title="Нагрузка не рассчитывается отдельно (500 тыс.)",
        delivered=Delivered.UNMEASURED,
        enforcement=Enforcement.NONE,
        baseline=Baseline.INHERITED,
        marker="[BASELINE-TAS]",
        note=(
            "Qator ikki narsani aytadi va ikkalasini ham tekshirib "
            "bo'lmaydi: «500 тыс.» soni `[BASELINE-TAS]` bilan keladi, "
            "ya'ni manbasi o'qib bo'lmaydigan paket; repoda esa "
            "yuklamani o'lchaydigan birorta asbob yo'q — na load-test, "
            "na harness, na sig'im hisobi. Da'vo na tasdiqlanadi, na "
            "inkor qilinadi. Belgining o'zi repoda yashaydi "
            "(`success.TAG_BASELINE_TAS`, 84-run) — bu qatorning "
            "yagona kod izi."
        ),
        binds=("app.release.success:TAG_BASELINE_TAS",),
        gap=(
            "Sonning manbasi ham, tekshiruv mexanizmi ham yo'q; "
            "buzilish (mas., ikki mintaqa yuklamasi gorizontdan "
            "chiqsa) hech narsada ko'rinmaydi."
        ),
    ),
    Nfr(
        code="NFR-S-04",
        title="Локализация хранения данных на территории РУз",
        delivered=Delivered.EXTERNAL,
        enforcement=Enforcement.MANUAL,
        baseline=Baseline.MIXED,
        marker="C-09",
        note=(
            "Infratuzilma talabi: qayerda joylashtirish — deploy "
            "qarori, deploy esa odamniki (CLAUDE.md: server odam "
            "tomonida). Kod bu yerda faqat qayd eta oladi va qayd "
            "etgan: `security.py` ning posture reyestrida huquqiy "
            "tekshiruv 👤 va `C-09` ochiq deb turadi (71-run). "
            "Talabning tayanchi — o'sha `C-09` — yo'q hujjatdan "
            "meros, ya'ni zamechaniening asl matnini o'qib bo'lmaydi."
        ),
        binds=("app.admin.security",),
        gap="Repo joylashuvni ko'rmaydi; kafolat butunlay deploy tomonida.",
    ),
    Nfr(
        code="NFR-S-05",
        title="Справочники границ версионируются",
        delivered=Delivered.BUILT,
        enforcement=Enforcement.TESTED,
        baseline=Baseline.LOCAL,
        note=(
            "Bo'limning eng puxta bajarilgan qatori va §8 `F-3` bilan "
            "**bitta mexanizm**: `valid_from`/`valid_to` sxemada, "
            "`districts_for_period` davr kesimini beradi, "
            "`boundaries.summarize` versiya raqamini va davr ichida "
            "chegara o'zgarganini javobga qo'yadi, tarixiy statistika "
            "`?at=` bilan o'sha kesimda qayta o'qiladi."
        ),
        binds=(
            "app.stats.boundaries:summarize",
            "app.geo.queries:districts_for_period",
            "tests/test_stats_boundaries.py",
        ),
        copies=("01 §8 F-3", "01 §16", "01 §17"),
    ),
    Nfr(
        code="NFR-S-06",
        title="Полный интерфейс на UZ и RU; непереведённая строка — дефект",
        delivered=Delivered.BUILT,
        enforcement=Enforcement.TESTED,
        baseline=Baseline.LOCAL,
        note=(
            "E4 ning o'zagi va loyihaning eng qattiq qoidalaridan "
            "biri: i18n kaliti kontrakti **ikki tomonlama** (kod → "
            "katalog, katalog → kod, 41/42-runlar), kataloglar UZ va "
            "RU da kalitma-kalit teng, til muzokarasi alohida "
            "testlanadi. Qattiq kodlangan matn testni qizartiradi — "
            "qator talab qilgan «bloklovchi defekt» maqomi amalda "
            "CI maqomi."
        ),
        binds=(
            "app.core.i18n",
            "tests/test_i18n_key_contract.py",
            "tests/test_language_contract.py",
        ),
        copies=("CLAUDE.md", "04 §6"),
    ),
    Nfr(
        code="NFR-S-07",
        title="Availability и latency — целевые значения общие с платформой",
        delivered=Delivered.UNREADABLE,
        enforcement=Enforcement.NONE,
        baseline=Baseline.INHERITED,
        note=(
            "Qator o'zi hech narsa talab qilmaydi — u ko'rsatadi. "
            "Ko'rsatgan joyi `04_NFR.md`, ro'yxatdagi to'rtinchi yo'q "
            "hujjat. Ya'ni mahsulot availability/latency bo'yicha "
            "**nimaga** va'da berganini paketdan bilib bo'lmaydi. "
            "Repo o'z tomonini to'g'ri bajaradi: javob vaqti "
            "gistogrammasi bor (`obs.latency`, 81-run), mintaqaviy "
            "SLO konstantasi esa hech qayerda yo'q — qator aynan "
            "shuni so'raydi."
        ),
        binds=("app.obs.latency",),
        gap=(
            "«Umumiy qiymatlar» ning o'zi ko'rinmas: chegara son "
            "sifatida faqat `03` §9 ning «API p95 >300 ms» tetigida "
            "uchraydi va u SLO emas, Redis qarorining sharti."
        ),
    ),
)


# --------------------------------------------------------------------------
# §31 — meros ro'yxati, zamechanielar, standartlar
# --------------------------------------------------------------------------

#: «Наследуемые документы» — aynan hujjatdagi tartibda. O'ntasidan
#: **noli** repoda bor; oltitasining prefiksi boshqa hujjat bilan band.
INHERITED_DOCS: tuple[InheritedDoc, ...] = (
    InheritedDoc(name="01_BRD.md", local_homonym="01_PRD_Samarkand.md"),
    InheritedDoc(name="02_PRD.md", local_homonym="02_Phase0_Validation_Plan_Samarqand.md"),
    InheritedDoc(name="03_Functional_Requirements.md", local_homonym="03_Development_Roadmap.md"),
    InheritedDoc(name="04_NFR.md", local_homonym="04_Epic_Roadmap_Solo.md"),
    InheritedDoc(name="05_API.md", local_homonym="05_Technical_Design.md"),
    InheritedDoc(name="06_Database.md", local_homonym="06_Confirmation_Logic.md"),
    InheritedDoc(name="07_RBAC.md"),
    InheritedDoc(name="08_System_Architecture.md"),
    InheritedDoc(name="17_OpenAPI.yaml"),
    InheritedDoc(name="18_ERD.md"),
)

#: «Обязательное к прочтению» dan meros qilingan ochiq zamechanielar —
#: §31 dagi tartibda, mavzulari qavsdagidek.
REMARKS: tuple[Remark, ...] = (
    Remark(
        code="C-04",
        topic="экономика",
        doc_mentions=4,
        binds=("app.release.risks", "app.release.roadmap"),
        note=(
            "§4 o'zi haqida «не описывает бизнес-модель» deydi, "
            "`RS-07` moliyalashtirish yo'qligini Faza 0 shlyuzi qiladi, "
            "roadmap chiqish mezoni manba topilishini talab qiladi."
        ),
    ),
    Remark(
        code="C-05",
        topic="оценки",
        doc_mentions=2,
        note=(
            "§24 «сроки не проставлены намеренно» — zamechanie hujjat "
            "darajasida hurmat qilinadi, kodda esa izi yo'q (muddat "
            "kodda umuman ifodalanmaydi, ya'ni bu kutilgan holat)."
        ),
    ),
    Remark(
        code="C-06",
        topic="персоны",
        doc_mentions=2,
        note=(
            "§5 butun bo'limni `[ГИПОТЕЗА]` deb belgilaydi va P0-3 "
            "intervyularigacha almashtirilmaydi. Kodda personalar "
            "ifodalanmaydi — iz yo'qligi kutilgan."
        ),
    ),
    Remark(
        code="C-09",
        topic="право",
        doc_mentions=4,
        binds=("app.admin.security", "app.release.roadmap", "app.release.dependencies"),
        note=(
            "Olti zamechaniedan repoda eng chuqur ildiz otgani: "
            "posture reyestrida 👤 qator, roadmap da `P0-7` gipotezasi, "
            "dependencies da huquqiy tugun."
        ),
    ),
    Remark(
        code="C-10",
        topic="метрики ML",
        doc_mentions=1,
        can_bite=False,
        note=(
            "Paketda faqat §31 ning ro'yxat qatorida uchraydi va "
            "tishlay olmaydi: mahsulotda ML sirti yo'q — na model, na "
            "bashorat, na o'rgatish yo'li. «В полном объёме» meros "
            "qilingan zamechanie hech narsani boshqarmaydi."
        ),
    ),
    Remark(
        code="C-11",
        topic="Coverage Index",
        doc_mentions=2,
        binds=("app.core.glossary:MARK_SOURCE", "app.stats.coverage"),
        note=(
            "Formula validatsiya qilinmagani kodda uch joyda ochiq "
            "yoziladi (glossary `MARK_SOURCE`, `config.py` izohi, "
            "`coverage.py` docstringi) va qiymat E11 ga qoldirilgan."
        ),
    ),
)

#: «Стандарты» qatori — aynan hujjatdagi tartibda va yozuvda.
STANDARDS: tuple[Standard, ...] = (
    Standard(name="BABOK v3"),
    Standard(name="PMBOK 7"),
    Standard(name="IEEE 830-1998"),
    Standard(
        name="ISO/IEC 25010",
        note="§15 epigrafi tayanadi; kodda nomi bilan uchramaydi.",
    ),
    Standard(
        name="WCAG 2.1 AA",
        binds=("app.release.ux_requirements",),
        note="`A11Y-01…A11Y-10` §14 dan; `A11Y-06` 96-run da bajarildi.",
    ),
    Standard(
        name="OpenAPI 3.1",
        binds=("app.core.api_requirements", "tests/test_openapi_contract.py"),
        note="`app.openapi()` kontraktlari ikki fayldan o'lchanadi.",
    ),
    Standard(name="UML 2.5"),
    Standard(
        name="BPMN 2.0",
        note=(
            "§12 ning diagrammalari o'qiladi (`ux_requirements`, 98-run), "
            "lekin BPMN sifatida emas — nom kodda uchramaydi."
        ),
    ),
    Standard(
        name="C4 Model",
        binds=("app.core.architecture",),
        note="§29 ning «C4 Container» bloki 79-run dan beri parse qilinadi.",
    ),
    Standard(
        name="OWASP ASVS",
        note=(
            "§20 ishora qiladi, `security.py` (71-run) esa ASVS ni "
            "nomlamaydi — daraja ham, tekshiruv ro'yxati ham qayd "
            "etilmagan."
        ),
    ),
)

#: «Исследования» bandi. Hujjat halol: «Отсутствуют» — va repoda ham
#: tadqiqot artefakti yo'q, ya'ni band bugungi haqiqatga mos.
RESEARCH_PRESENT = False


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class NfrAppendixReport:
    """§15 + §31 ning bugungi holati."""

    nfrs: tuple[Nfr, ...]
    inherited_docs: tuple[InheritedDoc, ...]
    remarks: tuple[Remark, ...]
    standards: tuple[Standard, ...]

    def __post_init__(self) -> None:
        codes = [n.code for n in self.nfrs]
        if len(set(codes)) != len(codes):
            raise NfrAppendixError("NFR kodlari takrorlanadi")
        for item in (*self.nfrs, *self.remarks):
            if not isinstance(item.binds, tuple):
                raise NfrAppendixError(f"{item.code}: `binds` kortej emas")
            if any(not isinstance(b, str) or "." not in b for b in item.binds):
                raise NfrAppendixError(f"{item.code}: `binds` shakli buzilgan")
        for nfr in self.nfrs:
            if nfr.enforcement is Enforcement.TESTED and not any(
                b.startswith("tests/") for b in nfr.binds
            ):
                raise NfrAppendixError(f"{nfr.code}: `TESTED`, lekin test bindi yo'q")
            if nfr.delivered is Delivered.EXTERNAL and nfr.enforcement is Enforcement.TESTED:
                raise NfrAppendixError(f"{nfr.code}: `EXTERNAL` qatorni test himoyalay olmaydi")
            if nfr.delivered in (Delivered.UNMEASURED, Delivered.UNREADABLE) and not nfr.gap:
                raise NfrAppendixError(f"{nfr.code}: tekshirib bo'lmaydigan qator, farq yozilmagan")
        for remark in self.remarks:
            if not remark.can_bite and remark.binds:
                raise NfrAppendixError(
                    f"{remark.code}: tishlay olmaydigan zamechanieda bind bo'lishi mumkin emas"
                )

    # --- §15 kesimlari ---

    @property
    def by_delivered(self) -> dict[Delivered, tuple[str, ...]]:
        result: dict[Delivered, list[str]] = {d: [] for d in Delivered}
        for nfr in self.nfrs:
            result[nfr.delivered].append(nfr.code)
        return {d: tuple(codes) for d, codes in result.items()}

    @property
    def by_enforcement(self) -> dict[Enforcement, tuple[str, ...]]:
        result: dict[Enforcement, list[str]] = {e: [] for e in Enforcement}
        for nfr in self.nfrs:
            result[nfr.enforcement].append(nfr.code)
        return {e: tuple(codes) for e, codes in result.items()}

    @property
    def kept(self) -> tuple[Nfr, ...]:
        """Qurilgan va aytilganidek qatorlar."""
        return tuple(n for n in self.nfrs if n.delivered in DELIVERED_KEPT)

    @property
    def unverifiable(self) -> tuple[Nfr, ...]:
        """Na tasdiqlab, na inkor qilib bo'lmaydigan qatorlar.

        Ikkala sinf ham (`UNMEASURED`, `UNREADABLE`) bitta xossani
        bo'lishadi: buzilish hech narsada ko'rinmaydi. Farqi sababda —
        birida mexanizm yo'q, ikkinchisida mazmunning o'zi.
        """
        return tuple(
            n
            for n in self.nfrs
            if n.delivered in (Delivered.UNMEASURED, Delivered.UNREADABLE)
        )

    @property
    def duplicated(self) -> tuple[Nfr, ...]:
        """Boshqa hujjat joylarida nusxasi bor qatorlar."""
        return tuple(n for n in self.nfrs if n.copies)

    @property
    def blind_spots(self) -> tuple[Nfr, ...]:
        """Buzilishini hech narsa ko'rsatmaydigan qatorlar."""
        return tuple(n for n in self.nfrs if n.enforcement is Enforcement.NONE)

    # --- §31 kesimlari ---

    @property
    def docs_declared(self) -> int:
        return len(self.inherited_docs)

    @property
    def homonym_docs(self) -> tuple[InheritedDoc, ...]:
        """Prefiksи repoda boshqa hujjat bilan band bo'lgan nomlar.

        Eng aldamchi holat: fayl bor, prefiks mos, mazmun boshqa.
        """
        return tuple(d for d in self.inherited_docs if d.local_homonym)

    @property
    def inheritance_witnessed(self) -> bool:
        """Meros manbalarini repo ko'ra oladimi.

        Bugun `False` va ro'yxatdagi hujjatlar paketga qo'shilmaguncha
        shunday qoladi (87-run `inheritance_witnessed` bilan bir shakl,
        lekin bitta hujjat emas — **o'ntasi** haqida).
        """
        return False

    @property
    def unwitnessed_remarks(self) -> tuple[Remark, ...]:
        """Kodda bir marta ham uchramaydigan zamechanielar."""
        return tuple(r for r in self.remarks if not r.binds)

    @property
    def dormant_remarks(self) -> tuple[Remark, ...]:
        """Tegadigan sirti umuman yo'q zamechanielar."""
        return tuple(r for r in self.remarks if not r.can_bite)

    @property
    def witnessed_standards(self) -> tuple[Standard, ...]:
        """Kod darajasida guvohi bor standartlar."""
        return tuple(s for s in self.standards if s.binds)

    # --- Yakuniy hukmlar ---

    @property
    def rows_hold(self) -> bool:
        """§15 ning har qatori bugun tekshiriladigan holatdami.

        Bugun `False`: yettitadan uchtasi (`S-03`, `S-04`, `S-07`)
        yo o'lchab bo'lmaydigan, yo repo tashqarisidagi qator.
        """
        return len(self.kept) == len(self.nfrs)

    @property
    def accurate(self) -> bool:
        """§15 + §31 bugungi haqiqatni to'liq tasvirlaydimi.

        Uch shart, uchalasi mustaqil (82-run sabog'i): qatorlar
        tekshiriladigan bo'lsin; meros manbalari o'qiladigan bo'lsin;
        meros zamechanielari tegadigan sirtga ega bo'lsin.
        """
        return (
            self.rows_hold
            and self.inheritance_witnessed
            and not self.dormant_remarks
        )


def evaluate() -> NfrAppendixReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kod tuzilishidan keladi (`scope`,
    `functional_requirements`, `ux_requirements` bilan bir xil sabab).
    """
    return NfrAppendixReport(
        nfrs=NFRS,
        inherited_docs=INHERITED_DOCS,
        remarks=REMARKS,
        standards=STANDARDS,
    )

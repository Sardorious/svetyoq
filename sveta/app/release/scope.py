"""Ko'lam (`01` §7 «Scope») ↔ kod.

**Nima uchun bu modul bor.** 84-run uchta nomzod qoldirdi va §7 ni
birinchi qatorga qo'ydi, bitta ogohlantirish bilan: bo'lim boshqa
reyestrlar bilan **ustma-tushadi** (§24 fazalar, §25 relizlar, §28
bog'liqliklar, §4 KPI lar), ya'ni uni nusxa qilib yozish ish emas,
takror bo'lardi. Shuning uchun bu modul ustma-tushishni **qulflaydi**:
har qatorning «Обоснование» katagi boshqa bo'limga havola qiladi va
test o'sha havolani **hujjatdan parse qilib** yechadi — havola nimani
o'lchashini bu yerda qayta o'lchamaydi.

Bo'limning o'z savoli ham qolganlaridan farq qiladi. §24 «qachon», §25
«nima bilan», §4 «qanchaga» deb so'raydi; §7 esa **chegara** chizadi:
uch ro'yxat — kiradi, keyinroq, umuman kirmaydi. Chegaraga beriladigan
savol bitta va u ikki tomonlama: *ichkaridagi qurilganmi va tashqaridagi
qurilmay qolganmi?*

## Asosiy topilma: bitta yo'q mexanizm uchala ro'yxatning ham qatorini hal qiladi

`reports.source` ustuni va `06` §2 ning olti qatorli manba registri
bor (`app.reports.sources:SOURCES`), `intake.create_report` esa
`source_code: str = DEFAULT_SOURCE_CODE` bilan e'lon qilingan va
**butun repoda birorta chaqiruvchi unga literal bermaydi** — na bot
(`app.bot.handlers`), na ma'muriy API (`app/api/v1/admin.py` da
uzilishni tasdiqlash yoki xabar kiritish endpointi yo'q), na asboblar
(`tools/recluster.py` va `tools/simulate.py` mavjud qatordan
ko'chiradi). Ya'ni `bot` dan boshqa manba tanlanadigan yo'l yo'q.

Shu bitta bo'shliq **to'rt** qatorni hal qiladi va ular uchala
ro'yxatda ham turibdi:

* **MVP `S-7`** — «Ручной разбор публикаций регионального источника
  1055» ning boradigan joyi yo'q: `official` qatori bazada bor,
  `is_authoritative=True`, `layer='official'` qoidasi yozilgan
  (`06` §2.2), va uni tanlaydigan kod yo'q → `HOLLOW`;
* **Future `F-4`** — «официальная интеграция с региональным
  оператором» **allaqachon bazada**: `operator_api` `0003` da seed
  qilinadi va u ham `is_authoritative=True`. Bu ko'lamdan chiqish
  bo'lardi, agar o'sha qatorni tanlaydigan yo'l bo'lsa. Yo'q — ya'ni
  chegara ushlab turilibdi, **o'z sababi bilan emas**;
* **Out of Scope `O-3`** — «официальный статус источника» ni ushlab
  turgan narsa ham o'sha: mahsulot o'zini rasmiy deb e'lon
  qilmasligini dislaymer mexanizmi emas (u statistika uchun,
  `stats.methodology`), balki rasmiy qatorga umuman yetib bo'lmasligi
  ta'minlaydi;
* va yana bitta MVP qatori, `S-8` — «партнёрская схема с
  махаллинскими чатами»: sherik aktivining og'irligi (`mahalla_active`,
  `2.0`) o'sha registrda turibdi va u ham tanlanmaydi, ya'ni sovuq
  start sxemasi kelishilgan taqdirda ham repo uni oddiy `bot`
  xabaridan ajrata olmaydi.

Uch xil ro'yxatdagi to'rt qator bitta kunda bir vaqtda o'z ma'nosini
o'zgartiradi — `source_code` ni beradigan birinchi chaqiruvchi
yozilgan kuni. §7 ni o'qigan odam buni ko'rmaydi: uning uchun bular
to'rtta mustaqil qaror.

## Ikkinchi topilma: `F-5` — ko'lamdan chiqqan yagona qator, va u eng katta

«Распространение на другие города области» — **Future Release**.
Repo esa ko'plikni qurgan: `registry.active_regions` **tuple**
qaytaradi, `registry.pick_for_point` ular orasidan tanlaydi,
`tools/region_admin.py` `N`-mintaqani qo'sha oladi, `GET /regions`
ro'yxat beradi, `reports.region_id` `NOT NULL` va `0008` unga indeks
qo'yadi. Bitta mintaqali mahsulotga bularning birortasi kerak emas:
unga dispetcher ham, ro'yxat ham, mintaqa bo'yicha filtr ham kerak
emas edi.

§7 ning MVP qatori (`S-1`) faqat **birlikni** ruxsat beradi —
«активация региона конфигурацией». Ko'plik esa `03` §3 da **R3.0**,
ya'ni uchinchi relizda. Bu — bir xil ishning uchinchi hujjatda
uchinchi joyga qo'yilishi: 77-run `01` §25 bilan `03` §3 ning `R3.0`
to'qnashuvini topgan, 82-run fazalar ro'yxatini o'lchagan, endi §7
o'sha ishni «keyinroq» deb ataydi — u allaqachon prodda.

⚠️ Farqni sezish oson emas, chunki qurilgani **ma'lumot emas,
mexanizm**: ikkinchi mintaqa hali import qilinmagan (E19 ning to'sig'i),
ya'ni tashqi qarashda chegara buzilmagan ko'rinadi. `CROSSED` shu
sababdan `Presence` dan **alohida** o'q: «qurilganmi» va «chegaradan
chiqdimi» bir savol emas.

## `Warrant` — «Обоснование» ustuni to'rt xil narsa deydi

Ustun bir xil ko'rinadi va sakkiz qatorda to'rt xil turdagi asos
beradi: paketdan tashqaridagi funksional talab (`FR-807`), shu
hujjatning maqsadi (`PG-S3`, `PG-S4`, `PG-S2`), shu hujjatning
bo'limi (`§17`), Faza 0 vazifasi (`P0-1`) va oddiy nasr («Ядро
продукта», «Митигация риска пустой карты»). Ularni bitta sinf bilan
o'qish 76-run ning `Блокирует` ustunidagi xatoning aynan o'zi
bo'lardi.

⚠️ **Eng jim topilma shu o'qda:** `S-6` («Подписка на адрес и
уведомления», MVP = Ph.0 + Ph.1) o'zini `PG-S2` bilan asoslaydi, va
`PG-S2` ning gorizonti — **Ph.2**. Ya'ni MVP qatori o'zidan
**keyinroq** keladigan maqsadga tayanadi va bunday asos hech narsani
asoslamaydi. Ustiga `PG-S2` ning mazmuni obuna haqida ham emas
(«Карта осмысленна на уровне махалли»): katak vaqt bo'yicha ham,
ma'no bo'yicha ham noto'g'ri manzilga havola qiladi. Gorizont **qo'lda
ko'chirilmaydi** — `01` §3 ning jadvalidan parse qilinadi, aks holda
57-run ning tuzog'i takrorlanardi (fayl o'z nusxasini o'lchaydi).

## Teskari yo'nalish: uchta qurilgan sirt uchala ro'yxatda ham yo'q

Ommaviy API (E15, `app/api/v1/`), moderatsiya (E8, `app/admin/`) va
H3 issiqlik xaritasi (E16, `/heatmap`) §7 da **na kiradi, na
keyinroq, na kirmaydi**. Ko'lam jadvalining ma'nosi shundaki, unda
yo'q narsa qurilmaydi — uchalasi qurilgan va ikkitasi prodda.

Ommaviy API uchun bu **to'rtinchi** hujjat: 77-run uni `01` §25 da,
82-run `01` §24 da, 84-run `01` §4 da topgan. Ya'ni bo'shliq bitta
hujjatning e'tiborsizligi emas — paketning butun rejalashtirish
qatlami mahsulotning bitta sirtini ko'rmaydi.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi: bu modul o'lchaydi, tahrirlamaydi (75-, 76-,
77-, 82-, 83- va 84-runlar bilan bir xil qoida). `Out of Scope` ning
qatorlari uchun «yo'qligi» dalili sifatida simvolning yo'qligi
olinadi — bu isbot emas, kuzatuv, va test uni aynan shunday
nomlaydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Hujjat bo'limi. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "01 §7"

#: Uchala ro'yxatning uzunligi. Hujjatdan parse qilinadi va reyestr
#: bilan solishtiriladi (`test_scope_contract`).
SPEC_MVP_ROWS = 8
SPEC_FUTURE_ITEMS = 5
SPEC_OUT_ITEMS = 5

#: MVP jadvalining sarlavhasi — aynan.
SPEC_COLUMNS: tuple[str, ...] = ("Входит", "Обоснование")

#: Uchala ro'yxatning sarlavhalari — aynan.
HEADING_MVP = "MVP (Phase 0 + Phase 1)"
HEADING_FUTURE = "Future Release"
HEADING_OUT = "Out of Scope"

#: MVP qaysi fazalarni o'z ichiga oladi. Sarlavhaning o'zidan keladi.
MVP_PHASES: tuple[str, ...] = ("Ph.0", "Ph.1")

#: `01` §3 «Product Goals» jadvalidagi gorizontlarning tartibi.
#: `Warrant.MISDATED` shu tartibdan hisoblanadi, qo'lda emas.
PHASE_ORDER: tuple[str, ...] = ("Ph.0", "Ph.1", "Ph.2", "Ph.3")


class Standing(StrEnum):
    """Qator qaysi ro'yxatda turibdi."""

    #: «Входит» — MVP (Phase 0 + Phase 1).
    IN = "in"
    #: «Future Release» — keyinroq.
    LATER = "later"
    #: «Out of Scope» — umuman kirmaydi.
    OUT = "out"


class Presence(StrEnum):
    """Repo bugun bu qator bo'yicha nima qilgan.

    Olti sinf, va ular bir-birini almashtirmaydi: «bor / yo'q» ikkiligi
    bu bo'limda **to'rtta** turli holatni bitta katakka tiqib qo'yardi
    (67- va 84-runlarning sabog'i).
    """

    #: To'liq qurilgan va yo'l ochiq.
    BUILT = "built"
    #: Qatorda **nomlangan** bo'laklarning bir qismi qurilgan.
    PARTIAL = "partial"
    #: Xulq-atvor bor, lekin qator nomlagan mexanizm orqali emas.
    DISPLACED = "displaced"
    #: Kod qurilgan, uni to'ldiradigan yo'l yoki ma'lumot yo'q.
    UNREACHABLE = "unreachable"
    #: Repoda hech narsa yo'q.
    ABSENT = "absent"
    #: Odam yoki sherik ishi — repo guvoh bo'la olmaydi.
    EXTERNAL = "external"


#: Qator «qurilgan» deb hisoblanadigan sinflar. `PARTIAL` bu yerda
#: **yo'q**: nomlangan bo'lakning biri yetishmasa, qator o'z va'dasini
#: bajarmaydi.
PRESENCE_BUILT: frozenset[Presence] = frozenset({Presence.BUILT})

#: Repo tomonidan yopilishi mumkin bo'lmagan sinf: kutilayotgani kod
#: emas, odam.
PRESENCE_OUTSIDE: frozenset[Presence] = frozenset({Presence.EXTERNAL})


class Fence(StrEnum):
    """Qatorning chegara da'vosi bugun rostmi."""

    #: Ichkaridagi qurilgan yoki tashqaridagi qurilmagan — mos.
    HELD = "held"
    #: «Keyinroq» yoki «kirmaydi» deb yozilgan, repoda esa bor.
    CROSSED = "crossed"
    #: «Kiradi» deb yozilgan, repoda esa to'liq emas.
    HOLLOW = "hollow"
    #: Repo bu qatorga umuman guvoh bo'la olmaydi.
    UNWITNESSED = "unwitnessed"


class Warrant(StrEnum):
    """«Обоснование» katagi nimaga tayanadi.

    `Standing.LATER` va `Standing.OUT` qatorlarida ustun **yo'q** —
    ular nasriy ro'yxat, jadval emas; shuning uchun `NONE`.
    """

    #: Shu hujjatda ta'riflangan va gorizonti qatordan keyin emas.
    ANCHORED = "anchored"
    #: Ta'riflangan, lekin gorizonti qatordan **keyinroq**.
    MISDATED = "misdated"
    #: Ta'rifi paketdan tashqarida (Toshkent paketi).
    FOREIGN = "foreign"
    #: Identifikator emas, nasr.
    PROSE = "prose"
    #: Ustun umuman yo'q.
    NONE = "none"


#: Asos «ishlaydi» deb hisoblanadigan sinflar. `PROSE` ham shu yerda:
#: nasriy sabab yomon emas, u shunchaki tekshirilmaydi.
WARRANT_SOUND: frozenset[Warrant] = frozenset({Warrant.ANCHORED, Warrant.PROSE, Warrant.NONE})


class ScopeError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class ScopeItem:
    """Uchala ro'yxatning bitta qatori va uning bugungi bahosi."""

    code: str
    #: Hujjatdagi matn — **aynan**, tarjimasiz.
    claim: str
    standing: Standing
    presence: Presence
    fence: Fence
    warrant: Warrant
    #: Nima uchun aynan shu baho. Keyingi o'quvchi uchun.
    note: str
    #: «Обоснование» katagi — aynan. `Standing.IN` da majburiy.
    warrant_text: str = ""
    #: `PG-S*` havolasining `01` §3 dagi gorizonti. Faqat `ANCHORED` va
    #: `MISDATED` da to'ldiriladi; test uni hujjatdan parse qilib
    #: solishtiradi.
    warrant_phase: str = ""
    #: Dalil: `modul:simvol`. `ABSENT` da bo'sh — yo'qlikning dalili
    #: simvolning yo'qligi, va uni test alohida o'lchaydi.
    binds: tuple[str, ...] = ()
    #: Da'vo bilan qurilgan narsa orasidagi farq.
    gap: str = ""


# --------------------------------------------------------------------------
# Reyestr — `01` §7, uchala ro'yxat ham hujjatdagi tartibda
# --------------------------------------------------------------------------

ITEMS: tuple[ScopeItem, ...] = (
    # ---- MVP (Phase 0 + Phase 1) -----------------------------------------
    ScopeItem(
        code="S-1",
        claim="Активация региона конфигурацией: полигоны районов, махаллей, зона покрытия",
        standing=Standing.IN,
        presence=Presence.PARTIAL,
        fence=Fence.HOLLOW,
        warrant=Warrant.FOREIGN,
        warrant_text="Наследует FR-807",
        note=(
            "Katakda **uchta** artefakt nomlangan va ular uch xil "
            "holatda. Tuman poligonlari: to'liq — `tools/import_boundaries.py` "
            "ularni yuklaydi, `geo.quality` oltita tekshiruv beradi. "
            "Mahalla poligonlari: `mahallas` jadvali bor, unga "
            "**yozadigan yo'l yo'q** — butun `app/`+`tools/`+`alembic/` "
            "da `INSERT INTO` faqat `districts` va `boundary_staging` "
            "ga boradi (83-run), `import_boundaries.py` da `mahalla` "
            "so'zi bir marta ham uchramaydi (82-run, `EX-2`). Qamrov "
            "zonasi: `coverage_zones` jadvali umuman yo'q — u BRD ning "
            "`IS-08` In Scope qatorida turibdi va bugungi eng yaqin "
            "narsa `regions.bbox`, ya'ni to'rtburchak, poligon emas."
        ),
        binds=(
            "app.geo.registry:active_regions",
            "app.geo.bbox:contains",
        ),
        gap=(
            "Uchtadan bittasi qurilgan. Qatorni «bajarildi» deb o'qish "
            "eng oson joyi shu: mintaqa **haqiqatan** konfiguratsiya "
            "bilan aktivlashadi (`tools/region_admin.py`), lekin "
            "aktivlashish uchun kerak bo'lgan uchta spravochnikdan "
            "faqat bittasi to'ladi."
        ),
    ),
    ScopeItem(
        code="S-2",
        claim="Узбекский язык по умолчанию для региона",
        standing=Standing.IN,
        presence=Presence.DISPLACED,
        fence=Fence.HELD,
        warrant=Warrant.ANCHORED,
        warrant_text="PG-S3",
        warrant_phase="Ph.0",
        note=(
            "Natija to'g'ri — foydalanuvchi o'zbekchani oladi — lekin "
            "qator nomlagan mexanizm orqali emas. «Для региона» "
            "mexanizmi bor va relizsiz o'zgaradi "
            "(`regions.default_language` ↔ `region_admin update --lang` "
            "↔ `i18n.pick_language`, 28-run), botda esa u "
            "**chaqirilmaydi**: `/start` da koordinata yo'q, ya'ni "
            "mintaqa ham yo'q, va `get_or_create_user` modul "
            'konstantasi `DEFAULT_LANGUAGE = "uz"` ga tushadi '
            "(75-run, `RS-08`)."
        ),
        binds=(
            "app.core.i18n:DEFAULT_LANGUAGE",
            "app.geo.registry:language_for",
        ),
        gap=(
            "Ikkinchi mintaqa boshqa til bilan qo'shilgan kunda qator "
            "jimgina yolg'onga aylanadi: konfiguratsiya o'zgaradi, bot "
            "esa baribir `uz` beradi."
        ),
    ),
    ScopeItem(
        code="S-3",
        claim="Приём репортов с геолокацией, кластеризация, карта",
        standing=Standing.IN,
        presence=Presence.BUILT,
        fence=Fence.HELD,
        warrant=Warrant.PROSE,
        warrant_text="Ядро продукта",
        note=(
            "Uchala bo'lak ham qurilgan va bog'langan: `app/bot/` → "
            "`app/reports/intake.py` → `app/clustering/` → "
            "`app/api/v1/map.py` + `web/`. Yagona ochiq uchi — botning "
            "haqiqiy Telegram runi (E3-a), ya'ni kod emas, token."
        ),
        binds=(
            "app.bot.service:submit_report",
            "app.clustering.service:assign",
            "app.api.v1.map:get_map",
        ),
    ),
    ScopeItem(
        code="S-4",
        claim="Трёхуровневая привязка: район → махалля → H3",
        standing=Standing.IN,
        presence=Presence.UNREACHABLE,
        fence=Fence.HOLLOW,
        warrant=Warrant.ANCHORED,
        warrant_text="§17",
        note=(
            "Uchala daraja ham kodda bor va o'rtadagisi hech qachon "
            "to'lmaydi: `find_mahalla_id` `None` qaytaradi, chunki "
            "`mahallas` bo'sh (`S-1`). Degradatsiya **xatosiz** "
            "ishlaydi (`FR-S-802`), ya'ni uch daraja amalda ikkitaga "
            "aylanadi va buni hech narsa ko'rsatmaydi — `mahalla_id` "
            "shunchaki `NULL` bo'lib qoladi."
        ),
        binds=(
            "app.geo.pipeline:find_mahalla_id",
            "app.geo.h3_cells:cell_of",
        ),
        gap=(
            "75-run topgan zid katak shu qatorga tegishli: `FR-S-802` "
            "bir vaqtda maxsus xato kodini **va** «привязка "
            "выполняется без ошибки» ni talab qiladi. Repo ikkinchisini "
            "bajaradi; xato kodi ataylab yo'q va uning yo'qligini "
            "`test_risk_register_contract` qulflaydi — shuning uchun bu "
            "yerda uning nomi **yozilmaydi** ham."
        ),
    ),
    ScopeItem(
        code="S-5",
        claim="Coverage Index на уровне махалли с дисклеймером",
        standing=Standing.IN,
        presence=Presence.UNREACHABLE,
        fence=Fence.HOLLOW,
        warrant=Warrant.ANCHORED,
        warrant_text="PG-S4",
        warrant_phase="Ph.1",
        note=(
            "Katakning **ikkinchi** yarmi to'liq bajarilgan: dislaymer "
            "majburiy va statistika javoblari usiz chiqmaydi "
            "(`stats.methodology`, 83-run `C-11` ni tasdiqladi). "
            "Birinchi yarmi esa `S-1` ga tayanadi: `mahalla_index` "
            "qurilgan, `summarize` pog'onalarni sanaydi va `missing()` "
            "bugun har doim qaytadi — ya'ni javob rost, faqat u har "
            "doim «o'lchanmagan»."
        ),
        binds=(
            "app.stats.service:mahalla_index",
            "app.stats.mahalla_coverage:missing",
            "app.stats.methodology:SECTION_KEYS",
        ),
        gap=(
            "`PG-S4` ning o'lchagichi «100% витрин с индексом покрытия» "
            "— u bugun **bajarilgan**, chunki indeks har vitrinada bor. "
            "Ya'ni maqsad ham, qator ham «ha» deydi, ko'rsatiladigan "
            "son esa yo'q."
        ),
    ),
    ScopeItem(
        code="S-6",
        claim="Подписка на адрес и уведомления",
        standing=Standing.IN,
        presence=Presence.BUILT,
        fence=Fence.HELD,
        warrant=Warrant.MISDATED,
        warrant_text="PG-S2",
        warrant_phase="Ph.2",
        note=(
            "Kod to'liq: obuna `0007`, `app/notifications/` outbox va "
            "renderi bilan, bildirishnoma matni ikki tilda. Ochiq uchi "
            "`S-3` bilan bir xil — Telegram runi. Asos esa ikki "
            "tomondan noto'g'ri: `PG-S2` ning gorizonti **Ph.2**, MVP "
            "esa Ph.0 + Ph.1, ya'ni qator o'zidan keyingi maqsadga "
            "tayanadi; ustiga `PG-S2` ning mazmuni obuna haqida emas, "
            "xaritaning **donadorligi** haqida («Карта осмысленна на "
            "уровне махалли»)."
        ),
        binds=(
            "app.notifications.outbox:publish",
            "app.notifications.render:render",
        ),
        gap=(
            "Obuna radiusining standarti hali Toshkentniki (500 m) — "
            "mintaqaviy qiymat E11 ga qoldirilgan."
        ),
    ),
    ScopeItem(
        code="S-7",
        claim=("Ручной разбор публикаций регионального источника 1055 (если он существует)"),
        standing=Standing.IN,
        presence=Presence.UNREACHABLE,
        fence=Fence.HOLLOW,
        warrant=Warrant.ANCHORED,
        warrant_text="P0-1",
        note=(
            "«Qo'lda razbor» ning natijasi qayerga tushishi kerakligi "
            "yozilgan: `official` manbasi `06` §2 da bor, `0003` uni "
            "seed qiladi, `is_authoritative=True` va `06` §2.2 unga "
            "alohida qoida beradi (og'irlik `0.0`, hodisa darhol "
            "`confirmed`, `layer='official'`). Yetishmayotgani — "
            "**kirish nuqtasi**: `create_report` ning `source_code` "
            "argumentini repoda birorta chaqiruvchi bermaydi va "
            "`app/api/v1/admin.py` da xabar kiritadigan endpoint yo'q. "
            "Ya'ni Faza 0 ning birinchi vazifasi bugun bajarilmaydi."
        ),
        binds=(
            "app.reports.sources:SOURCES",
            "app.reports.intake:create_report",
        ),
        gap=(
            "Bu `AS-IS` emas, **jim** holat: moderator hodisani "
            "tasdiqlay olmaydi (`05` §4.4) va rasmiy xabarni ham "
            "kirita olmaydi, ya'ni ikkala qo'l yo'li ham yopiq."
        ),
    ),
    ScopeItem(
        code="S-8",
        claim="Партнёрская схема с махаллинскими чатами для холодного старта",
        standing=Standing.IN,
        presence=Presence.EXTERNAL,
        fence=Fence.UNWITNESSED,
        warrant=Warrant.PROSE,
        warrant_text="Митигация риска пустой карты",
        note=(
            "Kelishuv ishi; repo unga na dalil, na qorovul bera oladi. "
            "Yagona bilvosita iz — `mahalla_active` manbasi "
            "(og'irlik `2.0`, «Tasdiqlangan mahalla aktivi»), va u ham "
            "`S-7` bilan bir xil sababdan tanlanmaydi."
        ),
        binds=("app.reports.sources:SOURCES",),
    ),
    # ---- Future Release --------------------------------------------------
    ScopeItem(
        code="F-1",
        claim="Автоматический парсинг регионального канала 1055",
        standing=Standing.LATER,
        presence=Presence.ABSENT,
        fence=Fence.HELD,
        warrant=Warrant.NONE,
        note=(
            "E18; repoda parser ham, uni chaqiradigan fon vazifasi ham "
            "yo'q (`app/jobs/` registri to'liq va unda bunday vazifa "
            "yo'q). Chegara ushlab turilibdi."
        ),
    ),
    ScopeItem(
        code="F-2",
        claim="статистика по махаллям с исторической глубиной",
        standing=Standing.LATER,
        presence=Presence.ABSENT,
        fence=Fence.HELD,
        warrant=Warrant.NONE,
        note=(
            "Mahalla kesimi bor (`S-5`), lekin **tarixsiz**: "
            "`mahalla_index` faqat `now` ni oladi va oynani "
            "`coverage_window_days` dan quradi — chaqiruvchi `from`/`to` "
            "bera olmaydi, holbuki tuman kesimi uchun bunday oyna bor "
            "(`stats_max_period_days = 366`). Ya'ni «tarixiy chuqurlik» "
            "aynan mahalla darajasida ataylab yo'q va chegara shu "
            "asimmetriya bilan ushlab turilibdi."
        ),
        binds=("app.stats.service:mahalla_index",),
    ),
    ScopeItem(
        code="F-3",
        claim="прогноз",
        standing=Standing.LATER,
        presence=Presence.ABSENT,
        fence=Fence.HELD,
        warrant=Warrant.NONE,
        note=(
            "Repoda bashorat qiluvchi hech narsa yo'q. Eng yaqin son — "
            "`DurationCut.median_min`/`p90_min`, va u **kuzatilgan** "
            "o'tmish; `01` §4 uni «не применимо как target» deb "
            "belgilaydi (84-run)."
        ),
    ),
    ScopeItem(
        code="F-4",
        claim="официальная интеграция с региональным оператором",
        standing=Standing.LATER,
        presence=Presence.UNREACHABLE,
        fence=Fence.HELD,
        warrant=Warrant.NONE,
        note=(
            "Qator **allaqachon bazada**: `operator_api` `SOURCES` da "
            "bor, `0003` uni seed qiladi va `is_authoritative=True`, "
            "ya'ni uning birinchi xabari hodisani darhol tasdiqlagan "
            "bo'lardi. Chegara buzilmaydi, chunki `S-7` ning kirish "
            "nuqtasi yo'q — ya'ni «keyinroq» ni ushlab turgan narsa "
            "reja emas, **bo'shliq**."
        ),
        binds=("app.reports.sources:SOURCES",),
        gap=(
            "Bu `PROGRESS.md` ning ochiq savolini (`official`/"
            "`operator_api` seedi tasdiqlanmagan holda "
            "`is_authoritative=True`) boshqa tomondan tasdiqlaydi: "
            "seed bugun zararsiz, va u zararsiz bo'lib qolishi "
            "mexanizmga emas, yo'qlikka tayanadi."
        ),
    ),
    ScopeItem(
        code="F-5",
        claim="распространение на другие города области",
        standing=Standing.LATER,
        presence=Presence.BUILT,
        fence=Fence.CROSSED,
        warrant=Warrant.NONE,
        note=(
            "Ko'plik qurilgan: `active_regions` **tuple** qaytaradi, "
            "`pick_for_point` ular orasidan tanlaydi, `for_point` "
            "koordinata bo'yicha dispetcherlik qiladi, "
            "`tools/region_admin.py` `N`-mintaqani qo'sha oladi, "
            "`GET /regions` ro'yxat beradi. Bitta mintaqali mahsulotga "
            "bularning birortasi kerak emas edi. §7 ning MVP qatori "
            "(`S-1`) faqat **birlikni** ruxsat beradi, `03` §3 esa "
            "ko'plikni `R3.0` ga qo'yadi."
        ),
        binds=(
            "app.geo.registry:active_regions",
            "app.geo.registry:pick_for_point",
            "app.api.v1.regions:get_regions",
        ),
        gap=(
            "Ikkinchi mintaqa hali import qilinmagan (E19 ning "
            "to'sig'i), ya'ni tashqi qarashda chegara buzilmagan "
            "ko'rinadi — qurilgani ma'lumot emas, **mexanizm**."
        ),
    ),
    # ---- Out of Scope ----------------------------------------------------
    ScopeItem(
        code="O-1",
        claim="Нативные мобильные приложения",
        standing=Standing.OUT,
        presence=Presence.ABSENT,
        fence=Fence.HELD,
        warrant=Warrant.NONE,
        note=(
            "Veb sirti statik build (`web/`, React + MapLibre), E20 "
            "esa PWA — bu qator emas. Repoda mobil platforma kodi yo'q."
        ),
    ),
    ScopeItem(
        code="O-2",
        claim="монетизация в любой форме",
        standing=Standing.OUT,
        presence=Presence.ABSENT,
        fence=Fence.HELD,
        warrant=Warrant.NONE,
        note=(
            "To'lov, tarif, hisob yoki reklama bilan bog'liq hech narsa "
            "yo'q. `01` §4 ning ikkinchi jadvali buni matn bilan ham "
            "takrorlaydi (84-run, `COMMERCIAL_PHRASE`)."
        ),
    ),
    ScopeItem(
        code="O-3",
        claim="официальный статус источника",
        standing=Standing.OUT,
        presence=Presence.ABSENT,
        fence=Fence.HELD,
        warrant=Warrant.NONE,
        note=(
            "Mahsulot o'zini rasmiy deb e'lon qilmaydi va buni ikkita "
            "narsa ta'minlaydi: dislaymer mexanizmi "
            "(`stats.methodology`) va — kuchliroq — `layer='official'` "
            "ga olib boradigan yo'lning yo'qligi (`S-7`). Ikkinchisi "
            "**reja emas**, va u yopilgan kunda bu qatorning qorovuli "
            "faqat dislaymer bo'lib qoladi."
        ),
        binds=(
            "app.stats.methodology:SECTION_KEYS",
            "app.reports.sources:SOURCES",
        ),
    ),
    ScopeItem(
        code="O-4",
        claim="SMS-канал (стоимость несовместима с некоммерческой моделью)",
        standing=Standing.OUT,
        presence=Presence.ABSENT,
        fence=Fence.HELD,
        warrant=Warrant.NONE,
        note=(
            "SMS yuboradigan kod yo'q. ⚠️ Qorovul esa **o'zga**: "
            "74-run topganidek, kanalni to'sib turgan narsa "
            "`app.admin.security:USERS_ALLOWED_COLUMNS` oq ro'yxati, "
            "u esa `01` §20 ning ПДн pozitsiyasi uchun yozilgan. "
            "Katakdagi sabab — narx, va narx haqida repoda hech narsa "
            "yo'q: bepul shlyuz topilsa, chegarani ushlab turadigan "
            "yagona narsa boshqa bo'lim uchun yozilgan ro'yxat bo'lardi."
        ),
        binds=("app.admin.security:USERS_ALLOWED_COLUMNS",),
    ),
    ScopeItem(
        code="O-5",
        claim="гарантии времени восстановления",
        standing=Standing.OUT,
        presence=Presence.ABSENT,
        fence=Fence.HELD,
        warrant=Warrant.NONE,
        note=(
            "Tiklanish vaqtini va'da qiladigan maydon ham, hisob ham "
            "yo'q; `outages` da faqat `autoclose_after` bor va u "
            "jimlikdan keyin yopish qoidasi, bashorat emas. "
            "⚠️ Chegara ushlab turilibdi, lekin uning **ruxsat "
            "etilgan yarmi ham** qurilmagan: `01` §3 ning User Goals i "
            "«понять, когда ориентировочно вернётся свет» deb yozadi, "
            "ya'ni taxminni **maqsad** qilib qo'yadi. Repo ikkalasini "
            "ham bermaydi va §7 buni bo'shliq deb ko'rsatmaydi."
        ),
    ),
)


@dataclass(frozen=True)
class UnlistedSurface:
    """§7 ning uchala ro'yxatida ham yo'q, repoda esa qurilgan sirt."""

    code: str
    surface: str
    note: str
    binds: tuple[str, ...]


UNLISTED: tuple[UnlistedSurface, ...] = (
    UnlistedSurface(
        code="U-1",
        surface="Ommaviy API (`/api/v1`, OpenAPI)",
        note=(
            "E15 ✅. §7 uni na kiritadi, na keyinga qoldiradi, na rad "
            "etadi. **To'rtinchi** hujjat: 77-run `01` §25 da, 82-run "
            "`01` §24 da, 84-run `01` §4 da o'sha bo'shliqni topgan. "
            "`01` §16 ommaviy API ga **talab** qo'yadi, ya'ni paket "
            "undan ko'lamsiz talab qiladi."
        ),
        binds=("app.api.v1.outages:get_outage", "app.api.v1.stats:get_stats"),
    ),
    UnlistedSurface(
        code="U-2",
        surface="Moderatsiya va ma'muriy panel",
        note=(
            "E8 🔄. §7 da yo'q; 77-run uni `01` §25 da ham topmagan. "
            "Rollar, audit va moderatsiya qurilgan va ular mahsulotning "
            "alohida sirti — `S-3` ning «ядро» si ularni qamramaydi."
        ),
        binds=("app.api.v1.admin:reject_outage", "app.admin.audit:record"),
    ),
    UnlistedSurface(
        code="U-3",
        surface="H3 issiqlik xaritasi (`/heatmap`)",
        note=(
            "E16 🔄. `S-4` H3 ni **biriktirish darajasi** sifatida "
            "nomlaydi, sirt sifatida emas: issiqlik xaritasi alohida "
            "endpoint, alohida keshi va alohida `ETag` i bilan."
        ),
        binds=("app.stats.heatmap:build", "app.api.v1.heatmap:get_heatmap"),
    ),
)


# --------------------------------------------------------------------------
# Reyestrning ichki tekshiruvi — import paytida
# --------------------------------------------------------------------------


def _check_registry() -> None:
    codes = [item.code for item in ITEMS]
    if len(set(codes)) != len(codes):
        raise ScopeError("kodlar takrorlangan")

    for item in ITEMS:
        if item.standing is Standing.IN:
            if not item.warrant_text:
                raise ScopeError(f"{item.code}: MVP qatori asossiz")
            if item.warrant is Warrant.NONE:
                raise ScopeError(f"{item.code}: MVP qatorida ustun bor")
        else:
            if item.warrant is not Warrant.NONE:
                raise ScopeError(f"{item.code}: ro'yxatda «Обоснование» ustuni yo'q")
            if item.warrant_text:
                raise ScopeError(f"{item.code}: ro'yxat qatorida asos matni")

        if item.warrant_phase and item.warrant not in {
            Warrant.ANCHORED,
            Warrant.MISDATED,
        }:
            raise ScopeError(f"{item.code}: gorizont faqat yechilgan havolada")
        if item.warrant_phase and item.warrant_phase not in PHASE_ORDER:
            raise ScopeError(f"{item.code}: noma'lum gorizont {item.warrant_phase}")

        if item.presence is Presence.ABSENT and item.binds and item.fence is Fence.HOLLOW:
            raise ScopeError(f"{item.code}: yo'q narsaning dalili bo'lmaydi")
        if item.presence is not Presence.ABSENT and not item.binds:
            raise ScopeError(f"{item.code}: dalilsiz")
        if not item.note:
            raise ScopeError(f"{item.code}: izohsiz")

    # `MISDATED` — hisoblanadigan hukm, e'lon emas: gorizont MVP dan
    # keyin bo'lishi shart va aksincha.
    for item in ITEMS:
        if not item.warrant_phase:
            continue
        later = PHASE_ORDER.index(item.warrant_phase) > PHASE_ORDER.index(MVP_PHASES[-1])
        if later != (item.warrant is Warrant.MISDATED):
            raise ScopeError(f"{item.code}: gorizont va hukm zid")

    unlisted_codes = [u.code for u in UNLISTED]
    if len(set(unlisted_codes)) != len(unlisted_codes):
        raise ScopeError("teskari yo'nalish kodlari takrorlangan")
    for entry in UNLISTED:
        if not entry.binds:
            raise ScopeError(f"{entry.code}: dalilsiz")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ScopeReport:
    """`01` §7 ning bugungi holati."""

    items: tuple[ScopeItem, ...]
    unlisted: tuple[UnlistedSurface, ...]

    @property
    def by_standing(self) -> dict[Standing, tuple[str, ...]]:
        result: dict[Standing, list[str]] = {s: [] for s in Standing}
        for item in self.items:
            result[item.standing].append(item.code)
        return {s: tuple(codes) for s, codes in result.items()}

    @property
    def by_presence(self) -> dict[Presence, tuple[str, ...]]:
        result: dict[Presence, list[str]] = {p: [] for p in Presence}
        for item in self.items:
            result[item.presence].append(item.code)
        return {p: tuple(codes) for p, codes in result.items()}

    @property
    def by_fence(self) -> dict[Fence, tuple[str, ...]]:
        result: dict[Fence, list[str]] = {f: [] for f in Fence}
        for item in self.items:
            result[item.fence].append(item.code)
        return {f: tuple(codes) for f, codes in result.items()}

    @property
    def by_warrant(self) -> dict[Warrant, tuple[str, ...]]:
        result: dict[Warrant, list[str]] = {w: [] for w in Warrant}
        for item in self.items:
            result[item.warrant].append(item.code)
        return {w: tuple(codes) for w, codes in result.items()}

    @property
    def crossed(self) -> tuple[ScopeItem, ...]:
        """«Keyinroq» yoki «kirmaydi» deb yozilgan, repoda esa bor."""
        return tuple(i for i in self.items if i.fence is Fence.CROSSED)

    @property
    def hollow(self) -> tuple[ScopeItem, ...]:
        """«Kiradi» deb yozilgan, repoda esa to'liq emas."""
        return tuple(i for i in self.items if i.fence is Fence.HOLLOW)

    @property
    def unsound_warrants(self) -> tuple[ScopeItem, ...]:
        """Asosi vaqt yoki manzil bo'yicha ishlamaydigan qatorlar."""
        return tuple(i for i in self.items if i.warrant not in WARRANT_SOUND)

    @property
    def blocked_by_missing_source_path(self) -> tuple[ScopeItem, ...]:
        """Bitta yo'q mexanizm hal qiladigan qatorlar.

        Bosh topilma **hisoblanadi**, e'lon qilinmaydi: dalili
        `app.reports.sources:SOURCES` bo'lgan har bir qator shu yerga
        tushadi va ular uchala ro'yxatda ham bor. Ro'yxat bo'shashi
        uchun `source_code` ni beradigan birinchi chaqiruvchi yozilishi
        kerak.
        """
        return tuple(i for i in self.items if "app.reports.sources:SOURCES" in i.binds)

    @property
    def standings_touched(self) -> frozenset[Standing]:
        """Yuqoridagi ro'yxat nechta ro'yxatga tegadi."""
        return frozenset(i.standing for i in self.blocked_by_missing_source_path)

    @property
    def boundaries_hold(self) -> bool:
        """Chegara ikkala tomondan ham rostmi.

        Hisobotning bosh xossasi. Bugun `False` va ikkala tomondan ham:
        to'rtta `HOLLOW` (ichkarida qurilmagan) va bitta `CROSSED`
        (tashqarida qurilgan).
        """
        return not self.crossed and not self.hollow

    @property
    def accurate(self) -> bool:
        """§7 bugungi haqiqatni to'g'ri tasvirlaydimi.

        Uchta shart, uchtasi ham mustaqil: chegara ikkala tomondan
        ushlansin; MVP qatorining asosi ishlasin; repo qurgan sirt
        uchala ro'yxatda ham nomsiz qolmasin.
        """
        return self.boundaries_hold and not self.unsound_warrants and not self.unlisted


def evaluate() -> ScopeReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi
    (`glossary.evaluate`, `roadmap.evaluate`, `success.evaluate` bilan
    bir xil sabab).
    """
    return ScopeReport(items=ITEMS, unlisted=UNLISTED)

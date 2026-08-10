"""Xavfsizlik kafolatlarining reyestri (`01` §20 + BRD «Безопасность» NFR lari).

**Nima uchun bu modul bor.** `01` §20 butun bo'limni bitta jumla bilan
yopadi: «Наследуется полностью: RBAC, MFA для админ-ролей, шифрование,
аудит, политика сессий и паролей, разделение `geom_exact` /
`geom_public`, право `outage.read_exact_geo`» — va ustiga beshta qatorli
jadval. Shu paytgacha bu ro'yxat hech qayerda o'qilmagan.

Fe'lning o'zi tuzoq. «Наследуется» — bu **kelib chiqish**, holat emas.
Toshkent paketidan meros olingan kafolat bu repoda avtomatik ishlamaydi:
bu yerda fork emas, noldan yozilgan kod. Ya'ni «meros» so'zi amalda
«qaytadan bajarilishi kerak» degani, va bo'limni «hammasi bor» deb
o'qish — eng arzon xato.

## Asosiy ajratma: bajarilgan ≠ himoyalangan

Bu modulning o'zagi — `ENFORCED` va `UNDEFENDED` orasidagi farq.

Xavfsizlik kafolati mahsulot xususiyatidan shunisi bilan farq qiladi:
u **buzilganda hech narsa yiqilmaydi**. `05` §3 haqida 60-run aytgan
gap butun §20 ga tegishli. Shundan kelib chiqadigan ikkinchi darajali,
lekin xavfliroq holat: kafolat **bugun rost**, chunki uni buzadigan kod
hali yozilmagan — lekin uni rost saqlab turadigan hech narsa yo'q.

Eng aniq misoli — «ПДн не собираются: ни ФИО, ни телефон, ни username».
Bugun rost: `users` da `tg_id`, `language`, `region_id`, `trust_score`,
`is_blocked`, `created_at` dan boshqa ustun yo'q. Lekin bu kafolatni
hech bir test o'lchamasdi, ya'ni `username` ustunini qo'shadigan bitta
migratsiya uni jimgina yolg'onga aylantirardi va butun to'plam yashil
qolardi. Tasodifan bajarilgan kafolat bitta commit narida.

Shuning uchun `ENFORCED` **ikkita** shartni talab qiladi: mexanizm kodda
bor **va** uni olib tashlaganda yiqiladigan test bor. Bittasi bo'lsa —
`UNDEFENDED`, va bu hisobotda alohida ko'rinadi.

## Ikkinchi ajratma: kafolat ≠ hujjat atagan mexanizm

`Mechanism` o'qi `Posture` ni takrorlamaydi. Hujjat ko'p joyda **nomni**
aytadi (`outage.read_exact_geo`, MFA, «политика паролей»), kafolat esa
boshqa mexanizm bilan ta'minlangan bo'lishi mumkin — va bu yomon emas,
lekin **ko'rinishi shart**.

`read_exact_geo` aynan shunday. Kafolat («aniq koordinatani faqat
huquqi bor odam ko'radi») bugun **kuchliroq** mexanizm bilan bajarilgan:
`05` §7.3 bo'yicha `geom_exact` **hech qanday** endpointdan chiqmaydi,
ya'ni uni hech kim ko'rmaydi. Reyestrda `SUBSTITUTED` turadi, va bu
qatorning izohi ogohlantirish: hujjat atagan `Permission` ni qo'shish
qatorni `AS_WRITTEN` ga ko'chiradi va **eshik ochadi** — gate siz ruxsat
xavfsizlikni oshirmaydi, faqat hisobotni yashillaydi. 70-run ning
`restated_count` bilan bir sinf.

## Uchinchi holat: `MISSTATED`

Bir kafolat yozilganidek **umuman bajarilishi mumkin emas**, va bu
`ABSENT` dan boshqa narsa. §20 «идентификатор Telegram хранится в
псевдонимизированном виде» deydi. `users.tg_id` esa xom `bigint`.
Uni bir tomonlama xeshlab bo'lmaydi, chunki u faqat identifikator emas,
**yetkazish manzili**: `app.notifications.service` xabarni
`sender.send(chat_id=item.tg_id, ...)` bilan yuboradi. Telegram orqali
ishlaydigan mahsulot Telegram identifikatorini pseudonimlashtira
olmaydi — aks holda foydalanuvchiga javob qaytara olmaydi.

Kod bu farqni **biladi**: `app.admin.auth.Actor.id` haqiqatan
pseudonim (`uuid5(ACTOR_NAMESPACE, name)`), ya'ni «псевдонимизированный
вид» bu repoda ma'noga ega. Shuning uchun §20 ning da'vosi shunchaki
bajarilmagan emas — u **noto'g'ri yozilgan**, va o'rnida amalda
bajariladigan torroq kafolat bor: identifikator tizimdan chiqmaydi
(`05` §7.3). `narrower` maydoni aynan shuni yozadi.

## Modul chegarasi

Modul **toza**: bazaga ham, `settings` ga ham, FastAPI ga ham murojaat
qilmaydi. U hech nimani o'lchamaydi va hech nimani majburlamaydi —
faqat kafolatlarning holatini **nomlaydi**. O'lchash kontrakt testining
ishi (`tests/test_security_posture_contract.py`), majburlash esa
qatorlarda ko'rsatilgan `lock` fayllariniki.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Bu ro'yxatning hujjatdagi manzili.
SPEC = "01 §20"

#: §20 «Геоданные» qatoridagi son: «в малой махалле точность **50 м**
#: может указывать на конкретный дом». Kontrakt testi uni hujjatdan
#: parse qilib solishtiradi va ommaviy aniqlik shundan **qo'polroq**
#: ekanini tekshiradi (r9 ning qirrasi ≈ 174 m hujjat bo'yicha, `h3`
#: 4.5.0 bo'yicha esa 200.8 m — 60-run ning ochiq savoli).
DOC_MAHALLA_PRECISION_M = 50

#: `users` da ruxsat etilgan ustunlar. §20 ning «ПДн не собираются»
#: qatori shu ro'yxat bilan qulflanadi: yangi ustun qo'shilsa test
#: yiqiladi va uni **ataylab** shu yerga yozish kerak bo'ladi.
#: Ro'yxat oq (allowlist), qora emas — `username` ni taqiqlash
#: `user_name` ni o'tkazib yuborardi.
USERS_ALLOWED_COLUMNS: frozenset[str] = frozenset(
    {
        "id",
        "tg_id",
        "language",
        "region_id",
        "trust_score",
        "is_blocked",
        "created_at",
    }
)

#: §20 sanaydigan ПДн turlari va ularni ifodalaydigan ustun nomlari.
#: Reyestr ustun **qo'shilishini** taqiqlamaydi (buni allowlist qiladi),
#: bu ro'yxat esa xatoni **o'qiladigan** qiladi: qaysi ПДн kirib keldi.
PDN_COLUMN_HINTS: dict[str, tuple[str, ...]] = {
    "ФИО": ("name", "first_name", "last_name", "full_name", "fio", "patronymic"),
    "телефон": ("phone", "msisdn", "tel", "mobile"),
    "username": ("username", "user_name", "handle", "nickname", "login"),
}


class Posture(StrEnum):
    """Kafolatning holati.

    Tartib **tasodifiy emas**: yuqoridan pastga — «ishonsa bo'ladi» dan
    «ishonib bo'lmaydi» ga.
    """

    #: Mexanizm kodda bor **va** uni olib tashlaganda yiqiladigan test
    #: bor. Faqat shu holat kafolat deb hisoblanadi.
    ENFORCED = "enforced"
    #: Bugun rost, lekin rost saqlab turadigan hech narsa yo'q.
    #: Modulning asosiy topilmasi — yuqoridagi izohga qarang.
    UNDEFENDED = "undefended"
    #: Shart-sharoitning o'zi yo'q, ya'ni buzish uchun narsa yo'q
    #: (parol siyosati — parol yo'q joyda). **Xavfsiz degani emas:**
    #: o'rnini bosgan xossa boshqa nom ostida turadi.
    VACUOUS = "vacuous"
    #: Hujjat talab qiladi, bajarish mumkin, kodda yo'q. Xavf tirik.
    ABSENT = "absent"
    #: Yozilganidek bajarilishi **mumkin emas**; o'rnida torroq kafolat
    #: bajariladi (`narrower`). Bu — hujjatning defekti, kodning emas.
    MISSTATED = "misstated"
    #: Mahsulot kodidan tashqarida: infratuzilma yoki huquq.
    #: Bo'shliq deb sanalmaydi (67-run ning `EXTERNAL` sababi).
    EXTERNAL = "external"


class Mechanism(StrEnum):
    """Hujjat atagan mexanizm bilan koddagi mexanizmning munosabati."""

    #: Hujjatdagi nom kodda o'sha nom bilan bor.
    AS_WRITTEN = "as_written"
    #: Kafolat bor, lekin **boshqa** mexanizm bilan. Yashil ko'rinadi va
    #: hujjatdagi nomni «tiklash» taklifini chaqiradi — izoh shuning
    #: uchun majburiy.
    SUBSTITUTED = "substituted"
    #: Hujjat nomni aytadi, kodda o'sha nom ham, o'rnini bosuvchi ham yo'q.
    NAMED_ONLY = "named_only"
    #: Hujjat kafolatni aytadi, mexanizmni atamaydi.
    UNNAMED = "unnamed"


@dataclass(frozen=True)
class Guarantee:
    """`01` §20 ning bitta kafolati.

    Har qator hujjatga **langar** bilan bog'lanadi va langar ikki xil:

    * `doc_item` — `01` §20 dagi matn: nasrdagi ro'yxat elementi yoki
      jadval qatorining birinchi ustuni. Jadvalning ikkita katagi
      `;` bilan ikkita **mustaqil** da'voni bir qatorga qo'ygan
      (ПДн, Геоданные — GDPR ham), shuning uchun `claim` o'sha
      da'voning tartib raqami;
    * `nfr` — BRD ning «Безопасность» NFR identifikatori. §20
      «наследуется полностью» deydi, ya'ni o'sha NFR lar ham shu
      bo'limning bir qismi, lekin ular §20 matnida ko'rinmaydi.

    Qatorda kamida bitta langar bo'lishi shart. Kontrakt testi reyestrni
    hujjat bilan aynan shular orqali bog'laydi — bu yerda qo'lda
    ko'chirilgan ro'yxat yo'q (61-run sabog'i).

    `lock` — kafolat olib tashlanganda **yiqiladigan** test. Bo'sh bo'lsa
    kafolat himoyalanmagan, va `Posture.ENFORCED` taqiqlanadi.
    """

    code: str
    #: Hujjatdagi manzil, o'qish uchun: `01 §20`, `BRD NFR-S-03` va h.k.
    spec: str
    posture: Posture
    mechanism: Mechanism
    #: `01` §20 dagi element matni (nasr elementi yoki jadval yorlig'i).
    doc_item: str = ""
    #: Jadval katagidagi `;` bilan ajratilgan da'voning raqami.
    claim: int = 0
    #: BRD «Безопасность» NFR identifikatori.
    nfr: str = ""
    #: Kodda qayerda: `modul:simvol`. Yo'q bo'lsa — bo'sh.
    where: str = ""
    #: Kafolatni qulflaydigan test fayli. Yo'q bo'lsa — bo'sh.
    lock: str = ""
    #: Nima uchun aynan shu holat. Bir-ikki jumla, majburiy.
    note: str = ""
    #: `MISSTATED` uchun: o'rnida **amalda** bajariladigan kafolat.
    narrower: str = ""


GUARANTEES: tuple[Guarantee, ...] = (
    # ---- §20 nasridagi «наследуется полностью» ro'yxati ----
    Guarantee(
        code="rbac",
        spec="01 §20",
        doc_item="RBAC",
        posture=Posture.ENFORCED,
        mechanism=Mechanism.AS_WRITTEN,
        where="app.admin.roles:PERMISSIONS",
        lock="tests/test_admin_roles.py",
        note=(
            "Uchta rol, o'nta ruxsat, matritsa testda to'liq qulflangan; "
            "noma'lum rol — ruxsat yo'q (xato yopiq tomonga)."
        ),
    ),
    Guarantee(
        code="mfa",
        spec="01 §20 + BRD NFR-S-01",
        doc_item="MFA для админ-ролей",
        nfr="NFR-S-01",
        posture=Posture.ABSENT,
        mechanism=Mechanism.NAMED_ONLY,
        note=(
            "`ADMIN_TOKENS` — bitta omil: sarlavhadagi bearer token. "
            "Ikkinchi omil yo'q va o'rnini bosadigan narsa ham yo'q "
            "(token muddatsiz, qurilma bog'lanmagan, qayta chaqirish "
            "faqat `.env` ni tahrirlash orqali). BRD NFR-S-01 uni "
            "«Обязательно» deb belgilaydi, ya'ni bu ochiq qarz."
        ),
    ),
    Guarantee(
        code="encryption",
        spec="01 §20",
        doc_item="шифрование",
        posture=Posture.EXTERNAL,
        mechanism=Mechanism.UNNAMED,
        note=(
            "Kanal (TLS) va diskdagi shifrlash — joylashtirish qatlami, "
            "mahsulot kodida qarori yo'q. Kod qabul qilgan yagona qaror "
            "qo'shni: sir **saqlanmaydi va loglanmaydi** "
            "(`app.admin.auth` — token bazaga tushmaydi; 56-run — "
            "`DB_ECHO` siz `INSERT` parametrlari jurnalga chiqmaydi)."
        ),
    ),
    Guarantee(
        code="audit",
        spec="01 §20",
        doc_item="аудит",
        posture=Posture.ENFORCED,
        mechanism=Mechanism.AS_WRITTEN,
        where="app.admin.audit:record",
        lock="tests/test_admin_audit.py",
        note=(
            "Har moderator harakati `audit_log` ga `before`/`after` bilan "
            "yoziladi; aktor — `uuid5` pseudonimi, token emas."
        ),
    ),
    Guarantee(
        code="session_password_policy",
        spec="01 §20",
        doc_item="политика сессий и паролей",
        posture=Posture.VACUOUS,
        mechanism=Mechanism.UNNAMED,
        note=(
            "Sessiya ham, parol ham yo'q: autentifikatsiya har so'rovda "
            "holatsiz token bilan. Buzish uchun narsa yo'q. **Lekin bu "
            "xavfsizroq degani emas** — o'rnini bosgan xossalar boshqa "
            "nom ostida turadi (`MIN_TOKEN_LENGTH`, `compare_digest`, "
            "sozlanmagan holat → `403`) va hujjat ularni atamaydi."
        ),
    ),
    Guarantee(
        code="geom_split",
        spec="01 §20",
        doc_item="разделение `geom_exact` / `geom_public`",
        posture=Posture.ENFORCED,
        mechanism=Mechanism.AS_WRITTEN,
        where="app.reports.models:Report",
        lock="tests/test_privacy_jitter_contract.py",
        note=(
            "Ikki ustun ajratilgan, ommaviy nuqta r9 katakchasi va "
            "deterministik siljitishdan quriladi, aniq nuqta 90 kundan "
            "keyin `NULL` ga o'tadi (`tests/test_purge_exact_geom.py`)."
        ),
    ),
    Guarantee(
        code="read_exact_geo",
        spec="01 §20 + BRD NFR-S-02",
        doc_item="право `outage.read_exact_geo`",
        nfr="NFR-S-02",
        posture=Posture.ENFORCED,
        mechanism=Mechanism.SUBSTITUTED,
        where="app.api.v1.outages:OutagePublic",
        lock="tests/test_api_surface_contract.py",
        note=(
            "Hujjat **ruxsatni** ataydi, kod esa kafolatni kuchliroq "
            "mexanizm bilan bajaradi: `05` §7.3 bo'yicha `geom_exact` "
            "hech qanday endpointdan chiqmaydi, ya'ni uni huquqi bori "
            "ham ko'rmaydi. ⚠️ `Permission.OUTAGE_READ_EXACT_GEO` ni "
            "qo'shish qatorni `AS_WRITTEN` ga ko'chiradi va **eshik "
            "ochadi**: gate siz ruxsat xavfsizlikni oshirmaydi, faqat "
            "hisobotni yashillaydi. 👤 `05` §7.3 bilan ziddiyat — "
            "26-run ning ochiq savoli."
        ),
    ),
    # ---- §20 jadvali ----
    Guarantee(
        code="pci_dss",
        spec="01 §20",
        doc_item="PCI DSS",
        posture=Posture.VACUOUS,
        mechanism=Mechanism.UNNAMED,
        note="To'lov yo'q — na endpoint, na model, na bog'liqlik.",
    ),
    Guarantee(
        code="gdpr",
        spec="01 §20",
        doc_item="GDPR",
        claim=0,
        posture=Posture.EXTERNAL,
        mechanism=Mechanism.UNNAMED,
        note=(
            "«Неприменим как основной режим» — huquqiy rejimning tanlovi, "
            "mahsulot kodida qarori yo'q."
        ),
    ),
    Guarantee(
        code="data_localisation",
        spec="01 §20 + 01 NFR-S-04",
        doc_item="GDPR",
        claim=1,
        posture=Posture.EXTERNAL,
        mechanism=Mechanism.UNNAMED,
        note=(
            "Amaldagi huquq — RUz ning ПДн qonunchiligi, saqlash joyiga "
            "talab bilan birga (`01` §15 NFR-S-04 uni takrorlaydi). "
            "Bu joylashtirish qarori: `docker-compose.yml` bazani "
            "qayerda ko'tarishni aytmaydi va aytishi ham kerak emas. "
            "👤 Yuridik tekshiruv o'tkazilmagan — C-09 ochiq."
        ),
    ),
    Guarantee(
        code="iso_27001",
        spec="01 §20",
        doc_item="ISO 27001",
        posture=Posture.EXTERNAL,
        mechanism=Mechanism.UNNAMED,
        note="Hujjatning o'zi «ориентир, не обязательство» deydi.",
    ),
    Guarantee(
        code="pdn_not_collected",
        spec="01 §20",
        doc_item="ПДн",
        claim=0,
        posture=Posture.ENFORCED,
        mechanism=Mechanism.AS_WRITTEN,
        where="app.admin.security:USERS_ALLOWED_COLUMNS",
        lock="tests/test_security_posture_contract.py",
        note=(
            "71-run gacha `UNDEFENDED` edi: da'vo rost edi, lekin uni "
            "o'lchaydigan test yo'q edi — `username` ustunini qo'shadigan "
            "bitta migratsiya butun to'plamni yashil qoldirgan holda uni "
            "yolg'onga aylantirardi. Endi `users` ning ustunlari oq "
            "ro'yxat bilan qulflangan."
        ),
    ),
    Guarantee(
        code="tg_id_pseudonymous",
        spec="01 §20",
        doc_item="ПДн",
        claim=1,
        posture=Posture.MISSTATED,
        mechanism=Mechanism.NAMED_ONLY,
        where="app.reports.models:User.tg_id",
        lock="tests/test_api_surface_contract.py",
        note=(
            "`users.tg_id` — xom `bigint`. Uni bir tomonlama xeshlab "
            "bo'lmaydi, chunki u identifikator **va yetkazish manzili**: "
            "`app.notifications.service` xabarni `send(chat_id=tg_id)` "
            "bilan yuboradi. Telegram orqali ishlaydigan mahsulot "
            "Telegram identifikatorini pseudonimlashtirsa, javob "
            "qaytara olmaydi. Kod farqni biladi — `app.admin.auth` "
            "dagi aktor haqiqatan `uuid5` pseudonimi. 👤 Hujjatni "
            "tahrirlash yoki pepper li xesh ustuni qo'shish — odam qarori."
        ),
        narrower=(
            "Identifikator tizimdan **chiqmaydi**: `05` §7.3 `user_id` va "
            "`tg_id` ni hech qanday javobda taqiqlaydi, analitika "
            "hodisalarida ham yo'q (`app.analytics.catalogue`)."
        ),
    ),
    Guarantee(
        code="geo_grid_snap",
        spec="01 §20",
        doc_item="Геоданные",
        claim=0,
        posture=Posture.ENFORCED,
        mechanism=Mechanism.AS_WRITTEN,
        where="app.geo.jitter:public_point",
        lock="tests/test_privacy_jitter_contract.py",
        note=(
            "Ommaviy nuqta r9 katakchasining markazidan va `blake2b` "
            "bilan hisoblangan doimiy siljitishdan quriladi. Hujjat "
            "riskni **50 m** aniqlikka qarab baholaydi, amaldagi "
            "katakcha esa undan qo'polroq — ya'ni kafolat hujjat "
            "kutganidan kuchli."
        ),
    ),
    Guarantee(
        code="mahalla_reid_check",
        spec="01 §20 (OQ-04)",
        doc_item="Геоданные",
        claim=1,
        posture=Posture.ABSENT,
        mechanism=Mechanism.NAMED_ONLY,
        note=(
            "«Проверка риска реидентификации» mahalla darajasi uchun "
            "o'tkazilmagan va bugun o'tkazib ham bo'lmaydi: mahalla "
            "poligonlari yo'q (E17). Mavjud to'siq bir daraja "
            "yuqorida — `app.stats.heatmap` katakchani `MIN_REPORTERS` "
            "dan kam turli foydalanuvchida yashiradi va `05` §7.3 "
            "uch xabardan kam hodisani ommaviy API dan olib tashlaydi. "
            "👤 OQ-04 ochiq."
        ),
    ),
    # ---- BRD «Безопасность» NFR lari (§20 «наследуется полностью» deydi) ----
    Guarantee(
        code="rate_limit_reports",
        spec="BRD NFR-S-03",
        nfr="NFR-S-03",
        posture=Posture.ENFORCED,
        mechanism=Mechanism.AS_WRITTEN,
        where="app.reports.intake:check_rate_limit",
        lock="tests/test_reports_intake.py",
        note=(
            "`REPORT_RATE_LIMIT_MIN` oynasi, turi bo'yicha "
            "filtrlanmaydi; NFR «Настраивается» deydi va u sozlanadi."
        ),
    ),
    Guarantee(
        code="rate_limit_api",
        spec="BRD NFR-S-03 + 01 §16",
        nfr="NFR-S-03",
        posture=Posture.ABSENT,
        mechanism=Mechanism.NAMED_ONLY,
        note=(
            "NFR «на приём репортов» deydi va o'sha yo'l himoyalangan, "
            "lekin `01` §16 rate limit ni `17_OpenAPI.yaml` dan **butun "
            "`/api/v1` uchun** meros qiladi. Bugun ommaviy API da "
            "cheklagich yo'q; yagona to'siq — `ETag`/`304` va snapshot "
            "keshi, ya'ni narxni kamaytiradi, so'rovlar sonini emas."
        ),
    ),
)

GUARANTEE_BY_CODE: dict[str, Guarantee] = {g.code: g for g in GUARANTEES}


# --------------------------------------------------------------------------
# Reyestrning ichki qoidalari
# --------------------------------------------------------------------------


def registry_errors() -> tuple[str, ...]:
    """Reyestrning o'zi qoidalarga mos keladimi.

    Qoidalar kafolatlarning **ta'rifidan** kelib chiqadi, ya'ni ularni
    buzish holat nomini yolg'onga aylantiradi:

    * `ENFORCED` — mexanizm ham (`where`), qulf ham (`lock`) shart;
      ikkinchisisiz bu `UNDEFENDED`;
    * `UNDEFENDED` — `lock` bo'lmasligi shart (aks holda u `ENFORCED`);
    * `ABSENT` — `where` ham, `lock` ham bo'lmasligi shart;
    * `MISSTATED` — `narrower` shart, aks holda holat «bajarilmagan» dan
      farq qilmaydi;
    * `narrower` faqat `MISSTATED` da;
    * `SUBSTITUTED` va `NAMED_ONLY` — izoh shart va u uzun bo'lishi
      kerak: aynan shu ikki qiymat keyingi o'quvchini «hujjatdagi nomni
      tiklaymiz» degan qarorga chaqiradi;
    * har qatorda izoh va kamida bitta langar bor;
    * `claim` faqat `doc_item` bilan birga ma'noga ega.
    """
    problems: list[str] = []
    for g in GUARANTEES:
        if not g.note.strip():
            problems.append(f"{g.code}: izoh yo'q")
        if not (g.doc_item or g.nfr):
            problems.append(f"{g.code}: langar yo'q — `doc_item` ham, `nfr` ham bo'sh")
        if g.claim and not g.doc_item:
            problems.append(f"{g.code}: `claim` `doc_item` siz ma'nosiz")
        if g.claim < 0:
            problems.append(f"{g.code}: `claim` manfiy")
        if g.posture is Posture.ENFORCED and not (g.where and g.lock):
            problems.append(f"{g.code}: ENFORCED uchun `where` va `lock` shart")
        if g.posture is Posture.UNDEFENDED and g.lock:
            problems.append(f"{g.code}: UNDEFENDED da `lock` bo'lmaydi — u ENFORCED")
        if g.posture is Posture.ABSENT and (g.where or g.lock):
            problems.append(f"{g.code}: ABSENT da `where`/`lock` bo'lmaydi")
        if g.posture is Posture.MISSTATED and not g.narrower.strip():
            problems.append(f"{g.code}: MISSTATED uchun `narrower` shart")
        if g.narrower and g.posture is not Posture.MISSTATED:
            problems.append(f"{g.code}: `narrower` faqat MISSTATED da")
        if g.mechanism in (Mechanism.SUBSTITUTED, Mechanism.NAMED_ONLY) and len(g.note) < 60:
            problems.append(f"{g.code}: {g.mechanism} uchun izoh yetarli emas")
    return tuple(problems)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SecurityReport:
    """§20 ning bugungi holati.

    `trustworthy` — hisobotning yagona ikkilik javobi, va u **ataylab**
    qattiq: bo'limni «meros, ya'ni bor» deb o'qishning oldini olish
    uchun `ABSENT` ham, `UNDEFENDED` ham, `MISSTATED` ham uni
    yiqitadi. `VACUOUS` va `EXTERNAL` yiqitmaydi — birinchisida buzish
    uchun narsa yo'q, ikkinchisi mahsulot kodining ishi emas (67-run).
    """

    guarantees: tuple[Guarantee, ...]
    trustworthy: bool
    #: Holat → nechta qator.
    counts: dict[Posture, int]
    #: E'tibor talab qiladigan qatorlar, o'qish tartibida.
    absent: tuple[str, ...]
    undefended: tuple[str, ...]
    misstated: tuple[str, ...]
    #: Hujjat atagan nomdan boshqa mexanizm bilan bajarilganlari.
    substituted: tuple[str, ...]


def evaluate() -> SecurityReport:
    """Reyestrni hisobotga yig'adi. Hech qanday I/O yo'q."""
    counts = {posture: 0 for posture in Posture}
    for g in GUARANTEES:
        counts[g.posture] += 1
    absent = tuple(g.code for g in GUARANTEES if g.posture is Posture.ABSENT)
    undefended = tuple(g.code for g in GUARANTEES if g.posture is Posture.UNDEFENDED)
    misstated = tuple(g.code for g in GUARANTEES if g.posture is Posture.MISSTATED)
    substituted = tuple(g.code for g in GUARANTEES if g.mechanism is Mechanism.SUBSTITUTED)
    return SecurityReport(
        guarantees=GUARANTEES,
        trustworthy=not (absent or undefended or misstated),
        counts=counts,
        absent=absent,
        undefended=undefended,
        misstated=misstated,
        substituted=substituted,
    )


def pdn_columns_found(columns: frozenset[str] | set[str]) -> dict[str, tuple[str, ...]]:
    """Berilgan ustunlar ichida §20 sanagan ПДн turlarini topadi.

    Oq ro'yxat (`USERS_ALLOWED_COLUMNS`) buzilgan bo'lsa, bu funksiya
    xatoni **o'qiladigan** qiladi: «ortiqcha ustun bor» emas, «telefon
    kirib keldi». Topilmasa bo'sh lug'at — ya'ni ustun ruxsatsiz, lekin
    ПДн emas (masalan `email_hash`), va bu ham xato, faqat boshqa turdagi.
    """
    lowered = {c.lower() for c in columns}
    found: dict[str, tuple[str, ...]] = {}
    for kind, hints in PDN_COLUMN_HINTS.items():
        hit = tuple(sorted(h for h in hints if h in lowered))
        if hit:
            found[kind] = hit
    return found

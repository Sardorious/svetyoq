"""Interfeys reyestri (`BRD` §18–§19) ↔ qurilgan mahsulot.

**Nima uchun bu modul bor.** 103-run BRD §14–§17 ni bog'ladi va §18–§19
ni keyingi nomzod deb qoldirdi. Bu ikki bo'lim — hujjatning **chegara**
sathi: mahsulot qaysi tizimlar bilan (§18, 10 qator) va qaysi odamlar
bilan (§19, 8 rol) gaplashadi. `01` §18 allaqachon kod bilan bog'langan
(`app.integrations.registry`, 73-run) — BRD §18 esa **boshqa** jadval:
qatorlari ko'proq, statuslari boshqa tilda va undan `01` ko'rmagan
ziddiyatlar chiqadi.

## Birinchi topilma: «Open Data API — вне скоупа», repo esa uni qurib bo'lgan

§18 ning oxirgi qatori Open Data API ni (`REST + CSV/GeoJSON`) uchinchi
fazaga suradi: «Ph.3, вне скоупа». Qurilgan mahsulotda esa bu sirt
**to'liq ishlaydi**: ommaviy REST (E15 ✅, `app/api/`), CSV eksport
dislaymeri bilan (`app.stats.export`), GeoJSON `FeatureCollection`
(`app.clustering.snapshot`). Ya'ni hujjat kelajakka surgan narsa —
allaqachon jo'natiladigan haqiqat. Bu `CON-02` bilan bir sinf (repo
hujjat ruxsatidan oldinda), lekin teskari ishorali: bu yerda «qarz» emas,
«ortiqcha» (👤 skoup qayta yoziladimi yoki sirt Ph.3 gacha yashirinadimi).

## Ikkinchi topilma: Kafka/Redis qatorlari `CON-05` savolini **yumshatadi**

§18 Kafka va Redis ni ichki integratsiya sifatida sanaydi — lekin maqomi
`BASELINE-TAS`, ya'ni «Toshkent bazasidan ko'chirilgan bilim», talab
emas. Bu 103-run savoliga (`CON-05`: §15 steki ↔ ADR-05) yangi dalil:
hujjatning o'z belgilash tizimi §18 da bu texnologiyalarni **meros**
deb ataydi, mintaqaviy majburiyat deb emas. §15 ning «не допускается»
jumlasi bilan §18 ning `BASELINE-TAS` belgisi bitta hujjatda ikki xil
ohangda gapiradi — «§15 Toshkent platformasini tasvirlaydi» degan o'qish
endi hujjat ichidan dalil topdi (👤 o'sha savolning davomi, javob emas).

## Uchinchi topilma: §19 sakkiz rol beradi, kod uchtasini biladi

`app.admin.roles` da uchta rol (viewer/moderator/admin) va o'nta ruxsat
bor — §19 esa sakkizta rol sanaydi. Beshtasining kodda umuman izi yo'q:
veb-ro'yxatdan o'tish yo'q (obuna faqat `tg_id` da — `01` §19 In-App
savolining davomi), «Региональный оператор» yo'q (rejalashtirilgan
uzilish importi ham yo'q), «Super Admin» yo'q (validatsiya parametrlari
— `.env`, runtime rol emas). «Куратор территорий» va «Аналитик» esa
rol sifatida emas, **boshqa mexanizm** sifatida yashaydi: birinchisi —
odam yurgizadigan asboblar (`tools/import_boundaries.py`,
`tools/region_admin.py`, versiyalash), ikkinchisi — ochiq vitrina
(eksport va API loginsiz hammaga ochiq, ya'ni «Аналитик» roli talab
qilgan o'qish huquqi hammaniki).

## To'rtinchi topilma: moderator §19 dagi huquqlarining yarmisiz

§19 moderatorga to'rt fe'l beradi: «подтверждение / отклонение /
объединение / разделение». Kodda ikkitasi bor (`outage.reject`,
`outage.merge`) va bloklash. **Tasdiqlash yo'q** — `05` §4.4 bo'yicha
tasdiqlash faqat avtomatik (`03` §11 ning ma'lum ochiq bandi), va
**bo'lish (split) ham yo'q** — `Permission` ro'yxatida ham,
`app.admin.service` da ham. Hujjat rolga mahsulot bermaydigan huquqni
va'da qiladi.

## §19 «Ограничения» — uchala jumla ham tanish qarzlar

2FA «обязательна» — MFA yo'q (`app.admin.security` da `mfa` qatori
`ABSENT`, BRD NFR-S-01 qarzi). `outage.read_exact_geo` — huquq
mavjud emas, o'rnida kuchliroq taqiq (`geom_exact` hech qanday
endpointdan chiqmaydi — o'sha reyestrda `SUBSTITUTED`). «Модератор не
изменяет параметры валидации» — qurilish bo'yicha bajariladi: bunday
ruxsat umuman yo'q, parametrlar runtime da tahrirlanmaydi. Uchchala
band shu yerda **qayta o'lchanmaydi** — `security` reyestriga bog'lam
bilan qulflanadi (ikki reyestr bir haqiqatni ikki marta e'lon qilmasin).

## Teskari yo'nalish: Overpass API bu jadvalda ham yo'q

73-run `01` §18 da Overpass yo'qligini topgan edi. BRD §18 ham uni
nomlamaydi — ya'ni E2 quvurining yagona tashqi tizimi **ikkala**
hujjatning integratsiya jadvalidan tashqarida. `undeclared = 1`.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi: Open Data sirti yashirilmadi (skoup qarori 👤),
rollar qo'shilmadi (beshta yangi rol — mahsulot qarori, `05` §2.5
minimal to'plamni ataylab tanlagan), split/confirm qurilmadi (`05` §4.4
qonun), MFA qurilmadi (ma'lum qarz, SEC reyestrida). Modul o'lchaydi,
tahrirlamaydi (75–77, 82–87, 99–103 runlar qoidasi).

Modul `app/release/` da yashaydi; runtime importlari — faqat qo'shni
reyestrlar (`app.integrations.registry` — `01` §18 bilan to'qnashuv
ikkala tomondan; `app.admin.roles` — rol/ruxsat matritsasi;
`app.admin.security` — «Ограничения» bandlari; `business_environment`
— Kafka/Redis ↔ `CON-05` bog'lami), `acceptance` ↔ `gates` naqshi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.admin import security as sec
from app.admin.roles import PERMISSIONS, Permission, Role
from app.integrations import registry as intreg
from app.release import business_environment as benv

#: Hujjat bo'limlari. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "BRD §18–§19"

#: Jadval o'lchamlari — hujjatdan parse qilinadi va solishtiriladi.
SPEC_INTEGRATION_ROWS = 10
SPEC_ROLE_ROWS = 8

#: Ikkala hujjatning §18 ida ham yo'q, kodda esa tarmoqqa chiqadigan
#: tizim (73-run + shu run). `Overpass` so'zi BRD §18 matnida uchramasligi
#: testda hujjatdan tekshiriladi.
UNDECLARED_SYSTEM = "Overpass API"

#: §19 «Ограничения» xatboshisining uch bandi — har biri `app.admin.security`
#: reyestridagi qatorga bog'lanadi (kod ustuni o'sha yerda o'lchanadi).
RESTRICTION_LOCKS: tuple[tuple[str, str], ...] = (
    ("2FA", "mfa"),
    ("outage.read_exact_geo", "read_exact_geo"),
    ("Разделение обязанностей", "rbac"),
)

#: §19 moderator qatori va'da qilgan to'rt fe'l — hujjat so'zlari bilan.
MODERATOR_VERBS: tuple[str, ...] = (
    "подтверждение",
    "отклонение",
    "объединение",
    "разделение",
)

#: To'rt fe'ldan kodda bor ikkitasi (`05` §4.4 o'tishlari).
MODERATOR_BUILT_VERBS: dict[str, Permission] = {
    "отклонение": Permission.OUTAGE_REJECT,
    "объединение": Permission.OUTAGE_MERGE,
}


class Claim(StrEnum):
    """§18 «Статус» katagining sinfi — katak matni heterogen, sinf yagona."""

    #: `ДАННЫЕ` — tekshirilgan bilim.
    DATA = "data"
    #: `ГИПОТЕЗА` — taxmin.
    HYPOTHESIS = "hypothesis"
    #: `BASELINE-TAS` — Toshkent bazasidan ko'chirilgan bilim.
    BASELINE = "baseline"
    #: «Требуется» — hujjat talab deb biladi.
    REQUIRED = "required"
    #: «Действует» — hujjat ishlayapti deb biladi.
    ACTIVE = "active"
    #: «Out of Scope» / «вне скоупа» — hujjat skoupdan chiqargan.
    OUT_OF_SCOPE = "out_of_scope"


def classify_status(cell: str) -> Claim:
    """`Статус` katagini sinfga o'giradi. Test hujjatdan qayta chaqiradi."""
    if "ДАННЫЕ" in cell:
        return Claim.DATA
    if "ГИПОТЕЗА" in cell:
        return Claim.HYPOTHESIS
    if "BASELINE-TAS" in cell:
        return Claim.BASELINE
    if "Требуется" in cell:
        return Claim.REQUIRED
    if "Действует" in cell:
        return Claim.ACTIVE
    if "Out of Scope" in cell or "вне скоупа" in cell:
        return Claim.OUT_OF_SCOPE
    raise ValueError(f"{SPEC}: notanish status katagi: {cell!r}")


class Build(StrEnum):
    """§18 tizimining qurilgan mahsulotdagi holati."""

    #: Ishlaydigan chaqiruv yoki so'rov yo'li bor.
    LIVE = "live"
    #: Sozlama/seed/ogohlantirish bor, chaqiruv yo'li yo'q.
    PROVISIONED = "provisioned"
    #: ADR bilan ataylab chiqarib tashlangan — o'rnini bosuvchisi bor.
    REJECTED = "rejected"
    #: Kodda hech narsa yo'q va hujjat ham buni kutmaydi — to'g'ri holat.
    DEFERRED = "deferred"
    #: Hujjat skoupdan chiqargan, repo esa qurib bo'lgan.
    AHEAD = "ahead"


class RoleBuild(StrEnum):
    """§19 rolining qurilgan mahsulotdagi holati."""

    #: Rol yoki unga teng sirt to'liq bor.
    BUILT = "built"
    #: Rol bor, hujjatdagi huquqlarining bir qismi yo'q — farq `gap` da.
    PARTIAL = "partial"
    #: Rol yo'q, vazifasini boshqa mexanizm bajaradi — qaysi ekani `note` da.
    SUBSTITUTED = "substituted"
    #: Kodda umuman izi yo'q.
    ABSENT = "absent"


class BusinessInterfacesError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class IntegrationRow:
    """§18 ning bitta qatori. `system`/`direction`/`status` — hujjat bilan aynan."""

    system: str
    #: «Направление» katagi — hujjat so'zlari bilan.
    direction: str
    #: «Статус» katagi — hujjat so'zlari bilan aynan (sinf undan hisoblanadi).
    status: str
    build: Build
    note: str
    #: `01` §18 dagi egizak qatorning `Система` katagi (bo'lsa) —
    #: `app.integrations.registry.ASSESSMENT_BY_SYSTEM` ga kalit.
    counterpart: str = ""
    binds: tuple[str, ...] = ()
    gap: str = ""

    @property
    def claim(self) -> Claim:
        return classify_status(self.status)


@dataclass(frozen=True)
class RoleRow:
    """§19 ning bitta qatori."""

    #: «Роль» katagi — hujjat so'zlari bilan aynan.
    name: str
    #: «Скоуп» katagi — hujjat so'zlari bilan aynan.
    scope: str
    build: RoleBuild
    note: str
    #: Kodda mos keladigan rol (bo'lsa).
    code_role: Role | None = None
    binds: tuple[str, ...] = ()
    gap: str = ""


# --------------------------------------------------------------------------
# §18 — integratsiyalar, hujjatdagi tartibda
# --------------------------------------------------------------------------

INTEGRATIONS: tuple[IntegrationRow, ...] = (
    IntegrationRow(
        system="Telegram Bot API",
        direction="Двустороннее",
        status="`ДАННЫЕ`, действует",
        build=Build.LIVE,
        counterpart="Telegram Bot API",
        note=(
            "Bot to'liq qurilgan, ikkala rejim ham ishlaydi. «REST + "
            "Webhook» katagi esa `01` §18 dagi bilan bir xil oshirib "
            "yuborilgan: jo'natiladigan standart — `polling` "
            "(`TELEGRAM_MODE`, 73-run `OVERSTATED` topilmasi)."
        ),
        binds=("app.bot.factory:create_bot", "app.bot.webhook:build_router"),
        gap="«Webhook» e'lon qilinadi, standart konfiguratsiya `polling` yuboradi (👤).",
    ),
    IntegrationRow(
        system="Telegram-каналы официальных сообщений (регион)",
        direction="Входящее",
        status="`ГИПОТЕЗА`, источник не подтверждён",
        build=Build.PROVISIONED,
        counterpart="Региональный канал «1055»",
        note=(
            "Belgi halol (`ГИПОТЕЗА`), lekin kod manba haqida qarorlarni "
            "qabul qilib bo'lgan: `official` qatori, og'irlik 0.0, "
            "`is_authoritative=True` — seed da muzlatilgan (73-run "
            "`PRESUMED`). BRD qo'shimchasi: parsing texnikasi «NER» deb "
            "nomlangan — `01` buni aytmagan edi; kodda NER ham, boshqa "
            "parsing ham yo'q."
        ),
        binds=("app.reports.sources:SOURCES",),
        gap="Tasdiqlanmagan manba haqidagi qarorlar seed da muzlatilgan (H-4, 👤).",
    ),
    IntegrationRow(
        system="Геокодер",
        direction="Исходящее",
        status="Требуется",
        build=Build.PROVISIONED,
        counterpart="Геокодер",
        note=(
            "«Требуется» — lekin qurilgan mahsulotga kerak emas: kirish "
            "faqat nuqta bilan (H-6 rad tomonga, `D-06` MOOT). "
            "Konfiguratsiya sirti bor, mexanizm yo'q."
        ),
        binds=("app.core.config:Settings.geocoder_provider",),
        gap="Hujjat talab deb biladi, mahsulot esa usiz qurilgan (`D-06` MOOT, 👤 H-6).",
    ),
    IntegrationRow(
        system="Обратное геокодирование",
        direction="Внутреннее",
        status="Требуется",
        build=Build.LIVE,
        note=(
            "Aynan hujjat aytganidek qurilgan: `ST_Contains` bilan nuqta → "
            "tuman/mahalla (`05` §3). Jadvaldagi yagona «Требуется» qatori "
            "bo'lib, talabi allaqachon bajarilgan."
        ),
        binds=("app.geo.pipeline:find_district_id", "app.geo.pipeline:find_mahalla_id"),
    ),
    IntegrationRow(
        system="Тайловый сервис карты",
        direction="Входящее",
        status="Действует",
        build=Build.LIVE,
        note="👤 ADR-08 hal (2026-08-11): manba OSM; env va veb qurilgan.",
        binds=("app.core.config:Settings.map_tile_url", "web/"),
    ),
    IntegrationRow(
        system="Kafka",
        direction="Внутреннее",
        status="`BASELINE-TAS`",
        build=Build.REJECTED,
        note=(
            "ADR-05 chiqarib tashlagan; o'rnida `outbox` jadvali. Belgi "
            "`BASELINE-TAS` — hujjatning o'zi buni Toshkent merosi deb "
            "ataydi, talab deb emas: `CON-05` savoliga hujjat ichidan "
            "dalil (§15 «не допускается» ↔ §18 «meros bilim», 👤)."
        ),
        binds=("app.notifications.models:OutboxMessage",),
        gap="§15 stekni qotiradi, §18 esa xuddi shu qatorni meros deb belgilaydi (👤 CON-05).",
    ),
    IntegrationRow(
        system="PostgreSQL + PostGIS",
        direction="Внутреннее",
        status="`BASELINE-TAS`",
        build=Build.LIVE,
        note="Yagona ombor va geo-mexanizm — `05` §1 bilan aynan mos.",
        binds=("app.db.spatial:point", "alembic.ini"),
    ),
    IntegrationRow(
        system="Redis",
        direction="Внутреннее",
        status="`BASELINE-TAS`",
        build=Build.REJECTED,
        note=(
            "ADR-05 chiqarib tashlagan; kesh o'rnida ETag + snapshot "
            "(`05` §7.4). Kafka qatori bilan bir juft — `CON-05` ga o'sha "
            "dalil."
        ),
        binds=("app.core.etag:payload_etag", "app.clustering.snapshot:build_payload"),
        gap="§15 stekni qotiradi, §18 esa xuddi shu qatorni meros deb belgilaydi (👤 CON-05).",
    ),
    IntegrationRow(
        system="API оператора электросети",
        direction="Входящее",
        status="Out of Scope v1",
        build=Build.DEFERRED,
        counterpart="Региональный оператор сети",
        note=(
            "Chaqiruv yo'li yo'q va hujjat ham kutmaydi — lekin `01` §18 "
            "egizagi ko'rsatganidek, seed allaqachon `operator_api` "
            "qatorini `is_authoritative=True` bilan saqlaydi (73-run "
            "`PRESUMED`; qaror shu yerda emas, o'sha reyestrda o'lchanadi)."
        ),
    ),
    IntegrationRow(
        system="Open Data API",
        direction="Исходящее",
        status="Ph.3, вне скоупа",
        build=Build.AHEAD,
        note=(
            "«Вне скоупа» — repo esa sirtni qurib bo'lgan: ommaviy REST "
            "(E15 ✅), CSV eksport (`03` §R1.2), GeoJSON snapshot. Qator "
            "aytgan hamma format jo'natiladigan holatda."
        ),
        binds=(
            "app.api.v1.stats:router",
            "app.stats.export:render",
            "app.clustering.snapshot:build_payload",
        ),
        gap="Hujjat Ph.3 ga surgan sirt allaqachon jo'natiladi (👤 skoup qayta yozilsinmi).",
    ),
)


# --------------------------------------------------------------------------
# §19 — rollar, hujjatdagi tartibda
# --------------------------------------------------------------------------

ROLES: tuple[RoleRow, ...] = (
    RoleRow(
        name="Гость (веб)",
        scope="Публичный",
        build=RoleBuild.BUILT,
        note=(
            "Ommaviy sirt loginsiz: karta, statistika, metodologiya — "
            "aynan §19 sanagan uchlik (`05` §7.2)."
        ),
        binds=("app.api.v1.map:router", "app.api.v1.stats:router", "web/"),
    ),
    RoleRow(
        name="Пользователь Telegram",
        scope="Свои ресурсы",
        build=RoleBuild.BUILT,
        note=(
            "Repport, «svet keldi» otmetkasi, obuna, til — to'rttala huquq "
            "botda qurilgan (E3 🔄 faqat haqiqiy token kutadi)."
        ),
        binds=(
            "app.reports.intake:create_report",
            "app.bot.handlers:on_language",
            "app.bot.service:add_subscription",
        ),
    ),
    RoleRow(
        name="Зарегистрированный пользователь (веб)",
        scope="Свои ресурсы",
        build=RoleBuild.ABSENT,
        note=(
            "Veb-ro'yxatdan o'tish yo'q: akkaunt jadvali ham, parol ham, "
            "sessiya ham yo'q — obuna faqat `tg_id` da (`01` §19 In-App "
            "savolining davomi, 👤)."
        ),
    ),
    RoleRow(
        name="Модератор региона",
        scope="Самарканд",
        build=RoleBuild.PARTIAL,
        code_role=Role.MODERATOR,
        note=(
            "Navbat, rad etish, birlashtirish, bloklash — bor. "
            "«Подтверждение» yo'q (tasdiqlash faqat avtomatik, `05` §4.4) "
            "va «разделение» (split) yo'q — na ruxsatda, na servisda."
        ),
        binds=("app.admin.service:reject_outage", "app.admin.service:merge_outage"),
        gap="To'rt fe'ldan ikkitasi qurilgan: confirm va split yo'q (`05` §4.4, 👤).",
    ),
    RoleRow(
        name="Региональный оператор",
        scope="Самарканд",
        build=RoleBuild.ABSENT,
        note=(
            "Rol ham, rejalashtirilgan uzilish importi ham, eskalatsiya "
            "ham yo'q — operator qatlami E18/H-4 bilan birga kutadi."
        ),
    ),
    RoleRow(
        name="Куратор территорий",
        scope="Самарканд",
        build=RoleBuild.SUBSTITUTED,
        note=(
            "Rol emas, asbob: chegara import/versiyalash odam yurgizadigan "
            "CLI da (`survey/stage/promote`), auditli veb-rol yo'q. "
            "Vazifa bajariladi, §19 kutgan shaklda emas."
        ),
        binds=("tools/import_boundaries.py", "tools/region_admin.py"),
    ),
    RoleRow(
        name="Аналитик",
        scope="Глобальный (чтение)",
        build=RoleBuild.SUBSTITUTED,
        note=(
            "Rol emas, ochiq vitrina: §19 bu rolga bergan hamma narsa "
            "(vitrinalar, eksport, hisobotlar) loginsiz hammaga ochiq — "
            "o'qish huquqi rolga emas, dunyoga berilgan."
        ),
        binds=("app.api.v1.stats:router", "app.stats.export:render"),
    ),
    RoleRow(
        name="Super Admin",
        scope="Глобальный",
        build=RoleBuild.ABSENT,
        note=(
            "Validatsiya parametrlari runtime da tahrirlanmaydi — ular "
            "`.env`/`confirm_params` da va faqat deploy bilan o'zgaradi; "
            "global skoupli rol kodda yo'q (`admin` roli — o'qish + "
            "moderatsiya, parametr emas)."
        ),
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessInterfacesReport:
    """BRD §18–§19 ning bugungi holati."""

    integrations: tuple[IntegrationRow, ...]
    roles: tuple[RoleRow, ...]

    def __post_init__(self) -> None:
        self._check_counts()
        self._check_integrations()
        self._check_roles()
        self._check_neighbors()

    # -- qorovullar --------------------------------------------------------

    def _check_counts(self) -> None:
        if len(self.integrations) != SPEC_INTEGRATION_ROWS:
            raise BusinessInterfacesError("§18 qatorlari soni hujjatga mos emas")
        if len(self.roles) != SPEC_ROLE_ROWS:
            raise BusinessInterfacesError("§19 qatorlari soni hujjatga mos emas")

    def _check_integrations(self) -> None:
        for row in self.integrations:
            try:
                classify_status(row.status)
            except ValueError as exc:  # notanish katak — shu yerda yiqilsin
                raise BusinessInterfacesError(str(exc)) from exc
            if row.build in (Build.LIVE, Build.PROVISIONED, Build.AHEAD, Build.REJECTED):
                if not row.binds:
                    raise BusinessInterfacesError(f"{row.system}: {row.build} dalilsiz bo'lmaydi")
            if row.build is Build.DEFERRED and row.binds:
                raise BusinessInterfacesError(
                    f"{row.system}: `DEFERRED` da dalil bo'lmaydi — dalil bor "
                    "bo'lsa, holat boshqa"
                )
            if row.build in (Build.AHEAD, Build.REJECTED) and not row.gap:
                raise BusinessInterfacesError(f"{row.system}: farq bor, `gap` yozilmagan")

    def _check_roles(self) -> None:
        for row in self.roles:
            if row.build in (RoleBuild.BUILT, RoleBuild.PARTIAL, RoleBuild.SUBSTITUTED):
                if not row.binds:
                    raise BusinessInterfacesError(f"{row.name}: {row.build} dalilsiz bo'lmaydi")
            if row.build is RoleBuild.PARTIAL and not row.gap:
                raise BusinessInterfacesError(f"{row.name}: `PARTIAL` da `gap` majburiy")
            if row.build is RoleBuild.ABSENT and (row.binds or row.code_role):
                raise BusinessInterfacesError(
                    f"{row.name}: `ABSENT` da na dalil, na kod roli bo'ladi"
                )
            if row.code_role is not None and row.code_role not in PERMISSIONS:
                raise BusinessInterfacesError(f"{row.name}: kod roli matritsada yo'q")

    def _check_neighbors(self) -> None:
        """Qo'shni reyestrlar bilan bog'lamlar — eskirsa shu yerda yiqiladi."""
        for row in self.integrations:
            if row.counterpart and row.counterpart not in intreg.ASSESSMENT_BY_SYSTEM:
                raise BusinessInterfacesError(
                    f"{row.system}: `01` §18 egizagi {row.counterpart!r} topilmadi"
                )
        if UNDECLARED_SYSTEM not in {u.system for u in intreg.UNDECLARED}:
            raise BusinessInterfacesError(
                f"{UNDECLARED_SYSTEM} endi `01` §18 reyestrida e'lon qilinmagan "
                "emas — teskari topilma qayta ko'rilsin"
            )
        rejected = {r.system for r in self.integrations if r.build is Build.REJECTED}
        if not rejected <= set(benv.BANNED_TECH):
            raise BusinessInterfacesError(
                "`REJECTED` qatorlar `business_environment.BANNED_TECH` dan "
                "tashqariga chiqdi — ADR-05 bog'lami eskirgan"
            )
        by_code = {g.code: g for g in sec.GUARANTEES}
        for _, sec_code in RESTRICTION_LOCKS:
            if sec_code not in by_code:
                raise BusinessInterfacesError(
                    f"§19 «Ограничения» bog'lami {sec_code!r} `security` da yo'q"
                )
        if by_code["mfa"].posture is not sec.Posture.ABSENT:
            raise BusinessInterfacesError(
                "MFA endi `ABSENT` emas — §19 «Ограничения» bahosi eskirgan"
            )
        confirm_like = {p for p in Permission if "confirm" in p.value}
        if confirm_like:
            raise BusinessInterfacesError(
                "`Permission` da confirm paydo bo'ldi — moderator qatori eskirgan"
            )

    # -- kesimlar ----------------------------------------------------------

    @property
    def ahead(self) -> tuple[IntegrationRow, ...]:
        """Hujjat skoupdan chiqargan, repo qurib bo'lgan: bugun Open Data API."""
        return tuple(r for r in self.integrations if r.build is Build.AHEAD)

    @property
    def rejected(self) -> tuple[IntegrationRow, ...]:
        """ADR bilan chiqarilganlar: Kafka, Redis (`CON-05` bog'lami)."""
        return tuple(r for r in self.integrations if r.build is Build.REJECTED)

    @property
    def flagged_integrations(self) -> tuple[IntegrationRow, ...]:
        """`gap` i bo'sh bo'lmagan qatorlar — hujjat bilan kod ajragan joylar."""
        return tuple(r for r in self.integrations if r.gap)

    @property
    def by_build(self) -> dict[Build, tuple[str, ...]]:
        result: dict[Build, list[str]] = {b: [] for b in Build}
        for row in self.integrations:
            result[row.build].append(row.system)
        return {b: tuple(v) for b, v in result.items()}

    @property
    def missing_roles(self) -> tuple[RoleRow, ...]:
        """Kodda izi yo'q rollar: veb-akkaunt, operator, Super Admin."""
        return tuple(r for r in self.roles if r.build is RoleBuild.ABSENT)

    @property
    def substituted_roles(self) -> tuple[RoleRow, ...]:
        return tuple(r for r in self.roles if r.build is RoleBuild.SUBSTITUTED)

    @property
    def flagged_roles(self) -> tuple[RoleRow, ...]:
        """`BUILT` dan boshqa hamma rollar — §19 va'dasi to'liq emas."""
        return tuple(r for r in self.roles if r.build is not RoleBuild.BUILT)

    @property
    def code_roles_covered(self) -> frozenset[Role]:
        """Kod rollaridan §19 jadvaliga bog'langanlari."""
        return frozenset(r.code_role for r in self.roles if r.code_role is not None)

    @property
    def moderator_missing_verbs(self) -> tuple[str, ...]:
        """§19 va'da qilgan, kodda yo'q fe'llar: confirm va split."""
        return tuple(v for v in MODERATOR_VERBS if v not in MODERATOR_BUILT_VERBS)

    @property
    def accurate(self) -> bool:
        """§18–§19 «hujjat kodni to'g'ri tasvirlaydi» deb o'qilsa rostmi.

        Bugun `False`: olti integratsiya qatori ajragan, olti rol to'liq
        emas, Overpass ikkala hujjatda ham e'lon qilinmagan.
        """
        return (
            not self.flagged_integrations
            and not self.flagged_roles
        )


def evaluate() -> BusinessInterfacesReport:
    """Reyestrdan to'liq hisobot. Argument yo'q — 85–87, 99–103 runlar qoidasi."""
    return BusinessInterfacesReport(integrations=INTEGRATIONS, roles=ROLES)

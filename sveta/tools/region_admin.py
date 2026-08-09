"""Mintaqalarni boshqarish — «ikkinchi mintaqa kodsiz» (`04` E19).

E19 ning chiqish mezoni: **yangi shahar deploysiz ishga tushadi.** Backend
tomonda buning uchun uchta narsa kerak edi: bbox bazada (`0005`), mintaqa
nuqtadan aniqlanishi (`app/geo/registry.py`) va — shu asbob — mintaqa
qatorini yaratish yo'li. Shusiz «kodsiz» qog'ozda qolardi: `regions` ga
qator qo'yish uchun qo'lda SQL yozish kerak bo'lardi, ya'ni ishga tushirish
bir marta bajariladigan, hujjatlanmagan va xatoga moyil amal bo'lardi.

## Yangi shaharni ishga tushirish tartibi

```
python -m tools.region_admin add --code bukhara \\
    --name-uz Buxoro --name-ru "Бухара" \\
    --bbox 39.70,64.35,39.85,64.52 --lang uz
python -m tools.import_boundaries survey --region bukhara      # ADR-07
python -m tools.import_boundaries stage --region bukhara --admin-level N \\
    --reference-level M
python -m tools.import_boundaries promote --region bukhara --batch <UUID>
python -m tools.region_admin activate --code bukhara
```

Mintaqa **o'chirilgan holda** yaratiladi. Sabab tartibning o'zida: chegara
importi va uni tekshirish bir necha bosqich, va shu oraliqda mintaqa
ommaviy ro'yxatda ko'rinmasligi kerak. `activate` — ataylab alohida qadam.

## Nima uchun `region_config` seed qilinadi

`06` §9 parametrlari va obuna radiusi (`01` §19: 500 m — Toshkentdan
olingan `[BASELINE-TAS]`, mintaqa uchun alohida kalibrlanadi)
`region_config` da. Seed qilinmasa kod
`app/clustering/params.py` dagi `DEFAULTS` ga tushadi — ishlaydi, lekin
qiymatlar **ko'rinmas** bo'lib qoladi: E11 da sozlaydigan odam nimani
o'zgartirishini bilmaydi va mintaqalar orasidagi farqni ko'rmaydi. Seed
mavjud qiymatni hech qachon qayta yozmaydi (`--reseed` bilan ham faqat
yetishmayotganlari qo'shiladi).

`center` bbox markazidan hisoblanadi: `05` §2.1 uni `NOT NULL` qiladi,
lekin uning yagona ishlatilishi — xarita boshlang'ich ko'rinishi, ya'ni
alohida so'rashning ma'nosi yo'q. Kerak bo'lsa `--center lat,lon`.

## Nima uchun har bir o'zgarish `audit_log` ga tushadi

`BRD` BR-024 (High) va NFR-AU-01: **har qanday** amal mintaqa
spravochnigi ustida o'zgarmas jurnalda qoladi. Bugungacha jurnalda faqat
moderator harakatlari bor edi (`outage.reject`, `user.block` …), ya'ni
talab moderatsiya uchun bajarilgan va spravochnik uchun bajarilmagan.

Bo'shliqning narxi eng ko'p `config` da ko'rinadi: u `06` §9
parametrlarini — tasdiqlash chegarasi, masshtab koeffitsientlari,
bildirishnoma radiusi — o'zgartiradi. `confirm.min_users` ni `1` ga
tushirish bir kechada butun mintaqaning statistikasini boshqa qiladi va
bugungi kodda bundan **hech qanday iz qolmaydi**: xato ham chiqmaydi,
kim va qachon qilgani ham ko'rinmaydi. Kesilgan qadam esa aynan
`06` §9 ning «qiymatlar E11 da sozlanadi» degan qismi, ya'ni bu
o'zgarish kelajakda tez-tez bo'ladi.

Yozuv o'zgarish bilan **bitta tranzaksiyada**: audit qatorisiz
o'zgarish ham, o'zgarishsiz audit qatori ham bo'lmaydi.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import func, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.admin import audit  # noqa: E402
from app.clustering.params import DEFAULTS  # noqa: E402
from app.core.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES  # noqa: E402
from app.db.session import dispose_engine, session_scope  # noqa: E402
from app.geo.bbox import BBoxError, parse_bbox  # noqa: E402
from app.geo.models import Region, RegionConfig  # noqa: E402
from app.notifications.params import seed_values as notify_seed_values  # noqa: E402

EXIT_OK = 0
EXIT_BLOCKED = 2
EXIT_USAGE = 64


def _parse_center(raw: str) -> tuple[float, float]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 2:
        raise BBoxError("center formati: lat,lon")
    try:
        lat, lon = (float(p) for p in parts)
    except ValueError as exc:
        raise BBoxError(f"center da son bo'lmagan qiymat: {raw}") from exc
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise BBoxError("center koordinatalari diapazondan tashqarida")
    return lat, lon


def _point(lat: float, lon: float):
    """`geography(Point,4326)` — `regions.center` uchun."""
    return func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)


async def _find(session, code: str) -> Region | None:
    return (
        await session.execute(select(Region).where(Region.code == code))
    ).scalar_one_or_none()


async def _seed_config(session, region_id) -> int:
    """Yetishmayotgan `region_config` kalitlarini qo'shadi; sonini qaytaradi.

    Mavjud kalit **hech qachon** qayta yozilmaydi: E11 da qo'lda
    sozlangan qiymatni asbobning jim ravishda tiklashi eng yomon
    kutilmagan holat bo'lardi.
    """
    existing = {
        key
        for (key,) in (
            await session.execute(
                select(RegionConfig.key).where(RegionConfig.region_id == region_id)
            )
        ).all()
    }
    added = 0
    for key, value in seed_defaults().items():
        if key in existing:
            continue
        session.add(RegionConfig(region_id=region_id, key=key, value=value))
        added += 1
    return added


def seed_defaults() -> dict[str, float]:
    """Seed qilinadigan barcha kalitlar: `06` §9 + obuna radiusi (`01` §19).

    Ikki manba **alohida** qoladi: `DEFAULTS` — `06` §9 jadvalining aynan
    nusxasi va unga begona kalit qo'shilsa spetsifikatsiya bilan
    solishtirish buzilardi. Birlashma faqat shu yerda, seed nuqtasida.
    """
    return {**DEFAULTS, **notify_seed_values()}


# --- buyruqlar ----------------------------------------------------------------


async def cmd_list(args: argparse.Namespace) -> int:
    async with session_scope() as session:
        rows = (await session.execute(select(Region).order_by(Region.code.asc()))).scalars().all()
        if not rows:
            print("Mintaqa yo'q. `region_admin add` bilan qo'shing.")
            return EXIT_OK
        print(f"{'kod':<14} {'faol':<5} {'til':<4} {'bbox':<34} nomi")
        print("-" * 88)
        for r in rows:
            box = r.bbox
            print(
                f"{r.code:<14} {'ha' if r.is_active else 'yo`q':<5} "
                f"{r.default_language:<4} {(box.as_overpass() if box else '—'):<34} "
                f"{r.name_uz} / {r.name_ru}"
            )
    return EXIT_OK


async def cmd_add(args: argparse.Namespace) -> int:
    code = args.code.strip().lower()
    try:
        box = parse_bbox(args.bbox)
        center = _parse_center(args.center) if args.center else box.center
    except BBoxError as exc:
        print(f"[BLOK] {exc}")
        return EXIT_USAGE

    async with session_scope() as session:
        if await _find(session, code) is not None:
            print(f"[BLOK] '{code}' allaqachon mavjud. O'zgartirish uchun `update`.")
            return EXIT_BLOCKED

        region = Region(
            code=code,
            name_uz=args.name_uz,
            name_ru=args.name_ru,
            default_language=args.lang,
            center=_point(*center),
            # Ataylab o'chirilgan: chegaralar import qilinib tekshirilgunicha
            # mintaqa ommaviy ro'yxatda ko'rinmasligi kerak.
            is_active=False,
            bbox_min_lat=box.min_lat,
            bbox_min_lon=box.min_lon,
            bbox_max_lat=box.max_lat,
            bbox_max_lon=box.max_lon,
        )
        session.add(region)
        await session.flush()
        added = await _seed_config(session, region.id)
        await audit.record(
            session,
            actor=audit.cli_actor(),
            action=audit.AuditAction.REGION_CREATE,
            object_id=region.id,
            # `before` yo'q va bu «bo'sh» degani emas: qator endi
            # yaratildi, ya'ni undan oldingi holat mavjud emas.
            after={
                "code": code,
                "name_uz": args.name_uz,
                "name_ru": args.name_ru,
                "default_language": args.lang,
                "bbox": [box.min_lat, box.min_lon, box.max_lat, box.max_lon],
                "center": [center[0], center[1]],
                "is_active": False,
                "config_keys_seeded": added,
            },
        )

    print(f"'{code}' qo'shildi (o'chirilgan holda), {added} ta konfiguratsiya kaliti seed qilindi.")
    print("Keyingi qadam: `python -m tools.import_boundaries survey --region " f"{code}`")
    return EXIT_OK


async def cmd_update(args: argparse.Namespace) -> int:
    code = args.code.strip().lower()
    # Kirish qiymatlari sessiya ochilishidan **oldin** tahlil qilinadi.
    #
    # Ilgari `--bbox` va `--center` o'z navbati kelganda, ya'ni boshqa
    # maydonlar allaqachon o'zgartirilgandan keyin tahlil qilinardi va
    # xato bo'lsa `return EXIT_USAGE` bajarilardi. `return` esa
    # `session_scope()` uchun **normal tugash**, ya'ni kontekst menejeri
    # `commit()` qilardi: `--name-uz Foo --center xato` buyrug'i nomni
    # bazaga yozib, audit qatorini esa yozmasdan chiqib ketardi — aynan
    # BR-024 ning buzilishi va uni «audit bitta tranzaksiyada» testi
    # ushlay olmaydi, chunki chaqiruv o'z joyida turibdi.
    #
    # `cmd_add` boshidan shunday qilingan; farq faqat shu funksiyada edi.
    try:
        box = parse_bbox(args.bbox) if args.bbox else None
        center = _parse_center(args.center) if args.center else None
    except BBoxError as exc:
        print(f"[BLOK] {exc}")
        return EXIT_USAGE

    async with session_scope() as session:
        region = await _find(session, code)
        if region is None:
            print(f"[BLOK] '{code}' topilmadi.")
            return EXIT_BLOCKED
        changed: list[str] = []
        before: dict[str, object] = {}
        after: dict[str, object] = {}
        if box is not None:
            before["bbox"] = [
                region.bbox_min_lat,
                region.bbox_min_lon,
                region.bbox_max_lat,
                region.bbox_max_lon,
            ]
            region.bbox_min_lat = box.min_lat
            region.bbox_min_lon = box.min_lon
            region.bbox_max_lat = box.max_lat
            region.bbox_max_lon = box.max_lon
            after["bbox"] = [box.min_lat, box.min_lon, box.max_lat, box.max_lon]
            changed.append("bbox")
        if args.name_uz:
            before["name_uz"] = region.name_uz
            region.name_uz = args.name_uz
            after["name_uz"] = args.name_uz
            changed.append("name_uz")
        if args.name_ru:
            before["name_ru"] = region.name_ru
            region.name_ru = args.name_ru
            after["name_ru"] = args.name_ru
            changed.append("name_ru")
        if args.lang:
            before["default_language"] = region.default_language
            region.default_language = args.lang
            after["default_language"] = args.lang
            changed.append("default_language")
        if center is not None:
            lat, lon = center
            region.center = _point(lat, lon)
            # `before["center"]` yo'q: ustundagi qiymat — `WKBElement`,
            # uni `jsonb` ga qo'yish yozuvni **amal bajarilgandan keyin**
            # yiqitardi (`audit.jsonable` docstringi). Eski markazni
            # o'qish uchun alohida `ST_Y/ST_X` so'rovi kerak bo'lardi va
            # u audit yozuvining narxini so'rovga aylantirardi.
            after["center"] = [lat, lon]
            changed.append("center")
        if not changed:
            print("Hech narsa berilmadi — o'zgarish yo'q.")
            return EXIT_USAGE
        await audit.record(
            session,
            actor=audit.cli_actor(),
            action=audit.AuditAction.REGION_UPDATE,
            object_id=region.id,
            before=before,
            after=after,
        )
    print(f"'{code}' yangilandi: {', '.join(changed)}.")
    print("Reyestr keshi REGION_CACHE_TTL_S dan keyin yangilanadi.")
    return EXIT_OK


async def _set_active(code: str, active: bool) -> int:
    async with session_scope() as session:
        region = await _find(session, code)
        if region is None:
            print(f"[BLOK] '{code}' topilmadi.")
            return EXIT_BLOCKED
        if active and region.bbox is None:
            # bbox siz mintaqa nuqta bo'yicha hech qachon tanlanmaydi
            # (`registry.pick_for_point`), ya'ni «faol» bo'lsa ham xabar
            # qabul qilmasdi. Jim yoqishdan ko'ra bloklagan afzal.
            print(f"[BLOK] '{code}' da bbox yo'q — `update --bbox` bilan to'ldiring.")
            return EXIT_BLOCKED
        was = region.is_active
        region.is_active = active
        # Holat allaqachon shunday bo'lsa yozuv qo'yilmaydi: jurnal
        # o'zgarishlar tarixi, buyruqlar tarixi emas. Qayta-qayta
        # `activate` qilingan mintaqa haqiqiy yoqilish sanasini
        # bir xil qatorlar orasida ko'mib tashlardi.
        if was != active:
            await audit.record(
                session,
                actor=audit.cli_actor(),
                action=(
                    audit.AuditAction.REGION_ACTIVATE
                    if active
                    else audit.AuditAction.REGION_DEACTIVATE
                ),
                object_id=region.id,
                before={"is_active": was},
                after={"is_active": active},
            )
    print(f"'{code}' {'yoqildi' if active else 'o`chirildi'}.")
    print("Reyestr keshi REGION_CACHE_TTL_S dan keyin yangilanadi.")
    return EXIT_OK


async def cmd_activate(args: argparse.Namespace) -> int:
    return await _set_active(args.code.strip().lower(), True)


async def cmd_deactivate(args: argparse.Namespace) -> int:
    return await _set_active(args.code.strip().lower(), False)


async def cmd_config(args: argparse.Namespace) -> int:
    code = args.code.strip().lower()
    async with session_scope() as session:
        region = await _find(session, code)
        if region is None:
            print(f"[BLOK] '{code}' topilmadi.")
            return EXIT_BLOCKED

        if args.seed:
            added = await _seed_config(session, region.id)
            if added:
                await audit.record(
                    session,
                    actor=audit.cli_actor(),
                    action=audit.AuditAction.REGION_CONFIG_SET,
                    object_id=region.id,
                    after={"seeded_keys": added},
                )
            print(f"{added} ta yetishmayotgan kalit qo'shildi.")
            return EXIT_OK

        if args.key:
            if args.key not in DEFAULTS:
                # `06` §9 dagi ro'yxat — yopiq. Noma'lum kalit jim yotib
                # qolardi va uni yozgan odam nima uchun ishlamayotganini
                # bilmasdi.
                print(f"[BLOK] noma'lum kalit '{args.key}'. `06` §9 ro'yxatiga qarang.")
                return EXIT_USAGE
            try:
                value = float(args.value)
            except (TypeError, ValueError):
                print("[BLOK] qiymat son bo'lishi kerak.")
                return EXIT_USAGE
            existing = await session.get(RegionConfig, (region.id, args.key))
            was = None if existing is None else float(existing.value)
            if existing is None:
                session.add(RegionConfig(region_id=region.id, key=args.key, value=value))
            else:
                existing.value = value
            # `before` da `None` — «kalit yo'q edi, kod `DEFAULTS` ga
            # tushardi». Uni standart qiymat bilan to'ldirish jurnalni
            # o'qiyotgan odamga qiymat bazada turgan degan yolg'onni
            # aytardi, holbuki farq aynan shunda.
            await audit.record(
                session,
                actor=audit.cli_actor(),
                action=audit.AuditAction.REGION_CONFIG_SET,
                object_id=region.id,
                before={args.key: was},
                after={args.key: value},
            )
            print(f"{code}.{args.key} = {value}")
            return EXIT_OK

        rows = (
            await session.execute(
                select(RegionConfig.key, RegionConfig.value)
                .where(RegionConfig.region_id == region.id)
                .order_by(RegionConfig.key.asc())
            )
        ).all()
        if not rows:
            print("Konfiguratsiya bo'sh — kod DEFAULTS ga tushadi. `config --seed` qiling.")
            return EXIT_OK
        for key, value in rows:
            mark = "" if key in DEFAULTS else "  [noma'lum kalit]"
            print(f"{key:<32} {value}{mark}")
    return EXIT_OK


# --- CLI ----------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="region_admin", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="mintaqalar ro'yxati")
    p_list.set_defaults(func=cmd_list)

    p_add = sub.add_parser("add", help="yangi mintaqa (o'chirilgan holda)")
    p_add.add_argument("--code", required=True, help="regions.code, masalan `bukhara`")
    p_add.add_argument("--name-uz", required=True, dest="name_uz")
    p_add.add_argument("--name-ru", required=True, dest="name_ru")
    p_add.add_argument("--bbox", required=True, help="min_lat,min_lon,max_lat,max_lon")
    # Ro`yxat `app.core.i18n` dan: uchinchi til qo`shilsa asbob uni
    # avtomatik qabul qiladi va ikki joyda ajralib ketmaydi.
    p_add.add_argument("--lang", default=DEFAULT_LANGUAGE, choices=SUPPORTED_LANGUAGES)
    p_add.add_argument("--center", default="", help="lat,lon — bo'sh bo'lsa bbox markazi")
    p_add.set_defaults(func=cmd_add)

    p_update = sub.add_parser("update", help="mavjud mintaqani o'zgartirish")
    p_update.add_argument("--code", required=True)
    p_update.add_argument("--bbox", default="")
    p_update.add_argument("--name-uz", default="", dest="name_uz")
    p_update.add_argument("--name-ru", default="", dest="name_ru")
    p_update.add_argument("--lang", default="", choices=("", *SUPPORTED_LANGUAGES))
    p_update.add_argument("--center", default="")
    p_update.set_defaults(func=cmd_update)

    p_on = sub.add_parser("activate", help="mintaqani yoqish")
    p_on.add_argument("--code", required=True)
    p_on.set_defaults(func=cmd_activate)

    p_off = sub.add_parser("deactivate", help="mintaqani o'chirish")
    p_off.add_argument("--code", required=True)
    p_off.set_defaults(func=cmd_deactivate)

    p_cfg = sub.add_parser("config", help="`06` §9 parametrlari")
    p_cfg.add_argument("--code", required=True)
    p_cfg.add_argument("--seed", action="store_true", help="yetishmayotgan kalitlarni qo'shish")
    p_cfg.add_argument("--key", default="", help="bitta kalitni o'rnatish")
    p_cfg.add_argument("--value", default=None)
    p_cfg.set_defaults(func=cmd_config)

    return parser


async def _main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return await args.func(args)
    finally:
        await dispose_engine()


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())

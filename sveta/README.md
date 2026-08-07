# Sveta.Net — backend

Elektr uzilishlari haqida jamoaviy xabar tizimi. Spetsifikatsiya: `../05_Technical_Design.md`,
`../06_Confirmation_Logic.md`. Joriy ish holati: `PROGRESS.md`.

## Ishga tushirish

```bash
cp .env.example .env      # qiymatlarni to'ldiring
docker compose up --build
curl http://localhost:8000/api/v1/health
```

`migrate` xizmati `api` dan oldin ishlaydi va `alembic upgrade head` ni bajaradi.

## Lokal ishlab chiqish

```bash
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
pytest -q
ruff check app tools tests alembic
```

## Tuzilma

| Katalog | Mas'uliyat |
|---|---|
| `app/core` | konfiguratsiya, log, i18n, xatoliklar |
| `app/db` | engine, sessiya, deklarativ baza |
| `app/geo` | nuqta → hudud, H3, poligon import |
| `app/reports` | xabar qabul qilish va validatsiya |
| `app/clustering` | hodisa yig'ish, statuslar |
| `app/notifications` | obuna, outbox, yuborish |
| `app/bot` | aiogram handlerlar |
| `app/api` | FastAPI routerlar |
| `app/admin` | moderatsiya |
| `app/jobs` | fon vazifalari |

**Modul chegarasi qat'iy:** bir modul boshqasining jadvaliga to'g'ridan-to'g'ri
murojaat qilmaydi, faqat funksiya chaqiruvi orqali (`05` §1).

## Qoidalar

- Foydalanuvchiga ko'rinadigan matn faqat `app/core/i18n/locales/` dan (UZ va RU).
- `geom_exact` hech qanday API javobida chiqmaydi (`05` §7.3).
- Klasterlash parametrlari konfiguratsiyada, kodda emas (`05` §4.2).
- Sirlar `.env` da; repoda faqat `.env.example`.

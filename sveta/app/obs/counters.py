"""Protsess ichidagi so'rov hisoblagichlari (`05` §10, «xatolik darajasi»).

`05` §10 to'rtta ogohlantirishdan birini «xatolik darajasi» deb belgilaydi.
Qolgan uchtasi bazadan o'qiladi (`app.obs.collector`), bu esa o'qilmaydi:
HTTP javoblari hech qayerda saqlanmaydi va saqlanmasligi ham kerak.

**Cheklovni ochiq yozamiz.** Hisoblagich protsessga tegishli: `api` bir
necha nusxada ishlasa, har nusxa o'z qismini ko'rsatadi va qayta ishga
tushirganda nol dan boshlanadi. Prometheus uchun bu normal (u nusxalarni
`instance` bo'yicha ajratadi va `rate()` qayta ishga tushishni o'zi
hisobga oladi), lekin bitta scrape dagi son butun servisniki emas.

Modul ataylab minimal: lug'at va ikkita funksiya. Qulf yo'q — CPython da
`dict` ning butun qiymatini o'zgartirish GIL ostida atomar emas, lekin
xatolik darajasi statistik ko'rsatkich va bitta yo'qolgan hisob unga
ta'sir qilmaydi; qulf esa har so'rovga narx qo'shardi.
"""

from __future__ import annotations

#: Status sinflari — `2xx`, `4xx`, `5xx` va h.k. Aynan kod emas: kardinallik
#: past qolishi kerak, xatolik darajasi uchun sinf yetarli.
_counts: dict[str, int] = {}


def status_class(status_code: int) -> str:
    return f"{status_code // 100}xx"


def observe(status_code: int) -> None:
    key = status_class(status_code)
    _counts[key] = _counts.get(key, 0) + 1


def snapshot() -> dict[str, int]:
    """Hisoblagichlarning nusxasi (o'qish uchun)."""
    return dict(_counts)


def reset() -> None:
    """Faqat testlar uchun: hisoblagichlar testlar orasida sizib o'tmasligi kerak."""
    _counts.clear()


def error_rate(counts: dict[str, int]) -> tuple[float, int]:
    """`(5xx ulushi, jami so'rovlar)`.

    Jami nol bo'lsa ulush ham nol — «ma'lumot yo'q» holati ogohlantirish
    emas (`app.obs.alerts` uni minimal so'rovlar soni bilan ajratadi).
    """
    total = sum(counts.values())
    if total <= 0:
        return 0.0, 0
    return counts.get("5xx", 0) / total, total

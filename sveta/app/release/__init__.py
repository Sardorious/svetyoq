"""Reliz gate lari (`03` §6) — relizni to'xtatadigan mezonlar.

* `gates.py` — **toza** modul: gate reyestri va baholovchi. Bazaga ham,
  `settings` ga ham murojaat qilmaydi; o'lchovlar chaqiruvchidan keladi.
* `plan.py` — `01` §25 ning reliz rejasi. `gates.py` bilan **bir xil
  savolga** javob beradi («chiqishga ruxsat bormi») va ikkalasi
  bog'lanmagan: §25 ning beshta shartidan birortasi ham `03` §6 ning
  gate i emas, identifikatorlar esa ustma-ust tushib boshqa relizlarni
  nomlaydi.

Bu modul boshqa modullarning jadvaliga murojaat qilmaydi (`05` §1).
"""

"""Statistika vitrinasi va Coverage Index (E14, `05` §7.2, `03` §R1.2).

Modul **hech qanday jadvalga ega emas**. U `app.clustering`, `app.reports` va
`app.geo` ning o'qish funksiyalarini chaqiradi va natijani birlashtiradi
(`05` §1: modul boshqa modulning jadvaliga to'g'ridan-to'g'ri murojaat
qilmaydi).

Ikki qism ataylab ajratilgan:

* `coverage.py` va `aggregate.py` — **toza** funksiyalar, bazasiz
  testlanadi. Indeks formulasi va agregatlarning yig'ilishi shu yerda.
* `service.py` — bazadan o'qish va yuqoridagilarni ulash.
"""

from __future__ import annotations

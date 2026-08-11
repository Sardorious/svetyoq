# 84-run ning mutatsiya harnessi shu yerda edi va **bo'shatildi**.
#
# Sabab — o'zi qulflagan qoida bilan to'qnashuvi: skriptning mutatsiya
# jadvalida `mahallas` ga qo'shish SQL i literal sifatida turardi, va
# `test_glossary_contract` (83-run) hamda yangi `test_success_metrics_contract`
# `app/` + `tools/` + `alembic/` bo'ylab aynan shu naqshni qidiradi.
# Ya'ni harness repoda qolgani uchun ikkala test ham «mahallalarga
# yozadigan yo'l paydo bo'ldi» deb qizarardi. Qoida yumshatilmadi va
# skanerdan istisno qilinmadi: mutatsiya natijasi kodda emas,
# `PROGRESS.md` da yashaydi (oldingi runlarning tartibi).
#
# Natija o'sha yerda: 18 mutatsiya, 0 survivor.
#
# 👤 Faylni o'chirish odamga qoldirildi — `CLAUDE.md` agentga
# `allow_cowork_file_delete` ni chaqirishni taqiqlaydi (30-sessiya
# shunday yo'qolgan).

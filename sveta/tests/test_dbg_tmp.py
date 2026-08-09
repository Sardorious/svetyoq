# 👤 BU FAYLNI O'CHIRING — u 30-sessiyadan qolgan vaqtinchalik nusxa.
#
# 30-sessiya (`01` §16 mahalla qamrovi) uni `test_language_contract` ning
# ichki funksiyalarini tekshirish uchun yozgan va run oxirida o'chirmoqchi
# bo'lgan. O'chirish `mcp__cowork__allow_cowork_file_delete` orqali odam
# tasdig'ini talab qildi, odam esa yo'q edi (rejalashtirilgan run) — va
# sessiya aynan shu chaqiruvda uzilib qoldi, arxivlanmasdan.
#
# 31-sessiya faylni o'chira olmadi (agent uchun o'chirish huquqi yo'q),
# lekin mazmunini olib tashladi. Sabab: fayl `assert` siz edi va faqat
# `print` qilardi — ya'ni test to'plamiga hech narsa qo'shmasdan uni
# ifloslantirardi. Endi pytest bu fayldan bitta ham test yig'maydi.
#
# Faylning asl mazmuni yo'qolmadi: u sinagan xatti-harakat
# `tests/test_language_contract.py` da 28-sessiyada allaqachon qulflangan
# (`_routes` rekursiyasi — `include_router` marshrutlarni tekis ro'yxatga
# qo'ymaydi va test avval jimgina yashil edi).
#
# Odam uchun: `git rm sveta/tests/test_dbg_tmp.py`

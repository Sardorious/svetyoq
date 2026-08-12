# `deploy-server/` — serverdagi umumiy compose

Bu papka **serverdagi `~/deploy/`** ning nusxasi: bitta xostda yashaydigan
bir nechta loyiha (ikkiattor, droneguard, utilitybot, yuksalish, dorilar va
Sveta.Net) bitta `docker-compose.yml` bilan boshqariladi. Repoda saqlanishining
sababi — ilgari bu fayl faqat serverda bor edi va `sveta/docker-compose.yml`
dan **jimgina ajralib** ketardi (`PROGRESS.md` 2026-08-12 dagi yozuv).

| Fayl | Nima |
|---|---|
| `docker-compose.yml` | serverdagi to'liq stek (hamma loyiha) |
| `bormitok.uz.nginx.conf` | **xost** nginx sayti: bormitok.uz → `sveta-web` (127.0.0.1:8080) |

## Sveta.Net qismidagi farqlar (`sveta/docker-compose.yml` ga nisbatan)

1. Xizmat nomlari `sveta-` prefiksi bilan; `DATABASE_URL` xosti — `sveta-db`.
2. `sveta-api` ga **`api` tarmoq aliasi** berilgan, chunki repo ichidagi
   `deploy/nginx.locations.conf` `proxy_pass http://api:8000/...` deb yozilgan
   va u ikkala joyda ham o'zgarishsiz ishlashi kerak.
3. `sveta-jobs` profilsiz (doim ishlaydi), `sveta-bot` esa
   **`profiles: ["polling"]`** — webhook bilan bir vaqtda ishlab qolmasligi
   uchun ataylab tanlanadi.
4. `sveta-jobs` va `sveta-bot` da `healthcheck: disable: true` — ular HTTP
   server emas, rasm healthcheck i ularni doim `unhealthy` ko'rsatardi.
5. `sveta-web` qo'shildi (`127.0.0.1:8080`), TLS siz: HTTPS xost nginx da.
6. Baza faqat `127.0.0.1:5433` da.

## Ko'chirish tartibi (bir marta)

**0. Avval qaysi bazada ma'lumot borligini aniqlang.** Serverda ikkita
stek ishlab turgan edi (`~/deploy/` va repodagi `sveta/docker-compose.yml`),
ya'ni **ikkita alohida Postgres volume i** bor. Ma'lumotni yo'qotmaslik uchun:

```bash
docker exec sveta-db   psql -U sveta -d sveta -c "select code, name_uz from regions;"
docker exec sveta-db-1 psql -U sveta -d sveta -c "select code, name_uz from regions;"
docker exec sveta-db   psql -U sveta -d sveta -c "select count(*) from districts;"
docker exec sveta-db-1 psql -U sveta -d sveta -c "select count(*) from districts;"
```

Samarqand va 6 tuman qaysi birida bo'lsa — **o'sha** qoladi. Agar ma'lumot
`sveta-db-1` da bo'lsa, ko'chirish kerak:

```bash
docker exec sveta-db-1 pg_dump -U sveta -d sveta -Fc > /tmp/sveta.dump
docker exec -i sveta-db pg_restore -U sveta -d sveta --clean --if-exists < /tmp/sveta.dump
```

**1. Ortiqcha stekni to'xtating** (volume lar `-v` siz saqlanadi):

```bash
cd ~/svetyoq/sveta && docker compose down
```

**2. Yangi compose ni qo'ying va ko'taring:**

```bash
cd ~/svetyoq && git pull
cp deploy-server/docker-compose.yml ~/deploy/docker-compose.yml
cd ~/deploy && docker compose up -d --build sveta-api sveta-jobs sveta-web
docker compose ps
curl -fsS 127.0.0.1:8080/health && echo OK
```

**3. Domen (xost nginx + certbot):**

```bash
sudo cp ~/svetyoq/deploy-server/bormitok.uz.nginx.conf /etc/nginx/sites-available/bormitok.uz
sudo ln -s /etc/nginx/sites-available/bormitok.uz /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
curl -I http://bormitok.uz            # 200 bo'lishi kerak
sudo certbot --nginx -d bormitok.uz -d www.bormitok.uz
```

**4. Polling → webhook** (`~/svetyoq/sveta/.env`):

```
MAP_PUBLIC_URL=https://bormitok.uz
TELEGRAM_WEBHOOK_URL=https://bormitok.uz/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=<python -c "import secrets; print(secrets.token_urlsafe(32))">
TELEGRAM_MODE=webhook
```

```bash
cd ~/deploy
docker compose stop sveta-bot && docker compose rm -f sveta-bot
docker compose up -d sveta-api
curl -s "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

Javobdagi `url` — `https://bormitok.uz/telegram/webhook`, `pending_update_count`
esa vaqt o'tishi bilan nolga tushishi kerak. `last_error_message` bo'lsa —
sertifikat yoki proksi yo'lida muammo.

**5. Parol.** `SVETA_POSTGRES_PASSWORD` `.env` da standart `sveta` bo'lib
qolmasin. O'zgartirilganda baza volume i allaqachon yaratilgan bo'lsa parol
o'z-o'zidan yangilanmaydi:

```bash
docker exec sveta-db psql -U sveta -d postgres -c "ALTER USER sveta PASSWORD 'yangi';"
```

va shundan keyin `~/deploy/.env` dagi qiymat yangilanib, `sveta-api`,
`sveta-jobs`, `sveta-migrate` qayta ishga tushiriladi.

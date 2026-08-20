"""Deploy qatlami: nginx ↔ ilova ↔ compose bitta faktning uch e'loni.

Bu qatlam **hech qanday test bilan qoplanmagan** edi va aynan shu sabab
ikkita jim defekt yashab turdi (122-run):

1. `nginx.conf` ning `location = /health` i `api:8000/health` ga borardi,
   ilovada esa ildiz sathida `/health` **yo'q** — u `/api/v1/health` da
   (`app/api/router.py` `api_router` ni `settings.api_prefix` bilan ulaydi).
   Ya'ni sog'liq tekshiruvi 404 qaytarardi; `scripts/deploy.sh` ning
   «API OK» qadami ham xuddi shu manzilni so'rardi.
2. Telegram webhook yo'li (`/telegram/webhook`) proksi qilinmagan edi —
   u API prefiksidan **tashqarida** turadi, ya'ni `/api/` qoidasi uni
   qamramaydi. Webhook rejimiga o'tilganda bot jimgina ishlamay turardi:
   Telegram 404 oladi, ilova esa hech narsa ko'rmaydi.

Ikkalasi ham «konfiguratsiya kodga ishora qiladi, kod esa boshqa joyda»
sinfi — birlik testlari uni ko'rmaydi, chunki nosozlik **fayllar
orasida** yashaydi.

Test bazasiz va Docker siz: fayllar matn sifatida o'qiladi, ilovaning
yo'llari esa `app` dan olinadi (qattiq yozilgan satr emas).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import settings

ROOT = Path(__file__).resolve().parents[1]
LOCATIONS = ROOT / "deploy/nginx.locations.conf"
NGINX_DEV = ROOT / "deploy/nginx.conf"
NGINX_PROD = ROOT / "deploy/nginx.prod.conf"
COMPOSE = ROOT / "docker-compose.yml"
COMPOSE_PROD = ROOT / "deploy/docker-compose.prod.yml"
DEPLOY_SH = ROOT / "scripts/deploy.sh"
INIT_TLS_SH = ROOT / "scripts/init_tls.sh"
#: Serverdagi ko'p loyihali stek va xost nginx sayti (repo ildizida).
SERVER_COMPOSE = ROOT.parent / "deploy-server/docker-compose.yml"
HOST_SITE = ROOT.parent / "deploy-server/bormitok.uz.nginx.conf"

#: Snippet ikkala qobiqqa ham shu nom bilan ulanadi.
SNIPPET_MOUNT = "/etc/nginx/snippets/sveta-locations.conf"

DOMAIN = "bormitok.uz"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


#: nginx `/health` ni shu yo'lga uzatadi.
HEALTH_TARGET = "/api/v1/health/live"


# --------------------------------------------------------------------------
# Fayllar joyida
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        LOCATIONS,
        NGINX_DEV,
        NGINX_PROD,
        COMPOSE,
        COMPOSE_PROD,
        DEPLOY_SH,
        INIT_TLS_SH,
        SERVER_COMPOSE,
        HOST_SITE,
    ],
    ids=lambda p: p.name,
)
def test_the_deploy_file_exists(path: Path) -> None:
    assert path.is_file(), f"{path} yo'q — deploy qatlami to'liq emas"


# --------------------------------------------------------------------------
# Yagona manba: proksi qoidalari bitta faylda
# --------------------------------------------------------------------------


def test_both_shells_include_the_same_locations_snippet() -> None:
    """Ikki nusxa albatta ajralib ketardi — webhook faqat bittasiga qo'shilib."""
    for shell in (NGINX_DEV, NGINX_PROD):
        assert f"include {SNIPPET_MOUNT};" in _read(shell), (
            f"{shell.name} snippetni ulamaydi — qoidalar ikkiga bo'linadi"
        )


def test_the_shells_do_not_redeclare_proxy_rules() -> None:
    """Qobiqda `proxy_pass` paydo bo'lsa — snippet endi yagona manba emas."""
    for shell in (NGINX_DEV, NGINX_PROD):
        body = "\n".join(
            line for line in _read(shell).splitlines() if not line.lstrip().startswith("#")
        )
        assert "proxy_pass" not in body, f"{shell.name} da proksi qoidasi takrorlangan"


def test_the_snippet_is_mounted_by_compose() -> None:
    assert SNIPPET_MOUNT in _read(COMPOSE), "snippet konteynerga ulanmagan"


# --------------------------------------------------------------------------
# Ilovaning yo'llari ↔ nginx
# --------------------------------------------------------------------------


async def test_the_health_location_points_at_a_path_the_app_serves(client) -> None:
    """Aynan shu tekshiruv 404 qaytarayotgan `/health` ni topdi.

    Yo'l matn sifatida emas, **haqiqiy so'rov** bilan tekshiriladi: nginx
    nima so'rasa, ilova aynan shunga javob berishi kerak.
    """
    assert f"proxy_pass http://api:8000{HEALTH_TARGET};" in _read(LOCATIONS)
    assert HEALTH_TARGET == f"{settings.api_prefix}/health/live"

    resp = await client.get(HEALTH_TARGET)
    assert resp.status_code == 200


async def test_the_app_has_no_root_level_health_path(client) -> None:
    """Qorovul: ildizda `/health` paydo bo'lsa yuqoridagi qoida qayta ko'riladi.

    Eski `proxy_pass http://api:8000/health` aynan shu sabab jimgina
    404 qaytarardi.
    """
    resp = await client.get("/health")
    assert resp.status_code == 404, (
        "ildiz sathida `/health` paydo bo'ldi — nginx va deploy.sh qayta ko'rilsin"
    )


def test_the_webhook_path_is_proxied_outside_the_api_prefix() -> None:
    """Webhook yo'li API prefiksidan tashqarida — o'z `location` i kerak."""
    path = settings.telegram_webhook_path
    assert not path.startswith(settings.api_prefix), (
        "webhook prefiks ichiga ko'chgan bo'lsa bu kontrakt qayta yozilsin"
    )
    body = _read(LOCATIONS)
    assert f"location {path}" in body, f"nginx `{path}` ni uzatmaydi"
    assert f"proxy_pass http://api:8000{path};" in body


def test_the_api_prefix_is_proxied() -> None:
    assert settings.api_prefix.startswith("/api/")
    assert "location /api/ {" in _read(LOCATIONS)


def test_deploy_sh_checks_the_same_health_path_as_nginx() -> None:
    """Skript va nginx bir xil manzilni so'rasin — ajralsa biri yolg'on yashil."""
    assert "/api/v1/health/live" in _read(DEPLOY_SH)


# --------------------------------------------------------------------------
# Prod qobig'i: HTTPS, ACME, domen
# --------------------------------------------------------------------------


def test_the_prod_shell_redirects_plain_http() -> None:
    body = _read(NGINX_PROD)
    assert "return 301 https://$host$request_uri;" in body


def test_the_prod_shell_serves_the_acme_challenge_before_redirecting() -> None:
    """ACME joyi redirectdan OLDIN turishi shart — aks holda yangilash o'ladi.

    Sertifikat 90 kunlik: qoida noto'g'ri tartibda tursa sayt uch oydan
    keyin, hech qanday deploysiz o'chadi.
    """
    body = _read(NGINX_PROD)
    acme = body.index("/.well-known/acme-challenge/")
    redirect = body.index("return 301 https://")
    assert acme < redirect, "ACME joyi redirectdan keyin qolgan"


def test_the_prod_shell_names_the_domain_everywhere_it_matters() -> None:
    body = _read(NGINX_PROD)
    assert f"server_name {DOMAIN} www.{DOMAIN};" in body
    assert f"/etc/letsencrypt/live/{DOMAIN}/fullchain.pem" in body
    assert f"/etc/letsencrypt/live/{DOMAIN}/privkey.pem" in body


def test_the_prod_override_replaces_the_dev_config_at_the_same_target() -> None:
    """Nishon yo'li bir xil bo'lmasa ikkala konfiguratsiya birga yuklanardi."""
    target = "/etc/nginx/conf.d/default.conf"
    assert f"./deploy/nginx.conf:{target}:ro" in _read(COMPOSE)
    assert f"./deploy/nginx.prod.conf:{target}:ro" in _read(COMPOSE_PROD)


def test_the_prod_override_publishes_the_web_ports() -> None:
    body = _read(COMPOSE_PROD)
    assert '"80:80"' in body
    assert '"443:443"' in body


def test_certbot_shares_the_webroot_with_nginx() -> None:
    """Tekshiruv fayli nginx ko'radigan joyga tushmasa HTTP-01 hech qachon o'tmaydi."""
    body = _read(COMPOSE_PROD)
    assert "certbot-www:/var/www/certbot" in body
    assert "certbot-etc:/etc/letsencrypt" in body
    assert "root /var/www/certbot;" in _read(NGINX_PROD)


def test_init_tls_creates_a_placeholder_certificate_first() -> None:
    """nginx sertifikatsiz ko'tarilmaydi, certbot esa nginx siz ishlamaydi."""
    body = _read(INIT_TLS_SH)
    placeholder = body.index("openssl req -x509")
    real = body.index("certonly --webroot")
    assert placeholder < real, "vaqtinchalik sertifikat certbot dan keyin qolgan"


# --------------------------------------------------------------------------
# Xavfsizlik: baza portining bog'lanishi
# --------------------------------------------------------------------------


def test_the_database_port_is_not_published_to_the_world_by_default() -> None:
    """`0.0.0.0:5432` — standart parol bilan birga to'g'ridan-to'g'ri xavf."""
    body = _read(COMPOSE)
    assert '"${POSTGRES_BIND:-127.0.0.1}:${POSTGRES_PORT:-5432}:5432"' in body


# --------------------------------------------------------------------------
# Serverdagi ko'p loyihali compose (`deploy-server/`)
# --------------------------------------------------------------------------
#
# Serverda Sveta.Net yolg'iz emas: bitta xostda ikkiattor, droneguard,
# utilitybot va boshqalar bilan **bitta** compose faylida yashaydi. O'sha
# fayl ilgari faqat serverda bor edi va repodagidan jimgina ajralib
# ketardi (2026-08-12: ikkita stek bir vaqtda ishlab turgani shundan).
# Endi u repoda, ya'ni ajralishi o'lchanadigan bo'ldi.


def test_the_server_compose_is_in_the_repo() -> None:
    assert SERVER_COMPOSE.is_file(), (
        "serverdagi compose repoda yo'q — u yana jimgina ajralib ketadi"
    )


def test_the_server_compose_gives_the_api_the_alias_the_snippet_expects() -> None:
    """Snippet `api:8000` ga murojaat qiladi, xizmat esa `sveta-api` deb atalgan.

    Aliassiz nginx `host not found in upstream "api"` bilan **umuman**
    ko'tarilmaydi — ya'ni xarita butunlay ochilmaydi.
    """
    assert "proxy_pass http://api:8000/api/;" in _read(LOCATIONS)
    body = _read(SERVER_COMPOSE)
    assert "aliases: [api]" in body


def test_the_server_compose_mounts_the_same_snippet_from_the_repo() -> None:
    """Nusxa emas, aynan repodagi fayl ulanadi — aks holda ikki manba bo'lardi."""
    body = _read(SERVER_COMPOSE)
    assert f"./svetyoq/sveta/deploy/nginx.locations.conf:{SNIPPET_MOUNT}:ro" in body
    assert "./svetyoq/sveta/deploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro" in body


def test_the_server_bot_is_behind_a_profile() -> None:
    """Polling va webhook bir vaqtda ishlasa nosozlik JIM bo'ladi.

    Telegram update larni ikki iste'molchi orasida tasodifiy bo'lib beradi:
    foydalanuvchi «bot goho javob bermaydi» deb ko'radi, jurnalda esa xato
    yo'q. Shuning uchun polling ataylab tanlanadi.
    """
    body = _read(SERVER_COMPOSE)
    assert 'profiles: ["polling"]' in body


def test_the_server_database_is_not_published_to_the_world() -> None:
    body = _read(SERVER_COMPOSE)
    assert '"127.0.0.1:5433:5432"' in body
    assert '"0.0.0.0:' not in body


def test_the_host_nginx_site_points_at_the_web_container() -> None:
    """Xost nginx faqat uzatadi — marshrutlash konteyner ichida (bitta manba)."""
    body = _read(HOST_SITE)
    assert "server_name bormitok.uz www.bormitok.uz;" in body
    assert "proxy_pass http://127.0.0.1:8080;" in body
    assert "proxy_set_header X-Forwarded-Proto $scheme;" in body
    # Marshrutlash takrorlanmasin: xost saytida `/api/` yoki webhook joyi
    # paydo bo'lsa ikki fayl ajralib ketadi. Izohlar hisobga olinmaydi —
    # ular aynan shu bo'linishni **tushuntiradi**.
    directives = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("#")
    )
    assert "location /api/" not in directives
    assert "/telegram/webhook" not in directives


def test_the_web_container_is_published_where_the_host_site_looks() -> None:
    assert '"127.0.0.1:8080:80"' in _read(SERVER_COMPOSE)


def test_the_http_only_services_do_not_pretend_to_be_healthy() -> None:
    """`jobs` va `bot` HTTP server emas — rasm healthcheck i ularni doim
    `unhealthy` deb ko'rsatardi va haqiqiy nosozlik shovqinda yo'qolardi."""
    body = _read(COMPOSE)
    assert body.count("healthcheck:\n      disable: true") == 2


# --------------------------------------------------------------------------
# `deploy.sh` ning ikkita teskari kafolati (193-run, 👤 talab)
# --------------------------------------------------------------------------
#
# Talab ikki tomonlama va tomonlari **qarama-qarshi**:
#
#   * ilova konteynerlari (`api`, `jobs`, `web`) HAR deployda o'chirilib
#     yangidan yaratilsin — eski konteyner jimgina ishlab qolmasin;
#   * `db` va migratsiya esa o'zgarish bo'lmasa TEGILMASIN.
#
# Bitta `docker compose up -d` chaqiruvi ikkalasini bajara olmaydi:
# `--force-recreate` xizmatlarni ajratmaydi. Shuning uchun skript
# chaqiruvlarni ikkiga bo'ladi va shu bo'linish quyida qulflanadi —
# u kelajakda bitta qatorga «soddalashtirilsa» talab jimgina buziladi.


def _deploy_lines() -> list[str]:
    """`deploy.sh` ning izohsiz qatorlari.

    Izohlar ataylab tashlanadi: ular aynan shu qarorlarni **tushuntiradi**
    va matn bo'yicha qidiruv o'z izohiga ilinardi (Т-1/Т-4 qorovullarining
    saboqi).
    """
    return [
        line
        for line in _read(DEPLOY_SH).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _compose_calls() -> list[str]:
    return [line.strip() for line in _deploy_lines() if "docker compose" in line]


def test_deploy_sh_is_valid_bash() -> None:
    """Sintaksis qorovuli: skript serverda birinchi marta ishga tushadi.

    193-run da `${VAR:-<yo'q>}` ichidagi APOSTROF butun faylni
    `unexpected EOF` bilan yiqitgan edi — qo'shtirnoq ichidagi
    `${...:-...}` ning sukut qismini bash alohida parse qiladi.
    Xato faylning **oxirgi** qatorida ko'rsatiladi, ya'ni ko'zga
    tashlanmaydi; `.ps1` dagi uzun tire minasining bash ko'rinishi.
    """
    import subprocess

    result = subprocess.run(
        ["bash", "-n", str(DEPLOY_SH)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_the_app_containers_are_always_recreated() -> None:
    """👤 talab: ishlab turgan konteyner o'chirilib, yangisi yaratilsin.

    `--force-recreate` siz compose konteyner sozlamasi va rasm ID si
    o'zgarmagan bo'lsa uni **qoldiradi**, ya'ni yangi kod bilan deploy
    «muvaffaqiyatli» ko'rinib, eski protsess ishlab turaverardi.
    """
    recreate = [
        call
        for call in _compose_calls()
        if "--force-recreate" in call and "api" in call and "web" in call
    ]
    assert recreate, "api/jobs/web `--force-recreate` bilan ko'tarilmaydi"
    call = recreate[0]
    assert "jobs" in call, "`jobs` tushib qolgan — xarita va bildirishnomalar o'ladi"
    assert "--profile jobs" in call, "`jobs` profilsiz ko'tarilmaydi"
    # `--no-deps` MAJBURIY: usiz compose `depends_on` bo'yicha `migrate`
    # ni qayta yurgizar va «o'zgarish bo'lmasa tegilmasin» qarori
    # jimgina bekor bo'lardi.
    assert "--no-deps" in call, "`--no-deps` yo'q — migrate qayta yuriladi"


def test_the_database_is_not_recreated_by_default() -> None:
    """👤 talab: o'zgarish bo'lmasa `db` konteyneriga tegilmasin.

    `db` — yagona holat saqlaydigan xizmat (`pgdata`). Sababsiz qayta
    yaratish downtime va xavf, foyda esa nol. Majburiy qayta yaratish
    faqat ochiq bayroq ostida qoladi.
    """
    calls = _compose_calls()
    db_up = [call for call in calls if " up -d db" in call]
    assert db_up, "`db` umuman ko'tarilmaydi"
    for call in db_up:
        assert "--force-recreate" not in call, "`db` sukut bo'yicha qayta yaratilyapti"
    forced = [call for call in calls if "--force-recreate db" in call]
    assert forced, "`--recreate-db` bayrog'ining yo'li yo'q"
    assert "RECREATE_DB" in _read(DEPLOY_SH)


def test_the_migration_runs_only_when_the_database_is_behind() -> None:
    """👤 talab: migratsiyada o'zgarish bo'lmasa yurgizilmasin.

    «O'zgarganmi» degan savolga javobni **baza** beradi, git emas:
    `alembic_version` repodagi head bilan solishtiriladi. Git diff ga
    tayanish `--no-git` va qo'lda ko'chirilgan kod holatlarida yolg'on
    javob berardi, oldingi deploy yarmida uzilib qolganini esa umuman
    ko'rmasdi.
    """
    body = _read(DEPLOY_SH)
    assert "alembic_version" in body, "baza holati o'qilmaydi"
    assert "NEED_MIGRATE" in body
    migrate_calls = [call for call in _compose_calls() if "migrate" in call and "run" in call]
    assert migrate_calls, "migratsiya alohida chaqirilmaydi"
    # Shartsiz `up -d … migrate …` qaytib kelmasin: aynan shu qator
    # migratsiyani har deployda yurgizardi.
    for call in _compose_calls():
        if " up -d" in call:
            assert "migrate" not in call, f"migrate yana `up` ga qo'shilgan: {call}"

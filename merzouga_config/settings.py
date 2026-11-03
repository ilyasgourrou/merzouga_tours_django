"""
Réglages Django de Morocco Riwa Tours.

Organisation du fichier :
  1. Outils pour lire l'environnement (.env et variables)
  2. Identité du site et coordonnées      <-- ce que vous modifiez le plus souvent
  3. Mode, clé secrète et domaines
  4. Applications, middleware et templates
  5. Base de données
  6. Langues
  7. Fichiers statiques et photos
  8. Emails
  9. Sécurité (admin, HTTPS)
 10. Vérifications pour Vercel

Les valeurs sensibles ou propres à chaque installation se règlent par variables d'environnement
(voir .env.example). Les valeurs par défaut conviennent au développement sur votre PC.
"""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# 1. Outils pour lire l'environnement
# =============================================================================

def _load_env_file(path):
    """Lit un fichier .env simple (CLE=valeur). Les vraies variables d'environnement restent prioritaires."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _sep, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _env_bool(name, default=False):
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name):
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


_load_env_file(BASE_DIR / ".env")

ON_VERCEL = bool(os.environ.get("VERCEL"))  # Vercel définit cette variable automatiquement


# =============================================================================
# 2. Identité du site et coordonnées
#    Affichées dans l'en-tête, le footer, la page Contact, les emails et pour Google.
#    Pour les changer en ligne, utilisez les variables d'environnement entre guillemets.
# =============================================================================

SITE_NAME = "Morocco Riwa Tours"
SITE_TAGLINE = "Explore. Experience. Discover."

# Adresse officielle du site, sans slash final. Ex : https://moroccoriwatours.com
SITE_URL = os.environ.get("DJANGO_SITE_URL", "").rstrip("/")

CONTACT_PHONE = os.environ.get("DJANGO_CONTACT_PHONE", "+212 6 88 69 45 28")
CONTACT_EMAIL = os.environ.get("DJANGO_CONTACT_EMAIL", "riwatoursmorocco@gmail.com")

# Numéro WhatsApp qui reçoit les confirmations de réservation (format international ou local marocain).
# Par défaut : le numéro de téléphone ci-dessus.
WHATSAPP_NUMBER = os.environ.get("DJANGO_WHATSAPP_NUMBER", "") or CONTACT_PHONE

# Lien Google Maps ouvert quand on clique sur la localisation (footer et page Contact).
MAPS_URL = os.environ.get("DJANGO_MAPS_URL", "https://maps.app.goo.gl/tFVeQxHwsSpJeNiU7?g_st=aw")


# =============================================================================
# 3. Mode, clé secrète et domaines
# =============================================================================

# En production, définissez DJANGO_SECRET_KEY (voir DEPLOY.md). La valeur par défaut ne sert qu'en développement.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or (
    "django-insecure-4%jg^xqw$mb1hz3izbxkbh32-zr9xssmk20b+20-)l4+o4f6hp"
)

# En production, définissez DJANGO_DEBUG=False.
DEBUG = _env_bool("DJANGO_DEBUG", default=True)

LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]", "testserver"}
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS")
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Origines autorisées pour les formulaires en HTTPS (déduites des domaines si non précisées).
CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS") or [
    f"https://{host.replace('.', '*.', 1) if host.startswith('.') else host}"
    for host in ALLOWED_HOSTS if host not in LOCAL_HOSTS
]

# Garde-fous : empêchent de mettre en ligne par erreur avec les réglages de développement.
if DEBUG and any(host not in LOCAL_HOSTS for host in ALLOWED_HOSTS):
    raise ImproperlyConfigured(
        "DJANGO_DEBUG est activé alors que DJANGO_ALLOWED_HOSTS contient un vrai domaine. "
        "En production, définissez DJANGO_DEBUG=False."
    )
if not DEBUG and SECRET_KEY.startswith("django-insecure"):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY doit être définie avec une valeur secrète quand DJANGO_DEBUG=False "
        "(voir DEPLOY.md pour en générer une)."
    )


# =============================================================================
# 4. Applications, middleware et templates
# =============================================================================

INSTALLED_APPS = [
    "modeltranslation",  # doit être avant django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "axes",
    "tours",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",  # doit rester en dernier
]

if not DEBUG:
    # En production, WhiteNoise sert les fichiers statiques (en développement, runserver s'en charge).
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "merzouga_config.urls"
WSGI_APPLICATION = "merzouga_config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tours.context_processors.site_info",  # variable `site` dans les templates
            ],
        },
    },
]


# =============================================================================
# 5. Base de données
#    Par défaut : fichier SQLite local. En ligne (Vercel...), définissez DATABASE_URL :
#    postgresql://utilisateur:motdepasse@hote:5432/postgres
# =============================================================================

DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0,  # serverless : pas de connexion gardée ouverte entre deux requêtes
    )
}
if DATABASES["default"]["ENGINE"].endswith("postgresql"):
    # Nécessaire avec les « poolers » de connexions (Supabase, Neon...)
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =============================================================================
# 6. Langues
# =============================================================================

LANGUAGE_CODE = "fr"
LANGUAGES = [
    ("fr", _("Français")),
    ("en", _("English")),
    ("es", _("Español")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]  # traductions de l'interface (fichiers .po)
TIME_ZONE = "Africa/Casablanca"
USE_I18N = True
USE_TZ = True

# Textes des circuits et catégories saisis dans chaque langue depuis l'admin (django-modeltranslation).
# Si une traduction est vide, le site affiche la langue de secours plutôt qu'un texte vide.
MODELTRANSLATION_DEFAULT_LANGUAGE = "fr"
MODELTRANSLATION_FALLBACK_LANGUAGES = {"default": ("fr",), "es": ("en", "fr")}


# =============================================================================
# 7. Fichiers statiques et photos
# =============================================================================

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Photos envoyées depuis l'admin
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
# En production sur un petit hébergement, Django peut servir lui-même les photos (DJANGO_SERVE_MEDIA=True).
SERVE_MEDIA = DEBUG or _env_bool("DJANGO_SERVE_MEDIA")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

# Photos sur un stockage externe compatible S3 (obligatoire sur Vercel, qui n'a pas de disque permanent).
# Supabase Storage, Cloudflare R2, AWS S3, etc. Voir DEPLOY_VERCEL.md.
S3_BUCKET = os.environ.get("DJANGO_S3_BUCKET", "")
if S3_BUCKET:
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": S3_BUCKET,
            "endpoint_url": os.environ.get("DJANGO_S3_ENDPOINT") or None,
            "region_name": os.environ.get("DJANGO_S3_REGION", "auto"),
            "access_key": os.environ.get("DJANGO_S3_ACCESS_KEY", ""),
            "secret_key": os.environ.get("DJANGO_S3_SECRET_KEY", ""),
            # Adresse publique d'où les visiteurs chargent les photos (sans https://)
            "custom_domain": os.environ.get("DJANGO_S3_PUBLIC_DOMAIN") or None,
            "addressing_style": os.environ.get("DJANGO_S3_ADDRESSING", "path"),
            "querystring_auth": False,
            "default_acl": None,
            "file_overwrite": False,
        },
    }

# Sur Vercel, une requête ne peut pas dépasser 4,5 Mo : l'admin prévient avant d'envoyer des photos trop lourdes.
ADMIN_UPLOAD_LIMIT = ON_VERCEL or _env_bool("DJANGO_ADMIN_UPLOAD_LIMIT")


# =============================================================================
# 8. Emails
# =============================================================================

# Sans DJANGO_EMAIL_HOST, les emails s'affichent dans la console (pratique en développement).
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_PASSWORD", "")
    EMAIL_USE_TLS = _env_bool("DJANGO_EMAIL_TLS", default=True)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_FROM_EMAIL", f"{SITE_NAME} <{CONTACT_EMAIL}>")

# Adresses qui reçoivent un email à chaque nouvelle réservation ou nouveau message (séparées par des virgules).
NOTIFY_EMAILS = _env_list("DJANGO_NOTIFY_EMAIL")


# =============================================================================
# 9. Sécurité
# =============================================================================

# Adresse de l'admin : changez-la via DJANGO_ADMIN_URL (ex. "gestion-x7k2/") et ne la partagez pas.
ADMIN_URL = os.environ.get("DJANGO_ADMIN_URL", "admin/").strip("/") + "/"

# django-axes : blocage après 5 échecs de connexion (par IP et identifiant), pendant 1 heure.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # heures
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_RESET_ON_SUCCESS = True

# Derrière un proxy HTTPS (Vercel, PythonAnywhere, Nginx...), mettre DJANGO_BEHIND_PROXY=True (automatique sur Vercel).
BEHIND_PROXY = ON_VERCEL or _env_bool("DJANGO_BEHIND_PROXY")
if BEHIND_PROXY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # django-axes doit voir la vraie IP du visiteur, sinon tout le monde partage l'IP du proxy.
    AXES_IPWARE_PROXY_COUNT = 1
    AXES_IPWARE_META_PRECEDENCE_ORDER = ("HTTP_X_FORWARDED_FOR", "REMOTE_ADDR")

# Cookies et HTTPS : activés automatiquement quand DEBUG=False.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = _env_bool("DJANGO_SSL_REDIRECT", default=True)
    # 1 h au départ ; passez à 31536000 (1 an) quand le HTTPS fonctionne parfaitement.
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"


# =============================================================================
# 10. Vérifications pour Vercel
#     Pas de disque permanent : sans base externe ni stockage de photos externe, rien ne peut être enregistré.
# =============================================================================

if ON_VERCEL and DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    raise ImproperlyConfigured(
        "Sur Vercel, définissez la variable DATABASE_URL (base PostgreSQL externe). "
        "SQLite ne peut pas enregistrer de données sur Vercel. Voir DEPLOY_VERCEL.md."
    )
if ON_VERCEL and not S3_BUCKET:
    raise ImproperlyConfigured(
        "Sur Vercel, définissez le stockage des photos (DJANGO_S3_BUCKET, DJANGO_S3_ENDPOINT, "
        "DJANGO_S3_ACCESS_KEY, DJANGO_S3_SECRET_KEY, DJANGO_S3_PUBLIC_DOMAIN). Voir DEPLOY_VERCEL.md."
    )

from django.conf import settings
from django.core.checks import Warning, register


@register(deploy=True)
def production_content_checks(app_configs, **kwargs):
    """Rappels avant mise en ligne : python manage.py check --deploy"""
    problems = []
    if not settings.SITE_URL:
        problems.append(Warning(
            "DJANGO_SITE_URL n'est pas défini : les liens canoniques et le sitemap utiliseront l'adresse de la requête.",
            hint="Exemple : DJANGO_SITE_URL=https://moroccoriwatours.com",
            id="tours.W001",
        ))
    if not settings.NOTIFY_EMAILS:
        problems.append(Warning(
            "Aucune adresse n'est prévue pour les alertes de réservation et de message.",
            hint="Définissez DJANGO_NOTIFY_EMAIL (et DJANGO_EMAIL_HOST pour l'envoi réel).",
            id="tours.W002",
        ))
    elif not settings.EMAIL_HOST:
        problems.append(Warning(
            "Des adresses d'alerte sont définies, mais aucun serveur d'envoi d'emails n'est configuré : rien ne partira.",
            hint="Définissez DJANGO_EMAIL_HOST, DJANGO_EMAIL_USER et DJANGO_EMAIL_PASSWORD (voir .env.example).",
            id="tours.W003",
        ))
    return problems

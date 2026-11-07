from urllib.parse import quote

from django import template
from django.conf import settings
from django.utils.translation import gettext as _

from tours.whatsapp import whatsapp_number

register = template.Library()


@register.simple_tag
def whatsapp_contact_url():
    """Lien wa.me vers le numéro WhatsApp du site, avec un message d'accueil dans la langue du visiteur.

    Renvoie une chaîne vide si aucun numéro n'est configuré (le bouton est alors masqué)."""
    number = whatsapp_number()
    if not number:
        return ""
    text = _("Bonjour %(site)s ! J'aimerais avoir des informations sur vos circuits.") % {"site": settings.SITE_NAME}
    return f"https://wa.me/{number}?text={quote(text, safe='')}"

from django.conf import settings

from .whatsapp import normalize_digits


def site_info(request):
    """Rend le nom du site et les coordonnées disponibles dans tous les templates (variable `site`)."""
    whatsapp = normalize_digits(settings.WHATSAPP_NUMBER)
    return {
        "site": {
            "name": settings.SITE_NAME,
            "tagline": settings.SITE_TAGLINE,
            "phone": settings.CONTACT_PHONE,
            "phone_tel": "+" + normalize_digits(settings.CONTACT_PHONE),
            "email": settings.CONTACT_EMAIL,
            "maps_url": settings.MAPS_URL,
            "whatsapp": whatsapp,
            "whatsapp_display": "+" + whatsapp if whatsapp else "",
        }
    }

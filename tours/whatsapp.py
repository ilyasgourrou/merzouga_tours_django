"""Message WhatsApp de confirmation de réservation (lien wa.me avec texte pré-rempli)."""
import re
from urllib.parse import quote

from django.conf import settings
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _


def normalize_digits(raw, default_country="212"):
    """Chiffres au format international, sans « + ». Accepte aussi le format local marocain (0688-694528)."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = default_country + digits[1:]
    return digits


def whatsapp_number():
    """Numéro au format que wa.me exige : international, chiffres seulement."""
    return normalize_digits(settings.WHATSAPP_NUMBER)


def build_message(reservation):
    travelers = f"{_('Adultes')} : {reservation.adults}"
    if reservation.children:
        travelers += f", {_('Enfants')} : {reservation.children}"
    lines = [
        _("Bonjour %(site)s ! Je souhaite confirmer ma réservation.") % {"site": settings.SITE_NAME},
        "",
        f"{_('Référence')} : {reservation.reference}",
        f"{_('Nom')} : {reservation.full_name}",
        f"{_('Circuit')} : {reservation.tour.title}",
        f"{_('Date souhaitée')} : {date_format(reservation.travel_date, 'DATE_FORMAT')}",
        f"{_('Voyageurs')} : {travelers}",
        f"{_('Total estimé')} : {reservation.total_price:.0f} MAD",
    ]
    return "\n".join(lines)


def whatsapp_url(reservation):
    return f"https://wa.me/{whatsapp_number()}?text={quote(build_message(reservation))}"

import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def notify_staff(subject, body, reply_to=None):
    """Prévient l'agence par email (DJANGO_NOTIFY_EMAIL). N'interrompt jamais la requête du visiteur."""
    recipients = settings.NOTIFY_EMAILS
    if not recipients:
        return
    try:
        EmailMessage(
            subject, body, settings.DEFAULT_FROM_EMAIL, recipients,
            reply_to=[reply_to] if reply_to else None,
        ).send(fail_silently=False)
    except Exception:  # noqa: BLE001 - un souci d'email ne doit pas casser la réservation
        logger.exception("Envoi de la notification impossible")

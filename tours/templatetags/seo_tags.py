import json

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse, translate_url
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


def _base_url(request):
    return settings.SITE_URL or f"{request.scheme}://{request.get_host()}"


def _absolute(request, path):
    if path.startswith("http"):
        return path
    return _base_url(request) + path


def _jsonld(data):
    """JSON-LD sûr à insérer dans une page (on neutralise < > & pour éviter toute injection)."""
    text = json.dumps(data, ensure_ascii=False)
    text = text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{text}</script>')


@register.simple_tag(takes_context=True)
def seo_links(context):
    """Lien canonique + liens hreflang vers chaque langue du site (+ noindex pour les pages filtrées)."""
    request = context["request"]
    path = request.path
    parts = [format_html('<link rel="canonical" href="{}">', _absolute(request, path))]

    codes = [code for code, _name in settings.LANGUAGES]
    for code in codes:
        parts.append(format_html(
            '<link rel="alternate" hreflang="{}" href="{}">',
            code, _absolute(request, translate_url(path, code)),
        ))
    default = "en" if "en" in codes else settings.LANGUAGE_CODE
    parts.append(format_html(
        '<link rel="alternate" hreflang="x-default" href="{}">',
        _absolute(request, translate_url(path, default)),
    ))
    if request.GET:  # résultats filtrés / recherche : inutile de les indexer
        parts.append(mark_safe('<meta name="robots" content="noindex,follow">'))
    return mark_safe("\n  ".join(parts))


@register.simple_tag(takes_context=True)
def absolute_url(context, path):
    return _absolute(context["request"], path)


@register.simple_tag(takes_context=True)
def jsonld_agency(context):
    request = context["request"]
    data = {
        "@context": "https://schema.org",
        "@type": "TravelAgency",
        "name": settings.SITE_NAME,
        "url": _absolute(request, reverse("tours:home")),
        "logo": _absolute(request, static("img/logo-full.png")),
        "slogan": settings.SITE_TAGLINE,
        "telephone": settings.CONTACT_PHONE,
        "email": settings.CONTACT_EMAIL,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Merzouga",
            "addressCountry": "MA",
        },
        "hasMap": settings.MAPS_URL,
        "areaServed": "MA",
    }
    return _jsonld(data)


@register.simple_tag(takes_context=True)
def jsonld_tour(context, tour):
    request = context["request"]
    url = _absolute(request, request.path)
    data = {
        "@context": "https://schema.org",
        "@type": "TouristTrip",
        "name": tour.title,
        "description": tour.short_description,
        "url": url,
        "provider": {"@type": "TravelAgency", "name": settings.SITE_NAME},
        "offers": {
            "@type": "Offer",
            "price": str(tour.discount_price or tour.price),
            "priceCurrency": "MAD",
            "availability": "https://schema.org/InStock",
            "url": url,
        },
    }
    if tour.cover_image:
        data["image"] = _absolute(request, tour.cover_image.url)
    return _jsonld(data)

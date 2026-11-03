from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Tour


class StaticViewSitemap(Sitemap):
    i18n = True          # une entrée par langue (fr, en, es)
    alternates = True    # avec les liens hreflang vers les autres langues
    x_default = False
    changefreq = "monthly"
    priority = 0.6
    protocol = None if settings.DEBUG else "https"

    def items(self):
        return ["tours:home", "tours:tour_list", "tours:about", "tours:contact"]

    def location(self, item):
        return reverse(item)

    def priority_for(self, item):
        return 1.0 if item == "tours:home" else 0.6


class TourSitemap(Sitemap):
    i18n = True
    alternates = True
    x_default = False
    changefreq = "weekly"
    priority = 0.9
    protocol = None if settings.DEBUG else "https"

    def items(self):
        return Tour.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

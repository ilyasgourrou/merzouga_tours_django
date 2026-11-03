from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve

from tours import views as tours_views
from tours.sitemaps import StaticViewSitemap, TourSitemap

sitemaps = {"pages": StaticViewSitemap, "tours": TourSitemap}

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # permet le changement de langue (formulaire dans le header)
    path('robots.txt', tours_views.robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

urlpatterns += i18n_patterns(
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('tours.urls')),
    prefix_default_language=True,
)

# Photos envoyées depuis l'admin (voir SERVE_MEDIA dans settings.py)
if settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'), serve, {'document_root': settings.MEDIA_ROOT}),
    ]

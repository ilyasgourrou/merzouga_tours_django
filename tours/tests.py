"""Tests automatiques : python manage.py test

Ils couvrent les parcours importants du site : pages dans chaque langue, textes traduits des circuits,
réservation avec confirmation WhatsApp, coordonnées affichées, référencement et admin.
"""
import datetime
import json
import re
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from .models import Category, ContactMessage, Reservation, Review, Tour
from .whatsapp import normalize_digits

LANGUAGES = [code for code, _name in settings.LANGUAGES]


def make_tour(**overrides):
    """Crée un circuit de test (texte français obligatoire, anglais et espagnol facultatifs)."""
    values = {
        "title_fr": "Sortie quad au lever du soleil",
        "title_en": "Quad ride at sunrise",
        "short_description_fr": "Les dunes en quad.",
        "short_description_en": "The dunes by quad.",
        "description_fr": "Description complète.",
        "duration_days": 1,
        "departure_city_fr": "Merzouga",
        "price": 320,
        "max_group_size": 10,
    }
    values.update(overrides)
    values.setdefault("slug", "quad-sunrise")
    return Tour.objects.create(**values)


def next_week():
    return (datetime.date.today() + datetime.timedelta(days=7)).isoformat()


class SiteTestCase(TestCase):
    """Base des tests : repart toujours en français pour que reverse() donne des adresses /fr/."""

    def setUp(self):
        super().setUp()
        translation.activate("fr")
        self.addCleanup(translation.deactivate)


class PublicPagesTests(SiteTestCase):
    def setUp(self):
        super().setUp()
        self.tour = make_tour()

    def test_every_page_renders_in_each_language(self):
        for lang in LANGUAGES:
            with translation.override(lang):
                urls = [
                    reverse("tours:home"), reverse("tours:tour_list"), reverse("tours:about"),
                    reverse("tours:contact"), self.tour.get_absolute_url(),
                ]
            for url in urls:
                with self.subTest(lang=lang, url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_unknown_page_shows_branded_404(self):
        response = self.client.get("/fr/cette-page-n-existe-pas/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "noindex", status_code=404)

    def test_inactive_tour_is_hidden(self):
        make_tour(slug="hidden", title_fr="Circuit caché", is_active=False)
        listing = self.client.get(reverse("tours:tour_list")).content.decode()
        self.assertNotIn("Circuit caché", listing)
        self.assertEqual(self.client.get("/fr/circuits/hidden/").status_code, 404)

    def test_language_switch_posts_to_django_and_keeps_the_page(self):
        response = self.client.post(
            reverse("set_language"), {"language": "es", "next": self.tour.get_absolute_url()}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/es/"))


class TranslatedContentTests(SiteTestCase):
    def setUp(self):
        super().setUp()
        self.tour = make_tour()

    def title_on_page(self, lang):
        html = self.client.get(f"/{lang}/circuits/{self.tour.slug}/").content.decode()
        return re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1).strip()

    def test_tour_text_follows_the_visitor_language(self):
        self.assertEqual(self.title_on_page("fr"), "Sortie quad au lever du soleil")
        self.assertEqual(self.title_on_page("en"), "Quad ride at sunrise")

    def test_missing_translation_falls_back_to_french_and_english(self):
        # Pas de titre espagnol : l'espagnol se rabat sur l'anglais, puis sur le français.
        self.assertEqual(self.title_on_page("es"), "Quad ride at sunrise")
        self.tour.title_en = ""
        self.tour.save()
        self.assertEqual(self.title_on_page("es"), "Sortie quad au lever du soleil")

    def test_search_matches_text_in_any_language(self):
        for query in ("quad ride", "lever du soleil"):
            with self.subTest(query=query):
                html = self.client.get("/en/circuits/", {"q": query}).content.decode()
                self.assertIn(self.tour.get_absolute_url(), html)

    def test_category_icon_classes(self):
        self.assertEqual(Category(name="x", icon="fa-sun").icon_classes, "fa-solid fa-sun")
        self.assertEqual(Category(name="x", icon="fas fa-sun").icon_classes, "fa-solid fa-sun")
        self.assertEqual(Category(name="x", icon="🌅").icon_classes, "")


class ReservationTests(SiteTestCase):
    def setUp(self):
        super().setUp()
        self.tour = make_tour()
        self.url = self.tour.get_absolute_url()
        self.data = {
            "full_name": "Anna Smith", "email": "anna@example.com", "phone": "+33611223344",
            "travel_date": next_week(), "adults": 2, "children": 1,
        }

    def book(self, **overrides):
        return self.client.post(self.url, {**self.data, **overrides})

    def test_booking_creates_reservation_with_unique_reference(self):
        response = self.book()
        reservation = Reservation.objects.get()
        self.assertRegex(reservation.reference, r"^MRT-[A-HJ-NP-Z2-9]{6}$")
        self.assertRedirects(response, reverse("tours:reservation_detail", args=[reservation.reference]))
        self.assertEqual(reservation.status, Reservation.STATUS_PENDING)
        self.assertEqual(reservation.total_price, 640)  # 2 adultes x 320

    def test_references_never_collide(self):
        codes = {Reservation.generate_reference() for _ in range(200)}
        self.assertEqual(len(codes), 200)

    def test_bots_and_past_dates_are_rejected(self):
        self.book(website="http://spam.example")
        self.book(travel_date="2020-01-01")
        self.assertEqual(Reservation.objects.count(), 0)

    def test_group_larger_than_tour_limit_is_rejected(self):
        self.book(adults=11)
        self.assertEqual(Reservation.objects.count(), 0)

    @override_settings(WHATSAPP_NUMBER="0688-694528")
    def test_whatsapp_button_opens_prefilled_message_and_records_the_click(self):
        self.book()
        reservation = Reservation.objects.get()
        page = self.client.get(reverse("tours:reservation_detail", args=[reservation.reference]))
        self.assertContains(page, reservation.reference)
        self.assertIsNone(reservation.whatsapp_clicked_at)

        response = self.client.get(reverse("tours:reservation_whatsapp", args=[reservation.reference]))
        target = urlparse(response["Location"])
        self.assertEqual((target.netloc, target.path), ("wa.me", "/212688694528"))
        message = parse_qs(target.query)["text"][0]
        self.assertIn(reservation.reference, message)
        self.assertIn(self.tour.title_fr, message)
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_whatsapp_opened)

    def test_message_uses_the_visitor_language(self):
        self.client.post(f"/en{self.url[3:]}", self.data)
        reservation = Reservation.objects.get()
        response = self.client.get(f"/en/reservation/{reservation.reference}/whatsapp/")
        message = parse_qs(urlparse(response["Location"]).query)["text"][0]
        self.assertIn("Quad ride at sunrise", message)

    def test_page_reflects_the_status_set_in_the_admin(self):
        self.book()
        reservation = Reservation.objects.get()
        reservation.status = Reservation.STATUS_CONFIRMED
        reservation.save()
        page = self.client.get(reverse("tours:reservation_detail", args=[reservation.reference]))
        self.assertContains(page, "confirmée")
        self.assertNotContains(page, "reservation_whatsapp")

    def test_unknown_reference_is_a_404(self):
        self.assertEqual(self.client.get("/fr/reservation/MRT-AAAAAA/").status_code, 404)
        self.assertEqual(self.client.get("/fr/reservation/MRT-AAAAAA/whatsapp/").status_code, 404)

    @override_settings(NOTIFY_EMAILS=["owner@example.com"])
    def test_owner_is_alerted_by_email_with_the_reference(self):
        self.book()
        reservation = Reservation.objects.get()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        self.assertIn(reservation.reference, mail.outbox[0].subject)

    def test_ratings_ignore_unapproved_reviews(self):
        Review.objects.create(tour=self.tour, author_name="A", rating=5, comment="Super", is_approved=True)
        Review.objects.create(tour=self.tour, author_name="B", rating=1, comment="Spam", is_approved=False)
        tour = Tour.objects.get(pk=self.tour.pk)
        self.assertEqual((tour.average_rating, tour.review_count), (5.0, 1))


class ContactAndCoordinatesTests(SiteTestCase):
    @override_settings(MAPS_URL="https://maps.example/agency", CONTACT_EMAIL="agency@example.com")
    def test_location_email_and_phone_come_from_settings(self):
        for url in (reverse("tours:home"), reverse("tours:contact")):
            html = self.client.get(url).content.decode()
            with self.subTest(url=url):
                self.assertIn('href="https://maps.example/agency" target="_blank" rel="noopener"', html)
                self.assertIn("mailto:agency@example.com", html)
                self.assertIn("tel:+212688694528", html)

    def test_contact_form_stores_message_and_hides_inactive_tours(self):
        make_tour(slug="hidden", title_fr="Circuit caché", is_active=False)
        page = self.client.get(reverse("tours:contact")).content.decode()
        self.assertNotIn("Circuit caché", page)
        response = self.client.post(
            reverse("tours:contact"), {"name": "Bob", "email": "bob@example.com", "message": "Bonjour"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_phone_numbers_are_converted_for_whatsapp(self):
        for raw in ("0688-694528", "+212 6 88 69 45 28", "00212688694528", "212688694528"):
            with self.subTest(raw=raw):
                self.assertEqual(normalize_digits(raw), "212688694528")


class SeoTests(SiteTestCase):
    def setUp(self):
        super().setUp()
        self.tour = make_tour()

    def test_pages_declare_canonical_and_every_language(self):
        html = self.client.get(self.tour.get_absolute_url()).content.decode()
        self.assertIn('rel="canonical"', html)
        for lang in LANGUAGES + ["x-default"]:
            self.assertIn(f'hreflang="{lang}"', html)

    def test_structured_data_describes_the_agency_and_the_tour(self):
        home = self.client.get(reverse("tours:home")).content.decode()
        agency = json.loads(re.search(r"ld\+json\">(.*?)</script>", home, re.S).group(1))
        self.assertEqual(agency["@type"], "TravelAgency")
        self.assertEqual(agency["hasMap"], settings.MAPS_URL)
        detail = self.client.get(self.tour.get_absolute_url()).content.decode()
        trip = json.loads(re.search(r"ld\+json\">(.*?)</script>", detail, re.S).group(1))
        self.assertEqual(trip["@type"], "TouristTrip")

    def test_sitemap_lists_tours_and_robots_points_to_it(self):
        sitemap = self.client.get("/sitemap.xml").content.decode()
        self.assertIn(self.tour.slug, sitemap)
        self.assertNotIn(settings.ADMIN_URL, sitemap)
        self.assertIn("Sitemap:", self.client.get("/robots.txt").content.decode())

    def test_filtered_listing_is_not_indexed(self):
        self.assertIn("noindex", self.client.get(reverse("tours:tour_list"), {"q": "x"}).content.decode())


class AdminTests(SiteTestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser("boss", "boss@example.com", "a-strong-pass-123")
        self.client.force_login(self.admin)
        self.tour = make_tour()

    def test_tour_form_has_one_field_per_language(self):
        html = self.client.get(f"/fr/{settings.ADMIN_URL}tours/tour/add/").content.decode()
        for lang in LANGUAGES:
            self.assertIn(f'name="title_{lang}"', html)

    def test_admin_lists_open(self):
        for model in ("tour", "category", "reservation", "contactmessage"):
            with self.subTest(model=model):
                self.assertEqual(self.client.get(f"/fr/{settings.ADMIN_URL}tours/{model}/").status_code, 200)

    def test_reservations_can_be_found_by_reference(self):
        reservation = Reservation.objects.create(
            tour=self.tour, full_name="Anna", email="a@example.com", travel_date=datetime.date.today(), adults=1
        )
        response = self.client.get(f"/fr/{settings.ADMIN_URL}tours/reservation/", {"q": reservation.reference})
        self.assertContains(response, reservation.reference)

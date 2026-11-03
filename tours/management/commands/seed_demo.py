from django.core.management.base import BaseCommand
from django.utils import translation

from tours.models import Category, Tour, Review


# (nom français, icône, nom anglais, nom espagnol)
CATEGORIES = [
    ("Excursions à la journée", "fa-mountain-sun", "Day trips", "Excursiones de un día"),
    ("Escapade de plusieurs jours", "fa-campground", "Multi-day getaways", "Escapadas de varios días"),
    ("Luxe", "fa-gem", "Luxury", "Lujo"),
    ("Lever du soleil", "fa-sun", "Sunrise", "Amanecer"),
    ("Coucher du soleil", "fa-cloud-sun", "Sunset", "Atardecer"),
    ("Sorties en quad", "fa-motorcycle", "Quad rides", "Excursiones en quad"),
]

# Traductions des circuits de démonstration, indexées par le titre français.
TRANSLATIONS = {
    "Marrakech → Merzouga : 3 jours dans le Sahara": {
        "en": {
            "title": "Marrakech → Merzouga: 3 days in the Sahara",
            "short_description": "Cross the High Atlas, visit Aït Ben Haddou and sleep in a Berber tent in the Erg Chebbi.",
            "description": (
                "A Moroccan desert classic: depart from Marrakech, cross the Tizi n'Tichka pass, visit the kasbah of "
                "Aït Ben Haddou (UNESCO), then drive to Merzouga for a camel ride at sunset and a night in a Berber "
                "camp under the stars."
            ),
            "highlights": "Tizi n'Tichka pass\nAït Ben Haddou kasbah\nCamel ride at sunset\nNight in a Berber camp\nSunrise over the dunes",
        },
        "es": {
            "title": "Marrakech → Merzouga: 3 días en el Sáhara",
            "short_description": "Cruce el Alto Atlas, visite Ait Ben Haddou y duerma en una tienda bereber en el Erg Chebbi.",
            "description": (
                "Un clásico del desierto marroquí: salida de Marrakech, paso por el puerto de Tizi n'Tichka, visita "
                "de la kasbah de Ait Ben Haddou (UNESCO) y ruta hacia Merzouga para un paseo en camello al atardecer "
                "y una noche en un campamento bereber bajo las estrellas."
            ),
            "highlights": "Puerto de Tizi n'Tichka\nKasbah de Ait Ben Haddou\nPaseo en camello al atardecer\nNoche en campamento bereber\nAmanecer sobre las dunas",
        },
    },
    "Nuit de luxe dans les dunes de l'Erg Chebbi": {
        "en": {
            "title": "Luxury night in the Erg Chebbi dunes",
            "short_description": "Private tent, gourmet dinner and personalised service in the heart of the desert.",
            "description": (
                "For those who want to experience the Sahara without giving up comfort: a luxury tent with a private "
                "bathroom, a refined Moroccan dinner under the stars, and a camel ride at sunset."
            ),
            "highlights": "Private tent with bathroom\nGourmet Moroccan dinner\nCamel ride\nStargazing",
        },
        "es": {
            "title": "Noche de lujo en las dunas del Erg Chebbi",
            "short_description": "Tienda privada, cena gastronómica y servicio personalizado en el corazón del desierto.",
            "description": (
                "Para quienes quieren vivir el Sáhara sin renunciar a la comodidad: tienda de lujo con baño privado, "
                "cena marroquí refinada bajo las estrellas y paseo en camello al atardecer."
            ),
            "highlights": "Tienda privada con baño\nCena gastronómica marroquí\nPaseo en camello\nObservación de estrellas",
        },
    },
    "Sortie quad au lever du soleil": {
        "en": {
            "title": "Quad ride at sunrise",
            "short_description": "Ride through the Erg Chebbi dunes by quad before the heat sets in.",
            "description": (
                "A morning adventure for thrill seekers: an experienced guide, recent quads, and an unforgettable "
                "sunrise over the golden dunes of the Erg Chebbi."
            ),
            "highlights": "Recent, well-maintained quads\nExperienced local guide\nSunrise over the dunes\nComplimentary mint tea",
        },
        "es": {
            "title": "Excursión en quad al amanecer",
            "short_description": "Recorra las dunas del Erg Chebbi en quad antes de que apriete el calor.",
            "description": (
                "Una aventura matinal para los amantes de las emociones: guía con experiencia, quads recientes y un "
                "amanecer inolvidable sobre las doradas dunas del Erg Chebbi."
            ),
            "highlights": "Quads recientes y bien mantenidos\nGuía local con experiencia\nAmanecer sobre las dunas\nTé a la menta de cortesía",
        },
    },
}

TOURS = [
    {
        "title": "Marrakech → Merzouga : 3 jours dans le Sahara",
        "short_description": "Traversez le Haut Atlas, visitez Aït Ben Haddou et dormez sous tente berbère dans l'Erg Chebbi.",
        "description": (
            "Un classique du désert marocain : départ de Marrakech, passage par le col de Tizi n'Tichka, "
            "visite de la kasbah d'Aït Ben Haddou (UNESCO), puis route vers Merzouga pour une balade à dos "
            "de chameau au coucher du soleil et une nuit en campement berbère sous les étoiles."
        ),
        "highlights": "Col de Tizi n'Tichka\nKasbah d'Aït Ben Haddou\nBalade à dos de chameau au coucher du soleil\nNuit en campement berbère\nLever du soleil sur les dunes",
        "duration_days": 3,
        "departure_city": "Marrakech",
        "price": 1250,
        "discount_price": 1090,
        "max_group_size": 12,
        "difficulty": "facile",
        "private_option": True,
        "is_featured": True,
        "categories": ["Escapade de plusieurs jours", "Excursions à la journée"],
    },
    {
        "title": "Nuit de luxe dans les dunes de l'Erg Chebbi",
        "short_description": "Tente privée, dîner gastronomique et service personnalisé au cœur du désert.",
        "description": (
            "Pour ceux qui veulent vivre le Sahara sans renoncer au confort : tente de luxe avec salle de bain "
            "privée, dîner marocain raffiné sous les étoiles, et balade à dos de chameau au coucher du soleil."
        ),
        "highlights": "Tente privée avec salle de bain\nDîner gastronomique marocain\nBalade à dos de chameau\nObservation des étoiles",
        "duration_days": 2,
        "departure_city": "Merzouga",
        "price": 890,
        "max_group_size": 6,
        "difficulty": "facile",
        "private_option": True,
        "is_featured": True,
        "categories": ["Luxe", "Coucher du soleil"],
    },
    {
        "title": "Sortie quad au lever du soleil",
        "short_description": "Parcourez les dunes de l'Erg Chebbi en quad avant que la chaleur ne s'installe.",
        "description": (
            "Une aventure matinale pour les amateurs de sensations : guide expérimenté, quads récents, "
            "et un lever de soleil inoubliable sur les dunes dorées de l'Erg Chebbi."
        ),
        "highlights": "Quads récents et entretenus\nGuide local expérimenté\nLever de soleil sur les dunes\nThé à la menthe offert",
        "duration_days": 1,
        "departure_city": "Merzouga",
        "price": 320,
        "max_group_size": 10,
        "difficulty": "modere",
        "private_option": False,
        "is_featured": True,
        "categories": ["Sorties en quad", "Lever du soleil", "Excursions à la journée"],
    },
]


def fill_if_empty(obj, values):
    """Remplit les champs vides (sans jamais écraser ce que vous avez saisi)."""
    changed = []
    for field, value in values.items():
        if not getattr(obj, field):
            setattr(obj, field, value)
            changed.append(field)
    if changed:
        obj.save(update_fields=changed)
    return changed


class Command(BaseCommand):
    help = "Crée des catégories et circuits de démonstration (en français, anglais et espagnol) pour Morocco Riwa Tours."

    def handle(self, *args, **options):
        with translation.override("fr"):
            cat_objs = {}
            for name, icon, name_en, name_es in CATEGORIES:
                cat, _created = Category.objects.get_or_create(name_fr=name, defaults={"name": name, "icon": icon})
                fill_if_empty(cat, {"name_fr": name, "name_en": name_en, "name_es": name_es})
                cat_objs[name] = cat

            for data in TOURS:
                data = dict(data)
                cats = data.pop("categories")
                tour, created = Tour.objects.get_or_create(title_fr=data["title"], defaults=data)
                tour.categories.set([cat_objs[c] for c in cats])

                values = {}
                for lang, fields in TRANSLATIONS.get(data["title"], {}).items():
                    values.update({f"{field}_{lang}": text for field, text in fields.items()})
                values.update({"departure_city_en": data["departure_city"], "departure_city_es": data["departure_city"]})
                fill_if_empty(tour, values)

                if created:
                    Review.objects.create(
                        tour=tour, author_name="Sophie", rating=5,
                        comment="Une expérience magique, guide très professionnel et attentionné !"
                    )
                    self.stdout.write(self.style.SUCCESS(f"Créé : {tour.title_fr}"))
                else:
                    self.stdout.write(f"Déjà existant (traductions complétées si vides) : {tour.title_fr}")

        self.stdout.write(self.style.SUCCESS("Données de démonstration prêtes."))

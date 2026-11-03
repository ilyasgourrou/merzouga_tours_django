import secrets
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """Type de circuit : excursion à la journée, luxe, plusieurs jours, etc."""
    name = models.CharField("Nom", max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(
        "Icône (classe Font Awesome)", max_length=50, blank=True,
        help_text="Nom d'une icône gratuite de Font Awesome, ex : fa-sun, fa-campground, fa-gem. "
                  "Liste : fontawesome.com/search?ic=free"
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def icon_classes(self):
        """Classes CSS de l'icône Font Awesome (style « solid »), ou "" si le champ n'en contient pas.

        Accepte « fa-sun », « fa-solid fa-sun » ou « fas fa-sun ».
        """
        style_tokens = {"fa-solid", "fa-regular", "fa-brands", "fas", "far", "fab"}
        tokens = [t for t in (self.icon or "").split() if t not in style_tokens]
        if not any(t.startswith("fa-") for t in tokens):
            return ""
        return "fa-solid " + " ".join(tokens)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tour(models.Model):
    """Un circuit / une activité proposée par l'agence."""

    DIFFICULTY_CHOICES = [
        ("facile", _("Facile")),
        ("modere", _("Modéré")),
        ("difficile", _("Difficile")),
    ]

    title = models.CharField("Titre", max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    categories = models.ManyToManyField(Category, related_name="tours", verbose_name="Catégories")
    short_description = models.CharField("Description courte", max_length=300)
    description = models.TextField("Description complète")
    highlights = models.TextField(
        "Temps forts", blank=True,
        help_text="Un point par ligne, affiché sous forme de liste."
    )
    duration_days = models.PositiveSmallIntegerField("Durée (jours)", default=1)
    departure_city = models.CharField("Ville de départ", max_length=100, default="Marrakech")
    price = models.DecimalField("Prix (MAD)", max_digits=8, decimal_places=2)
    discount_price = models.DecimalField(
        "Prix promo (MAD)", max_digits=8, decimal_places=2, null=True, blank=True
    )
    max_group_size = models.PositiveSmallIntegerField("Taille max du groupe", default=12)
    difficulty = models.CharField("Difficulté", max_length=20, choices=DIFFICULTY_CHOICES, default="facile")
    private_option = models.BooleanField("Option privée disponible", default=False)
    cover_image = models.ImageField("Photo principale", upload_to="tours/covers/", blank=True, null=True)
    is_featured = models.BooleanField("Mis en avant sur l'accueil", default=False)
    is_active = models.BooleanField("Actif / publié", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Circuit"
        verbose_name_plural = "Circuits"
        ordering = ["-is_featured", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("tours:tour_detail", kwargs={"slug": self.slug})

    @property
    def highlight_list(self):
        return [h.strip() for h in self.highlights.splitlines() if h.strip()]

    @property
    def approved_reviews(self):
        return [r for r in self.reviews.all() if r.is_approved]

    @property
    def average_rating(self):
        reviews = self.approved_reviews
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        return len(self.approved_reviews)


class TourImage(models.Model):
    """Photos supplémentaires pour la galerie d'un circuit."""
    tour = models.ForeignKey(Tour, related_name="gallery_images", on_delete=models.CASCADE)
    image = models.ImageField("Image", upload_to="tours/gallery/")
    caption = models.CharField("Légende", max_length=200, blank=True)

    class Meta:
        verbose_name = "Photo de galerie"
        verbose_name_plural = "Photos de galerie"

    def __str__(self):
        return f"Photo — {self.tour.title}"


class Review(models.Model):
    """Avis client sur un circuit."""
    tour = models.ForeignKey(Tour, related_name="reviews", on_delete=models.CASCADE)
    author_name = models.CharField("Nom", max_length=100)
    rating = models.PositiveSmallIntegerField("Note (1 à 5)")
    comment = models.TextField("Commentaire")
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField("Approuvé", default=True)

    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author_name} — {self.tour.title} ({self.rating}/5)"


class ContactMessage(models.Model):
    """Message envoyé via le formulaire de contact / demande de réservation."""
    name = models.CharField("Nom", max_length=100)
    email = models.EmailField("Email")
    phone = models.CharField("Téléphone", max_length=30, blank=True)
    tour = models.ForeignKey(
        Tour, related_name="inquiries", on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Circuit concerné"
    )
    message = models.TextField("Message")
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField("Traité", default=False)

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.created_at:%d/%m/%Y}"


class Reservation(models.Model):
    """Demande de réservation d'un circuit (indépendante des messages de contact)."""

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_CONFIRMED, "Confirmée"),
        (STATUS_CANCELLED, "Annulée"),
    ]

    tour = models.ForeignKey(
        Tour, related_name="reservations", on_delete=models.PROTECT, verbose_name="Circuit"
    )
    full_name = models.CharField("Nom complet", max_length=100)
    email = models.EmailField("Email")
    phone = models.CharField("Téléphone", max_length=30, blank=True)
    travel_date = models.DateField("Date souhaitée")
    adults = models.PositiveSmallIntegerField("Adultes", default=1)
    children = models.PositiveSmallIntegerField("Enfants", default=0)
    is_private = models.BooleanField("Circuit privé", default=False)
    notes = models.TextField("Remarques", blank=True)
    status = models.CharField("Statut", max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    internal_note = models.TextField(
        "Note interne", blank=True, help_text="Visible uniquement dans l'admin."
    )
    total_price = models.DecimalField(
        "Total estimé (MAD)", max_digits=10, decimal_places=2, null=True, blank=True, editable=False
    )
    reference = models.CharField(
        "Référence", max_length=16, unique=True, editable=False,
        help_text="Code unique envoyé par le client sur WhatsApp pour confirmer sa réservation.",
    )
    whatsapp_clicked_at = models.DateTimeField(
        "WhatsApp ouvert le", null=True, blank=True, editable=False,
        help_text="Date à laquelle le client a appuyé sur le bouton « Confirmer sur WhatsApp ».",
    )
    created_at = models.DateTimeField("Reçue le", auto_now_add=True)

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.tour.title} ({self.travel_date:%d/%m/%Y})"

    @property
    def travelers(self):
        return self.adults + self.children

    @property
    def is_whatsapp_opened(self):
        return self.whatsapp_clicked_at is not None

    @staticmethod
    def generate_reference():
        # Alphabet sans caractères ambigus (pas de 0/O ni 1/I) pour éviter les erreurs de saisie.
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        while True:
            code = "MRT-" + "".join(secrets.choice(alphabet) for _ in range(6))
            if not Reservation.objects.filter(reference=code).exists():
                return code

    def save(self, *args, **kwargs):
        # Calcul du total à la création uniquement (les enfants ne comptent pas dans le prix ici :
        # à adapter si l'agence applique un tarif enfant).
        if not self.reference:
            self.reference = self.generate_reference()
        if self.total_price is None and self.tour_id:
            unit = self.tour.discount_price or self.tour.price
            self.total_price = unit * self.adults
        super().save(*args, **kwargs)

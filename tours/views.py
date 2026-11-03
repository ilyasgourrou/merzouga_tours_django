from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.urls import reverse

from .models import Tour, Category, Reservation
from .forms import ContactForm, ReservationForm
from .notifications import notify_staff
from .whatsapp import whatsapp_number, whatsapp_url


def home(request):
    featured_tours = Tour.objects.filter(is_active=True, is_featured=True)[:6]
    if featured_tours.count() < 3:
        featured_tours = Tour.objects.filter(is_active=True)[:6]
    categories = Category.objects.all()
    return render(request, "tours/home.html", {
        "featured_tours": featured_tours,
        "categories": categories,
    })


def tour_list(request):
    tours = Tour.objects.filter(is_active=True)
    categories = Category.objects.all()

    category_slug = request.GET.get("category")
    if category_slug:
        tours = tours.filter(categories__slug=category_slug)

    query = request.GET.get("q")
    if query:
        # Cherche dans le titre et la description courte, dans toutes les langues
        search = Q()
        for code in dict(settings.LANGUAGES):
            search |= Q(**{f"title_{code}__icontains": query}) | Q(**{f"short_description_{code}__icontains": query})
        tours = tours.filter(search)

    duration = request.GET.get("duration")
    if duration == "1":
        tours = tours.filter(duration_days=1)
    elif duration == "2-3":
        tours = tours.filter(duration_days__gte=2, duration_days__lte=3)
    elif duration == "4+":
        tours = tours.filter(duration_days__gte=4)

    tours = tours.distinct()

    return render(request, "tours/tour_list.html", {
        "tours": tours,
        "categories": categories,
        "active_category": category_slug,
        "query": query or "",
    })


def tour_detail(request, slug):
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    related_tours = Tour.objects.filter(
        is_active=True, categories__in=tour.categories.all()
    ).exclude(pk=tour.pk).distinct()[:3]

    if request.method == "POST":
        form = ReservationForm(request.POST, tour=tour)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.tour = tour
            reservation.save()
            _notify_reservation(request, reservation)
            return redirect("tours:reservation_detail", reference=reservation.reference)
    else:
        form = ReservationForm(tour=tour)

    return render(request, "tours/tour_detail.html", {
        "tour": tour,
        "related_tours": related_tours,
        "form": form,
    })


def _notify_reservation(request, reservation):
    tour = reservation.tour
    notify_staff(
        f"Nouvelle réservation {reservation.reference} : {tour.title} le {reservation.travel_date:%d/%m/%Y}",
        (
            f"Référence : {reservation.reference}\n"
            f"Le client doit maintenant confirmer sur WhatsApp en envoyant ce code.\n\n"
            f"Client : {reservation.full_name}\n"
            f"Email : {reservation.email}\n"
            f"Téléphone : {reservation.phone or '-'}\n"
            f"Circuit : {tour.title}\n"
            f"Date souhaitée : {reservation.travel_date:%d/%m/%Y}\n"
            f"Personnes : {reservation.adults} adulte(s), {reservation.children} enfant(s)\n"
            f"Circuit privé : {'oui' if reservation.is_private else 'non'}\n"
            f"Total estimé : {reservation.total_price} MAD\n\n"
            f"Remarques :\n{reservation.notes or '-'}\n\n"
            f"Gérer : {request.build_absolute_uri(reverse('admin:tours_reservation_change', args=[reservation.pk]))}"
        ),
        reply_to=reservation.email,
    )


def reservation_detail(request, reference):
    """Page affichée après la réservation : référence unique + bouton « Confirmer sur WhatsApp »."""
    reservation = get_object_or_404(Reservation.objects.select_related("tour"), reference=reference)
    return render(request, "tours/reservation_detail.html", {
        "reservation": reservation,
        "whatsapp_ready": bool(whatsapp_number()),
    })


def reservation_whatsapp(request, reference):
    """Note que le client a ouvert WhatsApp, puis l'y envoie avec le message déjà écrit."""
    reservation = get_object_or_404(Reservation.objects.select_related("tour"), reference=reference)
    if reservation.whatsapp_clicked_at is None:
        reservation.whatsapp_clicked_at = timezone.now()
        reservation.save(update_fields=["whatsapp_clicked_at"])
    return redirect(whatsapp_url(reservation))


def about(request):
    return render(request, "tours/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            message = form.save()
            notify_staff(
                f"Nouveau message de {message.name}",
                (
                    f"De : {message.name} <{message.email}>\n"
                    f"Téléphone : {message.phone or '-'}\n"
                    f"Circuit concerné : {message.tour or '-'}\n\n"
                    f"{message.message}"
                ),
                reply_to=message.email,
            )
            messages.success(request, _("Merci ! Votre message a bien été envoyé, nous vous répondrons rapidement."))
            return redirect("tours:contact")
    else:
        form = ContactForm()
    return render(request, "tours/contact.html", {"form": form})


def robots_txt(request):
    base = settings.SITE_URL or f"{request.scheme}://{request.get_host()}"
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /i18n/",
        "",
        f"Sitemap: {base}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")

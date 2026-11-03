from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import ContactMessage, Reservation, Tour


class SpamGuardForm(forms.ModelForm):
    """Champ piège invisible : les robots le remplissent, les humains non."""
    website = forms.CharField(
        required=False, label="",
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam détecté.")
        return ""


class ContactForm(SpamGuardForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ne proposer que les circuits publiés
        self.fields["tour"].queryset = Tour.objects.filter(is_active=True)

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "tour", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": _("Votre nom"), "class": "form-input"}),
            "email": forms.EmailInput(attrs={"placeholder": _("Votre email"), "class": "form-input"}),
            "phone": forms.TextInput(attrs={"placeholder": _("Téléphone (optionnel)"), "class": "form-input"}),
            "tour": forms.Select(attrs={"class": "form-input"}),
            "message": forms.Textarea(attrs={"placeholder": _("Votre message"), "class": "form-input", "rows": 5}),
        }
        labels = {
            "tour": _("Circuit concerné (optionnel)"),
        }


class ReservationForm(SpamGuardForm):
    """Formulaire de réservation sur la fiche d'un circuit (le circuit est fixé par la vue)."""

    class Meta:
        model = Reservation
        fields = ["full_name", "email", "phone", "travel_date", "adults", "children", "is_private", "notes"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": _("Votre nom"), "class": "form-input"}),
            "email": forms.EmailInput(attrs={"placeholder": _("Votre email"), "class": "form-input"}),
            "phone": forms.TextInput(attrs={"placeholder": _("Téléphone (optionnel)"), "class": "form-input"}),
            "travel_date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "adults": forms.NumberInput(attrs={"min": 1, "max": 50, "class": "form-input"}),
            "children": forms.NumberInput(attrs={"min": 0, "max": 50, "class": "form-input"}),
            "notes": forms.Textarea(attrs={"placeholder": _("Une demande particulière ?"), "class": "form-input", "rows": 3}),
        }

    def __init__(self, *args, tour=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tour = tour
        self.fields["travel_date"].widget.attrs["min"] = timezone.localdate().isoformat()
        if tour is not None and not tour.private_option:
            del self.fields["is_private"]

    def clean_travel_date(self):
        d = self.cleaned_data["travel_date"]
        if d < timezone.localdate():
            raise forms.ValidationError(_("La date doit être dans le futur."))
        return d

    def clean_adults(self):
        n = self.cleaned_data["adults"]
        if n < 1:
            raise forms.ValidationError(_("Au moins un adulte."))
        return n

    def clean(self):
        data = super().clean()
        if self.tour is not None and data.get("adults") is not None:
            total = data["adults"] + (data.get("children") or 0)
            if total > self.tour.max_group_size and not data.get("is_private"):
                raise forms.ValidationError(
                    _("Le groupe dépasse la taille maximale de ce circuit (%(n)s personnes).") % {"n": self.tour.max_group_size}
                )
        return data

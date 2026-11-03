from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from .models import Category, Tour, TourImage, Review, ContactMessage, Reservation


class TourImageInline(TranslationTabularInline):
    model = TourImage
    extra = 1


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0


@admin.register(Category)
class CategoryAdmin(TabbedTranslationAdmin):
    list_display = ("name", "slug", "icon")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tour)
class TourAdmin(TabbedTranslationAdmin):
    list_display = ("title", "departure_city", "duration_days", "price", "is_featured", "is_active")
    list_filter = ("categories", "difficulty", "is_featured", "is_active")
    search_fields = ("title", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories",)
    inlines = [TourImageInline, ReviewInline]

    @property
    def media(self):
        media = super().media
        if settings.ADMIN_UPLOAD_LIMIT:  # hébergeur qui limite la taille des envois (Vercel : 4,5 Mo)
            media += forms.Media(js=["js/admin_upload_limit.js"])
        return media


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "tour", "created_at", "handled")
    list_filter = ("handled", "created_at")
    search_fields = ("name", "email", "message")


class WhatsappOpenedFilter(admin.SimpleListFilter):
    title = "WhatsApp ouvert"
    parameter_name = "whatsapp"

    def lookups(self, request, model_admin):
        return [("yes", "Oui"), ("no", "Non")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(whatsapp_clicked_at__isnull=False)
        if self.value() == "no":
            return queryset.filter(whatsapp_clicked_at__isnull=True)
        return queryset


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("reference", "full_name", "tour", "travel_date", "travelers_count", "status_badge", "whatsapp_ok", "total_price", "created_at")
    list_display_links = ("reference", "full_name")
    list_filter = ("status", WhatsappOpenedFilter, "tour", "travel_date", "is_private")
    search_fields = ("reference", "full_name", "email", "phone", "tour__title")
    date_hierarchy = "travel_date"
    list_select_related = ("tour",)
    readonly_fields = ("reference", "created_at", "total_price", "whatsapp_clicked_at")
    actions = ["mark_confirmed", "mark_cancelled"]
    fieldsets = (
        ("Client", {"fields": ("reference", "full_name", "email", "phone")}),
        ("Séjour", {"fields": ("tour", "travel_date", "adults", "children", "is_private", "notes")}),
        ("Suivi", {"fields": ("status", "whatsapp_clicked_at", "total_price", "internal_note", "created_at")}),
    )

    COLORS = {
        Reservation.STATUS_PENDING: "#b9770e",
        Reservation.STATUS_CONFIRMED: "#1e8449",
        Reservation.STATUS_CANCELLED: "#a93226",
    }

    @admin.display(description="Personnes")
    def travelers_count(self, obj):
        return f"{obj.adults} ad. + {obj.children} enf." if obj.children else f"{obj.adults} ad."

    @admin.display(description="WhatsApp ouvert", boolean=True, ordering="whatsapp_clicked_at")
    def whatsapp_ok(self, obj):
        return obj.is_whatsapp_opened

    @admin.display(description="Statut", ordering="status")
    def status_badge(self, obj):
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:10px;font-size:11px;">{}</span>',
            self.COLORS.get(obj.status, "#555"), obj.get_status_display(),
        )

    @admin.action(description="Marquer comme confirmées")
    def mark_confirmed(self, request, queryset):
        n = queryset.update(status=Reservation.STATUS_CONFIRMED)
        self.message_user(request, f"{n} réservation(s) confirmée(s).")

    @admin.action(description="Marquer comme annulées")
    def mark_cancelled(self, request, queryset):
        n = queryset.update(status=Reservation.STATUS_CANCELLED)
        self.message_user(request, f"{n} réservation(s) annulée(s).")


admin.site.site_header = "Morocco Riwa Tours"
admin.site.site_title = "Morocco Riwa Tours"
admin.site.index_title = "Administration du site"

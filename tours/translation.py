from modeltranslation.translator import TranslationOptions, register

from .models import Category, Tour, TourImage


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Tour)
class TourTranslationOptions(TranslationOptions):
    fields = ("title", "short_description", "description", "highlights", "departure_city")


@register(TourImage)
class TourImageTranslationOptions(TranslationOptions):
    fields = ("caption",)

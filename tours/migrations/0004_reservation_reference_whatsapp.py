import secrets

from django.db import migrations, models


def fill_references(apps, schema_editor):
    Reservation = apps.get_model("tours", "Reservation")
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    used = set()
    for reservation in Reservation.objects.filter(reference__isnull=True):
        while True:
            code = "MRT-" + "".join(secrets.choice(alphabet) for _ in range(6))
            if code not in used:
                used.add(code)
                break
        reservation.reference = code
        reservation.save(update_fields=["reference"])


class Migration(migrations.Migration):

    dependencies = [
        ("tours", "0003_category_icon_fontawesome"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="reference",
            field=models.CharField(editable=False, max_length=16, null=True, verbose_name="Référence"),
        ),
        migrations.AddField(
            model_name="reservation",
            name="whatsapp_clicked_at",
            field=models.DateTimeField(
                blank=True, editable=False, null=True, verbose_name="WhatsApp ouvert le",
                help_text="Date à laquelle le client a appuyé sur le bouton « Confirmer sur WhatsApp ».",
            ),
        ),
        migrations.RunPython(fill_references, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="reservation",
            name="reference",
            field=models.CharField(
                editable=False, max_length=16, unique=True, verbose_name="Référence",
                help_text="Code unique envoyé par le client sur WhatsApp pour confirmer sa réservation.",
            ),
        ),
    ]

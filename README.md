# Morocco Riwa Tours — site Django

Site vitrine d'une agence de circuits au Maroc (Merzouga, Erg Chebbi), en français, anglais et espagnol :
accueil, liste de circuits avec filtres, fiche détaillée avec réservation, à propos, contact.
Chaque réservation reçoit un code unique que le client envoie sur WhatsApp pour confirmer.

## Démarrage rapide (sur votre PC)

```powershell
python -m venv venv
venv\Scripts\activate            # Mac/Linux : source venv/bin/activate
python -m pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo       # 3 circuits d'exemple traduits + catégories
python manage.py runserver
```

- Le site : http://127.0.0.1:8000/
- L'admin : http://127.0.0.1:8000/fr/admin/ (ou `/fr/` + votre `DJANGO_ADMIN_URL`)
- Les tests automatiques : `python manage.py test`
- Les vérifications avant mise en ligne : `python manage.py check --deploy`

## Où modifier quoi

| Je veux changer... | Où |
|---|---|
| Téléphone, WhatsApp, email de contact, lien Google Maps, nom du site | `merzouga_config/settings.py`, section 2, ou variables `DJANGO_CONTACT_PHONE`, `DJANGO_WHATSAPP_NUMBER`, `DJANGO_CONTACT_EMAIL`, `DJANGO_MAPS_URL` (voir `.env.example`) |
| Circuits, catégories, photos, prix, réservations | l'admin (titres et descriptions en 3 langues, onglets par champ) |
| Textes fixes du site (menus, boutons, formulaires) | `locale/en/LC_MESSAGES/django.po` et `locale/es/...`, puis `python manage.py compilemessages` |
| Couleurs, tailles, mise en page | `static/css/style.css` (les couleurs sont des variables en haut du fichier) |
| Menu mobile, bouton « copier le code » | `static/js/main.js` |
| Logo, favicons, image de partage | `static/img/` |
| Structure d'une page | `templates/` (`base.html` = en-tête et pied de page, `tours/` = pages) |
| Message WhatsApp envoyé par le client | `tours/whatsapp.py` |
| Alertes email envoyées à l'agence | `tours/notifications.py` et `tours/views.py` |
| Langues du site | `LANGUAGES` dans `settings.py` + un dossier dans `locale/` |
| Référencement Google (sitemap, hreflang, données structurées) | `tours/sitemaps.py`, `tours/templatetags/seo_tags.py`, `base.html` |
| Avertissements avant mise en ligne | `tours/checks.py` |

## Structure du projet

- `merzouga_config/` : configuration Django (`settings.py` organisé en 10 sections, `urls.py`).
- `tours/` : l'application.
  - `models.py` : `Category`, `Tour`, `TourImage`, `Review`, `ContactMessage`, `Reservation`.
  - `translation.py` : champs traduits (django-modeltranslation).
  - `views.py`, `urls.py`, `forms.py` : pages, adresses, formulaires (avec champ anti-spam).
  - `admin.py` : administration (onglets de langue, filtres, actions sur les réservations).
  - `whatsapp.py` : numéro, message et lien WhatsApp.
  - `tests.py` : tests automatiques.
  - `management/commands/seed_demo.py` : données d'exemple.
- `templates/` : pages HTML. `templates/includes/lang_switch.html` est le sélecteur de langue.
- `static/` : CSS, JavaScript, images, Font Awesome Free (`static/vendor/fontawesome/`, hébergé en local).
- `locale/` : traductions du texte fixe (anglais, espagnol).

## Fonctionnement en bref

**Langues.** Les adresses commencent par la langue (`/fr/`, `/en/`, `/es/`). Le visiteur arrive dans la langue de son navigateur.
Les circuits et catégories se saisissent dans les trois langues dans l'admin. Si une traduction est vide, le français est affiché.
Pour modifier un texte fixe : changez le `msgstr` dans le fichier `.po`, puis `python manage.py compilemessages`.
Pour un nouveau texte, entourez-le de `{% trans "..." %}` dans le template et lancez `python manage.py makemessages -l en -l es`.

**Réservation.** Le client remplit le formulaire d'un circuit, reçoit un code `MRT-XXXXXX` et un bouton « Confirmer sur WhatsApp »
qui ouvre WhatsApp avec un message prêt à envoyer. Dans l'admin, cherchez le code dans Réservations
et passez la réservation en « Confirmée ». La page du client affiche alors le nouveau statut.

**Icônes.** Font Awesome Free 6.7.2 (licence dans `static/vendor/fontawesome/LICENSE.txt`).
Dans les templates : `<i class="fa-solid fa-compass" aria-hidden="true"></i>`. Les catégories ont un champ « Icône » dans l'admin
(par exemple `fa-sun`, liste sur https://fontawesome.com/search?ic=free). Les icônes Pro ne s'afficheront pas.

**Responsive.** Mobile jusqu'à 767 px, tablette 768 à 1023 px, ordinateur dès 1024 px (section RESPONSIVE de `style.css`).
Sous 1024 px la navigation passe dans un menu burger ; sous 640 px le sélecteur de langue et le bouton Réserver sont dans ce menu.

**Sécurité de l'admin.** L'adresse se règle avec `DJANGO_ADMIN_URL`. `django-axes` bloque une connexion après 5 échecs pendant 1 heure
(`python manage.py axes_reset` pour débloquer). Avec `DJANGO_DEBUG=False`, HTTPS et cookies sécurisés sont activés,
et le site refuse de démarrer si la clé secrète n'est pas définie.

## Mise en ligne

- Vercel : `DEPLOY_VERCEL.md` (base PostgreSQL et stockage des photos externes obligatoires).
- Hébergement classique (PythonAnywhere, VPS) : `DEPLOY.md`.
- Variables d'environnement : `.env.example`.

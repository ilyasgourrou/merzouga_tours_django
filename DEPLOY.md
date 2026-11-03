# Mettre le site en ligne

Vous voulez utiliser Vercel ? Lisez plutôt `DEPLOY_VERCEL.md`. Ce guide-ci concerne un hébergement classique avec disque permanent.

Ce guide suppose un hébergement Django classique. L'exemple détaillé est PythonAnywhere
(le plus simple pour débuter, disque persistant, HTTPS inclus). Les mêmes variables
fonctionnent sur un VPS ou ailleurs.

## 1. Avant de commencer

1. Copiez `.env.example` en `.env` et remplissez-le (clé secrète, domaine, vrai téléphone, numéro WhatsApp, vraie adresse email).
2. Vérifiez la configuration : `python manage.py check --deploy`
   Les avertissements `tours.W001` à `tours.W003` vous rappellent ce qui reste à remplir.
   Les avertissements `security.W005` et `security.W021` (HSTS) peuvent attendre.

## 2. PythonAnywhere, pas à pas

1. Créez un compte sur pythonanywhere.com. Le compte gratuit donne une adresse en
   `votrenom.pythonanywhere.com`. Un nom de domaine personnalisé demande un plan payant.
2. Onglet Files : envoyez le zip du projet, puis dans une console Bash :
   ```bash
   unzip merzouga_tours_django.zip -d merzouga_tours_django
   cd merzouga_tours_django
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env     # puis éditez .env dans l'onglet Files
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```
3. Onglet Web, Add a new web app, choisissez Manual configuration (même version de Python que le venv).
   - Source code et Working directory : le dossier du projet.
   - Virtualenv : `/home/VOTRENOM/merzouga_tours_django/venv`
   - Ouvrez le fichier WSGI et remplacez son contenu par :
     ```python
     import os, sys
     path = '/home/VOTRENOM/merzouga_tours_django'
     if path not in sys.path:
         sys.path.append(path)
     os.environ['DJANGO_SETTINGS_MODULE'] = 'merzouga_config.settings'
     from django.core.wsgi import get_wsgi_application
     application = get_wsgi_application()
     ```
   - Activez Force HTTPS.
4. Cliquez sur Reload. Le site est en ligne.
5. Dans `.env`, `DJANGO_ALLOWED_HOSTS` doit contenir `votrenom.pythonanywhere.com` (ou votre domaine) et `DJANGO_BEHIND_PROXY=True`.

Sur le compte gratuit, l'accès Internet sortant est restreint : l'envoi d'emails peut ne pas marcher.

## 3. Le nom de domaine moroccoriwatours.com

Achetez-le chez un registrar (un `.com` est plus simple à retenir pour des voyageurs étrangers),
puis suivez la documentation de votre hébergeur pour le relier au site (enregistrement CNAME ou A).
Dans `.env`, mettez :

```
DJANGO_ALLOWED_HOSTS=moroccoriwatours.com,www.moroccoriwatours.com
DJANGO_SITE_URL=https://moroccoriwatours.com
```

`DJANGO_SITE_URL` indique à Google l'adresse officielle (sans `www`). Chez votre hébergeur ou registrar,
faites une redirection de `www.moroccoriwatours.com` vers `moroccoriwatours.com` pour n'avoir qu'une seule adresse.
Pour avoir des emails en `@moroccoriwatours.com`, il faut une boîte mail liée au domaine (chez le registrar ou un service de messagerie).

## 4. Accéder à l'administration en ligne

L'admin n'a pas de lien sur le site. Son adresse est :

```
https://moroccoriwatours.com/fr/<DJANGO_ADMIN_URL>
```

Par exemple, avec `DJANGO_ADMIN_URL=gestion-x7k2/` : `https://moroccoriwatours.com/fr/gestion-x7k2/`.
Remplacez `/fr/` par `/en/` ou `/es/` pour avoir l'interface de l'admin dans une autre langue.

- Le compte se crée une seule fois sur le serveur avec `python manage.py createsuperuser`.
- Mettez l'adresse dans vos favoris et ne la partagez pas. L'ancienne adresse `/admin/` renvoie une erreur 404.
- Les touristes ne voient jamais l'admin. Ils utilisent seulement le site public, les formulaires de réservation et de contact.
- Vous y retrouvez les circuits, les réservations (statut En attente, Confirmée, Annulée) et les messages de contact.

### Ajouter un circuit dans les trois langues

Dans Circuits, chaque texte (titre, description courte, description complète, temps forts, ville de départ) et chaque nom de catégorie
a trois onglets : Français, English, Español. Seul le français est obligatoire. Si une traduction est vide,
le site affiche le français à la place. L'adresse (slug) du circuit reste unique et ne change pas selon la langue.

### Comment une réservation est confirmée (WhatsApp)

1. Le client remplit le formulaire sur la fiche d'un circuit. La réservation reçoit un code unique du type `MRT-7K3Q9X`.
2. Il arrive sur une page qui affiche ce code et un bouton vert « Confirmer sur WhatsApp ». Le bouton ouvre WhatsApp
   avec un message déjà écrit (code, nom, circuit, date, voyageurs, total) à destination de `DJANGO_WHATSAPP_NUMBER`.
3. Vous recevez le message sur WhatsApp. Dans l'admin, ouvrez Réservations et collez le code dans la barre de recherche.
4. Passez la réservation en « Confirmée » (menu Action ou fiche). La page du client affiche alors « Votre réservation est confirmée ».

Dans la liste, la colonne « WhatsApp ouvert » (coche verte) indique que le client a appuyé sur le bouton. Cela ne prouve pas
qu'il a envoyé le message : une réservation reste « En attente » tant que vous n'avez pas reçu son message avec le code.
- Après 5 mauvais mots de passe, l'accès est bloqué 1 heure. Pour débloquer : `python manage.py axes_reset`.
- Si `DJANGO_NOTIFY_EMAIL` est rempli, vous recevez un email à chaque réservation avec le lien direct vers la fiche dans l'admin.

## 5. Être trouvé sur Google

1. Ouvrez Google Search Console, ajoutez votre domaine et envoyez `https://moroccoriwatours.com/sitemap.xml`
   (déjà généré, avec les 3 langues et les liens hreflang).
2. Créez une fiche Google Business Profile pour l'agence (adresse à Merzouga, photos, horaires, lien du site).
3. Remplissez bien chaque circuit : titre clair, description courte (elle devient la description Google), photo principale, description complète.
4. Gardez le site à jour : un circuit désactivé disparaît du sitemap.

## 6. Après la mise en ligne

- Sauvegardez régulièrement `db.sqlite3` (réservations et messages) et le dossier `media/` (photos).
- Quand vous modifiez le code : envoyez les fichiers, puis `pip install -r requirements.txt`,
  `python manage.py migrate`, `python manage.py collectstatic --noinput` et rechargez le site.
- Quand le HTTPS fonctionne bien, mettez `DJANGO_HSTS_SECONDS=31536000` dans `.env`.

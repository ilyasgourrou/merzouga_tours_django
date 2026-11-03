# Mettre Morocco Riwa Tours en ligne sur Vercel

Vercel sait faire tourner Django, mais il fonctionne différemment d'un hébergement classique. Quatre points à connaître avant de commencer.

1. **Pas de disque permanent.** Le fichier `db.sqlite3` et le dossier `media/` ne survivent pas. Il faut donc une base de données externe (PostgreSQL) et un stockage externe pour les photos. Le site refuse de démarrer sur Vercel sans ces deux éléments.
2. **Le plan gratuit (Hobby) interdit l'usage commercial.** Une agence de circuits est une activité commerciale : il faut le plan Pro de Vercel (20 $ par mois et par utilisateur au moment où j'écris, à vérifier sur vercel.com/pricing).
3. **Chaque envoi est limité à 4,5 Mo.** Quand vous ajoutez des photos dans l'admin, tout le formulaire (toutes les photos ensemble) doit rester sous cette taille. L'admin vous prévient avant d'envoyer si vous dépassez 4 Mo.
4. **On ne peut pas ouvrir de terminal sur Vercel.** La création de la base et de votre compte admin se fait depuis votre PC (étape 6).

Si ces contraintes ne vous conviennent pas, `DEPLOY.md` explique PythonAnywhere, plus simple pour ce projet.

## 1. Les comptes

- GitHub (envoie le code à Vercel) : github.com
- Supabase (base PostgreSQL et stockage des photos, un seul compte pour les deux) : supabase.com
- Vercel (hébergement) : vercel.com. Prenez le plan Pro.

## 2. Supabase : base de données et photos

Les menus de Supabase changent parfois. Si un nom ne correspond pas exactement, cherchez le mot équivalent.

1. Créez un projet. Notez le mot de passe de la base, il ne sera plus affiché.
2. Base de données : bouton **Connect** en haut du projet, puis la chaîne de connexion **Transaction pooler** (port 6543). Remplacez `[YOUR-PASSWORD]` par votre mot de passe. Cette chaîne est votre `DATABASE_URL`.
3. Photos : menu **Storage**, créez un bucket nommé `media` et cochez **Public bucket**.
4. Toujours dans Storage, ouvrez les réglages **S3** : activez la connexion S3, notez l'**Endpoint** et la **Region**, puis cliquez **New access key** et notez l'Access key ID et le Secret (affiché une seule fois).
5. L'adresse publique des photos est : `VOTRE-REF.supabase.co/storage/v1/object/public/media` (`VOTRE-REF` est la partie avant `.supabase.co` dans l'adresse de votre projet).

## 3. Envoyer le projet sur GitHub

Dans PowerShell, dans le dossier du projet :

```powershell
git init
git add .
git commit -m "Morocco Riwa Tours"
git branch -M main
git remote add origin https://github.com/VOTRE-COMPTE/morocco-riwa-tours.git
git push -u origin main
```

Créez d'abord le dépôt vide sur github.com (en privé de préférence). Le fichier `.gitignore` empêche d'envoyer `.env`, `venv`, la base locale et les photos de test.

## 4. Vercel : importer le projet

1. Sur vercel.com : **Add New**, **Project**, choisissez le dépôt GitHub.
2. Vercel reconnaît Django tout seul (il trouve `manage.py`) et lance `collectstatic` pendant le déploiement.
3. Avant de cliquer sur Deploy, ouvrez **Environment Variables** et ajoutez :

| Variable | Valeur |
|---|---|
| `DJANGO_DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | une longue clé secrète (générez-la avec `python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `DJANGO_ALLOWED_HOSTS` | `moroccoriwatours.com,www.moroccoriwatours.com,.vercel.app` |
| `DJANGO_SITE_URL` | `https://moroccoriwatours.com` |
| `DJANGO_ADMIN_URL` | une adresse secrète, par exemple `gestion-x7k2/` |
| `DATABASE_URL` | la chaîne Transaction pooler de Supabase |
| `DJANGO_S3_BUCKET` | `media` |
| `DJANGO_S3_ENDPOINT` | l'Endpoint S3 de Supabase |
| `DJANGO_S3_REGION` | la Region S3 de Supabase |
| `DJANGO_S3_ACCESS_KEY` | l'Access key ID |
| `DJANGO_S3_SECRET_KEY` | le Secret |
| `DJANGO_S3_PUBLIC_DOMAIN` | `VOTRE-REF.supabase.co/storage/v1/object/public/media` |
| `DJANGO_NOTIFY_EMAIL` | (facultatif) l'adresse qui reçoit les alertes de réservation, avec `DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_USER` et `DJANGO_EMAIL_PASSWORD` pour l'envoi (mot de passe d'application Gmail) |

Le téléphone et WhatsApp (0688-694528), l'email de contact (riwatoursmorocco@gmail.com) et le lien Google Maps sont déjà dans le projet. Pour les changer, ajoutez `DJANGO_CONTACT_PHONE`, `DJANGO_WHATSAPP_NUMBER`, `DJANGO_CONTACT_EMAIL` ou `DJANGO_MAPS_URL`.

4. Cliquez **Deploy**. Si le déploiement échoue, le message du journal de build dit quelle variable manque.

## 5. Le nom de domaine

Dans le projet Vercel : **Settings**, **Domains**, ajoutez `moroccoriwatours.com` puis `www.moroccoriwatours.com`. Vercel affiche les enregistrements DNS exacts à créer chez votre registrar. Choisissez la redirection de `www` vers `moroccoriwatours.com`.

## 6. Créer les tables et votre compte admin (depuis votre PC)

Vercel n'a pas de terminal : c'est votre PC qui se connecte à la base Supabase. Dans PowerShell, dans le dossier du projet, avec l'environnement virtuel activé :

```powershell
$env:DATABASE_URL="collez-ici-la-chaine-Supabase"
python manage.py migrate
python manage.py createsuperuser
```

Cette variable n'existe que dans cette fenêtre PowerShell. Ne lancez pas `seed_demo` sur le vrai site, il ajoute des circuits d'exemple. Refaites `migrate` de la même façon chaque fois que le code change les tables.

## 7. Se connecter à l'admin et ajouter les circuits

L'adresse est :

```
https://moroccoriwatours.com/fr/gestion-x7k2/
```

(remplacez `gestion-x7k2` par votre `DJANGO_ADMIN_URL`, et `/fr/` par `/en/` pour l'admin en anglais). Connectez-vous avec le compte créé à l'étape 6.

1. **Catégories** : ajoutez-les d'abord. Dans « Icône », mettez un nom Font Awesome comme `fa-sun`.
2. **Circuits** : ajoutez un circuit avec son titre, ses descriptions, son prix en dirhams et sa photo principale. Cochez « Actif ».
   Chaque texte (titre, descriptions, temps forts, ville de départ) a trois onglets : **Français**, **English**, **Español**.
   Seul le français est obligatoire. Si l'anglais ou l'espagnol est vide, le site affiche le français à la place.
3. **Photos** : gardez-les sous 4 Mo au total par envoi (squoosh.app réduit une photo sans perte visible). Pour une galerie, enregistrez le circuit, puis ajoutez les photos par petits lots.
4. **Réservations** : voir `DEPLOY.md`, section « Comment une réservation est confirmée (WhatsApp) ».

## 8. Si quelque chose ne marche pas

- **Page d'erreur 500** : Vercel, onglet **Logs** du projet, pour lire l'erreur.
- **DisallowedHost** : le domaine utilisé n'est pas dans `DJANGO_ALLOWED_HOSTS`.
- **Erreur CSRF à la connexion admin** : même cause, ou `DJANGO_SITE_URL` incorrect.
- **« relation ... does not exist »** : les tables ne sont pas créées, refaites l'étape 6.
- **Les photos ne s'affichent pas** : le bucket n'est pas public, ou `DJANGO_S3_PUBLIC_DOMAIN` est faux (sans `https://`).
- **Erreur 413 en ajoutant des photos** : l'envoi dépasse 4,5 Mo, réduisez les photos.

## 9. Mettre à jour le site

Modifiez le code, puis `git add .`, `git commit -m "..."`, `git push`. Vercel redéploie tout seul. Si les tables ont changé, refaites `migrate` (étape 6).

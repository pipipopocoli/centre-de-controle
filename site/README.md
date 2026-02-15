# Cockpit V2 Launch Site

Ce dossier contient le "Site de Lancement" complet pour le projet Cockpit V2.
Il est conçu pour être **100% autonome et offline-first**.

## 1. Comment l'ouvrir (Localement)
Simplement double-cliquer sur `index.html`.
Aucun serveur n'est requis car toutes les données (Roadmap, Skills, Simulation) sont embarquées dans `app.js`.

## 2. Comment le partager (LAN / Réseau)
Si vous voulez le montrer à des collègues sur le même réseau Wi-Fi :

1. Ouvrez un terminal dans ce dossier :
   ```bash
   cd site/
   python3 -m http.server 8000
   ```
2. Vos collègues peuvent accéder à :
   `http://<VOTRE_IP_LOCALE>:8000`

## 3. Comment le publier (Public)
Ce site est une page statique pure (HTML/CSS/JS). Vous pouvez l'héberger gratuitement et instantanément sur :

- **GitHub Pages** : Poussez ce dossier sur un repo GitHub et activez Pages dans les settings.
- **Vercel / Netlify** : Glissez-déposez ce dossier.
- **Interne** : Copiez le dossier sur n'importe quel serveur web (Apache/Nginx).

## Contenu
- `index.html` : Structure et textes.
- `styles.css` : Thème visuel (Nature Minimal).
- `app.js` : Logique (Gantt interactif, Simulation console, Données embarquées).
- `assets/` : Icônes et fichiers JSON sources (optionnels, car embarqués).

## Sécurité
Le site ne contient **aucun secret** (clés API, mots de passe).
Les données de simulation sont fictives.
La roadmap contient des titres de tâches techniques, mais rien de compromettant publiquement.

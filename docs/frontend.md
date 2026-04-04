# 🎨 Assets Front-end

## `assets/style.css`

Feuille de style CSS globale (~770+ lignes). Dash sert automatiquement tous les fichiers du dossier `assets/`.

### Sections principales

| Sélecteur CSS | Rôle |
|:---|:---|
| `:root` | Définition des variables de couleurs et de la typographie (Inter) |
| `.intro-text` | Typographie spécifique à la page d'accueil |
| `.header-nav-tabs .mantine-Tabs-tab` | Style des onglets de navigation (pills) |
| `.header-nav-tabs .mantine-Tabs-tab[data-active]` | Onglet actif : fond bleu `#339af0`, texte blanc |
| `.header-nav-tabs .mantine-Tabs-tab:hover:not([data-active])` | Survol onglet **inactif** uniquement (gris clair) |
| `.app-sidebar` | Style de la sidebar (fond, ombres) |
| `.rc-slider` | Espacement et visibilité des RangeSliders Dash |
| `#accordion-item-prise-en-main` | `scroll-margin-top: 100px` pour le scroll "header-aware" |
| `.mantine-ScrollArea-*` | Masquage des scrollbars natives redondantes |
| `.help-button-animated` | Animation pulse violette sur le bouton d'aide |
| `.premium-hover-purple` | Effet lift au survol des boutons violets |
| `.methodo-markdown table` | Styling des tableaux en Markdown rendu |
| `.bounce` | Animation rebond sur l'indicateur de scroll |

### Animation "Premium Pulse" (Bouton Aide)

```css
@keyframes premium-pulse {
    0%   { transform: scale(1);    box-shadow: 0 0 0 0 rgba(132, 92, 246, 0.4); }
    50%  { transform: scale(1.03); box-shadow: 0 0 0 10px rgba(132, 92, 246, 0); }
    100% { transform: scale(1);    box-shadow: 0 0 0 0 rgba(132, 92, 246, 0); }
}

.help-button-animated {
    animation: premium-pulse 3s infinite ease-in-out;
}
```

Cette animation crée un effet de "respiration" périodique qui attire l'œil sans être agressif.

---

## `assets/scroll.js`

Clientside callback défini dans `home.py` et exécuté côté navigateur pour le scroll smooth.

```javascript
window.dash_clientside.clientside = {
    scrollToAccordion: function(n_clicks) {
        if (n_clicks) {
            document.getElementById('accordion-item-prise-en-main')
                .scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        return window.dash_clientside.no_update;
    }
};
```

!!! note "scroll-margin-top"
    Le CSS applique `scroll-margin-top: 100px` au composant ciblé pour que le contenu s'arrête **sous le header fixe** (hauteur 130px).

---

## `assets/Senio.png`

Logo officiel SeniAura, affiché en header à `height: 75px`.

!!! tip "Pour modifier le logo"
    Remplacez simplement le fichier `assets/Senio.png` par une nouvelle image PNG du même nom. Pas besoin de modifier le code.

---

## `assets/robots.txt`

Fichier de contrôle SEO, servi à `/robots.txt` via une route Flask dédiée dans `app_v2.py`.

```
User-agent: *
Allow: /
Sitemap: https://seniaura.onrender.com/sitemap.xml
```

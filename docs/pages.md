## 5. Pages

### 5.1 Accueil

**Fichier** : `src/pages/home.py`

#### Fonctionnement

1. **Lecture du fichier texte** : Parse `texte introductif du dashboard.txt`.
2. **Construction d'un Accordion** : Chaque section devient un `AccordionItem`.
3. **Boutons CTA** : Liens vers `/exploration` et Scroll smooth.

---

### 5.2 Exploration

**Fichier** : `src/pages/exploration.py`

#### Layout

- **Carte choroplèthe** : Gérée par `update_map()`.
- **Radar comparatif** : Géré par `update_radar()`.

#### Callbacks principaux

- `update_sliders` : Génère dynamiquement les `RangeSlider`.
- `update_map` : Rendu de la carte avec 6 couches (Fond, Focus, Départements, Highlight, Sélection, Villes).

---

### 5.3 Méthodologie

**Fichier** : `src/pages/methodology.py`

- Affiche les tables de variables dynamiquement.
- Divisé en 4 onglets : Socioéco, Offre de soins, Environnement, Santé.

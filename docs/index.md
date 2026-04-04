# Documentation Technique — CardiAURA / SeniAura Dashboard

> **Version** : 3.0 — Mars 2026  
> **Framework** : Dash + Dash Mantine Components (dmc v7) + Plotly  
> **Région** : Auvergne-Rhône-Alpes (ARA)  

---

## 1. Vue d'ensemble

CardiAURA (alias SeniAura) est un **tableau de bord interactif** permettant d'explorer les déterminants des maladies cardio-neuro-vasculaires à l'échelle des **EPCI** (Établissements Publics de Coopération Intercommunale) de la région Auvergne-Rhône-Alpes.

### Fonctionnalités principales

| Fonctionnalité | Description |
|---|---|
| **Carte choroplèthe** | Visualisation colorée d'un indicateur de santé (Incidence, Mortalité, Prévalence) par EPCI |
| **Filtrage par variables** | Sliders dynamiques pour filtrer les EPCI selon des critères socio-éco, offre de soins, environnement |
| **Radar comparatif** | Comparaison multi-variables de territoires sélectionnés vs. la moyenne régionale |
| **Analyse textuelle auto-générée** | Interprétations narratives et positionnement en quantiles |
| **Méthodologie** | Tables détaillées des variables avec descriptions, unités et sources |

### Stack technique

```
Python 3.x
├── dash                      # Framework web réactif
├── dash-mantine-components   # Composants UI (v7, style Mantine)
├── dash-iconify              # Icônes (Solar icon set)
├── plotly                    # Graphiques (Choropleth, Scatterpolar, Scattergeo)
├── geopandas                 # Manipulation des données géographiques
├── pandas / numpy            # Manipulation des données tabulaires
├── openpyxl                  # Lecture des fichiers Excel (.xlsx)
└── gunicorn                  # Serveur WSGI pour la production
```

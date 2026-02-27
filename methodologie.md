# Méthodologie

Ce document centralise les informations relatives aux choix méthodologiques appliqués sur le dataset du projet SeniAura.

## Gestion des valeurs manquantes

La stratégie de traitement des valeurs manquantes (N/A) varie selon le contexte d'utilisation de la donnée :

### 1. Au sein du Tableau de Bord (Dashboard)
Dans l'application interactive (`src/pages/clustering.py`, `screening_variables.py`), les valeurs manquantes sont généralement gérées de manière dynamique par **suppression des lignes concernées (`dropna()`)**. 
- Lorsqu'un utilisateur sélectionne des variables spécifiques pour générer un graphique, une carte ou une analyse, les EPCI possédant des données manquantes pour **ces seules variables** sont exclus temporairement de l'affichage. 
- Cette approche garantit que les calculs et les rendus visuels ne sont pas faussés par des imputations artificielles, privilégiant la précision des informations présentées en temps réel.

### 2. Phase Exploratoire et Modélisation (Notebooks)
Lors de l'étape de recherche et de développement des modèles (comme observé dans `Clustering_tests_for_Seniaura_Capstone_Project.ipynb`), une stratégie d'**imputation** a été mise en œuvre afin de préserver la taille du jeu de données pour l'apprentissage des algorithmes :
- **Variables numériques** : Les valeurs manquantes sont remplacées par la **moyenne** des valeurs de la colonne respective (`fillna(mean)`).
- **Variables catégorielles** : Les valeurs manquantes sont remplacées par le **mode**, c'est-à-dire la valeur la plus fréquente de la colonne (`fillna(mode)`).

---

## Gestion des valeurs aberrantes

*(Cette section est actuellement vide. Elle décrira ultérieurement les méthodes employées pour identifier et traiter les valeurs extrêmes ou aberrantes dans le dataset.)*

---

## Prétraitements effectués

*(Cette section est actuellement vide. Elle regroupera par la suite l'ensemble des opérations de transformation des données, telles que la normalisation Min-Max indispensable pour le calcul des scores au sein du radar, ou encore la standardisation avant clustering K-Means.)*

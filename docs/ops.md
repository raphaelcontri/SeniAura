## 8. Guide de déploiement

### Développement local

```bash
pip install -r requirements.txt
python3 app_v2.py
```

### Production (Gunicorn)

```bash
gunicorn app_v2:server -b 0.0.0.0:8050 --workers 4
```

---

## 9. FAQ technique

- **Ajouter une variable** : Modifier l'Excel + le Dictionnaire CSV.
- **Ajouter une ville** : Modifier la liste `cities` dans `exploration.py`.
- **SEO** : Géré via `robots.txt` et meta balises dans `app_v2.py`.

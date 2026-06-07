import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(env_path)

DATABRICKS_SERVER_HOSTNAME = os.environ.get("DATABRICKS_SERVER_HOSTNAME")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
# Chemin par défaut du notebook de traitement dans Databricks
DATABRICKS_NOTEBOOK_PATH = os.environ.get("DATABRICKS_NOTEBOOK_PATH", "/Users/your_user_email/SeniAura_Processing")

def trigger_databricks_run(file_path_in_bucket, scale):
    """
    Déclenche l'exécution du notebook sur Databricks via l'API REST Jobs (runs/submit).
    Retourne un dict avec le statut et l'identifiant du Run.
    """
    # Vérifier si les identifiants requis sont renseignés (et ne sont pas les placeholders par défaut)
    if (not DATABRICKS_SERVER_HOSTNAME or 
        not DATABRICKS_TOKEN or 
        "your_databricks_host" in DATABRICKS_SERVER_HOSTNAME or 
        "your_databricks_token" in DATABRICKS_TOKEN):
        return {
            "success": False, 
            "error": "Community Edition (Pas d'API) ou configuration manquante dans .env. Exécution manuelle requise."
        }
        
    url = f"https://{DATABRICKS_SERVER_HOSTNAME.replace('https://', '')}/api/2.1/jobs/runs/submit"
    
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "run_name": f"SeniAura Process: {os.path.basename(file_path_in_bucket)}",
        "tasks": [
            {
                "task_key": "csv_processing",
                "notebook_task": {
                    "notebook_path": DATABRICKS_NOTEBOOK_PATH,
                    "base_parameters": {
                        "file_path_in_bucket": file_path_in_bucket,
                        "scale": scale
                    }
                },
                "serverless": {}  # Compute serverless automatique
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200 or response.status_code == 201:
            run_id = response.json().get("run_id")
            return {"success": True, "run_id": run_id}
        else:
            error_msg = response.json().get("message") or response.text
            return {"success": False, "error": f"Erreur API Databricks ({response.status_code}) : {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

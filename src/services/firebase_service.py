import os
import pyrebase
import requests
import json
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration Firebase
firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.environ.get("FIREBASE_APP_ID"),
    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", "")
}

# Initialisation de Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
PROJECT_ID = firebase_config["projectId"]

def signup_user(email, password):
    """
    Inscrit un utilisateur avec son email et son mot de passe.
    Retourne les infos de l'utilisateur ou lève une exception.
    """
    try:
        user = auth.create_user_with_email_and_password(email, password)
        return {
            "success": True,
            "uid": user["localId"],
            "email": user["email"],
            "idToken": user["idToken"]
        }
    except Exception as e:
        error_json = e.args[1] if len(e.args) > 1 else str(e)
        try:
            error_msg = json.loads(error_json)["error"]["message"]
        except:
            error_msg = str(e)
        return {"success": False, "error": error_msg}

def login_user(email, password):
    """
    Connecte un utilisateur avec son email et son mot de passe.
    Retourne les infos de session ou lève une exception.
    """
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return {
            "success": True,
            "uid": user["localId"],
            "email": user["email"],
            "idToken": user["idToken"]
        }
    except Exception as e:
        error_json = e.args[1] if len(e.args) > 1 else str(e)
        try:
            error_msg = json.loads(error_json)["error"]["message"]
        except:
            error_msg = str(e)
        return {"success": False, "error": error_msg}

def save_dataset_metadata(id_token, uid, dataset_name, file_path, is_public=False, scale="epci", columns_metadata=None):
    """
    Enregistre les métadonnées d'un dataset dans Firestore via l'API REST officielle.
    """
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/datasets"
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    columns_metadata_str = json.dumps(columns_metadata or {})
    
    # Structure de données attendue par l'API REST de Firestore
    payload = {
        "fields": {
            "owner_uid": {"stringValue": uid},
            "dataset_name": {"stringValue": dataset_name},
            "file_path": {"stringValue": file_path},
            "is_public": {"booleanValue": is_public},
            "scale": {"stringValue": scale},
            "columns_metadata": {"stringValue": columns_metadata_str},
            "timestamp": {"stringValue": pd_timestamp_now()}
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            # Extraire l'ID du document généré
            doc_id = data["name"].split("/")[-1]
            return {"success": True, "document_id": doc_id}
        else:
            return {"success": False, "error": response.json().get("error", {}).get("message", "Erreur inconnue")}
    except Exception as e:
        return {"success": False, "error": str(e)}

_cached_guest_token = None

def get_guest_token():
    global _cached_guest_token
    if _cached_guest_token:
        return _cached_guest_token
    res = login_user("guest@cardiaura.fr", "guestcardiaura123")
    if res["success"]:
        _cached_guest_token = res["idToken"]
        return _cached_guest_token
    return None

def get_available_datasets(id_token=None, uid=None):
    """
    Récupère la liste des datasets disponibles.
    Si id_token est fourni, retourne les datasets PUBLICS + les datasets PRIVÉS de cet utilisateur.
    Si non fourni, utilise un compte invité sous le capot pour récupérer uniquement les datasets PUBLICS.
    """
    global _cached_guest_token
    
    is_guest = False
    if not id_token:
        id_token = get_guest_token()
        is_guest = True
        
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/datasets?pageSize=300"
    
    headers = {}
    if id_token:
        headers["Authorization"] = f"Bearer {id_token}"
        
    try:
        response = requests.get(url, headers=headers)
        
        # Si le token invité a expiré (401/403), on réinitialise le cache et on réessaie
        if response.status_code in [401, 403] and is_guest:
            _cached_guest_token = None
            id_token = get_guest_token()
            if id_token:
                headers["Authorization"] = f"Bearer {id_token}"
                response = requests.get(url, headers=headers)
                
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            
            datasets = []
            for doc in documents:
                fields = doc.get("fields", {})
                doc_id = doc["name"].split("/")[-1]
                
                owner_uid = fields.get("owner_uid", {}).get("stringValue", "")
                is_public = fields.get("is_public", {}).get("booleanValue", False)
                dataset_name = fields.get("dataset_name", {}).get("stringValue", "Sans nom")
                file_path = fields.get("file_path", {}).get("stringValue", "")
                scale = fields.get("scale", {}).get("stringValue", "epci")
                columns_metadata_str = fields.get("columns_metadata", {}).get("stringValue", "{}")
                
                try:
                    columns_metadata = json.loads(columns_metadata_str)
                except:
                    columns_metadata = {}
                
                # Filtrage côté client si invité (ne voir que les publics)
                if is_guest and not is_public:
                    continue
                # Si connecté avec un compte utilisateur normal, ne voir que les siens ou les publics
                if not is_guest and not is_public and owner_uid != uid:
                    continue
                    
                datasets.append({
                    "id": doc_id,
                    "name": dataset_name,
                    "dataset_name": dataset_name,
                    "file_path": file_path,
                    "owner_uid": owner_uid,
                    "is_public": is_public,
                    "scale": scale,
                    "columns_metadata": columns_metadata
                })
            return {"success": True, "datasets": datasets}
        else:
            if not is_guest:
                # Si connecté, c'est une vraie erreur de session (ex: token expiré)
                try:
                    err_msg = response.json().get("error", {}).get("message", f"Status {response.status_code}")
                except:
                    err_msg = f"Status {response.status_code}"
                return {"success": False, "error": f"Session expirée ou invalide. Veuillez vous reconnecter. ({err_msg})"}
            # Fallback en cas d'erreur de règles Firestore pour les utilisateurs non connectés
            return {"success": True, "datasets": []}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pd_timestamp_now():
    from datetime import datetime
    return datetime.now().isoformat()

def delete_dataset_metadata(id_token, doc_id):
    """
    Supprime les métadonnées d'un dataset de Firestore via l'API REST.
    """
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/datasets/{doc_id}"
    headers = {
        "Authorization": f"Bearer {id_token}"
    }
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code in [200, 204, 205]:
            return {"success": True}
        else:
            try:
                msg = response.json().get("error", {}).get("message", "Erreur lors de la suppression")
            except:
                msg = response.text
            return {"success": False, "error": f"Erreur API ({response.status_code}) : {msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_dataset_visibility(id_token, doc_id, is_public):
    """
    Met à jour le champ is_public d'un dataset spécifique dans Firestore via l'API REST.
    """
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/datasets/{doc_id}"
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "updateMask.fieldPaths": "is_public"
    }
    
    payload = {
        "fields": {
            "is_public": {"booleanValue": is_public}
        }
    }
    
    try:
        response = requests.patch(url, headers=headers, params=params, json=payload)
        if response.status_code == 200:
            return {"success": True}
        else:
            try:
                msg = response.json().get("error", {}).get("message", "Erreur lors de la mise à jour")
            except:
                msg = response.text
            return {"success": False, "error": f"Erreur API ({response.status_code}) : {msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET_NAME = os.environ.get("SUPABASE_BUCKET_NAME", "cardiaura-datasets")

# Initialisation du client Supabase
supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Erreur d'initialisation Supabase : {e}")

def upload_csv_file(file_path_in_bucket, file_bytes):
    """
    Téléverse des octets de fichier CSV dans le bucket privé Supabase.
    Retourne un dictionnaire avec le statut de succès ou l'erreur.
    """
    if not supabase_client:
        return {"success": False, "error": "Le client Supabase n'est pas initialisé (vérifiez vos variables d'environnement)."}
        
    try:
        # Téléverser dans Supabase
        # file_path_in_bucket exemple: "raw/user123_1717320000_indicateurs.csv"
        # Overwrite=True pour écraser en cas d'erreur de doublon
        response = supabase_client.storage.from_(BUCKET_NAME).upload(
            path=file_path_in_bucket,
            file=file_bytes,
            file_options={"content-type": "text/csv", "x-upsert": "true"}
        )
        return {"success": True, "path": file_path_in_bucket}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_signed_url(file_path_in_bucket, expiration_seconds=600):
    """
    Génère une URL signée temporaire (par défaut 10 minutes)
    permettant à DuckDB ou Pandas de lire le fichier privé.
    """
    if not supabase_client:
        return {"success": False, "error": "Le client Supabase n'est pas initialisé."}
        
    try:
        response = supabase_client.storage.from_(BUCKET_NAME).create_signed_url(
            path=file_path_in_bucket,
            expires_in=expiration_seconds
        )
        # Supabase retourne un dictionnaire avec 'signedURL' ou 'signedUrl'
        signed_url = response.get("signedURL") or response.get("signedUrl")
        if signed_url:
            return {"success": True, "url": signed_url}
        else:
            return {"success": False, "error": "URL signée non générée par Supabase."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_csv_file(file_path_in_bucket):
    """
    Supprime un fichier du bucket Supabase.
    """
    if not supabase_client:
        return {"success": False, "error": "Le client Supabase n'est pas initialisé."}
    try:
        supabase_client.storage.from_(BUCKET_NAME).remove([file_path_in_bucket])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

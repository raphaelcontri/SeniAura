import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ALL
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import base64
import io
import pandas as pd
import time
import json
import os
from src.services.databricks_service import trigger_databricks_run

# Déclarer l'interface utilisateur de la page d'import
layout = dmc.Container(
    size="md",
    py="xl",
    children=[
        # Store local pour la configuration chargée
        dcc.Store(id="loaded-config-store", data={}),
        
        dmc.Stack(gap="lg", children=[
            # Bouton de retour
            dcc.Link(
                dmc.Button(
                    "Retour au tableau de bord",
                    variant="subtle",
                    color="gray",
                    leftSection=DashIconify(icon="solar:arrow-left-outline", width=16),
                    style={"paddingLeft": 0}
                ),
                href="/exploration",
                style={"textDecoration": "none"}
            ),
            # Titre et introduction
            dmc.Box(children=[
                dmc.Title("Importer de nouvelles données territoriales", order=2, style={"color": "#2c3e50"}),
                dmc.Text(
                    "Enrichissez le diagnostic de la région Auvergne-Rhône-Alpes en important vos propres indicateurs par EPCI.",
                    c="dimmed",
                    size="sm"
                )
            ]),
            
            # Formulaire d'importation
            dmc.Paper(
                withBorder=True,
                shadow="sm",
                radius="lg",
                p="xl",
                style={"backgroundColor": "#ffffff"},
                children=[
                    dmc.Stack(
                        gap="md",
                        children=[
                            # Étape 0 : Charger une configuration existante (Optionnel)
                            dmc.Box([
                                dmc.Text("💡 Charger une configuration existante (Optionnel)", fw=700, size="sm", mb=5),
                                dcc.Upload(
                                    id="upload-config-file",
                                    children=html.Div([
                                        dmc.Group([
                                            DashIconify(icon="solar:file-text-bold-duotone", width=24, color="blue"),
                                            dmc.Text("Glissez-déposez un fichier de configuration .json ou cliquez ici", size="xs", c="dimmed")
                                        ], gap="xs", justify="center", align="center")
                                    ]),
                                    style={
                                        "width": "100%",
                                        "height": "50px",
                                        "borderWidth": "1px",
                                        "borderStyle": "dashed",
                                        "borderRadius": "8px",
                                        "borderColor": "#ced4da",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center",
                                        "backgroundColor": "#f8f9fa",
                                        "cursor": "pointer"
                                    },
                                    multiple=False
                                ),
                                html.Div(id="selected-config-name-display", style={"marginTop": "5px"}),
                            ]),

                            # Étape 1 : Nommer le jeu de données
                            dmc.Box([
                                dmc.Text("1. Nommer votre jeu de données", fw=700, size="sm", mb=5),
                                dmc.TextInput(
                                    id="upload-name",
                                    placeholder="Ex: Taux de couverture de soins de suite (2026)",
                                    required=True,
                                    radius="md"
                                )
                            ]),
                            

                            
                            # Étape 3 : Visibilité (Public vs Privé) - Masqué dans l'UI offline
                            dmc.Box([
                                dmc.Text("3. Paramètres de confidentialité", fw=700, size="sm", mb=5),
                                dmc.Card(
                                    withBorder=True,
                                    radius="md",
                                    p="sm",
                                    style={"backgroundColor": "#f8f9fa"},
                                    children=[
                                        dmc.Group(
                                            justify="space-between",
                                            children=[
                                                dmc.Stack(gap=2, children=[
                                                    dmc.Text("Rendre ce jeu de données public", fw=600, size="sm"),
                                                    dmc.Text("Si activé, tous les utilisateurs pourront visualiser ces indicateurs sur leurs cartes.", size="xs", c="dimmed")
                                                ]),
                                                dmc.Switch(
                                                    id="upload-public-switch",
                                                    checked=False,
                                                    color="teal",
                                                    size="md"
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ], style={"display": "none"}),
                            
                            # Étape 4 : Fichier CSV
                            dmc.Box([
                                dmc.Text("2. Sélectionner le fichier CSV", fw=700, size="sm", mb=5),
                                dcc.Upload(
                                    id="upload-file",
                                    children=html.Div([
                                        dmc.Stack(
                                            align="center",
                                            gap="xs",
                                            children=[
                                                dmc.ThemeIcon(
                                                    DashIconify(icon="solar:cloud-upload-bold-duotone", width=36),
                                                    size=48,
                                                    radius="xl",
                                                    variant="light",
                                                    color="blue"
                                                ),
                                                dmc.Text("Glissez-déposez votre fichier CSV ou cliquez ici", fw=500, size="sm"),
                                                dmc.Text("Format attendu : .csv encodé en UTF-8", size="xs", c="dimmed")
                                            ]
                                        )
                                    ]),
                                    style={
                                        "width": "100%",
                                        "height": "140px",
                                        "borderWidth": "1px",
                                        "borderStyle": "dashed",
                                        "borderRadius": "12px",
                                        "borderColor": "#339af0",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center",
                                        "backgroundColor": "#f8f9fa",
                                        "cursor": "pointer"
                                    },
                                    multiple=False
                                ),
                                # Affichage du nom du fichier sélectionné
                                html.Div(id="selected-file-name-display", style={"marginTop": "5px"}),
                                
                                # Étape 5 : Configuration des colonnes (générée dynamiquement)
                                html.Div(id="dynamic-columns-container", style={"marginTop": "15px"})
                            ]),
                            
                            # Zone d'alertes / retours d'information
                            html.Div(id="upload-alert-container"),
                            
                            # Groupe de boutons hors-ligne
                            dmc.Group([
                                dmc.Button(
                                    "Charger les données",
                                    id="upload-local-btn",
                                    radius="md",
                                    size="md",
                                    color="blue",
                                    leftSection=DashIconify(icon="solar:play-bold", width=18)
                                ),
                                dmc.Button(
                                    "Exporter la configuration (JSON)",
                                    id="export-config-btn",
                                    radius="md",
                                    size="md",
                                    color="teal",
                                    variant="outline",
                                    leftSection=DashIconify(icon="solar:download-bold", width=18)
                                ),
                                dcc.Download(id="download-config-json")
                            ], gap="sm"),
                            
                        ]
                    )
                ]
            )
        ])
    ]
)

# Callback pour afficher le nom du fichier sélectionné
@callback(
    Output("selected-file-name-display", "children"),
    Input("upload-file", "filename"),
    prevent_initial_call=True
)
def display_selected_file(filename):
    if not filename:
        return []
    return dmc.Group([
        DashIconify(icon="solar:document-bold", width=14, color="teal"),
        dmc.Text(f"Fichier sélectionné : {filename}", size="xs", fw=600, c="teal")
    ], gap="xs")

# Callback pour générer dynamiquement la configuration des colonnes après l'upload
@callback(
    Output("dynamic-columns-container", "children"),
    Input("upload-file", "contents"),
    [State("loaded-config-store", "data")],
    prevent_initial_call=True
)
def generate_column_config(file_contents, loaded_config):
    if not file_contents:
        return []
        
    try:
        content_type, content_string = file_contents.split(",")
        decoded = base64.b64decode(content_string)
        
        # Lire uniquement la première ligne
        df_temp = pd.read_csv(io.BytesIO(decoded), nrows=1)
        columns = list(df_temp.columns)
        
        # Filtre pour exclure les colonnes de codes géographiques
        geo_keys = ["code_epci", "epci_code", "code_commune", "insee_commune", "code_insee", "nom_epci", "libepci"]
        filtered_cols = [col for col in columns if str(col).lower().strip() not in geo_keys]
        
        if not filtered_cols:
            return dmc.Alert(
                "Aucune colonne d'indicateur numérique détectée à configurer (les codes géographiques de fusion sont exclus).",
                color="orange",
                radius="md"
            )
            
        children = [
            dmc.Divider(my="md"),
            dmc.Text("3. Configurer les indicateurs détectés dans le fichier", fw=700, size="sm", mb=5),
            dmc.Text("Spécifiez la catégorie et le nom d'affichage de chaque colonne.", size="xs", c="dimmed", mb="md")
        ]
        
        # Extraire la config JSON pré-chargée si disponible
        columns_metadata = {}
        if loaded_config and isinstance(loaded_config, dict):
            columns_metadata = loaded_config.get("columns_metadata", {})
            
        for col in filtered_cols:
            col_meta = columns_metadata.get(col, {})
            default_label = col_meta.get("label", str(col).replace("_", " ").strip().capitalize())
            default_cat = col_meta.get("category", "environnement")
            
            card_child = dmc.Card(
                withBorder=True,
                shadow="xs",
                radius="md",
                p="sm",
                mb="sm",
                children=[
                    dmc.Group(
                        grow=True,
                        gap="sm",
                        children=[
                            # Nom d'origine
                            dmc.Box([
                                dmc.Text("Colonne d'origine", size="xs", c="dimmed", fw=600),
                                dmc.Text(col, fw=700, size="sm")
                            ]),
                            # Nom d'affichage
                            dmc.TextInput(
                                id={"type": "col-label", "index": col},
                                label="Nom d'affichage",
                                value=default_label,
                                radius="md",
                                size="sm"
                             ),
                            # Catégorie
                            dmc.Select(
                                id={"type": "col-category", "index": col},
                                label="Catégorie",
                                data=[
                                    {"label": "Socio-économique", "value": "socioéco"},
                                    {"label": "Offre de soins", "value": "offre de soins"},
                                    {"label": "Environnement", "value": "environnement"},
                                    {"label": "Indicateur de Santé", "value": "santé"},
                                    {"label": "Autre", "value": "autre"}
                                ],
                                value=default_cat,
                                radius="md",
                                size="sm",
                                comboboxProps={"withinPortal": True}
                            )
                        ]
                    )
                ]
            )
            children.append(card_child)
            
        return children
        
    except Exception as e:
        return dmc.Alert(f"Erreur de lecture des colonnes : {str(e)}", color="red")




# Callback pour charger le fichier de configuration JSON
@callback(
    [Output("loaded-config-store", "data"),
     Output("selected-config-name-display", "children"),
     Output("upload-name", "value")],
    Input("upload-config-file", "contents"),
    State("upload-config-file", "filename"),
    prevent_initial_call=True
)
def load_config_json(file_contents, filename):
    if not file_contents:
        return no_update, no_update, no_update
        
    try:
        content_type, content_string = file_contents.split(",")
        decoded = base64.b64decode(content_string)
        config_data = json.loads(decoded)
        
        # Validation du format
        if not isinstance(config_data, dict):
            return {}, dmc.Text("Erreur : Le fichier de configuration doit être un objet JSON.", color="red", size="xs"), no_update
            
        dataset_name = config_data.get("dataset_name", "")
        
        display_msg = dmc.Group([
            DashIconify(icon="solar:check-circle-bold", width=14, color="teal"),
            dmc.Text(f"Configuration chargée : {filename}", size="xs", fw=600, color="teal")
        ], gap="xs")
        
        return config_data, display_msg, dataset_name
        
    except Exception as e:
        return {}, dmc.Text(f"Erreur lors de la lecture du fichier de configuration : {str(e)}", color="red", size="xs"), no_update


# Callback pour exporter la configuration en JSON
@callback(
    Output("download-config-json", "data"),
    Input("export-config-btn", "n_clicks"),
    [State("upload-name", "value"),
     State({"type": "col-label", "index": ALL}, "value"),
     State({"type": "col-category", "index": ALL}, "value"),
     State({"type": "col-label", "index": ALL}, "id")],
    prevent_initial_call=True
)
def export_config_to_json(n_clicks, dataset_name, col_labels, col_categories, col_ids):
    if not n_clicks:
        return no_update
        
    # Construire l'objet metadata des colonnes
    columns_metadata = {}
    for label, category, cid in zip(col_labels, col_categories, col_ids):
        col_name = cid["index"]
        columns_metadata[col_name] = {
            "label": label,
            "category": category
        }
        
    config_data = {
        "format": "cardiaura_config",
        "version": "1.0",
        "dataset_name": dataset_name or "Dataset local",
        "scale": "epci",
        "columns_metadata": columns_metadata
    }
    
    # Formater le nom du fichier
    safe_name = (dataset_name or "dataset").lower().replace(" ", "_").replace("'", "_")
    filename = f"config_{safe_name}.json"
    
    return dcc.send_bytes(json.dumps(config_data, indent=2, ensure_ascii=False).encode('utf-8'), filename)


# Callback principal pour gérer le chargement local offline
@callback(
    [Output("upload-alert-container", "children", allow_duplicate=True),
     Output("local-datasets-store", "data", allow_duplicate=True),
     Output("dataset-refresh-trigger", "data", allow_duplicate=True)],
    Input("upload-local-btn", "n_clicks"),
    [State("upload-name", "value"),
     State("upload-file", "contents"),
     State("upload-file", "filename"),
     State({"type": "col-label", "index": ALL}, "value"),
     State({"type": "col-category", "index": ALL}, "value"),
     State({"type": "col-label", "index": ALL}, "id"),
     State("local-datasets-store", "data"),
     State("dataset-refresh-trigger", "data")],
    prevent_initial_call=True
)
def process_local_upload(n_clicks, dataset_name, file_contents, filename, col_labels, col_categories, col_ids, local_datasets, refresh_trigger):
    if not n_clicks:
        return no_update, no_update, no_update
        
    if not dataset_name or not file_contents:
        return dmc.Alert(
            "Veuillez renseigner un nom pour le jeu de données et sélectionner un fichier CSV.",
            title="Champs obligatoires",
            color="orange",
            radius="md"
        ), no_update, no_update
        
    # 1. Décodage et validation du fichier CSV en mémoire avec Pandas
    try:
        content_type, content_string = file_contents.split(",")
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.BytesIO(decoded))
        
        # Validation géographique selon l'échelle
        columns_lower = [str(c).lower().strip() for c in df.columns]
        target_col = None
        
        if "code_epci" in columns_lower:
            target_col = df.columns[columns_lower.index("code_epci")]
        elif "epci_code" in columns_lower:
            target_col = df.columns[columns_lower.index("epci_code")]
            
        if not target_col:
            return dmc.Alert(
                "Le fichier CSV doit contenir obligatoirement une colonne nommée 'CODE_EPCI' ou 'EPCI_CODE' pour pouvoir être importé.",
                title="Erreur de validation",
                color="red",
                radius="md"
            ), no_update, no_update
        df = df.rename(columns={target_col: "CODE_EPCI"})
        df["CODE_EPCI"] = df["CODE_EPCI"].astype(str).str.replace(".0", "", regex=False).str.strip()
            
        # Échappement anti-injection CSV (Sécurité formule)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).apply(
                # Échapper avec une apostrophe simple
                lambda x: f"'{x}" if x.startswith(('=', '+', '-', '@')) else x
            )
            
    except Exception as e:
        return dmc.Alert(
            f"Impossible de lire le fichier CSV. Détails : {str(e)}",
            title="Erreur de lecture",
            color="red",
            radius="md"
        ), no_update, no_update
        
    # 2. Sauvegarder localement sur le disque
    import uuid
    local_id = f"local_{uuid.uuid4().hex}"
    local_filename = f"{local_id}.csv"
    
    # Résoudre le dossier local
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    local_dir = os.path.join(base_dir, "data", "local")
    os.makedirs(local_dir, exist_ok=True)
    
    local_path = os.path.join(local_dir, local_filename)
    
    try:
        df_clean = df.copy()
            
        df_clean.to_csv(local_path, index=False)
        
    except Exception as e:
        return dmc.Alert(
            f"Erreur lors du traitement et de la sauvegarde locale : {str(e)}",
            title="Erreur de sauvegarde",
            color="red",
            radius="md"
        ), no_update, no_update
        
    # 3. Construire les métadonnées de colonnes
    columns_metadata = {}
    for label, category, cid in zip(col_labels, col_categories, col_ids):
        col_name = cid["index"]
        # Nettoyage XSS simple des chaînes de caractères
        clean_label = str(label).replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
        columns_metadata[col_name] = {
            "label": clean_label,
            "category": category
        }
        
    # 4. Mettre à jour le store local
    new_local_dataset = {
        "id": local_id,
        "name": dataset_name,
        "dataset_name": dataset_name,
        "file_path": f"local/{local_filename}",
        "owner_uid": "local",
        "is_public": True,
        "scale": "epci",
        "columns_metadata": columns_metadata
    }
    
    updated_local_datasets = (local_datasets or []).copy()
    updated_local_datasets = [d for d in updated_local_datasets if d.get("name") != dataset_name]
    updated_local_datasets.append(new_local_dataset)
    
    next_refresh = (refresh_trigger or 0) + 1
    
    success_alert = dmc.Alert(
        children=[
            dmc.Text(f"Succès ! Le jeu de données '{dataset_name}' a été importé avec succès pour cette session.", fw=600),
            dmc.Text("Vous pouvez maintenant le sélectionner dans le menu déroulant 'Source de données' sur la page d'exploration.", size="xs", mt=5)
        ],
        title="Chargement réussi !",
        color="green",
        radius="md",
        icon=DashIconify(icon="solar:check-circle-bold")
    )
    
    return success_alert, updated_local_datasets, next_refresh

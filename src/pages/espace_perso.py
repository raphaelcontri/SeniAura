import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ALL
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import json
from src.services.firebase_service import login_user, signup_user, get_available_datasets, update_dataset_visibility

# Interface utilisateur de la page Espace Personnel
layout = dmc.Container(
    size="lg",
    py="xl",
    children=[
        # Notifications de retour
        html.Div(id="espace-perso-alert-container", style={"marginBottom": "20px"}),
        
        # 1. Conteneur Connexion (masqué si connecté)
        html.Div(
            id="espace-perso-login-container",
            style={"display": "none"},
            children=[
                dmc.Center(
                    style={"minHeight": "calc(100vh - 180px)", "padding": "40px 0"},
                    children=[
                        dmc.Card(
                            withBorder=True,
                            shadow="lg",
                            radius="lg",
                            p="xl",
                            style={
                                "width": "100%",
                                "maxWidth": "440px",
                                "backgroundColor": "#ffffff",
                                "borderColor": "#e9ecef"
                            },
                            children=[
                                dmc.Stack(
                                    align="center",
                                    gap="xs",
                                    mb="lg",
                                    children=[
                                        html.Img(src="/assets/Senio.png", height=50),
                                        dmc.Title("Espace Membre CardiAURA", order=3, style={"color": "#2c3e50"}),
                                        dmc.Text(
                                            "Connectez-vous ou créez un compte pour accéder à votre espace personnel.",
                                            size="sm",
                                            c="dimmed",
                                            ta="center"
                                        )
                                    ]
                                ),
                                dmc.Tabs(
                                    id="auth-tabs",
                                    value="login",
                                    color="blue",
                                    variant="outline",
                                    radius="md",
                                    children=[
                                        dmc.TabsList(
                                            grow=True,
                                            mb="md",
                                            children=[
                                                dmc.TabsTab(
                                                    "Se Connecter",
                                                    value="login",
                                                    leftSection=DashIconify(icon="solar:login-2-linear", width=18)
                                                ),
                                                dmc.TabsTab(
                                                    "S'inscrire",
                                                    value="register",
                                                    leftSection=DashIconify(icon="solar:user-plus-linear", width=18)
                                                )
                                            ]
                                        ),
                                        dmc.Stack(
                                            gap="sm",
                                            children=[
                                                dmc.TextInput(
                                                    id="auth-email",
                                                    label="Adresse email",
                                                    placeholder="exemple@univ.fr",
                                                    required=True,
                                                    radius="md",
                                                    leftSection=DashIconify(icon="solar:letter-linear", width=16)
                                                ),
                                                dmc.PasswordInput(
                                                    id="auth-password",
                                                    label="Mot de passe",
                                                    placeholder="Votre mot de passe",
                                                    required=True,
                                                    radius="md",
                                                    leftSection=DashIconify(icon="solar:lock-keyhole-linear", width=16)
                                                ),
                                                html.Div(id="auth-error-container", style={"marginTop": "5px"}),
                                                dmc.Button(
                                                    "Valider",
                                                    id="auth-submit-btn",
                                                    fullWidth=True,
                                                    radius="md",
                                                    size="md",
                                                    color="blue",
                                                    style={"marginTop": "15px"},
                                                    leftSection=DashIconify(icon="solar:arrow-right-bold", width=18)
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        ),
        
        # 2. Conteneur Espace Perso (masqué si déconnecté)
        html.Div(
            id="espace-perso-dashboard-container",
            style={"display": "none"},
            children=[
                dmc.Stack(
                    gap="xl",
                    children=[
                        # Header profil
                        dmc.Paper(
                            withBorder=True,
                            shadow="sm",
                            radius="lg",
                            p="xl",
                            style={"backgroundColor": "#ffffff"},
                            children=[
                                dmc.Group(
                                    justify="space-between",
                                    align="center",
                                    children=[
                                        dmc.Stack(
                                            gap="xs",
                                            children=[
                                                dmc.Title("Mon Espace Personnel", order=2, style={"color": "#2c3e50"}),
                                                dmc.Group(
                                                    gap="xs",
                                                    children=[
                                                        DashIconify(icon="solar:user-bold", color="#339af0"),
                                                        dmc.Text(id="espace-perso-user-email", fw=600, size="sm", c="dimmed")
                                                    ]
                                                )
                                            ]
                                        ),
                                        dmc.Button(
                                            "Se Déconnecter",
                                            id="espace-perso-logout-btn",
                                            color="red",
                                            variant="outline",
                                            radius="md",
                                            leftSection=DashIconify(icon="solar:logout-linear", width=16)
                                        )
                                    ]
                                )
                            ]
                        ),
                        
                        # Section Gestion des datasets
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
                                        dmc.Group(
                                            justify="space-between",
                                            children=[
                                                dmc.Title("Mes jeux de données importés", order=3, style={"color": "#2c3e50"}),
                                                dmc.Button(
                                                    "Importer un nouveau dataset",
                                                    id="espace-perso-goto-import-btn",
                                                    color="blue",
                                                    variant="light",
                                                    radius="md",
                                                    leftSection=DashIconify(icon="solar:cloud-upload-bold-duotone", width=16)
                                                )
                                            ]
                                        ),
                                        dmc.Divider(my="sm"),
                                        html.Div(id="espace-perso-datasets-table-container")
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)

# --- Callbacks ---

# 1. Gestion de la visibilité des blocs & Rendu du tableau dynamique des datasets
@callback(
    [Output("espace-perso-login-container", "style"),
     Output("espace-perso-dashboard-container", "style"),
     Output("espace-perso-user-email", "children"),
     Output("espace-perso-datasets-table-container", "children")],
    [Input("session-store", "data"),
     Input("dataset-refresh-trigger", "data")],
    [State('url', 'pathname')]
)
def sync_espace_perso_view(session_data, refresh_trigger, pathname):
    if pathname != '/espace-perso':
        raise dash.exceptions.PreventUpdate
    if not session_data or not session_data.get("authenticated"):
        return {"display": "block"}, {"display": "none"}, "", ""
        
    email = session_data.get("email", "")
    id_token = session_data.get("idToken")
    uid = session_data.get("uid")
    
    # Récupérer les jeux de données disponibles
    res = get_available_datasets(id_token=id_token, uid=uid)
    if not res["success"]:
        error_msg = res.get("error", "Erreur lors de la récupération des datasets.")
        error_view = dmc.Stack(
            align="center",
            py="xl",
            gap="sm",
            children=[
                DashIconify(icon="solar:danger-bold-duotone", width=48, color="red"),
                dmc.Text("Votre session a expiré ou est invalide.", fw=600, size="md", c="red"),
                dmc.Text(error_msg, size="xs", c="dimmed", ta="center"),
                dmc.Button(
                    "Se reconnecter",
                    id={"type": "espace-perso-reauth-btn", "index": "main"},
                    color="blue",
                    variant="filled",
                    radius="md",
                    leftSection=DashIconify(icon="solar:login-2-linear", width=16)
                )
            ]
        )
        return {"display": "none"}, {"display": "block"}, email, error_view
        
    datasets = res.get("datasets", [])
    # Filtrer uniquement les datasets appartenant à l'utilisateur connecté
    user_datasets = [d for d in datasets if d.get("owner_uid") == uid]
    
    if not user_datasets:
        empty_view = dmc.Stack(
            align="center",
            py="xl",
            gap="sm",
            children=[
                DashIconify(icon="solar:database-linear", width=48, color="gray"),
                dmc.Text("Vous n'avez importé aucun jeu de données pour le moment.", c="dimmed", size="sm"),
                dmc.Button(
                    "Déposer mon premier fichier",
                    id={"type": "empty-import-btn", "index": "espace-perso"},
                    color="blue",
                    variant="filled",
                    radius="md",
                    leftSection=DashIconify(icon="solar:upload-linear")
                )
            ]
        )
        return {"display": "none"}, {"display": "block"}, email, empty_view
        
    # Construire la table Mantine
    rows = []
    for d in user_datasets:
        doc_id = d.get("id")
        name = d.get("name", "Sans nom")
        scale = d.get("scale", "epci").upper()
        
        # Compter les indicateurs configurés
        cols_meta = d.get("columns_metadata", {})
        indicators = ", ".join([v.get("label", k) for k, v in cols_meta.items() if k not in ["CODE_EPCI", "EPCI_CODE", "CODE_COMMUNE"]])
        if not indicators:
            indicators = "Aucun indicateur spécifique"
            
        is_public = d.get("is_public", False)
        
        # Switch de visibilité interactif
        visibility_switch = dmc.Switch(
            id={"type": "dataset-visibility-switch", "index": doc_id},
            checked=is_public,
            color="teal",
            label="Public" if is_public else "Privé",
            size="sm",
            thumbIcon=DashIconify(icon="solar:global-linear" if is_public else "solar:lock-bold-duotone", width=12, color="teal" if is_public else "gray")
        )
        
        # Bouton supprimer
        delete_btn = dmc.ActionIcon(
            DashIconify(icon="solar:trash-bin-trash-bold", width=16),
            id={"type": "espace-perso-delete-btn", "index": doc_id},
            color="red",
            variant="light",
            radius="md",
            size="md"
        )
        
        rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Text(name, fw=500, size="sm")),
                dmc.TableTd(dmc.Badge(scale, color="blue" if scale == "EPCI" else "violet")),
                dmc.TableTd(dmc.Text(indicators, size="xs", c="dimmed", style={"maxWidth": "350px", "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"})),
                dmc.TableTd(visibility_switch),
                dmc.TableTd(delete_btn)
            ])
        )
        
    head = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Nom du Dataset"),
            dmc.TableTh("Échelle"),
            dmc.TableTh("Indicateurs détectés"),
            dmc.TableTh("Visibilité"),
            dmc.TableTh("Actions")
        ])
    )
    
    body = dmc.TableTbody(rows)
    table_widget = dmc.Table([head, body], highlightOnHover=True, withTableBorder=True, withColumnBorders=True)
    
    return {"display": "none"}, {"display": "block"}, email, table_widget

# 2. Callback de traitement de l'authentification (Connexion / Inscription)
@callback(
    [Output("session-store", "data", allow_duplicate=True),
     Output("auth-error-container", "children"),
     Output("url", "pathname", allow_duplicate=True)],
    Input("auth-submit-btn", "n_clicks"),
    [State("auth-tabs", "value"),
     State("auth-email", "value"),
     State("auth-password", "value")],
    prevent_initial_call=True
)
def handle_auth_submission(n_clicks, tab, email, password):
    if not n_clicks or not email or not password:
        return no_update, dmc.Alert("Veuillez remplir tous les champs.", color="red", radius="md"), no_update
        
    if tab == "login":
        res = login_user(email, password)
        if res["success"]:
            session_data = {
                "uid": res["uid"],
                "email": res["email"],
                "idToken": res["idToken"],
                "authenticated": True
            }
            # Rester sur la page espace-perso qui va charger le dashboard
            return session_data, None, "/espace-perso"
        else:
            return no_update, dmc.Alert(f"Erreur de connexion : {res['error']}", color="red", radius="md", title="Échec"), no_update
            
    elif tab == "register":
        res = signup_user(email, password)
        if res["success"]:
            session_data = {
                "uid": res["uid"],
                "email": res["email"],
                "idToken": res["idToken"],
                "authenticated": True
            }
            return session_data, None, "/espace-perso"
        else:
            return no_update, dmc.Alert(f"Erreur d'inscription : {res['error']}", color="red", radius="md", title="Échec"), no_update
            
    return no_update, no_update, no_update

# 3. Callback de Déconnexion / Réauthentification
@callback(
    [Output("session-store", "data", allow_duplicate=True),
     Output("url", "pathname", allow_duplicate=True)],
    [Input("espace-perso-logout-btn", "n_clicks"),
     Input({"type": "espace-perso-reauth-btn", "index": ALL}, "n_clicks")],
    prevent_initial_call=True
)
def handle_espace_perso_logout(n1, n2_list):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update
    trigger_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id_str == "espace-perso-logout-btn":
        if n1:
            return {"authenticated": False}, "/espace-perso"
            
    try:
        trigger_dict = json.loads(trigger_id_str)
        if trigger_dict.get("type") == "espace-perso-reauth-btn":
            if n2_list and any(n2_list):
                return {"authenticated": False}, "/espace-perso"
    except Exception as e:
        pass
        
    return no_update, no_update

# 4. Redirection vers Importation (Upload)
@callback(
    Output("url", "pathname", allow_duplicate=True),
    [Input("espace-perso-goto-import-btn", "n_clicks"),
     Input({"type": "empty-import-btn", "index": ALL}, "n_clicks")],
    prevent_initial_call=True
)
def goto_import_page(n1, n2_list):
    if n1 or (n2_list and any(n2_list)):
        return "/upload"
    return no_update

# 5. Modification dynamique de la visibilité d'un dataset
@callback(
    [Output("espace-perso-alert-container", "children", allow_duplicate=True),
     Output("dataset-refresh-trigger", "data", allow_duplicate=True)],
    Input({"type": "dataset-visibility-switch", "index": ALL}, "checked"),
    [State({"type": "dataset-visibility-switch", "index": ALL}, "id"),
     State("session-store", "data"),
     State("dataset-refresh-trigger", "data")],
    prevent_initial_call=True
)
def toggle_visibility(checked_list, id_list, session_data, current_refresh):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update
        
    triggered_prop = ctx.triggered[0]['prop_id']
    try:
        triggered_id_str = triggered_prop.split(".")[0]
        triggered_id = json.loads(triggered_id_str)
        doc_id = triggered_id["index"]
        
        # Trouver la valeur de checked pour ce document
        is_public = False
        for chk, idx in zip(checked_list, id_list):
            if idx["index"] == doc_id:
                is_public = bool(chk)
                break
                
        # Appel API Firebase de modification
        id_token = session_data.get("idToken")
        res = update_dataset_visibility(id_token, doc_id, is_public)
        
        if res["success"]:
            status_text = "Public (visible par tout le monde)" if is_public else "Privé (visible uniquement par vous)"
            alert = dmc.Alert(
                f"Statut mis à jour : le jeu de données est désormais {status_text}.",
                title="Modifié avec succès",
                color="green",
                radius="md",
                withCloseButton=True,
                icon=DashIconify(icon="solar:check-circle-bold")
            )
            next_refresh = (current_refresh or 0) + 1
            return alert, next_refresh
        else:
            return dmc.Alert(f"Échec de la modification : {res['error']}", color="red", radius="md", withCloseButton=True), no_update
    except Exception as e:
        return dmc.Alert(f"Une erreur est survenue : {str(e)}", color="red", radius="md", withCloseButton=True), no_update

# 6. Callback de gestion du modal de suppression depuis la table
@callback(
    [Output("delete-dataset-modal", "opened", allow_duplicate=True),
     Output("delete-dataset-temp-store", "data", allow_duplicate=True),
     Output("delete-dataset-modal-alert", "children", allow_duplicate=True)],
    [Input({"type": "espace-perso-delete-btn", "index": ALL}, "n_clicks"),
     Input("cancel-delete-dataset-btn", "n_clicks")],
    [State({"type": "espace-perso-delete-btn", "index": ALL}, "id"),
     State("available-datasets-store", "data")],
    prevent_initial_call=True
)
def manage_delete_modal_from_table(n_clicks_list, cancel_clicks, id_list, available_datasets):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, {}, []
        
    trigger_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id_str == "cancel-delete-dataset-btn":
        return False, {}, []
        
    try:
        trigger_dict = json.loads(trigger_id_str)
        if trigger_dict.get("type") == "espace-perso-delete-btn":
            # Vérifier si ce bouton a été réellement cliqué
            triggered_idx = -1
            for i, idx in enumerate(id_list):
                if idx == trigger_dict:
                    triggered_idx = i
                    break
            
            if triggered_idx != -1:
                n_clicks = n_clicks_list[triggered_idx]
                if not n_clicks: # None ou 0
                    return False, {}, []
            else:
                return False, {}, []
                
            doc_id = trigger_dict["index"]
            # Trouver les métadonnées du dataset ciblé
            target_dataset = {}
            for d in available_datasets:
                if d.get("id") == doc_id:
                    target_dataset = d
                    break
            return True, target_dataset, []
    except Exception as e:
        print(f"Error in delete modal from table trigger: {e}")
        
    return False, {}, []

"""
LodgePro Admin — Dashboard de gestion des clients.
Accès réservé à l'administrateur LodgePro.
"""
import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, date

st.set_page_config(
    page_title="LodgePro Admin",
    page_icon="🏖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Auth simple ────────────────────────────────────────────────────────────────
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD", "lodgepro2026"))

if not st.session_state.get("admin_logged_in"):
    st.markdown("""
    <div style='max-width:400px;margin:4rem auto;text-align:center'>
      <div style='font-size:56px'>🏖️</div>
      <h1 style='color:#1565C0'>LodgePro Admin</h1>
      <p style='color:#666'>Accès réservé</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("Mot de passe", type="password")
        if st.button("🔓 Connexion", type="primary", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state["admin_logged_in"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏖️ LodgePro Admin")
    st.divider()
    page = st.radio("Navigation", [
        "📊 Dashboard",
        "👥 Clients Particulier",
        "🏢 Clients Pro",
        "➕ Nouveau client",
        "🚀 Onboarding Pro",
        "📬 Demandes Pro",
        "🎯 Prospects démo",
        "📧 Emails",
        "💳 Abonnements",
        "⚙️ Paramètres",
    ], label_visibility="collapsed")
    st.divider()
    if st.button("🚪 Déconnexion"):
        st.session_state["admin_logged_in"] = False
        st.rerun()

# ── Base de données clients (Supabase LodgePro) ──────────────────────────────
SUPABASE_URL   = st.secrets.get("SUPABASE_URL",   os.environ.get("SUPABASE_URL", ""))
SUPABASE_KEY   = st.secrets.get("SUPABASE_KEY",   os.environ.get("SUPABASE_KEY", ""))
BREVO_API_KEY  = st.secrets.get("BREVO_API_KEY",  os.environ.get("BREVO_API_KEY", ""))
GITHUB_TOKEN   = st.secrets.get("GITHUB_TOKEN",   os.environ.get("GITHUB_TOKEN", ""))

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

def get_clients():
    if not SUPABASE_URL:
        return []
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/lodgepro_clients?select=*&order=created_at.desc",
                         headers=HEADERS_SB, timeout=10)
        return r.json() if r.status_code == 200 else []
    except: return []

def save_client(data):
    if not SUPABASE_URL:
        return False
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/lodgepro_clients",
                          headers=HEADERS_SB, json=data, timeout=10)
        return r.status_code in (200, 201)
    except: return False

def update_client(client_id, data):
    if not SUPABASE_URL:
        return False
    try:
        r = requests.patch(f"{SUPABASE_URL}/rest/v1/lodgepro_clients?id=eq.{client_id}",
                           headers=HEADERS_SB, json=data, timeout=10)
        return r.status_code in (200, 204)
    except: return False

def send_email_bienvenue(email, nom, app_url, login, password):
    if not BREVO_API_KEY:
        return False
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#1565C0;padding:24px;text-align:center">
        <h1 style="color:white;margin:0;font-size:28px">🏖️ Bienvenue sur LodgePro !</h1>
      </div>
      <div style="padding:28px;line-height:1.7">
        <p>Bonjour <b>{nom}</b>,</p>
        <p>Votre espace LodgePro est prêt. Voici vos accès :</p>
        <div style="background:#F4F7FF;border-radius:8px;padding:20px;margin:20px 0">
          <p style="margin:4px 0">🔗 <b>Votre app :</b> <a href="{app_url}">{app_url}</a></p>
          <p style="margin:4px 0">📧 <b>Login :</b> {login}</p>
          <p style="margin:4px 0">🔑 <b>Mot de passe provisoire :</b> {password}</p>
        </div>
        <p>De la réservation à la déclaration fiscale, tout en un clic.</p>
        <p style="text-align:center;margin:28px 0">
          <a href="{app_url}" style="background:#1565C0;color:white;padding:14px 28px;
             border-radius:8px;text-decoration:none;font-weight:bold">
            Accéder à mon espace →
          </a>
        </p>
        <p>L'équipe LodgePro</p>
      </div>
    </div>"""
    try:
        r = requests.post("https://api.brevo.com/v3/smtp/email",
            headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
            json={
                "sender": {"name": "LodgePro", "email": "c.trigano@gmail.com"},
                "to": [{"email": email, "name": nom}],
                "subject": "🏖️ Votre espace LodgePro est prêt !",
                "htmlContent": html,
            }, timeout=15)
        return r.status_code in (200, 201)
    except: return False

# ── PAGES ─────────────────────────────────────────────────────────────────────

if "📊 Dashboard" in page:
    st.title("📊 Dashboard LodgePro")
    clients = get_clients()

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    actifs    = [c for c in clients if c.get("statut") == "actif"]
    trials    = [c for c in clients if c.get("statut") == "trial"]
    inactifs  = [c for c in clients if c.get("statut") == "inactif"]
    mrr       = sum(c.get("prix_mensuel", 0) or 0 for c in actifs)

    k1.metric("👥 Clients actifs",    len(actifs))
    k2.metric("🔮 En essai",          len(trials))
    k3.metric("💶 MRR",               f"{mrr:,.0f} €")
    k4.metric("📊 Total clients",     len(clients))

    st.divider()

    if clients:
        df = pd.DataFrame(clients)
        cols = ["nom", "email", "app_url", "formule", "statut", "created_at"]
        cols_exist = [c for c in cols if c in df.columns]
        st.dataframe(df[cols_exist], use_container_width=True, hide_index=True,
                     column_config={
                         "nom":        "Client",
                         "email":      "Email",
                         "app_url":    "URL App",
                         "formule":    "Formule",
                         "statut":     "Statut",
                         "created_at": "Créé le",
                     })
    else:
        st.info("Aucun client pour l'instant. Créez votre premier client !")

elif "👥 Clients Particulier" in page:
    st.title("👥 Clients Particulier")
    clients = [c for c in get_clients() if c.get("type_client","particulier") != "pro"]

    if not clients:
        st.info("Aucun client.")
    else:
        for c in clients:
            statut_color = {"actif": "🟢", "trial": "🟡", "inactif": "🔴"}.get(c.get("statut",""), "⚪")
            with st.expander(f"{statut_color} {c.get('nom','?')} — {c.get('email','?')} — {c.get('formule','?')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**URL App :** {c.get('app_url','—')}")
                    st.markdown(f"**Formule :** {c.get('formule','—')}")
                    st.markdown(f"**Prix :** {c.get('prix_mensuel','—')} €/mois")
                with col2:
                    st.markdown(f"**Statut :** {c.get('statut','—')}")
                    st.markdown(f"**Propriétés :** {c.get('nb_proprietes','—')}")
                    st.markdown(f"**Créé le :** {str(c.get('created_at',''))[:10]}")

                # Changer statut
                new_statut = st.selectbox("Changer le statut",
                    ["actif", "trial", "inactif", "suspendu"],
                    index=["actif","trial","inactif","suspendu"].index(c.get("statut","trial")),
                    key=f"statut_{c['id']}")
                if st.button("💾 Mettre à jour", key=f"upd_{c['id']}"):
                    if update_client(c["id"], {"statut": new_statut}):
                        st.success("✅ Mis à jour !")
                        st.rerun()

elif "🏢 Clients Pro" in page:
    st.title("🏢 Clients Pro — Conciergeries")
    clients_pro = [c for c in get_clients() if c.get("type_client","particulier") == "pro"]

    if not clients_pro:
        st.info("Aucun client Pro pour l'instant.")
        st.markdown("Utilisez **➕ Nouveau client** en choisissant le type **Pro**.")
    else:
        for c in clients_pro:
            statut_color = {"actif":"🟢","trial":"🟡","inactif":"🔴"}.get(c.get("statut",""),"⚪")
            with st.expander(f"{statut_color} {c.get('nom','?')} — {c.get('email','?')} — {c.get('formule','?')} — {c.get('nb_proprietes',0)} propriétés"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**URL App :** {c.get('app_url','—')}")
                    st.markdown(f"**Formule :** {c.get('formule','—')}")
                    st.markdown(f"**Prix :** {c.get('prix_mensuel','—')} €/mois")
                with col2:
                    st.markdown(f"**Propriétés :** {c.get('nb_proprietes','—')}")
                    st.markdown(f"**Statut :** {c.get('statut','—')}")
                    st.markdown(f"**Créé le :** {str(c.get('created_at',''))[:10]}")
                with col3:
                    st.markdown(f"**Contacts :** {c.get('nb_employes',0) or 0} employés")
                    st.markdown(f"**Notes :** {c.get('notes','—') or '—'}")

                new_statut = st.selectbox("Changer statut",
                    ["actif","trial","inactif","suspendu"],
                    index=["actif","trial","inactif","suspendu"].index(c.get("statut","trial"))
                    if c.get("statut") in ["actif","trial","inactif","suspendu"] else 0,
                    key=f"statut_pro_{c['id']}")
                if st.button("💾 Mettre à jour", key=f"upd_pro_{c['id']}"):
                    if update_client(c["id"], {"statut": new_statut}):
                        st.success("✅ Mis à jour !")
                        st.rerun()

elif "➕ Nouveau client" in page:
    st.title("➕ Créer un nouveau client")
    st.caption("Remplis les informations du client — l'email de bienvenue sera envoyé automatiquement.")

    with st.form("form_nouveau_client"):
        c1, c2 = st.columns(2)
        with c1:
            nom     = st.text_input("Nom complet *", placeholder="Marie Dupont")
            email   = st.text_input("Email *", placeholder="marie@email.fr")
            tel     = st.text_input("Téléphone", placeholder="+33 6 12 34 56 78")
        with c2:
            formule = st.selectbox("Formule", ["Starter — 19€/mois", "Pro — 39€/mois", "Business — 79€/mois"])
            nb_prop = st.number_input("Nombre de propriétés", min_value=1, max_value=50, value=1)
            statut  = st.selectbox("Statut initial", ["trial", "actif"])

        st.divider()
        st.markdown("**Accès à l'application**")
        c3, c4 = st.columns(2)
        with c3:
            app_url  = st.text_input("URL de l'app *", placeholder="https://client-marie.streamlit.app")
            login    = st.text_input("Login (email)", value=email if email else "")
        with c4:
            password = st.text_input("Mot de passe provisoire", value="LodgePro2026!")
            notes    = st.text_area("Notes internes", height=80)

        envoyer_email = st.checkbox("📧 Envoyer l'email de bienvenue", value=True)

        submitted = st.form_submit_button("✅ Créer le client", type="primary", use_container_width=True)

        if submitted:
            if not nom or not email or not app_url:
                st.error("Nom, email et URL sont obligatoires.")
            else:
                prix_map = {
                    "Starter — 19€/mois": 19, "Pro — 39€/mois": 39, "Business — 79€/mois": 79,
                    "Starter Pro — 199€/mois": 199, "Business Pro — 399€/mois": 399,
                    "Enterprise — Sur mesure": 0
                }
                prix = prix_map.get(formule, 19)
                data = {
                    "nom": nom, "email": email, "telephone": tel,
                    "formule": formule.split(" — ")[0],
                    "prix_mensuel": prix,
                    "nb_proprietes": nb_prop,
                    "statut": statut,
                    "app_url": app_url,
                    "login": login or email,
                    "notes": notes,
                    "type_client": type_client,
                    "created_at": datetime.now().isoformat(),
                }
                if save_client(data):
                    st.success(f"✅ Client **{nom}** créé !")
                    if envoyer_email:
                        if send_email_bienvenue(email, nom, app_url, login or email, password):
                            st.success(f"📧 Email de bienvenue envoyé à {email}")
                        else:
                            st.warning("⚠️ Client créé mais email non envoyé.")
                    st.balloons()
                else:
                    st.warning("⚠️ Client créé localement (Supabase non configuré)")
                    if envoyer_email and email and app_url:
                        if send_email_bienvenue(email, nom, app_url, login or email, password):
                            st.success(f"📧 Email de bienvenue envoyé à {email}")

elif "🚀 Onboarding Pro" in page:
    st.title("🚀 Onboarding Client Pro")
    st.caption("Guide pas à pas pour configurer un nouveau client conciergerie.")

    # Sélectionner un client Pro existant ou créer
    clients_pro = [c for c in get_clients() if c.get("type_client") == "pro"]

    if not clients_pro:
        st.warning("Aucun client Pro existant. Créez d'abord un client Pro via **➕ Nouveau client**.")
    else:
        client_sel = st.selectbox(
            "Client à configurer",
            [c["id"] for c in clients_pro],
            format_func=lambda x: next((f"{c['nom']} — {c.get('formule','?')}" 
                                         for c in clients_pro if c["id"] == x), "?")
        )
        client = next((c for c in clients_pro if c["id"] == client_sel), {})

        st.markdown(f"""
        <div style='background:#EDE9FE;border-left:4px solid #7C3AED;padding:14px 18px;
                    border-radius:0 8px 8px 0;margin-bottom:20px'>
            <b style='color:#7C3AED'>{client.get('nom','')}</b> — 
            {client.get('formule','?')} — 
            {client.get('nb_proprietes',0)} propriétés prévues
        </div>
        """, unsafe_allow_html=True)

        # Étapes d'onboarding avec état
        etapes = [
            ("1", "Compte créé", "email" in client and bool(client.get("email"))),
            ("2", "URL app configurée", bool(client.get("app_url"))),
            ("3", "Email de bienvenue envoyé", client.get("statut") in ["actif","trial"]),
            ("4", "Propriétés importées", int(client.get("nb_proprietes",0) or 0) > 0),
            ("5", "Employés configurés", False),  # à vérifier
            ("6", "Formation effectuée", False),
        ]

        st.markdown("### Progression de l'onboarding")
        progress = sum(1 for _, _, done in etapes if done) / len(etapes)
        st.progress(progress, text=f"{int(progress*100)}% complété")
        st.markdown("")

        for num, label, done in etapes:
            icon = "✅" if done else "⏳"
            st.markdown(f"{icon} **Étape {num}** — {label}")

        st.divider()

        # Actions par étape
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📧 Bienvenue", "🏠 Propriétés", "👥 Employés", "📋 Templates", "✅ Validation"
        ])

        with tab1:
            st.subheader("Email de bienvenue personnalisé")
            nom_contact = st.text_input("Nom du contact", value=client.get("nom",""))
            app_url_val = st.text_input("URL de l'app", value=client.get("app_url",""))
            password_val = st.text_input("Mot de passe provisoire", value="LodgePro2026!")
            msg_perso = st.text_area("Message personnalisé", height=100,
                placeholder="Bienvenue dans l'équipe LodgePro ! Votre espace est configuré avec vos X propriétés...")

            if st.button("📧 Envoyer l'email de bienvenue Pro", type="primary",
                          use_container_width=True):
                html_pro = f"""
                <div style="font-family:Arial;max-width:600px;margin:auto">
                  <div style="background:#0B1F3A;padding:24px;text-align:center;border-radius:8px 8px 0 0">
                    <h1 style="color:white;margin:0;font-size:20px">LodgePro Pro</h1>
                    <p style="color:#F0B429;margin:4px 0 0;font-size:13px">Votre espace conciergerie est prêt</p>
                  </div>
                  <div style="padding:28px;background:#F8F9FF;line-height:1.7">
                    <p>Bonjour <b>{nom_contact}</b>,</p>
                    <p>{msg_perso or "Bienvenue sur LodgePro Pro ! Votre espace est configuré et prêt à l'emploi."}</p>
                    <div style="background:white;border-radius:8px;padding:20px;margin:20px 0;border:1px solid #E0E0E0">
                      <p><b>URL de votre espace :</b> <a href="{app_url_val}">{app_url_val}</a></p>
                      <p><b>Mot de passe provisoire :</b> {password_val}</p>
                    </div>
                    <h3>Vos prochaines étapes :</h3>
                    <ol>
                      <li>Connectez-vous et changez votre mot de passe</li>
                      <li>Ajoutez vos propriétés (onglet Propriétés)</li>
                      <li>Configurez votre équipe ménage (onglet Ménage)</li>
                      <li>Importez vos réservations existantes</li>
                    </ol>
                    <p>Notre équipe reste disponible pour vous accompagner.</p>
                    <p style="text-align:center;margin-top:24px">
                      <a href="{app_url_val}" style="background:#7C3AED;color:white;
                         padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold">
                        Accéder à mon espace Pro →
                      </a>
                    </p>
                  </div>
                </div>"""

                if send_email_bienvenue(client.get("email",""), nom_contact,
                                        app_url_val, client.get("email",""), password_val):
                    # Envoyer le vrai email personnalisé
                    if BREVO_API_KEY:
                        try:
                            requests.post("https://api.brevo.com/v3/smtp/email",
                                headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
                                json={
                                    "sender": {"name": "LodgePro Pro", "email": "c.trigano@gmail.com"},
                                    "to": [{"email": client.get("email",""), "name": nom_contact}],
                                    "subject": "Votre espace LodgePro Pro est prêt !",
                                    "htmlContent": html_pro,
                                }, timeout=15)
                        except: pass
                    st.success("✅ Email de bienvenue envoyé !")
                    update_client(client_sel, {"statut": "actif"})

        with tab2:
            st.subheader("Import des propriétés")
            st.markdown("**Option 1 — Import CSV**")
            st.caption("Format attendu : nom, adresse, ville, code_postal, signataire, tel_whatsapp")
            uploaded = st.file_uploader("Importer un CSV de propriétés", type=["csv"])
            if uploaded:
                import io
                df_import = pd.read_csv(io.StringIO(uploaded.read().decode("utf-8")))
                st.dataframe(df_import.head(10), use_container_width=True)
                st.success(f"✅ {len(df_import)} propriétés détectées")
                if st.button("📥 Importer dans l'app client", type="primary"):
                    st.info("Fonctionnalité à connecter à l'API Supabase du client.")

            st.divider()
            st.markdown("**Option 2 — Saisie du nombre de propriétés**")
            nb_actual = st.number_input("Nombre de propriétés importées", min_value=0,
                                         value=int(client.get("nb_proprietes",0) or 0))
            if st.button("💾 Mettre à jour", key="btn_nb_props"):
                update_client(client_sel, {"nb_proprietes": nb_actual})
                st.success("✅ Mis à jour !")

        with tab3:
            st.subheader("Configuration des employés")
            st.markdown("""
            Pour configurer les employés de cette conciergerie, voici les étapes dans l'app client :
            
            1. Connectez-vous à l'app client
            2. Allez dans **🧹 Ménage** → onglet **👥 Employés**
            3. Ajoutez chaque employé avec son taux horaire et contrat
            
            **Conseil :** Pour les conciergeries avec 10+ employés, 
            préparez un tableau Excel avec les colonnes : Prénom, Nom, Email, Téléphone, Taux horaire, Contrat
            """)

            nb_emp = st.number_input("Nombre d'employés configurés", min_value=0,
                                      value=int(client.get("nb_employes",0) or 0))
            if st.button("💾 Enregistrer", key="btn_nb_emp"):
                update_client(client_sel, {"nb_employes": nb_emp})
                st.success("✅ Mis à jour !")

        with tab4:
            st.subheader("Templates de messages")
            st.markdown("""
            Les templates de messages sont préconfigurés dans l'app. 
            
            Vérifiez avec le client qu'il souhaite personnaliser :
            - Le message de confirmation de réservation
            - Le message d'arrivée (J-3)
            - Le message post-départ avec questionnaire d'avis
            
            Ces templates se configurent dans **📧 Messages** → **📝 Modèles msgs** dans l'app client.
            """)
            notes_templates = st.text_area("Notes templates", 
                                            value=client.get("notes","") or "",
                                            placeholder="Ex: Client veut messages en français et anglais...")
            if st.button("💾 Sauvegarder les notes", key="btn_notes"):
                update_client(client_sel, {"notes": notes_templates})
                st.success("✅ Notes sauvegardées !")

        with tab5:
            st.subheader("Validation et mise en production")
            st.markdown("""
            **Checklist finale avant de valider l'onboarding :**
            """)

            checks = {
                "L'email de bienvenue a été envoyé": False,
                "Le client s'est connecté à son espace": False,
                "Au moins une propriété est configurée": int(client.get("nb_proprietes",0) or 0) > 0,
                "Les employés sont configurés": int(client.get("nb_employes",0) or 0) > 0,
                "Le client a testé l'import d'une réservation": False,
                "Le client a reçu sa formation": False,
            }

            all_done = True
            for check, done in checks.items():
                col_c, col_s = st.columns([4,1])
                col_c.markdown(f"{'✅' if done else '⬜'} {check}")
                if not done:
                    all_done = False

            st.markdown("")
            if all_done:
                st.success("🎉 Onboarding complet ! Le client est prêt.")
            else:
                st.warning("⚠️ Des étapes restent à compléter.")

            if st.button("🎉 Valider l'onboarding", type="primary",
                          use_container_width=True, disabled=not all_done):
                update_client(client_sel, {"statut": "actif"})
                st.success("✅ Client validé et actif !")
                st.balloons()

elif "🎯 Prospects démo" in page:
    st.title("🎯 Prospects démo")
    st.caption("Personnes qui ont accédé à la démo LodgePro et laissé leurs coordonnées.")

    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prospects_demo?select=*&order=created_at.desc",
                         headers=HEADERS_SB, timeout=10)
        prospects = r.json() if r.status_code == 200 else []
    except:
        prospects = []

    if not prospects:
        st.info("Aucun prospect pour l'instant.")
    else:
        k1, k2 = st.columns(2)
        k1.metric("👥 Total prospects", len(prospects))
        k2.metric("📞 À contacter", sum(1 for p in prospects if not p.get("contacte")))

        st.divider()
        df_p = pd.DataFrame(prospects)
        cols_p = ["nom","email","telephone","nb_proprietes","contacte","created_at"]
        cols_exist_p = [c for c in cols_p if c in df_p.columns]
        st.dataframe(df_p[cols_exist_p], use_container_width=True, hide_index=True,
                     column_config={
                         "nom":           "Nom",
                         "email":         "Email",
                         "telephone":     "Téléphone",
                         "nb_proprietes": "Nb propriétés",
                         "contacte":      st.column_config.CheckboxColumn("Contacté"),
                         "created_at":    "Date",
                     })

        st.divider()
        st.markdown("**Marquer comme contacté :**")
        prospect_emails = [p["email"] for p in prospects if not p.get("contacte")]
        if prospect_emails:
            email_sel = st.selectbox("Prospect", prospect_emails)
            if st.button("✅ Marquer comme contacté", type="primary"):
                try:
                    requests.patch(
                        f"{SUPABASE_URL}/rest/v1/prospects_demo?email=eq.{email_sel}",
                        headers=HEADERS_SB,
                        json={"contacte": True},
                        timeout=10
                    )
                    st.success("✅ Marqué comme contacté !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

elif "📧 Emails" in page:
    st.title("📧 Emails")
    clients = get_clients()
    if not clients:
        st.info("Aucun client.")
    else:
        dest = st.multiselect("Destinataires", [f"{c['nom']} <{c['email']}>" for c in clients])
        sujet = st.text_input("Sujet")
        corps = st.text_area("Message", height=200)
        if st.button("📤 Envoyer", type="primary"):
            ok = 0
            for d in dest:
                email_d = d.split("<")[1].rstrip(">")
                nom_d   = d.split("<")[0].strip()
                if send_email_bienvenue(email_d, nom_d, "", "", ""):
                    ok += 1
            st.success(f"✅ {ok} email(s) envoyé(s)")

elif "💳 Abonnements" in page:
    st.title("💳 Abonnements")

    st.markdown("#### 🔗 Liens de paiement Stripe")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.markdown("**Starter 19€** [Payer](https://buy.stripe.com/8x29ATg98davgCodUg6oo01)")
    col_s2.markdown("**Pro 39€** [Payer](https://buy.stripe.com/bJe5kD3mm2vRae0g2o6oo02)")
    col_s3.markdown("**Business 79€** [Payer](https://buy.stripe.com/4gM7sLe102vRcm84jG6oo03)")
    st.divider()
    clients = get_clients()
    actifs = [c for c in clients if c.get("statut") == "actif"]
    mrr    = sum(c.get("prix_mensuel", 0) or 0 for c in actifs)
    arr    = mrr * 12

    k1, k2, k3 = st.columns(3)
    k1.metric("💶 MRR", f"{mrr:,.0f} €")
    k2.metric("📅 ARR", f"{arr:,.0f} €")
    k3.metric("👥 Clients payants", len(actifs))

    st.divider()
    st.markdown("#### Répartition par formule")
    formules = {}
    for c in actifs:
        f = c.get("formule", "?")
        formules[f] = formules.get(f, 0) + 1
    PRIX_FORMULE = {"Starter": 19, "Pro": 39, "Business": 79}
    for f, nb in formules.items():
        prix = PRIX_FORMULE.get(f, 0)
        st.markdown(f"**{f}** : {nb} client(s) × {prix} € = **{nb * prix:,.0f} €/mois**")

elif "📬 Demandes Pro" in page:
    st.title("📬 Demandes de démo Pro")
    st.caption("Formulaires soumis depuis pro.lodgepro.eu")

    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/demandes_demo_pro?select=*&order=created_at.desc",
            headers=HEADERS_SB, timeout=10
        )
        demandes = r.json() if r.status_code == 200 else []
    except:
        demandes = []

    if not demandes:
        st.info("Aucune demande reçue pour l'instant.")
    else:
        k1, k2 = st.columns(2)
        k1.metric("📬 Total demandes", len(demandes))
        k2.metric("⏳ À traiter", sum(1 for d in demandes if not d.get("traite")))

        st.divider()

        for d in demandes:
            traite = d.get("traite", False)
            with st.expander(
                f"{'✅' if traite else '🔴'} {d.get('nom','?')} — {d.get('societe','?')} — "
                f"{d.get('nb_proprietes','?')} propriétés — {str(d.get('created_at',''))[:10]}"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Email :** {d.get('email','—')}")
                    st.markdown(f"**Téléphone :** {d.get('telephone','—') or '—'}")
                    st.markdown(f"**Société :** {d.get('societe','—') or '—'}")
                with col2:
                    st.markdown(f"**Propriétés :** {d.get('nb_proprietes','—')}")
                    st.markdown(f"**Date :** {str(d.get('created_at',''))[:16]}")

                if d.get('message'):
                    st.info(f"Message : {d['message']}")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if not traite:
                        if st.button("✅ Marquer traité", key=f"tr_{d['id']}"):
                            requests.patch(
                                f"{SUPABASE_URL}/rest/v1/demandes_demo_pro?id=eq.{d['id']}",
                                headers=HEADERS_SB, json={"traite": True}, timeout=10
                            )
                            st.rerun()
                with col_b:
                    st.markdown(f"[📧 Répondre](mailto:{d.get('email','')}?subject=Votre demande LodgePro Pro&body=Bonjour {d.get('nom','')},)")
                with col_c:
                    if st.button("➕ Créer client Pro", key=f"creer_{d['id']}"):
                        st.session_state["prefill_nom"]   = d.get("nom","")
                        st.session_state["prefill_email"] = d.get("email","")
                        st.info("Allez dans **➕ Nouveau client** pour créer le compte.")

elif "⚙️ Paramètres" in page:
    st.title("⚙️ Paramètres")
    st.info("Configurez les secrets dans Streamlit Cloud Settings.")
    st.markdown("**Secrets requis :**")
    secrets_list = ["ADMIN_PASSWORD", "SUPABASE_URL", "SUPABASE_KEY", "BREVO_API_KEY", "GITHUB_TOKEN"]
    for s in secrets_list:
        val = st.secrets.get(s, os.environ.get(s, ""))
        st.markdown(f"{'✅' if val else '❌'} `{s}`")

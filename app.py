import streamlit as st
import uuid
import os
import json
from agents import Runner
from agent import mon_agent
from upstash_redis import Redis
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(
    page_title="Chatbot Portfolio Lola",
    page_icon="🤖",
    layout="centered"
)


# connexion redis
@st.cache_resource
def get_redis():
    try:
        return Redis(url=os.getenv("UPSTASH_REDIS_REST_URL"), token=os.getenv("UPSTASH_REDIS_REST_TOKEN"))
    except:
        return None

redis = get_redis()

# sidebar
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.session_created_at = datetime.now().strftime("%d/%m/%Y %H:%M")

def charger_historique(key):
    if redis:
        data = redis.get(key)
        if data:
            return json.loads(data)
    return []

# sidebar
with st.sidebar:
    st.image("./img/photo_lola.jpg", width=105)
    st.header("Lola Dixneuf")
    st.caption("Data Science @ SNCF Voyageurs")
    
    # 1. GESTION DE L'HISTORIQUE (Bonus "ChatGPT style")
    st.divider()
    st.subheader("Conversations")
    
    if redis:
        # On récupère toutes les clés qui commencent par "chat:"
        try:
            keys = redis.keys("chat:*")
            
            # Récupérer les métadonnées de chaque session
            sessions_metadata = {}
            for k in keys:
                meta_key = f"meta:{k}"
                meta_data = redis.get(meta_key)
                if meta_data:
                    sessions_metadata[k] = json.loads(meta_data).get("created_at", "Date inconnue")
                else:
                    sessions_metadata[k] = "Date inconnue"
            
            # Bouton pour nouvelle conversation
            if st.button("Nouvelle conversation", use_container_width=True):
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.session_created_at = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.session_state.messages = []
                st.rerun()

            # Liste déroulante des sessions existantes
            selected_key = st.selectbox(
                "Historique", 
                options=keys, 
                format_func=lambda x: sessions_metadata.get(x, "Date inconnue"),
                index=None,
                placeholder="Choisir une ancienne session..."
            )
            
            # Si on sélectionne une ancienne session, on la charge
            if selected_key:
                st.session_state.session_id = selected_key.replace("chat:", "")
                st.session_state.messages = charger_historique(selected_key)
                # Charger aussi la date de création
                meta_data = redis.get(f"meta:{selected_key}")
                if meta_data:
                    st.session_state.session_created_at = json.loads(meta_data).get("created_at", "Date inconnue")
                
        except Exception as e:
            st.warning("Redis non accessible pour l'historique.")
    
    # 2. FORMULAIRE DE CONTACT (Pour aider le Tool)
    st.divider()
    with st.expander("Me contacter"):
        st.caption("Remplissez ce formulaire pour que le bot enregistre vos infos.")
        with st.form("contact_form"):
            f_nom = st.text_input("Nom")
            f_email = st.text_input("Email")
            f_motif = st.selectbox("Motif", ["Recrutement", "Alternance", "Information", "Autre"])
            submit_btn = st.form_submit_button("Envoyer")
            
            if submit_btn and f_nom and f_email:
                prompt_contact = f"Je souhaite laisser mes coordonnées. Nom: {f_nom}, Email: {f_email}, Motif: {f_motif}"
                st.session_state.messages.append({"role": "user", "content": prompt_contact})
                st.rerun()

# logique principale

redis_key = f"chat:{st.session_state.session_id}"

# Initialisation locale si vide
if "messages" not in st.session_state:
    st.session_state.messages = []

# TITRE
st.title("Discutez avec le :green[portfolio] de Lola")
st.markdown("Posez des questions sur son **expérience**, ses **projets** ou laissez vos **coordonnées** !")
#st.caption(f"Session active : {st.session_state.session_id}")

# AFFICHAGE DES MESSAGES
for msg in st.session_state.messages:
    # On met une couleur verte pour l'assistant via l'avatar ou le background (natif limité)
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# zone de saisie
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and len(st.session_state.messages) % 2 != 0:
    user_input = st.session_state.messages[-1]["content"]
    process_now = True
else:
    user_input = st.chat_input("Posez une question sur mon parcours...")
    process_now = False

if user_input and not process_now:
    st.chat_message("user", avatar="👤").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    process_now = True

# traitement ia
if process_now:
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Réflexion en cours..."):
                
                historique_texte = ""
                # on prend les 4 derniers échanges pour ne pas saturer
                for m in st.session_state.messages[-5:]:
                    historique_texte += f"{m['role'].upper()}: {m['content']}\n"
                
                prompt_final = f"""
                Voici l'historique de la conversation :
                {historique_texte}
                
                Réponds à la dernière demande de l'USER en tenant compte de l'historique ci-dessus.
                """
                
                # Appel à l'agent
                try:
                    result = Runner.run_sync(mon_agent, prompt_final)
                    reponse = result.final_output
                except Exception as e:
                    reponse = f"Désolé, une erreur est survenue : {e}"
                
                st.markdown(reponse)
                
                # Si le bot confirme l'enregistrement, petite notif
                if "noté" in reponse.lower() or "enregistré" in reponse.lower():
                    st.toast("Coordonnées sauvegardées !", icon="")

        st.session_state.messages.append({"role": "assistant", "content": reponse})
        
        # SAUVEGARDE REDIS
        if redis:
            redis.set(redis_key, json.dumps(st.session_state.messages))
            # Sauvegarder aussi les métadonnées de la session
            meta_key = f"meta:{redis_key}"
            if not redis.get(meta_key):  # Seulement si ça n'existe pas encore
                redis.set(meta_key, json.dumps({
                    "created_at": st.session_state.get("session_created_at", datetime.now().strftime("%d/%m/%Y %H:%M"))
                }))

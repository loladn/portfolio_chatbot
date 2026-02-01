import streamlit as st
import uuid
import os
import json
from agents import Runner
from agent import mon_agent
from upstash_redis import Redis
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Chatbot Portfolio Lola",
    page_icon="🤖",
    layout="centered"
)

#connexion à Redis
try:
    redis = Redis(url=os.getenv("UPSTASH_REDIS_REST_URL"), token=os.getenv("UPSTASH_REDIS_REST_TOKEN"))
except Exception as e:
    st.error("Erreur de connexion à la base de données Redis.")
    redis = None

# gestion de la session utilisateur pour conserver l'historique de conversations
# on crée un ID unique pour l'utilisateur s'il n'existe pas, pour stocker son historique
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Clé pour retrouver l'historique dans Redis
redis_key = f"chat:{st.session_state.session_id}"

# sidebar pour un visuel plus pro
with st.sidebar:
    st.header("Lola Dixneuf")
    st.caption("Data Science @ SNCF Voyageurs")
    st.image("https://api.dicebear.com/9.x/toon-head/svg?seed=Jade&beard=chin&beardProbability=0&clothes=shirt,tShirt&eyebrows=neutral&eyes=happy&hair=bun&hairColor=2c1b18&mouth=smile&rearHair=longWavy&skinColor=f1c3a5", width=150)
    st.divider()
    st.markdown("### Fonctionnalités")
    st.info("Ce chatbot utilise une mémoire persistante (Redis) et peut prendre vos messages (Tools).")
    
    # Bouton pour effacer l'historique
    if st.button("Effacer la conversation"):
        if redis:
            redis.delete(redis_key)
        st.session_state.messages = []
        st.rerun()

# chargement historique grâce à Redis
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Si Redis est connecté, on essaie de récupérer l'historique existant
    if redis:
        history = redis.get(redis_key)
        if history:
            st.session_state.messages = json.loads(history)

# titre principal
st.title("Discutez avec mon Portfolio")
st.markdown("Posez-moi des questions sur mon **expérience**, mes **projets** ou laissez-moi vos **coordonnées** !")

# affichage des messages
# on définit des avatars personnalisés pour le style
avatars = {"user": "👤", "assistant": "🤖"}

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=avatars.get(msg["role"])):
        st.markdown(msg["content"])

# interaction utilisateur
if question := st.chat_input("Ex: Sur quels projets as-tu travaillé ?"):
    
    # 1. Affichage et ajout message utilisateur
    st.chat_message("user", avatar="👤").markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    # 2. Réponse de l'IA
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analyse du portfolio en cours..."):
            result = Runner.run_sync(mon_agent, question)
            reponse = result.final_output
            st.markdown(reponse)
            
            # notification si un tool a été utilisé (détecté par mot clé dans la réponse)
            if "noté" in reponse or "enregistré" in reponse:
                st.toast("Action effectuée avec succès !", icon="🎉")

    # 3. Sauvegarde message assistant
    st.session_state.messages.append({"role": "assistant", "content": reponse})

    # 4. sauvegarde Redis (persistance)
    if redis:
        redis.set(redis_key, json.dumps(st.session_state.messages))
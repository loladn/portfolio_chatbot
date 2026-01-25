import streamlit as st
from agents import Runner
from agent import mon_agent

st.title("Chatbot Portfolio Lola")

# historisation de la conversation grâce à une liste
if "messages" not in st.session_state:
    st.session_state.messages = []

# affichage des anciens messages à l'écran
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# interaction avec l'utilisateur en le laissant écrire
if question := st.chat_input("Posez votre question sur Lola..."):
    st.chat_message("user").markdown(question)
    st.session_state.messages.append({"role":"user", "content": question})

    # appel à l'ia pour afficher la réponse
    with st.chat_message("assistant"):
        with st.spinner("LolaBot cherche dans le portfolio..."):
            result = Runner.run_sync(mon_agent, question)
            reponse = result.final_output
            st.markdown(reponse)

    # sauvegarde de la réponse dans l'historique
    st.session_state.messages.append({"role": "assistant", "content": reponse})
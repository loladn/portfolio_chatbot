import os
from dotenv import load_dotenv
from upstash_vector import Index
from agents import Agent, Runner, function_tool

load_dotenv()

# connexion à upstash (donc là où on a stocké les vecteurs)
index = Index(url=os.getenv("UPSTASH_VECTOR_REST_URL"), token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"))

@function_tool
def rechercher_dans_docs(query: str) -> str:
    """
    Cherche les passages les plus pertinents dans le portfolio de Lola.
    
    Args:
        query: La question ou le sujet à rechercher
    
    Returns:
        Le contexte trouvé ou un message si rien n'est trouvé
    """

    try:
        res = index.query(data=query, top_k=3, include_data=True, include_metadata=True)
        contexte = "\n".join([f"Info: {r.data}" for r in res])
        return contexte if contexte else "Aucune information trouvée."
    except Exception as e:
        return f"Erreur technique : {e}"

mon_agent = Agent(name="Chatbot-Lola", instructions="""Tu es l'assistant virtuel du portfolio de Lola Dixneuf.
    
            Tes règles d'or pour la recherche :
            1. Ne cherche JAMAIS la question brute de l'utilisateur.
            2. Convertis la question en MOTS-CLÉS techniques pour la base de données.
            - Si on demande "Qui es-tu ?", cherche : "Biographie présentation profil Lola".
            - Si on demande "Tes compétences ?", cherche : "Compétences stack technique langages".
            - Si on demande "Tes projets ?", cherche : "Projets réalisations portfolio".
            
            Règles de réponse :
            - Base-toi UNIQUEMENT sur le contexte trouvé via l'outil.
            - Parle de Lola à la 3ème personne ("Elle...").
            - Si l'outil ne renvoie rien, excuse-toi poliment.
            """,
                  model="gpt-4.1-nano",
                  tools=[rechercher_dans_docs])

if __name__ == "__main__":
    # question = "Qui es-tu ?"
    # print(f"Question : {question}")
    # result = Runner.run_sync(mon_agent, question)
    # print(f"Réponse : {result.final_output}")

    print("Bienvenue dans le chatbot du portfolio de Lola. Posez une question !")
    while True:
        question = input("\n Vous : ")
        
        if question.lower() in ["exit", "quitter", "quit", "q", "stop"]:
            print("Au revoir !")
            break

        print("LolaBot est en train de réfléchir...")
        result = Runner.run_sync(mon_agent, question)
        print(f"LolaBot : {result.final_output}")
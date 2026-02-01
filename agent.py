    import os
    from dotenv import load_dotenv

    load_dotenv()


    from upstash_vector import Index
    from agents import Agent, Runner, function_tool


    # connexion à upstash (donc là où on a stocké les vecteurs)
    index = Index(url=os.getenv("UPSTASH_VECTOR_REST_URL"), token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"))

    @function_tool
    def rechercher_dans_docs(query: str) -> str:
        """
        Cherche les informations pertinentes dans le portfolio de Lola.
        
        Args:
            query: La question de l'utilisateur (utilisée directement pour la recherche sémantique)
        
        Returns:
            Le contexte trouvé ou un message si rien n'est trouvé
        """

        try:
            # Recherche avec plus de résultats pour un meilleur contexte
            res = index.query(data=query, top_k=5, include_data=True, include_metadata=True)
            
            if not res:
                return "Aucune information trouvée dans le portfolio."
            
            # Formater le contexte avec les sources pour plus de clarté
            contexte_parts = []
            for r in res:
                source = r.metadata.get('source', '').replace('data/', '').replace('.md', '')
                contexte_parts.append(f"[Source: {source}]\n{r.data}")
            
            return "\n\n".join(contexte_parts)
            
        except Exception as e:
            return f"Erreur lors de la recherche : {e}"

    mon_agent = Agent(
        name="Chatbot-Lola",
        instructions="""Tu es l'assistant virtuel du portfolio de Lola Dixneuf.

    Contexte de base :
    Lola est une étudiante de 19 ans en 3ème année de BUT Science des Données à Niort,
    en alternance chez SNCF Voyageurs à Tours. Elle est passionnée par la géomatique,
    la data science, et s'investit dans des projets associatifs et culturels.

    Comment répondre aux questions :
    1. Utilise TOUJOURS l'outil `rechercher_dans_docs` en lui passant directement la question de l'utilisateur
    2. Base ta réponse UNIQUEMENT sur le contexte retourné par l'outil
    3. Parle de Lola à la 3ème personne ("Elle", "Lola", "Son parcours", etc.)
    4. Sois concise, naturelle et chaleureuse dans tes réponses
    5. Si aucune information n'est trouvée, excuse-toi poliment et propose de poser une autre question

    Important : La recherche utilise l'embedding sémantique, donc passe la question telle quelle à l'outil.
    """,
        model="gpt-4.1-nano",
        tools=[rechercher_dans_docs]
    )

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
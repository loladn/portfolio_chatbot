import os
import glob
from dotenv import load_dotenv
from upstash_vector import Index

# Chargement des variables d'environnement depuis le .env
load_dotenv()

index = Index(url=os.getenv("UPSTASH_VECTOR_REST_URL"), token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"))

def main():
    """ fonction principale qui trouve les fichiers et renvoie les données"""
    files = glob.glob("data/*.md")
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            contenu = f.read()

        chunks_base = contenu.split('#')

        # on définit les vecteurs pour Upstash
        vect = []
        for i, texte in enumerate(chunks_base):
            if texte.strip():
                texte_clean = "#" + texte.strip()
                
                vect.append({"id": f"{file}_{i}", "data": texte_clean, "metadata": {"source": file}})

        if vect:
            index.upsert(vectors=vect)
            print(f"{len(vect)} morceaux envoyés pour {file}")


if __name__ == "__main__":
    main()
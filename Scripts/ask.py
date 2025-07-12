# ask_codeon.py
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ========================== CONFIG ==========================
print("🔧 Loading environment variables...")
load_dotenv()

print("🧠 Initializing embedding model for retrieval...")
embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

print("🔍 Loading FAISS vector database...")
vectordb = FAISS.load_local(
    "code_index_faiss",
    embedding,
    allow_dangerous_deserialization=True
)

retriever = vectordb.as_retriever(search_kwargs={"k": 10})

print("⚡ Initializing Gemini Flash model...")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ======================== MAIN LOGIC ========================

def ask_codeon(query: str):
    print(f"🗣️ Asking CodeOn: {query}")
    
    docs = retriever.invoke(query)
    if not docs:
        return "🚫 CodeOn couldn't find anything relevant in the code index."

    context = "\n\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(docs)])

    prompt = f"""
You are CodeOn, a CLI-based code improvement and debugging assistant.
Use the following code context to answer the user's question. Be concise, helpful, and insightful.

Code Context:
{context}

User Question:
{query}

Answer:
""".strip()

    print("🤖 Sending query to Gemini Flash...")
    response = model.generate_content(prompt)
    return response.text

# ========================= CLI USE ==========================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python ask_codeon.py \"<your question about the code>\"")
        sys.exit(1)

    user_query = sys.argv[1]
    answer = ask_codeon(user_query)
    print("\n📌 CodeOn's Answer:\n")
    print(answer)

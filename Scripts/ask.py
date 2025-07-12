import os
import sys
import json
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

# ========================= MEMORY ===========================
HISTORY_PATH = "chat_history.json"
MAX_HISTORY_LENGTH = 8  # Max past exchanges to keep before summarizing

def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def summarize_history(history):
    history_text = "\n\n".join(f"User: {q}\nCodeOn: {a}" for q, a in history)
    summarizer_prompt = f"""
You are a summarizer for CodeOn, a code assistant. Summarize the following conversation history into a concise summary preserving the user's needs, CodeOn's answers, and any follow-up context.

Conversation:
{history_text}

Summary:
""".strip()

    summary_response = model.generate_content(summarizer_prompt)
    return summary_response.text.strip()

# ======================== MAIN LOGIC ========================

def ask_codeon(query: str, history: list):
    print(f"🗣️ Asking CodeOn: {query}")
    
    docs = retriever.invoke(query)
    if not docs:
        return "🚫 CodeOn couldn't find anything relevant in the code index.", history

    code_context = "\n\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(docs)])

    if len(history) > MAX_HISTORY_LENGTH:
        summary = summarize_history(history)
        history = [("Previous conversation summary", summary)]

    history_text = "\n\n".join(f"User: {q}\nCodeOn: {a}" for q, a in history)

    prompt = f"""
You are CodeOn, a CLI-based code improvement and debugging assistant.
Answer the user based on the following code context and chat history.

Code Context:
{code_context}

Chat History:
{history_text}

New Question:
{query}

Answer:
""".strip()

    print("🤖 Sending query to Gemini Flash...")
    response = model.generate_content(prompt)
    answer = response.text.strip()

    history.append((query, answer))
    save_history(history)

    return answer, history

# ========================= CLI USE ==========================

if __name__ == "__main__":
    print("💬 Entering interactive CodeOn chat mode.")
    print("💡 Type 'exit' or 'quit' to end the session.\n")

    history = load_history()

    while True:
        user_query = input("🧑 You: ").strip()
        if user_query.lower() in ("exit", "quit"):
            print("👋 Exiting CodeOn. See you later!")
            break

        answer, history = ask_codeon(user_query, history)
        print("\n🤖 CodeOn:\n" + answer + "\n")

import os
import sys
import json
import re
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
    allow_dangerous_deserialization=True #will not work if I remove it, Pickle objects
)

retriever = vectordb.as_retriever(search_kwargs={"k": 10})

print("Initializing Gemini Flash model...")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ========================= MEMORY ===========================
HISTORY_PATH = "chat_history.json"
MAX_HISTORY_LENGTH = 8  # Max past exchanges to keep before summarizing

#context bloat is a genuine issue, this rectifies the problem to a large degree
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

# ======================== FIXING COMPONENT ========================

def propose_code_fix(file_path, issue_description):
    print(f"🛠️ Analyzing `{file_path}` for issue: {issue_description}")
    
    if not os.path.exists(file_path):
        print("❌ File not found.")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        original_code = f.read()

    # Prompt with clear description for the response
    fix_prompt = f"""
You are a coding assistant. A user has described an issue with the following Python file.

ISSUE DESCRIPTION:
{issue_description}

SOURCE CODE:
{original_code}

Please analyze the code and provide fixes. You must respond with a valid JSON object containing exactly two fields:

1. "proposed_changes": An array of change objects, each with:
   - "line": line number (integer)
   - "description": brief description of the change
   - "reason": explanation of why this change is needed

2. "fixed_code": The complete corrected source code as a string

Important: 
- Respond ONLY with valid JSON
- Do not include markdown formatting, explanations, or extra text
- Extremely important to ensure the JSON is properly formatted and escaped
- Keep descriptions concise (under 100 characters each)
- The fixed_code should be the complete working code
- Ensure all double quotes inside fixed_code are escaped as \"
- You must escape characters as needed so the entire response is valid JSON
- Do not use raw print("...") unless properly escaped


Example format:
{{
  "proposed_changes": [
    {{"line": 1, "description": "Add import statement", "reason": "Missing required import"}}
  ],
  "fixed_code": "complete code here"
}}
""".strip()

    try:
        print("🤖 Sending fix request to Gemini Flash...")
        response = model.generate_content(fix_prompt)
        raw_response = response.text.strip()
        
        # Clean up the response
        cleaned_response = clean_json_response(raw_response)
        
        # Parse the JSON
        fix_data = json.loads(cleaned_response)
        
        # Validate the response structure
        if not validate_fix_response(fix_data):
            print("❌ Invalid response structure from LLM.")
            return None
            
        return fix_data
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response. Error: {e}")
        print(f"Raw response (first 500 chars): {raw_response[:500]}...")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def clean_json_response(raw_response):
    """Clean and extract JSON from LLM response"""
    # Remove markdown formatting
    cleaned = raw_response.strip()
    
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]  # Remove ```json
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]   # Remove ```
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]  # Remove closing ```
    
    cleaned = cleaned.strip()
    
    # Find JSON object boundaries
    start_idx = cleaned.find('{')
    if start_idx == -1:
        raise ValueError("No JSON object found in response")
    
    # Find the matching closing brace
    brace_count = 0
    end_idx = -1
    for i in range(start_idx, len(cleaned)):
        if cleaned[i] == '{':
            brace_count += 1
        elif cleaned[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break
    
    if end_idx == -1:
        raise ValueError("Incomplete JSON object in response")
    
    return cleaned[start_idx:end_idx + 1]

def validate_fix_response(fix_data):
    """Validate that the fix response has the required structure"""
    if not isinstance(fix_data, dict):
        return False
    
    if "proposed_changes" not in fix_data or "fixed_code" not in fix_data:
        return False
    
    if not isinstance(fix_data["proposed_changes"], list):
        return False
    
    if not isinstance(fix_data["fixed_code"], str):
        return False
    
    # Validate each change object
    for change in fix_data["proposed_changes"]:
        if not isinstance(change, dict):
            return False
        required_fields = ["line", "description", "reason"]
        if not all(field in change for field in required_fields):
            return False
    
    return True

#Actual function that is initially called when you ask for a fix
def run_fix_command(file_path, issue_description):
    """Run the fix command workflow"""
    fix_data = propose_code_fix(file_path, issue_description) #Calls the prompt creator that goes to the file and makes prompt and gets response
    if not fix_data:
        return

    #extracts the date from the json response
    changes = fix_data.get("proposed_changes", [])
    fixed_code = fix_data.get("fixed_code", "")

    if not changes:
        print("❌ No changes proposed.")
        return

    if not fixed_code.strip():
        print("❌ No fixed code provided.")
        return

    print("\n📋 Proposed Fixes:")
    for i, change in enumerate(changes, 1):
        line = change.get('line', 'N/A')
        description = change.get('description', 'No description')
        reason = change.get('reason', 'No reason provided')
        print(f"  {i}. Line {line}: {description}")
        print(f"     Reason: {reason}")

    print(f"\n📊 Total changes: {len(changes)}")
    
    # Show a preview of the fixed code (first few lines)
    preview_lines = fixed_code.split('\n')[:10]
    print("\n👀 Code preview (first 10 lines):")
    for i, line in enumerate(preview_lines, 1):
        print(f"  {i:2d}: {line}")
    if len(fixed_code.split('\n')) > 10:
        print(f"  ... and {len(fixed_code.split('\n')) - 10} more lines")

    confirm = input("\n✅ Apply these changes to the file? (yes/no): ").strip().lower()
    if confirm in ("yes", "y"):
        try:
            # Create a backup first
            backup_path = file_path + ".backup"
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original_content)
            print(f"💾 Backup created: {backup_path}")
            
            # Apply the changes
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            print("✅ Changes applied and file updated.")
            
        except Exception as e:
            print(f"❌ Error applying changes: {e}")
            # Restore from backup if something went wrong
            if os.path.exists(backup_path):
                with open(backup_path, "r", encoding="utf-8") as f:
                    backup_content = f.read()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(backup_content)
                print("🔄 File restored from backup.")
    else:
        print("🚫 No changes were made.")

# ========================= CLI USE ==========================

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "fix":
        if len(sys.argv) < 4:
            print("❌ Usage: python ask.py fix <file_path> <issue_description>")
            print("   Example: python ask.py fix script.py 'Add error handling'")
            sys.exit(1)
        file_path = sys.argv[2]
        issue_description = " ".join(sys.argv[3:])
        run_fix_command(file_path, issue_description)
    else:
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
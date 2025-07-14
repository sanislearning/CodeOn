import os
import sys
import json
import re
import difflib # Used to show the user a diff of the changes
from dotenv import load_dotenv
import google.generativeai as genai

# Required for existing chat mode, remove if only fixing stuff:
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ========================== CONFIG ==========================
print("🔧 Loading environment variables...")
load_dotenv()

# --- Existing Chat/RAG System Configuration ---
try:
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
except Exception as e:
    print(f"⚠️ Could not load FAISS vector database or embedding model. Chat functionality might be limited: {e}")
    retriever = None

print("Initializing Gemini Flash model...")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ========================= CHAT MODE ===========================
# This section remains unchanged.

HISTORY_PATH = "chat_history.json"
MAX_HISTORY_LENGTH = 8

def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("❌ Error loading chat history. Starting fresh.")
            return []
    return []

def save_history(history):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def summarize_history(history):
    history_text = "\n\n".join(f"User: {q}\nCodeOn: {a}" for q, a in history)
    summarizer_prompt = f"Summarize this conversation: {history_text}"
    summary_response = model.generate_content(summarizer_prompt)
    return summary_response.text.strip()

def ask_codeon(query: str, history: list):
    print(f"🗣️ Asking CodeOn: {query}")
    docs = []
    if retriever:
        docs = retriever.invoke(query)
    if not docs:
        code_context = "No specific code context available from vector database."
    else:
        code_context = "\n\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(docs)])
    if len(history) > MAX_HISTORY_LENGTH:
        summary = summarize_history(history)
        history = [("Previous conversation summary", summary)]
    history_text = "\n\n".join(f"User: {q}\nCodeOn: {a}" for q, a in history)
    prompt = f"You are CodeOn. Answer based on context and history.\n\nCode Context:\n{code_context}\n\nChat History:\n{history_text}\n\nNew Question:\n{query}\n\nAnswer:"
    print("🤖 Sending query to Gemini Flash...")
    response = model.generate_content(prompt)
    answer = response.text.strip()
    history.append((query, answer))
    save_history(history)
    return answer, history


# ======================== FIXING COMPONENT ========================

FILE_EXTENSIONS = ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rb', '.php', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.md', '.txt']

def get_codebase_files(path_or_dir):
    code_files = {}
    if os.path.isfile(path_or_dir):
        if any(path_or_dir.lower().endswith(ext) for ext in FILE_EXTENSIONS):
            try:
                with open(path_or_dir, "r", encoding="utf-8") as f:
                    code_files[os.path.abspath(path_or_dir)] = f.read()
                print(f"📂 Loaded single file: {path_or_dir}")
            except Exception as e:
                print(f"❌ Error reading file {path_or_dir}: {e}")
        else:
            print(f"⚠️ Skipping {path_or_dir}: Not a recognized code file extension.")
    elif os.path.isdir(path_or_dir):
        print(f"📂 Scanning directory: {path_or_dir}")
        for root, _, files in os.walk(path_or_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in FILE_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            code_files[os.path.abspath(file_path)] = f.read()
                    except Exception as e:
                        print(f"❌ Error reading file {file_path}: {e}")
        print(f"✅ Found {len(code_files)} code files in directory.")
    else:
        print(f"❌ '{path_or_dir}' is neither a file nor a directory.")
    return code_files

def generate_fix_proposal(code_files: dict, issue_description: str):
    if not code_files:
        print("🤷 No code files to process.")
        return None

    files_section_str = "\n".join(
        f"---FILE_START:{path}\n{content}\n---FILE_END:{path}" for path, content in code_files.items()
    )

    fix_prompt = f"""
You are an expert coding assistant. A user has a request to fix or refactor a codebase.

ISSUE DESCRIPTION:
{issue_description}

FULL CODEBASE:
{files_section_str}

Please analyze the code and provide the necessary fixes. Your response MUST be a single, valid JSON object.
The JSON object should have a single key "changes", which is an array of objects.
Each object in the array represents a file to be modified and must have the following three keys:
1. "file_path": The absolute path of the file to change (string).
2. "summary_of_changes": An array of objects, where each object describes a single, logical change within the file. Each change object must have:
   - "line": The approximate starting line number of the change (integer).
   - "description": A concise, one-sentence description of what was changed.
   - "reason": A brief explanation of why the change was necessary.
3. "fixed_code": The complete, new source code for the file as a single string.

EXAMPLE RESPONSE FORMAT:
{{
  "changes": [
    {{
      "file_path": "/path/to/your/script.py",
      "summary_of_changes": [
        {{
          "line": 15,
          "description": "Replaced a for-loop with a list comprehension for conciseness.",
          "reason": "Improves readability and is more idiomatic Python."
        }},
        {{
          "line": 42,
          "description": "Added error handling for the file open operation.",
          "reason": "Prevents the program from crashing if the file does not exist."
        }}
      ],
      "fixed_code": "import os\\n\\ndef new_function():\\n    # ... complete new content of the file ...\\n"
    }}
  ]
}}

IMPORTANT:
- Respond ONLY with the valid JSON object.
- Do not include markdown fences (```json), explanations, or any other text outside the JSON.
- Ensure all strings within the JSON, especially the "fixed_code", are properly escaped.
""".strip()

    try:
        print("🤖 Sending fix request to Gemini Flash...")
        #Added max_output_tokens to the generation config


        response = model.generate_content(
                        fix_prompt,
                        generation_config=genai.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=8192,
                            response_mime_type="application/json",  #This forces the response to be JSON only
                        )
                    )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Error during Gemini API call: {e}")
        return None

# ==============================================================================
# ======================= START OF REPLACEMENT =================================
# ==============================================================================

def parse_fix_proposal(raw_response: str):
    """
    A highly robust function to parse JSON from an LLM that may fail to properly
    escape quotes within its code blocks.
    """
    if not raw_response:
        print("❌ LLM returned an empty response.")
        return None

    # Clean potential markdown fences first, just in case.
    if raw_response.startswith("```json"):
        raw_response = raw_response[7:]
    if raw_response.endswith("```"):
        raw_response = raw_response[:-3]
    raw_response = raw_response.strip()

    try:
        # First, try to parse it directly. If it works, great!
        return json.loads(raw_response)
    except json.JSONDecodeError as e:
        print(f"⚠️ Initial JSON parse failed: {e}. Attempting robust extraction...")
        # The initial parse failed, so we'll try to fix the string.

    # This regex will find all instances of a "fixed_code" key and its value.
    # It uses a non-greedy match to capture everything until the next key or end of object.
    pattern = re.compile(r'"fixed_code":\s*"(.*?)"\s*(,|})', re.DOTALL)

    last_end = 0
    repaired_parts = []
    matches_found = 0

    for match in pattern.finditer(raw_response):
        matches_found += 1
        start, end = match.span()
        code_start, code_end = match.span(1)

        # Add the part of the string before this match
        repaired_parts.append(raw_response[last_end:code_start])

        # Get the captured code block
        code_block = match.group(1)

        # Escape the necessary characters for JSON
        # 1. Escape backslashes first!
        # 2. Escape double quotes.
        # 3. Escape other common control characters.
        escaped_code = code_block.replace('\\', '\\\\') \
                                 .replace('"', '\\"') \
                                 .replace('\n', '\\n') \
                                 .replace('\r', '\\r') \
                                 .replace('\t', '\\t')

        repaired_parts.append(escaped_code)

        # Update the last end position
        last_end = code_end
    
    if matches_found == 0:
        print("❌ No 'fixed_code' blocks found to repair. Parsing will likely fail.")
        # Fall through to the final parse attempt with the original string.
        repaired_json_str = raw_response
    else:
        # Add the remainder of the string after the last match
        repaired_parts.append(raw_response[last_end:])
        # Reassemble the string
        repaired_json_str = "".join(repaired_parts)


    try:
        # Now, try to parse the repaired string
        print("✅ Successfully repaired the JSON string. Parsing again...")
        return json.loads(repaired_json_str)
    except json.JSONDecodeError as final_e:
        print(f"❌❌ Final attempt to parse JSON failed even after repair. Error: {final_e}")
        print(f"--- Original Response (first 500 chars) ---\n{raw_response[:500]}...")
        print(f"--- Repaired Response (first 500 chars) ---\n{repaired_json_str[:500]}...")
        return None

# ==============================================================================
# ======================== END OF REPLACEMENT ==================================
# ==============================================================================

def display_diff(original_content: str, new_content: str):
    diff = difflib.unified_diff(
        original_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile='original',
        tofile='proposed',
    )
    for line in diff:
        if line.startswith('+'):
            print(f"\033[92m{line.strip()}\033[0m")  # Green
        elif line.startswith('-'):
            print(f"\033[91m{line.strip()}\033[0m")  # Red
        elif line.startswith('^'):
            print(f"\033[93m{line.strip()}\033[0m")  # Yellow
        else:
            print(line.strip())

def run_fix_command(path_or_dir: str, issue_description: str):
    print(f"🛠️ Analyzing '{path_or_dir}' for issue: {issue_description}")

    original_code_files = get_codebase_files(path_or_dir)
    if not original_code_files:
        return

    raw_proposal = generate_fix_proposal(original_code_files, issue_description)
    if not raw_proposal:
        return

    fix_data = parse_fix_proposal(raw_proposal)
    if not fix_data or not fix_data.get("changes"):
        print("💡 No changes were proposed by the AI.")
        return

    print("\n" + "="*80)
    print("📋 PROPOSED FIXES")
    print("="*80)

    for i, change in enumerate(fix_data["changes"], 1):
        file_path = change.get("file_path", "N/A")
        summary = change.get("summary_of_changes", [])
        fixed_code = change.get("fixed_code", "")

        print(f"\n[{i}/{len(fix_data['changes'])}] File: \033[1m{file_path}\033[0m")

        if not summary:
            print("   - No detailed summary provided.")
        for s in summary:
            print(f"   - \033[94mLine ~{s.get('line', '?')}:\033[0m {s.get('description', 'N/A')}")
            print(f"     \033[90mReason: {s.get('reason', 'N/A')}\033[0m")

        print("\n   --- DIFF ---")
        original_code = original_code_files.get(file_path, "")
        if not original_code:
            print(f"\033[93mWarning: Could not find original code for {file_path} to create a diff.\033[0m")
        elif original_code == fixed_code:
            print("\033[90m   (No difference in content)\033[0m")
        else:
            display_diff(original_code, fixed_code)
        print("   ------------")

    print("\n" + "="*80)
    confirm = input("✅ Apply ALL the changes listed above? (yes/no): ").strip().lower()

    if confirm not in ("yes", "y"):
        print("🚫 No changes were made.")
        return

    print("\nApplying changes...")
    for change in fix_data["changes"]:
        file_path = change["file_path"]
        fixed_code_escaped = change["fixed_code"]

        # --- THIS IS THE FIX ---
        # Decode the string to turn '\\n' into newlines and '\\"' into quotes
        fixed_code_decoded = fixed_code_escaped.encode().decode('unicode_escape')

        if not os.path.exists(file_path):
            print(f"⚠️ Skipped: File '{file_path}' does not exist.")
            continue

        try:
            # Backup first
            backup_path = file_path + ".backup_codeon"
            with open(file_path, "r", encoding="utf-8") as f_orig:
                with open(backup_path, "w", encoding="utf-8") as f_bak:
                    f_bak.write(f_orig.read())
            
            # Apply changes
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_code_decoded) # <--- Write the DECODED version
            print(f"✨ Successfully updated '{os.path.basename(file_path)}' (backup at {os.path.basename(backup_path)})")
        
        except Exception as e:
            print(f"❌ Error applying changes to {file_path}: {e}")

    print("\n🎉 Fix command completed.")


# ========================= CLI USE ==========================

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "fix":
        if len(sys.argv) < 4:
            print("❌ Usage: python v2.py fix <file_path_or_directory> <issue_description>")
            print("  Example: python v2.py fix my_script.py 'Add error handling'")
            print("  Example: python v2.py fix my_project/ 'Refactor main loop and add logging'")
            sys.exit(1)
        path_or_dir = sys.argv[2]
        issue_description = " ".join(sys.argv[3:])
        run_fix_command(path_or_dir, issue_description)
    else:
        print("💬 Entering interactive CodeOn chat mode.")
        print("💡 To use the fix command, run: python v2.py fix <file_or_dir> '<issue_description>'")
        print("💡 Type 'exit' or 'quit' to end the session.\n")

        history = load_history()

        while True:
            try:
                user_query = input("🧑 You: ").strip()
                if user_query.lower() in ("exit", "quit"):
                    print("👋 Exiting CodeOn. See you later!")
                    break
                answer, history = ask_codeon(user_query, history)
                print("\n🤖 CodeOn:\n" + answer + "\n")
            except KeyboardInterrupt:
                print("\n👋 Exiting CodeOn. See you later!")
                break

# 🧠 CodeOn

**CodeOn** is an intelligent CLI-based assistant that helps you **analyze**, **debug**, and **improve Python code** using large language models (LLMs). It combines semantic code search, conversational memory, and automatic fixing to streamline your development workflow.

> “Ask your code questions. Fix it automatically. All from your terminal.”

---

## 🚀 Features

* ✅ **LLM-powered code chat**: Ask what your code does or how to improve it
* 🧠 **Memory-aware conversations**: Retains past context without bloating prompts
* 🛠️ **Automatic fix suggestions**: Describe the issue, confirm the fix, and patch the code
* 🔍 **Code understanding with Tree-sitter + FAISS**: Parses code into structured chunks
* 📝 **Summarized history**: Smart truncation and summarization to keep context efficient
* 💾 **Safe editing**: Creates backups before overwriting files

---

## 📂 Folder Structure

```
CodeOn/
├── ask.py             # Main CLI for chat and fix modes
├── chunk.py           # Tree-sitter parser + FAISS indexer
├── chat_history.json  # Summarized memory for long-term context
├── index_metadata.json# Metadata for code chunks
├── .env               # API key config
├── ...
```

---

## 🔧 Setup

```bash
git clone https://github.com/yourusername/CodeOn.git
cd CodeOn
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create a `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key
```

---

## 🧠 Usage

### 🔹 Step 1: Index your code

Before you can ask questions or request fixes, index the Python file:

```bash
python chunk.py path/to/your_script.py
```

Example:

```bash
python chunk.py Scripts/Search/LinearSearch.py
```

> ✅ Code parsed and indexed with Tree-sitter + FAISS

---

### 🔹 Step 2: Talk to your code

Start the assistant:

```bash
python ask.py
```

Ask questions like:

```
🧑 You: What does my code do?
🧑 You: Can you point out inefficiencies?
🧑 You: How can I improve the structure?
```

Example response:

```
🤖 CodeOn:
Your code performs a linear search on a predefined list. It prompts the user for a key...
```

---

### 🔹 Step 3: Automatically fix issues

```bash
python ask.py fix path/to/file.py "Describe your fix here"
```

Example:

```bash
python ask.py fix Scripts/Search/LinearSearch.py "Make the code more efficient"
```

💬 Output:

```
📋 Proposed Fixes:
  1. Pass key as argument instead of input() inside function
  2. Add early return if list is empty
  3. Update function call with key

✅ Apply these changes to the file? (yes/no): yes
💾 Backup created: LinearSearch.py.backup
✅ Changes applied and file updated.
```

---

## 📌 Sample Before & After

### 🔻 Original Code

```python
def LinearSearch(list1):
    key = int(input())
    for i in range(0, len(list1)):
        if list1[i] == key:
            print(f"{key} found at index {i}")
            return
    print("Value not found")

list1 = [1, 2, 3, 4, 5]
LinearSearch(list1)
```

### 🔺 Improved Code (Auto-fixed by CodeOn)

```python
def LinearSearch(list1, key):
    if not list1:
        print("Value not found")
        return
    for i in range(len(list1)):
        if list1[i] == key:
            print(f"{key} found at index {i}")
            return
    print("Value not found")

list1 = [1, 2, 3, 4, 5]
key = int(input())
LinearSearch(list1, key)
```

---

## 💡 Tips

* Run `chunk.py` whenever you change or add a new Python file.
* You can re-run `ask.py` anytime to enter chat mode again.
* Fixes are safe: you get to preview and confirm before any code is changed.

---

## 🧱 Built With

* 🧩 [Tree-sitter](https://tree-sitter.github.io/)
* 🔍 [FAISS](https://github.com/facebookresearch/faiss)
* 🧠 [Gemini Flash API (Google Generative AI)](https://ai.google.dev/)
* 🤖 [LangChain](https://www.langchain.com/)
* 🐍 Python

---

## 🛣️ Roadmap

* [ ] Multi-file support and project-level understanding
* [ ] Integration with Git for version control-aware fixes
* [ ] VSCode extension for in-editor debugging
* [ ] Additional LLMs via [LiteLLM](https://github.com/BerriAI/litellm)

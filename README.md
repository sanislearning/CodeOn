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
* 📂 **Folder indexing**: Parse an entire folder (recursively) instead of just one file

---

## 📂 Folder Structure

```

CodeOn/
├── ask.py               # Main CLI for chat and fix modes
├── chunk.py             # Tree-sitter parser + FAISS indexer
├── chat\_history.json    # Summarized memory for long-term context
├── index\_metadata.json  # Metadata for code chunks
├── .env                 # API key config
├── ...

````

---

## 🔧 Setup

```bash
git clone https://github.com/yourusername/CodeOn.git
cd CodeOn
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
````

Create a `.env` file with your API key:

```env
GOOGLE_API_KEY=your_google_api_key
```

---

## 🧠 Usage

### 🔹 Step 1: Index your code

Before you can ask questions or request fixes, index your code with:

```bash
python chunk.py path/to/your_script.py
```

✅ Code is parsed and indexed with Tree-sitter + FAISS

#### 🗂 Index a whole folder

You can also index an **entire folder**:

```bash
python chunk.py path/to/your/folder/
```

This will recursively parse all `.py` files inside the folder and its subfolders.

---

### 🔹 Step 2: Talk to your code

Start the assistant:

```bash
python ask.py
```

Example conversation:

```
🧑 You: What does my code do?
🤖 CodeOn: Your code performs a linear search on a list. It prompts the user for a key...
🧑 You: How can I improve it?
🤖 CodeOn: You could pass the key as an argument instead of using input()...
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
  1. Pass key as argument instead of input()
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

* Re-run `chunk.py` after changing or adding new Python files
* You can enter chat mode anytime with `python ask.py`
* Fixes are non-destructive — backups are created before changes
* Chat history is stored and summarized for better LLM performance

---

## 🧱 Built With

* 🧩 [Tree-sitter](https://tree-sitter.github.io/)
* 🔍 [FAISS](https://github.com/facebookresearch/faiss)
* 🧠 [Gemini Flash API (Google Generative AI)](https://ai.google.dev/)
* 🤖 [LangChain](https://www.langchain.com/)
* 🐍 Python

---

## 🛣️ Roadmap

* [ ] Multi-file semantic reasoning
* [ ] Git integration for version-aware patching
* [ ] VSCode extension for real-time suggestions
* [ ] Support for more LLMs


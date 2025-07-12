import os
import sys
import json
from dotenv import load_dotenv
from tree_sitter import Language, Parser
import tree_sitter_python as tspython

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ========================== CONFIG ==========================
print("🔧 Loading environment variables...")
load_dotenv()

print("🧠 Initializing embedding model...")
embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

print("🌲 Setting up Tree-sitter Python parser...")
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

# ========================== HELPERS ==========================

def load_code_from_file(filepath):
    print(f"📂 Loading code from file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    print(f"✅ Code loaded from {filepath} ({len(code)} characters)")
    return code

def get_code_segment(code_bytes, node):
    return code_bytes[node.start_byte:node.end_byte].decode()

def extract_docstring_from_body(body_node, code_bytes):
    if len(body_node.children) > 0 and body_node.children[0].type == "expression_statement":
        expr_node = body_node.children[0]
        if expr_node.children and expr_node.children[0].type == "string":
            return get_code_segment(code_bytes, expr_node.children[0])
    return None

# ======================= CODE PARSING ========================

def extract_elements(code_str):
    print("🔍 Parsing code and extracting elements...")
    code_bytes = code_str.encode()
    tree = parser.parse(code_bytes)
    root_node = tree.root_node
    elements = []

    def walk(node, parent=None):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")
            body_node = node.child_by_field_name("body")

            name = get_code_segment(code_bytes, name_node)
            full_code = get_code_segment(code_bytes, node)
            docstring = extract_docstring_from_body(body_node, code_bytes)

            parent_context = name
            print(f"🔧 Found function: {name}")
            elements.append({
                "type": "function",
                "name": name,
                "code_chunk": full_code,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "parent": parent,
                "summary": docstring or "Function with no docstring"
            })
            for child in node.children:
                walk(child, parent_context)
            return

        elif node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            body_node = node.child_by_field_name("body")

            name = get_code_segment(code_bytes, name_node)
            full_code = get_code_segment(code_bytes, node)
            docstring = extract_docstring_from_body(body_node, code_bytes)

            summary = f"Class `{name}`"
            if docstring:
                summary += f": {docstring.strip('\"')}"
            else:
                summary += " with methods or properties."

            parent_context = name
            print(f"🏛️ Found class: {name}")
            elements.append({
                "type": "class",
                "name": name,
                "code_chunk": full_code,
                "summary": summary,
                "parent": parent
            })
            for child in node.children:
                walk(child, parent_context)
            return

        elif node.type == "expression_statement":
            child = node.children[0]
            if child.type == "comment":
                comment_text = get_code_segment(code_bytes, child)
                print(f"💬 Found comment")
                elements.append({
                    "type": "comment",
                    "code_chunk": comment_text,
                    "summary": f"Comment: {comment_text.strip('# ').strip()}",
                    "parent": parent
                })
            elif child.type == "call":
                call_text = get_code_segment(code_bytes, child)
                print(f"📞 Found function call")
                elements.append({
                    "type": "function_call",
                    "code_chunk": call_text,
                    "summary": f"Function call: {call_text}",
                    "parent": parent
                })

        elif node.type == "assignment":
            code_snippet = get_code_segment(code_bytes, node)
            print(f"📝 Found assignment")
            elements.append({
                "type": "assignment",
                "code_chunk": code_snippet,
                "summary": f"Variable assignment: {code_snippet}",
                "parent": parent
            })

        for child in node.children:
            walk(child, parent)

    walk(root_node)
    print(f"✅ Extracted {len(elements)} code elements")
    return elements

# ======================= FAISS INDEXING ========================

def build_faiss_from_chunks(chunks):
    print("🧠 Creating FAISS index from extracted chunks...")
    docs = [Document(page_content=chunk["code_chunk"], metadata=chunk) for chunk in chunks]
    vectordb = FAISS.from_documents(docs, embedding)
    vectordb.save_local("code_index_faiss")

    print("💾 Saving metadata to index_metadata.json...")
    with open("index_metadata.json", "w") as f:
        json.dump(chunks, f, indent=2)

    print(f"✅ Saved FAISS index and metadata for {len(docs)} chunks.")

# ============================ MAIN ============================

if __name__ == "__main__":
    print("🚀 Starting code indexing...")
    if len(sys.argv) < 2:
        print("❌ Usage: python code_indexer.py <path_to_python_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    code = load_code_from_file(filepath)
    elements = extract_elements(code)
    build_faiss_from_chunks(elements)
    print("🏁 Done!")

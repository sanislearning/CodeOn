import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from dotenv import load_dotenv
import google.generativeai as genai
import os
import sys
import json

#llm for code summarization
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model=genai.GenerativeModel('gemini-2.0-flash')

#parser that makes the AST tree
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

#code to load stuff from a file path we give
def load_code_from_file(filepath):
    with open(filepath,'r',encoding='utf-8') as f:
        return f.read()

def generate_summary(code_chunk):
    prompt=f"Explain clearly what this Python code does in a summarised and understandable manner :\n\n{code_chunk}"
    response=model.generate_content(prompt)
    return response.text.strip()

def get_code_segment(code_bytes, node):
    return code_bytes[node.start_byte:node.end_byte].decode()

def extract_docstring_from_body(body_node, code_bytes):
    if len(body_node.children) > 0 and body_node.children[0].type == "expression_statement":
        expr_node = body_node.children[0]
        if expr_node.children and expr_node.children[0].type == "string":
            return get_code_segment(code_bytes, expr_node.children[0])
    return None

def generate_file_summary(code_str):
    prompt = f"Summarize what this entire Python file is doing clearly and concisely:\n\n{code_str}"
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_summary_with_context(code_chunk, file_summary):
    prompt = (
        "You are analyzing a piece of Python code in the context of a larger program.\n"
        f"The entire file does the following:\n{file_summary}\n\n"
        f"Explain what the following specific code does in that context:\n\n{code_chunk}\n"
        "Respond clearly and concisely."
    )
    response = model.generate_content(prompt)
    return response.text.strip()


def extract_elements(code_str):
    file_summary = generate_file_summary(code_str)
    code_bytes = code_str.encode()
    tree = parser.parse(code_bytes) #creates a AST f the input code
    root_node = tree.root_node

    elements = []

    def walk(node,parent=None):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")
            body_node = node.child_by_field_name("body")

            name = get_code_segment(code_bytes, name_node)
            params = [
                get_code_segment(code_bytes, child)
                for child in params_node.children
                if child.type == "identifier"
            ]
            body_code = get_code_segment(code_bytes, body_node)
            full_code = get_code_segment(code_bytes, node)
            docstring = extract_docstring_from_body(body_node, code_bytes)

            parent_context = name  # use function name as parent
            elements.append({
                "type": "function",
                "name": name,
                "code_chunk": full_code,
                "summary": generate_summary_with_context(full_code, file_summary),
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "parent": parent
            })
            for child in node.children:
                walk(child, parent_context)
            return


        elif node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            body_node = node.child_by_field_name("body")

            name = get_code_segment(code_bytes, name_node)
            body_code = get_code_segment(code_bytes, body_node)
            full_code = get_code_segment(code_bytes, node)
            docstring = extract_docstring_from_body(body_node, code_bytes)

            summary = f"Class `{name}`"
            if docstring:
                summary += f": {docstring.strip('\"')}"
            else:
                summary += " with methods or properties."

            parent_context = name
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
                elements.append({
                    "type": "comment",
                    "code_chunk": comment_text,
                    "summary": f"Comment: {comment_text.strip('# ').strip()}",
                    "parent": parent
                })
            elif child.type == "call":
                call_text = get_code_segment(code_bytes, child)
                elements.append({
                    "type": "function_call",
                    "code_chunk": call_text,
                    "summary": f"Function call: {call_text}",
                    "parent": parent
                })




        elif node.type == "assignment":
            code_snippet = get_code_segment(code_bytes, node)
            elements.append({
                "type": "assignment",
                "code_chunk": code_snippet,
                "summary": f"Variable assignment: {code_snippet}",
                "parent": parent
            })


        # Recurse into child nodes
        for child in node.children:
            walk(child,parent)

    walk(root_node)
    return elements

if __name__=="__main__":
    if len(sys.argv)<2: #A list that holds the terminal message
        print("Add a file path after the trail1.py")
        sys.exit(1)

    filepath=sys.argv[1] #sys.argv[0] is the name of the python script
    #everything after is sys.argv[1]
    code=load_code_from_file(filepath) #waow actual file path
    elements=extract_elements(code)
    for elem in elements:
        print(json.dumps(elem,indent=2))
        print("-"*40)
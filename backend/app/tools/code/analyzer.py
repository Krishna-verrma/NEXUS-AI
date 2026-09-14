import ast
from typing import Dict, Any

def analyze_code_structure(code: str, language: str = "python") -> Dict[str, Any]:
    """Analyze code syntax, function count, class count, and potential issues."""
    if language.lower() == "python":
        try:
            tree = ast.parse(code)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            imports = [
                alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
            ] + [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) if node.module]

            return {
                "validSyntax": True,
                "language": "python",
                "lineCount": len(code.splitlines()),
                "functionCount": len(functions),
                "classCount": len(classes),
                "functions": functions[:10],
                "classes": classes[:10],
                "importedModules": list(set(imports)),
                "complexity": "Low" if len(functions) < 5 else "Medium"
            }
        except SyntaxError as e:
            return {
                "validSyntax": False,
                "language": "python",
                "error": f"SyntaxError at line {e.lineno}: {e.msg}"
            }
    
    # Generic analysis for TypeScript/JavaScript/others
    lines = code.splitlines()
    return {
        "validSyntax": True,
        "language": language,
        "lineCount": len(lines),
        "estimatedFunctions": len([l for l in lines if "function" in l or "=>" in l or "def " in l]),
        "notes": f"Generic structural inspection performed for {language} source."
    }

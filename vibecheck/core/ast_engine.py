import ast
from typing import List
from vibecheck.core.severity import Severity
from vibecheck.core.models import Issue

class AIHallucinationVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, lines: List[str]):
        self.filename = filename
        self.lines = lines
        self.issues: List[Issue] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # 1. Detect Mutable Default Arguments (The #1 AI Mistake)
        for arg in node.args.defaults:
            if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                line_idx = arg.lineno - 1
                self.issues.append(Issue(
                    pattern_name="Mutable Default Argument",
                    line_number=arg.lineno,
                    line_content=self.lines[line_idx].strip(),
                    description="Structural Match: A mutable object is used as a default argument. AI agents frequently hallucinate that this is safe state management.",
                    fix_hint="Use 'None' as default: def foo(data=None): data = data or {}",
                    severity=Severity.CRITICAL
                ))
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # 2. Detect Silent Agent Trap (except: pass)
        # Check if the body of the except block is JUST a 'pass' statement
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            line_idx = node.lineno - 1
            self.issues.append(Issue(
                pattern_name="Silent Agent Trap",
                line_number=node.lineno,
                line_content=self.lines[line_idx].strip(),
                description="Structural Match: An empty except-pass block detected. This is a common AI 'shortcut' to avoid crashing the agent loop.",
                fix_hint="Log the error or handle it properly instead of swallowing it.",
                severity=Severity.CRITICAL
            ))
        self.generic_visit(node)

def run_ast_audit(content: str, filename: str) -> List[Issue]:
    """Analyze Python code structure using AST for 100% precision."""
    try:
        tree = ast.parse(content)
        lines = content.splitlines()
        visitor = AIHallucinationVisitor(filename, lines)
        visitor.visit(tree)
        return visitor.issues
    except SyntaxError:
        # If code has syntax errors, we can't build AST. 
        # This is also a signal (AI often writes broken syntax).
        return []
    except Exception:
        return []

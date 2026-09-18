"""Safe deterministic calculator tool using AST parsing."""

import ast
import math
from typing import Any

from app.ai.tools.types import (
    ToolCategory,
    ToolDefinitionSchema,
    ToolParameterSchema,
)

SAFE_MATH_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
}

SAFE_MATH_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


class SafeEvalVisitor(ast.NodeVisitor):
    """Safely evaluates an AST representation of a mathematical expression."""

    def visit(self, node: ast.AST) -> Any:
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Expression contains unsupported operation: {type(node).__name__}")

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f"Only numeric constants are allowed, got: {type(node.value).__name__}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        elif isinstance(node.op, ast.USub):
            return -operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        elif isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
        elif isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left // right
        elif isinstance(node.op, ast.Mod):
            if right == 0:
                raise ZeroDivisionError("Modulo by zero")
            return left % right
        elif isinstance(node.op, ast.Pow):
            # Guard against resource exhaustion with huge exponents
            if abs(right) > 1000:
                raise ValueError("Exponent exceeds safe limit (|exp| <= 1000)")
            return left ** right
        raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")

    def visit_Name(self, node: ast.Name) -> Any:
        name = node.id
        if name in SAFE_MATH_CONSTANTS:
            return SAFE_MATH_CONSTANTS[name]
        raise ValueError(f"Unknown variable or constant: '{name}'")

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct safe function calls are allowed")
        func_name = node.func.id
        if func_name not in SAFE_MATH_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not in the safe math allowlist")

        args = [self.visit(arg) for arg in node.args]
        func = SAFE_MATH_FUNCTIONS[func_name]
        return func(*args)


def calculate(expression: str) -> dict[str, Any]:
    """Execute mathematical computation safely using AST traversal."""
    cleaned = expression.strip()
    if not cleaned:
        raise ValueError("Expression cannot be empty")
    if len(cleaned) > 500:
        raise ValueError("Expression length exceeds 500 characters")

    try:
        parsed = ast.parse(cleaned, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid math syntax: {str(e)}")

    visitor = SafeEvalVisitor()
    result = visitor.visit(parsed)

    # Format nicely
    if isinstance(result, float) and result.is_integer():
        formatted_result = int(result)
    else:
        formatted_result = result

    return {
        "expression": cleaned,
        "result": formatted_result,
        "type": type(formatted_result).__name__,
    }


CALCULATOR_TOOL = ToolDefinitionSchema(
    name="calculator",
    description="Safely evaluate mathematical and arithmetic expressions (e.g. 'sqrt(144) + 12 * 5', '2 ** 8', 'sin(pi / 2)').",
    category=ToolCategory.CALCULATOR,
    parameters=[
        ToolParameterSchema(
            name="expression",
            type="string",
            description="The mathematical formula or arithmetic expression to compute.",
            required=True,
        )
    ],
    requires_permission=None,
    is_sensitive=False,
    timeout_seconds=5.0,
)

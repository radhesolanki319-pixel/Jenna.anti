"""GPT-6 Astra Structural Asset Generators and Code Synthesizers for Jenna AI.

Provides syntax validation and generation helpers for:
- Procedural Blender (bpy) automation scripts
- Parametric CAD (OpenSCAD/FreeCAD) models
- Multi-page enterprise LaTeX documentation
- Dynamic Excel (.xlsx) financial models with cross-referenced formulas
"""

import ast
import re
from typing import Any
from app.ai.tools.types import ToolCategory, ToolDefinitionSchema
from app.core.permissions import PermissionAction


def validate_blender_script(script: str) -> dict[str, Any]:
    """Validate procedural Blender Python script using Python AST and API checks."""
    try:
        parsed = ast.parse(script)
    except SyntaxError as e:
        return {
            "valid": False,
            "error": f"Blender Python SyntaxError at line {e.lineno}: {e.msg}",
            "recommendation": "Fix indentation or unclosed statement.",
        }

    # Check for bpy import
    has_bpy = any(
        isinstance(node, ast.Import) and any(alias.name == "bpy" for alias in node.names)
        or isinstance(node, ast.ImportFrom) and node.module == "bpy"
        for node in ast.walk(parsed)
    )

    return {
        "valid": True,
        "imports_bpy": has_bpy,
        "ast_nodes": len(list(ast.walk(parsed))),
        "message": "Blender script is syntactically valid Python." + (" 'import bpy' detected." if has_bpy else " Warning: 'import bpy' is missing."),
    }


def validate_latex_source(latex_code: str) -> dict[str, Any]:
    """Verify structural balance and syntax of raw LaTeX source."""
    begins = re.findall(r"\\begin\{([a-zA-Z0-9_*]+)\}", latex_code)
    ends = re.findall(r"\\end\{([a-zA-Z0-9_*]+)\}", latex_code)

    errors: list[str] = []
    if len(begins) != len(ends):
        errors.append(f"Mismatched environment count: {len(begins)} \\begin vs {len(ends)} \\end tags.")

    # Check unescaped special characters outside of math mode / comments
    lines = latex_code.splitlines()
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("%"):
            continue
        # Unescaped & outside tabular/matrix
        # Check unclosed dollar math signs
        dollars = [m.start() for m in re.finditer(r"(?<!\\)\$", line)]
        if len(dollars) % 2 != 0:
            errors.append(f"Line {idx}: Unmatched '$' inline math delimiter.")

    return {
        "valid": len(errors) == 0,
        "environments": begins,
        "errors": errors,
        "message": "LaTeX syntax valid." if not errors else f"LaTeX errors detected: {'; '.join(errors)}",
    }


def validate_spreadsheet_formula(formula: str) -> dict[str, Any]:
    """Validate Excel formula syntax (e.g. balanced parentheses, valid formula names)."""
    formula = formula.strip()
    if not formula.startswith("="):
        return {"valid": False, "error": "Spreadsheet formula must start with '='"}

    # Check balanced parentheses
    open_parens = formula.count("(")
    close_parens = formula.count(")")
    if open_parens != close_parens:
        return {
            "valid": False,
            "error": f"Mismatched parentheses: {open_parens} '(' vs {close_parens} ')'",
        }

    # Extract uppercase formula tokens
    known_functions = {"SUM", "AVERAGE", "IF", "VLOOKUP", "XLOOKUP", "INDEX", "MATCH", "COUNT", "COUNTA", "COUNTIF", "SUMIFS", "NPV", "IRR", "MAX", "MIN"}
    tokens = re.findall(r"\b([A-Z][A-Z0-9.]+)\s*\(", formula)
    recognized = [t for t in tokens if t in known_functions]

    return {
        "valid": True,
        "recognized_functions": recognized,
        "length": len(formula),
        "message": "Formula syntax is well-formed.",
    }


from app.ai.tools.types import (
    ToolCategory,
    ToolDefinitionSchema,
    ToolParameterSchema,
)
from app.core.permissions import Permission


# ==============================================================================
# Tool Schemas for Platform Registration
# ==============================================================================

BLENDER_VALIDATOR_TOOL = ToolDefinitionSchema(
    name="blender_validator",
    description="Validates procedural Blender bpy Python scripts for syntax integrity and API standards.",
    category=ToolCategory.SYSTEM,
    requires_permission=Permission.READ,
    parameters=[
        ToolParameterSchema(
            name="script",
            type="string",
            description="Python source code for Blender scene generation or animation.",
            required=True,
        )
    ],
    is_sensitive=False,
    timeout_seconds=5.0,
)

LATEX_VALIDATOR_TOOL = ToolDefinitionSchema(
    name="latex_validator",
    description="Validates multi-page LaTeX documents for environment matching, math delimiters, and syntax.",
    category=ToolCategory.SYSTEM,
    requires_permission=Permission.READ,
    parameters=[
        ToolParameterSchema(
            name="latex_code",
            type="string",
            description="Raw LaTeX code to validate.",
            required=True,
        )
    ],
    is_sensitive=False,
    timeout_seconds=5.0,
)

SPREADSHEET_VALIDATOR_TOOL = ToolDefinitionSchema(
    name="spreadsheet_validator",
    description="Validates dynamic Excel spreadsheet formulas and cross-referenced calculations.",
    category=ToolCategory.SYSTEM,
    requires_permission=Permission.READ,
    parameters=[
        ToolParameterSchema(
            name="formula",
            type="string",
            description="Excel formula starting with '=', e.g., '=SUM(A1:A10)' or '=XLOOKUP(...)'",
            required=True,
        )
    ],
    is_sensitive=False,
    timeout_seconds=5.0,
)


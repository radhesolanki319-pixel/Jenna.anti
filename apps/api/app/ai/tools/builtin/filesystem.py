"""Scoped filesystem tools with strict directory boundary enforcement."""

import os
from pathlib import Path
from typing import Any

from app.ai.tools.types import (
    ToolCategory,
    ToolDefinitionSchema,
    ToolParameterSchema,
)
from app.core.permissions import Permission


# Default authorized root for scoped file operations (project root)
DEFAULT_WORKSPACE_ROOT = Path(os.getcwd()).resolve()


def _resolve_safe_path(requested_path: str, base_root: Path | None = None) -> Path:
    """Ensure requested path resolves strictly within the authorized directory root."""
    root = (base_root or DEFAULT_WORKSPACE_ROOT).resolve()
    target = (root / requested_path).resolve()

    # Path traversal check
    if not str(target).startswith(str(root)):
        raise PermissionError(
            f"Access denied: Requested path '{requested_path}' escapes the authorized workspace boundary '{root}'"
        )
    return target


def read_file(path: str, start_line: int | None = None, end_line: int | None = None, base_root: Path | None = None) -> dict[str, Any]:
    """Read contents of a file within authorized workspace root."""
    safe_path = _resolve_safe_path(path, base_root)

    if not safe_path.exists():
        raise FileNotFoundError(f"File not found: '{path}'")
    if not safe_path.is_file():
        raise ValueError(f"Path is not a regular file: '{path}'")

    # Guard against reading huge binary files
    stat = safe_path.stat()
    if stat.st_size > 5 * 1024 * 1024:
        raise ValueError(f"File size exceeds safe limit of 5MB ({stat.st_size} bytes)")

    with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total_lines = len(lines)
    s = max(1, start_line) if start_line is not None else 1
    e = min(total_lines, end_line) if end_line is not None else total_lines

    if s > total_lines:
        content = ""
    else:
        content = "".join(lines[s - 1:e])

    return {
        "path": path,
        "absolute_path": str(safe_path),
        "total_lines": total_lines,
        "start_line": s,
        "end_line": e,
        "content": content,
    }


def list_directory(path: str = ".", max_entries: int = 100, base_root: Path | None = None) -> dict[str, Any]:
    """List contents of a directory within authorized workspace root."""
    safe_path = _resolve_safe_path(path, base_root)

    if not safe_path.exists():
        raise FileNotFoundError(f"Directory not found: '{path}'")
    if not safe_path.is_dir():
        raise ValueError(f"Path is not a directory: '{path}'")

    entries = []
    for item in sorted(safe_path.iterdir()):
        if len(entries) >= max_entries:
            break
        try:
            stat = item.stat()
            entries.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size_bytes": stat.st_size if item.is_file() else None,
                "modified_time": stat.st_mtime,
            })
        except OSError:
            continue

    return {
        "directory": path,
        "entries": entries,
        "total_count": len(entries),
        "truncated": len(entries) >= max_entries,
    }


def write_file(path: str, content: str, overwrite: bool = False, base_root: Path | None = None) -> dict[str, Any]:
    """Write contents to a file within authorized workspace root."""
    safe_path = _resolve_safe_path(path, base_root)

    if safe_path.exists() and not overwrite:
        raise FileExistsError(f"File '{path}' already exists. Set overwrite=True to replace.")

    # Guard against huge writes
    if len(content.encode("utf-8")) > 5 * 1024 * 1024:
        raise ValueError("Write payload exceeds safe limit of 5MB")

    safe_path.parent.mkdir(parents=True, exist_ok=True)
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "path": path,
        "absolute_path": str(safe_path),
        "bytes_written": len(content.encode("utf-8")),
        "overwritten": safe_path.exists(),
        "status": "success",
    }


FILESYSTEM_READ_TOOL = ToolDefinitionSchema(
    name="filesystem_read",
    description="Read file contents within the authorized workspace with optional line ranges.",
    category=ToolCategory.FILESYSTEM,
    parameters=[
        ToolParameterSchema(name="path", type="string", description="Relative path to file inside workspace", required=True),
        ToolParameterSchema(name="start_line", type="integer", description="Starting line number (1-indexed)", required=False),
        ToolParameterSchema(name="end_line", type="integer", description="Ending line number (inclusive)", required=False),
    ],
    requires_permission=Permission.READ,
    is_sensitive=False,
    timeout_seconds=10.0,
)

FILESYSTEM_LIST_TOOL = ToolDefinitionSchema(
    name="filesystem_list",
    description="List files and directories in the workspace.",
    category=ToolCategory.FILESYSTEM,
    parameters=[
        ToolParameterSchema(name="path", type="string", description="Relative path of directory to inspect", required=False, default="."),
        ToolParameterSchema(name="max_entries", type="integer", description="Maximum number of items to return", required=False, default=100),
    ],
    requires_permission=Permission.READ,
    is_sensitive=False,
    timeout_seconds=10.0,
)

FILESYSTEM_WRITE_TOOL = ToolDefinitionSchema(
    name="filesystem_write",
    description="Write or overwrite text content to a file in the workspace. Sensitive action requiring authorization.",
    category=ToolCategory.FILESYSTEM,
    parameters=[
        ToolParameterSchema(name="path", type="string", description="Relative target path to write", required=True),
        ToolParameterSchema(name="content", type="string", description="Text content to write", required=True),
        ToolParameterSchema(name="overwrite", type="boolean", description="Whether to overwrite if file exists", required=False, default=False),
    ],
    requires_permission=Permission.WRITE,
    is_sensitive=True,
    timeout_seconds=15.0,
)

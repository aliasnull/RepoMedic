"""Zero-dependency TOML compatibility module for Python 3.10+.

Uses Python 3.11+ stdlib `tomllib` if available.
Falls back to `tomli` if installed on Python 3.10.
Falls back to a minimal pure-Python TOML parser for basic pyproject.toml structures
if neither is available, guaranteeing zero crashes and zero mandatory external dependencies.
"""
from __future__ import annotations

import re
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Python 3.10 with tomli
    except ImportError:
        tomllib = None  # Use minimal fallback


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if raw.isdigit():
        return int(raw)
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def _parse_minimal_toml(text: str) -> dict[str, Any]:
    """Minimal line-oriented TOML parser supporting tables, basic scalars, and string arrays."""
    root: dict[str, Any] = {}
    current_table = root
    
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        if not line or line.startswith("#"):
            continue
            
        # Table header: [section] or [section.subsection]
        if line.startswith("[") and line.endswith("]"):
            sec_name = line[1:-1].strip()
            parts = sec_name.split(".")
            curr = root
            for p in parts:
                p = p.strip()
                if p not in curr or not isinstance(curr[p], dict):
                    curr[p] = {}
                curr = curr[p]
            current_table = curr
            continue
            
        # Key = Value
        if "=" in line:
            key, val_part = line.split("=", 1)
            key = key.strip().strip('"\'')
            val_part = val_part.strip()
            
            # Array start: e.g. requires = [ ... ]
            if val_part.startswith("["):
                arr_tokens: list[str] = []
                accum = val_part
                while not accum.endswith("]") and i < len(lines):
                    next_line = lines[i].strip()
                    i += 1
                    accum += " " + next_line
                
                # Strip outside brackets
                inner = accum.strip()[1:-1].strip()
                items: list[Any] = []
                if inner:
                    # Parse comma-separated string literals or tokens
                    matches = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'|([^,]+)', inner)
                    for m in matches:
                        item = m[0] or m[1] or m[2]
                        item = item.strip()
                        if item and item != ",":
                            items.append(_parse_value(item))
                current_table[key] = items
            else:
                # Strip inline comment if any
                if "#" in val_part and not (val_part.startswith('"') and val_part.endswith('"')):
                    val_part = val_part.split("#", 1)[0].strip()
                current_table[key] = _parse_value(val_part)
                
    return root


def loads(s: str) -> dict[str, Any]:
    if tomllib is not None:
        return tomllib.loads(s)
    return _parse_minimal_toml(s)

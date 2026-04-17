"""
Citation utilities for referencing GB 50014-2021 standard.

This module resolves clause references to the actual markdown files bundled
under references/gb50014-2021/, including nested chapter directories.
"""

import os
import re
from functools import lru_cache
from typing import Optional


# Base path for GB 50014-2021 reference files
REFERENCE_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "references", "gb50014-2021"
)
REFERENCE_RELATIVE_ROOT = "references/gb50014-2021"


# Mapping of clause numbers to preferred reference file stems.
# Dynamic discovery below resolves the actual nested markdown path.
CLAUSE_FILE_MAPPING = {
    # Chapter 5: Water and drainage pipeline systems
    "5.2.2": "60-52-水力计算",
    "5.2.3": "60-52-水力计算",
    "5.2.4": "60-52-水力计算",
    "5.2.5": "60-52-水力计算",
    "5.2.6": "60-52-水力计算",
    "5.2.7": "60-52-水力计算",
    "5.2.10": "60-52-水力计算",
    "5.3": "212-53-管道",
    "5.3.1": "212-53-管道",
    "5.3.3": "212-53-管道",
    "5.3.4": "212-53-管道",
    "5.3.5": "212-53-管道",
    "5.3.7": "212-53-管道",
    "5.3.8": "212-53-管道",
    "5.3.9": "212-53-管道",
    "5.3.10": "212-53-管道",
    "5.3.11": "212-53-管道",
    "5.3.12": "212-53-管道",
    
    # Chapter 6: Pumping stations
    "6.1": "79-61-一般规定",
    "6.2": "80-62-设计流量和设计扬程",
    "6.3": "81-63-集水池",
    "6.4": "82-64-泵房设计",
    "6.4.2": "82-64-泵房设计",
    "6.5": "84-Ⅱ泵房",
    
    # Chapter 7: Treatment
    "7.1": "87-71-一般规定",
    "7.2": "89-73-格栅",
    "7.3": "90-74-沉砂池",
    "7.4": "91-75-沉淀池",
    "7.5": "101-76-活性污泥法",
    "7.6": "114-78-生物膜法",
    "7.7": "120-79-供氧设施",
    "7.10": "122-711-深度和再生处理",
    "7.11": "136-713-消毒",
    "7.12": "132-712-自然处理",
    
    # Chapter 8: Sludge
    "8.1": "141-81-一般规定",
    "8.2": "142-82-污泥浓缩",
    "8.3": "143-83-污泥消化",
    "8.4": "154-851-污泥机械脱水",
    "8.5": "155-852-污泥在脱水前应加药调理",
    
    # Chapter 4: Design flow and design water quality
    "4.1.7": "53-416-当地区改建时改建后相同设计重现期的径流量不得超过原径",
    "4.1.9": "54-419-设计暴雨强度应按下式计算",
    "4.1.11": "55-4110-暴雨强度公式应根据气候变化进行修订",
    "4.1.13": "56-Ⅱ污水量",
    "4.1.15": "56-Ⅱ污水量",

    # Default fallback
    "default": "06-室外排水设计标准",
}


CLAUSE_LINE_PATTERN = re.compile(
    r"^((?:附录\s*[A-Z](?:\.\d+(?:\.\d+)?)?)|(?:\d+(?:\.\d+)+(?:-\d+)?))\b"
)


def _normalize_clause_key(clause: str) -> str:
    return clause.strip().replace(" ", "")


def _format_clause_reference(clause: str) -> str:
    normalized = _normalize_clause_key(clause)
    if normalized.startswith("附录"):
        return normalized
    if normalized.count(".") == 1 and "-" not in normalized:
        return f"第{normalized}节"
    return f"第{normalized}条"


def _candidate_clause_keys(clause: str) -> list[str]:
    normalized = _normalize_clause_key(clause)
    candidates = [normalized]

    if "-" in normalized:
        candidates.append(normalized.rsplit("-", 1)[0])

    base = normalized
    while "." in base:
        base = base.rsplit(".", 1)[0]
        candidates.append(base)

    seen = set()
    ordered = []
    for item in candidates:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _reference_sort_key(relative_path: str) -> tuple[int, str]:
    basename = os.path.basename(relative_path)
    match = re.match(r"(\d+)-", basename)
    prefix = int(match.group(1)) if match else 10**9
    return prefix, relative_path


def _to_relative_reference_path(full_path: str) -> str:
    relative = os.path.relpath(full_path, REFERENCE_BASE_PATH).replace(os.sep, "/")
    return f"{REFERENCE_RELATIVE_ROOT}/{relative}"


def _normalize_file_hint(file_hint: str) -> str:
    normalized = file_hint.strip().replace("\\", "/")
    if normalized.startswith(f"{REFERENCE_RELATIVE_ROOT}/"):
        normalized = normalized[len(REFERENCE_RELATIVE_ROOT) + 1 :]
    return normalized


def _resolve_hint_to_full_path(file_hint: str) -> Optional[str]:
    normalized = _normalize_file_hint(file_hint)
    if not normalized:
        return None

    candidates = []
    if normalized.endswith(".md"):
        candidates.append(os.path.join(REFERENCE_BASE_PATH, normalized))
        stem = normalized[:-3]
        basename = os.path.basename(stem)
        candidates.append(os.path.join(REFERENCE_BASE_PATH, stem, f"{basename}.md"))
    else:
        candidates.append(os.path.join(REFERENCE_BASE_PATH, normalized))
        candidates.append(os.path.join(REFERENCE_BASE_PATH, f"{normalized}.md"))
        basename = os.path.basename(normalized)
        candidates.append(os.path.join(REFERENCE_BASE_PATH, normalized, f"{basename}.md"))

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate

    return None


@lru_cache(maxsize=1)
def _discover_clause_paths() -> dict[str, str]:
    discovered: dict[str, list[str]] = {}

    for root, dirs, files in os.walk(REFERENCE_BASE_PATH):
        dirs.sort()
        for filename in sorted(files):
            if not filename.endswith(".md"):
                continue

            full_path = os.path.join(root, filename)
            clause_key = None
            with open(full_path, "r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if line_number > 12:
                        break
                    match = CLAUSE_LINE_PATTERN.match(line.strip())
                    if match:
                        clause_key = _normalize_clause_key(match.group(1))
                        break

            if clause_key is None:
                continue

            relative_path = os.path.relpath(full_path, REFERENCE_BASE_PATH).replace(os.sep, "/")
            discovered.setdefault(clause_key, []).append(relative_path)

    resolved: dict[str, str] = {}
    for clause_key, candidates in discovered.items():
        resolved[clause_key] = min(candidates, key=_reference_sort_key)

    return resolved


def resolve_reference_relative_path(clause: str, file: Optional[str] = None) -> str:
    """Resolve a clause reference to a workspace-relative markdown path."""
    if file:
        resolved_file = _resolve_hint_to_full_path(file)
        if resolved_file:
            return _to_relative_reference_path(resolved_file)

    discovered = _discover_clause_paths()
    for candidate_clause in _candidate_clause_keys(clause):
        if candidate_clause in discovered:
            return f"{REFERENCE_RELATIVE_ROOT}/{discovered[candidate_clause]}"

        mapped_hint = CLAUSE_FILE_MAPPING.get(candidate_clause)
        if mapped_hint:
            resolved_file = _resolve_hint_to_full_path(mapped_hint)
            if resolved_file:
                return _to_relative_reference_path(resolved_file)

    fallback = _resolve_hint_to_full_path(CLAUSE_FILE_MAPPING["default"])
    if fallback is None:
        return f"{REFERENCE_RELATIVE_ROOT}/{CLAUSE_FILE_MAPPING['default']}.md"
    return _to_relative_reference_path(fallback)


def make_citation(clause: str, file: Optional[str] = None) -> str:
    """
    Create a standardized citation for GB 50014-2021.
    
    Args:
        clause: The clause number (e.g., "5.2.3", "6.3.1")
        file: Optional specific file path within references/gb50014-2021/
              If not provided, will try to determine from clause number
        
    Returns:
        Formatted citation string
        
    Example:
        >>> make_citation("5.2.3")
        'GB 50014-2021 第5.2.3条（见 references/gb50014-2021/60-52-水力计算/60-52-水力计算.md）'
    """
    # Validate clause format
    if not clause:
        raise ValueError("Clause cannot be empty")
    
    # Clean up clause - remove extra spaces
    clause = clause.strip()
    
    resolved_path = resolve_reference_relative_path(clause, file)
    citation = f"GB 50014-2021 {_format_clause_reference(clause)}（见 {resolved_path}）"
    
    return citation


def make_citation_from_section(section: str, clause: Optional[str] = None) -> str:
    """
    Create a citation from a section and optional clause.
    
    Args:
        section: Section number (e.g., "5.2")
        clause: Optional clause within the section (e.g., "3")
        
    Returns:
        Formatted citation string
        
    Example:
        >>> make_citation_from_section("5.2", "3")
        'GB 50014-2021 第5.2.3条（见 references/gb50014-2021/60-52-水力计算.md）'
    """
    if clause:
        full_clause = f"{section}.{clause}"
    else:
        full_clause = section
    
    return make_citation(full_clause)


def parse_clause_from_text(text: str) -> Optional[str]:
    """
    Extract a clause number from text using regex.
    
    Args:
        text: Text that may contain a clause reference
        
    Returns:
        Extracted clause number or None if not found
        
    Example:
        >>> parse_clause_from_text("根据第5.2.3条的规定")
        '5.2.3'
        >>> parse_clause_from_text("见5.2.4表5.2.3")
        '5.2.4'
    """
    # Pattern to match clause numbers like 5.2.3, 6.2.3-1, Appendix A, etc.
    pattern = r'((?:附录\s*[A-Z](?:\.\d+(?:\.\d+)?)?)|(?:\d+\.\d+(?:\.\d+)?(?:-\d+)?))'
    match = re.search(pattern, text)
    
    if match:
        return match.group(1)
    
    return None


def get_reference_path(clause: str) -> str:
    """
    Get the full file path for a given clause.
    
    Args:
        clause: Clause number
        
    Returns:
        Full path to the reference file
        
    Example:
        >>> get_reference_path("5.2.3")
        '.../references/gb50014-2021/60-52-水力计算/60-52-水力计算.md'
    """
    relative_path = resolve_reference_relative_path(clause)
    if relative_path.startswith(f"{REFERENCE_RELATIVE_ROOT}/"):
        suffix = relative_path[len(REFERENCE_RELATIVE_ROOT) + 1 :]
        return os.path.join(REFERENCE_BASE_PATH, suffix.replace("/", os.sep))
    return os.path.join(REFERENCE_BASE_PATH, relative_path.replace("/", os.sep))


def list_available_clauses() -> list:
    """Return list of clauses with known file mappings."""
    clauses = set(CLAUSE_FILE_MAPPING.keys())
    clauses.update(_discover_clause_paths().keys())
    return sorted(clauses)
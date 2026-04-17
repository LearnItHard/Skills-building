"""
Citation utilities for referencing GB 50014-2021 standard.

The skill now ships a compact reference bundle to avoid installer failures on
platforms that struggle with hundreds of tiny files. Clause citations resolve
to a small set of canonical markdown files under references/gb50014-2021/.
"""

import os
import re
from typing import Optional


# Base path for GB 50014-2021 reference files
REFERENCE_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "references", "gb50014-2021"
)
REFERENCE_RELATIVE_ROOT = "references/gb50014-2021"
DEFAULT_REFERENCE_FILE = "gb50014-2021-full.md"
APPENDIX_C_REFERENCE_FILE = "appendix-c-clearance.md"

SPECIAL_REFERENCE_HINTS = {
    "附录C": APPENDIX_C_REFERENCE_FILE,
    "净距": APPENDIX_C_REFERENCE_FILE,
    "181-附录C": APPENDIX_C_REFERENCE_FILE,
}


def _normalize_clause_key(clause: str) -> str:
    return clause.strip().replace(" ", "")


def _format_clause_reference(clause: str) -> str:
    normalized = _normalize_clause_key(clause)
    if normalized.startswith("附录"):
        return normalized
    if normalized.count(".") == 1 and "-" not in normalized:
        return f"第{normalized}节"
    return f"第{normalized}条"


def _build_relative_reference_path(filename: str) -> str:
    return f"{REFERENCE_RELATIVE_ROOT}/{filename}"


def _normalize_file_hint(file_hint: str) -> str:
    normalized = file_hint.strip().replace("\\", "/")
    if normalized.startswith(f"{REFERENCE_RELATIVE_ROOT}/"):
        normalized = normalized[len(REFERENCE_RELATIVE_ROOT) + 1 :]
    return normalized


def _resolve_hint_to_relative_path(file_hint: str) -> Optional[str]:
    normalized = _normalize_file_hint(file_hint)
    if not normalized:
        return None

    for marker, filename in SPECIAL_REFERENCE_HINTS.items():
        if marker in normalized:
            return _build_relative_reference_path(filename)

    candidate = normalized if normalized.endswith(".md") else f"{normalized}.md"
    candidate_path = os.path.join(REFERENCE_BASE_PATH, candidate.replace("/", os.sep))
    if os.path.isfile(candidate_path):
        return _build_relative_reference_path(candidate)

    if normalized.endswith(".md"):
        basename = os.path.basename(normalized)
        nested_candidate = os.path.join(REFERENCE_BASE_PATH, normalized[:-3], basename)
        if os.path.isfile(nested_candidate):
            return _build_relative_reference_path(normalized)

    return None


def resolve_reference_relative_path(clause: str, file: Optional[str] = None) -> str:
    """Resolve a clause reference to a workspace-relative markdown path."""
    if file:
        resolved_path = _resolve_hint_to_relative_path(file)
        if resolved_path:
            return resolved_path

    normalized_clause = _normalize_clause_key(clause)
    for marker, filename in SPECIAL_REFERENCE_HINTS.items():
        if marker in normalized_clause:
            return _build_relative_reference_path(filename)

    return _build_relative_reference_path(DEFAULT_REFERENCE_FILE)


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
        'GB 50014-2021 第5.2.3条（见 references/gb50014-2021/gb50014-2021-full.md）'
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
        'GB 50014-2021 第5.2.3条（见 references/gb50014-2021/gb50014-2021-full.md）'
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
        '.../references/gb50014-2021/gb50014-2021-full.md'
    """
    relative_path = resolve_reference_relative_path(clause)
    if relative_path.startswith(f"{REFERENCE_RELATIVE_ROOT}/"):
        suffix = relative_path[len(REFERENCE_RELATIVE_ROOT) + 1 :]
        return os.path.join(REFERENCE_BASE_PATH, suffix.replace("/", os.sep))
    return os.path.join(REFERENCE_BASE_PATH, relative_path.replace("/", os.sep))


def list_available_clauses() -> list:
    """Return representative clauses for the compact reference bundle."""
    return sorted(["附录C", "4.1.6", "4.1.7", "5.2.3", "6.2.4", "7.6.10", "8.3.6"])
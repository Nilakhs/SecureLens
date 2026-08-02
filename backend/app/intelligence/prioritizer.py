"""
prioritizer.py — Assigns internal action priority to each finding.

Priority is different from scanner severity.
Severity tells you HOW BAD the vulnerability is technically.
Priority tells you HOW URGENTLY a developer should act on it.

Example:
  "Hardcoded Test Password" can be HIGH severity from a scanner,
  but because it's likely a dev credential, its priority is HIGH (not IMMEDIATE).

  "SQL Injection" at HIGH severity → IMMEDIATE action needed.

Priority levels (highest → lowest):
    IMMEDIATE  — Drop everything, fix this now
    HIGH       — Fix before next release
    MEDIUM     — Fix in current sprint
    LOW        — Track and address over time
"""

# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------
PRIORITY_ORDER = ["IMMEDIATE", "HIGH", "MEDIUM", "LOW"]


# ---------------------------------------------------------------------------
# Priority matrix
# (canonical_category, severity) → priority
# If no exact match, falls back to severity-based default.
# ---------------------------------------------------------------------------
_PRIORITY_MATRIX = {
    # SQL Injection
    ("SQL Injection",         "CRITICAL"): "IMMEDIATE",
    ("SQL Injection",         "HIGH"):     "IMMEDIATE",
    ("SQL Injection",         "MEDIUM"):   "HIGH",
    ("SQL Injection",         "LOW"):      "MEDIUM",

    # Command Injection
    ("Command Injection",     "CRITICAL"): "IMMEDIATE",
    ("Command Injection",     "HIGH"):     "IMMEDIATE",
    ("Command Injection",     "MEDIUM"):   "HIGH",
    ("Command Injection",     "LOW"):      "MEDIUM",

    # Unsafe Deserialization
    ("Unsafe Deserialization","CRITICAL"): "IMMEDIATE",
    ("Unsafe Deserialization","HIGH"):     "IMMEDIATE",
    ("Unsafe Deserialization","MEDIUM"):   "HIGH",
    ("Unsafe Deserialization","LOW"):      "MEDIUM",

    # Code Execution
    ("Code Execution",        "CRITICAL"): "IMMEDIATE",
    ("Code Execution",        "HIGH"):     "IMMEDIATE",
    ("Code Execution",        "MEDIUM"):   "HIGH",
    ("Code Execution",        "LOW"):      "MEDIUM",

    # SSRF
    ("SSRF",                  "CRITICAL"): "IMMEDIATE",
    ("SSRF",                  "HIGH"):     "IMMEDIATE",
    ("SSRF",                  "MEDIUM"):   "HIGH",
    ("SSRF",                  "LOW"):      "MEDIUM",

    # Hardcoded Secrets — intentionally one step lower than SQLi
    ("Hardcoded Secrets",     "CRITICAL"): "IMMEDIATE",
    ("Hardcoded Secrets",     "HIGH"):     "HIGH",
    ("Hardcoded Secrets",     "MEDIUM"):   "MEDIUM",
    ("Hardcoded Secrets",     "LOW"):      "LOW",

    # Path Traversal
    ("Path Traversal",        "CRITICAL"): "IMMEDIATE",
    ("Path Traversal",        "HIGH"):     "HIGH",
    ("Path Traversal",        "MEDIUM"):   "MEDIUM",
    ("Path Traversal",        "LOW"):      "LOW",

    # XML Injection
    ("XML Injection",         "CRITICAL"): "IMMEDIATE",
    ("XML Injection",         "HIGH"):     "HIGH",
    ("XML Injection",         "MEDIUM"):   "MEDIUM",
    ("XML Injection",         "LOW"):      "LOW",

    # Input Validation
    ("Input Validation",      "CRITICAL"): "HIGH",
    ("Input Validation",      "HIGH"):     "HIGH",
    ("Input Validation",      "MEDIUM"):   "MEDIUM",
    ("Input Validation",      "LOW"):      "LOW",

    # Weak Cryptography
    ("Weak Cryptography",     "CRITICAL"): "HIGH",
    ("Weak Cryptography",     "HIGH"):     "MEDIUM",
    ("Weak Cryptography",     "MEDIUM"):   "MEDIUM",
    ("Weak Cryptography",     "LOW"):      "LOW",

    # Unsafe File Operations
    ("Unsafe File Operations","CRITICAL"): "HIGH",
    ("Unsafe File Operations","HIGH"):     "MEDIUM",
    ("Unsafe File Operations","MEDIUM"):   "LOW",
    ("Unsafe File Operations","LOW"):      "LOW",

    # Dependency Risk
    ("Dependency Risk",       "CRITICAL"): "IMMEDIATE",
    ("Dependency Risk",       "HIGH"):     "HIGH",
    ("Dependency Risk",       "MEDIUM"):   "MEDIUM",
    ("Dependency Risk",       "LOW"):      "LOW",
}

# Default priority by severity when category has no specific rule
_SEVERITY_DEFAULT = {
    "CRITICAL": "IMMEDIATE",
    "HIGH":     "HIGH",
    "MEDIUM":   "MEDIUM",
    "LOW":      "LOW",
    "INFO":     "LOW",
}


def assign_priority(finding: dict) -> str:
    """
    Return the internal priority for a finding.

    Args:
        finding: An enriched Finding dict (must have 'category' and 'severity').

    Returns:
        Priority string: "IMMEDIATE" | "HIGH" | "MEDIUM" | "LOW"
    """
    category = finding.get("category", "Other")
    severity = finding.get("severity", "LOW")

    # Try exact match from the matrix
    priority = _PRIORITY_MATRIX.get((category, severity))

    # Fall back to severity-based default
    if priority is None:
        priority = _SEVERITY_DEFAULT.get(severity, "LOW")

    return priority


def higher_priority(a: str, b: str) -> str:
    """Return whichever priority is higher (more urgent)."""
    idx_a = PRIORITY_ORDER.index(a) if a in PRIORITY_ORDER else len(PRIORITY_ORDER)
    idx_b = PRIORITY_ORDER.index(b) if b in PRIORITY_ORDER else len(PRIORITY_ORDER)
    return a if idx_a <= idx_b else b

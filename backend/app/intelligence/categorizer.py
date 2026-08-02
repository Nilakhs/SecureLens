"""
categorizer.py — Maps raw scanner output categories/rule IDs into SecureLens'
canonical vulnerability vocabulary.

Developers don't understand "B602" or "python.lang.security.audit.subprocess-shell-true".
They understand "Command Injection".

This module is the single source of truth for category names across the entire
application. Everything is keyword-based matching — no AI, fully deterministic.
"""

# ---------------------------------------------------------------------------
# Canonical category definitions
# Each entry: (canonical_name, [keywords_to_match])
# Matching is performed on: rule_id + category + title (all lowercased).
# First match wins.
# ---------------------------------------------------------------------------
_CATEGORY_RULES = [
    (
        "SQL Injection",
        ["sql", "sqli", "b608", "b610", "hardcoded_sql", "hardcoded-sql",
         "sql-injection", "sql_injection"],
    ),
    (
        "Command Injection",
        ["subprocess", "shell=true", "shell_true", "b602", "b603", "b604",
         "command-injection", "command_injection", "popen", "os.system",
         "os_system", "inject"],
    ),
    (
        "Hardcoded Secrets",
        ["hardcoded_password", "hardcoded-password", "hardcoded_bind",
         "b105", "b106", "b107", "secret", "password", "credential",
         "api_key", "apikey", "token", "private_key", "hardcoded"],
    ),
    (
        "Weak Cryptography",
        ["md5", "sha1", "des", "rc4", "b303", "b304", "b305", "b306",
         "weak-crypto", "weak_crypto", "insecure-hash", "insecure_hash",
         "weak-cipher", "blowfish"],
    ),
    (
        "Unsafe Deserialization",
        ["pickle", "yaml.load", "yaml_load", "b301", "b302", "b506",
         "deserialization", "unmarshalling", "marshal"],
    ),
    (
        "Code Execution",
        ["eval", "exec(", "b307", "b322", "code-execution", "code_execution",
         "arbitrary-code", "arbitrary_code", "rce"],
    ),
    (
        "Path Traversal",
        ["path-traversal", "path_traversal", "directory-traversal",
         "directory_traversal", "b101", "lfi", "open-redirect",
         "open_redirect", "traversal"],
    ),
    (
        "XML Injection",
        ["xml", "xpath", "xxe", "b405", "b406", "b408", "b409",
         "xml-injection", "xml_injection"],
    ),
    (
        "SSRF",
        ["ssrf", "server-side-request", "url-open", "urlopen",
         "request-forgery"],
    ),
    (
        "Unsafe File Operations",
        ["tempfile", "mktemp", "b108", "b110", "unsafe-file",
         "unsafe_file", "world-writable", "file-permission"],
    ),
    (
        "Input Validation",
        ["xss", "cross-site", "input-validation", "input_validation",
         "b610", "b611", "sanitize", "injection", "taint"],
    ),
    (
        "Dependency Risk",
        ["dependency", "package", "cve-", "outdated", "vulnerable-package",
         "npm-audit", "pip-audit"],
    ),
    (
        "Authentication",
        ["auth", "login", "session", "jwt", "token-expire",
         "brute-force", "password-reset"],
    ),
    (
        "Logging & Monitoring",
        ["log", "logging", "monitor", "audit-trail"],
    ),
]

# Fallback category when nothing matches
_FALLBACK_CATEGORY = "Other"


def canonicalize(finding: dict) -> str:
    """
    Return the canonical SecureLens category for a finding.

    Inspects rule_id, category, and title (all lowercased) for keyword matches.

    Args:
        finding: A normalized Finding dict from parser.py

    Returns:
        Canonical category string (e.g. "SQL Injection", "Command Injection")
    """
    # Build a single searchable string from all relevant fields
    search_text = " ".join([
        finding.get("rule_id",  "").lower(),
        finding.get("category", "").lower(),
        finding.get("title",    "").lower(),
    ])

    for canonical_name, keywords in _CATEGORY_RULES:
        for keyword in keywords:
            if keyword in search_text:
                return canonical_name

    return _FALLBACK_CATEGORY


def enrich_finding(finding: dict) -> dict:
    """
    Add canonical_category and preserve raw_category on a finding dict.
    Returns a new dict (does not mutate the original).
    """
    enriched = dict(finding)
    enriched["raw_category"] = finding.get("category", "")
    enriched["category"] = canonicalize(finding)
    return enriched

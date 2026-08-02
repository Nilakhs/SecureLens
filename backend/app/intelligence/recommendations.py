"""
recommendations.py — Curated, developer-friendly recommendations for each
canonical vulnerability category.

No AI. No external calls. Just a well-written static knowledge base.

Each recommendation tells the developer:
  1. What the problem is (one sentence)
  2. How to fix it (concrete action)
  3. The key principle behind the fix

This is a bonus feature today — it will become the foundation of
AI-enhanced recommendations in a future sprint.
"""

RECOMMENDATIONS: dict = {
    "SQL Injection": (
        "Never concatenate user input into SQL queries. "
        "Use parameterized queries or an ORM (e.g. SQLAlchemy) so the database "
        "driver handles escaping. "
        "Principle: treat user input as data, never as code."
    ),

    "Command Injection": (
        "Avoid shell=True in subprocess calls — it passes commands through the "
        "shell and enables injection. Pass arguments as a list instead: "
        "subprocess.run(['ls', '-la']). Validate and allowlist any user-controlled "
        "values before using them in system calls."
    ),

    "Hardcoded Secrets": (
        "Never store passwords, API keys, or tokens in source code. "
        "Use environment variables loaded via python-dotenv, or a dedicated secrets "
        "manager (AWS Secrets Manager, HashiCorp Vault). "
        "Add .env to .gitignore and rotate any leaked credentials immediately."
    ),

    "Weak Cryptography": (
        "Replace MD5 and SHA-1 with SHA-256 or SHA-3 for hashing. "
        "For passwords, use bcrypt, scrypt, or Argon2 — never plain hashes. "
        "For encryption, use AES-256-GCM. "
        "Avoid DES, RC4, and Blowfish entirely."
    ),

    "Unsafe Deserialization": (
        "Never deserialize data from untrusted sources using pickle, marshal, or "
        "yaml.load(). Use json.loads() for structured data. "
        "If YAML is required, use yaml.safe_load(). "
        "Deserialization of untrusted data can lead to remote code execution."
    ),

    "Code Execution": (
        "Avoid eval() and exec() on any user-supplied input. "
        "If dynamic evaluation is genuinely needed, use ast.literal_eval() for "
        "safe literal parsing. "
        "Consider redesigning the feature to avoid dynamic execution entirely."
    ),

    "Path Traversal": (
        "Always resolve and validate file paths before accessing them. "
        "Use os.path.realpath() to resolve symlinks, then check that the result "
        "starts with your intended base directory. "
        "Never pass raw user input directly to open(), os.path.join(), or similar."
    ),

    "XML Injection": (
        "Use a safe XML library that defends against XXE (XML External Entity) "
        "attacks by default, such as defusedxml. "
        "Disable DTD processing and external entity resolution in your XML parser. "
        "Validate and sanitize all XML input from external sources."
    ),

    "SSRF": (
        "Validate and allowlist URLs before making server-side HTTP requests. "
        "Block requests to internal IP ranges (127.0.0.1, 10.x, 192.168.x, 169.254.x). "
        "Use a DNS rebinding-safe HTTP client and consider an egress proxy."
    ),

    "Unsafe File Operations": (
        "Use tempfile.mkstemp() or tempfile.TemporaryFile() instead of mktemp(). "
        "These create files securely with proper permissions. "
        "Ensure temporary files are cleaned up and not world-readable."
    ),

    "Input Validation": (
        "Validate, sanitize, and encode all user input. "
        "Use an allowlist approach — define what is valid, reject everything else. "
        "For web output, HTML-encode user data to prevent XSS. "
        "Use a validation library (e.g. pydantic, cerberus) for structured input."
    ),

    "Dependency Risk": (
        "Regularly audit your dependencies with pip-audit or npm audit. "
        "Pin dependency versions in requirements.txt or package-lock.json. "
        "Set up automated security alerts (GitHub Dependabot, Snyk). "
        "Remove unused dependencies to reduce attack surface."
    ),

    "Authentication": (
        "Use a battle-tested authentication library rather than rolling your own. "
        "Enforce strong passwords, MFA, and account lockout policies. "
        "Store passwords with bcrypt or Argon2. "
        "Use short-lived, signed tokens (JWT with expiry) for sessions."
    ),

    "Logging & Monitoring": (
        "Log security-relevant events: failed logins, permission errors, "
        "admin actions. Never log passwords or tokens. "
        "Use structured logging and ship logs to a central SIEM. "
        "Set up alerts for anomalous patterns."
    ),

    "Other": (
        "Review this finding in context and consult the referenced documentation. "
        "Apply the principle of least privilege and defense in depth. "
        "When in doubt, follow OWASP guidelines for your language and framework."
    ),
}


def get_recommendation(category: str) -> str:
    """
    Return the developer recommendation for a given canonical category.

    Args:
        category: A canonical category string (e.g. "SQL Injection").

    Returns:
        Recommendation string. Falls back to the "Other" recommendation.
    """
    return RECOMMENDATIONS.get(category, RECOMMENDATIONS["Other"])


def get_all_recommendations(categories: list) -> dict:
    """
    Return recommendations for all unique categories in a findings list.

    Args:
        categories: List of category strings (may contain duplicates).

    Returns:
        dict mapping category → recommendation string.
    """
    return {cat: get_recommendation(cat) for cat in set(categories)}

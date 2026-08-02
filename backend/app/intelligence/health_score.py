"""
health_score.py — Calculates the Project Health Score (0–100) and letter grade.

This is SecureLens' signature feature. A simple, configurable algorithm that
gives developers an instant sense of how secure their project is.

Algorithm:
    Start at 100.
    Each finding deducts points based on:
        category_weight × severity_multiplier
    Capped at 25 points per individual finding to prevent one issue tanking the score.
    Final score is clamped to [0, 100].

The weights and multipliers are deliberately exposed as module-level constants
so they can be tuned without touching any logic.
"""

# ---------------------------------------------------------------------------
# Configurable weights (higher = more dangerous category)
# ---------------------------------------------------------------------------
CATEGORY_WEIGHTS: dict = {
    "SQL Injection":          20,
    "Command Injection":      20,
    "Unsafe Deserialization": 18,
    "Code Execution":         18,
    "SSRF":                   15,
    "Hardcoded Secrets":      15,
    "Path Traversal":         12,
    "XML Injection":          10,
    "Input Validation":        8,
    "Weak Cryptography":       8,
    "Authentication":          8,
    "Unsafe File Operations":  5,
    "Dependency Risk":         5,
    "Logging & Monitoring":    3,
    "Other":                   3,
}

# Default weight for categories not in the table
_DEFAULT_WEIGHT = 5

# ---------------------------------------------------------------------------
# Severity multipliers
# ---------------------------------------------------------------------------
SEVERITY_MULTIPLIERS: dict = {
    "CRITICAL": 1.5,
    "HIGH":     1.0,
    "MEDIUM":   0.5,
    "LOW":      0.2,
    "INFO":     0.05,
}

_DEFAULT_MULTIPLIER = 0.2

# Maximum deduction per single finding
_MAX_DEDUCTION_PER_FINDING = 25

# ---------------------------------------------------------------------------
# Grade scale
# ---------------------------------------------------------------------------
_GRADE_SCALE = [
    (95, "A+"),
    (90, "A"),
    (85, "B+"),
    (80, "B"),
    (75, "C+"),
    (70, "C"),
    (60, "D"),
    (0,  "F"),
]


def _letter_grade(score: int) -> str:
    for threshold, grade in _GRADE_SCALE:
        if score >= threshold:
            return grade
    return "F"


def calculate(findings: list) -> dict:
    """
    Calculate the health score, grade, and deduction breakdown.

    Args:
        findings: List of enriched Finding dicts
                  (must have 'category' and 'severity' already set).

    Returns:
        {
            "score":         int,   # 0–100
            "grade":         str,   # "A+" … "F"
            "deductions":    list,  # breakdown of what cost points
            "total_deducted":int,
        }
    """
    total_deducted = 0.0
    deduction_log = []

    # Group deductions by category for a cleaner summary
    category_deductions: dict = {}

    for finding in findings:
        category = finding.get("category", "Other")
        severity = finding.get("severity", "LOW")

        weight = CATEGORY_WEIGHTS.get(category, _DEFAULT_WEIGHT)
        multiplier = SEVERITY_MULTIPLIERS.get(severity, _DEFAULT_MULTIPLIER)

        raw_deduction = weight * multiplier
        deduction = min(raw_deduction, _MAX_DEDUCTION_PER_FINDING)

        total_deducted += deduction

        if category not in category_deductions:
            category_deductions[category] = {
                "category": category,
                "count":    0,
                "points":   0.0,
            }
        category_deductions[category]["count"]  += 1
        category_deductions[category]["points"] += deduction

    # Build sorted deduction list (highest impact first)
    deductions = sorted(
        category_deductions.values(),
        key=lambda x: x["points"],
        reverse=True,
    )

    # Round points for display
    for d in deductions:
        d["points"] = round(d["points"], 1)

    score = max(0, round(100 - total_deducted))

    return {
        "score":          score,
        "grade":          _letter_grade(score),
        "deductions":     deductions,
        "total_deducted": round(total_deducted, 1),
    }

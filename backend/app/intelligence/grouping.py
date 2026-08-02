"""
grouping.py — Groups findings by canonical category.

Instead of showing 15 separate SQL Injection findings, we group them:

  SQL Injection
  ├── 15 occurrences
  ├── Files: login.py, admin.py, payment.py
  └── Worst severity: HIGH, Priority: IMMEDIATE

This makes the dashboard scannable and professional.
"""

import os
from app.intelligence.prioritizer import PRIORITY_ORDER, higher_priority


# Severity ordering for comparison
_SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


def _higher_severity(a: str, b: str) -> str:
    idx_a = _SEVERITY_ORDER.index(a) if a in _SEVERITY_ORDER else len(_SEVERITY_ORDER)
    idx_b = _SEVERITY_ORDER.index(b) if b in _SEVERITY_ORDER else len(_SEVERITY_ORDER)
    return a if idx_a <= idx_b else b


def group_findings(findings: list) -> dict:
    """
    Group findings by canonical category.

    Args:
        findings: List of enriched Finding dicts
                  (must have 'category' and 'priority' fields already set).

    Returns:
        dict keyed by category name, each value:
        {
            "category":       str,
            "count":          int,
            "worst_severity": str,   # highest severity in this group
            "worst_priority": str,   # highest priority in this group
            "files":          list,  # unique affected files (sorted)
            "findings":       list,  # full finding objects
        }
    """
    groups: dict = {}

    for finding in findings:
        category = finding.get("category", "Other")

        if category not in groups:
            groups[category] = {
                "category":       category,
                "count":          0,
                "worst_severity": "INFO",
                "worst_priority": "LOW",
                "files":          [],
                "findings":       [],
            }

        group = groups[category]
        group["count"] += 1
        group["findings"].append(finding)

        # Track worst severity and priority
        group["worst_severity"] = _higher_severity(
            group["worst_severity"], finding.get("severity", "INFO")
        )
        group["worst_priority"] = higher_priority(
            group["worst_priority"], finding.get("priority", "LOW")
        )

        # Collect unique file paths
        file_path = finding.get("file", "")
        if file_path and file_path not in group["files"]:
            group["files"].append(file_path)

    # Sort files within each group alphabetically
    for group in groups.values():
        group["files"] = sorted(group["files"])

    return groups


def get_ordered_groups(groups: dict) -> list:
    """
    Return groups as a sorted list: by priority first, then by count (desc).

    Args:
        groups: Output of group_findings()

    Returns:
        List of group dicts in display order (most urgent first).
    """
    def sort_key(group):
        priority_idx = (
            PRIORITY_ORDER.index(group["worst_priority"])
            if group["worst_priority"] in PRIORITY_ORDER
            else len(PRIORITY_ORDER)
        )
        severity_idx = (
            _SEVERITY_ORDER.index(group["worst_severity"])
            if group["worst_severity"] in _SEVERITY_ORDER
            else len(_SEVERITY_ORDER)
        )
        return (priority_idx, severity_idx, -group["count"])

    return sorted(groups.values(), key=sort_key)

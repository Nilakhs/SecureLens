"""
insights.py — Extracts key intelligence insights from the findings list.

Turns raw data into actionable statements:
  - Most common vulnerability category
  - Highest-risk file (most findings)
  - Most affected folder
  - Which scanner found the most issues
  - Total unique files affected
"""

import os
from collections import Counter


def compute_insights(findings: list) -> dict:
    """
    Compute key insights from a list of enriched findings.

    Args:
        findings: List of enriched Finding dicts.

    Returns:
        dict with human-readable insight data.
    """
    if not findings:
        return {
            "most_common_category":       None,
            "most_common_category_count": 0,
            "highest_risk_file":          None,
            "highest_risk_file_count":    0,
            "most_affected_folder":       None,
            "most_affected_folder_count": 0,
            "scanner_with_most_findings": None,
            "scanner_finding_counts":     {},
            "total_files_affected":       0,
            "total_folders_affected":     0,
        }

    # --- Category frequency ---
    category_counts = Counter(
        f.get("category", "Other") for f in findings
    )
    most_common_category, most_common_count = category_counts.most_common(1)[0]

    # --- File frequency ---
    file_counts = Counter(f.get("file", "") for f in findings if f.get("file"))
    highest_risk_file, highest_risk_file_count = (
        file_counts.most_common(1)[0] if file_counts else (None, 0)
    )

    # --- Folder frequency ---
    # Extract the top-level folder of each file path
    folder_counts: Counter = Counter()
    for f in findings:
        file_path = f.get("file", "")
        if not file_path:
            continue
        # Normalize separators, take first directory component
        parts = file_path.replace("\\", "/").split("/")
        folder = parts[0] if len(parts) > 1 else "(root)"
        folder_counts[folder] += 1

    most_affected_folder, most_affected_folder_count = (
        folder_counts.most_common(1)[0] if folder_counts else (None, 0)
    )

    # --- Scanner breakdown ---
    scanner_counts: Counter = Counter()
    for f in findings:
        for scanner in f.get("detected_by", [f.get("scanner", "unknown")]):
            scanner_counts[scanner] += 1

    scanner_with_most = (
        scanner_counts.most_common(1)[0][0] if scanner_counts else None
    )

    # --- Unique files and folders ---
    unique_files = set(f.get("file", "") for f in findings if f.get("file"))
    unique_folders = set(
        f.get("file", "").replace("\\", "/").split("/")[0]
        for f in findings
        if f.get("file") and "/" in f.get("file", "").replace("\\", "/")
    )

    return {
        "most_common_category":       most_common_category,
        "most_common_category_count": most_common_count,
        "highest_risk_file":          highest_risk_file,
        "highest_risk_file_count":    highest_risk_file_count,
        "most_affected_folder":       most_affected_folder,
        "most_affected_folder_count": most_affected_folder_count,
        "scanner_with_most_findings": scanner_with_most,
        "scanner_finding_counts":     dict(scanner_counts),
        "total_files_affected":       len(unique_files),
        "total_folders_affected":     len(unique_folders),
    }

"""
intelligence_engine.py — The single entry point for the SecureLens Intelligence Layer.

ProjectAnalyzer calls ONLY this. Everything else is an internal implementation detail.

    IntelligenceEngine.analyze(findings, metadata) → intelligence dict

Pipeline:
    1. Categorize  — map raw scanner categories to SecureLens vocabulary
    2. Prioritize  — assign internal action priority to each finding
    3. Group       — group findings by category for overview display
    4. Score       — calculate health score and letter grade
    5. Insights    — extract key patterns and statistics
    6. Summarize   — build executive summary
    7. Chart data  — prepare chart-ready arrays (for future use)
    8. Recommend   — attach static recommendations per category
"""

from app.intelligence.categorizer    import enrich_finding
from app.intelligence.prioritizer    import assign_priority, PRIORITY_ORDER
from app.intelligence.grouping       import group_findings, get_ordered_groups
from app.intelligence.health_score   import calculate as calculate_health
from app.intelligence.insights       import compute_insights
from app.intelligence.recommendations import get_all_recommendations


class IntelligenceEngine:

    @staticmethod
    def analyze(findings: list, metadata: dict) -> dict:
        """
        Run the full intelligence pipeline on a set of merged findings.

        Args:
            findings: List of merged Finding dicts from ScannerManager.
                      These are mutated in-place (new fields added).
            metadata: Project metadata dict from ProjectAnalyzer.

        Returns:
            intelligence dict containing all analysis results.
        """

        # ----------------------------------------------------------------
        # Step 1 & 2 — Categorize + Prioritize (enrich every finding)
        # ----------------------------------------------------------------
        enriched = []
        for raw_finding in findings:
            finding = enrich_finding(raw_finding)          # sets canonical category
            finding["priority"] = assign_priority(finding) # sets priority
            enriched.append(finding)

        # ----------------------------------------------------------------
        # Step 3 — Group by category
        # ----------------------------------------------------------------
        grouped = group_findings(enriched)
        groups_ordered = get_ordered_groups(grouped)

        # Serialize groups_ordered to plain dicts (without the nested findings
        # for the summary — keep findings in grouped_findings separately)
        groups_summary = [
            {
                "category":       g["category"],
                "count":          g["count"],
                "worst_severity": g["worst_severity"],
                "worst_priority": g["worst_priority"],
                "files":          g["files"],
            }
            for g in groups_ordered
        ]

        # ----------------------------------------------------------------
        # Step 4 — Health Score + Grade
        # ----------------------------------------------------------------
        health = calculate_health(enriched)

        # ----------------------------------------------------------------
        # Step 5 — Insights
        # ----------------------------------------------------------------
        insights = compute_insights(enriched)

        # ----------------------------------------------------------------
        # Step 6 — Priority counts
        # ----------------------------------------------------------------
        priority_counts = {p: 0 for p in PRIORITY_ORDER}
        for f in enriched:
            p = f.get("priority", "LOW")
            if p in priority_counts:
                priority_counts[p] += 1

        # ----------------------------------------------------------------
        # Step 7 — Executive Summary
        # ----------------------------------------------------------------
        summary_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in enriched:
            sev = f.get("severity", "INFO")
            if sev in summary_counts:
                summary_counts[sev] += 1

        executive_summary = {
            "project_name":   metadata.get("project_name", "Unknown"),
            "languages":      list(metadata.get("languages", {}).keys()),
            "frameworks":     metadata.get("frameworks", []),
            "files_scanned":  metadata.get("statistics", {}).get("files", 0),
            "scanners_used":  [],          # filled in by project_analyzer
            "total_findings": len(enriched),
            "critical":       summary_counts["CRITICAL"],
            "high":           summary_counts["HIGH"],
            "medium":         summary_counts["MEDIUM"],
            "low":            summary_counts["LOW"],
            "info":           summary_counts["INFO"],
            "immediate_actions": priority_counts.get("IMMEDIATE", 0),
            "most_common_risk":  insights.get("most_common_category"),
            "highest_risk_file": insights.get("highest_risk_file"),
            "health_score":      health["score"],
            "grade":             health["grade"],
        }

        # ----------------------------------------------------------------
        # Step 8 — Chart-ready data (future use)
        # ----------------------------------------------------------------
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        chart_data = {
            "by_severity": [
                {"label": sev, "count": summary_counts[sev]}
                for sev in severity_order
            ],
            "by_category": [
                {"label": g["category"], "count": g["count"]}
                for g in groups_ordered
            ],
            "by_priority": [
                {"label": p, "count": priority_counts[p]}
                for p in PRIORITY_ORDER
            ],
        }

        # ----------------------------------------------------------------
        # Step 9 — Recommendations (one per unique category found)
        # ----------------------------------------------------------------
        unique_categories = list({f.get("category", "Other") for f in enriched})
        recommendations = get_all_recommendations(unique_categories)

        # ----------------------------------------------------------------
        # Return full intelligence report
        # ----------------------------------------------------------------
        return {
            "health_score":      health["score"],
            "grade":             health["grade"],
            "score_deductions":  health["deductions"],
            "total_deducted":    health["total_deducted"],
            "priority_counts":   priority_counts,
            "grouped_findings":  grouped,
            "groups_ordered":    groups_summary,
            "insights":          insights,
            "executive_summary": executive_summary,
            "chart_data":        chart_data,
            "recommendations":   recommendations,
            "enriched_findings": enriched,   # findings with category + priority set
        }

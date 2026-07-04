from statistics import mean

from utils.db import fetch_all, fetch_one


def get_user_performance(user_id):
    rows = fetch_all(
        """
        SELECT users.id, users.display_name,
               COALESCE(topic_counts.total, 0) AS topics,
               COALESCE(note_counts.total, 0) AS notes,
               COALESCE(category_counts.total, 0) AS categories,
               COALESCE(lab_counts.total, 0) AS completed_labs,
               COALESCE(finding_counts.total, 0) AS security_findings,
               COALESCE(finding_counts.closed_total, 0) AS closed_findings,
               COALESCE(finding_counts.high_risk_total, 0) AS high_risk_findings,
               COALESCE(recent_counts.total, 0) AS recent_actions
        FROM users
        LEFT JOIN (
            SELECT owner_id, COUNT(*) AS total
            FROM topics
            WHERE is_deleted = 0
            GROUP BY owner_id
        ) AS topic_counts ON topic_counts.owner_id = users.id
        LEFT JOIN (
            SELECT owner_id, COUNT(*) AS total
            FROM notes
            WHERE is_deleted = 0
            GROUP BY owner_id
        ) AS note_counts ON note_counts.owner_id = users.id
        LEFT JOIN (
            SELECT owner_id, COUNT(*) AS total
            FROM categories
            WHERE is_deleted = 0
            GROUP BY owner_id
        ) AS category_counts ON category_counts.owner_id = users.id
        LEFT JOIN (
            SELECT user_id, COUNT(*) AS total
            FROM lab_completions
            GROUP BY user_id
        ) AS lab_counts ON lab_counts.user_id = users.id
        LEFT JOIN (
            SELECT owner_id,
                   COUNT(*) AS total,
                   SUM(status IN ('managed', 'resolved')) AS closed_total,
                   SUM(severity IN ('high', 'critical')) AS high_risk_total
            FROM security_findings
            WHERE is_deleted = 0
            GROUP BY owner_id
        ) AS finding_counts ON finding_counts.owner_id = users.id
        LEFT JOIN (
            SELECT user_id, COUNT(*) AS total
            FROM (
                SELECT owner_id AS user_id
                FROM topics
                WHERE is_deleted = 0 AND updated_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                UNION ALL
                SELECT owner_id AS user_id
                FROM notes
                WHERE is_deleted = 0 AND updated_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                UNION ALL
                SELECT owner_id AS user_id
                FROM security_findings
                WHERE is_deleted = 0 AND updated_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                UNION ALL
                SELECT user_id
                FROM lab_completions
                WHERE completed_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ) AS recent_events
            GROUP BY user_id
        ) AS recent_counts ON recent_counts.user_id = users.id
        WHERE users.is_banned = 0 AND users.role = 'user'
        """
    )
    scored_rows = [score_user(row) for row in rows]
    if not scored_rows:
        return empty_performance()

    scored_rows.sort(key=lambda item: item["score"], reverse=True)
    target = next((item for item in scored_rows if item["id"] == user_id), None)
    if not target:
        return empty_performance(total_users=len(scored_rows))

    target_rank = scored_rows.index(target) + 1
    total_users = len(scored_rows)
    peer_scores = [item["score"] for item in scored_rows if item["id"] != user_id]
    peer_average = round(mean(peer_scores), 1) if peer_scores else target["score"]
    percentile = round(((total_users - target_rank + 1) / total_users) * 100) if total_users else 0
    target.update(
        {
            "rank": target_rank,
            "total_users": total_users,
            "peer_average": peer_average,
            "percentile": percentile,
            "activity_label": activity_label(target["recent_actions"]),
        }
    )
    return target


def get_user_security_summary(user_id):
    return fetch_one(
        """
        SELECT COUNT(*) AS total,
               SUM(activity_type = 'vulnerability_found') AS found_total,
               SUM(activity_type = 'vulnerability_tested') AS tested_total,
               SUM(activity_type = 'threat_managed') AS managed_total,
               SUM(severity = 'critical') AS critical_total,
               SUM(status IN ('managed', 'resolved')) AS closed_total
        FROM security_findings
        WHERE owner_id = %s AND is_deleted = 0
        """,
        (user_id,),
    ) or {}


def get_admin_security_summary():
    return fetch_one(
        """
        SELECT
            (SELECT COUNT(*)
             FROM security_findings
             WHERE is_deleted = 0) AS total_findings,
            (SELECT COUNT(*)
             FROM security_findings
             WHERE is_deleted = 0 AND severity = 'critical') AS critical_findings,
            (SELECT COUNT(*)
             FROM security_findings
             WHERE is_deleted = 0 AND activity_type = 'threat_managed') AS managed_threats,
            (SELECT COUNT(*)
             FROM vulnerability_catalog
             WHERE approval_status = 'pending') AS pending_vulnerabilities
        """
    ) or {}


def score_user(row):
    scored = dict(row)
    score = (
        int(scored["topics"]) * 8
        + int(scored["notes"]) * 6
        + int(scored["categories"]) * 3
        + int(scored["completed_labs"]) * 12
        + int(scored["security_findings"]) * 15
        + int(scored["closed_findings"]) * 7
        + int(scored["high_risk_findings"]) * 5
        + min(int(scored["recent_actions"]), 30) * 4
    )
    scored["score"] = score
    return scored


def empty_performance(total_users=0):
    return {
        "score": 0,
        "rank": 0,
        "total_users": total_users,
        "peer_average": 0,
        "percentile": 0,
        "recent_actions": 0,
        "activity_label": "Getting started",
    }


def activity_label(recent_actions):
    recent_actions = int(recent_actions or 0)
    if recent_actions >= 12:
        return "Highly active"
    if recent_actions >= 5:
        return "Consistent"
    if recent_actions >= 1:
        return "Warming up"
    return "Getting started"

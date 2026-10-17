import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ghostgrid.db")


class DatabaseManager:
    """
    SQLite Database Manager for GhostGrid:
    1. Persists investigation scans and their complete graph topologies.
    2. Maintains a global watchlist of identified bot accounts.
    3. Archives detected narrative claims across investigations.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Scans Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    scan_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    name TEXT NOT NULL,
                    total_posts INTEGER NOT NULL,
                    total_accounts INTEGER NOT NULL,
                    flagged_bots INTEGER NOT NULL,
                    suspicious_accounts INTEGER NOT NULL,
                    organic_accounts INTEGER NOT NULL,
                    max_coreness INTEGER NOT NULL,
                    narratives_count INTEGER NOT NULL,
                    graph_json TEXT NOT NULL,
                    summary_json TEXT NOT NULL
                )
            """)

            # 2. Flagged Accounts Table (Watchlist)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS flagged_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    threat_score REAL NOT NULL,
                    threat_level TEXT NOT NULL,
                    coreness INTEGER NOT NULL,
                    burst_count INTEGER NOT NULL,
                    narratives_json TEXT NOT NULL,
                    ground_truth TEXT DEFAULT 'unknown',
                    FOREIGN KEY (scan_id) REFERENCES scans (scan_id) ON DELETE CASCADE
                )
            """)

            # 3. Narratives Archive Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS narrative_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT NOT NULL,
                    narrative_id TEXT NOT NULL,
                    canonical_claim TEXT NOT NULL,
                    canonical_post_id TEXT NOT NULL,
                    post_count INTEGER NOT NULL,
                    unique_user_count INTEGER NOT NULL,
                    mean_similarity REAL NOT NULL,
                    FOREIGN KEY (scan_id) REFERENCES scans (scan_id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def save_scan(
        self,
        scan_id: str,
        name: str,
        total_posts: int,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        narratives: Dict[str, Any],
        flagged_accounts: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> str:
        """Saves a complete investigation run into SQLite."""
        created_at = datetime.utcnow().isoformat() + "Z"
        # Ensure narratives are converted to plain dicts for json.dumps
        clean_narratives = {}
        for nid, meta in narratives.items():
            if hasattr(meta, "model_dump"):
                clean_narratives[nid] = meta.model_dump()
            elif isinstance(meta, dict):
                clean_narratives[nid] = meta
            else:
                clean_narratives[nid] = meta.__dict__

        graph_payload = json.dumps({
            "nodes": [n.model_dump() if hasattr(n, "model_dump") else n for n in nodes],
            "edges": [e.model_dump() if hasattr(e, "model_dump") else e for e in edges],
            "narratives": clean_narratives
        })
        summary_payload = json.dumps(summary.model_dump() if hasattr(summary, "model_dump") else summary)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Insert scan metadata
            cursor.execute("""
                INSERT INTO scans (
                    scan_id, created_at, name, total_posts, total_accounts,
                    flagged_bots, suspicious_accounts, organic_accounts,
                    max_coreness, narratives_count, graph_json, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_id,
                created_at,
                name,
                total_posts,
                summary["total_accounts"],
                summary["flagged_bots"],
                summary["suspicious_accounts"],
                summary["organic_accounts"],
                summary["max_coreness"],
                summary["narratives_count"],
                graph_payload,
                summary_payload
            ))

            # Insert flagged accounts
            for acc in flagged_accounts:
                cursor.execute("""
                    INSERT INTO flagged_accounts (
                        scan_id, user_id, threat_score, threat_level,
                        coreness, burst_count, narratives_json, ground_truth
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    scan_id,
                    acc["user_id"],
                    acc["threat_score"],
                    acc["threat_level"],
                    acc["coreness"],
                    acc["burst_count"],
                    json.dumps(acc.get("narratives", [])),
                    acc.get("ground_truth", "unknown")
                ))

            # Insert narratives archive
            for nid, meta in narratives.items():
                if hasattr(meta, "model_dump"):
                    meta_dict = meta.model_dump()
                elif isinstance(meta, dict):
                    meta_dict = meta
                else:
                    meta_dict = meta.__dict__

                cursor.execute("""
                    INSERT INTO narrative_records (
                        scan_id, narrative_id, canonical_claim, canonical_post_id,
                        post_count, unique_user_count, mean_similarity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    scan_id,
                    meta_dict["narrative_id"],
                    meta_dict["canonical_claim"],
                    meta_dict.get("canonical_post_id", ""),
                    meta_dict["post_count"],
                    meta_dict["unique_user_count"],
                    meta_dict.get("mean_similarity", 1.0)
                ))

            conn.commit()
        return scan_id

    def list_scans(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns history of past scans without the heavy graph JSON."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT scan_id, created_at, name, total_posts, total_accounts,
                       flagged_bots, suspicious_accounts, organic_accounts,
                       max_coreness, narratives_count
                FROM scans
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single investigation with full graph payload."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
            row = cursor.fetchone()
            if not row:
                return None

            scan_dict = dict(row)
            graph_data = json.loads(scan_dict.pop("graph_json"))
            summary_data = json.loads(scan_dict.pop("summary_json"))

            # Fetch flagged accounts for this scan
            cursor.execute("""
                SELECT user_id, threat_score, threat_level, coreness,
                       burst_count, narratives_json, ground_truth
                FROM flagged_accounts
                WHERE scan_id = ?
                ORDER BY threat_score DESC
            """, (scan_id,))
            flagged = []
            for r in cursor.fetchall():
                d = dict(r)
                d["narratives"] = json.loads(d.pop("narratives_json"))
                flagged.append(d)

            return {
                **scan_dict,
                "nodes": graph_data["nodes"],
                "edges": graph_data["edges"],
                "narratives": graph_data["narratives"],
                "flagged_accounts": flagged,
                "summary": summary_data
            }

    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Returns unique bot accounts across all scans."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, MAX(threat_score) as max_threat_score,
                       threat_level, MAX(coreness) as max_coreness,
                       COUNT(DISTINCT scan_id) as scan_appearances,
                       ground_truth
                FROM flagged_accounts
                GROUP BY user_id
                ORDER BY max_threat_score DESC, scan_appearances DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

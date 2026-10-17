import math
from datetime import datetime
from typing import List, Dict, Any, Tuple
import networkx as nx


class GraphAnalysisEngine:
    """
    Graph & Network Analysis Engine for GhostGrid:
    1. Builds bipartite graph (Accounts <-> Narratives).
    2. Builds temporal co-coordination graph (Accounts linked if posting same narrative within delta_t).
    3. Runs k-Core decomposition to isolate dense collusive cores from casual organic users.
    4. Computes temporal burst density and composite anomaly risk scores (0% - 100%).
    5. Formats network topology into frontend-ready node-link payload.
    """

    def __init__(self):
        pass

    @staticmethod
    def parse_iso_timestamp(ts_str: str) -> datetime:
        """Parses ISO timestamp string (with or without 'Z')."""
        clean_ts = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_ts)

    def analyze(
        self,
        annotated_posts: List[Dict[str, Any]],
        narratives: Dict[str, Dict[str, Any]],
        burst_window_minutes: int = 20,
        k_core_min: int = 2
    ) -> Dict[str, Any]:
        """
        Runs full graph decomposition and threat assessment.

        Args:
            annotated_posts: Posts enriched by nlp_engine with 'narrative_id'.
            narratives: Metadata dict of detected narratives.
            burst_window_minutes: Time window threshold (in minutes) to consider posts coordinated.
            k_core_min: Threshold k for classifying dense coordinated cores.

        Returns:
            Dict containing graph topology (nodes, edges), flagged accounts, and statistics.
        """
        # 1. Initialize NetworkX Graph
        B = nx.Graph()
        coordination_graph = nx.Graph()

        # Track account statistics
        account_stats: Dict[str, Dict[str, Any]] = {}
        # Map narrative to its post timestamps: narrative_id -> [(user_id, datetime, post_id)]
        narrative_timeline: Dict[str, List[Tuple[str, datetime, str]]] = {
            nid: [] for nid in narratives.keys()
        }

        # 2. Populate bipartite nodes & edges
        for post in annotated_posts:
            user_id = post["user_id"]
            post_id = post["post_id"]
            narrative_id = post.get("narrative_id")
            ts = self.parse_iso_timestamp(post["timestamp"])

            if user_id not in account_stats:
                account_stats[user_id] = {
                    "user_id": user_id,
                    "total_posts": 0,
                    "narrative_posts": 0,
                    "narratives_touched": set(),
                    "timestamps": [],
                    "burst_participations": 0,
                    "ground_truth": post.get("ground_truth", "unknown")
                }

            account_stats[user_id]["total_posts"] += 1
            account_stats[user_id]["timestamps"].append(ts)

            if narrative_id and narrative_id in narratives:
                account_stats[user_id]["narrative_posts"] += 1
                account_stats[user_id]["narratives_touched"].add(narrative_id)
                narrative_timeline[narrative_id].append((user_id, ts, post_id))

                # Add Account <-> Narrative edge in Bipartite graph
                B.add_node(user_id, node_type="account")
                B.add_node(narrative_id, node_type="narrative")
                B.add_edge(
                    user_id,
                    narrative_id,
                    post_id=post_id,
                    timestamp=post["timestamp"],
                    similarity=post.get("centroid_similarity", 1.0)
                )
            else:
                # Organic singleton without narrative
                B.add_node(user_id, node_type="account")

        # 3. Detect Temporal Bursts & Build Co-Coordination Network
        # Two accounts are connected in coordination_graph if they posted the same narrative
        # within burst_window_minutes of each other.
        for nid, events in narrative_timeline.items():
            if len(events) < 2:
                continue

            events_sorted = sorted(events, key=lambda x: x[1])
            for i in range(len(events_sorted)):
                u1, t1, p1 = events_sorted[i]
                for j in range(i + 1, len(events_sorted)):
                    u2, t2, p2 = events_sorted[j]
                    if u1 == u2:
                        continue

                    delta_mins = abs((t2 - t1).total_seconds()) / 60.0
                    if delta_mins <= burst_window_minutes:
                        account_stats[u1]["burst_participations"] += 1
                        account_stats[u2]["burst_participations"] += 1

                        # Edge weight is inversely proportional to time difference (closer = higher weight)
                        weight = 1.0 / (1.0 + delta_mins)
                        if coordination_graph.has_edge(u1, u2):
                            coordination_graph[u1][u2]["weight"] += weight
                            coordination_graph[u1][u2]["narratives"].add(nid)
                        else:
                            coordination_graph.add_edge(
                                u1, u2,
                                weight=weight,
                                delta_minutes=round(delta_mins, 1),
                                narratives={nid}
                            )

        # 4. Run k-Core Decomposition on the Co-Coordination Graph
        core_numbers: Dict[str, int] = {}
        if len(coordination_graph.nodes) > 0:
            core_numbers = nx.core_number(coordination_graph)

        # 5. Calculate Threat Score (0.0 to 100.0) for each account
        flagged_accounts = []
        for user_id, stats in account_stats.items():
            coreness = core_numbers.get(user_id, 0)
            burst_count = stats["burst_participations"]
            narratives_count = len(stats["narratives_touched"])
            total_posts = stats["total_posts"]
            narrative_ratio = stats["narrative_posts"] / max(1, total_posts)

            # Threat score formula:
            # - Coreness weight: 40% (maxes at coreness >= 3)
            # - Burst participation weight: 35% (maxes at 5+ bursts)
            # - Narrative focus ratio: 25% (100% focused on attack narrative)
            score_core = min(1.0, coreness / 3.0) * 40.0
            score_burst = min(1.0, burst_count / 5.0) * 35.0
            score_focus = (narrative_ratio if narratives_count > 0 else 0.0) * 25.0

            threat_score = round(min(100.0, score_core + score_burst + score_focus), 1)

            # Classification
            if threat_score >= 70.0 and coreness >= k_core_min:
                threat_level = "COORDINATED_BOT"
            elif threat_score >= 40.0:
                threat_level = "SUSPICIOUS"
            else:
                threat_level = "ORGANIC"

            record = {
                "user_id": user_id,
                "threat_score": threat_score,
                "threat_level": threat_level,
                "coreness": coreness,
                "burst_count": burst_count,
                "narratives_count": narratives_count,
                "narratives": list(stats["narratives_touched"]),
                "ground_truth": stats["ground_truth"]
            }
            account_stats[user_id].update(record)

            if threat_level in ("COORDINATED_BOT", "SUSPICIOUS"):
                flagged_accounts.append(record)

        # Sort flagged accounts descending by threat score
        flagged_accounts.sort(key=lambda x: x["threat_score"], reverse=True)

        # 6. Format Network Topology for Frontend Force-Directed Graph
        # We deliver both Bipartite elements and Co-Coordination edges
        nodes = []
        edges = []

        # Account nodes
        for user_id, stats in account_stats.items():
            nodes.append({
                "id": user_id,
                "label": user_id,
                "type": "account",
                "threat_level": stats["threat_level"],
                "threat_score": stats["threat_score"],
                "coreness": stats["coreness"],
                "narratives": stats["narratives"],
                "val": 4 if stats["threat_level"] == "COORDINATED_BOT" else 2
            })

        # Narrative nodes (large hubs)
        for nid, meta in narratives.items():
            nodes.append({
                "id": nid,
                "label": f"Narrative: {meta['canonical_claim'][:40]}...",
                "canonical_claim": meta["canonical_claim"],
                "type": "narrative",
                "post_count": meta["post_count"],
                "user_count": meta["unique_user_count"],
                "threat_level": "NARRATIVE_HUB",
                "val": 10
            })

        # Bipartite Edges (Account <-> Narrative)
        for u, v, data in B.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "type": "posted_narrative",
                "timestamp": data.get("timestamp"),
                "similarity": data.get("similarity", 1.0)
            })

        # Co-Coordination Edges (Account <-> Account during bursts)
        for u, v, data in coordination_graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "type": "co_coordinated",
                "weight": round(data.get("weight", 1.0), 3),
                "delta_minutes": data.get("delta_minutes", 0.0),
                "narratives": list(data.get("narratives", []))
            })

        summary = {
            "total_accounts": len(account_stats),
            "flagged_bots": len([a for a in flagged_accounts if a["threat_level"] == "COORDINATED_BOT"]),
            "suspicious_accounts": len([a for a in flagged_accounts if a["threat_level"] == "SUSPICIOUS"]),
            "organic_accounts": len([a for a in account_stats.values() if a["threat_level"] == "ORGANIC"]),
            "narratives_count": len(narratives),
            "max_coreness": max(core_numbers.values()) if core_numbers else 0
        }

        return {
            "nodes": nodes,
            "edges": edges,
            "flagged_accounts": flagged_accounts,
            "summary": summary
        }

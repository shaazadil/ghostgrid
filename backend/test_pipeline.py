import json
from app.core.nlp_engine import SemanticClusterEngine
from app.core.graph_engine import GraphAnalysisEngine

def run_full_pipeline_test():
    with open("dataset.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    print("="*70)
    print("GHOSTGRID FULL PIPELINE INTEGRATION TEST")
    print("="*70)
    print(f"Total posts loaded: {len(posts)}")

    # 1. NLP Semantic Clustering
    nlp = SemanticClusterEngine()
    annotated_posts, narratives = nlp.cluster_posts(posts, similarity_threshold=0.70)
    print(f"\n[NLP Phase] Detected {len(narratives)} narrative clusters:")
    for nid, meta in narratives.items():
        print(f"  - {nid}: {meta['post_count']} posts by {meta['unique_user_count']} users")
        print(f"    Claim: \"{meta['canonical_claim'][:60]}...\"")

    # 2. Graph & Network Analysis
    graph = GraphAnalysisEngine()
    analysis_result = graph.analyze(
        annotated_posts=annotated_posts,
        narratives=narratives,
        burst_window_minutes=20,
        k_core_min=2
    )

    summary = analysis_result["summary"]
    flagged = analysis_result["flagged_accounts"]

    print("\n[Graph Phase] Summary Metrics:")
    print(f"  - Total Accounts Analyzed: {summary['total_accounts']}")
    print(f"  - Flagged Coordinated Bots: {summary['flagged_bots']}")
    print(f"  - Suspicious Accounts:      {summary['suspicious_accounts']}")
    print(f"  - Verified Organic Users:   {summary['organic_accounts']}")
    print(f"  - Max Graph Coreness (k):   {summary['max_coreness']}")
    print(f"  - Graph Nodes exported:     {len(analysis_result['nodes'])}")
    print(f"  - Graph Edges exported:     {len(analysis_result['edges'])}")

    print("\nTop 5 Flagged Threat Accounts:")
    for a in flagged[:5]:
        print(f"  * {a['user_id']:<18} | Threat: {a['threat_score']}% | Core: k={a['coreness']} | Status: {a['threat_level']} (Truth: {a['ground_truth']})")

    # Accuracy verification against Ground Truth
    bot_alpha_detected = sum(1 for a in flagged if "burner_alpha" in a["user_id"])
    bot_beta_detected = sum(1 for a in flagged if "burner_beta" in a["user_id"])
    false_positives = sum(1 for a in flagged if "user_real" in a["user_id"])

    print("\nGround Truth Verification:")
    print(f"  - Bot Ring Alpha caught: {bot_alpha_detected} / 20")
    print(f"  - Bot Ring Beta caught:  {bot_beta_detected} / 15")
    print(f"  - False Positives (Real users falsely flagged): {false_positives} / 35")
    print("="*70)

if __name__ == "__main__":
    run_full_pipeline_test()

import json
from app.core.nlp_engine import SemanticClusterEngine

def test_pipeline():
    with open("dataset.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    print(f"Loaded {len(posts)} posts from dataset.json")
    engine = SemanticClusterEngine()
    
    for thresh in [0.75, 0.70, 0.65]:
        annotated_posts, narratives = engine.cluster_posts(posts, similarity_threshold=thresh)
        print("\n" + "="*60)
        print(f"THRESHOLD: {thresh}")
        print(f"Total Canonical Narratives Detected: {len(narratives)}")
        for nid, meta in narratives.items():
            print(f"  [{nid}] {meta['post_count']} posts by {meta['unique_user_count']} users | \"{meta['canonical_claim'][:60]}...\"")
        singletons = [p for p in annotated_posts if not p['is_narrative']]
        print(f"  Organic Singletons (Uncoordinated / Ignored): {len(singletons)}")
        print("="*60)

if __name__ == "__main__":
    test_pipeline()

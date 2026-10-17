import json
from fastapi.testclient import TestClient
from app.main import app

def test_api():
    print("="*60)
    print("STARTING FASTAPI SERVER & DATABASE BUG CHECK")
    print("="*60)

    with TestClient(app) as client:
        # 1. Health Check
        print("\n[1] Testing GET /api/health ...")
        resp = client.get("/api/health")
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        data = resp.json()
        print(f" -> Status: {data['status']}, DB Ready: {data['database_ready']}, Model Loaded: {data['model_loaded']}")

        # 2. Sample Dataset
        print("\n[2] Testing GET /api/sample-dataset ...")
        resp = client.get("/api/sample-dataset")
        assert resp.status_code == 200, f"Sample dataset failed: {resp.text}"
        dataset = resp.json()
        print(f" -> Received {dataset['total_posts']} posts")

        # 3. Full /api/analyze with Database Auto-Save
        print("\n[3] Testing POST /api/analyze with SQLite Auto-Persist ...")
        payload = {
            "posts": dataset["posts"],
            "scan_name": "Automated Test Suite Investigation",
            "similarity_threshold": 0.70,
            "burst_window_minutes": 20,
            "k_core_min": 2
        }
        resp = client.post("/api/analyze", json=payload)
        assert resp.status_code == 200, f"Analysis failed: {resp.text}"
        result = resp.json()
        scan_id = result.get("scan_id")
        assert scan_id, "Missing scan_id in analysis response"
        print(f" -> Analysis Saved! Generated Scan ID: {scan_id}")
        print(f"    Nodes: {len(result['nodes'])}, Edges: {len(result['edges'])}")

        # 4. Test Scan History Endpoint
        print("\n[4] Testing GET /api/scans (History) ...")
        resp = client.get("/api/scans")
        assert resp.status_code == 200, f"Scans list failed: {resp.text}"
        scans_list = resp.json()
        assert len(scans_list) > 0, "Expected at least 1 scan in database"
        print(f" -> Successfully retrieved {len(scans_list)} scan records from SQLite")
        print(f"    Latest Scan: {scans_list[0]['name']} | Bots: {scans_list[0]['flagged_bots']}")

        # 5. Test Specific Scan Retrieval
        print(f"\n[5] Testing GET /api/scans/{scan_id} (Replay Graph) ...")
        resp = client.get(f"/api/scans/{scan_id}")
        assert resp.status_code == 200, f"Get scan failed: {resp.text}"
        loaded_scan = resp.json()
        assert loaded_scan["scan_id"] == scan_id
        assert len(loaded_scan["nodes"]) == len(result["nodes"])
        print(f" -> Successfully reloaded exact graph topology from SQLite ({len(loaded_scan['nodes'])} nodes)")

        # 6. Test Watchlist Endpoint
        print("\n[6] Testing GET /api/watchlist (Global Bot Watchlist) ...")
        resp = client.get("/api/watchlist")
        assert resp.status_code == 200, f"Watchlist failed: {resp.text}"
        watchlist = resp.json()
        assert len(watchlist) > 0, "Expected bots in watchlist"
        print(f" -> Watchlist contains {len(watchlist)} tracked burner accounts")
        print(f"    Top Threat: {watchlist[0]['user_id']} (Threat: {watchlist[0]['max_threat_score']}%, Core: k={watchlist[0]['max_coreness']})")

    print("\n" + "="*60)
    print("ALL DATABASE & API CHECKS PASSED ZERO BUGS FOUND!")
    print("="*60)

if __name__ == "__main__":
    test_api()

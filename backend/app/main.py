import os
import json
import uuid
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    NarrativeMeta,
    SummaryMetrics
)
from app.core.nlp_engine import SemanticClusterEngine
from app.core.graph_engine import GraphAnalysisEngine
from app.core.database import DatabaseManager

# Global engine and database references
nlp_engine: SemanticClusterEngine = None
graph_engine: GraphAnalysisEngine = None
db_manager: DatabaseManager = None

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset.json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes models and SQLite database on server boot."""
    global nlp_engine, graph_engine, db_manager
    print("[Startup] Initializing GhostGrid NLP & Graph Engines...")
    nlp_engine = SemanticClusterEngine(model_name="all-MiniLM-L6-v2")
    graph_engine = GraphAnalysisEngine()
    print("[Startup] Initializing SQLite database...")
    db_manager = DatabaseManager()
    print("[Startup] GhostGrid backend ready with persistent SQLite storage.")
    yield
    print("[Shutdown] Cleaning up GhostGrid backend resources.")


app = FastAPI(
    title="GhostGrid API",
    description="Astroturf botnet & narrative coordination detection system with persistent SQLite storage",
    version="1.1.0",
    lifespan=lifespan
)

# Enable CORS for local development with React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint confirming engine and database readiness."""
    return {
        "status": "online",
        "service": "GhostGrid Watchdog API",
        "model_loaded": nlp_engine is not None,
        "graph_ready": graph_engine is not None,
        "database_ready": db_manager is not None
    }


@app.get("/api/sample-dataset")
async def get_sample_dataset():
    """Returns the synthetic test dataset with ground truth for instant demoing."""
    if not os.path.exists(DATASET_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample dataset not found. Please run generate_dataset.py first."
        )

    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            posts = json.load(f)
        return {"total_posts": len(posts), "posts": posts}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read dataset: {str(e)}"
        )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_feed(request: AnalyzeRequest):
    """
    Main analysis endpoint:
    1. Clusters semantically identical claims using sentence embeddings.
    2. Constructs bipartite & co-coordination graphs.
    3. Runs k-core decomposition and temporal burst detection.
    4. Automatically saves scan results to SQLite database.
    5. Returns graph topology and anomaly metrics.
    """
    if not request.posts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No posts provided in the request payload."
        )

    try:
        raw_posts = [p.model_dump() for p in request.posts]

        # 1. Semantic NLP Clustering
        annotated_posts, narratives = nlp_engine.cluster_posts(
            posts=raw_posts,
            similarity_threshold=request.similarity_threshold
        )

        # 2. Graph Decomposition & Anomaly Scoring
        graph_result = graph_engine.analyze(
            annotated_posts=annotated_posts,
            narratives=narratives,
            burst_window_minutes=request.burst_window_minutes,
            k_core_min=request.k_core_min
        )

        # 3. Format Narratives
        narratives_dict = {
            nid: NarrativeMeta(**meta) for nid, meta in narratives.items()
        }

        # 4. Persist to SQLite Database
        scan_id = f"scan_{uuid.uuid4().hex[:8]}"
        scan_name = request.scan_name or f"Scan {scan_id}"
        db_manager.save_scan(
            scan_id=scan_id,
            name=scan_name,
            total_posts=len(raw_posts),
            nodes=graph_result["nodes"],
            edges=graph_result["edges"],
            narratives=narratives_dict,
            flagged_accounts=graph_result["flagged_accounts"],
            summary=graph_result["summary"]
        )

        return AnalyzeResponse(
            scan_id=scan_id,
            nodes=graph_result["nodes"],
            edges=graph_result["edges"],
            narratives=narratives_dict,
            flagged_accounts=graph_result["flagged_accounts"],
            summary=SummaryMetrics(**graph_result["summary"])
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {str(e)}"
        )


@app.get("/api/scans")
async def get_all_scans(limit: int = 20):
    """Returns list of past investigation scans from SQLite database."""
    try:
        return db_manager.list_scans(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scan history: {str(e)}"
        )


@app.get("/api/scans/{scan_id}")
async def get_scan_details(scan_id: str):
    """Retrieves full graph and results for a previous scan from SQLite."""
    scan = db_manager.get_scan(scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID '{scan_id}' not found."
        )
    return scan


@app.get("/api/watchlist")
async def get_bot_watchlist():
    """Returns the persistent watchlist of all bot accounts caught across investigations."""
    try:
        return db_manager.get_watchlist()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch watchlist: {str(e)}"
        )

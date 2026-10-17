import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("STARTING GHOSTGRID FASTAPI BACKEND SERVER")
    print("Access interactive API documentation at: http://127.0.0.1:8000/docs")
    print("Health check endpoint at: http://127.0.0.1:8000/api/health")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

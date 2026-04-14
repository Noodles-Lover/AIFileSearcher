from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.files import router as files_router
from api.search import router as search_router
from api.index import router as index_router
from api.llm import router as llm_router

app = FastAPI(title="AI File Searcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files_router)
app.include_router(search_router)
app.include_router(index_router)
app.include_router(llm_router)


@app.on_event("startup")
def on_startup():
    from backend.RAG.SystemManager import SystemManager
    print("=" * 50)
    print("🚀 启动 AI File Searcher 后端服务")
    print("=" * 50)
    SystemManager.get_instance()


@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI File Searcher Backend is running"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 启动 AI File Searcher 后端服务")
    print("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=8000)

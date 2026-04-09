from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.files import router as files_router
from api.search import router as search_router
from api.index import router as index_router
from api.llm import router as llm_router

app = FastAPI(title="AI File Searcher API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置为具体的域名，开发环境可以用 *
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含文件相關路由
app.include_router(files_router)
app.include_router(search_router)
app.include_router(index_router)
app.include_router(llm_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI File Searcher Backend is running"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 启动 AI File Searcher 后端服务")
    print("=" * 50)
    
    # 允许外部访问，端口 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)

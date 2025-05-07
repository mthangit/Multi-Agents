from fastapi import APIRouter, HTTPException
from app.agents.orchestrator import OrchestratorAgent
from app.config.settings import Settings

router = APIRouter()
orchestrator = OrchestratorAgent()
orchestrator.initialize(Settings.APP_NAME, Settings.USER_ID)

@router.post("/search")
async def search(query: str):
    """Endpoint xử lý tìm kiếm"""
    try:
        result = await orchestrator.process(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/text")
async def process_text(text: str):
    """Endpoint xử lý văn bản"""
    try:
        result = await orchestrator.process(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image")
async def process_image(image_url: str):
    """Endpoint xử lý ảnh"""
    try:
        result = await orchestrator.process(image_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
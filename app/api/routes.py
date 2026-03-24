from fastapi import APIRouter, HTTPException
import logging
from app.models.request import ExtractionRequest, SubmitRequest
from app.models.response import ExtractionResponse, SubmitResponse, JobResultResponse
from app.extraction.pipeline import ExtractionPipeline
from app.services.queue_service import QueueService
from app.services.fhir_service import map_to_fhir
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
pipeline = ExtractionPipeline()
queue_service = QueueService()

@router.post("/extract", response_model=ExtractionResponse)
async def extract_clinical_data(request: ExtractionRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        response = await pipeline.process(request.text, request.language)
        return response
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=503, detail="Service Unavailable: Failed to extract data")

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.app_version}

@router.post("/submit", response_model=SubmitResponse)
async def submit_extraction(request: SubmitRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    job_id = await queue_service.submit(request.text, request.language)
    return SubmitResponse(job_id=job_id, status="pending")

@router.get("/result/{job_id}", response_model=JobResultResponse)
async def get_job_result(job_id: str):
    return await queue_service.get_result(job_id)

@router.post("/extract/fhir")
async def extract_fhir(request: ExtractionRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        response = await pipeline.process(request.text, request.language)
        return map_to_fhir(response)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=503, detail="Service Unavailable")

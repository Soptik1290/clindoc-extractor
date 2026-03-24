import redis.asyncio as aioredis
import uuid, json, asyncio
from app.core.config import settings
from app.models.response import JobResultResponse, ExtractionResponse
import logging

logger = logging.getLogger(__name__)

class QueueService:
    def __init__(self):
        self.redis = aioredis.from_url(settings.redis_url)

    async def _process_background(self, job_id: str, text: str, language: str):
        try:
            from app.extraction.pipeline import ExtractionPipeline
            pipeline = ExtractionPipeline()
            # Update status to processing
            await self.redis.set(f"job:{job_id}:status", "processing")
            
            result = await pipeline.process(text, language)
            
            # Save result
            await self.redis.set(f"job:{job_id}:result", result.model_dump_json())
            await self.redis.set(f"job:{job_id}:status", "done")
            # Set expiration of 24h
            await self.redis.expire(f"job:{job_id}:status", 86400)
            await self.redis.expire(f"job:{job_id}:result", 86400)
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await self.redis.set(f"job:{job_id}:status", "failed")
            await self.redis.set(f"job:{job_id}:error", str(e))

    async def submit(self, text: str, language: str) -> str:
        job_id = str(uuid.uuid4())
        await self.redis.set(f"job:{job_id}:status", "pending")
        asyncio.create_task(self._process_background(job_id, text, language))
        return job_id
    
    async def get_result(self, job_id: str) -> JobResultResponse:
        status = await self.redis.get(f"job:{job_id}:status")
        if not status:
            return JobResultResponse(job_id=job_id, status="not_found", error="Job not found")
            
        status = status.decode("utf-8")
        resp = JobResultResponse(job_id=job_id, status=status)
        
        if status == "done":
            res_str = await self.redis.get(f"job:{job_id}:result")
            if res_str:
                resp.result = ExtractionResponse.model_validate_json(res_str.decode("utf-8"))
        elif status == "failed":
            err_str = await self.redis.get(f"job:{job_id}:error")
            if err_str:
                resp.error = err_str.decode("utf-8")
                
        return resp

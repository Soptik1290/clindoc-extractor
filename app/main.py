from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.api.routes import router
from app.core.config import settings
import logging

# Configure basic logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="ClinDoc Extractor",
    description="API for extracting structured clinical entities from medical dictations.",
    version=settings.app_version,
)

app.include_router(router)

@app.get("/", include_in_schema=False)
async def get_ui():
    html = """
    <!DOCTYPE html>
    <html lang="cs">
    <head>
        <meta charset="UTF-8">
        <title>ClinDoc Extractor</title>
        <style>
            body { font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #f9fafb; color: #111827; }
            textarea { width: 100%; height: 180px; padding: 12px; border: 1px solid #d1d5db; border-radius: 8px; font-family: inherit; margin-bottom: 15px; box-sizing: border-box; resize: vertical; }
            button { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: background 0.2s; }
            button:hover { background: #1d4ed8; }
            button:disabled { background: #9ca3af; cursor: not-allowed; }
            pre { background: #1f2937; color: #f3f4f6; padding: 20px; border-radius: 8px; overflow-x: auto; font-size: 14px; }
            select { padding: 8px; border-radius: 6px; border: 1px solid #d1d5db; margin-bottom: 15px; background: white; }
        </style>
    </head>
    <body>
        <h1>ClinDoc Extractor - Testing UI</h1>
        <p>You can paste texts here for quick API testing.</p>
        <textarea id="text" placeholder="Paste clinical report, dictation, or record here..."></textarea>
        <br>
        <select id="lang">
            <option value="auto">Auto detect (auto)</option>
            <option value="cs">Czech (cs)</option>
            <option value="en">English (en)</option>
        </select>
        <div style="display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;">
            <button onclick="extract('/extract')">1. Standard JSON Extraction</button>
            <button onclick="extract('/extract/fhir')">2. Map to FHIR R4 Bundle</button>
            <button onclick="submitAsync()" style="background: #10b981;">3. Async Redis Queue (/submit)</button>
        </div>
        
        <h3 id="status" style="display:none; color: #4b5563;">⚙️ Processing (LLM model / Regex)...</h3>
        <pre id="result" style="display:none;"></pre>

        <script>
            function setButtonsDisabled(disabled) {
                document.querySelectorAll('button').forEach(b => b.disabled = disabled);
            }

            async function extract(endpoint) {
                const status = document.getElementById('status');
                const result = document.getElementById('result');
                
                setButtonsDisabled(true);
                status.textContent = '⚙️ Processing (LLM model / Regex)...';
                status.style.display = 'block';
                result.style.display = 'none';
                
                try {
                    const res = await fetch(endpoint, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            text: document.getElementById('text').value,
                            language: document.getElementById('lang').value
                        })
                    });
                    const data = await res.json();
                    result.textContent = JSON.stringify(data, null, 2);
                    result.style.display = 'block';
                } catch (e) {
                    result.textContent = 'Error: ' + e;
                    result.style.display = 'block';
                } finally {
                    setButtonsDisabled(false);
                    status.style.display = 'none';
                }
            }

            async function submitAsync() {
                const status = document.getElementById('status');
                const result = document.getElementById('result');
                
                setButtonsDisabled(true);
                status.textContent = '⚙️ Submitting job to Redis queue...';
                status.style.display = 'block';
                result.style.display = 'none';
                
                try {
                    // Send to queue
                    let res = await fetch('/submit', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            text: document.getElementById('text').value,
                            language: document.getElementById('lang').value
                        })
                    });
                    let data = await res.json();
                    
                    if (res.ok && data.job_id) {
                        const jobId = data.job_id;
                        
                        // Polling for result
                        while (true) {
                            status.textContent = `⚙️ Job ${jobId} is in queue. Polling API...`;
                            await new Promise(r => setTimeout(r, 1500));
                            
                            let pollRes = await fetch('/result/' + jobId);
                            let pollData = await pollRes.json();
                            
                            if (pollData.status === 'done' || pollData.status === 'failed') {
                                result.textContent = JSON.stringify(pollData, null, 2);
                                break;
                            }
                        }
                    } else {
                        result.textContent = JSON.stringify(data, null, 2);
                    }
                    result.style.display = 'block';
                } catch (e) {
                    result.textContent = 'Error: ' + e;
                    result.style.display = 'block';
                } finally {
                    setButtonsDisabled(false);
                    status.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


"""
FastAPI backend for football panel discussions
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from enhanced_panel import EnhancedPanelDiscussion

app = FastAPI(
    title="Football AI Panel",
    description="AI-powered football match analysis with expert personas",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiscussionResponse(BaseModel):
    discussion_id: str
    script: List[Dict[str, str]]
    audio_url: Optional[str] = None
    video_url: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "Football AI Panel API",
        "description": "Generates expert panel discussions about football matches",
        "endpoints": [
            "/api/discussions/{match_id}"
        ]
    }

@app.get("/api/discussions/{match_id}")
async def get_discussion(match_id: str) -> DiscussionResponse:
    """Generate a panel discussion for a match"""
    try:
        # Create enhanced panel discussion
        panel = EnhancedPanelDiscussion(match_id)
        script = await panel.generate_script()
        
        if not script:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate discussion. Please check if match data exists."
            )
            
        return DiscussionResponse(
            discussion_id=match_id,
            script=script,
            audio_url=None,
            video_url=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

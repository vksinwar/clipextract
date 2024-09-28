from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, validator
import yt_dlp
import os
import tempfile
import re
import unicodedata
from typing import Dict, Any
from mangum import Mangum

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: HttpUrl

    @validator('url')
    def validate_url(cls, v):
        allowed_domains = [
            'instagram.com', 'youtube.com', 'youtu.be', 'facebook.com', 'fb.watch',
            'tiktok.com', 'twitter.com', 'vimeo.com', 'dailymotion.com', 'twitch.tv',
            'linkedin.com'
        ]
        if not any(domain in str(v).lower() for domain in allowed_domains):
            raise ValueError('URL must be from a supported platform')
        return v

def sanitize_filename(filename: str) -> str:
    filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    filename = re.sub(r'[^\w\-.]', '_', filename)
    return filename if filename else 'video'

@app.get("/api")
async def root():
    return {"message": "Application is running"}

@app.post("/api/download")
async def download_video(request: Request) -> Dict[str, Any]:
    try:
        data = await request.json()
        download_request = DownloadRequest(url=data['url'])
        
        ydl_opts = {
            'format': 'best',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(str(download_request.url), download=False)
            video_title = sanitize_filename(info['title'])
            video_url = info['url']
            
            return JSONResponse(content={
                "title": video_title,
                "url": video_url
            })
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

handler = Mangum(app)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
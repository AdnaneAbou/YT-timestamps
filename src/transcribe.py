import requests
import time
import os
import requests
import re

def transcribe_youtube_video(video_url: str, api_key: str, language: str = "auto") -> str:
    """
    Transcribes YouTube videos using SpeechFlow API without audio download
    Args:
        video_url: YouTube URL (full link or video ID)
        api_key: SpeechFlow API key (get from https://console.speechflow.io/home)
        language: ISO language code (e.g., 'en', 'ja') or 'auto' for detection
    Returns:
        Transcribed text with punctuation
    """
    # Clean URL format
    video_id = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", video_url)
    processed_url = f"https://youtu.be/{video_id.group(1)}" if video_id else video_url

    # API configuration
    endpoint = "https://api.speechflow.io/v1/transcribe"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": processed_url,
        "language": language,
        "output_format": "text"
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("transcript", "No transcript returned")
    
    except requests.exceptions.HTTPError as err:
        error_msg = response.json().get("error", "Unknown API error")
        raise Exception(f"HTTP Error: {err}\nAPI Message: {error_msg}")
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")


if __name__ == "__main__":
    api_key = os.getenv("SPEECHFLOW_API_KEY")
    youtube_link = "https://www.youtube.com/watch?v=WKjMtf8_l8A"  

    transcript = transcribe_youtube_video(
        video_url=youtube_link,
        api_key=api_key,
        language="auto"  # Optional language forcing
    )
    print(transcript)
   
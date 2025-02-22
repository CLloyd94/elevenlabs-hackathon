from typing import Optional, Dict, Any, Literal
import os
from pathlib import Path
import fal_client
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
env_path = Path(__file__).parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

AspectRatioType = Literal["16:9", "9:16", "1:1"]
DurationType = Literal["5", "10"]

@dataclass
class VideoGenerationConfig:
    """Configuration for video generation using Kling Video API.

    Attributes:
        prompt (str): Text description of how the video should look and behave.
        image_url (str): Local file path to the source image.
        duration (DurationType): Duration of the video in seconds. Either "5" or "10".
        aspect_ratio (AspectRatioType): Aspect ratio of the output video. Either "16:9", "9:16", or "1:1".
    """
    prompt: str  # video description
    image_url: str  # path to local image
    duration: DurationType = "5"
    aspect_ratio: AspectRatioType = "16:9"

class VideoCreator:
    """A tool for creating videos from images using the fal.ai Kling Video API.

    This class handles the interaction with fal.ai's Kling Video API to generate
    videos from static images with specified parameters like duration, aspect ratio,
    and creative direction through video descriptions.

    Note:
        Requires FAL_KEY in the .env file in the project root directory.
        Format: FAL_KEY=your_api_key_here
    """

    def __init__(self):
        """Initialize the VideoCreator.
        
        Raises:
            ValueError: If FAL_KEY is not found in environment variables.
        """
        self.api_key = os.getenv("FAL_KEY")
        if not self.api_key or self.api_key == "YOUR_FAL_API_KEY_HERE":
            raise ValueError(
                "FAL_KEY not found in .env file or contains default value. "
                "Please add your fal.ai API key to the .env file in the format: "
                "FAL_KEY=your_api_key_here"
            )

    async def create_video(self, config: VideoGenerationConfig) -> Dict[str, Any]:
        """Generate a video from a local image using the Kling Video API.

        Args:
            config (VideoGenerationConfig): Configuration for video generation including
                prompt (video description), image_url (local image path), duration, and aspect ratio.

        Returns:
            Dict[str, Any]: The API response containing the generated video information in format:
                {
                    "video": {
                        "url": "https://v2.fal.media/files/..."
                    }
                }

        Raises:
            Exception: If the video generation fails or the API returns an error.
        """
        try:
            # Get the URL for the image
            print(f"Uploading image from path: {config.image_url}")
            image_url = fal_client.upload_file(config.image_url)
            print(f"Image successfully uploaded to: {image_url}")

            print(f"Starting video generation with config: {config}")
            
            # Submit the request asynchronously
            handler = await fal_client.submit_async(
                "fal-ai/kling-video/v1.6/pro/image-to-video",
                arguments={
                    "prompt": config.prompt,
                    "image_url": image_url,
                    "duration": config.duration,
                    "aspect_ratio": config.aspect_ratio
                }
            )
            
            request_id = handler.request_id
            print(f"Request submitted with ID: {request_id}")
            
            # Poll for results
            max_attempts = 30  # 5 minutes total (10 second intervals)
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    print(f"Checking for results (attempt {attempt + 1}/{max_attempts})...")
                    result = await fal_client.result_async(
                        "fal-ai/kling-video/v1.6/pro/image-to-video",
                        request_id
                    )
                    
                    # If we get here, we have a result
                    print(f"Received API response: {result}")
                    
                    if not result or not isinstance(result, dict):
                        raise Exception(f"Invalid API response format: {result}")
                    
                    video_url = result.get("video", {}).get("url")
                    if not video_url:
                        raise Exception(f"Missing video URL in response: {result}")
                    
                    print(f"Successfully generated video at: {video_url}")
                    return {
                        "video": {
                            "url": video_url
                        }
                    }
                    
                except Exception as e:
                    if "not_found" in str(e).lower() or "no result" in str(e).lower():
                        # Result not ready yet, wait and try again
                        print("Result not ready yet, waiting...")
                        await asyncio.sleep(10)  # Wait 10 seconds before next attempt
                        attempt += 1
                        continue
                    else:
                        # Unexpected error
                        raise
            
            raise Exception(f"Timeout waiting for video generation after {max_attempts} attempts")
                
        except Exception as e:
            print(f"Error details: {str(e)}")
            raise Exception(f"Failed to generate video: {str(e)}")

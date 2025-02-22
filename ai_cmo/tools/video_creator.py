from typing import Optional, Dict, Any, Literal
import os
from pathlib import Path
import fal_client
from dataclasses import dataclass, field
from dotenv import load_dotenv
import asyncio
import openai
import requests
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import tempfile

# Load environment variables from .env file
env_path = Path(__file__).parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

AspectRatioType = Literal["16:9", "9:16", "1:1"]
DurationType = Literal["5", "10"]

@dataclass
class VoiceConfig:
    """Configuration for text-to-speech generation.
    
    Attributes:
        enabled (bool): Whether to generate a voiceover for the video.
        voice_id (str): ElevenLabs voice ID to use. Defaults to "JBFqnCBsd6RMkjVDRZzb".
        model_id (str): ElevenLabs model ID to use. Defaults to "eleven_multilingual_v2".
        output_format (str): Audio output format. Defaults to "mp3_44100_128".
    """
    enabled: bool = False
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    model_id: str = "eleven_multilingual_v2"
    output_format: str = "mp3_44100_128"

@dataclass
class ScriptConfig:
    """Configuration for script generation.
    
    Attributes:
        enabled (bool): Whether to generate a script for the video.
        base_script (Optional[str]): Optional base script to use. If not provided, one will be generated.
    """
    enabled: bool = False
    base_script: Optional[str] = None

@dataclass
class VideoGenerationConfig:
    """Configuration for video generation using Kling Video API.

    Attributes:
        prompt (str): Text description of how the video should look and behave.
        image_url (str): Local file path to the source image.
        duration (DurationType): Duration of the video in seconds. Either "5" or "10".
        aspect_ratio (AspectRatioType): Aspect ratio of the output video. Either "16:9", "9:16", or "1:1".
        script (ScriptConfig): Configuration for script generation.
        voice (VoiceConfig): Configuration for voice generation.
    """
    prompt: str  # video description
    image_url: str  # path to local image
    duration: DurationType = "5"
    aspect_ratio: AspectRatioType = "16:9"
    script: ScriptConfig = field(default_factory=ScriptConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)

class VideoCreator:
    """A tool for creating videos from images using the fal.ai Kling Video API.

    This class handles the interaction with fal.ai's Kling Video API to generate
    videos from static images with specified parameters like duration, aspect ratio,
    and creative direction through video descriptions. It can also generate scripts
    using GPT-4 and voiceovers using ElevenLabs.

    Note:
        Requires the following environment variables:
        - FAL_KEY: fal.ai API key
        - OPENAI_API_KEY: OpenAI API key for GPT-4
        - ELEVENLABS_API_KEY: ElevenLabs API key for text-to-speech
    """

    def __init__(self):
        """Initialize the VideoCreator.
        
        Raises:
            ValueError: If required API keys are not found in environment variables.
        """
        # Check fal.ai API key
        self.fal_api_key = os.getenv("FAL_KEY")
        if not self.fal_api_key or self.fal_api_key == "YOUR_FAL_API_KEY_HERE":
            raise ValueError(
                "FAL_KEY not found in .env file or contains default value. "
                "Please add your fal.ai API key to the .env file."
            )

        # Check OpenAI API key
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file.")
        openai.api_key = self.openai_api_key

        # Initialize ElevenLabs client
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in .env file.")
        self.elevenlabs_client = ElevenLabs()

    async def _generate_script(self, prompt: str, duration: str) -> str:
        """Generate a script using GPT-4.

        Args:
            prompt (str): The video description prompt.
            duration (str): Video duration in seconds.

        Returns:
            str: Generated script.

        Raises:
            Exception: If script generation fails.
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional script writer. Create engaging, concise scripts that match the timing constraints."},
                    {"role": "user", "content": f"Write a {duration}-second script for a video with this description: {prompt}. The script should be timed to match the video duration exactly."}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Failed to generate script: {str(e)}")

    async def _generate_voiceover(self, text: str, voice_config: VoiceConfig) -> bytes:
        """Generate a voiceover using ElevenLabs text-to-speech.

        Args:
            text (str): The text to convert to speech.
            voice_config (VoiceConfig): Configuration for voice generation.

        Returns:
            bytes: The generated audio data.

        Raises:
            Exception: If voiceover generation fails.
        """
        try:
            print(f"Generating voiceover for text: {text[:100]}...")
            audio = self.elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=voice_config.voice_id,
                model_id=voice_config.model_id,
                output_format=voice_config.output_format,
            )
            print("Voiceover generated successfully")
            return audio
        except Exception as e:
            raise Exception(f"Failed to generate voiceover: {str(e)}")

    def preview_audio(self, audio_data: bytes) -> None:
        """Preview the generated audio using the system's audio output.
        
        This method saves the audio data to a temporary file and plays it
        using the elevenlabs.play function.

        Args:
            audio_data (bytes): The audio data to play.
        """
        try:
            print("Playing generated voiceover...")
            play(audio_data)
        except Exception as e:
            print(f"Failed to play audio: {str(e)}")

    def save_audio(self, audio_data: bytes, output_path: str) -> None:
        """Save the generated audio to a file.
        
        Args:
            audio_data (bytes): The audio data to save.
            output_path (str): The path where to save the audio file.
        """
        try:
            print(f"Saving audio to {output_path}...")
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            print(f"Audio saved successfully to {output_path}")
        except Exception as e:
            raise Exception(f"Failed to save audio: {str(e)}")

    async def create_video(self, config: VideoGenerationConfig) -> Dict[str, Any]:
        """Generate a video from a local image using the Kling Video API.

        If script generation is enabled, this will also generate a script using GPT-4.
        If voice generation is enabled, this will generate a voiceover using ElevenLabs.

        Args:
            config (VideoGenerationConfig): Configuration for video generation including
                prompt (video description), image_url (local image path), duration,
                aspect ratio, script settings, and voice settings.

        Returns:
            Dict[str, Any]: The API response containing the generated video information,
                optionally the script, and optionally the voiceover audio data.

        Raises:
            Exception: If video generation fails.
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

                    response = {
                        "video": {
                            "url": video_url
                        }
                    }

                    # If script generation is enabled, generate script
                    if config.script.enabled:
                        print("Generating script...")
                        
                        # Generate or use provided script
                        script = config.script.base_script
                        if not script:
                            script = await self._generate_script(config.prompt, config.duration)
                        print(f"Using script: {script}")
                        response["script"] = script

                        # If voice generation is enabled and we have a script, generate voiceover
                        if config.voice.enabled:
                            print("Generating voiceover...")
                            audio_data = await self._generate_voiceover(script, config.voice)
                            response["voiceover"] = audio_data

                    return response
                    
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

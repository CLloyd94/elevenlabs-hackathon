from quart import Quart, request, send_file, jsonify
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os
from dotenv import load_dotenv
from io import BytesIO
import traceback
from openai import OpenAI
import json
import logging
import sys
import asyncio
from quart.templating import render_template_string
import subprocess
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('voiceover_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file (look in parent directories)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
logger.info(f"Looking for .env file at: {env_path}")
load_dotenv(dotenv_path=env_path)

app = Quart(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# Initialize ElevenLabs client
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
if not elevenlabs_api_key:
    logger.error("ELEVENLABS_API_KEY not found in .env file")
    raise ValueError("ELEVENLABS_API_KEY not found in .env file")
logger.info("ElevenLabs API key found")
client = ElevenLabs(api_key=elevenlabs_api_key)

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEY not found in .env file")
    raise ValueError("OPENAI_API_KEY not found in .env file")
logger.info("OpenAI API key found")
openai_client = OpenAI(api_key=openai_api_key)

# Create temp directory for uploads
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Voiceover Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        textarea {
            width: 100%;
            height: 150px;
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        select {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .audio-player {
            margin-top: 20px;
        }
        .error {
            color: red;
            margin-top: 10px;
            padding: 10px;
            background-color: #fee;
            border-radius: 4px;
            display: none;
        }
        .loading {
            display: none;
            margin-top: 20px;
            text-align: center;
            color: #666;
        }
        .scripts-container {
            margin-top: 20px;
            display: none;
        }
        .script-option {
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .script-option:hover {
            background-color: #f0f0f0;
        }
        .script-option.selected {
            background-color: #e8f5e9;
            border-color: #4CAF50;
        }
        .section {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        .duration-select {
            width: auto;
            display: inline-block;
            margin-right: 10px;
        }
        .video-preview {
            margin-top: 20px;
            max-width: 100%;
            border-radius: 4px;
        }
        .file-input-container {
            margin: 10px 0;
        }
        .upload-progress {
            display: none;
            margin-top: 10px;
            padding: 10px;
            background-color: #e8f5e9;
            border-radius: 4px;
        }
        .extracted-audio {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Voiceover Generator</h1>
        
        <!-- Video Upload Section -->
        <div class="section">
            <h2>1. Upload Video</h2>
            <div class="file-input-container">
                <label for="videoFile">Select a video file:</label>
                <input type="file" id="videoFile" accept="video/*" />
                <button id="uploadVideoBtn" style="display: none;">Upload Video</button>
            </div>
            <div id="uploadProgress" class="upload-progress">Processing video...</div>
            <div id="videoPreview"></div>
            <div id="videoError" class="error"></div>
        </div>
        
        <!-- Script Generation Section -->
        <div class="section">
            <h2>2. Generate Script</h2>
            <div>
                <label for="prompt">Enter your prompt for script generation:</label>
                <textarea id="prompt" placeholder="Describe what kind of script you want, e.g.: 'Write a 30-second commercial script for a luxury car that emphasizes safety and elegance'"></textarea>
            </div>
            <div style="margin: 10px 0;">
                <label for="duration">Duration:</label>
                <select id="duration" class="duration-select">
                    <option value="5">5 seconds</option>
                    <option value="10">10 seconds</option>
                    <option value="15">15 seconds</option>
                    <option value="30" selected>30 seconds</option>
                    <option value="60">60 seconds</option>
                </select>
                <button id="generateScripts">Generate Scripts</button>
            </div>
            <div id="scriptsLoading" class="loading">Generating scripts...</div>
            <div id="scriptsError" class="error"></div>
            <div id="scriptsContainer" class="scripts-container"></div>
        </div>

        <!-- Voice Generation Section -->
        <div class="section">
            <h2>3. Generate Voiceover</h2>
            <div>
                <label for="text">Script to convert to speech:</label>
                <textarea id="text" name="text" required placeholder="Select a generated script above or enter your own text here..."></textarea>
            </div>
            <div>
                <label for="voice">Select voice:</label>
                <select id="voice" name="voice">
                    <option value="wJqPPQ618aTW29mptyoc">Rita (Default)</option>
                    <option value="21m00Tcm4TlvDq8ikWAM">Charlie</option>
                    <option value="AZnzlk1XvdvUeBnXmlld">Domi</option>
                    <option value="EXAVITQu4vr4xnSDxMaL">Bella</option>
                    <option value="ErXwobaYiN019PkySvjV">Antoni</option>
                </select>
            </div>
            <button id="generateVoiceover">Preview Voiceover</button>
            <div id="voiceoverLoading" class="loading">Generating voiceover...</div>
            <div id="voiceoverError" class="error"></div>
            <div id="audioContainer" class="audio-player"></div>
        </div>

        <!-- Video Combination Section -->
        <div class="section" id="videoCombinationSection" style="display: none;">
            <h2>4. Combine Video with Voiceover</h2>
            <p>Listen to the voiceover above. If you're happy with it, click below to combine it with your video and add subtitles.</p>
            <button id="combineVideo">Combine Video & Voiceover</button>
            <div id="combinationLoading" class="loading">Creating final video with subtitles...</div>
            <div id="combinationError" class="error"></div>
            <div id="finalVideoContainer"></div>
        </div>

    </div>

    <script>
        // Video upload handling
        const videoFile = document.getElementById('videoFile');
        const uploadVideoBtn = document.getElementById('uploadVideoBtn');
        const uploadProgress = document.getElementById('uploadProgress');
        const videoPreview = document.getElementById('videoPreview');
        const videoError = document.getElementById('videoError');
        
        // Store paths globally
        let savedVideoPath = null;
        let currentVoiceoverAudioUrl = null;

        // Show upload button when file is selected
        videoFile.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (!file) {
                uploadVideoBtn.style.display = 'none';
                videoPreview.innerHTML = '';
                return;
            }
            
            // Clear previous preview and errors
            videoPreview.innerHTML = '';
            videoError.style.display = 'none';
            
            // Validate file type
            if (!file.type.startsWith('video/')) {
                videoError.textContent = 'Please select a valid video file';
                videoError.style.display = 'block';
                uploadVideoBtn.style.display = 'none';
                return;
            }
            
            // Show preview immediately after selection
            const videoURL = URL.createObjectURL(file);
            videoPreview.innerHTML = `
                <video controls class="video-preview">
                    <source src="${videoURL}" type="video/mp4">
                    Your browser does not support the video element.
                </video>
            `;
            
            // Show upload button
            uploadVideoBtn.style.display = 'inline-block';
        });
        
        // Handle video upload
        uploadVideoBtn.addEventListener('click', async () => {
            const file = videoFile.files[0];
            if (!file) return;
            
            uploadVideoBtn.disabled = true;
            uploadProgress.style.display = 'block';
            videoError.style.display = 'none';
            
            const formData = new FormData();
            formData.append('video', file);
            
            try {
                console.log('Uploading video file:', file.name, 'Size:', file.size);
                const response = await fetch('/api/upload-video', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to process video');
                }
                
                // Store the video path for later use
                savedVideoPath = data.video_path;
                console.log('Saved video path:', savedVideoPath);
                
                // Update video preview with the server URL
                videoPreview.innerHTML = `
                    <video controls class="video-preview">
                        <source src="${data.video_url}" type="video/mp4">
                        Your browser does not support the video element.
                    </video>
                `;
                
            } catch (error) {
                console.error('Upload error:', error);
                videoError.textContent = 'Error: ' + error.message;
                videoError.style.display = 'block';
            } finally {
                uploadVideoBtn.disabled = false;
                uploadProgress.style.display = 'none';
            }
        });

        // Script generation
        const generateScriptsBtn = document.getElementById('generateScripts');
        const prompt = document.getElementById('prompt');
        const duration = document.getElementById('duration');
        const scriptsContainer = document.getElementById('scriptsContainer');
        const scriptsLoading = document.getElementById('scriptsLoading');
        const scriptsError = document.getElementById('scriptsError');
        const scriptTextarea = document.getElementById('text');

        generateScriptsBtn.onclick = async () => {
            console.log('Generate Scripts button clicked');
            console.log('Current prompt:', prompt.value);
            console.log('Selected duration:', duration.value);

            if (!prompt.value.trim()) {
                console.log('Error: Empty prompt');
                scriptsError.textContent = 'Please enter a prompt';
                scriptsError.style.display = 'block';
                return;
            }

            console.log('Starting script generation process...');
            generateScriptsBtn.disabled = true;
            scriptsLoading.style.display = 'block';
            scriptsError.style.display = 'none';
            scriptsContainer.style.display = 'none';

            try {
                console.log('Sending request to /api/generate-scripts');
                console.log('Request payload:', {
                    prompt: prompt.value,
                    duration: duration.value
                });

                const response = await fetch('/api/generate-scripts', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        prompt: prompt.value,
                        duration: duration.value
                    }),
                });

                const data = await response.json();
                console.log('Response received:', data);

                if (!response.ok) {
                    console.error('API error:', data.error);
                    throw new Error(data.error || 'Failed to generate scripts');
                }

                console.log('Rendering generated scripts...');
                scriptsContainer.innerHTML = data.scripts.map((script, index) => `
                    <div class="script-option" onclick="selectScript(this, ${index})">
                        <strong>Option ${index + 1}:</strong><br>
                        ${script.replace(/\\n/g, '<br>')}
                    </div>
                `).join('');

                scriptsContainer.style.display = 'block';
                console.log('Scripts rendered successfully');
            } catch (error) {
                console.error('Error in script generation:', error);
                scriptsError.textContent = 'Error: ' + error.message;
                scriptsError.style.display = 'block';
            } finally {
                console.log('Script generation process completed');
                generateScriptsBtn.disabled = false;
                scriptsLoading.style.display = 'none';
            }
        };

        function selectScript(element, index) {
            console.log('Script selected:', index + 1);
            // Remove selection from all scripts
            document.querySelectorAll('.script-option').forEach(el => {
                el.classList.remove('selected');
            });
            
            // Add selection to clicked script
            element.classList.add('selected');
            
            // Set the script text in the voiceover textarea
            const scriptText = element.textContent.replace('Option ' + (index + 1) + ':', '').trim();
            scriptTextarea.value = scriptText;
            console.log('Script text set:', scriptText);
        }

        // Voiceover generation
        const generateVoiceoverBtn = document.getElementById('generateVoiceover');
        const voice = document.getElementById('voice');
        const audioContainer = document.getElementById('audioContainer');
        const voiceoverLoading = document.getElementById('voiceoverLoading');
        const voiceoverError = document.getElementById('voiceoverError');
        const videoCombinationSection = document.getElementById('videoCombinationSection');
        const combineVideoBtn = document.getElementById('combineVideo');
        const combinationLoading = document.getElementById('combinationLoading');
        const combinationError = document.getElementById('combinationError');
        const finalVideoContainer = document.getElementById('finalVideoContainer');

        generateVoiceoverBtn.onclick = async () => {
            if (!scriptTextarea.value.trim()) {
                voiceoverError.textContent = 'Please enter text or select a script';
                voiceoverError.style.display = 'block';
                return;
            }

            generateVoiceoverBtn.disabled = true;
            voiceoverLoading.style.display = 'block';
            voiceoverError.style.display = 'none';
            audioContainer.innerHTML = '';
            videoCombinationSection.style.display = 'none';

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: scriptTextarea.value,
                        voice: voice.value
                    }),
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to generate voiceover');
                }

                // Show the audio preview
                currentVoiceoverAudioUrl = data.audio_url;
                audioContainer.innerHTML = `
                    <audio controls autoplay>
                        <source src="${data.audio_url}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                `;

                // Show the video combination section
                videoCombinationSection.style.display = 'block';
            } catch (error) {
                voiceoverError.textContent = 'Error: ' + error.message;
                voiceoverError.style.display = 'block';
            } finally {
                generateVoiceoverBtn.disabled = false;
                voiceoverLoading.style.display = 'none';
            }
        };

        combineVideoBtn.onclick = async () => {
            console.log('Current video path:', savedVideoPath);  // Debug log
            
            if (!savedVideoPath) {
                combinationError.textContent = 'Please upload a video first';
                combinationError.style.display = 'block';
                return;
            }

            if (!currentVoiceoverAudioUrl) {
                combinationError.textContent = 'Please generate a voiceover first';
                combinationError.style.display = 'block';
                return;
            }

            combineVideoBtn.disabled = true;
            combinationLoading.style.display = 'block';
            combinationError.style.display = 'none';
            finalVideoContainer.innerHTML = '';

            try {
                const response = await fetch('/api/combine', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        video_path: savedVideoPath,
                        audio_url: currentVoiceoverAudioUrl,
                        text: scriptTextarea.value,
                        duration: parseInt(duration.value) || 30
                    }),
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to combine video');
                }

                // Show the final video
                finalVideoContainer.innerHTML = `
                    <h3>Final Video with Voiceover and Subtitles</h3>
                    <video controls>
                        <source src="${data.video_url}" type="video/mp4">
                        Your browser does not support the video element.
                    </video>
                    <p><a href="${data.video_url}" download class="download-link">Download Video</a></p>
                `;
            } catch (error) {
                combinationError.textContent = 'Error: ' + error.message;
                combinationError.style.display = 'block';
            } finally {
                combineVideoBtn.disabled = false;
                combinationLoading.style.display = 'none';
            }
        };

        // Add some CSS for the download link
        const style = document.createElement('style');
        style.textContent = `
            .download-link {
                display: inline-block;
                margin-top: 10px;
                padding: 8px 16px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
            .download-link:hover {
                background-color: #45a049;
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
"""

@app.route('/')
async def index():
    logger.info("Serving index page")
    return await render_template_string(HTML_TEMPLATE)

@app.route('/api/generate-scripts', methods=['POST'])
async def generate_scripts_endpoint():
    try:
        logger.info("Received script generation request")
        data = await request.get_json()
        logger.debug(f"Request data: {data}")
        
        if not data:
            logger.warning("No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400

        prompt = data.get('prompt')
        duration = data.get('duration', '30')

        if not prompt:
            logger.warning("No prompt provided")
            return jsonify({'error': 'No prompt provided'}), 400

        logger.info(f"Generating scripts for duration: {duration}s")
        scripts = await generate_scripts(prompt, duration)
        
        logger.info("Scripts generated successfully")
        return jsonify({
            'message': 'Scripts generated successfully',
            'scripts': scripts
        })

    except Exception as e:
        logger.error("Error in generate_scripts_endpoint:")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
async def generate():
    try:
        logger.info("Received voiceover generation request")
        data = await request.get_json()
        logger.debug(f"Request data: {data}")
        
        if not data:
            logger.warning("No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400

        text = data.get('text')
        voice_id = data.get('voice')

        if not text:
            logger.warning("No text provided")
            return jsonify({'error': 'No text provided'}), 400
        if not voice_id:
            logger.warning("No voice ID provided")
            return jsonify({'error': 'No voice ID provided'}), 400

        logger.info(f"Generating voiceover for text: {text[:100]}...")
        logger.info(f"Using voice ID: {voice_id}")

        # Generate audio
        logger.debug("Calling ElevenLabs API")
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        # Convert generator to bytes
        logger.debug("Converting audio generator to bytes")
        audio_data = b''
        for chunk in audio:
            if chunk:
                audio_data += chunk

        if not audio_data:
            logger.error("No audio data generated")
            return jsonify({'error': 'No audio data generated'}), 500

        logger.debug(f"Generated {len(audio_data)} bytes of audio data")

        # Save audio to temporary file
        temp_path = os.path.join(app.root_path, 'temp')
        os.makedirs(temp_path, exist_ok=True)
        
        audio_filename = f"voiceover_{abs(hash(text + voice_id))}.mp3"
        audio_filepath = os.path.join(temp_path, audio_filename)
        
        logger.debug(f"Saving audio to {audio_filepath}")
        with open(audio_filepath, 'wb') as f:
            f.write(audio_data)

        logger.info("Voiceover generated successfully")
        return jsonify({
            'message': 'Voiceover generated successfully',
            'audio_url': f'/api/audio/{audio_filename}'
        })

    except Exception as e:
        logger.error("Error generating voiceover:")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio/<filename>')
async def serve_audio(filename):
    try:
        logger.info(f"Serving audio file: {filename}")
        filepath = os.path.join(app.root_path, 'temp', filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"Audio file not found: {filepath}")
            return jsonify({'error': 'Audio file not found'}), 404
            
        return await send_file(
            filepath,
            mimetype='audio/mpeg'
        )
    except Exception as e:
        logger.error(f"Error serving audio file {filename}:")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 404

@app.route('/api/video/<filename>')
async def serve_video(filename):
    """Serve a generated video file.
    
    Args:
        filename (str): Name of the video file to serve
        
    Returns:
        Response: The video file response
    """
    try:
        logger.info(f"Serving video file: {filename}")
        filepath = os.path.join(TEMP_DIR, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"Video file not found: {filepath}")
            return jsonify({'error': 'Video file not found'}), 404
            
        return await send_file(
            filepath,
            mimetype='video/mp4'
        )
    except Exception as e:
        logger.error(f"Error serving video file {filename}:")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 404

async def extract_audio_ffmpeg(video_path: str, audio_path: str) -> bool:
    """Extract audio from video using FFmpeg.
    
    Args:
        video_path (str): Path to the input video file
        audio_path (str): Path where the audio should be saved
        
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    try:
        logger.info(f"Extracting audio from {video_path} to {audio_path}")
        # Use FFmpeg to extract audio, converting to mp3 format
        cmd = [
            'ffmpeg',
            '-i', video_path,           # Input file
            '-vn',                      # Disable video
            '-acodec', 'libmp3lame',    # Use MP3 codec
            '-q:a', '2',                # High quality (0-9, lower is better)
            '-y',                       # Overwrite output file
            audio_path
        ]
        
        # Run FFmpeg command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"FFmpeg error: {stderr.decode()}")
            return False
            
        logger.info("Audio extraction completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during audio extraction: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@app.route('/api/upload-video', methods=['POST'])
async def upload_video():
    try:
        logger.info("Received video upload request")
        
        if 'video' not in (await request.files):
            logger.warning("No video file in request")
            return jsonify({'error': 'No video file uploaded'}), 400
            
        video_file = (await request.files)['video']
        
        if not video_file or not allowed_file(video_file.filename):
            logger.warning("Invalid file type")
            return jsonify({'error': 'Invalid file type'}), 400
            
        # Secure the filename and save the video in temp directory
        filename = secure_filename(video_file.filename)
        video_path = os.path.join(TEMP_DIR, filename)
        await video_file.save(video_path)
        logger.info(f"Video saved to {video_path}")
        
        # Return both the URL for preview and the file path for processing
        return jsonify({
            'message': 'Video uploaded successfully',
            'video_url': f'/api/video/{filename}',
            'video_path': video_path
        })
        
    except Exception as e:
        logger.error("Error processing video upload:")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

async def generate_scripts(prompt: str, duration: str) -> list:
    """Generate multiple script variations using GPT-4."""
    try:
        logger.info(f"Generating scripts for prompt: {prompt[:100]}... (duration: {duration}s)")
        
        completion = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You are a professional script writer specializing in voiceovers and commercials. 
                Create engaging, natural-sounding scripts that match the timing constraints perfectly. 
                Each script should be carefully timed where speaking at a natural pace would match the specified duration."""},
                {"role": "user", "content": f"""Write 3 different {duration}-second script variations based on this prompt: {prompt}

                Requirements:
                1. Each script must be timed to be spoken in exactly {duration} seconds at a natural pace
                2. Use natural, conversational language
                3. Make each variation distinct but equally engaging
                4. Focus on clarity and impact
                5. Avoid any audio/visual directions - just the spoken words
                6. Keep the length to no more than 3 sentences.
                7. Keep sentences short.
                8. The last sentence should be a call-to-action like 'get your estimate' or 'learn more'.

                Return ONLY the three script variations, separated by ||| (three pipes)."""}
            ]
        )
        
        logger.debug(f"GPT-4 response: {completion.choices[0].message.content}")
        
        # Split the response into individual scripts
        scripts = completion.choices[0].message.content.split('|||')
        cleaned_scripts = [script.strip() for script in scripts]
        
        logger.info(f"Generated {len(cleaned_scripts)} script variations")
        return cleaned_scripts

    except Exception as e:
        logger.error(f"Error generating scripts: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def generate_srt_subtitles(text: str, duration: int) -> str:
    """Generate SRT subtitles from script text.
    
    Args:
        text (str): The script text to convert to subtitles
        duration (int): Total duration in seconds
        
    Returns:
        str: SRT formatted subtitles
    """
    try:
        logger.info(f"Generating SRT subtitles for text: {text[:100]}...")
        
        # Split text into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Calculate rough timing for each sentence
        time_per_sentence = duration / len(sentences)
        
        # Generate SRT format
        srt_content = []
        for i, sentence in enumerate(sentences, 1):
            start_time = (i - 1) * time_per_sentence
            end_time = i * time_per_sentence
            
            # Format timestamps as HH:MM:SS,mmm
            start_str = f"{int(start_time//3600):02d}:{int((start_time%3600)//60):02d}:{int(start_time%60):02d},000"
            end_str = f"{int(end_time//3600):02d}:{int((end_time%3600)//60):02d}:{int(end_time%60):02d},000"
            
            srt_content.extend([
                str(i),
                f"{start_str} --> {end_str}",
                sentence.strip() + ".",
                ""
            ])
        
        srt_text = "\n".join(srt_content)
        
        # Save to file
        temp_path = os.path.join(app.root_path, 'temp')
        os.makedirs(temp_path, exist_ok=True)
        
        filename = f"subtitles_{abs(hash(text))}.srt"
        filepath = os.path.join(temp_path, filename)
        
        logger.debug(f"Saving subtitles to {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(srt_text)
            
        logger.info("Subtitles generated successfully")
        return filepath
        
    except Exception as e:
        logger.error(f"Error generating subtitles: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def combine_video_audio_subtitles(video_path: str, audio_path: str, subtitles_path: str) -> str:
    """Combine video, audio and subtitles into a single video file using FFmpeg.
    
    Args:
        video_path (str): Path to the input video file
        audio_path (str): Path to the audio file
        subtitles_path (str): Path to the SRT subtitles file
        
    Returns:
        str: Path to the output video file
    """
    try:
        logger.info("Combining video, audio and subtitles...")
        
        # Create output filename
        output_filename = f"final_{os.path.basename(video_path)}"
        output_path = os.path.join(app.root_path, 'temp', output_filename)
        
        # FFmpeg command to combine video, audio and burn subtitles
        cmd = [
            'ffmpeg',
            '-i', video_path,           # Input video
            '-i', audio_path,           # Input audio
            '-c:v', 'libx264',          # Video codec
            '-c:a', 'aac',              # Audio codec
            '-b:a', '192k',             # Audio bitrate
            '-map', '0:v:0',            # Map first video stream from first input
            '-map', '1:a:0',            # Map first audio stream from second input
            '-vf', f"subtitles='{subtitles_path}'",  # Burn subtitles into video
            '-shortest',                # Match shortest input duration
            '-y',                       # Overwrite output file
            output_path
        ]
        
        # Run FFmpeg command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"FFmpeg error: {stderr.decode()}")
            raise Exception(f"FFmpeg error: {stderr.decode()}")
            
        logger.info(f"Successfully combined video, audio and subtitles to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error combining video, audio and subtitles: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.route('/api/combine', methods=['POST'])
async def combine():
    """Combine video with voiceover audio and subtitles."""
    try:
        logger.info("Received video combination request")
        data = await request.get_json()
        logger.debug(f"Request data: {data}")
        
        if not data:
            logger.warning("No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400

        video_path = data.get('video_path')
        audio_url = data.get('audio_url')
        text = data.get('text')
        duration = int(data.get('duration', '30'))

        if not video_path:
            logger.warning("No video path provided")
            return jsonify({'error': 'No video path provided'}), 400
        if not audio_url:
            logger.warning("No audio URL provided")
            return jsonify({'error': 'No audio URL provided'}), 400
        if not text:
            logger.warning("No text provided")
            return jsonify({'error': 'No text provided'}), 400

        # Get the audio file path from the URL
        audio_filename = audio_url.split('/')[-1]
        audio_path = os.path.join(app.root_path, 'temp', audio_filename)
        
        if not os.path.exists(audio_path):
            logger.error("Audio file not found")
            return jsonify({'error': 'Audio file not found'}), 404

        # Generate subtitles
        logger.info("Generating subtitles...")
        subtitles_filepath = await generate_srt_subtitles(text, duration)

        # Combine video, audio and subtitles
        logger.info("Combining video, audio and subtitles...")
        final_video_path = await combine_video_audio_subtitles(
            video_path,
            audio_path,
            subtitles_filepath
        )

        # Clean up subtitles file
        os.remove(subtitles_filepath)

        logger.info("Process completed successfully")
        return jsonify({
            'message': 'Video with voiceover and subtitles generated successfully',
            'video_url': f'/api/video/{os.path.basename(final_video_path)}'
        })

    except Exception as e:
        logger.error("Error combining video:")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Quart application")
    # Create temp directory if it doesn't exist
    temp_dir = os.path.join(app.root_path, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    logger.info(f"Temporary directory created at: {temp_dir}")
    
    # Log environment status
    logger.info(f"Environment variables loaded from: {env_path}")
    logger.info(f"OpenAI API key present: {bool(openai_api_key)}")
    logger.info(f"ElevenLabs API key present: {bool(elevenlabs_api_key)}")
    
    app.run(debug=True, port=5001) 

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
    </style>
</head>
<body>
    <div class="container">
        <h1>Voiceover Generator</h1>
        
        <!-- Script Generation Section -->
        <div class="section">
            <h2>1. Generate Script</h2>
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
            <h2>2. Generate Voiceover</h2>
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
            <button id="generateVoiceover">Generate & Play</button>
        </div>

        <div id="voiceoverLoading" class="loading">Generating voiceover...</div>
        <div id="audioContainer" class="audio-player"></div>
        <div id="voiceoverError" class="error"></div>
    </div>

    <script>
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

                audioContainer.innerHTML = `
                    <audio controls autoplay>
                        <source src="${data.audio_url}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                `;
            } catch (error) {
                voiceoverError.textContent = 'Error: ' + error.message;
                voiceoverError.style.display = 'block';
            } finally {
                generateVoiceoverBtn.disabled = false;
                voiceoverLoading.style.display = 'none';
            }
        };
    </script>
</body>
</html>
"""

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

        # Save to temporary file and serve
        temp_path = os.path.join(app.root_path, 'temp')
        os.makedirs(temp_path, exist_ok=True)
        
        filename = f"voiceover_{abs(hash(text + voice_id))}.mp3"
        filepath = os.path.join(temp_path, filename)
        
        logger.debug(f"Saving audio to {filepath}")
        with open(filepath, 'wb') as f:
            f.write(audio_data)

        logger.info("Voiceover generated and saved successfully")
        return jsonify({
            'message': 'Voiceover generated successfully',
            'audio_url': f'/api/audio/{filename}'
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

import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
import asyncio

# Add parent directory to Python path
parent_dir = str(Path(__file__).parents[1])
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from tools.video_creator import VideoCreator, VideoGenerationConfig, ScriptConfig

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
video_creator = VideoCreator()

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_active" not in st.session_state:
        st.session_state.conversation_active = False
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if "video_config" not in st.session_state:
        st.session_state.video_config = None
    if "test_mode" not in st.session_state:
        st.session_state.test_mode = False

def get_ai_response(prompt, context=None):
    """Get response from Small Mind (Llama-3.1-8b-instant)."""
    system_message = """You are an AI Chief Marketing Officer. You help with marketing strategy, content creation, and campaign management. 
    When users upload images for video creation:
    1. Ask them about their desired video style and creative direction
    2. Ask about preferred duration (5 or 10 seconds)
    3. Ask about aspect ratio preference (16:9, 9:16, or 1:1)
    4. Help craft a descriptive prompt for the video generation
    5. Ask if they would like a script generated
    
    For complex tasks, you defer to Big Mind, but for quick strategic advice and simple queries, you handle them directly."""
    
    messages = [
        {"role": "system", "content": system_message}
    ]
    
    if context:
        messages.append({"role": "assistant", "content": context})
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant", 
            temperature=0.7,
            max_tokens=1000,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

async def generate_video(image_path: str, prompt: str, duration: str, aspect_ratio: str, script_enabled: bool = False, script_text: str = None):
    """Generate video using the VideoCreator.
    
    Args:
        image_path (str): Path to the source image.
        prompt (str): Description of the desired video.
        duration (str): Video duration in seconds ("5" or "10").
        aspect_ratio (str): Video aspect ratio ("16:9", "9:16", or "1:1").
        script_enabled (bool, optional): Whether to generate a script. Defaults to False.
        script_text (str, optional): Custom script text. Defaults to None.
    """
    config = VideoGenerationConfig(
        prompt=prompt,
        image_url=image_path,
        duration=duration,
        aspect_ratio=aspect_ratio,
        script=ScriptConfig(
            enabled=script_enabled,
            base_script=script_text
        )
    )
    return await video_creator.create_video(config)

def main():
    st.title("AI Chief Marketing Officer 🎯")
    
    # Initialize session state
    initialize_session_state()
    
    # Add image upload and testing controls in the sidebar
    with st.sidebar:
        st.header("Upload Image")
        uploaded_file = st.file_uploader("Choose an image for video creation", type=["png", "jpg", "jpeg"])
        
        # Add test mode toggle at the top level of sidebar
        st.session_state.test_mode = st.checkbox(
            "🧪 Enable Test Mode",
            value=st.session_state.test_mode,
            help="Directly test the video creator without chat interface"
        )
        
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image")
            st.session_state.uploaded_image = uploaded_file
            
            # Add video configuration options
            st.header("Video Settings")
            duration = st.selectbox("Duration (seconds)", ["5", "10"], key="duration")
            aspect_ratio = st.selectbox("Aspect Ratio", ["16:9", "9:16", "1:1"], key="aspect_ratio")
            
            # Add script options
            st.header("Script Settings")
            script_enabled = st.checkbox("Generate Script", value=False, key="script_enabled")
            script_text = None
            if script_enabled:
                script_text = st.text_area(
                    "Custom Script (optional)",
                    help="Leave empty to auto-generate script",
                    key="script_text"
                )
                if script_text and not script_text.strip():
                    script_text = None
            
            # Show test controls if test mode is enabled
            if st.session_state.test_mode:
                test_prompt = st.text_area(
                    "Test Prompt",
                    "A serene landscape transforming through seasons",
                    help="Enter a prompt to test video generation"
                )
                
                if st.button("🚀 Test Video Generation"):
                    with st.spinner("Generating video..."):
                        try:
                            # Save uploaded image temporarily
                            temp_dir = Path("temp")
                            temp_dir.mkdir(exist_ok=True)
                            image_path = temp_dir / uploaded_file.name
                            with open(image_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Generate video with test parameters
                            video_result = asyncio.run(generate_video(
                                str(image_path),
                                test_prompt,
                                duration,
                                aspect_ratio,
                                script_enabled,
                                script_text
                            ))
                            
                            # Display video result
                            if "video" in video_result and "url" in video_result["video"]:
                                st.success("✅ Video generated successfully!")
                                st.video(video_result["video"]["url"])
                                
                                # Show script if it was generated
                                if "script" in video_result:
                                    st.info("📝 Generated Script:")
                                    st.text(video_result["script"])
                            else:
                                st.error("❌ Failed to generate video")
                                st.json(video_result)  # Show raw response for debugging
                            
                            # Cleanup
                            image_path.unlink()
                        except Exception as e:
                            st.error(f"❌ Error generating video: {str(e)}")
                            st.exception(e)  # Show full traceback for debugging
            
            if "video_config" not in st.session_state or st.session_state.video_config is None:
                st.session_state.video_config = {
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                    "prompt": None,
                    "script_enabled": script_enabled,
                    "script_text": script_text
                }
    
    # Only show chat interface if not in test mode
    if not st.session_state.test_mode:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("How can I help you with marketing today?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # If image is uploaded but no video config prompt yet
                    context = None
                    if st.session_state.uploaded_image and not st.session_state.video_config["prompt"]:
                        context = "I see you've uploaded an image! Let me help you create a video from it. "
                    
                    response = get_ai_response(prompt, context)
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # If this was a video prompt response, store it
                    if st.session_state.uploaded_image and not st.session_state.video_config["prompt"]:
                        st.session_state.video_config["prompt"] = prompt
                        
                        # Generate video button
                        if st.button("Generate Video"):
                            with st.spinner("Generating video... This may take a few minutes"):
                                try:
                                    # Save uploaded image temporarily
                                    temp_dir = Path("temp")
                                    temp_dir.mkdir(exist_ok=True)
                                    image_path = temp_dir / uploaded_file.name
                                    with open(image_path, "wb") as f:
                                        f.write(uploaded_file.getbuffer())
                                    
                                    # Show progress message
                                    progress_placeholder = st.empty()
                                    progress_placeholder.info("📤 Uploading image and initializing video generation...")
                                    
                                    # Generate video
                                    video_result = asyncio.run(generate_video(
                                        str(image_path),
                                        st.session_state.video_config["prompt"],
                                        st.session_state.video_config["duration"],
                                        st.session_state.video_config["aspect_ratio"],
                                        st.session_state.video_config["script_enabled"],
                                        st.session_state.video_config["script_text"]
                                    ))
                                    
                                    # Update progress
                                    progress_placeholder.info("✨ Video generation completed!")
                                    
                                    # Display video result
                                    if "video" in video_result and "url" in video_result["video"]:
                                        st.success(f"✅ Video generated successfully!")
                                        st.video(video_result["video"]["url"])
                                        
                                        # Show script if it was generated
                                        if "script" in video_result:
                                            st.info("📝 Generated Script:")
                                            st.text(video_result["script"])
                                        
                                        # Add direct link
                                        st.markdown(f"[📥 Download Video]({video_result['video']['url']})")
                                    else:
                                        st.error("❌ Failed to generate video - Invalid response format")
                                        st.json(video_result)  # Show raw response for debugging
                                    
                                    # Cleanup
                                    image_path.unlink()
                                except Exception as e:
                                    st.error(f"❌ Error generating video: {str(e)}")
                                    st.exception(e)  # Show full traceback for debugging

if __name__ == "__main__":
    main()
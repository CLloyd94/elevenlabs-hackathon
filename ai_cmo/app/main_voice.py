import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from agents.small_mind import SmallMind
from agents.Big_Mind import BigMind
from utils.logger import PromptLogger
from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ClientTools
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Load environment variables
load_dotenv()

# Initialize agents
small_mind = SmallMind()
big_mind = BigMind()

# Initialize logger
current_dir = os.path.dirname(os.path.abspath(__file__))
logger = PromptLogger(os.path.join(current_dir, 'current_prompt.txt'))

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_active' not in st.session_state:
    st.session_state.conversation_active = False
if 'conversation' not in st.session_state:
    st.session_state.conversation = None

def process_small_mind(parameters):
    """Client tool to process Small Mind response"""
    user_message = parameters.get("message")
    small_mind_response = small_mind.process_message(user_message)
    
    # Log Small Mind's response
    logger.log_interaction("SMALL_MIND", small_mind_response)
    
    # If Big Mind needs to be activated, do it in background
    if small_mind_response["activate_big_mind"]:
        thread = threading.Thread(
            target=execute_big_mind_task,
            args=(small_mind_response["action"], user_message)
        )
        thread.start()
    
    # Return response for voice output
    return {
        "response": small_mind_response["message_to_user"],
        "requires_action": small_mind_response["activate_big_mind"],
        "action_type": small_mind_response["action"]
    }

def execute_big_mind_task(action: str, user_message: str):
    """Execute Big Mind task in background"""
    big_mind_response = big_mind.process_request(user_message)
    logger.log_interaction("BIG_MIND", big_mind_response)
    print(f"Big Mind executing task: {action}")

def update_chat_history(role, content):
    """Update chat history in a thread-safe way"""
    if role and content:
        st.session_state.messages.append({"role": role, "content": content})

def log_agent_response(response):
    """Callback for agent responses"""
    if response:
        logger.log_interaction("AGENT", response)
        st.rerun()

def log_user_transcript(transcript):
    """Callback for user transcripts"""
    if transcript:
        logger.log_interaction("USER", transcript)
        st.rerun()

def main():
    st.title("AI Chief Marketing Officer 🎯 - Voice Edition")
    
    # Setup client tools
    client_tools = ClientTools()
    client_tools.register("processSmallMind", process_small_mind)
    
    # Start/Stop conversation button
    if st.button("Toggle Voice Conversation"):
        if not st.session_state.conversation_active:
            try:
                st.session_state.conversation = Conversation(
                    client=ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY")),
                    agent_id=os.getenv("ELEVENLABS_AGENT_ID"),
                    client_tools=client_tools,
                    requires_auth=True,
                    audio_interface=DefaultAudioInterface()
                )
                st.session_state.conversation.start_session()
                st.session_state.conversation_active = True
                st.write("Voice conversation active - speak to interact")
            except Exception as e:
                st.error(f"Error starting conversation: {e}")
        else:
            try:
                if st.session_state.conversation:
                    st.session_state.conversation.end_session()
                st.session_state.conversation_active = False
                st.session_state.conversation = None
                st.write("Voice conversation ended")
            except Exception as e:
                st.error(f"Error ending conversation: {e}")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Display conversation status
    if st.session_state.conversation_active:
        status_placeholder = st.empty()
        status_placeholder.write("🎤 Listening...")
    else:
        st.write("🔇 Voice interaction paused")

if __name__ == "__main__":
    main()
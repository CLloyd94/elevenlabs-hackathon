import streamlit as st
import sys
import os
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from agents.small_mind import SmallMind
from agents.Big_Mind import BigMind

# Load environment variables
load_dotenv()

# Initialize agents
small_mind = SmallMind()
big_mind = BigMind()

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_active" not in st.session_state:
        st.session_state.conversation_active = False

def execute_big_mind_task(action: str, user_message: str):
    """Execute Big Mind task in background"""
    big_mind_response = big_mind.process_request(user_message)
    # Here you would handle the actual tool execution
    # and potentially update status.txt or trigger notifications
    print(f"Big Mind executing task: {action}")  # For debugging

def process_request(user_message: str):
    """Process user request through Small Mind and potentially trigger Big Mind"""
    # Get Small Mind's response
    small_mind_response = small_mind.process_message(user_message)
    
    # If Big Mind needs to be activated, do it in background
    if small_mind_response["activate_big_mind"]:
        thread = threading.Thread(
            target=execute_big_mind_task,
            args=(small_mind_response["action"], user_message)
        )
        thread.start()
    
    # Return Small Mind's message to user
    return small_mind_response["message_to_user"]

def main():
    st.title("AI Chief Marketing Officer 🎯")
    
    # Initialize session state
    initialize_session_state()
    
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
        
        # Get AI response (only from Small Mind)
        with st.chat_message("assistant"):
            response = process_request(prompt)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
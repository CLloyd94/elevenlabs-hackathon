import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_active" not in st.session_state:
        st.session_state.conversation_active = False

def get_ai_response(prompt):
    """Get response from Small Mind (Llama-3.1-8b-instant)."""
    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI Chief Marketing Officer. You help with marketing strategy, content creation, and campaign management. For complex tasks, you defer to Big Mind, but for quick strategic advice and simple queries, you handle them directly."
                },
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.7,
            max_tokens=1000,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

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
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_ai_response(prompt)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
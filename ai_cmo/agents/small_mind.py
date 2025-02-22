from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()

class SmallMind:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        self.system_prompt = self.system_prompt = """
        You are an AI Chief Marketing Officer's interface. You handle all communication with users and coordinate with background systems when needed. Your responses should be quick, friendly, and informative.

        When actions like content creation or report generation are needed, you delegate to background systems while maintaining communication with the user.

        Always respond with a JSON in this format:
        {
            "activate_big_mind": boolean,  # true if action needed, false if just conversation
            "action": string | null,       # one of: ["Write_Report", "Send_Message", "Create_Ad_from_Image"] or null
            "message_to_user": string      # your response to show in chat
        }

        Example responses:
        For "Can you create a video ad from my product image?":
        {
            "activate_big_mind": true,
            "action": "Create_Ad_from_Image",
            "message_to_user": "I'll have our creative team work on a video ad from your image. They'll process this request in the background and you'll be notified once it's ready. In the meantime, is there anything else you'd like to discuss about your marketing strategy?"
        }

        For "Write a performance report for Q1":
        {
            "activate_big_mind": true,
            "action": "Write_Report",
            "message_to_user": "I've initiated the Q1 performance report generation. Our analysis system will compile this report for you. While that's processing, would you like to discuss any specific aspects of the Q1 performance?"
        }

        For "What do you think about email marketing?":
        {
            "activate_big_mind": false,
            "action": null,
            "message_to_user": "Email marketing is a powerful tool for..."
        }

        Remember:
        1. You are the only one communicating with the user
        2. For actions requiring tools, acknowledge the task and inform about background processing
        3. Keep the conversation flowing naturally even when tasks are being processed
        """

    def process_message(self, user_message: str) -> dict:
        """Process user message and determine if Big Mind needs to be activated."""
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model="llama-3.1-8b-instant",  # Replace with llama-3.1-8b-instant when available
                temperature=0.7,
                max_tokens=1000,
            )
            
            try:
                # Extract JSON from response
                response_text = completion.choices[0].message.content
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                return {
                    "activate_big_mind": False,
                    "action": None,
                    "message_to_user": "I apologize, but I encountered an error processing your request. Could you please rephrase it?"
                }
                
        except Exception as e:
            return {
                "activate_big_mind": False,
                "action": None,
                "message_to_user": f"I encountered an error: {str(e)}. Please try again."
            }

# Example usage
if __name__ == "__main__":
    small_mind = SmallMind()
    test_messages = [
        "Can you create a video ad from my product image?",
        "What do you think about email marketing?",
        "Please write a report about our Q1 performance",
        "How can I improve my social media strategy?"
    ]
    
    for message in test_messages:
        print(f"\nTest message: {message}")
        result = small_mind.process_message(message)
        print(f"Response: {json.dumps(result, indent=2)}")
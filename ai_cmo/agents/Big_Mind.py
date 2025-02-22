from anthropic import Anthropic
import json
from typing import Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class BigMind:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.available_tools = {
            "Write_Report": {"description": "Creates detailed marketing reports"},
            "Send_Message": {"description": "Sends message via telegram to user"},
            "Create_Ad_from_Image": {"description": "Creates video advertisements from input images + video description"}
        }
        
        self.system_prompt = """You are an AI Chief Marketing Officer with access to several tools. Your role is to analyze user requests and determine if and which tools should be used to fulfill them.

Available tools:
- Write_Report: For creating detailed marketing reports
- Send_Message: For sending emails or messages
- Create_Ad_from_Image: For creating video ads from images

When you receive a message, you should:
1. Analyze if the request requires using any of the available tools
2. Return a JSON response in the following format:
{
    "requires_tool": true/false,
    "tool_name": "name_of_tool_or_null",
    "reason": "explanation of your decision",
    "parameters": {...} # any parameters needed for the tool
}

Example user messages and responses:
"Can you create a video ad from this product image?" 
→ {"requires_tool": true, "tool_name": "Create_Ad_from_Image", "reason": "User explicitly requested video ad creation", "parameters": {"image_path": "path_to_image", “video_description”: “user_description."}}

"What do you think about our marketing strategy?"
→ {"requires_tool": false, "tool_name": null, "reason": "This is a general discussion query that doesn't require tool usage", "parameters": {}}

Remember: Only suggest using a tool when it's clearly needed to fulfill the user's request."""

    def process_request(self, user_message: str) -> Dict:
        """Process a user request and determine if tool usage is needed."""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1000,
                temperature=0,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract and parse JSON from response
            try:
                # Find JSON in the response content
                response_text = response.content[0].text
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError) as e:
                return {
                    "requires_tool": False,
                    "tool_name": None,
                    "reason": f"Error parsing response: {str(e)}",
                    "parameters": {}
                }
                
        except Exception as e:
            return {
                "requires_tool": False,
                "tool_name": None,
                "reason": f"Error processing request: {str(e)}",
                "parameters": {}
            }

    def validate_tool_name(self, tool_name: Optional[str]) -> bool:
        """Validate if a tool name exists in available tools."""
        if tool_name is None:
            return True
        return tool_name in self.available_tools

# Example usage:
if __name__ == "__main__":
    big_mind = BigMind()
    
    # Test cases
    test_messages = [
        "Can you create a video ad from this product image?",
        # "What do you think about our marketing strategy?",
        # "Please send an email to the team about the new campaign.",
        # "Write a report about our Q1 performance."
    ]
    
    for message in test_messages:
        print(f"\nTest message: {message}")
        result = big_mind.process_request(message)
        print(f"Response: {json.dumps(result, indent=2)}")
import json
import os
import time
import urllib.request
import subprocess
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI

# Import the get_campaign_insight function from your saved file
from tools.campaign_insight import get_campaign_insight

load_dotenv()

class BigMind:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Telegram configuration
        self.telegram_bot_token = os.getenv("BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TARGET_CHAT_ID")
        self.telegram_username = os.getenv("TARGET_USER_NAME")
        # Meta Ads configuration
        self.ad_account_id = os.getenv("AD_ACCOUNT_ID")
        self.meta_access_token = os.getenv("ACCESS_TOKEN")
        
        self.available_tools = {
            "Write_Report": {
                "description": "Creates detailed marketing reports",
                "parameters": ["campaign_data"]
            },
            "Send_Message": {
                "description": "Sends message via telegram to user",
                "parameters": ["message"]
            },
            "Create_Ad_from_Image": {
                "description": "Creates video advertisements from input images + video description"
            },
            "Post_Video_Ad": {
                "description": "Posts a video to Meta Ads campaign",
                "parameters": ["remote_file_path", "title", "description"]
            },
            "Fetch_Campaign_Insight": {
                "description": "Fetches campaign insight data from Facebook API for a given date range",
                "parameters": ["start_date", "end_date"]
            }
        }
        
        self.system_prompt = """You are an AI Chief Marketing Officer with access to several tools. Your role is to analyze user requests and determine if and which tools should be used to fulfill them.

Available tools:
- Write_Report: For creating detailed marketing reports (requires campaign_data parameter)
- Send_Message: For sending messages via Telegram
- Create_Ad_from_Image: For creating video ads from images
- Post_Video_Ad: For uploading videos to Meta Ads campaigns
- Fetch_Campaign_Insight: For fetching campaign insights from Facebook API

When you receive a message, you should:
1. Analyze if the request requires using any of the available tools
2. Return a JSON response in the following format:
{
    "requires_tool": true/false,
    "tool_name": "name_of_tool_or_null",
    "reason": "explanation of your decision",
    "parameters": {...} # any parameters needed for the tool
}

For Write_Report tool, include a "campaign_data" parameter with the path to the campaign data.
For Send_Message tool, include a "message" parameter with the text to be sent.

Example user messages and responses:
"Can you create a video ad from this product image?" 
→ {"requires_tool": true, "tool_name": "Create_Ad_from_Image", "reason": "User explicitly requested video ad creation", "parameters": {"image_path": "path_to_image", "video_description": "user_description"}}

"Generate a performance report for our campaign"
→ {"requires_tool": true, "tool_name": "Write_Report", "reason": "User requested performance report generation", "parameters": {"campaign_data": "campaign-data.json"}}

"Send a message to notify the team about the new campaign launch"
→ {"requires_tool": true, "tool_name": "Send_Message", "reason": "User requested to send a notification", "parameters": {"message": "New campaign launch notification: The marketing campaign is now live!"}}

"Upload our new product video to the Meta Ads campaign"
→ {"requires_tool": true, "tool_name": "Post_Video_Ad", "reason": "User requested to upload a video to Meta Ads Campaign", "parameters": {"remote_file_path": "https://example.com/video.mp4", "title": "New Product Launch", "description": "Exciting new product features"}}

"What do you think about our marketing strategy?"
→ {"requires_tool": false, "tool_name": null, "reason": "This is a general discussion query that doesn't require tool usage", "parameters": {}}

Remember: Only suggest using a tool when it's clearly needed to fulfill the user's request."""
    
def generate_performance_report(self, campaign_data: dict) -> dict:
    try:
        data_context = json.dumps(campaign_data, indent=2)
        
        system_prompt = """You are an expert marketing analyst tasked with creating detailed performance reports for Meta Ad campaigns.
        Your reports should be professional, data-driven, and ready to be sent to clients.
        
        Structure your report with the following sections:
        1. Executive Summary
        2. Campaign Performance Overview
        3. Key Metrics Analysis
        4. Week-over-Week Performance
        5. Areas for Optimization
        6. Recommendations"""
        
        user_prompt = f"""Please analyze this Meta Ads campaign performance data and generate a comprehensive report:

        Campaign Data:
        {data_context}

        Please provide a detailed analysis that highlights:
        - Overall performance trends
        - Key metrics and their changes over time
        - Notable improvements or areas of concern
        - Specific recommendations for optimization"""
        
        response = self.openai_client.chat.completions.create(
            model="o3-mini-2025-01-31",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        report_content = response.choices[0].message.content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_with_timestamp = f"Report Generated: {timestamp}\n\n{report_content}"
        
        return {
            "success": True,
            "report": report_with_timestamp
        }
        
    except Exception as e:
        return {
            "success": False,
            "details": f"Error generating report: {str(e)}"
        }


    def download_file(self, remote_url: str, file_name: str) -> bool:
        """Downloads a file from a remote repository and stores it locally."""
        try:
            urllib.request.urlretrieve(remote_url, file_name)
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False

    def upload_video_ad(self, remote_file_path: str, title: str, description: str) -> dict:
        """Uploads a video to Meta's Marketing API."""
        try:
            file_name = f"temp_video_{int(time.time())}.mp4"
            local_file_path = os.path.join(".", file_name)
            
            if not self.download_file(remote_file_path, local_file_path):
                return {
                    "success": False,
                    "details": "Failed to download video file"
                }
            
            url = f"https://graph.facebook.com/v20.0/act_{self.ad_account_id}/advideos"
            headers = {"Authorization": f"Bearer {self.meta_access_token}"}
            
            with open(local_file_path, "rb") as video_file:
                files = {"source": video_file}
                data = {"title": title, "description": description}
                response = requests.post(url, headers=headers, files=files, data=data)
            
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
            
            result = response.json()
            if 'id' in result:
                return {
                    "success": True,
                    "details": f"Video uploaded successfully! Video ID: {result['id']}"
                }
            else:
                return {
                    "success": False,
                    "details": f"Upload failed: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "details": f"Error uploading video: {str(e)}"
            }

    def send_telegram_message(self, message: str) -> dict:
        """Sends a message to a Telegram user via the bot."""
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload)
            result = response.json()
            return {
                "success": result.get('ok', False),
                "details": result
            }
        except Exception as e:
            return {
                "success": False,
                "details": str(e)
            }

    def fetch_campaign_insight(self, start_date: str, end_date: str) -> dict:
        """Fetches campaign insight data using the integrated get_campaign_insight function."""
        try:
            insight_data = get_campaign_insight(self.ad_account_id, self.meta_access_token, start_date, end_date)
            return {
                "success": True,
                "data": insight_data
            }
        except Exception as e:
            return {
                "success": False,
                "details": f"Error fetching campaign insight: {str(e)}"
            }

    def execute_tool(self, tool_name: str, parameters: dict) -> dict:
        """Execute the specified tool with given parameters."""
        if tool_name == "Write_Report":
            if "campaign_data" not in parameters:
                return {
                    "success": False,
                    "details": "Campaign data parameter is required for Write_Report tool"
                }
            return self.generate_performance_report(parameters["campaign_data"])
            
        elif tool_name == "Send_Message":
            if "message" not in parameters:
                return {
                    "success": False,
                    "details": "Message parameter is required for Send_Message tool"
                }
            return self.send_telegram_message(parameters["message"])
        
        elif tool_name == "Post_Video_Ad":
            required_params = ["remote_file_path", "title", "description"]
            if not all(param in parameters for param in required_params):
                return {
                    "success": False,
                    "details": f"Missing required parameters. Need: {required_params}"
                }
            return self.upload_video_ad(
                parameters["remote_file_path"],
                parameters["title"],
                parameters["description"]
            )
        
        elif tool_name == "Fetch_Campaign_Insight":
            required_params = ["start_date", "end_date"]
            if not all(param in parameters for param in required_params):
                return {
                    "success": False,
                    "details": f"Missing required parameters for Fetch_Campaign_Insight. Need: {required_params}"
                }
            return self.fetch_campaign_insight(parameters["start_date"], parameters["end_date"])
        
        return {
            "success": False,
            "details": f"Tool {tool_name} not implemented yet"
        }

    def process_request(self, user_message: str) -> dict:
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
            
            try:
                response_text = response.content[0].text
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                decision = json.loads(json_str)
                
                if decision["requires_tool"] and decision["tool_name"]:
                    tool_result = self.execute_tool(
                        decision["tool_name"],
                        decision["parameters"]
                    )
                    decision["tool_execution_result"] = tool_result
                
                return decision
                
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

    def validate_tool_name(self, tool_name: str) -> bool:
        """Validate if a tool name exists in available tools."""
        if tool_name is None:
            return True
        return tool_name in self.available_tools

# Example usage:
if __name__ == "__main__":
    big_mind = BigMind()
    
    # Test messages including a request for campaign insights
    test_messages = [
        "Can you create a video ad from this product image?",
        "Send a message to the team about our new campaign launch",
        "What do you think about our marketing strategy?",
        "Please write a report about our Q1 performance.",
        "Upload this video to our Meta Ads campaign: https://example.com/video.mp4",
        "Fetch campaign insights from 2024-01-01 to 2024-03-31"
    ]
    
    for message in test_messages:
        print(f"\nTest message: {message}")
        result = big_mind.process_request(message)
        print(f"Response: {json.dumps(result, indent=2)}")

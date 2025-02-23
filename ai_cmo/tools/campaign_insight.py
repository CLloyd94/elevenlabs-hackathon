import requests
import pandas as pd
import json
import os

# CAMPAIGN_AD_ACCOUNT_ID = os.getenv("CAMPAIGN_AD_ACCOUNT_ID")
# ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
# print(get_campaign_insight(CAMPAIGN_AD_ACCOUNT_ID, ACCESS_TOKEN, "2024-01-01", "2024-03-31"))

def get_campaign_insight(ad_account_id, access_token, start_date: str, end_date: str) -> pd.DataFrame:
    """Get campaign insight from Facebook API.
    Args: start_date, end_date: formatted as "YYYY-MM-DD".
    """
    time_range = json.dumps({
        "since": start_date,
        "until": end_date
    })
    params = {
        "fields": "campaign_id,campaign_name,impressions,clicks,spend",
        "level": "campaign",
        "time_range": time_range,
        "access_token": access_token
    }
    try:
        url = f"https://graph.facebook.com/v19.0/act_{ad_account_id}/insights"
        res = requests.get(url, params=params)
        return res.json()
    except Exception as e:
        print(f"Error: {e}")

def process_campaign_data_to_json(data):
    """Processes campaign data to calculate click thru rate and cost per click."""
    if not data:
        return "[]"
    df = pd.DataFrame(data)

    # Ensure required columns exist to prevent KeyError
    required_cols = {'clicks', 'impressions', 'spend'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_cols - set(df.columns)}")

    df = pd.DataFrame(data)
    df['click_thru_rate'] = (df['clicks'] / df['impressions']) * 100
    df['cost_per_click'] = df['spend'] / df['clicks']
    res = df.to_json(orient='records')
    return res
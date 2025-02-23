import requests
import pandas as pd
import json
import os

CAMPAIGN_AD_ACCOUNT_ID="312327524514512"
ACCESS_TOKEN = "EAASO6K2Xl0MBO8ZBXxGF1Rq1ZCYwyiMQZBbwl7F5X6HvGZCq0H6cgvCOdF0QPbrD9fjlHR5TvH5cAAevfnXFzJ0BDhj2GIQEFOdyV6XFCZADz5zGFMGEyKH6EOZBa1Q3FmIrYsZCNEXQl87yYd6MjZBoDwAGLJJWwlMOSkac1X02hHmQq0znwhCcchR12N3nB02K"

def get_campaign_insight() -> pd.DataFrame:
    """Get campaign insight from Facebook API.
    Args: start_date, end_date: formatted as "YYYY-MM-DD".
    """
    # time_range = json.dumps({
    #     "since": start_date,
    #     "until": end_date
    # })
    # params = {
    #     "fields": "campaign_id,campaign_name,impressions,clicks,spend",
    #     "level": "campaign",
    #     "time_range": time_range,
    #     "access_token": access_token
    # }
    # try:
    #     url = f"https://graph.facebook.com/v19.0/act_{ad_account_id}/insights"
    #     res = requests.get(url, params=params)
    #     return res.json()
    # except Exception as e:
    #     print(f"Error: {e}")
    json_data = '''[
        {"Week":"2025-02-20 - 2025-02-21","Reach":129351,"Impressions":212067,"Clicks (all)":1914,"Amount spent (GBP)":2214.25,"Result Type":"Website leads","Results":74,"Cost per result":29.9222973,"Video plays":59320,"Video plays at 25%":9825,"CTR (all)":0.90254495,"Reporting starts":"2025-02-20","Reporting ends":"2025-02-21"},
        {"Week":"2025-02-13 - 2025-02-19","Reach":146941,"Impressions":317377,"Clicks (all)":2768,"Amount spent (GBP)":3622.17,"Result Type":"Website leads","Results":177,"Cost per result":20.46423729,"Video plays":133882,"Video plays at 25%":22566,"CTR (all)":0.8721489,"Reporting starts":"2025-02-13","Reporting ends":"2025-02-19"},
        {"Week":"2025-02-06 - 2025-02-12","Reach":213710,"Impressions":461314,"Clicks (all)":3470,"Amount spent (GBP)":5070.8,"Result Type":"Website leads","Results":214,"Cost per result":23.6953271,"Video plays":135483,"Video plays at 25%":23008,"CTR (all)":0.75219915,"Reporting starts":"2025-02-06","Reporting ends":"2025-02-12"},
        {"Week":"2025-01-30 - 2025-02-05","Reach":194295,"Impressions":405852,"Clicks (all)":3163,"Amount spent (GBP)":3892.59,"Result Type":"Website leads","Results":196,"Cost per result":19.86015306,"Video plays":206476,"Video plays at 25%":33479,"CTR (all)":0.77934814,"Reporting starts":"2025-01-30","Reporting ends":"2025-02-05"},
        {"Week":"2025-01-23 - 2025-01-29","Reach":58819,"Impressions":97745,"Clicks (all)":874,"Amount spent (GBP)":948.77,"Result Type":"Website leads","Results":62,"Cost per result":15.30274194,"Video plays":38600,"Video plays at 25%":5772,"CTR (all)":0.89416338,"Reporting starts":"2025-01-23","Reporting ends":"2025-01-29"}
    ]'''
    data = json.loads(json_data)
    return data

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
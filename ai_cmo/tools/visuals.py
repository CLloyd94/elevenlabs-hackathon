import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

def get_campaign_data() -> pd.DataFrame:
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
    return pd.DataFrame(data)

def process_campaign_data():
    """Processes campaign data to calculate click_thru_rate and cost_per_click."""
    data = {
        "campaign_id": [
            23856815604440271, 23857760442610271, 23858000000000001,
            23858000000000002, 23858000000000003
        ],
        "campaign_name": [
            "02-20 - 02-21", "02-13 - 02-19", "02-06 - 02-12",
            "01-30 - 02-05", "01-23 - 01-29"
        ],
        "impressions": [4702116, 1878485, 3500000, 4200000, 3100000],
        "clicks": [37832, 16340, 25000, 4000, 3000],
        "spend": [58195.53, 21568.48, 40000.00, 50000.00, 30000.00],
        "date_start": ["2024-01-01", "2024-01-01", "2024-02-01", "2024-02-15", "2024-03-01"],
        "date_stop": ["2024-03-31", "2024-03-31", "2024-04-30", "2024-04-15", "2024-05-01"]
    }
    df = pd.DataFrame(data)
    df['click_thru_rate'] = (df['clicks'] / df['impressions']) * 100
    df['cost_per_click'] = df['spend'] / df['clicks']
    return df

def plot_campaign_metrics(df):
    """Generates a visuals for comparing metrics."""
    # dfs
    df_sorted_ctr = df.sort_values('click_thru_rate', ascending=False)
    df_sorted_cpc = df.sort_values('cost_per_click', ascending=False)

    # plots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Click Through Rate (%)", "Conversion Rate (%)")
    )
    fig.add_trace(
        go.Bar(
            x=df_sorted_ctr['campaign_name'],
            y=df_sorted_ctr['click_thru_rate'],
            marker_color='lightsalmon',
            name="Click through rate"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(
            x=df_sorted_cpc['campaign_name'],
            y=df_sorted_cpc['cost_per_click'],
            marker_color='lightblue',
            name="Cost per click"
        ),
        row=1, col=2
    )
    fig.update_layout(
        title_text="Campaign Metrics Comparison",
        showlegend=False,
        width=800,
        height=300
    )
    return fig

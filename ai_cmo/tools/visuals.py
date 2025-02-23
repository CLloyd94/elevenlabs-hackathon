import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def process_campaign_data():
    """Processes campaign data to calculate click_thru_rate and cost_per_click."""
    data = {
        "campaign_id": [
            23856815604440271, 23857760442610271, 23858000000000001,
            23858000000000002, 23858000000000003
        ],
        "campaign_name": [
            "Meta Leads 01", "Lookalike Campaign 01", "Brand Awareness 01",
            "Conversion Campaign 01", "Retargeting Campaign 01"
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
        subplot_titles=("Click Through Rate (%)", "CPC (Cost Per Click)")
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

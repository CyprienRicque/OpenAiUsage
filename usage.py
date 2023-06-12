import logging
from datetime import datetime, timedelta
import os

import pandas as pd
import requests
from dotenv import load_dotenv
import altair as alt

import streamlit as st
from matplotlib import pyplot as plt

# large streamlit layout
st.set_page_config(
    page_title="Openai usage",
    layout="wide",
    page_icon="💸",
    initial_sidebar_state="auto",
)

# load_dotenv("./credentials.env")

today = datetime.now().date()

this_month = (today.replace(day=1), today + timedelta(days=1))
all_months = (today.replace(day=1, month=5), today + timedelta(days=1))

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = "https://api.openai.com/v1/organizations/"


def fetch_openapi_usage_statistics(start_date, end_date):
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    API_USAGE_URL = f"https://api.openai.com/dashboard/billing/usage?end_date={end_date_str}&start_date={start_date_str}"

    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = requests.get(API_USAGE_URL, headers=headers)

    if response.status_code == 200:
        raw_usage_value = response.json()["total_usage"]
        total_usage_d = round(raw_usage_value / 100, 2)

        # Flatten the data
        data = []
        for entry in response.json()['daily_costs']:
            timestamp = entry['timestamp']
            for item in entry['line_items']:
                item['timestamp'] = timestamp
                data.append(item)

        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df.cost = df.cost.astype(float) / 100
        df.sort_values(by=['timestamp'], ascending=False, inplace=True)

        return df, total_usage_d
    else:
        st.error(
            f"Error fetching OpenAPI usage statistics: {response.status_code} - {response.text}"
        )
        st.stop()
        logging.error(
            f"Error fetching OpenAPI usage statistics: {response.status_code} - {response.text}"
        )
        return None, None

df_total, total_usage_d = fetch_openapi_usage_statistics(all_months[0], all_months[1])
df_this_month, this_month_usage_d = fetch_openapi_usage_statistics(this_month[0], this_month[1])

month, total = st.columns(2)

month.metric("Total usage cost ($)", total_usage_d)
total.metric("This month usage cost ($)", this_month_usage_d)

st.divider()

chart_daily = alt.Chart(df_this_month).mark_line().encode(
    x='datetime:T',
    y=alt.Y('cost:Q', axis=alt.Axis(format='$f')),
    color='name:N',
    tooltip=['date:T', 'cost:Q', 'name:N']
).properties(
    width=1200,
    height=400,
    title="Cost per model over time (This month)"
)

st.altair_chart(chart_daily, use_container_width=True)

# Plotting monthly usage

chart_monthly = alt.Chart(df_total).mark_line().encode(
    x='datetime:T',
    y=alt.Y('cost:Q', axis=alt.Axis(format='$f')),
    color='name:N',
    tooltip=['month_year:T', 'cost:Q', 'name:N']
).properties(
    width=800,
    height=400,
    title="Cost per model over time (Total)"
)

st.altair_chart(chart_monthly, use_container_width=True)


update = st.button("Update usage")
if update:
    st.balloons()

st.dataframe(df_total[df_total['cost'] > 0])

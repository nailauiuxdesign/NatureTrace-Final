# utils/data_utils.py
import snowflake.connector
import pandas as pd
import plotly.express as px
import streamlit as st

def get_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake_user"],
        password=st.secrets["snowflake_password"],
        account=st.secrets["snowflake_account"],
        warehouse=st.secrets["snowflake_warehouse"],
        database=st.secrets["snowflake_database"],
        schema=st.secrets["snowflake_schema"]
    )

def save_to_snowflake(image_id, animal_data):
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()

        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS animals (
                image_id STRING,
                name STRING,
                description STRING,
                facts STRING
            )
        """)

        # Insert record
        cur.execute("""
            INSERT INTO animals (image_id, name, description, facts)
            VALUES (%s, %s, %s, %s)
        """, (image_id, animal_data["name"], animal_data["description"], animal_data["facts"]))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Failed to save to Snowflake: {str(e)}")

def fetch_dashboard_data():
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()

        # Fetch data
        cur.execute("SELECT name, COUNT(*) AS count FROM animals GROUP BY name")
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=["Animal", "Count"])

        charts = []
        if not df.empty:
            bar = px.bar(df, x="Animal", y="Count", title="Animal Frequency")
            pie = px.pie(df, names="Animal", values="Count", title="Animal Distribution")
            charts.extend([bar, pie])

        cur.close()
        conn.close()
        return charts
    except Exception as e:
        st.error(f"Failed to fetch dashboard data: {str(e)}")
        return []

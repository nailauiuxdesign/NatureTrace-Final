# utils/data_utils.py

import snowflake.connector
import pandas as pd
from datetime import datetime
import streamlit as st


def get_snowflake_connection():
    try:
        conn = snowflake.connector.connect(
            user=st.secrets["snowflake_user"],
            password=st.secrets["snowflake_password"],
            account=st.secrets["snowflake_account"],
            warehouse=st.secrets["snowflake_warehouse"],
            database=st.secrets["snowflake_database"],
            schema=st.secrets["snowflake_schema"]
        )
        return conn
    except Exception as e:
        st.error("Snowflake not configured. Please check secrets.toml")
        return None

def save_to_snowflake(filename, name, description, facts, sound_url):
    conn = get_snowflake_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO animal_insight_data (filename, name, description, facts, sound_url)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT(filename) DO NOTHING
        """, (filename, name, description, facts, sound_url))
        cursor.close()
    except Exception as e:
        st.error(f"Error inserting into Snowflake: {e}")
    finally:
        conn.close()

def fetch_dashboard_data():
    conn = get_snowflake_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql("SELECT * FROM animal_insight_data ORDER BY timestamp DESC", conn)
        return df
    except Exception as e:
        st.error(f"Error fetching data from Snowflake: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# utils/data_utils.py
import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

# Setup Snowflake connection
@st.cache_resource
def get_snowflake_connection():
    conn = snowflake.connector.connect(
        account=st.secrets["snowflake_account"],
        user=st.secrets["snowflake_user"],
        password=st.secrets["snowflake_password"],
        warehouse=st.secrets["snowflake_warehouse"],
        database=st.secrets["snowflake_database"],
        schema=st.secrets["snowflake_schema"]
    )
    return conn

def save_to_snowflake(filename, data):
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    insert_query = f"""
    INSERT INTO animal_insight_data (filename, name, description, facts, sound_url)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (filename) DO NOTHING
    """

    try:
        cursor.execute(insert_query, (
            filename,
            data["name"],
            data["description"],
            data["facts"],
            data["sound"]
        ))
        conn.commit()
    except Exception as e:
        print("Snowflake insert error:", e)
    finally:
        cursor.close()
        conn.close()

def fetch_dashboard_data():
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM animal_insight_data")
        df = pd.DataFrame(cursor.fetchall(), columns=["name"])

        if df.empty:
            return []

        name_counts = df.value_counts("name").reset_index()
        name_counts.columns = ["name", "count"]

        fig = px.bar(name_counts, x="name", y="count", title="Animal Occurrences")
        return [fig]

    except Exception as e:
        print("Dashboard fetch error:", e)
        return []
    finally:
        cursor.close()
        conn.close()

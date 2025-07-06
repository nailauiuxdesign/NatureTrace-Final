# utils/data_utils.py

import snowflake.connector
import pandas as pd
from datetime import datetime
import streamlit as st
import logging

# Enable detailed logging for Snowflake connections
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_snowflake_connection():
    try:
        # Connect with FLORA0122 using ANIMAL_APP_ROLE
        conn = snowflake.connector.connect(
            user=st.secrets["snowflake_user"],
            password=st.secrets["snowflake_password"],
            account=st.secrets["snowflake_account"],
            warehouse=st.secrets["snowflake_warehouse"],
            role=st.secrets["snowflake_role"],
            autocommit=True
        )
        
        logger.info("Successfully connected to Snowflake")
        
        # Explicitly set the database and schema context
        cursor = conn.cursor()
        cursor.execute(f"USE DATABASE {st.secrets['snowflake_database']}")
        cursor.execute(f"USE SCHEMA {st.secrets['snowflake_schema']}")
        cursor.close()
        
        return conn
    except KeyError as e:
        st.error(f"Missing Snowflake configuration key: {e}. Please check secrets.toml")
        logger.error(f"Missing configuration: {e}")
        return None
    except snowflake.connector.errors.DatabaseError as e:
        st.error(f"Snowflake database error: {e}")
        logger.error(f"Database error: {e}")
        return None
    except Exception as e:
        st.error(f"Snowflake connection failed: {e}")
        logger.error(f"Connection failed: {e}")
        return None


def create_table_if_not_exists():
    """Create the animal_insight_data table if it doesn't exist"""
    conn = get_snowflake_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        # Try to create table with simpler approach
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animal_insight_data (
                id INTEGER AUTOINCREMENT PRIMARY KEY,
                filename VARCHAR(255) UNIQUE,
                name VARCHAR(255),
                description TEXT,
                facts TEXT,
                sound_url VARCHAR(500),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        cursor.close()
        return True
    except Exception as e:
        # If table creation fails, just log and continue - table might already exist
        print(f"Note: Table creation attempt: {e}")
        return True  # Return True to continue with the app
    finally:
        conn.close()

def save_to_snowflake(filename, name, description, facts, sound_url):
    # Ensure table exists first
    if not create_table_if_not_exists():
        return
    
    conn = get_snowflake_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        # Use MERGE for better duplicate handling in Snowflake
        # Try simple INSERT with ON CONFLICT handling
        cursor.execute("""
            INSERT INTO animal_insight_data (filename, name, description, facts, sound_url)
            VALUES (%s, %s, %s, %s, %s)
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
        # First try to query the table
        df = pd.read_sql("SELECT * FROM animal_insight_data ORDER BY timestamp DESC", conn)
        return df
    except Exception as e:
        # If table doesn't exist, try to create it
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE animal_insight_data (
                    id INTEGER AUTOINCREMENT PRIMARY KEY,
                    filename VARCHAR(255) UNIQUE,
                    name VARCHAR(255),
                    description TEXT,
                    facts TEXT,
                    sound_url VARCHAR(500),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
                )
            """)
            cursor.close()
            # Try querying again after creating table
            df = pd.read_sql("SELECT * FROM animal_insight_data ORDER BY timestamp DESC", conn)
            return df
        except Exception as create_error:
            st.error(f"Table doesn't exist and cannot be created. Please contact your Snowflake administrator to create the 'animal_insight_data' table in the ANIMAL_DB.INSIGHTS schema.")
            return pd.DataFrame()
    finally:
        conn.close()

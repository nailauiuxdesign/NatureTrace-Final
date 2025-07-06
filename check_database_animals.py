# check_database_animals.py
import streamlit as st
from utils.data_utils import fetch_dashboard_data

def main():
    st.title("🔍 Database Animals Check")
    
    # Fetch current data
    df = fetch_dashboard_data()
    
    if df.empty:
        st.warning("No animals found in database")
        return
    
    st.success(f"Found {len(df)} records in database:")
    
    # Show column names first
    st.write("**Database columns:**")
    st.write(list(df.columns))
    
    # Show unique animals if name column exists
    if 'name' in df.columns:
        unique_animals = df['name'].unique()
        st.write("**Animals in database:**")
        for animal in unique_animals:
            st.write(f"- {animal}")
    elif 'NAME' in df.columns:
        unique_animals = df['NAME'].unique()
        st.write("**Animals in database:**")
        for animal in unique_animals:
            st.write(f"- {animal}")
    
    # Show categories if available
    for col in ['category', 'CATEGORY']:
        if col in df.columns:
            categories = df[col].dropna().unique()
            if len(categories) > 0:
                st.write("**Categories:**")
                for category in categories:
                    st.write(f"- {category}")
            break
    
    # Show full dataframe
    st.subheader("Full Database Contents:")
    st.dataframe(df)

if __name__ == "__main__":
    main()

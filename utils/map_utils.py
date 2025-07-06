import streamlit as st

def get_animal_habitat_map(animal_name):
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Clean the animal name for URL
    query = f"habitat+of+{animal_name.replace(' ', '+')}"
    
    html = f"""
    <iframe
        width="100%"
        height="400"
        frameborder="0"
        style="border:0"
        src="https://www.google.com/maps/embed/v1/search?q={query}&key={google_maps_key}"
        allowfullscreen>
    </iframe>
    """
    return html

def get_animal_habitat_map_enhanced(animal_name, map_type="search"):
    """
    Enhanced Google Maps function with multiple map types and better habitat queries
    
    Args:
        animal_name: Name of the animal
        map_type: Type of map - 'search', 'place', or 'streetview'
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Create habitat-specific queries
    habitat_queries = {
        "search": f"{animal_name}+habitat+ecosystem+natural+environment",
        "conservation": f"{animal_name}+conservation+area+national+park+wildlife+reserve",
        "distribution": f"{animal_name}+range+distribution+native+habitat"
    }
    
    query = habitat_queries.get("search", f"habitat+of+{animal_name.replace(' ', '+')}")
    
    if map_type == "search":
        embed_url = f"https://www.google.com/maps/embed/v1/search?q={query}&key={google_maps_key}"
    elif map_type == "place":
        embed_url = f"https://www.google.com/maps/embed/v1/place?q={query}&key={google_maps_key}"
    else:
        embed_url = f"https://www.google.com/maps/embed/v1/search?q={query}&key={google_maps_key}"
    
    html = f"""
    <div style="border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <iframe
            width="100%"
            height="450"
            frameborder="0"
            style="border:0"
            src="{embed_url}"
            allowfullscreen>
        </iframe>
    </div>
    <p style="text-align: center; margin-top: 10px; color: #666; font-size: 0.9em;">
        🗺️ Showing habitat and conservation areas for <strong>{animal_name}</strong>
    </p>
    """
    return html

def get_interactive_map_with_controls(animal_name):
    """
    Interactive map with multiple view options
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Multiple search queries for comprehensive results
    queries = [
        f"{animal_name}+habitat+ecosystem",
        f"{animal_name}+national+park+wildlife",
        f"{animal_name}+conservation+area",
        f"{animal_name}+natural+environment"
    ]
    
    html = f"""
    <div style="border-radius: 15px; overflow: hidden; box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; text-align: center;">
            <h3 style="margin: 0; font-size: 1.2em;">🌍 {animal_name} Habitat Map</h3>
            <p style="margin: 5px 0 0 0; font-size: 0.9em; opacity: 0.9;">Explore natural habitats and conservation areas</p>
        </div>
        <iframe
            width="100%"
            height="500"
            frameborder="0"
            style="border:0"
            src="https://www.google.com/maps/embed/v1/search?q={queries[0].replace(' ', '+')}&key={google_maps_key}&zoom=6"
            allowfullscreen>
        </iframe>
        <div style="background: #f8f9fa; padding: 10px; text-align: center; border-top: 1px solid #e9ecef;">
            <small style="color: #6c757d;">🔍 Search includes habitats, national parks, and conservation areas</small>
        </div>
    </div>
    """
    return html

def get_comprehensive_animal_map(df, selected_category=None):
    """
    Create a comprehensive map showing all animals with different colors by category
    
    Args:
        df: DataFrame containing animal data
        selected_category: Optional category filter (None shows all)
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Color scheme for different categories
    category_colors = {
        'Bird': '#FF6B6B',      # Red
        'Mammal': '#4ECDC4',    # Teal
        'Reptile': '#45B7D1',   # Blue
        'Amphibian': '#96CEB4', # Green
        'Fish': '#FECA57',      # Yellow
        'Insect': '#FF9FF3',    # Pink
        'Arachnid': '#54A0FF',  # Light Blue
        'Other': '#9C88FF'      # Purple
    }
    
    # Handle column names
    name_col = 'NAME' if 'NAME' in df.columns else 'name'
    category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
    
    # Filter by category if specified
    if selected_category and selected_category != "All Categories":
        filtered_df = df[df[category_col] == selected_category]
        map_title = f"{selected_category} Animals"
        color = category_colors.get(selected_category, '#9C88FF')
    else:
        filtered_df = df
        map_title = "All Animals by Category"
        color = None
    
    # Create JavaScript for multiple markers
    markers_js = ""
    legend_html = ""
    
    if not filtered_df.empty:
        # Get unique categories for legend
        categories = filtered_df[category_col].dropna().unique() if category_col in filtered_df.columns else []
        
        # Create legend
        if len(categories) > 1 and not selected_category:
            legend_items = []
            for cat in sorted(categories):
                cat_color = category_colors.get(cat, '#9C88FF')
                legend_items.append(f'<div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 20px; height: 20px; background-color: {cat_color}; border-radius: 50%; margin-right: 10px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div><span>{cat}</span></div>')
            
            legend_html = f"""
            <div style="position: absolute; top: 20px; right: 20px; background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); z-index: 1000; max-width: 200px;">
                <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #333;">Animal Categories</h4>
                {''.join(legend_items)}
            </div>
            """
        
        # Create search queries for all animals
        animal_queries = []
        for _, animal in filtered_df.iterrows():
            animal_name = animal.get(name_col, 'Unknown')
            animal_category = animal.get(category_col, 'Other')
            animal_color = category_colors.get(animal_category, '#9C88FF')
            
            # Create habitat query for this animal
            query = f"{animal_name}+habitat+ecosystem+natural+environment"
            animal_queries.append({
                'name': animal_name,
                'category': animal_category,
                'color': animal_color,
                'query': query
            })
        
        # Create the search query for the main map (show all habitats)
        if selected_category and selected_category != "All Categories":
            main_query = f"{selected_category}+animals+habitat+ecosystem+conservation+wildlife"
        else:
            main_query = "wildlife+conservation+areas+national+parks+animal+habitats"
    else:
        main_query = "wildlife+conservation+areas+national+parks"
    
    # Create the enhanced map HTML
    html = f"""
    <div style="position: relative; border-radius: 15px; overflow: hidden; box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
            <h2 style="margin: 0; font-size: 1.4em;">🌍 {map_title}</h2>
            <p style="margin: 10px 0 0 0; font-size: 1em; opacity: 0.9;">
                {"Explore habitats and conservation areas" if not selected_category else f"Showing {len(filtered_df)} animals"}
            </p>
            {f'<div style="margin-top: 10px;"><span style="background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px; font-size: 0.9em;">🎨 Color-coded by category</span></div>' if not selected_category and len(categories) > 1 else ''}
        </div>
        
        <div style="position: relative;">
            <iframe
                width="100%"
                height="600"
                frameborder="0"
                style="border:0"
                src="https://www.google.com/maps/embed/v1/search?q={main_query.replace(' ', '+')}&key={google_maps_key}&zoom=4"
                allowfullscreen>
            </iframe>
            {legend_html}
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-top: 1px solid #e9ecef;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <strong style="color: #495057;">🔍 Map Coverage:</strong>
                    <span style="color: #6c757d; margin-left: 10px;">
                        {f"{len(filtered_df)} animals" if not filtered_df.empty else "Global wildlife areas"} • 
                        Habitats • Conservation areas • National parks
                    </span>
                </div>
                <div style="font-size: 0.9em; color: #6c757d;">
                    🌐 Interactive Google Maps
                </div>
            </div>
        </div>
    </div>
    """
    return html

def get_category_statistics_map(df):
    """
    Create a statistical overview map with category information
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Handle column names
    category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
    
    # Get category statistics
    if category_col in df.columns:
        category_stats = df[category_col].value_counts()
        total_animals = len(df)
        
        # Create statistics display
        stats_html = ""
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#9C88FF']
        
        for i, (category, count) in enumerate(category_stats.items()):
            percentage = (count / total_animals) * 100
            color = colors[i % len(colors)]
            stats_html += f"""
            <div style="display: flex; align-items: center; margin: 8px 0; padding: 8px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                <div style="width: 15px; height: 15px; background-color: {color}; border-radius: 50%; margin-right: 12px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>
                <div style="flex-grow: 1;">
                    <strong>{category}</strong>
                    <div style="font-size: 0.9em; opacity: 0.8;">{count} animals ({percentage:.1f}%)</div>
                </div>
            </div>
            """
    else:
        stats_html = "<p>No category data available</p>"
        total_animals = len(df)
    
    html = f"""
    <div style="border-radius: 15px; overflow: hidden; box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); margin-bottom: 20px;">
        <div style="background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: white; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <h2 style="margin: 0; font-size: 1.4em;">📊 Animal Distribution Overview</h2>
                    <p style="margin: 5px 0 0 0; font-size: 1em; opacity: 0.9;">
                        Total: {total_animals} animals across multiple categories
                    </p>
                </div>
                <div style="text-align: right; min-width: 200px;">
                    <div style="font-size: 0.9em; opacity: 0.8;">Category Breakdown:</div>
                    {stats_html}
                </div>
            </div>
        </div>
        
        <iframe
            width="100%"
            height="400"
            frameborder="0"
            style="border:0"
            src="https://www.google.com/maps/embed/v1/search?q=global+wildlife+conservation+areas+national+parks+animal+habitats&key={google_maps_key}&zoom=2"
            allowfullscreen>
        </iframe>
    </div>
    """
    return html

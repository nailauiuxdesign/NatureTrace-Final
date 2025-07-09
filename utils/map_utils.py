import streamlit as st
import pandas as pd
import json
from .data_utils import fetch_dashboard_data

# utils/map_utils.py
# Enhanced Google Maps integration with GPS database location support
# 
# ENHANCEMENTS MADE:
# 1. All map functions now prioritize actual GPS coordinates from the database
# 2. get_animal_habitat_map() - Uses GPS data for precise individual animal mapping
# 3. get_interactive_map_with_controls() - Enhanced with GPS location display
# 4. get_comprehensive_animal_map() - Mixed GPS + habitat mapping with visual indicators
# 5. get_actual_locations_map() - Dedicated GPS-only mapping function
# 6. get_location_enhanced_habitat_map() - Combines GPS precision with habitat context
# 7. Fallback system: GPS > iNaturalist > Wikipedia > Groq AI > Habitat search
# 8. Visual indicators distinguish between GPS vs habitat-based locations
# 9. Smart zoom and centering based on actual coordinate distribution
# 10. Enhanced info windows show location source and precision level

def get_animal_habitat_map(animal_name):
    """
    Enhanced animal habitat map that uses database location data when available,
    otherwise falls back to habitat search
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Try to get actual location data from database first
    try:
        df = fetch_dashboard_data()
        if not df.empty:
            name_col = 'NAME' if 'NAME' in df.columns else 'name'
            lat_col = 'LATITUDE' if 'LATITUDE' in df.columns else 'latitude'
            lng_col = 'LONGITUDE' if 'LONGITUDE' in df.columns else 'longitude'
            place_col = 'PLACE_GUESS' if 'PLACE_GUESS' in df.columns else 'place_guess'
            
            # Find the animal in the database
            animal_row = df[df[name_col].str.lower() == animal_name.lower()]
            
            if not animal_row.empty and lat_col in df.columns and lng_col in df.columns:
                animal_data = animal_row.iloc[0]
                latitude = animal_data.get(lat_col)
                longitude = animal_data.get(lng_col)
                place_guess = animal_data.get(place_col, '')
                
                if pd.notna(latitude) and pd.notna(longitude):
                    # Use actual GPS coordinates for a precise map
                    location_info = f"{place_guess}" if place_guess else f"{latitude:.4f}, {longitude:.4f}"
                    
                    html = f"""
                    <div style="border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 10px; text-align: center;">
                            <h4 style="margin: 0; font-size: 1.1em;">Precise Location: {animal_name}</h4>
                            <p style="margin: 5px 0 0 0; font-size: 0.9em;">{location_info}</p>
                        </div>
                        <iframe
                            width="100%"
                            height="400"
                            frameborder="0"
                            style="border:0"
                            src="https://www.google.com/maps/embed/v1/view?center={latitude},{longitude}&zoom=10&key={google_maps_key}"
                            allowfullscreen>
                        </iframe>
                        <div style="background: #f8f9fa; padding: 8px; text-align: center; border-top: 1px solid #e9ecef;">
                            <small style="color: #28a745;">Real GPS location from database</small>
                        </div>
                    </div>
                    """
                    return html
    except Exception as e:
        pass  # Fall back to habitat search if database query fails
    
    # Fallback to habitat search if no GPS data available
    query = f"habitat+of+{animal_name.replace(' ', '+')}"
    
    html = f"""
    <div style="border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 10px; text-align: center;">
            <h4 style="margin: 0; font-size: 1.1em;">Habitat Search: {animal_name}</h4>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">� General habitat areas</p>
        </div>
        <iframe
            width="100%"
            height="400"
            frameborder="0"
            style="border:0"
            src="https://www.google.com/maps/embed/v1/search?q={query}&key={google_maps_key}"
            allowfullscreen>
        </iframe>
        <div style="background: #f8f9fa; padding: 8px; text-align: center; border-top: 1px solid #e9ecef;">
            <small style="color: #6c757d;">� Habitat search - upload image for precise location</small>
        </div>
    </div>
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
        Showing habitat and conservation areas for <strong>{animal_name}</strong>
    </p>
    """
    return html

def get_interactive_map_with_controls(animal_name):
    """
    Interactive map with multiple view options that uses database location data when available
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Try to get actual location data from database first
    try:
        df = fetch_dashboard_data()
        if not df.empty:
            name_col = 'NAME' if 'NAME' in df.columns else 'name'
            lat_col = 'LATITUDE' if 'LATITUDE' in df.columns else 'latitude'
            lng_col = 'LONGITUDE' if 'LONGITUDE' in df.columns else 'longitude'
            place_col = 'PLACE_GUESS' if 'PLACE_GUESS' in df.columns else 'place_guess'
            category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
            
            # Find the animal in the database
            animal_row = df[df[name_col].str.lower() == animal_name.lower()]
            
            if not animal_row.empty and lat_col in df.columns and lng_col in df.columns:
                animal_data = animal_row.iloc[0]
                latitude = animal_data.get(lat_col)
                longitude = animal_data.get(lng_col)
                place_guess = animal_data.get(place_col, '')
                category = animal_data.get(category_col, 'Unknown')
                
                if pd.notna(latitude) and pd.notna(longitude):
                    # Create enhanced map with actual GPS location
                    location_info = f"{place_guess}" if place_guess else f"{latitude:.4f}, {longitude:.4f}"
                    
                    html = f"""
                    <div style="border-radius: 15px; overflow: hidden; box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);">
                        <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 15px; text-align: center;">
                            <h3 style="margin: 0; font-size: 1.2em;">{animal_name} Precise Location</h3>
                            <p style="margin: 5px 0 0 0; font-size: 0.9em;">{location_info}</p>
                            <p style="margin: 5px 0 0 0; font-size: 0.8em; opacity: 0.9;">{category} • GPS Coordinates Available</p>
                        </div>
                        <iframe
                            width="100%"
                            height="500"
                            frameborder="0"
                            style="border:0"
                            src="https://www.google.com/maps/embed/v1/view?center={latitude},{longitude}&zoom=12&maptype=satellite&key={google_maps_key}"
                            allowfullscreen>
                        </iframe>
                        <div style="background: #f8f9fa; padding: 10px; text-align: center; border-top: 1px solid #e9ecef;">
                            <div style="display: flex; justify-content: space-around; align-items: center;">
                                <small style="color: #28a745; font-weight: bold;">Real GPS Data</small>
                                <small style="color: #6c757d;">Satellite View</small>
                                <small style="color: #6c757d;">Exact Location</small>
                            </div>
                        </div>
                    </div>
                    """
                    return html
    except Exception as e:
        pass  # Fall back to habitat search if database query fails
    
    # Fallback to habitat search if no GPS data available
    queries = [
        f"{animal_name}+habitat+ecosystem",
        f"{animal_name}+national+park+wildlife",
        f"{animal_name}+conservation+area",
        f"{animal_name}+natural+environment"
    ]
    
    html = f"""
    <div style="border-radius: 15px; overflow: hidden; box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; text-align: center;">
            <h3 style="margin: 0; font-size: 1.2em;">{animal_name} Habitat Map</h3>
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
            <small style="color: #6c757d;">� Search includes habitats, national parks, and conservation areas</small>
        </div>
    </div>
    """
    return html

def get_comprehensive_animal_map(df, selected_category=None):
    """
    Create a comprehensive map showing all animals with different colors by category
    Uses actual GPS coordinates when available, falls back to habitat locations
    
    Args:
        df: DataFrame containing animal data (with latitude/longitude columns)
        selected_category: Optional category filter (None shows all)
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Color scheme for different categories (Google Maps compatible colors)
    category_colors = {
        'Bird': 'red',
        'Mammal': 'blue', 
        'Reptile': 'green',
        'Amphibian': 'purple',
        'Fish': 'yellow',
        'Insect': 'orange',
        'Arachnid': 'pink',
        'Other': 'gray'
    }
    
    # Handle column names
    name_col = 'NAME' if 'NAME' in df.columns else 'name'
    category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
    lat_col = 'LATITUDE' if 'LATITUDE' in df.columns else 'latitude'
    lng_col = 'LONGITUDE' if 'LONGITUDE' in df.columns else 'longitude'
    place_col = 'PLACE_GUESS' if 'PLACE_GUESS' in df.columns else 'place_guess'
    
    # Filter by category if specified
    if selected_category and selected_category != "All Categories":
        filtered_df = df[df[category_col] == selected_category]
        map_title = f"{selected_category} Animals"
    else:
        filtered_df = df
        map_title = "All Animals by Category"
    
    if filtered_df.empty:
        return "<p>No animals to display on map.</p>"
    
    # Check if we have GPS data available
    has_gps_data = (lat_col in df.columns and lng_col in df.columns and 
                    not df[lat_col].isna().all() and not df[lng_col].isna().all())
    
    # Count animals with actual GPS coordinates
    gps_animals = 0
    if has_gps_data:
        gps_animals = len(filtered_df.dropna(subset=[lat_col, lng_col]))
    
    # Get unique categories for legend and markers
    categories = filtered_df[category_col].dropna().unique() if category_col in filtered_df.columns else []
    
    # Create legend HTML
    legend_html = ""
    if len(categories) > 1 and not selected_category:
        legend_items = []
        for cat in sorted(categories):
            cat_color = category_colors.get(cat, 'gray')
            # Convert color names to hex for legend display
            color_hex = {
                'red': '#FF0000', 'blue': '#0000FF', 'green': '#008000',
                'purple': '#800080', 'yellow': '#FFD700', 'orange': '#FFA500',
                'pink': '#FFC0CB', 'gray': '#808080'
            }.get(cat_color, '#808080')
            
            legend_items.append(f'''
                <div style="display: flex; align-items: center; margin: 8px 0; padding: 5px;">
                    <div style="width: 16px; height: 16px; background-color: {color_hex}; 
                                border-radius: 50%; margin-right: 10px; 
                                border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                    </div>
                    <span style="font-size: 13px; font-weight: 500;">{cat}</span>
                </div>
            ''')
        
        legend_html = f'''
            <div style="position: absolute; top: 15px; right: 15px; 
                        background: rgba(255,255,255,0.95); padding: 12px; 
                        border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
                        z-index: 1000; max-width: 180px; backdrop-filter: blur(5px);">
                <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #333; text-align: center;">
                    Animal Categories
                </h4>
                {''.join(legend_items)}
            </div>
        '''
    
    # Generate markers data for JavaScript - prioritize actual GPS coordinates
    markers_data = []
    location_queries = []
    center_lat = 20.0  # Default global center
    center_lng = 0.0
    
    # Collect actual GPS locations for map centering
    gps_locations = []
    
    for idx, (_, animal) in enumerate(filtered_df.iterrows()):
        animal_name = animal.get(name_col, 'Unknown')
        animal_category = animal.get(category_col, 'Other')
        marker_color = category_colors.get(animal_category, 'gray')
        
        # Check if animal has actual GPS coordinates
        actual_lat = animal.get(lat_col) if has_gps_data else None
        actual_lng = animal.get(lng_col) if has_gps_data else None
        place_name = animal.get(place_col, '') if has_gps_data else ''
        
        if (pd.notna(actual_lat) and pd.notna(actual_lng) and 
            actual_lat != 0 and actual_lng != 0):
            # Use actual GPS coordinates
            gps_locations.append({'lat': actual_lat, 'lng': actual_lng})
            markers_data.append({
                'name': animal_name,
                'category': animal_category,
                'color': marker_color,
                'lat': actual_lat,
                'lng': actual_lng,
                'location_type': 'gps',
                'place_name': place_name,
                'id': idx
            })
        else:
            # Fall back to habitat-based location
            location_query = f"{animal_name} habitat natural range"
            location_queries.append(location_query)
            
            markers_data.append({
                'name': animal_name,
                'category': animal_category,
                'color': marker_color,
                'query': location_query,
                'location_type': 'habitat',
                'id': idx
            })
    
    # Calculate map center based on actual GPS data if available
    if gps_locations:
        center_lat = sum(loc['lat'] for loc in gps_locations) / len(gps_locations)
        center_lng = sum(loc['lng'] for loc in gps_locations) / len(gps_locations)
        # Adjust zoom level based on spread of coordinates
        lat_range = max(loc['lat'] for loc in gps_locations) - min(loc['lat'] for loc in gps_locations)
        lng_range = max(loc['lng'] for loc in gps_locations) - min(loc['lng'] for loc in gps_locations)
        zoom_level = max(2, min(10, int(12 - max(lat_range, lng_range) * 2)))
    else:
        zoom_level = 2
    
    # Generate unique map ID to avoid conflicts
    import time
    map_id = f"animal_map_{int(time.time())}"
    
    # Create status indicator for GPS vs habitat data
    status_indicator = ""
    if gps_animals > 0:
        habitat_animals = len(filtered_df) - gps_animals
        if habitat_animals > 0:
            status_indicator = f'<div style="margin-top: 12px; display: flex; justify-content: center; gap: 20px;"><span style="background: rgba(76, 175, 80, 0.9); color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8em;">{gps_animals} GPS locations</span><span style="background: rgba(103, 126, 234, 0.9); color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8em;">{habitat_animals} habitat areas</span></div>'
        else:
            status_indicator = f'<div style="margin-top: 12px;"><span style="background: rgba(76, 175, 80, 0.9); color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.9em; font-weight: 500;">All {gps_animals} animals with GPS data!</span></div>'
    else:
        status_indicator = f'<div style="margin-top: 12px;"><span style="background: rgba(103, 126, 234, 0.9); color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.9em; font-weight: 500;">� Habitat-based locations</span></div>'
    
    # Create the enhanced map with JavaScript API
    html = f'''
    <div style="position: relative; border-radius: 15px; overflow: hidden; 
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; text-align: center;">
            <h2 style="margin: 0; font-size: 1.4em; font-weight: 600;">{map_title}</h2>
            <p style="margin: 10px 0 0 0; font-size: 1em; opacity: 0.9;">
                {"Enhanced with GPS coordinates and habitat areas" if gps_animals > 0 else "Habitat and conservation area overview"}
            </p>
            {status_indicator if not selected_category and len(categories) > 1 else status_indicator}
        </div>
        
        <div style="position: relative;">
            <div id="{map_id}" style="width: 100%; height: 600px;"></div>
            {legend_html}
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-top: 1px solid #e9ecef;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <strong style="color: #495057;">� Map Coverage:</strong>
                    <span style="color: #6c757d; margin-left: 10px;">
                        {len(filtered_df)} animals • {"GPS locations • " if gps_animals > 0 else ""}Habitats • Conservation areas
                    </span>
                </div>
                <div style="font-size: 0.9em; color: #6c757d;">
                    {"Enhanced GPS mapping" if gps_animals > 0 else "Interactive habitat mapping"}
                </div>
            </div>
        </div>
    </div>
    
    <script async defer 
            src="https://maps.googleapis.com/maps/api/js?key={google_maps_key}&callback=initMap{map_id}&libraries=geometry">
    </script>
    
    <script>
        function initMap{map_id}() {{
            // Center the map on calculated position (GPS-based if available)
            const map = new google.maps.Map(document.getElementById("{map_id}"), {{
                zoom: {zoom_level},
                center: {{ lat: {center_lat}, lng: {center_lng} }},
                mapTypeId: {'satellite' if gps_animals > 0 else 'terrain'},
                styles: [
                    {{
                        "featureType": "administrative",
                        "elementType": "geometry.stroke",
                        "stylers": [{{ "color": "#c9b2a6" }}]
                    }},
                    {{
                        "featureType": "administrative.land_parcel",
                        "elementType": "geometry.stroke",
                        "stylers": [{{ "color": "#dcd2be" }}]
                    }},
                    {{
                        "featureType": "landscape",
                        "elementType": "geometry.fill",
                        "stylers": [{{ "color": "#faf5f0" }}]
                    }},
                    {{
                        "featureType": "landscape.natural",
                        "elementType": "geometry.fill",
                        "stylers": [{{ "color": "#e8f5e8" }}]
                    }}
                ]
            }});
            
            const geocoder = new google.maps.Geocoder();
            const infoWindow = new google.maps.InfoWindow();
            
            // Animal data from Python - includes both GPS and habitat-based locations
            const animals = {json.dumps(markers_data)};
            
            // Fallback habitat locations for animals without GPS data
            const categoryLocations = {{
                'Bird': [
                    {{ name: 'Amazon Rainforest', lat: -3.4653, lng: -62.2159 }},
                    {{ name: 'North American Forests', lat: 45.0, lng: -85.0 }},
                    {{ name: 'African Savanna', lat: -1.0, lng: 25.0 }}
                ],
                'Mammal': [
                    {{ name: 'African Safari Regions', lat: -2.0, lng: 35.0 }},
                    {{ name: 'North American Wilderness', lat: 50.0, lng: -100.0 }},
                    {{ name: 'Asian Forests', lat: 25.0, lng: 100.0 }}
                ],
                'Reptile': [
                    {{ name: 'Australian Outback', lat: -25.0, lng: 135.0 }},
                    {{ name: 'American Southwest', lat: 35.0, lng: -110.0 }},
                    {{ name: 'African Deserts', lat: 15.0, lng: 20.0 }}
                ],
                'Amphibian': [
                    {{ name: 'Tropical Rainforests', lat: 0.0, lng: -60.0 }},
                    {{ name: 'Wetlands', lat: 40.0, lng: -90.0 }},
                    {{ name: 'Temperate Forests', lat: 45.0, lng: 10.0 }}
                ],
                'Fish': [
                    {{ name: 'Coral Reefs', lat: -18.0, lng: 147.0 }},
                    {{ name: 'Atlantic Ocean', lat: 40.0, lng: -30.0 }},
                    {{ name: 'Pacific Ocean', lat: 0.0, lng: 160.0 }}
                ],
                'default': [
                    {{ name: 'Global Wildlife Areas', lat: 20.0, lng: 0.0 }}
                ]
            }};
            
            // Add markers for each animal
            animals.forEach((animal, index) => {{
                let markerLat, markerLng, locationInfo, markerIcon;
                
                if (animal.location_type === 'gps' && animal.lat && animal.lng) {{
                    // Use actual GPS coordinates
                    markerLat = animal.lat;
                    markerLng = animal.lng;
                    locationInfo = animal.place_name || `${{animal.lat.toFixed(4)}}, ${{animal.lng.toFixed(4)}}`;
                    
                    // GPS markers are larger and have a border to indicate precision
                    markerIcon = {{
                        path: google.maps.SymbolPath.CIRCLE,
                        fillColor: animal.color,
                        fillOpacity: 0.9,
                        strokeColor: '#ffffff',
                        strokeWeight: 3,
                        scale: 10
                    }};
                }} else {{
                    // Use fallback habitat location
                    const locations = categoryLocations[animal.category] || categoryLocations['default'];
                    const location = locations[index % locations.length];
                    markerLat = location.lat;
                    markerLng = location.lng;
                    locationInfo = location.name;
                    
                    // Habitat markers are smaller and have a different style
                    markerIcon = {{
                        path: google.maps.SymbolPath.CIRCLE,
                        fillColor: animal.color,
                        fillOpacity: 0.7,
                        strokeColor: '#ffffff',
                        strokeWeight: 2,
                        scale: 7
                    }};
                }}
                
                const marker = new google.maps.Marker({{
                    position: {{ lat: markerLat, lng: markerLng }},
                    map: map,
                    title: `${{animal.name}} (${{animal.category}})`,
                    icon: markerIcon,
                    animation: google.maps.Animation.DROP
                }});
                
                // Create info window with location type indicator
                const locationTypeIcon = animal.location_type === 'gps' ? 'GPS' : 'Habitat';
                const locationTypeText = animal.location_type === 'gps' ? 'GPS Location' : 'Habitat Area';
                
                marker.addListener('click', () => {{
                    const locationBadge = animal.location_type === 'gps' ? 
                        '<div style="margin-top: 8px; padding: 4px 8px; background: #e8f5e9; border-radius: 4px; font-size: 0.8em; color: #2e7d32;">Precise location data</div>' : 
                        '<div style="margin-top: 8px; padding: 4px 8px; background: #e3f2fd; border-radius: 4px; font-size: 0.8em; color: #1565c0;">� General habitat area</div>';
                        
                    infoWindow.setContent(`
                        <div style="padding: 12px; max-width: 220px;">
                            <h4 style="margin: 0 0 8px 0; color: #333;">${{animal.name}}</h4>
                            <p style="margin: 0 0 5px 0; color: #666;">
                                <strong>Category:</strong> ${{animal.category}}
                            </p>
                            <p style="margin: 0 0 5px 0; color: #666; font-size: 0.9em;">
                                <strong>${{locationTypeIcon}} ${{locationTypeText}}:</strong> ${{locationInfo}}
                            </p>
                            ${{locationBadge}}
                        </div>
                    `);
                    infoWindow.open(map, marker);
                }});
            }});
            
            // Set bounds to show all markers if GPS data is available
            if (animals.length > 0) {{
                const bounds = new google.maps.LatLngBounds();
                let hasGPSMarkers = false;
                
                animals.forEach((animal, index) => {{
                    let markerLat, markerLng;
                    
                    if (animal.location_type === 'gps' && animal.lat && animal.lng) {{
                        markerLat = animal.lat;
                        markerLng = animal.lng;
                        hasGPSMarkers = true;
                    }} else {{
                        const locations = categoryLocations[animal.category] || categoryLocations['default'];
                        const location = locations[index % locations.length];
                        markerLat = location.lat;
                        markerLng = location.lng;
                    }}
                    
                    bounds.extend(new google.maps.LatLng(markerLat, markerLng));
                }});
                
                // Only fit bounds if we have GPS markers, otherwise use global view
                if (hasGPSMarkers) {{
                    map.fitBounds(bounds);
                    
                    // Ensure reasonable zoom levels
                    google.maps.event.addListenerOnce(map, 'bounds_changed', function() {{
                        if (map.getZoom() > 15) {{
                            map.setZoom(15);  // Don't zoom too close
                        }}
                        if (map.getZoom() < 3) {{
                            map.setZoom(3);   // Don't zoom too far out
                        }}
                    }});
                }}
            }}
        }}
        
        // Initialize map when DOM is ready
        if (typeof google !== 'undefined' && google.maps) {{
            initMap{map_id}();
        }}
    </script>
    '''
    
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
                    <h2 style="margin: 0; font-size: 1.4em;">� Animal Distribution Overview</h2>
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

def get_simple_colored_map(df, selected_category=None):
    """
    Simpler approach using multiple iframes with different colors for categories
    Falls back when JavaScript API doesn't work
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Handle column names
    name_col = 'NAME' if 'NAME' in df.columns else 'name'
    category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
    
    # Filter by category if specified
    if selected_category and selected_category != "All Categories":
        filtered_df = df[df[category_col] == selected_category]
        map_title = f"{selected_category} Animals"
    else:
        filtered_df = df
        map_title = "All Animals by Category"
    
    if filtered_df.empty:
        return "<p>No animals to display on map.</p>"
    
    # Create category-specific search queries
    category_queries = []
    if category_col in filtered_df.columns:
        categories = filtered_df[category_col].dropna().unique()
        for category in categories:
            category_animals = filtered_df[filtered_df[category_col] == category]
            animal_list = "+".join([name.replace(" ", "+") for name in category_animals[name_col].tolist()[:5]])  # Limit to 5 animals per category
            query = f"{category}+animals+habitat+{animal_list}+conservation+wildlife"
            category_queries.append((category, query))
    
    # Generate the main query
    if selected_category and selected_category != "All Categories":
        main_query = f"{selected_category}+animals+habitat+ecosystem+conservation+wildlife"
    else:
        all_animals = "+".join([name.replace(" ", "+") for name in filtered_df[name_col].tolist()[:10]])  # Limit to prevent URL too long
        main_query = f"wildlife+conservation+areas+{all_animals}+animal+habitats"
    
    html = f"""
    <div style="position: relative; border-radius: 15px; overflow: hidden; 
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; text-align: center;">
            <h2 style="margin: 0; font-size: 1.4em; font-weight: 600;">{map_title}</h2>
            <p style="margin: 10px 0 0 0; font-size: 1em; opacity: 0.9;">
                Showing {len(filtered_df)} animals across different regions
            </p>
            <div style="margin-top: 12px;">
                <span style="background: rgba(255,255,255,0.25); padding: 6px 16px; 
                           border-radius: 20px; font-size: 0.9em; font-weight: 500;">
                    Comprehensive habitat overview
                </span>
            </div>
        </div>
        
        <div style="position: relative;">
            <iframe
                width="100%"
                height="600"
                frameborder="0"
                style="border:0"
                src="https://www.google.com/maps/embed/v1/search?q={main_query.replace(' ', '+')}&key={google_maps_key}&zoom=3"
                allowfullscreen>
            </iframe>
            
            <div style="position: absolute; top: 15px; right: 15px; 
                        background: rgba(255,255,255,0.95); padding: 12px; 
                        border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
                        z-index: 1000; max-width: 200px;">
                <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #333; text-align: center;">
                    � Animals Overview
                </h4>
                <div style="font-size: 12px; color: #666;">
                    <strong>Total Animals:</strong> {len(filtered_df)}<br>
                    {"<strong>Category:</strong> " + selected_category if selected_category and selected_category != "All Categories" else f"<strong>Categories:</strong> {len(filtered_df[category_col].dropna().unique()) if category_col in filtered_df.columns else 'N/A'}"}
                </div>
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-top: 1px solid #e9ecef;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <strong style="color: #495057;">� Showing:</strong>
                    <span style="color: #6c757d; margin-left: 10px;">
                        {len(filtered_df)} animals • Habitats • Conservation areas • Wildlife reserves
                    </span>
                </div>
                <div style="font-size: 0.9em; color: #6c757d;">
                    Google Maps Enhanced View
                </div>
            </div>
        </div>
    </div>
    """
    
    return html

def get_actual_locations_map(df, selected_category=None):
    """
    Create an interactive map using actual location data from the database
    
    Args:
        df: DataFrame with animal data including latitude/longitude columns
        selected_category: Optional category filter
    
    Returns:
        HTML string for the interactive map
    """
    google_maps_key = st.secrets.get("google_maps_key")
    
    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found.</p>"
    
    # Filter data by category if specified
    if selected_category and selected_category != "All Categories":
        category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
        if category_col in df.columns:
            df = df[df[category_col] == selected_category]
    
    # Get animals with valid location data
    lat_col = 'LATITUDE' if 'LATITUDE' in df.columns else 'latitude'
    lng_col = 'LONGITUDE' if 'LONGITUDE' in df.columns else 'longitude'
    name_col = 'NAME' if 'NAME' in df.columns else 'name'
    
    if lat_col not in df.columns or lng_col not in df.columns:
        return get_comprehensive_animal_map(df, selected_category)  # Fallback to habitat-based map
    
    # Filter animals with valid coordinates
    valid_locations = df.dropna(subset=[lat_col, lng_col])
    
    if valid_locations.empty:
        return get_comprehensive_animal_map(df, selected_category)  # Fallback to habitat-based map
    
    # Calculate map center
    center_lat = valid_locations[lat_col].mean()
    center_lng = valid_locations[lng_col].mean()
    
    # Color mapping for categories
    category_colors = {
        'Aves': '#FF6B6B',          # Red for birds
        'Mammalia': '#4ECDC4',      # Teal for mammals  
        'Reptilia': '#45B7D1',      # Blue for reptiles
        'Amphibia': '#96CEB4',      # Green for amphibians
        'Actinopterygii': '#FECA57', # Yellow for fish
        'Insecta': '#FF9FF3',       # Pink for insects
        'Arachnida': '#54A0FF',     # Light blue for arachnids
        'Other': '#9C88FF'          # Purple for others
    }
    
    # Generate markers for each animal
    markers_js = []
    info_windows_js = []
    
    for idx, (_, animal) in enumerate(valid_locations.iterrows()):
        lat = animal[lat_col]
        lng = animal[lng_col]
        name = animal.get(name_col, 'Unknown Animal')
        category = animal.get('CATEGORY', animal.get('category', 'Other'))
        place_guess = animal.get('PLACE_GUESS', animal.get('place_guess', ''))
        
        # Get category color
        color = category_colors.get(category, category_colors['Other'])
        
        # Create marker
        marker_id = f"marker_{idx}"
        info_id = f"info_{idx}"
        
        markers_js.append(f"""
        var {marker_id} = new google.maps.Marker({{
            position: {{lat: {lat}, lng: {lng}}},
            map: map,
            title: {json.dumps(name)},
            icon: {{
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: '{color}',
                fillOpacity: 0.8,
                strokeColor: '#ffffff',
                strokeWeight: 2,
                scale: 8
            }}
        }});
        """)
        
        # Create info window content
        location_info = f"{place_guess}" if place_guess else f"{lat:.4f}, {lng:.4f}"
        info_content = f"""
        <div style="max-width: 300px;">
            <h3 style="color: {color}; margin: 0 0 10px 0;">{name}</h3>
            <p><strong>Category:</strong> {category}</p>
            <p><strong>Location:</strong> {location_info}</p>
            <button onclick="window.open('?page=Profiles&animal={name.replace(' ', '%20')}', '_self')" 
                    style="background: {color}; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
                View Profile
            </button>
        </div>
        """
        
        info_windows_js.append(f"""
        var {info_id} = new google.maps.InfoWindow({{
            content: {json.dumps(info_content)}
        }});
        
        {marker_id}.addListener('click', function() {{
            // Close all other info windows
            infoWindows.forEach(function(iw) {{ iw.close(); }});
            {info_id}.open(map, {marker_id});
        }});
        
        infoWindows.push({info_id});
        """)
    
    # Create the complete HTML with JavaScript
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://maps.googleapis.com/maps/api/js?key={google_maps_key}"></script>
        <style>
            #map {{ height: 100%; width: 100%; }}
            .map-container {{ height: 600px; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <div class="map-container">
            <div id="map"></div>
        </div>
        
        <script>
            function initMap() {{
                var map = new google.maps.Map(document.getElementById('map'), {{
                    zoom: 4,
                    center: {{lat: {center_lat}, lng: {center_lng}}},
                    mapTypeId: 'hybrid',
                    styles: [
                        {{
                            "featureType": "all",
                            "elementType": "labels.text.fill",
                            "stylers": [{{ "color": "#ffffff" }}]
                        }},
                        {{
                            "featureType": "water",
                            "elementType": "geometry",
                            "stylers": [{{ "color": "#193c3e" }}]
                        }}
                    ]
                }});
                
                var infoWindows = [];
                
                {chr(10).join(markers_js)}
                
                {chr(10).join(info_windows_js)}
                
                // Add legend
                var legend = document.createElement('div');
                legend.innerHTML = `
                    <div style="background: white; padding: 15px; margin: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                        <h4 style="margin: 0 0 10px 0;">Animal Locations</h4>
                        <p style="margin: 0; font-size: 12px;"><strong>{len(valid_locations)}</strong> animals with GPS coordinates</p>
                        <p style="margin: 5px 0 0 0; font-size: 12px;">Click markers to view animal profiles</p>
                    </div>
                `;
                map.controls[google.maps.ControlPosition.TOP_LEFT].push(legend);
            }}
            
            // Initialize map when page loads
            window.onload = initMap;
        </script>
    </body>
    </html>
    """
    
    return html

def get_location_enhanced_habitat_map(animal_name, df=None):
    """
    Enhanced habitat map that combines actual GPS locations with habitat data
    
    Args:
        animal_name: Name of the animal
        df: Optional DataFrame with location data (if not provided, fetches from database)
    
    Returns:
        HTML string for the enhanced map
    """
    google_maps_key = st.secrets.get("google_maps_key")
    
    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found.</p>"
    
    # Fetch data from database if not provided
    if df is None:
        try:
            df = fetch_dashboard_data()
        except Exception as e:
            # If database fetch fails, fall back to basic habitat map
            return get_animal_habitat_map(animal_name)
    
    # Check if we have actual location data for this animal
    actual_locations = []
    if df is not None and not df.empty:
        name_col = 'NAME' if 'NAME' in df.columns else 'name'
        lat_col = 'LATITUDE' if 'LATITUDE' in df.columns else 'latitude'
        lng_col = 'LONGITUDE' if 'LONGITUDE' in df.columns else 'longitude'
        place_col = 'PLACE_GUESS' if 'PLACE_GUESS' in df.columns else 'place_guess'
        category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
        
        if all(col in df.columns for col in [name_col, lat_col, lng_col]):
            animal_rows = df[df[name_col].str.lower() == animal_name.lower()]
            for _, row in animal_rows.iterrows():
                if pd.notna(row[lat_col]) and pd.notna(row[lng_col]):
                    actual_locations.append({
                        'lat': row[lat_col],
                        'lng': row[lng_col],
                        'place': row.get(place_col, ''),
                        'category': row.get(category_col, 'Unknown')
                    })
    
    # Create base habitat search
    habitat_query = f"{animal_name}+habitat+ecosystem+natural+environment"
    
    if actual_locations:
        # If we have actual locations, center the map on them
        center_lat = sum(loc['lat'] for loc in actual_locations) / len(actual_locations)
        center_lng = sum(loc['lng'] for loc in actual_locations) / len(actual_locations)
        
        # Generate markers for actual sighting locations
        markers_js = []
        info_windows_js = []
        
        for i, loc in enumerate(actual_locations):
            place_info = f" - {loc['place']}" if loc['place'] else ""
            location_display = loc['place'] if loc['place'] else f"{loc['lat']:.4f}, {loc['lng']:.4f}";
            
            title_text = f"Actual {animal_name} Sighting{place_info}"
            
            markers_js.append(f"""
            var actualMarker_{i} = new google.maps.Marker({{
                position: {{lat: {loc['lat']}, lng: {loc['lng']}}},
                map: map,
                title: {json.dumps(title_text)},
                icon: {{
                    path: google.maps.SymbolPath.CIRCLE,
                    fillColor: '#FF4444',
                    fillOpacity: 1,
                    strokeColor: '#ffffff',
                    strokeWeight: 3,
                    scale: 12
                }},
                zIndex: 1000
            }});
            """);
            
            # Create info window content for JSON encoding
            info_content = f"""
                <div style="max-width: 250px;">
                    <h4 style="color: #FF4444; margin: 0 0 10px 0;">Actual Sighting</h4>
                    <p style="margin: 5px 0;"><strong>{animal_name}</strong></p>
                    <p style="margin: 5px 0;"><strong>Category:</strong> {loc['category']}</p>
                    <p style="margin: 5px 0;"><strong>Location:</strong> {location_display}</p>
                    <button onclick="window.open('?page=Profiles&animal={animal_name.replace(' ', '%20')}', '_self')" 
                            style="background: #FF4444; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
                        View Profile
                    </button>
                </div>
            """
            
            info_windows_js.append(f"""
            var actualInfo_{i} = new google.maps.InfoWindow({{
                content: {json.dumps(info_content)}
            }});
            
            actualMarker_{i}.addListener('click', function() {{
                // Close all info windows first
                infoWindows.forEach(function(iw) {{ iw.close(); }});
                actualInfo_{i}.open(map, actualMarker_{i});
            }});
            
            infoWindows.push(actualInfo_{i});
            """);
        
        map_center = f"{{lat: {center_lat}, lng: {center_lng}}}"
        zoom_level = 8
        status_text = f"Showing {len(actual_locations)} actual sighting(s)"
        map_type = "'hybrid'"
    else:
        # Fallback to habitat search center
        map_center = "{lat: 20, lng: 0}"  # World center
        zoom_level = 3
        markers_js = []
        info_windows_js = []
        status_text = "� No GPS data - showing habitat search"
        map_type = "'terrain'"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://maps.googleapis.com/maps/api/js?key={google_maps_key}&libraries=places"></script>
        <style>
            #map {{ height: 100%; width: 100%; }}
            .map-container {{ 
                height: 500px; 
                border-radius: 10px; 
                overflow: hidden; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border: 2px solid #4CAF50;
            }}
            .map-header {{
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 10px;
                text-align: center;
                font-family: Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div class="map-container">
            <div class="map-header">
                <h3 style="margin: 0; font-size: 1.1em;">{animal_name} Location Map</h3>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">{status_text}</p>
            </div>
            <div id="map"></div>
        </div>
        
        <script>
            var infoWindows = [];
            
            function initMap() {{
                var map = new google.maps.Map(document.getElementById('map'), {{
                    zoom: {zoom_level},
                    center: {map_center},
                    mapTypeId: {map_type}
                }});
                
                {chr(10).join(markers_js)}
                
                {chr(10).join(info_windows_js)}
                
                // Add habitat search layer if no actual locations
                if ({len(actual_locations)} === 0) {{
                    var request = {{
                        query: '{habitat_query}',
                        fields: ['name', 'geometry', 'place_id']
                    }};
                    
                    var service = new google.maps.places.PlacesService(map);
                    service.textSearch(request, function(results, status) {{
                        if (status === google.maps.places.PlacesServiceStatus.OK) {{
                            for (var i = 0; i < Math.min(results.length, 10); i++) {{
                                var place = results[i];
                                var marker = new google.maps.Marker({{
                                    position: place.geometry.location,
                                    map: map,
                                    title: place.name,
                                    icon: {{
                                        path: google.maps.SymbolPath.CIRCLE,
                                        fillColor: '#4CAF50',
                                        fillOpacity: 0.6,
                                        strokeColor: '#ffffff',
                                        strokeWeight: 1,
                                        scale: 8
                                    }}
                                }});
                                
                                var infoWindow = new google.maps.InfoWindow({{
                                    content: '<div><h4>� Habitat Area</h4><p>' + place.name + '</p></div>'
                                }});
                                
                                marker.addListener('click', function() {{
                                    infoWindows.forEach(function(iw) {{ iw.close(); }});
                                    infoWindow.open(map, marker);
                                }});
                                
                                infoWindows.push(infoWindow);
                            }}
                        }}
                    }});
                }}
                
                // Add legend
                var legend = document.createElement('div');
                legend.innerHTML = `
                    <div style="background: rgba(255,255,255,0.95); padding: 12px; margin: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); backdrop-filter: blur(5px);">
                        <h4 style="margin: 0 0 8px 0; color: #333;">{animal_name}</h4>
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <div style="width: 12px; height: 12px; background: #FF4444; border-radius: 50%; margin-right: 8px; border: 2px solid white;"></div>
                            <span style="font-size: 12px;">GPS Sightings ({len(actual_locations)})</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <div style="width: 12px; height: 12px; background: #4CAF50; border-radius: 50%; margin-right: 8px; opacity: 0.6;"></div>
                            <span style="font-size: 12px;">Habitat Areas</span>
                        </div>
                        <div style="margin-top: 8px; font-size: 11px; color: #666;">
                            Click markers for details
                        </div>
                    </div>
                `;
                map.controls[google.maps.ControlPosition.TOP_RIGHT].push(legend);
            }}
            
            window.onload = initMap;
        </script>
    </body>
    </html>
    """
    
    return html

def get_individual_animal_map(animal_name):
    """
    Create a focused map for a single animal using database location data
    
    Args:
        animal_name: Name of the animal to map
        
    Returns:
        HTML string for the map
    """
    return get_location_enhanced_habitat_map(animal_name)

def convert_category_name(cat):
    """Convert scientific category names to English."""
    name_mapping = {
        'Actinopterygii': 'Ray-Finned Fish',
        'Amphibia': 'Amphibians',
        'Animalia': 'Animals',
        'Aves': 'Birds',
        'Insecta': 'Insects',
        'Mammalia': 'Mammals',
        'Reptilia': 'Reptiles',
        'Arachnida': 'Arachnids',
        'Chondrichthyes': 'Cartilaginous Fish',
        'Crustacea': 'Crustaceans',
        'Mollusca': 'Mollusks',
        # Add plural forms to ensure consistent translation
        'Birds': 'Birds',
        'Mammals': 'Mammals',
        'Reptiles': 'Reptiles',
        'Amphibians': 'Amphibians',
        'Fish': 'Fish',
        'Insects': 'Insects',
        'Arachnids': 'Arachnids',
        'Animals': 'Animals'
    }
    # If category is already in English, return as is
    if cat in name_mapping.values():
        return cat
    translated = name_mapping.get(cat, cat)
    # Ensure consistent pluralization
    if translated.endswith('Fish'):
        return translated  # Keep 'Fish' as is
    elif not translated.endswith('s'):
        return f"{translated}s"  # Add 's' for pluralization
    return translated

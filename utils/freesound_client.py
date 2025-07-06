# utils/freesound_client.py

import requests
import streamlit as st
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class FreeSoundClient:
    """Client for FreeSound.org API to fetch animal sounds"""
    
    def __init__(self):
        self.base_url = "https://freesound.org/apiv2"
        self.api_key = st.secrets.get("free_sounds_key", "")
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Token {self.api_key}',
                'User-Agent': 'NatureTrace/1.0 (Educational Research)'
            })
    
    def get_best_animal_sound(self, animal_name: str, max_duration: int = 30) -> Optional[str]:
        """
        Get the best animal sound from FreeSound for the given animal
        
        Args:
            animal_name: Name of the animal to search for
            max_duration: Maximum duration in seconds
            
        Returns:
            Direct download URL to the best matching sound, or None if not found
        """
        if not self.api_key:
            logger.warning("FreeSound API key not configured")
            return None
            
        try:
            # Search for animal sounds
            search_params = {
                'query': f'"{animal_name}" animal sound call',
                'filter': f'duration:[0 TO {max_duration}] type:wav OR type:mp3',
                'sort': 'rating_desc',
                'fields': 'id,name,previews,download,duration,rating,description',
                'page_size': 20
            }
            
            response = self.session.get(
                f"{self.base_url}/search/text/",
                params=search_params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                sounds = data.get('results', [])
                
                if sounds:
                    # Score and rank sounds
                    scored_sounds = []
                    animal_lower = animal_name.lower()
                    
                    for sound in sounds:
                        score = 0
                        name = sound.get('name', '').lower()
                        description = sound.get('description', '').lower()
                        
                        # Exact match in name gets highest score
                        if animal_lower in name:
                            score += 100
                        
                        # Check description for animal-related keywords
                        animal_keywords = ['animal', 'wildlife', 'nature', 'bird', 'mammal', 'call', 'sound', 'vocalization']
                        for keyword in animal_keywords:
                            if keyword in description:
                                score += 10
                        
                        # Prefer shorter sounds for quick identification
                        duration = sound.get('duration', 0)
                        if duration <= 1:
                            score += 50
                        elif duration <= 5:
                            score += 30
                        elif duration <= 15:
                            score += 10
                        
                        # Rating bonus
                        rating = sound.get('rating', 0)
                        if rating:
                            score += min(rating * 5, 25)  # Max 25 points for rating
                        
                        if score > 0:
                            scored_sounds.append((score, sound))
                    
                    if scored_sounds:
                        # Sort by score and get the best one
                        scored_sounds.sort(reverse=True, key=lambda x: x[0])
                        best_sound = scored_sounds[0][1]
                        
                        # Get download URL
                        sound_id = best_sound.get('id')
                        if sound_id:
                            # Try to get direct download URL
                            download_response = self.session.get(
                                f"{self.base_url}/sounds/{sound_id}/download/",
                                timeout=10,
                                allow_redirects=False
                            )
                            
                            if download_response.status_code == 302:
                                # Redirect location is the download URL
                                download_url = download_response.headers.get('Location')
                                if download_url:
                                    logger.info(f"FreeSound found: {best_sound.get('name')} (rating: {best_sound.get('rating', 'N/A')})")
                                    return download_url
                            
                            # Fallback to preview URL if download fails
                            previews = best_sound.get('previews', {})
                            if previews.get('preview-hq-mp3'):
                                logger.info(f"FreeSound fallback preview: {best_sound.get('name')}")
                                return previews['preview-hq-mp3']
                            elif previews.get('preview-lq-mp3'):
                                return previews['preview-lq-mp3']
            
            return None
            
        except Exception as e:
            logger.error(f"FreeSound API error for {animal_name}: {str(e)}")
            return None
    
    def test_connection(self) -> dict:
        """Test the FreeSound API connection"""
        if not self.api_key:
            return {"success": False, "error": "No API key configured"}
        
        try:
            response = self.session.get(f"{self.base_url}/me/", timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "success": True,
                    "username": user_data.get('username', 'Unknown'),
                    "message": "FreeSound API connection successful"
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global instance
freesound_client = FreeSoundClient()

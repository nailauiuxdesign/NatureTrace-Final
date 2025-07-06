# utils/sound_utils.py
import requests
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
import time
import logging
import re
from urllib.parse import quote, urljoin
from utils.freesound_client import freesound_client
from utils.audio_processor import audio_processor, AUDIO_PROCESSING_AVAILABLE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnimalSoundFetcher:
    """Enhanced animal sound fetcher with multiple high-quality sources"""
    
    SOURCES = {
        "xeno_canto": "https://xeno-canto.org/api/2/recordings",
        "inaturalist": "https://api.inaturalist.org/v1/observations", 
        "freesound": "https://freesound.org/apiv2/search/text",
        "macaulay": "https://search.macaulaylibrary.org/api/v1/search",  # Cornell's Macaulay Library
        "animal_sounds": "https://www.animal-sounds.org",  # Animal Sounds Archive
        "huggingface": "https://huggingface.co/spaces/NailaRajpoot/NatureTrace/resolve/main/assets/sounds/",
        "internet_archive": "https://archive.org/advancedsearch.php"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NatureTrace/1.0 (Educational Research)'
        })
    
    def fetch_sound(self, animal_name: str, max_duration: int = 30, animal_type: str = "unknown") -> Optional[str]:
        """Fetch high-quality animal sound from multiple sources with priority logic"""
        logger.info(f"Fetching sound for {animal_name} (type: {animal_type})")
        
        # Define source priority based on animal type (FreeSound added as backup)
        if "bird" in animal_type.lower() or any(bird_word in animal_name.lower() for bird_word in ["eagle", "owl", "hawk", "robin", "sparrow", "crow", "duck", "goose", "parrot", "canary"]):
            source_priority = ["xeno_canto", "macaulay", "huggingface", "inaturalist", "freesound", "internet_archive"]
        elif "mammal" in animal_type.lower() or any(mammal_word in animal_name.lower() for mammal_word in ["bear", "wolf", "lion", "tiger", "elephant", "whale", "dolphin", "cat", "dog", "horse"]):
            source_priority = ["macaulay", "huggingface", "inaturalist", "freesound", "xeno_canto", "internet_archive"]
        else:
            source_priority = ["huggingface", "macaulay", "inaturalist", "freesound", "xeno_canto", "internet_archive"]
        
        # Try each source in priority order
        for source in source_priority:
            try:
                logger.info(f"Trying source: {source}")
                sound_url = self._query_source(source, animal_name, max_duration)
                if sound_url and self._validate_audio_enhanced(sound_url):
                    logger.info(f"Successfully found sound from {source}: {sound_url}")
                    return sound_url
            except Exception as e:
                logger.warning(f"{source} error: {str(e)}")
                continue
        
        logger.error(f"No valid sound found for {animal_name} from any source")
        return None
    
    def _query_source(self, source: str, animal_name: str, max_duration: int) -> Optional[str]:
        """Query specific source for animal sound"""
        if source == "xeno_canto":
            return self._query_xeno_canto_enhanced(animal_name, max_duration)
        elif source == "inaturalist":
            return self._query_inaturalist(animal_name, max_duration)
        elif source == "freesound":
            return self._query_freesound(animal_name, max_duration)
        elif source == "macaulay":
            return self._query_macaulay(animal_name, max_duration)
        elif source == "huggingface":
            return self._query_huggingface(animal_name, max_duration)
        elif source == "internet_archive":
            return self._query_internet_archive_enhanced(animal_name, max_duration)
        else:
            return None
    
    def _query_xeno_canto_enhanced(self, animal_name: str, max_duration: int) -> Optional[str]:
        """Query Xeno-Canto with enhanced quality filtering"""
        try:
            clean_name = animal_name.replace(" ", "+")
            # First try with quality filter, then without if no results
            urls_to_try = [
                f"https://xeno-canto.org/api/2/recordings?query={clean_name}+q:A,B,C",
                f"https://xeno-canto.org/api/2/recordings?query={clean_name}+q:A,B,C,D",
                f"https://xeno-canto.org/api/2/recordings?query={clean_name}"
            ]
            
            for url in urls_to_try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                recordings = data.get('recordings', [])
                
                if recordings:
                    # Enhanced sorting by quality, length, and rating
                    def quality_score(rec):
                        quality_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'no score': 2}
                        quality = quality_map.get(rec.get('q', 'no score'), 1)
                        
                        # Parse length which can be in formats like "0:50", "2.58", "1.20.53"
                        length_str = rec.get('length', '0')
                        try:
                            if ':' in length_str:
                                # Format: "0:50" (minutes:seconds)
                                parts = length_str.split(':')
                                length = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else 0
                            elif '.' in length_str and length_str.count('.') == 1:
                                # Format: "2.58" (seconds)
                                length = float(length_str)
                            elif '.' in length_str and length_str.count('.') == 2:
                                # Format: "1.20.53" (minutes.seconds.milliseconds)
                                parts = length_str.split('.')
                                length = float(parts[0]) * 60 + float(parts[1]) + float(parts[2])/100 if len(parts) == 3 else 0
                            else:
                                length = float(length_str) if length_str.replace('.', '').isdigit() else 0
                        except:
                            length = 0
                        
                        # Prefer sounds within 1 second for quick identification
                        length_score = 10 if length <= 1 else (5 if length <= 5 else (3 if length <= 30 else 1))
                        
                        # Consider recording type (prefer calls over songs for identification)
                        rec_type = rec.get('type', '').lower()
                        type_score = 3 if 'call' in rec_type else (2 if 'song' in rec_type else 1)
                        
                        return quality * 10 + length_score + type_score
                    
                    recordings.sort(key=quality_score, reverse=True)
                    
                    for recording in recordings[:5]:  # Try top 5 recordings
                        file_url = recording.get('file')
                        if file_url:
                            # Fix URL format
                            if file_url.startswith('//'):
                                clean_url = f"https:{file_url}"
                            elif not file_url.startswith('http'):
                                clean_url = f"https://{file_url}"
                            else:
                                clean_url = file_url
                            
                            # Validate duration
                            length_str = recording.get('length', '0')
                            try:
                                if ':' in length_str:
                                    # Format: "0:50" (minutes:seconds)
                                    parts = length_str.split(':')
                                    length = float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else 0
                                elif '.' in length_str and length_str.count('.') == 1:
                                    # Format: "2.58" (seconds)
                                    length = float(length_str)
                                elif '.' in length_str and length_str.count('.') == 2:
                                    # Format: "1.20.53" (minutes.seconds.milliseconds)
                                    parts = length_str.split('.')
                                    length = float(parts[0]) * 60 + float(parts[1]) + float(parts[2])/100 if len(parts) == 3 else 0
                                else:
                                    length = float(length_str) if length_str.replace('.', '').isdigit() else 0
                            except:
                                length = 0
                            
                            if length <= max_duration:
                                logger.info(f"Xeno-Canto found: {recording.get('en', 'Unknown')} (Q:{recording.get('q', 'no score')}, {length}s)")
                                return clean_url
                    
                    # If we found recordings but none met duration criteria, break to try next URL
                    break
            
            return None
            
        except Exception as e:
            logger.error(f"Xeno-Canto enhanced query error: {str(e)}")
            return None
    
    def _query_inaturalist(self, animal_name: str, max_duration: int) -> Optional[str]:
        """Query iNaturalist for observations with sounds using enhanced filtering"""
        try:
            # Use the enhanced approach with specific filters for audio
            url = "https://api.inaturalist.org/v1/observations"
            params = {
                "taxon_name": animal_name,
                "has[]": "sounds",  # Key filter for audio - only observations with sounds
                "quality_grade": "research",  # Verified observations only
                "order": "desc",  # Newest first
                "order_by": "created_at",  # Get recent recordings first
                "per_page": 20  # Get multiple options
            }
            
            logger.info(f"Querying iNaturalist for sounds: {animal_name}")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get('results', [])
            
            # Sort observations by sound quality/relevance
            for observation in observations:
                sounds = observation.get('sounds', [])
                if sounds:
                    # Try each sound in the observation
                    for sound in sounds:
                        file_url = sound.get('file_url')
                        if not file_url:
                            # Try alternative URL field
                            file_url = sound.get('url')
                        
                        if file_url:
                            # Validate it's an audio file
                            if file_url.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.aac')):
                                # Additional metadata available from iNaturalist
                                license_code = sound.get('license_code', '')
                                attribution = sound.get('attribution', '')
                                
                                logger.info(f"iNaturalist found sound: {file_url} (License: {license_code})")
                                return file_url
                            
                            # Even if extension not clear, try the URL if it looks like audio
                            if any(audio_hint in file_url.lower() for audio_hint in ['sound', 'audio', 'mp3', 'wav', 'ogg']):
                                logger.info(f"iNaturalist found potential sound: {file_url}")
                                return file_url
            
            logger.info(f"No sounds found for {animal_name} in iNaturalist")
            return None
            
        except Exception as e:
            logger.error(f"iNaturalist query error: {str(e)}")
            return None
    
    def _query_freesound(self, animal_name: str, max_duration: int) -> Optional[str]:
        """Query FreeSound.org for animal sounds using the integrated client"""
        try:
            # Use the FreeSound client
            sound_url = freesound_client.get_best_animal_sound(animal_name, max_duration)
            
            if sound_url:
                logger.info(f"FreeSound found sound for {animal_name}: {sound_url[:50]}...")
                return sound_url
            else:
                logger.info(f"No sound found for {animal_name} on FreeSound")
                return None
                
        except Exception as e:
            logger.error(f"FreeSound query error: {str(e)}")
            return None
    
    def _query_macaulay(self, animal_name: str, max_duration: int) -> Optional[str]:
        """Query Macaulay Library (Cornell) for high-quality recordings"""
        try:
            # Macaulay Library search with better filtering
            params = {
                'q': animal_name,
                'mediaType': 'audio',
                'sort': 'rating_rank_desc',
                'count': 50  # Get more results to find better matches
            }
            
            response = self.session.get(
                "https://search.macaulaylibrary.org/api/v1/search",
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', {}).get('content', [])
                
                # Score and sort results by relevance
                scored_results = []
                animal_lower = animal_name.lower()
                
                for result in results:
                    if result.get('mediaType') == 'Audio':
                        asset_id = result.get('assetId')
                        common_name = result.get('commonName', '').lower()
                        scientific_name = result.get('sciName', '').lower()
                        
                        if asset_id:
                            # Calculate relevance score
                            score = 0
                            
                            # Exact match in common name gets highest score
                            if animal_lower == common_name:
                                score += 100
                            elif animal_lower in common_name:
                                score += 80
                            elif any(word in common_name for word in animal_lower.split()):
                                score += 50
                            
                            # Check scientific name too
                            if animal_lower in scientific_name:
                                score += 30
                            
                            # Quality indicators
                            rating = result.get('rating', 0)
                            if rating and str(rating).replace('.', '').isdigit():
                                score += min(float(rating) * 10, 50)  # Max 50 points for rating
                            
                            # Prefer calls over songs for identification
                            behavior = result.get('behavior', '').lower()
                            if 'call' in behavior:
                                score += 20
                            elif 'song' in behavior:
                                score += 10
                            
                            if score > 0:
                                scored_results.append((score, asset_id, common_name))
                
                # Sort by score and return best match
                if scored_results:
                    scored_results.sort(reverse=True)
                    best_asset_id = scored_results[0][1]
                    best_name = scored_results[0][2]
                    
                    # Construct download URL
                    audio_url = f"https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{best_asset_id}/audio"
                    logger.info(f"Macaulay Library found: {best_name} (asset: {best_asset_id})")
                    return audio_url
            
            return None
            
        except Exception as e:
            logger.error(f"Macaulay Library query error: {str(e)}")
            return None
    
    def _query_huggingface(self, animal_name: str, max_duration: int) -> Optional[str]:
        """Query Hugging Face assets with enhanced logic"""
        try:
            animal_name_clean = animal_name.lower().strip().replace(" ", "_")
            hf_base = self.SOURCES["huggingface"]
            
            # Try multiple variations and formats
            variations = [
                animal_name_clean,
                animal_name.lower().replace(" ", "-"),
                animal_name.lower().replace(" ", "")
            ]
            
            for variation in variations:
                for ext in [".mp3", ".wav", ".ogg", ".m4a"]:
                    hf_url = f"{hf_base}{variation}{ext}"
                    try:
                        response = self.session.head(hf_url, timeout=5)
                        if response.status_code == 200:
                            return hf_url
                    except:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Hugging Face query error: {str(e)}")
            return None
    
    def _query_internet_archive_enhanced(self, animal_name: str, max_duration: int) -> Optional[str]:
        """Enhanced Internet Archive query with better filtering for actual animal sounds"""
        try:
            encoded_name = quote(animal_name)
            # Enhanced search with more specific terms for animal sounds
            sound_terms = ["sound", "call", "vocalization", "audio", "nature", "wildlife", "animal"]
            exclude_terms = ["podcast", "lecture", "talk", "interview", "music", "song", "album", "radio", "show", "documentary", "story", "book", "history", "culture", "human", "speech"]
            
            # Build more targeted search query
            sound_query = f"({'+OR+'.join(sound_terms)})"
            exclude_query = f"NOT+({'+OR+'.join(exclude_terms)})"
            search_url = f"https://archive.org/advancedsearch.php?q={encoded_name}+AND+{sound_query}+AND+{exclude_query}+AND+mediatype%3Aaudio&fl[]=identifier,title,description&output=json&rows=10"
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            docs = response.json().get("response", {}).get("docs", [])
            
            for doc in docs:
                identifier = doc["identifier"]
                title = doc.get("title", "").lower()
                description = doc.get("description", [""])[0].lower() if isinstance(doc.get("description"), list) else doc.get("description", "").lower()
                
                # Additional filtering based on title and description
                exclude_keywords = ["podcast", "lecture", "talk", "interview", "radio", "show", "documentary", "story", "book", "history", "culture", "human", "speech", "music", "album", "song"]
                include_keywords = ["sound", "call", "vocalization", "nature", "wildlife", "animal", "bird", "mammal", "recording"]
                
                # Skip if title or description contains excluded keywords
                if any(keyword in title or keyword in description for keyword in exclude_keywords):
                    logger.info(f"Skipping {identifier} - contains excluded keywords in title/description")
                    continue
                
                # Prefer items with included keywords
                has_good_keywords = any(keyword in title or keyword in description for keyword in include_keywords)
                if not has_good_keywords:
                    logger.info(f"Skipping {identifier} - no relevant keywords found")
                    continue
                
                # Get detailed metadata
                try:
                    details_url = f"https://archive.org/metadata/{identifier}"
                    details_resp = self.session.get(details_url, timeout=10)
                    if details_resp.ok:
                        metadata = details_resp.json()
                        
                        # Find appropriate audio files (prefer shorter files for animal sounds)
                        audio_files = []
                        for file_info in metadata.get("files", []):
                            filename = file_info.get("name", "").lower()
                            if filename.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                                # Skip if filename suggests non-animal content
                                if any(exclude in filename for exclude in ["podcast", "lecture", "talk", "interview", "radio", "music", "song"]):
                                    continue
                                    
                                size = file_info.get("size", "0")
                                file_size = int(size) if size.isdigit() else 0
                                
                                # Prefer smaller files (likely short animal sounds rather than long recordings)
                                # Skip very large files that are likely not animal sounds
                                if 0 < file_size < 50 * 1024 * 1024:  # Under 50MB
                                    audio_files.append((filename, file_size))
                        
                        # Sort by file size (prefer smaller files for shorter duration)
                        audio_files.sort(key=lambda x: x[1])
                        
                        if audio_files:
                            best_file = audio_files[0][0]
                            download_url = f"https://archive.org/download/{identifier}/{best_file}"
                            logger.info(f"Found potential animal sound: {download_url}")
                            return download_url
                
                except Exception as e:
                    logger.warning(f"Internet Archive metadata error for {identifier}: {str(e)}")
                    continue
            
            logger.info(f"No suitable animal sounds found for {animal_name} in Internet Archive")
            return None
            
        except Exception as e:
            logger.error(f"Internet Archive enhanced query error: {str(e)}")
            return None
    
    def _validate_audio_enhanced(self, url: str) -> bool:
        """Enhanced audio validation with quality checks"""
        try:
            # First, try HEAD request
            response = self.session.head(url, timeout=10, allow_redirects=True)
            
            if response.status_code not in [200, 206]:
                # Try GET with range header if HEAD fails
                headers = {'Range': 'bytes=0-1023'}
                response = self.session.get(url, headers=headers, timeout=10, allow_redirects=True)
            
            if response.status_code in [200, 206]:
                content_type = response.headers.get('content-type', '').lower()
                content_length = response.headers.get('content-length')
                
                # Check for audio content types
                audio_types = [
                    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 
                    'audio/mp4', 'audio/aac', 'audio/flac', 'audio/webm'
                ]
                
                is_audio = (
                    any(audio_type in content_type for audio_type in audio_types) or
                    any(url.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac'])
                )
                
                if is_audio:
                    # Additional quality checks
                    if content_length:
                        file_size_mb = int(content_length) / (1024 * 1024)
                        # Reject files that are too large (likely not short animal sounds)
                        if file_size_mb > 50:  # 50MB limit
                            logger.warning(f"File too large: {file_size_mb:.2f}MB")
                            return False
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Enhanced audio validation error for {url}: {str(e)}")
            return False

# Create global instance
sound_fetcher = AnimalSoundFetcher()

def save_sound_url_to_database(animal_name: str, sound_url: str, source: str) -> bool:
    """
    Save a valid sound URL to the database for future use
    
    Args:
        animal_name: Name of the animal
        sound_url: The sound URL to save
        source: Source of the sound (xeno_canto, inaturalist, etc.)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from utils.data_utils import update_animal_sound_url
        
        # Use the enhanced update function from data_utils
        result = update_animal_sound_url(
            animal_name=animal_name,
            sound_url=sound_url,
            source=source
        )
        
        if result["success"]:
            logger.info(f"Successfully saved sound URL for {animal_name}: {sound_url}")
            return True
        else:
            logger.error(f"Failed to save sound URL for {animal_name}: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to save sound URL to database: {e}")
        if 'st' in globals():
            st.error(f"Failed to save sound URL to database: {e}")
        return False

def batch_update_sounds_for_dashboard():
    """
    Update sound URLs for all animals in the dashboard that don't have sounds
    
    Returns:
        dict: Summary of the batch update process
    """
    try:
        from utils.data_utils import bulk_update_missing_sounds
        
        logger.info("Starting batch sound update for dashboard animals...")
        result = bulk_update_missing_sounds(limit=50)  # Process up to 50 at a time
        
        logger.info(f"Batch update completed: {result['successful']}/{result['total_processed']} successful")
        return result
        
    except Exception as e:
        logger.error(f"Batch sound update failed: {e}")
        return {"total_processed": 0, "successful": 0, "failed": 0, "results": []}

def generate_animal_sound(animal_name: str, animal_type: str = "unknown") -> str:
    """
    Enhanced animal sound generation using the new multi-source fetcher
    """
    try:
        # Use the enhanced fetcher with animal type for better source prioritization
        sound_url = sound_fetcher.fetch_sound(animal_name, max_duration=30, animal_type=animal_type)
        return sound_url if sound_url else ""
    except Exception as e:
        logger.error(f"Error generating animal sound for {animal_name}: {str(e)}")
        return ""

def validate_sound_url(url: str) -> Dict[str, Any]:
    """
    Validate if a sound URL is accessible and get metadata
    Returns dict with status, duration_estimate, file_size, etc.
    """
    if not url:
        return {"valid": False, "error": "Empty URL"}
    
    try:
        # Make a HEAD request to check if URL is accessible, following redirects
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        # If HEAD fails, try GET with range header to minimize download
        if response.status_code != 200:
            headers = {'Range': 'bytes=0-1023'}  # Only get first 1KB
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code in [200, 206]:  # 206 for partial content
            content_length = response.headers.get('content-length')
            content_type = response.headers.get('content-type', '').lower()
            
            # Check if it's an audio file
            is_audio = (
                any(audio_type in content_type for audio_type in ['audio/', 'application/octet-stream']) or
                url.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac'))
            )
            
            if is_audio:
                # Estimate duration based on file size (rough estimate for MP3)
                duration_estimate = None
                file_size_mb = None
                if content_length:
                    try:
                        file_size_mb = int(content_length) / (1024 * 1024)
                        # Rough estimate: assume 128kbps MP3 = ~1MB per minute
                        # So duration in seconds = (file_size_mb * 8 * 1024) / 128
                        duration_estimate = round((file_size_mb * 8 * 1024) / 128, 1)
                    except:
                        pass
                
                return {
                    "valid": True,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "file_size_bytes": content_length,
                    "file_size_mb": round(file_size_mb, 2) if file_size_mb else None,
                    "duration_estimate_seconds": duration_estimate,
                    "url": response.url  # Use final URL after redirects
                }
            else:
                return {"valid": False, "error": f"Not an audio file (content-type: {content_type})", "url": response.url}
        else:
            return {"valid": False, "error": f"HTTP {response.status_code}", "url": response.url if hasattr(response, 'url') else url}
    except Exception as e:
        return {"valid": False, "error": str(e), "url": url}

def test_multiple_sound_sources(animal_name: str, animal_type: str = "unknown") -> Dict[str, Any]:
    """
    Enhanced testing of all available sound sources using the new fetcher
    """
    results = {
        "animal": animal_name,
        "animal_type": animal_type,
        "sources": {},
        "best_url": None,
        "best_source": None,
        "attempted_urls": []
    }
    
    # Test each source individually using the enhanced fetcher
    for source_name in sound_fetcher.SOURCES.keys():
        try:
            logger.info(f"Testing source: {source_name}")
            sound_url = sound_fetcher._query_source(source_name, animal_name, 30)
            
            if sound_url:
                results["attempted_urls"].append({"source": source_name, "url": sound_url})
                validation = validate_sound_url(sound_url)
                validation["source"] = source_name
                results["sources"][source_name] = validation
                
                if validation["valid"] and not results["best_url"]:
                    results["best_url"] = sound_url
                    results["best_source"] = source_name
            else:
                results["sources"][source_name] = {
                    "valid": False, 
                    "error": "No URL returned from source",
                    "source": source_name
                }
                
        except Exception as e:
            results["sources"][source_name] = {
                "valid": False, 
                "error": str(e),
                "source": source_name
            }
    
    # Add quality scoring
    if results["best_url"]:
        best_validation = results["sources"][results["best_source"]]
        duration = best_validation.get("duration_estimate_seconds")
        file_size = best_validation.get("file_size_mb")
        
        quality_score = 0
        if duration and duration <= 1:
            quality_score += 5  # Highest score for sounds within 1 second
        elif duration and duration <= 5:
            quality_score += 3
        elif duration and duration <= 30:
            quality_score += 2
        
        if file_size and file_size < 2:  # Prefer smaller files (likely shorter)
            quality_score += 3
        elif file_size and file_size < 5:
            quality_score += 2
        
        results["quality_score"] = quality_score
        results["meets_1_second_requirement"] = duration and duration <= 1 if duration else "unknown"
    
    return results

def fetch_clean_animal_sound(animal_name: str, animal_type: str = "unknown") -> Dict[str, Any]:
    """
    Fetch animal sound and automatically remove human speech if detected
    """
    try:
        # First, get the best sound from multiple sources
        sound_results = test_multiple_sound_sources(animal_name, animal_type)
        
        if not sound_results.get('best_url'):
            return {
                "success": False,
                "message": "No sound sources found",
                "original_url": None,
                "processed_url": None,
                "analysis": None
            }
        
        original_url = sound_results['best_url']
        source = sound_results['best_source']
        
        # If audio processing is available, analyze and clean the audio
        if AUDIO_PROCESSING_AVAILABLE:
            logger.info(f"Analyzing audio content for {animal_name}")
            
            # Analyze the audio to detect speech content
            analysis = audio_processor.analyze_audio_content(original_url, animal_name)
            
            # If significant speech detected, process to remove it
            if analysis.get('speech_ratio', 0) > 0.3:  # More than 30% speech
                logger.info(f"High speech content detected ({analysis['speech_ratio']:.1%}) - processing audio")
                processed_url = audio_processor.process_audio_remove_speech(original_url, animal_name)
                
                if processed_url:
                    return {
                        "success": True,
                        "message": f"Sound processed to remove speech from {source}",
                        "original_url": original_url,
                        "processed_url": processed_url,
                        "source": source,
                        "analysis": analysis,
                        "speech_removed": True
                    }
            
            # If low speech content or processing failed, use original
            return {
                "success": True,
                "message": f"Clean animal sound from {source}",
                "original_url": original_url,
                "processed_url": original_url,  # Same as original
                "source": source,
                "analysis": analysis,
                "speech_removed": False
            }
        else:
            # Audio processing not available, return original
            return {
                "success": True,
                "message": f"Sound from {source} (processing not available)",
                "original_url": original_url,
                "processed_url": original_url,
                "source": source,
                "analysis": None,
                "speech_removed": False
            }
            
    except Exception as e:
        logger.error(f"Error in fetch_clean_animal_sound: {e}")
        return {
            "success": False,
            "message": f"Error processing sound: {str(e)}",
            "original_url": None,
            "processed_url": None,
            "analysis": None
        }

def prioritize_inaturalist_for_mammals(animal_name: str, animal_type: str = "unknown") -> Optional[str]:
    """
    Special function to prioritize iNaturalist for mammals like Bobcat
    since it's more reliable than Macaulay Library for certain species
    """
    logger.info(f"Prioritizing iNaturalist for {animal_name}")
    
    # Create fetcher instance
    fetcher = AnimalSoundFetcher()
    
    # Try iNaturalist first for mammals
    if "mammal" in animal_type.lower() or any(mammal in animal_name.lower() 
                                             for mammal in ["bobcat", "lynx", "cat", "bear", "wolf", "coyote"]):
        try:
            sound_url = fetcher._query_inaturalist(animal_name, max_duration=30)
            if sound_url and fetcher._validate_audio_enhanced(sound_url):
                logger.info(f"Found clean sound from iNaturalist for {animal_name}")
                return sound_url
        except Exception as e:
            logger.warning(f"iNaturalist failed for {animal_name}: {e}")
    
    # Fallback to other sources with speech processing
    result = fetch_clean_animal_sound(animal_name, animal_type)
    return result.get('processed_url') if result.get('success') else None

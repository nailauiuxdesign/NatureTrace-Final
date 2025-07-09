# � NatureTrace - Advanced Animal Discovery Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/framework-Streamlit-red.svg)](https://streamlit.io/)

> **An intelligent wildlife recognition and tracking platform that combines cutting-edge AI with real-time data analytics to help you discover and learn about animals in their natural habitats.**

## ⭐ Features

### 🔍 **Enhanced Image Recognition**
- **Dual AI Analysis**: Combines custom YOLO models with Azure Computer Vision for superior accuracy
- **Intelligent Comparison**: Uses Groq AI to compare results and handle conflicting detections
- **Duplicate Detection**: Smart image deduplication to prevent redundant entries
- **User Choice Interface**: When AI models disagree, presents options for user verification

### �️ **Interactive Mapping**
- **Real-time Location Tracking**: GPS-based animal sighting visualization
- **Category-based Color Coding**: Visual distinction between mammals, birds, reptiles, etc.
- **Google Maps Integration**: Seamless mapping with custom markers and info windows
- **Location Analytics**: Habitat distribution and migration pattern insights

### 🎵 **Multi-source Audio Integration**
- **Diverse Sound Libraries**: Integration with FreeSound, Xeno-Canto, and Macaulay Library
- **Intelligent Sound Matching**: Animal-specific audio based on classification
- **Fallback Systems**: Multiple API sources ensure sound availability
- **Audio Quality Control**: Duration and quality filtering for optimal user experience

### 📊 **Advanced Dashboard & Analytics**
- **Real-time Data Visualization**: Live charts and statistics
- **Snowflake Integration**: Enterprise-grade data warehousing
- **Export Capabilities**: Data download in multiple formats
- **Temporal Analysis**: Track animal sightings over time

### 🤖 **AI-Powered Insights**
- **YOLO v8 Integration**: State-of-the-art object detection
- **Azure Computer Vision**: Cloud-based recognition with high confidence scoring
- **Groq AI Analysis**: Intelligent comparison and decision-making
- **Continuous Learning**: Model improvement through user feedback

## 🛠️ Technology Stack

### **Backend & AI**
- **Python 3.8+** - Core application logic
- **Streamlit** - Web application framework
- **YOLOv8** - Object detection and classification
- **Azure Computer Vision** - Cloud-based image analysis
- **Groq AI** - Intelligent comparison and reasoning

### **Data & Storage**
- **Snowflake** - Cloud data warehouse
- **Pandas** - Data manipulation and analysis
- **PIL/OpenCV** - Image processing
- **NumPy** - Numerical computations

### **APIs & Services**
- **Google Maps API** - Interactive mapping
- **FreeSound API** - Animal audio library
- **Xeno-Canto** - Bird sound database
- **Macaulay Library** - Cornell Lab audio collection

## ⚙ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Git
- Required API keys (see Configuration section)

### 1. Clone the Repository
```bash
git clone https://github.com/FloraWebDesigner/NatureTrace-Python.git
cd NatureTrace-Python
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create `.streamlit/secrets.toml` with your API keys:
```toml
# AI & Language Models
groq_api_key = "your_groq_api_key"

# Computer Vision
AZURE_COMPUTER_VISION_ENDPOINT = "your_azure_endpoint"
AZURE_COMPUTER_VISION_KEY = "your_azure_key"

# Google Services
google_maps_key = "your_google_maps_key"

# Database
snowflake_account = "your_snowflake_account"
snowflake_user = "your_username"
snowflake_password = "your_password"
snowflake_warehouse = "your_warehouse"
snowflake_database = "your_database"
snowflake_schema = "your_schema"
snowflake_role = "your_role"

# Optional: Sound APIs
freesound_api_key = "your_freesound_key"
macaulay_api_key = "your_macaulay_key"
```

### 5. Run the Application
```bash
streamlit run app.py
```

## 📖 Usage Guide

### **Image Upload & Recognition**
1. **Upload Image**: Drag and drop or browse for animal photos
2. **AI Analysis**: Dual AI systems analyze the image automatically
3. **Review Results**: If models agree, result is displayed; if they differ, choose from options
4. **Confirm & Save**: Add verified detection to your dashboard

### **Dashboard Analytics**
- View real-time statistics and charts
- Filter by animal categories, time periods, or locations
- Export data for further analysis
- Track your discovery progress

### **Interactive Mapping**
- Explore animal sightings on an interactive map
- Click markers for detailed information
- Filter by animal types using color-coded categories
- Analyze habitat distributions and patterns

### **Audio Experience**
- Listen to authentic animal sounds
- Multiple audio sources ensure availability
- High-quality, curated sound libraries
- Educational audio descriptions

## 🏗️ Project Structure

```
NatureTrace/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .streamlit/
│   └── secrets.toml      # Configuration file
├── utils/                # Utility modules
│   ├── image_utils.py    # Image processing functions
│   ├── azure_vision.py   # Azure Computer Vision integration
│   ├── groq_comparison.py # AI comparison logic
│   ├── enhanced_image_processing.py # Enhanced recognition pipeline
│   ├── map_utils.py      # Google Maps integration
│   ├── sound_utils.py    # Audio processing
│   ├── data_utils.py     # Database operations
│   └── freesound_client.py # FreeSound API client
├── agents/               # AI agent modules
│   ├── sound_orchestrator.py
│   ├── bird_sound_agent.py
│   ├── mammal_sound_agent.py
│   └── fallback_sound_agent.py
└── test_*.py            # Test scripts and validation
```

## 🤝 Contributing

We welcome contributions! Please feel free to submit pull requests, report bugs, or suggest new features.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit with descriptive messages
5. Push to your fork and submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **YOLOv8** by Ultralytics for object detection
- **Azure Computer Vision** for cloud-based image analysis
- **Groq** for AI reasoning and comparison
- **FreeSound.org** for Creative Commons audio content
- **Xeno-Canto** for bird sound database
- **Cornell Lab's Macaulay Library** for scientific audio recordings
- **Snowflake** for enterprise data warehousing

## 📞 Support

For questions, suggestions, or support:
- 📧 Create an issue on GitHub
- 🌐 Check out the [live demo](https://huggingface.co/spaces/NatureTraceHack/NatureTrace)

---

**Built with ❤️ for wildlife conservation and education**

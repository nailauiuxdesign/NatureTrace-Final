# 🔐 Secrets Configuration

This directory contains secret configuration files that are **NOT** committed to git for security reasons.

## Setup Instructions

1. **Copy the template file:**
   ```bash
   cp secrets.toml.example secrets.toml
   ```

2. **Edit `secrets.toml`** and replace all placeholder values with your actual API keys:
   - Groq API Key (get from https://groq.com/)
   - Azure Computer Vision credentials
   - Google Maps API key
   - Snowflake database credentials
   - FreeSound API key (get from https://freesound.org/apiv2/apply/)

3. **Never commit `secrets.toml`** - it's already in `.gitignore`

## For Streamlit Cloud Deployment

When deploying to Streamlit Cloud, add these secrets in the app settings dashboard instead of using this file.

## Security Note

⚠️ **IMPORTANT**: Never commit actual API keys or passwords to git. Always use:
- Environment variables for local development
- Streamlit Cloud secrets for deployment
- This template file for documentation

# Google Docs Upload Setup

## Quick Setup (5 minutes)

### 1. Enable Google Docs API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "Google Docs API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Desktop Application"
6. Download the JSON file and rename it to `credentials.json`
7. Place `credentials.json` in the project root directory

### 2. Install Dependencies
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client markdown
```

### 3. Run the Upload
```bash
python utilities/google_docs_uploader.py
```

**First time:** Browser will open for Google authentication
**After that:** Automatic uploads with shareable links!

## Usage

The script will:
- ✅ Create a new Google Doc with timestamp
- ✅ Upload your analysis report with formatting
- ✅ Generate a shareable read-only link
- ✅ Anyone with the link can view (but not edit)

## Example Output
```
📤 Uploading Lyft QA Analysis to Google Docs...
📄 Created Google Doc: Lyft QA Analysis Report - 2025-06-13 15:30
🔗 Document ID: 1BxiMVs3WOBk7DhQUOFZd1gEEK8rGhysOAQz_example
✅ Successfully uploaded to Google Docs!
🔗 URL: https://docs.google.com/document/d/1BxiMVs3WOBk7DhQUOFZd1gEEK8rGhysOAQz_example/edit
📤 Share this link for read-only access
```
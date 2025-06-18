#!/usr/bin/env python3
"""
Google Docs Uploader - Upload analysis reports to Google Docs for easy sharing
"""

import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import markdown

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents']

def authenticate_google_docs():
    """Authenticate and return Google Docs service"""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('docs', 'v1', credentials=creds)
    return service

def create_google_doc(service, title, content):
    """Create a new Google Doc with the given title and content"""
    
    # Create the document
    document = {
        'title': title
    }
    
    doc = service.documents().create(body=document).execute()
    document_id = doc.get('documentId')
    
    print(f"📄 Created Google Doc: {title}")
    print(f"🔗 Document ID: {document_id}")
    
    # Prepare content for insertion
    # Split content into lines and create requests
    requests = []
    
    lines = content.split('\n')
    text_to_insert = '\n'.join(lines)
    
    # Insert all text at once
    requests.append({
        'insertText': {
            'location': {
                'index': 1,
            },
            'text': text_to_insert
        }
    })
    
    # Apply formatting for headers
    line_index = 1
    for line in lines:
        line_length = len(line)
        if line.startswith('# '):
            # Main title
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': line_index,
                        'endIndex': line_index + line_length
                    },
                    'textStyle': {
                        'fontSize': {'magnitude': 18, 'unit': 'PT'},
                        'bold': True
                    },
                    'fields': 'fontSize,bold'
                }
            })
        elif line.startswith('## '):
            # Section headers
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': line_index,
                        'endIndex': line_index + line_length
                    },
                    'textStyle': {
                        'fontSize': {'magnitude': 14, 'unit': 'PT'},
                        'bold': True
                    },
                    'fields': 'fontSize,bold'
                }
            })
        elif line.startswith('### '):
            # Subsection headers
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': line_index,
                        'endIndex': line_index + line_length
                    },
                    'textStyle': {
                        'fontSize': {'magnitude': 12, 'unit': 'PT'},
                        'bold': True
                    },
                    'fields': 'fontSize,bold'
                }
            })
        elif '**' in line:
            # Bold text
            start_bold = line.find('**')
            end_bold = line.find('**', start_bold + 2)
            if start_bold != -1 and end_bold != -1:
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': line_index + start_bold,
                            'endIndex': line_index + end_bold + 2
                        },
                        'textStyle': {
                            'bold': True
                        },
                        'fields': 'bold'
                    }
                })
        
        line_index += line_length + 1  # +1 for newline
    
    # Execute all formatting requests
    if requests:
        result = service.documents().batchUpdate(
            documentId=document_id, body={'requests': requests}).execute()
    
    # Generate shareable link
    doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
    
    return document_id, doc_url

def upload_analysis_report(report_path=None):
    """Upload the analysis report to Google Docs"""
    
    if not report_path:
        # Default to the latest analysis report
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        report_path = os.path.join(project_dir, 'results', 'analysis_summary.md')
    
    if not os.path.exists(report_path):
        print(f"❌ Report not found: {report_path}")
        return None, None
    
    # Read the report content
    with open(report_path, 'r') as f:
        content = f.read()
    
    # Generate title with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    title = f"Lyft QA Analysis Report - {timestamp}"
    
    try:
        # Authenticate and create document
        service = authenticate_google_docs()
        document_id, doc_url = create_google_doc(service, title, content)
        
        print(f"✅ Successfully uploaded to Google Docs!")
        print(f"📄 Title: {title}")
        print(f"🔗 URL: {doc_url}")
        print(f"📤 Share this link for read-only access")
        
        return document_id, doc_url
        
    except Exception as e:
        print(f"❌ Failed to upload to Google Docs: {e}")
        print("💡 Make sure you have:")
        print("   1. Google API credentials (credentials.json)")
        print("   2. Enabled Google Docs API in your project")
        return None, None

def main():
    """Main upload workflow"""
    print("📤 Uploading Lyft QA Analysis to Google Docs...")
    
    document_id, doc_url = upload_analysis_report()
    
    if doc_url:
        print(f"\n🎉 Upload complete!")
        print(f"🔗 Share this URL: {doc_url}")
    else:
        print(f"\n❌ Upload failed")

if __name__ == "__main__":
    main()
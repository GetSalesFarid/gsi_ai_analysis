"""
Archive Manager

Automatically archives previous analysis results with timestamp folders
and maintains clean results directory.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def archive_results():
    """
    Archive previous results to timestamped folder
    """
    print("📁 Archiving previous results...")
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    results_dir = os.path.join(project_root, 'results')
    archived_dir = os.path.join(results_dir, 'archived')
    
    # Create directories if they don't exist
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(archived_dir, exist_ok=True)
    
    # Check if there are existing results to archive
    existing_files = []
    for file in os.listdir(results_dir):
        if file != 'archived' and not file.startswith('.'):
            existing_files.append(file)
    
    if not existing_files:
        print("ℹ️ No previous results to archive")
        return
    
    # Create timestamp folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_folder = os.path.join(archived_dir, f'analysis_{timestamp}')
    os.makedirs(archive_folder, exist_ok=True)
    
    # Move existing files to archive
    for file in existing_files:
        src = os.path.join(results_dir, file)
        dst = os.path.join(archive_folder, file)
        
        if os.path.isfile(src):
            shutil.move(src, dst)
        elif os.path.isdir(src):
            shutil.move(src, dst)
    
    print(f"✅ Results archived to: analysis_{timestamp}")
    
    # Clean up old archives (keep only 5 most recent)
    cleanup_old_archives(archived_dir)

def cleanup_old_archives(archived_dir, keep_count=5):
    """
    Remove old archive folders, keeping only the most recent ones
    """
    archive_folders = []
    
    # Get all archive folders
    for item in os.listdir(archived_dir):
        item_path = os.path.join(archived_dir, item)
        if os.path.isdir(item_path) and item.startswith('analysis_'):
            archive_folders.append(item)
    
    # Sort by timestamp (newest first)
    archive_folders.sort(reverse=True)
    
    # Remove old archives
    if len(archive_folders) > keep_count:
        for old_archive in archive_folders[keep_count:]:
            old_path = os.path.join(archived_dir, old_archive)
            shutil.rmtree(old_path)
            print(f"🗑️ Removed old archive: {old_archive}")

if __name__ == "__main__":
    archive_results()
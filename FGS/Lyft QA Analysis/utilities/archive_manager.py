#!/usr/bin/env python3
"""
Archive Manager - Automatically archives old results and keeps results folder clean
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import glob

class ArchiveManager:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.archive_dir = self.results_dir / "archived"
        
        # Create directories if they don't exist
        self.results_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
    
    def archive_existing_results(self):
        """Move existing results to archived folder with timestamp"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Find all files in results directory (excluding archived folder)
        result_files = []
        for file_path in self.results_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                result_files.append(file_path)
        
        if not result_files:
            print("📁 No existing results to archive")
            return
        
        # Create timestamped archive folder
        archive_timestamp_dir = self.archive_dir / f"analysis_{timestamp}"
        archive_timestamp_dir.mkdir(exist_ok=True)
        
        print(f"📦 Archiving {len(result_files)} files to {archive_timestamp_dir}")
        
        # Move each file to archive
        for file_path in result_files:
            destination = archive_timestamp_dir / file_path.name
            shutil.move(str(file_path), str(destination))
            print(f"   Moved: {file_path.name}")
        
        print(f"✅ Results archived to: {archive_timestamp_dir}")
        return archive_timestamp_dir
    
    def clean_old_archives(self, keep_count=5):
        """Keep only the most recent N archived analyses"""
        
        # Get all archive directories
        archive_dirs = [d for d in self.archive_dir.iterdir() if d.is_dir() and d.name.startswith('analysis_')]
        
        if len(archive_dirs) <= keep_count:
            print(f"📚 {len(archive_dirs)} archives found, keeping all (limit: {keep_count})")
            return
        
        # Sort by creation time (newest first)
        archive_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old archives
        archives_to_remove = archive_dirs[keep_count:]
        
        print(f"🗑️  Removing {len(archives_to_remove)} old archives (keeping {keep_count} most recent)")
        
        for archive_dir in archives_to_remove:
            shutil.rmtree(archive_dir)
            print(f"   Removed: {archive_dir.name}")
    
    def list_archives(self):
        """List all archived analyses"""
        
        archive_dirs = [d for d in self.archive_dir.iterdir() if d.is_dir() and d.name.startswith('analysis_')]
        archive_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not archive_dirs:
            print("📁 No archived analyses found")
            return
        
        print(f"📚 Found {len(archive_dirs)} archived analyses:")
        for i, archive_dir in enumerate(archive_dirs, 1):
            timestamp = datetime.fromtimestamp(archive_dir.stat().st_mtime)
            files = list(archive_dir.glob("*"))
            print(f"   {i}. {archive_dir.name} ({timestamp.strftime('%Y-%m-%d %H:%M')}) - {len(files)} files")
    
    def prepare_for_new_analysis(self):
        """Complete workflow: archive existing results and clean old archives"""
        
        print("🔄 Preparing for new analysis...")
        
        # Archive existing results
        self.archive_existing_results()
        
        # Clean old archives (keep last 5)
        self.clean_old_archives(keep_count=5)
        
        print("✅ Results directory ready for new analysis")

def main():
    """Test the archive manager"""
    manager = ArchiveManager()
    
    print("Archive Manager Test")
    print("=" * 50)
    
    # List current archives
    manager.list_archives()
    
    # Prepare for new analysis
    manager.prepare_for_new_analysis()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Main runner script for Lyft QA Analysis
Handles proper paths and executes the complete analysis workflow
"""

import os
import sys
import subprocess
from pathlib import Path

def run_complete_analysis():
    """Run the complete Lyft QA analysis workflow"""
    
    print("🚀 Starting Lyft QA Analysis Workflow")
    print("=" * 50)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Fetch data from BigQuery
    print("📊 Step 1: Fetching opportunity data from BigQuery...")
    result = subprocess.run([sys.executable, "data_loaders/bigquery_manual_loader.py"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ BigQuery opportunity data loading failed:")
        print(result.stderr)
        return False
    
    print("✅ BigQuery opportunity data loaded successfully")
    
    # Step 1b: Fetch task data from BigQuery
    print("\n📱 Step 1b: Fetching task/communication data from BigQuery...")
    result = subprocess.run([sys.executable, "data_loaders/bigquery_task_loader.py"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ BigQuery task data loading failed:")
        print(result.stderr)
        return False
    
    print("✅ BigQuery task data loaded successfully")
    
    # Step 2: Run template-based analysis
    print("\n📋 Step 2: Running template-based analysis...")
    result = subprocess.run([sys.executable, "scripts/template_analysis.py"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Template analysis failed:")
        print(result.stderr)
        return False
    
    print("✅ Template analysis completed successfully")
    
    # Step 3: Run enhanced QA analysis with real task content
    print("\n🔍 Step 3: Running enhanced QA analysis with real task content...")
    result = subprocess.run([sys.executable, "scripts/enhanced_qa_analysis.py"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Enhanced QA analysis failed:")
        print(result.stderr)
        return False
    
    print("✅ Enhanced QA analysis completed successfully")
    
    # Step 4: Show results
    print("\n📁 Complete Analysis Finished! Results available in:")
    print("   📊 results/analysis_summary.md - Executive summary")
    print("   📈 results/segmented_analysis_report.md - Detailed segment breakdown")
    print("   🔍 results/enhanced_qa_analysis_report.md - Real communication pattern analysis")
    print("   📋 results/segmented_performance_data.csv - Raw segment data")
    print("   📋 results/enhanced_qa_analysis_data.json - Communication pattern data")
    print("   📚 results/archived/ - Historical analyses")
    
    return True

def run_bigquery_only():
    """Run only BigQuery data fetching"""
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("📊 Fetching opportunity data from BigQuery...")
    result = subprocess.run([sys.executable, "data_loaders/bigquery_manual_loader.py"])
    return result.returncode == 0

def run_tasks_only():
    """Run only BigQuery task data fetching"""
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("📱 Fetching task data from BigQuery...")
    result = subprocess.run([sys.executable, "data_loaders/bigquery_task_loader.py"])
    return result.returncode == 0

def run_segmented_only():
    """Run only segmented analysis (requires existing data)"""
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🎯 Running segmented analysis...")
    result = subprocess.run([sys.executable, "scripts/segmented_analysis.py"])
    return result.returncode == 0

def run_template_only():
    """Run only template-based analysis (requires existing data)"""
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("📋 Running template-based analysis...")
    result = subprocess.run([sys.executable, "scripts/template_analysis.py"])
    return result.returncode == 0

def run_enhanced_only():
    """Run only enhanced QA analysis with real task content (requires existing data)"""
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🔍 Running enhanced QA analysis with real task content...")
    result = subprocess.run([sys.executable, "scripts/enhanced_qa_analysis.py"])
    return result.returncode == 0

def test_bigquery_connection():
    """Test BigQuery connection"""
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🔍 Testing BigQuery connection...")
    result = subprocess.run([sys.executable, "utilities/simple_bigquery_test.py"])
    return result.returncode == 0

def main():
    """Main entry point with options"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "bigquery":
            success = run_bigquery_only()
        elif command == "tasks":
            success = run_tasks_only()
        elif command == "segmented":
            success = run_segmented_only()
        elif command == "template":
            success = run_template_only()
        elif command == "enhanced":
            success = run_enhanced_only()
        elif command == "test":
            success = test_bigquery_connection()
        elif command == "full":
            success = run_complete_analysis()
        else:
            print("Usage: python run_analysis.py [bigquery|tasks|segmented|template|enhanced|test|full]")
            print("  bigquery  - Fetch opportunity data from BigQuery only")
            print("  tasks     - Fetch task/communication data from BigQuery only")
            print("  segmented - Run segmented analysis only")
            print("  template  - Run template-based analysis (follows exact format)")
            print("  enhanced  - Run enhanced QA analysis with real task content")
            print("  test      - Test BigQuery connection")
            print("  full      - Run complete analysis (default)")
            return
    else:
        # Default: run complete analysis
        success = run_complete_analysis()
    
    if success:
        print("\n🎉 Analysis workflow completed successfully!")
    else:
        print("\n❌ Analysis workflow failed. Check error messages above.")

if __name__ == "__main__":
    main()
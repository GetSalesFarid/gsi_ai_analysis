#!/usr/bin/env python3
"""
DoorDash SMS Campaign Analysis Runner

This script serves as the main entry point for analyzing DoorDash SMS campaigns.
It coordinates data loading, analysis, and result generation.

Usage:
    python run_analysis.py [command]
    
Commands:
    full        - Run complete analysis (default)
    dbt         - Fetch DBT model data only
    campaigns   - Analyze campaign logic only
    tiers       - Analyze tier segmentation only
    overlaps    - Analyze campaign overlaps only
    performance - Analyze campaign performance only
    test        - Test DBT connection
"""

import sys
import os
from datetime import datetime
import argparse

# Add project paths for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'scripts'))
sys.path.append(os.path.join(project_root, 'data_loaders'))
sys.path.append(os.path.join(project_root, 'utilities'))

def print_banner():
    """Print analysis banner"""
    print("=" * 60)
    print("📱 DOORDASH SMS CAMPAIGN ANALYSIS")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def run_full_analysis():
    """Run complete SMS campaign analysis"""
    print("🚀 Running Full SMS Campaign Analysis...")
    
    try:
        # Archive previous results
        print("📁 Archiving previous results...")
        from utilities.archive_manager import archive_results
        archive_results()
        
        # Load DBT model data
        print("🔌 Loading DBT model data...")
        from data_loaders.dbt_model_loader import load_dbt_models
        load_dbt_models()
        
        # Analyze campaign logic
        print("📊 Analyzing campaign logic...")
        from scripts.sms_campaign_analyzer import analyze_campaigns
        analyze_campaigns()
        
        # Analyze tier segmentation
        print("🎯 Analyzing tier segmentation...")
        from scripts.cohort_overlap_detector import analyze_tier_segments
        analyze_tier_segments()
        
        # Detect campaign overlaps
        print("🔍 Detecting campaign overlaps...")
        from scripts.cohort_overlap_detector import detect_overlaps
        detect_overlaps()
        
        # Analyze performance if data available
        print("📈 Analyzing campaign performance...")
        from scripts.campaign_performance import analyze_performance
        analyze_performance()
        
        print("✅ Full analysis complete!")
        print(f"📂 Results saved to: {os.path.join(project_root, 'results')}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return False
    
    return True

def run_dbt_data():
    """Load DBT model data only"""
    print("🔌 Loading DBT model data...")
    try:
        from data_loaders.dbt_model_loader import load_dbt_models
        load_dbt_models()
        print("✅ DBT data loading complete!")
    except Exception as e:
        print(f"❌ Error loading DBT data: {str(e)}")
        return False
    return True

def run_campaign_analysis():
    """Analyze campaign logic only"""
    print("📊 Analyzing SMS campaign logic...")
    try:
        from scripts.sms_campaign_analyzer import analyze_campaigns
        analyze_campaigns()
        print("✅ Campaign analysis complete!")
    except Exception as e:
        print(f"❌ Error analyzing campaigns: {str(e)}")
        return False
    return True

def run_tier_analysis():
    """Analyze tier segmentation only"""
    print("🎯 Analyzing tier segmentation...")
    try:
        from scripts.cohort_overlap_detector import analyze_tier_segments
        analyze_tier_segments()
        print("✅ Tier analysis complete!")
    except Exception as e:
        print(f"❌ Error analyzing tiers: {str(e)}")
        return False
    return True

def run_overlap_analysis():
    """Analyze campaign overlaps only"""
    print("🔍 Analyzing campaign overlaps...")
    try:
        from scripts.cohort_overlap_detector import detect_overlaps
        detect_overlaps()
        print("✅ Overlap analysis complete!")
    except Exception as e:
        print(f"❌ Error analyzing overlaps: {str(e)}")
        return False
    return True

def run_performance_analysis():
    """Analyze campaign performance only"""
    print("📈 Analyzing campaign performance...")
    try:
        from scripts.campaign_performance import analyze_performance
        analyze_performance()
        print("✅ Performance analysis complete!")
    except Exception as e:
        print(f"❌ Error analyzing performance: {str(e)}")
        return False
    return True

def test_connection():
    """Test DBT connection"""
    print("🧪 Testing DBT connection...")
    try:
        from utilities.dbt_connection_test import test_dbt_connection
        test_dbt_connection()
        print("✅ Connection test complete!")
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False
    return True

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='DoorDash SMS Campaign Analysis')
    parser.add_argument('command', nargs='?', default='full',
                       choices=['full', 'dbt', 'campaigns', 'tiers', 'overlaps', 'performance', 'test'],
                       help='Analysis command to run')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Execute based on command
    success = False
    
    if args.command == 'full':
        success = run_full_analysis()
    elif args.command == 'dbt':
        success = run_dbt_data()
    elif args.command == 'campaigns':
        success = run_campaign_analysis()
    elif args.command == 'tiers':
        success = run_tier_analysis()
    elif args.command == 'overlaps':
        success = run_overlap_analysis()
    elif args.command == 'performance':
        success = run_performance_analysis()
    elif args.command == 'test':
        success = test_connection()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 Analysis completed successfully!")
    else:
        print("💥 Analysis failed - check error messages above")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
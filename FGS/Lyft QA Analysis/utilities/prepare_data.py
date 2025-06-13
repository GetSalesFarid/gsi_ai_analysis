#!/usr/bin/env python3
"""
Data preparation script for Lyft QA Generator
Converts the raw commission CSV into the expected format for analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path

def clean_commission_data(input_file: str, output_file: str = None):
    """Clean and format the commission data for QA analysis"""
    
    print(f"Processing: {input_file}")
    
    # Read the raw CSV, skipping header rows
    df = pd.read_csv(input_file, skiprows=6)
    
    # Clean column names (use the actual structure we see - 23 columns)
    df.columns = [
        'team_info', 'team_detail', 'rep_name', 'date', 'rep_name_2', 'rep_id', 
        'experiment', 'experiment_code', 'contact_method', 'contacts', 'frr', 
        'first_rides', 'contact_pct', 'ride_pct', 'col14', 'col15', 
        'experiment_2', 'col17', 'col18', 'col19', 'col20', 'col21', 'col22'
    ]
    
    # Filter to relevant rows (exclude empty or header rows)
    # Use rep_name_2 since that seems to have the actual rep names
    df = df[df['rep_name_2'].notna() & (df['rep_name_2'] != 'ISR') & (df['rep_name_2'] != 'Jarvis Johnson')]
    
    # Convert percentage strings to floats
    def clean_percentage(val):
        if pd.isna(val) or val == '':
            return 0.0
        if isinstance(val, str) and '%' in val:
            return float(val.replace('%', '')) / 100
        return float(val) if val != '' else 0.0
    
    df['frr_clean'] = df['frr'].apply(clean_percentage)
    df['contact_pct_clean'] = df['contact_pct'].apply(clean_percentage)
    df['ride_pct_clean'] = df['ride_pct'].apply(clean_percentage)
    
    # Convert contacts and first_rides to numeric
    df['contacts'] = pd.to_numeric(df['contacts'], errors='coerce').fillna(0)
    df['first_rides'] = pd.to_numeric(df['first_rides'], errors='coerce').fillna(0)
    
    # Calculate conversion rate (first rides / contacts)
    df['conversion_rate'] = np.where(df['contacts'] > 0, df['first_rides'] / df['contacts'], 0)
    
    # Aggregate by rep to get overall performance
    rep_summary = df.groupby(['rep_name_2', 'rep_id']).agg({
        'contacts': 'sum',
        'first_rides': 'sum', 
        'conversion_rate': 'mean'  # Average across different methods
    }).reset_index()
    
    # Recalculate overall conversion rate
    rep_summary['conversion_rate'] = np.where(
        rep_summary['contacts'] > 0, 
        rep_summary['first_rides'] / rep_summary['contacts'], 
        0
    )
    
    # Format for QA generator
    commission_formatted = pd.DataFrame({
        'rep_id': rep_summary['rep_id'],
        'rep_name': rep_summary['rep_name_2'],
        'conversion_rate': rep_summary['conversion_rate'],
        'total_opportunities': rep_summary['contacts'],
        'total_conversions': rep_summary['first_rides']
    })
    
    # Sort by conversion rate
    commission_formatted = commission_formatted.sort_values('conversion_rate', ascending=False)
    
    # Set output file
    if output_file is None:
        output_file = input_file.replace('.csv', '_formatted.csv')
    
    # Save formatted data
    commission_formatted.to_csv(output_file, index=False)
    print(f"✅ Formatted data saved to: {output_file}")
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"Total reps: {len(commission_formatted)}")
    print(f"Top performer: {commission_formatted.iloc[0]['rep_name']} ({commission_formatted.iloc[0]['conversion_rate']:.1%})")
    print(f"Avg conversion: {commission_formatted['conversion_rate'].mean():.1%}")
    
    return commission_formatted

def create_sample_conversion_data(commission_df: pd.DataFrame, output_file: str = "data/sample_conversion_data.csv"):
    """Create sample conversion data for testing (since we don't have the real data yet)"""
    
    np.random.seed(42)  # For reproducible results
    
    # Generate sample opportunities for each rep
    conversion_records = []
    
    for _, rep in commission_df.iterrows():
        rep_id = rep['rep_id'] 
        total_opps = int(rep['total_opportunities'])
        conversion_rate = rep['conversion_rate']
        
        # Generate opportunity UUIDs and outcomes
        for i in range(total_opps):
            opp_uuid = f"opp_{rep_id}_{i:04d}"
            # Use actual conversion rate to determine outcomes
            converted = np.random.random() < conversion_rate
            
            conversion_records.append({
                'opportunity_uuid': opp_uuid,
                'rep_id': rep_id,
                'converted': converted
            })
    
    conversion_df = pd.DataFrame(conversion_records)
    conversion_df.to_csv(output_file, index=False)
    print(f"✅ Sample conversion data created: {output_file}")
    
    return conversion_df

def create_sample_tasks_data(conversion_df: pd.DataFrame, output_file: str = "data/sample_tasks_data.csv"):
    """Create sample tasks data for testing"""
    
    np.random.seed(42)
    
    tasks = []
    call_templates = [
        "Hi {name}, this is about your Lyft driver application. Do you have a few minutes to talk?",
        "Good morning! I'm calling about getting you started with driving for Lyft. Are you still interested?",
        "Hi there! I wanted to follow up on your Lyft application and see if you have any questions.",
        "Hello, this is regarding your Lyft driver signup. When would be a good time to get you on the road?"
    ]
    
    sms_templates = [
        "Hi! Ready to start earning with Lyft? Let's get you driving today! 🚗",
        "Your Lyft application is approved! When can you start driving?", 
        "Quick question - what's holding you back from starting with Lyft?",
        "Great news! You can start driving for Lyft right now. Are you free to chat?"
    ]
    
    for _, row in conversion_df.iterrows():
        opp_uuid = row['opportunity_uuid']
        
        # Each opportunity gets 1-3 tasks
        num_tasks = np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])
        
        for task_num in range(num_tasks):
            task_type = np.random.choice(['call', 'sms'], p=[0.6, 0.4])
            
            if task_type == 'call':
                content = np.random.choice(call_templates)
            else:
                content = np.random.choice(sms_templates)
            
            # Add timestamp (random time in last 30 days)
            timestamp = pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(0, 30))
            
            tasks.append({
                'opportunity_uuid': opp_uuid,
                'task_type': task_type,
                'content': content,
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
    
    tasks_df = pd.DataFrame(tasks)
    tasks_df.to_csv(output_file, index=False)
    print(f"✅ Sample tasks data created: {output_file}")
    
    return tasks_df

def main():
    """Main data preparation workflow"""
    
    data_dir = Path("data")
    
    # Process the commission data
    input_file = "data/Lyft - Team Bonus & ISR II - XP Contacts By Team.csv"
    
    print("🔄 Preparing Lyft QA data...")
    
    # Clean and format commission data
    commission_df = clean_commission_data(input_file, "data/commission_dashboard_formatted.csv")
    
    # Create sample data for testing (remove when you have real data)
    conversion_df = create_sample_conversion_data(commission_df)
    tasks_df = create_sample_tasks_data(conversion_df)
    
    print(f"\n✅ Data preparation complete!")
    print(f"📁 Files ready in data/ directory:")
    print(f"   - commission_dashboard_formatted.csv")
    print(f"   - sample_conversion_data.csv") 
    print(f"   - sample_tasks_data.csv")
    print(f"\n🚀 Ready to run QA analysis!")

if __name__ == "__main__":
    main()
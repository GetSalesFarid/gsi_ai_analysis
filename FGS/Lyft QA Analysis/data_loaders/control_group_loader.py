#!/usr/bin/env python3
"""
Control Group Data Loader - Fetches control group baseline conversion rates
"""

from google.cloud import bigquery
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ControlGroupLoader:
    def __init__(self, project_id: str = "getsaleswarehouse"):
        self.client = bigquery.Client(project=project_id)
    
    def fetch_control_baselines(self, output_file: str = "data/control_baselines.csv"):
        """Fetch control group baseline conversion rates by experiment and language"""
        
        query = """
        select
         date_trunc(experiment_tag_date , month) xp_month
        ,language_c
        ,project experiment
        ,sum(1) leads
        ,sum(case
          when project in ('Lyft Funnel Conversion - Stale')
          then if(date_diff(date(first_ride_at) , exposure_date , day) <= 30 , 1, 0) 
          else if(date_diff(date(first_ride_at) , application_date , day) <= 30 , 1, 0) 
          end) full_conversion 
        ,sum(case
          when project not in ('Lyft Funnel Conversion - Upfunnel')
          then 0
          when project in ('Lyft Funnel Conversion - Upfunnel')
          then if(date_diff(date(approved_date) , application_date , day) <= 30 , 1 , 0)
          end) upfunnel_next_step_conversion
        from `getsaleswarehouse.gsi_mart_lyft.lyft_dim_opp` 
        where date_trunc(date(experiment_tag_date) , month) = date_trunc(date_sub(current_date , interval 1 month) , month)
        and opportunity_treatment_group = 'Control'
        group by 1,2,3
        """
        
        print("🔄 Fetching control group baseline data from BigQuery...")
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            # Convert to DataFrame
            data = []
            for row in results:
                data.append({
                    'xp_month': str(row.xp_month),
                    'language': row.language_c if row.language_c else 'English',
                    'experiment': row.experiment,
                    'leads': row.leads,
                    'full_conversion': row.full_conversion,
                    'upfunnel_next_step_conversion': row.upfunnel_next_step_conversion,
                    'control_conversion_rate': row.full_conversion / row.leads if row.leads > 0 else 0
                })
            
            df = pd.DataFrame(data)
            
            # Save to CSV
            df.to_csv(output_file, index=False)
            
            print(f"✅ Saved {len(df)} control baseline records to {output_file}")
            
            # Display baseline summary
            print("\n📊 Control Group Baselines:")
            for _, row in df.iterrows():
                print(f"   {row['experiment']} - {row['language']}: {row['control_conversion_rate']:.1%} ({row['full_conversion']}/{row['leads']})")
            
            return len(df)
            
        except Exception as e:
            print(f"❌ Error fetching control baseline data: {e}")
            raise
    
    def get_control_baseline(self, experiment, language, control_df=None):
        """Get control baseline conversion rate for a specific experiment and language"""
        
        if control_df is None:
            try:
                control_df = pd.read_csv("data/control_baselines.csv")
            except FileNotFoundError:
                print("⚠️  Control baselines not found, using default 0%")
                return 0.0
        
        # Find matching baseline
        match = control_df[
            (control_df['experiment'] == experiment) &
            (control_df['language'] == language)
        ]
        
        if not match.empty:
            return match.iloc[0]['control_conversion_rate']
        else:
            print(f"⚠️  No control baseline found for {experiment} - {language}, using 0%")
            return 0.0

def main():
    """Main control group loading workflow"""
    
    # Create data directory
    import os
    os.makedirs("data", exist_ok=True)
    
    # Initialize loader
    loader = ControlGroupLoader()
    
    try:
        # Fetch control baselines
        baseline_count = loader.fetch_control_baselines()
        
        print(f"\n🎯 Control Group Loading Complete!")
        print(f"📊 {baseline_count} experiment-language baselines fetched")
        print(f"📁 Data saved to: data/control_baselines.csv")
        
        print(f"\n🚀 Ready to calculate lift metrics against control baselines!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
import os
import sys
import pandas as pd
from datetime import datetime

# Add the DDOK scripts directory to path to import bigquery_client
sys.path.append('/Users/MacFGS/Machine/gsi_ai_analysis/SMS Analysis/DDOK/scripts')
from bigquery_client import query_to_dataframe

def main():
    """Execute Lyft call analysis query and save results to CSV"""
    
    # Define the query
    query = """
    select
    date_trunc(first_contacted_date_time_c , month) month 
    ,experiment
    ,oa.opportunity_uuid
    ,l.owner_name
    ,l.preferred_language_c
    ,oa.first_contact_activity_type
    ,e.call_summary
    ,call_timestamp
    ,call_direction
    ,call_duration
    ,if(date(first_ride_at) between opportunity_creation_date and opportunity_expiration_date , true, false) converted 
    ,row_number() over (partition by e.opportunity_uuid order by row_created_at) call_count_asc
    from `getsaleswarehouse.nlp.execvision_call_transcripts_compiled_conversations` e
    join `getsaleswarehouse.gsi_mart_lyft.lyft_dim_opp` l on e.opportunity_uuid = l.opportunity_uuid
    join `getsaleswarehouse.gsi_mart_core.sms_materialized_opportunity_oa_analytics` oa on oa.opportunity_uuid = l.opportunity_uuid
    where date_trunc(first_contacted_date_time_c , month) = '2025-05-01'
    order by 2 desc
    """
    
    print("Executing Lyft call analysis query...")
    print("Query targets: May 2025 call transcripts with conversion data")
    
    # Execute query
    df = query_to_dataframe(query)
    
    if df is not None:
        print(f"Query successful! Retrieved {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lyft_call_analysis_may2025_{timestamp}.csv"
        filepath = f"/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/{filename}"
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        print(f"Results saved to: {filename}")
        
        # Display summary stats
        print(f"\nSummary:")
        print(f"- Total opportunities: {df['opportunity_uuid'].nunique()}")
        print(f"- Total calls: {len(df)}")
        print(f"- Conversion rate: {df['converted'].mean():.2%}")
        if 'experiment' in df.columns:
            print(f"- Experiments: {df['experiment'].unique()}")
        
        print("\nFirst 5 rows:")
        print(df.head())
        
    else:
        print("Query failed - check BigQuery credentials and permissions")

if __name__ == "__main__":
    main()
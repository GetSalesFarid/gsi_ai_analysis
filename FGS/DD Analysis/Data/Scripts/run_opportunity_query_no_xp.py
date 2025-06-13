import sys
import os
sys.path.append('/Users/MacFGS/Machine/gsi_ai_analysis/SMS Analysis/DDOK/scripts')

from bigquery_client import query_to_dataframe
import pandas as pd

def main():
    """Run opportunity query and save results"""
    query = """
    select
    opportunity_uuid
    from `getsaleswarehouse.gsi_mart_dd.dd_dim_opp` 
    where 1=1 
    and date_trunc(application_date_c , month) >= date_trunc(current_date , month)
    and opportunity_id = 'dd_funnel_conversion'
    and experiment is not null
    group by 1
    """
    
    print("Executing opportunity query...")
    df = query_to_dataframe(query)
    
    if df is not None:
        print(f"Query successful! Retrieved {len(df)} rows")
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Save to CSV in the Data directory
        output_file = '../opportunity_uuids.csv'
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
    else:
        print("Query failed")

if __name__ == "__main__":
    main()
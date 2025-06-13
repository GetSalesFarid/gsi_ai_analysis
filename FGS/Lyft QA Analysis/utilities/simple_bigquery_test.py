#!/usr/bin/env python3
"""
Simple BigQuery test without pandas conversion
Export the query results manually and save to CSV
"""

from google.cloud import bigquery
import json

def test_bigquery_connection():
    """Test BigQuery connection and export query results"""
    
    client = bigquery.Client(project="getsaleswarehouse")
    
    query = """
    select
     opportunity_uuid 
    ,coalesce(language_c , 'English') language
    ,project experiment 
    ,date(first_contacted_date_time_c) first_contact_date
    ,first_contact_method
    ,if(date_diff(date(first_ride_at) , application_date , day) <= 30 , true, false) full_conversion 
    ,case
      when project not in ('Lyft Funnel Conversion - Upfunnel')
      then 'n/a'
      when project in ('Lyft Funnel Conversion - Upfunnel')
      then if(date_diff(date(approved_date) , application_date , day) <= 30 , 'true' , 'false')
      end upfunnel_next_step_conversion
    from `getsaleswarehouse.gsi_mart_lyft.lyft_dim_opp` 
    where date_trunc(date(first_contacted_date_time_c) , month) = date_trunc(date_sub(current_date , interval 1 month) , month)
    limit 10
    """
    
    print("🔄 Testing BigQuery connection...")
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        
        print(f"✅ Query successful! {query_job.num_dml_affected_rows} rows returned")
        
        # Print first few rows to verify data
        print("\n📊 Sample data:")
        for i, row in enumerate(results):
            if i >= 5:  # Just show first 5 rows
                break
            print(f"Row {i+1}:")
            print(f"  UUID: {row.opportunity_uuid}")
            print(f"  Language: {row.language}")
            print(f"  Experiment: {row.experiment}")
            print(f"  Contact Method: {row.first_contact_method}")
            print(f"  Converted: {row.full_conversion}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_bigquery_connection()
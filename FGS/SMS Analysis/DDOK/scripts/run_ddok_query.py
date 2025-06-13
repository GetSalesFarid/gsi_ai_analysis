#!/usr/bin/env python3
"""
Simple script to run the DDOK experiment BigQuery query.

Prerequisites:
1. Install gcloud CLI: brew install google-cloud-sdk
2. Authenticate: gcloud auth application-default login
3. Set project: gcloud config set project getsaleswarehouse
"""

import pandas as pd
from google.cloud import bigquery

def run_ddok_query():
    """Run the DDOK experiment query and save results"""
    
    query = """
    with tags as (
      select 
      opportunity_uuid
      ,lower(tag) like '%ai_agent%' ai_agent_tag
      from getsales.tags
      where lower(tag) in (
              -- ddok experiment
               'doordash_manned_sms_ddok_ai_agent_initial_unattempted_treatment'
              ,'doordash_manned_sms_ddok_ai_agent_initial_unattempted_control'
              ,'doordash_manned_sms_ddok_initial_unattempted_b_treatment'
              ,'doordash_manned_sms_ddok_initial_unattempted_b_control'
              ,'doordash_manned_sms_ddok_ai_agent_missed_unattempted_control'
              ,'doordash_manned_sms_ddok_ai_agent_missed_unattempted_treatment'
              ,'doordash_manned_sms_ddok_missed_unattempted_b_treatment'
              ,'doordash_manned_sms_ddok_missed_unattempted_b_control'
              )
      and tag_creation_timestamp >= '2025-04-01'        
    )      

    select
     oa.opportunity_uuid
    ,oa.owner_username task_owner
    ,oa.message
    ,oa.direction
    ,oa.overall_task_rank
    ,dd.owner_username lead_owner
    ,oa.task_datetime_cst
    ,t.ai_agent_tag
    from `getsaleswarehouse.gsi_mart_core.sms_materialized_outreach_activities` oa 
    join `getsaleswarehouse.gsi_mart_dd.dd_dim_opp` dd on oa.opportunity_uuid = dd.opportunity_uuid
    join `getsaleswarehouse.gsi_mart_core.sms_materialized_opportunity_oa_analytics` oq on oa.opportunity_uuid = oq.opportunity_uuid
    join tags t on t.opportunity_uuid = oa.opportunity_uuid
    where 1=1
    and task_type = 'SMS'
    and first_contact_activity_type = 'SMS'
    
    """
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project="getsaleswarehouse")
        print("Connected to BigQuery")
        
        # Run query
        print("Executing query...")
        query_job = client.query(query)
        results = query_job.result()
        
        # Convert to list first to avoid pandas dependency issues
        rows = []
        schema = results.schema
        
        for row in results:
            rows.append(dict(row))
        
        print(f"Query successful! Retrieved {len(rows)} rows")
        
        if len(rows) > 0:
            # Get column names from schema
            columns = [field.name for field in schema]
            print(f"Columns: {columns}")
            
            print("\nFirst 5 rows:")
            for i, row in enumerate(rows[:5]):
                print(f"Row {i+1}: {row}")
            
            # Save results to CSV manually
            import csv
            output_file = '../data/ddok_sms_fgs_l3m.csv'
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                if rows:
                    writer = csv.DictWriter(csvfile, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(rows)
            
            print(f"\nResults saved to {output_file}")
            
            # Basic stats
            print(f"\nBasic stats:")
            print(f"- Total messages: {len(rows)}")
            
            # Count unique values manually
            unique_opportunities = set(row['opportunity_uuid'] for row in rows)
            unique_owners = set(row['task_owner'] for row in rows)
            directions = {}
            for row in rows:
                direction = row['direction']
                directions[direction] = directions.get(direction, 0) + 1
            
            print(f"- Unique opportunities: {len(unique_opportunities)}")
            print(f"- Unique task owners: {len(unique_owners)}")
            print(f"- Message directions: {directions}")
        else:
            print("No results found")
            
        return rows
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Run: gcloud auth application-default login")
        print("2. Run: gcloud config set project getsaleswarehouse")
        print("3. Verify you have BigQuery access in the getsaleswarehouse project")
        return None

if __name__ == "__main__":
    run_ddok_query()
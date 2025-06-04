#!/usr/bin/env python3
"""
Script to run the DDOK experiment conversions BigQuery query.

Prerequisites:
1. Install gcloud CLI: brew install google-cloud-sdk
2. Authenticate: gcloud auth application-default login
3. Set project: gcloud config set project getsaleswarehouse
"""

import csv
from google.cloud import bigquery

def run_ddok_conversions_query():
    """Run the DDOK experiment conversions query and save results"""
    
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
     dd.opportunity_uuid
    ,dd.lead_tier_c
    ,dd.first_contacted_date_time_c
    ,dd.owner_name
    ,dd.experiment_tag_c
    ,date_diff(first_delivery_date_c , application_date_c , day) <= 25 successful_conversion
    ,t.ai_agent_tag
    from `getsaleswarehouse.gsi_mart_dd.dd_dim_opp` dd 
    join tags t on t.opportunity_uuid = dd.opportunity_uuid
    join `getsaleswarehouse.gsi_mart_core.sms_materialized_opportunity_oa_analytics` oq on dd.opportunity_uuid = oq.opportunity_uuid
    where 1=1
    and first_contact_activity_type = 'SMS'
    """
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project="getsaleswarehouse")
        print("Connected to BigQuery")
        
        # Run query
        print("Executing conversions query...")
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
            output_file = 'data/ddok_sms_fgs_l3m_conversions.csv'
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                if rows:
                    writer = csv.DictWriter(csvfile, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(rows)
            
            print(f"\nResults saved to {output_file}")
            
            # Basic stats
            print(f"\nBasic stats:")
            print(f"- Total opportunities: {len(rows)}")
            
            # Count unique values and conversions manually
            unique_owners = set(row['owner_name'] for row in rows if row['owner_name'])
            experiment_tags = {}
            lead_tiers = {}
            conversions = {"True": 0, "False": 0, "None": 0}
            
            for row in rows:
                # Count experiment tags
                tag = row['experiment_tag_c']
                experiment_tags[tag] = experiment_tags.get(tag, 0) + 1
                
                # Count lead tiers
                tier = row['lead_tier_c']
                lead_tiers[tier] = lead_tiers.get(tier, 0) + 1
                
                # Count conversions
                conversion = str(row['successful_conversion'])
                conversions[conversion] = conversions.get(conversion, 0) + 1
            
            print(f"- Unique owners: {len(unique_owners)}")
            print(f"- Experiment tags: {experiment_tags}")
            print(f"- Lead tiers: {lead_tiers}")
            print(f"- Successful conversions: {conversions}")
            
            # Calculate conversion rate
            total_with_conversion_data = conversions.get("True", 0) + conversions.get("False", 0)
            if total_with_conversion_data > 0:
                conversion_rate = (conversions.get("True", 0) / total_with_conversion_data) * 100
                print(f"- Overall conversion rate: {conversion_rate:.2f}%")
            
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
    run_ddok_conversions_query()
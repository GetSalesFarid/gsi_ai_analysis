import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def get_bigquery_client():
    """Initialize and return BigQuery client"""
    # Try using existing service account first, then fallback to default credentials
    try:
        # First try with service account
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../agent/gcp_key.json"
        client = bigquery.Client(project="getsaleswarehouse")
        return client
    except Exception as e:
        print(f"Service account auth failed: {e}")
        print("Trying with default credentials...")
        # Remove service account and try default
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        client = bigquery.Client(project="getsaleswarehouse")
        return client

def run_query(query_string):
    """Execute BigQuery query and return results"""
    client = get_bigquery_client()
    
    try:
        query_job = client.query(query_string)
        results = query_job.result()
        return results
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def query_to_dataframe(query_string):
    """Execute BigQuery query and return as pandas DataFrame"""
    client = get_bigquery_client()
    
    try:
        df = client.query(query_string).to_dataframe()
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Your query
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
    from `getsaleswarehouse.gsi_mart_core.sms_materialized_outreach_activities` oa 
    join `getsaleswarehouse.gsi_mart_dd.dd_dim_opp` dd on oa.opportunity_uuid = dd.opportunity_uuid
    join tags t on t.opportunity_uuid = oa.opportunity_uuid
    where 1=1
    and task_type = 'SMS'
    """
    
    # Execute query
    print("Executing BigQuery query...")
    df = query_to_dataframe(query)
    
    if df is not None:
        print(f"Query successful! Retrieved {len(df)} rows")
        print("\nFirst 5 rows:")
        print(df.head())
        print(f"\nColumns: {list(df.columns)}")
        
        # Save to CSV
        df.to_csv('ddok_experiment_results.csv', index=False)
        print(f"\nResults saved to ddok_experiment_results.csv")
    else:
        print("Query failed")
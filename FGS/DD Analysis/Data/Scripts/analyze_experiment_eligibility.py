from google.cloud import bigquery
import csv

# Configurable experiment tags list
EXPERIMENT_TAGS = [
    'instant_dash_bgc_pass_approved_no_delivery',
    'dropshipping_approved_no_delivery', 
    'doordash_tiktok_tof_lead_net_new',
    'up_funnel_6d_AnD',
    'late_approval',
    'doordash_facebook_tof_lead_net_new',
    'up_funnel_idv_approved_no_bgc',
    'up_funnel_prof_sub_no_bgc_2022_02_28',
    'up_funnel_app_sub_no_profile_2022_02_28',
    'up_funnel_no_bgc_from_no_profile',
    'up_funnel_prof_sub_no_bgc_missed'
]

def analyze_experiment_eligibility(tags_to_analyze=None):
    """
    Analyze why leads from run_opportunity_query (no experiment) are not eligible for experiment tags
    
    Args:
        tags_to_analyze: List of experiment tags to analyze. If None, uses default list.
    """
    if tags_to_analyze is None:
        tags_to_analyze = EXPERIMENT_TAGS
    
    print(f"Analyzing eligibility for {len(tags_to_analyze)} experiment tags...")
    
    # Query that focuses on leads that don't currently have experiments and checks eligibility constraints
    query = f"""
    WITH opportunities_no_exp AS (
        SELECT opportunity_uuid
        FROM `getsaleswarehouse.gsi_mart_dd.dd_dim_opp` 
        WHERE 1=1 
        AND date_trunc(application_date_c , month) >= date_trunc(current_date , month)
        AND opportunity_id = 'dd_funnel_conversion'
        AND experiment is null  -- Focus on leads without experiments
        GROUP BY 1
    ),
    
    analysis_data AS (
        SELECT
            o.opportunity_uuid,
            o.opportunity_id,
            o.application_date_c,
            o.experiment,
            o.nimda_bgc_status_c,
            o.orientation_type_c,
            o.orientation_date_c,
            o.activation_date_c,
            o.owner_id,
            o.country,
            DATE_DIFF(CURRENT_DATE('America/Chicago'), o.application_date_c, DAY) as days_applied,
            CASE WHEN o.activation_date_c IS NOT NULL 
                 THEN DATE_DIFF(CURRENT_DATE('America/Chicago'), cast(o.activation_date_c as date), DAY) 
                 ELSE NULL END as days_active,
            
            -- Check key experiment eligibility constraints
            CASE WHEN o.opportunity_id = 'dd_funnel_conversion' THEN 'OK' ELSE 'FAIL: Wrong opp_id' END as opp_id_check,
            CASE WHEN o.owner_id in ('0055w000009YDSjAAO','0055w000009YTSQAA4','0055w00000F6yh2AAB') THEN 'OK' ELSE 'FAIL: Wrong owner' END as owner_check,
            CASE WHEN lower(o.nimda_bgc_status_c) = 'clear' THEN 'OK' ELSE CONCAT('FAIL: BGC=', COALESCE(o.nimda_bgc_status_c, 'NULL')) END as bgc_check,
            CASE WHEN o.country <> 'Australia' THEN 'OK' ELSE 'FAIL: Australia' END as country_check,
            
            -- Check days_applied constraints for different experiments
            CASE 
                WHEN DATE_DIFF(CURRENT_DATE('America/Chicago'), o.application_date_c, DAY) <= 18 THEN 'OK for instant_dash/dropshipping'
                WHEN DATE_DIFF(CURRENT_DATE('America/Chicago'), o.application_date_c, DAY) BETWEEN 19 AND 24 THEN 'OK for late_approval'
                ELSE 'FAIL: Too old'
            END as days_applied_check,
            
            -- Check activation constraints
            CASE 
                WHEN o.orientation_type_c = 'instant_dash' AND o.activation_date_c is not null AND 
                     date_diff(CURRENT_DATE('America/Chicago'), o.orientation_date_c, day) >= 4 
                THEN 'OK for instant_dash'
                WHEN o.orientation_type_c = 'Dropshipping' AND 
                     DATE_DIFF(CURRENT_DATE('America/Chicago'), cast(o.activation_date_c as date), DAY) >= 4
                THEN 'OK for dropshipping' 
                ELSE CONCAT('FAIL: orientation_type=', COALESCE(o.orientation_type_c, 'NULL'), 
                           ', activation=', CAST(o.activation_date_c as STRING),
                           ', orientation=', CAST(o.orientation_date_c as STRING))
            END as activation_check
            
        FROM `getsaleswarehouse.gsi_mart_dd.dd_dim_opp` o
        INNER JOIN opportunities_no_exp oe ON o.opportunity_uuid = oe.opportunity_uuid
    )
    
    SELECT * FROM analysis_data
    ORDER BY opportunity_uuid
    LIMIT 500
    """
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project="getsaleswarehouse")
        print("Connected to BigQuery")
        
        # Run query
        print("Executing eligibility analysis query...")
        query_job = client.query(query)
        results = query_job.result()
        
        # Convert to list first to avoid pandas dependency issues
        rows = []
        schema = results.schema
        
        for row in results:
            rows.append(dict(row))
        
        print(f"Query successful! Retrieved {len(rows)} leads without experiments")
        
        if len(rows) > 0:
            # Get column names from schema
            columns = [field.name for field in schema]
            print(f"Columns: {columns}")
            
            print("\\nFirst 10 rows:")
            for i, row in enumerate(rows[:10]):
                print(f"Row {i+1}: {row}")
            
            # Save results to CSV manually
            output_file = '../experiment_eligibility_analysis.csv'
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                if rows:
                    writer = csv.DictWriter(csvfile, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(rows)
            
            print(f"\\nResults saved to {output_file}")
            
            # Basic analysis
            print(f"\\n=== ELIGIBILITY CONSTRAINT ANALYSIS ===")
            print(f"- Total leads without experiments: {len(rows)}")
            
            # Analyze constraint check results
            constraint_checks = ['opp_id_check', 'owner_check', 'bgc_check', 
                               'country_check', 'days_applied_check', 'activation_check']
            
            for check in constraint_checks:
                if check in columns:
                    check_results = {}
                    for row in rows:
                        result = row[check]
                        check_results[result] = check_results.get(result, 0) + 1
                    
                    print(f"\\n{check.replace('_', ' ').title()}:")
                    sorted_results = sorted(check_results.items(), key=lambda x: x[1], reverse=True)
                    for result, count in sorted_results:
                        print(f"  {result}: {count} leads ({count/len(rows)*100:.1f}%)")
            
            # Find leads that pass all checks
            print(f"\\n=== FULLY ELIGIBLE LEADS ===")
            eligible_count = 0
            for row in rows:
                all_ok = True
                for check in constraint_checks:
                    if check in columns and row[check] and not row[check].startswith('OK'):
                        all_ok = False
                        break
                if all_ok:
                    eligible_count += 1
            
            print(f"- Leads passing ALL constraint checks: {eligible_count}/{len(rows)} ({eligible_count/len(rows)*100:.1f}%)")
            
            # Show some field distributions
            print(f"\\n=== KEY FIELD DISTRIBUTIONS ===")
            
            key_fields = ['orientation_type_c', 'nimda_bgc_status_c', 'country', 'days_applied']
            for field in key_fields:
                if field in columns:
                    field_counts = {}
                    for row in rows:
                        value = row[field] or 'NULL'
                        field_counts[value] = field_counts.get(value, 0) + 1
                    
                    print(f"\\n{field}:")
                    sorted_values = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    for value, count in sorted_values:
                        print(f"  {value}: {count} leads ({count/len(rows)*100:.1f}%)")
        else:
            print("No results found")
            
        return rows
        
    except Exception as e:
        print(f"Error: {e}")
        print("\\nTroubleshooting steps:")
        print("1. Run: gcloud auth application-default login")
        print("2. Run: gcloud config set project getsaleswarehouse")
        print("3. Verify you have BigQuery access in the getsaleswarehouse project")
        return None

def update_experiment_tags(new_tags):
    """
    Update the list of experiment tags to analyze
    
    Args:
        new_tags: List of experiment tag names to analyze
    """
    global EXPERIMENT_TAGS
    EXPERIMENT_TAGS = new_tags
    print(f"Updated experiment tags list to: {new_tags}")

if __name__ == "__main__":
    # Run the analysis
    results = analyze_experiment_eligibility()
    
    # Example of how to customize tags:
    # custom_tags = ['instant_dash_bgc_pass_approved_no_delivery', 'dropshipping_approved_no_delivery']
    # update_experiment_tags(custom_tags)
    # results = analyze_experiment_eligibility(custom_tags)
#!/usr/bin/env python3
"""
Manual BigQuery data loader that doesn't require pyarrow
Processes BigQuery results manually and saves to CSV
"""

from google.cloud import bigquery
import csv
import pandas as pd
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ManualBigQueryLoader:
    def __init__(self, project_id: str = "getsaleswarehouse"):
        self.client = bigquery.Client(project=project_id)
    
    def fetch_and_save_opportunity_data(self, output_file: str = "data/bigquery_raw_data.csv"):
        """Fetch opportunity data and save to CSV manually"""
        
        query = """
        with notes as (
          select
           question_1
          ,question_2
          ,question_3
          ,coalesce(o.description ,l.notes_c_c) additional_notes
          ,l.opportunity_uuid
          from `getsaleswarehouse.gsi_intermediate.last_submitted_outreach_notes` o 
          join `getsaleswarehouse.gsi_mart_core.sfdc_lead` l on o.salesforce_id =l.id and l.opportunity_type_c in ('Lyft Funnel Conversion Launch' , 'Lyft W Plus Funnel Conversion', 'Lyft W Plus Funnel Conversion Stale AnA')
        )
        
        select
         l.opportunity_uuid
        ,coalesce(language_c , 'English') language
        ,project experiment
        ,date(first_contacted_date_time_c) first_contact_date
        ,owner_username
        ,owner_name
        ,first_contact_method
        ,case
          when project in ('Lyft Funnel Conversion - Stale')
          then if(date_diff(date(first_ride_at) , exposure_date , day) <= 30 , true, false)
          else if(date_diff(date(first_ride_at) , application_date , day) <= 30 , true, false)
          end full_conversion
        ,case
          when project not in ('Lyft Funnel Conversion - Upfunnel')
          then 'n/a'
          when project in ('Lyft Funnel Conversion - Upfunnel')
          then if(date_diff(date(approved_date) , application_date , day) <= 30 , 'true' , 'false')
          end upfunnel_next_step_conversion
        ,coalesce(question_1 , 'ignore question 1') what_are_your_goals_or_motivations_to_start_driving_for_lyft
        ,coalesce(question_2 , 'ignore question 2') what_else_do_you_need_to_submit
        ,coalesce(question_3 , 'ignore question 3') estimated_bgc_date
        ,coalesce(additional_notes , 'ignore question 4') additional_notes
        from `getsaleswarehouse.gsi_mart_lyft.lyft_dim_opp` l 
        left join notes n on l.opportunity_uuid = n.opportunity_uuid 
        where date_trunc(date(first_contacted_date_time_c) , month) = date_trunc(date_sub(current_date , interval 1 month) , month)
        """
        
        print("🔄 Fetching opportunity data from BigQuery...")
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            # Save to CSV manually
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'opportunity_uuid', 'language', 'experiment', 'first_contact_date',
                    'owner_username', 'owner_name', 'first_contact_method', 
                    'full_conversion', 'upfunnel_next_step_conversion', 
                    'what_are_your_goals_or_motivations_to_start_driving_for_lyft',
                    'what_else_do_you_need_to_submit', 'estimated_bgc_date', 'additional_notes'
                ])
                
                # Write data rows
                row_count = 0
                for row in results:
                    writer.writerow([
                        row.opportunity_uuid,
                        row.language,
                        row.experiment,
                        str(row.first_contact_date) if row.first_contact_date else '',
                        row.owner_username,
                        row.owner_name,
                        row.first_contact_method,
                        row.full_conversion,
                        row.upfunnel_next_step_conversion,
                        row.what_are_your_goals_or_motivations_to_start_driving_for_lyft if row.what_are_your_goals_or_motivations_to_start_driving_for_lyft else '',
                        row.what_else_do_you_need_to_submit if row.what_else_do_you_need_to_submit else '',
                        row.estimated_bgc_date if row.estimated_bgc_date else '',
                        row.additional_notes if row.additional_notes else ''
                    ])
                    row_count += 1
            
            print(f"✅ Saved {row_count} records to {output_file}")
            return row_count
            
        except Exception as e:
            print(f"❌ Error fetching BigQuery data: {e}")
            raise
    
    def calculate_performance_metrics(self, csv_file: str):
        """Calculate performance metrics from saved CSV"""
        
        print("📊 Calculating performance metrics...")
        
        # Read the CSV with pandas
        df = pd.read_csv(csv_file)
        
        # Convert boolean strings to actual booleans
        df['full_conversion'] = df['full_conversion'].astype(bool)
        
        # Calculate performance by individual rep
        performance_groups = []
        
        # Group by rep (owner_username)
        for owner_username in df['owner_username'].unique():
            if pd.isna(owner_username) or owner_username == '':
                continue
                
            rep_data = df[df['owner_username'] == owner_username]
            
            if len(rep_data) < 5:  # Skip reps with too few opportunities
                continue
            
            # Get rep details
            owner_name = rep_data['owner_name'].iloc[0] if not rep_data['owner_name'].empty else owner_username
            
            # Calculate overall rep metrics
            total_opps = len(rep_data)
            conversions = rep_data['full_conversion'].sum()
            conversion_rate = conversions / total_opps if total_opps > 0 else 0
            
            # Get breakdown by experiment and contact method
            experiments = rep_data['experiment'].value_counts().to_dict()
            contact_methods = rep_data['first_contact_method'].value_counts().to_dict()
            languages = rep_data['language'].value_counts().to_dict()
            
            performance_groups.append({
                'rep_id': owner_username,
                'rep_name': owner_name,
                'owner_username': owner_username,
                'total_opportunities': total_opps,
                'total_conversions': int(conversions),
                'conversion_rate': conversion_rate,
                'experiments': experiments,
                'contact_methods': contact_methods,
                'languages': languages,
                'primary_experiment': max(experiments.items(), key=lambda x: x[1])[0] if experiments else 'Unknown',
                'primary_contact_method': max(contact_methods.items(), key=lambda x: x[1])[0] if contact_methods else 'Unknown'
            })
        
        # Convert to DataFrame and sort
        metrics_df = pd.DataFrame(performance_groups)
        metrics_df = metrics_df.sort_values('conversion_rate', ascending=False)
        
        print(f"✅ Calculated metrics for {len(metrics_df)} performance groups")
        return metrics_df
    
    def create_qa_data_files(self, raw_csv: str):
        """Create all the files needed for QA analysis"""
        
        # Calculate performance metrics
        metrics_df = self.calculate_performance_metrics(raw_csv)
        
        # Save commission dashboard format
        commission_file = "data/commission_dashboard_bigquery.csv"
        commission_df = metrics_df[['rep_id', 'rep_name', 'conversion_rate', 'total_opportunities', 'total_conversions']].copy()
        commission_df.to_csv(commission_file, index=False)
        print(f"✅ Commission dashboard saved: {commission_file}")
        
        # Create conversion data format  
        raw_df = pd.read_csv(raw_csv)
        raw_df['rep_id'] = raw_df['owner_username']  # Use actual rep username
        
        conversion_file = "data/conversion_data_bigquery.csv"
        conversion_df = raw_df[['opportunity_uuid', 'rep_id', 'full_conversion']].copy()
        conversion_df.rename(columns={'full_conversion': 'converted'}, inplace=True)
        conversion_df.to_csv(conversion_file, index=False)
        print(f"✅ Conversion data saved: {conversion_file}")
        
        # Create sample tasks data (since we don't have real tasks data yet)
        tasks_file = "data/tasks_data_sample.csv"
        tasks_data = []
        
        # Sample 200 opportunities for testing
        sample_opps = conversion_df.head(200)
        
        for _, row in sample_opps.iterrows():
            # Each opportunity gets 1-2 tasks
            for i in range(1, 3):
                task_type = 'call' if i == 1 else 'sms'
                content = f"Sample {task_type} for opportunity {row['opportunity_uuid']}"
                
                tasks_data.append({
                    'opportunity_uuid': row['opportunity_uuid'],
                    'task_type': task_type,
                    'content': content,
                    'timestamp': '2025-06-01 10:00:00'
                })
        
        tasks_df = pd.DataFrame(tasks_data)
        tasks_df.to_csv(tasks_file, index=False)
        print(f"✅ Sample tasks data saved: {tasks_file}")
        
        # Generate performance report
        self.generate_performance_report(metrics_df)
        
        return commission_file, conversion_file, tasks_file
    
    def generate_performance_report(self, metrics_df):
        """Generate performance analysis report"""
        
        report_lines = []
        report_lines.append("# BigQuery Lyft Performance Analysis")
        report_lines.append(f"Generated: {pd.Timestamp.now()}")
        report_lines.append("")
        
        # Overall stats
        total_opps = metrics_df['total_opportunities'].sum()
        total_conversions = metrics_df['total_conversions'].sum()
        overall_rate = total_conversions / total_opps if total_opps > 0 else 0
        
        report_lines.append(f"## Overall Performance")
        report_lines.append(f"- Total Opportunities: {total_opps:,}")
        report_lines.append(f"- Total Conversions: {total_conversions:,}")
        report_lines.append(f"- Overall Conversion Rate: {overall_rate:.2%}")
        report_lines.append("")
        
        # Top performers
        top_5 = metrics_df.head(5)
        report_lines.append("## Top 5 Sales Reps")
        for _, row in top_5.iterrows():
            report_lines.append(f"- {row['rep_name']} ({row['owner_username']}): {row['conversion_rate']:.2%} ({row['total_conversions']}/{row['total_opportunities']})")
            report_lines.append(f"  - Primary Experiment: {row['primary_experiment']}")
            report_lines.append(f"  - Primary Contact Method: {row['primary_contact_method']}")
        report_lines.append("")
        
        # Bottom performers for comparison
        bottom_5 = metrics_df.tail(5)
        report_lines.append("## Bottom 5 Sales Reps (for comparison)")
        for _, row in bottom_5.iterrows():
            report_lines.append(f"- {row['rep_name']} ({row['owner_username']}): {row['conversion_rate']:.2%} ({row['total_conversions']}/{row['total_opportunities']})")
        report_lines.append("")
        
        # Experiment analysis
        all_experiments = {}
        for _, row in metrics_df.iterrows():
            for exp, count in row['experiments'].items():
                if exp not in all_experiments:
                    all_experiments[exp] = {'total_opps': 0, 'total_conversions': 0}
                all_experiments[exp]['total_opps'] += count
                # Calculate conversions for this experiment for this rep
                rep_exp_data = pd.read_csv("data/bigquery_raw_data.csv")
                rep_exp_subset = rep_exp_data[
                    (rep_exp_data['owner_username'] == row['owner_username']) & 
                    (rep_exp_data['experiment'] == exp)
                ]
                all_experiments[exp]['total_conversions'] += rep_exp_subset['full_conversion'].sum()
        
        report_lines.append("## Performance by Experiment")
        for exp, stats in all_experiments.items():
            if stats['total_opps'] > 0:
                conv_rate = stats['total_conversions'] / stats['total_opps']
                report_lines.append(f"- {exp}: {conv_rate:.2%} ({stats['total_conversions']}/{stats['total_opps']})")
        report_lines.append("")
        
        # Save report
        with open("data/bigquery_performance_report.md", "w") as f:
            f.write("\n".join(report_lines))
        
        print("✅ Performance report saved: data/bigquery_performance_report.md")

def main():
    """Main workflow"""
    
    # Archive existing results before starting new analysis
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utilities'))
    try:
        from archive_manager import ArchiveManager
        archive_manager = ArchiveManager()
        archive_manager.prepare_for_new_analysis()
    except ImportError:
        print("⚠️  Archive manager not available, continuing without archiving...")
    
    # Create data directory
    import os
    os.makedirs("data", exist_ok=True)
    
    # Initialize loader
    loader = ManualBigQueryLoader()
    
    try:
        # Fetch and save raw data
        raw_file = "data/bigquery_raw_data.csv"
        row_count = loader.fetch_and_save_opportunity_data(raw_file)
        
        # Process into QA-ready format
        commission_file, conversion_file, tasks_file = loader.create_qa_data_files(raw_file)
        
        print(f"\n🎯 BigQuery data processing complete!")
        print(f"📊 Total records processed: {row_count:,}")
        print(f"📁 Files ready for QA analysis:")
        print(f"   - {commission_file}")
        print(f"   - {conversion_file}")
        print(f"   - {tasks_file}")
        print(f"\n🚀 Run QA analysis with:")
        print(f"python lyft_qa_generator.py --commission-csv {commission_file} --conversion-csv {conversion_file} --tasks-csv {tasks_file} --response-json /path/to/response_instructions.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
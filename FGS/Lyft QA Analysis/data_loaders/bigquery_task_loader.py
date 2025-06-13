#!/usr/bin/env python3
"""
BigQuery Task Data Loader - Fetches real task data with communication content
"""

from google.cloud import bigquery
import csv
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class BigQueryTaskLoader:
    def __init__(self, project_id: str = "getsaleswarehouse"):
        self.client = bigquery.Client(project=project_id)
    
    def fetch_task_data(self, output_file: str = "data/tasks_data_bigquery.csv"):
        """Fetch real task data from BigQuery"""
        
        query = """
        with opps as (
          select
          opportunity_uuid 
          ,owner_username
          ,coalesce(language_c , 'English') language
          ,project experiment 
          ,first_contact_method
          from `getsaleswarehouse.gsi_mart_lyft.lyft_dim_opp` 
          where date_trunc(date(first_contacted_date_time_c) , month) = date_trunc(date_sub(current_date , interval 1 month) , month)
        ) 
        select
         o.opportunity_uuid 
        ,o.owner_username
        ,o.language
        ,o.experiment 
        ,o.first_contact_method
        ,task_start_timestamp
        ,task_type
        ,task_stage
        ,direction
        ,contact_flag
        ,case
          when task_type = 'Call' and call_summary = 'Due to the brevity of the meeting transcript, there is no call summary.'
          then false
          when task_type = 'Call' and not coalesce(contact_flag , false)
          then false
          when task_type = 'Call' and call_summary is null
          then false
          else true 
          end include_in_conext_analysis
        ,case
          when task_type = 'SMS'
          then message 
          when task_type = 'Call' and call_summary = 'Due to the brevity of the meeting transcript, there is no call summary.'
          then 'Call to Short, ignore for analysis'
          when task_type = 'Call' and not coalesce(contact_flag , false)
          then 'No Contact, ignore for analysis'
          when task_type = 'Call'
          then coalesce(call_summary , 'No Summary, ignore for analysis')
          end task_summary
        from opps o 
        join `getsaleswarehouse.gsi_mart_core.sms_materialized_outreach_activities` oa on o.opportunity_uuid = oa.opportunity_uuid
        left join `getsaleswarehouse.gsi_intermediate.execvision_call_transcripts` cc on oa.task_id = cc.task_id
        where task_stage in ('first_contact' , 'post_contact')
        """
        
        print("🔄 Fetching task data from BigQuery...")
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            # Save to CSV manually
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'opportunity_uuid', 'owner_username', 'language', 'experiment', 'first_contact_method',
                    'task_start_timestamp', 'task_type', 'task_stage', 'direction', 'contact_flag',
                    'include_in_conext_analysis', 'task_summary'
                ])
                
                # Write data rows
                row_count = 0
                for row in results:
                    writer.writerow([
                        row.opportunity_uuid,
                        row.owner_username,
                        row.language,
                        row.experiment,
                        row.first_contact_method,
                        str(row.task_start_timestamp) if row.task_start_timestamp else '',
                        row.task_type,
                        row.task_stage,
                        row.direction,
                        row.contact_flag,
                        row.include_in_conext_analysis,
                        row.task_summary
                    ])
                    row_count += 1
            
            print(f"✅ Saved {row_count} task records to {output_file}")
            return row_count
            
        except Exception as e:
            print(f"❌ Error fetching task data: {e}")
            raise
    
    def analyze_task_quality(self, csv_file: str = "data/tasks_data_bigquery.csv"):
        """Analyze task data quality and patterns"""
        
        print("📊 Analyzing task data quality...")
        
        df = pd.read_csv(csv_file)
        
        # Convert boolean columns
        df['contact_flag'] = df['contact_flag'].fillna(False).astype(bool)
        df['include_in_conext_analysis'] = df['include_in_conext_analysis'].fillna(False).astype(bool)
        
        # Basic statistics
        total_tasks = len(df)
        usable_for_analysis = df['include_in_conext_analysis'].sum()
        
        print(f"📈 Task Data Analysis:")
        print(f"   Total tasks: {total_tasks:,}")
        print(f"   Usable for content analysis: {usable_for_analysis:,} ({usable_for_analysis/total_tasks:.1%})")
        
        # By task type
        task_type_breakdown = df.groupby(['task_type', 'include_in_conext_analysis']).size().reset_index(name='count')
        print(f"\n📱 Task Type Breakdown:")
        for _, row in task_type_breakdown.iterrows():
            usable = "✅ Usable" if row['include_in_conext_analysis'] else "❌ Skip"
            print(f"   {row['task_type']}: {row['count']:,} tasks ({usable})")
        
        # By rep (top 10 by task volume)
        rep_stats = df.groupby('owner_username').agg({
            'opportunity_uuid': 'count',
            'include_in_conext_analysis': 'sum'
        }).rename(columns={
            'opportunity_uuid': 'total_tasks',
            'include_in_conext_analysis': 'usable_tasks'
        })
        rep_stats['usable_rate'] = rep_stats['usable_tasks'] / rep_stats['total_tasks']
        rep_stats = rep_stats.sort_values('total_tasks', ascending=False).head(10)
        
        print(f"\n👥 Top 10 Reps by Task Volume:")
        for owner_username, stats in rep_stats.iterrows():
            print(f"   {owner_username}: {stats['total_tasks']} tasks, {stats['usable_tasks']} usable ({stats['usable_rate']:.1%})")
        
        # Content analysis preview
        usable_content = df[df['include_in_conext_analysis'] == True]['task_summary']
        avg_content_length = usable_content.str.len().mean()
        
        print(f"\n📝 Content Analysis Preview:")
        print(f"   Average content length: {avg_content_length:.0f} characters")
        print(f"   Sample successful content:")
        
        # Show a few examples of usable content
        sample_content = usable_content.dropna().head(3)
        for i, content in enumerate(sample_content, 1):
            preview = content[:100] + "..." if len(content) > 100 else content
            print(f"   {i}. {preview}")
        
        return {
            'total_tasks': total_tasks,
            'usable_tasks': usable_for_analysis,
            'usable_rate': usable_for_analysis / total_tasks,
            'avg_content_length': avg_content_length
        }

def main():
    """Main task data loading workflow"""
    
    # Create data directory
    import os
    os.makedirs("data", exist_ok=True)
    
    # Initialize loader
    loader = BigQueryTaskLoader()
    
    try:
        # Fetch task data
        task_count = loader.fetch_task_data()
        
        # Analyze data quality
        stats = loader.analyze_task_quality()
        
        print(f"\n🎯 Task Data Loading Complete!")
        print(f"📊 {task_count:,} total tasks fetched")
        print(f"✅ {stats['usable_tasks']:,} tasks ready for content analysis")
        print(f"📁 Data saved to: data/tasks_data_bigquery.csv")
        
        print(f"\n🚀 Ready to run enhanced analysis with real task content!")
        print(f"   Next: Run segmented analysis to see communication patterns")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
BigQuery data loader for Lyft QA Generator
Fetches performance data directly from BigQuery and calculates top performers
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from pathlib import Path
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class BigQueryDataLoader:
    def __init__(self, project_id: str = None):
        """Initialize BigQuery client"""
        self.client = bigquery.Client(project=project_id)
    
    def fetch_opportunity_data(self) -> pd.DataFrame:
        """Fetch opportunity data from BigQuery"""
        
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
        """
        
        logger.info("Fetching opportunity data from BigQuery...")
        
        try:
            df = self.client.query(query).to_dataframe()
            logger.info(f"Fetched {len(df)} opportunity records")
            return df
        except Exception as e:
            logger.error(f"Error fetching BigQuery data: {e}")
            raise
    
    def calculate_performance_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate performance metrics by experiment, language, and contact method"""
        
        logger.info("Calculating performance metrics...")
        
        # Define performance groups
        performance_groups = ['experiment', 'language', 'first_contact_method']
        
        # Calculate conversion rates by group
        metrics_list = []
        
        for experiment in df['experiment'].unique():
            for language in df['language'].unique():
                for contact_method in df['first_contact_method'].unique():
                    
                    # Filter data for this combination
                    subset = df[
                        (df['experiment'] == experiment) & 
                        (df['language'] == language) & 
                        (df['first_contact_method'] == contact_method)
                    ]
                    
                    if len(subset) == 0:
                        continue
                    
                    # Calculate full conversion rate
                    total_opps = len(subset)
                    full_conversions = subset['full_conversion'].sum()
                    full_conversion_rate = full_conversions / total_opps if total_opps > 0 else 0
                    
                    # Calculate upfunnel conversion rate (where applicable)
                    upfunnel_subset = subset[subset['upfunnel_next_step_conversion'] != 'n/a']
                    upfunnel_conversions = len(upfunnel_subset[upfunnel_subset['upfunnel_next_step_conversion'] == 'true'])
                    upfunnel_total = len(upfunnel_subset)
                    upfunnel_conversion_rate = upfunnel_conversions / upfunnel_total if upfunnel_total > 0 else 0
                    
                    # Create unique identifier for this performance group
                    rep_id = f"{experiment}_{language}_{contact_method}".replace(' ', '_').replace('-', '_')
                    
                    metrics_list.append({
                        'rep_id': rep_id,
                        'rep_name': f"{experiment} - {language} - {contact_method}",
                        'experiment': experiment,
                        'language': language,
                        'first_contact_method': contact_method,
                        'total_opportunities': total_opps,
                        'full_conversions': full_conversions,
                        'full_conversion_rate': full_conversion_rate,
                        'upfunnel_conversions': upfunnel_conversions,
                        'upfunnel_total': upfunnel_total,
                        'upfunnel_conversion_rate': upfunnel_conversion_rate,
                        'primary_conversion_rate': full_conversion_rate  # Use full conversion as primary metric
                    })
        
        metrics_df = pd.DataFrame(metrics_list)
        
        # Filter out groups with too few opportunities (less than 10)
        metrics_df = metrics_df[metrics_df['total_opportunities'] >= 10]
        
        logger.info(f"Calculated metrics for {len(metrics_df)} performance groups")
        return metrics_df
    
    def create_commission_dashboard(self, metrics_df: pd.DataFrame, output_file: str) -> pd.DataFrame:
        """Create commission dashboard format for QA generator"""
        
        # Format for QA generator
        commission_df = pd.DataFrame({
            'rep_id': metrics_df['rep_id'],
            'rep_name': metrics_df['rep_name'],
            'conversion_rate': metrics_df['primary_conversion_rate'],
            'total_opportunities': metrics_df['total_opportunities'],
            'total_conversions': metrics_df['full_conversions'],
            'experiment': metrics_df['experiment'],
            'language': metrics_df['language'],
            'contact_method': metrics_df['first_contact_method']
        })
        
        # Sort by conversion rate
        commission_df = commission_df.sort_values('conversion_rate', ascending=False)
        
        # Save to CSV
        commission_df.to_csv(output_file, index=False)
        logger.info(f"Commission dashboard saved to: {output_file}")
        
        return commission_df
    
    def create_conversion_data(self, opp_df: pd.DataFrame, output_file: str) -> pd.DataFrame:
        """Create conversion data format for QA generator"""
        
        # Map opportunity data to conversion format
        conversion_df = pd.DataFrame({
            'opportunity_uuid': opp_df['opportunity_uuid'],
            'rep_id': opp_df['experiment'] + '_' + opp_df['language'] + '_' + opp_df['first_contact_method'],
            'converted': opp_df['full_conversion'],
            'experiment': opp_df['experiment'],
            'language': opp_df['language'],
            'contact_method': opp_df['first_contact_method'],
            'contact_date': opp_df['first_contact_date']
        })
        
        # Clean rep_id
        conversion_df['rep_id'] = conversion_df['rep_id'].str.replace(' ', '_').str.replace('-', '_')
        
        # Save to CSV
        conversion_df.to_csv(output_file, index=False)
        logger.info(f"Conversion data saved to: {output_file}")
        
        return conversion_df
    
    def generate_performance_report(self, metrics_df: pd.DataFrame) -> str:
        """Generate a performance analysis report"""
        
        report_lines = []
        report_lines.append("# Lyft Performance Analysis Report")
        report_lines.append(f"Generated: {pd.Timestamp.now()}")
        report_lines.append("")
        
        # Overall stats
        total_opps = metrics_df['total_opportunities'].sum()
        total_conversions = metrics_df['full_conversions'].sum()
        overall_rate = total_conversions / total_opps if total_opps > 0 else 0
        
        report_lines.append(f"## Overall Performance")
        report_lines.append(f"- Total Opportunities: {total_opps:,}")
        report_lines.append(f"- Total Conversions: {total_conversions:,}")
        report_lines.append(f"- Overall Conversion Rate: {overall_rate:.2%}")
        report_lines.append("")
        
        # Top performers
        top_5 = metrics_df.head(5)
        report_lines.append("## Top 5 Performers")
        for _, row in top_5.iterrows():
            report_lines.append(f"- {row['rep_name']}: {row['primary_conversion_rate']:.2%} ({row['full_conversions']}/{row['total_opportunities']})")
        report_lines.append("")
        
        # By experiment
        exp_stats = metrics_df.groupby('experiment').agg({
            'total_opportunities': 'sum',
            'full_conversions': 'sum',
            'primary_conversion_rate': 'mean'
        }).reset_index()
        exp_stats['conversion_rate'] = exp_stats['full_conversions'] / exp_stats['total_opportunities']
        
        report_lines.append("## Performance by Experiment")
        for _, row in exp_stats.iterrows():
            report_lines.append(f"- {row['experiment']}: {row['conversion_rate']:.2%}")
        report_lines.append("")
        
        # By language
        lang_stats = metrics_df.groupby('language').agg({
            'total_opportunities': 'sum',
            'full_conversions': 'sum'
        }).reset_index()
        lang_stats['conversion_rate'] = lang_stats['full_conversions'] / lang_stats['total_opportunities']
        
        report_lines.append("## Performance by Language")
        for _, row in lang_stats.iterrows():
            report_lines.append(f"- {row['language']}: {row['conversion_rate']:.2%}")
        report_lines.append("")
        
        # By contact method
        method_stats = metrics_df.groupby('first_contact_method').agg({
            'total_opportunities': 'sum',
            'full_conversions': 'sum'
        }).reset_index()
        method_stats['conversion_rate'] = method_stats['full_conversions'] / method_stats['total_opportunities']
        
        report_lines.append("## Performance by Contact Method")
        for _, row in method_stats.iterrows():
            report_lines.append(f"- {row['first_contact_method']}: {row['conversion_rate']:.2%}")
        
        return "\n".join(report_lines)

def main():
    """Main data loading workflow"""
    
    # Initialize BigQuery loader
    loader = BigQueryDataLoader()
    
    # Create data directory
    Path("data").mkdir(exist_ok=True)
    
    try:
        # Fetch opportunity data
        opp_df = loader.fetch_opportunity_data()
        
        # Calculate performance metrics
        metrics_df = loader.calculate_performance_metrics(opp_df)
        
        # Create commission dashboard
        commission_df = loader.create_commission_dashboard(
            metrics_df, 
            "data/commission_dashboard_bigquery.csv"
        )
        
        # Create conversion data
        conversion_df = loader.create_conversion_data(
            opp_df, 
            "data/conversion_data_bigquery.csv"
        )
        
        # Generate performance report
        report = loader.generate_performance_report(metrics_df)
        with open("data/performance_report.md", "w") as f:
            f.write(report)
        
        print("✅ BigQuery data loading complete!")
        print(f"📊 Performance groups identified: {len(metrics_df)}")
        print(f"📁 Files created:")
        print(f"   - data/commission_dashboard_bigquery.csv")
        print(f"   - data/conversion_data_bigquery.csv") 
        print(f"   - data/performance_report.md")
        print(f"\n🏆 Top performer: {commission_df.iloc[0]['rep_name']} ({commission_df.iloc[0]['conversion_rate']:.2%})")
        
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        print(f"❌ Error: {e}")
        print("Make sure you have BigQuery credentials configured")

if __name__ == "__main__":
    main()
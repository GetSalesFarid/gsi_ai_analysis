#!/usr/bin/env python3
"""
Segmented Analysis - Top performer for each combination of:
First Contact Method + Project + Language
"""

import pandas as pd
from collections import defaultdict

def analyze_top_performers_by_segment():
    """Find top performer for each First Contact Method + Project + Language combination"""
    
    # Load the raw BigQuery data
    raw_data = pd.read_csv("../data/bigquery_raw_data.csv")
    
    print("🔍 Analyzing top performers by segment...")
    print(f"Total opportunities: {len(raw_data):,}")
    
    # Convert boolean conversion column
    raw_data['full_conversion'] = raw_data['full_conversion'].astype(bool)
    
    # Group by segment combinations
    segments = {}
    
    # Get all unique combinations
    combinations = raw_data.groupby(['first_contact_method', 'experiment', 'language']).size()
    
    print(f"\n📊 Found {len(combinations)} unique segments:")
    
    segment_results = []
    
    for (contact_method, experiment, language), count in combinations.items():
        if count < 10:  # Skip segments with too few opportunities
            continue
            
        print(f"\n🎯 Analyzing: {contact_method} + {experiment} + {language}")
        print(f"   Total opportunities in segment: {count}")
        
        # Filter data for this segment
        segment_data = raw_data[
            (raw_data['first_contact_method'] == contact_method) &
            (raw_data['experiment'] == experiment) &
            (raw_data['language'] == language)
        ]
        
        # Calculate performance by rep within this segment
        rep_performance = []
        
        for owner_username in segment_data['owner_username'].unique():
            if pd.isna(owner_username):
                continue
                
            rep_segment_data = segment_data[segment_data['owner_username'] == owner_username]
            
            if len(rep_segment_data) < 5:  # Need minimum 5 opportunities to be meaningful
                continue
            
            rep_name = rep_segment_data['owner_name'].iloc[0]
            total_opps = len(rep_segment_data)
            conversions = rep_segment_data['full_conversion'].sum()
            conversion_rate = conversions / total_opps
            
            rep_performance.append({
                'owner_username': owner_username,
                'owner_name': rep_name,
                'total_opportunities': total_opps,
                'conversions': conversions,
                'conversion_rate': conversion_rate
            })
        
        if not rep_performance:
            print("   ⚠️  No reps with sufficient data in this segment")
            continue
            
        # Sort by conversion rate and get top performer
        rep_performance.sort(key=lambda x: x['conversion_rate'], reverse=True)
        top_performer = rep_performance[0]
        
        # Calculate segment averages
        segment_total_opps = len(segment_data)
        segment_conversions = segment_data['full_conversion'].sum()
        segment_avg_conversion = segment_conversions / segment_total_opps
        
        segment_result = {
            'contact_method': contact_method,
            'experiment': experiment,
            'language': language,
            'segment_total_opportunities': segment_total_opps,
            'segment_conversions': segment_conversions,
            'segment_avg_conversion_rate': segment_avg_conversion,
            'top_performer_username': top_performer['owner_username'],
            'top_performer_name': top_performer['owner_name'],
            'top_performer_opportunities': top_performer['total_opportunities'],
            'top_performer_conversions': top_performer['conversions'],
            'top_performer_conversion_rate': top_performer['conversion_rate'],
            'performance_advantage': top_performer['conversion_rate'] - segment_avg_conversion,
            'total_reps_in_segment': len(rep_performance)
        }
        
        segment_results.append(segment_result)
        
        print(f"   🏆 Top performer: {top_performer['owner_name']} ({top_performer['owner_username']})")
        print(f"       Conversion rate: {top_performer['conversion_rate']:.2%} ({top_performer['conversions']}/{top_performer['total_opportunities']})")
        print(f"       Segment average: {segment_avg_conversion:.2%}")
        print(f"       Advantage: +{(top_performer['conversion_rate'] - segment_avg_conversion):.2%}")
    
    return segment_results

def generate_segmented_report(segment_results):
    """Generate comprehensive segmented analysis report"""
    
    # Sort by top performer conversion rate
    segment_results.sort(key=lambda x: x['top_performer_conversion_rate'], reverse=True)
    
    report_lines = []
    report_lines.append("# Lyft QA Analysis - Top Performers by Segment")
    report_lines.append(f"Generated: {pd.Timestamp.now()}")
    report_lines.append("")
    report_lines.append("Analysis of top performing sales reps within each combination of:")
    report_lines.append("- **First Contact Method** (Call, SMS)")
    report_lines.append("- **Project/Experiment** (Lyft Funnel Conversion, Upfunnel, etc.)")
    report_lines.append("- **Language** (English, Spanish)")
    report_lines.append("")
    
    # Executive summary
    total_segments = len(segment_results)
    avg_advantage = sum(s['performance_advantage'] for s in segment_results) / total_segments
    
    report_lines.append("## Executive Summary")
    report_lines.append(f"- **{total_segments} segments** analyzed")
    report_lines.append(f"- **Average top performer advantage:** {avg_advantage:.2%} above segment average")
    report_lines.append("")
    
    # Top performing segments overall
    report_lines.append("## Highest Converting Segments (by top performer)")
    report_lines.append("")
    
    for i, segment in enumerate(segment_results[:5], 1):
        report_lines.append(f"### {i}. {segment['contact_method']} + {segment['experiment']} + {segment['language']}")
        report_lines.append(f"**Top Performer:** {segment['top_performer_name']} ({segment['top_performer_username']})")
        report_lines.append(f"- **Conversion Rate:** {segment['top_performer_conversion_rate']:.2%}")
        report_lines.append(f"- **Volume:** {segment['top_performer_conversions']}/{segment['top_performer_opportunities']} opportunities")
        report_lines.append(f"- **Segment Average:** {segment['segment_avg_conversion_rate']:.2%}")
        report_lines.append(f"- **Advantage:** +{segment['performance_advantage']:.2%}")
        report_lines.append(f"- **Total Reps in Segment:** {segment['total_reps_in_segment']}")
        report_lines.append("")
    
    # All segments breakdown
    report_lines.append("## Complete Segment Breakdown")
    report_lines.append("")
    
    # Group by contact method for easier reading
    by_contact_method = defaultdict(list)
    for segment in segment_results:
        by_contact_method[segment['contact_method']].append(segment)
    
    for contact_method, segments in by_contact_method.items():
        report_lines.append(f"### {contact_method} Segments")
        report_lines.append("")
        
        for segment in segments:
            report_lines.append(f"**{segment['experiment']} - {segment['language']}**")
            report_lines.append(f"- Top Performer: {segment['top_performer_name']} ({segment['top_performer_conversion_rate']:.2%})")
            report_lines.append(f"- Segment Average: {segment['segment_avg_conversion_rate']:.2%}")
            report_lines.append(f"- Total Segment Volume: {segment['segment_conversions']}/{segment['segment_total_opportunities']}")
            report_lines.append("")
    
    # Key insights
    report_lines.append("## Key Insights")
    report_lines.append("")
    
    # Find best contact method overall
    call_segments = [s for s in segment_results if s['contact_method'] == 'Call']
    sms_segments = [s for s in segment_results if s['contact_method'] == 'SMS']
    
    if call_segments and sms_segments:
        avg_call_rate = sum(s['top_performer_conversion_rate'] for s in call_segments) / len(call_segments)
        avg_sms_rate = sum(s['top_performer_conversion_rate'] for s in sms_segments) / len(sms_segments)
        
        report_lines.append(f"### Contact Method Analysis")
        report_lines.append(f"- **Call segments average:** {avg_call_rate:.2%}")
        report_lines.append(f"- **SMS segments average:** {avg_sms_rate:.2%}")
        
        if avg_call_rate > avg_sms_rate:
            report_lines.append(f"- **Calls outperform SMS** by {avg_call_rate - avg_sms_rate:.2%}")
        else:
            report_lines.append(f"- **SMS outperforms Calls** by {avg_sms_rate - avg_call_rate:.2%}")
        report_lines.append("")
    
    # Find best experiments
    experiments = defaultdict(list)
    for segment in segment_results:
        experiments[segment['experiment']].append(segment['top_performer_conversion_rate'])
    
    report_lines.append(f"### Experiment Analysis")
    for exp, rates in experiments.items():
        avg_rate = sum(rates) / len(rates)
        report_lines.append(f"- **{exp}:** {avg_rate:.2%} average top performer rate")
    report_lines.append("")
    
    # Coaching recommendations
    report_lines.append("## Coaching Recommendations")
    report_lines.append("")
    
    # Find segments where the advantage is highest
    high_advantage_segments = [s for s in segment_results if s['performance_advantage'] > 0.05]  # >5% advantage
    
    if high_advantage_segments:
        report_lines.append("### High-Impact Coaching Opportunities")
        report_lines.append("Segments where top performers significantly outperform others:")
        report_lines.append("")
        
        for segment in high_advantage_segments[:3]:
            report_lines.append(f"**{segment['contact_method']} + {segment['experiment']} + {segment['language']}**")
            report_lines.append(f"- Top performer ({segment['top_performer_name']}) has {segment['performance_advantage']:.2%} advantage")
            report_lines.append(f"- {segment['total_reps_in_segment']} reps could benefit from coaching")
            report_lines.append(f"- Potential impact: Training others to reach {segment['top_performer_conversion_rate']:.2%}")
            report_lines.append("")
    
    return "\n".join(report_lines)

def main():
    """Main segmented analysis workflow"""
    
    # Archive existing results before starting new analysis
    import sys
    sys.path.append('../utilities')
    from archive_manager import ArchiveManager
    archive_manager = ArchiveManager()
    archive_manager.prepare_for_new_analysis()
    
    print("🎯 Starting segmented analysis...")
    
    # Analyze segments
    segment_results = analyze_top_performers_by_segment()
    
    # Generate report
    report = generate_segmented_report(segment_results)
    
    # Save results
    with open("results/segmented_analysis_report.md", "w") as f:
        f.write(report)
    
    # Save raw data as CSV for further analysis
    segment_df = pd.DataFrame(segment_results)
    segment_df.to_csv("results/segmented_performance_data.csv", index=False)
    
    print(f"\n✅ Segmented analysis complete!")
    print(f"📊 Analyzed {len(segment_results)} segments")
    print(f"📁 Reports saved:")
    print(f"   - results/segmented_analysis_report.md")
    print(f"   - results/segmented_performance_data.csv")

if __name__ == "__main__":
    main()
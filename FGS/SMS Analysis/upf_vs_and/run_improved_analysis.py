#!/usr/bin/env python3

import pandas as pd
import json
import re
from datetime import datetime
from collections import defaultdict, Counter

def load_data():
    """Load messages and bucket definitions"""
    # Load messages
    messages_df = pd.read_csv('input_data/BGC_vs_AND_messages.csv')
    
    # Load improved bucket definitions
    with open('bucket_definitions/response_instructions_data_improved.json', 'r') as f:
        buckets = json.load(f)
    
    # Load prompt
    with open('input_data/message_effectiveness_claude_prompt.txt', 'r') as f:
        prompt = f.read()
    
    return messages_df, buckets, prompt

def classify_message(message_text, buckets):
    """Classify a message into one of the 74 improved buckets"""
    message_lower = message_text.lower()
    
    for bucket in buckets:
        bucket_id = bucket['id']
        phrases = bucket.get('identification_phrases', [])
        
        for phrase in phrases:
            if phrase.lower() in message_lower:
                return bucket_id
    
    return 'UNCLASSIFIED'

def analyze_bucket_performance(messages_df, buckets):
    """Comprehensive bucket analysis"""
    
    # Classify all messages
    print("Classifying messages into 74 improved buckets...")
    messages_df['bucket'] = messages_df['message'].apply(lambda x: classify_message(str(x), buckets))
    
    # Create bucket lookup
    bucket_lookup = {b['id']: b for b in buckets}
    
    # Analysis results
    results = {
        'bucket_distribution': {},
        'conversion_rates': {},
        'category_performance': {},
        'tag_group_summary': {}
    }
    
    # 1. Bucket Distribution by Tag Group
    print("Calculating bucket distribution...")
    tag_groups = messages_df['tag_grouping'].unique()
    
    for tag in tag_groups:
        tag_data = messages_df[messages_df['tag_grouping'] == tag]
        bucket_counts = tag_data['bucket'].value_counts()
        total_conversations = len(tag_data)
        
        results['bucket_distribution'][tag] = {}
        for bucket_id, count in bucket_counts.items():
            percentage = (count / total_conversations) * 100
            results['bucket_distribution'][tag][bucket_id] = {
                'count': count,
                'percentage': percentage
            }
    
    # 2. Conversion Rates by Bucket
    print("Calculating conversion rates by bucket...")
    for tag in tag_groups:
        tag_data = messages_df[messages_df['tag_grouping'] == tag]
        results['conversion_rates'][tag] = {}
        
        for bucket_id in tag_data['bucket'].unique():
            bucket_data = tag_data[tag_data['bucket'] == bucket_id]
            if len(bucket_data) >= 10:  # Sufficient data threshold
                conversion_rate = bucket_data['full_conversion'].mean()
                results['conversion_rates'][tag][bucket_id] = {
                    'conversion_rate': conversion_rate,
                    'sample_size': len(bucket_data)
                }
    
    # 3. Category Performance (by prefix)
    print("Analyzing category performance...")
    prefixes = ['OBJ-', 'TSI-', 'AI-', 'HCP-', 'UNC-']
    
    for tag in tag_groups:
        tag_data = messages_df[messages_df['tag_grouping'] == tag]
        results['category_performance'][tag] = {}
        
        for prefix in prefixes:
            prefix_data = tag_data[tag_data['bucket'].str.startswith(prefix)]
            if len(prefix_data) > 0:
                results['category_performance'][tag][prefix] = {
                    'count': len(prefix_data),
                    'percentage': (len(prefix_data) / len(tag_data)) * 100,
                    'avg_conversion': prefix_data['full_conversion'].mean(),
                    'buckets_used': prefix_data['bucket'].nunique()
                }
    
    # 4. Tag Group Summary
    print("Creating tag group summary...")
    for tag in tag_groups:
        tag_data = messages_df[messages_df['tag_grouping'] == tag]
        results['tag_group_summary'][tag] = {
            'total_conversations': len(tag_data),
            'overall_conversion_rate': tag_data['full_conversion'].mean(),
            'unique_buckets_used': tag_data['bucket'].nunique(),
            'unclassified_percentage': (tag_data['bucket'] == 'UNCLASSIFIED').mean() * 100
        }
    
    return results, messages_df

def generate_report(results, messages_df, buckets, prompt):
    """Generate the comprehensive report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_lines = []
    
    # Header
    report_lines.extend([
        "MESSAGE EFFECTIVENESS ANALYSIS - IMPROVED 74-BUCKET SYSTEM",
        "=" * 70,
        f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Messages: {len(messages_df):,}",
        f"Total Buckets: {len(buckets)}",
        f"Tag Groups: {', '.join(results['tag_group_summary'].keys())}",
        ""
    ])
    
    # 1. Bucket Distribution by Tag Group
    report_lines.extend([
        "1. BUCKET DISTRIBUTION BY TAG GROUP",
        "-" * 40,
        ""
    ])
    
    # Show top 20 most used buckets across all groups
    all_bucket_usage = defaultdict(int)
    for tag, buckets_data in results['bucket_distribution'].items():
        for bucket_id, data in buckets_data.items():
            all_bucket_usage[bucket_id] += data['count']
    
    top_buckets = sorted(all_bucket_usage.items(), key=lambda x: x[1], reverse=True)[:20]
    
    report_lines.append("Top 20 Most Used Buckets:")
    for bucket_id, total_count in top_buckets:
        report_lines.append(f"  {bucket_id}: {total_count} total conversations")
        for tag in results['bucket_distribution']:
            if bucket_id in results['bucket_distribution'][tag]:
                data = results['bucket_distribution'][tag][bucket_id]
                report_lines.append(f"    {tag}: {data['count']} ({data['percentage']:.1f}%)")
        report_lines.append("")
    
    # 2. Conversion Rates by Bucket
    report_lines.extend([
        "2. CONVERSION RATES BY BUCKET (>10 conversations)",
        "-" * 50,
        ""
    ])
    
    for tag in results['conversion_rates']:
        if results['conversion_rates'][tag]:
            report_lines.append(f"{tag} Tag Group:")
            # Sort by conversion rate
            sorted_buckets = sorted(
                results['conversion_rates'][tag].items(),
                key=lambda x: x[1]['conversion_rate'],
                reverse=True
            )
            
            for bucket_id, data in sorted_buckets:
                report_lines.append(
                    f"  {bucket_id}: {data['conversion_rate']:.1%} "
                    f"(n={data['sample_size']})"
                )
            report_lines.append("")
    
    # 3. Bucket Category Performance Summary
    report_lines.extend([
        "3. BUCKET CATEGORY PERFORMANCE SUMMARY",
        "-" * 42,
        ""
    ])
    
    categories = ['OBJ-', 'TSI-', 'AI-', 'HCP-', 'UNC-']
    for tag in results['category_performance']:
        report_lines.append(f"{tag} Tag Group:")
        for category in categories:
            if category in results['category_performance'][tag]:
                data = results['category_performance'][tag][category]
                report_lines.append(
                    f"  {category} prefix: {data['percentage']:.1f}% of conversations "
                    f"({data['count']} msgs), {data['avg_conversion']:.1%} conversion, "
                    f"{data['buckets_used']} buckets used"
                )
        report_lines.append("")
    
    # 4. Tag Group Performance Comparison
    report_lines.extend([
        "4. TAG GROUP PERFORMANCE COMPARISON",
        "-" * 35,
        ""
    ])
    
    for tag, summary in results['tag_group_summary'].items():
        report_lines.extend([
            f"{tag}:",
            f"  Total Conversations: {summary['total_conversations']:,}",
            f"  Overall Conversion Rate: {summary['overall_conversion_rate']:.1%}",
            f"  Unique Buckets Used: {summary['unique_buckets_used']}/74",
            f"  Unclassified Messages: {summary['unclassified_percentage']:.1f}%",
            ""
        ])
    
    # 5. Key Insights & Recommendations
    report_lines.extend([
        "5. KEY INSIGHTS & RECOMMENDATIONS",
        "-" * 33,
        ""
    ])
    
    # Find best performing categories
    best_categories = {}
    for tag in results['category_performance']:
        for category, data in results['category_performance'][tag].items():
            if category not in best_categories or data['avg_conversion'] > best_categories[category]['conversion']:
                best_categories[category] = {
                    'tag': tag,
                    'conversion': data['avg_conversion'],
                    'usage': data['percentage']
                }
    
    report_lines.append("High-Performance Categories:")
    for category, data in sorted(best_categories.items(), key=lambda x: x[1]['conversion'], reverse=True):
        report_lines.append(f"  {category} performs best in {data['tag']} group: {data['conversion']:.1%} conversion")
    
    report_lines.append("")
    report_lines.append("Recommendations:")
    report_lines.append("1. Focus on high-converting bucket categories (HCP-, AI-)")
    report_lines.append("2. Investigate underutilized buckets (<5% usage)")
    report_lines.append("3. Improve classification of unclassified messages")
    report_lines.append("4. Optimize messaging for low-performing but high-volume buckets")
    
    # Save report
    report_text = "\n".join(report_lines)
    output_file = f"final_results/bucket_analysis_IMPROVED_{timestamp}.txt"
    
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    # Save classified data
    classified_file = f"final_results/classified_messages_IMPROVED_{timestamp}.csv"
    messages_df.to_csv(classified_file, index=False)
    
    # Save performance data
    performance_file = f"final_results/bucket_performance_IMPROVED_{timestamp}.json"
    with open(performance_file, 'w') as f:
        # Convert numpy types to native Python types for JSON serialization
        results_serializable = json.loads(json.dumps(results, default=str))
        json.dump(results_serializable, f, indent=2)
    
    return output_file, classified_file, performance_file, report_text

def main():
    print("Loading data...")
    messages_df, buckets, prompt = load_data()
    
    print(f"Loaded {len(messages_df):,} messages and {len(buckets)} bucket definitions")
    print(f"Tag groups: {messages_df['tag_grouping'].unique()}")
    
    print("\nAnalyzing bucket performance...")
    results, classified_df = analyze_bucket_performance(messages_df, buckets)
    
    print("\nGenerating comprehensive report...")
    report_file, classified_file, performance_file, report_text = generate_report(
        results, classified_df, buckets, prompt
    )
    
    print(f"\nAnalysis complete!")
    print(f"Report saved to: {report_file}")
    print(f"Classified data saved to: {classified_file}")
    print(f"Performance data saved to: {performance_file}")
    
    print("\n" + "="*50)
    print("EXECUTIVE SUMMARY")
    print("="*50)
    
    # Print key metrics
    for tag, summary in results['tag_group_summary'].items():
        print(f"{tag}: {summary['overall_conversion_rate']:.1%} conversion, "
              f"{summary['unique_buckets_used']}/74 buckets used, "
              f"{summary['unclassified_percentage']:.1f}% unclassified")

if __name__ == "__main__":
    main()
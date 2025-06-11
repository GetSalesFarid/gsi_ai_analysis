#!/usr/bin/env python3

import pandas as pd
import json
import re
from datetime import datetime
from collections import defaultdict, Counter

def load_data():
    """Load messages and original JSON bucket definitions"""
    messages_df = pd.read_csv('input_data/BGC_vs_AND_messages.csv')
    
    # Load original JSON from app-sales-pilot
    with open('/Users/MacFGS/Machine/app-sales-pilot/db/agent_instructions_db/response_instructions_data.json', 'r') as f:
        original_buckets = json.load(f)
    
    return messages_df, original_buckets

def classify_message_by_title(message_text, buckets):
    """Classify a message using bucket TITLES (production-like approach)"""
    message_lower = message_text.lower()
    
    # Create keyword mapping from bucket titles
    title_keywords = {}
    
    for bucket in buckets:
        bucket_id = bucket['id']
        title = bucket.get('title', '').lower()
        
        # Extract meaningful keywords from titles
        if 'bike' in title:
            title_keywords[bucket_id] = ['bike', 'bicycle', 'cycling']
        elif 'car' in title or 'vehicle' in title:
            title_keywords[bucket_id] = ['car', 'vehicle', 'transportation', 'drive', 'driving']
        elif 'busy' in title:
            title_keywords[bucket_id] = ['busy', 'schedule', 'time', 'hectic']
        elif 'background check' in title:
            title_keywords[bucket_id] = ['background', 'check', 'checkr', 'pending']
        elif 'gas' in title:
            title_keywords[bucket_id] = ['gas', 'fuel', 'expensive']
        elif 'job' in title or 'work' in title:
            title_keywords[bucket_id] = ['job', 'work', 'employed', 'employment']
        elif 'weather' in title:
            title_keywords[bucket_id] = ['weather', 'rain', 'snow', 'storm']
        elif 'military' in title:
            title_keywords[bucket_id] = ['military', 'army', 'navy', 'deployment']
        elif 'nervous' in title:
            title_keywords[bucket_id] = ['nervous', 'scared', 'worried', 'anxious']
        elif 'vacation' in title or 'town' in title:
            title_keywords[bucket_id] = ['vacation', 'travel', 'out of town', 'trip']
        elif 'debt' in title:
            title_keywords[bucket_id] = ['debt', 'bills', 'money problems']
        elif 'pregnant' in title:
            title_keywords[bucket_id] = ['pregnant', 'baby', 'expecting']
        elif 'schedule' in title or 'scheduling' in title:
            title_keywords[bucket_id] = ['schedule', 'scheduling', 'calendar', 'time slot']
        elif 'dash' in title:
            title_keywords[bucket_id] = ['dash', 'delivery', 'delivering']
        elif 'promotion' in title:
            title_keywords[bucket_id] = ['promotion', 'bonus', 'incentive']
        elif 'scam' in title:
            title_keywords[bucket_id] = ['scam', 'fake', 'fraud', 'suspicious']
        elif 'license' in title:
            title_keywords[bucket_id] = ['license', 'drivers license', 'id']
        elif 'sick' in title or 'covid' in title:
            title_keywords[bucket_id] = ['sick', 'covid', 'ill', 'health']
        elif 'student' in title:
            title_keywords[bucket_id] = ['student', 'school', 'college', 'university']
        elif 'tax' in title:
            title_keywords[bucket_id] = ['tax', 'taxes', '1099', 'irs']
        elif 'unemployed' in title:
            title_keywords[bucket_id] = ['unemployed', 'no job', 'laid off']
        elif 'waiting' in title and 'kit' in title:
            title_keywords[bucket_id] = ['kit', 'welcome kit', 'equipment']
        elif 'waitlist' in title:
            title_keywords[bucket_id] = ['waitlist', 'waiting list', 'capacity']
        elif 'safety' in title:
            title_keywords[bucket_id] = ['safety', 'dangerous', 'unsafe']
        elif 'verification' in title:
            title_keywords[bucket_id] = ['verification', 'verify', '2fa', 'code']
        elif 'crash' in title:
            title_keywords[bucket_id] = ['crash', 'crashes', 'freezing', 'frozen']
        elif 'carplay' in title:
            title_keywords[bucket_id] = ['carplay', 'apple carplay', 'car play']
        elif 'buffer' in title:
            title_keywords[bucket_id] = ['buffer', 'buffering', 'loading', 'stuck']
        elif 'error' in title:
            title_keywords[bucket_id] = ['error', 'error code', '400']
        elif 'bank' in title:
            title_keywords[bucket_id] = ['bank', 'banking', 'direct deposit', 'account']
        elif 'login' in title:
            title_keywords[bucket_id] = ['login', 'log in', 'sign in', 'password']
        elif 'red zone' in title or 'hot zone' in title:
            title_keywords[bucket_id] = ['red zone', 'hot zone', 'busy area']
        elif 'accept' in title and 'order' in title:
            title_keywords[bucket_id] = ['accept order', 'orders', 'accepting']
        elif 'white screen' in title:
            title_keywords[bucket_id] = ['white screen', 'blank screen', 'screen']
        elif 'wrong location' in title:
            title_keywords[bucket_id] = ['wrong location', 'location', 'gps']
        elif 'wrong name' in title:
            title_keywords[bucket_id] = ['wrong name', 'name', 'account name']
        elif 'location' in title:
            title_keywords[bucket_id] = ['location', 'address', 'gps', 'maps']
        elif 'payment' in title or 'pay' in title:
            title_keywords[bucket_id] = ['payment', 'pay', 'payout', 'money']
        elif 'promotion' in title and 'lower' in title:
            title_keywords[bucket_id] = ['promotion', 'lower', 'reduced', 'less']
        elif 'worth' in title or 'low pay' in title:
            title_keywords[bucket_id] = ['worth it', 'low pay', 'not worth', 'earnings']
        elif 'deactivat' in title:
            title_keywords[bucket_id] = ['deactivat', 'suspended', 'banned']
        elif 'identity' in title:
            title_keywords[bucket_id] = ['identity', 'id verification', 'verify identity']
        elif 'name' in title and 'change' in title:
            title_keywords[bucket_id] = ['change name', 'name change', 'preferred name']
    
    # Check each bucket's keywords
    for bucket_id, keywords in title_keywords.items():
        for keyword in keywords:
            if keyword in message_lower:
                return bucket_id
    
    return 'UNCLASSIFIED'

def analyze_upf_inbound_production(messages_df, buckets):
    """Analyze UpF inbound messages using production-like classification"""
    
    print("Filtering to UpF inbound messages...")
    # Filter to UpF tag and inbound direction
    upf_inbound = messages_df[
        (messages_df['tag_grouping'] == 'UpF') & 
        (messages_df['direction'] == 'Inbound')
    ].copy()
    
    print(f"Found {len(upf_inbound)} UpF inbound messages")
    
    if len(upf_inbound) == 0:
        print("No UpF inbound messages found!")
        return None, None
    
    print("Classifying messages using production-like title approach...")
    upf_inbound['bucket_production'] = upf_inbound['message'].apply(
        lambda x: classify_message_by_title(str(x), buckets)
    )
    
    # Analysis results
    results = {
        'classification_stats': {},
        'bucket_performance': {},
        'sample_classifications': {}
    }
    
    # Classification statistics
    total_messages = len(upf_inbound)
    classified_messages = len(upf_inbound[upf_inbound['bucket_production'] != 'UNCLASSIFIED'])
    classification_rate = (classified_messages / total_messages) * 100
    
    results['classification_stats'] = {
        'total_messages': total_messages,
        'classified_messages': classified_messages,
        'classification_rate': classification_rate,
        'unclassified_messages': total_messages - classified_messages,
        'unique_buckets_used': upf_inbound['bucket_production'].nunique()
    }
    
    # Bucket performance analysis
    bucket_counts = upf_inbound['bucket_production'].value_counts()
    
    for bucket_id, count in bucket_counts.items():
        if bucket_id != 'UNCLASSIFIED' and count >= 5:  # Minimum threshold
            bucket_data = upf_inbound[upf_inbound['bucket_production'] == bucket_id]
            
            # Get bucket title
            bucket_title = 'Unknown'
            for bucket in buckets:
                if bucket['id'] == bucket_id:
                    bucket_title = bucket.get('title', 'Unknown')
                    break
            
            results['bucket_performance'][bucket_id] = {
                'title': bucket_title,
                'count': count,
                'percentage': (count / total_messages) * 100,
                'conversion_rate': bucket_data['full_conversion'].mean() * 100,
                'bgc_conversion_rate': bucket_data['bgc_conversion_7d'].mean() * 100 if 'bgc_conversion_7d' in bucket_data.columns else 0
            }
    
    # Sample classifications for validation
    sample_size = min(20, len(upf_inbound))
    sample_data = upf_inbound.sample(n=sample_size, random_state=42)
    
    for idx, row in sample_data.iterrows():
        message_text = str(row['message']) if not pd.isna(row['message']) else "N/A"
        results['sample_classifications'][idx] = {
            'message': message_text[:100] + "..." if len(message_text) > 100 else message_text,
            'bucket': row['bucket_production'],
            'conversion': row['full_conversion']
        }
    
    return results, upf_inbound

def generate_production_analysis_report(results, analyzed_df, buckets):
    """Generate production classification analysis report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_lines = []
    
    if results is None:
        return None, None, "No UpF inbound messages found for analysis"
    
    # Header
    report_lines.extend([
        "UPF INBOUND MESSAGE CLASSIFICATION - PRODUCTION APPROACH",
        "=" * 57,
        f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Focus: UpF Tagged Opportunities, Inbound Messages Only",
        "Method: Classification using bucket titles (production-like approach)",
        "",
        "CLASSIFICATION PERFORMANCE",
        "=" * 25,
    ])
    
    # Classification stats
    stats = results['classification_stats']
    report_lines.extend([
        f"Total UpF Inbound Messages: {stats['total_messages']:,}",
        f"Successfully Classified: {stats['classified_messages']:,}",
        f"Classification Rate: {stats['classification_rate']:.1f}%",
        f"Unclassified Messages: {stats['unclassified_messages']:,}",
        f"Active Buckets Used: {stats['unique_buckets_used']}/59",
        f"Bucket Utilization: {(stats['unique_buckets_used']/59)*100:.1f}%",
        ""
    ])
    
    # Bucket performance breakdown
    if results['bucket_performance']:
        report_lines.extend([
            "BUCKET PERFORMANCE BREAKDOWN",
            "=" * 29,
            ""
        ])
        
        # Sort by count (most frequent first)
        sorted_buckets = sorted(
            results['bucket_performance'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        for bucket_id, data in sorted_buckets:
            report_lines.extend([
                f"{bucket_id}: {data['title']}",
                f"• Messages: {data['count']} ({data['percentage']:.1f}% of total)",
                f"• Conversion Rate: {data['conversion_rate']:.1f}%",
                f"• BGC Conversion Rate: {data['bgc_conversion_rate']:.1f}%",
                ""
            ])
    
    # Sample classifications for validation
    if results['sample_classifications']:
        report_lines.extend([
            "SAMPLE CLASSIFICATIONS (for validation)",
            "=" * 38,
            ""
        ])
        
        for idx, data in list(results['sample_classifications'].items())[:10]:
            report_lines.extend([
                f"Message: {data['message']}",
                f"Classified as: {data['bucket']}",
                f"Converted: {'Yes' if data['conversion'] else 'No'}",
                ""
            ])
    
    # Key insights
    report_lines.extend([
        "KEY INSIGHTS",
        "=" * 12,
        ""
    ])
    
    classification_rate = stats['classification_rate']
    if classification_rate >= 70:
        report_lines.append(f"✓ EXCELLENT: {classification_rate:.1f}% classification rate meets production standards (>70%)")
    elif classification_rate >= 50:
        report_lines.append(f"⚠ GOOD: {classification_rate:.1f}% classification rate, approaching production standards")
    else:
        report_lines.append(f"✗ NEEDS IMPROVEMENT: {classification_rate:.1f}% classification rate below production standards")
    
    report_lines.extend([
        f"• Using {stats['unique_buckets_used']}/59 available buckets ({(stats['unique_buckets_used']/59)*100:.1f}% utilization)",
        ""
    ])
    
    if results['bucket_performance']:
        # Find top performing bucket
        top_bucket = max(results['bucket_performance'].items(), key=lambda x: x[1]['conversion_rate'])
        report_lines.extend([
            f"Top Performing Bucket: {top_bucket[0]} ({top_bucket[1]['title']})",
            f"• {top_bucket[1]['conversion_rate']:.1f}% conversion rate with {top_bucket[1]['count']} messages",
            ""
        ])
        
        # Find most frequent bucket
        frequent_bucket = max(results['bucket_performance'].items(), key=lambda x: x[1]['count'])
        report_lines.extend([
            f"Most Frequent Bucket: {frequent_bucket[0]} ({frequent_bucket[1]['title']})",
            f"• {frequent_bucket[1]['count']} messages ({frequent_bucket[1]['percentage']:.1f}% of total)",
            ""
        ])
    
    # Save report
    report_text = "\n".join(report_lines)
    output_file = f"final_results/upf_production_classification_{timestamp}.txt"
    
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    # Save classified data
    if analyzed_df is not None:
        classified_file = f"final_results/upf_production_classified_{timestamp}.csv"
        analyzed_df.to_csv(classified_file, index=False)
    else:
        classified_file = None
    
    return output_file, classified_file, report_text

def main():
    print("Loading data and original JSON buckets...")
    messages_df, buckets = load_data()
    
    print(f"Loaded {len(messages_df):,} messages")
    print(f"Original JSON buckets: {len(buckets)}")
    print(f"Tag groups: {messages_df['tag_grouping'].unique()}")
    print(f"Message directions: {messages_df['direction'].unique()}")
    
    print("\nAnalyzing UpF inbound messages with production-like classification...")
    results, analyzed_df = analyze_upf_inbound_production(messages_df, buckets)
    
    print("\nGenerating production classification report...")
    report_file, classified_file, report_text = generate_production_analysis_report(results, analyzed_df, buckets)
    
    if report_file:
        print(f"\nProduction Classification Analysis complete!")
        print(f"Report saved to: {report_file}")
        if classified_file:
            print(f"Classified data saved to: {classified_file}")
        
        print("\n" + "="*50)
        print("QUICK SUMMARY")
        print("="*50)
        
        if results:
            stats = results['classification_stats']
            print(f"UpF Inbound Messages: {stats['total_messages']:,}")
            print(f"Classification Rate: {stats['classification_rate']:.1f}%")
            print(f"Active Buckets: {stats['unique_buckets_used']}/59")
            
            if stats['classification_rate'] >= 70:
                print("✓ Meets production classification standards!")
            else:
                print("⚠ Below production classification standards")
    else:
        print("No UpF inbound messages found for analysis")

if __name__ == "__main__":
    main()
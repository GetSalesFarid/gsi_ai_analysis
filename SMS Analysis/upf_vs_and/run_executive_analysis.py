#!/usr/bin/env python3

import pandas as pd
import re
from datetime import datetime
from collections import defaultdict, Counter

def load_data():
    """Load messages data"""
    messages_df = pd.read_csv('input_data/BGC_vs_AND_messages.csv')
    
    with open('input_data/message_effectiveness_claude_prompt.txt', 'r') as f:
        prompt = f.read()
    
    return messages_df, prompt

def classify_message_20_category(message_text):
    """Classify messages using the proven 20-category system"""
    message_lower = message_text.lower()
    
    # Define the 20 categories with identification patterns
    categories = {
        'Equipment Concerns': [
            'red card', 'hot bag', 'equipment', 'delivery bag', 'card declined',
            'need equipment', 'missing card', 'activation kit'
        ],
        'Market Concerns': [
            'slow market', 'no orders', 'dead zone', 'not busy', 'market dead',
            'area slow', 'not getting orders', 'waiting for orders'
        ],
        'Personal Circumstances': [
            'busy', 'family', 'personal', 'kids', 'life', 'circumstances',
            'situation', 'schedule conflict', 'family obligations'
        ],
        'Needs Guidance': [
            'how to', 'help', 'guidance', 'confused', 'dont know', "don't know",
            'what do i', 'need help', 'not sure', 'questions'
        ],
        'Payment Questions': [
            'payment', 'pay', 'money', 'earnings', 'when paid', 'direct deposit',
            'bank', 'cash out', 'weekly pay'
        ],
        'Scheduling Issues': [
            'schedule', 'time', 'hours', 'when', 'availability', 'dash now',
            'calendar', 'book time', 'reserve time'
        ],
        'Background Check': [
            'background check', 'checkr', 'background', 'criminal', 'record',
            'pending check', 'background pending'
        ],
        'App Issues': [
            'app', 'login', 'password', 'technical', 'phone', 'crash',
            'bug', 'glitch', 'not working', 'error'
        ],
        'Vehicle Issues': [
            'car', 'vehicle', 'transportation', 'bike', 'scooter',
            'car problems', 'no car', 'vehicle requirements'
        ],
        'Documents': [
            'documents', 'license', 'insurance', 'registration', 'upload',
            'photo', 'id', 'drivers license'
        ],
        'Location Questions': [
            'area', 'zone', 'location', 'where', 'city', 'region',
            'delivery area', 'zones available'
        ],
        'No Interest': [
            'not interested', 'changed mind', 'dont want', "don't want",
            'no longer', 'decided against'
        ],
        'Already Working': [
            'already working', 'got job', 'full time', 'employed',
            'other job', 'working elsewhere'
        ],
        'Process Questions': [
            'process', 'how does', 'what happens', 'next steps',
            'procedure', 'workflow', 'how it works'
        ],
        'Encouragement': [
            'thanks', 'appreciate', 'good', 'great', 'excited',
            'looking forward', 'ready', 'motivated'
        ],
        'Earnings Concerns': [
            'earnings', 'income', 'profit', 'worth it', 'gas money',
            'expenses', 'costs', 'profitable'
        ],
        'Competition': [
            'uber', 'lyft', 'grubhub', 'instacart', 'other apps',
            'competitor', 'comparison'
        ],
        'Contact Issues': [
            'phone', 'call', 'text', 'contact', 'reach',
            'communication', 'message', 'respond'
        ],
        'Wait Time': [
            'waiting', 'long time', 'been waiting', 'how long',
            'delay', 'taking forever', 'still waiting'
        ],
        'Other': [
            'other', 'misc', 'general', 'unclear'
        ]
    }
    
    # Check each category
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in message_lower:
                return category
    
    return 'Unclassified'

def analyze_executive_summary(messages_df):
    """Generate executive summary analysis"""
    
    # Classify all messages
    print("Classifying messages using 20-category system...")
    messages_df['category'] = messages_df['message'].apply(lambda x: classify_message_20_category(str(x)))
    
    # Results structure
    results = {
        'tag_group_summary': {},
        'category_performance': {},
        'overall_stats': {}
    }
    
    # Overall stats
    total_messages = len(messages_df)
    classified_messages = len(messages_df[messages_df['category'] != 'Unclassified'])
    overall_classification_rate = (classified_messages / total_messages) * 100
    
    results['overall_stats'] = {
        'total_messages': total_messages,
        'classification_rate': overall_classification_rate,
        'categories_used': messages_df['category'].nunique()
    }
    
    # Tag group analysis
    tag_groups = messages_df['tag_grouping'].unique()
    
    for tag in tag_groups:
        tag_data = messages_df[messages_df['tag_grouping'] == tag]
        classified_tag = tag_data[tag_data['category'] != 'Unclassified']
        
        results['tag_group_summary'][tag] = {
            'total_leads': len(tag_data),
            'classification_rate': (len(classified_tag) / len(tag_data)) * 100,
            'conversion_rate': tag_data['full_conversion'].mean() * 100,
            'bgc_conversion_rate': tag_data['bgc_conversion_7d'].mean() * 100 if 'bgc_conversion_7d' in tag_data.columns else 0
        }
    
    # Category performance analysis
    categories = messages_df['category'].unique()
    
    for category in categories:
        if category == 'Unclassified':
            continue
            
        category_data = messages_df[messages_df['category'] == category]
        
        # Overall category stats
        results['category_performance'][category] = {
            'total_messages': len(category_data),
            'percentage_of_all': (len(category_data) / total_messages) * 100,
            'overall_conversion': category_data['full_conversion'].mean() * 100,
            'by_tag_group': {}
        }
        
        # Performance by tag group
        for tag in tag_groups:
            tag_category_data = category_data[category_data['tag_grouping'] == tag]
            if len(tag_category_data) > 0:
                results['category_performance'][category]['by_tag_group'][tag] = {
                    'count': len(tag_category_data),
                    'conversion_rate': tag_category_data['full_conversion'].mean() * 100
                }
        
        # Find best performing group
        best_group = None
        best_conversion = 0
        for tag, data in results['category_performance'][category]['by_tag_group'].items():
            if data['count'] >= 5 and data['conversion_rate'] > best_conversion:  # Minimum 5 messages
                best_conversion = data['conversion_rate']
                best_group = tag
        
        results['category_performance'][category]['best_performing_group'] = best_group
    
    return results, messages_df

def generate_executive_summary(results, messages_df):
    """Generate the executive summary report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_lines = []
    
    # Header
    report_lines.extend([
        "EXECUTIVE SUMMARY - MESSAGE EFFECTIVENESS ANALYSIS",
        "=" * 49,
        f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Classification System: 20-Category Strategic System",
        "",
        "TAG GROUP PERFORMANCE OVERVIEW",
        "=" * 30,
    ])
    
    # Tag group performance
    for tag, summary in results['tag_group_summary'].items():
        report_lines.extend([
            f"{tag} Group:",
            f"• Total Leads: {summary['total_leads']:,}",
            f"• Classification Success Rate: {summary['classification_rate']:.1f}%",
            f"• Conversion Rate: {summary['conversion_rate']:.1f}%",
            f"• BGC Conversion Rate: {summary['bgc_conversion_rate']:.1f}%",
            ""
        ])
    
    # Category performance breakdown
    report_lines.extend([
        "CATEGORY PERFORMANCE BREAKDOWN",
        "=" * 30,
        ""
    ])
    
    # Sort categories by total messages (most frequent first)
    sorted_categories = sorted(
        results['category_performance'].items(),
        key=lambda x: x[1]['total_messages'],
        reverse=True
    )
    
    for category, data in sorted_categories:
        if data['total_messages'] < 5:  # Skip categories with very few messages
            continue
            
        report_lines.extend([
            f"{category}:",
            f"• Total Messages: {data['total_messages']} ({data['percentage_of_all']:.1f}% of all messages)",
        ])
        
        # Performance by tag group
        for tag in ['UpF', 'AnD', 'AnD AI']:
            if tag in data['by_tag_group']:
                tag_data = data['by_tag_group'][tag]
                report_lines.append(f"• {tag}: {tag_data['count']} messages, {tag_data['conversion_rate']:.1f}% conversion")
        
        if data['best_performing_group']:
            report_lines.append(f"• Best Performing Group: {data['best_performing_group']}")
        
        report_lines.append("")
    
    # Key insights
    report_lines.extend([
        "KEY INSIGHTS & RECOMMENDATIONS",
        "=" * 30,
        ""
    ])
    
    # High-performance categories (>30% conversion)
    high_performance = [(cat, data) for cat, data in results['category_performance'].items() 
                       if data['overall_conversion'] > 30 and data['total_messages'] >= 10]
    high_performance.sort(key=lambda x: x[1]['overall_conversion'], reverse=True)
    
    if high_performance:
        report_lines.append("High-Performance Categories (>30% conversion):")
        for category, data in high_performance:
            report_lines.append(f"• {category}: {data['overall_conversion']:.1f}% conversion")
        report_lines.append("")
    
    # Underperforming categories (<20% conversion)
    low_performance = [(cat, data) for cat, data in results['category_performance'].items() 
                      if data['overall_conversion'] < 20 and data['total_messages'] >= 10]
    low_performance.sort(key=lambda x: x[1]['overall_conversion'])
    
    if low_performance:
        report_lines.append("Underperforming Categories (<20% conversion):")
        for category, data in low_performance:
            report_lines.append(f"• {category}: {data['overall_conversion']:.1f}% conversion")
        report_lines.append("")
    
    # Tag group analysis
    report_lines.append("Tag Group Analysis:")
    
    # Find best overall performing group
    best_tag = max(results['tag_group_summary'].items(), key=lambda x: x[1]['conversion_rate'])
    report_lines.append(f"• Best Overall Performance: {best_tag[0]} ({best_tag[1]['conversion_rate']:.1f}% conversion)")
    
    # AI vs traditional comparison
    and_ai_rate = results['tag_group_summary'].get('AnD AI', {}).get('conversion_rate', 0)
    and_rate = results['tag_group_summary'].get('AnD', {}).get('conversion_rate', 0)
    upf_rate = results['tag_group_summary'].get('UpF', {}).get('conversion_rate', 0)
    
    if and_ai_rate > 0:
        ai_improvement = and_ai_rate - and_rate
        report_lines.append(f"• AI vs Traditional AnD: {ai_improvement:+.1f} percentage point improvement")
        
        if and_ai_rate > upf_rate:
            report_lines.append(f"• AI outperforms UpF by {and_ai_rate - upf_rate:.1f} percentage points")
    
    report_lines.extend([
        "",
        "Recommendations:",
        "1. Focus resources on high-converting categories (Equipment, Market, Personal)",
        "2. Investigate and improve messaging for underperforming categories",
        "3. Scale AI-powered approaches if AnD AI shows superior performance",
        "4. Analyze successful message patterns in top-performing categories",
        "5. Consider redistributing effort away from consistently low-converting categories"
    ])
    
    # Save report
    report_text = "\n".join(report_lines)
    output_file = f"final_results/executive_summary_{timestamp}.txt"
    
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    # Save classified data
    classified_file = f"final_results/executive_classified_{timestamp}.csv"
    messages_df.to_csv(classified_file, index=False)
    
    return output_file, classified_file, report_text

def main():
    print("Loading data...")
    messages_df, prompt = load_data()
    
    print(f"Loaded {len(messages_df):,} messages")
    print(f"Tag groups: {messages_df['tag_grouping'].unique()}")
    
    print("\nAnalyzing with 20-category system...")
    results, classified_df = analyze_executive_summary(messages_df)
    
    print("\nGenerating executive summary...")
    report_file, classified_file, report_text = generate_executive_summary(results, classified_df)
    
    print(f"\nExecutive Summary complete!")
    print(f"Report saved to: {report_file}")
    print(f"Classified data saved to: {classified_file}")
    
    print("\n" + "="*50)
    print("QUICK SUMMARY")
    print("="*50)
    
    # Print key metrics
    for tag, summary in results['tag_group_summary'].items():
        print(f"{tag}: {summary['conversion_rate']:.1f}% conversion, "
              f"{summary['classification_rate']:.1f}% classified, "
              f"{summary['total_leads']:,} leads")
    
    # Show top categories
    print(f"\nClassification Rate: {results['overall_stats']['classification_rate']:.1f}%")
    print(f"Active Categories: {results['overall_stats']['categories_used']}/20")

if __name__ == "__main__":
    main()
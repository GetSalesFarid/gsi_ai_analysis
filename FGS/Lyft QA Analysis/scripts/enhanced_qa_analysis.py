#!/usr/bin/env python3
"""
Enhanced QA Analysis with Real Task Content
Analyzes actual call summaries and SMS messages from top vs low performers
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import re
from datetime import datetime

def load_all_data():
    """Load and merge all data sources"""
    print("📊 Loading all data sources...")
    
    # Load performance data
    raw_data = pd.read_csv("data/bigquery_raw_data.csv")
    
    # Load real task content
    tasks_data = pd.read_csv("data/tasks_data_bigquery.csv")
    
    print(f"   📈 Raw opportunity data: {len(raw_data):,} records")
    print(f"   📱 Task data: {len(tasks_data):,} records")
    
    # Convert boolean conversion column
    raw_data['full_conversion'] = raw_data['full_conversion'].astype(bool)
    
    # Filter to usable tasks only
    usable_tasks = tasks_data[tasks_data['include_in_conext_analysis'] == True]
    print(f"   ✅ Usable tasks for analysis: {len(usable_tasks):,} records")
    
    return raw_data, usable_tasks

def identify_performance_tiers(raw_data):
    """Identify top and bottom performing reps"""
    print("\n🎯 Identifying performance tiers...")
    
    # Calculate rep-level performance
    rep_performance = raw_data.groupby('owner_username').agg({
        'full_conversion': ['count', 'sum', 'mean'],
        'owner_name': 'first'
    }).round(4)
    
    # Flatten column names
    rep_performance.columns = ['total_opps', 'conversions', 'conversion_rate', 'owner_name']
    
    # Filter for meaningful sample sizes (minimum 20 opportunities)
    rep_performance = rep_performance[rep_performance['total_opps'] >= 20]
    
    # Sort by conversion rate
    rep_performance = rep_performance.sort_values('conversion_rate', ascending=False)
    
    # Get top 20% and bottom 20%
    total_reps = len(rep_performance)
    top_count = max(3, int(total_reps * 0.2))
    bottom_count = max(3, int(total_reps * 0.2))
    
    top_performers = rep_performance.head(top_count).index.tolist()
    bottom_performers = rep_performance.tail(bottom_count).index.tolist()
    
    print(f"   🏆 Top {len(top_performers)} performers (conversion rate: {rep_performance.head(top_count)['conversion_rate'].min():.1%} - {rep_performance.head(top_count)['conversion_rate'].max():.1%})")
    for i, (username, data) in enumerate(rep_performance.head(top_count).iterrows(), 1):
        print(f"      {i}. {data['owner_name']} ({username}): {data['conversion_rate']:.1%}")
    
    print(f"   📉 Bottom {len(bottom_performers)} performers (conversion rate: {rep_performance.tail(bottom_count)['conversion_rate'].min():.1%} - {rep_performance.tail(bottom_count)['conversion_rate'].max():.1%})")
    for i, (username, data) in enumerate(rep_performance.tail(bottom_count).iterrows(), 1):
        print(f"      {i}. {data['owner_name']} ({username}): {data['conversion_rate']:.1%}")
    
    return top_performers, bottom_performers, rep_performance

def analyze_communication_patterns(tasks_data, top_performers, bottom_performers):
    """Analyze real communication patterns from task content"""
    print("\n🔍 Analyzing communication patterns...")
    
    # Filter tasks for our performance groups
    top_tasks = tasks_data[tasks_data['owner_username'].isin(top_performers)]
    bottom_tasks = tasks_data[tasks_data['owner_username'].isin(bottom_performers)]
    
    print(f"   📊 Top performer tasks: {len(top_tasks):,}")
    print(f"   📊 Bottom performer tasks: {len(bottom_tasks):,}")
    
    patterns = {}
    
    # 1. Task Type Distribution
    patterns['task_type_distribution'] = analyze_task_type_distribution(top_tasks, bottom_tasks)
    
    # 2. Call Content Analysis
    patterns['call_content'] = analyze_call_content(top_tasks, bottom_tasks)
    
    # 3. SMS Content Analysis  
    patterns['sms_content'] = analyze_sms_content(top_tasks, bottom_tasks)
    
    # 4. Response Time Analysis
    patterns['response_timing'] = analyze_response_timing(top_tasks, bottom_tasks)
    
    return patterns

def analyze_task_type_distribution(top_tasks, bottom_tasks):
    """Compare task type usage between groups"""
    print("     📈 Analyzing task type distribution...")
    
    top_dist = top_tasks['task_type'].value_counts(normalize=True)
    bottom_dist = bottom_tasks['task_type'].value_counts(normalize=True)
    
    analysis = {
        'top_distribution': top_dist.to_dict(),
        'bottom_distribution': bottom_dist.to_dict(),
        'insights': []
    }
    
    # Compare major task types
    for task_type in ['Call', 'SMS']:
        if task_type in top_dist and task_type in bottom_dist:
            diff = top_dist[task_type] - bottom_dist[task_type]
            if abs(diff) > 0.05:  # 5% difference threshold
                direction = "more" if diff > 0 else "less"
                analysis['insights'].append(f"Top performers use {direction} {task_type}s ({diff:+.1%})")
    
    return analysis

def analyze_call_content(top_tasks, bottom_tasks):
    """Analyze call summary content patterns"""
    print("     📞 Analyzing call content patterns...")
    
    top_calls = top_tasks[top_tasks['task_type'] == 'Call']['task_summary'].dropna()
    bottom_calls = bottom_tasks[bottom_tasks['task_type'] == 'Call']['task_summary'].dropna()
    
    # Skip analysis messages
    top_calls = top_calls[~top_calls.str.contains('ignore for analysis', case=False, na=False)]
    bottom_calls = bottom_calls[~bottom_calls.str.contains('ignore for analysis', case=False, na=False)]
    
    if len(top_calls) == 0 or len(bottom_calls) == 0:
        return {'insights': ['Insufficient call data for analysis']}
    
    analysis = {
        'top_call_count': len(top_calls),
        'bottom_call_count': len(bottom_calls),
        'insights': []
    }
    
    # Analyze key patterns
    patterns = {
        'urgency': ['today', 'now', 'immediately', 'asap', 'urgent', 'quickly'],
        'benefit': ['save', 'earn', 'benefit', 'money', 'income', 'profit', 'bonus'],
        'personal': ['you', 'your', 'specifically', 'personally', 'custom'],
        'action': ['start', 'begin', 'try', 'test', 'schedule', 'book', 'set up'],
        'follow_up': ['follow up', 'check in', 'touch base', 'following up'],
        'questions': ['?', 'how', 'what', 'when', 'where', 'why', 'which'],
        'positive': ['great', 'excellent', 'perfect', 'awesome', 'fantastic', 'amazing']
    }
    
    for pattern_name, keywords in patterns.items():
        top_usage = calculate_keyword_usage(top_calls, keywords)
        bottom_usage = calculate_keyword_usage(bottom_calls, keywords)
        
        if abs(top_usage - bottom_usage) > 0.1:  # 10% difference threshold
            direction = "more" if top_usage > bottom_usage else "less"
            analysis['insights'].append(
                f"Top performers use {direction} {pattern_name} language ({top_usage:.1%} vs {bottom_usage:.1%})"
            )
    
    # Average call summary length
    top_avg_length = top_calls.str.len().mean()
    bottom_avg_length = bottom_calls.str.len().mean()
    
    if abs(top_avg_length - bottom_avg_length) > 20:  # 20 character difference
        direction = "longer" if top_avg_length > bottom_avg_length else "shorter"
        analysis['insights'].append(
            f"Top performers write {direction} call summaries ({top_avg_length:.0f} vs {bottom_avg_length:.0f} chars)"
        )
    
    # Sample successful call summaries
    analysis['top_call_samples'] = top_calls.head(3).tolist()
    
    return analysis

def analyze_sms_content(top_tasks, bottom_tasks):
    """Analyze SMS message content patterns"""
    print("     💬 Analyzing SMS content patterns...")
    
    top_sms = top_tasks[top_tasks['task_type'] == 'SMS']['task_summary'].dropna()
    bottom_sms = bottom_tasks[bottom_tasks['task_type'] == 'SMS']['task_summary'].dropna()
    
    if len(top_sms) == 0 or len(bottom_sms) == 0:
        return {'insights': ['Insufficient SMS data for analysis']}
    
    analysis = {
        'top_sms_count': len(top_sms),
        'bottom_sms_count': len(bottom_sms),
        'insights': []
    }
    
    # Message characteristics
    top_avg_length = top_sms.str.len().mean()
    bottom_avg_length = bottom_sms.str.len().mean()
    
    top_question_rate = top_sms.str.contains('\\?').mean()
    bottom_question_rate = bottom_sms.str.contains('\\?').mean()
    
    # Compare metrics
    if abs(top_avg_length - bottom_avg_length) > 10:
        direction = "longer" if top_avg_length > bottom_avg_length else "shorter"
        analysis['insights'].append(
            f"Top performers send {direction} SMS messages ({top_avg_length:.0f} vs {bottom_avg_length:.0f} chars)"
        )
    
    if abs(top_question_rate - bottom_question_rate) > 0.1:
        direction = "more" if top_question_rate > bottom_question_rate else "fewer"
        analysis['insights'].append(
            f"Top performers ask {direction} questions in SMS ({top_question_rate:.1%} vs {bottom_question_rate:.1%})"
        )
    
    # Sample successful SMS messages
    analysis['top_sms_samples'] = top_sms.head(5).tolist()
    
    return analysis

def analyze_response_timing(top_tasks, bottom_tasks):
    """Analyze response timing patterns"""
    print("     ⏰ Analyzing response timing patterns...")
    
    # This would require timestamp analysis - placeholder for now
    return {
        'insights': ['Response timing analysis requires additional timestamp processing']
    }

def calculate_keyword_usage(text_series, keywords):
    """Calculate the percentage of texts containing any of the keywords"""
    pattern = '|'.join(re.escape(word.lower()) for word in keywords)
    matches = text_series.str.lower().str.contains(pattern, na=False)
    return matches.mean()

def generate_enhanced_report(patterns, top_performers, bottom_performers, rep_performance):
    """Generate comprehensive enhanced QA analysis report"""
    print("\n📝 Generating enhanced analysis report...")
    
    report_lines = []
    report_lines.append("# Enhanced Lyft QA Analysis - Communication Pattern Analysis")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("Analysis of actual call summaries and SMS messages to identify what top performers do differently.")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append(f"**Performance Analysis:**")
    report_lines.append(f"- Top {len(top_performers)} performers: {rep_performance.head(len(top_performers))['conversion_rate'].mean():.1%} avg conversion rate")
    report_lines.append(f"- Bottom {len(bottom_performers)} performers: {rep_performance.tail(len(bottom_performers))['conversion_rate'].mean():.1%} avg conversion rate")
    report_lines.append(f"- **Performance gap:** {rep_performance.head(len(top_performers))['conversion_rate'].mean() - rep_performance.tail(len(bottom_performers))['conversion_rate'].mean():.1%}")
    report_lines.append("")
    
    # Task Type Analysis
    if 'task_type_distribution' in patterns:
        task_dist = patterns['task_type_distribution']
        if task_dist['insights']:
            report_lines.append("### Communication Channel Preferences")
            for insight in task_dist['insights']:
                report_lines.append(f"- {insight}")
            report_lines.append("")
    
    # Call Content Analysis
    if 'call_content' in patterns:
        call_analysis = patterns['call_content']
        if call_analysis['insights']:
            report_lines.append("## Call Strategy Differences")
            report_lines.append("")
            report_lines.append(f"**Data Volume:** {call_analysis.get('top_call_count', 0)} top performer calls vs {call_analysis.get('bottom_call_count', 0)} bottom performer calls")
            report_lines.append("")
            
            report_lines.append("### Key Patterns Identified:")
            for insight in call_analysis['insights']:
                report_lines.append(f"- {insight}")
            report_lines.append("")
            
            if 'top_call_samples' in call_analysis:
                report_lines.append("### Example Successful Call Summaries:")
                for i, sample in enumerate(call_analysis['top_call_samples'], 1):
                    preview = sample[:200] + "..." if len(sample) > 200 else sample
                    report_lines.append(f"{i}. \"{preview}\"")
                report_lines.append("")
    
    # SMS Content Analysis
    if 'sms_content' in patterns:
        sms_analysis = patterns['sms_content']
        if sms_analysis['insights']:
            report_lines.append("## SMS Strategy Differences")
            report_lines.append("")
            report_lines.append(f"**Data Volume:** {sms_analysis.get('top_sms_count', 0)} top performer SMS vs {sms_analysis.get('bottom_sms_count', 0)} bottom performer SMS")
            report_lines.append("")
            
            report_lines.append("### Key Patterns Identified:")
            for insight in sms_analysis['insights']:
                report_lines.append(f"- {insight}")
            report_lines.append("")
            
            if 'top_sms_samples' in sms_analysis:
                report_lines.append("### Example Successful SMS Messages:")
                for i, sample in enumerate(sms_analysis['top_sms_samples'], 1):
                    preview = sample[:100] + "..." if len(sample) > 100 else sample
                    report_lines.append(f"{i}. \"{preview}\"")
                report_lines.append("")
    
    # Coaching Recommendations
    report_lines.append("## Coaching Recommendations")
    report_lines.append("")
    
    all_insights = []
    for pattern_type, pattern_data in patterns.items():
        if isinstance(pattern_data, dict) and 'insights' in pattern_data:
            all_insights.extend(pattern_data['insights'])
    
    if all_insights:
        report_lines.append("Based on the analysis of actual communication content, here are specific coaching recommendations:")
        report_lines.append("")
        
        for i, insight in enumerate(all_insights, 1):
            if "more" in insight.lower():
                # Convert insight to actionable recommendation
                recommendation = insight.replace("Top performers use more", "Train all reps to use more")
                recommendation = recommendation.replace("Top performers send longer", "Train all reps to send longer")
                recommendation = recommendation.replace("Top performers ask more", "Train all reps to ask more")
                report_lines.append(f"{i}. {recommendation}")
            elif "less" in insight.lower() or "shorter" in insight.lower() or "fewer" in insight.lower():
                # Convert negative patterns to positive recommendations
                recommendation = insight.replace("Top performers use less", "Reduce usage of")
                recommendation = recommendation.replace("Top performers send shorter", "Keep messages concise, use shorter")
                recommendation = recommendation.replace("Top performers ask fewer", "Focus questions, ask fewer")
                report_lines.append(f"{i}. {recommendation}")
        report_lines.append("")
    else:
        report_lines.append("No significant patterns identified in current data. Consider expanding analysis period or data sources.")
        report_lines.append("")
    
    # Top Performers Reference
    report_lines.append("## Top Performer Reference")
    report_lines.append("")
    report_lines.append("Use these top performers as coaching mentors:")
    report_lines.append("")
    
    for i, username in enumerate(top_performers, 1):
        rep_data = rep_performance.loc[username]
        report_lines.append(f"{i}. **{rep_data['owner_name']}** ({username})")
        report_lines.append(f"   - Conversion Rate: {rep_data['conversion_rate']:.1%}")
        report_lines.append(f"   - Volume: {rep_data['conversions']}/{rep_data['total_opps']} opportunities")
        report_lines.append("")
    
    return "\n".join(report_lines)

def main():
    """Main enhanced QA analysis workflow"""
    
    # Archive existing results
    import sys
    sys.path.append('../utilities')
    from archive_manager import ArchiveManager
    archive_manager = ArchiveManager()
    archive_manager.prepare_for_new_analysis()
    
    print("🔍 Starting enhanced QA analysis with real task content...")
    
    try:
        # Load all data
        raw_data, tasks_data = load_all_data()
        
        # Identify performance tiers
        top_performers, bottom_performers, rep_performance = identify_performance_tiers(raw_data)
        
        # Analyze communication patterns
        patterns = analyze_communication_patterns(tasks_data, top_performers, bottom_performers)
        
        # Generate report
        report = generate_enhanced_report(patterns, top_performers, bottom_performers, rep_performance)
        
        # Save results
        with open("results/enhanced_qa_analysis_report.md", "w") as f:
            f.write(report)
        
        # Save analysis data as JSON for further processing
        import json
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'top_performers': top_performers,
            'bottom_performers': bottom_performers,
            'patterns': patterns,
            'rep_performance': rep_performance.to_dict('index')
        }
        
        with open("results/enhanced_qa_analysis_data.json", "w") as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        print(f"\n✅ Enhanced QA analysis complete!")
        print(f"📁 Reports saved:")
        print(f"   - results/enhanced_qa_analysis_report.md")
        print(f"   - results/enhanced_qa_analysis_data.json")
        print(f"\n🎯 Ready to use findings for targeted coaching and training!")
        
    except Exception as e:
        print(f"❌ Enhanced analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
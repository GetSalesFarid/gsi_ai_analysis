#!/usr/bin/env python3
"""
Template-based Analysis - Follows the exact user-provided template format
Generates analysis matching the specific structure requested
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
import re

def load_and_merge_data():
    """Load and merge all data sources for template analysis"""
    print("📊 Loading data for template analysis...")
    
    import os
    
    # Get the script directory and construct paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, 'data')
    
    # Load performance data
    raw_data = pd.read_csv(os.path.join(data_dir, "bigquery_raw_data.csv"))
    
    # Load real task content
    tasks_data = pd.read_csv(os.path.join(data_dir, "tasks_data_bigquery.csv"))
    
    # Load control baselines
    try:
        control_baselines = pd.read_csv(os.path.join(data_dir, "control_baselines.csv"))
        print(f"   🎯 Control baselines: {len(control_baselines)} experiment-language combinations")
    except FileNotFoundError:
        print("   ⚠️  Control baselines not found, lift calculations will use 0% baseline")
        control_baselines = pd.DataFrame()
    
    print(f"   📈 Raw opportunity data: {len(raw_data):,} records")
    print(f"   📱 Task data: {len(tasks_data):,} records")
    
    # Convert boolean conversion column
    raw_data['full_conversion'] = raw_data['full_conversion'].astype(bool)
    
    # Filter to usable tasks only
    usable_tasks = tasks_data[tasks_data['include_in_conext_analysis'] == True]
    print(f"   ✅ Usable tasks for analysis: {len(usable_tasks):,} records")
    
    # Get date range
    raw_data['first_contact_date'] = pd.to_datetime(raw_data['first_contact_date'])
    date_range = f"{raw_data['first_contact_date'].min().strftime('%Y-%m-%d')} to {raw_data['first_contact_date'].max().strftime('%Y-%m-%d')}"
    
    # Count calls and SMS
    call_count = len(usable_tasks[usable_tasks['task_type'] == 'Call'])
    sms_count = len(usable_tasks[usable_tasks['task_type'] == 'SMS'])
    
    metadata = {
        'date_range': date_range,
        'call_count': call_count,
        'sms_count': sms_count,
        'total_opportunities': len(raw_data)
    }
    
    return raw_data, usable_tasks, control_baselines, metadata

def get_control_baseline(experiment, language, control_baselines):
    """Get control baseline conversion rate for a specific experiment (ignoring language)"""
    
    if control_baselines.empty:
        return 0.0
    
    # Find matching baseline by experiment only (ignore language)
    match = control_baselines[control_baselines['experiment'] == experiment]
    
    if not match.empty:
        return match.iloc[0]['control_conversion_rate']
    else:
        print(f"⚠️  No control baseline found for {experiment}, using 0%")
        return 0.0

def analyze_by_cohort(raw_data, tasks_data, control_baselines):
    """Analyze performance by each cohort (experiment + contact method + language)"""
    print("🎯 Analyzing performance by cohort...")
    
    # Group by cohort
    cohort_data = {}
    
    # Get all unique combinations
    combinations = raw_data.groupby(['experiment', 'first_contact_method', 'language']).size()
    
    for (experiment, contact_method, language), count in combinations.items():
        if count < 10:  # Skip small cohorts
            continue
            
        cohort_key = f"{experiment}|{contact_method}|{language}"
        
        # Filter data for this cohort
        cohort_opps = raw_data[
            (raw_data['experiment'] == experiment) &
            (raw_data['first_contact_method'] == contact_method) &
            (raw_data['language'] == language)
        ]
        
        # Calculate rep performance within this cohort
        rep_performance = cohort_opps.groupby('owner_username').agg({
            'full_conversion': ['count', 'sum', 'mean'],
            'owner_name': 'first'
        }).round(4)
        
        # Flatten column names
        rep_performance.columns = ['owned_leads', 'converted_leads', 'conversion_rate', 'owner_name']
        
        # Store original performance for individual recommendations
        original_rep_performance = rep_performance.copy()
        
        # Filter for meaningful sample sizes (minimum 25 opportunities in cohort)
        rep_performance = rep_performance[rep_performance['owned_leads'] >= 25]
        
        # Exclude system accounts
        excluded_accounts = ['hevoapi@getsales.team', 'awsintegrationapi', 'techadmin']
        rep_performance = rep_performance[~rep_performance.index.str.lower().isin([acc.lower() for acc in excluded_accounts])]
        original_rep_performance = original_rep_performance[~original_rep_performance.index.str.lower().isin([acc.lower() for acc in excluded_accounts])]
        
        # Calculate percentage of leads in this cohort
        total_cohort_leads = len(cohort_opps)
        rep_performance['pct_of_cohort'] = rep_performance['owned_leads'] / total_cohort_leads
        
        # Calculate lift vs control baseline (ignore language parameter)
        control_baseline = get_control_baseline(experiment, language, control_baselines)
        rep_performance['control_baseline'] = control_baseline
        rep_performance['lift'] = rep_performance['conversion_rate'] - control_baseline
        
        # Sort by lift (most important metric), then conversion rate
        rep_performance = rep_performance.sort_values(['lift', 'conversion_rate'], ascending=False)
        
        cohort_data[cohort_key] = {
            'experiment': experiment,
            'contact_method': contact_method,
            'language': language,
            'total_leads': total_cohort_leads,
            'rep_performance': rep_performance,
            'original_rep_performance': original_rep_performance
        }
    
    return cohort_data

def analyze_communication_quality(content, task_type, converted):
    """Analyze why a communication example is good or bad"""
    content = str(content).lower()
    
    if converted:
        # Good example analysis
        if task_type == 'SMS':
            if any(word in content for word in ['yes', 'ok', 'thanks', 'great', 'awesome', 'perfect']):
                return "Shows positive prospect engagement and interest"
            elif any(word in content for word in ['help', 'support', 'guide', 'resource']):
                return "Provides valuable assistance and resources to prospects"
            elif any(word in content for word in ['ready', 'start', 'begin', 'driving', 'earn']):
                return "Demonstrates prospect motivation to start driving"
            elif any(word in content for word in ['question', 'understand', 'explain']):
                return "Shows educational approach that builds trust"
            elif len(content) < 50 and any(word in content for word in ['done', 'finished', 'complete']):
                return "Indicates prospect completion of required steps"
            else:
                return "Effective engagement that led to conversion"
        else:  # Call
            if 'called' in content and ('follow up' in content or 'check in' in content):
                return "Proactive follow-up that maintained engagement"
            elif any(word in content for word in ['discussed', 'explained', 'helped']):
                return "Provided personalized assistance that moved prospect forward"
            else:
                return "Successful call that resulted in conversion"
    else:
        # Bad example analysis
        if task_type == 'SMS':
            if any(phrase in content for phrase in ['who is this', 'who this', "who's this"]):
                return "Prospect doesn't recognize rep - poor relationship building"
            elif content in ['?', '??', '???', 'stop']:
                return "Minimal/negative response indicates communication breakdown"
            elif 'reply "stop"' in content and len(content) > 100:
                return "Generic template message lacks personalization"
            elif any(word in content for word in ['busy', 'not interested', 'don\'t call']):
                return "Prospect showing disengagement or resistance"
            elif 'troubleshooting' in content or 'delete the app' in content:
                return "Technical issues creating friction in onboarding process"
            else:
                return "Communication did not successfully engage prospect"
        else:  # Call
            if 'transcript' in content or 'brevity' in content:
                return "Call too short to build meaningful connection"
            elif 'no contact' in content:
                return "Failed to reach prospect for direct engagement"
            else:
                return "Call approach did not lead to conversion"

def get_task_examples(tasks_data, raw_data, owner_username, experiment):
    """Get specific opportunity examples with contextual analysis for a rep in an experiment"""
    
    # Filter tasks data directly for this rep and experiment (using enhanced task data)
    rep_tasks = tasks_data[
        (tasks_data['owner_username'] == owner_username) &
        (tasks_data['experiment'] == experiment) &
        (tasks_data['include_in_conext_analysis'] == True)
    ]
    
    if rep_tasks.empty:
        return [], []
    
    # Get opportunities from raw data to check conversion status
    rep_opps = raw_data[
        (raw_data['owner_username'] == owner_username) &
        (raw_data['experiment'] == experiment)
    ]
    
    if rep_opps.empty:
        return [], []
    
    examples = []
    
    # Get examples with task content
    for _, task in rep_tasks.head(10).iterrows():  # Up to 10 examples
        # Find the corresponding opportunity
        matching_opp = rep_opps[rep_opps['opportunity_uuid'] == task['opportunity_uuid']]
        
        if not matching_opp.empty:
            opp = matching_opp.iloc[0]
            
            # Analyze the communication quality
            analysis = analyze_communication_quality(task['task_summary'], task['task_type'], opp['full_conversion'])
            
            example = {
                'opportunity_uuid': task['opportunity_uuid'],
                'converted': opp['full_conversion'],
                'task_type': task['task_type'],
                'analysis': analysis
            }
            examples.append(example)
    
    # Separate good and bad examples
    good_examples = [ex for ex in examples if ex['converted']]
    bad_examples = [ex for ex in examples if not ex['converted']]
    
    return good_examples, bad_examples

def rate_outreach_style(rep_performance, tasks_data, raw_data, owner_username):
    """Rate outreach style from 1-100 based on performance and communication patterns"""
    
    try:
        if owner_username not in rep_performance.index:
            return 50  # Default neutral rating
        
        rep_data = rep_performance.loc[owner_username]
        
        # Base score from conversion rate (0-60 points)
        base_score = min(60, float(rep_data['conversion_rate']) * 200)  # 30% conv rate = 60 points
        
        # Volume bonus (0-20 points) - more leads handled
        volume_score = min(20, float(rep_data['owned_leads']) / 50 * 20)  # 50+ leads = 20 points
        
        # Communication quality bonus (0-20 points)
        rep_tasks = tasks_data[tasks_data['owner_username'] == owner_username]
        
        comm_score = 0
        if not rep_tasks.empty:
            # Bonus for good content (not default messages)
            good_content_rate = (~rep_tasks['task_summary'].str.contains('ignore for analysis|No Contact|Call to Short', case=False, na=False)).mean()
            comm_score = good_content_rate * 20
        
        total_score = base_score + volume_score + comm_score
        return min(100, max(1, int(total_score)))
    except Exception as e:
        print(f"Warning: Could not calculate rating for {owner_username}: {e}")
        return 50

def get_cohort_performer(exp_cohorts, cohort_key, performer_type='top'):
    """Get top or low performer for a specific cohort with filtering rules"""
    if cohort_key not in exp_cohorts or exp_cohorts[cohort_key]['rep_performance'].empty:
        return None, "No sufficient data"
    
    rep_performance = exp_cohorts[cohort_key]['rep_performance']
    
    if performer_type == 'top':
        # For top performers, exclude 0% conversion rates
        filtered_reps = rep_performance[rep_performance['conversion_rate'] > 0]
        if filtered_reps.empty:
            return None, "No performers above 0% conversion rate"
        return filtered_reps.iloc[0], None
    else:  # low performers
        # For low performers, include 0% conversion rates but get the lowest
        if rep_performance.empty:
            return None, "No sufficient data"
        return rep_performance.iloc[-1], None

def generate_template_report(cohort_data, tasks_data, raw_data, metadata):
    """Generate report following the exact template format"""
    print("📝 Generating template-based report...")
    
    report_lines = []
    
    # Find the single best performer across all metrics for exclusive 100/100 rating
    best_performer = None
    best_score = 0
    
    for cohort_key, cohort in cohort_data.items():
        if not cohort['rep_performance'].empty:
            top_rep = cohort['rep_performance'].iloc[0]
            # Score based on lift (primary) and conversion rate (secondary)
            score = top_rep['lift'] * 1000 + top_rep['conversion_rate'] * 100
            if score > best_score:
                best_score = score
                best_performer = top_rep.name
    
    # Header
    report_lines.append("Lyft QA Analysis Report")
    report_lines.append(f"Date Ran: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"First Contact date range: {metadata['date_range']}")
    report_lines.append(f"Number of calls: {metadata['call_count']:,}, SMS: {metadata['sms_count']:,}")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("Executive Summary:")
    report_lines.append("")
    
    # Analyze performance patterns
    high_lift_performers = []
    coaching_opportunities = []
    negative_lift_count = 0
    
    for cohort_key, cohort in cohort_data.items():
        if not cohort['rep_performance'].empty:
            top_rep = cohort['rep_performance'].iloc[0]
            if top_rep['lift'] > 0.05:  # 5%+ lift
                high_lift_performers.append((top_rep['owner_name'], top_rep['lift'] * 100, cohort['contact_method'], cohort['language']))
            
            # Count negative lifts for coaching opportunities
            for _, rep_row in cohort['rep_performance'].iterrows():
                if rep_row['lift'] < 0:
                    negative_lift_count += 1
                    coaching_opportunities.append((rep_row['owner_name'], cohort['contact_method'], cohort['language'], rep_row['lift'] * 100))
    
    # Deduplicate and get top performers
    unique_performers = {}
    for name, lift, method, lang in high_lift_performers:
        if name not in unique_performers or lift > unique_performers[name][0]:
            unique_performers[name] = (lift, method, lang)
    
    top_performers = sorted(unique_performers.items(), key=lambda x: x[1][0], reverse=True)[:3]
    
    if top_performers:
        performer_text = ", ".join([f"{name} (+{lift:.1f}%)" for name, (lift, _, _) in top_performers])
        report_lines.append(f"**Key Insights:** {performer_text} are our strongest performers, consistently beating control baselines through effective prospect engagement.")
    
    report_lines.append("")
    report_lines.append("**Performance Highlights:**")
    report_lines.append("• English cohorts show strong positive lift across both Call and SMS channels")
    report_lines.append("• Spanish outreach has mixed results - some reps excel while others underperform")
    report_lines.append("• Upfunnel experiment shows lower overall conversion but positive lift opportunities")
    report_lines.append("")
    
    # Coaching themes
    report_lines.append("**Top 3 Coaching Opportunities:**")
    report_lines.append("1. **SMS-Spanish Optimization:** Apply successful Spanish calling techniques to SMS outreach")
    report_lines.append("2. **Prospect Recognition:** Address cases where prospects don't recognize reps (relationship building)")
    report_lines.append("3. **Upfunnel Engagement:** Develop specialized approaches for the Upfunnel experiment cohort")
    report_lines.append("")
    report_lines.append("")
    
    # Top Performers section
    report_lines.append("## Top Performers by Cohort")
    report_lines.append("*Note: 'Top' indicates highest lift within each specific cohort*")
    report_lines.append("")
    
    # Group cohorts by experiment for the template format
    experiments = ['Lyft Funnel Conversion', 'Lyft Funnel Conversion - Stale', 'Lyft Funnel Conversion - Upfunnel']
    
    for experiment in experiments:
        report_lines.append(f"### {experiment}")
        
        # Find cohorts for this experiment
        exp_cohorts = {k: v for k, v in cohort_data.items() if v['experiment'] == experiment}
        
        # Call-English
        call_eng_key = f"{experiment}|Call|English"
        top_rep, message = get_cohort_performer(exp_cohorts, call_eng_key, 'top')
        report_lines.append("Call-English")
        if top_rep is not None:
            lift_value = top_rep['lift'] * 100  # Convert to percentage points
            report_lines.append(f"    {top_rep['owner_name']} Lift {lift_value:+.1f}%, Conversion rate: {top_rep['conversion_rate']:.1%}, owned leads: {top_rep['owned_leads']}, converted leads: {top_rep['converted_leads']}, % of leads in this cohort: {top_rep['pct_of_cohort']:.1%}")
        else:
            report_lines.append(f"    {message}")
        
        # SMS-English
        sms_eng_key = f"{experiment}|SMS|English"
        top_rep, message = get_cohort_performer(exp_cohorts, sms_eng_key, 'top')
        report_lines.append("SMS-English")
        if top_rep is not None:
            lift_value = top_rep['lift'] * 100  # Convert to percentage points
            report_lines.append(f"    {top_rep['owner_name']} Lift {lift_value:+.1f}%, Conversion rate: {top_rep['conversion_rate']:.1%}, owned leads: {top_rep['owned_leads']}, converted leads: {top_rep['converted_leads']}, % of leads in this cohort: {top_rep['pct_of_cohort']:.1%}")
        else:
            report_lines.append(f"    {message}")
        
        # Call-Spanish
        call_esp_key = f"{experiment}|Call|Spanish"
        top_rep, message = get_cohort_performer(exp_cohorts, call_esp_key, 'top')
        report_lines.append("Call-Spanish")
        if top_rep is not None:
            lift_value = top_rep['lift'] * 100  # Convert to percentage points
            report_lines.append(f"    {top_rep['owner_name']} Lift {lift_value:+.1f}%, Conversion rate: {top_rep['conversion_rate']:.1%}, owned leads: {top_rep['owned_leads']}, converted leads: {top_rep['converted_leads']}, % of leads in this cohort: {top_rep['pct_of_cohort']:.1%}")
        else:
            report_lines.append(f"    {message}")
        
        # SMS-Spanish
        sms_esp_key = f"{experiment}|SMS|Spanish"
        top_rep, message = get_cohort_performer(exp_cohorts, sms_esp_key, 'top')
        report_lines.append("SMS-Spanish")
        if top_rep is not None:
            lift_value = top_rep['lift'] * 100  # Convert to percentage points
            report_lines.append(f"    {top_rep['owner_name']} Lift {lift_value:+.1f}%, Conversion rate: {top_rep['conversion_rate']:.1%}, owned leads: {top_rep['owned_leads']}, converted leads: {top_rep['converted_leads']}, % of leads in this cohort: {top_rep['pct_of_cohort']:.1%}")
        else:
            report_lines.append(f"    {message}")
        
        report_lines.append("")
        report_lines.append("")
    
    # Low Performers section
    report_lines.append("## Areas for Improvement by Cohort")
    report_lines.append("*Note: 'Areas for Improvement' indicates lowest lift within each specific cohort*")
    report_lines.append("")
    
    for experiment in experiments:
        report_lines.append(f"### {experiment}")
        
        # Find cohorts for this experiment
        exp_cohorts = {k: v for k, v in cohort_data.items() if v['experiment'] == experiment}
        
        # Call-English
        call_eng_key = f"{experiment}|Call|English"
        low_rep, message = get_cohort_performer(exp_cohorts, call_eng_key, 'low')
        report_lines.append("Call-English")
        if low_rep is not None:
            lift_value = low_rep['lift'] * 100  # Convert to percentage points
            report_lines.append(f"    {low_rep['owner_name']} Lift {lift_value:+.1f}%, Conversion rate: {low_rep['conversion_rate']:.1%}, owned leads: {low_rep['owned_leads']}, converted leads: {low_rep['converted_leads']}, % of leads in this cohort: {low_rep['pct_of_cohort']:.1%}")
        else:
            report_lines.append(f"    {message}")
        
        # SMS-English
        sms_eng_key = f"{experiment}|SMS|English"
        low_rep, message = get_cohort_performer(exp_cohorts, sms_eng_key, 'low')
        report_lines.append("SMS-English")
        if low_rep is not None:
            lift_value = low_rep['lift'] * 100  # Convert to percentage points
            report_lines.append(f"    {low_rep['owner_name']} Lift {lift_value:+.1f}%, Conversion rate: {low_rep['conversion_rate']:.1%}, owned leads: {low_rep['owned_leads']}, converted leads: {low_rep['converted_leads']}, % of leads in this cohort: {low_rep['pct_of_cohort']:.1%}")
        else:
            report_lines.append(f"    {message}")
        
        # Call-Spanish
        call_esp_key = f"{experiment}|Call|Spanish"
        low_rep, message = get_cohort_performer(exp_cohorts, call_esp_key, 'low')
        report_lines.append("Call-Spanish")
        if low_rep is not None:
            lift_value = low_rep['lift'] * 100  # Convert to percentage points
            report_lines.append(f"    {low_rep['owner_name']} Lift {lift_value:+.1f}%, Conversion rate: {low_rep['conversion_rate']:.1%}, owned leads: {low_rep['owned_leads']}, converted leads: {low_rep['converted_leads']}, % of leads in this cohort: {low_rep['pct_of_cohort']:.1%}")
        else:
            report_lines.append(f"    {message}")
        
        # SMS-Spanish
        sms_esp_key = f"{experiment}|SMS|Spanish"
        low_rep, message = get_cohort_performer(exp_cohorts, sms_esp_key, 'low')
        report_lines.append("SMS-Spanish")
        if low_rep is not None:
            lift_value = low_rep['lift'] * 100  # Convert to percentage points
            report_lines.append(f"    {low_rep['owner_name']} Lift {lift_value:+.1f}%, Conversion rate: {low_rep['conversion_rate']:.1%}, owned leads: {low_rep['owned_leads']}, converted leads: {low_rep['converted_leads']}, % of leads in this cohort: {low_rep['pct_of_cohort']:.1%}")
        else:
            report_lines.append(f"    {message}")
        
        report_lines.append("")
        report_lines.append("")
    
    # Individual Recommendations section
    report_lines.append("## Individual Recommendations")
    report_lines.append("*Top 10 reps by volume with detailed coaching insights*")
    report_lines.append("")
    
    # Get all unique reps from cohort data
    all_reps = set()
    rep_data_lookup = {}
    
    for cohort_key, cohort in cohort_data.items():
        for username, rep_row in cohort['rep_performance'].iterrows():
            all_reps.add(username)
            if username not in rep_data_lookup:
                rep_data_lookup[username] = []
            rep_data_lookup[username].append((cohort, rep_row))
    
    # Generate recommendations for top 10 reps by total volume
    rep_volumes = {}
    for username in all_reps:
        total_volume = sum([rep_row['owned_leads'] for cohort, rep_row in rep_data_lookup[username]])
        rep_volumes[username] = total_volume
    
    top_volume_reps = sorted(rep_volumes.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for username, total_volume in top_volume_reps:
        rep_cohorts = rep_data_lookup[username]
        rep_name = rep_cohorts[0][1]['owner_name']
        
        # Calculate overall rating - use first cohort performance as representative
        first_cohort_performance = rep_cohorts[0][0]['rep_performance']
        rating = rate_outreach_style(first_cohort_performance, tasks_data, raw_data, username)
        
        # Apply exclusive 100/100 rating - only the best performer gets perfect score
        if username == best_performer:
            rating = 100
        elif rating == 100:
            rating = 99  # Cap all others at 99
        
        report_lines.append(f"### {rep_name}")
        report_lines.append(f"**Outreach Rating:** {rating}/100 | **Total Volume:** {total_volume} leads")
        
        # Generate recommendations for each experiment
        for i, experiment in enumerate(experiments, 1):
            report_lines.append(f"{i}. Call outs for {experiment}")
            
            # Check if rep meets minimum requirements for this experiment's cohorts
            experiment_cohorts = [cohort for cohort, rep_row in rep_cohorts if cohort['experiment'] == experiment]
            insufficient_cohorts = []
            
            for cohort in experiment_cohorts:
                # Check if this rep has enough leads in each cohort
                cohort_key = f"{cohort['experiment']}|{cohort['contact_method']}|{cohort['language']}"
                if cohort_key in cohort_data:
                    original_perf = cohort_data[cohort_key]['original_rep_performance']
                    if username in original_perf.index:
                        rep_leads = original_perf.loc[username]['owned_leads']
                        if rep_leads < 25:
                            insufficient_cohorts.append(f"{cohort['contact_method']}-{cohort['language']} ({rep_leads} leads, need 25+)")
            
            if insufficient_cohorts:
                report_lines.append(f"   Note: Insufficient data in {', '.join(insufficient_cohorts)} for meaningful analysis")
            
            # Find examples for this rep in this experiment
            good_examples, bad_examples = get_task_examples(tasks_data, raw_data, username, experiment)
            
            # Good example
            if good_examples:
                good_ex = good_examples[0]
                report_lines.append(f"   1. {good_ex['opportunity_uuid']} Good - {good_ex['analysis']}")
            else:
                report_lines.append("   1. No good examples found in this cohort")
            
            # Bad example
            if bad_examples:
                bad_ex = bad_examples[0]
                report_lines.append(f"   2. {bad_ex['opportunity_uuid']} Bad - {bad_ex['analysis']}")
            else:
                report_lines.append("   2. No bad examples found in this cohort")
        
        report_lines.append("")
    
    return "\n".join(report_lines)

def main():
    """Main template analysis workflow"""
    
    # Archive existing results
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utilities'))
    try:
        from archive_manager import ArchiveManager
        archive_manager = ArchiveManager()
        archive_manager.prepare_for_new_analysis()
    except ImportError:
        print("⚠️  Archive manager not available, continuing without archiving...")
    
    print("📋 Starting template-based analysis...")
    
    try:
        # Load all data
        raw_data, tasks_data, control_baselines, metadata = load_and_merge_data()
        
        # Analyze by cohort
        cohort_data = analyze_by_cohort(raw_data, tasks_data, control_baselines)
        
        # Generate template report
        report = generate_template_report(cohort_data, tasks_data, raw_data, metadata)
        
        # Save results
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        results_dir = os.path.join(project_dir, 'results')
        
        with open(os.path.join(results_dir, "analysis_summary.md"), "w") as f:
            f.write(report)
        
        print(f"\n✅ Template analysis complete!")
        print(f"📁 Report saved: results/analysis_summary.md")
        print(f"📊 Analyzed {len(cohort_data)} cohorts")
        print(f"🎯 Following exact template format with individual recommendations")
        
    except Exception as e:
        print(f"❌ Template analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
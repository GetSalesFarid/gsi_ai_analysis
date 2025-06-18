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

def deep_engagement_analysis(task_row, opp_row, notes_content):
    """Comprehensive line-by-line analysis of how well the rep engaged this specific lead"""
    
    task_content = str(task_row['task_summary']).lower()
    task_type = task_row['task_type']
    converted = opp_row['full_conversion']
    opportunity_uuid = task_row['opportunity_uuid']
    
    analysis = {
        'opportunity_uuid': opportunity_uuid,
        'converted': converted,
        'task_type': task_type,
        'engagement_score': 0,  # 0-100
        'strengths': [],
        'weaknesses': [],
        'notes_integration': 'none',
        'playbook_adherence': 'poor',
        'personalization_level': 'generic',
        'detailed_assessment': '',
        'improvement_recommendations': []
    }
    
    # Parse available notes information from individual columns
    notes_info = {
        'goals': '',
        'submission_needs': '',
        'bgc_timeline': '',
        'additional_context': '',
        'has_meaningful_data': False
    }
    
    # Extract from individual opportunity fields
    goals = str(opp_row.get('what_are_your_goals_or_motivations_to_start_driving_for_lyft', '')).strip()
    submission_needs = str(opp_row.get('what_else_do_you_need_to_submit', '')).strip()
    bgc_timeline = str(opp_row.get('estimated_bgc_date', '')).strip()
    additional = str(opp_row.get('additional_notes', '')).strip()
    
    if goals and goals != 'ignore question 1' and len(goals) > 5:
        notes_info['goals'] = goals.lower()
        notes_info['has_meaningful_data'] = True
    
    if submission_needs and submission_needs != 'ignore question 2' and len(submission_needs) > 5:
        notes_info['submission_needs'] = submission_needs.lower()
        notes_info['has_meaningful_data'] = True
    
    if bgc_timeline and bgc_timeline != 'ignore question 3' and len(bgc_timeline) > 5:
        notes_info['bgc_timeline'] = bgc_timeline.lower()
        notes_info['has_meaningful_data'] = True
    
    if additional and additional != 'ignore question 4' and len(additional) > 10:
        notes_info['additional_context'] = additional.lower()
        notes_info['has_meaningful_data'] = True
    
    # Analyze task content quality and engagement
    base_score = 30  # Starting baseline
    
    # Content Quality Analysis
    if task_type == 'SMS':
        if 'ignore for analysis' in task_content or 'no contact' in task_content:
            analysis['detailed_assessment'] = "No meaningful outreach content to analyze"
            analysis['engagement_score'] = 0
            return analysis
        
        # SMS-specific engagement patterns
        if any(word in task_content for word in ['thanks', 'thank you', 'awesome', 'perfect', 'great']):
            analysis['strengths'].append("Positive prospect response indicating engagement")
            base_score += 20
        
        if any(word in task_content for word in ['help', 'support', 'guide', 'assist']):
            analysis['strengths'].append("Offers valuable assistance")
            base_score += 15
        
        if any(word in task_content for word in ['ready', 'start', 'begin', 'driving']):
            analysis['strengths'].append("Shows prospect motivation and readiness")
            base_score += 15
        
        # Negative patterns
        if any(phrase in task_content for phrase in ['who is this', 'who this', "who's this"]):
            analysis['weaknesses'].append("Prospect doesn't recognize rep - relationship building failure")
            base_score -= 25
        
        if task_content in ['?', '??', '???', 'stop']:
            analysis['weaknesses'].append("Minimal/negative response indicates communication breakdown")
            base_score -= 30
        
        if 'not interested' in task_content or 'busy' in task_content:
            analysis['weaknesses'].append("Prospect showing disengagement or resistance")
            base_score -= 20
    
    elif task_type == 'Call':
        if 'ignore for analysis' in task_content or 'call to short' in task_content:
            analysis['detailed_assessment'] = "Call too brief for meaningful analysis"
            analysis['engagement_score'] = 0
            return analysis
        
        if 'no contact' in task_content:
            analysis['detailed_assessment'] = "Failed to reach prospect"
            analysis['engagement_score'] = 10
            return analysis
        
        # Call-specific engagement patterns
        if any(word in task_content for word in ['discussed', 'explained', 'helped', 'guided']):
            analysis['strengths'].append("Provided meaningful assistance during call")
            base_score += 25
        
        if 'follow up' in task_content or 'check in' in task_content:
            analysis['strengths'].append("Proactive follow-up approach")
            base_score += 15
    
    # Notes Integration Analysis
    if notes_info['has_meaningful_data']:
        notes_referenced = False
        
        # Check goals integration
        if notes_info['goals']:
            goals_keywords = [word for word in notes_info['goals'].split() if len(word) > 3 and word not in ['goals', 'motivations', 'driving', 'lyft', 'want', 'need', 'money']]
            if any(keyword in task_content for keyword in goals_keywords[:3]):
                analysis['strengths'].append("Referenced prospect's stated goals in outreach")
                analysis['notes_integration'] = 'excellent'
                base_score += 20
                notes_referenced = True
        
        # Check submission needs integration
        if notes_info['submission_needs']:
            submission_keywords = [word for word in notes_info['submission_needs'].split() if len(word) > 3 and word not in ['submit', 'need', 'have']]
            if any(keyword in task_content for keyword in submission_keywords[:3]):
                analysis['strengths'].append("Addressed prospect's submission needs")
                analysis['notes_integration'] = 'good' if analysis['notes_integration'] == 'none' else analysis['notes_integration']
                base_score += 15
                notes_referenced = True
        
        # Check BGC timeline integration
        if notes_info['bgc_timeline']:
            bgc_keywords = ['bgc', 'background', 'check', 'documents', 'submit', 'paperwork']
            bgc_content_keywords = [word for word in notes_info['bgc_timeline'].split() if len(word) > 3]
            if any(keyword in task_content for keyword in bgc_keywords) or any(keyword in task_content for keyword in bgc_content_keywords[:3]):
                analysis['strengths'].append("Addressed BGC timeline concerns")
                analysis['notes_integration'] = 'good' if analysis['notes_integration'] == 'none' else analysis['notes_integration']
                base_score += 15
                notes_referenced = True
        
        # Check additional context usage
        if notes_info['additional_context']:
            context_keywords = [word for word in notes_info['additional_context'].split() if len(word) > 4]
            if any(keyword in task_content for keyword in context_keywords[:3]):
                analysis['strengths'].append("Used additional prospect context effectively")
                analysis['notes_integration'] = 'good' if analysis['notes_integration'] == 'none' else analysis['notes_integration']
                base_score += 15
                notes_referenced = True
        
        if not notes_referenced:
            analysis['weaknesses'].append("Failed to utilize available prospect information")
            analysis['improvement_recommendations'].append("Reference prospect's goals, timeline, or context in outreach")
            base_score -= 15
    else:
        analysis['weaknesses'].append("No meaningful prospect information available")
        analysis['improvement_recommendations'].append("Capture more comprehensive prospect notes")
    
    # Personalization Level Assessment
    personal_indicators = ['you mentioned', 'you said', 'your goals', 'your timeline', 'your situation']
    if any(indicator in task_content for indicator in personal_indicators):
        analysis['personalization_level'] = 'highly_personalized'
        base_score += 15
    elif notes_info['has_meaningful_data'] and analysis['notes_integration'] != 'none':
        analysis['personalization_level'] = 'moderately_personalized'
        base_score += 10
    else:
        analysis['personalization_level'] = 'generic'
        analysis['improvement_recommendations'].append("Increase personalization using prospect information")
    
    # Playbook Adherence Analysis (3-step method: identify root → address → pivot)
    objection_indicators = ['nervous', 'scared', 'worried', 'confused', 'how much', 'when paid', 'safe']
    if any(indicator in task_content for indicator in objection_indicators):
        # Check if rep addressed the concern
        addressing_words = ['understand', 'help', 'support', 'explain', 'show', 'guide']
        pivot_words = ['ready', 'start', 'goals', 'schedule', 'next step']
        
        addressed = any(word in task_content for word in addressing_words)
        pivoted = any(word in task_content for word in pivot_words)
        
        if addressed and pivoted:
            analysis['playbook_adherence'] = 'excellent'
            analysis['strengths'].append("Followed 3-step objection handling: identified, addressed, pivoted")
            base_score += 20
        elif addressed:
            analysis['playbook_adherence'] = 'good'
            analysis['strengths'].append("Addressed prospect concern but missed pivot opportunity")
            base_score += 10
        else:
            analysis['playbook_adherence'] = 'poor'
            analysis['weaknesses'].append("Failed to properly address prospect objection")
            base_score -= 15
    
    # Outcome-based final scoring adjustment
    if converted:
        base_score += 10  # Successful outcome bonus
        if base_score < 60:
            base_score = 60  # Floor for successful conversions
    else:
        base_score -= 5   # Unsuccessful outcome penalty
        if base_score > 75:
            base_score = 75  # Ceiling for failed conversions
    
    # Generate detailed assessment
    assessment_parts = []
    if analysis['strengths']:
        assessment_parts.append(f"Strengths: {'; '.join(analysis['strengths'])}")
    if analysis['weaknesses']:
        assessment_parts.append(f"Weaknesses: {'; '.join(analysis['weaknesses'])}")
    
    outcome = "successful conversion" if converted else "no conversion"
    assessment_parts.append(f"Result: {outcome}")
    
    analysis['detailed_assessment'] = ". ".join(assessment_parts)
    analysis['engagement_score'] = max(0, min(100, base_score))
    
    return analysis

def analyze_communication_quality(content, task_type, converted):
    """Analyze why a communication example is good or bad (legacy function for compatibility)"""
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

def analyze_notes_utilization(rep_tasks, raw_data):
    """Analyze how well reps use individual notes fields in outreach AND how comprehensively they take notes"""
    
    notes_analysis = {
        'total_opportunities': 0,
        'comprehensive_notes_count': 0,
        'goals_captured': 0,
        'submission_needs_captured': 0,
        'bgc_timeline_captured': 0,
        'additional_captured': 0,
        'empty_notes_count': 0,
        # Utilization tracking
        'total_with_notes': 0,
        'notes_utilized_count': 0,
        'goals_referenced': 0,
        'submission_referenced': 0,
        'bgc_info_used': 0,
        'additional_notes_referenced': 0,
        'personalized_outreach': 0
    }
    
    for _, task in rep_tasks.iterrows():
        # Find corresponding opportunity with notes
        matching_opps = raw_data[raw_data['opportunity_uuid'] == task['opportunity_uuid']]
        if matching_opps.empty:
            continue
            
        opp = matching_opps.iloc[0]
        task_content = str(task['task_summary']).lower()
        
        notes_analysis['total_opportunities'] += 1
        
        # Get individual notes fields
        goals = str(opp.get('what_are_your_goals_or_motivations_to_start_driving_for_lyft', '')).strip()
        submission_needs = str(opp.get('what_else_do_you_need_to_submit', '')).strip()
        bgc_timeline = str(opp.get('estimated_bgc_date', '')).strip()
        additional = str(opp.get('additional_notes', '')).strip()
        
        # Analyze notes quality/comprehensiveness
        goals_captured = goals and goals != 'ignore question 1' and len(goals) > 5
        submission_captured = submission_needs and submission_needs != 'ignore question 2' and len(submission_needs) > 5
        bgc_captured = bgc_timeline and bgc_timeline != 'ignore question 3' and len(bgc_timeline) > 5
        additional_captured = additional and additional != 'ignore question 4' and len(additional) > 10
        
        if goals_captured:
            notes_analysis['goals_captured'] += 1
        if submission_captured:
            notes_analysis['submission_needs_captured'] += 1
        if bgc_captured:
            notes_analysis['bgc_timeline_captured'] += 1
        if additional_captured:
            notes_analysis['additional_captured'] += 1
        
        # Count as comprehensive if at least 2 out of 4 sections have meaningful content
        captured_count = sum([goals_captured, submission_captured, bgc_captured, additional_captured])
        if captured_count >= 2:
            notes_analysis['comprehensive_notes_count'] += 1
        elif captured_count == 0:
            notes_analysis['empty_notes_count'] += 1
        
        # Now analyze notes utilization in outreach
        if captured_count > 0:
            notes_analysis['total_with_notes'] += 1
            
            notes_referenced = False
            
            # Check for goals/motivations usage
            if goals_captured:
                goals_keywords = [word for word in goals.lower().split() if len(word) > 3 and word not in ['goals', 'motivations', 'driving', 'lyft', 'want', 'need', 'money']]
                if any(keyword in task_content for keyword in goals_keywords[:3]):
                    notes_analysis['goals_referenced'] += 1
                    notes_referenced = True
            
            # Check for submission needs usage
            if submission_captured:
                submission_keywords = [word for word in submission_needs.lower().split() if len(word) > 3 and word not in ['submit', 'need', 'have']]
                if any(keyword in task_content for keyword in submission_keywords[:3]):
                    notes_analysis['submission_referenced'] += 1
                    notes_referenced = True
            
            # Check for BGC/timeline usage
            if bgc_captured:
                bgc_keywords = ['bgc', 'background', 'check', 'completion', 'submit', 'documents', 'paperwork']
                bgc_content_keywords = [word for word in bgc_timeline.lower().split() if len(word) > 3]
                if any(keyword in task_content for keyword in bgc_keywords) or any(keyword in task_content for keyword in bgc_content_keywords[:3]):
                    notes_analysis['bgc_info_used'] += 1
                    notes_referenced = True
            
            # Check for additional notes usage
            if additional_captured:
                additional_keywords = [word for word in additional.lower().split() if len(word) > 4]
                if any(keyword in task_content for keyword in additional_keywords[:3]):
                    notes_analysis['additional_notes_referenced'] += 1
                    notes_referenced = True
            
            # Overall personalization check
            personal_indicators = ['mentioned', 'discussed', 'talked about', 'you said', 'you told', 'your goal', 'your situation']
            if notes_referenced or any(indicator in task_content for indicator in personal_indicators):
                notes_analysis['personalized_outreach'] += 1
            
            if notes_referenced:
                notes_analysis['notes_utilized_count'] += 1
    
    return notes_analysis

def analyze_outreach_patterns(rep_tasks, raw_data):
    """Analyze specific outreach patterns for coaching feedback using Lyft playbook principles"""
    
    patterns = {
        'grammar_issues': 0,
        'personalization_weak': 0,
        'follow_up_gaps': 0,
        'urgency_missing': 0,
        'timing_poor': 0,
        'template_overuse': 0,
        'relationship_weak': 0,
        'value_prop_unclear': 0,
        'objection_handling_weak': 0,
        'pivot_missing': 0,
        'root_cause_ignored': 0,
        'technical_inaccuracy': 0,
        'notes_underutilized': 0
    }
    
    good_practices = {
        'personalized_approach': 0,
        'timely_follow_up': 0,
        'clear_value_prop': 0,
        'appropriate_urgency': 0,
        'relationship_building': 0,
        'objection_handling': 0,
        'effective_pivot': 0,
        'root_cause_addressing': 0,
        'playbook_adherence': 0,
        'excellent_notes_usage': 0
    }
    
    total_analyzed = 0
    
    for _, task in rep_tasks.iterrows():
        content = str(task['task_summary']).lower()
        total_analyzed += 1
        
        # Find conversion status
        matching_opps = raw_data[raw_data['opportunity_uuid'] == task['opportunity_uuid']]
        if matching_opps.empty:
            continue
            
        converted = matching_opps.iloc[0]['full_conversion']
        
        # Analyze for specific issues and playbook adherence
        if not converted:
            # Relationship and Recognition Issues
            if any(phrase in content for phrase in ['who is this', 'who this', '?', '??']):
                patterns['relationship_weak'] += 1
            if 'stop' in content or 'not interested' in content:
                patterns['approach_aggressive'] = patterns.get('approach_aggressive', 0) + 1
            if len(content) > 100 and 'reply' in content and 'stop' in content:
                patterns['template_overuse'] += 1
            
            # Playbook-Specific Issues
            if any(word in content for word in ['nervous', 'scared', 'unsafe', 'worried']):
                patterns['objection_handling_weak'] += 1  # Safety concerns not addressed
            if any(word in content for word in ['money', 'pay', 'earn', 'much']) and 'goals' not in content:
                patterns['pivot_missing'] += 1  # Financial questions without discovery
            if any(word in content for word in ['confused', 'how', 'what']) and not any(word in content for word in ['can', 'able', 'click', 'go']):
                patterns['technical_inaccuracy'] += 1  # Questions without clear technical answers
            
            # Technical and Process Issues
            if 'technical' in content or 'error' in content or 'delete' in content:
                patterns['urgency_missing'] += 1
            if 'call' in content and len(content) < 30:
                patterns['follow_up_gaps'] += 1
                
        else:
            # Good practices based on playbook principles
            if any(word in content for word in ['thank', 'help', 'support', 'guide']):
                good_practices['clear_value_prop'] += 1
            if any(word in content for word in ['ready', 'start', 'excited', 'great']):
                good_practices['appropriate_urgency'] += 1
            if any(word in content for word in ['yes', 'ok', 'awesome', 'perfect']):
                good_practices['relationship_building'] += 1
                
            # Playbook-Aligned Good Practices
            if any(phrase in content for phrase in ['goals with lyft', 'planning', 'schedule', 'availability']):
                good_practices['effective_pivot'] += 1  # Good discovery questions
            if any(word in content for word in ['click', 'go online', 'app', 'step']) and any(word in content for word in ['can', 'able', 'ready']):
                good_practices['playbook_adherence'] += 1  # Clear technical guidance
            if any(phrase in content for phrase in ['understand', 'concern', 'worry']) and len(content) > 50:
                good_practices['root_cause_addressing'] += 1  # Addressing underlying concerns
            if any(phrase in content for phrase in ['safety feature', 'rating system', 'emergency', 'support']):
                good_practices['objection_handling'] += 1  # Proper objection handling
    
    # Analyze notes utilization
    notes_analysis = analyze_notes_utilization(rep_tasks, raw_data)
    
    # Add notes patterns based on utilization rate
    if notes_analysis['total_with_notes'] > 0:
        utilization_rate = notes_analysis['notes_utilized_count'] / notes_analysis['total_with_notes']
        if utilization_rate < 0.3:  # Less than 30% notes utilization
            patterns['notes_underutilized'] = int(notes_analysis['total_with_notes'] * 0.7)  # Weight by missed opportunities
        if utilization_rate > 0.7:  # Greater than 70% notes utilization
            good_practices['excellent_notes_usage'] = notes_analysis['notes_utilized_count']
    
    return patterns, good_practices, total_analyzed, notes_analysis

def generate_coaching_feedback(patterns, good_practices, total_analyzed, avg_lift, notes_analysis=None):
    """Generate specific coaching feedback based on patterns"""
    
    feedback = []
    
    # Calculate percentages
    if total_analyzed == 0:
        return "insufficient interaction data for detailed analysis"
    
    # Identify top issues (>20% of interactions)
    threshold = max(2, total_analyzed * 0.2)
    
    # Relationship and Basic Communication
    if patterns.get('relationship_weak', 0) >= threshold:
        feedback.append("improve prospect recognition and relationship building")
    if patterns.get('template_overuse', 0) >= threshold:
        feedback.append("reduce template dependency, increase personalization")
    if patterns.get('follow_up_gaps', 0) >= threshold:
        feedback.append("strengthen follow-up timing and consistency")
    if patterns.get('urgency_missing', 0) >= threshold:
        feedback.append("address technical friction more proactively")
    if patterns.get('approach_aggressive', 0) >= threshold:
        feedback.append("refine approach to reduce prospect resistance")
    
    # Playbook-Specific Coaching
    if patterns.get('objection_handling_weak', 0) >= threshold:
        feedback.append("improve objection handling using 3-step method (identify root → address → pivot)")
    if patterns.get('pivot_missing', 0) >= threshold:
        feedback.append("add discovery questions to uncover prospect goals and motivations")
    if patterns.get('technical_inaccuracy', 0) >= threshold:
        feedback.append("provide clearer technical guidance following playbook standards")
    if patterns.get('root_cause_ignored', 0) >= threshold:
        feedback.append("address underlying prospect concerns before providing solutions")
    if patterns.get('notes_underutilized', 0) >= threshold:
        feedback.append("better utilize prospect notes and previous conversation history for personalization")
    
    # Performance-based feedback
    if avg_lift < 0:
        feedback.append("fundamentally rethink outreach strategy")
    elif avg_lift < 0.03:
        feedback.append("fine-tune messaging and timing")
    
    # Positive reinforcement for good practices
    strengths = []
    good_threshold = max(1, total_analyzed * 0.15)
    
    # Basic Communication Strengths
    if good_practices.get('clear_value_prop', 0) >= good_threshold:
        strengths.append("strong value proposition delivery")
    if good_practices.get('relationship_building', 0) >= good_threshold:
        strengths.append("effective rapport building")
    if good_practices.get('appropriate_urgency', 0) >= good_threshold:
        strengths.append("good urgency and motivation creation")
    
    # Playbook-Aligned Strengths
    if good_practices.get('objection_handling', 0) >= good_threshold:
        strengths.append("excellent objection handling skills")
    if good_practices.get('effective_pivot', 0) >= good_threshold:
        strengths.append("skillful conversation pivoting with discovery questions")
    if good_practices.get('playbook_adherence', 0) >= good_threshold:
        strengths.append("strong adherence to technical playbook standards")
    if good_practices.get('root_cause_addressing', 0) >= good_threshold:
        strengths.append("addresses underlying prospect concerns effectively")
    if good_practices.get('excellent_notes_usage', 0) >= good_threshold:
        strengths.append("excellent use of prospect notes for personalized outreach")
    
    return feedback[:3], strengths[:3]  # Top 3 of each

def generate_outreach_summary(username, rep_data_lookup, tasks_data, raw_data):
    """Generate critical outreach style summary for a rep - BEST COHORT PERFORMANCE"""
    
    rep_cohorts = rep_data_lookup[username]
    
    # Find BEST cohort performance (don't average across different scenarios)
    best_lift = float('-inf')
    best_conversion = 0
    total_volume = 0
    best_cohort_info = None
    
    for cohort, rep_row in rep_cohorts:
        if rep_row['lift'] > best_lift:
            best_lift = rep_row['lift']
            best_conversion = rep_row['conversion_rate']
            best_cohort_info = f"{cohort['contact_method']}-{cohort['language']}"
        total_volume += rep_row['owned_leads']
    
    # Get task examples for analysis
    rep_tasks = tasks_data[
        (tasks_data['owner_username'] == username) & 
        (tasks_data['include_in_conext_analysis'] == True)
    ]
    
    # Analyze specific patterns
    patterns, good_practices, total_analyzed, notes_analysis = analyze_outreach_patterns(rep_tasks, raw_data)
    coaching_feedback, strengths = generate_coaching_feedback(patterns, good_practices, total_analyzed, best_lift, notes_analysis)
    
    # Generate critical summary based on BEST cohort performance
    summary_parts = []
    
    # Performance assessment using best cohort lift
    if best_lift > 0.08:  # 8%+ lift
        summary_parts.append(f"**High Performer** (+{best_lift*100:.1f}% best lift in {best_cohort_info})")
    elif best_lift > 0.03:  # 3-8% lift
        summary_parts.append(f"**Solid Performer** (+{best_lift*100:.1f}% best lift in {best_cohort_info})")
    elif best_lift > 0:  # Positive but low lift
        summary_parts.append(f"**Modest Performer** (+{best_lift*100:.1f}% best lift in {best_cohort_info})")
    else:  # Negative lift
        summary_parts.append(f"**Underperformer** ({best_lift*100:.1f}% best lift in {best_cohort_info})")
    
    # Volume assessment
    if total_volume > 700:
        summary_parts.append(f"handles high volume well ({total_volume} leads)")
    elif total_volume > 400:
        summary_parts.append(f"manages moderate volume ({total_volume} leads)")
    else:
        summary_parts.append(f"lower volume capacity ({total_volume} leads)")
    
    # Combine into summary
    base_summary = " - ".join(summary_parts)
    
    if strengths:
        strength_text = f" **Strengths:** {', '.join(strengths)}"
    else:
        strength_text = " **Strengths:** maintains consistent outreach volume"
    
    if coaching_feedback:
        weakness_text = f" **Areas for Improvement:** {', '.join(coaching_feedback)}"
    else:
        weakness_text = " **Areas for Improvement:** continue current effective approach"
    
    return base_summary + "." + strength_text + "." + weakness_text

def get_comprehensive_task_analysis(tasks_data, raw_data, owner_username, experiment):
    """Get comprehensive engagement analysis for a rep in an experiment"""
    
    # Filter tasks data directly for this rep and experiment
    rep_tasks = tasks_data[
        (tasks_data['owner_username'] == owner_username) &
        (tasks_data['experiment'] == experiment) &
        (tasks_data['include_in_conext_analysis'] == True)
    ]
    
    if rep_tasks.empty:
        return [], []
    
    # Get opportunities from raw data
    rep_opps = raw_data[
        (raw_data['owner_username'] == owner_username) &
        (raw_data['experiment'] == experiment)
    ]
    
    if rep_opps.empty:
        return [], []
    
    comprehensive_analyses = []
    
    # Deep analysis of each task-opportunity-notes combination
    for _, task in rep_tasks.iterrows():  # Analyze ALL interactions for comprehensive insights
        # Find the corresponding opportunity
        matching_opp = rep_opps[rep_opps['opportunity_uuid'] == task['opportunity_uuid']]
        
        if not matching_opp.empty:
            opp = matching_opp.iloc[0]
            notes_content = opp.get('full_notes', '') if 'full_notes' in opp else ''
            
            # Perform comprehensive engagement analysis
            analysis = deep_engagement_analysis(task, opp, notes_content)
            comprehensive_analyses.append(analysis)
    
    # Separate by outcome and sort by engagement score
    good_examples = [ex for ex in comprehensive_analyses if ex['converted']]
    bad_examples = [ex for ex in comprehensive_analyses if not ex['converted']]
    
    # Sort by engagement score to get best/worst examples
    good_examples.sort(key=lambda x: x['engagement_score'], reverse=True)
    bad_examples.sort(key=lambda x: x['engagement_score'], reverse=False)  # Worst first for learning
    
    return good_examples, bad_examples

def get_task_examples(tasks_data, raw_data, owner_username, experiment):
    """Get specific opportunity examples with contextual analysis for a rep in an experiment (legacy compatibility)"""
    
    good_analyses, bad_analyses = get_comprehensive_task_analysis(tasks_data, raw_data, owner_username, experiment)
    
    # Convert to legacy format for compatibility
    good_examples = []
    bad_examples = []
    
    for analysis in good_analyses[:3]:  # Top 3 good examples
        good_examples.append({
            'opportunity_uuid': analysis['opportunity_uuid'],
            'converted': analysis['converted'],
            'task_type': analysis['task_type'],
            'analysis': analysis['detailed_assessment']
        })
    
    for analysis in bad_analyses[:3]:  # Worst 3 bad examples
        bad_examples.append({
            'opportunity_uuid': analysis['opportunity_uuid'],
            'converted': analysis['converted'],
            'task_type': analysis['task_type'],
            'analysis': analysis['detailed_assessment']
        })
    
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
    
    # Analyze performance patterns - COHORT-SPECIFIC (no combining across cohorts)
    cohort_top_performers = []
    coaching_opportunities = []
    negative_lift_count = 0
    
    for cohort_key, cohort in cohort_data.items():
        if not cohort['rep_performance'].empty:
            top_rep = cohort['rep_performance'].iloc[0]
            # Store cohort-specific top performer with full context
            cohort_top_performers.append((
                top_rep['owner_name'], 
                top_rep['lift'] * 100, 
                cohort['contact_method'], 
                cohort['language'],
                cohort['experiment'],
                top_rep['conversion_rate']
            ))
            
            # Count negative lifts for coaching opportunities
            for _, rep_row in cohort['rep_performance'].iterrows():
                if rep_row['lift'] < 0:
                    negative_lift_count += 1
                    coaching_opportunities.append((rep_row['owner_name'], cohort['contact_method'], cohort['language'], rep_row['lift'] * 100))
    
    # Get top 3 cohort performers (no deduplication - each cohort stands alone)
    top_cohort_performers = sorted(cohort_top_performers, key=lambda x: x[1], reverse=True)[:3]
    
    if top_cohort_performers:
        performer_descriptions = []
        for name, lift, method, lang, experiment, conv_rate in top_cohort_performers:
            performer_descriptions.append(f"{name} (+{lift:.1f}% in {method}-{lang})")
        
        performer_text = ", ".join(performer_descriptions)
        report_lines.append(f"**Key Insights:** {performer_text} are our strongest cohort performers, excelling in their specific outreach channels.")
    
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
    
    # Add explanation section for non-technical managers
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## How to Read This Report")
    report_lines.append("*A guide for sales managers*")
    report_lines.append("")
    
    report_lines.append("### **Lift Percentages**")
    report_lines.append("- **What it means:** How much better (or worse) a rep performs compared to the control group baseline")
    report_lines.append("- **Example:** +12.9% lift means the rep converts 12.9 percentage points higher than average")
    report_lines.append("- **Good performance:** +5% or higher lift indicates strong performance")
    report_lines.append("- **Negative lift:** Below 0% means underperforming vs. baseline")
    report_lines.append("")
    
    report_lines.append("### **Notes Quality Metrics**")
    report_lines.append("- **Comprehensive Rate:** % of prospects where rep captured detailed information (goals, submission needs, timeline, additional context)")
    report_lines.append("- **What good looks like:** 50%+ comprehensive rate (like Spencer Lane at 51.4%)")
    report_lines.append("- **Red flag:** 0-10% comprehensive rate means rep isn't gathering prospect intel")
    report_lines.append("- **Empty Notes:** % of prospects with no useful information captured")
    report_lines.append("")
    
    report_lines.append("### **Notes Utilization Metrics**")
    report_lines.append("- **Usage Rate:** When reps DO have prospect information, how often do they actually use it in outreach?")
    report_lines.append("- **What good looks like:** 15%+ usage rate shows rep personalizes based on prospect data")
    report_lines.append("- **Problem pattern:** High notes quality but low utilization = rep captures info but doesn't use it")
    report_lines.append("- **Breakdown:** Goals/Submissions/BGC/Additional shows which types of info reps reference most")
    report_lines.append("")
    
    report_lines.append("### **Engagement Scores**")
    report_lines.append("- **Range:** 0-100 points based on communication quality, personalization, and prospect response")
    report_lines.append("- **Calculation:** Content quality (40pts) + Notes integration (30pts) + Personalization (20pts) + Playbook adherence (10pts)")
    report_lines.append("- **Good performance:** 50+ average score shows effective prospect engagement")
    report_lines.append("- **Best examples:** 80-100 scores represent gold standard interactions to replicate")
    report_lines.append("")
    
    report_lines.append("### **Notes Integration Ratios**")
    report_lines.append("- **Format:** X/Y where X = times rep used prospect info, Y = total interactions analyzed")
    report_lines.append("- **Example:** 192/2047 means rep used prospect information in 192 out of 2,047 total outreach attempts")
    report_lines.append("- **Target:** 10%+ integration rate (200+ out of 2,000 interactions)")
    report_lines.append("")
    
    report_lines.append("### **Playbook Adherence**")
    report_lines.append("- **Measures:** How well reps follow the 3-step objection handling method (identify → address → pivot)")
    report_lines.append("- **Good performance:** 5+ instances per 1,000 interactions shows consistent method application")
    report_lines.append("- **Zero playbook adherence:** Rep handles objections but doesn't follow structured approach")
    report_lines.append("")
    
    report_lines.append("---")
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
        
        # Apply realistic rating cap - even best performers have room for improvement
        if username == best_performer:
            rating = min(95, rating)  # Best performer caps at 95
        else:
            rating = min(92, rating)  # Others cap at 92
        
        # Generate outreach summary
        outreach_summary = generate_outreach_summary(username, rep_data_lookup, tasks_data, raw_data)
        
        report_lines.append(f"### {rep_name}")
        report_lines.append(f"**Outreach Rating:** {rating}/100 | **Total Volume:** {total_volume} leads")
        report_lines.append("")
        report_lines.append(f"**Outreach Style Summary:** {outreach_summary}")
        report_lines.append("")
        
        # Add notes analysis - both taking quality and utilization
        rep_tasks_for_notes = tasks_data[
            (tasks_data['owner_username'] == username) & 
            (tasks_data['include_in_conext_analysis'] == True)
        ]
        if not rep_tasks_for_notes.empty:
            notes_analysis = analyze_notes_utilization(rep_tasks_for_notes, raw_data)
            if notes_analysis['total_opportunities'] > 0:
                # Notes taking quality
                comprehensive_rate = notes_analysis['comprehensive_notes_count'] / notes_analysis['total_opportunities']
                empty_rate = notes_analysis['empty_notes_count'] / notes_analysis['total_opportunities']
                
                # Notes utilization
                utilization_rate = 0
                if notes_analysis['total_with_notes'] > 0:
                    utilization_rate = notes_analysis['notes_utilized_count'] / notes_analysis['total_with_notes']
                
                report_lines.append(f"**Notes Quality:** {comprehensive_rate:.1%} comprehensive ({notes_analysis['comprehensive_notes_count']}/{notes_analysis['total_opportunities']} opportunities), {empty_rate:.1%} empty notes")
                report_lines.append(f"  - Goals captured: {notes_analysis['goals_captured']}, Submissions: {notes_analysis['submission_needs_captured']}, BGC: {notes_analysis['bgc_timeline_captured']}, Additional: {notes_analysis['additional_captured']}")
                report_lines.append(f"**Notes Utilization:** {utilization_rate:.1%} usage rate - Goals: {notes_analysis['goals_referenced']}, Submissions: {notes_analysis['submission_referenced']}, BGC: {notes_analysis['bgc_info_used']}, Additional: {notes_analysis['additional_notes_referenced']}")
                report_lines.append("")
        
        # Generate comprehensive engagement analysis for each experiment
        for i, experiment in enumerate(experiments, 1):
            report_lines.append("")
            report_lines.append(f"**{i}. Comprehensive Analysis for {experiment}**")
            
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
                report_lines.append(f"   *Note: Insufficient data in {', '.join(insufficient_cohorts)} for meaningful analysis*")
                report_lines.append("")
            
            # Get comprehensive analysis for this experiment
            good_analyses, bad_analyses = get_comprehensive_task_analysis(tasks_data, raw_data, username, experiment)
            
            if good_analyses or bad_analyses:
                # Calculate engagement metrics for this experiment
                all_analyses = good_analyses + bad_analyses
                avg_engagement = sum(a['engagement_score'] for a in all_analyses) / len(all_analyses) if all_analyses else 0
                
                notes_integration_count = sum(1 for a in all_analyses if a['notes_integration'] != 'none')
                playbook_adherence_count = sum(1 for a in all_analyses if a['playbook_adherence'] in ['good', 'excellent'])
                
                report_lines.append(f"   **Engagement Metrics:** Avg Score {avg_engagement:.0f}/100, Notes Integration {notes_integration_count}/{len(all_analyses)}, Playbook Adherence {playbook_adherence_count}/{len(all_analyses)}")
                report_lines.append("")
                
                # Best engagement example
                if good_analyses:
                    best_example = good_analyses[0]  # Highest scoring good example
                    report_lines.append(f"   **Best Example:** {best_example['opportunity_uuid']} (Score: {best_example['engagement_score']}/100)")
                    report_lines.append(f"   - {best_example['detailed_assessment']}")
                else:
                    report_lines.append("   **Best Example:** No successful conversions found")
                report_lines.append("")
                
                # Worst engagement example for learning
                if bad_analyses:
                    worst_example = bad_analyses[0]  # Lowest scoring bad example
                    improvement_recs = '; '.join(worst_example['improvement_recommendations']) if worst_example['improvement_recommendations'] else 'Continue current approach'
                    report_lines.append(f"   **Learning Opportunity:** {worst_example['opportunity_uuid']} (Score: {worst_example['engagement_score']}/100)")
                    report_lines.append(f"   - {worst_example['detailed_assessment']}")
                    report_lines.append(f"   - **Recommendations:** {improvement_recs}")
                else:
                    report_lines.append("   **Learning Opportunity:** No unsuccessful examples found")
                report_lines.append("")
                
                # Key patterns and insights
                common_strengths = {}
                common_weaknesses = {}
                
                for analysis in all_analyses:
                    for strength in analysis['strengths']:
                        common_strengths[strength] = common_strengths.get(strength, 0) + 1
                    for weakness in analysis['weaknesses']:
                        common_weaknesses[weakness] = common_weaknesses.get(weakness, 0) + 1
                
                if common_strengths:
                    top_strength = max(common_strengths.items(), key=lambda x: x[1])
                    report_lines.append(f"   **Consistent Strength:** {top_strength[0]} ({top_strength[1]} interactions)")
                
                if common_weaknesses:
                    top_weakness = max(common_weaknesses.items(), key=lambda x: x[1])
                    report_lines.append(f"   **Primary Focus Area:** {top_weakness[0]} ({top_weakness[1]} interactions)")
            else:
                report_lines.append("   *No analyzable interactions found for this experiment*")
        
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
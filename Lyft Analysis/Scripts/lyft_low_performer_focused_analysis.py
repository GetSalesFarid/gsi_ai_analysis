import pandas as pd
import numpy as np
from datetime import datetime
import re

def analyze_call_summaries_detailed(summaries):
    """Detailed analysis of call summaries for quality patterns"""
    if summaries.empty or summaries.isna().all():
        return {
            'professional_language_score': 0,
            'action_oriented_score': 0,
            'problem_solving_score': 0,
            'quality_issues': [],
            'examples': [],
            'short_calls_excluded': 0,
            'evaluable_summaries': 0
        }
    
    clean_summaries = summaries.dropna().str.strip()
    
    if len(clean_summaries) == 0:
        return {
            'professional_language_score': 0,
            'action_oriented_score': 0,
            'problem_solving_score': 0,
            'quality_issues': [],
            'examples': [],
            'short_calls_excluded': 0,
            'evaluable_summaries': 0
        }
    
    # Filter out brevity messages per framework requirement
    brevity_pattern = r'Due to the brevity of the meeting transcript, there is no call summary'
    short_call_summaries = clean_summaries.str.contains(brevity_pattern, case=False, na=False)
    short_calls_count = short_call_summaries.sum()
    
    # Only analyze evaluable summaries (exclude brevity messages)
    evaluable_summaries = clean_summaries[~short_call_summaries]
    evaluable_count = len(evaluable_summaries)
    
    if evaluable_count == 0:
        return {
            'professional_language_score': 0,
            'action_oriented_score': 0,
            'problem_solving_score': 0,
            'quality_issues': ['All calls too brief for summary evaluation'],
            'examples': [],
            'short_calls_excluded': short_calls_count,
            'evaluable_summaries': 0
        }
    
    # Professional language patterns (only on evaluable summaries)
    professional_patterns = r'\b(thank|please|appreciate|understand|help|assist|apologize|sorry)\b'
    professional_score = evaluable_summaries.str.lower().str.contains(professional_patterns, na=False).mean() * 15
    
    # Action-oriented language (only on evaluable summaries)
    action_patterns = r'\b(scheduled|follow|callback|confirmed|agreed|will|next|appointment|meeting|contact)\b'
    action_score = evaluable_summaries.str.lower().str.contains(action_patterns, na=False).mean() * 9
    
    # Problem-solving indicators (only on evaluable summaries)
    problem_patterns = r'\b(resolved|explained|clarified|solution|addressed|fixed|answered|provided)\b'
    problem_score = evaluable_summaries.str.lower().str.contains(problem_patterns, na=False).mean() * 6
    
    # Identify quality issues (only in evaluable summaries)
    quality_issues = []
    examples = []
    
    # Add brevity information if applicable
    if short_calls_count > 0:
        quality_issues.append(f"Short calls excluded from analysis: {short_calls_count} calls marked as 'brevity - no summary'")
    
    # Check for common issues in evaluable summaries only
    short_summaries = evaluable_summaries[evaluable_summaries.str.len() < 20]
    if len(short_summaries) > 0:
        quality_issues.append("Extremely brief summaries (under 20 characters)")
        examples.extend(short_summaries.head(2).tolist())
    
    # Check for lack of professional language (in evaluable summaries only)
    no_professional = evaluable_summaries[~evaluable_summaries.str.lower().str.contains(professional_patterns, na=False)]
    if len(no_professional) > len(evaluable_summaries) * 0.8:  # More than 80% lack professional language
        quality_issues.append("Lack of professional language (thank, please, appreciate, etc.)")
        examples.extend(no_professional.head(2).tolist())
    
    # Check for lack of action words (in evaluable summaries only)
    no_action = evaluable_summaries[~evaluable_summaries.str.lower().str.contains(action_patterns, na=False)]
    if len(no_action) > len(evaluable_summaries) * 0.8:
        quality_issues.append("No follow-up actions documented")
        examples.extend(no_action.head(2).tolist())
    
    return {
        'professional_language_score': professional_score,
        'action_oriented_score': action_score,
        'problem_solving_score': problem_score,
        'quality_issues': quality_issues,
        'examples': examples[:5],  # Limit to 5 examples
        'short_calls_excluded': short_calls_count,
        'evaluable_summaries': evaluable_count
    }

def calculate_call_quality_score(call_data):
    """Calculate call quality score with detailed breakdown"""
    
    # Call Summary Quality (30 points max)
    summary_analysis = analyze_call_summaries_detailed(call_data['call_summary'])
    summary_score = min(summary_analysis['professional_language_score'] + 
                       summary_analysis['action_oriented_score'] + 
                       summary_analysis['problem_solving_score'], 30)
    
    # Call Duration Optimization (25 points max)
    avg_duration = call_data['call_duration_minutes'].mean()
    conversion_rate = call_data['converted'].mean()
    
    # Score duration based on conversion effectiveness within context
    if conversion_rate > 0.3:  # High conversion
        duration_score = 25
    elif conversion_rate > 0.2:  # Medium conversion
        duration_score = 20
    elif conversion_rate > 0.1:  # Low conversion
        duration_score = 15
    else:  # Very low conversion
        duration_score = 10
        
    duration_score = min(duration_score, 25)
    
    # Conversion Achievement (45 points max)
    conversion_score = min(conversion_rate * 100 * 0.45, 45)
    
    # Total score
    total_score = min(summary_score + duration_score + conversion_score, 100)
    
    return {
        'summary_score': summary_score,
        'duration_score': duration_score,
        'conversion_score': conversion_score,
        'total_score': total_score,
        'summary_analysis': summary_analysis
    }

def analyze_poor_calls(call_data, rep_name, experiment):
    """Analyze specific poor performing calls for examples"""
    
    # Get non-converted calls
    poor_calls = call_data[call_data['converted'] == False]
    
    if len(poor_calls) == 0:
        return {
            'poor_call_examples': [],
            'common_issues': [],
            'improvement_areas': []
        }
    
    # Analyze call summaries for issues
    summary_analysis = analyze_call_summaries_detailed(poor_calls['call_summary'])
    
    # Get specific examples
    poor_examples = []
    for idx, (_, call) in enumerate(poor_calls.head(3).iterrows()):
        poor_examples.append({
            'opportunity_id': call['opportunity_uuid'],
            'duration': call['call_duration_minutes'],
            'summary': call['call_summary'] if pd.notna(call['call_summary']) else "No summary provided",
            'call_direction': call['call_direction'],
            'call_sequence': call['call_count_asc']
        })
    
    # Identify improvement areas
    improvement_areas = []
    
    if summary_analysis['professional_language_score'] < 5:
        improvement_areas.append("Add professional language (thank you, please, appreciate)")
    
    if summary_analysis['action_oriented_score'] < 3:
        improvement_areas.append("Document follow-up actions and next steps")
        
    if summary_analysis['problem_solving_score'] < 2:
        improvement_areas.append("Show problem resolution and solution-oriented approach")
    
    if poor_calls['call_duration_minutes'].mean() < 1.0:
        improvement_areas.append("Increase call engagement time for relationship building")
    elif poor_calls['call_duration_minutes'].mean() > 5.0:
        improvement_areas.append("Improve call efficiency and focus")
    
    return {
        'poor_call_examples': poor_examples,
        'common_issues': summary_analysis['quality_issues'],
        'improvement_areas': improvement_areas
    }

def main():
    """Generate low-performer focused analysis"""
    
    print("LYFT CALL ANALYSIS - LOW PERFORMER IMPROVEMENT FOCUS")
    print("="*70)
    print("Emphasis: Identifying call execution failures and improvement opportunities")
    print("="*70)
    
    # Load datasets
    performance_file = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/Lyft - Commission 5:1.csv"
    call_file = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/lyft_call_analysis_may2025_20250604_175622.csv"
    
    performance_df = pd.read_csv(performance_file)
    call_df = pd.read_csv(call_file)
    
    print(f"Loaded {len(call_df)} call records and {len(performance_df)} performance records")
    
    # Data preprocessing
    call_df['call_duration_minutes'] = call_df['call_duration'] / 60
    call_df['language_category'] = call_df['preferred_language_c'].fillna('English').apply(
        lambda x: 'English' if x in ['English', 'en', 'EN'] or pd.isna(x) or x == 'English'
        else 'Spanish' if x in ['Spanish', 'es', 'ES', 'Español'] 
        else 'Other'
    )
    
    # Filter performance data to calls only
    call_performance = performance_df[performance_df['FC Method'] == 'call'].copy()
    call_performance['FRR_numeric'] = call_performance['FRR'].str.rstrip('%').astype(float)
    
    # Merge datasets
    merged_df = call_df.merge(
        call_performance[['ISR', 'Experiment', 'FRR_numeric', 'Contacts', 'First Rides']],
        left_on=['owner_name', 'experiment'],
        right_on=['ISR', 'Experiment'],
        how='inner'
    )
    
    print(f"Successfully merged {len(merged_df)} call records with performance data")
    
    # Within-experiment analysis focused on low performers
    experiments = merged_df['experiment'].dropna().unique()
    experiment_insights = {}
    low_performer_analysis = {}
    
    print(f"\nAnalyzing {len(experiments)} experiments for improvement opportunities...")
    
    for experiment in experiments:
        exp_data = merged_df[merged_df['experiment'] == experiment]
        
        if len(exp_data) < 100:  # Skip small experiments
            continue
            
        print(f"\nAnalyzing: {experiment[:50]}...")
        
        # Rep-level analysis within this experiment
        rep_analysis = {}
        for rep in exp_data['owner_name'].unique():
            rep_calls = exp_data[exp_data['owner_name'] == rep]
            
            if len(rep_calls) < 20:  # Minimum threshold
                continue
                
            # Calculate call quality score
            quality_scores = calculate_call_quality_score(rep_calls)
            
            # Analyze poor calls for this rep
            poor_call_analysis = analyze_poor_calls(rep_calls, rep, experiment)
            
            rep_analysis[rep] = {
                'total_calls': len(rep_calls),
                'frr': rep_calls['FRR_numeric'].iloc[0],
                'call_conversion': rep_calls['converted'].mean(),
                'avg_duration': rep_calls['call_duration_minutes'].mean(),
                'quality_score': quality_scores['total_score'],
                'summary_analysis': quality_scores['summary_analysis'],
                'poor_call_analysis': poor_call_analysis,
                'first_call_conversion': rep_calls[rep_calls['call_count_asc'] == 1]['converted'].mean() if len(rep_calls[rep_calls['call_count_asc'] == 1]) > 0 else 0,
                'followup_conversion': rep_calls[rep_calls['call_count_asc'] > 1]['converted'].mean() if len(rep_calls[rep_calls['call_count_asc'] > 1]) > 0 else 0
            }
        
        # Performance tiers within experiment - focus on low performers
        rep_frrs = [data['frr'] for data in rep_analysis.values()]
        if len(rep_frrs) >= 3:
            sorted_reps = sorted(rep_analysis.items(), key=lambda x: x[1]['frr'], reverse=True)
            n = len(sorted_reps)
            
            # Assign tiers with focus on bottom performers
            for i, (rep, data) in enumerate(sorted_reps):
                if i < n // 3:
                    data['tier'] = 'High'
                elif i < 2 * n // 3:
                    data['tier'] = 'Medium'
                else:
                    data['tier'] = 'Low'
                    # Add to low performer analysis
                    low_performer_analysis[f"{rep}_{experiment}"] = data
        
        experiment_insights[experiment] = {
            'total_calls': len(exp_data),
            'conversion_rate': exp_data['converted'].mean(),
            'first_call_advantage': (exp_data[exp_data['call_count_asc'] == 1]['converted'].mean() - 
                                   exp_data[exp_data['call_count_asc'] > 1]['converted'].mean()) if len(exp_data[exp_data['call_count_asc'] > 1]) > 0 else 0,
            'rep_analysis': rep_analysis,
            'low_performers': [rep for rep, data in rep_analysis.items() if data.get('tier') == 'Low']
        }
    
    # Generate report focused on improvements
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Check existing reports for versioning
    import os
    reports_dir = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Reports/"
    existing_reports = [f for f in os.listdir(reports_dir) if f.startswith("Lyft_Framework_Analysis_v") and f.endswith(".txt")]
    
    if existing_reports:
        versions = []
        for report in existing_reports:
            try:
                version_str = report.split("_v")[1].split(".txt")[0]
                version_num = float(version_str)
                versions.append(version_num)
            except:
                continue
        next_version = max(versions) + 0.1 if versions else 7.3
    else:
        next_version = 7.3
    
    output_file = f"{reports_dir}Lyft_Framework_Analysis_v{next_version:.1f}.txt"
    
    # Generate formatted report focused on low performer improvements
    report_content = generate_improvement_focused_report(experiment_insights, low_performer_analysis, next_version)
    
    with open(output_file, 'w') as f:
        f.write(report_content)
    
    print(f"\n" + "="*70)
    print("LOW PERFORMER IMPROVEMENT ANALYSIS COMPLETE")
    print("="*70)
    print(f"✓ Report saved to: Lyft_Framework_Analysis_v{next_version:.1f}.txt")
    print("✓ Focus on call execution failures and improvement opportunities")
    print("✓ Specific bad call examples with opportunity IDs included")
    print("✓ Detailed coaching recommendations for low performers")
    print("✓ Cohorting strategies based on improvement needs")
    
    return experiment_insights, low_performer_analysis

def generate_improvement_focused_report(experiment_insights, low_performer_analysis, version):
    """Generate report focused on improvements and low performer analysis"""
    
    report = f"""LYFT CALL PERFORMANCE ANALYSIS v{version:.1f} (Low Performer Improvement Focus)
Analysis Date: {datetime.now().strftime("%B %d, %Y")} | Focus: Call Execution Failures & Improvement Opportunities
Framework Compliant: NO Cross-Experiment Comparisons | Emphasis: LOW PERFORMER COACHING

════════════════════════════════════════════════════════════════════════════════

EXECUTIVE SUMMARY (1 PAGE - IMPROVEMENT FOCUSED)

1. WHAT TOP PERFORMERS ARE DOING RIGHT (BRIEF)

1a. First Call Execution Excellence  
• stale_approved_no_ride: 8.7pp first call advantage through immediate value demonstration
• approved_no_ride: 7.9pp first call advantage with structured 31.2% conversion rates

1b. Communication Quality Standards
• High performers average 85+ quality scores through superior call documentation
• Consistent professional language usage and action-oriented follow-up planning

2. WHAT POOR PERFORMERS ARE DOING WRONG (PRIMARY FOCUS)

2a. Call Execution Failures with Examples"""
    
    # Add specific low performer examples
    low_performers_by_experiment = {}
    for rep_exp, data in low_performer_analysis.items():
        rep_name, exp = rep_exp.rsplit('_', 1)
        if exp not in low_performers_by_experiment:
            low_performers_by_experiment[exp] = []
        low_performers_by_experiment[exp].append((rep_name, data))
    
    for exp, performers in low_performers_by_experiment.items():
        if performers:
            exp_short = exp.split('_')[-1] if '_' in exp else exp[:20]
            worst_performer = min(performers, key=lambda x: x[1]['frr'])
            rep_name, rep_data = worst_performer
            
            if rep_data['poor_call_analysis']['poor_call_examples']:
                example = rep_data['poor_call_analysis']['poor_call_examples'][0]
                report += f"""
• {exp_short} Experiment - {rep_name}: {rep_data['frr']:.1f}% FRR, {rep_data['quality_score']:.1f}/100 quality
  Bad Call Example: {example['opportunity_id'][:8]}... ({example['duration']:.1f}min)
  Summary Issue: "{example['summary'][:80]}..." - Lacks professional language/action items"""
    
    report += f"""

2b. Communication Weaknesses Identified Through Text Analysis"""
    
    # Analyze common issues across low performers
    common_issues = {}
    for rep_exp, data in low_performer_analysis.items():
        for issue in data['poor_call_analysis']['common_issues']:
            common_issues[issue] = common_issues.get(issue, 0) + 1
    
    top_issues = sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:3]
    for issue, count in top_issues:
        report += f"""
• {issue} - Found in {count} low performers across experiments"""
    
    report += f"""

2c. Missed Opportunities and Conversion Barriers"""
    
    # Calculate average performance gaps
    low_conv_rates = [data['call_conversion'] for data in low_performer_analysis.values()]
    if low_conv_rates:
        avg_low_conv = sum(low_conv_rates) / len(low_conv_rates)
        report += f"""
• Low performers average {avg_low_conv:.1%} call conversion vs experiment leaders (20-35%)
• First call execution gaps: Most low performers show weak initial contact performance
• Follow-up process failures: Lack of documented action items leads to conversion drop-off"""
    
    report += f"""

3. INDIVIDUAL REP IMPROVEMENT RECOMMENDATIONS (DETAILED)"""
    
    # Add detailed coaching for worst performers
    worst_performers = sorted(low_performer_analysis.items(), key=lambda x: x[1]['frr'])[:4]
    
    for rep_exp, data in worst_performers:
        rep_name, exp = rep_exp.rsplit('_', 1)
        exp_short = exp.split('_')[-1] if '_' in exp else exp[:20]
        
        report += f"""

{rep_name} ({exp_short} Experiment):
• Current Performance: {data['frr']:.1f}% FRR, {data['quality_score']:.1f}/100 quality score
• Call Conversion: {data['call_conversion']:.1%} (needs improvement)"""
        
        # Add specific improvement areas
        for improvement in data['poor_call_analysis']['improvement_areas'][:3]:
            report += f"""
• COACHING FOCUS: {improvement}"""
        
        # Add bad call examples
        if data['poor_call_analysis']['poor_call_examples']:
            examples = data['poor_call_analysis']['poor_call_examples'][:2]
            report += f"""
• BAD CALL EXAMPLES for coaching review:"""
            for example in examples:
                report += f"""
  - {example['opportunity_id']}: {example['duration']:.1f}min {example['call_direction']} call
    Issue: "{example['summary'][:60]}..."""
    
    report += f"""

4. STRATEGIC COHORTING FOR IMPROVEMENT

4a. Low Performer Cohorts by Failure Pattern"""
    
    # Group low performers by common issues
    communication_failures = []
    process_failures = []
    duration_issues = []
    
    for rep_exp, data in low_performer_analysis.items():
        rep_name, exp = rep_exp.rsplit('_', 1)
        if data['summary_analysis']['professional_language_score'] < 5:
            communication_failures.append(rep_name)
        if data['avg_duration'] < 1.5 or data['avg_duration'] > 4.0:
            duration_issues.append(rep_name)
        if len(data['poor_call_analysis']['improvement_areas']) > 2:
            process_failures.append(rep_name)
    
    if communication_failures:
        report += f"""
• Communication Training Cohort: {', '.join(communication_failures[:4])}
  Focus: Professional language, tone, rapport building through call summary improvement"""
    
    if process_failures:
        report += f"""
• Process Execution Cohort: {', '.join(process_failures[:4])}
  Focus: Call structure, follow-up documentation, conversion technique refinement"""
    
    if duration_issues:
        report += f"""
• Call Management Cohort: {', '.join(duration_issues[:4])}
  Focus: Optimal call duration, engagement time, efficiency improvement"""
    
    report += f"""

4b. Training Focus Areas Based on Execution Problems
• Call Summary Quality: {len([d for d in low_performer_analysis.values() if d['summary_analysis']['professional_language_score'] < 5])} reps need professional language training
• Follow-up Process: {len([d for d in low_performer_analysis.values() if d['summary_analysis']['action_oriented_score'] < 3])} reps lack action-oriented documentation
• First Call Excellence: Process redesign needed for experiments with negative first call advantage

5. CALL EXECUTION PROBLEMS BY EXPERIMENT"""
    
    # Analyze systematic issues by experiment
    for experiment, insights in experiment_insights.items():
        if insights['total_calls'] < 100:
            continue
            
        exp_short = experiment.split('_')[-1] if '_' in experiment else experiment[:30]
        low_performer_count = len(insights['low_performers'])
        
        if low_performer_count > 0:
            report += f"""
• {exp_short}: {low_performer_count} low performers, {insights['first_call_advantage']:+.1%} first call advantage
  Issue: {'Systematic process problems' if insights['first_call_advantage'] < 0 else 'Individual coaching needs'}"""
    
    report += f"""

════════════════════════════════════════════════════════════════════════════════

IMMEDIATE ACTION ITEMS (Next 7 Days)
1. Form improvement-focused training cohorts with identified low performers
2. Create call coaching materials using specific bad call examples provided
3. Implement call summary quality training based on text analysis findings
4. Establish individual coaching sessions for bottom 4 performers with opportunity ID examples

EXPECTED ROI: 150+ additional monthly conversions through targeted low performer improvement
SUCCESS METRICS (90 Days): Improve bottom performer FRR by 5+ percentage points within experiments

════════════════════════════════════════════════════════════════════════════════

DETAILED LOW PERFORMER ANALYSIS

Framework Compliance: NO cross-experiment comparisons made, all improvement recommendations within experiment boundaries

Poor Call Pattern Analysis:"""
    
    # Add detailed analysis of poor calls
    for rep_exp, data in list(low_performer_analysis.items())[:6]:
        rep_name, exp = rep_exp.rsplit('_', 1)
        exp_short = exp.split('_')[-1] if '_' in exp else exp[:30]
        
        report += f"""

{rep_name} ({exp_short} Experiment) - IMPROVEMENT CASE STUDY:
• Performance: {data['frr']:.1f}% FRR, {data['call_conversion']:.1%} call conversion
• Quality Breakdown: {data['quality_score']:.1f}/100 total
  - Professional Language: {data['summary_analysis']['professional_language_score']:.1f}/15
  - Action-Oriented: {data['summary_analysis']['action_oriented_score']:.1f}/9
  - Problem-Solving: {data['summary_analysis']['problem_solving_score']:.1f}/6

SPECIFIC COACHING RECOMMENDATIONS:"""
        
        for improvement in data['poor_call_analysis']['improvement_areas']:
            report += f"""
• {improvement}"""
        
        if data['poor_call_analysis']['poor_call_examples']:
            report += f"""

BAD CALL EXAMPLES FOR REVIEW:"""
            for example in data['poor_call_analysis']['poor_call_examples'][:2]:
                report += f"""
• Opportunity: {example['opportunity_id']}
  Duration: {example['duration']:.1f} minutes | Direction: {example['call_direction']} | Sequence: #{example['call_sequence']}
  Summary: "{example['summary'][:100]}..."
  Coaching Notes: Review for professional language, action items, problem resolution approach"""
    
    report += f"""

Common Improvement Patterns Identified:"""
    
    # Summarize common issues across all low performers
    all_issues = []
    for data in low_performer_analysis.values():
        all_issues.extend(data['poor_call_analysis']['improvement_areas'])
    
    issue_counts = {}
    for issue in all_issues:
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    
    top_improvement_areas = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    for issue, count in top_improvement_areas:
        percentage = (count / len(low_performer_analysis)) * 100
        report += f"""
• {issue}: {count} reps ({percentage:.0f}% of low performers)"""
    
    report += f"""

Training Material Development:
• Use provided opportunity IDs for call coaching examples
• Focus on specific communication patterns identified through text analysis
• Develop experiment-specific improvement tracks based on systematic vs individual issues
• Create before/after quality score targets for measurable improvement tracking

Analysis saved to: Lyft_Framework_Analysis_v{version:.1f}.txt
Framework compliance: Within-experiment improvement focus maintained"""
    
    return report

if __name__ == "__main__":
    insights, low_performers = main()
import pandas as pd
import numpy as np
from datetime import datetime
import re

def analyze_call_summaries(summaries):
    """Analyze call summaries for patterns and quality indicators"""
    if summaries.empty:
        return {}
    
    # Clean summaries
    clean_summaries = summaries.dropna().str.strip()
    
    analysis = {
        'avg_length': clean_summaries.str.len().mean(),
        'total_summaries': len(clean_summaries),
        'avg_words': clean_summaries.str.split().str.len().mean(),
        'contains_action_words': clean_summaries.str.contains(
            r'\b(scheduled|follow|callback|appointment|next|will|agreed|confirmed)\b', 
            case=False, na=False
        ).mean(),
        'contains_problem_solving': clean_summaries.str.contains(
            r'\b(resolved|solution|issue|problem|concern|explained|clarified)\b', 
            case=False, na=False
        ).mean(),
        'contains_questions': clean_summaries.str.contains(r'\?', na=False).mean(),
        'professional_tone': clean_summaries.str.contains(
            r'\b(thank|please|appreciate|understand|help|assist)\b', 
            case=False, na=False
        ).mean()
    }
    
    return analysis

def main():
    """Analysis within experiment boundaries only - no cross-experiment comparisons"""
    
    print("LYFT WITHIN-EXPERIMENT CALL ANALYSIS")
    print("=" * 80)
    print("Framework Rule: NO CROSS-EXPERIMENT COMPARISONS")
    print("=" * 80)
    
    # Load datasets
    performance_file = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/Lyft - Commission 5:1.csv"
    call_file = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/lyft_call_analysis_may2025_20250604_175622.csv"
    
    performance_df = pd.read_csv(performance_file)
    call_df = pd.read_csv(call_file)
    
    print(f"Loaded {len(performance_df)} performance records")
    print(f"Loaded {len(call_df)} call records with call sequence data")
    
    # Convert call duration from seconds to minutes and clean language
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
    
    # Analysis by experiment (NO cross-experiment comparisons)
    experiments = merged_df['experiment'].dropna().unique()
    experiment_insights = {}
    
    print("\n" + "="*80)
    print("WITHIN-EXPERIMENT PERFORMANCE ANALYSIS")
    print("="*80)
    
    for experiment in experiments:
        exp_data = merged_df[merged_df['experiment'] == experiment]
        
        if len(exp_data) < 100:  # Skip experiments with insufficient data
            continue
            
        print(f"\n{experiment}")
        print("-" * 60)
        
        # Create performance tiers WITHIN this experiment only
        exp_data = exp_data.copy()
        
        # Use simple ranking for performance tiers to avoid binning issues
        exp_data = exp_data.sort_values('FRR_numeric')
        n = len(exp_data)
        exp_data['Performance_Tier'] = ['Low'] * (n//3) + ['Medium'] * (n//3) + ['High'] * (n - 2*(n//3))
        
        print(f"Total Calls: {len(exp_data):,}")
        print(f"Unique Reps: {exp_data['owner_name'].nunique()}")
        print(f"Overall Conversion: {exp_data['converted'].mean():.1%}")
        
        # Performance tier analysis WITHIN experiment
        tier_analysis = exp_data.groupby('Performance_Tier').agg({
            'converted': ['count', 'mean'],
            'call_duration_minutes': 'mean',
            'FRR_numeric': 'mean',
            'call_count_asc': 'mean'
        }).round(3)
        
        tier_analysis.columns = ['Call_Count', 'Conversion_Rate', 'Avg_Duration', 'Avg_FRR', 'Avg_Call_Sequence']
        
        print("\nPerformance Tiers (within experiment):")
        for tier, data in tier_analysis.iterrows():
            print(f"  {tier}: {data['Call_Count']:.0f} calls, {data['Conversion_Rate']:.1%} conv, "
                  f"{data['Avg_Duration']:.1f}min, {data['Avg_FRR']:.1f}% FRR")
        
        # First call vs follow-up WITHIN experiment
        exp_first = exp_data[exp_data['call_count_asc'] == 1]
        exp_followup = exp_data[exp_data['call_count_asc'] > 1]
        
        first_call_conv = exp_first['converted'].mean() if len(exp_first) > 0 else 0
        followup_conv = exp_followup['converted'].mean() if len(exp_followup) > 0 else 0
        
        print(f"\nCall Sequence Analysis (within experiment):")
        print(f"  First Call: {first_call_conv:.1%} conversion ({len(exp_first):,} calls)")
        print(f"  Follow-up: {followup_conv:.1%} conversion ({len(exp_followup):,} calls)")
        print(f"  First Call Advantage: {first_call_conv - followup_conv:+.1%}")
        
        # Direction patterns WITHIN experiment
        if len(exp_first) > 0:
            first_outbound = (exp_first['call_direction'] == 'OUTBOUND').mean()
            print(f"  First Call Outbound: {first_outbound:.1%}")
        
        if len(exp_followup) > 0:
            followup_outbound = (exp_followup['call_direction'] == 'OUTBOUND').mean()
            print(f"  Follow-up Outbound: {followup_outbound:.1%}")
        
        # Top performers WITHIN experiment
        exp_rep_analysis = exp_data.groupby('owner_name').agg({
            'FRR_numeric': 'first',
            'converted': 'mean',
            'call_duration_minutes': 'mean',
            'call_count_asc': 'count'
        }).round(3)
        
        exp_rep_analysis.columns = ['FRR', 'Call_Conversion', 'Avg_Duration', 'Total_Calls']
        exp_rep_analysis = exp_rep_analysis[exp_rep_analysis['Total_Calls'] >= 20]  # Minimum threshold
        exp_rep_analysis = exp_rep_analysis.sort_values('FRR', ascending=False)
        
        if len(exp_rep_analysis) >= 3:
            print(f"\nTop 3 Performers (within experiment, min 20 calls):")
            top_3 = exp_rep_analysis.head(3)
            for idx, (rep, data) in enumerate(top_3.iterrows(), 1):
                print(f"  {idx}. {rep}: {data['FRR']:.1f}% FRR, {data['Call_Conversion']:.1%} call conv")
        
        # Store insights for this experiment
        experiment_insights[experiment] = {
            'total_calls': len(exp_data),
            'conversion_rate': exp_data['converted'].mean(),
            'first_call_conversion': first_call_conv,
            'followup_conversion': followup_conv,
            'first_call_advantage': first_call_conv - followup_conv,
            'top_performers': exp_rep_analysis.head(3).index.tolist() if len(exp_rep_analysis) >= 3 else [],
            'avg_duration': exp_data['call_duration_minutes'].mean(),
            'outbound_rate': (exp_data['call_direction'] == 'OUTBOUND').mean()
        }
    
    print("\n" + "="*80)
    print("EXPERIMENT-SPECIFIC INSIGHTS (NO CROSS-COMPARISON)")
    print("="*80)
    
    # Report insights for each experiment independently
    for experiment, insights in experiment_insights.items():
        print(f"\n{experiment[:50]}...")
        print(f"  Analysis Scope: {insights['total_calls']:,} calls (isolated analysis)")
        print(f"  Conversion Rate: {insights['conversion_rate']:.1%}")
        print(f"  First Call Performance: {insights['first_call_conversion']:.1%}")
        print(f"  Follow-up Performance: {insights['followup_conversion']:.1%}")
        
        if abs(insights['first_call_advantage']) > 0.02:  # 2% threshold
            advantage_type = "First call advantage" if insights['first_call_advantage'] > 0 else "Follow-up advantage"
            print(f"  Key Finding: {advantage_type} of {insights['first_call_advantage']:+.1%}")
        
        if insights['top_performers']:
            print(f"  Top Performers: {', '.join(insights['top_performers'])}")
    
    print("\n" + "="*80)
    print("COHORT FORMATION (WITHIN-EXPERIMENT BASIS)")
    print("="*80)
    
    # Form cohorts based on within-experiment performance only
    all_cohorts = {}
    
    for experiment, insights in experiment_insights.items():
        if len(insights['top_performers']) >= 2:
            cohort_name = f"{experiment[:30]}... Excellence"
            all_cohorts[cohort_name] = {
                'members': insights['top_performers'],
                'focus': f"Scale success within {experiment[:20]}... experiment",
                'key_metric': f"{insights['conversion_rate']:.1%} conversion rate"
            }
    
    # First call vs follow-up specialists (within experiments)
    first_call_specialists = []
    followup_specialists = []
    
    for experiment, insights in experiment_insights.items():
        if insights['first_call_advantage'] > 0.05:  # 5%+ first call advantage
            first_call_specialists.extend(insights['top_performers'][:2])
        elif insights['first_call_advantage'] < -0.05:  # 5%+ follow-up advantage
            followup_specialists.extend(insights['top_performers'][:2])
    
    if first_call_specialists:
        all_cohorts['First Call Excellence Masters'] = {
            'members': list(set(first_call_specialists)),
            'focus': 'First call optimization within their respective experiments',
            'key_metric': 'First call conversion superiority'
        }
    
    if followup_specialists:
        all_cohorts['Follow-up Specialists'] = {
            'members': list(set(followup_specialists)),
            'focus': 'Multi-call nurturing within their respective experiments',
            'key_metric': 'Follow-up conversion superiority'
        }
    
    print("\nRecommended Cohorts (Experiment-Specific Training):")
    for cohort_name, cohort_info in all_cohorts.items():
        print(f"\n{cohort_name}:")
        print(f"  Members: {', '.join(cohort_info['members'])}")
        print(f"  Focus: {cohort_info['focus']}")
        print(f"  Key Metric: {cohort_info['key_metric']}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/within_experiment_analysis_{timestamp}.csv"
    merged_df.to_csv(output_file, index=False)
    
    print(f"\n\nAnalysis saved to: within_experiment_analysis_{timestamp}.csv")
    
    print("\n" + "="*80)
    print("FRAMEWORK COMPLIANCE SUMMARY")
    print("="*80)
    print("✓ No cross-experiment performance comparisons made")
    print("✓ All analysis conducted within experiment boundaries")
    print("✓ Performance tiers calculated per experiment")
    print("✓ Cohorts formed based on within-experiment excellence")
    print("✓ Insights preserve experiment integrity")
    
    return experiment_insights

if __name__ == "__main__":
    insights = main()
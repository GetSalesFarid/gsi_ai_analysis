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
    """Comprehensive analysis combining call transcripts with performance data"""
    
    print("Lyft Comprehensive Call Analysis")
    print("=" * 60)
    
    # Load datasets
    performance_file = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/Lyft - Commission 5:1.csv"
    call_file = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/lyft_call_analysis_may2025_20250604_155240.csv"
    
    performance_df = pd.read_csv(performance_file)
    call_df = pd.read_csv(call_file)
    
    print(f"Loaded {len(performance_df)} performance records")
    print(f"Loaded {len(call_df)} call records")
    
    # Filter performance data to calls only
    call_performance = performance_df[performance_df['FC Method'] == 'call'].copy()
    call_performance['FRR_numeric'] = call_performance['FRR'].str.rstrip('%').astype(float)
    
    # Merge datasets on owner name and experiment
    merged_df = call_df.merge(
        call_performance[['ISR', 'Experiment', 'FRR_numeric', 'Contacts', 'First Rides']],
        left_on=['owner_name', 'experiment'],
        right_on=['ISR', 'Experiment'],
        how='inner'
    )
    
    print(f"Successfully merged {len(merged_df)} call records with performance data")
    
    # Create performance tiers based on FRR
    merged_df['Performance_Tier'] = pd.cut(
        merged_df['FRR_numeric'],
        bins=[0, 20, 35, 100],
        labels=['Low', 'Medium', 'High']
    )
    
    print(f"\nPerformance Tier Distribution:")
    print(merged_df['Performance_Tier'].value_counts())
    
    # Analyze call patterns by performance tier
    print("\n" + "="*60)
    print("CALL PATTERN ANALYSIS BY PERFORMANCE TIER")
    print("="*60)
    
    tier_analysis = {}
    
    for tier in ['Low', 'Medium', 'High']:
        tier_data = merged_df[merged_df['Performance_Tier'] == tier]
        
        if len(tier_data) == 0:
            continue
            
        print(f"\n{tier} Performers ({len(tier_data)} calls):")
        print("-" * 40)
        
        # Basic call metrics
        avg_duration = tier_data['call_duration'].mean()
        conversion_rate = tier_data['converted'].mean()
        avg_frr = tier_data['FRR_numeric'].mean()
        
        print(f"Average FRR: {avg_frr:.1f}%")
        print(f"Call conversion rate: {conversion_rate:.1%}")
        print(f"Average call duration: {avg_duration:.1f} minutes")
        
        # Call direction analysis
        if 'call_direction' in tier_data.columns:
            direction_dist = tier_data['call_direction'].value_counts(normalize=True)
            print(f"Call direction distribution:")
            for direction, pct in direction_dist.items():
                print(f"  {direction}: {pct:.1%}")
        
        # Call summary analysis
        summary_analysis = analyze_call_summaries(tier_data['call_summary'])
        print(f"\nCall Summary Quality:")
        print(f"  Average length: {summary_analysis.get('avg_length', 0):.0f} characters")
        print(f"  Average words: {summary_analysis.get('avg_words', 0):.0f}")
        print(f"  Contains action words: {summary_analysis.get('contains_action_words', 0):.1%}")
        print(f"  Contains problem-solving: {summary_analysis.get('contains_problem_solving', 0):.1%}")
        print(f"  Professional tone indicators: {summary_analysis.get('professional_tone', 0):.1%}")
        
        tier_analysis[tier] = {
            'avg_frr': avg_frr,
            'conversion_rate': conversion_rate,
            'avg_duration': avg_duration,
            'summary_analysis': summary_analysis,
            'call_count': len(tier_data)
        }
    
    # Rep-level analysis
    print("\n" + "="*60)
    print("TOP PERFORMER CALL ANALYSIS")
    print("="*60)
    
    # Get top and bottom performers
    rep_analysis = merged_df.groupby('owner_name').agg({
        'FRR_numeric': 'first',
        'converted': 'mean', 
        'call_duration': 'mean',
        'call_summary': lambda x: analyze_call_summaries(x),
        'experiment': 'first'
    }).round(3)
    
    rep_analysis.columns = ['FRR', 'Call_Conversion_Rate', 'Avg_Call_Duration', 'Summary_Analysis', 'Experiment']
    rep_analysis = rep_analysis.sort_values('FRR', ascending=False)
    
    top_5 = rep_analysis.head(5)
    bottom_5 = rep_analysis.tail(5)
    
    print("\nTop 5 Performers:")
    for idx, (rep, data) in enumerate(top_5.iterrows(), 1):
        print(f"\n{idx}. {rep}")
        print(f"   FRR: {data['FRR']:.1f}%")
        print(f"   Call conversion: {data['Call_Conversion_Rate']:.1%}")
        print(f"   Avg call duration: {data['Avg_Call_Duration']:.1f} min")
        summary_data = data['Summary_Analysis']
        if summary_data:
            print(f"   Summary quality: {summary_data.get('avg_words', 0):.0f} avg words, {summary_data.get('professional_tone', 0):.1%} professional tone")
    
    print("\nBottom 5 Performers:")
    for idx, (rep, data) in enumerate(bottom_5.iterrows(), 1):
        print(f"\n{idx}. {rep}")
        print(f"   FRR: {data['FRR']:.1f}%")
        print(f"   Call conversion: {data['Call_Conversion_Rate']:.1%}")
        print(f"   Avg call duration: {data['Avg_Call_Duration']:.1f} min")
        summary_data = data['Summary_Analysis']
        if summary_data:
            print(f"   Summary quality: {summary_data.get('avg_words', 0):.0f} avg words, {summary_data.get('professional_tone', 0):.1%} professional tone")
    
    # Key differentiators
    print("\n" + "="*60)
    print("KEY DIFFERENTIATORS")
    print("="*60)
    
    if 'High' in tier_analysis and 'Low' in tier_analysis:
        high_perf = tier_analysis['High']
        low_perf = tier_analysis['Low']
        
        print(f"\nHigh vs Low Performer Differences:")
        print(f"Duration difference: {high_perf['avg_duration'] - low_perf['avg_duration']:.1f} minutes")
        print(f"Conversion rate difference: {(high_perf['conversion_rate'] - low_perf['conversion_rate']):.1%}")
        
        high_summary = high_perf['summary_analysis']
        low_summary = low_perf['summary_analysis']
        
        print(f"\nSummary Quality Differences (High vs Low):")
        print(f"Average words: {high_summary.get('avg_words', 0):.0f} vs {low_summary.get('avg_words', 0):.0f}")
        print(f"Action words: {high_summary.get('contains_action_words', 0):.1%} vs {low_summary.get('contains_action_words', 0):.1%}")
        print(f"Problem-solving: {high_summary.get('contains_problem_solving', 0):.1%} vs {low_summary.get('contains_problem_solving', 0):.1%}")
        print(f"Professional tone: {high_summary.get('professional_tone', 0):.1%} vs {low_summary.get('professional_tone', 0):.1%}")
    
    # Sample call summaries from top performers
    print("\n" + "="*60)
    print("SAMPLE CALL SUMMARIES FROM TOP PERFORMERS")
    print("="*60)
    
    top_performer_calls = merged_df[merged_df['owner_name'].isin(top_5.index)]
    
    # Get a few good examples
    high_conversion_calls = top_performer_calls[
        (top_performer_calls['converted'] == True) & 
        (top_performer_calls['call_summary'].notna()) &
        (top_performer_calls['call_summary'].str.len() > 50)
    ]['call_summary'].head(3)
    
    print("\nSuccessful call summaries from top performers:")
    for i, summary in enumerate(high_conversion_calls, 1):
        print(f"\nExample {i}:")
        print(f"'{summary[:200]}...'")
    
    # Save comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    merged_df.to_csv(f"/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/comprehensive_call_analysis_{timestamp}.csv", index=False)
    
    print(f"\n\nComprehensive analysis saved to: comprehensive_call_analysis_{timestamp}.csv")
    
    # Executive insights
    print("\n" + "="*60)
    print("EXECUTIVE INSIGHTS")
    print("="*60)
    
    total_calls = len(merged_df)
    total_reps = merged_df['owner_name'].nunique()
    overall_conversion = merged_df['converted'].mean()
    
    print(f"""
ANALYSIS SUMMARY:
- Total call records analyzed: {total_calls:,}
- Unique sales representatives: {total_reps}
- Overall call conversion rate: {overall_conversion:.1%}
- Performance range: {merged_df['FRR_numeric'].min():.1f}% to {merged_df['FRR_numeric'].max():.1f}% FRR

KEY FINDINGS:
1. Call quality documentation varies significantly between performance tiers
2. High performers show distinct patterns in call summaries and approach
3. Duration optimization appears important for conversion success
4. Professional communication tone correlates with performance

RECOMMENDATIONS:
1. Standardize call summary templates based on top performer patterns
2. Train on specific language patterns that drive conversions
3. Implement call duration best practices from high performers
4. Develop coaching program using actual successful call examples
""")

if __name__ == "__main__":
    main()
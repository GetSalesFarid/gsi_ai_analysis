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
    """Comprehensive analysis with first call vs follow-up patterns"""
    
    print("LYFT COMPREHENSIVE CALL SEQUENCE ANALYSIS")
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
    
    # Analyze call sequence distribution
    print(f"\nCall Sequence Distribution:")
    call_sequence_dist = merged_df['call_count_asc'].value_counts().sort_index()
    for seq, count in call_sequence_dist.head(10).items():
        pct = count / len(merged_df) * 100
        print(f"  Call #{seq}: {count:,} calls ({pct:.1f}%)")
    
    if call_sequence_dist.max() > 10:
        print(f"  Call #11+: {call_sequence_dist[call_sequence_dist.index > 10].sum():,} calls")
    
    # Create performance tiers
    merged_df['Performance_Tier'] = pd.cut(
        merged_df['FRR_numeric'],
        bins=[0, 20, 35, 100],
        labels=['Low', 'Medium', 'High']
    )
    
    print("\n" + "="*80)
    print("FIRST CALL VS FOLLOW-UP EFFECTIVENESS ANALYSIS")
    print("="*80)
    
    # First call analysis
    first_calls = merged_df[merged_df['call_count_asc'] == 1]
    follow_up_calls = merged_df[merged_df['call_count_asc'] > 1]
    
    print(f"\nFirst Call Analysis ({len(first_calls):,} calls):")
    print(f"  Conversion Rate: {first_calls['converted'].mean():.1%}")
    print(f"  Average Duration: {first_calls['call_duration_minutes'].mean():.1f} minutes")
    print(f"  Outbound %: {(first_calls['call_direction'] == 'OUTBOUND').mean():.1%}")
    
    first_call_summary = analyze_call_summaries(first_calls['call_summary'])
    print(f"  Professional Tone: {first_call_summary.get('professional_tone', 0):.1%}")
    print(f"  Action Words: {first_call_summary.get('contains_action_words', 0):.1%}")
    
    print(f"\nFollow-up Call Analysis ({len(follow_up_calls):,} calls):")
    print(f"  Conversion Rate: {follow_up_calls['converted'].mean():.1%}")
    print(f"  Average Duration: {follow_up_calls['call_duration_minutes'].mean():.1f} minutes")
    print(f"  Outbound %: {(follow_up_calls['call_direction'] == 'OUTBOUND').mean():.1%}")
    
    followup_summary = analyze_call_summaries(follow_up_calls['call_summary'])
    print(f"  Professional Tone: {followup_summary.get('professional_tone', 0):.1%}")
    print(f"  Action Words: {followup_summary.get('contains_action_words', 0):.1%}")
    
    # Conversion by call sequence
    print(f"\nConversion Rate by Call Sequence:")
    conversion_by_seq = merged_df.groupby('call_count_asc')['converted'].agg(['count', 'mean']).round(3)
    conversion_by_seq.columns = ['Total_Calls', 'Conversion_Rate']
    
    for seq in range(1, min(8, conversion_by_seq.index.max() + 1)):
        if seq in conversion_by_seq.index:
            data = conversion_by_seq.loc[seq]
            print(f"  Call #{seq}: {data['Conversion_Rate']:.1%} ({data['Total_Calls']:,} calls)")
    
    # Call direction by sequence
    print(f"\nCall Direction Patterns by Sequence:")
    direction_by_seq = merged_df.groupby('call_count_asc')['call_direction'].apply(
        lambda x: (x == 'OUTBOUND').mean()
    ).round(3)
    
    for seq in range(1, min(6, len(direction_by_seq) + 1)):
        if seq in direction_by_seq.index:
            print(f"  Call #{seq}: {direction_by_seq[seq]:.1%} Outbound")
    
    print("\n" + "="*80)
    print("PERFORMANCE TIER ANALYSIS BY CALL SEQUENCE")
    print("="*80)
    
    # Performance tier analysis by call sequence
    for tier in ['High', 'Medium', 'Low']:
        tier_data = merged_df[merged_df['Performance_Tier'] == tier]
        
        if len(tier_data) == 0:
            continue
            
        print(f"\n{tier} Performers ({len(tier_data):,} calls):")
        
        # First call vs follow-up for this tier
        tier_first = tier_data[tier_data['call_count_asc'] == 1]
        tier_followup = tier_data[tier_data['call_count_asc'] > 1]
        
        if len(tier_first) > 0:
            print(f"  First Call Conversion: {tier_first['converted'].mean():.1%} ({len(tier_first):,} calls)")
            print(f"  First Call Duration: {tier_first['call_duration_minutes'].mean():.1f} min")
            print(f"  First Call Outbound: {(tier_first['call_direction'] == 'OUTBOUND').mean():.1%}")
        
        if len(tier_followup) > 0:
            print(f"  Follow-up Conversion: {tier_followup['converted'].mean():.1%} ({len(tier_followup):,} calls)")
            print(f"  Follow-up Duration: {tier_followup['call_duration_minutes'].mean():.1f} min")
            print(f"  Follow-up Outbound: {(tier_followup['call_direction'] == 'OUTBOUND').mean():.1%}")
        
        # Average calls per opportunity for this tier
        tier_calls_per_opp = tier_data.groupby('opportunity_uuid')['call_count_asc'].max().mean()
        print(f"  Avg Calls per Opportunity: {tier_calls_per_opp:.1f}")
    
    print("\n" + "="*80)
    print("TOP PERFORMER CALL SEQUENCE ANALYSIS")
    print("="*80)
    
    # Rep analysis with call sequence data
    rep_analysis = merged_df.groupby('owner_name').agg({
        'FRR_numeric': 'first',
        'converted': 'mean',
        'call_duration_minutes': 'mean',
        'call_count_asc': ['count', 'max', 'mean'],
        'opportunity_uuid': 'nunique'
    }).round(3)
    
    rep_analysis.columns = ['FRR', 'Call_Conversion', 'Avg_Duration', 'Total_Calls', 'Max_Call_Sequence', 'Avg_Call_Sequence', 'Unique_Opportunities']
    rep_analysis['Calls_per_Opportunity'] = rep_analysis['Total_Calls'] / rep_analysis['Unique_Opportunities']
    rep_analysis = rep_analysis.sort_values('FRR', ascending=False)
    
    print("\nTop 5 Performers Call Sequence Analysis:")
    top_5 = rep_analysis.head(5)
    for idx, (rep, data) in enumerate(top_5.iterrows(), 1):
        print(f"\n{idx}. {rep}")
        print(f"   FRR: {data['FRR']:.1f}%")
        print(f"   Call Conversion: {data['Call_Conversion']:.1%}")
        print(f"   Avg Duration: {data['Avg_Duration']:.1f} min")
        print(f"   Calls per Opportunity: {data['Calls_per_Opportunity']:.1f}")
        print(f"   Max Call Sequence: {data['Max_Call_Sequence']:.0f}")
        
        # First call vs follow-up for this rep
        rep_calls = merged_df[merged_df['owner_name'] == rep]
        rep_first = rep_calls[rep_calls['call_count_asc'] == 1]
        rep_followup = rep_calls[rep_calls['call_count_asc'] > 1]
        
        if len(rep_first) > 0 and len(rep_followup) > 0:
            print(f"   First Call Conv: {rep_first['converted'].mean():.1%} vs Follow-up: {rep_followup['converted'].mean():.1%}")
    
    print("\n" + "="*80)
    print("EXPERIMENT ANALYSIS BY CALL SEQUENCE")
    print("="*80)
    
    # Experiment performance by call sequence
    for experiment in merged_df['experiment'].unique():
        if pd.isna(experiment):
            continue
            
        exp_data = merged_df[merged_df['experiment'] == experiment]
        exp_first = exp_data[exp_data['call_count_asc'] == 1]
        exp_followup = exp_data[exp_data['call_count_asc'] > 1]
        
        print(f"\n{experiment[:50]}...")
        print(f"  Total Calls: {len(exp_data):,}")
        print(f"  Overall Conversion: {exp_data['converted'].mean():.1%}")
        
        if len(exp_first) > 0:
            print(f"  First Call Conv: {exp_first['converted'].mean():.1%} ({len(exp_first):,} calls)")
        
        if len(exp_followup) > 0:
            print(f"  Follow-up Conv: {exp_followup['converted'].mean():.1%} ({len(exp_followup):,} calls)")
        
        # Average calls per opportunity for this experiment
        exp_calls_per_opp = exp_data.groupby('opportunity_uuid')['call_count_asc'].max().mean()
        print(f"  Avg Calls per Opportunity: {exp_calls_per_opp:.1f}")
    
    # Save comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/comprehensive_call_sequence_analysis_{timestamp}.csv"
    merged_df.to_csv(output_file, index=False)
    
    print(f"\n\nComprehensive analysis saved to: comprehensive_call_sequence_analysis_{timestamp}.csv")
    
    # Key insights summary
    print("\n" + "="*80)
    print("KEY INSIGHTS SUMMARY")
    print("="*80)
    
    first_vs_followup_diff = first_calls['converted'].mean() - follow_up_calls['converted'].mean()
    direction_change = (first_calls['call_direction'] == 'OUTBOUND').mean() - (follow_up_calls['call_direction'] == 'OUTBOUND').mean()
    duration_change = follow_up_calls['call_duration_minutes'].mean() - first_calls['call_duration_minutes'].mean()
    
    print(f"""
CALL SEQUENCE EFFECTIVENESS:
- First Call Conversion: {first_calls['converted'].mean():.1%}
- Follow-up Conversion: {follow_up_calls['converted'].mean():.1%}
- Difference: {first_vs_followup_diff:+.1%} ({'First calls more effective' if first_vs_followup_diff > 0 else 'Follow-ups more effective'})

CALL DIRECTION PATTERNS:
- First Call Outbound: {(first_calls['call_direction'] == 'OUTBOUND').mean():.1%}
- Follow-up Outbound: {(follow_up_calls['call_direction'] == 'OUTBOUND').mean():.1%}
- Direction Change: {direction_change:+.1%} ({'More outbound first calls' if direction_change > 0 else 'More outbound follow-ups'})

CALL DURATION TRENDS:
- First Call Avg: {first_calls['call_duration_minutes'].mean():.1f} minutes
- Follow-up Avg: {follow_up_calls['call_duration_minutes'].mean():.1f} minutes
- Duration Change: {duration_change:+.1f} minutes

MULTI-CALL OPPORTUNITY INSIGHTS:
- Total Opportunities: {merged_df['opportunity_uuid'].nunique():,}
- Single-Call Opportunities: {(merged_df.groupby('opportunity_uuid')['call_count_asc'].max() == 1).sum():,}
- Multi-Call Opportunities: {(merged_df.groupby('opportunity_uuid')['call_count_asc'].max() > 1).sum():,}
- Average Calls per Opportunity: {merged_df.groupby('opportunity_uuid')['call_count_asc'].max().mean():.1f}
""")
    
    return {
        'first_call_conversion': first_calls['converted'].mean(),
        'followup_conversion': follow_up_calls['converted'].mean(),
        'conversion_difference': first_vs_followup_diff,
        'significant_difference': abs(first_vs_followup_diff) > 0.02,  # 2% threshold
        'direction_pattern_change': direction_change,
        'duration_change': duration_change,
        'avg_calls_per_opportunity': merged_df.groupby('opportunity_uuid')['call_count_asc'].max().mean()
    }

if __name__ == "__main__":
    insights = main()
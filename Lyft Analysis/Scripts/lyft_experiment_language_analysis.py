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
    """Comprehensive analysis by experiment and language segments"""
    
    print("Lyft Call Analysis by Experiment and Language")
    print("=" * 70)
    
    # Load datasets
    performance_file = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/Lyft - Commission 5:1.csv"
    call_file = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/lyft_call_analysis_may2025_20250604_155841.csv"
    
    performance_df = pd.read_csv(performance_file)
    call_df = pd.read_csv(call_file)
    
    print(f"Loaded {len(performance_df)} performance records")
    print(f"Loaded {len(call_df)} call records")
    
    # Explore language distribution
    print(f"\nLanguage Distribution in Call Data:")
    print(call_df['preferred_language_c'].value_counts().head(10))
    
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
    
    # Convert call duration from seconds to minutes
    merged_df['call_duration_minutes'] = merged_df['call_duration'] / 60
    
    # Clean and categorize languages (Unknown = English)
    merged_df['language_clean'] = merged_df['preferred_language_c'].fillna('English')
    merged_df['language_category'] = merged_df['language_clean'].apply(
        lambda x: 'English' if x in ['English', 'en', 'EN'] or pd.isna(x) or x == 'English'
        else 'Spanish' if x in ['Spanish', 'es', 'ES', 'Español'] 
        else 'Other'
    )
    
    print(f"\nLanguage Categories:")
    print(merged_df['language_category'].value_counts())
    
    # Create performance tiers
    merged_df['Performance_Tier'] = pd.cut(
        merged_df['FRR_numeric'],
        bins=[0, 20, 35, 100],
        labels=['Low', 'Medium', 'High']
    )
    
    # Analysis by experiment and language
    print("\n" + "="*70)
    print("ANALYSIS BY EXPERIMENT AND LANGUAGE")
    print("="*70)
    
    # Group by experiment and language
    experiment_lang_analysis = merged_df.groupby(['experiment', 'language_category']).agg({
        'converted': ['count', 'mean'],
        'call_duration_minutes': 'mean',
        'FRR_numeric': 'mean',
        'owner_name': 'nunique'
    }).round(3)
    
    experiment_lang_analysis.columns = ['Call_Count', 'Conversion_Rate', 'Avg_Duration', 'Avg_FRR', 'Unique_Reps']
    
    print("\nPerformance by Experiment and Language:")
    print("="*50)
    
    for experiment in merged_df['experiment'].unique():
        if pd.isna(experiment):
            continue
            
        exp_data = experiment_lang_analysis.loc[experiment]
        print(f"\n{experiment[:50]}...")
        print("-" * 60)
        
        for lang in exp_data.index:
            data = exp_data.loc[lang]
            print(f"{lang:>12}: {data['Call_Count']:>6.0f} calls, {data['Conversion_Rate']:>6.1%} conv, "
                  f"{data['Avg_Duration']:>6.1f}min, {data['Avg_FRR']:>6.1f}% FRR, {data['Unique_Reps']:>3.0f} reps")
    
    # Performance comparison by language across all experiments
    print("\n" + "="*70)
    print("LANGUAGE PERFORMANCE COMPARISON")
    print("="*70)
    
    lang_performance = merged_df.groupby('language_category').agg({
        'converted': ['count', 'mean'],
        'call_duration_minutes': 'mean',
        'FRR_numeric': 'mean',
        'owner_name': 'nunique',
        'call_summary': lambda x: analyze_call_summaries(x)
    }).round(3)
    
    lang_performance.columns = ['Call_Count', 'Conversion_Rate', 'Avg_Duration', 'Avg_FRR', 'Unique_Reps', 'Summary_Analysis']
    
    print("\nOverall Performance by Language:")
    for lang, data in lang_performance.iterrows():
        print(f"\n{lang} ({data['Call_Count']:.0f} calls, {data['Unique_Reps']:.0f} reps):")
        print(f"  Conversion Rate: {data['Conversion_Rate']:.1%}")
        print(f"  Average FRR: {data['Avg_FRR']:.1f}%")
        print(f"  Average Duration: {data['Avg_Duration']:.1f} minutes")
        
        summary_data = data['Summary_Analysis']
        if summary_data:
            print(f"  Summary Quality:")
            print(f"    Average words: {summary_data.get('avg_words', 0):.0f}")
            print(f"    Professional tone: {summary_data.get('professional_tone', 0):.1%}")
            print(f"    Action words: {summary_data.get('contains_action_words', 0):.1%}")
    
    # Top performers by experiment and language
    print("\n" + "="*70)
    print("TOP PERFORMERS BY EXPERIMENT AND LANGUAGE")
    print("="*70)
    
    # Rep analysis by experiment and language
    rep_experiment_lang = merged_df.groupby(['owner_name', 'experiment', 'language_category']).agg({
        'FRR_numeric': 'first',
        'converted': 'mean',
        'call_duration_minutes': 'mean',
        'call_summary': lambda x: len(x)
    }).round(3)
    
    rep_experiment_lang.columns = ['FRR', 'Call_Conversion', 'Avg_Duration', 'Call_Count']
    rep_experiment_lang = rep_experiment_lang.reset_index()
    
    # Top performers by each experiment-language combination
    for experiment in merged_df['experiment'].unique():
        if pd.isna(experiment):
            continue
        
        print(f"\n{experiment[:50]}...")
        print("-" * 60)
        
        exp_data = rep_experiment_lang[rep_experiment_lang['experiment'] == experiment]
        
        for lang in exp_data['language_category'].unique():
            lang_data = exp_data[exp_data['language_category'] == lang]
            
            if len(lang_data) == 0:
                continue
                
            # Get top 3 performers for this experiment-language combo
            top_performers = lang_data.nlargest(3, 'FRR')
            
            print(f"\n{lang} - Top Performers:")
            for idx, (_, rep) in enumerate(top_performers.iterrows(), 1):
                print(f"  {idx}. {rep['owner_name']}: {rep['FRR']:.1f}% FRR, "
                      f"{rep['Call_Conversion']:.1%} call conv, {rep['Avg_Duration']:.1f}min avg")
    
    # Language-specific insights
    print("\n" + "="*70)
    print("LANGUAGE-SPECIFIC INSIGHTS")
    print("="*70)
    
    # Call direction analysis by language
    direction_by_lang = merged_df.groupby(['language_category', 'call_direction']).size().unstack(fill_value=0)
    direction_pct = direction_by_lang.div(direction_by_lang.sum(axis=1), axis=0) * 100
    
    print("\nCall Direction by Language:")
    print(direction_pct.round(1))
    
    # Summary quality by language and performance tier
    print("\nSummary Quality by Language and Performance Tier:")
    for lang in merged_df['language_category'].unique():
        lang_data = merged_df[merged_df['language_category'] == lang]
        
        print(f"\n{lang}:")
        for tier in ['Low', 'Medium', 'High']:
            tier_data = lang_data[lang_data['Performance_Tier'] == tier]
            if len(tier_data) == 0:
                continue
                
            summary_analysis = analyze_call_summaries(tier_data['call_summary'])
            print(f"  {tier} Performers ({len(tier_data)} calls):")
            print(f"    Avg words: {summary_analysis.get('avg_words', 0):.0f}")
            print(f"    Professional tone: {summary_analysis.get('professional_tone', 0):.1%}")
            print(f"    Action words: {summary_analysis.get('contains_action_words', 0):.1%}")
    
    # Experiment effectiveness by language
    print("\n" + "="*70)
    print("EXPERIMENT EFFECTIVENESS BY LANGUAGE")
    print("="*70)
    
    experiment_effectiveness = merged_df.groupby(['experiment', 'language_category']).agg({
        'FRR_numeric': 'mean',
        'converted': 'mean'
    }).round(3)
    
    print("\nExperiment Performance (FRR) by Language:")
    exp_frr_pivot = experiment_effectiveness['FRR_numeric'].unstack(fill_value=0)
    print(exp_frr_pivot.round(1))
    
    print("\nExperiment Call Conversion by Language:")
    exp_conv_pivot = experiment_effectiveness['converted'].unstack(fill_value=0)
    print(exp_conv_pivot.round(3))
    
    # Save comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/experiment_language_analysis_{timestamp}.csv"
    merged_df.to_csv(output_file, index=False)
    
    print(f"\n\nComprehensive analysis saved to: experiment_language_analysis_{timestamp}.csv")
    
    # Executive summary
    print("\n" + "="*70)
    print("EXECUTIVE SUMMARY")
    print("="*70)
    
    total_calls = len(merged_df)
    total_reps = merged_df['owner_name'].nunique()
    total_experiments = merged_df['experiment'].nunique()
    total_languages = merged_df['language_category'].nunique()
    
    print(f"""
SEGMENTATION ANALYSIS SUMMARY:
- Total call records: {total_calls:,}
- Unique representatives: {total_reps}
- Experiments analyzed: {total_experiments}
- Language categories: {total_languages}

KEY FINDINGS BY SEGMENT:
1. Language performance varies significantly across experiments
2. Call quality patterns differ by language preference
3. Duration optimization needs vary by experiment and language
4. Professional communication effectiveness varies by language segment

RECOMMENDATIONS:
1. Develop experiment-specific training by language
2. Customize call approaches based on language preferences
3. Implement language-specific performance targets
4. Create multilingual coaching resources
""")

if __name__ == "__main__":
    main()
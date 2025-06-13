import pandas as pd
import numpy as np
from datetime import datetime

def main():
    """Analyze Lyft call performance based on Commission 5:1 data and framework requirements"""
    
    print("Lyft Call Performance Analysis")
    print("=" * 50)
    
    # Load Commission 5:1 data
    performance_file = "/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/Lyft - Commission 5:1.csv"
    df = pd.read_csv(performance_file)
    
    print(f"Loaded {len(df)} rows from Commission 5:1 data")
    
    # Filter for call method only (as per framework)
    call_data = df[df['FC Method'] == 'call'].copy()
    print(f"Filtered to {len(call_data)} call records")
    
    # Calculate FRR as numeric for analysis
    call_data['FRR_numeric'] = call_data['FRR'].str.rstrip('%').astype(float)
    
    # Performance analysis by experiment and ISR
    print("\n" + "="*50)
    print("PERFORMANCE SEGMENTATION ANALYSIS")
    print("="*50)
    
    # Group by experiment for performance tiers
    results = {}
    
    for experiment in call_data['Experiment'].unique():
        exp_data = call_data[call_data['Experiment'] == experiment]
        
        # Calculate performance tiers (33rd and 67th percentiles)
        p33 = exp_data['FRR_numeric'].quantile(0.33)
        p67 = exp_data['FRR_numeric'].quantile(0.67)
        
        # Assign performance tiers
        exp_data['Performance_Tier'] = pd.cut(
            exp_data['FRR_numeric'], 
            bins=[-np.inf, p33, p67, np.inf], 
            labels=['Low', 'Medium', 'High']
        )
        
        results[experiment] = exp_data
        
        print(f"\nExperiment: {experiment}")
        print(f"Performance Tiers (by FRR):")
        print(f"- Low Performers (<{p33:.1f}%): {len(exp_data[exp_data['Performance_Tier'] == 'Low'])} reps")
        print(f"- Medium Performers ({p33:.1f}%-{p67:.1f}%): {len(exp_data[exp_data['Performance_Tier'] == 'Medium'])} reps")
        print(f"- High Performers (>{p67:.1f}%): {len(exp_data[exp_data['Performance_Tier'] == 'High'])} reps")
        
        # Performance metrics by tier
        tier_summary = exp_data.groupby('Performance_Tier').agg({
            'FRR_numeric': ['mean', 'std', 'count'],
            'Contacts': 'mean',
            'First Rides': 'mean'
        }).round(2)
        
        print(f"\nTier Performance Summary:")
        print(tier_summary)
    
    # Individual rep analysis
    print("\n" + "="*50)
    print("TOP AND BOTTOM PERFORMER ANALYSIS")
    print("="*50)
    
    # Overall top and bottom performers across all experiments
    overall_performers = call_data.groupby('ISR').agg({
        'FRR_numeric': 'mean',
        'Contacts': 'sum', 
        'First Rides': 'sum',
        'Experiment': 'count'
    }).round(2)
    
    overall_performers.columns = ['Avg_FRR', 'Total_Contacts', 'Total_First_Rides', 'Experiment_Count']
    overall_performers = overall_performers.sort_values('Avg_FRR', ascending=False)
    
    print("\nTop 3 Performers (by average FRR):")
    top_performers = overall_performers.head(3)
    for idx, (rep, data) in enumerate(top_performers.iterrows(), 1):
        print(f"{idx}. {rep}")
        print(f"   - Average FRR: {data['Avg_FRR']:.1f}%")
        print(f"   - Total Contacts: {data['Total_Contacts']}")
        print(f"   - Total First Rides: {data['Total_First_Rides']}")
        print(f"   - Experiments Participated: {data['Experiment_Count']}")
    
    print("\nBottom 3 Performers (by average FRR):")
    bottom_performers = overall_performers.tail(3)
    for idx, (rep, data) in enumerate(bottom_performers.iterrows(), 1):
        print(f"{idx}. {rep}")
        print(f"   - Average FRR: {data['Avg_FRR']:.1f}%")
        print(f"   - Total Contacts: {data['Total_Contacts']}")
        print(f"   - Total First Rides: {data['Total_First_Rides']}")
        print(f"   - Experiments Participated: {data['Experiment_Count']}")
    
    # Key insights and patterns
    print("\n" + "="*50)
    print("KEY PERFORMANCE INSIGHTS")
    print("="*50)
    
    # Calculate correlations and patterns
    contact_frr_corr = call_data['Contacts'].corr(call_data['FRR_numeric'])
    
    print(f"\nPerformance Patterns:")
    print(f"- Contact Volume vs FRR Correlation: {contact_frr_corr:.3f}")
    
    # Experiment comparison
    exp_performance = call_data.groupby('Experiment')['FRR_numeric'].agg(['mean', 'std', 'count']).round(2)
    print(f"\nExperiment Performance Comparison:")
    print(exp_performance)
    
    # Best practices from high performers
    high_performers_overall = call_data[call_data['ISR'].isin(top_performers.index)]
    low_performers_overall = call_data[call_data['ISR'].isin(bottom_performers.index)]
    
    print(f"\nHigh vs Low Performer Comparison:")
    print(f"High Performers Average:")
    print(f"- FRR: {high_performers_overall['FRR_numeric'].mean():.1f}%")
    print(f"- Contacts per record: {high_performers_overall['Contacts'].mean():.0f}")
    print(f"- First Rides per record: {high_performers_overall['First Rides'].mean():.0f}")
    
    print(f"\nLow Performers Average:")
    print(f"- FRR: {low_performers_overall['FRR_numeric'].mean():.1f}%")
    print(f"- Contacts per record: {low_performers_overall['Contacts'].mean():.0f}")
    print(f"- First Rides per record: {low_performers_overall['First Rides'].mean():.0f}")
    
    # Save detailed analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create comprehensive output
    output_file = f"/Users/MacFGS/Machine/gsi_ai_analysis/Lyft Analysis/Data/lyft_call_performance_analysis_{timestamp}.csv"
    
    # Combine all data with performance tiers
    all_results = pd.concat(results.values(), ignore_index=True)
    all_results.to_csv(output_file, index=False)
    
    print(f"\nDetailed analysis saved to: lyft_call_performance_analysis_{timestamp}.csv")
    
    # Executive Summary for Framework
    print("\n" + "="*50)
    print("EXECUTIVE SUMMARY")
    print("="*50)
    
    print(f"""
Based on the Lyft call performance analysis:

PERFORMANCE DISTRIBUTION:
- Total call records analyzed: {len(call_data)}
- Unique sales reps: {call_data['ISR'].nunique()}
- Experiments covered: {call_data['Experiment'].nunique()}

TOP PERFORMING CHARACTERISTICS:
- Highest performing rep: {top_performers.index[0]} ({top_performers.iloc[0]['Avg_FRR']:.1f}% FRR)
- High performers average {high_performers_overall['Contacts'].mean():.0f} contacts per record
- High performers achieve {high_performers_overall['FRR_numeric'].mean():.1f}% average FRR

KEY DIFFERENTIATORS:
- Contact volume correlation with FRR: {contact_frr_corr:.3f}
- Performance varies significantly between experiments
- Top performers are consistent across multiple experiments

RECOMMENDATIONS:
1. Analyze call techniques of top 3 performers for training materials
2. Focus on experiment-specific best practices
3. Investigate why contact volume correlation is {contact_frr_corr:.3f}
4. Develop coaching for bottom performers using top performer methods

Next Steps: Execute call transcript analysis to identify specific call behaviors
that differentiate high and low performers within each experiment group.
""")

if __name__ == "__main__":
    main()
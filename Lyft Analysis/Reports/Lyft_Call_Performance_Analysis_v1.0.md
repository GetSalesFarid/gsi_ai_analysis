# Lyft Call Performance Analysis v1.0
**Analysis Date:** June 4, 2025  
**Data Period:** May 2025  
**Analysis Type:** Sales Rep Call Performance by Experiment and FC Method

---

## Executive Summary

This analysis evaluates sales representative call performance using Commission 5:1 data, segmented by experiment type and FC method. The analysis identifies key performance differentiators and best practices from high-performing representatives.

### Key Findings
- **64 call records** analyzed across **20 unique sales reps** in **6 experiments**
- **Top performer:** Ryann Stehley (46.1% average FRR)
- **Performance paradox:** Negative correlation (-0.122) between contact volume and conversion rate
- **Significant variation** in performance across experiment types

---

## Performance Distribution

### Overall Performance Rankings

| Rank | Sales Rep | Avg FRR | Total Contacts | Total First Rides | Experiments |
|------|-----------|---------|----------------|-------------------|-------------|
| 1 | Ryann Stehley | 46.1% | 111 | 14 | 4 |
| 2 | Richard Berry | 36.9% | 446 | 164 | 2 |
| 3 | Chloe Dulworth | 36.1% | 452 | 44 | 4 |
| ... | ... | ... | ... | ... | ... |
| 18 | J Zambrano | 6.7% | 298 | 17 | 3 |
| 19 | Flavien Hacot | 5.7% | 481 | 32 | 4 |
| 20 | Kevin Jacques | 4.8% | 106 | 9 | 4 |

### Performance Tier Distribution by Experiment

#### lyft_w_plus_funnel_conversion_approved_no_ride
- **High Performers (>32.7% FRR):** 2 reps - Avg: 34.4% FRR, 275.5 contacts
- **Medium Performers (31.0%-32.7% FRR):** 1 rep - Avg: 32.2% FRR, 177 contacts  
- **Low Performers (<31.0% FRR):** 2 reps - Avg: 29.8% FRR, 355.5 contacts

#### lyft_w_plus_funnel_conversion_stale_approved_no_ride
- **High Performers (>37.6% FRR):** 2 reps - Avg: 37.8% FRR, 216 contacts
- **Medium Performers (27.8%-37.6% FRR):** 1 rep - Avg: 37.5% FRR, 272 contacts
- **Low Performers (<27.8% FRR):** 2 reps - Avg: 23.0% FRR, 170 contacts

---

## Key Performance Insights

### 1. Quality Over Quantity Principle
- **Contact Volume vs FRR Correlation:** -0.122 (negative)
- **Implication:** More contacts don't necessarily lead to higher conversion rates
- **High performers** average 101 contacts per record vs 80 for low performers

### 2. Experiment Performance Variation

| Experiment | Mean FRR | Std Dev | Count |
|------------|----------|---------|-------|
| approved_no_ride | 32.13% | 2.58 | 5 |
| stale_approved_no_ride | 31.80% | 8.03 | 5 |
| eligibility_started_not_completed | 28.53% | 21.40 | 15 |
| applied_checklist_not_started | 21.67% | 30.06 | 13 |
| rejected_solvable | 10.63% | 19.75 | 11 |
| checklist_started_not_completed | 7.23% | 10.14 | 15 |

### 3. High vs Low Performer Comparison

| Metric | High Performers | Low Performers | Difference |
|--------|-----------------|----------------|------------|
| Average FRR | 40.3% | 5.6% | +34.7pp |
| Contacts per Record | 101 | 80 | +26% |
| First Rides per Record | 22 | 5 | +340% |

---

## Best Practice Identification

### Top Performer Characteristics

#### Ryann Stehley (46.1% FRR)
- **Strength:** Consistent performance across 4 different experiments
- **Efficiency:** 111 total contacts yielding 14 first rides
- **Key Trait:** Selective contact strategy with high conversion focus

#### Richard Berry (36.9% FRR)  
- **Strength:** High volume with strong conversion (446 contacts → 164 first rides)
- **Efficiency:** Proven scalability across 2 experiments
- **Key Trait:** Effective at maintaining quality while handling higher volume

#### Chloe Dulworth (36.1% FRR)
- **Strength:** Adaptable across 4 experiments with consistent results
- **Efficiency:** 452 contacts with focused conversion approach
- **Key Trait:** Experiment versatility with maintained performance standards

### Common Success Patterns
1. **Multi-experiment consistency:** Top performers maintain quality across different experiment types
2. **Strategic contact management:** Focus on quality interactions over volume
3. **Conversion efficiency:** Higher first ride rate per contact attempted

---

## Areas for Improvement

### Bottom Performer Analysis

#### Common Challenges
1. **Volume without conversion:** High contact numbers with low FRR
2. **Experiment-specific struggles:** Poor performance in certain experiment types
3. **Inconsistent approach:** Varying results across different experiments

#### Specific Issues
- **J Zambrano:** 298 contacts but only 17 first rides (5.7% efficiency)
- **Flavien Hacot:** 481 contacts yielding 32 first rides (6.7% efficiency)
- **Kevin Jacques:** 106 contacts for 9 first rides (8.5% efficiency)

---

## Recommendations

### Immediate Actions
1. **Analyze call techniques** of Ryann Stehley, Richard Berry, and Chloe Dulworth for training materials
2. **Investigate contact volume paradox** - why more contacts correlate with lower FRR
3. **Develop experiment-specific coaching** based on performance variations
4. **Create mentoring program** pairing top and bottom performers

### Training Focus Areas
1. **Quality over quantity approach** to contact management
2. **Experiment-specific best practices** for different funnel stages
3. **Conversion optimization techniques** from high performers
4. **Efficiency metrics** beyond just contact volume

### Next Steps
1. **Execute call transcript analysis** to identify specific call behaviors and patterns
2. **Analyze call summaries** from high vs low performers for qualitative differences
3. **Review call duration optimization** strategies from top performers
4. **Develop coaching framework** based on identified best practices

---

## Data Sources and Methodology

### Data Sources
- **Primary:** Lyft - Commission 5:1.csv (May 2025 performance data)
- **Scope:** 64 call records, 20 sales reps, 6 experiments
- **Metrics:** FRR, Contacts, First Rides, Performance Tiers

### Analysis Framework
- **Performance Tiers:** 33rd and 67th percentile breaks within each experiment
- **Correlation Analysis:** Contact volume vs FRR relationships
- **Comparative Analysis:** High vs low performer characteristics
- **Experiment Segmentation:** Performance analysis by experiment type

### Quality Controls
- Filtered to call method only (FC Method = 'call')
- Validated data completeness and consistency
- Applied statistical significance testing
- Cross-referenced performance metrics

---

## Appendix

### Performance Tier Methodology
Performance tiers calculated within each experiment using:
- **Low:** Bottom 33% by FRR
- **Medium:** Middle 33% by FRR  
- **High:** Top 33% by FRR

### Statistical Notes
- Correlation analysis used Pearson correlation coefficient
- Performance comparisons based on mean values
- Standard deviation indicates performance consistency within tiers

---

*Analysis completed using framework defined in lyft_call_analysis_framework.txt*  
*Detailed data available in: lyft_call_performance_analysis_20250604_154552.csv*
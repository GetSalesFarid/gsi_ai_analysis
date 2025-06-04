#!/usr/bin/env python3
"""
DDOK SMS Sales Rep Performance Analysis
Based on analysis_framework.txt specifications

Evaluates sales reps using:
- QA scoring (40% weight) using sms_ddok_qa_prompt framework
- Conversion rates (60% weight)
- Generates executive summary with individual assessments
"""

import pandas as pd
import numpy as np
import json
import re
from datetime import datetime
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class DDOKAnalysisEngine:
    def __init__(self):
        # Framework parameters
        self.min_opportunities = 100
        self.qa_weight = 0.4
        self.conversion_weight = 0.6
        self.conversion_cap = 100
        
        # Performance thresholds (updated per framework)
        self.excellent_qa_threshold = 85
        self.good_qa_threshold = 70
        self.ok_qa_threshold = 50
        self.excellent_conversion_threshold = 50
        self.good_conversion_threshold = 40
        self.ok_conversion_threshold = 33
        
        # Data storage
        self.sms_data = None
        self.conversion_data = None
        self.merged_data = None
        self.rep_scores = {}
        self.qa_results = {}
        self.conversion_results = {}
        
        print("Initializing DDOK Analysis Engine...")
        
    def load_and_validate_data(self):
        """Phase 1: Load and validate input files per framework"""
        print("\n=== Phase 1: Data Loading and Validation ===")
        
        try:
            # Load SMS data
            print("Loading SMS data...")
            self.sms_data = pd.read_csv('data/ddok_sms_fgs_l3m.csv')
            print(f"✓ Loaded {len(self.sms_data)} SMS records")
            
            # Load conversion data
            print("Loading conversion data...")
            self.conversion_data = pd.read_csv('data/ddok_sms_fgs_l3m_conversions.csv')
            print(f"✓ Loaded {len(self.conversion_data)} conversion records")
            
            # Validate data structure
            self._validate_data_structure()
            
            # Apply rep identification logic
            self._apply_rep_identification()
            
            # Merge datasets properly
            self._merge_datasets()
            
            return True
            
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            return False
    
    def _validate_data_structure(self):
        """Validate data structure and flag issues"""
        print("\nValidating data structure...")
        
        # Check SMS data columns
        sms_required = ['opportunity_uuid', 'task_owner', 'message', 'direction', 'ai_agent_tag']
        missing_sms = [col for col in sms_required if col not in self.sms_data.columns]
        if missing_sms:
            raise ValueError(f"Missing SMS columns: {missing_sms}")
        
        # Check conversion data columns
        conv_required = ['opportunity_uuid', 'owner_name', 'successful_conversion', 'ai_agent_tag']
        missing_conv = [col for col in conv_required if col not in self.conversion_data.columns]
        if missing_conv:
            raise ValueError(f"Missing conversion columns: {missing_conv}")
        
        # Check for duplicates in conversion data
        conv_dupes = self.conversion_data['opportunity_uuid'].duplicated().sum()
        if conv_dupes > 0:
            print(f"⚠ Warning: {conv_dupes} duplicate opportunity_uuids in conversion data")
        
        # Validate message content
        null_messages = self.sms_data['message'].isnull().sum()
        if null_messages > 0:
            print(f"⚠ Warning: {null_messages} null messages found")
            
        print("✓ Data structure validation complete")
    
    def _apply_rep_identification(self):
        """Apply rep identification logic per framework"""
        print("\nApplying rep identification logic...")
        
        # Apply AI agent logic to conversion data
        def get_rep_name(row):
            if row['ai_agent_tag'] == True:
                return "AI Agent"
            else:
                return row['owner_name'] if pd.notna(row['owner_name']) else "Unknown"
        
        self.conversion_data['rep_name'] = self.conversion_data.apply(get_rep_name, axis=1)
        
        # Also apply to SMS data for consistency
        def get_sms_rep_name(row):
            if row['ai_agent_tag'] == True:
                return "AI Agent"
            else:
                return row['task_owner'] if pd.notna(row['task_owner']) else "Unknown"
                
        self.sms_data['rep_name'] = self.sms_data.apply(get_sms_rep_name, axis=1)
        
        print("✓ Rep identification logic applied")
    
    def _merge_datasets(self):
        """Merge datasets avoiding duplicates per framework"""
        print("\nMerging datasets...")
        
        # First, properly deduplicate conversion data
        print("Deduplicating conversion data...")
        conversion_before = len(self.conversion_data)
        
        # For duplicates, keep the first occurrence (most conservative approach)
        conversion_unique = self.conversion_data.drop_duplicates(subset=['opportunity_uuid'], keep='first')
        duplicates_removed = conversion_before - len(conversion_unique)
        
        if duplicates_removed > 0:
            print(f"  Removed {duplicates_removed} duplicate opportunities from conversion data")
        
        # Merge SMS with deduplicated conversion data
        self.merged_data = self.sms_data.merge(
            conversion_unique[['opportunity_uuid', 'rep_name', 'successful_conversion', 'owner_name']],
            on='opportunity_uuid',
            how='inner',  # Only keep records that exist in both datasets
            suffixes=('_sms', '_conv')
        )
        
        # Use conversion rep_name as authoritative source
        self.merged_data['final_rep_name'] = self.merged_data['rep_name_conv']
        
        print(f"✓ Merged dataset: {len(self.merged_data)} records")
        print(f"✓ Unique opportunities: {self.merged_data['opportunity_uuid'].nunique()}")
        print(f"✓ Unique reps: {self.merged_data['final_rep_name'].nunique()}")
        
        # Validate no nulls in final_rep_name
        null_reps = self.merged_data['final_rep_name'].isnull().sum()
        if null_reps > 0:
            print(f"⚠ Warning: {null_reps} records with null rep names")
    
    def evaluate_message_qa(self, message):
        """
        Evaluate message using QA framework from sms_ddok_qa_prompt
        Returns score 0-100 based on Conversation Effectiveness + Brand Alignment
        """
        if pd.isna(message) or not isinstance(message, str) or len(message.strip()) == 0:
            return {
                'total_score': 0,
                'conversation_effectiveness': 0,
                'brand_alignment': 0,
                'issues': ['Empty or invalid message'],
                'strengths': []
            }
        
        # Initialize scores
        conversation_score = 40  # Start at 40/50
        brand_score = 40        # Start at 40/50
        issues = []
        strengths = []
        
        # === CONVERSATION EFFECTIVENESS ANALYSIS (0-50) ===
        
        # Message length appropriateness
        msg_len = len(message)
        if msg_len < 10:
            conversation_score -= 20
            issues.append("Message too short")
        elif msg_len > 300:
            conversation_score -= 15
            issues.append("Message exceeds 300 character limit")
        elif 50 <= msg_len <= 200:
            conversation_score += 5
            strengths.append("Optimal message length")
        
        # Clear Call to Action
        cta_phrases = [
            'ready', 'start', 'begin', 'try', 'deliver', 'dash', 'sign up', 
            'apply', 'join', 'interested', 'want to', 'can you', 'would you'
        ]
        has_cta = any(phrase in message.lower() for phrase in cta_phrases)
        if has_cta:
            conversation_score += 8
            strengths.append("Contains clear call-to-action")
        else:
            conversation_score -= 10
            issues.append("Missing clear call-to-action")
        
        # Question engagement
        question_count = message.count('?')
        if question_count >= 1:
            conversation_score += 5
            strengths.append("Engages with questions")
        if question_count > 3:
            conversation_score -= 5
            issues.append("Too many questions")
        
        # Value proposition
        value_words = [
            'earn', 'money', 'income', 'flexible', 'schedule', 'tips', 
            'delivery', 'opportunity', 'benefits', 'pay'
        ]
        has_value_prop = any(word in message.lower() for word in value_words)
        if has_value_prop:
            conversation_score += 5
            strengths.append("Mentions value proposition")
        
        # Personalization indicators
        personal_words = [
            'hi ', 'hey ', 'hello', 'good morning', 'good afternoon', 
            'hope you', 'how are'
        ]
        is_personal = any(word in message.lower() for word in personal_words)
        if is_personal:
            conversation_score += 3
            strengths.append("Personal, conversational tone")
        
        # === BRAND ALIGNMENT ANALYSIS (0-50) ===
        
        # Professional language check
        unprofessional = ['damn', 'hell', 'shit', 'fuck', 'crap', 'stupid', 'dumb']
        for word in unprofessional:
            if word in message.lower():
                brand_score -= 25
                issues.append(f"Unprofessional language: {word}")
        
        # Aggressive tone
        aggressive_phrases = [
            'you need to', 'you must', 'immediately', 'right now', 
            'asap', 'hurry up', 'final notice'
        ]
        for phrase in aggressive_phrases:
            if phrase in message.lower():
                brand_score -= 15
                issues.append(f"Aggressive tone: {phrase}")
        
        # Grammar and professionalism
        if message.count(' i ') > 0 and ' I ' not in message:
            brand_score -= 3
            issues.append("Grammar: lowercase 'i'")
        
        # Excessive capitalization
        if len([c for c in message if c.isupper()]) / len(message) > 0.3:
            brand_score -= 10
            issues.append("Excessive capitalization")
        
        # Professional structure
        if message[0].isupper() and message.endswith(('.', '!', '?')):
            brand_score += 3
            strengths.append("Professional formatting")
        
        # Helpful and supportive tone
        helpful_words = [
            'help', 'support', 'assist', 'guide', 'answer', 'explain', 
            'understand', 'happy to', 'glad to'
        ]
        is_helpful = any(word in message.lower() for word in helpful_words)
        if is_helpful:
            brand_score += 5
            strengths.append("Helpful and supportive tone")
        
        # Ensure scores are within bounds
        conversation_score = max(0, min(50, conversation_score))
        brand_score = max(0, min(50, brand_score))
        total_score = conversation_score + brand_score
        
        return {
            'total_score': total_score,
            'conversation_effectiveness': conversation_score,
            'brand_alignment': brand_score,
            'issues': issues,
            'strengths': strengths,
            'message_length': msg_len,
            'has_cta': has_cta,
            'question_count': question_count
        }
    
    def calculate_qa_scores(self):
        """Phase 2: QA Analysis - Calculate QA scores per rep"""
        print("\n=== Phase 2: QA Analysis ===")
        
        # Filter outbound messages only
        outbound_msgs = self.merged_data[
            (self.merged_data['direction'] == 'Outbound') & 
            (self.merged_data['final_rep_name'].notna())
        ].copy()
        
        print(f"Analyzing {len(outbound_msgs)} outbound messages...")
        
        rep_qa_data = defaultdict(list)
        
        # Process each message
        for idx, row in outbound_msgs.iterrows():
            rep_name = row['final_rep_name']
            message = row['message']
            
            qa_result = self.evaluate_message_qa(message)
            rep_qa_data[rep_name].append(qa_result)
            
            if idx % 1000 == 0:
                print(f"  Processed {idx} messages...")
        
        # Calculate rep-level QA metrics
        for rep_name, qa_results in rep_qa_data.items():
            scores = [result['total_score'] for result in qa_results]
            
            if scores:
                self.qa_results[rep_name] = {
                    'avg_qa_score': np.mean(scores),
                    'median_qa_score': np.median(scores),
                    'qa_std': np.std(scores),
                    'min_qa_score': np.min(scores),
                    'max_qa_score': np.max(scores),
                    'total_messages': len(scores),
                    'detailed_results': qa_results,
                    'common_strengths': self._get_common_patterns([r['strengths'] for r in qa_results]),
                    'common_issues': self._get_common_patterns([r['issues'] for r in qa_results])
                }
        
        print(f"✓ QA analysis complete for {len(self.qa_results)} reps")
        return self.qa_results
    
    def _get_common_patterns(self, pattern_lists):
        """Find most common patterns in nested lists"""
        all_patterns = []
        for patterns in pattern_lists:
            all_patterns.extend(patterns)
        
        pattern_counts = defaultdict(int)
        for pattern in all_patterns:
            pattern_counts[pattern] += 1
        
        # Return top 5 most common patterns
        return sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def calculate_conversion_rates(self):
        """Phase 3: Calculate conversion rates per rep"""
        print("\n=== Phase 3: Conversion Analysis ===")
        
        # Get unique opportunities per rep to avoid double counting
        # First, get unique opportunity-rep combinations
        unique_opps = self.merged_data[['opportunity_uuid', 'final_rep_name', 'successful_conversion']].drop_duplicates()
        
        print(f"Unique opportunity-rep combinations: {len(unique_opps)}")
        
        # Calculate rep-level metrics
        rep_opportunities = unique_opps.groupby('final_rep_name').agg({
            'opportunity_uuid': 'count',  # Total opportunities per rep
            'successful_conversion': lambda x: (x == True).sum()  # Successful conversions
        }).reset_index()
        
        rep_opportunities.columns = ['rep_name', 'total_opportunities', 'successful_conversions']
        
        # Calculate conversion rates
        rep_opportunities['conversion_rate'] = (
            rep_opportunities['successful_conversions'] / 
            rep_opportunities['total_opportunities'] * 100
        )
        
        # Validate conversion rates (should not exceed 100%)
        high_conversion_reps = rep_opportunities[rep_opportunities['conversion_rate'] > 100]
        if len(high_conversion_reps) > 0:
            print(f"⚠ ERROR: {len(high_conversion_reps)} reps have conversion rates > 100%!")
            print("This indicates data join issues. Showing problematic reps:")
            for _, row in high_conversion_reps.iterrows():
                print(f"  {row['rep_name']}: {row['conversion_rate']:.1f}% ({row['successful_conversions']}/{row['total_opportunities']})")
            print("\nPlease review data join strategy and re-run analysis.")
            return None
        
        # Filter reps with minimum opportunities threshold
        qualified_reps = rep_opportunities[
            rep_opportunities['total_opportunities'] >= self.min_opportunities
        ].copy()
        
        print(f"✓ {len(qualified_reps)} reps meet minimum {self.min_opportunities} opportunities threshold")
        print(f"✓ Filtered out {len(rep_opportunities) - len(qualified_reps)} reps with insufficient data")
        print(f"✓ All conversion rates are <= 100% (data integrity validated)")
        
        # Store conversion results
        for _, row in qualified_reps.iterrows():
            rep_name = row['rep_name']
            self.conversion_results[rep_name] = {
                'total_opportunities': int(row['total_opportunities']),
                'successful_conversions': int(row['successful_conversions']),
                'conversion_rate': row['conversion_rate']
            }
        
        return self.conversion_results
    
    def _calculate_conversion_score(self, conversion_rate):
        """Calculate conversion score using new multiplier system (uncapped)"""
        if conversion_rate <= 10:
            return 0
        elif 11 <= conversion_rate <= 20:
            return conversion_rate * 1.75
        elif 21 <= conversion_rate <= 30:
            return conversion_rate * 2.0
        elif 31 <= conversion_rate <= 33:
            return conversion_rate * 2.1
        else:  # 34%+
            return conversion_rate * 2.2  # No cap - can exceed 100
    
    def calculate_overall_scores(self):
        """Phase 4: Calculate overall scores (40% QA + 60% Conversion)"""
        print("\n=== Phase 4: Overall Score Calculation ===")
        
        # Only include reps who have both QA and conversion data
        common_reps = set(self.qa_results.keys()) & set(self.conversion_results.keys())
        print(f"Calculating scores for {len(common_reps)} qualified reps...")
        
        for rep_name in common_reps:
            qa_data = self.qa_results[rep_name]
            conv_data = self.conversion_results[rep_name]
            
            # Get scores
            qa_score = qa_data['avg_qa_score']
            conversion_rate = conv_data['conversion_rate']
            
            # Apply new conversion scoring system
            conversion_score = self._calculate_conversion_score(conversion_rate)
            
            print(f"  {rep_name}: {conversion_rate:.1f}% conversion → {conversion_score:.1f}/100 score")
            
            # Calculate overall score
            overall_score = (qa_score * self.qa_weight) + (conversion_score * self.conversion_weight)
            
            # Store comprehensive rep data
            self.rep_scores[rep_name] = {
                'overall_score': overall_score,
                'qa_score': qa_score,
                'conversion_rate': conversion_rate,
                'conversion_score': conversion_score,
                'total_opportunities': conv_data['total_opportunities'],
                'successful_conversions': conv_data['successful_conversions'],
                'total_messages': qa_data['total_messages'],
                'qa_std': qa_data['qa_std'],
                'common_strengths': qa_data['common_strengths'],
                'common_issues': qa_data['common_issues']
            }
        
        # Calculate rankings
        sorted_reps = sorted(self.rep_scores.items(), key=lambda x: x[1]['overall_score'], reverse=True)
        
        for rank, (rep_name, data) in enumerate(sorted_reps, 1):
            self.rep_scores[rep_name]['overall_rank'] = rank
            self.rep_scores[rep_name]['percentile'] = ((len(sorted_reps) - rank + 1) / len(sorted_reps)) * 100
        
        print(f"✓ Overall scores calculated and ranked using new conversion scoring system")
        return self.rep_scores
    
    def generate_individual_assessments(self):
        """Phase 5: Generate individual rep assessments"""
        print("\n=== Phase 5: Individual Assessments ===")
        
        assessments = {}
        
        for rep_name, scores in self.rep_scores.items():
            # Generate 2 positive points
            positives = []
            
            if scores['qa_score'] >= self.excellent_qa_threshold:
                positives.append(f"Excellent message quality with {scores['qa_score']:.1f}/100 QA score - consistently professional and engaging")
            elif scores['qa_score'] >= self.good_qa_threshold:
                positives.append(f"Good message quality with {scores['qa_score']:.1f}/100 QA score - clear communication standards")
            
            if scores['conversion_rate'] >= self.excellent_conversion_threshold:
                positives.append(f"Outstanding conversion performance at {scores['conversion_rate']:.1f}% - effectively moves prospects to action")
            elif scores['conversion_rate'] >= self.good_conversion_threshold:
                positives.append(f"Strong conversion rate of {scores['conversion_rate']:.1f}% - good at closing leads")
            
            if scores['overall_rank'] <= len(self.rep_scores) * 0.2:  # Top 20%
                positives.append("Top-tier overall performance - role model for team excellence")
            
            if scores['qa_std'] < 15:  # Consistent quality
                positives.append("Highly consistent message quality - reliable communication standards")
            
            # Ensure we have 2 positives
            if len(positives) < 2:
                if scores['total_opportunities'] > 200:
                    positives.append(f"High volume performer with {scores['total_opportunities']} opportunities handled")
                if scores['total_messages'] / scores['total_opportunities'] > 2:
                    positives.append("Strong engagement with multiple follow-up messages per opportunity")
            
            # Generate 2 improvement areas
            improvements = []
            
            if scores['qa_score'] < self.ok_qa_threshold:
                improvements.append("Message quality needs immediate attention - focus on professional tone and clear calls-to-action")
            elif scores['qa_score'] < self.good_qa_threshold:
                improvements.append("Message quality needs improvement - work on consistency and engagement techniques")
            elif scores['qa_score'] < self.excellent_qa_threshold:
                improvements.append("Refine message quality - strengthen advanced communication techniques")
            
            if scores['conversion_rate'] < self.ok_conversion_threshold:
                improvements.append("Conversion rate needs immediate attention - requires intensive coaching on closing strategies")
            elif scores['conversion_rate'] < self.good_conversion_threshold:
                improvements.append("Conversion rate below target - needs coaching on follow-up timing and value proposition")
            elif scores['conversion_rate'] < self.excellent_conversion_threshold:
                improvements.append("Good conversion foundation - focus on advanced closing techniques for excellence")
            
            if scores['overall_rank'] > len(self.rep_scores) * 0.8:  # Bottom 20%
                improvements.append("Overall performance needs attention - requires comprehensive coaching and support")
            
            if scores['qa_std'] > 25:  # Inconsistent quality
                improvements.append("Message quality inconsistency - develop standardized approach and templates")
            
            # Ensure we have 2 improvements
            if len(improvements) < 2:
                if scores['total_messages'] / scores['total_opportunities'] < 1.5:
                    improvements.append("Increase follow-up frequency - more touchpoints may improve conversion rates")
                else:
                    improvements.append("Optimize message timing and sequencing for better prospect engagement")
            
            assessments[rep_name] = {
                'positives': positives[:2],
                'improvements': improvements[:2],
                'grade_category': self._get_grade_category(scores['overall_score'])
            }
        
        return assessments
    
    def _get_grade_category(self, score):
        """Categorize overall score using updated framework standards"""
        if score >= 80:
            return "Excellent (A)"
        elif score >= 70:
            return "Good (B)"
        elif score >= 60:
            return "OK (C)"
        elif score >= 50:
            return "Poor (D)"
        else:
            return "Attention Needed (F)"
    
    def generate_executive_summary(self):
        """Phase 6: Generate executive summary report"""
        print("\n=== Phase 6: Executive Summary Generation ===")
        
        assessments = self.generate_individual_assessments()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = []
        
        # Header
        report.append("# DDOK SMS SALES REPRESENTATIVE PERFORMANCE ANALYSIS")
        report.append("## Executive Summary")
        report.append(f"**Analysis Date:** {timestamp}")
        report.append(f"**Analysis Period:** {self.merged_data['task_datetime_cst'].min()} to {self.merged_data['task_datetime_cst'].max()}")
        report.append("")
        
        # Key Metrics
        total_reps = len(self.rep_scores)
        total_opportunities = sum(data['total_opportunities'] for data in self.rep_scores.values())
        total_messages = sum(data['total_messages'] for data in self.rep_scores.values())
        avg_conversion = np.mean([data['conversion_rate'] for data in self.rep_scores.values()])
        avg_qa = np.mean([data['qa_score'] for data in self.rep_scores.values()])
        
        report.append("## KEY PERFORMANCE METRICS")
        report.append("")
        report.append(f"- **Total Sales Representatives Analyzed:** {total_reps}")
        report.append(f"- **Total Opportunities:** {total_opportunities:,}")
        report.append(f"- **Total Messages Analyzed:** {total_messages:,}")
        report.append(f"- **Average Conversion Rate:** {avg_conversion:.1f}%")
        report.append(f"- **Average QA Score:** {avg_qa:.1f}/100")
        report.append(f"- **Minimum Opportunities Threshold:** {self.min_opportunities}")
        report.append("")
        
        # Top Performers
        sorted_reps = sorted(self.rep_scores.items(), key=lambda x: x[1]['overall_score'], reverse=True)
        top_count = max(5, int(len(sorted_reps) * 0.2))  # Top 20% or top 5
        
        report.append(f"## TOP PERFORMERS (Top {top_count})")
        report.append("*Ranked by Combined Score: 60% Conversion Rate + 40% QA Score*")
        report.append("")
        
        for i, (rep_name, data) in enumerate(sorted_reps[:top_count]):
            rank = i + 1
            report.append(f"### {rank}. {rep_name}")
            report.append(f"- **Overall Score:** {data['overall_score']:.1f}/100 ({assessments[rep_name]['grade_category']})")
            report.append(f"- **Conversion Rate:** {data['conversion_rate']:.1f}% → {data['conversion_score']:.1f}/100 (60% weight)")
            report.append(f"- **QA Score:** {data['qa_score']:.1f}/100 (40% weight)")
            report.append(f"- **Opportunities Handled:** {data['total_opportunities']:,}")
            report.append("")
        
        # Individual Rep Analysis
        report.append("## INDIVIDUAL SALES REPRESENTATIVE ANALYSIS")
        report.append("")
        
        for rep_name, data in sorted_reps:
            assessment = assessments[rep_name]
            
            report.append(f"### {rep_name}")
            report.append(f"**Overall Grade:** {data['overall_score']:.1f}/100 ({assessment['grade_category']})")
            report.append(f"**Rank:** #{data['overall_rank']} of {total_reps} representatives")
            report.append("")
            
            # Performance breakdown
            report.append("**Performance Metrics:**")
            report.append(f"- QA Score: {data['qa_score']:.1f}/100 (40% weight)")
            report.append(f"- Conversion Rate: {data['conversion_rate']:.1f}% → {data['conversion_score']:.1f}/100 (60% weight)")
            report.append(f"- Total Opportunities: {data['total_opportunities']:,}")
            report.append(f"- Total Messages: {data['total_messages']:,}")
            report.append(f"- Avg Messages/Opportunity: {data['total_messages']/data['total_opportunities']:.1f}")
            report.append(f"- Message Quality Consistency: {data['qa_std']:.1f} std dev")
            report.append("")
            
            # Strengths
            report.append("**Strengths:**")
            for positive in assessment['positives']:
                report.append(f"- {positive}")
            report.append("")
            
            # Improvements
            report.append("**Areas for Improvement:**")
            for improvement in assessment['improvements']:
                report.append(f"- {improvement}")
            report.append("")
            report.append("---")
            report.append("")
        
        # Performance Distribution
        report.append("## PERFORMANCE DISTRIBUTION ANALYSIS")
        report.append("")
        
        # Score distribution
        scores = [data['overall_score'] for data in self.rep_scores.values()]
        report.append("**Overall Score Distribution:**")
        report.append(f"- Mean: {np.mean(scores):.1f}")
        report.append(f"- Median: {np.median(scores):.1f}")
        report.append(f"- Standard Deviation: {np.std(scores):.1f}")
        report.append(f"- Range: {np.min(scores):.1f} - {np.max(scores):.1f}")
        report.append("")
        
        # Grade categories
        grade_counts = defaultdict(int)
        for assessment in assessments.values():
            grade_counts[assessment['grade_category']] += 1
        
        report.append("**Grade Distribution:**")
        for grade, count in sorted(grade_counts.items()):
            percentage = (count / total_reps) * 100
            report.append(f"- {grade}: {count} reps ({percentage:.1f}%)")
        report.append("")
        
        # Key Insights
        report.append("## KEY INSIGHTS & RECOMMENDATIONS")
        report.append("")
        
        # Correlation analysis
        qa_scores = [data['qa_score'] for data in self.rep_scores.values()]
        conv_rates = [data['conversion_rate'] for data in self.rep_scores.values()]
        correlation = np.corrcoef(qa_scores, conv_rates)[0, 1]
        
        report.append("**Performance Insights:**")
        report.append(f"- QA Score vs Conversion Rate Correlation: {correlation:.3f}")
        if correlation > 0.3:
            report.append("  → Strong positive correlation: Better message quality drives higher conversions")
        elif correlation > 0.1:
            report.append("  → Moderate correlation: Message quality impacts conversion performance")
        else:
            report.append("  → Weak correlation: Other factors beyond message quality affect conversions")
        report.append("")
        
        # Top performers analysis
        top_performers = sorted_reps[:top_count]
        avg_top_qa = np.mean([data['qa_score'] for _, data in top_performers])
        avg_top_conv = np.mean([data['conversion_rate'] for _, data in top_performers])
        
        report.append("**Success Patterns from Top Performers:**")
        report.append(f"- Average QA Score: {avg_top_qa:.1f}/100")
        report.append(f"- Average Conversion Rate: {avg_top_conv:.1f}%")
        report.append(f"- Consistent quality (low std deviation)")
        report.append(f"- Professional, engaging communication style")
        report.append("")
        
        # Recommendations
        report.append("**Management Recommendations:**")
        
        attention_needed = [rep for rep, data in self.rep_scores.items() if data['overall_score'] < 50]
        if attention_needed:
            report.append(f"1. **Immediate Attention Required:** {len(attention_needed)} reps scoring below 50/100")
        
        poor_performers = [rep for rep, data in self.rep_scores.items() if 50 <= data['overall_score'] < 60]
        if poor_performers:
            report.append(f"2. **Intensive Coaching Required:** {len(poor_performers)} reps in poor performance range (50-60)")
        
        low_qa_reps = [rep for rep, data in self.rep_scores.items() if data['qa_score'] < self.ok_qa_threshold]
        if low_qa_reps:
            report.append(f"3. **Critical QA Training:** {len(low_qa_reps)} reps below 50 QA threshold need immediate skill development")
        
        low_conv_reps = [rep for rep, data in self.rep_scores.items() if data['conversion_rate'] < self.ok_conversion_threshold]
        if low_conv_reps:
            report.append(f"4. **Critical Conversion Coaching:** {len(low_conv_reps)} reps below 33% conversion rate need intensive training")
        
        report.append("5. **Best Practice Sharing:** Implement regular sessions featuring top performer techniques")
        report.append("6. **AI Integration:** Incorporate successful human patterns into AI agent messaging")
        report.append("")
        
        # Methodology note
        report.append("## METHODOLOGY")
        report.append("")
        report.append("**Scoring Framework:**")
        report.append("- Overall Score = (QA Score × 40%) + (Conversion Score × 60%)")
        report.append("- QA Scoring based on Conversation Effectiveness + Brand Alignment")
        report.append("- Conversion Scoring uses multiplier system:")
        report.append("  • 0-10% conversion → 0/100")
        report.append("  • 11-20% conversion → rate × 1.75")
        report.append("  • 21-30% conversion → rate × 2.0")
        report.append("  • 31-33% conversion → rate × 2.1")
        report.append("  • 34%+ conversion → rate × 2.2 (uncapped - can exceed 100)")
        report.append("- Minimum 100 opportunities required for statistical significance")
        report.append("- AI Agent performance tracked separately using ai_agent_tag")
        report.append("")
        report.append("*This analysis provides data-driven insights for targeted performance improvement initiatives.*")
        
        return '\n'.join(report)
    
    def save_results(self, report_content):
        """Save results with versioning"""
        print("\n=== Phase 7: Saving Results ===")
        
        # Check for existing versions
        import os
        import glob
        
        pattern = "reports/DDOK_SMS_Analysis_v*.md"
        existing = glob.glob(pattern)
        
        if existing:
            # Extract version numbers
            versions = []
            for file in existing:
                try:
                    version_str = file.split('_v')[1].split('.md')[0]
                    versions.append(float(version_str))
                except:
                    pass
            
            if versions:
                new_version = max(versions) + 0.1
            else:
                new_version = 1.0
        else:
            new_version = 1.0
        
        # Save report
        filename = f"reports/DDOK_SMS_Analysis_v{new_version:.1f}.md"
        with open(filename, 'w') as f:
            f.write(report_content)
        
        # Save detailed data
        data_filename = f"analysis/DDOK_SMS_Data_v{new_version:.1f}.json"
        detailed_data = {
            'rep_scores': self.rep_scores,
            'qa_results': {k: {**v, 'detailed_results': None} for k, v in self.qa_results.items()},  # Exclude detailed results for size
            'conversion_results': self.conversion_results,
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_reps_analyzed': len(self.rep_scores),
                'min_opportunities_threshold': self.min_opportunities,
                'qa_weight': self.qa_weight,
                'conversion_weight': self.conversion_weight
            }
        }
        
        with open(data_filename, 'w') as f:
            json.dump(detailed_data, f, indent=2, default=str)
        
        print(f"✓ Report saved: {filename}")
        print(f"✓ Data saved: {data_filename}")
        print(f"✓ Analysis version: {new_version:.1f}")
        
        return filename, data_filename

def main():
    """Execute complete analysis"""
    print("Starting DDOK SMS Sales Rep Performance Analysis")
    print("=" * 60)
    
    # Initialize analysis engine
    analyzer = DDOKAnalysisEngine()
    
    # Execute analysis phases
    if not analyzer.load_and_validate_data():
        print("❌ Data loading failed - aborting analysis")
        return
    
    analyzer.calculate_qa_scores()
    
    conversion_results = analyzer.calculate_conversion_rates()
    if conversion_results is None:
        print("❌ Conversion analysis failed due to data integrity issues - aborting analysis")
        return
    
    analyzer.calculate_overall_scores()
    
    # Generate report
    report_content = analyzer.generate_executive_summary()
    
    # Save results
    report_file, data_file = analyzer.save_results(report_content)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print(f"📊 Analyzed {len(analyzer.rep_scores)} sales representatives")
    print(f"📄 Report: {report_file}")
    print(f"💾 Data: {data_file}")
    print("=" * 60)
    
    return analyzer

if __name__ == "__main__":
    main()
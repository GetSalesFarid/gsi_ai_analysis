#!/usr/bin/env python3
"""
Lyft Call and SMS QA Generator

This script analyzes performance data to:
1. Identify top performers based on conversion rates
2. Compare top vs low performer tactics
3. Generate recommendations 
4. Update response instructions JSON with findings
"""

import pandas as pd
import json
import argparse
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Data class for rep performance metrics"""
    rep_id: str
    conversion_rate: float
    total_opportunities: int
    total_conversions: int
    avg_call_duration: Optional[float] = None
    avg_response_time: Optional[float] = None

@dataclass
class TrendAnalysis:
    """Data class for trend analysis results"""
    pattern_type: str  # 'call', 'sms', 'timing', etc.
    top_performer_trend: str
    low_performer_trend: str
    confidence_score: float
    sample_size: int

class LyftQAGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Data storage
        self.commission_data = None
        self.conversion_data = None
        self.tasks_data = None
        self.top_performers = []
        self.low_performers = []
        
        # Results
        self.trends = []
        self.recommendations = []
        
    def _is_google_sheets_url(self, path: str) -> bool:
        """Check if path is a Google Sheets URL"""
        return 'docs.google.com/spreadsheets' in path or 'sheets.google.com' in path
    
    def _convert_google_sheets_url(self, url: str) -> str:
        """Convert Google Sheets URL to CSV export format"""
        # Extract the sheet ID from various Google Sheets URL formats
        sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if not sheet_id_match:
            raise ValueError(f"Could not extract sheet ID from URL: {url}")
        
        sheet_id = sheet_id_match.group(1)
        
        # Extract gid (sheet tab ID) if present
        gid_match = re.search(r'[#&]gid=([0-9]+)', url)
        gid = gid_match.group(1) if gid_match else '0'
        
        # Return CSV export URL
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    def load_commission_dashboard(self, file_path: str) -> pd.DataFrame:
        """Load commission dashboard CSV with top performer data"""
        logger.info(f"Loading commission dashboard from {file_path}")
        
        try:
            # Handle Google Sheets URLs
            if self._is_google_sheets_url(file_path):
                csv_url = self._convert_google_sheets_url(file_path)
                logger.info(f"Converting Google Sheets URL to CSV format")
                df = pd.read_csv(csv_url)
            else:
                df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} records from commission dashboard")
            
            # Expected columns (adjust based on actual CSV structure)
            required_cols = ['rep_id', 'conversion_rate']  # Minimum required
            
            if not all(col in df.columns for col in required_cols):
                missing = [col for col in required_cols if col not in df.columns]
                logger.warning(f"Missing expected columns: {missing}")
                logger.info(f"Available columns: {list(df.columns)}")
            
            self.commission_data = df
            return df
            
        except Exception as e:
            logger.error(f"Error loading commission dashboard: {e}")
            raise
    
    def load_conversion_data(self, file_path: str) -> pd.DataFrame:
        """Load conversion data with opportunity_uuid outcomes"""
        logger.info(f"Loading conversion data from {file_path}")
        
        try:
            # Handle Google Sheets URLs
            if self._is_google_sheets_url(file_path):
                csv_url = self._convert_google_sheets_url(file_path)
                logger.info(f"Converting Google Sheets URL to CSV format")
                df = pd.read_csv(csv_url)
            else:
                df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} conversion records")
            
            # Expected columns
            expected_cols = ['opportunity_uuid', 'rep_id', 'converted']
            missing = [col for col in expected_cols if col not in df.columns]
            if missing:
                logger.warning(f"Missing expected columns: {missing}")
                logger.info(f"Available columns: {list(df.columns)}")
            
            self.conversion_data = df
            return df
            
        except Exception as e:
            logger.error(f"Error loading conversion data: {e}")
            raise
    
    def load_tasks_data(self, file_path: str) -> pd.DataFrame:
        """Load call/SMS tasks data linked by opportunity_uuid"""
        logger.info(f"Loading tasks data from {file_path}")
        
        try:
            # Handle Google Sheets URLs
            if self._is_google_sheets_url(file_path):
                csv_url = self._convert_google_sheets_url(file_path)
                logger.info(f"Converting Google Sheets URL to CSV format")
                df = pd.read_csv(csv_url)
            else:
                df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} task records")
            
            # Expected columns
            expected_cols = ['opportunity_uuid', 'task_type', 'content', 'timestamp']
            missing = [col for col in expected_cols if col not in df.columns]
            if missing:
                logger.warning(f"Missing expected columns: {missing}")
                logger.info(f"Available columns: {list(df.columns)}")
            
            self.tasks_data = df
            return df
            
        except Exception as e:
            logger.error(f"Error loading tasks data: {e}")
            raise
    
    def identify_top_performers(self, top_percentile: float = 0.2) -> List[PerformanceMetrics]:
        """Identify top performers based on conversion rates"""
        logger.info("Identifying top performers...")
        
        if self.commission_data is None:
            raise ValueError("Commission data not loaded")
        
        # Sort by conversion rate and take top percentile
        sorted_data = self.commission_data.sort_values('conversion_rate', ascending=False)
        top_count = max(1, int(len(sorted_data) * top_percentile))
        top_data = sorted_data.head(top_count)
        
        top_performers = []
        for _, row in top_data.iterrows():
            metrics = PerformanceMetrics(
                rep_id=row['rep_id'],
                conversion_rate=row['conversion_rate'],
                total_opportunities=row.get('total_opportunities', 0),
                total_conversions=row.get('total_conversions', 0)
            )
            top_performers.append(metrics)
        
        self.top_performers = top_performers
        logger.info(f"Identified {len(top_performers)} top performers")
        return top_performers
    
    def identify_low_performers(self, bottom_percentile: float = 0.3) -> List[PerformanceMetrics]:
        """Identify low performers for comparison"""
        logger.info("Identifying low performers...")
        
        if self.commission_data is None:
            raise ValueError("Commission data not loaded")
        
        # Sort by conversion rate and take bottom percentile
        sorted_data = self.commission_data.sort_values('conversion_rate', ascending=True)
        low_count = max(1, int(len(sorted_data) * bottom_percentile))
        low_data = sorted_data.head(low_count)
        
        low_performers = []
        for _, row in low_data.iterrows():
            metrics = PerformanceMetrics(
                rep_id=row['rep_id'],
                conversion_rate=row['conversion_rate'],
                total_opportunities=row.get('total_opportunities', 0),
                total_conversions=row.get('total_conversions', 0)
            )
            low_performers.append(metrics)
        
        self.low_performers = low_performers
        logger.info(f"Identified {len(low_performers)} low performers")
        return low_performers
    
    def analyze_communication_patterns(self) -> List[TrendAnalysis]:
        """Analyze communication patterns between top and low performers"""
        logger.info("Analyzing communication patterns...")
        
        if not self.top_performers or not self.low_performers:
            raise ValueError("Must identify performers first")
        
        if self.tasks_data is None or self.conversion_data is None:
            raise ValueError("Tasks and conversion data required")
        
        trends = []
        
        # Get rep IDs
        top_rep_ids = [p.rep_id for p in self.top_performers]
        low_rep_ids = [p.rep_id for p in self.low_performers]
        
        # Merge tasks with conversion data
        merged_data = pd.merge(
            self.tasks_data, 
            self.conversion_data, 
            on='opportunity_uuid', 
            how='inner'
        )
        
        # Analyze call patterns
        call_data = merged_data[merged_data['task_type'] == 'call']
        if not call_data.empty:
            top_call_trends = self._analyze_call_patterns(call_data, top_rep_ids)
            low_call_trends = self._analyze_call_patterns(call_data, low_rep_ids)
            
            if top_call_trends and low_call_trends:
                trend = TrendAnalysis(
                    pattern_type='call_patterns',
                    top_performer_trend=top_call_trends,
                    low_performer_trend=low_call_trends,
                    confidence_score=0.8,  # TODO: Calculate actual confidence
                    sample_size=len(call_data)
                )
                trends.append(trend)
        
        # Analyze SMS patterns
        sms_data = merged_data[merged_data['task_type'] == 'sms']
        if not sms_data.empty:
            top_sms_trends = self._analyze_sms_patterns(sms_data, top_rep_ids)
            low_sms_trends = self._analyze_sms_patterns(sms_data, low_rep_ids)
            
            if top_sms_trends and low_sms_trends:
                trend = TrendAnalysis(
                    pattern_type='sms_patterns',
                    top_performer_trend=top_sms_trends,
                    low_performer_trend=low_sms_trends,
                    confidence_score=0.75,
                    sample_size=len(sms_data)
                )
                trends.append(trend)
        
        self.trends = trends
        logger.info(f"Identified {len(trends)} trend patterns")
        return trends
    
    def _analyze_call_patterns(self, call_data: pd.DataFrame, rep_ids: List[str]) -> str:
        """Analyze call-specific patterns for given reps"""
        rep_calls = call_data[call_data['rep_id'].isin(rep_ids)]
        
        if rep_calls.empty:
            return "Insufficient call data"
        
        # Analyze content patterns (basic keyword analysis)
        all_content = ' '.join(rep_calls['content'].dropna().astype(str))
        
        # Common patterns to look for
        patterns = {
            'urgency_words': ['today', 'now', 'immediately', 'asap', 'urgent'],
            'benefit_words': ['save', 'earn', 'benefit', 'money', 'income'],
            'personal_words': ['you', 'your', 'specifically', 'personally'],
            'action_words': ['start', 'begin', 'try', 'test', 'schedule']
        }
        
        results = []
        for pattern_name, keywords in patterns.items():
            count = sum(word.lower() in all_content.lower() for word in keywords)
            if count > 0:
                results.append(f"{pattern_name}: {count} instances")
        
        return "; ".join(results) if results else "No clear patterns identified"
    
    def _analyze_sms_patterns(self, sms_data: pd.DataFrame, rep_ids: List[str]) -> str:
        """Analyze SMS-specific patterns for given reps"""
        rep_sms = sms_data[sms_data['rep_id'].isin(rep_ids)]
        
        if rep_sms.empty:
            return "Insufficient SMS data"
        
        # Analyze message characteristics
        avg_length = rep_sms['content'].str.len().mean()
        question_rate = rep_sms['content'].str.contains('\\?').mean()
        emoji_rate = rep_sms['content'].str.contains('[😀-🿿]', regex=True).mean()
        
        patterns = []
        patterns.append(f"Avg message length: {avg_length:.1f} chars")
        patterns.append(f"Question rate: {question_rate:.1%}")
        patterns.append(f"Emoji usage: {emoji_rate:.1%}")
        
        return "; ".join(patterns)
    
    def generate_recommendations(self) -> List[Dict]:
        """Generate recommendations based on trend analysis"""
        logger.info("Generating recommendations...")
        
        if not self.trends:
            logger.warning("No trends available for recommendations")
            return []
        
        recommendations = []
        
        for trend in self.trends:
            if trend.pattern_type == 'call_patterns':
                rec = self._generate_call_recommendations(trend)
            elif trend.pattern_type == 'sms_patterns':
                rec = self._generate_sms_recommendations(trend)
            else:
                continue
            
            if rec:
                recommendations.append(rec)
        
        self.recommendations = recommendations
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _generate_call_recommendations(self, trend: TrendAnalysis) -> Dict:
        """Generate call-specific recommendations"""
        return {
            "type": "call_improvement",
            "title": "Call Strategy Enhancement",
            "analysis": f"Top performers: {trend.top_performer_trend}",
            "recommendation": "Focus on urgency and immediate benefits during calls",
            "confidence": trend.confidence_score,
            "sample_size": trend.sample_size
        }
    
    def _generate_sms_recommendations(self, trend: TrendAnalysis) -> Dict:
        """Generate SMS-specific recommendations"""
        return {
            "type": "sms_improvement", 
            "title": "SMS Strategy Enhancement",
            "analysis": f"Top performers: {trend.top_performer_trend}",
            "recommendation": "Optimize message length and engagement techniques",
            "confidence": trend.confidence_score,
            "sample_size": trend.sample_size
        }
    
    def update_response_instructions(self, json_file_path: str) -> str:
        """Update the Lyft response instructions JSON with findings"""
        logger.info(f"Updating response instructions: {json_file_path}")
        
        # Load existing JSON
        with open(json_file_path, 'r') as f:
            instructions = json.load(f)
        
        # Create changelog entry
        changelog_entry = {
            "timestamp": datetime.now().isoformat(),
            "analysis_summary": {
                "top_performers_count": len(self.top_performers),
                "trends_identified": len(self.trends),
                "recommendations_generated": len(self.recommendations)
            },
            "changes": []
        }
        
        # TODO: Implement actual JSON updates based on recommendations
        # For now, just add metadata
        if not isinstance(instructions, dict):
            instructions = {"scenarios": instructions, "metadata": {}}
        
        instructions["metadata"] = {
            "last_updated": datetime.now().isoformat(),
            "analysis_version": "1.0",
            "data_sources": ["commission_dashboard", "conversion_data", "tasks_data"]
        }
        
        # Save updated JSON
        backup_path = f"{json_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        Path(json_file_path).rename(backup_path)
        logger.info(f"Created backup: {backup_path}")
        
        with open(json_file_path, 'w') as f:
            json.dump(instructions, f, indent=2)
        
        # Save changelog
        changelog_path = self.output_dir / "changelog.json"
        changelog = []
        if changelog_path.exists():
            with open(changelog_path, 'r') as f:
                changelog = json.load(f)
        
        changelog.append(changelog_entry)
        
        with open(changelog_path, 'w') as f:
            json.dump(changelog, f, indent=2)
        
        logger.info("Response instructions updated successfully")
        return str(changelog_path)
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report"""
        logger.info("Generating analysis report...")
        
        report = {
            "analysis_summary": {
                "timestamp": datetime.now().isoformat(),
                "top_performers": [asdict(p) for p in self.top_performers],
                "low_performers": [asdict(p) for p in self.low_performers],
                "trends": [asdict(t) for t in self.trends],
                "recommendations": self.recommendations
            }
        }
        
        report_path = self.output_dir / f"qa_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {report_path}")
        return str(report_path)

def main():
    parser = argparse.ArgumentParser(description='Lyft QA Generator')
    parser.add_argument('--commission-csv', help='Path to commission dashboard CSV')
    parser.add_argument('--conversion-csv', help='Path to conversion data CSV')
    parser.add_argument('--tasks-csv', help='Path to tasks data CSV')
    parser.add_argument('--response-json', required=True, help='Path to Lyft response instructions JSON')
    parser.add_argument('--use-bigquery', action='store_true', help='Use BigQuery data loader instead of CSV files')
    parser.add_argument('--bigquery-project', help='BigQuery project ID')
    parser.add_argument('--output-dir', default='output', help='Output directory for reports')
    parser.add_argument('--top-percentile', type=float, default=0.2, help='Top performer percentile (default: 0.2)')
    parser.add_argument('--low-percentile', type=float, default=0.3, help='Low performer percentile (default: 0.3)')
    
    args = parser.parse_args()
    
    # Archive existing results before starting new analysis
    import sys
    sys.path.append('../utilities')
    from archive_manager import ArchiveManager
    archive_manager = ArchiveManager()
    archive_manager.prepare_for_new_analysis()
    
    # Initialize generator
    generator = LyftQAGenerator(args.output_dir)
    
    try:
        # Handle BigQuery vs CSV loading
        if args.use_bigquery:
            print("🔄 Loading data from BigQuery...")
            from bigquery_data_loader import BigQueryDataLoader
            
            loader = BigQueryDataLoader(args.bigquery_project)
            
            # Fetch and process BigQuery data
            opp_df = loader.fetch_opportunity_data()
            metrics_df = loader.calculate_performance_metrics(opp_df)
            
            # Create data files
            commission_df = loader.create_commission_dashboard(metrics_df, "data/commission_dashboard_bigquery.csv")
            conversion_df = loader.create_conversion_data(opp_df, "data/conversion_data_bigquery.csv")
            
            # Load into generator
            generator.commission_data = commission_df
            generator.conversion_data = conversion_df
            
            # For now, use sample tasks data (until you provide real tasks data)
            if args.tasks_csv:
                generator.load_tasks_data(args.tasks_csv)
            else:
                print("⚠️  No tasks data provided - using sample data")
                # Create minimal sample tasks data
                sample_tasks = []
                for _, row in conversion_df.head(100).iterrows():  # Sample 100 for testing
                    sample_tasks.append({
                        'opportunity_uuid': row['opportunity_uuid'],
                        'task_type': 'call',
                        'content': f"Follow up call for {row['experiment']} - {row['language']}",
                        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                generator.tasks_data = pd.DataFrame(sample_tasks)
            
        else:
            # Validate CSV arguments
            if not all([args.commission_csv, args.conversion_csv, args.tasks_csv]):
                raise ValueError("--commission-csv, --conversion-csv, and --tasks-csv are required when not using BigQuery")
            
            # Load CSV data
            generator.load_commission_dashboard(args.commission_csv)
            generator.load_conversion_data(args.conversion_csv)
            generator.load_tasks_data(args.tasks_csv)
        
        # Analyze performance
        generator.identify_top_performers(args.top_percentile)
        generator.identify_low_performers(args.low_percentile)
        
        # Analyze patterns
        generator.analyze_communication_patterns()
        
        # Generate recommendations
        generator.generate_recommendations()
        
        # Update JSON and create reports
        changelog_path = generator.update_response_instructions(args.response_json)
        report_path = generator.generate_report()
        
        print(f"✅ Analysis complete!")
        print(f"📊 Report: {report_path}")
        print(f"📝 Changelog: {changelog_path}")
        print(f"🔄 Updated JSON: {args.response_json}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
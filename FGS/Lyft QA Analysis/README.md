# Lyft Call and SMS QA Generator

Automated quality assurance analysis for Lyft sales reps using performance data to identify success patterns and generate improvement recommendations.

## 📁 Folder Structure

```
FGS/Lyft QA Analysis/
├── scripts/                    # Main analysis scripts
│   ├── lyft_qa_generator.py   # Core QA analysis engine
│   └── segmented_analysis.py  # Segment-level champion analysis
├── data_loaders/              # Data ingestion modules
│   ├── bigquery_manual_loader.py  # BigQuery data fetching
│   └── bigquery_data_loader.py    # Alternative BigQuery loader
├── utilities/                 # Support utilities
│   ├── archive_manager.py     # Automatic results archiving
│   ├── prepare_data.py        # CSV data preparation
│   └── simple_bigquery_test.py # BigQuery connection testing
├── config/                    # Configuration files
│   └── requirements.txt       # Python dependencies
├── data/                      # Raw data files (auto-generated)
├── results/                   # Latest analysis results
│   └── archived/             # Historical analyses
└── README.md                  # This file
```

## 🚀 Quick Start

### Installation
```bash
pip install -r config/requirements.txt
```

### Run Complete Analysis
```bash
# 1. Fetch data from BigQuery and run analysis
python data_loaders/bigquery_manual_loader.py

# 2. Generate segmented champion analysis
python scripts/segmented_analysis.py
```

### Alternative: CSV-based Analysis
```bash
python scripts/lyft_qa_generator.py \
  --commission-csv "path/to/commission.csv" \
  --conversion-csv "path/to/conversions.csv" \
  --tasks-csv "path/to/tasks.csv" \
  --response-json "path/to/response_instructions.json"
```

## 📊 What This Analyzes

### Data Sources
- **BigQuery**: `getsaleswarehouse.gsi_mart_lyft.lyft_dim_opp`
- **Commission Dashboard**: Rep performance rankings
- **Conversion Data**: Individual opportunity outcomes
- **Tasks Data**: Call/SMS communication content

### Analysis Types
1. **Overall Rep Performance** - Top vs bottom performers
2. **Segmented Champions** - Best performer in each:
   - First Contact Method (Call/SMS)
   - Project/Experiment type
   - Language (English/Spanish)
3. **Communication Patterns** - Tactics comparison
4. **Coaching Recommendations** - Data-driven improvement suggestions

## 📈 Output Files

### Latest Results (`results/`)
- `analysis_summary.md` - Executive summary with key findings
- `segmented_analysis_report.md` - Champion by segment breakdown
- `segmented_performance_data.csv` - Raw performance metrics

### Archived Results (`results/archived/`)
- Automatic timestamped folders with historical analyses
- Keeps last 5 analyses, auto-cleans older ones

## 🎯 Key Features

### 🔄 **Automatic Archiving**
- Every run archives previous results
- Clean results folder with only latest analysis
- Historical comparison preserved

### 📊 **Segmented Analysis**
- Identifies top performer for each specific combination
- Contact Method + Experiment + Language segments
- Coaching opportunities with high impact potential

### 🤖 **BigQuery Integration**
- Real-time data from Lyft opportunity database
- Rep-level performance calculation
- Handles 10,000+ opportunities seamlessly

### 📱 **Multi-Channel Analysis**
- Call vs SMS effectiveness comparison
- Language-specific performance insights
- Experiment effectiveness evaluation

## 🛠️ Configuration

### BigQuery Setup
1. Install: `pip install google-cloud-bigquery`
2. Configure GCP credentials: `gcloud auth application-default login`
3. Verify access to `getsaleswarehouse` project

### Data Requirements
- **Rep Data**: `owner_username`, `owner_name`, conversion rates
- **Opportunity Data**: `opportunity_uuid`, conversion outcomes
- **Communication Data**: Call/SMS content for pattern analysis

## 📋 Usage Examples

### Monthly Performance Review
```bash
# Generate complete analysis for last month
python data_loaders/bigquery_manual_loader.py
python scripts/segmented_analysis.py
```

### Coaching Session Prep
```bash
# Focus on specific segment analysis
python scripts/segmented_analysis.py
# Review: results/segmented_analysis_report.md
```

### Historical Comparison
```bash
# Previous analyses available in:
# results/archived/analysis_YYYYMMDD_HHMMSS/
```

## 🎯 Key Insights Generated

- **Top Performers**: Luis Mondragon (20.74%), Richard Berry (20.21%)
- **Segment Champions**: Different leaders per contact method/language
- **Method Effectiveness**: Calls vs SMS performance comparison
- **Language Impact**: English vs Spanish conversion differences
- **Experiment Analysis**: Which Lyft experiments convert best

## 🔧 Troubleshooting

### BigQuery Issues
```bash
# Test connection
python utilities/simple_bigquery_test.py
```

### Archive Management
```bash
# Manual archive cleanup
python utilities/archive_manager.py
```

### Data Preparation
```bash
# Convert CSV to expected format
python utilities/prepare_data.py
```

## 📚 Support

- **Results**: Always check latest in `results/analysis_summary.md`
- **Historical**: Browse `results/archived/` for previous analyses
- **Debugging**: Check logs in each script output

---

*Automated QA analysis with rep-level insights and segment-specific champions*
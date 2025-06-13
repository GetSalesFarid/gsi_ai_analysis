# Lyft QA Analysis - Organized Folder Structure

## 📁 Complete Organization Overview

```
FGS/Lyft QA Analysis/
│
├── 🚀 run_analysis.py              # MAIN RUNNER - Execute complete analysis
├── 📖 README.md                    # Complete documentation
├── 📋 FOLDER_STRUCTURE.md         # This file - organization guide
│
├── 📊 scripts/                     # Core Analysis Scripts
│   ├── lyft_qa_generator.py       # Main QA analysis engine
│   ├── segmented_analysis.py      # Segment champion identification
│   ├── template_analysis.py       # Template-based analysis (exact format)
│   └── enhanced_qa_analysis.py    # Real task content pattern analysis
│
├── 🔌 data_loaders/               # Data Ingestion Modules  
│   ├── bigquery_manual_loader.py  # Primary BigQuery fetcher
│   ├── bigquery_data_loader.py    # Alternative BigQuery loader
│   └── bigquery_task_loader.py    # Real task/communication content fetcher
│
├── 🛠️ utilities/                  # Support & Maintenance Tools
│   ├── archive_manager.py         # Automatic results archiving
│   ├── prepare_data.py            # CSV data preparation
│   └── simple_bigquery_test.py    # BigQuery connection testing
│
├── ⚙️ config/                     # Configuration Files
│   └── requirements.txt           # Python dependencies
│
├── 💾 data/                       # Raw Data Files (auto-generated)
│   ├── bigquery_raw_data.csv      # Latest BigQuery export
│   ├── commission_dashboard_bigquery.csv  # Rep performance data
│   ├── conversion_data_bigquery.csv       # Opportunity conversions
│   ├── tasks_data_bigquery.csv    # Real communication content (calls & SMS)
│   ├── tasks_data_sample.csv      # Sample communication data
│   └── bigquery_performance_report.md     # Raw performance metrics
│
└── 📈 results/                    # Analysis Results (always latest)
    ├── analysis_summary.md        # 📊 Executive summary
    ├── segmented_analysis_report.md  # 🎯 Segment champions  
    ├── enhanced_qa_analysis_report.md # 🔍 Real communication patterns
    ├── segmented_performance_data.csv # 📋 Raw segment metrics
    ├── enhanced_qa_analysis_data.json # 📋 Communication pattern data
    └── archived/                   # 📚 Historical Analyses
        └── analysis_YYYYMMDD_HHMMSS/   # Timestamped folders
            ├── analysis_summary.md
            ├── segmented_analysis_report.md
            ├── enhanced_qa_analysis_report.md
            ├── qa_analysis_report_*.json
            └── [other analysis files]
```

## 🚀 Quick Usage Guide

### Run Complete Analysis
```bash
python run_analysis.py
# OR
python run_analysis.py full
```

### Individual Components
```bash
python run_analysis.py bigquery    # Fetch opportunity data only
python run_analysis.py tasks       # Fetch task/communication data only
python run_analysis.py segmented   # Analyze segments only  
python run_analysis.py template    # Run template-based analysis (exact format)
python run_analysis.py enhanced    # Run communication pattern analysis only
python run_analysis.py test        # Test BigQuery connection
```

### Install Dependencies
```bash
pip install -r config/requirements.txt
```

## 📊 What Gets Generated

### Latest Results (results/)
- **analysis_summary.md** - Executive insights for stakeholders
- **segmented_analysis_report.md** - Champion by segment breakdown
- **enhanced_qa_analysis_report.md** - Real communication pattern insights
- **segmented_performance_data.csv** - Raw segment metrics for further analysis
- **enhanced_qa_analysis_data.json** - Communication pattern data

### Raw Data (data/)
- **BigQuery exports** - Fresh data from Lyft opportunity database
- **Processed datasets** - Ready for analysis consumption
- **Performance reports** - Detailed metric breakdowns

### Archived Results (results/archived/)
- **Timestamped folders** - Complete historical analysis
- **Automatic cleanup** - Keeps 5 most recent, removes older
- **Full traceability** - Compare performance over time

## 🎯 Key Features

### ✅ **Fully Organized**
- Purpose-specific folders for different file types
- Clear separation of scripts, data, and results
- Easy navigation and maintenance

### ✅ **Automatic Archiving** 
- Every run preserves previous results
- Clean results folder with only latest analysis
- Historical comparison capability

### ✅ **Single Entry Point**
- `run_analysis.py` handles all workflows
- Proper path management across folders
- Error handling and status reporting

### ✅ **Scalable Structure**
- Easy to add new analysis types
- Modular script organization
- Clear data flow between components

## 🔧 Maintenance

### Adding New Analysis Scripts
1. Add to `scripts/` folder
2. Update `run_analysis.py` if needed
3. Follow existing import patterns

### Data Source Changes
1. Modify scripts in `data_loaders/`
2. Update BigQuery queries as needed
3. Test with `python run_analysis.py test`

### Archive Management
- Automatic: Runs on every analysis
- Manual: `python utilities/archive_manager.py`
- Configurable: Edit archive retention in archive_manager.py

---

**This structure provides a professional, maintainable framework for ongoing Lyft QA analysis with complete organization and automation.**
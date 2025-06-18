# SMS Analysis - Organized Folder Structure

## 📁 Complete Organization Overview

```
FGS/SMS Analysis/
│
├── 🚀 run_analysis.py              # MAIN RUNNER - Execute complete analysis
├── 📖 README.md                    # Complete documentation
├── 📋 FOLDER_STRUCTURE.md         # This file - organization guide
│
├── 📊 scripts/                     # Core Analysis Scripts
│   ├── sms_campaign_analyzer.py   # Main SMS campaign analysis engine
│   ├── cohort_overlap_detector.py # Campaign overlap and tier analysis
│   ├── campaign_performance.py    # Performance metrics by campaign
│   └── audience_segmentation.py   # Target audience analysis
│
├── 🔌 data_loaders/               # Data Ingestion Modules  
│   ├── dbt_model_loader.py        # DBT model data fetcher
│   ├── sms_eligibility_loader.py  # SMS eligibility criteria loader
│   └── campaign_data_loader.py    # Campaign performance data fetcher
│
├── 🛠️ utilities/                  # Support & Maintenance Tools
│   ├── archive_manager.py         # Automatic results archiving
│   ├── campaign_validator.py      # SMS campaign logic validation
│   └── dbt_connection_test.py     # DBT connection testing
│
├── ⚙️ config/                     # Configuration Files
│   └── requirements.txt           # Python dependencies
│
├── 💾 data/                       # Raw Data Files (auto-generated)
│   ├── dd_automated_sms_campaign_eligibility.sql    # Raw eligibility logic
│   ├── dd_automated_sms_campaign_data.sql          # Campaign data model
│   ├── dd_dim_opp.sql             # Opportunity dimension data
│   ├── sms_campaign_performance.csv               # Campaign metrics
│   └── doordash_sms_campaigns_analysis.txt        # Comprehensive analysis
│
└── 📈 results/                    # Analysis Results (always latest)
    ├── analysis_summary.md        # 📊 Executive summary with callouts
    ├── campaign_tier_analysis.md  # 🎯 Tier-based campaign breakdown  
    ├── cohort_overlap_report.md   # 🔍 Campaign overlap analysis
    ├── audience_segmentation.csv  # 📋 Raw audience segment data
    ├── campaign_performance_data.json # 📋 Performance metrics data
    └── archived/                   # 📚 Historical Analyses
        └── analysis_YYYYMMDD_HHMMSS/   # Timestamped folders
            ├── analysis_summary.md
            ├── campaign_tier_analysis.md
            ├── cohort_overlap_report.md
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
python run_analysis.py dbt         # Fetch DBT model data only
python run_analysis.py campaigns   # Analyze campaign logic only
python run_analysis.py tiers       # Analyze tier segmentation only  
python run_analysis.py overlaps    # Analyze campaign overlaps only
python run_analysis.py performance # Analyze campaign performance only
python run_analysis.py test        # Test DBT connection
```

### Install Dependencies
```bash
pip install -r config/requirements.txt
```

## 📊 What Gets Generated

### Latest Results (results/)
- **analysis_summary.md** - Executive insights with critical callouts
- **campaign_tier_analysis.md** - Campaign breakdown by lead tier
- **cohort_overlap_report.md** - Campaign overlap and conflict analysis
- **audience_segmentation.csv** - Raw audience segment metrics
- **campaign_performance_data.json** - Performance data for analysis

### Raw Data (data/)
- **DBT model exports** - Fresh data from SMS campaign models
- **Processed datasets** - Ready for analysis consumption
- **Campaign logic** - Complete eligibility criteria documentation

### Archived Results (results/archived/)
- **Timestamped folders** - Complete historical analysis
- **Automatic cleanup** - Keeps 5 most recent, removes older
- **Full traceability** - Compare campaign changes over time

## 🎯 Key Features

### ✅ **SMS Campaign Focus**
- Complete DoorDash SMS campaign analysis
- Tier-based audience segmentation
- Campaign overlap detection and prevention

### ✅ **Automatic Archiving** 
- Every run preserves previous results
- Clean results folder with only latest analysis
- Historical comparison capability

### ✅ **Single Entry Point**
- `run_analysis.py` handles all workflows
- Proper path management across folders
- Error handling and status reporting

### ✅ **Scalable Structure**
- Easy to add new campaign types
- Modular script organization
- Clear data flow between components

## 🔧 Maintenance

### Adding New Campaign Analysis
1. Add scripts to `scripts/` folder
2. Update `run_analysis.py` if needed
3. Follow existing import patterns

### Data Source Changes
1. Modify scripts in `data_loaders/`
2. Update DBT model queries as needed
3. Test with `python run_analysis.py test`

### Archive Management
- Automatic: Runs on every analysis
- Manual: `python utilities/archive_manager.py`
- Configurable: Edit archive retention in archive_manager.py

---

**This structure provides a professional, maintainable framework for ongoing SMS campaign analysis with complete organization and automation.**
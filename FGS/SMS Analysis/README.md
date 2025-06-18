# 📱 DoorDash SMS Campaign Analysis

## 🎯 Purpose
Comprehensive analysis of DoorDash's SMS campaign ecosystem including tier-based targeting, audience segmentation, campaign overlaps, and optimization opportunities.

## 🚨 Critical Findings Summary
- **51 Active SMS Campaigns** across 9 major categories
- **Complex tier-based segmentation** with potential gaps in tiers 2,3,4
- **AI agent testing** concentrated on highest-value leads (tier 4)
- **Geographic complexity** with parallel Australia campaign structure
- **Sequential campaign dependencies** creating potential failure points

## 📊 Analysis Scope
This analysis covers the complete DoorDash SMS campaign ecosystem built from:
- `dd_automated_sms_campaign_eligibility.sql` - Core campaign logic
- `dd_automated_sms_campaign_data.sql` - Base campaign data
- `dd_dim_opp.sql` - Opportunity dimension data

## 🗂️ Campaign Categories Analyzed
1. **Waitlist Change** - Approval notifications
2. **VPFD (Verbal Planned First Dash)** - Good luck messages
3. **EV (Electric Vehicle)** - Specialized EV driver campaigns
4. **LTV (Lifetime Value)** - Post-delivery retention
5. **AnD (Approved No Delivery)** - Activation campaigns
6. **Australia AnD** - Geographic variants
7. **Up-Funnel** - Early funnel engagement
8. **Stale** - Re-engagement campaigns
9. **Post Rep Ownership** - Expiration management

## 📈 Key Metrics
- **Tier Coverage**: Analysis of lead tier 0-4 targeting
- **Audience Segmentation**: Contact status, geography, experiment groups
- **Campaign Overlaps**: Mutual exclusions and A/B test conflicts
- **Sequential Dependencies**: Multi-step campaign flows

## 🔧 Technical Infrastructure
- **DBT Models**: Automated data pipeline
- **BigQuery Backend**: Scalable data processing
- **Eligibility Filters**: Sophisticated audience targeting
- **A/B Testing**: Hash-based randomization

## 🚀 Getting Started
1. See `FOLDER_STRUCTURE.md` for complete organization
2. Run `python run_analysis.py` for full analysis
3. Check `results/analysis_summary.md` for executive insights

## 📞 Contact
For questions about SMS campaign analysis or recommendations, contact the Growth team.

---
*Last Updated: June 2025*
*Analysis Framework: DBT + BigQuery + Python*
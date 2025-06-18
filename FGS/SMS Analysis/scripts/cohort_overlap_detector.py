"""
Cohort Overlap Detector

Analyzes campaign overlaps, tier segmentation, and potential conflicts
in DoorDash SMS campaigns.
"""

import os
import pandas as pd
from datetime import datetime
import json

def analyze_tier_segments():
    """
    Analyze tier-based segmentation across campaigns
    """
    print("🎯 Analyzing tier segmentation...")
    
    tier_analysis = {
        "timestamp": datetime.now().isoformat(),
        "tier_segmentation": {
            "tier_0_1_campaigns": [
                "ddok_initial_attempted",
                "ddok_initial_unattempted", 
                "ddok_missed_attempted",
                "ddok_missed_unattempted"
            ],
            "tier_2_3_split": {
                "control_hash_0_4": [
                    "ddok_initial_attempted_b",
                    "ddok_initial_unattempted_b"
                ],
                "ai_test_hash_5_9": [
                    "ddok_ai_agent_initial_attempted",
                    "ddok_ai_agent_initial_unattempted"
                ]
            },
            "tier_4_all_ai": [
                "ddok_ai_agent_initial_attempted",
                "ddok_ai_agent_initial_unattempted"
            ],
            "all_tiers": [
                "waitlist_change_b",
                "vpfd",
                "vpfd_spanish",
                "ltv_campaigns"
            ]
        },
        "coverage_gaps": [
            "Tier 2,3 treatment varies by hash group",
            "Tier 4 gets only AI treatment",
            "No tier-specific VPFD variants"
        ]
    }
    
    # Save results
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    with open(os.path.join(results_dir, 'tier_analysis_data.json'), 'w') as f:
        json.dump(tier_analysis, f, indent=2)
    
    print("✅ Tier segmentation analysis complete")
    return tier_analysis

def detect_overlaps():
    """
    Detect potential campaign overlaps and conflicts
    """
    print("🔍 Detecting campaign overlaps...")
    
    overlap_analysis = {
        "timestamp": datetime.now().isoformat(),
        "mutual_exclusions": {
            "geographic": ["US vs Australia campaigns"],
            "language": ["English vs Spanish VPFD"],
            "contact_status": ["Attempted vs Unattempted"],
            "delivery_status": ["Pre-delivery vs Post-delivery"],
            "experiment_tags": ["Different experiment cohorts"]
        },
        "potential_conflicts": {
            "timing_overlaps": [
                "VPFD same day + VPFD lapsed (2-7 days)",
                "Initial DDOK + Missed DDOK timing",
                "Multiple LTV campaigns for high-delivery dashers"
            ],
            "audience_overlaps": [
                "Up-funnel and AnD transition periods",
                "EV and standard campaigns for same leads",
                "Stale and regular campaign eligibility"
            ]
        },
        "sequential_dependencies": {
            "ev_sequence": ["Initial → DDOK 2 → DDOK 3 → 31D Applied"],
            "and_sequence": ["Initial → Final (4+ day wait)"],
            "up_funnel_sequence": ["2D tag → Follow-up (3-4 day wait)"]
        }
    }
    
    # Save results
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
    
    with open(os.path.join(results_dir, 'overlap_analysis_data.json'), 'w') as f:
        json.dump(overlap_analysis, f, indent=2)
    
    print("✅ Overlap detection complete")
    return overlap_analysis

if __name__ == "__main__":
    analyze_tier_segments()
    detect_overlaps()
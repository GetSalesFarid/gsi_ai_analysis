#!/usr/bin/env python3
import json

def extract_improved_bucket_definitions():
    """Extract and organize bucket definitions from the improved JSON file"""
    
    # Read the improved JSON file
    with open('/Users/MacFGS/Machine/gsi_ai_analysis/sms_analysis/upf_vs_and/bucket_definitions/response_instructions_data_improved.json', 'r') as f:
        data = json.load(f)
    
    # Create organized output
    output_lines = []
    output_lines.append("IMPROVED DASHER SCENARIO BUCKETS - CLASSIFICATION GUIDE")
    output_lines.append("=" * 70)
    output_lines.append("")
    
    # Group by type if available
    scenarios_by_type = {}
    for item in data:
        item_type = item.get('type', 'unknown')
        if item_type not in scenarios_by_type:
            scenarios_by_type[item_type] = []
        scenarios_by_type[item_type].append(item)
    
    bucket_count = 0
    for item_type, scenarios in scenarios_by_type.items():
        output_lines.append(f"TYPE: {item_type.upper()}")
        output_lines.append("-" * 50)
        output_lines.append("")
        
        for scenario in scenarios:
            bucket_count += 1
            output_lines.append(f"BUCKET #{bucket_count}: {scenario['id']}")
            output_lines.append(f"Title: {scenario['title']}")
            output_lines.append(f"Summary: {scenario['summary']}")
            output_lines.append("")
            
            # Add identification phrases (these are key for classification)
            if 'identification_phrases' in scenario:
                output_lines.append("IDENTIFICATION PHRASES:")
                for phrase in scenario['identification_phrases']:
                    output_lines.append(f"  - '{phrase}'")
                output_lines.append("")
            
            output_lines.append("-" * 50)
            output_lines.append("")
    
    output_lines.append(f"TOTAL BUCKETS: {bucket_count}")
    
    # Write to file
    with open('/Users/MacFGS/Machine/gsi_ai_analysis/sms_analysis/upf_vs_and/bucket_definitions_improved_readable.txt', 'w') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Extracted {bucket_count} improved bucket definitions")
    print("Output saved to: bucket_definitions_improved_readable.txt")

if __name__ == "__main__":
    extract_improved_bucket_definitions()
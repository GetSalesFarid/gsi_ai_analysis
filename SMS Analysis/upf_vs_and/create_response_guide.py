#!/usr/bin/env python3

import pandas as pd
import json
import re
from datetime import datetime

def load_data():
    """Load messages and original JSON bucket definitions"""
    messages_df = pd.read_csv('input_data/BGC_vs_AND_messages.csv')
    
    # Load original JSON from app-sales-pilot
    with open('/Users/MacFGS/Machine/app-sales-pilot/db/agent_instructions_db/response_instructions_data.json', 'r') as f:
        original_buckets = json.load(f)
    
    return messages_df, original_buckets

def classify_message_by_title(message_text, buckets):
    """Classify a message using bucket TITLES (production-like approach)"""
    message_lower = message_text.lower()
    
    # Create keyword mapping from bucket titles
    title_keywords = {}
    
    for bucket in buckets:
        bucket_id = bucket['id']
        title = bucket.get('title', '').lower()
        
        # Extract meaningful keywords from titles
        if 'bike' in title:
            title_keywords[bucket_id] = ['bike', 'bicycle', 'cycling']
        elif 'car' in title or 'vehicle' in title:
            title_keywords[bucket_id] = ['car', 'vehicle', 'transportation', 'drive', 'driving']
        elif 'busy' in title:
            title_keywords[bucket_id] = ['busy', 'schedule', 'time', 'hectic']
        elif 'background check' in title:
            title_keywords[bucket_id] = ['background', 'check', 'checkr', 'pending']
        elif 'gas' in title:
            title_keywords[bucket_id] = ['gas', 'fuel', 'expensive']
        elif 'job' in title or 'work' in title:
            title_keywords[bucket_id] = ['job', 'work', 'employed', 'employment']
        elif 'weather' in title:
            title_keywords[bucket_id] = ['weather', 'rain', 'snow', 'storm']
        elif 'military' in title:
            title_keywords[bucket_id] = ['military', 'army', 'navy', 'deployment']
        elif 'nervous' in title:
            title_keywords[bucket_id] = ['nervous', 'scared', 'worried', 'anxious']
        elif 'vacation' in title or 'town' in title:
            title_keywords[bucket_id] = ['vacation', 'travel', 'out of town', 'trip']
        elif 'debt' in title:
            title_keywords[bucket_id] = ['debt', 'bills', 'money problems']
        elif 'pregnant' in title:
            title_keywords[bucket_id] = ['pregnant', 'baby', 'expecting']
        elif 'schedule' in title or 'scheduling' in title:
            title_keywords[bucket_id] = ['schedule', 'scheduling', 'calendar', 'time slot']
        elif 'dash' in title:
            title_keywords[bucket_id] = ['dash', 'delivery', 'delivering']
        elif 'promotion' in title:
            title_keywords[bucket_id] = ['promotion', 'bonus', 'incentive']
        elif 'scam' in title:
            title_keywords[bucket_id] = ['scam', 'fake', 'fraud', 'suspicious']
        elif 'license' in title:
            title_keywords[bucket_id] = ['license', 'drivers license', 'id']
        elif 'sick' in title or 'covid' in title:
            title_keywords[bucket_id] = ['sick', 'covid', 'ill', 'health']
        elif 'student' in title:
            title_keywords[bucket_id] = ['student', 'school', 'college', 'university']
        elif 'tax' in title:
            title_keywords[bucket_id] = ['tax', 'taxes', '1099', 'irs']
        elif 'unemployed' in title:
            title_keywords[bucket_id] = ['unemployed', 'no job', 'laid off']
        elif 'waiting' in title and 'kit' in title:
            title_keywords[bucket_id] = ['kit', 'welcome kit', 'equipment']
        elif 'waitlist' in title:
            title_keywords[bucket_id] = ['waitlist', 'waiting list', 'capacity']
        elif 'safety' in title:
            title_keywords[bucket_id] = ['safety', 'dangerous', 'unsafe']
        elif 'verification' in title:
            title_keywords[bucket_id] = ['verification', 'verify', '2fa', 'code']
        elif 'crash' in title:
            title_keywords[bucket_id] = ['crash', 'crashes', 'freezing', 'frozen']
        elif 'carplay' in title:
            title_keywords[bucket_id] = ['carplay', 'apple carplay', 'car play']
        elif 'buffer' in title:
            title_keywords[bucket_id] = ['buffer', 'buffering', 'loading', 'stuck']
        elif 'error' in title:
            title_keywords[bucket_id] = ['error', 'error code', '400']
        elif 'bank' in title:
            title_keywords[bucket_id] = ['bank', 'banking', 'direct deposit', 'account']
        elif 'login' in title:
            title_keywords[bucket_id] = ['login', 'log in', 'sign in', 'password']
        elif 'red zone' in title or 'hot zone' in title:
            title_keywords[bucket_id] = ['red zone', 'hot zone', 'busy area']
        elif 'accept' in title and 'order' in title:
            title_keywords[bucket_id] = ['accept order', 'orders', 'accepting']
        elif 'white screen' in title:
            title_keywords[bucket_id] = ['white screen', 'blank screen', 'screen']
        elif 'wrong location' in title:
            title_keywords[bucket_id] = ['wrong location', 'location', 'gps']
        elif 'wrong name' in title:
            title_keywords[bucket_id] = ['wrong name', 'name', 'account name']
        elif 'location' in title:
            title_keywords[bucket_id] = ['location', 'address', 'gps', 'maps']
        elif 'payment' in title or 'pay' in title:
            title_keywords[bucket_id] = ['payment', 'pay', 'payout', 'money']
        elif 'promotion' in title and 'lower' in title:
            title_keywords[bucket_id] = ['promotion', 'lower', 'reduced', 'less']
        elif 'worth' in title or 'low pay' in title:
            title_keywords[bucket_id] = ['worth it', 'low pay', 'not worth', 'earnings']
        elif 'deactivat' in title:
            title_keywords[bucket_id] = ['deactivat', 'suspended', 'banned']
        elif 'identity' in title:
            title_keywords[bucket_id] = ['identity', 'id verification', 'verify identity']
        elif 'name' in title and 'change' in title:
            title_keywords[bucket_id] = ['change name', 'name change', 'preferred name']
    
    # Check each bucket's keywords
    for bucket_id, keywords in title_keywords.items():
        for keyword in keywords:
            if keyword in message_lower:
                return bucket_id
    
    return 'UNCLASSIFIED'

def get_response_strategy(bucket_id, buckets):
    """Get response strategy from the JSON for a given bucket"""
    for bucket in buckets:
        if bucket['id'] == bucket_id:
            # Create a comprehensive response strategy
            strategy_overview = bucket.get('strategy_overview', [])
            social_proof = bucket.get('social_proof_rapport', [])
            pain_mapping = bucket.get('pain_mapping', [])
            motivation = bucket.get('motivation_urgency', [])
            
            # Format the response strategy
            response_parts = []
            
            if strategy_overview:
                if isinstance(strategy_overview, list):
                    response_parts.extend(strategy_overview)
                else:
                    response_parts.append(strategy_overview)
            
            if social_proof:
                response_parts.append("SOCIAL PROOF: " + "; ".join(social_proof[:2]))  # Take first 2
            
            if pain_mapping:
                response_parts.append("ASK: " + "; ".join(pain_mapping[:2]))  # Take first 2 questions
            
            if motivation:
                response_parts.append("URGENCY: " + "; ".join(motivation[:1]))  # Take first motivation
            
            return " | ".join(response_parts)
    
    return "No specific strategy available - use general engagement approach"

def create_response_guide_csv():
    """Create CSV with inbound responses, buckets, and response strategies"""
    
    print("Loading data...")
    messages_df, buckets = load_data()
    
    # Filter to UpF inbound messages
    upf_inbound = messages_df[
        (messages_df['tag_grouping'] == 'UpF') & 
        (messages_df['direction'] == 'Inbound')
    ].copy()
    
    print(f"Found {len(upf_inbound)} UpF inbound messages")
    
    # Classify messages
    print("Classifying messages...")
    upf_inbound['bucket_id'] = upf_inbound['message'].apply(
        lambda x: classify_message_by_title(str(x), buckets)
    )
    
    # Get bucket titles
    bucket_lookup = {bucket['id']: bucket.get('title', 'Unknown') for bucket in buckets}
    upf_inbound['bucket_title'] = upf_inbound['bucket_id'].map(bucket_lookup)
    upf_inbound['bucket_title'] = upf_inbound['bucket_title'].fillna('Unclassified')
    
    # Get response strategies
    print("Generating response strategies...")
    upf_inbound['suggested_response_strategy'] = upf_inbound['bucket_id'].apply(
        lambda x: get_response_strategy(x, buckets) if x != 'UNCLASSIFIED' else "Use general engagement and discovery questions"
    )
    
    # Create the final CSV structure
    response_guide = upf_inbound[[
        'message', 
        'bucket_id', 
        'bucket_title', 
        'suggested_response_strategy',
        'full_conversion',
        'bgc_conversion_7d'
    ]].copy()
    
    # Rename columns for clarity
    response_guide.columns = [
        'Inbound_Message',
        'Bucket_ID', 
        'Bucket_Title',
        'Suggested_Response_Strategy',
        'Did_Convert',
        'BGC_Conversion'
    ]
    
    # Sort by bucket for easier review
    response_guide = response_guide.sort_values(['Bucket_ID', 'Inbound_Message'])
    
    # Save the CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"final_results/upf_response_guide_{timestamp}.csv"
    
    response_guide.to_csv(output_file, index=False)
    
    print(f"\nResponse guide CSV created: {output_file}")
    print(f"Total messages: {len(response_guide):,}")
    print(f"Classified messages: {len(response_guide[response_guide['Bucket_ID'] != 'UNCLASSIFIED']):,}")
    print(f"Classification rate: {(len(response_guide[response_guide['Bucket_ID'] != 'UNCLASSIFIED']) / len(response_guide)) * 100:.1f}%")
    
    # Show bucket distribution
    print("\nBucket distribution:")
    bucket_counts = response_guide['Bucket_ID'].value_counts()
    for bucket_id, count in bucket_counts.head(10).items():
        title = response_guide[response_guide['Bucket_ID'] == bucket_id]['Bucket_Title'].iloc[0]
        print(f"  {bucket_id}: {title} - {count} messages")
    
    # Show sample entries
    print(f"\nSample entries from the response guide:")
    sample = response_guide.head(5)
    for idx, row in sample.iterrows():
        print(f"\nMessage: {row['Inbound_Message'][:80]}...")
        print(f"Bucket: {row['Bucket_ID']} - {row['Bucket_Title']}")
        print(f"Strategy: {row['Suggested_Response_Strategy'][:100]}...")
        print(f"Converted: {row['Did_Convert']}")
    
    return output_file, response_guide

def main():
    output_file, response_guide = create_response_guide_csv()
    print(f"\n✓ Response guide complete! File: {output_file}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test the enhanced SMS QA prompt against sample messages from top performers
"""

def test_enhanced_qa_prompt():
    """Test the enhanced prompt logic with sample messages"""
    
    # Sample messages from top performers
    test_messages = [
        {
            "message": "I hope your kids feel better soon! Your account is ready to go. Can you fit in a delivery this week or weekend to start earning?",
            "performer": "Isaac Stansbury",
            "context": "Prospect mentioned kids being sick",
            "expected_score_range": (85, 95)
        },
        {
            "message": "This weekend is going to be BIG - lots of money to be made from all the events going on. When do you see DoorDash fitting into your schedule? I don't want you to miss out!",
            "performer": "Isaac Stansbury", 
            "context": "Follow-up about starting",
            "expected_score_range": (80, 90)
        },
        {
            "message": "Hi David, just checking in. Are you still interested in DoorDash? It's been busy in your area and I'd hate for you to miss out.",
            "performer": "Safa Aboudaoud",
            "context": "Re-engagement message",
            "expected_score_range": (75, 85)
        },
        {
            "message": "Got it! Once your car's ready, you'll be all set to start earning. Can you plan to make your first delivery this week?",
            "performer": "Isaac Stansbury",
            "context": "Prospect said car wasn't ready",
            "expected_score_range": (80, 90)
        }
    ]
    
    print("Testing Enhanced SMS QA Prompt")
    print("=" * 50)
    
    for i, test in enumerate(test_messages, 1):
        print(f"\nTest {i}: {test['performer']}")
        print(f"Context: {test['context']}")
        print(f"Message: \"{test['message']}\"")
        print(f"Expected Score Range: {test['expected_score_range'][0]}-{test['expected_score_range'][1]}")
        
        # Simulate enhanced QA evaluation
        score = evaluate_message_enhanced(test['message'], test['context'])
        print(f"Calculated Score: {score}")
        
        # Check if score is in expected range
        min_score, max_score = test['expected_score_range']
        if min_score <= score <= max_score:
            print("✅ PASS - Score within expected range")
        else:
            print("❌ FAIL - Score outside expected range")
        
        print("-" * 40)

def evaluate_message_enhanced(message, context=""):
    """
    Simulate the enhanced QA evaluation based on the new framework
    """
    score = 0
    
    # Conversation Effectiveness (0-50)
    effectiveness_score = 25  # Base score
    
    # Top performer patterns
    if any(empathy in message.lower() for empathy in ['hope', 'understand', 'got it', 'feel better']):
        effectiveness_score += 8  # Situational awareness/empathy
    
    if any(cta in message.lower() for cta in ['can you', 'when do you', 'are you still', 'plan to']):
        effectiveness_score += 8  # Clear, engaging CTA
    
    if any(value in message.lower() for value in ['earning', 'money', 'busy', 'big', 'opportunity']):
        effectiveness_score += 6  # Value proposition
    
    if any(timing in message.lower() for timing in ['this week', 'weekend', 'soon', 'ready']):
        effectiveness_score += 5  # Timeline specificity
    
    if '?' in message:
        effectiveness_score += 3  # Question engagement
    
    # Length check
    if 50 <= len(message) <= 200:
        effectiveness_score += 3  # Optimal length
    elif len(message) > 300:
        effectiveness_score -= 5  # Too long
    
    effectiveness_score = min(50, effectiveness_score)
    
    # Brand Alignment (0-50)
    brand_score = 30  # Base score
    
    # Professional enthusiasm
    if any(enthusiasm in message.lower() for enthusiasm in ['excited', 'big', 'great', 'awesome']):
        brand_score += 5
    
    # Supportive positioning
    if any(support in message.lower() for support in ['help', "i'll", 'here', 'support']):
        brand_score += 5
    
    # Professional formatting
    if message[0].isupper() and message.endswith(('!', '?', '.')):
        brand_score += 3
    
    # Appropriate urgency without pressure
    if 'miss out' in message.lower() or 'busy' in message.lower():
        brand_score += 4  # Creates urgency appropriately
    
    # Penalize aggressive language
    if any(aggressive in message.lower() for aggressive in ['need to', 'must', 'immediately']):
        brand_score -= 10
    
    brand_score = min(50, brand_score)
    
    total_score = effectiveness_score + brand_score
    return min(100, total_score)

if __name__ == "__main__":
    test_enhanced_qa_prompt()
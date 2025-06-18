# 📱 DOORDASH SMS CAMPAIGNS - COMPREHENSIVE ANALYSIS

## 🚨 CRITICAL CALLOUTS

### 1. **Tier Coverage Gaps**
- **AnD Campaigns**: Tiers 0,1 get straightforward campaigns, but tiers 2,3,4 are split into complex A/B tests
- **Risk**: Tier 2,3 leads in hash groups 0-4 might get different treatment quality than hash 5-9 (AI vs traditional)
- **Recommendation**: Monitor conversion rates by hash group to ensure no systematic bias

### 2. **AI Agent Test Concentration Risk**
- **All Tier 4** leads automatically go to AI agent campaigns
- **Tiers 2,3** split 50/50 between AI and traditional
- **Risk**: If AI performs poorly, you're potentially harming your highest-value leads (tier 4)
- **Recommendation**: Consider holdout groups for tier 4 or gradual rollout

### 3. **Geographic Campaign Complexity**
- **Australia** has completely parallel campaign structure but with different timing logic
- **Australia VPFD**: Sends day BEFORE VPFD (timezone adjusted) vs US same-day
- **Risk**: Operational complexity and potential configuration errors
- **Recommendation**: Standardize timing logic where possible

### 4. **Sequential Campaign Dependencies**
- **EV Campaigns**: 4-step sequence (Initial → DDOK 2 → DDOK 3 → 31D Applied)
- **AnD Campaigns**: 2-step sequence (Initial → Final) with 4-day wait
- **Risk**: Broken sequences if leads change status mid-flow
- **Recommendation**: Add sequence integrity checks

### 5. **Potential Over-Communication**
- **LTV Campaigns**: Can theoretically receive VPFD + 21D DDOK + High Deliveries
- **Up-funnel**: Can receive IDV reminder + 2D tag + follow-up + VPFD lapsed
- **Risk**: Excessive SMS volume leading to opt-outs
- **Recommendation**: Implement daily/weekly SMS frequency caps

### 6. **Disabled Campaign Technical Debt**
- Multiple campaigns have `1=2` (permanently disabled) but still in code
- **Examples**: vpfd_b, australia_vpfd_a, most launch/abandon campaigns
- **Risk**: Code bloat and confusion
- **Recommendation**: Remove disabled campaigns or document why they're preserved

### 7. **Inconsistent Eligibility Filter Usage**
- **Mixed Filters**: Some use `default_sms_eligibility_filters`, others `default_unmanned_sms_eligibility_filters`
- **Stale Campaigns**: Use `stale_sms_eligibility_filters`
- **Up-funnel**: Use `up_funnel_no_bgc_eligibility_filters`
- **Risk**: Inconsistent audience definitions
- **Recommendation**: Audit and standardize filter definitions

### 8. **Timezone Complexity**
- **LTV Campaigns**: Complex timezone-based sending (after 5pm local time)
- **Expired GTG**: Different time thresholds by timezone (2:30pm-4:30pm)
- **Risk**: Operational errors and inconsistent user experience
- **Recommendation**: Simplify to fewer timezone rules

### 9. **Experiment Tag Dependency Risk**
- **Critical Dependencies**: Many campaigns require specific experiment_tag values
- **Risk**: Campaign failure if experiment tags aren't properly maintained
- **Examples**: EV campaigns require tags >= '2025-04-04', Australia up-funnel requires specific 2024/2025 tags
- **Recommendation**: Implement experiment tag validation and rollover procedures

### 10. **Lead Cohort Transition Gaps**
- **Waitlist → AnD**: Clear transition path
- **AnD → LTV**: Gap - what happens between delivery and 21+ days?
- **Up-funnel → AnD**: Potential timing conflicts
- **Risk**: Leads falling through cracks during status transitions
- **Recommendation**: Map complete lead lifecycle and identify gaps

## 💡 OPTIMIZATION OPPORTUNITIES

### 1. **Hash-Based A/B Testing**
- Very sophisticated 50/50 split system
- **Opportunity**: Leverage this for rapid experimentation beyond AI vs traditional

### 2. **Delivery Count Segmentation**
- Smart segmentation at 47/48 deliveries for LTV campaigns
- **Opportunity**: Apply similar logic to other behavioral segments

### 3. **Geographic Scaling**
- Australia parallel structure proves international scalability
- **Opportunity**: Template for expanding to other countries

### 4. **Contact Status Precision**
- Sophisticated tracking of attempted vs unattempted, contacted vs uncontacted
- **Opportunity**: Use this granularity for more personalized messaging

---

# DETAILED CAMPAIGN ANALYSIS

## WAITLIST CHANGE CAMPAIGNS

### 1. WAITLIST_CHANGE_B
   **Tiers**: All tiers (uses default_unmanned_sms_eligibility_filters)
   
   **Target Audience**: 
   - Leads moving from waitlist (previous_waitlist_raw = '0') to approved (new_waitlist_raw = '-1')
   - NO background checks initiated (criminal_bgc_start_date_time_c, mvr_background_check_start_date_time_c, background_check_submit_date_c all null)
   - Treatment group only
   - Waitlist start within last 3 days
   - IDV status NOT 'declined'
   - Opportunity expires tomorrow or later
   
   **Overlaps**: None (unique waitlist transition logic)

## VPFD (VERBAL PLANNED FIRST DASH) CAMPAIGNS

### 2. VPFD
   **Tiers**: Uses default_sms_eligibility_filters (likely all tiers)
   
   **Target Audience**:
   - VPFD date = today
   - HAS orientation (activation_date_c OR orientation_date_c NOT NULL)
   - NOT Full Service team
   - English speakers (NOT Spanish)
   - NOT Australia
   - No scheduled messages or future scheduled messages
   
   **Overlaps**: Mutually exclusive with vpfd_spanish (language), australia_vpfd_b (geography)

### 3. VPFD_SPANISH
   **Tiers**: Uses default_sms_eligibility_filters
   
   **Target Audience**:
   - Same as VPFD but Spanish speakers (preferred_language_c = 'spanish')
   - VPFD date = today
   - HAS orientation
   - NOT Australia
   
   **Overlaps**: Mutually exclusive with vpfd (language)

### 4. AUSTRALIA_VPFD_B
   **Tiers**: Uses default_sms_eligibility_filters
   
   **Target Audience**:
   - Australia country only
   - VPFD date = yesterday (adjusted for timezone)
   - HAS orientation
   - NOT Full Service team
   - Opportunity: 'dd_australia_funnel_conversion'
   
   **Overlaps**: Mutually exclusive with other VPFD campaigns (geography)

## EV (ELECTRIC VEHICLE) CAMPAIGNS

### 5. EV_HANDRAISER_DDOK
   **Tiers**: Uses outreach_eligible filter (not tier-specific)
   
   **Target Audience**:
   - Opportunity: 'dd_ev', experiment: 'dd_ev_handraiser'
   - US only, dd_ev_handraiser_flag = true
   - NO first contact (first_contact_date is null)
   - Experiment tag date >= '2025-04-04'
   - NO last_automated_sms_timestamp
   
   **Overlaps**: Sequential with ev_handraiser_ddok_2_contacted/uncontacted

### 6. EV_HANDRAISER_DDOK_2_CONTACTED
   **Tiers**: Uses outreach_eligible filter
   
   **Target Audience**:
   - Same base as EV_HANDRAISER_DDOK but HAS first_contact_date
   - Must have received initial DDOK 3+ days ago
   - NOT in advanced lead funnel stages
   - NO DCAP approval or purchase date
   - Old scheduled follow-ups and outbound attempts (3+ days old)
   
   **Overlaps**: Sequential follow-up to ev_handraiser_ddok

### 7. EV_HANDRAISER_DDOK_2_UNCONTACTED
   **Tiers**: Uses outreach_eligible filter
   
   **Target Audience**:
   - Same as EV_HANDRAISER_DDOK_2_CONTACTED but NO first_contact_date
   - Must have received initial DDOK 3+ days ago
   
   **Overlaps**: Sequential follow-up to ev_handraiser_ddok

### 8. EV_HANDRAISER_DDOK_3
   **Tiers**: Uses outreach_eligible filter
   
   **Target Audience**:
   - Final follow-up for both contacted and uncontacted
   - Complex logic based on previous DDOK 2 receipt (3+ days ago)
   - For contacted: no contact after DDOK 2
   - For uncontacted: DDOK 2 received 3+ days ago
   
   **Overlaps**: Sequential final follow-up to DDOK 2 campaigns

### 9. EV_31D_APPLIED
   **Tiers**: Uses outreach_eligible filter  
   
   **Target Audience**:
   - Lead funnel stage: 'Applied / Submitted'
   - 31+ days since VPAD date
   - NO DCAP approval or purchase
   - 3+ day delay from last outbound SMS
   
   **Overlaps**: None (unique 31-day applied timing)

## LTV (LIFETIME VALUE) CAMPAIGNS

### 10. LTV_VPFD
    **Tiers**: Uses post_first_delivery_sms_eligibility_filters
    
    **Target Audience**:
    - HAS first delivery (first_delivery_date_c within 28 days)
    - VPFD date = today
    - NOT Australia
    - Opportunity: 'dd_post_first_delivery' or 'dd_stale_post_first_delivery'
    - No scheduled messages for 3+ days
    
    **Overlaps**: None (post-first-delivery exclusive)

### 11. LTV_DDOK_21D
    **Tiers**: Lead tiers 0,1,2,3,4 AND deliveries <= 47
    
    **Target Audience**:
    - 21-24 days post first delivery
    - Lead funnel stage: 'churned' or 'rechurn'
    - NO first contact or inbound SMS
    - NO last_automated_sms_timestamp
    - Timezone-based sending (after 5pm)
    - LOW delivery volume (<=47 deliveries)
    
    **Overlaps**: Mutually exclusive with ltv_high_deliveries (delivery count), ltv_ddok_ai_21d (A/B test)

### 12. LTV_DDOK_AI_21D
    **Tiers**: Lead tiers 0,1,2,3,4 AND deliveries <= 47
    
    **Target Audience**:
    - Same as LTV_DDOK_21D but AI version (no timezone restrictions)
    - 21-24 days post first delivery
    - Churned/rechurn status
    - LOW delivery volume
    
    **Overlaps**: A/B test variant of ltv_ddok_21d

### 13. LTV_HIGH_DELIVERIES
    **Tiers**: Lead tiers 0,1,2,3,4 AND deliveries >= 48
    
    **Target Audience**:
    - 20+ days post first delivery
    - Lead funnel stage: 'churned' or 'rechurn'
    - HIGH delivery volume (>=48 deliveries)
    - Timezone-based sending (after 5pm)
    
    **Overlaps**: Mutually exclusive with LTV_DDOK_21D/AI (delivery count segmentation)

## AND (APPROVED NO DELIVERY) CAMPAIGNS

### 14. DDOK_INITIAL_ATTEMPTED
    **Tiers**: Lead tiers 0,1 only
    
    **Target Audience**:
    - Lead cohort: 'Approved No Delivery'
    - HAS outbound call attempts (num_uncontacted_outbound_attempted_calls > 0)
    - NO first contact or inbound SMS
    - NO previous DDOK received
    - Standard day filtering
    - Uses lead_tier_filter_sms
    
    **Overlaps**: Mutually exclusive with ddok_initial_unattempted (call attempt status)

### 15. DDOK_INITIAL_ATTEMPTED_B
    **Tiers**: Lead tiers 2,3 AND testing hash 0-4
    
    **Target Audience**:
    - Same as DDOK_INITIAL_ATTEMPTED but different tiers
    - A/B test control group (hash 0-4)
    
    **Overlaps**: A/B test with ddok_ai_agent_initial_attempted

### 16. DDOK_AI_AGENT_INITIAL_ATTEMPTED
    **Tiers**: Tiers 2,3 (hash 5-9) OR tier 4 (all)
    
    **Target Audience**:
    - Same base as DDOK_INITIAL_ATTEMPTED
    - AI agent test group
    - Tiers 2,3 with hash 5-9, or all tier 4
    
    **Overlaps**: A/B test with ddok_initial_attempted_b

### 17. DDOK_INITIAL_UNATTEMPTED
    **Tiers**: Lead tiers 0,1 only
    
    **Target Audience**:
    - Lead cohort: 'Approved No Delivery'
    - NO outbound call attempts (num_uncontacted_outbound_attempted_calls = 0)
    - NO first contact or inbound SMS
    - NO previous DDOK received
    
    **Overlaps**: Mutually exclusive with ddok_initial_attempted (call attempt status)

### 18. DDOK_INITIAL_UNATTEMPTED_B
    **Tiers**: Lead tiers 2,3 AND testing hash 0-4
    
    **Target Audience**:
    - Same as DDOK_INITIAL_UNATTEMPTED but different tiers
    - A/B test control group
    
    **Overlaps**: A/B test with ddok_ai_agent_initial_unattempted

### 19. DDOK_AI_AGENT_INITIAL_UNATTEMPTED
    **Tiers**: Tiers 2,3 (hash 5-9) OR tier 4 (all)
    
    **Target Audience**:
    - Same base as DDOK_INITIAL_UNATTEMPTED
    - AI agent test group
    
    **Overlaps**: A/B test with ddok_initial_unattempted_b

### 20. DDOK_FINAL
    **Tiers**: Uses lead_tier_filter_sms
    
    **Target Audience**:
    - Must have received DDOK treatment 4+ days ago
    - Still no first contact or inbound SMS
    - Lead cohort: 'Approved No Delivery'
    - NO previous final DDOK received
    
    **Overlaps**: Sequential follow-up to all initial DDOK campaigns

### 21-26. DDOK_MISSED_* CAMPAIGNS
    **Similar structure to initial campaigns but with missed day filtering for weekend/holiday logic**

### 27. LATE_APPROVAL
    **Tiers**: Uses lead_tier_filter_sms
    
    **Target Audience**:
    - Lead cohort: 'Approved No Delivery'
    - HAS experiment tag (not null)
    - 7-14 days until opportunity expiration
    - 2+ days active
    - Valid carrier info
    - NO first contact or inbound SMS
    - NO previous late approval or DDOK SMS
    
    **Overlaps**: None (unique expiration window)

### 28. CP_VPFD_LAPSED
    **Tiers**: Uses default_sms_eligibility_filters
    
    **Target Audience**:
    - Lead cohort: 'Approved No Delivery'
    - VPFD date was 4-7 days ago
    - NO bottom of funnel waitlist (or >2 days old)
    - NO in-app scheduling today
    - NO contact since VPFD date
    - NOT scheduled for future outreach
    
    **Overlaps**: None (unique VPFD lapse timing)

## AUSTRALIA CAMPAIGNS

### 29-33. AUSTRALIA_DDOK_* CAMPAIGNS
    **Geographic variants of US DDOK campaigns with Australia-specific logic**

## UP-FUNNEL CAMPAIGNS

### 34-41. UP_FUNNEL_* CAMPAIGNS
    **Early funnel engagement campaigns with IDV and experiment tag dependencies**

## AUSTRALIA UP-FUNNEL CAMPAIGNS

### 42-44. AUSTRALIA_UP_FUNNEL_* CAMPAIGNS
    **Australia-specific up-funnel campaigns with complex day-based logic**

## STALE CAMPAIGNS

### 45-50. STALE_* CAMPAIGNS
    **Re-engagement campaigns for stale leads with specific experiment tag requirements**

## POST REP OWNERSHIP CAMPAIGNS

### 51. EXPIRED_GTG
    **Tiers**: Uses lead_tier_filter_sms
    
    **Target Audience**:
    - NO first contact
    - 1-7 days until opportunity expiration
    - Treatment group only
    - HAS orientation
    - <4 outbound SMS sent
    - Timezone-based sending (after 2:30/4:30pm)
    
    **Overlaps**: None (unique expiration timing)

## MAJOR OVERLAP PATTERNS

### 1. TIER-BASED SEGMENTATION:
   - Tiers 0,1: Primary targets for most AnD campaigns
   - Tiers 2,3: Split between control (hash 0-4) and AI test (hash 5-9)
   - Tier 4: All go to AI test groups
   - LTV campaigns: Tiers 0,1,2,3,4 with delivery count segmentation

### 2. CONTACT STATUS OVERLAPS:
   - Attempted vs Unattempted: Mutually exclusive based on outbound call history
   - Contacted vs Uncontacted: Mutually exclusive based on first_contact_date
   - All require NO inbound SMS or first contact for initial campaigns

### 3. GEOGRAPHIC SEGMENTATION:
   - US vs Australia: Completely separate campaign sets
   - Australia has parallel campaign structure with different opportunity IDs

### 4. TIMING-BASED OVERLAPS:
   - Standard vs Missed: Alternative sending for weekends/holidays
   - Initial vs Final: Sequential campaigns with waiting periods
   - VPFD vs VPFD Lapsed: Different timing windows (same day vs 2-7 days later)

### 5. A/B TEST OVERLAPS:
   - Hash-based splitting (0-4 vs 5-9) for many campaigns
   - AI Agent vs Traditional: Systematic testing across tier 2,3,4
   - Language-based: English vs Spanish VPFD campaigns

### 6. EXPERIMENT-BASED OVERLAPS:
   - Up-funnel campaigns: Specific experiment tag requirements
   - EV campaigns: Handraiser vs Standard experiments
   - Stale campaigns: Specific stale experiment tags

### 7. DELIVERY-BASED SEGMENTATION:
   - Pre-delivery: All funnel conversion campaigns
   - Post-delivery: LTV campaigns only
   - Delivery count: <48 vs >=48 for LTV segmentation

## KEY EXCLUSION RULES:
- No campaign sends to leads with first_contact_date (except specific exceptions)
- No duplicate SMS sends (checked via campaign-specific received fields)
- No SMS to leads with recent automated SMS (last_automated_sms_timestamp checks)
- Geographic exclusions (Australia vs US)
- Experiment tag requirements create natural segmentation
- Lead cohort requirements ('Approved No Delivery', 'AUS - Approved No Delivery', etc.)

---

**Analysis Generated**: June 2025  
**Source**: dd_automated_sms_campaign_eligibility.sql  
**Total Campaigns Analyzed**: 51 active campaigns across 9 categories
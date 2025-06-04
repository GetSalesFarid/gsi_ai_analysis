-- DD AI outbound

select 
    e.message_uuid, 
    e.message, 
    e.direction, 
    e.owner_email, 
    t.opportunity_uuid, 
    e.sender_id, 
    e.account_id, 
    c.name, 
    e.origin, 
    e.ticket_id,
    e.created_at_timestamp,
    -- count(e2.message_uuid) as conversation_turns,
    count(*) over (partition by e.ticket_id) as conversation_turns,
    string_agg(
    to_json_string(struct(
        e2.message as message,
        e2.direction as direction,
        cast(e2.created_at_timestamp as string) as timestamp,
        e2.sender_id as sender_id,
        e2.owner_email as owner_email
    )), 
    '\n' 
    order by e2.created_at_timestamp
) as conversation_transcript
from `getsaleswarehouse.gsi_intermediate.avochato_sms_events` e 
join `getsaleswarehouse.avochato.channels` c on e.account_id = c.account_id
join `getsaleswarehouse`.`getsales`.`tags` t on t.opportunity_uuid = e.opportunity_uuid
left join `getsaleswarehouse.gsi_intermediate.avochato_sms_events` e2 
    on e2.ticket_id = e.ticket_id 
    and e2.created_at_timestamp < e.created_at_timestamp
where e.created_at_timestamp > timestamp_sub(current_timestamp, interval 10 day) 
    and lower(e.direction) in ('outbound', 'out') 
    and e.owner_email not in ('farid@getsales.team') 
    and c.account_id = 'lmA7bl898p' 
    and t.tag in ('doordash_manned_sms_ltv_ddok_ai_21d_treatment', 'doordash_manned_sms_ltv_ddok_ai_25d_treatment', 'doordash_manned_sms_ddok_ai_agent_initial_unattempted_treatment', 'doordash_manned_sms_ddok_ai_agent_missed_unattempted_treatment') 
    and e.origin = 'api'
group by 
    e.message_uuid, 
    e.message, 
    e.direction, 
    e.owner_email, 
    t.opportunity_uuid, 
    e.sender_id, 
    e.account_id, 
    c.name, 
    e.origin, 
    e.ticket_id,
    e.created_at_timestamp
order by e.ticket_id, e.created_at_timestamp desc

--------
-- DD Human outbound
select 
    e.message_uuid, 
    e.message, 
    e.direction, 
    e.owner_email, 
    t.opportunity_uuid, 
    e.sender_id, 
    e.account_id, 
    c.name, 
    e.origin,
    e.ticket_id,
    e.created_at_timestamp,
    count(*) over (partition by e.ticket_id) as conversation_turns,
    string_agg(
        to_json_string(struct(
            e2.message as message,
            e2.direction as direction,
            cast(e2.created_at_timestamp as string) as timestamp,
            e2.sender_id as sender_id,
            e2.owner_email as owner_email
        )), 
        '\n' 
        order by e2.created_at_timestamp
    ) as conversation_transcript
from `getsaleswarehouse.gsi_intermediate.avochato_sms_events` e 
join `getsaleswarehouse.avochato.channels` c on e.account_id = c.account_id
join `getsaleswarehouse`.`getsales`.`tags` t on t.opportunity_uuid = e.opportunity_uuid
left join `getsaleswarehouse.gsi_intermediate.avochato_sms_events` e2 
    on e2.ticket_id = e.ticket_id 
    and e2.created_at_timestamp < e.created_at_timestamp
where e.created_at_timestamp > timestamp_sub(current_timestamp, interval 8 day)
    and lower(e.direction) in ('outbound', 'out')
    and e.owner_email not in ('farid@getsales.team')
    and c.account_id = 'lmA7bl898p'
    and t.tag not in ('doordash_manned_sms_ltv_ddok_ai_21d_treatment', 'doordash_manned_sms_ltv_ddok_ai_25d_treatment', 'doordash_manned_sms_ddok_ai_agent_initial_unattempted_treatment', 'doordash_manned_sms_ddok_ai_agent_missed_unattempted_treatment')
    and e.origin = 'web'
    and e.message not in (
        select message
        from `getsaleswarehouse.gsi_intermediate.avochato_sms_events` e3
        join `getsaleswarehouse.avochato.channels` c3 on e3.account_id = c3.account_id
        join `getsaleswarehouse`.`getsales`.`tags` t3 on t3.opportunity_uuid = e3.opportunity_uuid
        where e3.created_at_timestamp > timestamp_sub(current_timestamp, interval 8 day)
            and lower(e3.direction) in ('outbound', 'out')
            and e3.owner_email not in ('farid@getsales.team')
            and c3.account_id = 'lmA7bl898p'
            and t3.tag not in ('doordash_manned_sms_ltv_ddok_ai_21d_treatment', 'doordash_manned_sms_ltv_ddok_ai_25d_treatment', 'doordash_manned_sms_ddok_ai_agent_initial_unattempted_treatment', 'doordash_manned_sms_ddok_ai_agent_missed_unattempted_treatment')
            and e3.origin = 'web'
        group by message
        having count(*) > 100
    )
group by 
    e.message_uuid, 
    e.message, 
    e.direction, 
    e.owner_email, 
    t.opportunity_uuid, 
    e.sender_id, 
    e.account_id, 
    c.name, 
    e.origin,
    e.ticket_id,
    e.created_at_timestamp
order by e.ticket_id, e.created_at_timestamp desc
------
-- lyft human query


select 
    e.message_uuid, 
    e.message, 
    e.direction, 
    e.owner_email, 
    t.opportunity_uuid, 
    e.sender_id, 
    e.account_id, 
    c.name, 
    e.origin,
    e.ticket_id,
    e.created_at_timestamp,
    count(*) over (partition by e.ticket_id) as conversation_turns,
    string_agg(
        to_json_string(struct(
            e3.message as message,
            e3.direction as direction,
            cast(e3.created_at_timestamp as string) as timestamp,
            e3.sender_id as sender_id,
            e3.owner_email as owner_email
        )), 
        '\n' 
        order by e3.created_at_timestamp
    ) as conversation_transcript
from `getsaleswarehouse.gsi_intermediate.avochato_sms_events` e 
join `getsaleswarehouse.avochato.channels` c on e.account_id = c.account_id
join `getsaleswarehouse`.`getsales`.`tags` t on t.opportunity_uuid = e.opportunity_uuid
left join `getsaleswarehouse.gsi_intermediate.avochato_sms_events` e3 
    on e3.ticket_id = e.ticket_id 
    and e3.created_at_timestamp < e.created_at_timestamp
where e.created_at_timestamp > timestamp_sub(current_timestamp, interval 24 day)
    and lower(e.direction) in ('outbound', 'out')
    and e.owner_email not in ('farid@getsales.team')
    and c.account_id = 'lmA7nQP98p'
    and e.origin = 'web'
    and e.message not in (
        select message
        from `getsaleswarehouse.gsi_intermediate.avochato_sms_events` e2
        join `getsaleswarehouse.avochato.channels` c2 on e2.account_id = c2.account_id
        join `getsaleswarehouse`.`getsales`.`tags` t2 on t2.opportunity_uuid = e2.opportunity_uuid
        where e2.created_at_timestamp > timestamp_sub(current_timestamp, interval 24 day)
            and lower(e2.direction) in ('outbound', 'out')
            and e2.owner_email not in ('farid@getsales.team')
            and c2.account_id = 'lmA7nQP98p'
            and e2.origin = 'web'
        group by message
        having count(*) > 100
    )
group by 
    e.message_uuid, 
    e.message, 
    e.direction, 
    e.owner_email, 
    t.opportunity_uuid, 
    e.sender_id, 
    e.account_id, 
    c.name, 
    e.origin,
    e.ticket_id,
    e.created_at_timestamp
order by e.ticket_id, e.created_at_timestamp desc
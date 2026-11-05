-- where do subscriptions come from?

-- 1) volume vs conversion over time
create or replace view a_monthly as
select
    month_start,
    count(*)                                   as calls,
    count(*) filter (where subscribed)         as subscriptions,
    avg(subscribed::int)                       as conversion_rate,
    avg(euribor3m)                             as avg_euribor3m
from stg_calls_dated
group by 1
order by 1;

-- 2) diminishing returns from calling the same client again in one campaign
create or replace view a_attempts as
select
    least(attempts_this_campaign, 10)                       as attempt_number,
    count(*)                                                as calls,
    avg(subscribed::int)                                    as conversion_rate,
    sum(count(*)) over (order by least(attempts_this_campaign, 10))
        / sum(count(*)) over ()                             as cumulative_share_of_clients
from stg_calls
group by 1
order by 1;

-- 3) what happened in the previous campaign
create or replace view a_previous_outcome as
select
    previous_outcome,
    count(*)                                   as calls,
    avg(subscribed::int)                       as conversion_rate,
    count(*) filter (where subscribed)         as subscriptions
from stg_calls
group by 1
order by conversion_rate desc;

-- 4) client segments
create or replace view a_segments as
select 'age' as dimension,
       case when age < 25 then '1. under 25' when age < 35 then '2. 25-34' when age < 45 then '3. 35-44'
            when age < 55 then '4. 45-54' when age < 65 then '5. 55-64' else '6. 65+' end as segment,
       count(*) as calls, avg(subscribed::int) as conversion_rate
from stg_calls group by 1, 2
union all
select 'job', job, count(*), avg(subscribed::int) from stg_calls group by 1, 2
union all
select 'contact', contact_type, count(*), avg(subscribed::int) from stg_calls group by 1, 2
order by dimension, segment;

-- 5) the interest rate environment
create or replace view a_euribor as
select
    case when euribor3m < 1 then '1. under 1%' when euribor3m < 2 then '2. 1-2%'
         when euribor3m < 4 then '3. 2-4%' else '4. 4%+' end   as euribor_band,
    count(*)                                                   as calls,
    avg(subscribed::int)                                       as conversion_rate
from stg_calls
group by 1
order by 1;

-- data quality checks, run before any analysis

create or replace view dq_report as
select 'Rows' as check_name, count(*)::varchar as result, 'expect 41,188 (UCI documentation)' as note
from stg_calls
union all
select 'Subscribed (yes)', count(*) filter (where subscribed)::varchar, 'expect 4,640'
from stg_calls
union all
select 'Fully duplicated rows', (count(*) - count(distinct (age, job, marital, education, credit_default,
        housing_loan, personal_loan, contact_type, month, day_of_week, call_seconds, attempts_this_campaign,
        days_since_last_campaign, previous_contacts, previous_outcome, employment_variation_rate,
        consumer_price_index, consumer_confidence_index, euribor3m, employees_thousands, subscribed)))::varchar,
       'kept: different clients can have identical attributes'
from stg_calls
union all
select 'job = unknown', count(*) filter (where job = 'unknown')::varchar, 'kept as its own category'
from stg_calls
union all
select 'education = unknown', count(*) filter (where education = 'unknown')::varchar, 'kept as its own category'
from stg_calls
union all
select 'credit_default = unknown', count(*) filter (where credit_default = 'unknown')::varchar,
       'very common; only 3 clients say yes, so the column says little'
from stg_calls
union all
select 'housing/personal loan = unknown', count(*) filter (where housing_loan = 'unknown')::varchar,
       'same rows for both columns'
from stg_calls
union all
select 'pdays = 999 (never contacted)', count(*) filter (where never_contacted_before)::varchar,
       '999 is a code, not 999 days; turned into null + flag'
from stg_calls
union all
select 'call_seconds = 0', count(*) filter (where call_seconds = 0)::varchar,
       'all of these are "no"; shows why duration leaks the answer'
from stg_calls;

-- clean staging view over the raw UCI file
-- run from repo root (relative path)

create or replace view stg_calls as
with raw as (
    select
        row_number() over () as call_id,
        *
    from read_csv('data/raw/bank-additional-full.csv', delim = ';', header = true)
)
select
    call_id,
    -- The file is in time order (May 2008 - Nov 2010) but has no year column.
    -- Rows 27,691 and 39,131 are the first calls of March 2009 and March 2010,
    -- right after the December rows, so the year is recovered from row position.
    case
        when call_id < 27691 then 2008
        when call_id < 39131 then 2009
        else 2010
    end                                                     as campaign_year,
    month,
    list_position(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'], month)
                                                            as month_num,
    day_of_week,
    age,
    job,
    marital,
    education,
    "default"                                               as credit_default,
    housing                                                 as housing_loan,
    loan                                                    as personal_loan,
    contact                                                 as contact_type,
    -- call length is only known after the call ends, so it can't be used to
    -- decide who to call. kept for analysis, never used in the model.
    duration                                                as call_seconds,
    campaign                                                as attempts_this_campaign,
    case when pdays = 999 then null else pdays end          as days_since_last_campaign,
    pdays = 999                                             as never_contacted_before,
    previous                                                as previous_contacts,
    poutcome                                                as previous_outcome,
    "emp.var.rate"                                          as employment_variation_rate,
    "cons.price.idx"                                        as consumer_price_index,
    "cons.conf.idx"                                         as consumer_confidence_index,
    euribor3m,
    "nr.employed"                                           as employees_thousands,
    y = 'yes'                                               as subscribed
from raw;

create or replace view stg_calls_dated as
select
    *,
    make_date(campaign_year, month_num, 1) as month_start
from stg_calls;

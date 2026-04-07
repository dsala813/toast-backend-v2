-- Bar Chef Production Control
-- First Retool slice queries
-- Use these as separate Retool queries, not as one giant query.

-- =====================================================
-- getPrepShifts
-- =====================================================
select
  ps.id,
  ps.shift_date,
  ps.status,
  ps.started_at,
  ps.ended_at,
  ps.bar_chef_name,
  l.name as location_name,
  ps.created_at
from public.prep_shifts ps
join public.locations l on l.id = ps.location_id
order by ps.shift_date desc, ps.created_at desc;

-- =====================================================
-- getPrepShiftById
-- Retool input: {{ prep_shift_id }}
-- =====================================================
select
  ps.*, 
  l.name as location_name
from public.prep_shifts ps
join public.locations l on l.id = ps.location_id
where ps.id = {{ prep_shift_id }};

-- =====================================================
-- getBarCheckSessionsByPrepShift
-- Retool input: {{ prep_shift_id }}
-- =====================================================
select
  bcs.id,
  bcs.started_at,
  bcs.ended_at,
  bcs.status,
  bcs.started_by,
  bcs.notes,
  l.name as location_name,
  b.name as bar_name,
  count(li.id) as line_item_count
from public.bar_check_sessions bcs
join public.locations l on l.id = bcs.location_id
join public.bars b on b.id = bcs.bar_id
left join public.bar_check_line_items li on li.bar_check_session_id = bcs.id
where bcs.prep_shift_id = {{ prep_shift_id }}
group by bcs.id, bcs.started_at, bcs.ended_at, bcs.status, bcs.started_by, bcs.notes, l.name, b.name
order by bcs.started_at asc;

-- =====================================================
-- getBarCheckSessionById
-- Retool input: {{ bar_check_session_id }}
-- =====================================================
select
  bcs.*, 
  ps.id as prep_shift_id,
  l.name as location_name,
  b.name as bar_name
from public.bar_check_sessions bcs
join public.prep_shifts ps on ps.id = bcs.prep_shift_id
join public.locations l on l.id = bcs.location_id
join public.bars b on b.id = bcs.bar_id
where bcs.id = {{ bar_check_session_id }};

-- =====================================================
-- getBarCheckLineItemsBySession
-- Retool input: {{ bar_check_session_id }}
-- =====================================================
select
  li.id,
  li.batch_configuration_id,
  bp.name as batch_product_name,
  li.crew_bottle_quantity_ml,
  li.crew_bottle_count,
  li.crew_bottle_expiration,
  li.usable,
  li.consolidated,
  li.empty_bottles_pulled,
  li.packaging_exception,
  li.packaging_exception_notes,
  li.notes,
  li.created_at
from public.bar_check_line_items li
join public.batch_configurations bc on bc.id = li.batch_configuration_id
join public.batch_products bp on bp.id = bc.batch_product_id
where li.bar_check_session_id = {{ bar_check_session_id }}
order by bp.name asc;

-- =====================================================
-- getBatchConfigurationsByLocation
-- Retool input: {{ location_id }}
-- =====================================================
select
  bc.id,
  bp.name as batch_product_name,
  bc.standard_batch_size_ml,
  bc.crew_bottle_type,
  bc.crew_bottle_volume_ml
from public.batch_configurations bc
join public.batch_products bp on bp.id = bc.batch_product_id
where bc.location_id = {{ location_id }}
  and bc.is_active = true
order by bp.name asc;

-- =====================================================
-- createBarCheckLineItem
-- Retool inputs:
-- {{ bar_check_session_id }}
-- {{ batch_configuration_id }}
-- {{ crew_bottle_quantity_ml }}
-- {{ crew_bottle_count }}
-- {{ crew_bottle_expiration }}
-- {{ usable }}
-- {{ consolidated }}
-- {{ empty_bottles_pulled }}
-- {{ notes }}
-- {{ packaging_exception }}
-- {{ packaging_exception_notes }}
-- =====================================================
insert into public.bar_check_line_items (
  bar_check_session_id,
  batch_configuration_id,
  crew_bottle_quantity_ml,
  crew_bottle_count,
  crew_bottle_expiration,
  usable,
  consolidated,
  empty_bottles_pulled,
  notes,
  packaging_exception,
  packaging_exception_notes
)
values (
  {{ bar_check_session_id }},
  {{ batch_configuration_id }},
  {{ crew_bottle_quantity_ml }},
  {{ crew_bottle_count }},
  {{ crew_bottle_expiration }},
  {{ usable }},
  {{ consolidated }},
  {{ empty_bottles_pulled }},
  {{ notes }},
  {{ packaging_exception }},
  {{ packaging_exception_notes }}
)
returning *;

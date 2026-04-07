-- Bar Chef Production Control
-- First-pass Supabase schema
-- v1 slice:
--   locations
--   bars
--   batch_products
--   batch_configurations
--   prep_shifts
--   bar_check_sessions
--   bar_check_line_items

begin;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create table if not exists public.locations (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  code text unique,
  notes text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_locations_updated_at
before update on public.locations
for each row
execute function public.set_updated_at();

create table if not exists public.bars (
  id uuid primary key default gen_random_uuid(),
  location_id uuid not null references public.locations(id) on delete restrict,
  name text not null,
  code text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint bars_location_name_unique unique (location_id, name),
  constraint bars_location_code_unique unique (location_id, code)
);

create index if not exists idx_bars_location_id
  on public.bars(location_id);

create index if not exists idx_bars_active
  on public.bars(is_active);

create trigger trg_bars_updated_at
before update on public.bars
for each row
execute function public.set_updated_at();

create table if not exists public.batch_products (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  code text unique,
  category text,
  storage_notes text,
  default_crew_bottle_type text,
  default_crew_bottle_volume_ml numeric(10,2),
  default_cooler_batch_standard_size_ml numeric(10,2),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint batch_products_default_crew_bottle_volume_nonnegative
    check (
      default_crew_bottle_volume_ml is null
      or default_crew_bottle_volume_ml >= 0
    ),
  constraint batch_products_default_cooler_batch_standard_size_nonnegative
    check (
      default_cooler_batch_standard_size_ml is null
      or default_cooler_batch_standard_size_ml >= 0
    )
);

create index if not exists idx_batch_products_active
  on public.batch_products(is_active);

create trigger trg_batch_products_updated_at
before update on public.batch_products
for each row
execute function public.set_updated_at();

create table if not exists public.batch_configurations (
  id uuid primary key default gen_random_uuid(),
  batch_product_id uuid not null references public.batch_products(id) on delete restrict,
  location_id uuid not null references public.locations(id) on delete restrict,
  standard_batch_size_ml numeric(10,2) not null,
  crew_bottle_type text,
  crew_bottle_volume_ml numeric(10,2),
  notes text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint batch_configurations_product_location_unique
    unique (batch_product_id, location_id),
  constraint batch_configurations_standard_batch_size_positive
    check (standard_batch_size_ml > 0),
  constraint batch_configurations_crew_bottle_volume_nonnegative
    check (
      crew_bottle_volume_ml is null
      or crew_bottle_volume_ml >= 0
    )
);

create index if not exists idx_batch_configurations_location_active
  on public.batch_configurations(location_id, is_active);

create index if not exists idx_batch_configurations_batch_product_id
  on public.batch_configurations(batch_product_id);

create trigger trg_batch_configurations_updated_at
before update on public.batch_configurations
for each row
execute function public.set_updated_at();

create table if not exists public.prep_shifts (
  id uuid primary key default gen_random_uuid(),
  location_id uuid not null references public.locations(id) on delete restrict,
  shift_date date not null default current_date,
  bar_chef_name text,
  started_at timestamptz,
  ended_at timestamptz,
  status text not null default 'open',
  notes text,
  low_86_notes text,
  shift_summary text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint prep_shifts_status_valid
    check (status in ('open', 'closed')),
  constraint prep_shifts_ended_after_started
    check (
      ended_at is null
      or started_at is null
      or ended_at >= started_at
    )
);

create index if not exists idx_prep_shifts_location_id
  on public.prep_shifts(location_id);

create index if not exists idx_prep_shifts_shift_date
  on public.prep_shifts(shift_date desc);

create index if not exists idx_prep_shifts_status
  on public.prep_shifts(status);

create trigger trg_prep_shifts_updated_at
before update on public.prep_shifts
for each row
execute function public.set_updated_at();

create table if not exists public.bar_check_sessions (
  id uuid primary key default gen_random_uuid(),
  prep_shift_id uuid not null references public.prep_shifts(id) on delete cascade,
  location_id uuid not null references public.locations(id) on delete restrict,
  bar_id uuid not null references public.bars(id) on delete restrict,
  started_at timestamptz not null default now(),
  started_by text,
  ended_at timestamptz,
  status text not null default 'open',
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint bar_check_sessions_status_valid
    check (status in ('open', 'finalized', 'locked')),
  constraint bar_check_sessions_ended_after_started
    check (
      ended_at is null
      or ended_at >= started_at
    )
);

create index if not exists idx_bar_check_sessions_prep_shift_id
  on public.bar_check_sessions(prep_shift_id);

create index if not exists idx_bar_check_sessions_location_id
  on public.bar_check_sessions(location_id);

create index if not exists idx_bar_check_sessions_bar_id
  on public.bar_check_sessions(bar_id);

create index if not exists idx_bar_check_sessions_status
  on public.bar_check_sessions(status);

create trigger trg_bar_check_sessions_updated_at
before update on public.bar_check_sessions
for each row
execute function public.set_updated_at();

create table if not exists public.bar_check_line_items (
  id uuid primary key default gen_random_uuid(),
  bar_check_session_id uuid not null references public.bar_check_sessions(id) on delete cascade,
  batch_configuration_id uuid not null references public.batch_configurations(id) on delete restrict,
  crew_bottle_quantity_ml numeric(10,2),
  crew_bottle_count numeric(10,2),
  crew_bottle_expiration date,
  usable boolean,
  consolidated boolean,
  empty_bottles_pulled integer,
  notes text,
  packaging_exception boolean,
  packaging_exception_notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint bar_check_line_items_session_config_unique
    unique (bar_check_session_id, batch_configuration_id),
  constraint bar_check_line_items_quantity_nonnegative
    check (
      crew_bottle_quantity_ml is null
      or crew_bottle_quantity_ml >= 0
    ),
  constraint bar_check_line_items_count_nonnegative
    check (
      crew_bottle_count is null
      or crew_bottle_count >= 0
    ),
  constraint bar_check_line_items_empty_bottles_nonnegative
    check (
      empty_bottles_pulled is null
      or empty_bottles_pulled >= 0
    )
);

create index if not exists idx_bar_check_line_items_session_id
  on public.bar_check_line_items(bar_check_session_id);

create index if not exists idx_bar_check_line_items_batch_configuration_id
  on public.bar_check_line_items(batch_configuration_id);

create trigger trg_bar_check_line_items_updated_at
before update on public.bar_check_line_items
for each row
execute function public.set_updated_at();

commit;

-- Move & Thrive — initial schema
-- Single-user MVP, but uses auth.users so it's ready for multi-tenant later.

-- 1. Profile: conditions, diet, goals, current week, gym weights
create table public.profiles (
  id uuid primary key references auth.users on delete cascade,
  display_name text,
  conditions jsonb not null default '[]'::jsonb,   -- [{name, severity, notes}]
  diet jsonb not null default '{}'::jsonb,         -- {type, restrictions, notes}
  goals jsonb not null default '[]'::jsonb,        -- ["build muscle", ...]
  current_week int not null default 1,
  weights jsonb not null default '{}'::jsonb,      -- {upper: {...}, lower: {...}}
  preferences jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 2. Session logs (workouts)
create table public.session_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  block_id text not null,         -- A, B, C, D, E, F
  block_name text not null,
  date date not null,
  duration text,
  mood text,                      -- Low | Ok | Good | Great
  pain text,                      -- none | back | knee | both
  notes text,
  week int,
  created_at timestamptz not null default now()
);
create index session_logs_user_date_idx on public.session_logs (user_id, date desc);

-- 3. Coach chat history
create table public.coach_messages (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);
create index coach_messages_user_created_idx on public.coach_messages (user_id, created_at);

-- 4. Rolling coach summary (so the LLM doesn't need full history each call)
create table public.coach_summaries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  summary text not null,
  message_count_at_summary int not null default 0,
  created_at timestamptz not null default now()
);
create index coach_summaries_user_created_idx on public.coach_summaries (user_id, created_at desc);

-- 5. Adaptations (coach-suggested plan tweaks surfaced on Plan tab)
create table public.adaptations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  text text not null,
  created_at timestamptz not null default now()
);
create index adaptations_user_created_idx on public.adaptations (user_id, created_at desc);

-- Updated-at trigger for profiles
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;
create trigger profiles_touch_updated_at
  before update on public.profiles
  for each row execute function public.touch_updated_at();

-- Auto-create a profile row when a new auth user signs up
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id) values (new.id) on conflict do nothing;
  return new;
end;
$$;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- RLS: every user only sees their own data
alter table public.profiles enable row level security;
alter table public.session_logs enable row level security;
alter table public.coach_messages enable row level security;
alter table public.coach_summaries enable row level security;
alter table public.adaptations enable row level security;

create policy "own profile" on public.profiles for all
  using (auth.uid() = id) with check (auth.uid() = id);
create policy "own logs" on public.session_logs for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own messages" on public.coach_messages for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own summaries" on public.coach_summaries for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own adaptations" on public.adaptations for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

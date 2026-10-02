-- Run once in Supabase > SQL Editor.
create table if not exists public.portfolio_state (
  key text primary key,
  content jsonb not null,
  updated_at timestamptz not null default now()
);

create or replace function public.set_portfolio_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end; $$;

drop trigger if exists portfolio_state_updated_at on public.portfolio_state;
create trigger portfolio_state_updated_at
before update on public.portfolio_state
for each row execute function public.set_portfolio_updated_at();

insert into storage.buckets (id, name, public)
values ('portfolio-media', 'portfolio-media', true)
on conflict (id) do update set public = true;

-- The app writes with the server-side service-role key stored only in Streamlit Secrets.
-- No public write policy is required.

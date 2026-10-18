-- Run in the EXISTING Supabase project's SQL editor.
create table if not exists public.voice_jobs (
 id uuid primary key default gen_random_uuid(),
 title text not null,
 script text not null,
 reference_path text not null,
 reference_text text not null,
 status text not null default 'queued' check (status in ('queued','processing','done','failed')),
 output_path text,
 error text,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
alter table public.voice_jobs enable row level security;
revoke all on public.voice_jobs from anon, authenticated;
insert into storage.buckets (id,name,public) values ('voice-private','voice-private',false)
on conflict (id) do update set public=false;
-- Access is restricted to the server-side service role. Never expose that key in client-side code.

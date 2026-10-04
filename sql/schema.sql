-- Eseguire una volta nel SQL Editor di un nuovo progetto Supabase.
begin;
create table public.participants (
 id uuid primary key default gen_random_uuid(),
 full_name text not null check(length(trim(full_name)) between 1 and 120),
 team text not null check(team in ('ENERGETICI','RDM')),
 submitted boolean not null default false,
 submitted_at timestamptz,
 created_at timestamptz not null default now(),
 check(submitted = (submitted_at is not null))
);
create table public.sponsors (
 id uuid primary key default gen_random_uuid(),
 team text not null check(team in ('ENERGETICI','RDM')),
 slot_number integer not null check(slot_number between 1 and 3),
 sponsor_name text not null check(length(trim(sponsor_name)) between 1 and 120),
 active boolean not null default true,
 unique(team,slot_number)
);
create table public.votes (
 id uuid primary key default gen_random_uuid(),
 participant_id uuid not null unique references public.participants(id),
 team text not null check(team in ('ENERGETICI','RDM')),
 team_name_choice text not null,
 sponsor_id uuid not null references public.sponsors(id),
 crest_choice text not null,
 kit_choice text not null,
 submitted_at timestamptz not null default now()
);
create table public.contest_settings (key text primary key, value text not null);
insert into public.contest_settings values ('contest_open','true');
insert into public.sponsors(team,slot_number,sponsor_name) values
 ('ENERGETICI',1,'Cosφ 0.9'), ('ENERGETICI',2,'Perdite < 1%'), ('ENERGETICI',3,'MPPT & Chill'),
 ('RDM',1,'Fuori Computo'), ('RDM',2,'Variante in Corso'), ('RDM',3,'Da Verificare in Cantiere');

-- Tutte le scritture autorizzate passano per RPC e condividono lo stesso
-- lock transazionale: invio, cambio squadra, chiusura e sponsor non corrono.
create function public.submit_vote(p_participant uuid, p_name text, p_sponsor uuid, p_crest text, p_kit text)
returns uuid language plpgsql security definer set search_path = '' as $$
declare person public.participants; allowed text[]; result uuid;
begin
 perform pg_advisory_xact_lock(749320);
 select * into person from public.participants where id=p_participant for update;
 if not found then raise exception 'INVALID_CHOICE'; end if;
 if person.submitted or exists(select 1 from public.votes where participant_id=p_participant) then
   raise exception 'ALREADY_SUBMITTED';
 end if;
 if not exists(select 1 from public.contest_settings where key='contest_open' and value='true') then
   raise exception 'CONTEST_CLOSED';
 end if;
 allowed := case when person.team='ENERGETICI' then array['energetici_fc','renewables','energentus']
   else array['rdm_fc','rdm_world','rdm_internazionale'] end;
 if p_name is null or p_crest is null or p_kit is null or p_sponsor is null
   or not(p_name=any(allowed)) or not(p_crest=any(allowed)) or not(p_kit=any(allowed))
   or not exists(select 1 from public.sponsors where id=p_sponsor and team=person.team and active) then
   raise exception 'INVALID_CHOICE';
 end if;
 insert into public.votes(participant_id,team,team_name_choice,sponsor_id,crest_choice,kit_choice)
 values(p_participant,person.team,p_name,p_sponsor,p_crest,p_kit) returning id into result;
 update public.participants set submitted=true,submitted_at=now() where id=p_participant;
 return result;
end $$;

create function public.manage_participant(p_action text, p_id uuid, p_name text, p_team text)
returns void language plpgsql security definer set search_path = '' as $$
begin
 perform pg_advisory_xact_lock(749320);
 if p_action='add' then
   insert into public.participants(full_name,team) values(trim(p_name),p_team);
 else
   if exists(select 1 from public.participants where id=p_id and submitted)
     or exists(select 1 from public.votes where participant_id=p_id) then
     raise exception 'PARTICIPANT_LOCKED';
   end if;
   if p_action='update' then update public.participants set team=p_team where id=p_id;
   elsif p_action='delete' then delete from public.participants where id=p_id;
   else raise exception 'INVALID_CHOICE'; end if;
 end if;
end $$;

create function public.update_sponsors(p_team text, p_names text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
 perform pg_advisory_xact_lock(749320);
 if exists(select 1 from public.votes where team=p_team) then raise exception 'SPONSORS_LOCKED'; end if;
 if cardinality(p_names)<>3 or p_team not in ('ENERGETICI','RDM') then raise exception 'INVALID_CHOICE'; end if;
 update public.sponsors set sponsor_name=trim(p_names[slot_number]) where team=p_team;
end $$;

create function public.set_contest_open(p_open boolean)
returns void language plpgsql security definer set search_path = '' as $$
begin
 perform pg_advisory_xact_lock(749320);
 update public.contest_settings set value=case when p_open then 'true' else 'false' end where key='contest_open';
end $$;

alter table public.participants enable row level security;
alter table public.sponsors enable row level security;
alter table public.votes enable row level security;
alter table public.contest_settings enable row level security;
revoke all on public.participants,public.sponsors,public.votes,public.contest_settings from anon,authenticated,service_role;
grant select on public.participants,public.sponsors,public.votes,public.contest_settings to service_role;
revoke all on function public.submit_vote(uuid,text,uuid,text,text) from public,anon,authenticated;
revoke all on function public.manage_participant(text,uuid,text,text) from public,anon,authenticated;
revoke all on function public.update_sponsors(text,text[]) from public,anon,authenticated;
revoke all on function public.set_contest_open(boolean) from public,anon,authenticated;
grant execute on function public.submit_vote(uuid,text,uuid,text,text), public.manage_participant(text,uuid,text,text),
 public.update_sponsors(text,text[]), public.set_contest_open(boolean) to service_role;
commit;

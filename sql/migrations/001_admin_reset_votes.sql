-- Run once in the EXISTING Calcetto FAVERO project. Does not reset any votes.
-- Adds a server-only, transactional reset for explicitly selected participants.
begin;
create or replace function public.admin_reset_votes(p_participants uuid[], p_confirmation text)
returns integer language plpgsql security definer set search_path = '' as $$
declare removed integer;
begin
 perform pg_advisory_xact_lock(749320);
 if p_confirmation is distinct from 'RESET'
    or p_participants is null or cardinality(p_participants) not between 1 and 50
    or array_position(p_participants,null) is not null then
   raise exception 'INVALID_RESET';
 end if;
 if exists(select 1 from unnest(p_participants) as selected(id)
           where not exists(select 1 from public.participants p where p.id=selected.id)) then
   raise exception 'INVALID_RESET';
 end if;
 delete from public.votes where participant_id=any(p_participants);
 get diagnostics removed = row_count;
 update public.participants set submitted=false,submitted_at=null where id=any(p_participants);
 return removed;
end $$;
revoke all on function public.admin_reset_votes(uuid[],text) from public,anon,authenticated;
grant execute on function public.admin_reset_votes(uuid[],text) to service_role;
commit;

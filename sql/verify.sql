-- Dopo schema.sql, nel SQL Editor. Nessuna modifica viene conservata.
begin;
do $$
declare person uuid; sponsor uuid; n integer;
begin
 perform public.set_contest_open(true);
 perform public.manage_participant('add',null,'SQL verification','ENERGETICI');
 select id into person from public.participants where full_name='SQL verification' order by created_at desc limit 1;
 select id into sponsor from public.sponsors where team='ENERGETICI' and slot_number=1;
 begin
   perform public.submit_vote(person,'rdm_fc',sponsor,'energetici_fc','energentus');
   raise exception 'Test failed: cross-team vote accepted';
 exception when others then
   if sqlerrm <> 'INVALID_CHOICE' then raise; end if;
 end;
 perform public.submit_vote(person,'renewables',sponsor,'energetici_fc','energentus');
 select count(*) into n from public.votes where participant_id=person;
 if n<>1 or not exists(select 1 from public.participants where id=person and submitted and submitted_at is not null) then
   raise exception 'Test failed: atomic submit';
 end if;
 begin
   perform public.submit_vote(person,'renewables',sponsor,'energetici_fc','energentus');
   raise exception 'Test failed: duplicate accepted';
 exception when others then if sqlerrm<>'ALREADY_SUBMITTED' then raise; end if; end;
 begin
   perform public.update_sponsors('ENERGETICI',array['A','B','C']);
   raise exception 'Test failed: sponsors changed';
 exception when others then if sqlerrm<>'SPONSORS_LOCKED' then raise; end if; end;
 begin
   perform public.manage_participant('delete',person,null,null);
   raise exception 'Test failed: voted participant deleted';
 exception when others then if sqlerrm<>'PARTICIPANT_LOCKED' then raise; end if; end;
 if has_function_privilege('anon','public.submit_vote(uuid,text,uuid,text,text)','EXECUTE')
 or has_table_privilege('service_role','public.votes','INSERT') then
   raise exception 'Test failed: unexpected privilege';
 end if;
 raise notice 'PASS: validation, atomic submit, duplicate, sponsor and participant locks, privileges';
end $$;
rollback;

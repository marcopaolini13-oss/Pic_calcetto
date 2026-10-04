-- Only isolated test databases: creates temporary test rows inside a rollback.
begin;
do $$
declare first_id uuid; second_id uuid; sponsor uuid; removed integer;
begin
 insert into public.participants(full_name,team) values('Reset check one','RDM') returning id into first_id;
 insert into public.participants(full_name,team) values('Reset check two','RDM') returning id into second_id;
 select id into sponsor from public.sponsors where team='RDM' and slot_number=1;
 perform public.submit_vote(first_id,'rdm_fc',sponsor,'rdm_fc','rdm_world');
 perform public.submit_vote(second_id,'rdm_world',sponsor,'rdm_world','rdm_fc');
 begin
   perform public.admin_reset_votes(array[first_id],'wrong');
   raise exception 'Invalid confirmation was accepted';
 exception when raise_exception then
   if sqlerrm <> 'INVALID_RESET' then raise; end if;
 end;
 removed:=public.admin_reset_votes(array[first_id],'RESET');
 if removed<>1 or exists(select 1 from public.votes where participant_id=first_id)
    or not exists(select 1 from public.participants where id=first_id and not submitted and submitted_at is null)
    or not exists(select 1 from public.votes where participant_id=second_id)
    or not exists(select 1 from public.participants where id=second_id and submitted) then
   raise exception 'Reset did not preserve the other participant vote';
 end if;
 perform public.submit_vote(first_id,'rdm_fc',sponsor,'rdm_fc','rdm_internazionale');
 if (select count(*) from public.votes where participant_id=first_id)<>1 then
   raise exception 'Resubmission failed';
 end if;
 if has_function_privilege('anon','public.admin_reset_votes(uuid[],text)','execute')
    or has_function_privilege('authenticated','public.admin_reset_votes(uuid[],text)','execute')
    or not has_function_privilege('service_role','public.admin_reset_votes(uuid[],text)','execute') then
   raise exception 'Reset privileges are incorrect';
 end if;
end $$;
rollback;

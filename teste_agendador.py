from service.agendador_service import agendador, iniciar_agendador

iniciar_agendador()

trabalho = agendador.get_job("rotina_diaria_prazus")

if trabalho:
    print("Agendador funcionando!")
    print("Próxima execução:", trabalho.next_run_time)
else:
    print("Agendamento não encontrado.")

agendador.shutdown()
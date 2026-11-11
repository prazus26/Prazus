from datetime import timedelta


def eh_dia_util(data, feriados):
    return data.weekday() < 5 and data not in feriados


def proximo_dia_util(data, feriados):
    data += timedelta(days=1)

    while not eh_dia_util(data, feriados):
        data += timedelta(days=1)

    return data


def calcular_data_publicacao(data_disponibilizacao, feriados):
    return proximo_dia_util(data_disponibilizacao, feriados)


def calcular_data_inicio(data_publicacao, feriados):
    return proximo_dia_util(data_publicacao, feriados)


def calcular_vencimento(data_inicio, dias, tipo_contagem, feriados):
    data = data_inicio

    if tipo_contagem == "uteis":
        dias_contados = 1

        while dias_contados < dias:
            data += timedelta(days=1)

            if eh_dia_util(data, feriados):
                dias_contados += 1

    else:
        data += timedelta(days=dias - 1)

        while not eh_dia_util(data, feriados):
            data += timedelta(days=1)

    return data

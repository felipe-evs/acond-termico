from src.db.connection import get_connection


def validar_modelo(modelo_id, tests_aprobados, total_tests):
    conn = get_connection()
    if tests_aprobados == total_tests:
        resultado = "validado"
        razon = None
    else:
        resultado = "no_validado"
        fallados = total_tests - tests_aprobados
        razon = f"{fallados} de {total_tests} tests fallaron"

    conn.execute(
        "INSERT INTO eco_validacion (modelo_id, resultado_global, razon_rechazo) VALUES (?, ?, ?)",
        (modelo_id, resultado, razon),
    )
    conn.commit()
    conn.close()
    return resultado, razon

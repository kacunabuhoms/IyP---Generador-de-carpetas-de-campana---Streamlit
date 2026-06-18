import sql_service


class _StubConnection:
    def __init__(self):
        self.llamadas = []

    def query(self, sql, ttl=None):
        self.llamadas.append((sql, ttl))
        return "fake-dataframe"


def test_get_campaigns_runs_expected_query_without_cache():
    conn = _StubConnection()
    resultado = sql_service.get_campaigns(conn)

    assert resultado == "fake-dataframe"
    sql_ejecutado, ttl_usado = conn.llamadas[0]
    assert sql_ejecutado == sql_service.CAMPAIGNS_QUERY
    assert ttl_usado == 0

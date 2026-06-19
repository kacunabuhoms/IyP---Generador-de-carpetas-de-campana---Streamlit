from campaign_data import campaigns_for_client, unique_clients


def test_unique_clients_returns_sorted_unique_names(campanas_df):
    clientes = unique_clients(campanas_df)
    assert clientes == sorted(set(clientes))
    assert "FDA" in clientes
    assert "DQ" in clientes


def test_campaigns_for_client_deduplicates_by_name(campanas_df):
    campanas = campaigns_for_client(campanas_df, "FDA")
    nombres = campanas["campana"].tolist()
    assert len(nombres) == len(set(nombres))


def test_campaigns_for_client_includes_known_duplicate_once(campanas_df):
    campanas = campaigns_for_client(campanas_df, "FDA")
    coincidencias = campanas[campanas["campana"] == "Campana Marzo"]
    assert len(coincidencias) == 1


def test_campaigns_for_client_keeps_cliente_column(campanas_df):
    campanas = campaigns_for_client(campanas_df, "FDA")
    assert (campanas["cliente"] == "FDA").all()

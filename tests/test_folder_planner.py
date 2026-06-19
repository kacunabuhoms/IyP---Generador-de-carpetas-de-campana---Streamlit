from datetime import date

from folder_planner import compute_default_year
import folder_planner
from folder_planner import CampanaDecision


def test_compute_default_year_same_year_when_no_rollover():
    assert compute_default_year(date(2026, 8, 15)) == 2026


def test_compute_default_year_rolls_over_in_december():
    assert compute_default_year(date(2026, 12, 1)) == 2027


def test_compute_default_year_january_stays_same_year():
    assert compute_default_year(date(2026, 1, 5)) == 2026


def test_build_preview_skips_campana_lookup_when_anio_missing(monkeypatch):
    calls = []

    def fake_find(drive, parent_id, name):
        calls.append((parent_id, name))
        return None

    monkeypatch.setattr(folder_planner.drive_service, "find_child_folder", fake_find)
    preview = folder_planner.build_preview(
        drive=object(), root_id="root1", cliente="FDA", anio=2026, nombre_campana="Campana X"
    )

    assert preview.anio.existe is False
    assert preview.campana.existe is False
    assert calls == [("root1", "FDA 2026")]


def test_build_preview_checks_campana_when_anio_exists(monkeypatch):
    def fake_find(drive, parent_id, name):
        if parent_id == "root1":
            return "anio_id_1"
        if parent_id == "anio_id_1":
            return "campana_id_1"
        return None

    monkeypatch.setattr(folder_planner.drive_service, "find_child_folder", fake_find)
    preview = folder_planner.build_preview(
        drive=object(), root_id="root1", cliente="FDA", anio=2026, nombre_campana="Campana X"
    )

    assert preview.anio.existe is True
    assert preview.anio.folder_id == "anio_id_1"
    assert preview.campana.existe is True
    assert preview.campana.folder_id == "campana_id_1"


def test_execute_plan_creates_everything_when_nothing_exists(monkeypatch):
    created = []

    def fake_create(drive, parent_id, name):
        created.append((parent_id, name))
        return f"id-{name}"

    monkeypatch.setattr(folder_planner.drive_service, "create_folder", fake_create)

    preview = folder_planner.CampanaPreview(
        anio=folder_planner.PreviewNode(nombre="FDA 2026", existe=False, folder_id=None),
        campana=folder_planner.PreviewNode(nombre="Campana X", existe=False, folder_id=None),
    )
    decision = CampanaDecision(accion="crear_nueva", nombre_final="Campana X")

    resultado = folder_planner.execute_plan(
        drive=object(),
        root_id="root1",
        preview=preview,
        decision=decision,
        subfolder_names=["Fotos", "Totales"],
    )

    nombres_creados = [c[1] for c in created]
    assert nombres_creados == ["FDA 2026", "Campana X", "Fotos", "Totales"]
    assert resultado.campana_folder_id == "id-Campana X"
    assert resultado.error is None
    assert all(item["accion"] == "creada" for item in resultado.items)


def test_execute_plan_reuses_existing_campana_and_its_subfolders(monkeypatch):
    def fake_find_sub(drive, parent_id, name):
        if name == "Fotos":
            return "fotos_id"
        return None

    created = []

    def fake_create(drive, parent_id, name):
        created.append(name)
        return f"id-{name}"

    monkeypatch.setattr(folder_planner.drive_service, "find_child_folder", fake_find_sub)
    monkeypatch.setattr(folder_planner.drive_service, "create_folder", fake_create)

    preview = folder_planner.CampanaPreview(
        anio=folder_planner.PreviewNode(nombre="FDA 2026", existe=True, folder_id="anio_id_1"),
        campana=folder_planner.PreviewNode(nombre="Campana X", existe=True, folder_id="campana_id_1"),
    )
    decision = CampanaDecision(accion="reusar", nombre_final="Campana X")

    resultado = folder_planner.execute_plan(
        drive=object(),
        root_id="root1",
        preview=preview,
        decision=decision,
        subfolder_names=["Fotos", "Totales"],
    )

    assert resultado.campana_folder_id == "campana_id_1"
    assert resultado.error is None
    assert created == ["Totales"]
    acciones = {item["nombre"]: item["accion"] for item in resultado.items}
    assert acciones["FDA 2026"] == "reusada"
    assert acciones["Campana X"] == "reusada"
    assert acciones["Fotos"] == "reusada"
    assert acciones["Totales"] == "creada"


def test_execute_plan_creates_new_campana_with_edited_name_even_if_original_exists(monkeypatch):
    created = []

    def fake_create(drive, parent_id, name):
        created.append((parent_id, name))
        return f"id-{name}"

    monkeypatch.setattr(folder_planner.drive_service, "create_folder", fake_create)

    preview = folder_planner.CampanaPreview(
        anio=folder_planner.PreviewNode(nombre="FDA 2026", existe=True, folder_id="anio_id_1"),
        campana=folder_planner.PreviewNode(nombre="Campana X", existe=True, folder_id="campana_id_1"),
    )
    decision = CampanaDecision(accion="crear_nueva", nombre_final="Campana X (2)")

    resultado = folder_planner.execute_plan(
        drive=object(),
        root_id="root1",
        preview=preview,
        decision=decision,
        subfolder_names=["Fotos"],
    )

    assert ("anio_id_1", "Campana X (2)") in created
    assert resultado.campana_folder_id == "id-Campana X (2)"


def test_build_subfolder_preview_marks_all_missing_when_campana_is_new(monkeypatch):
    calls = []

    def fake_find(drive, parent_id, name):
        calls.append((parent_id, name))
        return "should-not-be-called"

    monkeypatch.setattr(folder_planner.drive_service, "find_child_folder", fake_find)

    resultado = folder_planner.build_subfolder_preview(
        drive=object(), campana_folder_id=None, subfolder_names=["Fotos", "Totales"]
    )

    assert calls == []
    assert [n.nombre for n in resultado] == ["Fotos", "Totales"]
    assert all(n.existe is False and n.folder_id is None for n in resultado)


def test_build_subfolder_preview_checks_each_subfolder_when_campana_exists(monkeypatch):
    def fake_find(drive, parent_id, name):
        assert parent_id == "campana_id_1"
        if name == "Fotos":
            return "fotos_id"
        return None

    monkeypatch.setattr(folder_planner.drive_service, "find_child_folder", fake_find)

    resultado = folder_planner.build_subfolder_preview(
        drive=object(), campana_folder_id="campana_id_1", subfolder_names=["Fotos", "Totales"]
    )

    assert resultado[0].nombre == "Fotos"
    assert resultado[0].existe is True
    assert resultado[0].folder_id == "fotos_id"
    assert resultado[1].nombre == "Totales"
    assert resultado[1].existe is False
    assert resultado[1].folder_id is None


def test_render_tree_when_anio_and_campana_are_new():
    anio = folder_planner.PreviewNode(nombre="FDA 2026", existe=False, folder_id=None)
    subcarpetas = [
        folder_planner.PreviewNode(nombre="Fotos", existe=False, folder_id=None),
        folder_planner.PreviewNode(nombre="Totales", existe=False, folder_id=None),
    ]

    arbol = folder_planner.render_tree(
        anio=anio, campana_nombre="Campana X", campana_reutilizada=False, subcarpetas=subcarpetas
    )

    assert arbol == (
        "FDA 2026/  (se creará)\n"
        "└── Campana X/  (se creará)\n"
        "    ├── Fotos/  (se creará)\n"
        "    └── Totales/  (se creará)"
    )


def test_render_tree_when_reusing_existing_campana_with_mixed_subfolders():
    anio = folder_planner.PreviewNode(nombre="FDA 2026", existe=True, folder_id="anio_id_1")
    subcarpetas = [
        folder_planner.PreviewNode(nombre="Fotos", existe=True, folder_id="fotos_id"),
        folder_planner.PreviewNode(nombre="Totales", existe=False, folder_id=None),
        folder_planner.PreviewNode(nombre="Acomodo", existe=False, folder_id=None),
    ]

    arbol = folder_planner.render_tree(
        anio=anio, campana_nombre="Campana X", campana_reutilizada=True, subcarpetas=subcarpetas
    )

    assert arbol == (
        "FDA 2026/  (ya existe)\n"
        "└── Campana X/  (se reusará)\n"
        "    ├── Fotos/  (ya existe)\n"
        "    ├── Totales/  (se creará)\n"
        "    └── Acomodo/  (se creará)"
    )


def test_render_tree_with_no_subcarpetas():
    anio = folder_planner.PreviewNode(nombre="FDA 2026", existe=False, folder_id=None)

    arbol = folder_planner.render_tree(
        anio=anio, campana_nombre="Campana X", campana_reutilizada=False, subcarpetas=[]
    )

    assert arbol == "FDA 2026/  (se creará)\n└── Campana X/  (se creará)"


def test_execute_plan_stops_and_reports_error_on_drive_failure(monkeypatch):
    def fake_create(drive, parent_id, name):
        if name == "Campana X":
            raise RuntimeError("permiso denegado")
        return f"id-{name}"

    monkeypatch.setattr(folder_planner.drive_service, "create_folder", fake_create)

    preview = folder_planner.CampanaPreview(
        anio=folder_planner.PreviewNode(nombre="FDA 2026", existe=False, folder_id=None),
        campana=folder_planner.PreviewNode(nombre="Campana X", existe=False, folder_id=None),
    )
    decision = CampanaDecision(accion="crear_nueva", nombre_final="Campana X")

    resultado = folder_planner.execute_plan(
        drive=object(),
        root_id="root1",
        preview=preview,
        decision=decision,
        subfolder_names=["Fotos"],
    )

    assert resultado.error is not None
    assert "Campana X" in resultado.error
    assert resultado.campana_folder_id is None
    assert len(resultado.items) == 1
    assert resultado.items[0]["nombre"] == "FDA 2026"

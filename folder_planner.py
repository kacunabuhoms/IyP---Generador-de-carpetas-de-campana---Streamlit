from datetime import date
from dataclasses import dataclass

import drive_service


def compute_default_year(today: date) -> int:
    if today.month == 12:
        return today.year + 1
    return today.year


@dataclass
class PreviewNode:
    nombre: str
    existe: bool
    folder_id: str | None


@dataclass
class CampanaPreview:
    anio: PreviewNode
    campana: PreviewNode


@dataclass
class CampanaDecision:
    accion: str  # "reusar" o "crear_nueva"
    nombre_final: str


@dataclass
class ExecutionResult:
    items: list[dict]
    campana_folder_id: str | None
    error: str | None = None


def build_preview(drive, root_id: str, cliente: str, anio: int, nombre_campana: str) -> CampanaPreview:
    anio_nombre = f"{cliente} {anio}"
    anio_id = drive_service.find_child_folder(drive, root_id, anio_nombre)
    campana_id = None
    if anio_id is not None:
        campana_id = drive_service.find_child_folder(drive, anio_id, nombre_campana)
    return CampanaPreview(
        anio=PreviewNode(nombre=anio_nombre, existe=anio_id is not None, folder_id=anio_id),
        campana=PreviewNode(nombre=nombre_campana, existe=campana_id is not None, folder_id=campana_id),
    )


def build_subfolder_preview(
    drive, campana_folder_id: str | None, subfolder_names: list[str]
) -> list[PreviewNode]:
    nodos = []
    for nombre in subfolder_names:
        folder_id = None
        if campana_folder_id is not None:
            folder_id = drive_service.find_child_folder(drive, campana_folder_id, nombre)
        nodos.append(PreviewNode(nombre=nombre, existe=folder_id is not None, folder_id=folder_id))
    return nodos


def render_tree(
    anio: PreviewNode, campana_nombre: str, campana_reutilizada: bool, subcarpetas: list[PreviewNode]
) -> str:
    anio_estado = "ya existe" if anio.existe else "se creará"
    campana_estado = "se reusará" if campana_reutilizada else "se creará"

    lineas = [
        f"{anio.nombre}/  ({anio_estado})",
        f"└── {campana_nombre}/  ({campana_estado})",
    ]
    for i, sub in enumerate(subcarpetas):
        conector = "└──" if i == len(subcarpetas) - 1 else "├──"
        sub_estado = "ya existe" if sub.existe else "se creará"
        lineas.append(f"    {conector} {sub.nombre}/  ({sub_estado})")

    return "\n".join(lineas)


def execute_plan(
    drive,
    root_id: str,
    preview: CampanaPreview,
    decision: CampanaDecision,
    subfolder_names: list[str],
) -> ExecutionResult:
    resultados: list[dict] = []

    try:
        if preview.anio.existe:
            anio_id = preview.anio.folder_id
            resultados.append({"nombre": preview.anio.nombre, "accion": "reusada", "folder_id": anio_id})
        else:
            anio_id = drive_service.create_folder(drive, root_id, preview.anio.nombre)
            resultados.append({"nombre": preview.anio.nombre, "accion": "creada", "folder_id": anio_id})
    except Exception as exc:
        return ExecutionResult(
            items=resultados, campana_folder_id=None, error=f"Error creando '{preview.anio.nombre}': {exc}"
        )

    reutilizando_campana = decision.accion == "reusar" and preview.campana.existe
    try:
        if reutilizando_campana:
            campana_id = preview.campana.folder_id
            campana_nombre_final = preview.campana.nombre
            resultados.append({"nombre": campana_nombre_final, "accion": "reusada", "folder_id": campana_id})
        else:
            campana_nombre_final = decision.nombre_final
            campana_id = drive_service.create_folder(drive, anio_id, campana_nombre_final)
            resultados.append({"nombre": campana_nombre_final, "accion": "creada", "folder_id": campana_id})
    except Exception as exc:
        return ExecutionResult(
            items=resultados, campana_folder_id=None, error=f"Error creando '{campana_nombre_final}': {exc}"
        )

    for nombre_sub in subfolder_names:
        try:
            sub_id = None
            if reutilizando_campana:
                sub_id = drive_service.find_child_folder(drive, campana_id, nombre_sub)
            if sub_id is None:
                sub_id = drive_service.create_folder(drive, campana_id, nombre_sub)
                resultados.append({"nombre": nombre_sub, "accion": "creada", "folder_id": sub_id})
            else:
                resultados.append({"nombre": nombre_sub, "accion": "reusada", "folder_id": sub_id})
        except Exception as exc:
            return ExecutionResult(
                items=resultados, campana_folder_id=campana_id, error=f"Error creando '{nombre_sub}': {exc}"
            )

    return ExecutionResult(items=resultados, campana_folder_id=campana_id)

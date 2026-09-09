import click
import json
import pandas as pd
from src.db.connection import init_db
from src.hvac.constants import TIPOS_COMBUSTIBLE, TIPOS_TECNOLOGIA, FUENTES_DATOS_PERMITIDAS, FUENTES_VALIDAS
from src.hvac.repository import (
    CombustibleRepository,
    PrecioCombustibleRepository,
    TipoTecnologiaRepository,
    EquipoHVACRepository,
)
from src.hvac.matrix import calcular_matriz

init_db()


@click.group()
def cli():
    pass


@cli.group()
def combustible():
    pass


@combustible.command("create")
@click.option("--nombre", required=True, type=click.Choice(TIPOS_COMBUSTIBLE))
@click.option("--unidad", required=True)
@click.option("--pci", required=True, type=float)
@click.option("--pcs", required=True, type=float)
@click.option("--rendimiento", required=True, type=float)
@click.option("--unidades-por-gcal", required=True, type=float)
def combustible_create(nombre, unidad, pci, pcs, rendimiento, unidades_por_gcal):
    data = {"nombre": nombre, "unidad_medida": unidad, "pci": pci, "pcs": pcs,
            "rendimiento_transformacion": rendimiento, "unidades_por_gcal": unidades_por_gcal}
    result, errores = CombustibleRepository.create(data)
    if errores:
        click.echo(json.dumps({"error": errores}))
    else:
        click.echo(json.dumps({"id": result.id, "nombre": nombre}))


@combustible.command("list")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def combustible_list(fmt):
    rows = CombustibleRepository.list()
    if fmt == "json":
        click.echo(json.dumps(rows, indent=2))
    else:
        if not rows:
            click.echo("No hay combustibles registrados.")
            return
        headers = ["id", "nombre", "unidad_medida", "pci", "pcs", "rendimiento_transformacion", "unidades_por_gcal"]
        click.echo("\t".join(headers))
        for r in rows:
            click.echo("\t".join(str(r.get(h, "")) for h in headers))


@cli.group()
def precio():
    pass


@precio.command("add")
@click.option("--combustible-id", required=True, type=int)
@click.option("--region", required=True, type=int)
@click.option("--precio", required=True, type=float)
@click.option("--fecha-vigencia", required=True)
@click.option("--fuente", default="MANUAL",
              type=click.Choice(FUENTES_VALIDAS))
def precio_add(combustible_id, region, precio, fecha_vigencia, fuente):
    data = {"combustible_id": combustible_id, "region": region,
            "precio_por_unidad": precio, "fecha_vigencia": fecha_vigencia, "fuente": fuente}
    result, errores = PrecioCombustibleRepository.add(data)
    if errores:
        click.echo(json.dumps({"error": errores}))
    else:
        click.echo(json.dumps({"id": result.id}))


@precio.command("list")
@click.option("--combustible-id", type=int, default=None)
@click.option("--region", type=int, default=None)
def precio_list(combustible_id, region):
    rows = PrecioCombustibleRepository.list(combustible_id, region)
    click.echo(json.dumps(rows, indent=2))


@precio.command("fetch-cne")
@click.option("--combustible", required=True, type=click.Choice(TIPOS_COMBUSTIBLE))
@click.option("--region", required=True, type=int)
def precio_fetch_cne(combustible, region):
    from src.hvac.cne_fetcher import fetch_precio_cne
    result = fetch_precio_cne(combustible, region)
    click.echo(json.dumps(result))


@cli.group()
def equipo():
    pass


@equipo.command("create")
@click.option("--tipo-tecnologia-id", required=True, type=int)
@click.option("--combustible-id", required=True, type=int)
@click.option("--modelo", required=True)
@click.option("--potencia", required=True, type=float)
@click.option("--rendimiento", required=True, type=float)
@click.option("--costo-adquisicion", required=True, type=float)
@click.option("--tasa-consumo", required=True, type=float)
@click.option("--unidad-tasa", required=True)
@click.option("--costo-instalacion", type=float, default=0)
@click.option("--costo-mantencion", type=float, default=0)
@click.option("--fuente-datos", required=True)
@click.option("--url-fuente", default=None)
def equipo_create(tipo_tecnologia_id, combustible_id, modelo, potencia, rendimiento,
                  costo_adquisicion, tasa_consumo, unidad_tasa, costo_instalacion,
                  costo_mantencion, fuente_datos, url_fuente):
    data = {
        "tipo_tecnologia_id": tipo_tecnologia_id,
        "combustible_id": combustible_id,
        "modelo": modelo,
        "potencia_nominal_kw": potencia,
        "rendimiento_termico_pct": rendimiento,
        "costo_adquisicion_clp": costo_adquisicion,
        "tasa_consumo": tasa_consumo,
        "unidad_tasa_consumo": unidad_tasa,
        "costo_instalacion_clp": costo_instalacion,
        "costo_mantencion_anual_clp": costo_mantencion,
        "fuente_datos": fuente_datos,
        "url_fuente": url_fuente,
    }
    result, errores = EquipoHVACRepository.create(data)
    if errores:
        click.echo(json.dumps({"error": errores}))
    else:
        click.echo(json.dumps({"id": result.id, "modelo": modelo}))


@equipo.command("list")
@click.option("--tipo-tecnologia-id", type=int, default=None)
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def equipo_list(tipo_tecnologia_id, fmt):
    rows = EquipoHVACRepository.list(tipo_tecnologia_id)
    if fmt == "json":
        click.echo(json.dumps(rows, indent=2))
    else:
        if not rows:
            click.echo("No hay equipos registrados.")
            return
        headers = ["id", "modelo", "tecnologia_nombre", "combustible_nombre",
                   "potencia_nominal_kw", "rendimiento_termico_pct", "costo_adquisicion_clp"]
        click.echo("\t".join(headers))
        for r in rows:
            click.echo("\t".join(str(r.get(h, "")) for h in headers))


@equipo.command("update")
@click.argument("equipo_id", type=int)
@click.option("--modelo", default=None)
@click.option("--potencia", type=float, default=None)
@click.option("--rendimiento", type=float, default=None)
@click.option("--costo-adquisicion", type=float, default=None)
@click.option("--fuente-datos", default=None)
def equipo_update(equipo_id, modelo, potencia, rendimiento, costo_adquisicion, fuente_datos):
    data = {}
    if modelo:
        data["modelo"] = modelo
    if potencia:
        data["potencia_nominal_kw"] = potencia
    if rendimiento:
        data["rendimiento_termico_pct"] = rendimiento
    if costo_adquisicion:
        data["costo_adquisicion_clp"] = costo_adquisicion
    if fuente_datos:
        data["fuente_datos"] = fuente_datos
    result, errores = EquipoHVACRepository.update(equipo_id, data)
    if errores:
        click.echo(json.dumps({"error": errores}))
    else:
        click.echo(json.dumps(result))


@equipo.command("delete")
@click.argument("equipo_id", type=int)
@click.option("--force", is_flag=True)
def equipo_delete(equipo_id, force):
    if not force:
        click.confirm(f"Eliminar equipo {equipo_id}?", abort=True)
    ok = EquipoHVACRepository.delete(equipo_id)
    click.echo(json.dumps({"id": equipo_id, "deleted": ok}))


@equipo.command("import-csv")
@click.argument("archivo", type=click.Path(exists=True))
def equipo_import_csv(archivo):
    from src.hvac.csv_handler import importar_equipos
    importados, errores = importar_equipos(archivo)
    click.echo(json.dumps({"imported": importados, "errors": len(errores), "failed_rows": errores}))


@equipo.command("export")
@click.argument("archivo", type=click.Path())
def equipo_export(archivo):
    rows = EquipoHVACRepository.list()
    if not rows:
        click.echo(json.dumps({"error": "No hay equipos para exportar"}))
        return
    df = pd.DataFrame(rows)
    df.to_csv(archivo, index=False)
    click.echo(json.dumps({"exported": len(rows), "archivo": archivo}))


@cli.group()
def matrix():
    pass


@matrix.command("show")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def matrix_show(fmt):
    rows = calcular_matriz()
    if fmt == "json":
        click.echo(json.dumps(rows, indent=2))
    else:
        if not rows:
            click.echo("No hay datos para calcular la matriz.")
            return
        headers = ["equipo_id", "tecnologia", "combustible", "modelo",
                   "potencia_nominal_kw", "costo_fijo_anualizado_clp", "costo_variable_por_gcal"]
        click.echo("\t".join(headers))
        for r in rows:
            click.echo("\t".join(str(r.get(h, "")) for h in headers))


if __name__ == "__main__":
    cli()

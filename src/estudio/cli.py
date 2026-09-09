import click
import json
import pandas as pd
from src.db.connection import init_db
from src.estudio.repository import EstudioRepository, SimulacionRepository
from src.shared.csv_validator import validar_csv_headers, REQUIRED_COLUMNS

init_db()


@click.group()
def cli():
    pass


@cli.command()
@click.option("--nombre", default="Modelo Optimizacion Termico Chile", help="Nombre del estudio")
@click.option("--descripcion", default=None, help="Descripcion del estudio")
def estudio_init(nombre, descripcion):
    estudio_id = EstudioRepository.init(nombre, descripcion)
    click.echo(json.dumps({"id": estudio_id, "nombre": nombre, "fecha_creacion": "today"}))


@cli.command()
@click.option("--tipologia", required=True, type=click.Choice(
    ["aislada_1piso", "aislada_2pisos", "pareada_1piso", "pareada_2pisos"]
))
@click.option("--zona-termica", required=True, type=int)
@click.option("--u-prom", required=True, type=float)
@click.option("--demanda-anual", required=True, type=float)
@click.option("--peak-demanda", required=True, type=float)
@click.option("--gdc", required=True, type=float)
@click.option("--descripcion", default=None)
@click.option("--archivo-modelo", default=None)
def simulacion_create(tipologia, zona_termica, u_prom, demanda_anual, peak_demanda, gdc, descripcion, archivo_modelo):
    data = {
        "tipologia": tipologia,
        "zona_termica": zona_termica,
        "u_prom": u_prom,
        "demanda_anual_kwh": demanda_anual,
        "peak_demanda_kw": peak_demanda,
        "gdc": gdc,
        "descripcion": descripcion,
        "archivo_modelo": archivo_modelo,
    }
    result, errores = SimulacionRepository.create(data)
    if errores:
        click.echo(json.dumps({"error": "Error de validacion", "detalles": errores}))
    else:
        click.echo(json.dumps({"id": result.id, "tipologia": tipologia, "zona_termica": zona_termica}))


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def simulacion_list(fmt):
    rows = SimulacionRepository.list()
    if fmt == "json":
        click.echo(json.dumps(rows, indent=2))
    else:
        if not rows:
            click.echo("No hay simulaciones registradas.")
            return
        headers = ["id", "tipologia", "zona_termica", "u_prom", "demanda_anual_kwh", "peak_demanda_kw", "gdc"]
        click.echo("\t".join(headers))
        for r in rows:
            vals = [str(r.get(h, "")) for h in headers]
            click.echo("\t".join(vals))


@cli.command()
@click.argument("sim_id", type=int)
@click.option("--tipologia", default=None)
@click.option("--zona-termica", default=None, type=int)
@click.option("--u-prom", default=None, type=float)
@click.option("--demanda-anual", default=None, type=float)
@click.option("--peak-demanda", default=None, type=float)
@click.option("--gdc", default=None, type=float)
@click.option("--descripcion", default=None)
def simulacion_update(sim_id, tipologia, zona_termica, u_prom, demanda_anual, peak_demanda, gdc, descripcion):
    data = {k: v for k, v in {
        "tipologia": tipologia, "zona_termica": zona_termica,
        "u_prom": u_prom, "demanda_anual_kwh": demanda_anual,
        "peak_demanda_kw": peak_demanda, "gdc": gdc,
        "descripcion": descripcion,
    }.items() if v is not None}
    result, errores = SimulacionRepository.update(sim_id, data)
    if errores:
        click.echo(json.dumps({"error": "Error de validacion", "detalles": errores}))
    else:
        click.echo(json.dumps(result))


@cli.command()
@click.argument("sim_id", type=int)
@click.option("--force", is_flag=True, help="Eliminar sin confirmacion")
def simulacion_delete(sim_id, force):
    if not force:
        click.confirm(f"Eliminar simulacion {sim_id}?", abort=True)
    ok = SimulacionRepository.delete(sim_id)
    click.echo(json.dumps({"id": sim_id, "deleted": ok}))


@cli.command()
@click.argument("archivo", type=click.Path(exists=True))
def simulacion_import(archivo):
    df = pd.read_csv(archivo)
    valido, msg = validar_csv_headers(list(df.columns))
    if not valido:
        click.echo(json.dumps({"error": msg}))
        return
    simulaciones = df.to_dict("records")
    importados, errores = SimulacionRepository.bulk_create(simulaciones)
    click.echo(json.dumps({"imported": importados, "errors": len(errores), "failed_rows": errores}))


@cli.command()
@click.argument("archivo", type=click.Path())
def simulacion_export(archivo):
    rows = SimulacionRepository.list()
    if not rows:
        click.echo(json.dumps({"error": "No hay simulaciones para exportar"}))
        return
    df = pd.DataFrame(rows)
    df.to_csv(archivo, index=False)
    click.echo(json.dumps({"exported": len(rows), "archivo": archivo}))


if __name__ == "__main__":
    cli()

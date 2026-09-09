import click
import json
import pandas as pd
from src.db.connection import init_db
from src.optimizer.solver import ejecutar_optimizacion, ParametroRepository, ResultadoRepository

init_db()


@click.group()
def cli():
    pass


@cli.command()
def run():
    click.echo("Ejecutando optimizacion MILP...")
    resultado = ejecutar_optimizacion()
    click.echo(json.dumps(resultado, indent=2))


@cli.command()
@click.option("--tasa-descuento", type=float, default=None)
@click.option("--vida-util", type=int, default=None)
@click.option("--perdida-sistemica", type=float, default=None)
def config(tasa_descuento, vida_util, perdida_sistemica):
    if tasa_descuento is None and vida_util is None and perdida_sistemica is None:
        params = ParametroRepository.get()
        click.echo(json.dumps(params, indent=2))
        return
    params = ParametroRepository.update(
        tasa_descuento or 8.0,
        vida_util or 15,
        perdida_sistemica or 5.0,
    )
    click.echo(json.dumps(params, indent=2))


@cli.command()
@click.option("--zona", type=int, default=None)
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def results(zona, fmt):
    rows = ResultadoRepository.list(zona)
    if fmt == "json":
        click.echo(json.dumps(rows, indent=2))
    else:
        if not rows:
            click.echo("No hay resultados de optimizacion.")
            return
        headers = ["id", "zona_termica", "tipologia", "costo_anual_equivalente_clp", "timestamp"]
        click.echo("\t".join(headers))
        for r in rows:
            click.echo("\t".join(str(r.get(h, "")) for h in headers))


@cli.command()
@click.argument("archivo", type=click.Path())
def export(archivo):
    rows = ResultadoRepository.list()
    if not rows:
        click.echo(json.dumps({"error": "No hay resultados para exportar"}))
        return
    for r in rows:
        selecciones = ResultadoRepository.get_selecciones(r["id"])
        r["tecnologia_seleccionada"] = selecciones[0]["tecnologia_nombre"] if selecciones else ""
        r["combustible"] = selecciones[0]["combustible_nombre"] if selecciones else ""
        r["capacidad_kw"] = selecciones[0]["capacidad_asignada_kw"] if selecciones else 0
    df = pd.DataFrame(rows)
    df.to_csv(archivo, index=False, columns=[
        "zona_termica", "tipologia", "costo_anual_equivalente_clp",
        "tecnologia_seleccionada", "combustible", "capacidad_kw",
    ])
    click.echo(json.dumps({"exported": len(rows), "archivo": archivo}))


if __name__ == "__main__":
    cli()

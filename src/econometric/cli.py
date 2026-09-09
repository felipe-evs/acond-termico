import click
import json
from src.db.connection import init_db
from src.econometric.engine import ejecutar_modelo
from src.econometric.csv_export import exportar_resultados

init_db()


@click.group()
def cli():
    pass


@cli.command()
@click.option("--input", "archivo", required=True, type=click.Path(exists=True))
def run(archivo):
    click.echo("Ejecutando modelo econometrico...")
    resultado = ejecutar_modelo(archivo)
    click.echo(json.dumps(resultado, indent=2, default=str))


@cli.command()
def results():
    from src.db.connection import get_connection
    conn = get_connection()
    cur = conn.execute("SELECT * FROM eco_modelo ORDER BY id DESC LIMIT 1")
    modelo = cur.fetchone()
    if not modelo:
        click.echo("No hay modelo estimado.")
        conn.close()
        return
    click.echo(json.dumps(dict(modelo), indent=2))
    mid = modelo["id"]
    cur = conn.execute("SELECT * FROM eco_coeficiente WHERE modelo_id=?", (mid,))
    coefs = [dict(r) for r in cur.fetchall()]
    click.echo("\nCoeficientes:")
    click.echo(json.dumps(coefs, indent=2))
    cur = conn.execute("SELECT * FROM eco_test_diagnostico WHERE modelo_id=?", (mid,))
    tests = [dict(r) for r in cur.fetchall()]
    click.echo("\nTests:")
    click.echo(json.dumps(tests, indent=2))
    conn.close()


@cli.command()
@click.argument("archivo", type=click.Path())
def export(archivo):
    ok = exportar_resultados(archivo)
    if ok:
        click.echo(json.dumps({"exported": True, "archivo": archivo}))
    else:
        click.echo(json.dumps({"error": "No hay modelo para exportar"}))


if __name__ == "__main__":
    cli()

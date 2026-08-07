import typer

app = typer.Typer(help="Entertainment Tracker user administration helpers.")


@app.command()
def instructions() -> None:
    """Print the supported account-management path."""
    typer.echo(
        "Create the first owner in Supabase Auth, apply the bootstrap SQL from README.md, "
        "then use POST /api/v1/admin/users for additional accounts."
    )


if __name__ == "__main__":
    app()

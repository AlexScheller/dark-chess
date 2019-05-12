from dark_chess_app import create_app, cli

app = create_app()
cli.init(app)

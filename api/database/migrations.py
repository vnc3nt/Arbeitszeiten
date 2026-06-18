from flask_migrate import Migrate


migrate = Migrate(directory="./database/migrations", render_as_batch=True)

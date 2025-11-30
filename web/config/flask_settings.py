import os
import dotenv

env_file = dotenv.find_dotenv()
if env_file == '':
    print("No env file found")
    raise SystemExit(-1)
print(f"Using env file '{env_file}'")
dotenv.load_dotenv(verbose=True)

if (db_uri := os.environ.get("DB_URI")) is not None:
    SQLALCHEMY_DATABASE_URI = db_uri
else:
    # TODO legacy
    SQLALCHEMY_DATABASE_URI = "postgresql://{}.{}:{}@{}:{}/{}".format(
        os.environ.get("uname"),
        os.environ.get("db"),
        os.environ.get("password"),
        os.environ.get("host"),
        os.environ.get("port"),
        os.environ.get("scheme")
    )

BUNDLE_ERRORS = True
SECRET_KEY = os.urandom(40)
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Strict"
DEBUG=os.environ.get("DEBUG") == "True"

SQLALCHEMY_ECHO = DEBUG

SQLALCHEMY_NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


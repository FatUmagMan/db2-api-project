from litestar import Litestar

from app.controlers import AuthorController, BookController, ClientController, LoanController
from app.database import sqlalchemy_config

app = Litestar([AuthorController, BookController, ClientController, LoanController], debug=True, plugins=[sqlalchemy_config])
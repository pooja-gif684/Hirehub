from app.routes.api import api_blueprints
from app.routes.web import web_blueprints


def register_blueprints(app):
    for blueprint in web_blueprints + api_blueprints:
        app.register_blueprint(blueprint)

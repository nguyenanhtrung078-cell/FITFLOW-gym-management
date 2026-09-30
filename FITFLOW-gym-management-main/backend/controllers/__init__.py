from . import attendance, auth, members, packages, payments, reports, schedule


def register_blueprints(app):
    for module in (auth, members, packages, schedule, attendance, payments, reports):
        app.register_blueprint(module.bp)

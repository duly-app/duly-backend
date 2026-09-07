from src.app_factory import create_app
from src.environment import EnvVar, load_env_vars

env_vars = load_env_vars()
app = create_app(env_vars)


if __name__ == "src.app":
    app.run(debug=env_vars.get(EnvVar.FLASK_DEBUG, "") == "1")

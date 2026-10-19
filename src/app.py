from src.app_factory import create_app
from src.environment import EnvVar, load_env_vars
from src.logs import DEFAULT_LEVEL
from src.logs import configure as configure_logging
from src.service.sweeper_thread import start_sweeper

env_vars = load_env_vars()
configure_logging(env_vars.get(EnvVar.LOG_LEVEL) or DEFAULT_LEVEL)
app = create_app(env_vars)
start_sweeper(env_vars)


if __name__ == "src.app":
    app.run(debug=env_vars.get(EnvVar.FLASK_DEBUG, "") == "1")

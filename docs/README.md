# Flask – Project Documentation

## Overview

Flask is a lightweight and flexible **WSGI web application framework** for Python. It is designed to make getting started fast and easy, while providing the tools needed to build anything from a simple one-file script to a complex, modular application.

Flask is based on the **Werkzeug** WSGI toolkit and the **Jinja2** template engine. It includes:

- A built-in development server and interactive debugger.
- Integrated support for unit testing with `pytest`.
- RESTful request dispatching using URL routing.
- Secure session handling based on signed cookies.
- A pluggable architecture via blueprints, extensions, and application factories.
- Support for both synchronous and `async` view functions.

This repository contains the Flask core library (`src/flask`), its test suite (`tests`), Sphinx documentation configuration (`docs`), and several example applications (`examples`).

---

## Installation

### Runtime Dependencies

Flask requires Python 3.9 or newer. Its core dependencies are:

| Package       | Purpose                                    |
|---------------|--------------------------------------------|
| `Werkzeug`    | WSGI utilities, routing, and HTTP handling |
| `Jinja2`      | Template engine                            |
| `itsdangerous`| Cryptographically signed data (sessions)   |
| `click`       | CLI framework for the `flask` command      |
| `blinker`     | Signal support                             |
| `MarkupSafe`  | Safe HTML escaping in templates            |

Optional dependencies:

- `asgiref` – required to run `async` view functions.
- `python-dotenv` – required to load `.env` / `.flaskenv` files.

### Setting Up a Development Environment

The repository includes a devcontainer setup script (`.devcontainer/on-create-command.sh`) that prepares the environment. For a manual install:

```bash
# macOS / Linux
python3 -m venv --upgrade-deps .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
pip install -e .
pre-commit install --install-hooks
```

On Windows, activate the virtual environment with:

```powershell
.venv\Scripts\activate
```

### Installing from PyPI

For end users, Flask is available on PyPI:

```bash
pip install Flask
```

To enable `async` view support:

```bash
pip install "Flask[async]"
```

To enable `.env` file support:

```bash
pip install "Flask[dotenv]"
```

---

## Usage

### The `flask` Command-Line Interface

Flask provides a CLI entry point. After installing the project, you can run:

```bash
flask --app myapp run          # Start the development server
flask --app myapp shell        # Open an interactive Python shell
flask --app myapp routes       # List all registered URL routes
flask --app myapp --help       # Show help
```

Key CLI options:

- `-A, --app IMPORT` – module or file path of the Flask app or factory.
- `--debug / --no-debug` – toggle debug mode.
- `-e, --env-file PATH` – load environment variables from a file.
- `--version` – show Python, Flask, and Werkzeug versions.

### A Minimal Application

```python
# app.py
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"
```

Run it with:

```bash
flask --app app run
```

Or programmatically:

```python
if __name__ == "__main__":
    app.run(debug=True)
```

### Using the `Flask` Class as a WSGI Application

```python
from flask import Flask

app = Flask(__name__)

@app.get("/data")
def get_data():
    return {"message": "Hello"}
```

The `Flask` object is itself a WSGI application; it implements `__call__(environ, start_response)`.

### Using an Application Factory

A common production pattern is the application factory:

```python
# factory.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY="dev")

    @app.route("/")
    def index():
        return "Hello"

    return app
```

Load it with:

```bash
flask --app factory:create_app run
```

### Testing

Flask ships a test client. The repository's tests are run with `pytest`:

```bash
pytest
```

Example test:

```python
def test_hello(client):
    response = client.get("/")
    assert response.data == b"Hello, World!"
```

### Example Applications

The repository includes several runnable examples:

| Example            | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `examples/tutorial`| A complete blog application (`flaskr`) with auth, database setup, and tests.|
| `examples/celery`  | Integrating Flask with Celery for background task processing.               |
| `examples/javascript` | Demonstrates `fetch`, `xhr`, and `jQuery` frontends with Flask JSON APIs.    |

---

## API Reference

### Module: `src/flask/app.py` — The `Flask` Class

The central object of a Flask application. It implements a WSGI application, holds the URL map, view functions, configuration, template environment, and more.

#### `class Flask(App)`

**Constructor parameters:**

| Parameter                  | Type                          | Default     | Description                                                  |
|----------------------------|-------------------------------|-------------|--------------------------------------------------------------|
| `import_name`              | `str`                         | –           | Name of the application package (use `__name__`).           |
| `static_url_path`          | `str \| None`                 | `None`      | URL prefix for static files.                                 |
| `static_folder`            | `str \| os.PathLike \| None`  | `"static"`  | Folder containing static files, relative to `root_path`.     |
| `static_host`              | `str \| None`                 | `None`      | Host to use for the static route when `host_matching=True`.  |
| `host_matching`            | `bool`                        | `False`     | Enable host-based URL matching.                              |
| `subdomain_matching`       | `bool`                        | `False`     | Match subdomains relative to `SERVER_NAME`.                  |
| `template_folder`          | `str \| os.PathLike \| None`  | `"templates"` | Folder containing Jinja templates.                           |
| `instance_path`            | `str \| None`                 | `None`      | Absolute path to the instance folder.                        |
| `instance_relative_config` | `bool`                        | `False`     | Load config files relative to the instance path.             |
| `root_path`                | `str \| None`                 | `None`      | Root path of the application files; auto-detected normally.  |

**Key methods:**

- `route(rule, **options)` – decorator that registers a URL rule with a view function.
- `get(rule, **options)`, `post(rule, **options)`, `put`, `delete`, `patch` – method-specific route shortcuts.
- `add_url_rule(rule, endpoint=None, view_func=None, provide_automatic_options=None, **options)` – register a rule directly.
- `run(host=None, port=None, debug=None, load_dotenv=True, **options)` – start the built-in development server.
- `test_client(use_cookies=True, **kwargs)` – create a `FlaskClient` for unit tests.
- `test_cli_runner(**kwargs)` – create a `FlaskCliRunner` for testing CLI commands.
- `make_response(rv)` – convert a view return value into a `Response` object.
- `url_for(endpoint, _anchor=None, _method=None, _scheme=None, _external=None, **values)` – generate a URL for an endpoint.
- `app_context()` – create an `AppContext` (use as `with app.app_context():`).
- `test_request_context(*args, **kwargs)` – create a request context for testing.
- `request_context(environ)` – create a request context from a WSGI environ.
- `wsgi_app(environ, start_response)` – the actual WSGI application call.
- `before_request(f)`, `after_request(f)`, `teardown_request(f)` – register request lifecycle hooks.
- `teardown_appcontext(f)` – register a hook called when the app context pops.
- `errorhandler(code_or_exception)` – decorate a function as an error handler.
- `register_error_handler(code_or_exception, f)` – register an error handler programmatically.
- `context_processor(f)` – register a template context processor.
- `template_filter(name=None)`, `template_test(name=None)`, `template_global(name=None)` – register Jinja extensions.
- `ensure_sync(func)` – convert `async def` functions to synchronous for WSGI.
- `async_to_sync(func)` – run a coroutine function synchronously.
- `handle_http_exception(ctx, e)` / `handle_user_exception(ctx, e)` / `handle_exception(ctx, e)` – exception handling pipeline.

**Example:**

```python
from flask import Flask, request

app = Flask(__name__)

@app.route("/hello/<name>", methods=["GET"])
def hello(name):
    return f"Hello, {name}!"

with app.test_request_context("/hello/Flask"):
    assert request.method == "GET"
```

---

### Module: `src/flask/blueprints.py` — Blueprints

Blueprints allow you to organize an application into reusable modules, defining routes and other app behavior without the app object.

#### `class Blueprint(SansioBlueprint)`

**Constructor parameters:**

| Parameter         | Type                         | Default     | Description                                               |
|-------------------|------------------------------|-------------|-----------------------------------------------------------|
| `name`            | `str`                        | –           | Blueprint name. Must not contain dots.                    |
| `import_name`     | `str`                        | –           | Package/module name (usually `__name__`).                 |
| `static_folder`   | `str \| os.PathLike \| None` | `None`      | Static files folder for this blueprint.                    |
| `static_url_path` | `str \| None`                | `None`      | URL prefix for static files.                              |
| `template_folder` | `str \| os.PathLike \| None` | `None`      | Templates folder for this blueprint.                       |
| `url_prefix`      | `str \| None`                | `None`      | URL prefix applied to all routes in the blueprint.        |
| `subdomain`       | `str \| None`                | `None`      | Subdomain for all routes in the blueprint.                |
| `url_defaults`    | `dict \| None`               | `None`      | Default values for URL variables.                         |
| `root_path`       | `str \| None`                | `None`      | Manual root path.                                         |
| `cli_group`       | `str \| None`                | `_sentinel` | Name of the CLI group; `None` merges commands into `flask`.|

**Key methods:**

- `route(rule, **options)` and method shortcuts (`get`, `post`, `put`, `delete`, `patch`).
- `before_request(f)`, `after_request(f)`, `teardown_request(f)` – hooks scoped to requests handled by this blueprint.
- `before_app_request(f)`, `after_app_request(f)`, `teardown_app_request(f)` – hooks applied to every request of the app.
- `errorhandler(code_or_exception)` – error handlers scoped to the blueprint.
- `app_errorhandler(code_or_exception)` – error handlers applied to the whole app.
- `context_processor(f)`, `app_context_processor(f)` – template context processors.
- `url_defaults(f)`, `url_value_preprocessor(f)` and their app-wide variants.
- `app_template_filter(name)`, `app_template_test(name)`, `app_template_global(name)` – register app-wide Jinja extensions.
- `record(func)` / `record_once(func)` – defer registration callbacks.
- `register(app, options)` – called when the blueprint is registered on the app.
- `register_blueprint(blueprint, **options)` – nest blueprints inside blueprints.

**Example:**

```python
from flask import Blueprint, render_template

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
def index():
    return render_template("admin/index.html")

# In main app:
# app.register_blueprint(bp)
```

---

### Module: `src/flask/config.py` — Configuration

#### `class Config(dict)`

The configuration object is a dictionary subclass with additional loading methods.

| Method | Description |
|--------|-------------|
| `from_pyfile(filename, silent=False)` | Load config from a Python file. Only uppercase variable names are used. |
| `from_object(obj)` | Load config from a module/class or an import string. |
| `from_file(filename, load, silent=False, text=True)` | Load config from a JSON/TOML/other file via a `load` callable. |
| `from_envvar(variable_name, silent=False)` | Load config from a file path stored in an environment variable. |
| `from_mapping(mapping=None, **kwargs)` | Update config from a mapping, ignoring non-uppercase keys. |
| `from_prefixed_env(prefix="FLASK", loads=json.loads)` | Load environment variables starting with `FLASK_`; supports nested keys via `__`. |
| `get_namespace(namespace, lowercase=True, trim_namespace=True)` | Return a subset of options matching a namespace prefix. |

**Example:**

```python
app = Flask(__name__)
app.config.from_mapping(SECRET_KEY="dev")
app.config.from_prefixed_env()  # reads FLASK_* env variables
app.config.from_pyfile("config.py", silent=True)
```

---

### Module: `src/flask/ctx.py` — Contexts

Flask uses context variables to provide request-local and app-local data.

#### `class AppContext`

Represents an application and (optionally) request context. A combined app/request context is pushed for each request and CLI command.

- `push()` – make this context active.
- `pop(exc=None)` – make the context inactive and run teardown functions.
- `copy()` – create a copy of the context (used for background tasks).
- `match_request()` – perform URL routing for the request.
- Properties: `app`, `g`, `request`, `session`, `url_adapter`, `has_request`.

**Module-level functions:**

| Function | Description |
|----------|-------------|
| `after_this_request(f)` | Register a function to run after the *current* request only. |
| `copy_current_request_context(f)` | Decorate a function to run inside the active request context (e.g., in a background thread). |
| `has_request_context()` | Return `True` if a request context is active. |
| `has_app_context()` | Return `True` if an app context is active. |

**Example:**

```python
from flask import Flask, g, has_app_context

app = Flask(__name__)

with app.app_context():
    assert has_app_context()
    g.user = "flask"
    assert g.user == "flask"
```

---

### Module: `src/flask/globals.py` — Context Globals

Context-local proxy objects exposed at the top level of the `flask` package:

| Global | Type | Description |
|--------|------|-------------|
| `current_app` | proxy to `Flask` | The active application. |
| `app_ctx` | proxy to `AppContext` | The active context. |
| `g` | proxy to `_AppCtxGlobals` | Namespace for storing data during a request/app context. |
| `request` | proxy to `Request` | The current HTTP request. |
| `session` | proxy to `SessionMixin` | The current session. |

**Example:**

```python
from flask import request, session, g

@app.get("/")
def index():
    g.last_seen = request.path
    session["visits"] = session.get("visits", 0) + 1
    return g.last_seen
```

---

### Module: `src/flask/helpers.py` — Utility Functions

| Function | Description |
|----------|-------------|
| `url_for(endpoint, _anchor=None, _method=None, _scheme=None, _external=None, **values)` | Build a URL for an endpoint. |
| `redirect(location, code=303, Response=None)` | Create a redirect response. |
| `abort(code, *args, **kwargs)` | Raise an HTTP exception for a status code. |
| `flash(message, category="message")` | Store a message to show on the next request. |
| `get_flashed_messages(with_categories=False, category_filter=())` | Retrieve flashed messages. |
| `make_response(*args)` | Create a response object from view return values. |
| `send_file(path_or_file, mimetype=None, as_attachment=False, download_name=None, conditional=True, etag=True, last_modified=None, max_age=None)` | Send a file to the client. |
| `send_from_directory(directory, path, **kwargs)` | Safely send a file from within a directory. |
| `stream_with_context(generator_or_function)` | Run a response generator inside the current request context. |
| `get_template_attribute(template_name, attribute)` | Load a macro or variable exported by a template. |
| `get_debug_flag()` | Read the `FLASK_DEBUG` environment variable. |

---

### Module: `src/flask/sessions.py` — Session Interface

#### `class SessionMixin(MutableMapping)`

Mixin providing `permanent`, `modified`, `new`, and `accessed` session attributes.

#### `class SecureCookieSession(CallbackDict, SessionMixin)`

The default session object, backed by a signed cookie.

#### `class SessionInterface`

Base interface for session implementations:

- `open_session(app, request)` – load the session; return `None` to indicate failure.
- `save_session(app, session, response)` – persist the session (e.g., set a cookie).
- `make_null_session(app)` – create a null session when real sessions are unavailable.
- `is_null_session(obj)` – test if an object is a null session.
- `get_cookie_name(app)`, `get_cookie_domain(app)`, `get_cookie_path(app)`, `get_cookie_httponly(app)`, `get_cookie_secure(app)`, `get_cookie_samesite(app)`, `get_cookie_partitioned(app)` – derive cookie parameters from app config.
- `get_expiration_time(app, session)` – compute cookie expiry.
- `should_set_cookie(app, session)` – decide whether to send a `Set-Cookie` header.

#### `class SecureCookieSessionInterface(SessionInterface)`

The default implementation that stores sessions in signed cookies using `itsdangerous`. Supports the `SECRET_KEY_FALLBACKS` config key for key rotation.

---

### Module: `src/flask/json/` — JSON Support

Public helper functions:

- `flask.json.dumps(obj, **kwargs)` – serialize to JSON (uses the active app's provider).
- `flask.json.dump(obj, fp, **kwargs)` – serialize to a file.
- `flask.json.loads(s, **kwargs)` – deserialize JSON.
- `flask.json.load(fp, **kwargs)` – deserialize from a file.
- `flask.json.jsonify(*args, **kwargs)` – create a JSON response with `application/json` mimetype.

**Classes:**

- `JSONProvider(app)` – abstract base class for JSON providers. Subclasses implement `dumps` and `loads`. Also provides `dump`, `load`, and `response`.
- `DefaultJSONProvider(JSONProvider)` – uses Python's `json` module. Adds support for `datetime`/`date` (serialized as RFC 822 strings), `decimal.Decimal`, `uuid.UUID`, `dataclasses`, and objects with `__html__()`.
- `TaggedJSONSerializer` – compact serializer used for signed session data; supports `dict`, `tuple`, `bytes`, `Markup`, `UUID`, and `datetime` via tag classes.
- `JSONTag` – base class for custom tags in the tagged serializer.

**Example:**

```python
from flask import jsonify

@app.get("/health")
def health():
    return jsonify(status="ok", code=200)
```

---

### Module: `src/flask/templating.py` — Template Rendering

| Function | Description |
|----------|-------------|
| `render_template(template_name_or_list, **context)` | Render a template by name; a list renders the first existing name. |
| `render_template_string(source, **context)` | Render a template from a string. |
| `stream_template(template_name_or_list, **context)` | Render a template as a streaming iterator. |
| `stream_template_string(source, **context)` | Render a template string as a streaming iterator. |

**Classes:**

- `Environment(BaseEnvironment)` – Flask-aware Jinja environment.
- `DispatchingJinjaLoader(BaseLoader)` – searches the app's and blueprints' template folders.

---

### Module: `src/flask/views.py` — Class-Based Views

#### `class View`

Base class for class-based views.

- `dispatch_request(self, **kwargs)` – override to implement view behavior.
- `as_view(name, *class_args, **class_kwargs)` – classmethod that converts the class into a route-compatible view function.
- `methods` – allowed HTTP methods (defaults to `None`, i.e., `GET`, `HEAD`, `OPTIONS`).
- `decorators` – list of decorators applied to the generated view function.
- `provide_automatic_options` – controls automatic `OPTIONS` handling.
- `init_every_request` – if `False`, one class instance is reused for all requests.

#### `class MethodView(View)`

Dispatches HTTP methods to corresponding instance methods (`get`, `post`, `put`, `delete`, `patch`, etc.). `methods` is derived automatically from defined method names.

**Example:**

```python
from flask.views import MethodView

class CounterAPI(MethodView):
    def get(self):
        return {"count": 1}

    def post(self):
        return {"created": True}

app.add_url_rule("/api/counter", view_func=CounterAPI.as_view("counter"))
```

---

### Module: `src/flask/wrappers.py` — Request and Response

#### `class Request(RequestBase)`

Flask's default request object. Extends Werkzeug's request with:

- `url_rule` – the matched `Rule`, or `None`.
- `view_args` – dict of URL variables, or `None`.
- `routing_exception` – routing error if URL matching failed.
- `endpoint` – matched endpoint name (read-only).
- `blueprint` / `blueprints` – blueprint scope of the matched route.
- `max_content_length` / `max_form_memory_size` / `max_form_parts` – configurable request limits (defaults to app config `MAX_CONTENT_LENGTH`, `MAX_FORM_MEMORY_SIZE`, `MAX_FORM_PARTS`).
- `json_module` – points to `flask.json`.

#### `class Response(ResponseBase)`

Flask's default response object:

- Default mimetype is `text/html`.
- `json_module = flask.json`.
- `max_cookie_size` – reflects the `MAX_COOKIE_SIZE` config value.

---

### Module: `src/flask/cli.py` — Command-Line Interface

| Class / Function | Description |
|------------------|-------------|
| `FlaskGroup(AppGroup)` | The custom `click.Group` used by the `flask` command. Supports `-A/--app`, `--debug`, `-e/--env-file`. |
| `AppGroup(click.Group)` | A group whose `command` decorator automatically wraps callbacks with `@with_appcontext`. |
| `ScriptInfo` | Stores app import path / factory and loads the app lazily. |
| `find_best_app(module)` | Discovers the Flask app in a module by common names (`app`, `application`), a single Flask instance, or factory functions (`create_app`, `make_app`). |
| `locate_app(module_name, app_name, raise_if_not_found=True)` | Import and locate an app by module and optional name/expression. |
| `load_dotenv(path=None, load_defaults=True)` | Load `.flaskenv` / `.env` files via `python-dotenv`. |
| `with_appcontext(f)` | Decorator that guarantees an app context is active for a CLI callback. |
| `run_command` | `flask run` – development server command. Options: `--host`, `--port`, `--cert`, `--key`, `--reload/--no-reload`, `--debugger/--no-debugger`, `--with-threads/--without-threads`, `--extra-files`, `--exclude-patterns`. |
| `shell_command` | `flask shell` – interactive Python shell with app context. |
| `routes_command` | `flask routes` – list routes, with `--sort` and `--all-methods`. |

---

### Module: `src/flask/signals.py` — Signals

Flask uses the `blinker` library to provide the following core signals:

| Signal | Sent when |
|--------|-----------|
| `template_rendered` | A template has been rendered. |
| `before_render_template` | Before a template is rendered. |
| `request_started` | A request begins processing. |
| `request_finished` | A request finishes and the response is sent. |
| `request_tearing_down` | Request teardown runs. |
| `got_request_exception` | An unhandled exception occurs during a request. |
| `appcontext_tearing_down` | App context teardown runs. |
| `appcontext_pushed` | An app context is pushed. |
| `appcontext_popped` | An app context is popped. |
| `message_flashed` | A message is flashed. |

---

### Module: `src/flask/testing.py` — Testing Utilities

#### `class EnvironBuilder(werkzeug.test.EnvironBuilder)`

Builds a WSGI environ with defaults taken from the app (server name, application root, preferred URL scheme, JSON serialization settings).

#### `class FlaskClient(werkzeug.test.Client)`

The test client created by `app.test_client()`.

- Supports `with client:` blocks that preserve the request context.
- `session_transaction()` – context manager to modify the session within tests.
- `environ_base` – default environment values (`REMOTE_ADDR`, `HTTP_USER_AGENT`).
- `open(*args, buffered=False, follow_redirects=False, **kwargs)` – performs a request.

#### `class FlaskCliRunner(click.testing.CliRunner)`

Test runner for CLI commands, created by `app.test_cli_runner()`. Automatically provides a `ScriptInfo` for the app.

---

### Module: `src/flask/debughelpers.py` — Debug Assistance

| Class / Function | Description |
|------------------|-------------|
| `UnexpectedUnicodeError` | Raised when unexpected unicode/binary data is encountered. |
| `DebugFilesKeyError` | Provides a helpful error when accessing a missing file key in `request.files` in debug mode. |
| `FormDataRoutingRedirect` | Raised in debug mode when a routing redirect would drop form data (for methods other than `GET`/`HEAD`/`OPTIONS` and non-307/308 status codes). |
| `explain_template_loading_attempts(...)` | Logs detailed template-loader search attempts when `EXPLAIN_TEMPLATE_LOADING` is enabled. |

---

### Module: `src/flask/logging.py` — Logging

| Function | Description |
|----------|-------------|
| `create_logger(app)` | Creates and configures the app logger. |
| `has_level_handler(logger)` | Checks whether any handler in the logger chain can handle the effective level. |
| `wsgi_errors_stream` | A `LocalProxy` resolving to `wsgi.errors` during a request, or `sys.stderr` otherwise. |
| `default_handler` | The default `StreamHandler` attached to app loggers. |

---

## Contributing

Contributions to Flask are welcome. The project follows the guidelines of the Pallets organization.

### Getting Started

1. **Fork and clone** the repository.
2. Set up a development environment as described under [Installation](#installation).
3. Create a feature branch:

   ```bash
   git checkout -b my-feature
   ```

### Code Quality

- Run the test suite:

  ```bash
  pytest
  ```

- Run the linter/type checker configured for the project (e.g., `ruff`, `mypy`).
- The repository uses **pre-commit**. Install the hooks with:

  ```bash
  pre-commit install --install-hooks
  ```

### Submitting Changes

- Keep changes focused and well-tested.
- Add or update tests in the `tests/` directory.
- Update documentation in `docs/` if behavior or APIs change.
- Open a pull request against the `main` branch.

---

## License

The project is developed and maintained by **Pallets** (copyright 2010 Pallets, as stated in `docs/conf.py`).

**License:** Not explicitly included in the provided file snapshot, but Flask is officially released under the **BSD-3-Clause license**. For the full license text, refer to the Flask repository or the official website: <https://flask.palletsprojects.com/license/>.
"""
The Flutter web fallback route must only ever serve files inside the web
build directory. Encoded dot segments ("/%2E%2E/...") used to walk out of it
and return any readable file, including .env and /proc/self/environ.
"""
import pytest
from fastapi.testclient import TestClient

import backend.app.main as main_module

SECRET = "TRAVERSAL-PROBE-SECRET"


@pytest.fixture
def spa_client(tmp_path):
    web = tmp_path / "frontend" / "build" / "web"
    web.mkdir(parents=True)
    (web / "index.html").write_text("<html>spa</html>")
    (web / "main.dart.js").write_text("console.log('app')")
    (tmp_path / "secret.txt").write_text(SECRET)

    source = open(main_module.__file__, encoding="utf-8").read()
    marker = 'frontend_web_dir = os.path.join('
    start = source.index(marker)
    end = source.index("\n", start)
    source = source[:start] + f"frontend_web_dir = {str(web)!r}" + source[end:]
    namespace = {"__name__": "spa_probe", "__file__": main_module.__file__}
    exec(compile(source, "spa_probe", "exec"), namespace)
    return TestClient(namespace["app"])


@pytest.mark.parametrize("path", [
    "/%2E%2E/%2E%2E/%2E%2E/secret.txt",
    "/%2e%2e/%2e%2e/%2e%2e/secret.txt",
    "/..%2F..%2F..%2Fsecret.txt",
    "/assets/%2E%2E/%2E%2E/%2E%2E/%2E%2E/secret.txt",
])
def test_spa_fallback_never_serves_files_outside_web_build(spa_client, path):
    res = spa_client.get(path)
    assert SECRET not in res.text


def test_spa_fallback_still_serves_build_files_and_index(spa_client):
    assert "console.log" in spa_client.get("/main.dart.js").text
    assert "<html>spa</html>" in spa_client.get("/citizen/report").text

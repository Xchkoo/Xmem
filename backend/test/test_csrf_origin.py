"""
CSRF Origin 校验测试。

背景：安卓端使用 Capacitor 打包，页面跑在 WebView 内的 https://localhost，
跨域请求的 Origin 会被固定成 https://localhost。若部署环境把
CSRF_TRUSTED_ORIGINS 限制为只允许主域名，登录等写请求会被 403 拦截，
表现为"网页端正常、安卓端无法登录"。
"""
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import NATIVE_WEBVIEW_ORIGINS, app, get_csrf_trusted_origins, normalize_origin


@pytest.fixture
def client():
    """创建并在用例结束后正确关闭 TestClient。"""
    with TestClient(app) as c:
        yield c


def _post_login(client: TestClient, origin: str):
    """带上 Origin 与转发协议头发起一次登录请求（凭据故意无效）。"""
    return client.post(
        "/auth/login",
        json={"email": "csrf-probe@example.com", "password": "Not_a_real_password_1"},
        headers={"Origin": origin, "X-Forwarded-Proto": "https"},
    )


class TestCsrfTrustedOrigins:
    def test_native_webview_origins_always_trusted(self, monkeypatch):
        """即使环境变量只允许主域名，App 内置 WebView 的 Origin 依然可信。"""
        monkeypatch.setattr(settings, "csrf_trusted_origins", "https://xmem.top")
        trusted = get_csrf_trusted_origins()

        assert "https://xmem.top" in trusted
        for origin in NATIVE_WEBVIEW_ORIGINS:
            assert origin in trusted

    def test_origin_normalized_before_compare(self, monkeypatch):
        """大小写、末尾斜杠等写法差异不应影响白名单匹配。"""
        monkeypatch.setattr(settings, "csrf_trusted_origins", "https://xmem.top")
        trusted = get_csrf_trusted_origins()

        assert normalize_origin("HTTPS://LOCALHOST/") in trusted
        assert normalize_origin("capacitor://localhost/") in trusted

    def test_unrelated_origin_still_rejected(self, monkeypatch):
        """白名单外的站点仍然被拒绝，避免修复被放宽成"任意 Origin 放行"。"""
        monkeypatch.setattr(settings, "csrf_trusted_origins", "https://xmem.top")
        assert normalize_origin("https://evil.example.com") not in get_csrf_trusted_origins()


@pytest.mark.integration
class TestCsrfMiddleware:
    def test_android_webview_origin_passes_csrf(self, client: TestClient, monkeypatch):
        """安卓 WebView 的 Origin 不再被 CSRF 中间件拦截：凭据无效时返回 401 而不是 403。"""
        monkeypatch.setattr(settings, "csrf_trusted_origins", "https://xmem.top")
        resp = _post_login(client, "https://localhost")

        assert resp.status_code != 403, resp.text

    def test_ios_webview_origin_passes_csrf(self, client: TestClient, monkeypatch):
        """iOS（capacitor://localhost）同样不被拦截。"""
        monkeypatch.setattr(settings, "csrf_trusted_origins", "https://xmem.top")
        resp = _post_login(client, "capacitor://localhost")

        assert resp.status_code != 403, resp.text

    def test_untrusted_origin_returns_403(self, client: TestClient, monkeypatch):
        """白名单外的 Origin 仍然返回 403。"""
        monkeypatch.setattr(settings, "csrf_trusted_origins", "https://xmem.top")
        resp = _post_login(client, "https://evil.example.com")

        assert resp.status_code == 403
        assert "CSRF" in resp.json()["detail"]
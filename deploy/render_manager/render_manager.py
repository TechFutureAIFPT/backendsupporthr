import os
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

RENDER_API_KEY = os.environ.get("RENDER_API_KEY", "")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Render Service Manager</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f6f8;
            color: #333;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            color: #4a5568;
            margin-top: 0;
            border-bottom: 2px solid #edf2f7;
            padding-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-live { background-color: #c6f6d5; color: #22543d; }
        .status-suspended { background-color: #feebc8; color: #744210; }
        .status-building { background-color: #e2e8f0; color: #4a5568; }
        .status-error { background-color: #fed7d7; color: #742a2a; }
        
        .service-card {
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        }
        .service-card:hover {
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-color: #cbd5e0;
        }
        .service-info h3 {
            margin: 0 0 5px 0;
            color: #2d3748;
        }
        .service-info p {
            margin: 0;
            font-size: 14px;
            color: #718096;
        }
        .btn {
            background-color: #3182ce;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }
        .btn:hover {
            background-color: #2b6cb0;
        }
        .btn-deploy {
            background-color: #38a169;
        }
        .btn-deploy:hover {
            background-color: #2f855a;
        }
        .alert {
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .alert-error {
            background-color: #fed7d7;
            color: #9b2c2c;
            border: 1px solid #feb2b2;
        }
        .alert-success {
            background-color: #c6f6d5;
            color: #22543d;
            border: 1px solid #9ae6b4;
        }
        .refresh-btn {
            background-color: #4a5568;
            font-size: 14px;
        }
        .refresh-btn:hover {
            background-color: #2d3748;
        }
        .key-input-form {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .key-input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #cbd5e0;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <span>Render Service Manager</span>
            <button onclick="location.reload()" class="btn refresh-btn">Tải lại danh sách</button>
        </h1>

        {alert_placeholder}

        {key_form_placeholder}

        <div id="services-list">
            {services_placeholder}
        </div>
    </div>

    <script>
        function triggerDeploy(serviceId) {
            if (!confirm("Bạn có chắc chắn muốn deploy lại service này không?")) return;
            
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/deploy';
            
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'service_id';
            input.value = serviceId;
            
            form.appendChild(input);
            document.body.appendChild(form);
            form.submit();
        }
    </script>
</body>
</html>
"""

class RenderManagerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence default logs to keep docker stdout clean
        pass

    def _get_api_key(self):
        # Try to read from cookie first
        cookie_header = self.headers.get('Cookie', '')
        if 'render_key=' in cookie_header:
            parts = cookie_header.split('render_key=')
            if len(parts) > 1:
                return parts[1].split(';')[0]
        return RENDER_API_KEY

    def _fetch_services(self, api_key):
        if not api_key:
            return None, "Chưa cung cấp Render API Key."
            
        req = urllib.request.Request(
            "https://api.render.com/v1/services?limit=20",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8')), None
        except urllib.error.HTTPError as e:
            return None, f"Lỗi API Render (HTTP {e.code}): {e.reason}"
        except Exception as e:
            return None, f"Lỗi kết nối: {str(e)}"

    def _trigger_deploy(self, api_key, service_id):
        if not api_key:
            return False, "Chưa cung cấp Render API Key."
            
        req = urllib.request.Request(
            f"https://api.render.com/v1/services/{service_id}/deploys",
            data=b"{}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return True, "Đã gửi yêu cầu Deploy thành công!"
        except urllib.error.HTTPError as e:
            try:
                err_data = json.loads(e.read().decode('utf-8'))
                err_msg = err_data.get("message", e.reason)
            except:
                err_msg = e.reason
            return False, f"Không thể deploy (HTTP {e.code}): {err_msg}"
        except Exception as e:
            return False, f"Lỗi kết nối: {str(e)}"

    def do_GET(self):
        api_key = self._get_api_key()
        services, err = self._fetch_services(api_key)

        alert_html = ""
        if err:
            alert_html = f'<div class="alert alert-error"><strong>Lỗi:</strong> {err}</div>'

        # Create key form if not set in system env
        key_form_html = ""
        if not RENDER_API_KEY:
            key_form_html = f"""
            <form class="key-input-form" method="POST" action="/save-key">
                <input type="password" name="api_key" class="key-input" placeholder="Nhập Render API Key của bạn tại đây..." value="{api_key}">
                <button type="submit" class="btn">Lưu Key</button>
            </form>
            """

        services_html = ""
        if services:
            for item in services:
                srv = item.get("service", {})
                srv_id = srv.get("id")
                name = srv.get("name")
                srv_type = srv.get("type", "unknown")
                state = srv.get("state", "unknown")
                repo = srv.get("repo", "")
                
                status_class = "status-building"
                if state == "suspended":
                    status_class = "status-suspended"
                elif state in ("started", "live", "active"):
                    status_class = "status-live"
                elif state == "failed":
                    status_class = "status-error"

                services_html += f"""
                <div class="service-card">
                    <div class="service-info">
                        <h3>{name} <span class="status-badge {status_class}">{state}</span></h3>
                        <p>ID: <code>{srv_id}</code> | Type: <strong>{srv_type}</strong></p>
                        <p style="font-size: 12px; margin-top: 5px;">Repo: {repo}</p>
                    </div>
                    <div>
                        <button onclick="triggerDeploy('{srv_id}')" class="btn btn-deploy">Deploy Lại</button>
                    </div>
                </div>
                """
        else:
            if not err:
                services_html = "<p style='text-align: center; color: #718096;'>Không tìm thấy dịch vụ nào trên Render.</p>"

        # Render HTML
        response_html = HTML_TEMPLATE.format(
            alert_placeholder=alert_html,
            key_form_placeholder=key_form_html,
            services_placeholder=services_html
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(response_html.encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse simple form urlencoded
        params = {}
        for pair in post_data.split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                import urllib.parse
                params[urllib.parse.unquote(k)] = urllib.parse.unquote(v)

        api_key = self._get_api_key()

        if self.path == '/save-key':
            new_key = params.get('api_key', '').strip()
            self.send_response(303)
            self.send_header('Set-Cookie', f'render_key={new_key}; Path=/; HttpOnly')
            self.send_header('Location', '/')
            self.end_headers()
            return

        elif self.path == '/deploy':
            service_id = params.get('service_id', '')
            success, msg = self._trigger_deploy(api_key, service_id)
            
            alert_html = ""
            if success:
                alert_html = f'<div class="alert alert-success"><strong>Thành công:</strong> {msg}</div>'
            else:
                alert_html = f'<div class="alert alert-error"><strong>Lỗi:</strong> {msg}</div>'
                
            services, _ = self._fetch_services(api_key)
            services_html = ""
            if services:
                for item in services:
                    srv = item.get("service", {})
                    srv_id = srv.get("id")
                    name = srv.get("name")
                    srv_type = srv.get("type")
                    state = srv.get("state")
                    repo = srv.get("repo", "")
                    status_class = "status-live" if state in ("started", "live", "active") else "status-suspended" if state == "suspended" else "status-building"
                    services_html += f"""
                    <div class="service-card">
                        <div class="service-info">
                            <h3>{name} <span class="status-badge {status_class}">{state}</span></h3>
                            <p>ID: <code>{srv_id}</code> | Type: <strong>{srv_type}</strong></p>
                            <p style="font-size: 12px; margin-top: 5px;">Repo: {repo}</p>
                        </div>
                        <div>
                            <button onclick="triggerDeploy('{srv_id}')" class="btn btn-deploy">Deploy Lại</button>
                        </div>
                    </div>
                    """
            
            # Form
            key_form_html = ""
            if not RENDER_API_KEY:
                key_form_html = f"""
                <form class="key-input-form" method="POST" action="/save-key">
                    <input type="password" name="api_key" class="key-input" placeholder="Nhập Render API Key..." value="{api_key}">
                    <button type="submit" class="btn">Lưu Key</button>
                </form>
                """

            response_html = HTML_TEMPLATE.format(
                alert_placeholder=alert_html,
                key_form_placeholder=key_form_html,
                services_placeholder=services_html
            )
            
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(response_html.encode('utf-8'))
            return

        # Redirect to home for any other paths
        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()

def run(port=9090):
    server_address = ('', port)
    httpd = HTTPServer(server_address, RenderManagerHandler)
    print(f"Starting Render Manager server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    run()

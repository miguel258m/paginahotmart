#!/usr/bin/env python3
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os, re

class Handler(SimpleHTTPRequestHandler):

    def do_POST(self):
        if self.path == '/upload-icon':
            try:
                content_type = self.headers.get('Content-Type', '')
                # Extraer boundary
                boundary_match = re.search(r'boundary=(.+)', content_type)
                if not boundary_match:
                    self._respond(400, b'{"error":"no boundary"}')
                    return

                boundary = boundary_match.group(1).strip().encode()
                length   = int(self.headers.get('Content-Length', 0))
                body     = self.rfile.read(length)

                # Buscar los datos del archivo entre los boundaries
                # Formato: --boundary\r\nHeaders\r\n\r\nDATA\r\n--boundary--
                parts = body.split(b'--' + boundary)
                image_data = None
                for part in parts:
                    if b'filename=' in part and b'Content-Type' in part:
                        # Separar headers del contenido
                        header_end = part.find(b'\r\n\r\n')
                        if header_end != -1:
                            image_data = part[header_end + 4:]
                            # Quitar \r\n del final
                            if image_data.endswith(b'\r\n'):
                                image_data = image_data[:-2]
                            break

                if image_data and len(image_data) > 0:
                    base = os.path.dirname(os.path.abspath(__file__))
                    # Guardar como TODOS los íconos para reemplazar el logo en notificaciones Y en la app
                    for fname in ['custom-icon.png','icon-72.png','icon-96.png','icon-128.png','icon-144.png','icon-152.png','icon-192.png','icon-512.png']:
                        with open(os.path.join(base, fname), 'wb') as f:
                            f.write(image_data)
                    print(f"✅ Logo guardado en todos los íconos: {len(image_data)} bytes")
                    self._respond(200, b'{"success":true,"url":"/custom-icon.png"}')
                else:
                    self._respond(400, b'{"error":"no image data"}')

            except Exception as e:
                print(f"❌ Error: {e}")
                self._respond(500, f'{{"error":"{e}"}}'.encode())
        else:
            self._respond(404, b'{"error":"not found"}')

    def _respond(self, code, body):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} - {fmt % args}")

if __name__ == '__main__':
    import os as _os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = int(_os.environ.get('PORT', 8080))
    print(f"✅ Servidor corriendo en http://0.0.0.0:{port}")
    print(f"📁 Carpeta: {os.getcwd()}")
    HTTPServer(('', port), Handler).serve_forever()

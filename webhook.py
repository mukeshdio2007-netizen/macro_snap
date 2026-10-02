from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 5000

class TwilioWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        print(f"[MacroSnap Webhook] Incoming message: {post_data}")
        
        twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>🥗 Welcome to MacroSnap! Your message has been received. Open http://localhost:8501 to track your meals and view your daily calorie &amp; macro breakdown!</Message>
</Response>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/xml')
        self.send_header('Content-Length', str(len(twiml_response.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(twiml_response.encode('utf-8'))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>MacroSnap Twilio Webhook is Active!</h1>")

if __name__ == "__main__":
    print(f"Starting MacroSnap Webhook Server on port {PORT}...")
    server = HTTPServer(('0.0.0.0', PORT), TwilioWebhookHandler)
    server.serve_forever()

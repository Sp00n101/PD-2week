import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import psycopg2

DB_HOST = 'localhost'
DB_NAME = 'PD-TODO'
DB_USER = 'postgres'
DB_PASSWORD = 'root'

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/tasks':
            self.get_all_tasks()
        elif self.path.startswith('/tasks/'):
            task_id = self.path.split('/')[-1]
            self.get_task(task_id)

    def do_POST(self):
        if self.path == '/tasks':
            self.add_task()

    def do_PUT(self):
        if self.path == '/tasks':
            self.update_task()

    def do_DELETE(self):
        if self.path == '/tasks':
            self.delete_task()

    def connect_db(self):
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

    def get_all_tasks(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks;")
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(tasks).encode('utf-8'))

    def get_task(self, task_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = %s;", (task_id,))
        task = cursor.fetchone()
        cursor.close()
        conn.close()

        if task:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(task).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def add_task(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        data = json.loads(body)

        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (description) VALUES (%s) RETURNING id;", (data['description'],))
        task_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        self.send_response(201)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'id': task_id}).encode('utf-8'))

    def update_task(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        data = json.loads(body)

        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = %s WHERE id = %s;", (data['status'], data['id']))
        conn.commit()
        cursor.close()
        conn.close()

        self.send_response(200)
        self.end_headers()

    def delete_task(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        data = json.loads(body)

        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s;", (data['id'],))
        conn.commit()
        cursor.close()
        conn.close()

        self.send_response(204)
        self.end_headers()

def run(server_class=HTTPServer, handler_class=RequestHandler, port=1000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()

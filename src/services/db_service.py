import sys
import os
import psycopg2
import uuid
from urllib.parse import urlparse

class DbService:
    def __init__(self):
        parameters = urlparse(os.environ['PG_CONNECTION_URI'])
        self.db = psycopg2.connect(
            database = parameters.path[1:],
            user = parameters.username,
            password = parameters.password,
            host = parameters.hostname)
        self.db.autocommit = True

    def execute_sql(self, query, *args):
        cursor = self.db.cursor()
        cursor.execute(query, tuple(args))
        cursor.close()
        return

    def execute_sql_with_response(self, query, *args):
        cursor = self.db.cursor()
        cursor.execute(query, tuple(args))
        return cursor.fetchall()

    def fetch_by(self, col, val):
        columns = ('uuid', 'url', 'status', 'created_at')
        query = 'SELECT uuid, url, status, created_at FROM photos WHERE {} = %s'.format(col)
        rows = self.execute_sql_with_response(query, val)
        return [dict(zip(columns, row)) for row in rows]

    def get_by_id(self, id):
        rows = self.fetch_by('uuid', id)
        if len(rows) > 0:
            return rows[0]
        return None

    def get_by_status(self, status):
        return self.fetch_by('status', status)

    def add_thumbnail(self, id, width, height, path):
        statement = """
INSERT INTO photo_thumbnails (photo_uuid, width, height, url)
VALUES (%s, %s, %s, %s)
ON CONFLICT(photo_uuid,width,height)
DO NOTHING;
"""
        self.execute_sql(
            statement,
            id,
            width,
            height,
            path)

    def set_status(self, id, new_status):
        self.execute_sql('UPDATE photos SET status = %s WHERE uuid = %s;',
            new_status,
            id)

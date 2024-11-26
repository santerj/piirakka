import requests
import sqlite3
import validators
import html

from pydantic import BaseModel


class Station(BaseModel):
    url: str
    description: str
    source: str

    def check(self) -> tuple[bool, str]:
        # TODO: double check these
        allowed_content_types = (
            'application/pls+xml',
            'audio/mpeg',
            'audio/x-scpls',
            'audio/aac',
            'audio/flac',
            'audio/ogg',
            'audio/vnd.wav',
            'audio/x-wav',
            'audio/x-ms-wax',
            'audio/x-pn-realaudio',
            'audio/x-pn-realaudio-plugin',
            'audio/x-realaudio',
            'audio/x-aac',
            'audio/x-ogg',
            'audio/webm',
        )
        # TODO: have to rethink the validator gates.
        # TODO: many servers have a working stream endpoint, but times out upon HEAD
        # TODO: also keep in mind server-side request forgery vuln
        try:
            # gate 1 - validate url
            validators.url(self.url)
        except validators.ValidationError:
            return False, "invalid url"

        try:
            # gates 2 + 3 - respond within timeout + have correct header
            r = requests.head(self.url, timeout=1)
            content_type = r.headers.get('content-type')
            if content_type not in allowed_content_types:
                return False, f"content-type {content_type} not allowed"
        except requests.exceptions.Timeout:
            return False, "connection timed out"
        
        if html.escape(self.url) != self.url or self.url.replace("'", "''") != self.url:
            # gate 4 - check if sanitization affects description
            return False, "invalid description"

        return True, "success"

    def create(self, db: str):
        # adds a new station to database
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO stations VALUES ('{self.url}', '{self.description}', 'custom')")
        conn.commit()
        conn.close()

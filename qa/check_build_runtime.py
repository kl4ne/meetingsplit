"""Fail closed for the approved development build runtime (not a CVE scanner)."""
import json
import platform
import sqlite3
import ssl
import struct
import sys

PYTHON = (3, 14, 10)
OPENSSL_MIN = (3, 5, 9)
SQLITE_MIN = (3, 50, 4)


def blockers(python, openssl, sqlite, bits):
    failures=[]
    if tuple(python[:3]) != PYTHON:
        failures.append('Python 3.14.10 is required')
    if tuple(openssl[:3]) < OPENSSL_MIN:
        failures.append('OpenSSL 3.5.9 or later is required')
    if tuple(sqlite[:3]) < SQLITE_MIN:
        failures.append('SQLite 3.50.4 or later is required')
    if bits != 64:
        failures.append('64-bit runtime is required')
    return failures


def main():
    failures=blockers(sys.version_info,ssl.OPENSSL_VERSION_INFO,sqlite3.sqlite_version_info,struct.calcsize('P')*8)
    print(json.dumps({'python':platform.python_version(),'openssl':ssl.OPENSSL_VERSION,
                      'sqlite':sqlite3.sqlite_version,'blockers':failures}))
    return 2 if failures else 0

if __name__=='__main__':
    raise SystemExit(main())

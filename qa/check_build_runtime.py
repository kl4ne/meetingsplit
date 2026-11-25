"""Fail closed for the approved development build runtime (not a CVE scanner)."""
import json
import platform
import re
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


def openssl_runtime_version(text):
    # Use the runtime version string and record the legacy tuple separately.
    match=re.fullmatch(r'OpenSSL (\d+)\.(\d+)\.(\d+)(?:\s+\d{1,2} [A-Za-z]{3} \d{4})?',text)
    if not match:
        return (0,0,0)
    return tuple(map(int,match.groups()))


def main():
    runtime=openssl_runtime_version(ssl.OPENSSL_VERSION)
    failures=blockers(sys.version_info,runtime,sqlite3.sqlite_version_info,struct.calcsize('P')*8)
    print(json.dumps({'python':platform.python_version(),'openssl':ssl.OPENSSL_VERSION,
                      'openssl_runtime_parsed':runtime,'openssl_legacy_tuple':ssl.OPENSSL_VERSION_INFO,
                      'sqlite':sqlite3.sqlite_version,'blockers':failures}))
    return 2 if failures else 0

if __name__=='__main__':
    raise SystemExit(main())

"""Optional user accounts: username + password, with sign-in tokens kept on the device.

Passwords are stored only as scrypt hashes (memory-hard, so guessing is slow even with a GPU).
Sign-in tokens are random; only their SHA-256 is stored, so a copy of the database can't be used to sign in.
WebSockets can't carry headers from a browser, so they use a one-time ticket that expires in 30 seconds.
"""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import time

DATABASE_PATH = os.path.join(os.environ.get("POLYLANG_DATA", "/data"), "accounts.sqlite3")
USERNAME = re.compile(r"[a-z0-9][a-z0-9_.-]{2,31}")
SHORTEST_PASSWORD = 8
SCRYPT_SETTINGS = {"n": 2 ** 15, "r": 8, "p": 1, "maxmem": 64 * 1024 * 1024, "dklen": 32}
TOKEN_LIFETIME_SECONDS = 180 * 24 * 3600
TICKET_LIFETIME_SECONDS = 30
FAILED_LOGINS_ALLOWED = 8
FAILED_LOGIN_WINDOW_SECONDS = 15 * 60
EMAIL = re.compile(r"[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s.]{2,24}")
RESET_CODE_LIFETIME_SECONDS = 15 * 60
RESET_CODE_TRIES_ALLOWED = 5
RESET_REQUESTS_ALLOWED_PER_HOUR = 5

_database_lock = threading.Lock()
_failed_logins = {}
_live_tickets = {}


class AccountError(Exception):
    pass


def _database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("""CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash BLOB NOT NULL,
        salt BLOB NOT NULL, created REAL NOT NULL)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS sign_ins (
        token_hash TEXT PRIMARY KEY, account_id INTEGER NOT NULL, created REAL NOT NULL, last_used REAL NOT NULL)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS password_resets (
        account_id INTEGER PRIMARY KEY, code_hash TEXT NOT NULL, expires REAL NOT NULL, tries_left INTEGER NOT NULL)""")
    columns = {row[1] for row in connection.execute("PRAGMA table_info(accounts)")}
    if "email" not in columns:
        connection.execute("ALTER TABLE accounts ADD COLUMN email TEXT")
    return connection


def _hash_password(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, **SCRYPT_SETTINGS)


def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _issue_token(connection, account_id):
    token = secrets.token_urlsafe(32)
    now = time.time()
    connection.execute("INSERT INTO sign_ins VALUES (?, ?, ?, ?)", (_hash_token(token), account_id, now, now))
    return token


def _check_not_locked_out(*keys):
    now = time.time()
    for key in keys:
        recent = [moment for moment in _failed_logins.get(key, []) if now - moment < FAILED_LOGIN_WINDOW_SECONDS]
        _failed_logins[key] = recent
        if len(recent) >= FAILED_LOGINS_ALLOWED:
            raise AccountError("Too many tries. Wait 15 minutes and try again.")


def _record_failure(*keys):
    for key in keys:
        _failed_logins.setdefault(key, []).append(time.time())


def normalise_email(email):
    email = (email or "").strip().lower()
    if email and not EMAIL.fullmatch(email):
        raise AccountError("That email address doesn't look right.")
    return email or None


def create_account(username, password, email=""):
    username = username.strip().lower()
    email = normalise_email(email)
    if not USERNAME.fullmatch(username):
        raise AccountError("Usernames are 3–32 letters, numbers, dots, dashes or underscores.")
    if len(password) < SHORTEST_PASSWORD:
        raise AccountError(f"Use a password of at least {SHORTEST_PASSWORD} characters.")
    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt)
    with _database_lock, _database() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO accounts (username, password_hash, salt, created, email) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, salt, time.time(), email))
        except sqlite3.IntegrityError:
            raise AccountError("That username is taken.")
        return {"username": username, "token": _issue_token(connection, cursor.lastrowid)}


def sign_in(username, password, client_key):
    username = username.strip().lower()
    _check_not_locked_out("user:" + username, "client:" + client_key)
    with _database_lock, _database() as connection:
        row = connection.execute("SELECT id, password_hash, salt FROM accounts WHERE username = ?", (username,)).fetchone()
        # Hash even for unknown usernames, so response time doesn't reveal which usernames exist.
        candidate = _hash_password(password, row[2] if row else b"no-such-account!")
        if not row or not hmac.compare_digest(candidate, row[1]):
            _record_failure("user:" + username, "client:" + client_key)
            raise AccountError("Wrong username or password.")
        return {"username": username, "token": _issue_token(connection, row[0])}


def account_for_token(token):
    if not token:
        return None
    with _database_lock, _database() as connection:
        row = connection.execute(
            "SELECT accounts.id, accounts.username, sign_ins.created, accounts.email FROM sign_ins"
            " JOIN accounts ON accounts.id = sign_ins.account_id WHERE token_hash = ?", (_hash_token(token),)).fetchone()
        if not row or time.time() - row[2] > TOKEN_LIFETIME_SECONDS:
            return None
        connection.execute("UPDATE sign_ins SET last_used = ? WHERE token_hash = ?", (time.time(), _hash_token(token)))
        return {"id": row[0], "username": row[1], "email": row[3]}


def set_email(account_id, email):
    email = normalise_email(email)
    with _database_lock, _database() as connection:
        connection.execute("UPDATE accounts SET email = ? WHERE id = ?", (email, account_id))
    return email


# ---------- forgot password: a 6-digit code sent by email ----------

_reset_requests = {}


def start_password_reset(email, client_key):
    """Returns (address, code) to send, or None. Callers reply the same either way, so this can't reveal who has an account."""
    email = (email or "").strip().lower()
    now = time.time()
    for key in ("email:" + email, "client:" + client_key):
        recent = [moment for moment in _reset_requests.get(key, []) if now - moment < 3600]
        _reset_requests[key] = recent + [now]
        if len(recent) >= RESET_REQUESTS_ALLOWED_PER_HOUR:
            return None
    with _database_lock, _database() as connection:
        row = connection.execute("SELECT id FROM accounts WHERE email = ?", (email,)).fetchone()
        if not row:
            return None
        code = f"{secrets.randbelow(10 ** 6):06d}"
        connection.execute("INSERT OR REPLACE INTO password_resets VALUES (?, ?, ?, ?)",
                           (row[0], _hash_token(f"{row[0]}:{code}"), now + RESET_CODE_LIFETIME_SECONDS, RESET_CODE_TRIES_ALLOWED))
        return email, code


def finish_password_reset(email, code, new_password):
    """Checks the code, sets the new password, signs out every device, and signs this one in."""
    if len(new_password) < SHORTEST_PASSWORD:
        raise AccountError(f"Use a password of at least {SHORTEST_PASSWORD} characters.")
    wrong = AccountError("That code is wrong or has expired. Ask for a new one.")
    email = (email or "").strip().lower()
    with _database_lock, _database() as connection:
        account = connection.execute("SELECT id, username FROM accounts WHERE email = ?", (email,)).fetchone()
        if not account:
            raise wrong
        reset = connection.execute("SELECT code_hash, expires, tries_left FROM password_resets WHERE account_id = ?",
                                   (account[0],)).fetchone()
        if not reset or reset[1] < time.time() or reset[2] <= 0:
            raise wrong
        if not hmac.compare_digest(reset[0], _hash_token(f"{account[0]}:{(code or '').strip()}")):
            connection.execute("UPDATE password_resets SET tries_left = tries_left - 1 WHERE account_id = ?", (account[0],))
            connection.commit()  # keep the used-up try: raising inside "with connection" would roll it back
            raise wrong
        salt = secrets.token_bytes(16)
        connection.execute("UPDATE accounts SET password_hash = ?, salt = ? WHERE id = ?",
                           (_hash_password(new_password, salt), salt, account[0]))
        connection.execute("DELETE FROM password_resets WHERE account_id = ?", (account[0],))
        connection.execute("DELETE FROM sign_ins WHERE account_id = ?", (account[0],))
        _failed_logins.pop("user:" + account[1], None)
        return {"username": account[1], "token": _issue_token(connection, account[0])}


def sign_out(token):
    with _database_lock, _database() as connection:
        connection.execute("DELETE FROM sign_ins WHERE token_hash = ?", (_hash_token(token or ""),))


def issue_live_ticket(person):
    now = time.time()
    for ticket, (_, expires_at) in list(_live_tickets.items()):
        if expires_at < now:
            del _live_tickets[ticket]
    ticket = secrets.token_urlsafe(24)
    _live_tickets[ticket] = (person, now + TICKET_LIFETIME_SECONDS)
    return ticket


def redeem_live_ticket(ticket):
    person, expires_at = _live_tickets.pop(ticket or "", (None, 0))
    return person if expires_at >= time.time() else None


def bearer_token(headers):
    value = headers.get("authorization") or ""
    return value[7:].strip() if value.lower().startswith("bearer ") else ""

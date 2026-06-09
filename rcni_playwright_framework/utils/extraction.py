# tests/sftp_connection_check.py

import socket
import traceback
import paramiko
from stat import S_ISDIR, S_ISREG
from datetime import datetime


# =========================
# CONFIG
# =========================
SFTP_HOST = ""
SFTP_PORT = 22

SFTP_USERNAME = "username"
SFTP_PASSWORD = "YOUR_PASSWORD"

REMOTE_DIR = "/archive/in/good/834"


def log(message: str):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def check_dns():
    log("DNS check started")

    ip = socket.gethostbyname(SFTP_HOST)

    log(f"DNS success: {SFTP_HOST} -> {ip}")
    return ip


def check_port():
    log(f"Port check started: {SFTP_HOST}:{SFTP_PORT}")

    sock = socket.create_connection((SFTP_HOST, SFTP_PORT), timeout=20)
    sock.close()

    log("Port check success")


def connect_sftp():
    log("SFTP connection started")

    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))

    transport.banner_timeout = 60
    transport.auth_timeout = 60
    transport.set_keepalive(30)

    log("Authenticating...")

    transport.connect(
        username=SFTP_USERNAME,
        password=SFTP_PASSWORD
    )

    log("Authentication successful")

    sftp = paramiko.SFTPClient.from_transport(transport)

    log("SFTP client created")

    return transport, sftp


def list_directory(sftp):
    log(f"Changing remote directory to: {REMOTE_DIR}")

    sftp.chdir(REMOTE_DIR)

    log(f"Current remote directory: {sftp.getcwd()}")

    log("Reading directory listing...")

    items = sftp.listdir_attr(".")

    log(f"Directory listing successful. Total items: {len(items)}")

    print("\nREMOTE DIRECTORY CONTENT")
    print("-" * 100)

    for item in items:
        if S_ISDIR(item.st_mode):
            item_type = "DIR "
        elif S_ISREG(item.st_mode):
            item_type = "FILE"
        else:
            item_type = "OTHER"

        print(f"{item_type} | {item.st_size:>12} bytes | {item.filename}")

    print("-" * 100)


def main():
    transport = None
    sftp = None

    log("SCRIPT STARTED")
    log("IMPORTANT: Close FileZilla before running this script.")
    log(f"Host: {SFTP_HOST}")
    log(f"Port: {SFTP_PORT}")
    log(f"Username: {SFTP_USERNAME}")
    log(f"Remote directory: {REMOTE_DIR}")

    try:
        check_dns()
        check_port()

        transport, sftp = connect_sftp()

        list_directory(sftp)

        log("SCRIPT COMPLETED SUCCESSFULLY")

    except Exception as e:
        log("ERROR OCCURRED")
        log(f"Error type: {type(e).__name__}")
        log(f"Error message: {repr(e)}")

        print("\nFULL TRACEBACK")
        print("-" * 100)
        traceback.print_exc()
        print("-" * 100)

    finally:
        log("Closing connections...")

        try:
            if sftp:
                sftp.close()
                log("SFTP client closed")
        except Exception as e:
            log(f"Error while closing SFTP client: {repr(e)}")

        try:
            if transport:
                transport.close()
                log("Transport closed")
        except Exception as e:
            log(f"Error while closing transport: {repr(e)}")

        log("SCRIPT FINISHED")


if __name__ == "__main__":
    main()

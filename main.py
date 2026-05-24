#!/usr/bin/env python3
"""Simple network monitor CLI.

Commands:
 - ip: show public and local IP
 - ping: ping a host
 - speed: run a speedtest (requires `speedtest-cli`)
 - status: online/offline check
 - monitor: periodic summary (loop)
"""
import argparse
import platform
import socket
import subprocess
import sys
import time


def get_public_ip(timeout=5):
	try:
		import requests
		r = requests.get("https://api.ipify.org", timeout=timeout)
		if r.ok:
			return r.text.strip()
	except Exception:
		return None


def get_local_ip():
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		ip = s.getsockname()[0]
		s.close()
		return ip
	except Exception:
		try:
			return socket.gethostbyname(socket.gethostname())
		except Exception:
			return None


def ping_host(host, count=4, timeout=4):
	system = platform.system().lower()
	if system == "windows":
		args = ["ping", "-n", str(count), "-w", str(int(timeout * 1000)), host]
	else:
		args = ["ping", "-c", str(count), "-W", str(int(timeout)), host]

	try:
		p = subprocess.run(args, capture_output=True, text=True)
		return p.returncode, p.stdout + p.stderr
	except FileNotFoundError:
		return 2, "ping command not found"
	except Exception as e:
		return 2, str(e)


def speed_test():
	try:
		import speedtest
	except Exception:
		return None, "speedtest module not installed"

	try:
		s = speedtest.Speedtest()
		s.get_best_server()
		dl = s.download()
		ul = s.upload(pre_allocate=False)
		ping = s.results.ping
		return {"download_mbps": dl / 1e6, "upload_mbps": ul / 1e6, "ping_ms": ping}, None
	except Exception as e:
		return None, str(e)


def check_online(timeout=3):
	try:
		socket.create_connection(("8.8.8.8", 53), timeout=timeout).close()
		return True
	except Exception:
		return False


def main(argv=None):
	parser = argparse.ArgumentParser(description="Network monitor utility")
	sub = parser.add_subparsers(dest="cmd")

	sp_ip = sub.add_parser("ip", help="Show public and local IP")

	sp_ping = sub.add_parser("ping", help="Ping a host")
	sp_ping.add_argument("host")
	sp_ping.add_argument("-c", "--count", type=int, default=4)

	sp_speed = sub.add_parser("speed", help="Run speedtest (requires speedtest-cli)")

	sp_status = sub.add_parser("status", help="Check online/offline status")

	sp_mon = sub.add_parser("monitor", help="Run periodic summary")
	sp_mon.add_argument("--interval", type=int, default=30, help="Seconds between checks")

	args = parser.parse_args(argv)

	if args.cmd == "ip":
		pub = get_public_ip()
		loc = get_local_ip()
		print("Public IP:", pub or "(unavailable)")
		print("Local IP:", loc or "(unavailable)")
		return 0

	if args.cmd == "ping":
		code, out = ping_host(args.host, count=args.count)
		print(out)
		return code

	if args.cmd == "speed":
		res, err = speed_test()
		if err:
			print("Error:", err)
			print("Install requirements: pip install -r requirements.txt")
			return 2
		print(f"Download: {res['download_mbps']:.2f} Mbps")
		print(f"Upload:   {res['upload_mbps']:.2f} Mbps")
		print(f"Ping:     {res['ping_ms']:.1f} ms")
		return 0

	if args.cmd == "status":
		online = check_online()
		print("Online" if online else "Offline")
		return 0

	if args.cmd == "monitor":
		try:
			while True:
				online = check_online()
				loc = get_local_ip() or "-"
				pub = get_public_ip() or "-"
				print(time.strftime("%Y-%m-%d %H:%M:%S"), end=" ")
				print("Online" if online else "Offline", end=" | ")
				print(f"Local: {loc}", end=" | ")
				print(f"Public: {pub}")
				time.sleep(args.interval)
		except KeyboardInterrupt:
			print("\nStopped monitor")
			return 0

	parser.print_help()
	return 1


if __name__ == "__main__":
	sys.exit(main())

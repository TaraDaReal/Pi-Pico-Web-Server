import os
import time
import ipaddress
import wifi # type: ignore
import socketpool # type: ignore
import board # type: ignore
import microcontroller # type: ignore
from digitalio import DigitalInOut, Direction # type: ignore
from adafruit_httpserver import Server, Request, Response, POST # type: ignore
import adafruit_requests # type: ignore
import sys

ctrlc = 0

connection = None

ssid = os.getenv('CIRCUITPY_WIFI_SSID')
passwd = os.getenv('CIRCUITPY_WIFI_PASSWORD')

# Configure onboard LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = False

ipv4 =  ipaddress.IPv4Address("192.168.68.198")
netmask =  ipaddress.IPv4Address("255.255.255.0")
gateway =  ipaddress.IPv4Address("192.168.1.1")
wifi.radio.set_ipv4_address(ipv4=ipv4,netmask=netmask,gateway=gateway)


pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static",debug=True)

font_family = "monospace"

htmlcache = {}

def cache_html(filename: str, contents: str):
    htmlcache[filename] = contents

def get_html(filename: str):
    return htmlcache[filename]

def preload_cache(htmldir: str):
    try:
        for filename in os.listdir(htmldir):
            if filename.endswith(".html"):
                with open(os.path.join(htmldir, filename), 'r') as f:
                    cache_html(filename, f.read())
    except OSError as e:
        print("Error preloading cache: ", e)

def serve_html(name: str, data: dict):
    if name in htmlcache:
        content = get_html(name)

        for var, val in data.items():
            content = content.replace("{{" + var + "}}", str(val))
        return str(content)


def is_connected():
    try:
        requests = adafruit_requests.Session(pool)
        response = requests.get("http://www.google.com", timeout=5)
        return True
    except (ValueError, RuntimeError):
        return False
    
def connectToWifi(skipCheck=False):
    if not skipCheck:
        if not is_connected():
            print("Connecting to wifi")
            while not is_connected():
                wifi.radio.connect(ssid, passwd)
                time.sleep(2)
            print(f"Connected to {ssid}")
            return
        return
    wifi.radio.connect(ssid, passwd)


@server.route("/")
def base(request: Request):
    return Response(request, serve_html('login.html', {'state': led.value}), content_type='text/html')

@server.route("/", methods=[POST])
def changeLED(request: Request):
    raw_text = request.raw_request.decode('utf-8')
    print(raw_text)
    if "TOGGLE" in raw_text:
        led.value = not led.value
        return Response(request, serve_html('index.html', {'state': led.value}), content_type='text/html')
    if "STOP_PICO" in raw_text:
        stopChip()
    if "username=admin" in raw_text and "password=admin" in raw_text:
        return Response(request, serve_html('index.html', {'state': led.value}), content_type='text/html')
        
    return Response(request, serve_html('login.html', {'state': led.value}), content_type='text/html')

def stopChip():
    print("Stopping")
    time.sleep(3)
    sys.exit()

connectToWifi(True)

print("Starting server")

try:
    server.start(str(wifi.radio.ipv4_address), 80)
    print(f"Listening on {ipv4}:80")
except OSError:
    time.sleep(5)
    print("Restarting")
    microcontroller.reset()
ping_addr = ipaddress.ip_address("8.8.4.4")

clock = time.monotonic()

while True:
    try:
        server.poll()
    except SystemExit:
        break
    except BaseException as e:
        print(e)
        continue
    


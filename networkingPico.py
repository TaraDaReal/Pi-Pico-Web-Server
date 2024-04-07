import os
import time
import ipaddress
import wifi
import socketpool
import board
import microcontroller
from digitalio import DigitalInOut, Direction
from adafruit_httpserver import Server, Request, Response, POST
import adafruit_requests
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

def webpage(name: str, vars: dict):
    path = "./webpage/" + name
    htmlF = open(path, 'r')
    html = htmlF.read()
    htmlF.close()

    for var, val in vars.items():
        html = html.replace("{{" + var + "}}", str(val))
    return str(html)

@server.route("/")
def base(request: Request):
    return Response(request, webpage('login.html', {'state': led.value}), content_type='text/html')

@server.route("/", methods=[POST])
def changeLED(request: Request):
    raw_text = request.raw_request.decode('utf-8')
    print(raw_text)
    if "TOGGLE" in raw_text:
        led.value = not led.value
        return Response(request, webpage('index.html', {'state': led.value}), content_type='text/html')
    if "STOP_PICO" in raw_text:
        stopChip()
    if "username=admin" in raw_text and "password=admin" in raw_text:
        return Response(request, webpage('index.html', {'state': led.value}), content_type='text/html')
        
    return Response(request, webpage('login.html', {'state': led.value}), content_type='text/html')

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
    


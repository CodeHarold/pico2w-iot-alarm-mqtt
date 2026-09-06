import machine
import utime
import network
import _thread
from umqtt.simple import MQTTClient
from buzzer import activate_buzzer

# ---------------------------------------------------------
# Wi-Fi configuration
# Replace these placeholders with your own local credentials.
# ---------------------------------------------------------
SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

# ---------------------------------------------------------
# HiveMQ Cloud configuration
# Use your own HiveMQ Cloud cluster hostname and credentials.
# ---------------------------------------------------------
MQTT_SERVER = "YOUR_HIVEMQ_CLUSTER_HOSTNAME"
MQTT_PORT = 8883
MQTT_USER = "YOUR_HIVEMQ_USERNAME"
MQTT_PASSWORD = "YOUR_HIVEMQ_PASSWORD"

MQTT_TOPIC = b"IoTAlarm"

pir = machine.Pin(26, machine.Pin.IN)
led = machine.Pin(21, machine.Pin.OUT)
wlan = network.WLAN(network.STA_IF)
mqtt_client = None


def connect_wifi():
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        print("Trying to connect to wifi...")
        utime.sleep(5)

    print("WIFI connection established")


def sub_iotalarm(topic, msg):
    print((topic, msg))

    if topic == MQTT_TOPIC and msg == b"motion":
        print("Motion detected! Activate buzzer...")
        activate_buzzer()


def motion_handler(pin):
    print("Motion detected!!")

    if mqtt_client is not None:
        mqtt_client.publish(MQTT_TOPIC, b"motion")
    else:
        print("MQTT Client is not connected")


def connect_mqtt(device_id, callback):
    global mqtt_client

    while mqtt_client is None:
        try:
            print("Trying to MQTT Server...")

            mqtt_client = MQTTClient(
                device_id,
                MQTT_SERVER,
                user=MQTT_USER,
                password=MQTT_PASSWORD,
                port=MQTT_PORT,
                ssl=True,
                ssl_params={"server_hostname": MQTT_SERVER},
            )

            mqtt_client.set_callback(callback)
            mqtt_client.connect()
            print("MQTT connection established")

        except Exception as e:
            mqtt_client = None
            print("Failed to connect:", e)
            utime.sleep(5)


def connection_status():
    while True:
        if wlan.isconnected():
            if mqtt_client is not None:
                led.on()
            else:
                led.on()
                utime.sleep(0.5)
                led.off()
                utime.sleep(0.5)
        else:
            led.on()
            utime.sleep(1)
            led.off()
            utime.sleep(1)


_thread.start_new_thread(connection_status, ())

connect_wifi()
connect_mqtt("IoTAlarmSystem", sub_iotalarm)

mqtt_client.subscribe(MQTT_TOPIC)

pir.irq(
    trigger=machine.Pin.IRQ_RISING,
    handler=motion_handler
)

while True:
    mqtt_client.wait_msg()

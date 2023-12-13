# Imports
import Stepper
import network
from time import sleep
from umqtt.simple import MQTTClient
from machine import Pin, ADC, PWM
import time
import machine
import _thread as threading

MQTT_BROKER = "192.168.1.100"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = ""
MQTT_TOPIC = "utng/Jose/ledMotorBuzzer"
MQTT_PORT = 1883

# Pines
led_pin = Pin(2, Pin.OUT)
buzzer_pin = PWM(Pin(4))
buzzer_pin.deinit()

# for ESP32
In1 = Pin(32, Pin.OUT)
In2 = Pin(33, Pin.OUT)
In3 = Pin(25, Pin.OUT)
In4 = Pin(26, Pin.OUT)
infrarouge = ADC(Pin(34))
s1 = Stepper.create(In1, In2, In3, In4, delay=1)

# Configura el sensor ultrasónico (HC-SR04)
trig_pin = Pin(14, Pin.OUT)
echo_pin = Pin(12, Pin.IN)

def play_jingle_bells():
    melody = [
        (659, 150), (0, 300),(659, 150),(0, 300), (659, 200), (0, 300),
        (659, 150), (0, 300),(659, 150),(0, 300), (659, 200), (0, 300),(659, 300), (0, 300),
        (784, 200), (0, 300), (523, 150), (0, 300), (587, 150), (0, 300), (659, 250), (0, 300),
        (698, 150), (0, 300), (698, 150), (0, 300), (698, 200), (0, 300), (698, 150), (0, 300),
        (659, 150), (0, 300), (659, 200), (0, 300), (659, 150), (0, 300),
        (587, 150), (0, 300), (587, 150), (0, 300),
        (659, 150), (0, 300), (587, 150), (0, 300), (784, 400)
    ]

    # Inicializa el zumbador
    buzzer_pin.init()
    for note in melody:
        if 1 <= note[0] <= 4000:  # Limita la frecuencia a un rango seguro
            buzzer_pin.freq(note[0])
            time.sleep_ms(note[1])
        else:
            buzzer_pin.freq(1000)  # Frecuencia predeterminada si la nota es inválida

    # Detén el zumbador
    buzzer_pin.deinit()

def play_melody_2():
    melody = [
        (800, 150), (0, 300),(300, 150),(0, 300), (700, 200), (0, 300),
        (450, 150), (0, 300),(659, 150),(0, 300)
    ]

    # Inicializa el zumbador
    buzzer_pin.init()
    for note in melody:
        if 1 <= note[0] <= 4000:  # Limita la frecuencia a un rango seguro
            buzzer_pin.freq(note[0])
            time.sleep_ms(note[1])
        else:
            buzzer_pin.freq(1000)  # Frecuencia predeterminada si la nota es inválida

    # Detén el zumbador
    buzzer_pin.deinit()


def led_motor_buzzer():
    # Enciende el LED
    led_pin.value(1)
    # Enciende el motor
    s1.step(200, -1)
    time.sleep(2)
    s1.step(200)

    # Reproduce la melodía Jingle Bells
    play_jingle_bells()
    # Apaga el LED
    led_pin.value(0)
    # Detiene el motor

def get_distance():
    # Genera un pulso corto en el pin TRIG para activar el sensor
    trig_pin.value(0)
    time.sleep_us(2)
    trig_pin.value(1)
    time.sleep_us(10)
    trig_pin.value(0)

    # Configura el pin ECHO como entrada antes de medir el pulso de eco
    echo_pin.init(Pin.IN)

    # Mide el tiempo de vuelo del pulso eco en el pin ECHO
    pulse_time = machine.time_pulse_us(echo_pin, 1, 30000)
    # Asegúrate de que la distancia calculada sea siempre no negativa
    distance_cm = max(pulse_time / 58, 0)
    return distance_cm

def wifi_connect():
    print ("Conectando ", end="")
    sta_if = network.WLAN (network.STA_IF)
    sta_if.active(True)
    sta_if.connect("linksys", "")
    # Tiempo máximo para intentar la conexión en segundos
    max_connection_time = 20  # Ajusta el tiempo máximo de espera según sea necesario
    start_time = time.ticks_ms()
    
    while not sta_if.isconnected():
        if time.ticks_diff(time.ticks_ms(), start_time) > max_connection_time * 1000:
            print("\nNo se pudo conectar. Continuando sin conexión.")
            break

        print(".", end="")
        sleep(0.3)

    if sta_if.isconnected():
        print("\nWi-Fi está conectado")
    else:
        print("\nNo se pudo conectar a Wi-Fi")
    
def llegada_mensaje(topic, msg):
    print("Mensaje recibido:", msg)
    
    if msg == b'1':
        led_pin.value(1)
    elif msg == b'0':
        led_pin.value(0)
    elif msg == b'3':
        s1.step(200)
    elif msg == b'2':
        s1.step(200, -1)
    elif msg == b'5':
        # Reproduce la melodía Jingle Bells
        play_jingle_bells()
    elif msg == b'4':
        play_melody_2()

        
        

def subscribirse():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD, keepalive=0)
        client.set_callback(llegada_mensaje)
        client.connect()
        client.subscribe(MQTT_TOPIC)
        print("Conectado en %s, al tópico %s" %(MQTT_BROKER, MQTT_TOPIC))
        return client
    except OSError as e:
        print(f"No se pudo conectar a MQTT: {e}")
        return None

wifi_connect()
client = subscribirse()

while True:
    # Lógica del sensor ultrasónico
    distance = get_distance()
    print("Distancia:", distance, "cm")

    if 5 <= distance <= 15:
        # Ejecuta las funciones de melodía y motor en un hilo
        threading.start_new_thread(led_motor_buzzer, ())
        # Espera un tiempo antes de ejecutar la función del zumbador
        time.sleep(2)  # Ajusta el tiempo según sea necesario para tu aplicación
        # Ejecuta la función del zumbador en un hilo separado
    elif distance == 0:
        # No ejecuta nada si la distancia es 0 cm
        pass


    # Lógica MQTT
    if client is not None:
        client.check_msg()
    
    sleep(2)



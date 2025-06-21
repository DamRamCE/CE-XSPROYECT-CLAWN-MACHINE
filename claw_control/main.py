"""Control script for the claw machine.

El codigo maneja los motores X, Y y Z junto con el servo de la garra.
El joystick y los finales de carrera se leen mediante dos PCF8574.
Los comentarios usan solo ASCII por compatibilidad.
"""

import time
import threading
from enum import Enum


try:  # pragma: no cover - running on development machine
    import RPi.GPIO as GPIO
    from pcf8574 import PCF8574
    from gpiozero import Servo
    from RPLCD.i2c import CharLCD
    import board
    import neopixel
except ImportError:  # Allows running on machines without the libraries
    from unittest import mock

    GPIO = mock.MagicMock()
    PCF8574 = mock.MagicMock()
    Servo = mock.MagicMock()
    CharLCD = mock.MagicMock()
    board = mock.MagicMock()
    neopixel = mock.MagicMock()


MOTORS = {
    "X": {"step": 17, "dir": 27},
    "Y": {"step": 22, "dir": 23},
    "Z": {"step": 24, "dir": 25},
}

PCF1_ADDR = 0x20
PCF2_ADDR = 0x21

JOY = {"UP": 0, "DOWN": 1, "LEFT": 2, "RIGHT": 3, "BTN": 4}
LIM = {"X1": 0, "X2": 1, "Y1": 2, "Y2": 3}

STEP_DELAY = 0.0001
STEPS_Z_BAJA = 4500
STEPS_Z_SUBE = 4500
STEPS_Z_DESCARGA = 2500
PASOS_MOV = 20

SERVO_PIN = 18
NEOPIXEL_PIN = 13
NEOPIXEL_COUNT = 8
BUZZER_PIN = 19
IR_PIN = 26

LCD_ADDR = 0x27
LCD_COLS = 20
LCD_ROWS = 4
_buzzer = None


def buzzer_setup():
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    global _buzzer
    _buzzer = GPIO.PWM(BUZZER_PIN, 440)
    _buzzer.start(0)


def reproducir_tono(freq: int, dur: float) -> None:
    if _buzzer is None:
        return
    if freq > 0:
        _buzzer.ChangeFrequency(freq)
        _buzzer.ChangeDutyCycle(50)
    time.sleep(dur)
    _buzzer.ChangeDutyCycle(0)
    time.sleep(0.05)


def _sonido_thread(func) -> None:
    t = threading.Thread(target=func)
    t.daemon = True
    t.start()


def _tono_inicio() -> None:
    for f in [880, 988, 1047]:
        reproducir_tono(f, 0.1)


def _tono_jugar() -> None:
    for f in [659, 784]:
        reproducir_tono(f, 0.1)


def _tono_exito() -> None:
    for f in [523, 659, 784, 1047]:
        reproducir_tono(f, 0.08)


def _tono_timeout() -> None:
    for f in [784, 659, 523, 392, 262]:
        reproducir_tono(f, 0.1)


def _tono_error() -> None:
    for _ in range(2):
        reproducir_tono(300, 0.1)


def _melodia_arcade() -> None:
    notas = [(660, 0.1), (660, 0.1), (0, 0.1), (660, 0.1), (0, 0.1), (520, 0.1), (660, 0.1), (0, 0.1), (770, 0.1), (0, 0.3), (380, 0.1)]
    for freq, dur in notas:
        reproducir_tono(freq, dur)


def sonido_inicio():
    _sonido_thread(_tono_inicio)

def sonido_jugar():
    _sonido_thread(_tono_jugar)

def sonido_exito():
    _sonido_thread(_tono_exito)

def sonido_timeout():
    _sonido_thread(_tono_timeout)

def sonido_error():
    _sonido_thread(_tono_error)

def sonido_arcade():
    _sonido_thread(_melodia_arcade)


class PixelFX:
    """Efectos simples para la tira neopixel."""

    def __init__(self, pin: int, cantidad: int) -> None:
        board_pin = getattr(board, f"D{pin}", pin)
        self.pixels = neopixel.NeoPixel(board_pin, cantidad, brightness=0.3, auto_write=False)
        self.n = cantidad

    def _wheel(self, pos: int) -> tuple[int, int, int]:
        if pos < 85:
            return pos * 3, 255 - pos * 3, 0
        if pos < 170:
            pos -= 85
            return 255 - pos * 3, 0, pos * 3
        pos -= 170
        return 0, pos * 3, 255 - pos * 3

    def clear(self) -> None:
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def ola(self, color: tuple[int, int, int] = (0, 0, 255), espera: float = 0.05) -> None:
        for offset in range(self.n * 2):
            for i in range(self.n):
                if (i + offset) % 6 < 3:
                    self.pixels[i] = color
                else:
                    self.pixels[i] = (0, 0, 0)
            self.pixels.show()
            time.sleep(espera)

    def arcoiris(self, espera: float = 0.05) -> None:
        for j in range(255):
            for i in range(self.n):
                idx = (i * 256 // self.n) + j
                self.pixels[i] = self._wheel(idx & 255)
            self.pixels.show()
            time.sleep(espera)

    def barrido_centro(self, color: tuple[int, int, int] = (0, 255, 0), espera: float = 0.1) -> None:
        mid = self.n // 2
        for d in range(mid + 1):
            self.clear()
            for i in range(d + 1):
                if mid - i >= 0:
                    self.pixels[mid - i] = color
                if mid + i < self.n:
                    self.pixels[mid + i] = color
            self.pixels.show()
            time.sleep(espera)

    def explosion(self, color: tuple[int, int, int] = (255, 0, 0), espera: float = 0.05) -> None:
        self.clear()
        mid = self.n // 2
        for d in range(mid + 1):
            for i in range(self.n):
                if abs(i - mid) == d:
                    self.pixels[i] = color
            self.pixels.show()
            time.sleep(espera)
        self.clear()

    def tren_multicolor(self, espera: float = 0.1) -> None:
        colores = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        for offset in range(self.n * 3):
            for i in range(self.n):
                self.pixels[i] = colores[(i + offset) % len(colores)]
            self.pixels.show()
            time.sleep(espera)

    def flash_multi(self, repeticiones: int = 5, espera: float = 0.1) -> None:
        colores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        for _ in range(repeticiones):
            for color in colores:
                self.pixels.fill(color)
                self.pixels.show()
                time.sleep(espera)
        self.clear()



def inicializar_lcd():
    """Inicializa y limpia la pantalla LCD."""

    lcd = CharLCD("PCF8574", LCD_ADDR, cols=LCD_COLS, rows=LCD_ROWS)
    lcd.clear()
    return lcd


def mostrar_bienvenida(lcd) -> None:
    """Muestra la secuencia de bienvenida."""

    lcd.clear()
    lcd.cursor_pos = (1, 3)
    lcd.write_string("CE - Loading...")
    time.sleep(2)

    lcd.clear()
    lcd.cursor_pos = (0, 4)
    lcd.write_string("BIENVENIDO")
    lcd.cursor_pos = (1, 2)
    lcd.write_string("CE - XSPROYECT")
    lcd.cursor_pos = (2, 2)
    lcd.write_string("CLAWN MACHINE")
    time.sleep(3)

    lcd.clear()
    lcd.cursor_pos = (1, 2)
    lcd.write_string("Pulsa el boton")
    lcd.cursor_pos = (2, 1)
    lcd.write_string("para comenzar...")

class Estado(Enum):
    INICIO = 0
    POSICION = 1
    JUEGO = 2
    CAPTURA = 3
    DEPOSITO = 4
    VERIFICAR = 5
    GANADO = 6
    PERDIDO = 7
    RESET = 8



class ClawMachine:
    """Control basico de la garra usando joystick y servo."""

    def __init__(self, bus_num: int = 1) -> None:
        self.pcf1 = PCF8574(bus_num, PCF1_ADDR)
        self.pcf2 = PCF8574(bus_num, PCF2_ADDR)
        self.servo = None
        self.setup_gpio()

        self.state = Estado.INICIO
    def setup_gpio(self) -> None:
        GPIO.setmode(GPIO.BCM)
        for motor in MOTORS.values():
            GPIO.setup(motor["step"], GPIO.OUT)
            GPIO.setup(motor["dir"], GPIO.OUT)
        GPIO.setup(IR_PIN, GPIO.IN)
        self.servo = Servo(
            SERVO_PIN, min_pulse_width=0.5 / 1000, max_pulse_width=2.4 / 1000
        )
        self.fx = PixelFX(NEOPIXEL_PIN, NEOPIXEL_COUNT)
        buzzer_setup()
        self.open_claw()
        print("Gripper abierto al inicio.")

    def leer(self, pin: int, pcf: PCF8574) -> bool:
        """Devuelve el estado logico de un pin del PCF8574."""

        return not pcf.read_pin(pin)

    def read_joystick(self) -> dict:
        """Lee todos los pines del joystick."""

        return {
            "LEFT": self.leer(JOY["LEFT"], self.pcf1),
            "RIGHT": self.leer(JOY["RIGHT"], self.pcf1),
            "UP": self.leer(JOY["UP"], self.pcf1),
            "DOWN": self.leer(JOY["DOWN"], self.pcf1),
            "BTN": self.leer(JOY["BTN"], self.pcf1),
        }

    def read_limit(self, key: str) -> bool:
        """Devuelve el estado de un final de carrera."""

        return self.leer(LIM[key], self.pcf2)

    def motor_step(self, axis: str, direction: int) -> None:
        GPIO.output(MOTORS[axis]["dir"], direction)
        GPIO.output(MOTORS[axis]["step"], GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(MOTORS[axis]["step"], GPIO.LOW)
        time.sleep(STEP_DELAY)

    def move_motor(
        self,
        step_pin: int,
        dir_pin: int,
        direction: int,
        steps: int,
        limit_key: str | None = None,
    ) -> None:
        """Mueve un motor por pasos con opcion de limite."""

        GPIO.output(dir_pin, direction)
        for _ in range(steps):
            if limit_key is not None and self.read_limit(limit_key):
                break
            GPIO.output(step_pin, GPIO.HIGH)
            time.sleep(STEP_DELAY)
            GPIO.output(step_pin, GPIO.LOW)
            time.sleep(STEP_DELAY)

    def open_claw(self) -> None:
        """Abre la garra."""

        self.servo.min()
        time.sleep(1)

    def close_claw(self) -> None:
        """Cierra la garra."""

        self.servo.max()
        time.sleep(1)

    def move_inicio(self) -> None:
        """Lleva la garra a la posicion inicial."""

        self.move_motor(
            MOTORS["Y"]["step"],
            MOTORS["Y"]["dir"],
            GPIO.HIGH,
            5000,
            "Y1",
        )
        self.move_motor(
            MOTORS["X"]["step"],
            MOTORS["X"]["dir"],
            GPIO.HIGH,
            5000,
            "X2",
        )

    def move_descarga(self) -> None:
        """Lleva la garra a la zona de descarga."""

        self.move_motor(
            MOTORS["Y"]["step"],
            MOTORS["Y"]["dir"],
            GPIO.LOW,
            5000,
            "Y2",
        )
        self.move_motor(
            MOTORS["X"]["step"],
            MOTORS["X"]["dir"],
            GPIO.HIGH,
            5000,
            "X2",
        )

    def secuencia(self) -> None:
        """Ejecuta la toma de peluche y descarga."""

        self.move_motor(
            MOTORS["Z"]["step"],
            MOTORS["Z"]["dir"],
            GPIO.LOW,
            STEPS_Z_BAJA,
        )
        self.close_claw()
        time.sleep(0.5)
        self.move_motor(
            MOTORS["Z"]["step"],
            MOTORS["Z"]["dir"],
            GPIO.HIGH,
            STEPS_Z_SUBE,
        )
        self.move_descarga()
        self.move_motor(
            MOTORS["Z"]["step"],
            MOTORS["Z"]["dir"],
            GPIO.LOW,
            STEPS_Z_DESCARGA,
        )
        self.open_claw()
        time.sleep(1)
        self.move_motor(
            MOTORS["Z"]["step"],
            MOTORS["Z"]["dir"],
            GPIO.HIGH,
            STEPS_Z_SUBE,
        )
        self.move_inicio()
    def loop(self) -> None:
        """Bucle principal basado en estados."""

        try:
            while True:
                if self.state == Estado.INICIO:
                    print("Posicionando en X2-Y1 (inicio)...")
                    sonido_inicio()
                    self.open_claw()
                    self.move_inicio()
                    print("Esperando boton...")
                    self.state = Estado.JUEGO

                elif self.state == Estado.JUEGO:
                    joy = self.read_joystick()
                    if joy["BTN"]:
                        print("Boton presionado. Iniciando secuencia...")
                        sonido_jugar()
                        self.state = Estado.CAPTURA
                    else:
                        if joy["LEFT"] and not self.read_limit("X1"):
                            self.motor_step("X", GPIO.LOW)
                        elif joy["RIGHT"] and not self.read_limit("X2"):
                            self.motor_step("X", GPIO.HIGH)
                        elif joy["UP"] and not self.read_limit("Y1"):
                            self.motor_step("Y", GPIO.HIGH)
                        elif joy["DOWN"] and not self.read_limit("Y2"):
                            self.motor_step("Y", GPIO.LOW)
                    time.sleep(0.05)

                elif self.state == Estado.CAPTURA:
                    self.move_motor(MOTORS["Z"]["step"], MOTORS["Z"]["dir"], GPIO.LOW, STEPS_Z_BAJA)
                    self.close_claw()
                    time.sleep(0.5)
                    self.move_motor(MOTORS["Z"]["step"], MOTORS["Z"]["dir"], GPIO.HIGH, STEPS_Z_SUBE)
                    self.state = Estado.DEPOSITO

                elif self.state == Estado.DEPOSITO:
                    self.move_descarga()
                    self.move_motor(MOTORS["Z"]["step"], MOTORS["Z"]["dir"], GPIO.LOW, STEPS_Z_DESCARGA)
                    self.open_claw()
                    time.sleep(1)
                    self.move_motor(MOTORS["Z"]["step"], MOTORS["Z"]["dir"], GPIO.HIGH, STEPS_Z_SUBE)
                    self.state = Estado.VERIFICAR

                elif self.state == Estado.VERIFICAR:
                    if GPIO.input(IR_PIN):
                        self.state = Estado.GANADO
                    else:
                        self.state = Estado.PERDIDO

                elif self.state == Estado.GANADO:
                    sonido_exito()
                    self.state = Estado.RESET

                elif self.state == Estado.PERDIDO:
                    sonido_timeout()
                    self.state = Estado.RESET

                elif self.state == Estado.RESET:
                    self.move_inicio()
                    print("Esperando boton...")
                    self.state = Estado.JUEGO
        except KeyboardInterrupt:
            pass



    def cleanup(self) -> None:
        if self.servo:
            try:
                self.servo.detach()
            except AttributeError:
                pass
        GPIO.cleanup()


def main() -> None:
    lcd = inicializar_lcd()
    mostrar_bienvenida(lcd)
    machine = ClawMachine()
    try:
        machine.loop()
    finally:
        machine.cleanup()


if __name__ == "__main__":
    main()

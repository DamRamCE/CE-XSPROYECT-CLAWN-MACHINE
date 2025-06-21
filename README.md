# CE-XSPROYECT-CLAWN-MACHINE

Este proyecto contiene la base para controlar una maquina de garra con Raspberry Pi y Python. A continuacion se describen los primeros pasos para comenzar el desarrollo.

## Requisitos

- Raspberry Pi con Raspbian o similar
- Python 3
- Bibliotecas `RPi.GPIO`, `gpiozero`, `pcf8574`, `RPLCD` y `adafruit-circuitpython-neopixel`
- Se usa `gpiozero` para el servo y `pcf8574` para leer joystick y finales

Instala las dependencias ejecutando:

```bash
pip install -r requirements.txt
```

## Uso básico

El script `claw_control/main.py` integra el control de sonidos y una pequena maquina de estados. Al iniciarse muestra una pantalla de bienvenida, reproduce un tono y posiciona la garra en el punto inicial. Con el joystick se controlan los ejes **X** e **Y** y, al pulsar el boton, la maquina realiza la secuencia de captura y deposito. Los finales de carrera impiden movimientos fuera del recorrido.
```bash
python -m claw_control.main
```

Utiliza este archivo como punto de partida para anadir las funciones especificas de tu hardware.

## Hardware principal

La siguiente tabla muestra las conexiones sugeridas usando numeracion BCM:

| Modulo | GPIO | Descripcion |
|--------|------|-------------|
| DRV8825 X | 17 STEP / 27 DIR | Motor eje X |
| DRV8825 Y | 22 STEP / 23 DIR | Motor eje Y |
| DRV8825 Z | 24 STEP / 25 DIR | Motor eje Z |
| Servo MG995 | 18 PWM | Gripper |
| Neopixel | 13 PWM | Luces |
| Buzzer | 19 | Tonos |
| Sensor IR | 26 | Deteccion |
| LCD 20x4 | SDA 2 / SCL 3 | Direccion 0x27 |
| PCF8574 #1 | SDA 2 / SCL 3 | Joystick y boton |
| PCF8574 #2 | SDA 2 / SCL 3 | Finales de carrera |

Los pines de cada PCF8574 se usan para las direcciones del joystick, el boton de inicio y los finales de carrera.

El programa lee los finales de carrera en cada iteracion del bucle para impedir el movimiento cuando alguno esta activado. Esto protege los ejes de golpes y mantiene la garra dentro de su recorrido.

## Efectos de luces

Se utilizan neopixels controlados por la biblioteca Adafruit CircuitPython NeoPixel. El archivo `main.py` incluye funciones para los siguientes efectos:

- Desplazamiento tipo ola
- Efecto arcoiris
- Barrido desde centro
- Explosion radial
- Tren multicolor
- Flash multicolor

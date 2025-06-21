import types
import sys
sys.path.insert(0, ".")
from claw_control import main

def test_leer_true():
    machine = main.ClawMachine()
    machine.pcf1 = types.SimpleNamespace(read_pin=lambda pin: 0)
    assert machine.leer(0, machine.pcf1) is True

def test_move_motor_stops(monkeypatch):
    machine = main.ClawMachine()
    # Fake limit switch: high for two steps then low
    class DummyPCF:
        def __init__(self):
            self.calls = 0
        def read_pin(self, pin):
            self.calls += 1
            return 1 if self.calls <= 2 else 0
    machine.pcf2 = DummyPCF()
    steps = []
    def fake_output(pin, value):
        if pin == main.MOTORS["X"]["step"] and value == main.GPIO.HIGH:
            steps.append(1)
    monkeypatch.setattr(main.GPIO, "output", fake_output)
    monkeypatch.setattr(main.time, "sleep", lambda x: None)
    machine.move_motor(
        main.MOTORS["X"]["step"],
        main.MOTORS["X"]["dir"],
        main.GPIO.HIGH,
        10,
        "X1",
    )
    assert len(steps) == 2

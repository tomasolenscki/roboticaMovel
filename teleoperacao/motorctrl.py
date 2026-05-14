import gpiod
from gpiod.line import Direction, Value
from rpi_hardware_pwm import HardwarePWM
import contextlib
import numpy as np
# Cria um controlador de motor.
# Este gerador ´e decorado com contextmanager para garantir
# que o estado do gpio e pwm seja resetado na sa´ıda de escopo
@contextlib.contextmanager
def cria_controle_motor():
# Configura¸c~ao inicial: output com n´ıvel inicial baixo
    print("Criando controle de motores...", end="")
    confoutlow = gpiod.LineSettings(direction=Direction.OUTPUT, output_value = Value.INACTIVE)
    with gpiod.Chip("/dev/gpiochip0") as chip0:
    # Cria acesso `as linhas de GPIO 5 e 6
        with chip0.request_lines({5:confoutlow, 6:confoutlow}) as linhas:
            pwma = HardwarePWM(0, 20, 0)
            pwmb = HardwarePWM(1, 20, 0)
            motor = motorCtrl(linhas, 5, 6, pwma, pwmb)
            print("Feito.")
            try:
                yield motor
            finally:
                print("Encerrando controle de motores...", end="")
                pwma.stop()
                pwmb.stop()
                print("Feito.")

class motorCtrl():
    def __init__(self, linhas, canal_direita, canal_esquerda, pwma, pwmb):
        # Acesso a linhas gpio por gpiod
        self._linhas = linhas
        # Numero do canal de GPIO da fase "B" do motor da direita
        self._cdireita = canal_direita
        # Numero do canal de GPIO da fase "B" do motor da esquerda
        self._cesquerda = canal_esquerda
        # PWM conectado `a fase "A" do motor da direita
        self._pwma = pwma
        # PWM conectado `a fase "B" do motor da direita
        self._pwmb = pwmb
        self._pwma.start(0)
        self._pwmb.start(0)
    def set_lr(self, l, r):
        r = np.clip(r,-100,100)
        l = np.clip(l, -100, 100) 
        if l>=0: #left motor forward
            self._pwmb.change_duty_cycle(l)
            self._linhas.set_value(self._cesquerda, Value.INACTIVE)
        elif l<0:       #move left motor backwards
            self._pwmb.change_duty_cycle(l+100)
            self._linhas.set_value(self._cesquerda, Value.ACTIVE)
        if r>=0:       # right motor
            self._pwma.change_duty_cycle(r)
            self._linhas.set_value(self._cdireita, Value.INACTIVE)
        elif r<0:
            self._pwma.change_duty_cycle(r+100)
            self._linhas.set_value(self._cdireita, Value.ACTIVE)
    # Aplica comandos nos motores:
    # l ´e o valor (de -100 a 100) para o motor esquerdo
    # r ´e o valor (de -100 a 100) para o motor esquerdo


# GPIO 5 - input B of motor A (right); controls direction
# GPIO 6 - input B of motor B (left)


# pin 32 - input A of motor A(PWM signal); controls duty cycle -> angular speed
# pin 33 - input A of motor B(PWM signal)

#out B Low and out A high -> motor rotates 'forward'

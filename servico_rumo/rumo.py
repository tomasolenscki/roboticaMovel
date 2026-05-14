import numpy as np


H_MAG = np.array([42.16124924, 111.04649021, -142.35053646], dtype=float)

# W maps raw magnetometer samples, after hard-iron subtraction, to the robot
# local frame. The unit-field calibration is enough for heading estimation,
# because atan2 only depends on the horizontal field direction.
W_MAG = np.array([
    [-1.24665325e-07,  6.70445493e-03, -1.47351765e-03],
    [-7.12520332e-03,  2.19207098e-05,  2.36572507e-04],
    [ 1.79320011e-04,  3.03670888e-04,  7.88038890e-03],
], dtype=float)

DECLINACAO_RAD = np.deg2rad(-21.838268612775256)


def cria_estimador_rumo(t0, rumo0, incerteza0, callback, nome_estimador="bussola"):
    if nome_estimador == "bussola":
        return Bussola(callback, t0, rumo0, incerteza0)
    if nome_estimador in ("bussola_filtrada", "filtrada"):
        return BussolaFiltrada(callback, t0, rumo0, incerteza0)
    raise ValueError(f"Estimador {nome_estimador} desconhecido!")


def normaliza_angulo(angulo):
    return (angulo + np.pi) % (2.0 * np.pi) - np.pi


def rumo_por_magnetometro(mx, my, mz):
    medida = np.array([mx, my, mz], dtype=float)
    campo_local = W_MAG @ (medida - H_MAG)
    phi = np.arctan2(campo_local[1], campo_local[0])
    return normaliza_angulo(DECLINACAO_RAD - phi)


class Bussola:
    def __init__(self, callback, t0, rumo0, incerteza0):
        self._angulo = float(rumo0)
        self._t0_sensor = None
        self._ultimo_tempo = None
        self._nova_previsao = callback

    def _tempo_segundos(self, t):
        if self._t0_sensor is None:
            self._t0_sensor = t
        return (t - self._t0_sensor) * 1e-9

    def processa_dados(self, t, mx, my, mz):
        tempo = self._tempo_segundos(t)
        angulo = rumo_por_magnetometro(mx, my, mz)
        self._angulo = angulo
        self._ultimo_tempo = tempo
        self._nova_previsao(tempo, angulo, 0, 0)

    def callback(self, data):
        mx = int.from_bytes(data[14:16], byteorder="big", signed=True)
        my = int.from_bytes(data[16:18], byteorder="big", signed=True)
        mz = int.from_bytes(data[18:20], byteorder="big", signed=True)
        t = int.from_bytes(data[-8:], byteorder="little", signed=False)
        self.processa_dados(t, mx, my, mz)


class BussolaFiltrada(Bussola):
    def __init__(self, callback, t0, rumo0, incerteza0, fc=0.25, fs=20.0):
        super().__init__(callback, t0, rumo0, incerteza0)
        self._alpha = np.exp(-2.0 * np.pi * fc / fs)
        self._angulo_filtrado = None

    def processa_dados(self, t, mx, my, mz):
        tempo = self._tempo_segundos(t)
        angulo = rumo_por_magnetometro(mx, my, mz)

        if self._angulo_filtrado is None:
            self._angulo_filtrado = angulo
        else:
            diferenca = normaliza_angulo(angulo - self._angulo_filtrado)
            self._angulo_filtrado = normaliza_angulo(
                self._angulo_filtrado + (1.0 - self._alpha) * diferenca
            )

        self._angulo = self._angulo_filtrado
        self._ultimo_tempo = tempo
        self._nova_previsao(tempo, self._angulo_filtrado, 0, 0)

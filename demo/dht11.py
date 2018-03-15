# upy to read temperature, humidity

import dht
import machine

d = dht.DHT11(machine.Pin(0)) #D3
d.measure()
d.temperature() # eg. 23 (℃)
d.humidity()    # eg. 41 (% RH)
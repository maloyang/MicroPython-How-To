
import machine
import time

p = machine.Pin(2, machine.Pin.OUT) #D4

for i in range(6):
    p.value(not p.value())
    time.sleep(1)

# send T/H sensor data to MQTT cloud platform
# control light with MQTT

from umqtt.simple import MQTTClient
from machine import Pin
import dht
import ubinascii
import machine
import network
import time
import os

# ESP8266 ESP-12 modules have blue, active-low LED on GPIO2
led = Pin(2, Pin.OUT, value=1)
my_new_msg = None
TOPIC_BASE = 'malo-iot'

#Control Function
def led_onoff(onoff):
    """ control led ON or OFF
        parameter:
        onoff
            0-->ON, 1-->OFF (acturely, led ON when level=0)
    """
    global led
    
    if(onoff==1):
        led.value(0)
    elif(onoff==-1):
        led.value(not led.value())
    else:
        led.value(1)

def dht_get():
    ''' get dht11 sensor's value (T, H)
        return:
            (Temperature, Humidity)
    '''
    T=None
    H=None
    try:
        dht11 = dht.DHT11(Pin(0)) #D3

        dht11.measure()
        T = dht11.temperature()
        H = dht11.humidity()
    except Exception as e:
        print('dht_get error:', str(e))
    
    return T, H

    
def sub_cb(topic, msg):
    global my_new_msg
    global TOPIC_BASE
    topic_light = TOPIC_BASE+"/light"
    topic_t = TOPIC_BASE+'/T'
    topic_h = TOPIC_BASE+'/H'

    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    my_new_msg = '['+topic+'] '+ msg
    print(my_new_msg)
    
    if(topic == topic_light):
        if msg == "0":
            led_onoff(0)
        else:
            led_onoff(1)
    if(topic == topic_t):
        pass
    if(topic == topic_h):
        pass
    
def main():
    global my_new_msg
    global TOPIC_BASE
    
    mq_fail_count = 0
    tm_pub_th = time.ticks_ms()

    led_onoff(1)

    #- check ap config file
    AP_SSID = 'upy'
    AP_PWD = 'pypypypy'
    ap_config = None
    ap_config_fn = 'ap.txt'
    if ap_config_fn in os.listdir():
        print('ap config here!')
        f = open(ap_config_fn)
        ap_config = f.read()
        f.close()
    if ap_config:
        print( ('ap_config:', ap_config))
        ap_config = ap_config.split('\n')
        AP_SSID = ap_config[0].strip()
        AP_PWD = ap_config[1].strip()
    print('line to: ', (AP_SSID, AP_PWD))
    
    # Default MQTT server to connect to
    server = "iot.eclipse.org"
    CLIENT_ID = ubinascii.hexlify(machine.unique_id()).decode('utf-8')
    topic_light = TOPIC_BASE+"/light"
    topic_t = TOPIC_BASE+'/T'
    topic_h = TOPIC_BASE+'/H'
    topic_msg = TOPIC_BASE+'/msg'
    

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(AP_SSID, AP_PWD)
    print('connecting to AP')
    while(not wlan.isconnected()):
        print(wlan.ifconfig())
        time.sleep(0.1)
        led_onoff(-1)
    print('connected!  --> ', wlan.ifconfig())

    c = MQTTClient(CLIENT_ID, server)
    # Subscribed messages will be delivered to this callback
    c.set_callback(sub_cb)
    c.connect()
    c.subscribe(topic_light)
    print("Connected to %s, subscribed to %s topic" % (server, topic_light))

    # wifi ready, blink led
    for i in range(3):
        led_onoff(1)
        time.sleep(1)
        led_onoff(0)
        time.sleep(1)
    print('I am ready!, ID='+str(CLIENT_ID))
    c.publish(topic_msg, 'I am ready!, ID='+str(CLIENT_ID))

    try:
        while 1:
            if(not wlan.isconnected()):
                # not do any mq operation
                time.sleep(0.1)
                led_onoff(-1)                
                continue
            
            try:
                #c.wait_msg()
                c.check_msg()
                if my_new_msg:
                    c.publish(topic_msg, my_new_msg)
                    my_new_msg = None

                if(time.ticks_ms()-tm_pub_th > 5000):
                    # public some information
                    T, H = dht_get()
                    c.publish(topic_t, str(T))
                    c.publish(topic_h, str(H))
                    
                    tm_pub_th = time.ticks_ms()
                    
            except Exception as e:
                print('wlan:', wlan.isconnected())
                print('ex: ', str(e))
                mq_fail_count+=1
                time.sleep(1)
                
            try:
                if mq_fail_count>5:
                    mq_fail_count=0
                    c = MQTTClient(CLIENT_ID, server)
                    # Subscribed messages will be delivered to this callback
                    c.set_callback(sub_cb)
                    c.connect()
                    c.subscribe(topic_light)
                    print("Connected to %s, subscribed to %s topic" % (server, topic_light))
            except Exception as e:
                print('wlan:', wlan.isconnected())
                print('ex: ', str(e))
                    

            time.sleep(0.001)
                        
    finally:
        c.disconnect()


if __name__ == '__main__':
    main()

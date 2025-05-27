from tw_mssp import Mssp
from tw_mssp import MASTER_BIT
import json

mssp = Mssp("COM1", 9600, 5, True)

def read_main():
    try:
        with open('data/main.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print("Could not read the defaults:", e)
        return None

while True:

    msg = mssp.get_msg()
    ctrl = msg.get_ctrl()
    ctrl = ctrl & ~MASTER_BIT
    add = msg.get_addr()
    cmd = msg.get_cmd()
    data = msg.get_data()
    m_data = read_main()

    if (cmd == mssp.MSG_GET_LIGHT_VALUE_REQ):

        try:
            light_raw = int(m_data.get("light_raw"))
            light_avg = int(m_data.get("light_avg"))
            light_last = int(m_data.get("light_last"))
        except Exception as e:
            light_raw = 100
            light_avg = 100
            light_last = 100
        message = mssp.create_msg_get_light_value_resp(light_raw, light_avg, light_last)
        message.set_addr(mssp.LIGHT_SENSOR_ADDRESS)
        message.set_ctrl(ctrl)
        mssp.send_msg(message)

    elif (cmd == mssp.MSG_DEVICE_INFO_REQ):
        devType = 4096
        devId = 65535
        fw = 16842753
        addr = mssp.LIGHT_SENSOR_ADDRESS 
        group = 254 
        message = mssp.create_msg_device_info_resp(devType, devId, fw, addr, group)
        message.set_addr(mssp.LIGHT_SENSOR_ADDRESS)
        message.set_ctrl(ctrl) 
        mssp.send_msg(message)
    
    elif (cmd == mssp.MSG_GET_SINGLE_PARAM_REQ):
        
        try:
            temp = int(m_data.get("temp"))
            ptype=mssp.PARAM_TEMPERATURE 
            message = mssp.create_msg_get_single_param_resp(ptype, 1, temp)
        except Exception as e:
            temp=0
            ptype=mssp.PARAM_TEMPERATURE
            message = mssp.create_msg_get_single_param_resp(ptype, 1, temp)

        try:
            volt = int(m_data.get("volt"))
            ptype=mssp.PARAM_VOLTAGE
            message = mssp.create_msg_get_single_param_resp(ptype, 1, volt)
        except Exception as e:
            volt=0
            ptype=mssp.PARAM_VOLTAGE
            message = mssp.create_msg_get_single_param_resp(ptype, 1, volt)
        message.set_addr(mssp.LIGHT_SENSOR_ADDRESS)
        message.set_ctrl(ctrl) 
        mssp.send_msg(message)

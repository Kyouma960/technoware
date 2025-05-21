
import serial
import serial.rs485
import struct
from cobs import cobs
import time
import tw_fast_crc

import logging

PROTOCOL_VERSION = 0x1
MASTER_BIT = 0b01000000
#Non constants
protocol_version = PROTOCOL_VERSION

CTR_INIT = 1
CTR_ADD = 2

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.ERROR) # set to ERROR for no debug data, set to DEBUG for debug


msg_counter = 0x00

def handle_counter(value):
    global msg_counter
    
    msg_counter += value
    if (msg_counter > 0x0F):
        msg_counter = 0x01
    #logger.debug("Counter: %d", msg_counter)
    return msg_counter

def setProtVersion(protVer):
    global protocol_version
    if protVer == 1:
        protocol_version = 0x1
    elif protVer == 2:
        protocol_version = 0x2


# Mssp_message class is extension to bytearray
# 
# There are helper functions to update message header.
# Header bytes must be always updated using these functions, 
# which ensures that header stucture can be later changed without 
# modifications to other code

class Mssp_message(bytearray):

    def __init__(self, message_data=4):
        # create header without any data, if message_data was empty
        # otherwise, create message from the message_data
        self[:] = bytearray(message_data)
        self[0] = protocol_version
        
    def set_ctrl(self, ctrl):
        self[1] = ctrl

    def set_addr(self, addr):
        self[2] = addr

    def set_cmd(self, cmd):
        self[3] = cmd

    def get_ctrl(self):
        return self[1]

    def get_addr(self):
        return self[2]

    def get_cmd(self):
        return self[3]
    
    def get_data(self):
        return self[4:]
    
    def inc_counter(self):
        ctr = handle_counter(0x01)
        self[1] = ( self[1] | ctr )
    

class Mssp:

    # messages
    MSG_DEVICE_INFO_REQ					= 0x00
    MSG_DEVICE_INFO_RESP				= 0x00
    MSG_FIND_DEVICE_ID_REQ				= 0x01
    MSG_FIND_DEVICE_ID_RESP				= 0x01
    MSG_SET_ADDRESS_REQ					= 0x03
    MSG_SET_ADDRESS_RESP				= 0x03
    MSG_GET_PARAMS_REQ					= 0x04
    MSG_GET_PARAMS_RESP					= 0x04
    MSG_SET_PARAMS_IND					= 0x05
    MSG_GET_LIGHT_VALUE_REQ				= 0x0A
    MSG_GET_LIGHT_VALUE_RESP			= 0x0A
    MSG_SET_DEVICE_ID_REQ				= 0x0B
    MSG_SET_DEVICE_ID_RESP				= 0x0B
    MSG_GET_SINGLE_PARAM_REQ			= 0x0C
    MSG_GET_SINGLE_PARAM_RESP			= 0x0C
    MSG_GET_RESET_STATUS_REQ			= 0x0D
    MSG_GET_RESET_STATUS_RESP			= 0x0D
    MSG_GET_MULTI_LIGHT_VALUE_REQ		= 0x0E
    MSG_GET_MULTI_LIGHT_VALUE_RESP		= 0x0E


    # addresses
    LIGHT_SENSOR_ADDRESS                = 0x7D      #Sensor address in one-node-network, sensor = only device in network
    FORCED_SLAVE_ADDRESS		        = 0x7F
    UNSET_ADDRESS                       = 0xFE      # = 254
    BROADCAST_ADDRESS			        = 0xFF
    
    # message result codes
    TW_MSSP_OK                              = 0x00
    TW_MSSP_INVALID_CHANNEL                 = 0x01
    TW_MSSP_INVALID_COMMAND                 = 0x02
    TW_MSSP_INVALID_LENGTH                  = 0x03
    TW_MSSP_INVALID_CRC                     = 0x04
    TW_MSSP_NO_MSG                          = 0x05
    TW_MSSP_MSG_NOT_FOR_ME                  = 0x06
    TW_MSSP_BUSY                            = 0x07
    TW_MSSP_NOT_IMPLEMENTED                 = 0x08
    TW_MSSP_ERASE_FAILED                    = 0x09
    TW_MSSP_ALIGNMENT_ERROR                 = 0x0A
    TW_MSSP_INVALID_ACTIVE_FW               = 0x0B
    TW_MSSP_MESSAGE_LOST                    = 0x0C
    TW_MSSP_LAST_FRAME_NOT_RECEIVED         = 0x0E
    TW_MMSP_DATA_NOT_FOR_ERASED_PARTITION   = 0x0F
    TW_MSSP_PARAMETER_SIZE_TOO_LARGE        = 0x10
    TW_MSSP_WRONG_DEVICE_TYPE               = 0x12
    TW_MSSP_NOT_IN_CORRECT_STATE            = 0x13
    TW_MSSP_CRC_FAILED                      = 0x14

    # param types
    PARAM_LIGHT_SENSOR_CONFIG	= 0x00
    PARAM_LIGHT_SENSOR_SETUP	= 0x01
    PARAM_PWM_SETPOINT			= 0x02
    PARAM_COLOR_TEMP_SETPOINT	= 0x03
    PARAM_PWM					= 0x80
    PARAM_LIGHTSENSOR			= 0x81
    PARAM_TEMPERATURE			= 0x82
    PARAM_VOLTAGE				= 0x83
    PARAM_ALARM                 = 0x85
    PARAM_UNKNOWN				= 0xFF

    # default timeout
    TIMEOUT = 1 # 1 second
    

   
    def __init__(self, port, baudrate, timeout, enable_rs485 = False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        
        logger.debug("Now init port: %s", port)
        try:
            #set to None, so we can check later, if serial port was opened successfully
            #set port and baudrate
            self.ser = serial.Serial(port, baudrate, timeout = timeout)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
        except Exception as e:
            print(f"INIT: {e}")
            pass

        if enable_rs485 == True:
            #set port to rs485 mode
            self.ser.rs485_mode = serial.rs485.RS485Settings(rts_level_for_tx=True, rts_level_for_rx=False)


    def send_message(self, ser, message, badCRC = False):         
        # convert to bytes
        message = bytes(message)

        #add crc
        crc = tw_fast_crc.crc16ccitt(message)
        if badCRC:
            message = message + crc.to_bytes(2, byteorder='big') #Reversing byte order is enough for garbled CRC
        else:
            message = message + crc.to_bytes(2, byteorder='little')

        # cobs encode message
        encoded = cobs.encode(message)

        # add 0x00 to the start and end of the message
        encoded = bytes([0x00]) + encoded + bytes([0x00]) 

        logger.debug("SEND: %s", bytes(encoded).hex())

        # write to port  
        for c in range(len(encoded)):
            x = ser.write(encoded[c : c+1])
            time.sleep(0.01)

        
    def receive_message(self, ser, cmd):
        data = []
        
        # wait for start of frame
        while True:
            try:
                ch = ser.read(1)
            except Exception as e:
                print(f"REC: {e}")
                return Mssp_message() # return empty message

            if ch == b'':
                print("Timeout, when waiting start of frame")
                return Mssp_message() # return empty message

            if ch == b'\x00':
                break
        
        # read data until end of frame received
        while True:
            try:
                ch = ser.read()
            except Exception as e:
                print(f"REC: {e}")
                return Mssp_message() # return empty message

            if ch == b'':
                print("Timeout, when receiving data")
                return Mssp_message() # return empty message

            if ch == b'\x00':
                break
 
            data += ch

        # decode data
        data = bytes(data)

        logger.debug("RESP: %s", bytes(data).hex())
        message = cobs.decode(data)
        
        logger.debug("RESP decoded: %s", bytes(message).hex())

        # remove CRC from the message
        message = message[:-2]
        return Mssp_message(message)
            
    def receive_data(self, ser):
        while True:
            try:
                ch = ser.read(1)
            except Exception as e:
                print(f"REC DATA: {e}")
                return

            print(ch)

    def get_msg(self):
        msg = Mssp_message()
        try:
            if(self.ser == None):
                self.ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)
            msg = self.receive_message(self.ser, None)
        except Exception as error:
            print(f"GET MSG: {error}")
            logger.error(error)
            #Try this to fix index out of range
            self.reset_buffers()

        logger.debug("Msg to return: %s", bytes(msg).hex())
        return msg

    def send_msg(self, msg, badCRC = False):
        logger.debug("Msg to send: %s", bytes(msg).hex())
        try:
            if(self.ser == None):
                self.ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)
            if badCRC:
                self.send_message(self.ser, msg, True)
            else:
                self.send_message(self.ser, msg)
        except Exception as error:
            print("Send MSG")
            logger.error(error)


    #DEVICE INFOS
    def create_msg_device_info_resp(self, type, id, fwVer, addr, group):   
        message = Mssp_message()
        message.set_cmd(self.MSG_DEVICE_INFO_RESP)
        # set parameters
        data = struct.pack('<IIIBB', type, id, fwVer, addr, group)
        message.extend(bytearray(data))
        return message

    # ----- LIGHT SENSOR SIMULATION ---------
    def create_msg_get_light_value_resp(self, sensor_value, avg_value, last_value):
        message = Mssp_message()
        message.set_cmd(self.MSG_GET_LIGHT_VALUE_RESP)
        # set parameters
        data = struct.pack('<HHH', sensor_value, avg_value, last_value)
        message.extend(bytearray(data))
        return message

    def create_msg_get_single_param_resp(self, name, number, value):
        message = Mssp_message()
        message.set_cmd(self.MSG_GET_SINGLE_PARAM_RESP)
        # set parameters
        data = struct.pack('<BBH', name, number, value)
        message.extend(bytearray(data))
        return message



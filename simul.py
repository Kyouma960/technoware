# start
from tw_mssp import Mssp
from tw_mssp import MASTER_BIT

# Init the Mssp library
mssp = Mssp("/dev/ttyUSB1", 9600, 8, True)
while True:
    # Get the msg from COM port
    print(mssp.get_msg())

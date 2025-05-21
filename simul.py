# start
from tw_mssp import Mssp
from tw_mssp import MASTER_BIT

# Init the Mssp library
mssp = Mssp('/dev/ttyUSB0', 8, 2000, 0)
while True:
    # Get the msg from COM port
    print(mssp.get_msg())

import sys
'''
  A function that calculates CRC-16-CCIT
  Initialize value can be given as parameter.
  Default initialization value is 0xffff
 
  Returns   CRC-16-CCIT value of given data.
 '''

def crc16ccitt(data, init_value=0xffff):
    crc = init_value

    for i in range(len(data)):
        x = (crc >> 8) ^ data[i]
        x ^= x >> 4
        crc = ((crc << 8) ^ (x << 12) ^ (x << 5) ^ x) & 0xffff

    return crc

if __name__ == "__main__":
    # execute module tests
    # correct testcrc values calculated with online tool:
    # https://www.lammertbies.nl/comm/info/crc-calculation.html

    testvalues = "123456789"
    testcrc = 0x29b1
    testdata = bytearray(testvalues.encode('utf-8'))

    crc = crc16ccitt(testdata)

    print("testdata:", testdata)
    print("crc:", hex(crc))

    if crc != testcrc:
        print ("FAILED")
        sys.exit()

    testvalues = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
    testcrc = 0x97df
    testdata = bytearray(testvalues)

    crc = crc16ccitt(testdata)

    print("testdata:", testdata)
    print("crc:", hex(crc))

    if crc != testcrc:
        print ("FAILED")
        sys.exit()

    testvalues = [0x00, 0x00]
    testcrc = 0x1d0f
    testdata = bytearray(testvalues)

    crc = crc16ccitt(testdata)

    print("testdata:", testdata)
    print("crc:", hex(crc))

    if crc != testcrc:
        print ("FAILED")
        sys.exit()

    print ("PASSED")
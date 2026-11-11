# smbus.py (dummy version for Windows testing)

# class SMBus:
#     def __init__(self, bus):
#         print("Dummy SMBus initialized on bus", bus)
#     
#     def write_byte_data(self, addr, reg, value):
#         print(f"Dummy write_byte_data to addr {addr}, reg {reg}, value {value}")
#     
#     def read_i2c_block_data(self, addr, reg, length):
#         # Return a list of zeros as dummy data.
#         return [0] * length
# 
# # For compatibility with code that does "import smbus"
# SMBus = SMBus
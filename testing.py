# a = True

# if a:
#     b = "a"
# else:
#     b = "b"

# print(b)


# string = "a"
# list1 = list(string.split(","))
# print(list1)
# print(type(list1))


# string = "qqqqqq/123.ext"

# print(string.split("/")[0])

# import shutil
# import os

# source_dir = "/home/demo/automation/"
# source_item = "file.txt"
# new_item_name = "new_file.txt"
# tmp_workspace = "/home/demo/automation/tmp_workspace/"

# shutil.move(
#     os.path.join(source_dir, source_item), os.path.join(source_dir, new_item_name)
# )


# list_a = [".mp4"]
# ext = ".mp4"

# if ext in list_a:
#     print("True")

# n = 100
# # list = [i=n while i<=n+10: i++]
# list = list(range(n, n + 10, 1))
# print(list)


import socket

# fqdn = socket.getfqdn()
# hostname = socket.gethostname()
# IPAddr = socket.gethostbyname(hostname)
# print(f"FQDN is: {fqdn}")
# print("Your Computer Name is:" + hostname)
# print("Your Computer IP Address is:" + IPAddr)


# # import socket
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.connect(("8.8.8.8", 80))
# print(s.getsockname()[0])
# s.close()

# port = 30000
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.settimeout(5)
# try:
#     # Get host ip:
#     sock.connect(("8.8.8.8", 80))
#     host_address = sock.getsockname()[0]
#     # Get port statsu:
#     sock.bind((host_address, port))
# except socket.error as err:
#     print("Port is not open:", str(err))
# finally:
#     sock.close()

# def get_host_ip():
#     host_name = socket.gethostname()
#     ip_address = socket.gethostbyname(host_name)
#     return ip_address


# current_ip = get_host_ip()
# print("Current IP Address:", current_ip)


# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# result = sock.connect_ex(("192.168.11.123", 22))
# print(result)
# if result == 0:
#     print("Port is open")
# else:
#     print("Port is not open")
# sock.close()


# def check_socket(port: int):
#     """Checks provided port number for availability"""
#     # Very clever, works perfectly. Instead of gmail or 8.8.8.8, you can also use the IP
#     # or address of the server you want to be seen from, if that is applicable.
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.settimeout(5)
#     logger.debug(f"Current sock: {sock}")
#     try:
#         # Get host ip:
#         sock.connect(("8.8.8.8", 80))
#         host_address = sock.getsockname()[0]
#         logger.debug(f"Current host_address: {host_address}")
#         # Get port statsu:
#         sock.bind((host_address, port))
#         logger.info(f"Port {port} is open.")
#         return "open"
#     except (Exception, KeyboardInterrupt, socket.error) as err:
#         # print("Port is not open:", str(err))
#         logger.info(f"Port {port} is NOT open: {err} \n Checking next one...")
#         return "busy"
#     finally:
#         sock.close()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(s.connect_ex(("localhost", 8001)) == 0)


ffmpeg -y -i vid1.mp4 -ss 1 -vf scale='1920x1080' -an -r 30 -vcodec libx264 vid1_out.mp4
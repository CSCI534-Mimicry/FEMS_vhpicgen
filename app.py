# Only support python 2.7 & 64 bit OS
import sys
import time
import inspect, os, time
sys.path.append(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+ '/libs64')

from flask import Flask, request
from flask_cors import *
import vhmsg_python

import threading
import time
sem = threading.Semaphore()

app = Flask('FENS_vhpicgen', static_folder="static/")

action_units = {
    'au_1': 0.0,    # LR
    'au_2': 0.0,    # LR
    'au_4': 0.0,    # LR
    'au_5': 0.0,
    'au_6': 0.0,
    'au_7': 0.0,
    'au_10': 0.0,
    'au_12': 0.0,   # LR
    'au_25': 0.0,
    'au_26': 0.0,
    'au_45': 0.0    # LR
}

curr_sex = ""

def reset_au():
    for key in action_units:
        action_units[key] = 0
    print(action_units)
    send_adjust_au_msg(0)

def set_au(au_1, au_2, au_4, au_5, au_6, au_7, au_10, au_12, au_25, au_26, au_45):
    reset_au()
    action_units['au_1'] = au_1
    action_units['au_2'] = au_2
    action_units['au_4'] = au_4
    action_units['au_5'] = au_5
    action_units['au_6'] = au_6
    action_units['au_7'] = au_7
    action_units['au_10'] = au_10
    action_units['au_12'] = au_12
    action_units['au_25'] = au_25
    action_units['au_26'] = au_26
    action_units['au_45'] = au_45

def set_au_from_form(form_dict):
    reset_au()
    for key in action_units:
        if key in form_dict:
            action_units[key] = form_dict[key]

def is_action_unit_key_has_lr(key):
    return key == 'au_1' or key == 'au_2' or key == 'au_4' or key == 'au_12' or key == 'au_45'

def send_adjust_au_msg(wait_time=2):
    send_msg_arr = []
    for key in action_units:
        if is_action_unit_key_has_lr(key) == True:
            send_msg_arr.append('sbm char * viseme ' + key + '_left ' + str(action_units[key]))
            send_msg_arr.append('sbm char * viseme ' + key + '_right ' + str(action_units[key]))
        else:
            send_msg_arr.append('sbm char * viseme ' + key + ' ' + str(action_units[key]))
    send_msg(send_msg_arr, wait_time)

def set_male():
    global curr_sex
    curr_sex = "m"
    send_msg(["renderer destroyAllCharacters", "vrProcEnd sbm", "renderer create Brad Brad"], 4, True)

def set_female():
    global curr_sex
    curr_sex = "f"
    send_msg(["renderer destroyAllCharacters", "vrProcEnd sbm", "renderer create Rachel Rachel"], 4, True)

def PrintResult(result):
	print "SUCCESS" if result == 0 else "FAILURE" 
	
def vhmsg_callback(str):
	print str

def connect():
    print "Attempting to connect..."
    ret = vhmsg_python.connect("localhost", "DEFAULT_SCOPE", "61616")
    PrintResult(ret)

def close():
    print "Attempting to close..."
    ret = vhmsg_python.close()
    PrintResult(ret)

def send_msg(msg_arr, wait_time=1, mid_wait=False):
    for msg_str in msg_arr:
        print "Attempting to send \"" + msg_str + "\" ..."
        ret = vhmsg_python.send(msg_str)
        PrintResult(ret)

        if mid_wait:
            print "Attempting to wait..."
            ret = vhmsg_python.wait(1)
            PrintResult(ret)

    print "Attempting to wait..."
    ret = vhmsg_python.wait(1)
    PrintResult(ret)
    time.sleep(wait_time)

def record():
    print "Attempting to send ..."
    ret = vhmsg_python.send("renderer_record start")
    PrintResult(ret)

    print "Attempting to wait for recording ..."
    ret = vhmsg_python.wait(1)
    PrintResult(ret)

    time.sleep(1.5)

    print "Attempting to send ..."
    ret = vhmsg_python.send("renderer_record stop")
    PrintResult(ret)

    print "Attempting to wait..."
    ret = vhmsg_python.wait(1)
    PrintResult(ret)

    time.sleep(1.5)

@app.route("/receive_au", methods=["POST"])
@cross_origin()
def receive_au():
    global curr_sex
    sex = request.json["sex"]
    user = request.json["user"]
    mny = request.json["mny"]

    sem.acquire()
    connect()
    set_au_from_form(request.json)
    if sex != curr_sex:
        if sex == "m":
            set_male()
        elif sex == "f":
            set_female()
    
    send_adjust_au_msg()

    record()

    close()
    
    os.system("ffmpeg.exe -i E:/vhtoolkit/bin/vhtoolkitUnity/movie.avi -frames:v 1 static/out1.png")
    while not os.path.exists("static/out1.png"):
        connect()
        record()
        close()
        os.system("ffmpeg.exe -i E:/vhtoolkit/bin/vhtoolkitUnity/movie.avi -frames:v 1 static/out1.png")
    filename = "out-" + str(user) + "-" + str(mny) + ".png"
    os.system("magick static/out1.png -flip static/" + filename)
    if os.path.exists("static/out1.png"):
        os.remove("static/out1.png")
    
    sem.release()
    return "/" + filename

@app.route('/')
def index():
    return 'Hello, worker!'

CORS(app, supports_credentials=True)
app.run(port=22500)

# renderer background file Ict07.jpg
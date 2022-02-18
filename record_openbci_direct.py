import numpy as np
# import pandas as pd
import os
# from pylsl import StreamInlet, resolve_byprop
# from sklearn.linear_model import LinearRegression
import time
# from .stream import find_muse
# from .muse import Muse
# from .constants import LSL_SCAN_TIMEOUT, LSL_EEG_CHUNK, LSL_PPG_CHUNK, LSL_ACC_CHUNK, LSL_GYRO_CHUNK
import writetocsv
# from mne_bids import BIDSPath
# import pyautogui
import socket
import json  
# import sys
import lib.open_bci_v3_modded_by_oleg as bci

def record_obci_direct(duration, logfile=None, recfile = None, port=None):
    channel_name_string = '"timestamp","NA","TP9","NA","NA","NA","TP10","NA","NA"'
    ch_names = ["NA","TP9","NA","NA","NA","TP10","NA","NA"]    
    rec = []
    timestamp = []
    
    def mycallback(sample):
        rec.append(sample.channel_data)
        timestamp.append(sample.id)
        if sample.id == 250:       
            
            udppacket = {'header': UDP_HEADER, 'data': rec[-250:], 'timestamp':timestamp[-250:], 'num_channels': 8, 'srate': 250,'ch_names': ch_names, 'device_type': device_type}
            #print("sending UDP", len(json.dumps(udppacket) ))
            sock.sendto(bytes(json.dumps(udppacket), 'utf-8'), (UDP_IP, UDP_PORT))
       
    UDP_IP = "127.0.0.1"
    UDP_PORT=8890
    UDP_HEADER = "EEG_DATA"
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # UDP
    print("requested duration of recording is ", duration)
    device_type = "OPENBCI"
    filename = os.path.join(os.getcwd(
    ), logfile[0:3], recfile + f"{device_type}_recording_{time.strftime('%Y-%m-%d-%H.%M.%S', time.localtime())}.csv")
    print('Recording file name {0}'.format(filename))
    writetocsv.writelogcsv('Recording file name {0} '.format(filename), logfile)


    tic = time.time()
    board = bci.OpenBCIBoard(port)
    # eeg_channels =board.getNbEEGChannels()
    # aux_channels = board.getNbAUXChannels()
    # srate = board.getSampleRate()
    # Nchan = 8
    print("board init time ", time.time() - tic)

    print("requested recording duration is ", duration , " seconds")
    t_init = time.time()
    writetocsv.writelogcsv('Recording start time = {0} '.format(t_init), logfile)
    rec = []
    timestamp = []
    #board.test_signal(signal=4)
    board.start_streaming(mycallback, duration)
    board.stop()
    print("stopping stream")   
    board.disconnect()
    print("disconnecting board")
    
    
    timestamp_np = np.asarray(timestamp)
    timestamp_np.shape = (timestamp_np.shape[0], 1)
    output = np.concatenate( (timestamp_np, np.asarray(rec)), axis = 1)
    
    
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)
    time.sleep(0.1)        
    np.savetxt(filename, output, delimiter = ',', header = channel_name_string,comments='')
    sock.close()
  
  
    if len(output) == 0:
        print("ZERO FILE LENGTH, DAMAGED RECORDING STREAM!!!")
  
    print('Done - wrote file: ' + filename + '.')
    #sys.exit()




import numpy as np
import pandas as pd
import os
from typing import Union, List, Optional
from pathlib import Path
from pylsl import StreamInlet, resolve_byprop
from sklearn.linear_model import LinearRegression
from time import time, sleep, strftime, gmtime
from .stream import find_muse
from .muse import Muse
from .constants import LSL_SCAN_TIMEOUT, LSL_EEG_CHUNK, LSL_PPG_CHUNK, LSL_ACC_CHUNK, LSL_GYRO_CHUNK
import subprocess
import json
import platform

# Define EEG bands
fs = 256
eeg_bands = {'Delta': (0, 4),
             'Theta': (4, 8),
             'Alpha': (8, 12),
             'Beta': (12, 30),
             'Gamma': (30, 45)}
electrodes = ["AF7", "AF8", "TP9", "TP10"]
threshold_tei = 0.8
with open('experiment_config.json') as f:
    config = json.load(f)

def plot_power(eeg_bands, eeg_band_fft, xlabel):
    # Plot the data (using pandas here cause it's easy)
    df = pd.DataFrame(columns=['band', 'val'])
    df['band'] = eeg_bands.keys()
    df['val'] = [eeg_band_fft[band] for band in eeg_bands]
    ax = df.plot.bar(x='band', y='val', legend=False)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Mean band Amplitude")


def fft_power(data, xlabel):
    # Get real amplitudes of FFT (only in postive frequencies)
    fft_vals = np.absolute(np.fft.rfft(data))

    # Get frequencies for amplitudes in Hz
    fft_freq = np.fft.rfftfreq(len(data), 1.0 / fs)

    # Take the mean of the fft amplitude for each EEG band
    eeg_band_fft = dict()
    for band in eeg_bands:
        freq_ix = np.where((fft_freq >= eeg_bands[band][0]) &
                           (fft_freq <= eeg_bands[band][1]))[0]
        eeg_band_fft[band] = np.mean(fft_vals[freq_ix])

    # plot_power(eeg_bands, eeg_band_fft, xlabel)
    # betapower/(alphapower+thetapower)
    task_engagement_index = eeg_band_fft['Beta'] / (eeg_band_fft['Alpha'] + eeg_band_fft['Theta'])
    return task_engagement_index


def anal_data_raw(res):
    task_engagement_index = []
    for i in range(0, 2):
        task_engagement_index.append(fft_power(res[electrodes[i]].values, electrodes[i]))
    print(task_engagement_index)
    if np.mean(task_engagement_index) > config["TEILow"]:  # To add enemies
        with open(config["LoggingLocation"], 'a') as f:
            f.write('TEI: ' + str(np.mean(task_engagement_index)) + ' Time: ' + str(time()) + '\n')
            f.write('add' + '\n')
            print("Add")
    else:
        with open(config["LoggingLocation"], 'a') as f:
            f.write('TEI: ' + str(np.mean(task_engagement_index)) + ' Time: ' + str(time()) + '\n')
            f.write('idle' + '\n')

def set_first_threshold(res,duration):
    task_engagement_index = []
    for i in range(0, 2):
        task_engagement_index.append(fft_power(res[electrodes[i]].values, electrodes[i]))

    if duration == config["Lowtimeframe"]:
        with open(config["LowThresholdLocation"], 'a') as f:
            f.write(str(np.mean(task_engagement_index)) + '\n')
            # print(np.mean(task_engagement_index))
    elif duration == config["Hightimeframe"]:
        with open(config["HighThresholdLocation"], 'a') as f:
            f.write(str(np.mean(task_engagement_index)) + '\n')



# Records a fixed duration of EEG data from an LSL stream into a CSV file
def record(
        duration: int,
        filename=None,
        dejitter=False,
        data_source="EEG",
        continuous: bool = True,
) -> None:
    def run_blueMuse():
        os.system('start bluemuse://start?streamfirst=true')
    chunk_length = LSL_EEG_CHUNK
    if data_source == "PPG":
        chunk_length = LSL_PPG_CHUNK
    if data_source == "ACC":
        chunk_length = LSL_ACC_CHUNK
    if data_source == "GYRO":
        chunk_length = LSL_GYRO_CHUNK

    if not filename:
        filename = os.path.join(os.getcwd(), "%s_recording_%s.csv" %
                                (data_source,
                                 strftime('%Y-%m-%d-%H.%M.%S', gmtime())))

    # p = subprocess.Popen('OpenBlueMuse.bat', shell=True, stdout=subprocess.PIPE)
    run_blueMuse()
    sleep(3)
    # stdout, stderr = p.communicate()
    # if p.returncode == 0:
    #     print('Blue Muse connected pre start record')

    print("Looking for a %s stream..." % (data_source))
    streams = resolve_byprop('type', data_source, timeout=LSL_SCAN_TIMEOUT)

    if len(streams) == 0:
        print("Can't find %s stream." % (data_source))
        return

    print("Started acquiring data.")
    inlet = StreamInlet(streams[0], max_chunklen=chunk_length)

    info = inlet.info()
    description = info.desc()

    Nchan = info.channel_count()

    ch = description.child('channels').first_child()
    ch_names = [ch.child_value('label')]
    for i in range(1, Nchan):
        ch = ch.next_sibling()
        ch_names.append(ch.child_value('label'))

    res = []
    timestamps = []
    markers = []
    t_init = time()
    time_correction = inlet.time_correction()
    last_written_timestamp = None
    print('Start recording at time t=%.3f' % t_init)
    print('Time correction: ', time_correction)
    txtfile = "muse_logging.txt"
    while (time() - t_init) < duration:
        try:
            data, timestamp = inlet.pull_chunk(timeout=1.0, max_samples=chunk_length)
        except:
            print("reconnecting to LSL source...")
            run_blueMuse()
            try:
                streams = resolve_byprop('type', data_source, timeout=LSL_SCAN_TIMEOUT)
                inlet = StreamInlet(streams[0], max_chunklen=chunk_length, recover=False)
            except:
                print("unable to reconnect to LSL source")
            continue
        if timestamp:
            res.append(data)
            timestamps.extend(timestamp)
            tr = time()
            # Save every TEIInterval
            if continuous and (last_written_timestamp is None or last_written_timestamp + config["TEIInterval"] < timestamps[-1]):
                _save(
                    duration,
                    filename,
                    res,
                    timestamps,
                    time_correction,
                    dejitter,
                    markers,
                    ch_names,
                    last_written_timestamp=last_written_timestamp,
                )
                last_written_timestamp = timestamps[-1]
                print("last_written_timestamp " + str(last_written_timestamp))

    time_correction = inlet.time_correction()
    print("Time correction: ", time_correction)

    _save(
        duration,
        filename,
        res,
        timestamps,
        time_correction,
        dejitter,
        markers,
        ch_names,
    )

    print("Done - wrote file: {}".format(filename))


def _save(
        duration: int,
        filename: Union[str, Path],
        res: list,
        timestamps: list,
        time_correction,
        dejitter: bool,
        # inlet_marker,
        markers,
        ch_names: List[str],
        last_written_timestamp: Optional[float] = None,
):
    try:
        res = np.concatenate(res, axis=0)
        timestamps = np.array(timestamps) + time_correction
    except:
        timestamps = [time()-5,time()]
        print("Res empty")
        return

    if dejitter:
        y = timestamps
        X = np.atleast_2d(np.arange(0, len(y))).T
        lr = LinearRegression()
        lr.fit(X, y)
        timestamps = lr.predict(X)

    res = np.c_[timestamps, res]
    data = pd.DataFrame(data=res, columns=["timestamps"] + ch_names)

    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # If file doesn't exist, create with headers
    # If it does exist, just append new rows
    # if not Path(filename).exists():
        # print("Saving whole file")
        # data.to_csv(filename, float_format='%.3f', index=False)
    # else:
        # print("Appending file")
        # truncate already written timestamps


    data = data[data['timestamps'] > last_written_timestamp]
    #Set low threshold
    if len(data[electrodes[0]].values): # If there are values from electrodes
        if duration == config["DurationAll"]: # Main run
            anal_data_raw(data)
        else: # Electrodes choose
            set_first_threshold(data,duration)
        # data.to_csv(filename, float_format='%.3f', index=False, mode='a', header=False)
# Rercord directly from a Muse without the use of LSL


def record_direct(duration,
                  address,
                  filename=None,
                  backend='auto',
                  interface=None,
                  name=None):
    if backend == 'bluemuse':
        raise (NotImplementedError(
            'Direct record not supported with BlueMuse backend. Use record after starting stream instead.'
        ))

    if not address:
        found_muse = find_muse(name, backend)
        if not found_muse:
            print('Muse could not be found')
            return
        else:
            address = found_muse['address']
            name = found_muse['name']
        print('Connecting to %s : %s...' % (name if name else 'Muse', address))

    if not filename:
        filename = os.path.join(
            os.getcwd(),
            ("recording_%s.csv" % strftime("%Y-%m-%d-%H.%M.%S", gmtime())))

    eeg_samples = []
    timestamps = []

    def save_eeg(new_samples, new_timestamps):
        eeg_samples.append(new_samples)
        timestamps.append(new_timestamps)

    muse = Muse(address, save_eeg, backend=backend)
    muse.connect()
    muse.start()

    t_init = time()
    print('Start recording at time t=%.3f' % t_init)

    while (time() - t_init) < duration:
        try:
            sleep(1)
        except KeyboardInterrupt:
            break

    muse.stop()
    muse.disconnect()

    timestamps = np.concatenate(timestamps)
    eeg_samples = np.concatenate(eeg_samples, 1).T
    recording = pd.DataFrame(
        data=eeg_samples, columns=['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX'])

    recording['timestamps'] = timestamps

    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

    recording.to_csv(filename, float_format='%.3f')
    print('Done - wrote file: ' + filename + '.')

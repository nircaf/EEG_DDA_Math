import csv
import time

def writelogcsv(txttocsv, logfile):
    rowtocsv = [txttocsv, time.ctime(), time.time()]
    with open(logfile, 'a', newline='') as f:
        # create the csv writer
        writer = csv.writer(f)
        writer.writerow(rowtocsv)
    f.close()

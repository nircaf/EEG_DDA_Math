# import muselsl.viewer_v2 as viewing
from muselsl import viewer_v2
import os
# this app is called from command line with following arguments:
#duration of recording
#name of session log file
#name of recording file
#recording device type

if __name__ == '__main__':
    os.system('start bluemuse://start?streamfirst=true')
    viewer_v2.view()
    #exit()
    #sys.exit(0)

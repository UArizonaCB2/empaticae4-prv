"""
@brief : A quick code to calculate the HRV using using Empatica IBI.
@errata : Empatica's IBI drops points that do not lead to the detection of R-R peaks.
@date updated : 5.23.22

Recommended Window sizes for each PRV (Pulse Rate Variability) metric.

1. RMSSD : 60 seconds.
2. HR Max - HR Min : 120 seconds.
3. NN50 - 120 seconds.
4. pNN50 - 120 seconds.
5. SDNN - 60 seconds.

"""

import pandas as pd
import numpy as np
import sys

def main():
    args = sys.argv
    output_dir = None
    if len(args) < 2:
        print("python prv.py <IBI File> [Output directory]")
        exit(1)

    if len(args) > 2:
        # The output directory has been specified on command line
        output_dir = args[2]

    filename = args[1]
    raw_data = pd.read_csv(open(filename, 'r'))
    
    time = raw_data[raw_data.columns[0]].values
    data = raw_data[' IBI'].values

    # Calculating time domain metrics PRV.
    values_rmssd = chunckData(time, data, 60, rmssd)
    values_hrmaxmin = chunckData(time, data, 120, hrMaxMin)
    values_nn50 = chunckData(time, data, 120, nn50)
    values_pnn50 = chunckData(time, data, 120, pnn50)
    values_sdnn = chunckData(time, data, 60, sdnn)

    # Save these files if the output directory has been specified.
    if not output_dir is None:
        values_rmssd.to_csv(output_dir+'/rmssd.csv', index=False)
    else:
        print('Output not saved. Not output directory specified')

def getRMSSD(time, data):
    return chunckData(time, data, 60, rmssd) 

def getHRMaxMin(time, data):
    return chunckData(time, data, 120, hrMaxMin)

def getNN50(time, data):
    return chunckData(time, data, 120, nn50)

def getPNN50(time, data):
    return chunckData(time, data, 120, pnn50)

def getSDNN(time, data):
    return chunckData(time, data, 60, sdnn) 

def chunckData(time : np.array, data : np.array, window_size : int, operation) -> np.array:
    """
    Method which chunks the data down using the given window size
    and then performs the requested operation.

    Parameters
    -----------
    data : 1d.array
        Raw IBI (Inter-beat Interval) data. 
    window_size (seconds) : int
        Window size in seconds to the chunk the data into
    """
    
    start_index = 0
    values = []
    start_time = []
    end_time = []
    for t in range(0, len(time)):
    # Make sure to take care of the last tail portion.
    # We do not take into consideration any slice of data that is less than the window size.
        if time[t] - time[start_index] >= window_size:  
            if len(data[start_index : t-1]) > 0:
                _operation = operation(data[start_index : t-1])
                values.append(_operation)
                start_time.append(time[start_index])
                end_time.append(time[t])
            start_index = t

    return pd.DataFrame({'startTime':start_time, 'endTime':end_time, 'values':values}) 

def rmssd(ibi : np.array):
    """
    Method which calculates the RMSSD (Root Mean Square Standard Diviation

    Parameters
    -----------
    ibi : 1d.array
        An array of inter beat interval data over which the RMSSD will be calculated.
    """
    rmssd = 0
    sum = 0
    for i in range(1, len(ibi)):
        sum = sum + ((ibi[i] - ibi[i-1]) * (ibi[i] - ibi[i-1]))

    if sum > 0:
        rmssd = np.sqrt(sum / (len(ibi)-1)) 

    return rmssd

def sdnn(ibi : np.array):
    return np.std(ibi)

def nn50(ibi : np.array):
    nn50 = 0
    for i in range(1, len(ibi)):
        if ibi[i] - ibi[i-1] > 0.05:
            nn50 += 1
    return nn50

def pnn50(ibi : np.array):
    return (nn50(ibi) * 100) / len(ibi)

def hrMaxMin(ibi : np.array):
    hrmax = 0
    hrmin = 1000

    for i in range(0, len(ibi)):
        hr = 60 / ibi[i]
        if hr > hrmax:
            hrmax = hr
        if hr < hrmin:
            hrmin = hr

    return hrmax - hrmin

if __name__ == '__main__':
    main()

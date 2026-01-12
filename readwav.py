import argparse
import wave
import struct
import sys
import matplotlib.pyplot as plt


from dataclasses import dataclass
from enum import Enum


def decode_bit(dt):
    if 80 <= dt <= 120:
        return 0
    if 175 <= dt <= 225:
        return 1
    return 'err'


@dataclass
class DCFData:
    startofminute = 0 #
    M = 0
    A1 = 0
    Z1 = 0
    Z2 = 0
    A2 = 0
    S = 0
    minutes = 0
    P1 = 0
    hours = 0
    P2 = 0
    DoM = 0
    DoW = 0
    Month = 0
    Year = 0
    P3 = 0


def validate(dcfdata, dp1, dp2, dp3):
    d = dcfdata
    p1v = True if (d.P1 + dp1) & 1 == 0 else False
    p2v = True if (d.P2 + dp2) & 1 == 0 else False
    p3v = True if (d.P3 + dp3) & 1 == 0 else False
    res = d.M == 0 and d.S == 1 and p1v and p2v and p3v
    status = f'M: {d.M == 0:1}, S: {d.S == 1:1}, P1: {p1v:1}, P2: {p2v:1}, P3: {p3v:1}'
    return res, status



class SyncState(Enum):
    Unsynched = 1   # Minute marker not known
    Low = 2         # Minute marker known low amplitude
    High = 3        # Minute marker known high amplitude


def BCD(l):
    coeff = [1, 2, 4, 8, 10, 20, 40, 80]
    res = 0
    for i, b in enumerate(l):
        res += b * coeff[i]
    return res


def Parity(l):
    return sum(l)


def DCF77Decode(l):
    d = DCFData()
    day = {0: '-', 1:'Mon', 2:'Tue', 3:'Wed', 4:'Thu', 5:'Fri', 6:'Sat', 7:'Sun'}

    d.M = l[0]
    d.R = l[15]
    d.A1 = l[16]
    d.Z1, d.Z2 = l[17], l[18]
    d.A2 = l[19]
    d.S = l[20]

    d.P1, d.P2, d.P3 = l[28], l[35], l[58]

    tz = ' '
    if d.Z1 == 1 and d.Z2 == 0:
        tz = 'CEST'
    if d.Z1 == 0 and d.Z2 == 1:
        tz = 'CST'

    minutes =   l[21:28]
    hours =     l[29:35]
    days =      l[36:42]
    dayofweek = l[42:45]
    month =     l[45:49]
    year =      l[50:58]

    mp = Parity(minutes)
    hp = Parity(hours)
    dp = Parity(l[36:58])

    d.minutes, d.hours = BCD(minutes), BCD(hours)
   
    d.DoM, d.Month, d.Year = BCD(days), BCD(month), BCD(year)
    d.DoW = BCD(dayofweek)

    res, status = validate(d, mp, hp, dp)

    decode = 'good ' if  res else 'error'
    print(f'decode: ({decode}) {d.DoM:02}-{d.Month:02}-{d.Year:02} ({day[d.DoW]}) {d.hours:02}:{d.minutes:02} ({tz:4}) - {status}')

  

def read_wav_file(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_rate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        
        audio_data = wav_file.readframes(n_frames)
        
        return {
            'channels': n_channels,
            'sample_width': sample_width,
            'frame_rate': frame_rate,
            'n_frames': n_frames,
            'audio_data': audio_data
        }


def processdfc77(data, args):
    hilo_thr = args.threshold
    t_silent = 1700
    thi, tlo  = 0, 0
    state = SyncState.Unsynched
    s = 0
    bits = [-1 for x in range(59)]


    filter = SampleFilter(10)


    vals = [0 for x in range(10)]
    for i, d in enumerate(data):
       
        val = filter.add(max(d[0], 4000))
        if val == None:
            continue


        if state == SyncState.Unsynched:
            if val < hilo_thr:
                 state = SyncState.Low
            else:
                 state = SyncState.High
            continue

        if state == SyncState.Low:
            if val < hilo_thr:
                tlo += 1
            else:
                #print(f'low  -> high - low  time {tlo:3}, s {s:3}')
                res = decode_bit(tlo)
                if res == 'err':
                    #print(f'error in bit decode at {i}: {tlo}')
                    state = SyncState.Unsynched
                    thi = 0
                    tlo = 0
                    s = 0
                    continue
                bits[s] = res
                tlo = 0
                state = SyncState.High
            continue
    
        if state == SyncState.High:
            if val > hilo_thr:
                thi += 1
            else:
                if thi > 1600:
                    #print(f'high -> low  - high time {thi:3}')  
                    print(f'#### MINUTE MARK #### - {i} {s}')
                    if s == 58:
                        print(bits[:14])
                        DCF77Decode(bits)
                        print()
                    s = 0
                else:
                    s += 1
                thi = 0
                state = SyncState.Low
            continue



class SampleFilter:
    def __init__(self, average=10):
        self.n = average
        self.data = [0 for x in range(average)]
        self.samples = 0


    def add(self, value):
        self.data[self.samples % self.n] = value
        self.samples += 1
        if self.samples < self.n:
            return
        return sum(self.data)//self.n


def plot(data, args):
    fig, ax = plt.subplots()

    n = 5
    filter = SampleFilter(5)
   
    y = []
    y2 = [0 for x in range(n)]
    for d in data:
        val = max(d[0], 4000)
        y.append(val)
        val2 = filter.add(val)
        if val2 != None:
            y2.append(val2)
    t = [x * 0.001 for x in range(len(y))]

    ax.plot(t[args.pbeg:args.pend], y[args.pbeg:args.pend])
    ax.plot(t[args.pbeg:args.pend], y2[args.pbeg:args.pend])

    ax.set(xlabel='time (s)', ylabel='Ampl',
        title='DCF77 samples')
    ax.grid()
    #fig.savefig("test.png")
    plt.show()   


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Decode DCF77 from a WAV file')
    parser.add_argument('input', nargs='?', default='samples/DCF77_Puls_1000_10-01-2026_16-02-34.wav',
                        help='input WAV file (default: sample file)')
    parser.add_argument('--plot', action='store_true', help='show a plot of the samples and exit')
    parser.add_argument('--threshold', type=int, default=20000, help='high/low threshold')
    parser.add_argument('--pbeg', type=int, default=0, help='start sample for plot')
    parser.add_argument('--pend', type=int, default=-1, help='end sample for plot')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose output')
    args = parser.parse_args()
    

    res = read_wav_file(args.input)
    if args.verbose:
        print(f'{res["channels"]=}')
        print(f'{res["sample_width"]=}')
        print(f'{res["frame_rate"]=}')
        print(f'{res["n_frames"]=}')

    #data = struct.iter_unpack("H", res['audio_data'])
    data = struct.iter_unpack("h", res['audio_data']) # signed words


    if args.plot:
        plot(data, args)
        sys.exit()

    processdfc77(data, args)

    
  
                 
             

        
import src.filter as filter

from dataclasses import dataclass
from enum import Enum


@dataclass
class DCFData:
    A1, A2 = 0, 0
    Z1, Z2 = 0, 0
    M, S = 0, 0
    minutes, hours = 0, 0
    P1, P2, P3 = 0, 0, 0
    DoM, Month, Year = 0, 0, 0
    DoW = 0
    # status of decode, not part of DCF77
    valid = False


class SyncState(Enum):
    Init = 1  # start state
    Low = 2   # 
    High = 3


class DCF77Util:

    def decode_bit(dt:int) -> int|str:
        if 80 <= dt <= 120:
            return 0
        if 175 <= dt <= 225:
            return 1
        return 'err'
    

    def validate(dcfdata:DCFData, dp1:int, dp2:int, dp3:int) -> (bool, str):
        d = dcfdata
        p1v = True if (d.P1 + dp1) & 1 == 0 else False
        p2v = True if (d.P2 + dp2) & 1 == 0 else False
        p3v = True if (d.P3 + dp3) & 1 == 0 else False
        valid = d.M == 0 and d.S == 1 and p1v and p2v and p3v
        status_text = f'M: {d.M == 0:1}, S: {d.S == 1:1}, P1: {p1v:1}, P2: {p2v:1}, P3: {p3v:1}'
        return valid, status_text
    
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

        mp = DCF77Util.Parity(minutes)
        hp = DCF77Util.Parity(hours)
        dp = DCF77Util.Parity(l[36:58])

        d.minutes, d.hours = DCF77Util.BCD(minutes), DCF77Util.BCD(hours)
    
        d.DoM, d.Month, d.Year = DCF77Util.BCD(days), DCF77Util.BCD(month), DCF77Util.BCD(year)
        d.DoW = DCF77Util.BCD(dayofweek)

        valid, status_text = DCF77Util.validate(d, mp, hp, dp)
        d.valid = valid

        if valid:
            decode = 'good '
            s = ''
        else:
            decode = 'error'
            s = '- ' + status_text
        print(f'decode: ({decode}) {d.DoM:02}-{d.Month:02}-{d.Year:02} ({day[d.DoW]}) {d.hours:02}:{d.minutes:02} ({tz:4}) {s}')
        return d



class Decode:

    def __init__(self, threshold):
        self.synched = False
        self.goodcount = 0

        self.i = 0
        self.refm = 0
        self.hilo_thr = threshold
        self.t_silent = 1700 # quiet period is 1s + preceeding high period (minimum 1800)
        self.thi, self.tlo  = 0, 0
        self.state = SyncState.Init
        self.s = 0
        self.bits = [-1 for x in range(59)]

        self.flt = filter.SampleFilter(10)


    def state_init(self, val):
        if val < self.hilo_thr:
            self.state = SyncState.Low
        else:
            self.state = SyncState.High


    def state_low(self, val):
        if val < self.hilo_thr:
            self.tlo += 1
        else:
            # print(f'low  -> high - low  time {tlo:3}, s {s:3}')
            # roll back to state High if low interval is too short
            # could do the same in the opposite direction, but currently
            # not implemented
            if self.tlo < 17:
                self.thi = self.prevthi + self.tlo
                self.tlo = 0
                self.state = SyncState.High
                self.s -= 1
                return

            # Regular transition from low to high
            res = DCF77Util.decode_bit(self.tlo)
            if res == 'err':
                print(f'{self.state}: error in bit decode at {self.i}: {self.tlo}')
                self.state = SyncState.High
                self.thi = 0
                self.tlo = 0
                self.s = 0
                return

            #
            self.bits[self.s] = res
            self.tlo = 0
            self.state = SyncState.High


    def state_high(self, val):
        # if data is still high we just count the time ticks in this state
        if val > self.hilo_thr:
            self.thi += 1
        else:
            # Transition from high to low marks a new second (and of course minute)

            # Minute marker
            # this is where we decode the data buffer
            if self.thi > self.t_silent:
                # print(f'high -> low  - high time {thi:3}')  
                print(f'#### MINUTE MARK #### - {self.i} {self.s}')
                if self.s == 58: # the 59th second
                    d = DCF77Util.DCF77Decode(self.bits)

                    if not self.synched and d.valid:
                        if self.goodcount == 0:
                            self.refm = d.hours*60 + d.minutes
                            print(f'  ref minutes {self.refm}')
                            self.goodcount += 1
                        elif self.goodcount == 1:
                            if self.refm + 1 == d.hours*60 + d.minutes:
                                print(f'  two consecutive good decodes. time synched to {d.hours:02}:{d.minutes:02}')
                                self.synched = True
                            self.goodcount = 0
                else:
                    print(f'decode: (error) second {self.s}')
                self.s = 0
            else:
                self.s += 1
            self.prevthi = self.thi
            self.thi = 0
            self.state = SyncState.Low


    def process(self, data):
        for i, d in enumerate(data):
            self.i = i
            val = self.flt.add(max(d[0], 4000))
            #val = self.flt.median_add(max(d[0], 4000))
            if val == None:
                continue

            # print(f'{i}, {state},{val=}, {thi=}, {tlo=}')

            if self.state == SyncState.Init:
                self.state_init(val)
                continue

            if self.state == SyncState.Low:
                self.state_low(val)
                continue
        
            if self.state == SyncState.High:
                self.state_high(val)
                continue
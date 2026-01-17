import argparse
import struct
import sys
import src.dcf77 as dcf77
import src.plot as plot
import src.wavfile as wavfile


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
    

    res = wavfile.read_file(args.input)
    if args.verbose:
        print(f'{res["channels"]=}')
        print(f'{res["sample_width"]=}')
        print(f'{res["frame_rate"]=}')
        print(f'{res["n_frames"]=}')

    data = struct.iter_unpack("h", res['audio_data']) # signed words

    if args.plot:
        plot.plot(data, args)
        sys.exit()


    decode = dcf77.Decode(args.threshold)
    
    decode.process(data)

    
  
                 
             

        
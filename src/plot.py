import src.filter
import matplotlib.pyplot as plt

def plot(data, args):
    fig, ax = plt.subplots()

    n = 5
    flt = filter.SampleFilter(5)
   
    y = []
    y2 = [0 for x in range(n)]
    for d in data:
        val = max(d[0], 4000)
        y.append(val)
        val2 = flt.add(val)
        if val2 != None:
            y2.append(val2)
    t = [x * 0.001 for x in range(len(y))]

    ax.plot(t[args.pbeg:args.pend], y[args.pbeg:args.pend])
    ax.plot(t[args.pbeg:args.pend], y2[args.pbeg:args.pend])

    ax.set(xlabel='time (s)', ylabel='Ampl', title='DCF77 samples')
    ax.grid()
    #fig.savefig("test.png")
    plt.show()   
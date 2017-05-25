import matplotlib.pyplot as plt
import pyart

def plot_data(infilename, outpng, maxrange):
  radar = pyart.io.read_nexrad_archive(infilename)
  display = pyart.graph.RadarDisplay(radar)
  fig = plt.figure(figsize=(10, 10))

  ax = fig.add_subplot(221)
  display.plot('velocity', 1, ax=ax, title='Doppler Velocity',
             colorbar_label='',
             axislabels=('', 'North South distance from radar (km)'))
  display.set_limits((-maxrange, maxrange), (-maxrange, maxrange), ax=ax)
  ax = fig.add_subplot(222)
  display.plot('reflectivity', 0, ax=ax,
             title='Reflectivity lowest', colorbar_label='',
             axislabels=('', ''))
  display.set_limits((-maxrange, maxrange), (-maxrange, maxrange), ax=ax)

  ax = fig.add_subplot(223)
  display.plot('reflectivity', 1, ax=ax,
             title='Reflectivity second', colorbar_label='')
  display.set_limits((-maxrange, maxrange), (-maxrange, maxrange), ax=ax)

  ax = fig.add_subplot(224)
  display.plot('cross_correlation_ratio', 0, ax=ax,
             title='Correlation Coefficient', colorbar_label='',
             axislabels=('East West distance from radar (km)', ''))
  display.set_limits((-maxrange, maxrange), (-maxrange, maxrange), ax=ax)

  fig.savefig(outpng)
  
if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='plot some radar data')
  parser.add_argument('nexrad', help="volume scan filename")
  parser.add_argument('png', help="output png filename")
  parser.add_argument('range', help="maximum range to plot. default=300", default=300, type=float, nargs='?')
  args = parser.parse_args()

  print "Plotting {} into {} upto {} km".format(args.nexrad, args.png, args.range)
  plot_data(args.nexrad, args.png, args.range)

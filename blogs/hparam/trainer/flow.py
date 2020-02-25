import argparse
import hypertune
import logging

# Problem from GINO program (Liebman, Lasdon, Schrage, and Waren 1986)
# as quoted in SAS manual Version 8 on p340
# See: http://www.math.wpi.edu/saspdf/iml/chap11.pdf
# Reformulated slightly to meet boxed constrained optimization

def compute_delay(flow, x12, x32):
    # traffic on other roads, assuming all traffic that arrives
    # at an intersection has to leave it
    x13 = flow - x12
    x24 = x12 + x32
    x34 = x13 - x32

    # travel time on each road segment
    t12 = 5 + .1 * x12 / (1. - x12 / 10.);
    t13 = x13 / (1. - x13 / 30.);
    t32 = 1. + x32 / (1. - x32 / 10.);
    t24 = x24 / (1. - x24 / 30.);
    t34 = 5 + .1 * x34 / (1. - x34 / 10.);
  
    # total delay
    f = t12*x12 + t13*x13 + t32*x32 + t24*x24 + t34*x34;
    return(f);

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--x12', type=float, required=True)
    parser.add_argument('--x32', type=float, required=True)
    parser.add_argument('--flow', type=float, default=5.0)
    parser.add_argument('--job-dir', default='ignored') # output directory to save artifacts. we have none

    # get args and invoke model
    args = parser.parse_args()
    delay = compute_delay(args.flow, args.x12, args.x32)
    logging.info('{} Resulting delay: {}'.format(args.__dict__, delay)) 
    print('{} Resulting delay: {}'.format(args.__dict__, delay))

    # write out the metric so that the executable can be
    # invoked again with next set of metrics
    hpt = hypertune.HyperTune()
    hpt.report_hyperparameter_tuning_metric(
       hyperparameter_metric_tag='delay',
       metric_value=delay,
       global_step=1) 

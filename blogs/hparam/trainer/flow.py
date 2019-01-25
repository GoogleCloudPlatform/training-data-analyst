import argparse
import hypertune
import logging

def compute_delay(F, x1, x2, x3, x4, x5):
    t12 = F + .1 * x1 / (1. - x1 / 10.);
    t13 = x2 / (1. - x2 / 30.);
    t32 = 1. + x3 / (1. - x3 / 10.);
    t24 = x4 / (1. - x4 / 30.);
    t34 = F + .1 * x5 / (1. - x5 / 10.);
    f = t12*x1 + t13*x2 + t32*x3 + t24*x4 + t34*x5;
    return(f);

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--x1', type=float, required=True)
    parser.add_argument('--x2', type=float, required=True)
    parser.add_argument('--x3', type=float, required=True)
    parser.add_argument('--x4', type=float, required=True)
    parser.add_argument('--x5', type=float, required=True)
    parser.add_argument('--F', type=float, default=5.0)
    parser.add_argument('--job-dir', default='ignored') # output directory to save artifacts. we have none

    # get args and invoke model
    args = parser.parse_args()
    delay = compute_delay(args.F, args.x1, args.x2, args.x3, args.x4, args.x5)
    logging.info('{} Resulting delay: {}'.format(args.__dict__, delay)) 
    print('{} Resulting delay: {}'.format(args.__dict__, delay))

    # write out the metric so that the executable can be
    # invoked again with next set of metrics
    hpt = hypertune.HyperTune()
    hpt.report_hyperparameter_tuning_metric(
       hyperparameter_metric_tag='delay',
       metric_value=delay,
       global_step=1) 

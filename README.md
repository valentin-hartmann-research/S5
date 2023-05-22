# S5

This repository contains the code for generating the data, running the experiments and producing the plots of the paper "Secure Summation via Subset Sums: A New Primitive for Privacy-Preserving Distributed Machine Learning".
All scripts obtain their parameters from `experiment_params.py`, so you only need to specify them once there.

Start by installing the packages from `requirements.txt`.


## Generating the data
Simply run `data_generator.py`, which will produce a folder `data`.

## Running the experiments
- Adjust the variable `GUNICORN_PATH` in `run_experiments.py` to point to your Gunicorn installation.
- If you don't want to measure traffic but only runtime, simply run `run_experiments.py`. It will create a folder `results` with the runtimes.

### Measuring traffic
- Install tcpdump: `sudo apt-get install tcpdump`
- Set the variable `TRAFFIC_CAPTURE_BREAKS` in `run_experiments.py` to True. This will introduce 30 s breaks between the different experiments so that we can see in the traffic logs when one experiment ended and the next one started.
- Start tcpdump and then run the experiments by running `run_experiments.py`. To capture the data sent by the server:

  ```tcpdump -e -i lo 'src localhost && dst localhost && src port 5000 && tcp' > sent.txt```

  To capture the data received by the server:

  ```tcpdump -e -i lo 'src localhost && dst localhost && dst port 5000 && tcp' > received.txt```

  You might need to change `lo` to the name of your loopback interface (e.g., `lo0` on Mac).
- Extract the time and the packet size column of tcpdump's output:

  `cut -d ' ' -f 1,13 <tcpdump file> > <output file>`
  
- Run the cells in the Jupyter notebook `traffic_log_analysis.ipynb` to sum up the sizes of the packets belonging to the same experiment.

## Producing the plots
Run `plots.py`.
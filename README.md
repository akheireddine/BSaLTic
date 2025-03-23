Contact:
   - anissa.kheireddine@lip6.fr
   - etienne.renault@sipearl.com
   - souheib.baarir@lip6.fr
  
submitted by Anissa Kheireddine, Etienne Renault and Souheib Baarir

It contains the tools implementing. The artifact also contains the
scripts used to perform all or a demo benchmarks presented in the paper and
regenerate the figures from the results.

************************************************************************************************************************************************
******************** YOU CAN USE A VIRTUAL MACHINE WHERE BSALTIC IS ALREADY INSTALLED, SEE  https://akheireddine.github.io/ ********************
************************************************************************************************************************************************

This zip file contains:

   - sources/
        The sources of the development version of BSaLTic.
   - packages/
        It contains dependencies for building BSaLTic and running
        the various experiments.
   - examples/
	It contains some examples of SMV instances and some LTL properties. 
   - spot/
        The source code of spot.
   - bench/
        Contains the demo benchmark demo_benchmark.zip (a subset of the  main benchmark in DIMACS format NO NEED TO UNZIP),
	classified according the handled LTL property (after negation)
   	You can found the main benchmark "main_benchmark.zip" in: https://akheireddine.github.io/
	The main benchmark take over 16Go of space.	 
	If you want to run the main benchmark, place it in bench/ repository (NO NEED TO UNZIP).
   - results/
        This holds the consolidated results of the benchmark, as run by the provided
        scripts (see below). 
	It also contains the real CSV files and plots of the paper (in results/all). 
   - scripts/
        Contains scripts that generate the summary table and scatter-plots from csv files.
   - install.sh
        This is the installation for script BSaLTic, NuSMV, Spot and all dependencies.
   - demo.sh
        To run a subset of the main benmchark using a time-limit of 600 seconds and
        5 Go of memory limit.
   - ltl_generator.sh
	Script to generate LTL property for input SMV model(s)
   - OUTPUT.txt
        The prints obtained by running the demo benchmark (sh demo.sh) in the VM. 
   - benchmarks.sh
        Script to run the main or demo benchmark with various options and build a consolidated 
        CSV file.
   - analyze.sh 
        Script to run the analysis phase with various options for the demo or training benchmark and 
        generates the corresponding plots. 


==== HOW TO INSTALL THIS ARTIFACT IN THE VM ====

1. unzip the artifact somewhere in the VM (preferably not in /media repository)
2. run the following commands to install all tools and dependencies:

   $ sudo sh install.sh
   $ export LD_LIBRARY_PATH=<path-to-artifact-repository>/sources/NuSMV-2.6.0/NuSMV/lib:$LD_LIBRARY_PATH

The script install Spot in spot/ and BSaLTic in sources/. The binaries for 
BSaLTic have been compiled in two flavors:
  i) bsaltic_analyzer for the analysis part (study), and 
 ii) bsaltic for the experimentation part.


==== HOW TO RUN THE DEMO BENCHMARK ====

  Before running the rest of the commands, run (if not already done):
   $ export LD_LIBRARY_PATH=<path-to-artefact-repository>/sources/NuSMV-2.6.0/NuSMV/lib:$LD_LIBRARY_PATH
  
   Then:

    $ ./demo.sh

  it will run a subset of the main benchmark. It took 1h40 in the VM. We increased however, 
  the number of CPUs to 4 to speed up the benchmark. You can find the results time we obtained 
  in the csv file and scatter-plots at results/demo/. We also provided the whole output prints
  when running the demo benchmark in OUTPUT.txt
 
  The main benchmark took 1 week using 64 parallel runs in an Intel Xeon E5645 machines
  and 25 Go of memory-limit. You find the results time and scatter-plots presented in the paper
  in results/all directory.


#############################################################################################
#########                             DISCLAIMER                                    #########
######### The next sections explain how can we use BSaLTic with various parameters  #########
#############################################################################################



==== HOW TO USE BSaLTic ON ATOMIC INSTANCE  ====
   
  To run a specific BMC problem, you need to specify the model (.smv), the bound k and the LTL file (.ltl>. 
  The script bsaltic.sh can be used as follow:
    
    $ ./bsaltic.sh -k <int> [-selector <hf or none>] [-protect <e or dr>] -ltl <file.ltl> <file.smv>

  The LTL formula needs to be in SPOT's format. The atomic propositions are between "" : 
	GF ( "a > 3" ) 

  See https://spot.lrde.epita.fr/app/ for the LTL format.
  For instance:

    $ ./bsaltic.sh -k 20 -selector hf -protect dr -r 4 -o=results/compare_time.csv ltl examples/abp8.ltl examples/abp8.smv

  In here, we fix the Hf heuristic for the selector and the database reduction "dr" strategy for managing 
  the learnt clause databases (r=4 for the multiplicative factor). 
    
  To run the original MapleCOMSPS solver, no need of selector neither protect parameter:

    $ ./bsaltic.sh -k 20 -o=results/compare_time.csv ltl examples/abp8.ltl examples/abp8.smv

==== HOW TO RUN THE DEMO AND THE MAIN BENCHMARK ====

1) STUDY:

   To run the demo or the training benchmark for any LTL property do:

     $ ./analyze.sh -mode <demo | paper> -ltl all [-t <time-in-seconds> default is 200s] [-m <memory-in-Go> default is 10Go] [-g]

  For instance:

     $ ./analyze.sh -mode demo -ltl all -t 200 -m 5

   This will start bsaltic_analyzer, and creates many individual LOGs files in the
   analysis/demo/{ltl-property}/log directory, and then generates the 
   corresponding plots in analysis/demo/{ltl-property} with a timeout of 200 seconds
   and a memory limited to 5Go for the demo benchmark.

   The main benchmark takes about 4 days for analysis (64 parallel jobs) with time-limit of 6000s.
   We also provide the final LOGs files (used in the paper) in the directory analysis/training_log/.
   To regenerate the plots displayed in the paper from this LOGS, you can run
   the following command: 

     $ ./analyze.sh -mode paper -ltl all

   Plots are in analysis/training_log/{ltl-property}/ for each property

   If the Gurobi License is available, use option -g to apply the heuristic on the demo benchmark:

     $ ./analyze.sh -mode demo -ltl all -t 200 -m 5 -g

   To run the demo benchmark for a specific LTL property do:

     $ ./analyze.sh -mode demo -ltl persistence -t 200 -m 5


2) EXPERIMENTATION:

   To run the demo or the main benchmark for any LTL property do:

     $ ./benchmarks.sh -mode <demo | all> -ltl all -selector <all | hf | none> -protect <all | e | dr> [-t <time-in-seconds> default is 600s] [-m <memory-in-Go> default is 10Go]

   For instance:

     $ ./benchmarks.sh -mode all -ltl all -selector all -protect all -t 600 -m 5


   This will run the experiments on original MapleCOMSPS, BSaLTic-DHf and BSaLTic-Ehf solvers on bench/main_benchmarks.zip (download at: https://akheireddine.github.io). 
   It will create ONE csv file in results/all/ directory, in order to print out the summary table in the terminal.

   The demo benchmark takes 1h40 hours in the VM using a time-limit of 600s
   We increased however the number of CPUs to 4 to speed up the benchmark.
   The main benchmark takes about 1 week using a time-limit of 7200s (64 parallel jobs).

   You can found the results we obtained in the csv file at /results/demo/compare.csv
   and plots at /results/demo/


   To run the demo benchmark for a specific LTL property do:

     $ ./benchmarks.sh -mode demo -ltl safety -selector all -protect all -t 600 -m 5


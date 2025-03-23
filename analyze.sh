#!/bin/bash

export LD_LIBRARY_PATH=`pwd`/NuSMV-2.6.0/NuSMV/lib:$LD_LIBRARY_PATH

analyse_rep=./analysis
training_logs=$analyse_rep/training_log
bench=./bench
sub_scripts=./scripts

timeout=200
memory=10
gurobi="no"
mode="paper"
ltl="all"

if [[ $# = 0 ]]; then
      echo -e "Need at least 2 parameters:\n -mode <demo | paper > demo: portion of the benchmark, \n\t\t       paper: training benchmark already logged and used for SAT22 paper.\n -ltl <all | safety | gurantee | obligation | recurrence |persistence | reactivity>\n [-t|--timelimit <timelimit in seconds, default is 200s>]\n [-m|--memory <memory limit in Go, default is 10Go>]\n [-g|--gurobi    !!MANDATORY LICENSE FOR GUROBI!!]"
      exit 1;
fi;

POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -mode)
      bench_mode=$2
      shift # past argument
      shift # past value
      ;;
    -t|--timelimit)
      timeout="$2"
      shift # past argument
      shift # past value
      ;;
    -m|--memory)
      memory="$2"
      shift # past argument
      shift # past value
      ;;
    -ltl)
      property_mode="$2"
      shift # past argument
      shift # past value
      ;;
    -g|--gurobi)
      gurobi="yes"
      shift # past argument
      shift # past value
      ;;
    -h|--help)
      echo -e "Need at least 2 parameters:\n -mode <demo | paper > demo: portion of the benchmark, \n\t\t       paper: training benchmark already logged and used for SAT22 paper.\n -ltl <all | safety | gurantee | obligation | recurrence |persistence | reactivity>\n [-t|--timelimit <timelimit in seconds, default is 200s>]\n [-m|--memory <memory limit in Go, default is 10Go>]\n [-g|--gurobi    !!MANDATORY LICENSE FOR GUROBI!!]"
      exit 1
      ;;
    --default)
      shift # past argument
      ;;
    -*|--*)
      echo -e "Unknown option $1"
      exit 1
      ;;
    *)
      smv_file=$1
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters


echo -e "\nParameters: mode "$bench_mode", ltlspec "$property_mode", timeout "$timeout"sec, memory "$memory"Go, Gurobi? "$gurobi".\n"




if [ $bench_mode = "demo" ]; then
	echo -e "\n##############################################################
##############        LOG DEMO BENCHMARK        ##############   
##############################################################\n"
	analyse_rep=$analyse_rep/demo
	BENCHZIP=$bench/"demo_benchmark.zip"

elif [ $bench_mode = "paper" ]; then
	echo -e "\n##############################################################
##############        RUN DEMO BENCHMARK        ##############   
##############################################################\n"
	for ltl_dir in $training_logs/*; do
		ltlname=$(basename $ltl_dir)
		if [ $ltlname != $property_mode ] && [ $property_mode != "all" ];then
			continue;
		fi
		echo -e "******************     "$ltlname" property     ******************"
		train_log_ltl=$training_logs/$ltlname/log/
		train_log_ltl_rep=$training_logs/$ltlname/
	
		echo -e "   PLOT traditional LBD."
		python3 $sub_scripts/BMCClauseClassification.py $train_log_ltl $train_log_ltl_rep lbd "TRAINING-LOG "$ltlname
		echo -e "   SAVE associated csv."
		python3 $sub_scripts/BMCClauseClassification.py $train_log_ltl $train_log_ltl_rep  pl "TRAINING-LOG "$ltlname
		echo -e "   PLOT refined classification."	
		python3 $sub_scripts/BMCClauseClassification.py $train_log_ltl $train_log_ltl_rep  lbd-bmc "TRAINING-LOG "$ltlname

		if [ $gurobi = "yes" ]; then
			echo -e "\n   Generate selectors using Hf heuristic for "$ltlname":"
			python2.7 $sub_scripts/LinearProgramming.py $train_log_ltl_rep $train_log_ltl_rep "TRAINING-LOG "$ltlname "Hf"
		fi
	done;
	exit 0
fi



################## CLEAR OLD LOG ##################
#for r in $analyse_rep/*; do 
#	rep_name=$(basename $r)
#	echo -e "Clean old logs if exist "$rep_name"."
#	rm -rf $r/*
#	mkdir -p $r/log
#done;
#echo -e "\n\n"
################## CLEAR OLD LOG ##################

properties="safety guarantee obligation recurrence reactivity persistence"
for ltlname in $properties; do

	if [ $ltlname != $property_mode ] && [ $property_mode != "all" ];then
		continue;
	fi

	echo -e "LOG LTL "$ltlname" problems......"

	analysis_ltl_log=$analyse_rep/$ltlname/log/
	analysis_ltl=$analyse_rep/$ltlname/

	for filezip in $(zipinfo -1 $BENCHZIP benchmark/$ltlname/*.dimacs); do
		filename=$(basename $filezip)
		tmp_file=./$filename
		echo -e "   "$filename"......"
		unzip -p $BENCHZIP benchmark/$ltlname/$filename > $tmp_file

		./bsaltic_analyzer -t=$timeout -max-memory=$memory $tmp_file > $analysis_ltl_log/$filename".log"
		rm $tmp_file
	done;

	echo -e "ANALYZE LTL "$ltlname" LOGs......"

	echo -e "   PLOT traditional LBD."
	python3 $sub_scripts/BMCClauseClassification.py $analysis_ltl_log $analysis_ltl lbd $ltlname
	echo -e "   SAVE associated csv."
	python3 $sub_scripts/BMCClauseClassification.py $analysis_ltl_log $analysis_ltl pl $ltlname
	echo -e "   PLOT refined classification."	
	python3 $sub_scripts/BMCClauseClassification.py $analysis_ltl_log $analysis_ltl lbd-bmc $ltlname
	echo -e "PLOTS are located in: "$analysis_ltl


	if [ $gurobi = "yes" ]; then
		echo -e "\n   Generate selectors using Hf strategy for "$ltlname":"
		python2.7 $sub_scripts/LinearProgramming.py $analysis_ltl $analysis_ltl $ltlname "Hf"

	fi
done;
echo -e "Done."


#!/bin/bash

curr_position=`pwd`
bench=./bench
result_rep=./results
scripts=./scripts


if [[ $# = 0 ]]; then
      echo -e "Need at least 4 parameters:\n -mode <demo | all benchmark>\n -ltl <LTL specificity: all, safety, gurantee, obligation, recurrence, persistence, reactivity>\n -selector <selector heuristic: all, hf, none>\n -protect <protection strategy: all, e, dr>\n [-t|--timelimit <timelimit in seconds, default is 600s>]\n [-m|--memory <memory limit in Go, default is 10Go>]"
      exit 1
fi

POSITIONAL_ARGS=()

timeout=600
memory=10
protect="e"
selector="none"
ltl="none"
mode="demo"

while [[ $# -gt 0 ]]; do
  case $1 in
    -mode)
      bench_mode="$2"
      shift # past argument
      shift # past value
      ;;
    -m|--memory)
      memory="$2"
      shift # past argument
      shift # past value
      ;;
    -t|--timelimit)
      timeout="$2"
      shift # past argument
      shift # past value
      ;;
    -ltl)
      property_mode="$2"
      shift # past argument
      shift # past value
      ;;
    -protect)
      protect=$2
      shift # past argument
      shift # past value
      ;;
    -selector)
      heuristic=$2
      shift # past argument
      shift # past value
      ;;
    -h|--help)
      echo -e "Need at least 4 parameters:\n -mode <demo | all benchmark>\n -ltl <LTL specificity: all, safety, gurantee, obligation, recurrence, persistence, reactivity>\n -selector <selector heuristic: all, hf, none>\n -protect <protection strategy: all, e, dr>\n [-t|--timelimit <timelimit in seconds, default is 600s>]\n [-m|--memory <memory limit in Go, default is 10Go>]"
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
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

echo -e "Parameters: mode "$bench_mode", timelimit "$timeout"sec, memory "$memory"Go, ltlspec "$property_mode", selector "$heuristic" heuristic, benchmark repository "$bench


export LD_LIBRARY_PATH=$curr_position/NuSMV-2.6.0/NuSMV/lib:$LD_LIBRARY_PATH



if [ $bench_mode = "demo" ]; then
	echo -e "\n##############################################################
##############        RUN DEMO BENCHMARK        ##############   
##############################################################\n"
	BENCHZIP=$bench/"demo_benchmark.zip"
elif [ $bench_mode = "all" ]; then
	echo -e "##############################################################
##############        RUN MAIN BENCHMARK        ##############   
##############################################################\n"
	BENCHZIP="main_benchmark.zip"
fi

csv_result=$result_rep/$bench_mode/"compare.csv"

echo "Solver Configuration,LTL,Instance,Result Code,Wall Time" > $csv_result


properties="safety guarantee obligation recurrence reactivity persistence"
for ltlname in $properties; do
	if [ $ltlname != $property_mode ] && [ $property_mode != "all" ];then
		continue;
	fi
	
	echo -e "...Run LTL "$ltlname" instances.\n"
	for filezip in $(zipinfo -1 $BENCHZIP benchmark/$ltlname/*.dimacs); do
		filename=$(basename $filezip)
		tmp_file=./$filename
		unzip -p $BENCHZIP benchmark/$ltlname/$filename > $tmp_file
		if [ $heuristic = "hf" ] || [ $heuristic = "all" ] ; then
			if [ $protect = "e" ] || [ $protect = "all" ]; then
				echo -e "   "$filename" with Frequency-based Heuristic Hf  - Explicit protection"
				./bsaltic -no-model -ltl=$ltlname -selector="hf" -t=$timeout -protect="e" -max-memory=$memory -o=$csv_result $tmp_file 
			fi
			if [ $protect = "dr" ] || [ $protect = "all" ]; then
				echo -e "   "$filename" with Frequency-based Heuristic Hf - Database reduction"
				./bsaltic -no-model -ltl=$ltlname -selector="hf" -t=$timeout -protect="dr" -r=4 -max-memory=$memory -o=$csv_result $tmp_file 
			fi
		fi
		if [ $heuristic = "none" ] || [ $heuristic = "all" ]; then 
			echo -e "   "$filename" with traditional MapleCOMSPS solver......"
			./bsaltic -no-model -t=$timeout -ltl=$ltlname -max-memory=$memory -o=$csv_result $tmp_file 
		fi
		rm $tmp_file
	done;
done;

echo -e "##############################################################
##############        RESUME EXPERIMENTS        ##############   
##############################################################\n"

python3 $scripts/ranking.py --timeout $timeout $csv_result 

python3 $scripts/scatter-plotly.py --s1 MapleCOMSPS --s2 BSaLTic-DHf --timeout $timeout --output $result_rep/$bench_mode/ $csv_result 
python3 $scripts/scatter-plotly.py --s1 MapleCOMSPS --s2 BSaLTic-EHf --timeout $timeout --output $result_rep/$bench_mode/ $csv_result 

echo -e "done."


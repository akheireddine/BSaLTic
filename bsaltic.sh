#!/bin/bash

POSITIONAL_ARGS=()

if [[ $# = 0 ]]; then
      echo -e "Need at least 3 parameters:\n   -k <bound value>\n   -ltl <LTL filename>\n   [-selector <used selector: hf or none, default is none>]\n   [-protect <protection strategy: e or dr, default is e>]\n   [-r <multiplicative factor when using dr protection strategy, default is 1>]\n   [-o|--output <repository for output csv>]\n   [-t|--timelimit <timelimit in seconds, default is 600s>]\n   [-m|--memory <memory limit in Go, default is 10Go>]\n   <SMV filename>\n"
     exit 1
fi
echo -e "#############################################################
###############         INITIALIZATION        ###############
#############################################################\n"
timelimit=600
memory=10
k=1
ltl="none"
selector="none"
protect="e"
output=""
r=1

while [[ $# -gt 0 ]]; do
  case $1 in
    -t|--timelimit)
      timelimit="$2"
      shift # past argument
      shift # past value
      ;;
    -m|--memory)
      memory="$2"
      shift # past argument
      shift # past value
      ;;
    -o|--output)
      output="$2"
      shift # past argument
      shift # past value
      ;;
    -k)
      k="$2"
      shift # past argument
      shift # past value
      ;;
    -r)
      r="$2"
      shift # past argument
      shift # past value
      ;;
    -ltl)
      ltl="$2"
      shift # past argument
      shift # past value
      ;;
    -selector)
      selector="$2"
      shift # past argument
      shift # past value
      ;;
    -h|--help)
      echo -e "Need at least 3 parameters:\n   -k <bound value>\n   -ltl <LTL filename>\n   [-selector <used selector: hf or none, default is none>]\n   [-protect <protection strategy: e or dr, default is e>]\n   [-r <multiplicative factor when using dr protection strategy, default is 4>]\n   [-o|--output <repository for output csv>]\n   [-t|--timelimit <timelimit in seconds, default is 600s>]\n   [-m|--memory <memory limit in Go, default is 10Go>]\n   <SMV filename>\n"
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

echo -e "Parameters: k \""$k"\", selector \""$selector"\" heuristic, protection mode \""$protect"\", r value \""$r"\",  timelimit \""$timelimit"s\", memory \""$memory"Go\".\n LTL file \""$ltl"\"\n SMV file \""$smv_file"\"\n"


path=$(dirname $smv_file)
smv_name=$(basename "$smv_file" ".smv")


echo -e "##############################################################
######      IDENTIFY LTL class & COMBINE MODEL+LTL      ######   
##############################################################\n"

ltl_class=$(bash ./ltlclass.sh $ltl)

echo -e "...LTL class is "$ltl_class".\n"

LTL_NUSMV=`cat $ltl | tr \" " "`

SMV_LTL_FILE=$path"/"$smv_name"_"$ltl_class".smv"

sed '/LTLSPEC/Q' $smv_file > $SMV_LTL_FILE
echo -e "\nLTLSPEC "$LTL_NUSMV"\n" >> $SMV_LTL_FILE
echo -e "...Combine MODEL and LTL property in one file: "$SMV_LTL_FILE".\n"



echo -e "#############################################################
######################   RUN Solving   ######################
#############################################################\n"

#########    CONVERT SMV TO DIMACS
echo -e "...Convert SMV+LTL into DIMACS format using Sheridan conversion.\n"
./bsaltic -mode=c -conv=1 -k=$k -t=$timelimit -max-memory=$memory $SMV_LTL_FILE

DIMACS_FILE=$path"/"$(basename $SMV_LTL_FILE ".smv")"_k"$k".dimacs"


#########    RUN SOLVING
echo -e "...Run solving of "$ltl_class" property.\n...Using "$selector" heuristic and \""$protect"\" protection strategy.\n"
if [[ $output != "" ]]; then
	echo -e "...Save results in csv file at \""$output"\"\n"
	./bsaltic -ltl=$ltl_class -protect=$protect -selector=$selector -r=$r -t=$timelimit -max-memory=$memory -o=$output $DIMACS_FILE ;
else
	./bsaltic -ltl=$ltl_class -protect=$protect -selector=$selector -r=$r -t=$timelimit -max-memory=$memory $DIMACS_FILE
fi


echo "Done."

#!/bin/bash


spotPath="./spot/bin"
scripts="./scripts"

if [ "$#" -le 3 ]; then
	echo -e "Need 4 parameters :\n -ltl <LTLSPEC: safety, guarantee, obligation, recurrence,persistence, reactivity>\n -n|--number <Number of random LTL>\n -o|--output <output repository>\n <repository of .smv file(s)>\n";
	exit 1;
fi

export LD_LIBRARY_PATH=`pwd`/NuSMV-2.6.0/NuSMV/lib:$LD_LIBRARY_PATH

ltlType="safety"
number=1
outputdir=`pwd`

POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--number)
      number="$2"
      shift # past argument
      shift # past value
      ;;
    -ltl)
      ltlType="$2"
      shift # past argument
      shift # past value
      ;;
    -o|--output)
      outputdir=$2 
      shift # past argument
      shift # past value
      ;;
    -h|--help)
	echo -e "Need 4 parameters :\n -ltl <LTLSPEC: safety, guarantee, obligation, recurrence,persistence, reactivity>\n -n|--number <Number of random LTL>\n -o|--output <output repository>\n <repository of .smv file(s)>\n";
	exit 1;
      ;;
    --default)
      shift # past argument
      ;;
    -*|--*)
      echo -e "Unknown option $1"
      exit 1
      ;;
    *)
      DIRECTORY=$1
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

number=$((number+1))

echo -e "dirname "$DIRECTORY

for f in $DIRECTORY"/"*.smv; do 
	
	echo -e $f"\n"

	if [ ! -f "$f" ]; then
		continue;
	fi

	f_no_extension=$(echo -e "$f" | sed -e 's/\.[^.]*$//');

	SMVName=$(basename $f_no_extension)
	SMVfile=$DIRECTORY"/"$SMVName

	LTLfilename=$SMVfile"_LTLSPEC.txt"

	modelNameUnparsed="varnames"$ltlType".txt"

	modelNameParsed="modelNames"$ltlType".txt"

	./bsaltic -mode=c -conv=1 -k=2 -show-var $SMVfile > $modelNameUnparsed

	python3 $scripts/benchmark_preprocess.py $modelNameUnparsed > $modelNameParsed

	if [ $ltlType = "reactivity" ]; then
		$spotPath/randltl --ltl --simplify -p -n $number $(cat $modelNameParsed) |  $spotPath/ltlfilt -v -p -r --remove-wm --persistence --unabbreviate=R | $spotPath/ltlfilt -v -p -r --remove-wm --recurrence --unabbreviate=R > $LTLfilename 
#| sed '/1/d' | tr \" " " > $LTLfilename
	elif [ $ltlType = "obligation" ]; then
		$spotPath/randltl --ltl --simplify -p -n $number $(cat $modelNameParsed) |  $spotPath/ltlfilt -p -r --remove-wm --obligation --unabbreviate=R | $spotPath/ltlfilt -v -p -r --remove-wm --safety --unabbreviate=R | $spotPath/ltlfilt -v -p -r --remove-wm --guarantee --unabbreviate=R > $LTLfilename
#| sed '/1/d' | tr \" " " > $LTLfilename;
	elif [ $ltlType = "recurrence" ]; then
		$spotPath/randltl --ltl --simplify -p -n $number $(cat $modelNameParsed) | $spotPath/ltlfilt -p -r --remove-wm --recurrence --unabbreviate=R | $spotPath/ltlfilt -v -p -r --remove-wm --obligation --unabbreviate=R  > $LTLfilename
#| sed '/1/d' | tr \" " " > $LTLfilename;
	elif [ $ltlType = "safety" ]; then
		$spotPath/randltl --ltl --simplify -p -n $number $(cat $modelNameParsed) | $spotPath/ltlfilt -p -r --remove-wm --safety --unabbreviate=R > $LTLfilename
#| sed '/1/d' | tr \" " " > $LTLfilename;
	elif [ $ltlType = "guarantee" ]; then
		$spotPath/randltl --ltl --simplify -p -n $number $(cat $modelNameParsed) | $spotPath/ltlfilt -p -r --remove-wm --guarantee --unabbreviate=R > $LTLfilename
#| sed '/1/d' | tr \" " " > $LTLfilename;
	elif [ $ltlType = "persistence" ]; then
		$spotPath/randltl --ltl --simplify -p -n $number $(cat $modelNameParsed) | $spotPath/ltlfilt -p -r --remove-wm --persistence --unabbreviate=R | $spotPath/ltlfilt -v -p -r --remove-wm --obligation --unabbreviate=R > $LTLfilename	
#| sed '/1/d' | tr \" " " > $LTLfilename;
	else
		echo -e "Eroor ltl type "$ltlType
		exit 1 
	fi;

	rm $modelNameUnparsed $modelNameParsed

	i=0
	while read ltl; do
		new_smv_file=$outputdir"/"$SMVName"_"$ltlType"_"$i".smv"
		sed '/SPEC/Q' $SMVfile".smv" > $new_smv_file
		echo -e "\nLTLSPEC "$ltl"\n" >> $new_smv_file
		i=$((i+1));
	done < $LTLfilename

	echo -e $SMVNAME" "$i": done.\n"
done;


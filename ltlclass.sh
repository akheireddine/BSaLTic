#!/bin/bash


spotPath="./spot/bin"


POSITIONAL_ARGS=()

ltl=""

if [[ $# = 0 ]]; then
     echo -e "Need the filename of the LTL property.\n"
     exit 1
fi

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      echo -e "Need the filename of the LTL property.\n"
      exit 1
      ;;
    *)
      ltl="$1"
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters


if [[ $ltl = "" ]];then
     echo -e "Need the filename of the LTL property.\n"
     exit 1
fi


tmp_spot=$ltl

result=""
result=$($spotPath/ltlfilt -v -p -r --remove-wm --persistence --unabbreviate=R $tmp_spot | $spotPath/ltlfilt -v -p -r --remove-wm --recurrence --unabbreviate=R)

if ! [ -z $result ]; then
	echo -e "reactivity"
	exit 0
fi

result=""
result=$($spotPath/ltlfilt -p -r --remove-wm --obligation --unabbreviate=R $tmp_spot | $spotPath/ltlfilt -v -p -r --remove-wm --safety --unabbreviate=R | $spotPath/ltlfilt -v -p -r --remove-wm --guarantee --unabbreviate=R)

if ! [ -z $result ]; then
	echo -e "obligation"
	exit 0
fi

result=""
result=$($spotPath/ltlfilt -p -r --remove-wm --recurrence --unabbreviate=R $tmp_spot | $spotPath/ltlfilt -v -p -r --remove-wm --obligation --unabbreviate=R)
if ! [ -z "$result" ]; then
	echo -e "recurrence"
	exit 0
fi


result=""
result=$($spotPath/ltlfilt -p -r --remove-wm --persistence --unabbreviate=R $tmp_spot | $spotPath/ltlfilt -v -p -r --remove-wm --obligation --unabbreviate=R)
if ! [ -z $result ]; then
	echo -e "persistence"
	exit 0
fi


result=""
result=$($spotPath/ltlfilt -p -r --remove-wm --safety --unabbreviate=R $tmp_spot)
if ! [ -z $result ]; then
	echo -e "safety"
	exit 0
fi


result=""
result=$($spotPath/ltlfilt -p -r --remove-wm --guarantee --unabbreviate=R $tmp_spot)
if ! [ -z $result ]; then
	echo -e "guarantee"
	exit 0
fi


echo -e "Error in LTL class identification!\n"

rm *".tmp"

echo -e "none"
exit 1


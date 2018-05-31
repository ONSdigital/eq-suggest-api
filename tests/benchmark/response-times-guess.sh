#!/bin/bash
declare -a terms=("teaching" "teaching assistant" "director" "managing director" "executive" "chief executive" 
                  "chief" "farmer" "ass farmer" "sheep farmer" "Manufacturer" "Manufacturer basketry" 
                  "Manufacturer joinery" "Manufacturer knit" "no such job ever")
for term in "${terms[@]}"
do
   cmd="curl -sL http://localhost:5000/api/occupations/?s=guess&q=$term"
   timing="$(time -p  ( $cmd )  2>&1 >/dev/null )"
   t2=$(echo -e "$timing" | awk '/real/ {print $2}')
   printf " %25s:  %10s\n" "$term" $t2
done

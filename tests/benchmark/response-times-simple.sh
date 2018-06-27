#!/bin/bash
declare -a terms=("the" "the republic" "new" "the dem" "feder" "federation" 
                  "social" "social unioin" "yugoslavia" "yugosl" "the king" "ithe kingdom" 
                  "zanadu" "xanadu" "pastry")
for term in "${terms[@]}"
do
   cmd="curl -sL http://localhost:5000/api/countries_official_names/?s=simple&q=$term"
   timing="$(time -p  ( $cmd  ) 2>&1 1>/dev/null )"
   t2=$(echo -e "$timing" | awk '/real/ {print $2}')
   printf " %25s:  %10s\n" "$term" $t2
done

#!/bin/bash

ERRORCOUNT=0

if [ -n "$1" ]
  then
    count=1
      for srv in "$@"
       do
        PGPASSWORD=pwd psql -h ${srv} -U user -w -d set -c "select shop_number,fiscal_printer from public.cash where status = 'ACTIVE'" >> pars_dump.json
    count=$(( $count + 1 ))
  done
  t=$(cat pars_dump.json | grep "notSendedFDCount" | sed 's, ,,g')
  threads=($t)
    for thread in ${threads[@]}
        do
              echo "$thread" > pars_tmp
              convert_for_i=$(cat pars_tmp | grep -oE 'notSendedFDCount":...' | sed s/[^0-9]//g)
              shop_num=$(cat pars_tmp | sed 's,|{, ,g' | awk '{print $1}')
              i=$convert_for_i
              if [ "$i" -gt "$ERRORCOUNT" ]
               then
                 cat pars_tmp | sed 's,|{, {,g' | jq '.fnInfo | [.fnNumber, .firstNotSendedFDDate, .notSendedFDCount] | [@csv]' | 
                 sed 's,],,g;s,",,g;s,\[,,g;s,\\,,g;s/^[ \t]*//;/^\s*$/d' | sed s/^/${shop_num},/ >> report.cvs
              fi      
         done

  sed -i '1i Номер кассы,Фискальный номер принтера,Дата первого неотправленного документа,Количество неотправленных документов' report.cvs
else
  echo "-------- ERROR no parameters found."
fi

if [ -s report.cvs ]
  then
  cvs=$(cat report.cvs)
  touch mail.txt
 cat << EOF > mail.txt
   To: example@example.ru
   From: example@example.ru
   Subject: Mail with error from psql
   $cvs
EOF
   ssmtp example@example.ru < mail.txt
   cat report.cvs
   echo "-------- Mail with error possibly sended"
#  rm -rf pars_dump.json report.cvs tmp mail.txt
else
echo "-------- Perhaps no error found" 
fi

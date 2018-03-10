LFILE=`ls logs/log_*.log -r | head -1`
LFILE=${LFILE#logs/log_*}
LFILE=${LFILE%*-*}

i=0
SUF="-$i"

while [ -e "logs/log_$LFILE$SUF.log" ]; do
    i=$[$i+1]
    SUF="-$i"
done
SUF="-$[$i-1]"
reset

echo -e "Reading: logs/log_$LFILE$SUF.log\n"

tail -f "logs/log_$LFILE$SUF.log" | grep --line-buffered '^[ProcController]'

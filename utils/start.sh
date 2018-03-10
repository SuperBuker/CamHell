DATE=`date +%y%m%d`

mkdir -p logs

i=0
SUF="-$i"

while [ -e "logs/log_$DATE$SUF.log" ]; do
    i=$[$i+1]
    SUF="-$i"
done
reset

echo -e "Writting: logs/log_$DATE$SUF.log\n"

python controller.py | tee "logs/log_$DATE$SUF.log"

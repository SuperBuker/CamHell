if [[ $# -lt 1 ]]; then
    echo "Usage : $0 queue"
    exit
fi

[ `curl -s 'http://10.0.0.20:3000/status' | jq "if .Queues[0] < $1 and (.Feeders.ShodanProc | length == 0) then true else false end"` == true ] && curl -H 'Feeder: ShodanProc' -X POST 'http://10.0.0.20:3000/start_feeder' > /dev/null

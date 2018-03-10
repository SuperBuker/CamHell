if [[ $# -lt 1 ]]; then
    echo "Usage : $0 feeder"
    exit
fi

[ `curl -s 'http://10.0.0.20:3000/status' | jq "if .Feeders.$1 == 0 then true else false end"` == true ] && curl -s -H "Feeder: $1" -X POST 'http://10.0.0.20:3000/start_feeder' > /dev/null

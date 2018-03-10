if [[ $# -lt 1 ]]; then
    echo "Usage : $0 feeder"
    exit
fi

curl -H "Feeder: $1" -X POST 'http://10.0.0.20:3000/stop_feeder'

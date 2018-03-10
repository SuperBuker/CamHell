USER=''
PASSWD=''
HOST='127.0.0.1'
PORT='3306'

T6=$(date -d '6 hour ago' "+%Y-%m-%d %H:%M:%S")
T12=$(date -d '12 hour ago' "+%Y-%m-%d %H:%M:%S")
T24=$(date -d '24 hour ago' "+%Y-%m-%d %H:%M:%S")
T48=$(date -d '48 hour ago' "+%Y-%m-%d %H:%M:%S")

RESULT=($(mysql --raw --batch -s -u $USER -p$PASSWD -h $HOST -P $PORT -D $1 <<EOF
	SELECT Count(*) FROM camera;
	SELECT Count(*) FROM camera WHERE camera.retry = 0;
	SELECT Count(*) FROM timestamp;
	SELECT Count(*) FROM timestamp WHERE timestamp.date > '$T6';
	SELECT Count(*) FROM timestamp WHERE timestamp.date > '$T12';
	SELECT Count(*) FROM timestamp WHERE timestamp.date > '$T24';
	SELECT Count(*) FROM timestamp WHERE timestamp.date > '$T48';
	SELECT Count(*) FROM address;
	SELECT Count(*) FROM credentials;
        SELECT Count(*) FROM ddns;
        SELECT Count(*) FROM ftp;
        SELECT Count(*) FROM mail;
	SELECT Count(*) FROM status;
        SELECT Count(*) FROM smarteye;
	SELECT Count(*) FROM wifi_scan;
	SELECT Count(*) FROM wifi_ap;
	SELECT Count(*) FROM wifi;
	SELECT Count(*) FROM location;
	SELECT Count(*) FROM location WHERE detail = 0;
	SELECT Count(*) FROM location WHERE detail < 2;
	SELECT Count(DISTINCT addr_country) FROM location;
EOF
))

echo -e "Cameras: ${RESULT[0]}\n\t-Active: ${RESULT[1]}\nTimestamp: ${RESULT[2]}\n\t-Last 6 hours: ${RESULT[3]}\n\t-Last 12 hours: ${RESULT[4]}\n\t-Last 24 hours: ${RESULT[5]}\n\t-Last 48 hours: ${RESULT[6]}\nAddress: ${RESULT[7]}\nCredentials: ${RESULT[8]}\nDDNS: ${RESULT[9]}\nFTP: ${RESULT[10]}\nMail: ${RESULT[11]}\nStatus: ${RESULT[12]}\nSmartEye: ${RESULT[13]}\nWifi Scan: ${RESULT[14]}\n\t-APs: ${RESULT[15]}\n\t-Wifis: ${RESULT[16]}\nLocation: ${RESULT[17]}\n\t-Precise: ${RESULT[18]}\n\t-LatLng: ${RESULT[19]}\n\t-Countries: ${RESULT[20]}"

# Welcome to CamHell!
CamHell is an IP camera crawler capable of hacking, parsing, storing and postprocessing most of the data available in all the products based on the **Ingenic T10** platform and affected by [this](https://pierrekim.github.io/blog/2017-03-08-camera-goahead-0day.html) and [this](https://blogs.securiteam.com/index.php/archives/3043) bugs. Have fun!

# The origins

## Long story short
This software follows the work of Pierre Kim, SSD and Cybereason, who published in March 2017 multiple vulnerabilities hitting the Ingenic T10 based products and all his owners.
Given that the platform was present in a huge number of products (of multiple rebranders), it was very difficult to determine how many and which of them were affected. Pierre Kim published a [list](https://github.com/SuperBuker/CamHell/tree/master/doc/cameralist.txt), maybe too early, maybe not as polished as the rest of his work, but it was a beginning: more than **1000 affected products**. Sadly, after some time, that list disappeared from the original report but still available in some internet caches.

Two months after the publication of the vulnerabilities these cameras were included in the botnet [ELF_PERSIRAI.A](http://blog.trendmicro.com/trendlabs-security-intelligence/persirai-new-internet-things-iot-botnet-targets-ip-cameras/), and now they're part of the [Satori](https://securityboulevard.com/2018/02/satori-adds-known-exploit-chain-to-enslave-wireless-ip-cameras/) botnet.

At this moment, the vast majority of the rebranders haven't published any security update, or warned their clients; betraying them. Now, as the original list of products and brands is no longer available, they claim they're not affected. They lie, and this software is the proof.

## Motivations
As a cybersecurity enthousiast I wanted to understand the consequences of putting the marketing and financial departments dealing with a huge security issue. Please don't laugh, this kind of investigations shall be run by experts and not by dressed up cockroaches.
Also, as a customer and owner of an affected product, I wanted to know how many devices were vulnerable through internet; how much information was exposed, and in which ways it could be exploited. In my early tests I managed to geolocate my camera using the wifi scanner utility and Google Maps API, but that was just the beginning.

# Architecture
![CamHell architecture](https://github.com/SuperBuker/CamHell/raw/master/doc/architecture.png)
CamHell is composed by three stages: Feeders, PwnProc, and GeoProc, connected through multiprocessing pipes and leaded by a the ProcController.

## Feeders
The first stage is composed by the feeders: Shodan, Censys, ZoomEye, Local Database and SmartEye.
The first three ones are online crawlers. Just pay the subscription, put the right query and you'll get a list of host candidates. The forth one is the local database, with all the previous hacked cameras. And the fifth one is SmartEye, a dynamic DNS provided with the cameras and lacking of authentication procedures.
The online crawlers work as external source of camera candidates. The Local Database work as internal source, reusing the last working address of every camera. And finally, SmartEye provides the address of the cameras connected to that service.

### Shodan
Shodan, our european crawler, offers two kind of services: regular queries and real-time stream. Each one has his own feeder. Both services require a valid user API key.
**ShodanProc** asks Shodan services how many host are available in their database, then launches as many **ShodanWorkers** to assign up to 100 pages (each one with 100 host) to each one; finally enters in token-bucket mode, synchronizing the worker queries. It's not allowed to send more than 1 request/s, but multiple workers can be waiting for a reply at the same time. It's quite common that Shodan doesn't reply (and sdk throws a timeout) or replies with 0 hosts. In those cases, the previous request is automatically resent.
**ShodanStreamProc** subscribes to a kind of NMAP data stream, then filters the given results locally. It is possible to launch as ShodanStreamProcs as desired, but currently it's not possible to check duplicated hosts in the processing queues, so be careful.
It's important to notice that both feeders only put in their feeding queue those hosts who are not currently set as active in database.

### Censys
Censys, our «gringo» crawler, offers a service similar to Shodan regular queries, but much more limited in performance and daily fresh results. Anyway, it's good enough as secondary feeder, and requires a valid user API key.
Censys only allows access to the last 10k results through his API; to access the rest a special permission is needed. Never tell Censys your true purposes because this application breaks their ToS.
As Censys has a very limited number of queries in their free accounts it's useful to have multiple accounts and API keys.
It's important to notice that this feeder only puts in his feeding queue those hosts who are not currently set as active in database.

### ZoomEye
ZoomEye, our «dim sum» crawler, also offers the same kind of service as Censys and Shodan regular queries. This service is suitable as secondary feeder and requires a valid user API key.
As ZoomEye has a very limited number of queries in their free accounts it's useful to have multiple accounts and API keys.
It's important to notice that this feeder only puts in his feeding queue those hosts who are not currently set as active in database.

### Local Database
The local database offers fast and reliable access to the last network address recorded for each camera. **DBProc** has multiple filters allowing to select only the active cameras (with retries < 3), and outdated cameras (with last record > 12h), this parameters are customizable.  The camera candidate objects put in the feeding queue have the Id of the camera in addition to the network address, this speeds up the recovery of the last valid credentials at the PwnProc stage.
It's important to notice that this feeder works as a garbage collector, forcing current active cameras to be checked at least once a day until they're no longer available.

### SmartEye
SmartEye is an insecure DDNS service hardcoded in a considerable number of cameras.
Each camera has a unique identifier for that service and can be accessed through `http://id.domain.com:80`. All the subdomains point to the same IP, and depending on the subdomain requested an Apache server replies with an `HTTP 301 Moved Permanently`, redirecting to the current address of the camera.
As a consequence of the secuencialisation of the subdomain names, it's possible to determine the dimensions of the name space and guess the valid ones. There are around 500k valid subdomains, that can be accessed with **SmartEyeProc** and processed with PwnProc in less than 24 hours.
For daily use, we can ask just for the current address of the valid subdomains, the ones stored in the database and related to a camera. **SmartEyeDBProc** was designed for that purpose.
It's important to notice that both feeders only put in their feeding queue those hosts who are not currently set as active in database.

## PwnProc
The second stage is composed by the **PwnProc**. This process is in charge of hacking the cameras, downloading and parsing all the available data, and finally storing it.

The process complies the following guidelines:
 - Ensure the process concurrency and isolate the points of collision
 - Allow concurrent access to database
 - Store deltas in database, and each wifiscan report
 - Recover already hacked credentials, when possible
 - Connect through anonymous proxy (TOR like), and be protected against temporary network instabilities
 - Support heartbeat and graceful unlock, in case the process hangs in a request
 - Support as many camera variants as possible
 - Output data to the postprocessing stage

## GeoProc
The third and last stage is **GeoProc**, currently our only postprocessor.
This process formats the last wifiscan and sends it to Google Maps API Geolocation service; receiving the location of the camera in the 85% of the cases, and with an accuracy of around 40m. Then ask the Geocoding service for the street address of that location.
The wifiscan is sent to Google only if the camera is new, or the last available record is older than 7 day. Also, the geolocations with a accuracy higher than 150m are discarded.
If the Google geolocation service the process records the country based on the IP address using `http://ip2c.org` service.

## Controller
The **ProcController** is the main process of the platform.
Does the initial setup, launches and stops the feeders on demand and provisions PwnProcs and GeoProcs depending on the size of the multiprocessing queues.
It also monitors the heartbeats of the PwnProcs, sending them a SIGALARM if they hang.

For making easier the tunning of the "desired workers" formula, a LibreOffice Calc [file](https://github.com/SuperBuker/CamHell/tree/master/doc/worker_formula.ods) is available.

### API REST
The ProcController API REST is a simple flask server runned by a thread; allowing monitoring and managing the different processes and feeders. All the responses are in JSON format.

**GET status:** Current active processes

    $ curl  -X GET 'http://localhost:3000/status'

**GET database status:** Database statistics

    $ curl  -X GET 'http://localhost:3000/status_db'

**GET log:** Last 10 feeders launched or stopped

    $ curl  -X GET 'http://localhost:3000/status'
   
**POST start feeder:** Start a certain feeder

    $ curl -H "Feeder: $FEEDER" -X POST 'http://localhost:3000/start_feeder'

**POST stop feeder:** Stop a certain feeder

    $ curl -H "Feeder: $FEEDER" -X POST 'http://localhost:3000/stop_feeder'
*$FEEDER* should be one of the following feeders: ['DBProc', 'SmartEyeDBProc', 'ShodanProc', 'ShodanStreamProc', 'CensysProc', 'ZoomEyeProc', 'SmartEyeProc']

**POST stop:** Stop the controller and his subprocesses

    $ curl -X POST 'http://localhost:3000/stop'

### Automation and Hooks
In order to simplify the user interaction with the controller through API REST multiple bash scripts have been preconfigured and are available in the [hooks](https://github.com/SuperBuker/CamHell/tree/master/hooks) directory.

 - `$ ./hooks/status.sh` ⇒ GET status 
 - `$ ./hooks/start.sh $1` ⇒ POST start feeder $1 
 - `$ ./hooks/stop.sh $1` ⇒ POST stop feeder $1. 
 - `$  ./hooks/start_feeder.sh $1` ⇒ GET status + POST start feeder $1 if
   not currently running
 - `$ ./hooks/start_shodan.sh` ⇒ GET status + POST    start shodan if not running and queue < $1

# Installation
CamHell requires at least one host with **Python**, running the program, and a MySQL/**MariaDB** server. The SQL server can be hosted in a different computer, and multiple computers can run CamHell in parallel; selecting different feeders for each one and sharing the database. In order to anonymize all the generated traffic, it's quite recommended to setup a **TOR** proxy socks and edit the corresponding config in the `processmodel.py` file.

## Python dependencies
CamHell requieres Python 3 and the following packages:
 - censys==0.1.0
 - Flask==0.12.2
 - Flask-Compress==1.4.0
 - mysqlclient==1.3.12
 - peewee==2.10.2
 - requests==2.18.4
 - shodan==1.7.7
 - simplejson==3.13.2
 - zoomeye==1.0.0

For automatic dependencies instalation execute:

    $ pip install -r requirements.txt 

## API keys
Google API, Shodan, Censys and ZoomEye requiere a valid user API key. The almost mandatory ones are Google and Shodan, but the final decision relies on the final user. Those API Keys are currently defined as variables at the beginning of the `processmodel.py`.
Also, it's possible (and very easy) to modify the application allowing more than one API per service, in order to multiply your free service quota on those services; but please don't ask for that feature.

## Database setup
The database chosen for development has been MariaDB. Due to the use of utf8mb4 and the significant number of parallel connections, the database server config (`/etc/mysql/my.cnf`) requires some tweaks to work properly.

    [client]
    default-character-set = utf8mb4
    
    [mysqld]
    collation_server = utf8mb4_unicode_ci
    character_set_server = utf8mb4
    innodb_file_format = barracuda
    innodb_file_per_table = 1
    innodb_large_prefix = 1

	max_connections = 500
	max_user_connections = 500
    
    [mysql]
    default-character-set = utf8mb4
Addionally, an SQL scheme can be found in [scheme.sql](https://github.com/SuperBuker/CamHell/tree/master/doc/scheme.sql)
![SQL scheme](https://github.com/SuperBuker/CamHell/raw/master/doc/scheme.png)

The chosen server should be defined in the configuration of the database, located just at the beginning of the `model.py`.
Also, the scripts `utils/mysql_{monitor,reset_db}.sh` make easier the management and visualization of the DB; both expect the database name as first argument.

Finally, even if the datamodel was written in Peewee, in order to allow compatibility with other databases, that was broken due to some "custom queries" specific for MariaDB. In theory, PostgreSQL still is a valid alternative, but will require changing the Peewee SQL driver, and modifying the specific MariaDB queries.

## Cron setup
The best and simplest way I found to setup a tunable logic in the ProcController was to run some preconfigured scripts periodically, using cron.

This is my cron config:

    55 3 * * *  bash '/pathtocamhell/hooks/start_feeder.sh' DBProc
    55 6 * * *  bash '/pathtocamhell/hooks/start_feeder.sh' CensysProc
    55 8 * * *  bash '/pathtocamhell/hooks/start_feeder.sh' ZoomEyeProc
    55 11 * * *  bash '/pathtocamhell/hooks/start_feeder.sh' SmartEyeDBProc
    */15 * * * *  bash '/pathtocamhell/hooks/start_shodan.sh' 30000

This setup is just an example, it might change if newer feeder or custom feeders are added to the current processing architecture.

## Start
For starting the platform just execute:

    $ ./start.sh
This script launches the `controller.py` and records the log in `logs/yymmdd-i.log`. The script has been programmed expecting `/usr/bin/python` to be Python 3. If you're using a Debian distribution or any other distribution having Python 3 as `/usr/bin/python3` please modify the script.

As the process has a huge verbosity and it's difficult to follow the ProController outputs, a log grep utility has been programmed:

    $ ./log.sh

## Fine tuning
The current platform is enough flexible to accept custom inputs. Also, the PwnProc might be completely changed on order to do alternative tasks; for example spreading Mirai or any other botnet. But, if you decide to preserve a big part of this software you might be interested in going deep in the code and tune the global constant variables in order to adapt this solution to your network, infrastructure or even needs. Feel free to suggest any optimization or enhancement.

## Coming Soon
 - More documentation (`model.py` and `controller.py` aren't documented at this moment)
 - `model.py` enhancement, please make any suggestion
 - Configuration by JSON file
 - Connection to the cameras though cloud (requires privative protocol reversal)
 - API token balancer
 - FOFA feeder, requires translation
 - Support for country selection on CensysProc and ZoomEyeProc or deletion of country support in ShodanProc
 - Bug fixes, and more bug fixes ;)
 
# Last thoughts
As you can see, CamHell is a powerful tool, that should have never been made; but here it is.

At this point I would encourage you to meditate about the responsibility that the manufacturers have regarding the black boxes (also called IoTs) they sell; and up to which point that responsibility should be reinforced by law. Also, by our side as electronics consumers, it would be interesting to meditate how much trust and personal information we put in IoTs we don't know how they really work, because they lack of any external certification.

We can not buy a $15 IP camera and expect the support of a $200 one. In the end cheap becomes expensive, and you're paying with your privacy and personal data.

Happy hunting!


  
# License

The software is available as open source under the terms of the [GPLv3](https://opensource.org/licenses/GPL-3.0).

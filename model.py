from peewee import *
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import RetryOperationalError
import datetime
from math import radians, cos, sin, asin, sqrt


class MyRetryDatabase(RetryOperationalError, MySQLDatabase):
    commit_select = False


# MySQL Database cfg
db = MyRetryDatabase(
    '',  # Database
    host='',
    port=3306,
    user='',
    passwd='',
    charset='utf8mb4',
    threadlocals=True)


class BaseModel(Model):
    class Meta:
        database = db


class Camera(BaseModel):
    id = CharField(primary_key=True)
    mac = CharField()
    wifimac = CharField()
    deviceid = CharField()
    retry = IntegerField(default=0)
    creation_date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        order_by = ('id',)

    def _create(mac, wifimac, deviceid):
        cam_id = Camera.calc_id(mac, wifimac, deviceid)
        cam = Camera._get(cam_id)
        if cam:
            return cam.set_online()

        camera = None
        try:
            with db.execution_context() as ctx:
                # Attempt to create the camera. If the id is taken, due to the
                # unique constraint, the database will raise an IntegrityError.
                camera = Camera.create(
                    id=cam_id,
                    # replace('-', ':') was not supposed to be necessary, but...
                    mac=mac.replace('-', ':').upper(),
                    # replace('-', ':') was not supposed to be necessary, but...
                    wifimac=wifimac.replace('-', ':').upper(),
                    deviceid=deviceid
                )
        except IntegrityError:
            pass
        return camera

    def _get(id):
        camera = None
        try:
            with db.execution_context() as ctx:
                camera = Camera.get(Camera.id == id)
        except Camera.DoesNotExist:
            pass
        return camera

    def _get_by_ip(ip):
        camera = None
        try:
            with db.execution_context() as ctx:
                subquery = Address.select(Address.camera).where(
                    Address.ip == ip).order_by(Address.date_id.desc()).limit(1)
                camera = Camera.get(Camera.id == subquery)
        except Camera.DoesNotExist:
            pass
        return camera

    def _get_by_addr(ip, port):
        camera = None
        try:
            with db.execution_context() as ctx:
                subquery = Address.select(Address.camera).where((Address.ip == ip) & (
                    Address.port == port)).order_by(Address.date_id.desc()).limit(1)
                camera = Camera.get(Camera.id == subquery)
        except Camera.DoesNotExist:
            pass
        return camera

    def set_online(self):
        try:
            with db.execution_context() as ctx:
                # Attempt to set a camera online. If the camera doesn't exist
                # the database will raise an IntegrityError.
                self.retry = 0
                self.save()
        except IntegrityError:
            pass
        return self

    def set_offline(self):
        try:
            with db.execution_context() as ctx:
                # Attempt to set a camera offline. If the camera doesn't exist
                # the database will raise an IntegrityError.
                self.retry += 1
                self.save()
        except IntegrityError:
            pass
        return self

    def get_creds(self):
        creds = None
        try:
            with db.execution_context() as ctx:
                creds = Credentials.select().where(Credentials.camera == self).order_by(
                    Credentials.date_id.desc()).get()
        except Credentials.DoesNotExist:
            pass
        return creds

    def get_creds_hist(self):
        creds = None
        try:
            with db.execution_context() as ctx:
                creds = list(Credentials.select().distinct().where(
                    Credentials.camera == self))
        except Credentials.DoesNotExist:
            pass
        return creds

    def get_addr(self):
        address = None
        try:
            with db.execution_context() as ctx:
                address = Address.select().where(
                    Address.camera == self).order_by(Address.date_id.desc()).get()
        except Address.DoesNotExist:
            pass
        return address

    def get_addr_hist(self):
        address = None
        try:
            with db.execution_context() as ctx:
                address = list(Address.select().distinct().where(
                    Address.camera == self))
        except Address.DoesNotExist:
            pass
        return address

    def get_ddns(self):
        ddns = None
        try:
            with db.execution_context() as ctx:
                ddns = DDNS.select().where(DDNS.camera == self).order_by(DDNS.date_id.desc()).get()
        except DDNS.DoesNotExist:
            pass
        return ddns

    def get_ddns_hist(self):
        ddns = None
        try:
            with db.execution_context() as ctx:
                ddns = list(DDNS.select().distinct().where(
                    DDNS.camera == self))
        except DDNS.DoesNotExist:
            pass
        return ddns

    def get_ftp(self):
        ftp = None
        try:
            with db.execution_context() as ctx:
                ftp = FTP.select().where(FTP.camera == self).order_by(FTP.date_id.desc()).get()
        except FTP.DoesNotExist:
            pass
        return ftp

    def get_ftp_hist(self):
        ftp = None
        try:
            with db.execution_context() as ctx:
                ftp = list(FTP.select().distinct().where(FTP.camera == self))
        except FTP.DoesNotExist:
            pass
        return ftp

    def get_loc(self, det=3):
        loc = None
        try:
            with db.execution_context() as ctx:
                loc = Location.select().where((Location.camera == self) & (
                    Location.detail < det)).order_by(Location.date_id.desc()).get()
        except Location.DoesNotExist:
            pass
        return loc

    def get_loc_hist(self):
        loc = None
        try:
            with db.execution_context() as ctx:
                loc = list(Location.select().distinct().where(
                    Location.camera == self))
        except Location.DoesNotExist:
            pass
        return loc

    def get_mail(self):
        mail = None
        try:
            with db.execution_context() as ctx:
                mail = Mail.select().where(Mail.camera == self).order_by(Mail.date_id.desc()).get()
        except Mail.DoesNotExist:
            pass
        return mail

    def get_mail_hist(self):
        mail = None
        try:
            with db.execution_context() as ctx:
                mail = list(Mail.select().distinct().where(
                    Mail.camera == self))
        except Mail.DoesNotExist:
            pass
        return mail

    def get_status(self):
        status = None
        try:
            with db.execution_context() as ctx:
                status = Status.select().where(Status.camera == self).order_by(
                    Status.date_id.desc()).get()
        except Status.DoesNotExist:
            pass
        return status

    def get_status_hist(self):
        status = None
        try:
            with db.execution_context() as ctx:
                status = list(Status.select().distinct().where(
                    Status.camera == self))
        except Status.DoesNotExist:
            pass
        return status

    def get_smarteye(self):
        smarteye = None
        try:
            with db.execution_context() as ctx:
                smarteye = SmartEye.select().where(
                    SmartEye.camera == self).order_by(SmartEye.date_id.desc()).get()
        except SmartEye.DoesNotExist:
            pass
        return smarteye

    def get_smarteye_hist(self):
        status = None
        try:
            with db.execution_context() as ctx:
                smarteye = list(SmartEye.select().distinct().where(
                    SmartEye.camera == self))
        except SmartEye.DoesNotExist:
            pass
        return smarteye

    def get_wifiscan(self):
        wifi_scan = None
        try:
            with db.execution_context() as ctx:
                wifi_scan = Wifi_scan.select().where(
                    Wifi_scan.camera == self).order_by(Wifi_scan.date_id.desc()).get()
        except Wifi_scan.DoesNotExist:
            pass
        return wifi_scan

    def get_wifiscan_hist(self):
        wifi_scan = None
        try:
            with db.execution_context() as ctx:
                wifi_scan = list(Wifi_scan.select().distinct().where(
                    Wifi_scan.camera == self))
        except Wifi_scan.DoesNotExist:
            pass
        return wifi_scan

    def get_wifiap(self):
        wifi_ap = None
        try:
            wifi_ap = Wifi_AP.select().join(Wifi_scan).where(
                Wifi_scan.camera == self).order_by(Wifi_scan.date_id.desc()).get()
        except Wifi_AP.DoesNotExist:
            pass
        return wifi_ap

    def get_wifiap_hist(self):
        wifi_ap = None
        try:
            with db.execution_context() as ctx:
                wifi_ap = list(Wifi_AP.select().distinct().join(
                    Wifi_scan).where(Wifi_scan.camera == self))
        except Wifi_AP.DoesNotExist:
            pass
        return wifi_ap

    def get_last(self):
        ts = None
        try:
            with db.execution_context() as ctx:
                ts = Timestamp.select().join(Wifi_scan).where(Wifi_scan.camera ==
                                                              self).order_by(Wifi_scan.date_id.desc()).get()
        except Timestamp.DoesNotExist:
            pass
        return ts

    def get_last_hist(self):
        ts = None
        try:
            with db.execution_context() as ctx:
                ts = list(Timestamp.select().distinct().join(
                    Wifi_scan).where(Wifi_scan.camera == self))
        except Timestamp.DoesNotExist:
            pass
        return ts

    def _get_online():
        cameras = None
        try:
            with db.execution_context() as ctx:
                cameras = list(Camera.select().where(Camera.retry < 3))
        except Camera.DoesNotExist:
            pass
        return cameras

    def _get_outdated(hh=12):
        datetime_span = datetime.datetime.now() - datetime.timedelta(hours=hh)
        cameras = None
        try:
            with db.execution_context() as ctx:
                subquery = Camera.select(Camera.id).distinct().join(Wifi_scan).join(
                    Timestamp).where((Camera.retry < 3) & (Timestamp.date > datetime_span))
                cameras = list(Camera.select().distinct().join(Address).where((Camera.retry < 3) & ~(
                    Camera.id << subquery)).order_by(fn.Rand()))  # .order_by(fn.Random()) for Postgresql and Sqlite
        except Camera.DoesNotExist:
            pass
        return cameras

    def _get_outdated_dict(hh=12):
        datetime_span = datetime.datetime.now() - datetime.timedelta(hours=hh)
        mydict = None
        try:
            with db.execution_context() as ctx:
                subquery1 = Camera.select(Camera.id).distinct().join(Wifi_scan).join(
                    Timestamp).where((Camera.retry < 3) & (Timestamp.date > datetime_span))
                subquery2 = Camera.select(Camera.id.alias('camid')).annotate(Address, fn.Max(Address.id).alias(
                    'addrid')).where((Camera.retry < 3) & ~(Camera.id << subquery1)).alias('subquery2')
                mydict = list(Camera.select(Camera.id, Address.ip, Address.port).join(subquery2, on=(Camera.id == subquery2.c.camid).alias('cam')).join(
                    Address, on=(Address.id == subquery2.c.addrid).alias('addr')).order_by(fn.Rand()).dicts())  # .order_by(fn.Random()) for Postgresql and Sqlite
        except Camera.DoesNotExist:
            pass
        return mydict

    def _get_located(det=2):
        cameras = None
        try:
            with db.execution_context() as ctx:
                cameras = list(Camera.select().distinct().join(Location).where((Camera.retry < 3) & (
                    Location.detail < det)).order_by(fn.Rand()))  # .order_by(fn.Random()) for Postgresql and Sqlite
        except Camera.DoesNotExist:
            pass
        return cameras

    def _get_located_dict(det=2, **kwargs):
        mydict = None
        try:
            with db.execution_context() as ctx:
                camquery = Camera.select(Camera.id.alias(
                    'camid')).where(Camera.retry < 3)
                subquery = Camera.select(Camera.id.alias('camid')).annotate(Address, fn.Max(Address.id).alias('addrid')).annotate(Credentials, fn.Max(
                    Credentials.id).alias('credid')).annotate(Location, fn.Max(Location.id).alias('locid')).where(Camera.id << camquery).alias('subquery')
                if 'country' in kwargs:
                    mydict = list(Camera.select(Camera.deviceid, Camera.mac, Camera.wifimac, Camera.retry, Address.ip, Address.port, Credentials.user_admin, Credentials.passwd_admin, Location.lat, Location.lng, Location.addr_formatted).join(subquery, on=(Camera.id == subquery.c.camid).alias('cam')).join(Address, on=(Address.id == subquery.c.addrid).alias(
                        'addr')).join(Credentials, on=(Credentials.id == subquery.c.credid).alias('creds')).join(Location, on=(Location.id == subquery.c.locid).alias('loc')).where((Location.detail < 1) & (Location.addrcountry == kwargs['country'])).order_by(fn.Rand()).dicts())
                    # .order_by(fn.Random()) for Postgresql and Sqlite
                else:
                    mydict = list(Camera.select(Camera.deviceid, Camera.mac, Camera.wifimac, Camera.retry, Address.ip, Address.port, Credentials.user_admin, Credentials.passwd_admin, Location.lat, Location.lng, Location.addr_formatted).join(subquery, on=(Camera.id == subquery.c.camid).alias('cam')).join(Address, on=(
                        Address.id == subquery.c.addrid).alias('addr')).join(Credentials, on=(Credentials.id == subquery.c.credid).alias('creds')).join(Location, on=(Location.id == subquery.c.locid).alias('loc')).where(Location.detail < det).order_by(fn.Rand()).dicts())
                    # .order_by(fn.Random()) for Postgresql and Sqlite
        except Camera.DoesNotExist:
            pass
        return mydict

    def _get_all_located_dict(det=2, **kwargs):
        mydict = None
        try:
            with db.execution_context() as ctx:
                subquery = Camera.select(Camera.id.alias('camid')).annotate(Address, fn.Max(Address.id).alias('addrid')).annotate(
                    Credentials, fn.Max(Credentials.id).alias('credid')).annotate(Location, fn.Max(Location.id).alias('locid')).alias('subquery')
                if 'country' in kwargs:
                    mydict = list(Camera.select(Camera.deviceid, Camera.mac, Camera.wifimac, Camera.retry, Address.ip, Address.port, Credentials.user_admin, Credentials.passwd_admin, Location.lat, Location.lng, Location.addr_formatted).join(subquery, on=(Camera.id == subquery.c.camid).alias('cam')).join(Address, on=(Address.id == subquery.c.addrid).alias(
                        'addr')).join(Credentials, on=(Credentials.id == subquery.c.credid).alias('creds')).join(Location, on=(Location.id == subquery.c.locid).alias('loc')).where((Location.detail < 1) & (Location.addrcountry == kwargs['country'])).order_by(fn.Rand()).dicts())
                    # .order_by(fn.Random()) for Postgresql and Sqlite
                else:
                    mydict = list(Camera.select(Camera.deviceid, Camera.mac, Camera.wifimac, Camera.retry, Address.ip, Address.port, Credentials.user_admin, Credentials.passwd_admin, Location.lat, Location.lng, Location.addr_formatted).join(subquery, on=(Camera.id == subquery.c.camid).alias('cam')).join(Address, on=(
                        Address.id == subquery.c.addrid).alias('addr')).join(Credentials, on=(Credentials.id == subquery.c.credid).alias('creds')).join(Location, on=(Location.id == subquery.c.locid).alias('loc')).where(Location.detail < det).order_by(fn.Rand()).dicts())
                    # .order_by(fn.Random()) for Postgresql and Sqlite
        except Camera.DoesNotExist:
            pass
        return mydict

    ###Statistics###
    def _get_distinct_deviceid_stats(retry=None):
        cameras = None
        try:
            with db.execution_context() as ctx:
                if retry is None or retry < 0:
                    cameras = Camera.select(
                        fn.Count(fn.Distinct(Camera.deviceid))).scalar()
                else:
                    cameras = Camera.select(fn.Count(fn.Distinct(Camera.deviceid))).where(
                        Camera.retry < retry + 1).scalar()
        except Camera.DoesNotExist:
            pass
        return cameras

    def _get_located_stats_dict(det=2):
        mydict = None
        try:
            with db.execution_context() as ctx:
                camquery = Camera.select(Camera.id.alias(
                    'camid')).where(Camera.retry < 3)
                subquery = Camera.select(Camera.id.alias('camid')).annotate(Address, fn.Max(Address.id).alias('addrid')).annotate(Credentials, fn.Max(
                    Credentials.id).alias('credid')).annotate(Location, fn.Max(Location.id).alias('locid')).where(Camera.id << camquery).alias('subquery')
                mydict = list(Camera.select(Location.addr_country.alias('country'), fn.Count(Camera.id).alias('camera')).join(subquery, on=(Camera.id == subquery.c.camid).alias('cam')).join(Address, on=(Address.id == subquery.c.addrid).alias('addr')).join(
                    Credentials, on=(Credentials.id == subquery.c.credid).alias('creds')).join(Location, on=(Location.id == subquery.c.locid).alias('loc')).where(Location.detail < det).group_by(SQL('country')).order_by(SQL('camera').desc()).dicts())
                mydict = {d['country']: d['camera'] for d in mydict}
        except Camera.DoesNotExist:
            pass
        return mydict

    def _get_all_located_stats_dict(det=2):
        mydict = None
        try:
            with db.execution_context() as ctx:
                subquery = Camera.select(Camera.id.alias('camid')).annotate(Address, fn.Max(Address.id).alias('addrid')).annotate(
                    Credentials, fn.Max(Credentials.id).alias('credid')).annotate(Location, fn.Max(Location.id).alias('locid')).alias('subquery')
                mydict = list(Camera.select(Location.addr_country.alias('country'), fn.Count(Camera.id).alias('camera')).join(subquery, on=(Camera.id == subquery.c.camid).alias('cam')).join(Address, on=(Address.id == subquery.c.addrid).alias('addr')).join(
                    Credentials, on=(Credentials.id == subquery.c.credid).alias('creds')).join(Location, on=(Location.id == subquery.c.locid).alias('loc')).where(Location.detail < det).group_by(SQL('country')).order_by(SQL('camera').desc()).dicts())
                mydict = {d['country']: d['camera'] for d in mydict}
        except Camera.DoesNotExist:
            pass
        return mydict

    def calc_id(mac, wifimac, deviceid):
        macs = [mac, wifimac]
        for i in range(len(macs)):
            # replace('-', '') was not supposed to be necessary, but...
            macs[i] = macs[i].replace(':', '').replace('-', '')
            if not macs[i]:
                macs[i] = '0'
            macs[i] = int(str(macs[i]), 16)
        return('%s-%s-%s' % (macs[0], macs[1], deviceid))

    def cmp(self, camera_candidate):  # compare
        return self.id == camera_candidate.id


class Timestamp(BaseModel):
    date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        order_by = ('-date',)

    def _create():
        try:
            with db.execution_context() as ctx:
                # Attempt to create the timestamp.
                date = Timestamp.create()
        except IntegrityError:
            pass
        return date

    ###Statistics###
    def _get_stats(hh=None):
        dates = None
        try:
            with db.execution_context() as ctx:
                if hh is None or hh < 0:
                    dates = Timestamp.select().count()
                else:
                    datetime_span = datetime.datetime.now() - datetime.timedelta(hours=hh)
                    dates = Timestamp.select().where(Timestamp.date > datetime_span).count()
        except Timestamp.DoesNotExist:
            pass
        return dates


class Credentials(BaseModel):
    camera = ForeignKeyField(Camera, related_name='creds_belongs_to')
    date = ForeignKeyField(Timestamp, related_name='creds_at')
    user_admin = CharField()
    passwd_admin = CharField()
    user_mod = CharField()
    passwd_mod = CharField()
    user_guest = CharField()
    passwd_guest = CharField()

    class Meta:
        order_by = ('camera', '-date')

    def _create(camera, date, user_a, passwd_a, user_m, passwd_m, user_g, passwd_g):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the credentials.
                credentials = Credentials.create(
                    camera=camera,
                    date=date,
                    user_admin=user_a,
                    passwd_admin=passwd_a,
                    user_mod=user_m,
                    passwd_mod=passwd_m,
                    user_guest=user_g,
                    passwd_guest=passwd_g
                )
        except IntegrityError:
            pass
        return credentials

    def _create_dict(camera, date, cred_dict):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the credentials.
                credentials = Credentials.create(
                    camera=camera,
                    date=date,
                    user_admin=cred_dict.get('3_name', ''),
                    passwd_admin=cred_dict.get('3_pwd', ''),
                    user_mod=cred_dict.get('2_name', ''),
                    passwd_mod=cred_dict.get('2_pwd', ''),
                    user_guest=cred_dict.get('1_name', ''),
                    passwd_guest=cred_dict.get('1_pwd', '')
                )
        except IntegrityError:
            pass
        return credentials

    ###Statistics###
    def _get_stats(limit=50):
        credentials = None
        try:
            with db.execution_context() as ctx:
                subquery = Camera.select(Camera.id.alias('camid')).annotate(
                    Credentials, fn.Max(Credentials.id).alias('credid')).alias('subquery')
                user = list(Credentials.select(Credentials.user_admin.alias('user'), fn.Count(Credentials.id).alias('rep')).join(subquery, on=(
                    Credentials.id == subquery.c.credid).alias('credid')).group_by(SQL('user')).order_by(SQL('rep').desc()).limit(limit).dicts())
                passwd = list(Credentials.select(Credentials.passwd_admin.alias('passwd'), fn.Count(Credentials.id).alias('rep')).join(subquery, on=(
                    Credentials.id == subquery.c.credid).alias('credid')).group_by(SQL('passwd')).order_by(SQL('rep').desc()).limit(limit).dicts())
                credentials = {'user': {d['user']: d['rep'] for d in user}, 'passwd': {
                    d['passwd']: d['rep'] for d in passwd}}
        except Credentials.DoesNotExist:
            pass
        return credentials

    def cmp(self, user_a, passwd_a, user_m, passwd_m, user_g, passwd_g):  # compare
        return self.user_admin == user_a and self.passwd_admin == passwd_a and self.user_mod == user_m and self.passwd_mod == passwd_m and \
            self.user_guest == user_g and self.passwd_guest == passwd_g

    def cmp_dict(self, cred_dict):  # compare
        return self.user_admin == cred_dict.get('3_name', '') and self.passwd_admin == cred_dict.get('3_pwd', '') and self.user_mod == cred_dict.get('2_name', '') and \
            self.passwd_mod == cred_dict.get('2_pwd', '') and self.user_guest == cred_dict.get(
                '1_name', '') and self.passwd_guest == cred_dict.get('1_pwd', '')


class Address(BaseModel):
    camera = ForeignKeyField(Camera, related_name='addr_belongs_to')
    date = ForeignKeyField(Timestamp, related_name='addr_at')
    ip = CharField()
    port = IntegerField()

    class Meta:
        order_by = ('camera', '-date')

    def _create(camera, date, ip, port):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the address.
                address = Address.create(
                    camera=camera,
                    date=date,
                    ip=ip,
                    port=port
                )
        except IntegrityError:
            pass
        return address

    ###Statistics###
    def _get_stats(limit=50):
        address = None
        try:
            with db.execution_context() as ctx:
                subquery = Camera.select(Camera.id.alias('camid')).annotate(
                    Address, fn.Max(Address.id).alias('addrid')).alias('subquery')
                ip_prefix = list(Address.select(fn.substring_index(Address.ip, '.', 2).alias('ip_prefix'), fn.Count(Address.id).alias('rep')).join(
                    subquery, on=(Address.id == subquery.c.addrid).alias('addrid')).group_by(SQL('ip_prefix')).order_by(SQL('rep').desc()).limit(limit).dicts())
                port = list(Address.select(Address.port.alias('port'), fn.Count(Address.id).alias('rep')).join(subquery, on=(
                    Address.id == subquery.c.addrid).alias('addrid')).group_by(SQL('port')).order_by(SQL('rep').desc()).limit(limit).dicts())
                address = {'ip_prefix': {d['ip_prefix']: d['rep'] for d in ip_prefix}, 'port': {
                    d['port']: d['rep'] for d in port}}
        except Address.DoesNotExist:
            pass
        return address

    def cmp(self, ip, port):  # compare
        return self.ip == ip and self.port == port


class DDNS(BaseModel):
    camera = ForeignKeyField(Camera, related_name='ddns_belongs_to')
    date = ForeignKeyField(Timestamp, related_name='ddns_at')
    service = IntegerField()
    host = CharField()
    user = CharField()
    passwd = CharField()
    proxy_host = CharField()
    proxy_port = IntegerField()
    status = IntegerField()

    def _create(camera, date, service, host, user, passwd, proxy_host, proxy_port, status):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the ddns.
                ddns = DDNS.create(
                    camera=camera,
                    date=date,
                    service=int(service),
                    host=host,
                    user=user,
                    passwd=passwd,
                    proxy_host=proxy_host,
                    proxy_port=int(proxy_port),
                    status=int(status)
                )
        except IntegrityError:
            pass
        return ddns

    def _create_dict(camera, date, ddns_dict):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the ddns with dict.
                ddns = DDNS.create(
                    camera=camera,
                    date=date,
                    service=int(ddns_dict.get('service', '0')),
                    host=ddns_dict.get('host', ''),
                    user=ddns_dict.get('user', ''),
                    passwd=ddns_dict.get('pwd', ''),
                    proxy_host=ddns_dict.get('proxy_svr', ''),
                    proxy_port=int(ddns_dict.get('proxy_port', '0')),
                    status=int(ddns_dict.get('status', '0'))
                )
        except IntegrityError:
            pass
        return ddns

    def cmp(self, service, host, user, passwd, proxy_host, proxy_port, status):  # compare
        return self.service == int(service) and self.host == host and self.user == user and self.passwd == passwd and \
            self.proxy_host == proxy_host and self.proxy_port == int(
                proxy_port) and self.status == int(status)

    def cmp_dict(self, ddns_dict):  # compare
        return self.service == int(ddns_dict.get('service', '0')) and self.host == ddns_dict.get('host', '') and self.user == ddns_dict.get('user', '') and \
            self.passwd == ddns_dict.get('pwd', '') and self.proxy_host == ddns_dict.get('proxy_host', '') and \
            self.proxy_port == int(ddns_dict.get('proxy_port', '0')) and self.status == int(
                ddns_dict.get('status', '0'))


class FTP(BaseModel):
    camera = ForeignKeyField(Camera, related_name='ftp_belongs_to')
    date = ForeignKeyField(Timestamp, related_name='ftp_at')
    host = CharField()
    port = IntegerField()
    user = CharField()
    passwd = CharField()
    path = CharField()
    mode = BooleanField()
    upload_interval = IntegerField()

    def _create(camera, date, host, port, user, passwd, path, mode, upload_interval):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the ftp.
                ftp = FTP.create(
                    camera=camera,
                    date=date,
                    host=host,
                    port=int(port),
                    user=user,
                    passwd=passwd,
                    path=path,
                    mode=str(mode) == '1',
                    upload_interval=int(upload_interval)
                )
        except IntegrityError:
            pass
        return ftp

    def _create_dict(camera, date, ftp_dict):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the cftp with a dict.
                ftp = FTP.create(
                    camera=camera,
                    date=date,
                    host=ftp_dict.get('svr', ''),
                    port=int(ftp_dict.get('port', '0')),
                    user=ftp_dict.get('user', ''),
                    passwd=ftp_dict.get('pwd', ''),
                    path=ftp_dict.get('dir', ''),
                    mode=str(ftp_dict.get('mode', '0')) == '1',
                    upload_interval=int(ftp_dict.get('upload_interval', '0'))
                )
        except IntegrityError:
            pass
        return ftp

    def cmp(self, host, port, user, passwd, path, mode, upload_interval):  # compare
        return self.host == host and self.port == int(port) and self.user == user and self.passwd == passwd and self.path == path and \
            self.mode == (str(mode) == '1') and self.upload_interval == int(
                upload_interval)

    def cmp_dict(self, ftp_dict):  # compare
        return self.host == ftp_dict.get('svr', '') and self.port == int(ftp_dict.get('port', '0')) and self.user == ftp_dict.get('user', '') and \
            self.passwd == ftp_dict.get('pwd', '') and self.path == ftp_dict.get('dir', '') and \
            self.mode == (str(ftp_dict.get('mode', '0')) == '1') and self.upload_interval == int(
                ftp_dict.get('upload_interval', '0'))


class Location(BaseModel):
    camera = ForeignKeyField(Camera, related_name='loc_belongs_to')
    date = ForeignKeyField(Timestamp, related_name='loc_at')
    lat = DoubleField(null=True)
    lng = DoubleField(null=True)
    accuracy = DoubleField(null=True)
    max_accuracy = 150
    addr_street_number = TextField(null=True)
    addr_route = TextField(null=True)
    addr_city = TextField(null=True)
    addr_region = TextField(null=True)
    addr_postal_code = TextField(null=True)
    addr_country = TextField()
    addr_formatted = TextField(null=True)
    # detail [0: geoloc+geocode, 1:geoloc+country(ip based), 2:country(ip based)]
    detail = IntegerField()

    class Meta:
        order_by = ('camera', '-date')

    def _create(camera, date, geoloc, addr):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the location with geoloc and a dict.
                location = Location.create(
                    camera=camera,
                    date=date,
                    lat=geoloc['lat'],
                    lng=geoloc['lng'],
                    accuracy=geoloc['accuracy'],
                    # street_number, premise, sublocality_level_4
                    addr_street_number=addr.get('street_number', ''),
                    # route, sublocality_level_2
                    addr_route=addr.get('route', ''),
                    addr_city=addr.get('city', ''),  # locality
                    # administrative_area_level_1
                    addr_region=addr.get('region', ''),
                    addr_postal_code=addr.get('postal_code', ''),
                    addr_country=addr.get('country', ''),
                    addr_formatted=addr.get('formatted', ''),
                    detail=0
                )
        except IntegrityError:
            pass
        return location

    def _create_loc(camera, date, geoloc, country):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the address only with geoloc and country (ip based).
                location = Location.create(
                    camera=camera,
                    date=date,
                    lat=geoloc['lat'],
                    lng=geoloc['lng'],
                    accuracy=geoloc['accuracy'],
                    addr_country=country,
                    detail=1
                )
        except IntegrityError:
            pass
        return location

    def _create_country(camera, date, country):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the address only with a country (ip based).
                location = Location.create(
                    camera=camera,
                    date=date,
                    addr_country=country,
                    detail=2
                )
        except IntegrityError:
            pass
        return location

    def distance(self, lat, lng):
        # Calculate the great circle distance between two points
        # on the earth (specified in decimal degrees)
        for i in [self.lat, self.lng]:
            if type(i) != int:
                return 0

        for i in [lat, lng]:
            if type(i) != int:
                return self.max_accuracy

        lat1, lng1, lat2, lng2 = map(radians, [self.lat, self.lng, lat, lng])

        dlat = lat2 - lat1
        dlon = lng2 - lng1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        m = 6367000 * c
        return m

    ###Statistics###
    def _get_stats_dict(det=2):
        mydict = None
        try:
            with db.execution_context() as ctx:
                subquery = Camera.select(Camera.id.alias('camid')).annotate(
                    Location, fn.Max(Location.id).alias('locid')).alias('subquery')
                locations_raw = list(Location.select(Location.addr_country.alias('country'), Location.addr_region.alias('region'), fn.Count(SQL('*')).alias('rep')).join(
                    subquery, on=(Location.id == subquery.c.locid).alias('loc')).where(Location.detail < det).group_by(SQL('country, region')).order_by(SQL('rep').desc()).dicts())
                mydict = {}
                for loc in locations_raw:
                    loc_country = loc.get('country', '')
                    if loc_country is None or loc_country == '':
                        loc_country = 'unkown'
                    loc_region = loc.get('region', '')
                    if loc_region is None or loc_region == '':
                        loc_region = 'unkown'
                    country = mydict.get(
                        loc_country, {'total': 0, 'region': {}})
                    region = country.get('region')
                    region.update({loc_region: loc.get('rep', 0)})
                    country.update({'total': country.get(
                        'total') + loc.get('rep', 0), 'region': region})
                    mydict.update({loc_country: country})
        except Location.DoesNotExist:
            pass
        return mydict

    def cmp(self, lat, lng, accuracy):  # Returns false if nos equal or accuracy shitty
        if self.accuracy:
            # if self.accuracy is not None:
            if accuracy < self.max_accuracy:
                return self.distance(lat, lng) < min(self.accuracy, accuracy)
            else:
                return False
        else:
            return True

    def cmp_country(self, country):
        return self.addr_country == country

    def addr_format(self):
        if self.detail == 0:
            return "%s %s, %s, %s %s, %s" % (self.addr_street_number, self.addr_route, self.addr_city, self.addr_region, self.addr_postal_code, self.addr_country)
        else:
            return self.addr_country


class Mail(BaseModel):
    camera = ForeignKeyField(Camera, related_name='mail_belongs_to')
    date = ForeignKeyField(Timestamp, related_name='mail_at')
    email = CharField()
    host = CharField()
    port = IntegerField()
    user = CharField()
    passwd = CharField()
    ssl = BooleanField()
    receiver1 = CharField()
    receiver2 = CharField()
    receiver3 = CharField()
    receiver4 = CharField()
    inet_ip = BooleanField()

    def _create(camera, date, email, host, port, user, passwd, ssl, receiver1, receiver2, receiver3, receiver4, inet_ip):
        receivers = sorted([receiver1, receiver2, receiver3,
                            receiver4], key=lambda x: (x == "", x.lower()))
        try:
            with db.execution_context() as ctx:
                # Attempt to create the mail.
                mail = Mail.create(
                    camera=camera,
                    date=date,
                    email=email,
                    host=host,
                    port=int(port),
                    user=user,
                    passwd=passwd,
                    ssl=str(ssl) == '1',
                    receiver1=receivers[0],
                    receiver2=receivers[1],
                    receiver3=receivers[2],
                    receiver4=receivers[3],
                    inet_ip=str(inet_ip) == '1'
                )
        except IntegrityError:
            pass
        return mail

    def _create_dict(camera, date, mail_dict):
        receivers = sorted([mail_dict.get('receiver1', ''), mail_dict.get('receiver2', ''), mail_dict.get(
            'receiver3', ''), mail_dict.get('receiver4', '')], key=lambda x: (x == "", x.lower()))
        try:
            with db.execution_context() as ctx:
                # Attempt to create the credentials.
                mail = Mail.create(
                    camera=camera,
                    date=date,
                    email=mail_dict.get('sender', ''),
                    host=mail_dict.get('svr', ''),
                    port=int(mail_dict.get('port', '0')),
                    user=mail_dict.get('user', ''),
                    passwd=mail_dict.get('pwd', ''),
                    ssl=str(mail_dict.get('ssl', '0')) == '1',
                    receiver1=receivers[0],
                    receiver2=receivers[1],
                    receiver3=receivers[2],
                    receiver4=receivers[3],
                    inet_ip=str(mail_dict.get('inet_ip', '0')) == '1'
                )
        except IntegrityError:
            pass
        return mail

    def cmp(self, email, host, port, user, passwd, ssl, receiver1, receiver2, receiver3, receiver4, inet_ip):  # compare
        receivers = sorted([receiver1, receiver2, receiver3,
                            receiver4], key=lambda x: (x == "", x.lower()))
        return self.email == email and self.host == host and self.port == int(port) and self.user == user and self.passwd == passwd and self.ssl == (str(ssl) == '1') and \
            self.receiver1 == receivers[0] and self.receiver2 == receivers[1] and self.receiver3 == receivers[
                2] and self.receiver4 == receivers[3] and self.inet_ip == (str(inet_ip) == '1')

    def cmp_dict(self, mail_dict):  # compare
        receivers = sorted([mail_dict.get('receiver1', ''), mail_dict.get('receiver2', ''), mail_dict.get(
            'receiver3', ''), mail_dict.get('receiver4', '')], key=lambda x: (x == "", x.lower()))
        return self.email == mail_dict.get('sender', '') and self.host == mail_dict.get('svr', '') and self.port == int(mail_dict.get('port', '0')) and \
            self.user == mail_dict.get('user', '') and self.passwd == mail_dict.get('pwd', '') and self.ssl == (str(mail_dict.get('ssl', '0')) == '1') and \
            self.receiver1 == receivers[0] and self.receiver2 == receivers[1] and self.receiver3 == receivers[2] and self.receiver4 == receivers[3] and \
            self.inet_ip == (str(mail_dict.get('inet_ip', '0')) == '1')


class Status(BaseModel):
    camera = ForeignKeyField(Camera, related_name='stat_belongs_to')
    date = ForeignKeyField(Timestamp, related_name='stat_at')
    alias = CharField()
    sys_ver = CharField()
    app_ver = CharField()
    oem_id = CharField()
    sd_status = IntegerField()
    syswifi_mode = IntegerField()

    class Meta:
        order_by = ('camera', '-date')

    def _create(camera, date, alias, sys_ver, app_ver, oem_id, sd_status, syswifi_mode):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the status.
                status = Status.create(
                    camera=camera,
                    date=date,
                    alias=alias,
                    sys_ver=sys_ver,
                    app_ver=app_ver,
                    oem_id=oem_id,
                    sd_status=int(sd_status),
                    syswifi_mode=int(syswifi_mode)
                )
        except IntegrityError:
            pass
        return status

    def cmp(self, alias, sys_ver, app_ver, oem_id, sd_status, syswifi_mode):
        return self.alias == alias and self.sys_ver == sys_ver and self.app_ver == app_ver and self.oem_id == oem_id and self.sd_status == int(sd_status) and self.syswifi_mode == int(syswifi_mode)


class SmartEye(BaseModel):
    camera = ForeignKeyField(Camera, related_name='se_belongs_to')
    date = ForeignKeyField(Timestamp, related_name='se_at')
    enable = BooleanField()
    domain = CharField()
    port = IntegerField()
    user = CharField()
    passwd = CharField()
    service = CharField()
    interval = IntegerField()
    status = IntegerField()

    class Meta:
        order_by = ('camera', '-date')

    def _create(camera, date, enable, name, port, user, pwd, svr, interval, status):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the status.
                smarteye = SmartEye.create(
                    camera=camera,
                    date=date,
                    enable=str(enable) == '1',
                    domain=name,
                    port=port,
                    user=user,
                    passwd=pwd,
                    service=svr,
                    interval=int(interval),
                    status=int(status)
                )
        except IntegrityError:
            pass
        return smarteye

    def _create_dict(camera, date, se_dict):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the credentials.
                smarteye = SmartEye.create(
                    camera=camera,
                    date=date,
                    enable=str(se_dict.get('enable', '0')) == '1',
                    domain=se_dict.get('name', ''),
                    port=int(se_dict.get('port', '0')),
                    user=se_dict.get('user', ''),
                    passwd=se_dict.get('pwd', ''),
                    service=se_dict.get('svr', ''),
                    interval=int(se_dict.get('interval', '0')),
                    status=int(se_dict.get('status', '0'))
                )
        except IntegrityError:
            pass
        return smarteye

    def _get_distinct_id(provider=None):
        smarteye = None
        try:
            with db.execution_context() as ctx:
                if provider is not None:
                    smarteye = list(SmartEye.select(SmartEye.domain, SmartEye.service).distinct(
                    ).where((SmartEye.service == provider) and (SmartEye.domain != '')).dicts())
                else:
                    smarteye = list(SmartEye.select(SmartEye.domain, SmartEye.service).distinct(
                    ).where((SmartEye.service != '') and (SmartEye.domain != '')).dicts())

        except SmartEye.DoesNotExist:
            pass
        return smarteye

    def cmp(self, enable, name, port, user, pwd, svr, interval, status):  # compare
        return self.enable == (str(enable) == '1') and self.domain == name and self.port == int(port) and self.user == user and self.passwd == passwd and self.service == svr and \
            self.interval == int(interval) and self.status == int(status)

    def cmp_dict(self, se_dict):  # compare
        return self.enable == (str(se_dict.get('enable', '0')) == '1') and self.domain == se_dict.get('name', '') and self.port == int(se_dict.get('port', '0')) and \
            self.user == se_dict.get('user', '') and self.passwd == se_dict.get('pwd', '') and self.service == se_dict.get('svr', '') and \
            self.interval == int(se_dict.get('interval', '0')) and self.status == int(
                se_dict.get('status', '0'))


class Wifi_scan(BaseModel):
    camera = ForeignKeyField(Camera, related_name='ws_belongs_to')
    date = ForeignKeyField(Timestamp, related_name='ws_at')
    enabled = BooleanField()

    class Meta:
        order_by = ('camera', '-date')

    def _create(camera, date, enabled):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the wifi_scan.
                wifi_scan = Wifi_scan.create(
                    camera=camera,
                    date=date,
                    enabled=enabled
                )
        except IntegrityError:
            pass
        return wifi_scan

    def get_wifis(self):
        wifis = None
        try:
            with db.execution_context() as ctx:
                wifis = list(Wifi.select().distinct().where(Wifi.scan == self))
        except Wifi_scan.DoesNotExist:
            pass
        return wifis


class Wifi(BaseModel):
    scan = ForeignKeyField(Wifi_scan, related_name='wi_belongs_to')
    ssid = CharField()
    mac = CharField()
    mode = BooleanField()  # True infrastructure, False ad-hoc
    security = IntegerField()  # 0-7
    channel = IntegerField()  # 0-14
    power = IntegerField()  # 0-100
    is_ap = BooleanField(default=False)
    security_types = [
        "None", "WEP", "WPAPSK(TKIP)", "WPAPSK(AES)", "WPA2PSK(AES)", "WPA2PSK(TKIP)", "Not supported"]

    class Meta:
        order_by = ('scan',)

    def _create(scan, ssid, mac, mode, security, channel, power, is_ap):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the wifi.
                wifi = Wifi.create(
                    scan=scan,
                    ssid=ssid,
                    # replace('-', ':') was not supposed to be necessary, but...
                    mac=mac.replace('-', ':').upper(),
                    mode=mode,
                    security=security,
                    channel=channel,
                    power=power,
                    is_ap=is_ap
                )
            return wifi
        except IntegrityError:
            pass

    def _create_dict(scan, wifi_d, is_ap):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the wifi with a dict.
                wifi = Wifi.create(
                    scan=scan,
                    ssid=wifi_d.get('ap_ssid', ''),
                    # replace('-', ':') was not supposed to be necessary, but...
                    mac=wifi_d['ap_mac'].replace('-', ':').upper(),
                    mode=str(wifi_d['ap_mode']) == '0',
                    security=wifi_d['ap_security'],
                    channel=wifi_d['ap_channel'],
                    power=wifi_d['ap_dbm0'],
                    is_ap=wifi_d['is_ap']
                )
        except IntegrityError:
            pass
        return wifi

    def _create_dict_bulk(scan, wifis_d):
        wifis = []
        if len(wifis_d) != 0:
            try:
                with db.execution_context() as ctx:
                    # Attempt to create the wifis with a dict, bulk method.
                    for wifi_d in wifis_d:
                        wifi = Wifi.create(
                            scan=scan,
                            ssid=wifi_d.get('ap_ssid', ''),
                            # replace('-', ':') was not supposed to be necessary, but damn dim sum...
                            mac=wifi_d['ap_mac'].replace('-', ':').upper(),
                            mode=str(wifi_d['ap_mode']) == '0',
                            security=wifi_d['ap_security'],
                            channel=wifi_d['ap_channel'],
                            power=wifi_d['ap_dbm0'],
                            is_ap=wifi_d['is_ap']
                        )
                        wifis.append(wifi)
            except IntegrityError:
                pass
        return wifis

    def _get_distinct_mac():
        wifis = None
        try:
            with db.execution_context() as ctx:
                wifis = list(Wifi.select(Wifi.mac).distinct().dicts())
        except Wifi.DoesNotExist:
            pass
        return wifis

    ###Statistics###
    def _get_stats():
        wifis = None
        try:
            with db.execution_context() as ctx:
                wifis = Wifi.select(fn.Count(fn.Distinct(Wifi.mac))).scalar()
        except Wifi.DoesNotExist:
            pass
        return wifis


class Wifi_AP(BaseModel):
    scan = ForeignKeyField(Wifi_scan, related_name='wa_belongs_to')
    ssid = CharField()
    mode = BooleanField()  # True infrastructure, False ad-hoc
    security = IntegerField()  # 0-7
    wep_encrypt = BooleanField(default=False)
    password = CharField()
    password_bits = BooleanField(default=False)

    class Meta:
        order_by = ('scan',)

    def _create(scan, ssid, mode, security, wep_encrypt, password, password_bits):
        try:
            with db.execution_context() as ctx:
                # Attempt to create the wifi_ap.
                wifi = Wifi_AP.create(
                    scan=scan,
                    ssid=ssid,
                    mode=mode,
                    security=security,
                    wep_encrypt=wep_encrypt,
                    password=password,
                    password_bits=password_bits
                )
        except IntegrityError:
            pass
        return wifi

    def _create_open(scan, ssid, mode):
        return Wifi_AP._create(scan, ssid, mode, 0, False, '', False)

    def _create_wep(scan, ssid, mode, wep_encrypt, password, password_bits):
        return Wifi_AP._create(scan, ssid, mode, 1, wep_encrypt, password, password_bits)

    def _create_wpa(scan, ssid, mode, security, password):
        return Wifi_AP._create(scan, ssid, mode, security, False, password, False)

    def _get_located_dict(det=2, **kwargs):
        mydict = None
        try:
            with db.execution_context() as ctx:
                wifiquery = Wifi_AP.select(Wifi_AP.scan_id.alias('wifiid'))
                scanquery = Wifi_scan.select(Wifi_scan.id, Wifi_scan.camera_id).where(
                    Wifi_scan.id << wifiquery).alias('wscanid')
                subquery = Camera.select(fn.Max(scanquery.c.id).alias('scanid'), fn.Max(Location.id).alias('locid')).join(
                    scanquery, on=(Camera.id == scanquery.c.camera_id)).join(Location).group_by(Camera.id).alias('subquery')
                if 'country' in kwargs:
                    mydict = list(Wifi_AP.select(Wifi_AP.ssid, Wifi_AP.security, Wifi_AP.password, Location.lat, Location.lng, Location.addr_formatted).join(subquery, on=(Wifi_AP.scan_id == subquery.c.scanid).alias(
                        'wifi')).join(Location, on=(Location.id == subquery.c.locid).alias('loc')).where((Location.detail < 1) & (Location.addrcountry == kwargs['country'])).dicts())
                else:
                    mydict = list(Wifi_AP.select(Wifi_AP.ssid, Wifi_AP.security, Wifi_AP.password, Location.lat, Location.lng, Location.addr_formatted).join(subquery, on=(
                        Wifi_AP.scan_id == subquery.c.scanid).alias('wifi')).join(Location, on=(Location.id == subquery.c.locid).alias('loc')).where(Location.detail < det).dicts())
        except Wifi_AP.DoesNotExist:
            pass
        return mydict

    ###Statistics###
    def _get_stats(limit=50):
        mydict = None
        try:
            with db.execution_context() as ctx:
                wifiquery = Wifi_AP.select(Wifi_AP.scan_id.alias('wifiid'))
                scanquery = Wifi_scan.select(Wifi_scan.id, Wifi_scan.camera_id).where(
                    Wifi_scan.id << wifiquery).alias('wscanid')
                subquery = Camera.select(fn.Max(scanquery.c.id).alias('scanid')).join(scanquery, on=(
                    Camera.id == scanquery.c.camera_id)).group_by(Camera.id).alias('subquery')
                ssid = list(Wifi_AP.select(Wifi_AP.ssid.alias('ssid'), fn.Count(SQL('*')).alias('rep')).join(subquery, on=(
                    Wifi_AP.scan_id == subquery.c.scanid).alias('wifi')).group_by(SQL('ssid')).order_by(SQL('rep').desc()).limit(limit).dicts())
                passwd = list(Wifi_AP.select(Wifi_AP.password.alias('passwd'), fn.Count(SQL('*')).alias('rep')).join(subquery, on=(
                    Wifi_AP.scan_id == subquery.c.scanid).alias('wifi')).group_by(SQL('passwd')).order_by(SQL('rep').desc()).limit(limit).dicts())
                security = list(Wifi_AP.select(Wifi_AP.security.alias('security'), fn.Count(SQL('*')).alias('rep')).join(subquery, on=(
                    Wifi_AP.scan_id == subquery.c.scanid).alias('wifi')).group_by(SQL('security')).order_by(SQL('rep').desc()).limit(limit).dicts())
                mydict = {'ssid': {d['ssid']: d['rep'] for d in ssid}, 'passwd': {d['passwd']: d['rep'] for d in passwd}, 'security': {
                    Wifi.security_types[int(d['security'])]: d['rep'] for d in security}}
        except Wifi_AP.DoesNotExist:
            pass
        return mydict

    def _get_located_stats_dict(det=2):
        mydict = None
        try:
            with db.execution_context() as ctx:
                wifiquery = Wifi_AP.select(Wifi_AP.scan_id.alias('wifiid'))
                scanquery = Wifi_scan.select(Wifi_scan.id, Wifi_scan.camera_id).where(
                    Wifi_scan.id << wifiquery).alias('wscanid')
                subquery = Camera.select(fn.Max(scanquery.c.id).alias('scanid'), fn.Max(Location.id).alias('locid')).join(
                    scanquery, on=(Camera.id == scanquery.c.camera_id)).join(Location).group_by(Camera.id).alias('subquery')
                list(Wifi_AP.select(Location.addr_country.alias('country'), fn.Count(Wifi_AP.id).alias('wifi_ap')).join(subquery, on=(Wifi_AP.scan_id == subquery.c.scanid).alias(
                    'wifi')).join(Location, on=(Location.id == subquery.c.locid).alias('loc')).where(Location.detail < det).group_by(Location.addr_country).dicts())
        except Wifi_AP.DoesNotExist:
            pass
        return mydict

    def cmp(self, ssid, mode, security, wep_encrypt, password, password_bits):
        return self.ssid == ssid and self.mode == mode and self.security == security and self.wep_encrypt == wep_encrypt and self.password == password, self.password_bits == password_bits


def get_stats():
    ###Statistics###
    mytuples = None
    mydict = None
    dt = [datetime.datetime.now() - datetime.timedelta(hours=hh)
          for hh in [6, 12, 24, 48]]
    try:
        with db.execution_context() as ctx:
            mydict = {'Camera': {'Total': Camera.select().count(), 'Active': Camera.select().where(Camera.retry == 0).count()},
                      'Timestamp': {'Total': Timestamp.select().count(), 'last 6h': Timestamp.select().where(Timestamp.date > dt[0]).count(), 'last 12h': Timestamp.select().where(Timestamp.date > dt[1]).count(), 'last 24h': Timestamp.select().where(Timestamp.date > dt[2]).count(), 'last 48h': Timestamp.select().where(Timestamp.date > dt[3]).count()},
                      'Address': Address.select().count(),
                      'Credentials': Credentials.select().count(),
                      'DDNS': DDNS.select().count(),
                      'FTP': FTP.select().count(),
                      'Mail': Mail.select().count(),
                      'Status': Status.select().count(),
                      'SmartEye': SmartEye.select().count(),
                      'Wifi Scan': {'Total': Wifi_scan.select().count(), 'APs': Wifi_AP.select().count(), 'Wifis': Wifi.select().count()},
                      'Location': {'Total': Location.select().count(), 'Precise': Location.select().where(Location.detail < 1).count(), 'LatLng': Location.select().where(Location.detail < 2).count(), 'Countries': Location.select(fn.Count(fn.Distinct(Location.addr_country))).scalar()}}
    except Exception:
        pass
    return mydict


def create_tables():
    db.connect()

    db.create_tables([Camera, Timestamp, Credentials, Address, DDNS, FTP,
                      Location, Mail, Status, SmartEye, Wifi_scan, Wifi, Wifi_AP], safe=True)

    if not db.is_closed():
        db.close()

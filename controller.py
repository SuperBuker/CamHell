from model import db, create_tables, get_stats
from processmodel import DBProc, SmartEyeDBProc, ShodanProc, ShodanStreamProc, CensysProc, ZoomEyeProc, SmartEyeProc, PwnProc, GeoProc, PriorityQueue

from flask import Flask, request, render_template, send_from_directory, send_file, redirect, Response
#from flask.logging import default_handler
from flask_compress import Compress

import sys
from os import kill, getpid
from signal import signal, SIGALRM, SIGTERM

from multiprocessing import Event, Queue, Value
from threading import Thread
from math import log
from time import sleep
from json import dumps as json_dumps
from datetime import datetime


class Controller:
    runFlag = True
    myFeeders = {feeder: [] for feeder in ['DBProc', 'SmartEyeDBProc', 'ShodanProc',
                                           'ShodanStreamProc', 'CensysProc', 'ZoomEyeProc', 'SmartEyeProc']}
    myDB = []
    myShodan = []
    q = [PriorityQueue(3), PriorityQueue(1), None]
    myProcs = {'class': [PwnProc, GeoProc], 'name': [
        'PwnProc', 'GeoProc'], 'list': [[], []]}

    # Idealworkers formula
    workers_formula = [{'base_log': 100, 'exp': 4.5},
                       {'base_log': 10, 'exp': 2.3}]

    #countries = ['ES', 'PT', 'AD', 'FR', 'BE', 'IT', 'CH', 'NL', 'DE','GB', 'IE']
    countries = [None]

    def __init__(self):
        pass

    def setup_db():
        print('Setting DB')
        sys.stdout.flush()
        create_tables()

    def connect_db():
        print('Processing started')
        print('Main PID: %s' % (getpid()))
        db.connect()

    def start_feeder(self, feeder):
        if feeder == 'ShodanProc':
            for i in range(len(self.countries)):
                s_p = ShodanProc(
                    len(self.myFeeders[feeder]), self.q[0], self.countries[i])
                self.myFeeders[feeder].append(s_p)
                s_p.start()
                sleep(2)
            return True
        elif feeder in ['DBProc', 'SmartEyeDBProc', 'ShodanStreamProc', 'CensysProc', 'ZoomEyeProc', 'SmartEyeProc']:
            if feeder == 'DBProc':
                f_p = DBProc(len(self.myFeeders[feeder]), self.q[0], 12)
            elif feeder == 'SmartEyeDBProc':
                f_p = SmartEyeDBProc(len(self.myFeeders[feeder]), self.q[0])
            elif feeder == 'ShodanStreamProc':
                f_p = ShodanStreamProc(len(self.myFeeders[feeder]), self.q[0])
            elif feeder == 'CensysProc':
                f_p = CensysProc(len(self.myFeeders[feeder]), self.q[0])
            elif feeder == 'ZoomEyeProc':
                f_p = ZoomEyeProc(len(self.myFeeders[feeder]), self.q[0])
            elif feeder == 'SmartEyeProc':
                f_p = SmartEyeProc(len(self.myFeeders[feeder]), self.q[0])
            self.myFeeders[feeder].append(f_p)
            f_p.start()
            sleep(1)
            return True
        else:
            return False

    def stop_feeder(self, feeder):
        if feeder in self.myFeeders:
            feeder_list = [
                feeder for feeder in self.myFeeders[feeder] if feeder.getFlag()]
            if len(feeder_list) > 0:
                feeder_list[-1].stop()
                return True
        return False

    def loop(self):
        Controller.connect_db()
        loop = 0
        while(int(self.runFlag) + len(self.myProcs['list'][0]) + len(self.myProcs['list'][1]) > 0):
            for feeder in self.myFeeders:
                self.myFeeders[feeder] = [
                    f_p for f_p in self.myFeeders[feeder] if f_p.getFlag() and f_p.is_alive()]

            for i in range(len(self.myProcs['list'])):
                self.myProcs['list'][i] = [
                    p_p for p_p in self.myProcs['list'][i] if p_p.is_alive()]
                ulock = [[p_p.getID(), kill(p_p.pid, SIGALRM)]
                         for p_p in self.myProcs['list'][i] if p_p.beat() == 0]
                if len(ulock) != 0:  # Unlocking hanged processes
                    print('[ProcController] Unlocking process', [p_p[0]
                                                                 for p_p in ulock])
                self.myProcs['list'][i] = [
                    p_p for p_p in self.myProcs['list'][i] if p_p.is_alive()]

            for i in range(len(self.q) - 1):
                print('[ProcController] Status Q%s: %s elements' %
                      (i + 1, self.q[i].qsize(True)))
                sys.stdout.flush()

            for i in range(len(self.myProcs['class'])):
                if self.runFlag:
                    idealWorkers = max(int(round(log(self.q[i].qsize() + 0.509 * self.workers_formula[0]['base_log'], self.workers_formula[0]['base_log'])**self.workers_formula[0]['exp'])),
                                       int(round(log(self.q[i].qsize() + 0.509 * self.workers_formula[1]['base_log'], self.workers_formula[1]['base_log'])**self.workers_formula[1]['exp'])))
                    if self.q[i].qsize() > 0 and idealWorkers == 0:  # Safety measure
                        idealWorkers = 1
                else:
                    idealWorkers = 0
                    # Consider this a graceful stop. Not the best because all the process (including the GeoProcs) are stopped.

                futureWorkers = [p_p.getFlag()
                                 for p_p in self.myProcs['list'][i]].count(True)
                print('[ProcController] %s: %s of %s' %
                      (self.myProcs['name'][i], futureWorkers, idealWorkers))
                sys.stdout.flush()

                if idealWorkers < futureWorkers:
                    diff = futureWorkers - idealWorkers
                    counter = 0
                    for p_p in reversed(self.myProcs['list'][i]):
                        if counter == diff:
                            break
                        if p_p.is_alive() and p_p.getFlag():
                            p_p.stop()
                            counter += 1
                    print('[ProcController] %s: -%s' %
                          (self.myProcs['name'][i], counter))
                    sys.stdout.flush()

                elif idealWorkers > futureWorkers:
                    diff = idealWorkers - futureWorkers
                    counter = 0
                    for p_p in self.myProcs['list'][i]:
                        if counter == diff:
                            break
                        if p_p.is_alive() and not p_p.getFlag():
                            p_p.rerun()
                            counter += 1
                    while counter < diff:
                        myThreadIDs = [
                            p_p.getID() for p_p in self.myProcs['list'][i] if p_p.is_alive()]
                        if myThreadIDs:
                            p_p = self.myProcs['class'][i](
                                (set(range(max(myThreadIDs) + 2)) - set(myThreadIDs)).pop(), self.q[i], self.q[i + 1])
                        else:
                            p_p = self.myProcs['class'][i](
                                (set(range(2)) - set(myThreadIDs)).pop(), self.q[i], self.q[i + 1])
                        counter += 1
                        self.myProcs['list'][i].append(p_p)
                        p_p.start()
                    print('[ProcController] %s: +%s' %
                          (self.myProcs['name'][i], counter))
                    sys.stdout.flush()

            loop += 1
            sleep(10)
        Controller.disconnect_db()

    def feeders_status(self, feeder):
        if feeder == 'ShodanProc':
            return {idx: p_p.getWorkers() for idx, p_p in enumerate(self.myFeeders[feeder])}
        else:
            return len(self.myFeeders[feeder])

    def status(self):
        return {'Queues': [self.q[idx].qsize() for idx in range(len(self.q) - 1)],
                'Workers': {self.myProcs['name'][idx]: [p_p.getFlag() for p_p in self.myProcs['list'][idx]].count(True) for idx in range(len(self.myProcs['class']))},
                'Feeders': {feeder: self.feeders_status(feeder) for feeder in self.myFeeders}
                }

    def disconnect_db():
        if not db.is_closed():
            db.close()
        print('Processing finished')
        sys.stdout.flush()


app = Flask(__name__, static_url_path='')
Compress(app)
'''formatter = RequestFormatter(
    '[ProcController REST] %(remote_addr)s - %(asctime)s - %(url)s'
)
default_handler.setFormatter(formatter)'''
controller = None
log_com = []


@app.route('/')
def main():
    return Response(json_dumps({'status': 'ok'}, sort_keys=True, indent=4), mimetype='application/json')


@app.route('/status')
def status():
    global controller
    if controller is not None:
        return Response(json_dumps(controller.status(), sort_keys=True, indent=4), mimetype='application/json')
    else:
        return Response(json_dumps({'Queues': [controller.q[0].qsize(), controller.q[1].qsize()],
                                    'Workers': {'PwnProc': 0, 'GeoProc': 0},
                                    'Feeders': {'ShodanProc': {}, 'DBProc': 0}}, sort_keys=True, indent=4), status=500, mimetype='application/json')


@app.route('/status_db')
def status_db():
    global controller
    return Response(json_dumps(get_stats(), sort_keys=True, indent=4), mimetype='application/json')


@app.route('/start_feeder', methods=["POST"])
def start_feeder():
    global controller
    global log_com
    feeder = request.headers.get('Feeder')
    rst = 'fail'
    if controller is not None:
        if controller.runFlag:
            rst = controller.start_feeder(feeder)
            log_com.append('[%s] START %s: %s' % (
                datetime.now().strftime("%Y/%m/%d %H:%M:%S"), feeder, rst))
            log_com = log_com[-10:]
    return Response(json_dumps({'result': rst}, sort_keys=True, indent=4), mimetype='application/json')


@app.route('/stop_feeder', methods=["POST"])
def stop_feeder():
    global controller
    global log_com
    feeder = request.headers.get('Feeder')
    rst = 'fail'
    if controller is not None:
        if controller.runFlag:
            rst = controller.stop_feeder(feeder)
            log_com.append('[%s] STOP %s: %s' % (
                datetime.now().strftime("%Y/%m/%d %H:%M:%S"), feeder, rst))
            log_com = log_com[-10:]
    return Response(json_dumps({'result': rst}, sort_keys=True, indent=4), mimetype='application/json')


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/stop', methods=["POST"])
def stop():
    global controller
    if controller is not None:
        controller.runFlag = False
    try:
        shutdown_server()
    except RuntimeError:
        pass
    return Response(json_dumps({'result': 'ok'}, sort_keys=True, indent=4), mimetype='application/json')


@app.route('/log')
def log_commands():
    return Response(json_dumps(log_com, sort_keys=True, indent=4), mimetype='application/json')


def signal_handler(signum, stack):
    if signum == SIGTERM:
        global controller
        if controller is not None:
            controller.runFlag = False
        try:
            shutdown_server()
        except RuntimeError:
            pass


@app.after_request
def apply_caching(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    if response.cache_control.max_age == None:
        response.cache_control.max_age = 300
    return response


def flask_thread():
    app.run(host='0.0.0.0', port=3000)


if __name__ == '__main__':
    signal(SIGTERM, signal_handler)
    controller = Controller()
    Controller.setup_db()
    Thread(target=flask_thread).start()
    controller.loop()

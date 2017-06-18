# -*- coding: utf-8 -*-
from flask import Flask, request
from fbmq import Page, QuickReply, Attachment, Template
import requests, records, re, json
from flask_restful import Resource, Api
token = '<auth token here>'
metricsData = {}
macid = 111111111111
pg = Page(token)
import time
db = records.Database('mysql://<user>:<password>@<url>:3306/db')
app = Flask(__name__)
api = Api(app)

class deviceMetrics(Resource):
    def get(self):
        return {"energy": metricsData["energy"], "money_saved": metricsData["savings"], "days": metricsData["days"], "charging_status": "charging"}

@app.route('/')
def index():
    # return str(macid)
    return '^_^'

def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError

@app.route('/device/dbase')
def dbaser():
    data = db.query('select * from client where mac = %s LIMIT 1' % macid)
    time.sleep(1)
    return json.dumps(data.as_dict(), default=date_handler)

@app.route('/hook', methods=['POST'])
def hook():
    db = records.Database('mysql://<user>:<password>@<url>:3306/db')
    pg.greeting("Welcome, get started below!")
    # pg.show_starting_button("startpay")
    pg.handle_webhook(request.get_data(as_text=True))
    return 'ok'

@pg.handle_message
def mhandle(event):
    sender_id = event.sender_id.decode('utf-8')
    pg.typing_on(sender_id)

    # print event.message # debugging
    quick_replies = [
      {'title': 'Charging status', 'payload': 'charge_stat'},
      {'title': 'Last saved', 'payload': 'l_saved'},
      {'title': 'Total saving', 'payload': 'c_saved'},
    ]

    message = event.message_text
    rec = db.query("select * from user where fbid = %s" % sender_id)
    time.sleep(.5)
    if len(rec.as_dict()) == 0:
        user = pg.get_user_profile(sender_id)[u'first_name']
        message = ''.join(re.findall('\d+', message))
        if (len(str(message)) != 12):
            pg.send(sender_id, "Kindly enter your 12 digit MAC ID")
        else:
            db.query("insert into user values(DEFAULT, %s, %s)" % (sender_id, str(message)))
            pg.send(sender_id, "Registration successful!")
    else:
        pg.send(sender_id, "What do you want to know?", quick_replies=quick_replies)

@pg.callback(['startpay'])
def start_callback(payload, event):
    sender_id = event.sender_id.decode('utf-8')
    pg.typing_on(sender_id)
    db = records.Database('mysql://<user>:<password>@<url>:3306/db')
    rec = db.query("select * from user where fbid = %s" % sender_id)
    if len(rec.as_dict()) == 0:
        user = pg.get_user_profile(sender_id)[u'first_name']
        pg.send(sender_id, "Hey %s, please send me your MAC ID" % user)
    else:
        pg.typing_on(sender_id)
        quick_replies = [
          {'title': 'Charging status', 'payload': 'charge_stat'},
          {'title': 'Last saved', 'payload': 'l_saved'},
          {'title': 'Total saving', 'payload': 'c_saved'},
        ]
        pg.send(sender_id, "What do you want to know?", quick_replies=quick_replies)

@pg.callback(['charge_stat', 'l_saved', 'c_saved'])
def doer(payl, event):
    global macid
    global metricsData
    sender_id = event.sender_id
    pg.typing_on(sender_id)
    quick_replies = [
      {'title': 'Charging status', 'payload': 'charge_stat'},
      {'title': 'Last saved', 'payload': 'l_saved'},
      {'title': 'Total saving', 'payload': 'c_saved'},
    ]
    if payl == 'charge_stat':
        pg.send(sender_id, "Charging status: Charging", quick_replies=quick_replies)
    elif payl == 'l_saved':
        pg.send(sender_id, "Last savings: ₹ 131!", quick_replies=quick_replies)
    elif payl == 'c_saved':
        macid = db.query("select mac from user where fbid = %s" % sender_id)
        macid = macid[0].as_dict()["mac"]
        data = db.query('select * from client where mac = %s' % macid)
        row = data.as_dict()[::-1]
        # fav_rows = {}
        fav_rows = []
        maxi = 1
        start = 0
        total_hrs = list()
        for r in row:
            if (r['status'] == 0):
                maxi += 1
                if start == 0:
                    sTime = r['timestamp']
                    start += 1
                else:
                    eTime = r['timestamp']
                    # print eTime
            else:
                if r['strength']>96:
                    # fav_rows[maxi] = [sTime, eTime, r['strength']]
                    # fav_rows[maxi] = [sTime, eTime]
                    fav_rows.append(sTime - eTime)
                maxi = 0
                start = 0
        days = sum([x.days for x in fav_rows])
        fav_rows = sum([x.total_seconds()/60 for x in fav_rows])
        # total_hrs = sum(total_hrs)
        power = .5  # in watt
        price = 5  # per KWh
        energy = ((fav_rows*power)/1000)*days
        # print fav_rows, days
        pg.send(sender_id, "You've saved total %d KWh of energy so a total of"\
                            " %d ₹ of savings in last %d days!" % (energy, energy*price,\
                            days), quick_replies=quick_replies)
        metricsData["energy"] = energy
        metricsData["savings"] = energy*price
        metricsData["days"] = days

api.add_resource(deviceMetrics, '/device/metrics')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

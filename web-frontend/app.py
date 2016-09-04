#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import subprocess
import sqlite3
from datetime import datetime, timedelta
from flask import *
from evdev import ecodes as e

app = Flask(__name__)
app.secret_key = 'SDF%$^HDS$%dgsVbgjthew4E5yr%4E5'

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

e_codes = sorted([x for x in e.keys.values() if "KEY" in x])

# TABLES: status, schedule, settings
conn = sqlite3.connect("config.db", 
                       detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES, #use this to save datetime
                       check_same_thread=False)
# returned rows can be called with case-insensitive column names
conn.row_factory = sqlite3.Row
c = conn.cursor()

def reloadDaemon():
    subprocess.call(("systemctl", "reload", "gpioneer"))
                                     
                                        
@app.route('/')
def schedule_form():
    options = c.execute('SELECT * FROM gpioneer').fetchall()
    if getDaemonStatus():
        daemonValue = "stop"
        daemonOption = "Stop GPioneer"
    else:
        daemonValue = "start"
        daemonOption = "Start GPioneer"
    return render_template("index.html", daemonValue = daemonValue,
                                         daemonOption = daemonOption,
                                         options = options)

@app.route('/delete', methods=['POST'])
def schedule_delete():
    if 'id' in request.form:
        c.execute('DELETE FROM gpioneer WHERE id = (?)',request.form['id'])
        conn.commit()
        reloadDaemon()
    return redirect(url_for('schedule_form'))

@app.route('/edit', methods=['GET'])
def schedule_edit():
    id = request.args.get('id', '')
    if id and id != 'new':
        entry = c.execute('SELECT * FROM gpioneer WHERE id = {0}'.format(id)).fetchone()
    else:
        entry = { 'id': 'new',
                'name':'', 
                'command':'KEY_0',
                'pins':''
                }
    return render_template("edit_form.html", ecodes = e_codes,
                                             entry = entry)

@app.route('/edit', methods=['POST'])
def schedule_submit():
    entry = {
                'id': request.form.get('id', ''),
                'name': request.form.get('name', ''),
                'command': request.form.get('command', ''),
                'pins': request.form.get('pins', '')
            }
    
    found_errors = False
    
    try:
        # make sure comma separated list of numbers
        test = map(int, entry['pins'].split(','))
    except:
        flash("Only numbers can be assigned to pins. Use comma separation for pin combos (ex. 7, 9, 10)","danger")
        found_errors = True
    
    if found_errors:
        return render_template("edit_form.html", ecodes = e_codes,
                                                 entry = entry)
    
    # Update and redirect
    if entry['id'] == 'new' or entry['id'] == '':
        try:
            c.execute('INSERT INTO gpioneer \
                                (id, name, command, pins) VALUES (?,?,?,?)', 
                                (None, entry['name'], entry['command'], entry['pins'],))
            conn.commit()
            reloadDaemon()
            flash("Created new entry", "info")
        except:
            flash("Could not save new entry", "danger")
            
        return redirect(url_for('schedule_form'))
    else:
        try:
            c.execute('INSERT OR REPLACE INTO gpioneer \
                                (id, name, command, pins) VALUES (?,?,?,?)', 
                                (entry['id'], entry['name'], entry['command'], entry['pins'],))
            conn.commit()
            reloadDaemon()
            flash("Updated entry. Name: {0}, Pins: {1}".format(entry['name'], entry['pins']), "info")
        except:
            flash("Could not update entry", "danger")
        return redirect(url_for('schedule_form'))
 

    return render_template("edit_form.html", entry=entry)

def getDaemonStatus():
    try:
        return 'active' in subprocess.check_output(['systemctl', 'is-active', 'gpioneer'])
    except:
        return False
        
        
@app.route('/daemon_action', methods= ['POST'])
def setDaemonAction():
    action = request.form.get('daemonAction', 'start')
    subprocess.call(("systemctl", action, "gpioneer"))
    return redirect(url_for('schedule_form'))
    
@app.route('/web_action', methods= ['POST'])
def setWebAction():
    subprocess.call(("systemctl", "stop", "gpioneer-web"))
    return redirect(url_for('schedule_form'))


@app.route('/logs', methods= ['GET'])
def updateDaemonLogs():
    weekAgo = (datetime.now() + timedelta(days=-7)).date()
    raw = subprocess.check_output(['journalctl', '-u', 'gpioneer', '--since={0}'.format(weekAgo)])
    head = ('<head>' + 
                '<link href="/static/css/bootstrap.css" rel="stylesheet">' +
                '<link href="/static/css/main.css" rel="stylesheet">' +
            '</head>' + 
            '<body style="padding: 20px 10px;"><div class="container">' +
            '<h1 class="blue-letterpress">GPioneer Logs</h1><hr style="width:100%;">' +
            '<table class="table blue box-shadow table-striped table-bordered table-hover model-list">' +
                '<thead>' +
                    '<tr>' +
                        '<th>Date</th>' +
                        '<th>Message</th>' +
                    '</tr>' +
                '</thead>' +
                '<tbody>')
    html = ''
    rows = raw.split('\n')[1:]
    date = ''
    message = ''
    for row in rows:
        message += row[40:].lstrip(']:').replace('>','&gt;').replace('<', '&lt;') + '<br>'
        if date != row[:15]:
            date = row[:15]
            # do it this way to display in reverse order
            if date:
                html = '<tr><td>{date}</td><td><p>{message}</p></td></tr>'.format(date = date, message = message) + html
                message = ''
    html += '</tbody></table></div></body>'
    return head + html



@app.route('/_reloadConfig', methods = ['POST'])
def reloadDaemonConfig():
    reloadDaemon()
    return 'daemon has been reloaded'
    


if __name__ == "__main__":
    app.run("0.0.0.0", port=80, debug=True)
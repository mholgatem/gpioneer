from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, url_for, request
import yaml
import os
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
import sys
import subprocess


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'
app.config['SQLALCHEMY_BINDS'] = {
	'config':        'sqlite:///config.db',
	'games':      'sqlite:///games_master.db'
}


app.config['SECRET_KEY'] = 'jdhq7864r8uihblk'


db = SQLAlchemy(app)


class GPioneer(db.Model):
	__tablename__ = 'gpioneer'
	__bind_key__ = 'config'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text)
	command = db.Column(db.Text)
	pins = db.Column(db.Text)
	
	def __unicode__(self):
		return self.name

class CustomModelView(ModelView):
	edit_template = 'edit_admin.html'
	create_template = 'create_admin.html'
	list_template = 'list_admin.html'

class LocalRomsAdmin(CustomModelView):
	column_searchable_list = ('title')
	column_filters = ('title')


admin = Admin(app, 'GPioneer DB Interface', base_template='layout.html', template_mode='bootstrap2')
admin.add_view(CustomModelView(GPioneer, db.session))

	
@app.route("/", )
def index():
	name = "index"
	return redirect('/admin/gpioneer')
	return render_template('index.html', name=name)


if __name__ == '__main__':
	if 'DEBUG' in os.environ:
		app.debug = True
	app.debug = True
	
	
	if (not os.path.isfile('/etc/supervisor/conf.d/gunicorn.conf') and
		not os.path.isfile('/etc/supervisor/conf.d/pimame_menu.conf')):
			app.run(host="0.0.0.0", port=80)

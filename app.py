import os
from flask import Flask, render_template, request, redirect

import pandas as pd
import requests

from datetime import date
#import random
from jinja2 import Template
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
#from bokeh.util.browser import view
from bokeh.models import ColumnDataSource
#from bokeh.io import output_file, show

app = Flask(__name__)

app.vars={}

@app.route('/make_a_choice',methods=['GET','POST'])
def make_a_choice():
    if request.method=='GET':
        return render_template('stock_ticker_selection.html')
    else:
        # request was a POST
        app.vars['stock']=request.form['stock_ticker']
        app.vars['month']=request.form['month']
        # get stock price online
        r=requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+app.vars['stock']+'&apikey=FI9AYSSNHV9964Y7&datatype=csv&outputsize=full')
        filename=app.vars['stock']+'.csv'
        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
        # use pandas to process the data
        stock = pd.read_csv(filename)        
        stock['timestamp']=stock.timestamp.map(convert_date)
        y,m=app.vars['month'].split('.')
        startdate=date(int(y),int(m),1)
        if m=='12':
            enddate=date(int(y)+1,1,1)
        else:
            enddate=date(int(y),int(m)+1,1)
        st_month=stock[stock.timestamp >=startdate]
        st_month=st_month[st_month.timestamp < enddate ]
        st=st_month.set_index(['timestamp'])
        
        PLOT_OPTIONS = dict(plot_width=800, plot_height=300)
        
        source = ColumnDataSource(data=st)

        TOOLS="pan,wheel_zoom,box_zoom,reset"
        red = figure(sizing_mode='scale_width', tools=TOOLS, **PLOT_OPTIONS,x_axis_type='datetime')
        red.line(x='timestamp',y='close',source=source)

        template = Template("""\
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="utf-8">
                <title>Responsive plots</title>
                {{ resources }}
            </head>
            <body>
            <h2>Stock Closing Price </h2>
            <h3>Stock ticker - {{stock}}, Month: {{month}}</h3>
            {{ plot_div.red }}           
            {{ plot_script }}
            </body>
        </html>        
        """)
        
        resources = INLINE.render()
        script, div = components({'red': red})
        stock=app.vars['stock']
        month=app.vars['month']
        
        html = template.render(resources=resources,
                       plot_script=script,
                       plot_div=div,stock=stock,month=month)
        return html
         

def convert_date(val):
    y,m,d=val.split('-')
    return date(int(y),int(m),int(d))


if __name__ == '__main__':
    port=int(os.envron.get("PORT",5000))
    app.run(host='0.0.0.0', port=port)
#    app.run(port=33507)
#    app.run(debug=True)
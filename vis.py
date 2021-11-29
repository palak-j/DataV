import json
from flask import Flask, request, jsonify, render_template
import matplotlib.pyplot as plt
from jinja2 import Template
from bokeh.embed import json_item
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.layouts import gridplot
from bokeh.models import Slider, Range1d
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, CustomJS, TapTool
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from bokeh.layouts import row
from wordcloud import WordCloud
import numpy as np
import os
import pandas as pd
import io
import base64
from flask import Response
from matplotlib.figure import Figure
from PIL import Image
from collections import OrderedDict

print(os.getcwd())

data = pd.read_pickle("sample.p")

app = Flask(__name__)

landing_page = Template("""
<!DOCTYPE html>
<head>
  {{ resources }}
  <title>Example Visualization Web App</title>
  
  <style>
  
  img {
  object-fit: cover;
  display: block;
  margin-left: auto;
  margin-right: auto;
  
  }
  
  </style>
</head>
<body>
  <div id="visualization0" >
  
  <div class="img-container">     
    
     <img src="/visual0" width="1000" height="400" >
  </div>
  </div>

  <div id="visualization1">Visualization 1</div>
  <script>
    fetch('/visual1')
      .then(function(response) {return response.json();})
      .then(function(item) {return Bokeh.embed.embed_item(item);})
  </script>
  
  <div id="visualization2">Visualization 2</div>
  <script>
    fetch('/visual2')
      .then(function(response) {return response.json();})
      .then(function(item) {return Bokeh.embed.embed_item(item);})
  </script>
  
</body>
""")




#print(data)


region_count = data['region'].value_counts()

labels  = data['region'].unique()
counts = region_count.tolist()


freq = pd.DataFrame(columns = ['Region', 'Number_of_cars'])

for i in range(0, len(labels)):
    freq = freq.append({'Region' : labels[i], 'Number_of_cars' : counts[i]}, 
                ignore_index = True)
    #freq[labels[i]]= counts[i]

#freq = freq.sort_values(by=['Number_of_cars'], ascending=False)


# TOP 20 regions
freq = freq.head(20)             
print(freq)

data_20_regions = data[data['region'].isin(freq['Region'])]
data_20_regions = data_20_regions[data_20_regions['year']>2000]

year_region = dict.fromkeys(freq['Region'])
for reg in freq['Region']:
    year_freq = dict.fromkeys(data_20_regions['year'].unique())
    a = data[data['region'] == reg]
    for key in year_freq.keys():
        considered = a[a['year']== key]
        year_freq[key]=considered.shape[0]
    dict1 = OrderedDict(sorted(year_freq.items()))
    year_region[reg]= list(dict1.values())

freq['year_freq'] = year_region.values()

print(freq)


@app.route('/')
def home():
    
  return landing_page.render(resources=CDN.render())


@app.route('/visual0')
def produce_visual0():  
    
    text = ' '.join(data['manufacturer'].tolist())
    mask = np.array(Image.open('car.jpg'))
    wordcloud = WordCloud(width = 7000, height = 5000, random_state=1, prefer_horizontal=1,background_color='steelblue', contour_color='cornflowerblue', colormap='Set2', contour_width=4, collocations=True, mask=mask).generate(text)
    img = io.BytesIO()
    wordcloud.to_image().save(img, 'PNG')
    img.seek(0)
    
    return Response(img.getvalue(), mimetype='image/png')




@app.route('/visual1')
def produce_visual1():
    
  source_bars = ColumnDataSource({'x': np.array(freq['Region']), 'y': np.array(freq['Number_of_cars'])})
  lines_y = np.array(freq['year_freq'])
#source_lines = ColumnDataSource({'x': np.array(sorted(data_20_regions['year'].unique())), 'y': lines_y[0]})
  y_l = []
  for i in range(21):
    sum = 0
    for j in lines_y:
        sum+= j[i]
    y_l.append(sum)
  yrange = Range1d(1000, 2500)
  plot1 = figure(x_range=freq['Region'], y_range = yrange, tools = 'tap')
  bars = plot1.vbar(x = 'x', top = 'y', source = source_bars, bottom = 0, width = 0.5)

  plot1.xaxis.major_label_orientation = "vertical"

  plot2 = figure()
  lines = plot2.line(x = 'x', y = 'y', source = ColumnDataSource({'x': np.array(sorted(data_20_regions['year'].unique())), 'y': y_l}))
#lines = plot2.line(x = 'x', y = 'y', source = source_lines)
  lines.visible = True


  code = '''if (cb_data.source.selected.indices.length > 0){
            lines.visible = true;
            var selected_index = cb_data.source.selected.indices[0];
            lines.data_source.data['y'] = lines_y[selected_index]
            lines.data_source.change.emit(); 
          }'''


  plots = row(plot1, plot2)
  plot1.select(TapTool).callback = CustomJS(args = {'lines': lines, 'lines_y': lines_y}, code = code)   
  
  return json.dumps(json_item(plots, "visualization1"))

  

#df2 = data[data['region'].isin(freq['Region'].tolist() )]
#print(df2)

@app.route('/visual2')
def produce_visual2():
      
  source_bars = ColumnDataSource({'x': [1, 2, 3], 'y': [2, 4, 1] , 'colnames': ['A', 'B', 'C']})
  lines_y = [np.random.random(5) for i in range(3)]

  plot1 = figure(tools = 'tap', width=300, height=300)
  bars = plot1.vbar(x = 'x', top = 'y', source = source_bars, bottom = 0, width = 0.5)

  plot2 = figure(width=300, height=300)
  lines = plot2.line(x = 'x', y = 'y', source = ColumnDataSource({'x': np.arange(5), 'y': lines_y[0]}))
  lines.visible = False

  code = '''if (cb_data.source.selected.indices.length > 0){
            lines.visible = true;
            var selected_index = cb_data.source.selected.indices[0];
            lines.data_source.data['y'] = lines_y[selected_index]
            lines.data_source.change.emit(); 
          }'''

  plots = row(plot1, plot2)
  plot1.select(TapTool).callback = CustomJS(args = {'lines': lines, 'lines_y': lines_y}, code = code)
    
  
  return json.dumps(json_item(plots, "visualization2"))



if __name__ == "__main__":
    app.run(debug=True)




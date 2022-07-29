import dash
from dash import html, ctx
from dash import dcc 
from dash import dash_table
import plotly.graph_objects as go
import plotly.express as px
from dash import Input, Output, State
import numpy as np
import base64
import io
import pandas as pd

# PRV Libraries for analysing Pulse Rate Variability from E4 data.
from PRV import prv 

app = dash.Dash()
app.title = 'Empatica E4 PRV Application'

# Strings to be included in the template.
txt_introduction = """
Pulse Rate Variability(PRV) is similar to HRV, with the key difference being that is applied to P-P waveforms extracted from a PPG signal, rather than R-R waveforms from an ECG signal. This application makes use of the IBI (Inter-Beat Interval) file from the Empatica E4 to calculate various time domain (frequency domain coming soon) PRV metrics. 

### Note about PRV vs HRV 

 The similarity between HRV and PRV is still under debate, with some suggesting that PRV is a good surrogate marker for HRV, while others arguing otherwise. Unlike ECG which relies on measuring the electric activity, with the R peak corresponding directly to ventricular contraction, PPG measures the change in blood volume in the arteries. Yuda et.al. (Yuda et al., 2020) state that there are several factors that can affect the conversion from an ECG R wave to the PPG pulse wave, thus arguing that PRV must be treated as separate variable from HRV. Physiological factors such as Pre-ejection period, Aortic pressure elevation (stroke volume, intrathoracic pressure), Pulse conduction time (internal radius, wall thickness & elasticity, blood density), tissue volume (blood flow, venous pressure) must be taken into consideration. Finally, sensor sensitivity to light scattering and absorption based on pressure applied (Tamura et al., 2014), skin tone, red cellhemoglobin, light wavelength and motion can all affect the final value. 


However, Kumar et.al (Kiran kumar et al., 2021) recently showed a good co-relation between HRV and PRV for N=50 female participants aged between 18-25. They showed a positive co-relation of r=0.99 between mean R-R intervals (700 +/-81.34ms) and PRV (703.6 +/-86.28ms). Kumar et.al. also showed a strong co-relation for several derived metrics –SDNN (r=0.61), RMSSD (r=0.78), NN50 (r=0.79), pNN50 (r=0.92). 
"""

app.layout = html.Div([
        # Heading
        html.Div([
            html.Center([html.H1('Empatica E4 PRV (Pulse Rate Variability) Analysis')])
        ]),
        # File upload
        html.Div([
            dcc.Upload(
                id='upload-ibi',
                children=html.Div(['Drag and Drop or ',
                    html.A('Select'), ' a E4 IBI (Inter-Beat Interval) File']),
                style={
                    'width' : '100%',
                    'height' : '60px',
                    'lineHeight' : '60px',
                    'borderWidth' : '1px',
                    'borderStyle' : 'dashed',
                    'borderRadius' : '5px',
                    'textAlign' : 'center',
                    'margin' : '10px',
                    'border-color' : '#708090',
                    'background-color' : '#F5F5F5',
                },
                multiple=False  # Disable uploading multiple files.
            ),
            html.Center(html.Button('Or Try Our Sample Data', id='try-sample', n_clicks=0),
                    id='sample_data',
                    style={
                        'margin-top' : '20px',
                    }),
            # Holder for the callback output.
            html.Div(id='output-hrv'),

            # Holder for the introduction text.
            html.Div(dcc.Markdown(txt_introduction), className='content'),
        ])
    ])

# Method which renders the IBI waveform graph.
def plotIBI(time, data):
    # Calculate the instantaneous HR value so we can use that for mouse over.
    hr = np.zeros(data.size)
    for i, ibi in enumerate(data):
        hr[i] = np.round(60 / ibi, decimals=2)

    df = pd.DataFrame({'Time':time, 'IBI': data, 'Instant HR':hr})

    fig = px.scatter(df, x='Time', y='IBI', 
				labels={'Time':'Time since start of session (seconds)', 'IBI':'IBI'}, 
                color='Instant HR', hover_data=['Instant HR', 'IBI']) 

    return fig

# Method which renders the section for derived metrics.
def renderDerived(metric, title='', tag='', window_size=0):
    fig = px.scatter(metric, x='startTime', y='values', labels={
            'startTime':'Window start time(s). Window length = {}s'.format(window_size),
            'values':tag.upper()})

    div = html.Div([
            html.Hr(), 
            html.H2(title),
            dcc.Graph(figure=fig),
            html.Div(id='table-{}'.format(tag)),    # Place holder for the actual table data.
            #html.Button('Show raw {} values'.format(tag.upper()), id='show-more-button', value=tag),
            #dash_table.DataTable(metric.to_dict('records')),
        ])

    return div

# Method which processes the sample data file.
def processSampleData():
    children = []

    try:
        f = open('sample_data/IBI.csv','r')
        raw_data = pd.read_csv(f) 
        children = renderOutput(raw_data)
    except Exception as ex:
        print(ex)
        return html.Div(['There was internal problem processing your data.'])

    return children

# Method which parses the contents of the uploaded file.
def parse_contents(contents, filename, date):
    content_type, content_stirng = contents.split(',')

    # Decode base64 content string.
    decoded = base64.b64decode(content_stirng)
    
    # Children that will be used to populate the output div.
    children = []

    try:
        if 'csv' in content_type: 
            raw_data = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            children = renderOutput(raw_data)
        else:
            # Wrong file format has been uploaded. Let the user know.
            return html.Div(['Incorrect file type. Currently only supports IBI csv files.'])
    except Exception as ex:
        print(ex)
        return html.Div(['There was internal problem processing your data.'])

    return children

# Method which renders the output content.
def renderOutput(raw_data):
    children = []


    # Parse the IBI file uploaded.
    time = raw_data[raw_data.columns[0]].values
    data = raw_data[' IBI'].values

    # Plot the raw graph for IBI.
    children.append(
        html.Div([html.H2('Inter-Beat Interval Raw Plot'),
            dcc.Graph(figure=plotIBI(time, data))])
    )

    rmssd = prv.getRMSSD(time, data) 
    hrmaxmin = prv.getHRMaxMin(time, data) 
    nn50 = prv.getNN50(time, data) 
    pnn50 = prv.getPNN50(time, data) 
    sdnn = prv.getSDNN(time, data) 

    children.append(renderDerived(rmssd, 'RMSSD', 'rmssd', 60))
    children.append(renderDerived(hrmaxmin, '|MAX - MIN| HR', 'max - min hr', 120))
    children.append(renderDerived(nn50, 'NN50', 'nn50', 120))
    children.append(renderDerived(pnn50, 'pNN50', 'pnn50', 120))
    children.append(renderDerived(sdnn, 'SDNN', 'SDNN', 60))

    return children 

# App callback for file upload.
@app.callback(Output('output-hrv', 'children'),
                Input('upload-ibi', 'contents'),
                Input('try-sample', 'n_clicks'),
                State('upload-ibi', 'filename'),
                State('upload-ibi', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates, n_clicks):
    print(ctx.triggered_id)
    if ctx.triggered_id == 'upload-ibi':
        if list_of_contents is not None:
            return parse_contents(list_of_contents, list_of_names, list_of_dates)
    elif ctx.triggered_id == 'try-sample':
        return processSampleData()

if __name__ == '__main__':
    app.run_server(debug=True)

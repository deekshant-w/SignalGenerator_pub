from flask import Flask, request, render_template
from flask_cors import CORS
from pathlib import Path
import traceback
import warnings

from generator_prenormalized import main as signalGenerator
from generator_finitelength_opt import main as signalGenerator_fl
from misc import validate_and_sanitize_generate_signal_data
from sigalModifications import signalAttenuate, applyBessel, interpolate

# if .dkdev file exists, then it is in development mode
if Path(".dkdev").exists():
    print("\033[1;32;40mDevelopment Mode\033[0m", flush=True)
    app = Flask(__name__)
    CORS(app) # Only for development, remove this in production
else:
    app = Flask(
        __name__,
        static_url_path="/static"
    )

ROUTING_PARAM = '-_-at-_'

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.errorhandler(404)
def page_not_found(e):
    # https://stylishtextmaker.com/
    data = r"""<div><pre>
             ________________________________________________
            /                                                \
           |    _________________________________________     |
           |   |                                         |    |
           |   |  C:\> 404                               |    |
           |   |  Page Not Found▯                       |    |
           |   |                                         |    |
           |   |                                         |    |
           |   |                                         |    |
           |   |                                         |    |
           |   |                                         |    |
           |   |                                         |    |
           |   |                                         |    |
           |   |                                         |    |
           |   |                                         |    |
           |   |                                         |    |
           |   |_________________________________________|    |
           |                                                  |
            \_________________________________________________/
                   \___________________________________/
                ___________________________________________
             _-'    .-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  --- `-_
          _-'.-.-. .---.-.-.-.-.-.-.-.-.-.-.-.-.-.-.--.  .-.-.`-_
       _-'.-.-.-. .---.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-`__`. .-.-.-.`-_
    _-'.-.-.-.-. .-----.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-----. .-.-.-.-.`-_
 _-'.-.-.-.-.-. .---.-. .-------------------------. .-.---. .---.-.-.-.`-_
:-------------------------------------------------------------------------:
`---._.-------------------------------------------------------------._.---'
</pre></div>"""
    return data, 404

def getHandler(request):
    data = request.args
    print(f"Get Request: {data}")
    path = data.get(ROUTING_PARAM, "").lower().strip()
    return render_template('index.html')

def postHandler(request):
    data = request.get_json()
    if not isinstance(data, dict):
        return {"error": "Invalid JSON body."}, 400
    # print(data,flush=True)
    path = data.get(ROUTING_PARAM, "").lower().strip()
    if path == "ping":
        return {"ping": "ok"}
    elif path == "generate":
        print(f"Raw: {data}", flush=True)
        status, data = validate_and_sanitize_generate_signal_data(data)
        print(f"Cleaned Data: {status} {data}", flush=True)
        if status is False:
            return {"error": data}, 400
        assert isinstance(data, dict)
        if data['poreType'] == '2dPore':
            try:
                x,y = signalGenerator(data["components"], data["nanoporeRadius"], data["signalResolution"])
            except Exception as e:
                print(f"Error in 2dPore: {e}", flush=True)
                return {"error": str(e)}, 500
        else:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    x,y = signalGenerator_fl(data["components"], data["pore"], data["signalResolution"])
            except Exception as e:
                print(f"Error occurred in {data['poreType']}: {e.__traceback__.tb_frame.f_code.co_filename} at line: {e.__traceback__.tb_lineno}", flush=True)
                print(traceback.format_exc(), flush=True)
                # return {"error": str(e)}, 500
                return {"error": "Molecule structure and pore configuration combination is invalid."}, 500
        x = x.tolist()
        y = y.tolist()
        if len(x) != len(y) or len(x) == 0:
            print(f"Unable to generate signal. Signal length: {len(x)}, {len(y)}", flush=True)
            return {"error": f"Unable to generate signal. Signal length: {len(x)}, {len(y)}"}, 500
        return {"x": x, "y": y}
    elif path == "attenuate":
        y = data.get("y", None)
        sigma = data.get("sigma", None)
        transition_time = data.get("transition_time", None)
        sampling_rate = data.get("sampling_rate", None)
        cutoff_frequency = data.get("cutoff_frequency", None)
        filter_poles = data.get("filter_poles", None)
        x_max = data.get("x_max", None)
        args = ("y", "sigma", "transition_time", "sampling_rate", "cutoff_frequency", "filter_poles", "x_max")
        for arg_name in args:
            if locals()[arg_name] is None:
                return {"error": f"{arg_name} is invalid."}, 400
        
        y, x_new, x_old = interpolate(y,transition_time,sampling_rate,x_max)
        y = signalAttenuate(y, sigma)
        status, y = applyBessel(y,filter_poles,cutoff_frequency,sampling_rate)
        if not status:
            return {"error":y},400
        # y is numpy array here
        return {
            "y": y.tolist(),
            "x_new": x_new.tolist(),
            "x_old": x_old.tolist()
        }
    
    return {"post": "ok"}

# Routing Handler
@app.route("/", methods = ['GET', 'POST'])
def router():
    method = request.method
    if method == "GET":
        return getHandler(request)
    elif method == "POST":
        return postHandler(request)
    else:
        return "Wrong Method", 405

if __name__ == '__main__':
    app.run(debug=True if Path(".dkdev").exists() else False)
"""
An entry point to the backend of AirTrafficSim.

Attributes:

app : Flask()
    A flask server object.
socketio : SocketIO()
    A SocketIO object for communication.

"""

from pathlib import Path
from importlib import import_module
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
# import eventlet

from airtrafficsim.server.replay import Replay
from airtrafficsim.server.data import Data

# eventlet.monkey_patch()

frontend_path = Path(__file__).parent.parent.parent.parent.joinpath('out')

app = Flask(__name__, static_url_path='', static_folder=frontend_path, template_folder=frontend_path)
socketio = SocketIO(app, cors_allowed_origins='*', max_http_buffer_size=1e8,
                    ping_timeout=60, async_mode='eventlet')  # engineio_logger=True

running_environment = None

@socketio.on('connect')
def test_connect():
    """
    Debug function to test whether the client is connected.
    """
    print('Client connected')


@socketio.on('disconnect')
def test_disconnect():
    """
    Debug function to inform the client is disconnected.
    """
    print('Client disconnected')


@socketio.on('getReplayDir')
def get_replay_dir():
    """Get the list of directories in data/replay"""
    return Replay.get_replay_dir()


@socketio.on('getReplayCZML')
def get_replay_czml(replayCategory, replayFile):
    """
    Generate a CZML file to client for replaying data.

    Parameters
    ----------
    replayCategory : string
        The category to replay (historic / simulation)
    replayFile : string
        Name of the replay file directory

    Returns
    -------
    {}
        JSON dictionary of the CZML data file
    """
    return Replay.get_replay_czml(replayCategory, replayFile)


@socketio.on('getGraphHeader')
def get_graph_header(mode, replayCategory, replayFile):
    """
    Get the list of parameters name of a file suitable for plotting graph.

    Parameters
    ----------
    mode : string
        AirTrafficSim mode (replay / simulation)
    replayCategory : string
        The category to replay (historic / simulation)
    replayFile : string
        Name of the replay file directory

    Returns
    -------
    string[]
        List of graph headers
    """
    return Replay.get_graph_header(mode, replayCategory, replayFile)


@socketio.on('getGraphData')
def get_graph_data(mode, replayCategory, replayFile, simulationFile, graph):
    """
    Get the data for the selected parameters to plot a graph.

    Parameters
    ----------
    mode : string
        AirTrafficSim mode (replay / simulation)
    replayCategory : string
        The category to replay (historic / simulation)
    replayFile : string
        Name of the replay file directory

    Returns
    -------
    {}
        JSON file for graph data for Plotly.js
    """
    return Replay.get_graph_data(mode, replayCategory, replayFile, simulationFile, graph)


@socketio.on('getSimulationFile')
def get_simulation_file():
    """
    Get the list of files in airtrafficsim/env/

    Returns
    -------
    string[]
        List of simulation environment file names
    """
    simulation_list = []
    for file in sorted(Path(__file__).parent.parent.joinpath('data/environment/').glob('*.py')):
        if file.name != '__init__.py':
            simulation_list.append(file.name.removesuffix('.py'))
    return simulation_list


@socketio.on('runSimulation')
def run_simulation(file):
    """
    Start the simulation given file name.

    Parameters
    ----------
    file : string
        Environment file name
    """
    global running_environment
    print(file)
    if file == "ConvertHistoricDemo":
        socketio.emit('loadingMsg', 'Converting historic data to simulation data... <br> Please check the terminal for progress.')
    elif file == "WeatherDemo":
        socketio.emit('loadingMsg', 'Downloading weather data... <br> Please check the terminal for progress.')
    else:
        socketio.emit('loadingMsg', 'Running simulation... <br> Please check the terminal for progress.')
    socketio.sleep(0)
    Env = getattr(import_module('airtrafficsim.data.environment.' + file, '...'), file)
    env = Env()

    if running_environment is not None:
        running_environment.stop()
    running_environment = env

    env.run(socketio)


@socketio.on('getNav')
def get_Nav(lat1, long1, lat2, long2):
    """
    Get the navigation waypoint data given

    Parameters
    ----------
    lat1 : float
        Latitude (South)
    long1 : float
        Longitude (West)
    lat2 : float
        Latitude (North)
    long2 : float
        Longitude (East)

    Returns
    -------
    {}
        JSON CZML file of navigation waypoint data
    """
    return Data.get_nav(lat1, long1, lat2, long2)


@socketio.on('getEra5Wind')
def get_era5_wind(lat1, long1, lat2, long2, file, time):
    """
    Get the ERA5 wind data image to client

    Parameters
    ----------
    lat1 : float
        Latitude (South)
    long1 : float
        Longitude (West)
    lat2 : float
        Latitude (North)
    long2 : float
        Longitude (East)

    Returns
    -------
    {}
        JSON CZML file of ERA5 wind data image
    """
    return Data.get_era5_wind(file, lat1, long1, lat2, long2, time)


@socketio.on('getEra5Rain')
def get_era5_rain(lat1, long1, lat2, long2, file, time):
    """
    Get the ERA5 rain data image to client

    Parameters
    ----------
    lat1 : float
        Latitude (South)
    long1 : float
        Longitude (West)
    lat2 : float
        Latitude (North)
    long2 : float
        Longitude (East)

    Returns
    -------
    {}
        JSON CZML file of ERA5 rain data image
    """
    return Data.get_era5_rain(file, lat1, long1, lat2, long2, time)


@socketio.on('getRadarImage')
def get_radar_img(lat1, long1, lat2, long2, file, time):
    """
    Get the radar data image to client

    Parameters
    ----------
    lat1 : float
        Latitude (South)
    long1 : float
        Longitude (West)
    lat2 : float
        Latitude (North)
    long2 : float
        Longitude (East)
    time : string
        Time in ISO format
    file : string
        File name of the radar image

    Returns
    -------
    {}
        JSON CZML file of radar data image
    """
    return Data.get_radar_img(file, lat1, long1, lat2, long2, time)


@socketio.on('webrtc')
def webrtc(data):
    """Send webrtc data to client"""
    emit('webrtc', data, broadcast=True, include_self=False)


@app.route("/")
def serve_client():
    """Serve client folder to user"""
    return render_template("index.html")


def run_server(port=6111, host="0.0.0.0"):
    # Change host to 0.0.0.0 during deployment
    """Start the backend server."""
    print("Running server at http://localhost:"+str(port))
    socketio.run(app, port=port, host=host, certfile=Path(__file__).parent.parent.parent.parent.resolve().joinpath('certificates/localhost.pem'), keyfile=Path(__file__).parent.parent.parent.parent.resolve().joinpath('certificates/localhost-key.pem'))

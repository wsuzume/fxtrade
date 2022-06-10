import numpy as np
import plotly.graph_objects as go

from .fx import FX

def summarize(fx: FX):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['low'].apply(np.log10), name="low"))
    fig.show()
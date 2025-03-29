import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def pseudo(s, t, dt):
    index = np.arange(s, t, dt)
    columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'other1', 'other2']
    
    df = pd.DataFrame(index=index, columns=columns)
    df['timestamp'] = [ int(t.timestamp()) for t in df.index ]
    
    df[['open', 'high', 'low', 'close']] = np.random.normal(3700000, 100000, (len(index), 4))
    df[['volume', 'other1', 'other2']] = np.random.normal(30, 10, (len(index), 3))
    
    arr = np.array(df.index)
    np.random.shuffle(arr)
    
    return df.loc[arr].copy()
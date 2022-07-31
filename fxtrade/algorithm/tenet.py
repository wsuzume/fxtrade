import math
import plotly.graph_objects as go

from datetime import datetime
from fractions import Fraction

from ..fx import FX
from ..analysis import analyze, estimate_probability, geomeans
from ..stock import Rate
from ..trade import Trade

def calc_zpc(xs, dt, alphas=None):
    if alphas is None:
        alphas = np.linspace(0.1, 1, 91)
    zs = []
    ps = []
    cs = []
    for a in alphas:
        gmeans = geomeans(xs, alpha=a, dt=dt)

        zs.append(infinite_trade_result(xs, gmeans))
        ps.append(over_under_ratio(xs, gmeans))
        cs.append(straddle_count(xs, gmeans))

    zs = np.array(zs)
    ps = np.array(ps)
    cs = np.array(cs)
    
    zpc = pd.DataFrame([alphas, zs, ps, cs, zs * ps, zs * ps / cs]).T
    zpc.columns = ['alpha', 'z', 'p', 'c', 'zp', 'zp/c']
    
    return zpc

def calc_best_alpha(xs, dt, alphas=None):
    zpc = calc_zpc(xs, dt, alphas=None)
    zpc_sorted = zpc[(zpc['p'] > 0.9) & (zpc['p'] < 1.4)].sort_values('zp', ascending=False)

    return zpc_sorted.iloc[0]
    
class Tenet:
    def __init__(self, crange_interval, dt, window=3, alpha=0.87):
        self.crange_interval = crange_interval
        self.dt = dt
        self.window = window
        self.alpha = alpha
        
        self.df_low = None
        self.df_high = None
        self.gmeans = None
        self.rise = None
        self.fall = None
        
    def analyze(self, fx: FX, t=None):
        df = analyze(fx.chart[self.crange_interval]['low'])
        df_high = analyze(fx.chart[self.crange_interval]['high'])
        
        dif = df['diff'].rolling(self.window).sum()
        prob = estimate_probability(df['diff'], self.window)
        
        rise = prob[(dif > 0) & (prob < 0.4)]
        fall = prob[(dif < 0) & (prob < 0.2)]
        
        gmeans = geomeans(df['log'], alpha=self.alpha, dt=self.dt)
        trend = geomeans(gmeans.diff(), alpha=self.alpha, dt=self.dt)
        
        gm = gmeans.loc[trend.index]
        uptrend = gm.loc[(((trend > 0).astype(float)).diff() > 0).values]
        downtrend = gm.loc[(((trend > 0).astype(float)).diff() < 0).values]
        
        self.df_low = df
        self.df_high = df_high
        self.gmeans = gmeans
        self.rise = rise
        self.fall = fall
        
        self.trend = trend
        self.uptrend = uptrend
        self.downtrend = downtrend
        
        return df
    
    def decide_to_buy(self, fx):
        last_trade = fx.get_last_trade()
        
        if last_trade.x.code == 'JPY':
            # last trade was BUY
            best_bid = 1 / fx.trader.get_best_bid()
            
            return Trade.from_stock_and_rate(last_trade.x, best_bid).yfloor()
        
        # last trade was SELL
        trade = fx.get_max_available()
        return trade % 4
        
    
    def decide_to_sell(self, fx):
        return fx.get_max_salable()
        
    def __call__(self, fx: FX, t=None):
        self.analyze(fx, t)
        
        now = self.df_low.index[-1]
        print('now:', now)
        
        is_rising = self.rise.index[-1] == now
        is_falling = self.fall.index[-1] == now
        
        is_after_falling = self.fall.index[-1] > self.rise.index[-1]
        is_after_rising = self.rise.index[-1] > self.fall.index[-1]
        
        is_uptrend = self.uptrend.index[-1] > self.downtrend.index[-1]
        is_downtrend = self.uptrend.index[-1] < self.downtrend.index[-1]
        
        is_over_gmeans = self.gmeans.iloc[-1] < self.df_low['log'].iloc[-1]
        is_under_gmeans = self.gmeans.iloc[-1] > self.df_low['log'].iloc[-1]
        
        ### 買い時
        # アップトレンドかつ平均より下かつ暴落ではない
        # アップトレンドかつ暴騰中（大きく張る）
        # アップトレンドかつ暴落終了直後
        # ダウントレンドかつ暴落終了後の暴騰（大きく張る）

        ### 売り時
        # 暴騰終了直後
        # 暴落開始
        
        if is_uptrend:
            if is_under_gmeans and (not is_falling):
                print('uptrend: under: not falling: buy some')
                return self.decide_to_buy(fx)
            elif is_rising:
                print('uptrend: rinsing: buy more')
                return self.decide_to_buy(fx)
            elif is_after_falling:
                print('uptrend: after falling: buy more')
                return self.decide_to_buy(fx)
            elif (not is_rising) and is_after_rising:
                print('uptrend: rising end: sell all')
                return self.decide_to_sell(fx)
        elif is_downtrend:
            if is_rising:
                print('downtrend: rising: buy more')
                return self.decide_to_buy(fx)
            else:
                print('downtrend: sell all')
                return self.decide_to_sell(fx)

        if is_falling:
            print('falling: sell all')
            return self.decide_to_sell(fx)
        
        return None
    
    def plot(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.df_high.index, y=self.df_high['log'],
                            mode='lines',
                            line=dict(color='#87cefa'),
                            opacity=0.5,
                            name="high"))
        fig.add_trace(go.Scatter(x=self.df_low.index, y=self.df_low['log'],
                            mode='lines+markers',
                            line=dict(color='#87cefa'),
                            name="low"))
        
        fig.add_trace(go.Scatter(x=self.gmeans.index, y=self.gmeans.values,
                            mode='lines',
                            line=dict(color='#FF9900'),
                            name="gmeans"))
        
        fig.add_trace(go.Scatter(x=self.rise.index, y=self.df_low['log'].loc[self.rise.index],
                            mode='markers',
                            marker=dict(color='#109618'),
                            name="rise"))
        
        fig.add_trace(go.Scatter(x=self.fall.index, y=self.df_low['log'].loc[self.fall.index],
                            mode='markers',
                            marker=dict(color='#DC3912'),
                            name="fall"))
        
        fig.add_trace(go.Scatter(x=self.uptrend.index, y=self.uptrend.values,
                            mode='markers',
                            marker=dict(color='#FF9900',
                                        symbol='triangle-up',
                                        size=15,
                                        line=dict(color='#B68100',
                                                  width=2)),
                            name="up"))
        
        fig.add_trace(go.Scatter(x=self.downtrend.index, y=self.downtrend.values,
                            mode='markers',
                            marker=dict(color='#FF9900',
                                        symbol='triangle-down',
                                        size=15,
                                        line=dict(color='#B68100',
                                                  width=2)),
                            name="down"))
        
        
        #fig.update_xaxes(title="datetime") # X軸タイトルを指定
        fig.update_yaxes(title="log(rate)") # Y軸タイトルを指定

        #fig.update_xaxes(rangeslider={"visible":True}) # X軸に range slider を表示（下図参照）

        fig.update_layout(title="Chart") # グラフタイトルを設定
        #fig.update_layout(font={"family":"Meiryo", "size":20}) # フォントファミリとフォントサイズを指定
        fig.update_layout(showlegend=True) # 凡例を強制的に表示（デフォルトでは複数系列あると表示）
        fig.update_layout(width=800, height=600) # 図の高さを幅を指定
        fig.show()
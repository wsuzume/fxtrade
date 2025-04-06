import pandas as pd
from datetime import datetime
from dateutil import parser

######## utils for saving exec_list
import uuid


def assign_unique_name_to_executions(
    exec_list: list, dt: datetime, fstring: str = "%Y%m%d-%H%M%S-%f"
):
    xs = sorted(exec_list, key=lambda x: x["id"])

    min_id = xs[0]["id"]
    max_id = xs[-1]["id"]

    min_date = parser.isoparse(xs[0]["exec_date"])
    max_date = parser.isoparse(xs[-1]["exec_date"])

    return "_".join(
        [
            f"{min_id}",
            f"{max_id}",
            f"{min_date.strftime(fstring)}",
            f"{max_date.strftime(fstring)}",
            f"{dt.strftime(fstring)}",
            str(uuid.uuid4()),
        ]
    )


######## utils for analyze trades


def trade_split(df: pd.DataFrame):
    """
    BUY, SELL とそれ以外に分ける。

    Example
    =======
    ```
    jpy_hists = BalanceHistory.get_backward(
        api_key=api_key,
        api_secret=api_secret,
        currency_code="JPY",
        count=100,
        max_iter=5,
    )
    df_jpy = pd.DataFrame([hist.model_dump() for hist in jpy_hists])

    df_x, df_v = trade_split(df_jpy)
    ```
    """
    idx = df["trade_type"].isin({"BUY", "SELL"})
    return df[idx], df[~idx]


def trade_merge(df_x: pd.DataFrame, df_y: pd.DataFrame):
    """
    日本円と暗号通貨の取引記録をマッチさせる。

    Example
    =======

    ```
    # 直近500件のデータを取得
    jpy_hists = BalanceHistory.get_backward(
        api_key=api_key,
        api_secret=api_secret,
        currency_code="JPY",
        count=100,
        max_iter=5,
    )
    btc_hists = BalanceHistory.get_backward(
        api_key=api_key,
        api_secret=api_secret,
        currency_code="BTC",
        count=100,
        max_iter=5,
    )

    # データフレームに変換
    df_jpy = pd.DataFrame([hist.model_dump() for hist in jpy_hists])
    df_btc = pd.DataFrame([hist.model_dump() for hist in btc_hists])

    # マージ
    df, df_other = trade_merge(
        df_x=df_jpy[df_jpy["trade_date"] >= datetime(2025, 1, 1)],
        df_y=df_btc[df_btc["trade_date"] >= datetime(2025, 1, 1)],
    )
    ```
    """

    df_x, df_v = trade_split(df_x)
    df_y, df_w = trade_split(df_y)

    y_columns = [
        "id",
        "currency_code",
        "price",
        "amount",
        "quantity",
        "commission",
        "balance",
    ]

    df = pd.merge(df_x, df_y[y_columns], on="id", how="inner")

    if len(df) != len(df_x) or len(df) != len(df_y):
        raise ValueError(
            "df_x and df_y must have matching trades by ID, excluding DEPOSIT, WITHDRAW, and FEE"
        )

    df_other = pd.concat([df_v, df_w], axis=0)

    return df, df_other


def calc_price(df):
    """
    手元にある暗号通貨の価格を求める。求め方はいろいろあり、どの買い取引とどの売り取引をマッチさせるかで
    いま手元にある暗号通貨の価格は変わる（損益を含みのまま残すか確定させるか）。
    過去すべての取引（DEPOSITやWITHDRAWなども）を見れば含み益を最大化するか最小化するかで
    正確に価格を求めることができるが、取引回数が増えたときに求めるのが面倒になる。
    この計算方法では簡易的に手元にある暗号通貨に対して新しい順にマッチさせる。
    """
    # 最新順にマッチさせる
    df = df.sort_values("trade_date", ascending=False)

    df_buy = df[df["trade_type"] == "BUY"]
    df_sell = df[df["trade_type"] == "SELL"]

    # いま保有している暗号通貨の量
    M = Fraction(df.iloc[0]["balance_y"])

    rows = []
    for idx, row in df_buy.iterrows():
        # 手数料が負の値で記載されているので取引量に加えて手元に残る量を計算する
        m = Fraction(row["quantity_y"]) + Fraction(row["commission_y"])
        # 日本円の取引金額を手元に残った暗号通貨の量で割る
        p = abs(Fraction(row["amount_x"])) / m

        xs = {
            "id": row["id"],
            "trade_date": row["trade_date"],
            "currency_code": row["currency_code_y"],
            "price": p,
        }

        if M > m:
            M -= m
            xs["amount"] = m
            rows.append(xs)
        else:
            xs["amount"] = M
            rows.append(xs)
            break

    return pd.DataFrame(rows)


def calc_balance_transition(df):
    """
    手持ち資産の推移を計算する。trade_merge でマージした df を引数に与える。
    """
    transition = df["balance_x"].apply(int) + df["balance_y"].apply(Fraction).multiply(
        df["price_x"].apply(int)
    )

    df_transition = df[["trade_date"]].copy()
    df_transition["transition"] = transition

    return df_transition

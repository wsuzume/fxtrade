######## get_executions utils
import time
import datetime


def get_min_id_from_exec_list(xs: list):
    return min([x["id"] for x in xs])


def get_max_id_from_exec_list(xs: list):
    return max([x["id"] for x in xs])


def get_executions_backward(
    product_code: str = "btc_jpy",
    count: int | str = None,
    before: int | str = None,
    after: int | str = None,
    max_iter: int = 500,
) -> list:
    min_id = after
    max_id = before

    ret = []
    for _ in range(max_iter):
        response = get_executions(
            product_code=product_code, count=count, before=max_id, after=min_id
        )

        if response.status_code != requests.codes.ok:
            # 通信エラーや取得できる範囲を超えて取得した場合
            break

        exec_list = response.json()

        if len(exec_list) == 0:
            # before < after の関係になったなど、
            # 条件に一致する取引が存在しなくなった
            break

        # 取得したうちの最小の id が、次の最大の id となる。
        max_id = get_min_id_from_exec_list(exec_list)

        ret.append(response)

        # rate limit は 0.6 秒くらいなので
        # 安全マージンを入れて 1 秒
        time.sleep(1)

    return ret


def flatten_response_list(response_list):
    ret = []
    for resp in response_list:
        ret.extend(resp.json())
    return ret


def sort_exec_list_by_id(exec_list, reverse: bool = False):
    """
    id をキーとしてソートする関数

    :param data: ソート対象の辞書リスト
    :return: id の昇順でソートされたリスト
    """
    return sorted(exec_list, key=lambda x: x["id"], reverse=reverse)


def parse_exec_date(exec_date: str) -> datetime:
    if "." in exec_date:
        # 2024-03-10T09:19:13.68
        dt = datetime.strptime(exec_date, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        # 2024-03-10T09:19:13
        dt = datetime.strptime(exec_date, "%Y-%m-%dT%H:%M:%S")
    return dt


def convert_exec_list_to_table(exec_list: list):
    table = {}
    for exec in exec_list:
        dt = parse_exec_date(exec["exec_date"])
        key = dt.strftime("%Y-%m-%dT%H")
        if key not in table:
            table[key] = []
        table[key].append(exec)
    return table


def get_executions_as_table(
    product_code: str = "btc_jpy",
    count: int | str = None,
    before: int | str = None,
    after: int | str = None,
    max_iter: int = 500,
):
    response_list = get_executions_backward(
        product_code=product_code,
        count=count,
        before=before,
        after=after,
        max_iter=max_iter,
    )

    exec_table = convert_exec_list_to_table(
        sort_exec_list_by_id(
            flatten_response_list(response_list),
            reverse=False,
        )
    )

    return exec_table


######## utils for saving exec_list
import json
import gzip
import uuid
from pathlib import Path


def assign_unique_name_to_exec_list(
    exec_list: list, dt: datetime, fstring: str = "%Y%m%d-%H%M%S-%f"
):
    xs = sort_exec_list_by_id(exec_list, reverse=False)

    min_id = xs[0]["id"]
    max_id = xs[-1]["id"]

    min_date = parse_exec_date(xs[0]["exec_date"])
    max_date = parse_exec_date(xs[-1]["exec_date"])

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


def save_exec_list(exec_list: list, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(path, "wb") as f:
        f.write(json.dumps(exec_list).encode("utf_8"))

    return path


########
import requests

from datetime import datetime
from pathlib import Path
from typing import Callable
# from tqdm.auto import tqdm


def parse_event_date(event_date: str) -> datetime:
    if "." in event_date:
        # 2024-03-10T09:19:13.68
        dt = datetime.strptime(event_date, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        # 2024-03-10T09:19:13
        dt = datetime.strptime(event_date, "%Y-%m-%dT%H:%M:%S")
    return dt


def split_event_list(xs: list) -> dict[str, list]:
    table = {}
    for x in xs:
        day = x["event_date"].split("T")[0]
        if day not in table:
            table[day] = [x]
        else:
            table[day].append(x)
    return table


def sort_event_list_by_id(event_list: list) -> list:
    return sorted(event_list, reverse=True, key=lambda x: x["id"])


def parse_event_date(event_date: str) -> datetime:
    if "." in event_date:
        # 2024-03-10T09:19:13.68
        dt = datetime.strptime(event_date, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        # 2024-03-10T09:19:13
        dt = datetime.strptime(event_date, "%Y-%m-%dT%H:%M:%S")
    return dt


def get_event_log_name(
    event_list: list, dt: datetime, fstring: str = "%Y%m%d-%H%M%S-%f"
) -> str:
    xs = sort_event_list_by_id(event_list)

    max_id = xs[0]["id"]
    min_id = xs[-1]["id"]

    max_date = parse_event_date(xs[0]["event_date"])
    min_date = parse_event_date(xs[-1]["event_date"])

    return "_".join(
        [
            f"{max_date.strftime(fstring)}",
            f"{min_date.strftime(fstring)}",
            f"{max_id}",
            f"{min_id}",
            f"{dt.strftime(fstring)}",
            str(uuid.uuid4()),
        ]
    )


def get_min_id_from_event_list(xs: list):
    return min([x["id"] for x in xs])


########
# import pandas as pd
from datetime import datetime


def get_exec_log_name(
    exec_list: list, dt: datetime, fstring: str = "%Y%m%d-%H%M%S-%f"
) -> str:
    xs = sort_exec_list_by_id(exec_list)

    max_id = xs[0]["id"]
    min_id = xs[-1]["id"]

    max_date = parse_exec_date(xs[0]["exec_date"])
    min_date = parse_exec_date(xs[-1]["exec_date"])

    return "_".join(
        [
            f"{max_date.strftime(fstring)}",
            f"{min_date.strftime(fstring)}",
            f"{max_id}",
            f"{min_id}",
            f"{dt.strftime(fstring)}",
            str(uuid.uuid4()),
        ]
    )


def exec_item_to_list(x: dict):
    return [
        str(x[key])
        for key in [
            "id",
            "side",
            "price",
            "size",
            "exec_date",
            "buy_child_order_acceptance_id",
            "sell_child_order_acceptance_id",
        ]
    ]


# def get_exec_table(exec_list: list) -> pd.DataFrame:
#     return pd.DataFrame([ exec_item_to_list(x) for x in exec_list ])


def is_id_in_exec_list(xs: list, id: int):
    return int(id) in {x["id"] for x in xs}


def get_exec_list_after(xs: list, id: int):
    ret = []
    for x in xs:
        if int(x["id"]) <= id:
            break
        ret.append(x)
    return ret


def split_exec_list(xs: list) -> dict[str, list]:
    table = {}
    for x in xs:
        day = x["exec_date"].split("T")[0]
        if day not in table:
            table[day] = [x]
        else:
            table[day].append(x)
    return table


from datetime import datetime
from pathlib import Path
# from tqdm.auto import tqdm


class Executions:
    def __init__(
        self,
        root_dir: Path,
        glob: str = "**/*.json.gz",
        ignore: Callable[[Path], bool] = "default",
    ):
        self.root_dir = Path(root_dir)
        self._glob = glob

        ignore_set = {"__pycache__", ".ipynb_checkpoints"}

        if ignore is None:
            self.ignore = lambda x: False
        elif ignore == "default":
            self.ignore = lambda x: (len(set(x.parts) & ignore_set)) != 0
        elif isinstance(ignore, set):
            ignore_set |= ignore
            self.ignore = lambda x: (len(set(x.parts) & ignore_set)) != 0
        elif isinstance(ignore, Callable):
            self.ignore = ignore
        else:
            raise TypeError(
                "ignore must be one of (None, 'default', set[str], Callable[[Path], bool])."
            )

    def glob(self):
        return sorted(
            [path for path in self.root_dir.glob(self._glob) if not self.ignore(path)]
        )

    @property
    def min_id(self):
        min_ids = [int(path.stem.split("_")[3]) for path in self.glob()]
        if len(min_ids) == 0:
            return None
        return min(min_ids)

    @property
    def max_id(self):
        max_ids = [int(path.stem.split("_")[2]) for path in self.glob()]
        if len(max_ids) == 0:
            return None
        return max(max_ids)

    def save(self, exec_list: list, dt: datetime = None) -> list[Path]:
        if len(exec_list) == 0:
            return []

        if dt is None:
            dt = datetime.now()

        exec_dict = split_exec_list(xs=exec_list)

        paths = []
        for _date, _xs in exec_dict.items():
            xs = sort_exec_list_by_id(_xs)
            name = get_exec_log_name(xs, dt)

            date = datetime.strptime(_date, "%Y-%m-%d")
            save_dir = (
                self.root_dir
                / date.strftime("%Y")
                / date.strftime("%Y-%m")
                / date.strftime("%Y-%m-%d")
            )
            path = (save_dir / name).with_suffix(".json.gz")

            save_dir.mkdir(parents=True, exist_ok=True)

            with gzip.open(path, "wb") as f:
                f.write(json.dumps(xs).encode("utf_8"))

            paths.append(path)

        return paths

    def read(self, path: Path):
        path = Path(path)

        with gzip.open(path, "rb") as f:
            xs = f.read()

        return json.loads(xs.decode("utf-8"))

    def get_executions(
        self,
        mode: str = "forward",
        max_iter: int = 1000,
        before: int = None,
        after: int = None,
    ):
        if mode not in {"forward", "backward"}:
            raise ValueError("Undefined mode.")

        # １回目の取得設定
        if mode == "backward":
            before = before if before is not None else self.min_id
            after = after
        elif mode == "forward":
            before = before
            after = after if after is not None else self.max_id

        ret = []
        for _ in tqdm(range(max_iter)):
            now = datetime.now()

            resp = get_executions(count=500, before=before, after=after)

            if resp.status_code != requests.codes.ok:
                print(f"Error: {resp.status_code}")
                print(resp.content.decode("utf-8"))
                break

            xs = resp.json()
            paths = self.save(xs, now)

            if len(paths) == 0:
                print("All available executions have been retrieved.")
                break

            ret.extend(paths)

            # ２回目以降の取得設定
            # get_executions の挙動的に遡る方向（backward）でしか取得できないので、
            # backward, forward 問わず before のみ更新する
            before = get_min_id_from_exec_list(xs)

            # rate limit は 0.6 秒くらいなので
            # 安全マージンを入れて 1 秒
            time.sleep(1)

        return ret


# # def order_cancel(self):
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = "/v1/me/cancelchildorder"

# #     body = {
# #         "product_code": 'btc_jpy',
# #         "child_order_acceptance_id": "JRF20150707-033333-099999"
# #     }

# #     body = json.dumps(body)
# #     headers = self.header('POST', endpoint=endpoint, body=body)

# #     response = requests.post(base_url + endpoint, data=body, headers=headers)
# #     return response.status_code

# # def all_order_cancel():
# #     base_url = 'https://api.bitflyer.com'
# #     endpoint = "/v1/me/cancelallchildorders"

# #     body = {
# #         "product_code": 'btc_jpy'
# #     }

# #     body = json.dumps(body)
# #     headers = self.header('POST', endpoint=endpoint, body=body)

# #     response = requests.post(base_url + endpoint, data=body, headers=headers)
# #     return response.status_code

# def cashflow_to_history(df):
#     normalized_column = ['t', 'id', 'from', 'X(t)', 'to', 'Y(t+dt)', 'R(yt/xt)']

#     df = df.dropna(subset='product_code')

#     df_buy = df[df['trade_type'] == 'BUY']
#     df_sell = df[df['trade_type'] == 'SELL']

#     df_other = df[~df['trade_type'].isin({'BUY', 'SELL'})]

#     buy_his = df_buy[['trade_date', 'id', 'code_x', 'X(t)', 'code_y', 'Y(t+dt)']].copy()
#     buy_his['R(yt/xt)'] = buy_his['Y(t+dt)'] / buy_his['X(t)']
#     buy_his.columns = normalized_column

#     sell_his = df_sell[['trade_date', 'id', 'code_y', 'Y(t)', 'code_x', 'X(t+dt)']].copy()
#     sell_his['R(yt/xt)'] = sell_his['X(t+dt)'] / sell_his['Y(t)']
#     sell_his.columns = normalized_column

#     other_his = df_other[['trade_date', 'id', 'code_x', 'X(t)', 'code_x', 'X(t+dt)']].copy()
#     other_his['R(yt/xt)'] = 0
#     other_his.columns = normalized_column

#     ret = pd.concat([buy_his, sell_his, other_his], axis=0).sort_values('t', ascending=True).reset_index(drop=True)

#     return History(ret)

# class BitflyerAPI(TraderAPI):
#     @staticmethod
#     def make_code_pair_string(base: Union[str, CodePair], quote: Optional[str]=None) -> str:
#         if isinstance(base, str):
#             return f"{base.upper()}_{quote.upper()}"
#         elif isinstance(base, CodePair):
#             return f"{base.base.upper()}_{base.quote.upper()}"
#         raise TypeError("unrecognized type arguments")

#     def __init__(self, api_key, api_secret):
#         self._api_key = api_key
#         self._api_secret = api_secret

#     @property
#     def api_key(self):
#         return self._api_key

#     @property
#     def api_secret(self):
#         return self._api_secret

#     def __repr__(self):
#         if self.api_key == '[frozen]' and self.api_secret == '[frozen]':
#             return f"BitflyerAPI(api_key='{self.api_key}', " + \
#                 f"api_secret='{self.api_secret}')"
#         return f"BitflyerAPI(api_key='{self.api_key[:4]}...', " + \
#             f"api_secret='{self.api_secret[:4]}...')"

#     def freeze(self):
#         return BitflyerAPI(api_key='[frozen]', api_secret='[frozen]')

#     def minimum_order_quantity(self, code_pair, t=None):
#         code = code_pair.base

#         qs = {
#             'BTC': BTC('0.001')
#         }
#         return qs[code]

#     def maximum_order_quantity(self, code_pair, t=None):
#         code = code_pair.base

#         qs = {
#             'BTC': BTC('1000')
#         }
#         return qs[code]

#     def get_commission(self, code_pair):
#         product_code = self.make_code_pair_string(code_pair)

#         try:
#             response = get_commission(self.api_key, self.api_secret, product_code)
#             response.raise_for_status()
#         except RequestException as e:
#             print(e)
#             response = None

#         resp = response.json()

#         return Fraction(str(resp['commission_rate']))

#     def get_ticker(self, code_pair, t=None):
#         product_code = self.make_code_pair_string(code_pair)

#         try:
#             response = get_ticker(product_code=product_code)
#             response.raise_for_status()
#         except RequestException as e:
#             print(e)
#             response = None

#         return response.json()

#     def get_best_bid(self, code_pair, t=None):
#         ticker = self.get_ticker(code_pair, t=t)

#         # 買い値
#         bid_rate = Rate(from_code='BTC', to_code='JPY', r=str(ticker['best_bid']))

#         return bid_rate

#     def get_best_ask(self, code_pair, t=None):
#         ticker = self.get_ticker(code_pair, t=t)

#         # 売り値
#         ask_rate = Rate(from_code='BTC', to_code='JPY', r=str(ticker['best_ask']))

#         return ask_rate

#     def buy(self, size, t=None, wallet=None, history=None):
#         try:
#             response = order(self.api_key, self.api_secret, 'BUY', 'MARKET', 0, size)
#             response.raise_for_status()
#         except RequestException as e:
#             print(e)
#             print(response)
#             response = None

#         return response.json()

#     def sell(self, size, t=None, wallet=None, history=None):
#         try:
#             response = order(self.api_key, self.api_secret, 'SELL', 'MARKET', 0, size)
#             response.raise_for_status()
#         except RequestException as e:
#             print(e)
#             print(response)
#             response = None

#         return response.json()

#     def download_wallet(self):
#         response = get_balance(self.api_key, self.api_secret)
#         response.raise_for_status()

#         stocks = response.json()

#         w = Wallet()
#         for stock in stocks:
#             w.add(Stock(stock['currency_code'], str(stock['available'])))

#         return w

#     def get_balance_history(self, currency_code='JPY'):
#         """
#         Response の内訳は以下。
#         id ... 注文のイベントに結びついたID（と思われる）
#         trade_date ... 取引が成立した時間（と思われる）
#         event_date ... イベントが受け付けられた時間（と思われる、trade_date と同じ値が入っている）
#         product_code ... その取引における通貨のペア
#         currency_code ... 所持しているどの通貨に関する情報か
#         trade_type ... BUY, SELL, DEPOSIT, あとおそらく WITHDRAW がある
#                        currency_code を基準とした trade の type なので、
#                        currency_code='JPY', trade_type='sell' ならば、
#                        日本円を売って product_code の商品を買ったことを意味する
#         price ... その時点での商品の値段
#         amount ... 取引した currency_code の通貨の量
#         quantity ... 取引した product_code の商品の量
#         commission ... 取引手数料。あくまでも currency_code の通貨から引かれた量であり、
#                        Bitflyer は手数料は BTC から引くので JPY の履歴には手数料の記録は残らない。
#         balance ... 取引前に所持していた currency_code の通貨の量
#         order_id ... 取引に結びついたID（と思われる）
#                      たとえば１回の注文の成立に２回の取引が必要になったとき、
#                      おそらくその２回の取引について order_id は一致する。
#         """
#         response = get_balance_history(self.api_key, self.api_secret, currency_code=currency_code)
#         return response

#     def get_cashflow(self, t=None):
#         # DEPOSIT と WITHDRAW も考慮したい
#         df_jpy = pd.DataFrame.from_dict(self.get_balance_history(currency_code='JPY').json())
#         df_btc = pd.DataFrame.from_dict(self.get_balance_history(currency_code='BTC').json())

#         meta_columns = ['order_id', 'trade_date', 'product_code', 'trade_type']
#         cash_columns = ['balance', 'amount', 'commission']
#         x_columns = ['x(t)', 'X(t)', 'commission_x']
#         y_columns = ['y(t)', 'Y(t)', 'commission_y']
#         all_columns = ['id'] + meta_columns + \
#             ['code_x', 'code_y', 'x(t)', 'y(t)', 'X(t)', 'Y(t)', 'X(t+dt)', 'Y(t+dt)', 'commission_x', 'commission_y']

#         # id, 日付など
#         df_meta = df_jpy[['id'] + meta_columns].copy()
#         df_meta['trade_date'] = df_meta['trade_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%f'))

#         # quote（BTC_JPY で言えば JPY）の残高や取引金額などの情報
#         df_x = df_jpy[['id'] + cash_columns].copy()
#         df_x.columns = ['id'] + x_columns

#         # お金に関しては数値誤差を防ぐためいったん有理数へ変換
#         df_x[x_columns] = df_x[x_columns].applymap(lambda x: Fraction(str(x)))
#         # 取引金額に手数料を加算（手数料は負の値で格納されている）
#         df_x['X(t)'] += df_x['commission_x']
#         # X(t) はもともと amount（取引金額）なので、正の金額なら取引後に増加、負の値なら減少
#         df_x['X(t+dt)'] = df_x['X(t)'].apply(lambda x: x if x >= 0 else Fraction(0))
#         df_x['X(t)'] = df_x['X(t)'].apply(lambda x: -x if x < 0 else Fraction(0))
#         df_x['code_x'] = df_jpy['currency_code']

#         # base（BTC_JPY で言えば BTC）についても同様に処理
#         df_y = df_btc[['id'] + cash_columns].copy()
#         df_y.columns = ['id'] + y_columns

#         df_y[y_columns] = df_y[y_columns].applymap(lambda y: Fraction(str(y)))
#         df_y['Y(t)'] += df_y['commission_y']
#         df_y['Y(t+dt)'] = df_y['Y(t)'].apply(lambda y: y if y >= 0 else Fraction(0))
#         df_y['Y(t)'] = df_y['Y(t)'].apply(lambda y: -y if y < 0 else Fraction(0))
#         df_y['code_y'] = df_btc['currency_code']

#         df_xy = pd.merge(df_x, df_y, left_on='id', right_on='id', how='outer')
#         df_all = pd.merge(df_meta, df_xy, left_on='id', right_on='id', how='outer')

#         df_ret = df_all[all_columns]

#         return focus(df_ret, t, column='trade_date')

#     def download_history(self, t=None):
#         df = self.get_cashflow(t=t)
#         return cashflow_to_history(df)

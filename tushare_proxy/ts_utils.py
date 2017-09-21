import datetime
import os

import pandas as pd
import tushare as ts
from easyutils import get_stock_type
from pandas.compat import StringIO


def trade_cal():
    today = datetime.date.today()
    filename = '{}/trade_cal_{}.csv'.format(get_cache_path(), today)
    if os.path.exists(filename):
        text = open(filename, encoding='GBK').read()
        text = text.replace('--', '')
        cal = pd.read_csv(StringIO(text))
        cal = cal.set_index('calendarDate')
    else:
        cal = ts.trade_cal()
        cal = cal.set_index('calendarDate')
        cal.to_csv(filename)
    return cal


def get_settlement(hist):
    """计算前一日的收盘价，hist必须按时间倒序排列"""
    settlement = list(hist['close'])
    settlement.append(round(hist['open'][len(hist) - 1] / 1.1, 2))
    settlement.pop(0)
    return settlement


def clear_cache():
    __import__('shutil').rmtree(get_cache_path())


def get_stock_basics():
    """获取A股所有股票基本信息，如果服务器不好用则从文件读取"""
    filename = '_'.join(['get_stock_basics', str(datetime.date.today())])
    filename = get_cache_path() + os.path.sep + filename + '.csv'

    if os.path.exists(filename):
        text = open(filename, encoding='GBK').read()
        text = text.replace('--', '')
        hist = pd.read_csv(StringIO(text), dtype={'code': 'object'})
        hist = hist.set_index('code')
    else:
        try:
            hist = ts.get_stock_basics()
            hist.to_csv(filename)
        except Exception as e:
            hist = None
            print(e)
    return hist


def get_h_data(code, start=None, end=None, autype='qfq',
               index=False, retry_count=3, pause=0.001, drop_factor=True):
    filename = '_'.join(
        ['get_h_data', code, str(start), str(end), autype, str(index), str(drop_factor), str(datetime.date.today())])
    filename = get_cache_path() + os.path.sep + filename + '.csv'
    if os.path.exists(filename):
        text = open(filename, encoding='GBK').read()
        text = text.replace('--', '')
        hist = pd.read_csv(StringIO(text), dtype={'date': 'object'})
        hist['date'] = pd.to_datetime(hist['date'])
        hist = hist.set_index('date')
    else:
        try:
            # r = requests.get('http://127.0.0.1:8000/?types=0&country=国内')
            # ip_ports = json.loads(r.text)
            # id = random.randint(0, len(ip_ports) - 1)
            # ip = ip_ports[id][0]
            # port = ip_ports[id][1]
            #
            # key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            #                      r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0,
            #                      winreg.KEY_ALL_ACCESS)
            # print("proxy")
            # winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            # winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "{}:{}".format(ip, port))
            # winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "localhost;127.0.0.1")

            hist = ts.get_h_data(code, start, end, autype, index, retry_count, pause, drop_factor)
        except Exception as e:
            raise e
        finally:
            # print("disable proxy")
            # winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            pass

        hist.to_csv(filename)
    return hist


def get_hist_data(code, start=None, end=None):
    """从文件读取日K"""
    filename = 'd:/analyze_data/k/{}.csv'.format(code)
    if os.path.exists(filename):
        text = open(filename, encoding='GBK').read()
        text = text.replace('--', '')
        df = pd.read_csv(StringIO(text), dtype={'date': 'object'})
        df = df.set_index('date')
        if start is not None:
            df = df[df.index >= start]
        if end is not None:
            df = df[df.index <= end]
        return df
    else:
        return ts.get_hist_data(code, start=start, end=end)


def get_k_data(code='600423', date='2016-01-01', ktype='1'):
    """获取任意分钟K线"""

    filename = 'd:/analyze_data/tick/{}/{}.csv'.format(code, date)
    if os.path.exists(filename):
        text = open(filename, encoding='GBK').read()
        text = text.replace('--', '')
        df = pd.read_csv(StringIO(text), dtype={'date': 'object'})
        # df = df.set_index('date')
    else:
        df = ts.get_tick_data(code, date=date)
        df.to_csv(filename)
    # print(df)

    try:
        df['time'] = date + ' ' + df['time']
        df['time'] = pd.to_datetime(df['time'])
    except Exception as e:
        print(code, df['time'])
        return None

    df = df.set_index('time')
    # print(df)

    # 生成 一分钟 open high low close
    price_df = df['price'].resample('1min').ohlc()
    price_df = price_df.dropna()
    # print(price_df)

    # 累计成交额和成交量
    vols = df['volume'].resample('1min').sum()
    vols = vols.dropna()
    vol_df = pd.DataFrame(vols, columns=['volume'])

    amounts = df['amount'].resample('1min').sum()
    amounts = amounts.dropna()
    amount_df = pd.DataFrame(amounts, columns=['amount'])

    # 合并df
    try:
        min_df = price_df.merge(vol_df, left_index=True, right_index=True).merge(amount_df, left_index=True,
                                                                                 right_index=True)
    except Exception as e:
        print(code, price_df, vol_df, amount_df)
        return None
    # print(min_df)

    # 合成指定k线
    d_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'amount': 'sum'}

    r_df = pd.DataFrame()
    for col in min_df:
        r_df[col] = min_df[col].resample(ktype + 'min', how=d_dict[col])
    r_df = r_df.dropna()

    # print(r_df)

    return r_df


def get_high_time(index):
    """获取股价最高时间点"""
    df = get_k_data(index, date='2017-02-03', ktype='30')
    if df is not None:
        max = df['high'].max()
        # print(df[df['high'] == max].index[0])
        print(df[df['high'] == max].head(1))


def get_xueqiu_url(index):
    return 'https://xueqiu.com/S/{}{}'.format(get_stock_type(index).upper(), index)


def get_cache_path():
    path = os.path.expanduser('~') + os.path.sep + '.tushare_cache'
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def is_open_today():
    cal = trade_cal()
    today = datetime.date.today()

    return cal.loc[str(today)]['isOpen'] == 1


if __name__ == '__main__':
    # basics = get_stock_basics()
    # td = ThreadPool()
    # td.map(get_high_time, basics.index)

    print(get_cache_path())
    print(is_open_today())

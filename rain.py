import re
from datetime import date, timedelta
import pandas as pd
import getamedas
import requests
from bs4 import BeautifulSoup

amedas_dic = dict(気仙沼=1, 川渡=2, 築館=3, 志津川=4, 古川=5, 大衡=6, 鹿島台=7,
                  石巻=8, 新川=9, 仙台=10, 白石=11, 亘理=12, 米山=14, 塩釜=15,
                  駒ノ湯=16, 丸森=17, 名取=20, 蔵王=23, 女川=24)

# 西部の市町村をリスト化
east_city = ['泉区', '白石市', '蔵王町', '七ヶ宿町', '川崎町', '大和町',
             '大衡村', '色麻町', '加美町']
# 市町村と気象協会のコードの辞書
city_dic = dict(仙台市=4100, 青葉区=4101, 宮城野区=4102, 若林区=4103,
                太白区=4104, 泉区=4105, 白石市=4206, 角田市=4208, 蔵王町=4301,
                七ヶ宿町=4302, 大河原町=4321, 村田町=4322, 柴田町=4323,
                川崎町=4324, 丸森町=4341, 名取市=4207, 岩沼市=4211, 亘理町=4361,
                山元町=4362, 塩釜市=4203, 多賀城市=4209, 富谷市=4216,
                松島町=4401, 七ヶ浜町=4404, 利府町=4406, 大和町=4421,
                大郷町=4422, 大衡村=4424, 大崎市=4215, 色麻町=4444, 加美町=4445,
                涌谷町=4501, 美里町=4505, 栗原市=4213, 登米市=4212, 石巻市=4202,
                東松島市=4214, 女川町=4581, 気仙沼市=4205, 南三陸町=4606)


def past_rain_list(area, b_date, e_date):
    """当年の過去の降水量のリストを取得する関数

    getamedasモジュールで指定期間単年度の日別のデータを取得し、降水量のカラムを切り取る
    Args:
        area (str): アメダス地点名
        b_date (date): 取得開始日
        e_date (date): 取得最終日
    Returns:
        list:降水量のリスト
    """
    df = getamedas.get_amedas_data(area, b_date, e_date, 1, True)
    rain_l = list(df['降水量'])
    return rain_l


def forecast_rain_list(city, b_day, e_day):
    """気象協会の天気予報から2週間先までの降水量を予測する関数

    Args:
        city (str):予測する市町村名
        b_day (int):取得開始日
        e_day (int):取得終了日
    Returns:
        frl (list):降水量のリスト
    """
    ew_num = 3420 if city in east_city else 3410
    city_num = city_dic[city]
    url = f'https://tenki.jp/forecast/2/7/{ew_num}/{city_num}/10days.html'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')

    def get_rain(clas_name):
        rsp = soup.find_all('div', class_=clas_name)
        rlt = [r.text for r in rsp]
        rl = [int(re.sub(r"\D", "", s)) for s in rlt[1:31]]
        return rl

    frl = get_rain('precip')
    frl = frl[b_day - 1: e_day]
    return frl


def rain_list(area, city, b_date, length):
    """降水量のデータフレームを返す関数
    Args:
        area (str):アメダス地点名
        city (str): 市町村名
        b_date (date): 降水量の取得開始日
        length (int): 降水量の取得日数(〇日間）
    Returns:
        pd.Series:降水量のデータフレーム
    """
    e_date = b_date + timedelta(days=length - 1)
    y_date = date.today() - timedelta(days=1)
    tw_date = date.today() + timedelta(days=13)
    tw1_date = date.today() + timedelta(days=14)
    d_by = (b_date - y_date).days
    d_ey = (e_date - y_date).days
    if e_date <= y_date:
        rain_l = past_rain_list(area, b_date, e_date)
    elif b_date <= y_date and e_date <= tw_date:
        rain_l = past_rain_list(area, b_date, y_date) + \
                    forecast_rain_list(city, 1, d_ey)
    elif b_date <= y_date and e_date > tw_date:
        rain_l = past_rain_list(area, b_date, y_date) + \
                    forecast_rain_list(city, 1, 14)
    elif y_date < b_date <= tw_date and e_date <= tw_date:
        rain_l = forecast_rain_list(city, d_by, d_ey)
    else:
        rain_l = forecast_rain_list(city, d_by, 14)

    # temp_list を length に合わせて調整（不足分は 0）
    if len(rain_l) < length:
        rain_l += [0] * (length - len(rain_l))

    # 日付リストを作成 (スラッシュ区切りフォーマット)
    date_list = [(b_date + timedelta(days=i)).strftime('%Y/%m/%d') for i in
                 range(length)]
    rain_df = pd.Series(rain_l, index=date_list)
    return rain_df


# 動作確認用
def main():
    area = '石巻'
    city = '石巻市'
    b_date = date(2026, 4, 1)
    length = 60
    temp_df = rain_list(area, city, b_date, length)
    print(temp_df)


if __name__ == '__main__':
    main()

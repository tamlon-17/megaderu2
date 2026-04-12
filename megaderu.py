from datetime import date, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import streamlit as st
import averagetemplist as atl
import rain

amedas_l = ['丸森', '白石', '蔵王', '亘理', '名取', '仙台', '新川', '塩釜',
            '大衡', '古川', '川渡', '鹿島台', '築館', '駒ノ湯', '米山', '石巻',
            '女川', '気仙沼', '志津川']
city_l = ['白石市', '角田市', '蔵王町', '七ヶ宿町', '大河原町', '村田町',
          '柴田町', '川崎町', '丸森町', '名取市', '岩沼市', '亘理町', '山元町',
          '仙台市', '塩釜市', '多賀城市', '富谷市', '松島町', '七ヶ浜町',
          '利府町', '大和町', '大郷町', '大衡村', '大崎市', '色麻町', '加美町',
          '涌谷町', '美里町', '栗原市', '登米市', '石巻市', '東松島市',
          '女川町', '気仙沼市', '南三陸町']

st.set_page_config(page_title='めがで～る２！', page_icon='icon.ico')
st.caption('水稲乾田直播 出芽予測ウェブアプリ')
st.title('めがで～る２！')
st.text('有効積算気温から、乾直（乾籾の場合）の出芽日を予測します。')
st.text('実際の出芽のタイミングは、種もみを掘り起こして確認してください。')
if st.button('アプリの説明～まずはここを読んでから！'):
    st.switch_page('pages/readme.py')

with st.form(key='input_form'):
    st.header('入力フォーム')
    a_area = st.radio('アメダス地点の選択', amedas_l, horizontal=True)
    city = st.radio('市町村の選択', city_l, horizontal=True)
    seeding_date = st.date_input('播種日')
    # 播種日が3月１日以前の場合は。播種日を３月１日に補正する。
    mar1_day = date(date.today().year, 3, 1)
    seeding_date = seeding_date if (mar1_day < seeding_date) else mar1_day
    begin_date = seeding_date + timedelta(days=1)
    years = st.slider('平年値の年数（直近〇か年）', min_value=1, max_value=10,
                      value=5, step=1)

    submit_button = st.form_submit_button(label='予測開始')

if submit_button:
    ave_temp_series = atl.ave_temp_list(a_area, city, begin_date, 80,
                                        int(years))
    # 平均気温リストから11.5℃を引いた有効積算リストを作成
    ef_temp_list = [0 if xx * 10 <= 115 else round(xx - 11.5, 1) for xx in
                    ave_temp_series]
    cum_temp_series = np.array(ef_temp_list).cumsum()
    rain_list = rain.rain_list(a_area, city, begin_date, 80)
    df_chart80 = pd.DataFrame({
        '平均気温': ave_temp_series,
        '有効積算気温': cum_temp_series,
        '降水量': rain_list
    })
    threshold = 100  # ここに好きな閾値を入れる
    # 積算気温が threshold を超えた最初の行の index を取得
    cut_idx = df_chart80[df_chart80['有効積算気温'] > threshold].index
    # 超えた行が存在する場合、その行までを切り出す
    if len(cut_idx) > 0:
        df_chart = df_chart80.loc[:cut_idx[0]]
    else:
        df_chart = df_chart80.copy()

    # 30〜50℃に該当する行を抽出
    mask = (df_chart['有効積算気温'] >= 30) & (
            df_chart['有効積算気温'] <= 50)
    # 該当期間の開始・終了日を取得
    highlight_dates = df_chart[mask].index
    if not highlight_dates.empty:
        start_date = highlight_dates[0]
        end_date = highlight_dates[-1]

    st.header('予測結果')
    st.caption(
        '黄色の網掛け部分が積算気温30～50℃の範囲。緑の点線は平均気温11.5℃のライン。')

    fig = go.Figure()
    # 平均気温グラフ（右軸に変更）
    fig.add_trace(go.Scatter(
        x=df_chart.index,
        y=df_chart['平均気温'],
        name='平均気温',
        line=dict(color='green'),
        yaxis='y2'  # ← 右軸へ変更
    ))

    # 有効積算気温グラフ（左軸に変更）
    fig.add_trace(go.Scatter(
        x=df_chart.index,
        y=df_chart['有効積算気温'],
        name='有効積算気温',
        line=dict(color='orange'),
        yaxis='y1'  # ← 左軸へ変更
    ))

    # 降水量の棒グラフ（右軸）
    fig.add_trace(go.Bar(
        x=df_chart.index,
        y=df_chart['降水量'],
        name='降水量',
        marker=dict(color='blue'),
        opacity=0.3,
        yaxis='y2'
    ))

    # 積算気温の帯（y1 に合わせる）
    fig.add_shape(
        type="rect",
        x0=0, x1=1,
        xref="paper",
        y0=30, y1=50,
        yref="y1",  # ← 左軸に変更
        fillcolor="yellow",
        opacity=0.1,
        layer="below",
        line_width=0
    )

    # 日付範囲の帯（そのまま）
    fig.add_shape(
        type="rect",
        x0=start_date,
        x1=end_date,
        xref="x",
        y0=0,
        y1=1,
        yref="paper",
        fillcolor="yellow",
        opacity=0.2,
        layer="below",
        line_width=0
    )

    fig.add_shape(
        type="line",
        x0=df_chart.index.min(),
        x1=df_chart.index.max(),
        xref="x",
        y0=11.5,
        y1=11.5,
        yref="y2",  # ← 右軸（平均気温）基準
        line=dict(color="green", width=1, dash="dash")
    )

    fig.update_layout(
        xaxis=dict(title='日付'),

        # 左軸（有効積算気温）
        yaxis=dict(
            title=dict(text='有効積算気温（℃）', font=dict(color='orange')),
            range=[0, 105],
            dtick=10,
            showgrid=False
        ),
        # 右軸（平均気温）
        yaxis2=dict(
            title=dict(text='<span style="color:blue;">降水量（mm）</span>・'
                            '<span style="color:green;">平均気温（℃）</span>'),
            overlaying='y',
            side='right',
            range=[0, 25],
            dtick=5,
            showgrid=False,
        ),
        legend=dict(x=0.05, y=0.95),
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    st.text('播種後の平均気温と降水量')
    st.dataframe(df_chart, width=360)

import os
import pandas as pd
import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objs as go

data_directory = 'data'
data_file_name = 'viz.csv'

# データの読み込み
data = pd.read_csv(os.path.join(data_directory, data_file_name))

# データの処理（小数点第3位まで）
for column in data.select_dtypes(include=['float', 'int']):
    data[column] = data[column].round(3)

# 平均GDP成長率の計算 (2024年から2028年)
data['average_growth_2024_2028'] = data[[
    '2024', '2025', '2026', '2027', '2028']].mean(axis=1).round(3)

# Dashアプリの初期化
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 年の一覧を取得
years = [str(year) for year in range(2019, 2029)]

# アプリレイアウト
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("国別気温とGDP成長率分析ダッシュボード")
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Label("年の選択:"),
            dcc.Dropdown(
                id='year-dropdown', options=[{'label': year, 'value': year} for year in years], value='2023')
        ], width=4),
        dbc.Col([
            html.Label("平均気温の範囲:"),
            dcc.RangeSlider(id='temp-slider', min=data['mean'].min(), max=data['mean'].max(), step=0.5, value=[data['mean'].min(
            ), data['mean'].max()], marks={i: f'{i}°' for i in range(int(data['mean'].min()), int(data['mean'].max())+1, 5)})
        ], width=4),
        dbc.Col([
            html.Label("GDP成長率の範囲:"),
            dcc.RangeSlider(id='gdp-slider', min=data[years].min().min(), max=data[years].max().max(), step=0.1, value=[data[years].min().min(
            ), data[years].max().max()], marks={i: f'{i}%' for i in range(int(data[years].min().min()), int(data[years].max().max())+1, 5)})
        ], width=4)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='mean-temp-gdp-plot')
        ], width=6),
        dbc.Col([
            dcc.Graph(id='max-min-temp-plot')
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dash_table.DataTable(
                id='country-table',
                columns=[{'name': i, 'id': i} for i in data.columns],
                data=data.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'},
                    {'if': {'state': 'selected'},
                        'backgroundColor': 'rgba(0, 116, 217, 0.3)', 'border': '1px solid blue'}
                ],
                sort_action="native",
                filter_action="native"
            )
        ], width=12)
    ])
], fluid=True)

# コールバック定義


@app.callback(
    [Output('country-table', 'data'),
     Output('mean-temp-gdp-plot', 'figure'),
     Output('max-min-temp-plot', 'figure')],
    [Input('year-dropdown', 'value'),
     Input('temp-slider', 'value'),
     Input('gdp-slider', 'value')]
)
def update_plots(selected_year, temp_range, gdp_range):
    # データフィルタリング
    filtered_data = data[(data['mean'] >= temp_range[0]) & (data['mean'] <= temp_range[1]) & (
        data[selected_year] >= gdp_range[0]) & (data[selected_year] <= gdp_range[1])]
    # 表示する列を更新
    table_data = filtered_data.to_dict('records')

    # 平均気温とGDP成長率のプロット
    fig_mean_temp_gdp = go.Figure()
    for region in filtered_data['Region'].unique():
        region_data = filtered_data[filtered_data['Region'] == region]
        # 選択された国に応じた透明度を設定
        fig_mean_temp_gdp.add_trace(go.Scatter(
            x=region_data[selected_year],
            y=region_data['mean'],
            mode='markers',
            error_y=dict(
                type='data', array=region_data['mean_sd'], color='#aaa', thickness=1.5, width=2),
            name=region,
            text=region_data['Country'],
            marker=dict(size=10)
        ))
    fig_mean_temp_gdp.update_layout(
        title=f"{selected_year}年の平均気温とGDP成長率",
        xaxis_title="GDP成長率 (%)",
        yaxis_title="平均気温 (°C)"
    )

    # 最高気温と最低気温のプロット
    fig_max_min_temp = go.Figure()
    for region in filtered_data['Region'].unique():
        region_data = filtered_data[filtered_data['Region'] == region]
        fig_max_min_temp.add_trace(go.Scatter(
            x=region_data['min'],
            y=region_data['max'],
            mode='markers',
            error_x=dict(
                type='data', array=region_data['min_sd'], color='#888', thickness=1.5, width=2),
            error_y=dict(
                type='data', array=region_data['max_sd'], color='#888', thickness=1.5, width=2),
            marker=dict(color=region_data['average_growth_2024_2028'],
                        colorscale='Viridis', showscale=True, size=10),
            text=region_data['Country']
        ))

    fig_max_min_temp.update_layout(
        title="最高気温と最低気温の関係",
        xaxis_title="最低気温 (°C)",
        yaxis_title="最高気温 (°C)"
    )

    return table_data, fig_mean_temp_gdp, fig_max_min_temp


# ポート番号の取得
port = int(os.environ.get("PORT", 8080))

# アプリを起動
if __name__ == '__main__':
    app.run_server(debug=True, port=port)

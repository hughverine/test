import streamlit as st
import time
import logging
from typing import Optional, Dict
from scraper import fetch_exchange_rates, fetch_historical_rates
from webdriver_utils import setup_driver

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ページタイトル設定
st.title("為替レート取得ツール")

# セッション状態の初期化
if 'exchange_rates' not in st.session_state:
    st.session_state.exchange_rates = {}  # 初期値
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = None
# 履歴データ用のセッション状態
if 'historical_rates' not in st.session_state:
    st.session_state.historical_rates = {}  # 初期値
if 'historical_last_update' not in st.session_state:
    st.session_state.historical_last_update = None

# メイン表示エリア
st.markdown("指定された外部サイトから為替レート情報を取得します。「最新のレートを取得」ボタンをクリックしてください。")

# 対象URLと要素情報
target_url = "https://prismatic-centaur-0eadf3.netlify.app/"
st.caption(f"対象サイト: {target_url}")

# 取得ボタン
if st.button("最新のレートを取得", key="get_rates_button"):
    # 取得中のスピナー表示
    with st.spinner("為替レートを取得中です..."):
        try:
            # 前回のエラーメッセージをクリア
            st.session_state.error_message = None
            st.session_state.debug_info = None
            
            # WebDriverの取得
            driver = setup_driver()
            if driver is None:
                st.session_state.error_message = "WebDriverの初期化に失敗しました。"
                logger.error("WebDriverの初期化に失敗")
            else:
                # 対象サイトから為替レート取得
                exchange_rates = fetch_exchange_rates(
                    driver=driver,
                    url=target_url,
                    timeout=20
                )
                
                if exchange_rates and len(exchange_rates) > 0:
                    # 取得成功時
                    st.session_state.exchange_rates = exchange_rates
                    st.session_state.last_update_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    st.success(f"{len(exchange_rates)}通貨の為替レートを取得しました。")
                else:
                    # 取得失敗時
                    st.session_state.error_message = "為替レートの取得に失敗しました。"
                    st.session_state.debug_info = "ネットワーク接続や対象サイトの状態、またはテーブル要素を確認してください。"
                    logger.error("為替レート取得に失敗")
        except Exception as e:
            st.session_state.error_message = "エラーが発生しました"
            st.session_state.debug_info = str(e)
            logger.error(f"予期しないエラー: {str(e)}")

# エラー情報表示
if st.session_state.error_message:
    st.error(st.session_state.error_message)
    if st.session_state.debug_info:
        st.warning(st.session_state.debug_info)
    
    # トラブルシューティング情報
    with st.expander("トラブルシューティング"):
        st.markdown("""
        **考えられる問題と対処法:**
        1. **ネットワーク接続の問題**: インターネット接続を確認してください
        2. **対象サイトの変更**: サイトが変更されたか、停止している可能性があります
        3. **テーブル要素の変更**: 為替レートテーブルの構造が変更された可能性があります
        4. **ブラウザドライバの問題**: ChromeDriverの再インストールが必要かもしれません
        """)

# 為替レート表示エリア
if st.session_state.exchange_rates:
    st.subheader("取得した為替レート")
    st.markdown("1 JPYあたりの各通貨レート")
    
    # データフレームに変換してテーブル表示
    import pandas as pd
    
    # データを整形
    rates_data = []
    for currency, rate in st.session_state.exchange_rates.items():
        rates_data.append({
            "通貨コード": currency,
            "レート (1 JPY)": rate,
            "逆レート (1通貨あたりのJPY)": round(1 / rate if rate != 0 else 0, 2)
        })
    
    # DataFrameに変換
    df = pd.DataFrame(rates_data)
    
    # テーブル表示
    st.dataframe(df, use_container_width=True)
    
    # 特定の通貨の詳細表示（米ドルなど）
    if "USD" in st.session_state.exchange_rates:
        usd_rate = st.session_state.exchange_rates["USD"]
        st.metric(
            label="USD/JPY レート", 
            value=f"{usd_rate:.6f}",
            delta=None
        )
else:
    st.info("まだ為替レートを取得していません。「最新のレートを取得」ボタンをクリックしてください。")

# 最終更新時刻表示（取得済みの場合のみ）
if st.session_state.last_update_time:
    st.caption(f"最終更新: {st.session_state.last_update_time}")

# 履歴データ取得セクション
st.markdown("---")
st.subheader("為替レート履歴データ")
st.markdown("USDの過去1ヶ月分の為替レート推移を取得します。")

historical_url = "https://prismatic-centaur-0eadf3.netlify.app/historical"
st.caption(f"データソース: {historical_url}")

# 履歴データ取得ボタン
if st.button("USD履歴データを取得", key="get_historical_button"):
    # 取得中のスピナー表示
    with st.spinner("履歴データを取得中です..."):
        try:
            # 前回のエラーメッセージをクリア
            st.session_state.error_message = None
            st.session_state.debug_info = None
            
            # WebDriverの取得
            driver = setup_driver()
            if driver is None:
                st.session_state.error_message = "WebDriverの初期化に失敗しました。"
                logger.error("WebDriverの初期化に失敗")
            else:
                # 対象サイトから履歴データ取得
                historical_rates = fetch_historical_rates(
                    driver=driver,
                    url=historical_url,
                    currency_code="USD",
                    timeout=30
                )
                
                if historical_rates and len(historical_rates) > 0:
                    # 取得成功時
                    st.session_state.historical_rates = historical_rates
                    st.session_state.historical_last_update = time.strftime("%Y-%m-%d %H:%M:%S")
                    st.success(f"{len(historical_rates)}日分のUSD履歴データを取得しました。")
                else:
                    # 取得失敗時
                    st.session_state.error_message = "履歴データの取得に失敗しました。"
                    st.session_state.debug_info = "ネットワーク接続や対象サイトの状態、またはテーブル要素を確認してください。"
                    logger.error("履歴データ取得に失敗")
        except Exception as e:
            st.session_state.error_message = "エラーが発生しました"
            st.session_state.debug_info = str(e)
            logger.error(f"予期しないエラー: {str(e)}")

# 履歴データのグラフ表示
if st.session_state.historical_rates:
    st.subheader("USD/JPY 過去1ヶ月の為替レート推移")
    
    # データフレーム作成
    import pandas as pd
    import datetime
    
    # 日付と値のリストを作成
    dates = []
    rates = []
    for date_str, rate in st.session_state.historical_rates.items():
        try:
            # 日付文字列をdatetimeオブジェクトに変換（フォーマットは実際のデータに合わせて調整）
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(date_obj)
            rates.append(rate)
        except ValueError:
            logger.warning(f"日付変換エラー: {date_str}")
            continue
    
    # データフレーム作成
    df_hist = pd.DataFrame({
        "日付": dates,
        "レート (1 JPY)": rates
    })
    
    # 日付でソート
    df_hist = df_hist.sort_values(by="日付")
    
    # インデックスを日付に設定
    df_hist = df_hist.set_index("日付")
    
    # グラフ表示
    st.line_chart(df_hist)
    
    # データテーブル表示
    st.subheader("履歴データ一覧")
    st.dataframe(df_hist, use_container_width=True)
    
    # 最終更新時刻表示
    if st.session_state.historical_last_update:
        st.caption(f"最終更新: {st.session_state.historical_last_update}")
else:
    st.info("USDの履歴データをまだ取得していません。「USD履歴データを取得」ボタンをクリックしてください。")

# 注意事項
st.markdown("---")
st.caption(f"※ このツールは外部サイト（{target_url}）から情報を取得します。")
st.caption("※ 対象サイトの構造変更により、動作しなくなる可能性があります。") 
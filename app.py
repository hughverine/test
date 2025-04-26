import streamlit as st
import time
import logging
from typing import Optional, Dict
from scraper import fetch_exchange_rates
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

# 注意事項
st.markdown("---")
st.caption(f"※ このツールは外部サイト（{target_url}）から情報を取得します。")
st.caption("※ 対象サイトの構造変更により、動作しなくなる可能性があります。") 
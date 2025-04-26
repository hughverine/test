import atexit
import logging
from typing import Optional

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager  # クラウド環境では不要

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@st.cache_resource
def setup_driver() -> Optional[webdriver.Chrome]:
    """
    WebDriverインスタンスをセットアップして返す関数
    キャッシュ機能により、アプリケーション実行中は同じインスタンスが再利用される
    
    Returns:
        webdriver.Chrome: 設定済みWebDriverインスタンス、失敗時はNone
    """
    try:
        logger.info("WebDriverをセットアップ中...")
        
        # Chromeオプションの設定
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # 新しいヘッドレスモード（Chrome 109以降）
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Streamlit Cloud環境用の追加設定
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--single-process")
        
        # WebDriverインスタンスの作成（クラウド環境向けに簡易化）
        driver = webdriver.Chrome(options=chrome_options)
        
        # タイムアウト設定
        driver.set_page_load_timeout(30)  # ページ読み込みタイムアウト30秒
        driver.implicitly_wait(10)  # 要素検索の暗黙的待機時間10秒
        
        # 終了時にWebDriverを閉じるよう登録
        atexit.register(lambda: close_driver(driver))
        
        logger.info("WebDriverのセットアップが完了しました")
        return driver
        
    except Exception as e:
        logger.error(f"WebDriverのセットアップ中にエラーが発生しました: {str(e)}")
        return None

def close_driver(driver: webdriver.Chrome) -> None:
    """
    WebDriverインスタンスを安全に閉じる関数
    
    Args:
        driver (webdriver.Chrome): 閉じるWebDriverインスタンス
    """
    try:
        if driver:
            logger.info("WebDriverを終了しています...")
            driver.quit()
            logger.info("WebDriverを正常に終了しました")
    except Exception as e:
        logger.error(f"WebDriverの終了中にエラーが発生しました: {str(e)}") 
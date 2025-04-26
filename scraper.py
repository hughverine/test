import logging
import time
from typing import Optional, Dict, List, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_exchange_rates(driver: webdriver.Chrome, url: str, timeout: int = 20) -> Optional[Dict[str, float]]:
    """
    指定されたURLのウェブサイトから為替レート情報を取得する関数
    
    Args:
        driver (webdriver.Chrome): 設定済みWebDriverインスタンス
        url (str): アクセス先のURL
        timeout (int, optional): 要素検索のタイムアウト秒数. デフォルトは20秒
    
    Returns:
        Optional[Dict[str, float]]: 取得した為替レート情報（通貨コード: レート値）、取得失敗時はNone
    """
    try:
        logger.info(f"サイト {url} へアクセス中...")
        
        # 指定URLへアクセス
        driver.get(url)
        
        # JavaScript完全読み込みを待機
        time.sleep(2)
        
        # ページ読み込み状態をログに出力
        logger.info(f"ページタイトル: {driver.title}")
        logger.info(f"現在のURL: {driver.current_url}")
        
        # 為替レートテーブルが表示されるまで待機
        logger.info("為替レートテーブルを待機中...")
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.ID, "exchange-rate-table"))
        )
        
        # テーブル内の行をすべて取得
        rate_rows = driver.find_elements(By.CSS_SELECTOR, "#rate-list-body .rate-row")
        logger.info(f"{len(rate_rows)}個の通貨レート行を検出しました")
        
        if not rate_rows:
            logger.error("為替レート行が見つかりませんでした")
            return None
        
        # 通貨コードとレートの辞書を作成
        exchange_rates = {}
        
        for row in rate_rows:
            try:
                currency_code = row.find_element(By.CSS_SELECTOR, ".currency-code").text
                rate_value_element = row.find_element(By.CSS_SELECTOR, ".rate-value")
                # data-rate-value属性から値を取得（より正確）
                rate_value = float(rate_value_element.get_attribute("data-rate-value"))
                exchange_rates[currency_code] = rate_value
                logger.info(f"取得: {currency_code} = {rate_value}")
            except (NoSuchElementException, ValueError) as e:
                logger.warning(f"一部のレート情報取得中にエラー: {str(e)}")
                continue
        
        if not exchange_rates:
            logger.error("有効な為替レート情報を取得できませんでした")
            return None
        
        logger.info(f"{len(exchange_rates)}個の通貨レートの取得に成功しました")
        return exchange_rates
        
    except TimeoutException:
        logger.error(f"タイムアウト: {timeout}秒以内に為替レートテーブルが見つかりませんでした")
        
        # ページソースをログに出力
        try:
            logger.info("ページソース（一部）:")
            page_source = driver.page_source
            logger.info(page_source[:1000] + "..." if len(page_source) > 1000 else page_source)
        except Exception as e:
            logger.error(f"ページソース取得中にエラー: {str(e)}")
        
        return None
        
    except NoSuchElementException:
        logger.error("要素が見つかりません: 為替レートテーブルの要素が存在しないか変更された可能性があります")
        return None
        
    except WebDriverException as e:
        logger.error(f"WebDriverでエラーが発生しました: {str(e)}")
        return None
        
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}")
        return None

def fetch_historical_rates(driver: webdriver.Chrome, url: str, currency_code: str = "USD", timeout: int = 30) -> Optional[Dict[str, float]]:
    """
    指定されたURLから特定通貨の過去1ヶ月分の為替レート履歴を取得する関数
    
    Args:
        driver (webdriver.Chrome): 設定済みWebDriverインスタンス
        url (str): ヒストリカルデータページのURL
        currency_code (str): 取得対象の通貨コード（デフォルトはUSD）
        timeout (int): 要素検索のタイムアウト秒数
    
    Returns:
        Optional[Dict[str, float]]: 取得した履歴データ（日付: レート値）、取得失敗時はNone
    """
    try:
        logger.info(f"履歴データページ {url} へアクセス中...")
        
        # 指定URLへアクセス
        driver.get(url)
        
        # JavaScript完全読み込みを待機
        time.sleep(2)
        
        # ページ読み込み状態をログに出力
        logger.info(f"ページタイトル: {driver.title}")
        logger.info(f"現在のURL: {driver.current_url}")
        
        # 履歴テーブルが表示されるまで待機
        logger.info("履歴データテーブルを待機中...")
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.TAG_NAME, "table"))
        )
        
        # テーブルの行を全て取得
        table_rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
        logger.info(f"{len(table_rows)}行のテーブルデータを検出しました")
        
        if len(table_rows) <= 1:  # ヘッダー行のみの場合
            logger.error("テーブルにデータ行が見つかりませんでした")
            return None
        
        # 日付とレートの辞書を作成
        historical_rates = {}
        
        # 1行目はヘッダーなのでスキップし、2行目から処理
        for row in table_rows[1:]:
            try:
                columns = row.find_elements(By.TAG_NAME, "td")
                if len(columns) >= 2:
                    date_str = columns[0].text.strip()
                    rate_str = columns[1].text.strip()
                    
                    # レート値を数値に変換
                    try:
                        rate_value = float(rate_str)
                        historical_rates[date_str] = rate_value
                        logger.info(f"取得: {date_str} = {rate_value}")
                    except ValueError:
                        logger.warning(f"レート値の変換に失敗: {rate_str}")
                        continue
            except (NoSuchElementException, IndexError) as e:
                logger.warning(f"行データの解析中にエラー: {str(e)}")
                continue
        
        if not historical_rates:
            logger.error("有効な履歴データを取得できませんでした")
            return None
        
        logger.info(f"{len(historical_rates)}日分の履歴データの取得に成功しました")
        return historical_rates
        
    except TimeoutException:
        logger.error(f"タイムアウト: {timeout}秒以内に履歴データテーブルが見つかりませんでした")
        return None
        
    except NoSuchElementException:
        logger.error("要素が見つかりません: 履歴データテーブルの要素が存在しないか変更された可能性があります")
        return None
        
    except WebDriverException as e:
        logger.error(f"WebDriverでエラーが発生しました: {str(e)}")
        return None
        
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}")
        return None 
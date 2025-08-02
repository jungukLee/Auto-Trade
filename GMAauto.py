import pyupbit
import time
import datetime
import traceback
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

pd.options.display.float_format = '{:.2f}'.format
TICKER = "KRW-ETH"

class AutoTradeGMMA:
    def __init__(self, start_cash, slack_bot):
        self.fee = 0.0011  # 수수료
        self.ticker = TICKER  # 티커
        self.buy_price = 0  # 매수가
        self.holding = False
        self.start_cash = start_cash  # 시작 자산
        self.slack_bot = slack_bot  # Slack 인스턴스

        # 초기 자산 상태를 슬랙으로 알림
        self.slack_bot.message(f"자동 매매 프로그램이 시작되었습니다\n시작 자산 : {self.start_cash}")

    def wait_for_next_interval(self):
        now = datetime.datetime.now()
        # 현재 시간이 몇 분인지 계산
        seconds_until_next_interval = (5 - now.minute % 5) * 60 - now.second
        # 5분 정각까지 대기
        if seconds_until_next_interval > 0:
            print(f"Waiting for {seconds_until_next_interval} seconds to reach the next 5-minute interval.")
            time.sleep(seconds_until_next_interval)

        print("Waiting 20 seconds for data to be updated.")
        time.sleep(20)

    def start(self):
        self.wait_for_next_interval()  # 시작 시점이 5분 정각이 되도록 대기

        while True:
            try:
                # 데이터 갱신
                self.get_data()

                # 최신 데이터로 신호 확인 및 거래 실행
                self.check_signals()

                # 상태 출력
                current_price = pyupbit.get_current_price(self.ticker)
                print(datetime.datetime.now(), "\tCurrent :", current_price, "\t holding:", self.holding)
                
                # 5분마다 반복
                time.sleep(300)

            except SlackApiError as e:
                self.handle_error(e)
            except Exception as err:
                self.handle_error(err)

    def check_signals(self):
        row = self.minute_data.iloc[-1]  # 최신 데이터 행을 가져옵니다.
        # 거래 신호 확인 및 실행
        if self.buy_condition(row) and not self.holding:
            self.buy_coin()
            self.holding = True
        elif self.holding and self.sell_condition(row):
            self.sell_coin()
            self.holding = False

    def buy_coin(self):
        balance = upbit.get_balance()  # 잔고 조회
        if balance > 5000:  # 잔고 5000원 이상일 때
            upbit.buy_market_order(self.ticker, balance * 0.9995)
            buy_price = pyupbit.get_orderbook(self.ticker)['orderbook_units'][0]['ask_price']  # 최우선 매도 호가
            
            print('====================매수 시도====================')
            self.slack_bot.message(f"#매수 주문\n매수 주문 가격 : {buy_price}원")

    def sell_coin(self):
        balance = upbit.get_balance(self.ticker)  # 잔고 조회
        upbit.sell_market_order(self.ticker, balance)
        sell_price = pyupbit.get_orderbook(self.ticker)['orderbook_units'][0]['bid_price']  # 최우선 매수 호가
        
        print('====================매도 시도====================')
        self.slack_bot.message(f"#매도 주문\n매도 주문 가격 : {sell_price}원")

    def get_data(self):
        print("\n==================== [ 데이터 갱신 시도 ] ====================")
        self.minute_data = pyupbit.get_ohlcv(self.ticker, interval="minute5", count=4320)  # 15일간의 5분봉 데이터
        ma_periods = {
            'ma3': 3 * 288,  # 3일 이동평균
            'ma5': 5 * 288,  # 5일 이동평균
            'ma8': 8 * 288,  # 8일 이동평균
            'ma10': 10 * 288,  # 10일 이동평균
            'ma12': 12 * 288,  # 12일 이동평균
            'ma15': 15 * 288  # 15일 이동평균
        }
        for ma, period in ma_periods.items():
            self.minute_data[ma] = self.minute_data['close'].rolling(window=period, min_periods=1).mean().shift(1)
        print(self.minute_data.tail())
        print("==================== [ 데이터 갱신 완료 ] ====================\n")

    def buy_condition(self, row):
        return (row['ma3'] > row['ma5'] and
                row['ma5'] > row['ma8'] and
                row['ma8'] > row['ma10'] and
                row['ma10'] > row['ma12'] and
                row['ma12'] > row['ma15'])

    def sell_condition(self, row):
        return (row['ma3'] < row['ma5'] or
                row['ma5'] < row['ma8'] or
                row['ma8'] < row['ma10'] or
                row['ma10'] < row['ma12'] or
                row['ma12'] < row['ma15'])

    def handle_error(self, error):
        error_message = f"Error: {error}"
        print(error_message)
        self.slack_bot.message(error_message)
        traceback.print_exc()

class Slack:
    def __init__(self, token, channel):
        self.client = WebClient(token=token)
        self.channel = channel

    def message(self, message):
        try:
            self.client.chat_postMessage(channel=self.channel, text=message)
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")

# 상수 값들
upbit = pyupbit.Upbit(acc_key, sec_key)
slack_bot = Slack(appToken, channel)

start_cash = upbit.get_balance()
trading_bot = AutoTradeGMMA(start_cash, slack_bot)
trading_bot.start()

print("프로그램 실행!")
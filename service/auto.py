import pyupbit
import time
import datetime
import traceback
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class autoTrade :
    def __init__(self, start_cash, ticker) :
        self.fee = 0.05 # 수수료
        self.target_price = 0 # 목표 매수가
        self.ma5 = 0 # 5일 이동평균
        self.ticker = ticker # 티커
        self.buy_yn = False # 매수 여부
        self.start_cash = start_cash # 시작 자산
        self.timer = 0
        self.get_today_data()        

    def start(self) :
        now = datetime.datetime.now() # 현재 시간
        current_price = pyupbit.get_current_price(self.ticker)
        slackBot.message(f"자동 매매 프로그램이 시작되었습니다\n시작 시간 : {now}\n매매 대상 : {self.ticker}\n시작 자산 : {self.start_cash}\n목표가 : {self.target_price}\n현재 가격 : {current_price}")
        openTime = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=9, seconds=10) # 09:00:10

        while True:
            try :
                now = datetime.datetime.now()
                current_price = pyupbit.get_current_price(self.ticker)

                if(self.timer % 60 == 0) :
                    print(now, "\topenTime :", openTime, "\tTarget :", self.target_price, "\tCurrent :", current_price, "\tMA5 :", self.ma5, "\tBuy_yn :", self.buy_yn)

                if openTime < now < openTime + datetime.timedelta(seconds=10) :
                    openTime = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=9, seconds=10)
                    if(self.buy_yn) :
                        print("==================== [ 매도 시도 ] ====================")
                        slackBot.message("매도 시도")
                        self.sell_coin()
                    self.get_today_data() # 데이터 갱신
                    slackBot.message(f"데이터가 갱신되었습니다.시간 : {now}\n매매 대상 : {self.ticker}\n 자산 : {upbit.get_balance()}\n목표가 : {self.target_price}\n현재 가격 : {current_price}")
                    print(f"9시20초 데이터 갱신 완료. 시간 : {now}")

                if((current_price >= self.target_price) and (current_price >= self.ma5) and not self.buy_yn) : # 매수 시도
                    print("==================== [ 매수 시도 ] ====================")
                    slackBot.message("매수 시도")
                    self.buy_coin()

            except SlackApiError as e:
                print(f"Error fetching messages: {e.response['error']}")
                slackBot.message(f"Error fetching messages: {e.response['error']}")
            except Exception as err:
                slackBot.message("!!! 프로그램 오류 발생 !!!")
                slackBot.message(err)
                traceback.print_exc()
            
            self.timer += 1
            time.sleep(1)

    def get_today_data(self) :
        print("\n==================== [ 데이터 갱신 시도 ] ====================")
        daily_data = pyupbit.get_ohlcv(self.ticker, count=41)
        # 노이즈 계산 ( 1- 절대값(시가 - 종가) / (고가 - 저가) )
        daily_data['noise'] = 1 - abs(daily_data['open'] - daily_data['close']) / (daily_data['high'] - daily_data['low'])
        # 노이즈 20일 평균
        daily_data['noise_ma20'] = daily_data['noise'].rolling(window=20).mean().shift(1)
        # 변동폭 ( 고가 - 저가 )
        daily_data['range'] = daily_data['high'] - daily_data['low']
        # 목표매수가 ( 시가 + 변동폭 * K )
        daily_data['targetPrice'] = daily_data['open'] + daily_data['range'].shift(1) * daily_data['noise_ma20']
        # 5일 이동평균선
        daily_data['ma5'] = daily_data['close'].rolling(window=5, min_periods=1).mean().shift(1)
        # 상승장 여부
        # daily_data['bull'] = daily_data['open'] > daily_data['ma5']
        today = daily_data.iloc[-1]
        self.target_price = today.targetPrice
        self.ma5 = today.ma5
        print(daily_data.tail())
        print("==================== [ 데이터 갱신 완료 ] ====================\n")

    def buy_coin(self) :
        self.buy_yn = True
        balance = upbit.get_balance() # 잔고 조회
        
        if balance > 5000 : # 잔고 5000원 이상일 때
            upbit.buy_market_order(self.ticker, balance * 0.9995)

            buy_price = pyupbit.get_orderbook(self.ticker)['orderbook_units'][0]['ask_price'] # 최우선 매도 호가
            print('====================매수 시도====================')
            slackBot.message("#매수 주문\n매수 주문 가격 : " + str(buy_price) + "원")

    def sell_coin(self) :
        self.buy_yn = False
        balance = upbit.get_balance(self.ticker) # 잔고 조회

        upbit.sell_market_order(ticker, balance)

        sell_price = pyupbit.get_orderbook(self.ticker)['orderbook_units'][0]['bid_price'] # 최우선 매수 호가
        print('====================매도 시도====================')
        slackBot.message("#매도 주문\n매도 주문 가격 : " + str(sell_price) + "원")

class slack :
    def __init__(self, token, channel) :
        self.token = token
        self.channel = channel
        self.client = WebClient(token=token)

    def message(self, message):
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message
            )
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")

upbit = pyupbit.Upbit(acc_key, sec_key)
slackBot = slack(appToken, channel)

start_cash = upbit.get_balance()
ticker = "KRW-ETH"

tradingBot = autoTrade(start_cash, ticker)
tradingBot.start()

print(start_cash)
print("프로그램 실행!")

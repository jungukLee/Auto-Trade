import pyupbit
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime

class BackTesting:
    def __init__(self, daily_data, start_cash):
        self.daily_data = daily_data  # 일봉 데이터
        self.fee = 0.0011  # 수수료
        self.buy_signal = False  # 매수 신호

        self.start_cash = start_cash  # 시작 자산
        self.current_cash = start_cash  # 현재 자산
        self.highest_cash = start_cash  # 자산 최고점
        self.lowest_cash = start_cash  # 자산 최저점

        self.ror = 1  # 수익률
        self.accumulated_ror = 1  # 누적 수익률
        self.mdd = 0  # 최대 낙폭

        self.trade_count = 0  # 거래횟수
        self.win_count = 0  # 승리횟수

        #시각화 데이터
        self.buy_dates = []
        self.buy_prices = []
        self.sell_dates = []
        self.sell_prices = []

    def execute(self):
        # 노이즈 계산 (1 - 절대값(시가 - 종가) / (고가 - 저가))
        self.daily_data['noise'] = 1 - abs(self.daily_data['open'] - self.daily_data['close']) / (self.daily_data['high'] - self.daily_data['low'])
        # 노이즈 20일 평균
        self.daily_data['noise_ma20'] = self.daily_data['noise'].rolling(window=20, min_periods=1).mean()

        # 변동폭 (고가 - 저가)
        self.daily_data['range'] = self.daily_data['high'] - self.daily_data['low']
        # 목표 매수가 (시가 + 변동폭 * 노이즈 평균)
        self.daily_data['targetPrice'] = self.daily_data['open'] + self.daily_data['range'].shift(1) * self.daily_data['noise_ma20']
        # 5일 이동평균선
        self.daily_data['ma5'] = self.daily_data['close'].rolling(window=5, min_periods=1).mean().shift(1)
        # 상승장 여부
        self.daily_data['bull'] = self.daily_data['open'] > self.daily_data['ma5']

        holding = False  # 보유 상태
        buy_price = 0  # 매수 가격

        for idx, row in self.daily_data.iterrows():
            # 매수 신호 확인
            if row['targetPrice'] <= row['high'] and row['bull']:
                if not holding:
                    holding = True
                    buy_price = row['targetPrice']
                    self.trade_count += 1

                    #시각화
                    self.buy_dates.append(idx)
                    self.buy_prices.append(buy_price)

                    print(f"매수: {row.name}, 목표가: {buy_price}")

            # 매도 신호 확인
            if holding and (row['close'] < buy_price or row['targetPrice'] > row['high']):
                holding = False
                self.ror = (row['close'] / buy_price) - self.fee
                self.win_count += 1 if self.ror > 1 else 0
                self.accumulated_ror *= self.ror
                self.current_cash *= self.ror

                self.highest_cash = max(self.highest_cash, self.current_cash)
                self.lowest_cash = min(self.lowest_cash, self.current_cash)
                dd = (self.highest_cash - self.current_cash) / self.highest_cash * 100
                self.mdd = max(self.mdd, dd)

                #시각화
                self.sell_dates.append(idx)
                self.sell_prices.append(row['close'])
                print(f"매도: {row.name}, 가격: {row['close']}")

        self.result()
        self.visualize()


    def result(self):
        print()
        print('='*40)
        print('테스트 결과')
        print('-'*40)
        print(f'총 거래 횟수 : {self.trade_count}')
        print(f'승리 횟수 : {self.win_count}')
        print(f'승률 : {self.win_count / self.trade_count * 100:.2f}%')
        print(f'누적 수익률 : {self.accumulated_ror:.2f}')
        print(f'현재 잔액 : {self.current_cash:.2f}')
        print(f'최고 잔액 : {self.highest_cash:.2f}')
        print(f'최저 잔액 : {self.lowest_cash:.2f}')
        print(f'최대 낙폭 (MDD) : {self.mdd:.2f}%')
        print('='*40)

    def visualize(self):
        plt.figure(figsize=(14, 7))
        plt.plot(self.daily_data['close'], label='Close Price', color='black')
        plt.scatter(self.buy_dates, self.buy_prices, marker='^', color='blue', label='Buy Signal', alpha=1)
        plt.scatter(self.sell_dates, self.sell_prices, marker='v', color='red', label='Sell Signal', alpha=1)
        plt.title('Bitcoin Price Backtesting')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid()
        plt.show()



# 날짜 범위 설정
#from_date = datetime.datetime(2017, 11, 1)
#to_date = datetime.datetime(2023, 1, 1)

# 비트코인 이력 불러오기
#df = pyupbit.get_ohlcv_from(ticker="KRW-BTC", fromDatetime=from_date, to=to_date)

# 데이터와 백테스트 실행
df = pyupbit.get_ohlcv("KRW-ETH", count=700)  # 일봉 데이터
backtest = BackTesting(df, 1000000)
backtest.execute()
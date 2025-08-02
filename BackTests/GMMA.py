import pyupbit
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime

class BackTestingGMMA:
    def __init__(self, minute_data, start_cash):
        self.minute_data = minute_data  # 5분봉 데이터
        self.fee = 0.0011  # 수수료

        self.start_cash = start_cash  # 시작 자산
        self.current_cash = start_cash  # 현재 자산
        self.highest_cash = start_cash  # 자산 최고점
        self.lowest_cash = start_cash  # 자산 최저점

        self.ror = 1  # 수익률
        self.accumulated_ror = 1  # 누적 수익률
        self.mdd = 0  # 최대 낙폭

        self.trade_count = 0  # 거래횟수
        self.win_count = 0  # 승리횟수

        # 시각화 데이터
        self.buy_dates = []
        self.buy_prices = []
        self.sell_dates = []
        self.sell_prices = []

    def calculate_gmma(self):
        # 5분봉에서의 이동평균선 기간
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

    def execute(self):
        self.calculate_gmma()

        holding = False  # 보유 상태
        buy_price = 0  # 매수 가격

        for idx, row in self.minute_data.iterrows():
            # 매수 신호 확인
            if row['ma3'] > row['ma5'] and row['ma5'] > row['ma8'] and row['ma8'] > row['ma10'] and row['ma10'] > row['ma12'] and row['ma12'] > row['ma15']:
                if not holding:
                    holding = True
                    buy_price = row['close']
                    self.trade_count += 1

                    # 시각화
                    self.buy_dates.append(idx)
                    self.buy_prices.append(buy_price)

                    print(f"매수: {row.name}, 가격: {buy_price}")

            # 매도 신호 확인
            if holding and (row['ma3'] < row['ma5'] or row['ma5'] < row['ma8'] or row['ma8'] < row['ma10'] or row['ma10'] < row['ma12'] or row['ma12'] < row['ma15']):
                holding = False
                self.ror = (row['close'] / buy_price) - self.fee
                self.win_count += 1 if self.ror > 1 else 0
                self.accumulated_ror *= self.ror
                self.current_cash *= self.ror

                self.highest_cash = max(self.highest_cash, self.current_cash)
                self.lowest_cash = min(self.lowest_cash, self.current_cash)
                dd = (self.highest_cash - self.current_cash) / self.highest_cash * 100
                self.mdd = max(self.mdd, dd)

                # 시각화
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
        plt.plot(self.minute_data['close'], label='Close Price', color='black', linewidth=0.5)
        
        # 단기 이동평균선 시각화
        plt.plot(self.minute_data['ma3'], label='MA 3', color='blue', linewidth=0.8)
        plt.plot(self.minute_data['ma8'], label='MA 8', color='green', linewidth=0.8)
        plt.plot(self.minute_data['ma12'], label='MA 12', color='purple', linewidth=0.8)
        plt.plot(self.minute_data['ma15'], label='MA 15', color='red', linewidth=0.8)
        
        plt.scatter(self.buy_dates, self.buy_prices, marker='^', color='blue', label='Buy Signal', alpha=1, s=70)
        plt.scatter(self.sell_dates, self.sell_prices, marker='v', color='red', label='Sell Signal', alpha=1, s=70)
        
        plt.title('GMMA Backtesting (5 Min)')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend(loc='upper left')
        plt.grid()
        plt.show()


# from_date = datetime.datetime(2021, 11, 1)
# to_date = datetime.datetime(2023, 1, 1)

# 비트코인 이력 불러오기
# df = pyupbit.get_ohlcv_from(ticker="KRW-BTC", interval="minute5", fromDatetime=from_date, to=to_date)

df = pyupbit.get_ohlcv("KRW-ETH", interval="minute5", count=180*288)
backtest = BackTestingGMMA(df, 1000000)
backtest.execute()

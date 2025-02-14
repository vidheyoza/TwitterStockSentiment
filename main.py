import datetime as dt
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
from sklearn import preprocessing
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import yfinance as yf
import tweepy
from textblob import TextBlob

import constants as ct
from Tweet import Tweet

style.use('ggplot')


def check_stock_symbol(companies_file='nasdaq_list.csv'):
    df = pd.read_csv(companies_file)
    ticker = 'AAPL'
    c_name = ''

    while c_name == '':
        ticker = input('Enter a stock symbol to retrieve data from: ').upper()
        for index in range(len(df)):
            if df['Symbol'][index] == ticker:
                c_name = df['Name'][index]

    return c_name, ticker


def get_stock_data(ticker, from_date, to_date):
    data = yf.download(tickers=ticker, start=from_date, end=to_date)
    df = pd.DataFrame(data=data)

    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df['HighLoad'] = (df['High'] - df['Close']) / df['Close'] * 100.0
    df['Change'] = (df['Close'] - df['Open']) / df['Open'] * 100.0

    df = df[['Close', 'HighLoad', 'Change', 'Volume']]
    return df


def stock_forecasting(df):
    forecast_col = 'Close'
    forecast_out = int(math.ceil(0.1 * len(df)))
    df['Label'] = df[[forecast_col]].shift(-forecast_out)

    X = np.array(df.drop(['Label'], axis=1))
    X = preprocessing.scale(X)
    X_forecast = X[-forecast_out:]
    X = X[:-forecast_out]

    df.dropna(inplace=True)
    y = np.array(df['Label'])

    # print(X)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5)

    clf = LinearRegression(n_jobs=-1)
    clf.fit(X_train, y_train)
    accuracy = clf.score(X_test, y_test)
    forecast = clf.predict(X_forecast)

    df['Prediction'] = np.nan

    last_date = df.iloc[-1].name
    last_date = dt.datetime.strptime(str(last_date), "%Y-%m-%d %H:%M:%S")

    # print(df.index)

    for pred in forecast:
        last_date += dt.timedelta(days=1)
        df.loc[last_date.strftime("%Y-%m-%d")] = [np.nan for _ in range(len(df.columns) - 1)] + [pred]
    return df, forecast_out


def forecast_plot(df, ticker):
    plt.plot(df.index, df['Close'], color='black', label='Close')
    plt.plot(df.index, df['Prediction'], color='green', label='Prediction')

    plt.legend()
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.xticks(rotation=90)

    plt.savefig('plots/' + ticker + '.png', bbox_inches='tight')
    plt.show()


def retrieving_tweets_polarity(query):
    auth = tweepy.OAuthHandler(ct.consumer_key, ct.consumer_secret)
    auth.set_access_token(ct.access_token, ct.access_token_secret)
    user = tweepy.API(auth)

    tweets = tweepy.Cursor(user.search, q=str(query), tweet_mode='extended', lang='en').items(ct.num_of_tweets)

    tweet_list = []
    global_polarity = 0
    for tweet in tweets:
        tw = tweet.full_text
        blob = TextBlob(tw)
        polarity = 0
        for sentence in blob.sentences:
            polarity += sentence.sentiment.polarity
            global_polarity += sentence.sentiment.polarity
        tweet_list.append(Tweet(tw, polarity))
        print(Tweet(tw, polarity))
        # print("Polarity: ", polarity)

    global_polarity = global_polarity / len(tweet_list)
    return global_polarity


def recommending(df, forecast_out, global_polarity):
    print('Market Sentiment: ', global_polarity)
    if df.iloc[-forecast_out - 1]['Close'] < df.iloc[-1]['Prediction']:
        if global_polarity > 0:
            print(
                "According to the predictions and twitter sentiment analysis -> Investing in %s is a GREAT idea!" % str(
                    symbol))
        elif global_polarity < 0:
            print("According to the predictions and twitter sentiment analysis -> Investing in %s is a BAD idea!" % str(
                symbol))
    else:
        print("According to the predictions and twitter sentiment analysis -> Investing in %s is a BAD idea!" % str(
            symbol))


if __name__ == "__main__":
    (company_name, symbol) = check_stock_symbol()
    if company_name != '':
        # Setup timeline from today till 2 years ago
        actual_date = dt.date.today()
        past_date = actual_date - dt.timedelta(days=(365 * 2))
        actual_date = actual_date.strftime("%Y-%m-%d")
        past_date = past_date.strftime("%Y-%m-%d")

        print("Retrieving Stock Data from introduced symbol...")
        dataframe = get_stock_data(symbol, past_date, actual_date)

        print("Forecasting stock DataFrame...")
        (dataframe, forecast_price) = stock_forecasting(dataframe)

        print("Plotting existing and forecasted values...")
        forecast_plot(dataframe, symbol)

        print("Retrieving %s related tweets polarity..." % symbol)
        polarity = retrieving_tweets_polarity(company_name)

        print("Generating recommendation based on prediction & polarity...")
        recommending(dataframe, forecast_price, polarity)

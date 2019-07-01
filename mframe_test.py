import unittest
from mframe import DataFrame, Series, parse_date, IS_JYTHON
import datetime as dt
import time
from tabulate import tabulate


def jython_only(f):
    def wrapper(*args, **kwargs):
        if IS_JYTHON:
            f(*args, **kwargs)
    return wrapper


def str_to_dt(s):
    return dt.datetime.strptime(s, '%Y-%m-%d')


def str_to_java_date(s):
    from java.text import SimpleDateFormat
    return SimpleDateFormat('yyy-MM-dd').parse(s)


def to_float(f):
    return float(f)


tickers = {
    'tick': [
        'aapl', 'goog', 'msft',
        'aapl', 'goog', 'msft',
        'aapl', 'goog', 'msft',
        'aapl', 'goog', 'msft',
        'aapl', 'goog', 'msft',
        'aapl', 'goog', 'msft',
    ],
    'date': [
        '2019-01-01', '2019-01-01', '2019-01-01',
        '2019-01-02', '2019-01-02', '2019-01-02',
        '2019-01-03', '2019-01-03', '2019-01-03',
        '2019-01-04', '2019-01-04', '2019-01-04',
        '2019-01-05', '2019-01-05', '2019-01-05',
        '2019-01-06', '2019-01-06', '2019-01-06'
    ],
    'price': [
        '100', 123, 45.67,
        100.10, 125, 45,
        '100.35', 124, 46,
        105, '123', '47',
        106, 123.50, 45,
        105, 122.50, 45,
    ],
}

positions = {
    'tick': [
        'aapl', 'goog', 'msft',
        'aapl', 'goog', 'msft',
        'aapl', 'goog', 'msft',
        'aapl', 'goog', 'msft', 
    ],
    'position': [
        'open   ', 'close      ', 'close   ',
        'close   ', 'close      ', 'open',
        'open   ', 'close      ', 'open',
        'close   ', 'close      ', 'open   ',
    ],
    'date': [
        '2019-01-01', '2019-01-01', '2019-01-01',
        '2019-01-03', '2019-01-02', '2019-01-02',
        '2019-01-04', '2019-01-03', '2019-01-04',
        '2019-01-06', '2019-01-05', '2019-01-06',
    ],
}

expected_result = [
 {'tick': 'aapl', 'date': '2019-01-01', 'price': 100, 'position': 'open'},
 {'tick': 'goog', 'date': '2019-01-01', 'price': 123, 'position': 'close'},
 {'tick': 'msft', 'date': '2019-01-01', 'price': 45.67, 'position': 'close'},
 {'tick': 'aapl', 'date': '2019-01-02', 'price': 100.1, 'position': 'open'},
 {'tick': 'goog', 'date': '2019-01-02', 'price': 125, 'position': 'close'},
 {'tick': 'msft', 'date': '2019-01-02', 'price': 45, 'position': 'open'},
 {'tick': 'aapl', 'date': '2019-01-03', 'price': 100.35, 'position': 'close'},
 {'tick': 'goog', 'date': '2019-01-03', 'price': 124, 'position': 'close'},
 {'tick': 'msft', 'date': '2019-01-03', 'price': 46, 'position': 'open'},
 {'tick': 'aapl', 'date': '2019-01-04', 'price': 105, 'position': 'open'},
 {'tick': 'goog', 'date': '2019-01-04', 'price': 123, 'position': 'close'},
 {'tick': 'msft', 'date': '2019-01-04', 'price': 47, 'position': 'open'},
 {'tick': 'aapl', 'date': '2019-01-05', 'price': 106, 'position': 'open'},
 {'tick': 'goog', 'date': '2019-01-05', 'price': 123.5, 'position': 'close'},
 {'tick': 'msft', 'date': '2019-01-05', 'price': 45, 'position': 'open'},
 {'tick': 'aapl', 'date': '2019-01-06', 'price': 105, 'position': 'close'},
 {'tick': 'goog', 'date': '2019-01-06', 'price': 122.5, 'position': 'close'},
 {'tick': 'msft', 'date': '2019-01-06', 'price': 45, 'position': 'open'}
]


class TestDataFrame(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame(tickers)
        self.pdf = DataFrame(positions)

    def test_apply(self):
        for date in self.df.get('date'):
            self.assertIsInstance(date, str)        
        self.df['date'] = self.df['date'].apply(str_to_dt)
        for date in self.df['date']:
            self.assertIsInstance(date, dt.datetime)  

    def test_get(self):
        items = self.df.get('price')
        for price, expected in zip(items, expected_result):
            self.assertEqual(str(price), str(expected['price']))

    def test_set(self):
        self.df.set([True]*len(self.df), 'position', None)
        for item in self.df.get('position'):
            self.assertIsNone(item)
        self.df.set('all', 'position1', None)
        for item in self.df.get('position1'):
            self.assertIsNone(item)
        try:
            self.df.unknown = 2
            self.fail('Should not be able to set attributes')
        except AttributeError:
            pass

    def test_iterrows(self):
        rows = list(self.pdf.iterrows())
        self.assertEqual(12, len(rows))
        self.assertEqual('aapl', rows[0]['tick'])
        self.assertEqual('msft', rows[5]['tick'])


class TestDataFrameSugar(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame(tickers)
        self.pdf = DataFrame(positions)

    def test_get(self):
        # Dict access
        items = self.df['price']
        self.assertIsInstance(items, Series)
        for price, expected in zip(items, expected_result):
            self.assertEqual(str(price), str(expected['price']))
        # Attribute access
        items = self.df.tick
        self.assertIsInstance(items, Series)
        for tick, expected in zip(items, expected_result):
            self.assertEqual(tick, expected['tick'])

    def test_set(self):
        # Dict setting
        self.df['position'] = None
        for item in self.df['position']:
            self.assertIsNone(item)
        # Set a list
        self.df['position'] = ['open']*len(self.df)
        for item in self.df['position']:
            self.assertEqual(item, 'open')

    def test_filter(self):
        results = self.df['date'] == '2019-01-02'
        self.assertListEqual(
            [False]*3 + [True]*3 + [False]*12,
            list(results)
        )
        results = self.df['date'] >= '2019-01-02'
        self.assertListEqual(
            [False]*3 + [True]*15,
            list(results)
        )

        self.assertEqual(18, len(self.df))
        df = self.df[self.df['date'] >= '2019-01-03']
        self.assertEqual(12, len(df))
        self.assertListEqual(
            ['2019-01-03', '2019-01-03', '2019-01-03','2019-01-04', '2019-01-04', '2019-01-04','2019-01-05', '2019-01-05', '2019-01-05','2019-01-06', '2019-01-06', '2019-01-06'],
            list(df['date']),
        )

        df = self.df[(self.df['date'] >= '2019-01-02') & (self.df['date'] <= '2019-01-04')]
        self.assertEqual(9, len(df))
        self.assertListEqual(
            ['2019-01-02', '2019-01-02', '2019-01-02','2019-01-03', '2019-01-03', '2019-01-03','2019-01-04', '2019-01-04', '2019-01-04'],
            list(df['date']),
        )        

    def test_drop(self):
        results = self.df['date'] == '2019-01-02'
        self.assertEqual(18, len(self.df))
        self.df.drop(results)
        self.assertEqual(15, len(self.df))
        
        results = self.df['date'] == '2019-01-02'
        self.assertEqual(0, len(self.df[results]))

        results = self.df['date'] == '2019-01-01'
        self.assertEqual(3, len(self.df[results]))
        results = self.df['date'] == '2019-01-03'
        self.assertEqual(3, len(self.df[results]))
        results = self.df['date'] == '2019-01-04'
        self.assertEqual(3, len(self.df[results]))
        results = self.df['date'] == '2019-01-05'
        self.assertEqual(3, len(self.df[results]))
        results = self.df['date'] == '2019-01-06'
        self.assertEqual(3, len(self.df[results]))

    def test_drop_all(self):
        self.df.drop('all')
        self.assertEqual(0, len(self.df))        

    def test_contains(self):
        self.assertIn('date', self.df)
        self.assertNotIn('season', self.df)

    def test_features(self):
        self.df['date'] = self.df['date'].apply(str_to_dt)
        self.df['price'] = self.df['price'].apply(to_float)
        
        self.pdf['date'] = self.pdf['date'].apply(str_to_dt)        
        self.pdf['position'] = self.pdf['position'].apply(lambda x: x.strip())
        
        for row in self.pdf.iterrows():    
            sset = (self.df['date'] >= row['date']) & (self.df['tick'] == row['tick'])
            self.df.set(sset, 'position', row['position'])

        for actual, expected in zip(self.df.iterrows(), expected_result):
            self.assertEqual(actual['tick'], expected['tick'])
            self.assertEqual(actual['price'], expected['price'])
            self.assertEqual(actual['position'], expected['position'])


class TestTimeSeries(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame(tickers)
        self.df['date'] = self.df['date'].apply(str_to_dt)

    def test_parse_date(self):
        dates = [ 
            '2019-26-06', 
            '26-06-2019',
            '2019-06-26',
            '2019-06-26T10:54:55',
            '2019-06-26T10:54:55Z',
            '20190626T105455Z',
            '2019-01-01 00:00:00',
        ]
        for date in dates:
            try:
                parse_date(date)
            except:
                self.fail('Should have parsed {} correctly'.format(date))
        try:
            parse_date('31-31-31')
            self.fail('Should have raised a TypeError')
        except TypeError:
            pass


    def test_filter_with_string_dates(self):
        d3 = dt.datetime(2019, 1, 3, 0, 0)
        d4 = dt.datetime(2019, 1, 4, 0, 0)
        d5 = dt.datetime(2019, 1, 5, 0, 0)
        d6 = dt.datetime(2019, 1, 6, 0, 0)

        df = self.df[self.df['date'] >= '2019-01-03']
        self.assertEqual(12, len(df))
        self.assertListEqual(
            [d3]*3 + [d4]*3 + [d5]*3 + [d6]*3,
            list(df['date']),
        )


class TestJavaTimeSeries(unittest.TestCase):
    def setUp(self):
        self.df = DataFrame(tickers)

    @jython_only
    def test_filter_with_java_date(self):
        from java.util import GregorianCalendar, Calendar

        self.df['date'] = self.df['date'].apply(str_to_dt)
        date = GregorianCalendar(2019, Calendar.JANUARY, 3).getTime()

        d3 = dt.datetime(2019, 1, 3, 0, 0)
        d4 = dt.datetime(2019, 1, 4, 0, 0)
        d5 = dt.datetime(2019, 1, 5, 0, 0)
        d6 = dt.datetime(2019, 1, 6, 0, 0)

        df = self.df[self.df['date'] >= date]
        self.assertEqual(12, len(df))
        self.assertListEqual(
            [d3]*3 + [d4]*3 + [d5]*3 + [d6]*3,
            list(df['date']),
        )        

    @jython_only
    def test_filter_with_java_dates(self):
        from java.util import GregorianCalendar, Calendar
        self.df['date'] = self.df['date'].apply(str_to_java_date)

        d3 = GregorianCalendar(2019, Calendar.JANUARY, 3).getTime()
        d4 = GregorianCalendar(2019, Calendar.JANUARY, 4).getTime()
        d5 = GregorianCalendar(2019, Calendar.JANUARY, 5).getTime()
        d6 = GregorianCalendar(2019, Calendar.JANUARY, 6).getTime()

        df = self.df[self.df['date'] >= '2019-01-03']
        self.assertEqual(12, len(df))
        self.assertListEqual(
            [d3]*3 + [d4]*3 + [d5]*3 + [d6]*3,
            list(df['date']),
        ) 


if __name__ == '__main__':
    unittest.main()
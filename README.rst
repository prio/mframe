============================
MFrame - A minimal DataFrame
============================


A lightweight single file DataFrame implementation that works on older Python distrubtions such as Jython.

I use it with Java data tools such as `Streamsets <https://streamsets.com/>`_.

Feel free to fork, add tests and features and make a pull request.

Install
=======


 $ pip install mframe


or copy mframe.py to your project folder.

Usage
=====

It's goal is to be familar to pandas users without promising 100% compatability. My workflow usually involves writing the code in a Jupyter notebook using Python 3 and then testing it with Jython before deploying it to Streamsets.


    >>> from mframe import DataFrame
    >>> data = {'col_1': [3, 2, 1, 0], 'col_2': ['a', 'b', 'c', 'd']}
    >>> df = DataFrame(data)
    >>> df
    {'col_1': [3, 2, 1, 0], 'col_2': ['a', 'b', 'c', 'd']}

    >>> df.pd #  the pd alias returns a pandas dataframe, useful for printing in Jupyter when developing
         col_1 col_2
    0      3     a
    1      2     b
    2      1     c
    3      0     d

    >>> df['col_1'] # Subscript access
    [3, 2, 1, 0]

    >>> df.col_1 # Attribute access
    [3, 2, 1, 0]

    >>> df[df.col_1 > 1] # filtering works
         col_1 col_2
    0      3     a
    1      2     b
    >>> df[(df.col_1 > 1) & (df.col_2 == 'a')]
         col_1 col_2
    0      3     a

    >>> df['col_1'] = df.col_1.apply(str) # Apply is available
    >>> df.col_1
    ['3', '2', '1', '0']

    >>> list(df.iterrows()) # returns a generator of dictionaries
    [{'col_1': '3', 'col_2': 'a'}, {'col_1': '2', 'col_2': 'b'}, {'col_1': '1', 'col_2': 'c'}, {'col_1': '0', 'col_2': 'd'}]

Tested on
=========

- Python 3.7
- Jython 2.7
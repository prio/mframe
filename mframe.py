import operator
import types
import datetime as dt


IS_JYTHON = False
try:
    import java.util.Date as JavaDate
    IS_JYTHON = True
except ImportError:
    pass


def parse_date(sdt):
    if isinstance(sdt, dt.datetime):
        return sdt
    if IS_JYTHON and isinstance(sdt, JavaDate):
        return dt.datetime.fromtimestamp(sdt.getTime()/1000)

    # Limited support to guess datetime formats
    patterns = [
        '%Y-%m-%d', '%Y-%d-%m', '%d-%m-%Y',
        '%Y-%m-%d %H:%M:%S',
        # ISO 8601, offset (%z) not supported in Jython :(
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y%m%dT%H%M%SZ',
    ]
    for pattern in patterns:
        try:
            return dt.datetime.strptime(sdt, pattern)
        except:
            pass
    raise TypeError("{} is not a recognized datetime format".format(sdt))


class Series:
    __slots__ = ['data', 'dtype']

    def __init__(self, data):
        self.data = data
        self.dtype = self._dtype()

    def _dtype(self):
        if len(self) > 0:
            if isinstance(self.data[0], dt.datetime) or (IS_JYTHON and isinstance(self.data[0], JavaDate)):
                return 'datetime'
        return 'object'

    def __iter__(self):
        return iter(self.data)

    def _dt_conversion(self, other):
        if isinstance(other, (list, Series)):
            return [parse_date(o) for o in other]
        else:
            return parse_date(other)

    def _compare(self, other, op):
        if self.dtype == 'datetime':
            other = self._dt_conversion(other)
        if isinstance(other, (list, Series)):
            return op(self.data, other)
        else:
            return Series([op(data, other) for data in self.data])

    def _operator_apply(self, other, op_, reverse=False):
        if reverse:
            op = lambda x, y: op_(y, x)
        else:
            op = op_

        _values = []
        if isinstance(other, (list, Series)):
            for s, o in zip(self.data, other):
                _values.append(op(s, o))
        else:
            _values = [op(s, other) for s in self.data]
        return Series(_values)

    def apply(self, fn):
        self.data = [fn(value) for value in self.data]
        return Series(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

    def __eq__(self, other):
        return self._compare(other, operator.eq)

    def __ge__(self, other):
        return self._compare(other, operator.ge)

    def __gt__(self, other):
        return self._compare(other, operator.gt)

    def __le__(self, other):
        return self._compare(other, operator.le)

    def __lt__(self, other):
        return self._compare(other, operator.lt)

    def __and__(self, other):
        return Series([all([b1, b2]) for b1, b2 in zip(self.data, other)])

    def __add__(self, other):
        return self._operator_apply(other, operator.add)

    def __sub__(self, other):
        return self._operator_apply(other, operator.sub)

    def __mul__(self, other):
        return self._operator_apply(other, operator.mul)

    def __div__(self, other):
        return self._operator_apply(other, operator.truediv)

    def __truediv__(self, other):
        return self._operator_apply(other, operator.truediv)

    def __rdiv__(self, other):
        return self._operator_apply(other, operator.truediv, reverse=True)

    def __rtruediv__(self, other):
        return self._operator_apply(other, operator.truediv, reverse=True)

    def __rsub__(self, other):
        return self._operator_apply(other, operator.sub, reverse=True)

    def __rmul__(self, other):
        return self._operator_apply(other, operator.mul)

    def __radd__(self, other):
        return self._operator_apply(other, operator.add)

    def __round__(self, value):
        self.data = [round(x, value) for x in self.data]
        return self

    def __abs__(self):
        _data = [abs(x) for x in self.data]
        return Series(_data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return str(self.data)


class DataFrame(object):
    # As the dataframe object does not allow setting columns via
    # attribute access, we take some pre-cautions to prevent it
    # happening accidently.
    __slots__ = ['data', '_values', '_columns', '_selected_column'] # Python 3

    # __slots__ not supported in Jython
    def _slot(self, attr, value):
        super(DataFrame, self).__setattr__(attr, value)

    def __setattr__(self, name, value):
        raise AttributeError('{} is an unknown attribute'.format(name))
    #########

    def __init__(self, data=None, values=None, columns=None):
        if data is None:
            data = {column: [] for column in columns}
            for row in values:
                for i, column in enumerate(columns):
                    data[column].append(row[i])
        # TODO Test shape
        self._slot('_values', list(data.values()))
        self._slot('_columns', list(data.keys()))

    def _get(self, column):
        if isinstance(column, list): # Multiple select
            return DataFrame({c: self.get(c) for c in column})
        if isinstance(column, Series): # Filter
            _vals = [[] for _ in range(len(self._values))] # Empty list of lists
            for i, value in enumerate(column):
                if value:
                    for j, value in enumerate(self._values):
                        _vals[j].append(value[i])
            return DataFrame(values=list(map(list, zip(*_vals))), columns=self._columns)

        idx = self._columns.index(column)
        return Series(self._values[idx])

    def get(self, column, default=None):
        try:
            return self._get(column)
        except ValueError:
            return Series([default]*len(self))

    def _get_row_filter(self, mask):
        if isinstance(mask, str) and mask == 'all':
            return [True]*len(self)
        if isinstance(mask[0], list):
            _index = []
            for items in zip(*mask):
                if all(items):
                    _index.append(True)
                else:
                    _index.append(False)
            mask = _index
        return mask

    def drop(self, mask):
        mask = self._get_row_filter(mask)
        _values = []
        for row in self._values:
            _row_values = []
            for i, remove in enumerate(mask):
                if not remove:
                    _row_values.append(row[i])
            _values.append(_row_values)
        self._slot('_values', _values)

    def set(self, mask, column, value):
        mask = self._get_row_filter(mask)
        _values = []
        try:
            idx = self._columns.index(column)
        except ValueError: # Add New Column
            self._columns.append(column)
            idx = self._columns.index(column)
            self._values.append([None]*len(self))

        for i, (should_apply, current_value) in enumerate(zip(mask, self._values[idx])):
            if should_apply:
                if isinstance(value, (Series, list)):
                    _values.append(value[i])
                else:
                    _values.append(value)
            else:
                _values.append(current_value)
        self._values[idx] = _values

    def iterrows(self):
        for i in range(len(self)):
            row = {}
            for j in range(len(self._columns)):
                row[self._columns[j]] = self._values[j][i]
            yield row

    def to_dict(self):
        d = {}
        for idx, column in enumerate(self._columns):
            d[column] = self._values[idx]
        return d

    def to_pandas(self):
        import pandas
        return pandas.DataFrame(self.to_dict())

    def pivot(self, index, columns, values):
        iidx = self._columns.index(index)
        cidx = self._columns.index(columns)
        vidx = self._columns.index(values)
        _values = { index: set() }
        for column in self._values[cidx]:
            _values[column] = []
        for idx, col, val in zip(self._values[iidx], self._values[cidx], self._values[vidx]):
            _values[index].add(idx)
            _values[col].append(val)
        return DataFrame(_values)

    def pivot_table(self, index, values, columns, fill_value=None):
        # Build shape
        _values = {}
        for i in index:
            _values[i] = []
        for value_column in values:
            for c in columns:
                cidx = self._columns.index(c)
                for column in self._values[cidx]:
                    _values['{}_{}'.format(value_column, column)] = []

        for column in columns:
            column_values = set(self[column])
            combos = set()
            for index_values in zip(*self.get(index)._values):
                if index_values not in combos: # Make sure we dont revist the same index combination
                    combos.add(index_values)
                    
                    filters = []
                    for idx, idx_val in zip(index, index_values):
                        filters.append((self[idx] == idx_val)) # Filter by each index value
                        _values[idx].append(idx_val) # and add index values while looping

                    # Combine filter results (list of bools) into 1 filter
                    combined_filters = []
                    for pair in zip(*filters):
                        combined_filters.append(all(pair))
                    # Get the filtered subset
                    sset = self[Series(combined_filters)]

                    for column_value in column_values:
                        for value_column in values:
                            value = sset[sset[column] == column_value][value_column]
                            if len(value) > 0:
                                value = value[0]
                            else:
                                value = fill_value
                            _values['{}_{}'.format(value_column, column_value)].append(value)

        return DataFrame(_values)

    @property
    def pd(self):
        return self.to_pandas()

    def head(self, num=5):
        from tabulate import tabulate
        cut_values = zip(*[v[:num] for v in self._values])
        return tabulate(cut_values, headers=self._columns)

    def tail(self, num=5):
        from tabulate import tabulate
        cut_values = zip(*[v[len(v)-num:] for v in self._values])
        return tabulate(cut_values, headers=self._columns)

    def __getitem__(self, name):
        return self._get(name)

    def __setitem__(self, name, value):
        self.set('all', name, value)

    def __getattr__(self, name):
        return self._get(name)

    def __len__(self):
        if len(self._values) == 0:
            return 0
        return len(self._values[0])

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return str(self.to_dict())

    def __contains__(self, value):
        return value in self._columns

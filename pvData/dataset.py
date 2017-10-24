#! /usr/bin/env python

from .constants import DEFAULT_FOLDER, FileTypes
from .decorators import cast, cached

from os.path import exists, join
from datetime import datetime, date
from os import getenv, listdir, stat
from stat import S_ISDIR

from pandas import tslib as td

import pandas as pd
import numpy as np
import logging
import re

MAX_WATTS=500000

class pvDataSet(object):
    def __init__(self, folder=DEFAULT_FOLDER):
        self._folder = folder
        self._epoch = datetime.utcfromtimestamp(0)

        self._specs = [
            ("consumption", FileTypes.Consumption),
            ("generation", FileTypes.Generation),
            # ("battery", FileTypes.Battery),
        ]

        self._special_labels = [
            ("2016 charge controller degradation 1", "2016-10-31"), # Estimated
            ("2017 charge controller fix 1", "2017-07-19"),
            ("2017 charge controller restoration 1", "2017-07-20"), # Full day after fix

            ("2017 charge controller degradation 2", "2017-08-03"),
            ("2017 charge controller restoration 2", "2017-09-13"),

            ("2017 eclipse", "2017-08-21"),
            ("cloudless day", "2016-10-24"),

            ("2017 spring equinox", "2017-03-20"),
            ("2017 summer solstice", "2017-06-21"),
            ("2017 autumn equinox", "2017-09-22"),
            ("2017 winter solstice", "2017-12-21"),

            ("2018 spring equinox", "2017-03-20"),
            ("2018 summer solstice", "2017-06-21"),
            ("2018 autumn equinox", "2017-09-22"),
            ("2018 winter solstice", "2017-12-21"),
        ]

    @property
    @cached
    def special_dates(self):
        df = self.full

        extra_labels = [
            ("Peak Generation Day", df[df["generation"] == df["generation"].max()]["date"][0].date().strftime("%Y-%m-%d")),
            ("Peak Consumption Day", df[df["consumption"] == df["consumption"].max()]["date"][0].date().strftime("%Y-%m-%d")),
        ]

        return pd.DataFrame(
            [
                [_label, td.parse_datetime_string(_date)]
                for _label, _date
                in self._special_labels + extra_labels
            ],

            columns=[
                "name",
                "date",
            ]
        )

    @property
    @cast(sorted)
    def dates(self):
        for _name in listdir(self._folder):
            if not S_ISDIR(stat(join(self._folder, _name)).st_mode):
                continue

            if not re.match("^[0-9]{4}-[0-9]{2}-[0-9]{2}$", _name):
                continue

            yield _name

    def _read_dataset(self, filename, limit=None):
        df = pd.read_csv(
            filename,
            parse_dates=False,
            # date_parser=lambda _val: pd.to_datetime(_val, unit='s', errors="coerce",),
            names=["timestamp", "value"],
            # index_col=["timestamp"],
            # keep_date_col=True,
            header=None,
        )

        first_date = datetime.utcfromtimestamp(df["timestamp"][0]).date()
    
        # __import__("code").interact(local=dict(globals().items() + locals().items()))

        df.loc[-1, ["timestamp", "value"]] = [
            int(df["timestamp"][0] - 1),
            0.0
        ]

        df.loc[-2, ["timestamp", "value"]] = [
            int((datetime(first_date.year, first_date.month, first_date.day) - self._epoch).total_seconds()),
            0.0
        ]

        for _ in range(2):
            try:
                df["timestamp"] = pd.to_datetime(
                    df["timestamp"],
                    unit='s',
                    errors="coerce",
                    utc=True,
                )

                break
            except OverflowError, _exception:
                pass

            logging.warning("Correcting timestamp error in %s", filename)
            mask = df["timestamp"].apply(lambda _x: len(str(_x)) > 11)
            df.loc[mask, "timestamp"] = df.loc[mask, "timestamp"].apply(lambda _val: int(str(int(_val))[-10:]))
        else:
            raise _exception

        mask = (~df["value"].isnull())

        if limit is not None:
            mask = mask & (df["value"] <= limit)

        df = df[mask]

        df.set_index(keys=["timestamp"], drop=False, inplace=True)

        return df

    def _read_all(self, filetype, limit=None):
        return reduce(
            lambda _df, _newdf: _df.append(_newdf), (
                self._read_dataset(filename=_file, limit=limit)
                for _date in self.dates
                for _file in [join(self._folder, _date, filetype)] if exists(_file)
            )
        )

    @property
    @cached
    def consumption(self):
        return self._read_all(FileTypes.Consumption, limit=MAX_WATTS)

    @property
    @cached
    def generation(self):
        return self._read_all(FileTypes.Generation, limit=MAX_WATTS)

    @property
    @cached
    def battery(self):
        return self._read_all(FileTypes.Battery)

    @property
    def full(self):
        def merge(_df, _newdf):
            return _df.merge(
                _newdf,
                how="outer",
                on=["timestamp"],
                left_index=True,
                right_index=True,
            )

        df = reduce(
            merge, (
                _df
                for _property, _filetype in self._specs
                for _df in [getattr(self, _property).rename(index=str, columns={"value": _property})]
            )
        )

        df["date"] = df["timestamp"].apply(lambda _x: td.Timestamp(td.datetime_date(_x.year, _x.month, _x.day)))
        df["delta_time"] = df["timestamp"].diff(periods=1) / np.timedelta64(1, 's')

        for _label, _ in self._specs:
            logging.warning("Calculating absolute energy for %s", _label)
            joules_key = "{}_joules".format(_label)

            df[joules_key] = (
                (df[_label] * df["delta_time"]) +
                (((df[_label] - df[_label].shift(1)) * df["delta_time"]) / 2)
            )

            df.loc[df["timestamp"] == df["date"], [joules_key]] = [0.0]

        return df

    @property
    @cached
    def daily(self):
        source_df = self.full

        logging.warning("Computing daily statistics")

        df = source_df.groupby(by=["date"]).max().reset_index()

        sum_keys = ["{}_joules".format(_label) for _label, _ in self._specs]

        df[sum_keys] = source_df.groupby(by=["date"]).sum().reset_index()[sum_keys]

        for _label, _ in self._specs:
            df["{}_daily".format(_label)] = df["{}_joules".format(_label)] / 86400

        return df

    @property
    def special_days(self):
        return self.daily.merge(self.special_dates, on=["date"])

    def fetch(self, selection):
        if selection == "total":
            return self.daily

        df = self.full

        for _date in self.special_dates[self.special_dates["name"] == selection]["date"]:
            return df.loc[df["date"] == _date]

        return df.loc[df["date"] == td.parse_datetime_string(selection)]

    def __getitem__(self, key):
        return self.fetch(key)
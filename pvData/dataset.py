#! /usr/bin/env python

from .constants import DEFAULT_DATASET, FileTypes
from .decorators import cast, cached

from os.path import exists, join
from datetime import datetime, date
from os import getenv, listdir, stat
from stat import S_ISDIR

from itertools import chain

from functools import reduce
import pandas as pd
import numpy as np
import logging
import re

MAX_WATTS=500000

class pvDataSet(object):
    def __init__(self, folder=DEFAULT_DATASET):
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
    def folder(self):
        return self._folder

    def sync(self, folder):
        from subprocess import call

        parameters=[
            "rsync",
            "-az",
            # "--delete",
            "{}/".format(folder),
            "{}/".format(self._folder),
        ]

        call(parameters)

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
                [_label, pd.to_datetime(_date)]
#                [_label, td.parse_datetime_string(_date)]
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
            names=["timestamp", "value"],
            header=None,
        )

        first_date = datetime.utcfromtimestamp(df["timestamp"][0]).date()

        # Presume that the dataset is only for one day
        df["date"] = pd.Timestamp(first_date)

        # Append an entry with one second earlier than the first known entry and 0 watts
        df.loc[-1, ["timestamp", "value"]] = [
            int(df["timestamp"][0] - 1),
            0.0
        ]

        # Append an entry for the last second of the day and 0 watts
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
            except OverflowError as _exception:
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
        """ Read entire series of filetype
        """
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
    @cached
    def full(self):
        """ Merge all full length series into single dataset
        """
        def merge(_df, _newdf):
            return _df.merge(
                _newdf.iloc[:, _newdf.columns.difference(["date"])],
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

    def _fetch(self, selection):
        if selection in ("total", "daily"):
            return self.daily

        df = self.full

        for _date in self.special_dates[self.special_dates["name"] == selection]["date"]:
            return df.loc[df["date"] == _date]

        return df.loc[df["date"] == pd.to_datetime(selection)]

    def __getitem__(self, key):
        return self._fetch(key)

    def keys(self):
        return chain(
            (_x for _x, _ in self._special_labels),
            self.daily["date"],
        )

    @staticmethod
    def graphed(df, suffix=""):
        targets = ["consumption", "generation"]

        sources = [
            "{}{}{}".format(_label, "_" if len(suffix) else "", suffix) for _label in targets
        ]

        extra_keys = list(df.keys().intersection(["timestamp", "date", "delta_time"]))

        all_keys = extra_keys + sources

        return df[all_keys].rename(
            index=str,
            columns=dict(zip(sources, targets)),
        )

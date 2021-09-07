#!/usr/bin/env python

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

from stat import S_ISDIR
from os import stat, listdir
from os.path import join, exists
from functools import reduce

PROJECT_PATH = "/".join(
    [
        e[:[_x.startswith("Environment") for _x in e].index(True)]
        for e in [__import__("ipykernel").__file__.split("/")]
    ][0]
)

data_folder = f'{PROJECT_PATH}/Data/pvData'
parquet_path = f'{data_folder}/parquet/pvdata.parquet'

dates = sorted(
    (_date, _path)
    for _date in listdir(data_folder)
    if sum(_e.isdigit() for _e in _date.split("-")) == 3
    for _path in [join(data_folder, _date)]
    if S_ISDIR(stat(_path).st_mode)
)

name_mapping = [
    ("battery", "XBSYS.BATT_BANK1_V.csv"),
    ("load", "XBSYS.LOAD.P.csv"),
    ("pv", "XBSYS.PV.P.csv"),
]

descriptors = [
    [
        (_date, _key, f'{_folder}/{_filename}') for _key, _filename in name_mapping
    ] for _date, _folder in dates
]

def get_df(filename):
    columns=[
        "timestamp",
        "watts",
    ]

    dtype={
        "timestamp": np.int64,
        "watts": np.float64,
    }

    try:
        df = pd.read_csv(
            filename,
            names=columns,
            skip_blank_lines=True,
            # dtype=dtype,
        )

        df = df.dropna().reset_index(drop=True)

        for _key, _type in dtype.items():
            df[_key] = df[_key].astype(_type)
    except FileNotFoundError:
        df = pd.DataFrame(
            {
                _col: pd.Series(dtype=dtype[_col]) for _col in columns
            }
        )

    df = df.dropna().reset_index(drop=True).set_index(
        columns[0],
        drop=True,
    )

    return df

def get_date_set(row_descriptor):
    def get_frames():
        for _, _key, _path in row_descriptor:
            df = get_df(filename=_path).rename(
                columns={"watts": _key}
            )

            yield df

    return reduce(
        lambda _acc, _df: _df if _acc is None else _acc.join(_df, how="outer"),
        get_frames(),
    )

def write_parquet(descriptors, parquet_path):
    writer = None

    for _row in descriptors:
        df = get_date_set(_row)

        if not len(df):
            continue

        table = pa.Table.from_pandas(df)
        print("DATE {} LENGTH {}".format(_row[0][0], len(table)))

        if writer is None:
            writer = pq.ParquetWriter(parquet_path, table.schema)

        try:
            writer.write_table(table)
        except ValueError as _e:
            print("{}".format(_e))
            __import__("code").interact(local=dict(list(globals().items()) + list(locals().items())))

write_parquet(
    descriptors=descriptors[:],
    parquet_path=parquet_path,
)

__import__("code").interact(local=dict(list(globals().items()) + list(locals().items())))

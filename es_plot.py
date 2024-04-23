import json
from pathlib import Path
import pandas as pd

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from scipy import stats
from vdbbench.plot.query_plot import parse_query_results, plot_recall_latency, plot_result


data_ub = pd.read_pickle("final_results/elasticsearch_query_glove_100d_k10.pkl.xz")
data_b = pd.read_pickle("final_results/elasticsearch_query_glove_100d_k10_batched.pkl.xz")


data_ub['batched'] = "Unbatched"
data_b['batched'] = "Batched"
df = pd.concat([data_b, data_ub], ignore_index=True)
df = df[ ['batched'] + [ col for col in df.columns if col != 'batched'] ]

def plot(
    df: pd.DataFrame,
    title: str,
    x: str,
    x_label: str,
    y: str,
    y_label: str,
):
    f, ax = plt.subplots()
    df = df.explode(y)
    sns.lineplot(
        data=df,
        x=x,
        y=y,
        hue="series",
        legend="full",
        ax=ax,
        markers=True,
        style="series",
        sort=False,
        errorbar="ci",
        orient="x",
    )
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend(loc="upper left").set_title(None)
    return f

def plot_latency_ef(
    data: dict | pd.DataFrame,
    name: str = "Elasticsearch",
    group_by: list[str] = ["replica_count"],
    labels: dict[str, str] = {
        "shard_count": "Shard Count",
        "replica_count": "Replica Count",
        "num_candidates": "Num Candidates",
    },
    out_dir: Path = Path("plots"),
):
    out_dir.mkdir(exist_ok=True)
    df = parse_query_results(data)
    df["latency"] = df["latency"] * 1000  # Convert from s to ms
    df["latency"] /= df["batch_size"]
    del df["batch_size"]
    config_columns = df.columns[:df.columns.get_loc("latency")]
    series_columns = [
        c
        for c in config_columns
        if c not in group_by and df[c].nunique() > 1 and c != 'num_candidates'
    ]
    if group_by:
        gb = df.groupby(group_by)
        groups = [gb.get_group((x,)).copy() for x in gb.groups]
    else:
        groups = [df]
    for group in groups:
        plot_name = (
            name
            + " - "
            + ", ".join((f"{labels.get(k, k)} = {group[k].iloc[0]}" if not isinstance(group[k].iloc[0], str) else group[k].iloc[0]) for k in group_by)
        )
        group["series"] = [
            ", ".join((v if isinstance(v, str) else f"{labels.get(k, k)} = {v}") for k, v in zip(series_columns, row))
            for row in group[series_columns].itertuples(index=False)
        ]
        print(plot_name)
        get_linear_regression_coefs(group)
        print()
        f = plot(
            group,
            plot_name,
            "num_candidates",
            "Num Candidates (ef per shard)",
            "latency",
            "Mean Latency per Queried Vector (ms)",
        )
        f.savefig(
            out_dir
            / (name + "_" + "_".join(f"{k}_{group[k].iloc[0]}" for k in group_by))
        )
        plt.close(f)

def get_linear_regression_coefs(df):
    series_values = df["series"].unique()
    for s in series_values:
        sdf = df[df["series"] == s]
        sdf = sdf.explode("latency")
        x = sdf["num_candidates"]
        y = sdf["latency"]
        y = y.astype(float)
        slope, intercept = np.polyfit(x, y, 1)
        print(f"{s}: {slope}x + {intercept}")

plot_latency_ef(df, group_by=["replica_count"])
plot_latency_ef(df, group_by=["shard_count"])
# plot_recall_latency(df[
#     (df['batch_size'] == 100) &
#     (((df['shard_count'] == 1) & (df['replica_count'] == 2)) | ((df['shard_count'] == 3) & (df['replica_count'] == 0)) | ((df['shard_count'] == 2) & (df['replica_count'] == 1)))
#     ], group_by=[])

# Show qq plot at shard_count 1, batch_size 1, replica_count 2, num_candidates 1600
data = df[
    (df['batch_size'] == 1) &
    (df['shard_count'] == 1) &
    (df['replica_count'] == 2) &
    (df['num_candidates'] == 400)
]
f, ax = plt.subplots()
data = data.explode("latency")
data["latency"] = data["latency"].astype(float)
# Filter out outliers (> 4 std dev)
data = data[np.abs(data["latency"] - data["latency"].mean()) <= (4 * data["latency"].std())]
stats.probplot(data["latency"], dist="norm", plot=plt)
# Save to plots/qqplot.png
f.savefig("plots/qqplot.png")

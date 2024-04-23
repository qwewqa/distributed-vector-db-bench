from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np


def plot_result(
    df: pd.DataFrame,
    title: str,
    x: str,
    x_label: str,
    y: str,
    y_label: str,
):
    f, ax = plt.subplots()
    df = df.explode(x)
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
        errorbar=None,
        orient="y",
    )
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend(loc="lower right").set_title(None)
    return f


def plot_recall_latency(
    data: dict | pd.DataFrame,
    name: str = "Elasticsearch",
    vary: str = "num_candidates",
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
    config_columns = df.columns[:df.columns.get_loc("latency")]
    df["latency"] = df["latency"] * 1000  # Convert from s to ms
    series_columns = [
        c
        for c in config_columns
        if c not in group_by and c != vary and df[c].nunique() > 1
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
            + ", ".join(f"{labels.get(k, k)} = {group[k].iloc[0]}" for k in group_by)
        )
        group["series"] = [
            ", ".join(f"{labels.get(k, k)} = {v}" for k, v in zip(series_columns, row))
            for row in group[series_columns].itertuples(index=False)
        ]
        f = plot_result(
            group,
            plot_name,
            "latency",
            "Mean Latency (ms)",
            "recall_mean",
            "Mean Recall",
        )
        f.savefig(
            out_dir
            / (name + "_" + "_".join(f"{k}_{group[k].iloc[0]}" for k in group_by))
        )
        plt.close(f)


def parse_query_results(data: dict | pd.DataFrame) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.copy()
    data = data["data"]
    rows = []
    for data_config in data:
        for group in data_config["groups"]:
            for query in group["queries"]:
                row = {}
                row.update(data_config["data_config"])
                row.update(group["group_config"])
                row.update(query["query_config"])
                for k, v in query.items():
                    if k == "query_config":
                        continue
                    row[k] = np.array(v)
                    row[f"{k}_mean"] = row[k].mean()
                rows.append(row)

    return pd.DataFrame(rows)

# 🧾 Pandas Cheatsheet

A quick reference to all major pandas operations used in **PandasPlayground** – grouped by category for rapid recall.

---

## 📥 Data Loading

```python
pd.read_csv("file.csv")
pd.read_excel("file.xlsx", sheet_name="Sheet1")
pd.read_json("file.json")
pd.read_parquet("file.parquet")
```

---

## 🔍 Data Inspection

```python
df.head(), df.tail()
df.info(), df.describe()
df.shape, df.columns, df.dtypes
df["col"].value_counts(), df.nunique()
```

---

## 🧹 Data Cleaning

```python
df.dropna(), df.fillna()
df.drop(columns=["A", "B"])
df.rename(columns={"old": "new"})
df.duplicated(), df.drop_duplicates()
df.astype({"col": "int"})
```

---

## 🔤 String Operations

```python
df["col"].str.lower(), str.upper()
df["col"].str.contains("pattern")
df["col"].str.replace("old", "new")
df["col"].str.extract(r"(regex)")
```

---

## 🗃️ Filtering & Indexing

```python
df[df["col"] > 10]
df.loc[5:10, ["A", "B"]]
df.iloc[0:5, 1:3]
df.query("col > 10 and other_col < 5")
```

---

## 🧮 Aggregation & Grouping

```python
df.groupby("col").agg({"sales": "sum"})
df.groupby(["A", "B"]).mean()
df.pivot_table(index="Region", columns="Category", values="Sales", aggfunc="sum")
```

---

## 🔗 Merging & Joining

```python
pd.merge(df1, df2, on="key", how="inner")
pd.concat([df1, df2], axis=0)
df.set_index("col"), df.reset_index()
```

---

## 🕒 Time Series

```python
df["Date"] = pd.to_datetime(df["Date"])
df.set_index("Date", inplace=True)
df.resample("M").sum()
df["col"].rolling(window=3).mean()
```

---

## 🛠️ Apply & Map

```python
df["new"] = df["old"].apply(lambda x: x + 1)
df["label"] = df["score"].map({0: "Low", 1: "High"})
```

---

## 🪄 Method Chaining

```python
(df
 .dropna()
 .query("col > 5")
 .assign(new_col=lambda d: d["col"] * 2)
)
```

---

## 💾 Exporting Data

```python
df.to_csv("output.csv", index=False)
df.to_excel("output.xlsx", sheet_name="Cleaned")
df.to_parquet("file.parquet")
```

---

## 📈 Visualization with pandas

```python
df["col"].plot(kind="bar")
df.plot(x="Date", y="Sales", kind="line")
df.boxplot(column="Profit", by="Category")
```

---

## 🧠 Performance Profiling

```python
df.memory_usage(deep=True)
%timeit df["col"].sum()
from memory_profiler import profile
```

---

## ⚙️ Miscellaneous

```python
pd.get_dummies(df, columns=["col"])
df["col"].astype("category")
df.eval("new_col = A + B")
```

---

> ✅ Pro Tip: Combine `.pipe()` with custom functions for cleaner pipelines!

---

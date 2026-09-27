"""A small, dependency-free declarative schema validator for DataFrames.

Schemas double as documentation: :meth:`DataFrameSchema.to_markdown` renders the data
dictionary, so the documented contract and the enforced contract cannot drift apart.

Example:
    >>> schema = DataFrameSchema("people", [Column("age", "int", min=0, nullable=False)])
    >>> report = schema.validate(pd.DataFrame({"age": [3, -1]}))
    >>> report.ok
    False
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

LogicalType = Literal["int", "float", "numeric", "string", "datetime", "bool", "category", "any"]

_TYPE_CHECKS: dict[str, Callable[[pd.Series], bool]] = {
    "int": pd.api.types.is_integer_dtype,
    "float": pd.api.types.is_float_dtype,
    "numeric": lambda s: pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s),
    "string": lambda s: pd.api.types.is_string_dtype(s) or s.dtype == object,
    "datetime": pd.api.types.is_datetime64_any_dtype,
    "bool": pd.api.types.is_bool_dtype,
    "category": lambda s: isinstance(s.dtype, pd.CategoricalDtype),
    "any": lambda s: True,
}


class SchemaError(ValueError):
    """Raised by :meth:`ValidationReport.raise_for_errors` when validation fails."""


@dataclass(frozen=True)
class Column:
    """Contract for a single column."""

    name: str
    dtype: LogicalType = "any"
    description: str = ""
    nullable: bool = True
    unique: bool = False
    min: float | str | None = None
    max: float | str | None = None
    allowed: Sequence[Any] | None = None
    pattern: str | None = None
    coerce_datetime: bool = False

    def rules(self) -> str:
        """Human-readable summary of constraints, used in generated documentation."""
        parts: list[str] = []
        if self.coerce_datetime:
            parts.append("parseable as datetime")
        if not self.nullable:
            parts.append("not null")
        if self.unique:
            parts.append("unique")
        if self.min is not None or self.max is not None:
            parts.append(
                f"range [{self.min if self.min is not None else '-inf'}, {self.max if self.max is not None else 'inf'}]"
            )
        if self.allowed is not None:
            parts.append("one of {" + ", ".join(map(str, self.allowed)) + "}")
        if self.pattern:
            parts.append(f"matches `{self.pattern}`")
        return "; ".join(parts) or "-"


@dataclass(frozen=True)
class Check:
    """A dataframe-level rule. ``func`` returns a boolean Series (True = row passes) or a single bool."""

    name: str
    func: Callable[[pd.DataFrame], pd.Series | bool]
    description: str = ""


@dataclass(frozen=True)
class Failure:
    column: str | None
    check: str
    n_failures: int
    examples: tuple[Any, ...] = ()

    def __str__(self) -> str:
        where = f"[{self.column}] " if self.column else ""
        ex = f" e.g. {list(self.examples)}" if self.examples else ""
        return f"{where}{self.check}: {self.n_failures} failing{ex}"


@dataclass
class ValidationReport:
    schema: str
    n_rows: int
    failures: list[Failure] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    def raise_for_errors(self) -> None:
        if self.failures:
            details = "\n  - ".join(str(f) for f in self.failures)
            raise SchemaError(f"Schema {self.schema!r} failed with {len(self.failures)} error(s):\n  - {details}")

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"column": f.column, "check": f.check, "n_failures": f.n_failures, "examples": list(f.examples)}
                for f in self.failures
            ],
            columns=["column", "check", "n_failures", "examples"],
        )

    def __str__(self) -> str:
        status = "PASSED" if self.ok else f"FAILED ({len(self.failures)} issue(s))"
        lines = [f"Schema {self.schema!r} on {self.n_rows:,} rows: {status}"]
        lines += [f"  - {f}" for f in self.failures]
        return "\n".join(lines)


def _examples(values: pd.Series, k: int = 5) -> tuple[Any, ...]:
    return tuple(values.drop_duplicates().head(k).tolist())


@dataclass(frozen=True)
class DataFrameSchema:
    """Contract for a whole DataFrame."""

    name: str
    columns: Sequence[Column]
    description: str = ""
    strict: bool = False
    min_rows: int = 0
    unique_together: Sequence[Sequence[str]] = ()
    checks: Sequence[Check] = ()

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def validate(self, df: pd.DataFrame, sample_size: int = 5) -> ValidationReport:
        """Check ``df`` against every rule and collect *all* failures (does not stop at the first)."""
        report = ValidationReport(self.name, len(df))
        add = report.failures.append

        if len(df) < self.min_rows:
            add(Failure(None, f"min_rows>={self.min_rows}", self.min_rows - len(df)))

        missing = [c for c in self.column_names if c not in df.columns]
        for col in missing:
            add(Failure(col, "column present", 1))
        if self.strict:
            for col in (c for c in df.columns if c not in self.column_names):
                add(Failure(str(col), "unexpected column (strict schema)", 1))

        for spec in self.columns:
            if spec.name in missing:
                continue
            s = df[spec.name]
            if spec.coerce_datetime and not pd.api.types.is_datetime64_any_dtype(s):
                coerced = pd.to_datetime(s, errors="coerce")
                bad = s.notna() & coerced.isna()
                if bad.any():
                    add(Failure(spec.name, "parseable as datetime", int(bad.sum()), _examples(s[bad], sample_size)))
                s = coerced
            elif not _TYPE_CHECKS[spec.dtype](s):
                hint = ""
                if spec.dtype == "int" and pd.api.types.is_float_dtype(s) and s.isna().any():
                    hint = " (missing values upcast integers to float)"
                add(Failure(spec.name, f"dtype is {spec.dtype}{hint}", 1, (str(s.dtype),)))

            nulls = s.isna()
            if not spec.nullable and nulls.any():
                add(Failure(spec.name, "not null", int(nulls.sum())))
            present = s[~nulls]

            if spec.unique:
                dup = present.duplicated(keep=False)
                if dup.any():
                    add(Failure(spec.name, "unique", int(dup.sum()), _examples(present[dup], sample_size)))
            for bound, label, op in ((spec.min, ">=", "lt"), (spec.max, "<=", "gt")):
                if bound is None:
                    continue
                value = pd.Timestamp(bound) if isinstance(bound, str) else bound
                try:
                    bad = getattr(present, op)(value)
                except TypeError:  # values not comparable with the bound; the dtype failure already covers it
                    continue
                if bad.any():
                    add(Failure(spec.name, f"{label} {bound}", int(bad.sum()), _examples(present[bad], sample_size)))
            if spec.allowed is not None:
                bad = ~present.isin(list(spec.allowed))
                if bad.any():
                    add(Failure(spec.name, "in allowed set", int(bad.sum()), _examples(present[bad], sample_size)))
            if spec.pattern is not None:
                bad = ~present.astype(str).str.fullmatch(spec.pattern).astype(bool)
                if bad.any():
                    add(
                        Failure(
                            spec.name, f"matches {spec.pattern!r}", int(bad.sum()), _examples(present[bad], sample_size)
                        )
                    )

        for cols in self.unique_together:
            if all(c in df.columns for c in cols):
                dup = df.duplicated(subset=list(cols), keep=False)
                if dup.any():
                    add(Failure(",".join(cols), "unique together", int(dup.sum())))

        for check in self.checks:
            try:
                outcome = check.func(df)
            except Exception as exc:  # a broken check is itself a failure, not a crash
                add(Failure(None, f"{check.name} (raised {type(exc).__name__}: {exc})", len(df)))
                continue
            if isinstance(outcome, pd.Series):
                n_bad = int((~outcome.fillna(False).astype(bool)).sum())
                if n_bad:
                    add(Failure(None, check.name, n_bad))
            elif not bool(outcome):
                add(Failure(None, check.name, 1))

        return report

    def to_markdown(self) -> str:
        """Render the schema as a Markdown data-dictionary table."""
        lines = [
            "| Column | Type | Nullable | Constraints | Description |",
            "| --- | --- | --- | --- | --- |",
        ]
        for c in self.columns:
            lines.append(
                f"| `{c.name}` | {c.dtype} | {'yes' if c.nullable else 'no'} | {c.rules()} | {c.description} |"
            )
        if self.checks:
            lines.append("")
            lines.append("**Table-level checks:**")
            lines.append("")
            lines.extend(f"- `{chk.name}`: {chk.description}" for chk in self.checks)
        return "\n".join(lines)

"""PandasPlayground: a reproducible, tested toolkit for rigorous data manipulation with pandas.

The package is organised into focused modules:

* :mod:`pandasplayground.io` - format-aware loading/saving and content hashing
* :mod:`pandasplayground.cleaning` - non-mutating cleaning and outlier detection
* :mod:`pandasplayground.aggregation` - grouped, pivoted and time-based summaries
* :mod:`pandasplayground.merging` - merges/concats with cardinality and coverage checks
* :mod:`pandasplayground.memory` - dtype optimisation with before/after reporting
* :mod:`pandasplayground.validation` - declarative, dependency-free schema validation
* :mod:`pandasplayground.schemas` - schemas for every bundled dataset
* :mod:`pandasplayground.stats` - bootstrap, permutation and effect-size statistics
* :mod:`pandasplayground.benchmark` - repeatable micro-benchmarks with environment capture
* :mod:`pandasplayground.provenance` - run manifests (inputs, outputs, versions, git SHA)
* :mod:`pandasplayground.pipeline` - the end-to-end, deterministic analysis pipeline
* :mod:`pandasplayground.datagen` - seeded synthetic data generation
"""

from __future__ import annotations

__version__ = "2.0.0"
__author__ = "Satvik Praveen"
__email__ = "satvikpraveen707@gmail.com"

__all__ = ["__version__"]

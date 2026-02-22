# Algorithm Documentation: `quicksort_routes`

## Overview

`quicksort_routes` is a recursive sorting function that sorts a list of route dictionaries in **descending order** by their `trip_count` field. It is based on the classic **Quicksort** algorithm, adapted for structured route data.

---

## Function Signature

```python
def quicksort_routes(routes: list) -> list
```

### Parameters

| Parameter | Type   | Description                                                      |
|-----------|--------|------------------------------------------------------------------|
| `routes`  | `list` | A list of route dictionaries, each containing a `trip_count` key |

### Returns

A new list of route dictionaries sorted in **descending order** by `trip_count`.

### Raises

| Exception         | Condition                                                         |
|-------------------|-------------------------------------------------------------------|
| `ValueError`      | `routes` is not a list                                            |
| `KeyError`        | Any route dictionary is missing the `trip_count` key             |
| `Exception`       | Wraps any other unexpected error with the message `"Algorithm error: <details>"` |

---

## Algorithm

### Strategy: Divide and Conquer

Quicksort works by selecting a **pivot** value and partitioning the input into three groups:

- **left** — elements greater than the pivot (sorted first, for descending order)
- **middle** — elements equal to the pivot
- **right** — elements less than the pivot (sorted last)

The function then recursively sorts `left` and `right`, and concatenates the results as `left + middle + right`.

### Pivot Selection

The pivot is the `trip_count` of the element at the **middle index** of the current list:

```python
pivot = routes[len(routes) // 2]["trip_count"]
```

This middle-element strategy reduces the chance of worst-case performance on already-sorted or nearly-sorted inputs, compared to always choosing the first or last element.

### Base Case

Recursion terminates when the input list has 0 or 1 elements, which are trivially sorted:

```python
if len(routes) <= 1:
    return routes
```

---

## Complexity

| Case    | Time Complexity | Space Complexity |
|---------|-----------------|------------------|
| Average | O(n log n)      | O(n log n)       |
| Worst   | O(n²)           | O(n)             |

> **Note:** Worst-case O(n²) occurs when the pivot consistently produces highly unbalanced partitions (e.g., all elements are identical). In practice, this implementation's middle-pivot strategy performs well on typical datasets.

The space complexity is higher than an in-place quicksort because new `left`, `middle`, and `right` lists are created at each recursive level.

---

## Example

### Input

```python
routes = [
    {"route_id": "A", "trip_count": 5},
    {"route_id": "B", "trip_count": 12},
    {"route_id": "C", "trip_count": 3},
    {"route_id": "D", "trip_count": 12},
    {"route_id": "E", "trip_count": 8},
]
```

### Output

```python
[
    {"route_id": "B", "trip_count": 12},
    {"route_id": "D", "trip_count": 12},
    {"route_id": "E", "trip_count": 8},
    {"route_id": "A", "trip_count": 5},
    {"route_id": "C", "trip_count": 3},
]
```

---

## Error Handling

The function validates input at two points:

1. **Before sorting** — confirms the input is a `list`.
2. **During partitioning** — confirms every route contains a `trip_count` key.

All exceptions are caught and re-raised as a generic `Exception` with the prefix `"Algorithm error: "`, making it easy to identify sorting-related failures in calling code.

---

## Notes and Limitations

- **Descending order only.** The sort order is hardcoded (`left` holds larger values). To sort ascending, swap the `>` and `<` comparisons in the partitioning loop.
- **Non-mutating.** The original `routes` list is not modified; a new sorted list is returned.
- **Homogeneous `trip_count` types expected.** Comparing `trip_count` values of mixed types (e.g., `int` vs `str`) will raise a `TypeError`, which will be caught and re-raised as an `Algorithm error`.
- **Not in-place.** Memory usage scales with input size due to list creation at each recursion level. For very large datasets, an in-place implementation may be preferable.

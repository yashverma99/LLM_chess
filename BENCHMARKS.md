# Benchmarks

Run the reproducible starting-position benchmark with:

```powershell
python scripts\benchmark_search.py --depth 2
```

The script reports, for both original and hybrid search:

- selected move;
- evaluation score;
- search depth;
- minimax nodes;
- alpha-beta cutoffs;
- elapsed seconds;
- nodes per second.

No benchmark result is recorded here until the command is run in the target
environment. A lower latency or higher node rate is not evidence of stronger
play, and the tiny sample LSTM is not evidence of chess strength.

## Recorded baseline run

Environment: Windows, Python 3.14, TensorFlow 2.22.0-rc0, starting position,
depth 2.

| Mode | Move | Score | Nodes | Cutoffs | Seconds | Nodes/sec |
|---|---:|---:|---:|---:|---:|---:|
| Engine | `(57, 42)` | 0 | 167 | 14 | 0.2191 | 762.2 |
| Hybrid | `(62, 45)` | 0 | 69 | 19 | 27.0541 | 2.6 |

The hybrid search visited fewer nodes in this run, but model loading/inference
dominated elapsed time. This single starting-position measurement does not
establish a strength or speed advantage.

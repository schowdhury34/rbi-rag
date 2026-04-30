# eval/benchmark.py
# Runs evaluation and compares against previous benchmark.
# Use after any significant change: new circulars, chunk size, model swap.
#
# Usage:
#   python eval/benchmark.py                  # run and print
#   python eval/benchmark.py --save           # run and save to benchmarks/
#   python eval/benchmark.py --compare        # compare with last saved benchmark

import sys, argparse, logging
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from eval.ragas_eval import run_eval

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BENCH_DIR = Path(__file__).parent.parent / "benchmarks"
METRICS   = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]


def compare_with_last(current_df: pd.DataFrame, mode: str):
    """Compare current run against the most recent saved benchmark."""
    saved = sorted(BENCH_DIR.glob(f"eval_{mode}_*.csv"))
    if len(saved) < 2:
        print("\nNo previous benchmark to compare against.")
        return

    prev_df = pd.read_csv(saved[-2])  # second-to-last file

    print("\n" + "="*55)
    print(f"  Benchmark Comparison | mode={mode}")
    print("="*55)
    print(f"  {'Metric':<22} {'Previous':>10} {'Current':>10} {'Delta':>8}")
    print("  " + "-"*51)
    for m in METRICS:
        if m in prev_df.columns and m in current_df.columns:
            prev = prev_df[m].mean()
            curr = current_df[m].mean()
            delta = curr - prev
            arrow = "▲" if delta > 0.01 else ("▼" if delta < -0.01 else "~")
            print(f"  {m:<22} {prev:>10.3f} {curr:>10.3f} {arrow}{abs(delta):>6.3f}")
    print("="*55)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode",    choices=["rag", "agent"], default="rag")
    parser.add_argument("--split",   choices=["dev", "test", "all"], default="dev")
    parser.add_argument("--save",    action="store_true")
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()

    current_df = run_eval(args.mode, args.split, save=args.save)

    if args.compare:
        compare_with_last(current_df, args.mode)


if __name__ == "__main__":
    main()

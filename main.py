import sys
from baseline import collect_baseline, compute_baseline_stats
from detector import run_detector

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [baseline|detect]")
        return
    if sys.argv[1] == "baseline":
        collect_baseline()
        compute_baseline_stats()
    elif sys.argv[1] == "detect":
        run_detector()

if __name__ == "__main__":
    main()

"""Runs every experiment in order and draws the charts.

    python src/run_all.py          # 10 seeds (about 2 minutes)
    python src/run_all.py 3        # 3 seeds  (quick check)
"""
import sys

import benchmark
import blackout_sim
import make_figures
import nonce_collision
import nonce_reuse_demo
import predictability
import replay_test
import sensitivity
import tamper_tests

if __name__ == "__main__":
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print("\n=== E3 Tamper tests (RQ3) ===");                tamper_tests.main()
    print("\n=== E3b Replay and counter reset (RQ3) ===");  replay_test.main()
    print("\n=== E2 Nonce-reuse attack (RQ2) ===");           nonce_reuse_demo.main()
    print("\n=== E2b Plaintext predictability, PVGIS data (RQ2) ==="); predictability.main()
    print(f"\n=== E4 20-year simulation, {seeds} seeds (RQ4) ==="); blackout_sim.main(seeds=seeds)
    print("\n=== E4b Sensitivity to flash endurance ===");     sensitivity.main()
    print("\n=== Random-nonce collision probability ===");    nonce_collision.main()
    print("\n=== E1 Benchmark (RQ1) ===");                   benchmark.main()
    print("\n=== Charts ===");                               make_figures.main()
import benchmark
import blackout_sim
import make_figures
import nonce_reuse_demo
import tamper_tests
import sensitivity

if __name__ == "__main__":
    print("\n=== E3 Tamper tests (RQ3) ===");          tamper_tests.main()
    print("\n=== E2 Nonce-reuse attack (RQ2) ===");     nonce_reuse_demo.main()
    print("\n=== E4 20-year outage simulation (RQ4) ==="); blackout_sim.main(seeds=3)
    print("\n=== Sensitivity Analysis (RQ5) ===");     sensitivity.main()
    print("\n=== E1 Benchmark (RQ1) ===");             benchmark.main()
    print("\n=== Charts ===");                         make_figures.main()
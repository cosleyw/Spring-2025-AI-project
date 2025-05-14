import pstats

# A small parser to read/interpret profiling information

p = pstats.Stats("out")
p.sort_stats("cumtime").print_stats("main.py")
# p.sort_stats("tottime").print_stats(20)

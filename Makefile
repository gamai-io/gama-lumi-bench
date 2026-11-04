.PHONY: test

test:
	python3 det_router_bench.py --selftest && python3 embed_qdrant_bench.py --selftest && python3 retrieval_eval.py --selftest
	python3 -m unittest discover -s tests -v

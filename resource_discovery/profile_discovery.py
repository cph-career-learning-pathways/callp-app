"""Read-only CaLLP Resource Discovery latency profiler.

Run from repository root using python -m resource_discovery.profile_discovery.
No production modules are modified. Uses the real Brave API and publisher pages.
"""
import argparse
import statistics
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from unittest.mock import patch

from dotenv import load_dotenv
from resource_discovery import search as discovery


def run_once(query, filters):
    lock = threading.Lock()
    inspections = []
    brave_times = []
    original_brave = discovery.search_brave
    original_inspect = discovery.inspect_resource

    def timed_brave(search_query):
        start = perf_counter()
        try:
            return original_brave(search_query)
        finally:
            brave_times.append(perf_counter() - start)

    def timed_inspect(candidate):
        start = perf_counter()
        outcome = 'error'
        try:
            result = original_inspect(candidate)
            outcome = 'none' if result is None else 'classified'
            return result
        finally:
            duration = perf_counter() - start
            with lock:
                inspections.append((duration, outcome, candidate.get('url', '')))

    start = perf_counter()
    with patch.object(discovery, 'search_brave', side_effect=timed_brave), \
         patch.object(discovery, 'inspect_resource', side_effect=timed_inspect):
        results = discovery.search_resources(query, filters)
    elapsed = perf_counter() - start

    print(f'  End-to-end: {elapsed:.2f}s | Brave: {sum(brave_times):.2f}s')
    print(f'  Inspected: {len(inspections)} | Returned: {len(results)}')
    if inspections:
        durations = [entry[0] for entry in inspections]
        print(f'  Inspection durations: min={min(durations):.2f}s '
              f'median={statistics.median(durations):.2f}s '
              f'max={max(durations):.2f}s '
              f'sum={sum(durations):.2f}s')
        print(f'  Outcomes: {dict(Counter(entry[1] for entry in inspections))}')
        print('  Slowest publisher inspections:')
        for seconds, outcome, url in sorted(inspections, reverse=True)[:5]:
            print(f'    {seconds:6.2f}s  {outcome:10s}  {url[:120]}')
    return elapsed



def compare_workers(query, filters, runs):
    """Compare fixed Brave candidates; no production settings are changed."""
    normalized = discovery.normalize_filters(filters)
    built_query = discovery.build_discovery_query(query=query, filters=filters)
    if not built_query:
        print('Empty query; nothing to benchmark.')
        return
    brave_query = discovery.build_search_query_for_filters(built_query, normalized)
    start = perf_counter()
    candidates = discovery.search_brave(brave_query)
    brave_seconds = perf_counter() - start
    print(f'Fixed Brave candidate set: {len(candidates)} URLs; API: {brave_seconds:.2f}s')
    if not candidates:
        return

    samples = {5: [], 8: []}
    signatures = {5: [], 8: []}
    for repeat in range(runs):
        order = (5, 8) if repeat % 2 == 0 else (8, 5)
        print(f'\nPair {repeat + 1}/{runs} (order {order[0]} then {order[1]}):')
        for workers in order:
            start = perf_counter()
            outcomes = [None] * len(candidates)
            errors = {}
            with ThreadPoolExecutor(max_workers=min(workers, len(candidates))) as pool:
                futures = {pool.submit(discovery.inspect_resource, candidate): i
                           for i, candidate in enumerate(candidates)}
                for future in as_completed(futures):
                    i = futures[future]
                    try:
                        outcomes[i] = future.result()
                    except Exception as exc:
                        errors[i] = type(exc).__name__
            elapsed = perf_counter() - start
            present = [r for r in outcomes if isinstance(r, dict)]
            accepted = [r for r in present if discovery.matches_discovery_filters(r, normalized)]
            desc = sum(bool(r.get('description')) for r in present)
            fmt = sum(bool(r.get('resource_format')) for r in present)
            kind = sum(bool(r.get('resource_type')) for r in present)
            difficulty = sum(bool(r.get('difficulty')) for r in present)
            signature = [(r.get('url'), r.get('resource_format'),
                          r.get('resource_type'), bool(r.get('description')))
                         if isinstance(r, dict) else None for r in outcomes]
            signatures[workers].append(signature)
            samples[workers].append(elapsed)
            print(f'  {workers} workers: {elapsed:.2f}s | returned={len(accepted)} '
                  f'non-null={len(present)} none={len(candidates)-len(present)-len(errors)} '
                  f'errors={len(errors)} | metadata: descriptions={desc}, '
                  f'formats={fmt}, types={kind}, difficulty={difficulty}')
            if errors:
                print(f'    Error types: {dict(Counter(errors.values()))}')

    print('\nInspection-only summary (Brave API time excluded):')
    for workers in (5, 8):
        times = samples[workers]
        print(f'  {workers} workers: median={statistics.median(times):.2f}s '
              f'min={min(times):.2f}s max={max(times):.2f}s')
    med5 = statistics.median(samples[5])
    med8 = statistics.median(samples[8])
    print(f'  Median change (8 vs 5): {(med8 / med5 - 1) * 100:+.1f}%')
    differences = [sum(a != b for a, b in zip(sig5, sig8))
                   for sig5, sig8 in zip(signatures[5], signatures[8])]
    print(f'  Paired result/metadata signature differences: {differences}')
    print('  Note: repeated live requests can vary due to publisher responses, '
          'rate limits, and connection warming.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query', default='Python programming tutorial')
    parser.add_argument('--format', choices=['video', 'document', 'webpage', 'mixed'])
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--compare-workers', action='store_true',
                        help='Compare 5 and 8 workers on one fixed Brave candidate list')
    args = parser.parse_args()
    if not 1 <= args.runs <= 10:
        parser.error('--runs must be between 1 and 10')

    load_dotenv(dotenv_path='.env', override=True)
    filters = {'formats': [args.format]} if args.format else None
    if args.compare_workers:
        compare_workers(args.query, filters, args.runs)
        return
    times = []
    print(f'Query: {args.query!r} | Format: {args.format or "any"} | Runs: {args.runs}')
    for number in range(1, args.runs + 1):
        print(f'\nRun {number}:')
        try:
            times.append(run_once(args.query, filters))
        except Exception as exc:
            print(f'  Failed: {type(exc).__name__}: {exc}')
            break
    if times:
        print(f'\nEnd-to-end summary: median={statistics.median(times):.2f}s '
              f'min={min(times):.2f}s max={max(times):.2f}s')


if __name__ == '__main__':
    main()

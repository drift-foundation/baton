"""Independent bounded verifier: read a selected capsule; emit a review report.

No model, credentials, engine, authority mutations or certification. The caller
must transport this output through the independently assigned review workload.
"""
import argparse
import sys
from qualification_packet import read, review, encoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capsule', required=True)
    parser.add_argument('--approved-capsule', required=True)
    args = parser.parse_args()
    try:
        report = review(read(args.capsule), args.approved_capsule)
    except Exception as error:
        # No input content/path is echoed on failure.
        print('qualification evidence refused: ' + type(error).__name__, file=sys.stderr)
        return 2
    sys.stdout.buffer.write(encoded(report) + b'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

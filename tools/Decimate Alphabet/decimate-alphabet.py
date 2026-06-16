import argparse

parser = argparse.ArgumentParser(
    description="Cryptographically decimate an alphabet across a range of "
                "decimation values, printing the cycle decomposition for each."
)
parser.add_argument("alphabet", help="The alphabet to decimate.")
parser.add_argument(
    "--even",
    action="store_true",
    help="Include even-valued decimations. By default, even decimations are skipped.",
)
args = parser.parse_args()

alphabet = args.alphabet


def get_total_length(chain):
    """Returns the total number of characters in all strings within the list."""
    return sum(len(s) for s in chain)


for decimation in range(2, len(alphabet)):
    if not args.even and decimation % 2 == 0:
        continue
    chain = []
    starting_offset = 0
    while get_total_length(chain) < len(alphabet):
        current_offset = starting_offset
        s = ''
        while True:
            s += alphabet[current_offset]
            current_offset = (current_offset + decimation) % len(alphabet)
            if current_offset == starting_offset:
                # We've cycled back to the starting offset, we have the partial chain
                break
        chain.append(s)
        starting_offset = starting_offset + 1
    cycles = ' '.join('(%s)' % s for s in chain)
    print("%3d: %s" % (decimation, cycles))
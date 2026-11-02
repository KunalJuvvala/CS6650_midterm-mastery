#!/usr/bin/env bash
# Creates the test files used in all three experiments and (optionally) uploads them to S3.
#
# Usage (run from the midterm-mastery folder):
#   scripts/make_files.sh                      # just create ./test-files
#   scripts/make_files.sh <your-bucket-name>   # create and upload to s3://<bucket>/tmp/
#
# The service splits files into 64-byte chunks and the client refuses more than 65,536
# chunks, so 4 MiB (4,194,304 bytes) is the largest file that should work.
# size-over-limit.txt is 64 bytes past that limit, to show what happens when you exceed it.
set -eu   # no pipefail: "tr | head" ends tr with SIGPIPE on purpose

DIR="test-files"
mkdir -p "$DIR"

make_file() {   # make_file <name> <bytes>
  LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c "$2" > "$DIR/$1"
  echo "created $DIR/$1 ($2 bytes, $(( ($2 + 63) / 64 )) chunks)"
}

make_file size-1k.txt          1024
make_file size-64k.txt         65536
make_file size-256k.txt        262144
make_file size-1m.txt          1048576
make_file size-2m.txt          2097152
make_file size-4m.txt          4194304
make_file size-over-limit.txt  4194368

if [[ $# -ge 1 ]]; then
  aws s3 cp "$DIR/" "s3://$1/tmp/" --recursive
  echo "uploaded to s3://$1/tmp/"
  aws s3 ls "s3://$1/tmp/"
fi

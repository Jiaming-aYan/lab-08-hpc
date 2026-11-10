#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: bash get_books.sh BUCKET BOOK_DIRECTORY" >&2
    exit 1
fi

bucket=$1
book_dir=$2
mkdir -p "$book_dir"
book_dir=$(realpath "$book_dir")

aws s3 cp "s3://$bucket/" "$book_dir/" --recursive --exclude "*" --include "*.txt"

echo "File path" > book_list.txt
find "$book_dir" -type f -name '*.txt' | sort >> book_list.txt
count=$(( $(wc -l < book_list.txt) - 1 ))
echo "Wrote $count book files to book_list.txt"

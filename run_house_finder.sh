#!/usr/bin/env bash

set -euo pipefail

INPUT_FILE="${1:-input.csv}"
OUTPUT_FILE="${2:-output.csv}"

DB_FILE="house_finder.db"
LOG_FILE="house_finding.log"
DEBUG_FILE="${OUTPUT_FILE%.*}_debug.${OUTPUT_FILE##*.}"

echo "Cleaning previous run..."

rm -f "$DB_FILE"
rm -f "$LOG_FILE"
rm -f "$OUTPUT_FILE"
rm -f "$DEBUG_FILE"


# -----
OUTPUT_BASE="${OUTPUT_FILE%.*}"

rm -f "$DB_FILE"
rm -f "$LOG_FILE"

rm -f "$OUTPUT_FILE"
rm -f "${OUTPUT_BASE}_debug.${OUTPUT_FILE##*.}"

rm -f "$OUTPUT_BASE.csv"
rm -f "${OUTPUT_BASE}_debug.csv"

rm -f "$OUTPUT_BASE.xlsx"
rm -f "${OUTPUT_BASE}_debug.xlsx"

# ----


echo "Starting house finder..."
echo "Input : $INPUT_FILE"
echo "Output: $OUTPUT_FILE"

python3 main.py \
  --input-file "$INPUT_FILE" \
  --output-file "$OUTPUT_FILE"

echo ""
echo "Run completed."
echo "Output file: $OUTPUT_FILE"
echo "Debug file : $DEBUG_FILE"
echo "Log file   : $LOG_FILE"
#!/bin/bash
# Publishes the next queued article from _articles/pending/ to src/pages/blog/
# Used by the weekly GitHub Action workflow.

set -e

PENDING_DIR="_articles/pending"
BLOG_DIR="src/pages/blog"
TODAY=$(date +%Y-%m-%d)

# Find the first pending article alphabetically
FIRST=$(ls "$PENDING_DIR"/*.md 2>/dev/null | sort | head -1)

if [ -z "$FIRST" ]; then
  echo "No pending articles found. All done!"
  exit 0
fi

FILENAME=$(basename "$FIRST")

# Strip leading number prefix (e.g. "06-" → "")
SLUG=$(echo "$FILENAME" | sed 's/^[0-9]*-//')

echo "Publishing: $FILENAME → $SLUG"

# Update pubDate in frontmatter to today
sed -i "s/^pubDate: .*/pubDate: \"$TODAY\"/" "$FIRST"

# Move to blog directory
cp "$FIRST" "$BLOG_DIR/$SLUG"
rm "$FIRST"

echo "Published: $SLUG on $TODAY"

# Export slug for GitHub Actions step output
if [ -n "$GITHUB_OUTPUT" ]; then
  echo "slug=$SLUG" >> "$GITHUB_OUTPUT"
  echo "published_date=$TODAY" >> "$GITHUB_OUTPUT"
fi

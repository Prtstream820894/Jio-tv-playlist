import os
import re
import requests

url1 = "https://sportlink-playlist.pages.dev/zio.m3u"
url2 = "https://premiumplugx.me/vzy/playlist.php"

# Create a session with browser headers
session = requests.Session()
session.headers.update({
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    ),
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
})


def parse_m3u_blocks(content):
  lines = content.splitlines()
  blocks = []
  i = 0
  n = len(lines)

  while i < n:
    line = lines[i].strip()
    if line.startswith('#EXTINF:'):
      extinf = line
      extra_lines = []
      i += 1
      # Collect intermediate lines (like #KODIPROP, etc.) until URL is found
      while i < n and lines[i].strip().startswith('#'):
        extra_lines.append(lines[i].strip())
        i += 1

      url = lines[i].strip() if i < n else ''
      blocks.append({'extinf': extinf, 'extra': extra_lines, 'url': url})
    i += 1
  return blocks


new_blocks = []

# --- 1. Process Source 1 (Star Sports Only) ---
try:
  print('Fetching Source 1...')
  resp1 = session.get(url1, timeout=30)
  if resp1.status_code == 200:
    blocks1 = parse_m3u_blocks(resp1.text)
    print(f'Source 1 total parsed items: {len(blocks1)}')

    count1 = 0
    for b in blocks1:
      extinf = b['extinf']
      if ',' in extinf:
        header_part, title = extinf.split(',', 1)

        if re.search(r'star\s*sports', title, re.IGNORECASE):
          if 'group-title=' in header_part:
            header_part = re.sub(
                r'group-title="[^"]*"', 'group-title="Sports"', header_part
            )
          else:
            header_part += ' group-title="Sports"'

          clean_title = title.strip()
          if not clean_title.endswith('[Jio Tv]'):
            clean_title = f'{clean_title} [Jio Tv]'

          new_extinf = f'{header_part},{clean_title}'
          new_blocks.append(
              {'extinf': new_extinf, 'extra': b['extra'], 'url': b['url']}
          )
          count1 += 1
    print(f'Source 1 Star Sports added: {count1}')
  else:
    print(f'Source 1 status code: {resp1.status_code}')
except Exception as e:
  print(f'Error Source 1: {e}')

# --- 2. Process Source 2 (Via URL or Local Fallback file 'source2.m3u') ---
source2_content = ''
try:
  print('Fetching Source 2...')
  resp2 = session.get(url2, timeout=30)
  if resp2.status_code == 200:
    source2_content = resp2.text
    print('Source 2 fetched successfully from URL.')
  else:
    print(
        f'Source 2 returned status code: {resp2.status_code}. Checking local'
        ' fallback file...'
    )
except Exception as e:
  print(f'Error fetching Source 2 via URL: {e}. Checking local fallback file...')

# Fallback: If URL failed or got 403, read from local 'source2.m3u' file in repo if it exists
if not source2_content and os.path.exists('source2.m3u'):
  with open('source2.m3u', 'r', encoding='utf-8') as f:
    source2_content = f.read()
  print('Loaded Source 2 data from local fallback file: source2.m3u')

if source2_content:
  blocks2 = parse_m3u_blocks(source2_content)
  print(f'Source 2 total parsed items: {len(blocks2)}')

  count2 = 0
  for b in blocks2:
    extinf = b['extinf']
    if ',' in extinf:
      header_part, title = extinf.split(',', 1)
      clean_title = title.strip()

      # Rule for 9x -> Music
      if re.search(r'\b9x\b', clean_title, re.IGNORECASE):
        if 'group-title=' in header_part:
          header_part = re.sub(
              r'group-title="[^"]*"', 'group-title="Music"', header_part
          )
        else:
          header_part += ' group-title="Music"'

      # Rule for Big Magic -> Entertainment
      elif re.search(r'big\s*magic', clean_title, re.IGNORECASE):
        if 'group-title=' in header_part:
          header_part = re.sub(
              r'group-title="[^"]*"', 'group-title="Entertainment"', header_part
          )
        else:
          header_part += ' group-title="Entertainment"'

      new_extinf = f'{header_part},{clean_title}'
      new_blocks.append(
          {'extinf': new_extinf, 'extra': b['extra'], 'url': b['url']}
      )
      count2 += 1
  print(f'Source 2 channels added: {count2}')
else:
  print(
      'Warning: Source 2 content is empty! (No URL data and no source2.m3u file'
      ' found)'
  )

# --- Output Final M3U File ---
output_lines = ['#EXTM3U']
for b in new_blocks:
  output_lines.append(b['extinf'])
  for ex in b['extra']:
    output_lines.append(ex)
  output_lines.append(b['url'])

with open('playlist.m3u', 'w', encoding='utf-8') as f:
  f.write('\n'.join(output_lines))

print(f'Done! Saved {len(new_blocks)} total channels in playlist.m3u')

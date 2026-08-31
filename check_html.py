import urllib.request, json, re

# Check the actual HTML page served
req = urllib.request.Request('http://localhost:8052/')
with urllib.request.urlopen(req) as r:
    html = r.read().decode()

# Find script tags
scripts = re.findall(r'src="([^"]+)"', html)
print('Script/link sources:')
for s in scripts:
    print(' ', s)

print()
# Find link tags
links = re.findall(r'href="([^"]+)"', html)
print('Link hrefs:')
for l in links:
    print(' ', l)

print()
# Check for any inline errors
if '_dash-renderer' in html:
    print('dash-renderer found in HTML')
    
# Print the full HTML for inspection
print()
print('=== FULL HTML ===')
print(html[:3000])

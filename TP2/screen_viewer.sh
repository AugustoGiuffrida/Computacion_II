grep screenshot page.json | awk '{print $2}' | sed 's/\"//g' | sed 's/,//' | base64 -d > page.png

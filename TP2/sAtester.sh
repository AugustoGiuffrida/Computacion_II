echo "Orden de las urls:"
for url in {'https://asherwycoff.com/','https://holeinmyheart.neocities.org/','https://www.librarian.net/','https://hackernewsletter.com/','https://dayzerosec.com/','http://cow.net/cows/'} ; do echo "  - $url" ; curl -X POST http://localhost:8080/scrape -H "Content-Type: application/json" -d "{\"url\": \"$url\"}" >> out.json & done

from TheYes import MovieDB
movie_db = MovieDB("/tmp/movies.txt")
print(movie_db.search("Tom Hanks"))
print(movie_db.search("love"))
print(movie_db.search("Tom Hanks", full_term_search=True))
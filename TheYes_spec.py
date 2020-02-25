# This file just provides some simple,quick,easy unit tests. This tests that the MovieDB
# class can be insantiated from a cache file of movies. It doesn't test that the web crawling
# works. If I had more time, i'd spend some of it writing tests for webcrawling
from TheYes import MovieDB
from TheYes import Movie
import json

movie1 = Movie("Cool Action Movie", ['Action', 'Drama'], "A pair of buddies rob a bank", "Kevin Fallon", ["Joe Smith", "Smith Joe"])
movie2 = Movie("Funny Romantic Movie", ['Comedy', "Romantic"], "Two people fall in love in unpredictable way", "Bob Direct", ["Alexa Booker", "Bill Nye", "Kevin Fallon"])
movies = list(map(lambda movie: movie.to_d(), [movie1,movie2]))
with open('/tmp/movies_test.txt', 'w') as outfile:
	json.dump(movies, outfile)	
movie_db = MovieDB("/tmp/movies_test.txt")


# Test Director full name search
print(movie_db.search("Kevin Fallon") == ["Cool Action Movie", "Funny Romantic Movie"])
# Test case insensivity
print(movie_db.search("kevin fallon") == ["Cool Action Movie", "Funny Romantic Movie"])
# Test all terms get searched individually
print(movie_db.search("Nye Drama") == ["Cool Action Movie", "Funny Romantic Movie"])
# Test we can search only by last name
print(movie_db.search("Nye") == ['Funny Romantic Movie'])
# Test 'full term search'. It searches for whole string 'Nye Darama'
print(movie_db.search("Nye Drama", full_term_search=True) == [])
# Test that description search works
print(movie_db.search("love") == ["Funny Romantic Movie"])
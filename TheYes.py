# Build search for the top 1000 IMDB moives. Users should be able to search for different aspects of the movie

# Assumptions
# Movie titles are all unique, people first+last name combos are unique
# with a large system, probably need a service that looks for duplicates in the system and removes them.
# We currently cache data to make subsequent runs of the program quicker

from bs4 import BeautifulSoup
import requests
import re
import json
import os
import collections

class Movie:
	def __init__(self, title, genres, description, director, actors):
		self.title = title
		self.genres = genres
		self.description = description
		self.director = director
		self.actors = actors

	# Used to write movie data to disk so we don't have to make requests each time
	def to_d(self):
		return {
			"title": self.title,
			"genres": self.genres,
			"description": self.description,
			"director": self.director,
			"actors": self.actors
		}

	@classmethod
	def parse_movie_html(cls, movie_html):
		title = movie_html.find("h3", {"class": 'lister-item-header'}).a.string
		content = movie_html.find("div", {"class": 'lister-item-content'}).find_all("p")
		raw_genres = content[0].find("span", {"class": "genre"}).string.strip("\n").split(", ")
		genres = list(map(lambda genre: re.sub(r"\W", "", genre), raw_genres))
		description = content[1].get_text().strip()
		names = list(map(lambda name: name.string, content[2].find_all("a")))
		director = names[0]
		actors = names[1:]
		return title, genres, description, director, actors

class MovieDB:
	def __init__(self, data_file):
		movies = []
		if not os.path.exists(data_file):
			movies = self._download_movie_information()
			movies_json = list(map(lambda movie: movie.to_d(), movies))
			with open(data_file, 'w') as outfile:
				json.dump(movies_json, outfile)
		else:
			with open(data_file, 'r') as json_file:
				raw_movies = json.load(json_file)
				extract_attr = lambda m: Movie(m['title'], m['genres'], m['description'], m['director'], m['actors'])
				movies = list(map(extract_attr, raw_movies))

		movies_by_person = collections.defaultdict(set)
		movies_by_genre = collections.defaultdict(set)
		movies_by_description = collections.defaultdict(set)
		# Granted more time, 'common_words' would be more expansive
		common_words = set(["in", "a", "the", "and", "of"])
		for movie in movies:
			for genre in movie.genres:
				movies_by_genre[genre.lower()].add(movie.title)
			for person in [movie.director] + movie.actors:
				# Assume first entry is whole first name and last entry is whole last name
				for name in [person, person.split(" ")[0], person.split(" ")[-1]]:
					movies_by_person[name.lower()].add(movie.title)
			for word in movie.description.split(" "):
				if word not in common_words:
					movies_by_description[word.lower()].add(movie.title)
		self.indexes = [movies_by_person, movies_by_genre, movies_by_description]

	def _parse_movies(self, page_response):
		page_content = BeautifulSoup(page_response.content, "html.parser")
		list_items = page_content.find_all("div", {"class": "lister-item mode-advanced"})
		movies = []
		for list_item in list_items:
			movie_attrs = Movie.parse_movie_html(list_item)
			movies.append(Movie(*movie_attrs))
		return movies

	def _download_movie_information(self):
		movies = []
		for i in range(1, 1000, 50):
			page_link = "https://www.imdb.com/search/title/?groups=top_1000&sort=user_rating,desc&start=" + str(i) + "&ref_=adv_nxt"
			page_response = requests.get(page_link, timeout=5)
			retries = 3
			while retries > 0 and not page_response.ok:
				page_response = requests.get(page_link, timeout=5)
				retries -= 1
			if retries == 0 and not page_response.ok:
				raise "Unable to fetch data"
			movies += self._parse_movies(page_response)
		return movies

	def search(self, query, full_term_search=False):
		query = query.lower()
		to_search = set([])
		if full_term_search:
			to_search.add(query)
		else:
			terms = query.split(" ")
			for i in range(len(terms)):
				for j in range(i+1, len(terms)+1):
					to_search.add(" ".join(terms[i:j]))
		results = set([])

		for term in to_search:
			for index in self.indexes:
				results = results.union(index[term])
		# Sort to give back results in the same order each time
		return sorted(list(results))
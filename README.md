pip3 install --upgrade pip
sudo pip3 install requests
sudo pip3 install beautifulsoup4


To run tests:
python3 TheYes_spec.py


Assumptions and why:
- The movie data is read only and never gets updated. This means that upon various web crawls, we're always going to
  get back the same data. Because of this assumption, data retreived from the first web crawl gets stored
  on disk so that we can minimize network I/O. We don't have to worry about invalidating the cache since it'll
  never be updated.
- The data provided on the "detailed" view mode of IMDB's top 1000 movies is enough for us to create worth while
  searches from. This was just to save time
- Movie titles are all unique, people first+last name combos are unique
- Searches only have correct spelling
- People don't want to search with case sensitivity
- Memory isn't a problem, disk space isn't a problem
- The only 'common words' in descriptions that we'll come aross are "in", "a", "the", "and", "of". I didn't actually do
  any verification on this, I just added the first 5 words to come to mind
- People want consistent results across searches, so we sort by title
- Program has read/write access to /tmp
- Each movie only has 1 director - made this assumption because only one was listed in the view I scraped

# with a large system, probably need a service that looks for duplicates in the system and removes them.
# We currently cache data to make subsequent runs of the program quicker


Thoughts on improvement/scale:
How to improve on software architecture, scale, performance, and quality
Assumptions: 
As of January 2020, IMDb has 6.5 million titles, 10.4 million personalities, 83 million registered users

Schema:
Movies
Movie_id, movie title, release date, rating_total, number_of_ratings, genre, popularity_ranking, description, language

Personalities
Person_id, name, D.O.B, biography, actor (bool), director (bool), actor_ranking, director_ranking
int32, 128 bytes, 512 bytes, 1 bit, 1 bit, 

Actors
Person_id, popularity_ranking

Directors
Person_id, popularity_ranking

Movies_to_actors
movie_id, person_id

Movies_to_directors
movie_id, person_id

Users table
User_id, email, name, etc.

If I had to expand this to be a large scale system, some of the changes I would make:
1. If we have a frontend, we could provide a typeahead service, using a Trie to suggest autocompletes
2. A query correction service - A service that figures out the intended search and polishes up input
3. Ranking service per actors, movies, and directors- takes into account user votes, critic ratings, actors, articles, number of top movies, cast, box office profit. Run this once per day, at a low traffic time. Pull current popularity_rankings from DB, compare diffs and write the diffs within a transaction.
4. LRU cache for movies, actors, directors. 
5. New Entity service - Allows internal IMDB employees to add new movies and personalities to the system. Checks for duplicates, ensure required data is present
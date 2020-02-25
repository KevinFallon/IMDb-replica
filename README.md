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


Thoughts on improvement/scale:
How to improve on software architecture, scale, performance, and quality
Assumptions: 
As of January 2020, IMDb has 6.5 million titles, 10.4 million personalities

Schema:
Movies
Movie_id, movie title, release date, genre, popularity_ranking, description, language
int32(4bytes), 128 bytes, 4 bytes, 64 bytes, int32(4bytes), 512 bytes, 8 bytes(use enum for languages. Have language table) = 724 bytes
724 bytes * 6,500,000 = 4.7GB

Personalities
Person_id, name, D.O.B, biography, actor (bool), director (bool), actor_ranking, director_ranking
int32(4bytes), 128 bytes, 512 bytes, 1 byte, 1 byte, int32(4bytes), int32 = 654 bytes 
738 bytes * 10.4M = 6.7GB
(Use int32 for person_id, actor_ranking, director_ranking because it allows up to 5B ids)

Actors
Person_id, popularity_ranking
int32(4bytes), int32(4bytes)

Directors
Person_id, popularity_ranking
int32(4bytes), int32(4bytes)

actors and directors tables
8 bytes * (10,400,000) = 83.2MB

Movies_to_actors
movie_id, person_id, role in movie
int32(4bytes), int32(4bytes), 128 bytes
assume 80% of personalities are actors. Assume ratio of 100 actors/movie
136bytes * (10,400,000 * 0.8) * 100 = 113GB

Movies_to_directors
movie_id, person_id
int32(4bytes), int32(4bytes)
assume 20% of personalities are directors. assume 1 director per movie
8 bytes * (10,400,000 * .2) = 66.6MB

4.7GB + 6.7GB + 113GB + 83.2MB + 66.6MB = ~ 125GB

according to a quick google search, only 600 movies are made each year. This is less than 1 percent increase in movies and assume less than 1 percent increase in actors. to be safe, we'll say data storage grows by 1 % y/y

125GB * (1.01)^5 = 131.3GB.
We also want to probably stay around 80% capacity so 131.3/.8 = ~ 165GB

If I had to expand this to be a large scale system, some of the changes I would make:
1. If we have a frontend, we could provide a typeahead service, using a Trie to suggest autocompletes
2. A query correction service - A service that figures out the intended search and polishes up input
3. Ranking service per actors, movies, and directors- takes into account user votes, critic ratings, actors, articles, number of top movies, cast, box office profit. Run this once per day, at a low traffic time. Pull current popularity_rankings from DB, compare diffs and write the diffs within a transaction. 
4. New Entity service - Allows users to add new movies and personalities to the system. Checks for duplicates, ensure required data is present. Maybe must be approved by IMDb employees?
5. Store everything in relational DB, since there are clear relations between movies, actors, directors. The total amount of disk space needed above is not much, so we don't need to worry about scaling a large DB cluster which is what NoSQL DBs are good at. We can have 1 primary relational DB that accepts read/writes and several replicas that accept read requests only. It is probably a good idea to have indexes on movie_title in the movies table, and actor name in actors table
165GB is a reasonable amount of data to keep in memory so we could even keep all the data in memory which backups stored on disk. 
6. Have load balancers that distributed load based on round robin at first amongst applicaion servers. These initial LBs can take care of rate limiting users. The application servers then make requests to either the in-memory DBs or the PG instances. It is useful to have application servrs in between to expose several requests via an API, to limit the number of connections that can be made to the PG instances and for security.

Assumptions:
movie titles and actor names are unique
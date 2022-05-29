# Importing the necessary libraries
from flask import Flask, request, render_template
from flask_cors import cross_origin
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches
from tmdbv3api import TMDb, Movie
import requests
import sys

# Initialising flask app   
app = Flask(__name__)

# load the data
df = pd.read_csv('preprocessed_data.csv')
# load cache data
df_cache = pd.read_csv('cache_data.csv')
# storing movie title into list
movie_list = list(df['movie_title'])

# creating TMDB Api Object
tmdb = TMDb()
tmdb.api_key = 'de74c364ccd8b4f9f4f8e86439d794c4'

movies_trending =[]
movies_popular = []
movies_upcoming = []
movies_top_rated = []

# This Function take movie name list and return their Poster link, Tag Line and Title into dictionary
def get_poster_link_main(title):
    """
    This Function take movie name list and return their Poster link, Tag line and Title into dictionary.
    """
    # TMDB Movie Api Object
    tmdb_movie = Movie()

    # Storing data in to dictionary
    dic_data = {"Movie_Title": [], "Poster_Links": [], "Tag_Line": [],"Runtime":[], "Popularity":'',
                "Overview":[], "Genres":[], "ReleaseDate":[], "Cast": [], "Director":[],"Writer":[],
                "Keywords":[], "Reviews":[], "Images":[], "Videos":[{'Url':'','Title':''}]}
    try:
        result = tmdb_movie.search(title)
        movie_id = result[0].id
        #for fetching movie details
        try:
            response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key={}'.format(movie_id, tmdb.api_key))
            data_json = response.json()
            movie_title = data_json['title']
            movie_poster_link = "https://image.tmdb.org/t/p/original" + data_json['poster_path']
            movie_runtime = data_json['runtime']
            movie_popularity = data_json['popularity']
            movie_tag_line = data_json['tagline']
            movie_overview = data_json['overview']
            movie_releasedate = data_json['release_date']
            movie_genres=[]
            for genre in data_json['genres']:
                movie_genres.append(genre['name'])
        except:
            movie_genres=[]

        # For cast and crew
        response_credits = requests.get('https://api.themoviedb.org/3/movie/{}/credits?api_key={}'.format(movie_id, tmdb.api_key))
        data_json_credits = response_credits.json()
        
        #for cast
        try:
            movie_cast=[]
            for cast in data_json_credits['cast']:
                if len(movie_cast) > 10:
                    break
                cast['profile_path'] = 'https://image.tmdb.org/t/p/original' + cast['profile_path']
                movie_cast.append(cast)
        except:
            movie_cast=[]

        #for crew
        try: 
            movie_director=[]
            movie_writer=[]
            for crew in data_json_credits['crew']:
                if "Director" == crew['job']:
                    movie_director.append(crew['name'])
                if "Writer" == crew['job']:
                    movie_writer.append(crew['name']+"(Writer)")
                if "Story" == crew['job']:
                    movie_writer.append(crew['name']+"(Story)")
                if "Screenplay" == crew['job']:
                    movie_writer.append(crew['name']+"(Screenplay)")
        except:
            movie_director=[]
            movie_writer=[]
        
        # For keywords
        try:
            response_keywords = requests.get('https://api.themoviedb.org/3/movie/{}/keywords?api_key={}'.format(movie_id, tmdb.api_key))
            data_json_keywords = response_keywords.json()
            movie_keywords=[]
            for keyword in data_json_keywords['keywords']:
                movie_keywords.append(keyword['name'])
        except:
            movie_keywords=[]
        
        # For Reviews
        try:
            response_reviews = requests.get('https://api.themoviedb.org/3/movie/{}/reviews?api_key={}'.format(movie_id, tmdb.api_key))
            data_json_reviews = response_reviews.json()
            movie_reviews=[]
            for review in data_json_reviews['results']:
                movie_reviews.append(review)
        except:
            movie_reviews=[]
        
        # For images
        try:
            response_images = requests.get('https://api.themoviedb.org/3/movie/{}/images?api_key={}'.format(movie_id, tmdb.api_key))
            data_json_images = response_images.json()
            movie_images=[]
            for image in data_json_images['backdrops']:
                movie_images.append('https://image.tmdb.org/t/p/original'+image['file_path'])
        except:
            movie_images=[]
        
        # For videos
        try:
            response_videos = requests.get('https://api.themoviedb.org/3/movie/{}/videos?api_key={}'.format(movie_id, tmdb.api_key))
            data_json_videos = response_videos.json()
            movie_videos=[]
            for video in data_json_videos['results']:
                if 'YouTube' in video['site']:
                    movie_videos.append({'Url': video['key'],'Title': video['name']})      
        except:
            movie_videos=[]
        # Appending movie title and poster link into dictionary
        dic_data['Movie_Title'].append(movie_title)
        dic_data['Poster_Links'].append(movie_poster_link)
        dic_data['Tag_Line'].append(movie_tag_line)
        dic_data['Runtime'].append(movie_runtime)
        dic_data['Popularity']=movie_popularity
        dic_data['Overview'].append(movie_overview)
        dic_data['Genres']=movie_genres
        dic_data['ReleaseDate'].append(movie_releasedate)
        dic_data['Cast']=movie_cast
        dic_data['Director']=movie_director
        dic_data['Writer']=movie_writer
        dic_data['Keywords']=movie_keywords
        dic_data['Reviews']=movie_reviews
        dic_data['Images']=movie_images
        dic_data['Videos']=movie_videos
    except:
        # checking given movie is present in our cache database or not.
        r_df = df_cache[df_cache['Title'] == title]
        if len(r_df) >= 1:
                dic_data["Movie_Title"].append(r_df['Movie_Title'].values[0])
                dic_data["Poster_Links"].append(r_df['Poster_Links'].values[0])
                dic_data["Tag_Line"].append(r_df['Tag_Line'].values[0])

    return dic_data

# This Function take movie name list and return their Poster link, Tag Line and Title into dictionary
def get_poster_link(title_list):
    """
    This Function take movie name list and return their Poster link, Tag line and Title into dictionary.
    """
    # TMDB Movie Api Object
    tmdb_movie = Movie()

    # Storing data in to dictionary
    dic_data = {"Movie_Title": [], "Poster_Links": [], "Tag_Line": []}

    for title in title_list:

        # checking given movie is present in our cache database or not.
        r_df = df_cache[df_cache['Title'] == title]
        try:
            # if given movie is found in our cache database then run this part
            if len(r_df) >= 1:
                dic_data["Movie_Title"].append(r_df['Movie_Title'].values[0])
                dic_data["Poster_Links"].append(r_df['Poster_Links'].values[0])
                dic_data["Tag_Line"].append(r_df['Tag_Line'].values[0])

            # otherwise retrieve the data from tmdbi api
            else:
                result = tmdb_movie.search(title)
                movie_id = result[0].id
                response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key={}'.format(movie_id, tmdb.api_key))
                data_json = response.json()
                # Fetching movie title and poster link
                movie_title = data_json['title']
                movie_poster_link = "https://image.tmdb.org/t/p/original" + data_json['poster_path']
                movie_tag_line = data_json['tagline']

                # Appending movie title and poster link into dictionary
                dic_data['Movie_Title'].append(movie_title)
                dic_data['Poster_Links'].append(movie_poster_link)
                dic_data['Tag_Line'].append(movie_tag_line)
        except:
            pass

    return dic_data

def recommendation(title):
            
            title = title.lower()
            # create count matrix from this new combined column
            cv = CountVectorizer(stop_words='english')
            count_matrix = cv.fit_transform(df['comb'])

            # now compute the cosine similarity
            cosine_sim = cosine_similarity(count_matrix)

            # correcting user input spell (close match from our movie list)
            correct_title = get_close_matches(title, movie_list, n=3, cutoff=0.6)[0]

            # get the index value of given movie title
            idx = df['movie_title'][df['movie_title'] == correct_title].index[0]

            # get the pairwise similarity scores of all movies with that movie
            sim_score = list(enumerate(cosine_sim[idx]))

            # sort the movie based on similarity scores
            sim_score = sorted(sim_score, key=lambda x: x[1], reverse=True)[0:15]

            # suggested movies are storing into a list
            suggested_movie_list = []
            for i in sim_score:
                movie_index = i[0]
                suggested_movie_list.append(df['movie_title'][movie_index])

            # calling get_poster_link function to fetch their title and poster link.
            main_movie = get_poster_link_main(suggested_movie_list[0])
            
            poster_title_link = get_poster_link(suggested_movie_list)
            return main_movie,poster_title_link


def get_trending_movies():

    # Storing data in to dictionary
    dic_data = []
    genre_list = {28: 'Action',12: 'Adventure',16: 'Animation',35: 'Comedy',80: 'Crime',
                99: 'Documentary',18: 'Drama',10751: 'Family',14: 'Fantasy',36: 'History',
                27: 'Horror',10402: 'Music',9648: 'Mystery',10749: 'Romance',
                878: 'Science Fiction',10770: 'TV Movie',53: 'Thriller',10752: 'War',37: 'Western'}

    try:
        response = requests.get('https://api.themoviedb.org/3/trending/movie/day?api_key={}'.format(tmdb.api_key))
        data_json = response.json()
        # Fetching movie title and poster link
        for data in data_json["results"]:
            movie_title=data['title']
            movie_poster_link="https://image.tmdb.org/t/p/original" + data['poster_path']
            movie_rating=data['vote_average']
            movie_overview=data['overview']
            movie_releasedate=data['release_date']
            movie_genre=[]
            for gen in data['genre_ids']:
                movie_genre.append(genre_list[gen])
            # Appending movie details into dictionary
            dic_data.append({'Movie_Title':movie_title,'Poster_Links':movie_poster_link,
                            'Rating':movie_rating,'Genre':movie_genre,'Overview':movie_overview,
                            'Release_Date':movie_releasedate})
          
    except:
        pass
    return dic_data

def get_popular_movies():

    # Storing data in to dictionary
    dic_data = []
    genre_list = {28: 'Action',12: 'Adventure',16: 'Animation',35: 'Comedy',80: 'Crime',
                99: 'Documentary',18: 'Drama',10751: 'Family',14: 'Fantasy',36: 'History',
                27: 'Horror',10402: 'Music',9648: 'Mystery',10749: 'Romance',
                878: 'Science Fiction',10770: 'TV Movie',53: 'Thriller',10752: 'War',37: 'Western'}

    try:
        response = requests.get('https://api.themoviedb.org/3/movie/popular?api_key={}'.format(tmdb.api_key))
        data_json = response.json()
        # Fetching movie title and poster link
        for data in data_json["results"]:
            movie_title=data['title']
            movie_poster_link="https://image.tmdb.org/t/p/original" + data['poster_path']
            movie_rating=data['vote_average']
            movie_overview=data['overview']
            movie_releasedate=data['release_date']
            movie_genre=[]
            for gen in data['genre_ids']:
                movie_genre.append(genre_list[gen])
            # Appending movie details into dictionary
            dic_data.append({'Movie_Title':movie_title,'Poster_Links':movie_poster_link,
                            'Rating':movie_rating,'Genre':movie_genre,'Overview':movie_overview,
                            'Release_Date':movie_releasedate})
          
    except:
        pass
    return dic_data

def get_top_rated_movies():

    # Storing data in to dictionary
    dic_data = []
    genre_list = {28: 'Action',12: 'Adventure',16: 'Animation',35: 'Comedy',80: 'Crime',
                99: 'Documentary',18: 'Drama',10751: 'Family',14: 'Fantasy',36: 'History',
                27: 'Horror',10402: 'Music',9648: 'Mystery',10749: 'Romance',
                878: 'Science Fiction',10770: 'TV Movie',53: 'Thriller',10752: 'War',37: 'Western'}

    try:
        response = requests.get('https://api.themoviedb.org/3/movie/top_rated?api_key={}'.format(tmdb.api_key))
        data_json = response.json()
        # Fetching movie title and poster link
        for data in data_json["results"]:
            movie_title=data['title']
            movie_poster_link="https://image.tmdb.org/t/p/original" + data['poster_path']
            movie_rating=data['vote_average']
            movie_overview=data['overview']
            movie_releasedate=data['release_date']
            movie_genre=[]
            for gen in data['genre_ids']:
                movie_genre.append(genre_list[gen])
            # Appending movie details into dictionary
            dic_data.append({'Movie_Title':movie_title,'Poster_Links':movie_poster_link,
                            'Rating':movie_rating,'Genre':movie_genre,'Overview':movie_overview,
                            'Release_Date':movie_releasedate})
          
    except:
        pass
    return dic_data

def get_upcoming_movies():

    # Storing data in to dictionary
    dic_data = []
    genre_list = {28: 'Action',12: 'Adventure',16: 'Animation',35: 'Comedy',80: 'Crime',
                99: 'Documentary',18: 'Drama',10751: 'Family',14: 'Fantasy',36: 'History',
                27: 'Horror',10402: 'Music',9648: 'Mystery',10749: 'Romance',
                878: 'Science Fiction',10770: 'TV Movie',53: 'Thriller',10752: 'War',37: 'Western'}

    try:
        response = requests.get('https://api.themoviedb.org/3/movie/upcoming?api_key={}'.format(tmdb.api_key))
        data_json = response.json()
        # Fetching movie title and poster link
        for data in data_json["results"]:
            movie_title=data['title']
            movie_poster_link="https://image.tmdb.org/t/p/original" + data['poster_path']
            movie_rating=data['vote_average']
            movie_overview=data['overview']
            movie_releasedate=data['release_date']
            movie_genre=[]
            for gen in data['genre_ids']:
                movie_genre.append(genre_list[gen])
            # Appending movie details into dictionary
            dic_data.append({'Movie_Title':movie_title,'Poster_Links':movie_poster_link,
                            'Rating':movie_rating,'Genre':movie_genre,'Overview':movie_overview,
                            'Release_Date':movie_releasedate})
          
    except:
        pass
    return dic_data



@app.route('/', methods=['GET'])  # route to display the Home Page
@cross_origin()
def home():
    return render_template('index.html',movies_trending=movies_trending,
    movies_popular=movies_popular,
    movies_upcoming=movies_upcoming,
    movies_top_rated=movies_top_rated,
    movie_titles=df['movie_title'])

@app.route('/', methods=['POST', 'GET'])  # route to show the recommendation in web UI
@cross_origin()
# This function take movie name from user, and return 10 similar type of movies.
def moviesingle():
    if request.method == 'POST':
    # reading the inputs given by the user
        try:
            title = request.form["search"]
            main_movie, suggested_movies = recommendation(title)
            return render_template("moviesingle.html",movie=main_movie, output=suggested_movies,movie_titles=df['movie_title'])
        except:
            return render_template("404error.html",movie_titles=df['movie_title'])


@app.route("/landing")
def landing():
    return render_template('landing.html')

@app.route("/404error")
def error404():
    return render_template('404error.html',movie_titles=df['movie_title'])

@app.route("/trending")
def trending():
    return render_template('moviegridfw.html',title="Trending",movies=movies_trending,movie_titles=df['movie_title'])

@app.route("/popular")
def popular():
    return render_template('moviegridfw.html',title="Popular",movies=movies_popular,movie_titles=df['movie_title'])

@app.route("/toprated")
def toprated():
    return render_template('moviegridfw.html',title="Top Rated",movies=movies_top_rated,movie_titles=df['movie_title'])

@app.route("/upcoming")
def upcoming():
    return render_template('moviegridfw.html',title="Upcoming",movies=movies_upcoming,movie_titles=df['movie_title'])

@app.route("/moviedetails", methods=['POST', 'GET'])
def moviedetails():
    if request.method == 'GET':
        try:
            if request.args.get("trending") != None:
                search=request.args.get("trending")
                for movie in movies_trending:
                    if search in movie['Movie_Title']:
                        return render_template('moviedetails.html',movie=movie)
                        break
                    else:
                        pass
            elif request.args.get("popular") != None:
                search=request.args.get("popular")
                for movie in movies_popular:
                    if search in movie['Movie_Title']:
                        return render_template('moviedetails.html',movie=movie)
                        break
                    else:
                        pass
            elif request.args.get("top_rated") != None:
                search=request.args.get("top_rated")
                for movie in movies_top_rated:
                    if search in movie['Movie_Title']:
                        return render_template('moviedetails.html',movie=movie)
                        break
                    else:
                        pass
            elif request.args.get("upcoming") != None:
                search=request.args.get("upcoming")
                for movie in movies_upcoming:
                    if search in movie['Movie_Title']:
                        return render_template('moviedetails.html',movie=movie)
                        break
                    else:
                        pass
            else:
                pass      
        except:
            return render_template("404error.html",movie_titles=df['movie_title'])


movies_trending = get_trending_movies()
movies_popular = get_popular_movies()
movies_upcoming = get_upcoming_movies()
movies_top_rated = get_top_rated_movies()

if __name__ == '__main__':
    print("App is running")
    app.run(debug=True)
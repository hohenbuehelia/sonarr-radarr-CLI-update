from tmdbv3api import Movie
from tmdbv3api import TMDb
from tmdbv3api import TV
from tmdbv3api import Season
import tmdbsimple
import time
import sqlite3
import requests
import json


tmdb = TMDb()
tv = TV()
season = Season()
tmdb.api_key = ''
radarr_api_key = ''
sonarr_api_key = ''
home_IP = ''
radarr_port = ':'
sonarr_port = ':'
tmdbsimple.API_KEY = tmdb.api_key
tmdb.language = 'en'
tmdb.debug = False
movie_dict = {}
tv_dict = {}
last_season = 1
season_count = 1
movie = Movie()
connection = sqlite3.connect('trakt.db')
crsr = connection.cursor()
sql_command = ''


def movie_search():
    global sql_command
    sql_command = """CREATE TABLE IF NOT EXISTS movies (  
    ref_num INTEGER,  
    mname VARCHAR(20),  
    released DATE,  
    TMDB_ID INTEGER PRIMARY KEY,
    IMDB_ID INTEGER,
    rating INTEGER,
    description VARCHAR(30));"""
    crsr.execute(sql_command)
    user_movie = input('Enter the movie you want to search: ')  # this will need to be a search bar
    results = movie.search(user_movie)
    result_count = 0
    for result in results:
        movie_name = result.title
        tmdbId = result.id
        baseurl = "https://api.themoviedb.org/3/movie/"
        response = requests.request("GET", baseurl + str(tmdbId) + '/external_ids?api_key=' + tmdb.api_key
                                    + '&language=en-US')
        imdb_dirty = response.json()
        imdbId = imdb_dirty['imdb_id']
        crsr.execute('SELECT * FROM movies')
        sql_select_movie = """select * from movies where TMDB_ID = ?"""
        check = crsr.execute(sql_select_movie, (tmdbId,))  # assigns
        pass_var = 0
        try:
            # this is checking if it exists in the SQL database already, if it = 0, then it doesn't
            if check.fetchone()[0] == 0:
                description = 'Could not find description.'
                try:
                    description = movie.details(movie_id=tmdbId)
                except KeyError:
                    pass  # passes if the description doesn't exist, leaving desc not found
                search = tmdbsimple.Search()
                response = search.movie(query=movie_name)
                release_cc = (response['results'])
                rating = result.vote_average
                release = 'Could not find release date.'
                try:
                    # attempts to find the english release date if it exists
                    for i in release_cc:
                        if i['original_language'] == 'en':
                            release = i['release_date']
                except KeyError:
                    pass
                try:
                    # if the movie was able to be successfully found and populated it adds it to the database
                    result_count = result_count + 1
                    crsr.execute(
                        """
                        INSERT INTO movies
                        (ref_num, mname, released, TMDB_ID, IMDB_ID, rating, description)
                        values (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (str(result_count), str(movie_name), str(release), str(tmdbId), str(imdbId), str(rating),
                         str(description.overview))
                    )
                    movie_dict[result_count] = tmdbId
                except AttributeError:
                    # print(str(movie_name) + ' failed at 2')
                    result_count = result_count - 1
                    pass
            else:
                # if it already exists in the database it skips the previous step
                pass_var = 1
                pass
        except TypeError:
            # print(str(movie_name) + ' failed at 1')
            description = 'Could not find description.'
            try:
                description = movie.details(movie_id=tmdbId)
            except KeyError:
                pass
            search = tmdbsimple.Search()
            response = search.movie(query=movie_name)
            release_cc = (response['results'])
            rating = result.vote_average
            release = 'Could not find release date.'
            try:
                for i in release_cc:
                    if i['original_language'] == 'en':
                        release = i['release_date']
            except KeyError:
                pass
            try:
                result_count = result_count + 1
                crsr.execute(
                    """
                    INSERT INTO movies
                    (ref_num, mname, released, TMDB_ID, IMDB_ID, rating, description)
                    values (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (str(result_count), str(movie_name), str(release), str(tmdbId), str(imdbId), str(rating),
                     str(description.overview))
                )
                movie_dict[result_count] = tmdbId
            except AttributeError:
                print(str(movie_name) + ' failed at 3')
                result_count = result_count - 1
                pass
        crsr.execute(sql_select_movie, (tmdbId,))
        ans = crsr.fetchall()
        for i in ans:
            print(' ' + i[1] + '\n' +
                  ' Released: ' + str(i[2]) + '\n' +
                  ' TMDB ID: ' + str(i[3]) + '\n' +
                  ' IMDB ID: ' + str(i[4]) + '\n' +
                  ' Rating: ' + str(i[5]) + '\n' +
                  ' ' + str(i[6]) + '\n')
        crsr.connection.commit()
        if pass_var == 0:
            time.sleep(1)
        else:
            pass
    pick = input('Would you like to choose a movie? [Yes / No] ')  # this should be a dialog box with yes/no answer
    if pick == 'Yes':  # Yes button
        movie_user_choice()
    elif pick == 'No':  # no button obvs
        pick2 = input("Would you like to restart "
                      "the program? [Yes / No] ")  # this should be a dialog box with yes/no answer
        if pick2 == 'Yes':  # yes button
            main()
        elif pick2 == 'No':  # no button
            print('Program ending.')  # dialog box saying something nice like, 'Happy pirating' or some shit
            connection.close()
            exit(0)
    else:
        print('Incorrect usage, ending program.')  # this part should be gone with buttons
        connection.close()
        exit(0)


def tv_search():
    global tv_dict
    global sql_command
    sql_command = """CREATE TABLE IF NOT EXISTS shows (  
    ref_num INTEGER,  
    shname VARCHAR(20),  
    released DATE,  
    TMDB_ID INTEGER PRIMARY KEY,
    IMDB_ID INTEGER,
    TVDB_ID INTEGER,
    description VARCHAR(30));"""
    crsr.execute(sql_command)
    user_show = input('Enter the TV Show you want to search: ')
    results = tv.search(user_show)
    result_count = 0
    pass_var = 0
    for result in results:
        result_count = result_count + 1
        tv_name = result.name
        tmdbId = result.id
        baseurl = "https://api.themoviedb.org/3/tv/"
        response = requests.request("GET", baseurl + str(tmdbId) + '/external_ids?api_key=' + tmdb.api_key
                                    + '&language=en-US')
        imdb_dirty = response.json()
        tvdbId = imdb_dirty['tvdb_id']
        imdbId = imdb_dirty['imdb_id']
        crsr.execute('SELECT * FROM shows')
        sql_select_show = """select * from shows where TMDB_ID = ?"""
        check = crsr.execute(sql_select_show, (tmdbId,))
        try:
            if check.fetchone()[0] == 0:
                try:
                    description = tv.details(show_id=tmdbId)
                    first_season = season.details(tmdbId, 1)
                    release = first_season.air_date
                    crsr.execute(
                        """
                        INSERT INTO shows
                        (ref_num, shname, released, TMDB_ID, IMDB_ID, TVDB_ID, description)
                        values (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (result_count, tv_name, release, tmdbId, imdbId, tvdbId, description.overview)
                    )
                except AttributeError:
                    # this shit looks ugly as hell, but it was the easiest way to find out if the desc or release date
                    # could not be found and continue if one or the other couldn't be
                    # print('failed at try 2')
                    try:
                        first_season = season.details(tmdbId, 1)
                        release = first_season.air_date
                        crsr.execute(
                            """
                            INSERT INTO shows
                            (ref_num, shname, released, TMDB_ID, IMDB_ID, TVDB_ID, description)
                            values (?, ?, ?, ?, ?, ?, ?);
                            """,
                            (result_count, tv_name, release, tmdbId, imdbId, tvdbId, "Description could not be found.")
                        )
                    except AttributeError:
                        # print('failed at try 2.1')
                        try:
                            description = tv.details(show_id=tmdbId)
                            crsr.execute(
                                """
                                INSERT INTO shows
                                (ref_num, shname, released, TMDB_ID, IMDB_ID, TVDB_ID, description)
                                values (?, ?, ?, ?, ?, ?, ?);
                                """,
                                (result_count, tv_name, 'Release date could not be found.', tmdbId, imdbId, tvdbId,
                                 description.overview)
                            )
                        except AttributeError:
                            # print('failed at try 2.2')
                            crsr.execute(
                                """
                                INSERT INTO shows
                                (ref_num, shname, released, TMDB_ID, IMDB_ID, TVDB_ID, description)
                                values (?, ?, ?, ?, ?, ?, ?);
                                """,
                                (result_count, tv_name, 'Release date could not be found.', tmdbId, imdbId, tvdbId,
                                 "Description could not be found.")
                            )
            else:
                pass_var = 1
                pass
        except TypeError:
            # print('failed at try 1')
            try:
                description = tv.details(show_id=tmdbId)
                first_season = season.details(tmdbId, 1)
                release = first_season.air_date
                crsr.execute(
                    """
                    INSERT INTO shows
                    (ref_num, shname, released, TMDB_ID, IMDB_ID, TVDB_ID, description)
                    values (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (result_count, tv_name, release, tmdbId, imdbId, tvdbId, description.overview)
                )
            except AttributeError:
                # this shit looks ugly as hell, but it was the easiest way to find out if the desc or release date
                # could not be found and continue if one or the other couldn't be
                # print('failed at try 1.1')
                try:
                    first_season = season.details(tmdbId, 1)
                    release = first_season.air_date
                    crsr.execute(
                        """
                        INSERT INTO shows
                        (ref_num, shname, released, TMDB_ID, IMDB_ID, TVDB_ID, description)
                        values (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (result_count, tv_name, release, tmdbId, imdbId, tvdbId, "Description could not be found.")
                    )
                except AttributeError:
                    # print('failed at try 1.2')
                    try:
                        description = tv.details(show_id=tmdbId)
                        crsr.execute(
                            """
                            INSERT INTO shows
                            (ref_num, shname, released, TMDB_ID, IMDB_ID, TVDB_ID, description)
                            values (?, ?, ?, ?, ?, ?, ?);
                            """,
                            (result_count, tv_name, 'Release date could not be found.', tmdbId, imdbId, tvdbId,
                             description.overview)
                        )
                    except AttributeError:
                        # print('failed at try 1.3')
                        crsr.execute(
                            """
                            INSERT INTO shows
                            (ref_num, shname, released, TMDB_ID, IMDB_ID, TVDB_ID, description)
                            values (?, ?, ?, ?, ?, ?, ?);
                            """,
                            (result_count, tv_name, 'Release date could not be found.', tmdbId, imdbId, tvdbId,
                             "Description could not be found.")
                        )
        tv_dict[result_count] = str(tmdbId)
        crsr.execute(sql_select_show, (tmdbId,))
        ans = crsr.fetchall()
        for i in ans:
            print(' ' + i[1] + '\n' +
                  ' Released: ' + str(i[2]) + '\n' +
                  ' TMDB ID: ' + str(i[3]) + '\n' +
                  ' IMDB ID: ' + str(i[4]) + '\n' +
                  ' TVDB ID: ' + str(i[5]) + '\n' +
                  ' ' + str(i[6]) + '\n')
        crsr.connection.commit()
        if pass_var == 0:
            time.sleep(2)
        else:
            pass
    pick = input('Would you like to choose a show? [Yes / No] ')
    if pick == 'Yes':
        show_user_choice()
    elif pick == 'No':
        pick2 = input("Would you like to restart the program? [Yes / No] ")
        if pick2 == 'Yes':
            main()
        elif pick2 == 'No':
            print('Program ending.')
            connection.close()
            exit(0)
    else:
        print('Incorrect usage, ending program.')
        connection.close()
        exit(0)


def movie_user_choice():
    inp_num = input('Type the TMDB ID of the movie you want to add: ')
    sql_select_movie = """select * from movies where TMDB_ID = ?"""
    check = crsr.execute(sql_select_movie, (inp_num,))
    if check.fetchone() is not None:
        response = requests.request("GET", home_IP + radarr_port + '/api/movie/lookup/tmdb?tmdbId=' + inp_num +
                                    '&apikey=' + radarr_api_key)
        clean_json = response.json()
        tmdbId = int(inp_num)
        title = clean_json['title']
        qualityProfileId = 4
        titleSlug = clean_json['titleSlug']
        images = clean_json['images']
        year = clean_json['year']
        rootFolderPath = 'd:\\Movies'
        monitored = True
        addOptions = {
            "searchForMovie": True
        }
        data = \
            {
                'title': title,
                'qualityProfileId': qualityProfileId,
                'titleSlug': titleSlug,
                'images': images,
                'tmdbId': tmdbId,
                'year': year,
                'rootFolderPath': rootFolderPath,
                'monitored': monitored,
                'addOptions': addOptions
            }
        headers = {'Content-type': 'application/json'}
        url = home_IP + radarr_port + '/api/movie?apikey=' + radarr_api_key
        r = requests.post(url=url, data=json.dumps(data, indent=2), headers=headers)
        if r.status_code != 201:
            print(r.status_code)
            print(r.reason)
            print(r.text)
        else:
            print('Success. Added ' + title + ' to the download queue.')
            connection.close()
            exit(0)
    else:
        print('TMDB ID not in database, please run the program again and search for the movie.')
        connection.close()
        exit(0)


def show_user_choice():
    inp_num = input('Type the TVDB ID of the show you want to add: ')
    sql_select_show = """select * from shows where TVDB_ID = ?"""
    check = crsr.execute(sql_select_show, (inp_num,))
    if check.fetchone()[0] == 1:
        response = requests.request("GET", home_IP + sonarr_port + '/api/series/lookup?term=tvdb:' + inp_num +
                                    '&apikey=' + sonarr_api_key)
        dirty_json = response.json()
        tvdbId = int(inp_num)
        for i in dirty_json:
            clean_json = i
            title = clean_json['title']
            qualityProfileID = 6
            titleSlug = clean_json['titleSlug']
            images = clean_json['images']
            rootFolderPath = 'd:\\TV Shows'
            seasons = clean_json['seasons']
            monitored = True
            data = \
                {
                    'tvdbId': tvdbId,
                    'title': title,
                    'qualityProfileID': qualityProfileID,
                    'titleSlug': titleSlug,
                    'images': images,
                    'rootFolderPath': rootFolderPath,
                    'seasons': seasons,
                    'monitored': monitored
                }
            headers = {'Content-type': 'application/json'}
            url = home_IP + sonarr_port + '/api/series?apikey=' + sonarr_api_key
            r = requests.post(url=url, data=json.dumps(data, indent=2), headers=headers)
            print(data)
            if r.status_code != 201:
                print(r.status_code)
                print(r.reason)
                print(r.text)
            else:
                print('Success. Added ' + title + ' to the download queue.')
                connection.close()
                exit(0)
    else:
        print('TVDB ID not in database, please run the program again and search for the show.')
        connection.close()
        exit(0)


def main():
    tv_or_movie = input('Do you want to search for a Movie or a TV Show? ')
    if tv_or_movie == 'TV Show':
        tv_search()
    elif tv_or_movie == 'Movie':
        movie_search()
    else:
        print("Please type 'Movie' or 'TV Show'")
        main()
    connection.close()
    print('You shouldn\'t have gotten here. Fucking damn it.')
    exit(0)


main()

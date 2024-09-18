from flask import Flask, render_template, jsonify, request , Response ,send_file, session
import asyncio
import csv
from shazamio import Shazam
import time
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import json
from datetime import datetime, timedelta
from io import StringIO
app = Flask(__name__)
app.secret_key = 'this_is_the_secret_key_for_my_shazam_web_app'
UPLOAD_FOLDER = 'static/upload_partial_wav'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

details = {}
is_listening = False
stop_listening = False
current_details_song = ''
var_for_stop = {}

async def find_song(file_path):
    global details,current_details_song
    shazam = Shazam()
    out = await shazam.recognize(file_path)
    if out.get("track"):
        details = out
        current_details_song = out           
        save_to_csv_and_database(details['track']['title'], details['track']['subtitle'],details)
        if os.path.exists(file_path):
            os.remove(file_path)
        return out  
    else:
        if session:
            adding_stop_time()
        return None
    

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize the database
db = SQLAlchemy(app)

class SongData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_international_code = db.Column(db.Integer)
    title = db.Column(db.String(120), nullable=False)
    sub_title = db.Column(db.String(120))
    artist = db.Column(db.String(120))
    album_title = db.Column(db.Text)
    released_year = db.Column(db.Text)
    song_played = db.Column(db.Integer , default=1)
    timestamp = db.Column(db.DateTime)
    bg_image = db.Column(db.Text)
    shazam_link = db.Column(db.Text)
    raw_data = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)
    
    # Define a relationship to the MusicRepeatedDetails table
    details = relationship('MusicRepeatedDetails', backref='song_data', lazy=True)
    def __repr__(self):
        return f'<User {self.title}>'

    
    
class MusicRepeatedDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_international_code = db.Column(db.Integer, ForeignKey('song_data.unique_international_code'), nullable=False)
    music_repeated_played = db.Column(db.Integer)
    title = db.Column(db.String(120))

    def __repr__(self):
        return f'<MusicRepeatedDetails {self.id}>'

with app.app_context():
    db.create_all()

def save_to_csv_and_database(title, artist, details):
    last_song = SongData.query.order_by(SongData.id.desc()).first()
    if last_song is not None and last_song.title == title:
        # Calculate the time difference
        time_difference = datetime.now() - last_song.timestamp

        # Check if the time difference is more than 5 minutes
        if time_difference <= timedelta(minutes=5):
            print(f"Song with title '{title}' was recently added within the last 5 minutes.")
            return  # Skip inserting the song
    album_title_single = None
    released_year_single = None
    raw_data_json = json.dumps(details)

    # Loop through the sections to find the "SONG" type
    for section in details['track']['sections']:
        if section['type'] == 'SONG':
            # Loop through the metadata to find Album and Released year
            for item in section['metadata']:
                if item['title'] == 'Album':
                    album_title_single = item['text']
                elif item['title'] == 'Released':
                    released_year_single = item['text']

    unique_international_code = details['track']['key']
    sub_title = details['track']['subtitle']
    bg_image = details['track']['images']['background']
    shazam_link = details['track']['share']['href']
    song_played = 1
    # Get the current timestamp as a datetime object
    timestamp = datetime.now()
    add_song = SongData(
        title=title,
        sub_title=sub_title,
        artist=artist,
        bg_image=bg_image,
        shazam_link=shazam_link,
        album_title=album_title_single,
        released_year=released_year_single,
        raw_data=raw_data_json,
        unique_international_code=unique_international_code,
        song_played=song_played,
        timestamp=timestamp,
        start_time=timestamp
    )    
    
    # check in songdata table if the song is there or not
    check_in_song_data = SongData.query.filter_by(unique_international_code=unique_international_code).first()
    if check_in_song_data:
        add_repeated_music = MusicRepeatedDetails.query.filter_by(unique_international_code= unique_international_code).first() 
        if add_repeated_music:
            add_repeated_music.music_repeated_played += 1
        else:
            add_repeated_music = MusicRepeatedDetails(
            title = title,
            unique_international_code = unique_international_code,
            music_repeated_played = 1
        )        
    else:
        add_repeated_music = MusicRepeatedDetails(
            title = title,
            unique_international_code = unique_international_code,
            music_repeated_played = 1
        )

    
    db.session.add(add_song)
    db.session.add(add_repeated_music)
    db.session.commit()
    
    if session :
        if session['current_song_id'] != add_song.id :
            session['previous_adding_the_stop_time'] = True
            session['previous_song_id'] = session['current_song_id']
            adding_stop_time()
    session['current_song_id'] = add_song.id
    session['unique_international_code'] = add_song.unique_international_code

    with open('static/song_history.csv', mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([unique_international_code, timestamp, title, sub_title, artist,song_played,  album_title_single, released_year_single,bg_image, shazam_link, raw_data_json])

def adding_stop_time():
    print('adding-stop-time')
    print('----'*10)
    if session:
        if session.get('previous_adding_the_stop_time'):
            updating_stop_time(session['previous_song_id'])
            session.pop('previous_adding_the_stop_time' , None)
            session.pop('previous_song_id' , None)
            
        else:  
            updating_stop_time(session['current_song_id'])               
            session.clear()

def updating_stop_time(user_id):
    toBeUpdateSong = SongData.query.get(user_id)
    if toBeUpdateSong:
        latest_time = datetime.now()
        duration = (latest_time - toBeUpdateSong.start_time).seconds
        
        toBeUpdateSong.end_time = latest_time 
        toBeUpdateSong.duration = duration
        db.session.commit()    

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recorder')
def recorder():
    return render_template('recorder.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        # file.save(r'static/upload_partial_wav' + file.filename)  
        file_path = os.path.join('static', 'upload_partial_wav', file.filename)
        file.save(file_path)  
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        data = loop.run_until_complete(find_song(file_path))
        if data:
            return jsonify(data)
        else:
            return jsonify({'data' : False})

@app.route('/subscribe' , methods = ['GET' , 'POST'])
def subscribe():
    if request.method == 'POST':
        email_sub = request.form.get('email')
        with open('subscription.csv' , 'a' , newline='') as csvfile:    
            fieldnames = ['email']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({'email': email_sub})
    return Response('Successfully Subscribed')


@app.route('/recent_songs', methods=['GET'])
def recent_songs():
    recent_songs = SongData.query.order_by(SongData.timestamp.desc()).limit(6).all()
    songs = [
        {
            'title': song.title,
            'artist': song.sub_title,
            'bg_image': song.bg_image,
            'shazam_link': song.shazam_link,
            'timestamp': song.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for song in recent_songs
    ]
    return jsonify(songs)


@app.route('/top_3', methods=['GET'])
def top_3():
    top_tracks = MusicRepeatedDetails.query.order_by(MusicRepeatedDetails.music_repeated_played.desc()).limit(3).all()
    unique_international_codes = [track.unique_international_code for track in top_tracks]
    
    distinct_songs = []
    for i in unique_international_codes:
        data = SongData.query.filter_by(unique_international_code=i).first()
        if data:  # Make sure data is not None before appending
            distinct_songs.append(data)

    top_songs = [
        {
            'title': song.title,
            'artist': song.artist,
            'album_title': song.album_title,
            'released_year': song.released_year,
            'bg_image': song.bg_image,
            'shazam_link': song.shazam_link,
            'timestamp': song.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'play_count': next((track.music_repeated_played for track in top_tracks if track.unique_international_code == song.unique_international_code), 0)
        } for song in distinct_songs
    ]
    return jsonify(top_songs)

@app.route('/details_table', methods=['GET'])
def details_table():
    recent_songs_table = SongData.query.order_by(SongData.timestamp.desc()).limit(10).all()
    songs = [
        {
            'title': song.title,
            'artist': song.sub_title,
            'bg_image': song.bg_image,
            'shazam_link': song.shazam_link,
            'timestamp': song.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'date': song.timestamp.strftime('%Y-%m-%d'),
            'start_time': song.start_time.strftime('%H:%M:%S')  if song.start_time else ' - '  ,
            'end_time': song.end_time.strftime('%H:%M:%S')  if song.end_time else ' - '  ,
            'duration': format_duration(song.duration) if song.duration else ' - '
        } for song in recent_songs_table
    ]
    return jsonify(songs)


def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours:02}:{minutes:02}:{seconds:02}'
@app.route('/download_csv')
def download_csv():
    songs = SongData.query.all()
    # Use StringIO to write CSV content in memory
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Unique International Code', 'Title', 'Subtitle', 'Artist', 'Album Title', 'Released Year', 'Song Played', 'Timestamp', 'Start Time','End Time', 'Duration' 'Background Image', 'Shazam Link'])

    # Write the data for each song
    for song in songs:
        writer.writerow([
            song.id,
            song.unique_international_code,
            song.title,
            song.sub_title,
            song.artist,
            song.album_title,
            song.released_year,
            song.song_played,
            song.timestamp.strftime('%Y-%m-%d %H:%M:%S') if song.timestamp else '',
            song.start_time.strftime('%Y-%m-%d %H:%M:%S') if song.start_time else '',
            song.end_time.strftime('%Y-%m-%d %H:%M:%S') if song.end_time else '',
            song.duration,
            song.shazam_link
        ])
    
    # Move back to the start of the StringIO object
    output.seek(0)
    
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=data.csv"}
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug = 'true',ssl_context = 'adhoc')
    # app.run(host='0.0.0.0', debug = 'true')

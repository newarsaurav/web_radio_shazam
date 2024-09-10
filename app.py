from flask import Flask, render_template, jsonify, request , Response
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
app = Flask(__name__)

UPLOAD_FOLDER = 'static/upload_partial_wav'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

details = {}
is_listening = False
stop_listening = False
current_details_song = ''

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
        timestamp=timestamp
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

    with open('static/song_history.csv', mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([unique_international_code, timestamp, title, sub_title, artist,song_played,  album_title_single, released_year_single,bg_image, shazam_link, raw_data_json])


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
        # file.save(r'static/upload_partial_wav' + file.filename)  
        print(f"received at{time.time()}")
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


if __name__ == '__main__':
    app.run(host='0.0.0.0',ssl_context = 'adhoc')

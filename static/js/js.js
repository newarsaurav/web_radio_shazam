

// function fetchCurrentSong() {
//     $.get('/current_song', function (data) {
//         updateSongCard(data);
//     });
// }

// $(document).ready(function () {
//     setInterval(fetchCurrentSong, 5000); // Fetch every 5 seconds
// });

function updateRecentSongs(songs) {
    $('#recent-songs-list').empty();  // Clear existing content
    songs.forEach(function (song, index) {
        $('#recent-songs-list').append(
            `<div class="max-w-sm rounded overflow-hidden shadow-lg m-6 relative">
                    <div class="card">
                        <img class="w-full" src="${song.bg_image ?? 'https://via.placeholder.com/150'}" alt="${song.title}">
                        <a style = 'box-shadow: 0px 0px 9px 2px rgba(0, 0, 0, 0.2);' href="${song.shazam_link}" class="absolute top-4 left-4 bg-white text-gray-800 py-1 px-2 text-sm rounded" target="_blank">Listen on Shazam</a>
                        
                        <div class="p-4">
                            <h4 class="font-bold text-xl mb-2">${song.title}</h4>
                            <p class="text-gray-700 mb-4">${song.artist}</p>
                            <p class="text-gray-600">${song.timestamp}</p>
                        </div>
                    </div>
                </div>`
        );
    });
}

function fetchRecentSongs() {
    $.get('/recent_songs', function (data) {
        updateRecentSongs(data);
    });
}

$(document).ready(function () {
    // fetchRecentSongs();  
    setInterval(fetchRecentSongs(), 5000);
});

function top3(songs) {

    $('#top-3-list').empty();  // Clear existing content
    songs.forEach(function (song, index) {
        $('#top-3-list').append(
            `<div class="max-w-sm rounded overflow-hidden shadow-lg m-6 relative">
                    <div class="card">
                        <img class="w-full" src="${song.bg_image ?? 'https://via.placeholder.com/150'}" alt="${song.title}">
                        <a style = 'box-shadow: 0px 0px 9px 2px rgba(0, 0, 0, 0.2);' href="${song.shazam_link}" class="absolute top-4 left-4 bg-white text-gray-800 py-1 px-2 text-sm rounded" target="_blank">Listen on Shazam</a>
                        <div class="number-overlay">${song.play_count}</div>
                        <div class="p-4">
                            <h4 class="font-bold text-xl mb-2">${song.title}</h4>
                            <p class="text-gray-700 mb-4">${song.artist}</p>
                            <p class="text-gray-600">${song.timestamp}</p>
                        </div>
                    </div>
                </div>`
        );
    });
}

function fetchTop3() {
    $.get('/top_3', function (data) {
        top3(data);
    });
}

$(document).ready(function () {
    // fetchTop3();  
    setInterval(fetchTop3(), 5000);
});


function detailTable(songs) {
    $('#table_song_data').empty();  // Clear existing content
    songs.forEach(function (song, index) {
        $('#table_song_data').append(
            `  
             <tr >
                      <td style='text-align :center;'>${song.date}</td>
                      <td style='text-align :center;'>${song.title} </td>
                      <td style='text-align :center;'>${song.artist}</td>
                      <td style='text-align :center;'>${song.start_time || '-'} </td>
                      <td style='text-align :center;'>${song.end_time || '-'}</td>
                      <td style='text-align :center;'>${song.duration || '-'}</td>
            </tr>          
            `
        );
    });
}

function fetchdetailTable() {
    $.get('/details_table', function (data) {
        detailTable(data);
    });
}

$(document).ready(function () {
    // fetchdetailTable();  
    setInterval(fetchdetailTable(), 2000);
});




$(document).ready(function () {
    let isListening = false;
    let isPlaying = false;
    let recorder = null;
    let chunks = [];
    let recordingInterval = null;
    const $toggleBtn = $('#toggle-btn');
    const RECORDING_DURATION = 10 * 1000; // 10 seconds in milliseconds

    // Function to send audio data to the server

    var formData = new FormData();

    async function sendDataToServer(voice_data) {
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: voice_data
            });
            if (response.ok) {
                const data = await response.json();
                console.log('Response from server:', data);

                if (data['track']) {
                    updateSongCard(data['track']);
                   
                } else {
                    updateSongCard(data);
                }
                fetchTop3()
                fetchRecentSongs()
                fetchdetailTable()
            }
        } catch (error) {
            console.error('Error sending data to server:', error);
        }
    }

    // Function to initialize media devices (microphone access)
    function setupAudio() {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => setupStream(stream))
                .catch(err => console.error('Microphone access error:', err));
        } else {
            console.error('getUserMedia not supported by the browser');
        }
    }

    // Setup the media stream for recording
    function setupStream(stream) {
        recorder = new MediaRecorder(stream);
        recorder.ondataavailable = e => chunks.push(e.data);
        recorder.onstop = () => {
            const blob = new Blob(chunks, { type: 'audio/ogg; codecs=opus' });
            formData.append('file', blob, 'temp.ogg');
            sendDataToServer(formData);
            chunks = [];
            formData.delete("file")

            fetchTop3()
            fetchRecentSongs()
            fetchdetailTable()
        };
    }

    // Start listening and recording audio
    function startListening() {
        if (isListening) return;
        isListening = true;

        setupAudio();

        recordingInterval = setInterval(() => {
            console.log('repeat starts here ');

            if (recorder && recorder.state === 'inactive') {
                recorder.start();
                console.log('recorder start here ----------------- ');
            }

            setTimeout(() => {
                if (recorder && recorder.state === 'recording') {
                    recorder.stop();
                    console.log('recorder stops here ----------------- ');

                }
            }, RECORDING_DURATION);

        }, 15000);
    }

    // Stop listening and recording audio
    function stopListening() {
        if (!isListening) return;
        isListening = false;

        clearInterval(recordingInterval);

        if (recorder && recorder.state !== 'inactive') {
            recorder.stop();
        }
    }

    // Toggle the recording state with the button
    $toggleBtn.click(function () {
        if (isPlaying) {
            // Stop action
            stopListening();
            $toggleBtn.removeClass("a_animation pause").addClass("play");
            isPlaying = false;
            $('#song-card').hide();
        } else {
            // Start action
            $toggleBtn.removeClass("play").addClass("a_animation pause");
            isPlaying = true;
            startListening();
        }
    });
});

// Update the song card with data received from the server
function updateSongCard(song) {
    console.log('Updating song card:', song);

    if (song && song.title) {
        $('#song-title').text(song.title);
        $('#song-artist').text(song.subtitle);
        $('#song-image').attr('src', song.images.background ?? 'https://via.placeholder.com/150');
        $('#shazam-link').attr('href', song.share.href);
        $('#song-card').show();
        console.log('Song found and displayed.');
    } else {
        console.log('No song data received.');
        $('#song-card').hide();
    }
}

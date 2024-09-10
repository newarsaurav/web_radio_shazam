// Global variables
let isRecording = false;
let mediaRecorder;
let audioChunks = [];
const $toggleBtn = $('#toggle-btn');

function startListening() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        console.log('getUserMedia supported.');
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                    if (audioChunks.length >= 5) {  // Adjust this number to change frequency of server requests
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        sendDataToServer(audioBlob);
                        audioChunks = [];  // Clear the chunks after sending
                    }
                };

                mediaRecorder.start(1000);  // Collect data every second
                isRecording = true;
                console.log('MediaRecorder started');
            })
            .catch(error => console.error('Error accessing media devices:', error));
    } else {
        console.log('getUserMedia not supported on your browser!');
    }
}

function stopListening() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        console.log('MediaRecorder stopped');
    }
}

async function sendDataToServer(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Response from server:', data);

            if (data['track']) {
                updateSongCard(data['track']);
            } else {
                updateSongCard(data);
            }
        }
    } catch (error) {
        console.error('Error sending data to server:', error);
    }
}

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

$toggleBtn.click(function () {
    if (isRecording) {
        // Stop action
        stopListening();
        $toggleBtn.removeClass("a_animation pause").addClass("play");
        $('#song-card').hide();
    } else {
        // Start action
        $toggleBtn.removeClass("play").addClass("a_animation pause");
        startListening();
    }
});

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
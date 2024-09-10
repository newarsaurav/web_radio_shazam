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

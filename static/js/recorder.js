const mic_btn = document.querySelector('#mic');
const playback = document.querySelector('.playback');
const download_btn = document.querySelector('#download');

mic_btn.addEventListener('click', ToggleMic);
download_btn.addEventListener('click', downloadAudio);


let can_record = false;
let is_recording = false;

let recorder = null;
let chunks = []

function setupAudio() {
    console.log('setup');

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({
            audio: true
        })
            .then(SetupStream)
            .catch(err => {
                console.log(err);

            });
    }
}
setupAudio()


function SetupStream(stream) {
    recorder = new MediaRecorder(stream);
    recorder.ondataavailable = e => {
        chunks.push(e.data);
    }
    recorder.onstop = e => {
        const blob = new Blob(chunks, { type: 'audio/ogg; codecs = opus;'});
        chunks = [];
        const audioURL = window.URL.createObjectURL(blob)
        playback.src = audioURL;
        download_btn.href = audioURL;
        download_btn.download = 'recorded-audio.ogg';

    }
    can_record = true;
}

function ToggleMic(){
    console.log('toggle');
    
    if(!can_record){
        console.log('err');
        return;
    } 
    is_recording = !is_recording;
    if(is_recording){
        recorder.start();
        console.log('recording');
        
    }else{
        recorder.stop();
        console.log('stop recording');
    }
}

function downloadAudio() {
    if (download_btn.href) {
        const anchor = document.createElement('a');
        anchor.href = download_btn.href;
        anchor.download = 'recorded-audio.ogg';
        anchor.click();
        
    } else {
        console.log('No audio to download');
    }
}
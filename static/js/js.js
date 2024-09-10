

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
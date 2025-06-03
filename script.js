// URL فایل JSON در GitHub
const playlistURL = "https://raw.githubusercontent.com/imohammadkamranii/mymusic/main/playlist.json";

// عناصر DOM
const audioPlayer = document.getElementById("audioPlayer");
const playlistElement = document.getElementById("playlist");

// بارگذاری فایل JSON و نمایش لینک‌ها
fetch(playlistURL)
    .then(response => {
        if (!response.ok) throw new Error("Unable to fetch playlist.json");
        return response.json();
    })
    .then(playlist => {
        playlist.forEach((track, index) => {
            const li = document.createElement("li");
            li.textContent = `Track ${index + 1}`;
            li.addEventListener("click", () => {
                audioPlayer.src = track;
                audioPlayer.play();
            });
            playlistElement.appendChild(li);
        });
    })
    .catch(error => {
        console.error("Error fetching playlist:", error);
        playlistElement.innerHTML = "<li>Unable to load playlist</li>";
    });

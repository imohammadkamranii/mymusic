// app.js

// لینک مستقیم به فایل JSON (اگر روی GitHub Pages آپلود شود)
// فرض کنید مخزن شما عمومی است و فایل playlist.json در شاخه اصلی قرار دارد:
const playlistURL = "https://raw.githubusercontent.com/imohammadkamranii/mymusic/main/playlist.json";

// تابع اصلی برای بارگذاری لیست و نمایش آن
async function loadAndRenderPlaylist() {
    try {
        const response = await fetch(playlistURL, { cache: "no-store" });
        if (!response.ok) {
            throw new Error("عدم توانایی در بارگذاری فایل playlist.json");
        }

        const songs = await response.json();
        renderPlaylist(songs);
    } catch (err) {
        console.error("خطا در دریافت لیست:", err);
        const container = document.getElementById("playlist");
        container.innerHTML = "<p class=\"error\">❌ بارگذاری لیست با خطا مواجه شد.</p>";
    }
}

// تابع نمایش لیست آهنگ‌ها در صفحه
function renderPlaylist(songs) {
    const container = document.getElementById("playlist");
    container.innerHTML = "";

    if (!Array.isArray(songs) || songs.length === 0) {
        container.innerHTML = "<p class=\"no-songs\">فعلاً آهنگی موجود نیست.</p>";
        return;
    }

    songs.forEach(song => {
        // هر آیتم آهنگ
        const item = document.createElement("div");
        item.className = "song-item";

        // بخش هدر: نام آهنگ و خواننده
        const header = document.createElement("div");
        header.className = "song-header";

        const title = document.createElement("h2");
        title.textContent = song.name;

        const artist = document.createElement("span");
        artist.textContent = song.artist;

        header.appendChild(title);
        header.appendChild(artist);

        // پلیر صوتی
        const audio = document.createElement("audio");
        audio.controls = true;

        const source = document.createElement("source");
        source.src = song.url;
        source.type = "audio/mpeg";

        audio.appendChild(source);

        // اضافه کردن به آیتم
        item.appendChild(header);
        item.appendChild(audio);

        container.appendChild(item);
    });
}

// فراخوانی تابع هنگام لود شدن صفحه
document.addEventListener("DOMContentLoaded", loadAndRenderPlaylist);

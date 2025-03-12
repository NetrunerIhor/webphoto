let currentIndex = 0;
const images = Array.from(document.querySelectorAll('.photo-thumb img'));

function openModal(index) {
    currentIndex = index;
    document.getElementById('modalImage').src = images[currentIndex].src;
    document.getElementById('photoModal').classList.remove('hidden');
    updateNavigation();
}

function closeModal() {
    document.getElementById('photoModal').classList.add('hidden');
}

function nextImage() {
    if (currentIndex < images.length - 1) {
        currentIndex++;
        openModal(currentIndex);
    }
}

function prevImage() {
    if (currentIndex > 0) {
        currentIndex--;
        openModal(currentIndex);
    }
}

function updateNavigation() {
    document.getElementById('prevButton').style.display = (currentIndex > 0) ? 'block' : 'none';
    document.getElementById('nextButton').style.display = (currentIndex < images.length - 1) ? 'block' : 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    images.forEach((img, index) => {
        img.addEventListener('click', () => openModal(index));
    });
});

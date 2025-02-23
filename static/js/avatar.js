document.addEventListener("DOMContentLoaded", function () {
    const profilePicture = document.getElementById("profilePicture");
    const fileInput = document.getElementById("fileInput");
    const uploadForm = document.getElementById("uploadForm");

    profilePicture.addEventListener("dblclick", function () {
        if (confirm("Хочете змінити фото профілю?")) {
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            uploadForm.submit();
        }
    });
});
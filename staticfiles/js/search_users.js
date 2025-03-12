document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".photo-share-form, .folder-share-form").forEach(form => {
        const input = form.querySelector(".usernameInput");
        const userList = form.querySelector(".userList");

        input.addEventListener("input", function () {
            let query = input.value.trim();

            if (query.length < 3) {
                userList.innerHTML = "";
                userList.classList.add("hidden");
                return;
            }

            fetch(`/search-users/?query=${query}`)
                .then(response => response.json())
                .then(data => {
                    userList.innerHTML = "";
                    if (data.users.length > 0) {
                        data.users.forEach(user => {
                            let listItem = document.createElement("li");
                            listItem.textContent = user.username;
                            listItem.classList.add("p-2", "hover:bg-gray-200", "cursor-pointer");
                            listItem.addEventListener("click", function () {
                                input.value = user.username;
                                userList.innerHTML = "";
                                userList.classList.add("hidden");
                            });
                            userList.appendChild(listItem);
                        });
                        userList.classList.remove("hidden");
                    } else {
                        userList.classList.add("hidden");
                    }
                })
                .catch(error => console.error("Помилка пошуку:", error));
        });

        document.addEventListener("click", function (event) {
            if (!input.contains(event.target) && !userList.contains(event.target)) {
                userList.classList.add("hidden");
            }
        });
    });
});
document.addEventListener("DOMContentLoaded", function () {
    const usernameInput = document.getElementById("usernameInput");
    const userList = document.getElementById("userList");

    usernameInput.addEventListener("input", function () {
        let query = usernameInput.value.trim();

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
                            usernameInput.value = user.username;
                            userList.innerHTML = "";
                            userList.classList.add("hidden");
                        });
                        userList.appendChild(listItem);
                    });
                    userList.classList.remove("hidden");
                } else {
                    userList.classList.add("hidden");
                }
            });
    });

    document.addEventListener("click", function (event) {
        if (!usernameInput.contains(event.target) && !userList.contains(event.target)) {
            userList.classList.add("hidden");
        }
    });
});
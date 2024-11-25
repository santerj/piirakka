document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector(".btn");
    button.addEventListener("click", async () => {
        try {
            const response = await axios.get("/api/hello");
            console.log(response.data);
        } catch (error) {
            console.error(error);
        }
    });
});


const startButton =
    document.getElementById("startButton");

const ideaInput =
    document.getElementById("idea");

const errorMessage =
    document.getElementById("error");

const result =
    document.getElementById("result");


startButton.addEventListener(
    "click",
    createProject
);


async function createProject() {

    const idea = ideaInput.value.trim();


    errorMessage.textContent = "";


    if (!idea) {

        errorMessage.textContent =
            "Please enter your startup idea.";

        return;
    }


    startButton.disabled = true;

    startButton.textContent =
        "ANALYZING IDEA...";


    try {

        const response = await fetch(
            "http://127.0.0.1:8000/api/projects",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    idea: idea
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Something went wrong"
            );
        }


        displayProject(data);


    } catch (error) {

        errorMessage.textContent =
            error.message;

    } finally {

        startButton.disabled = false;

        startButton.textContent =
            "START X-RAY";
    }
}


function displayProject(data) {

    result.classList.remove("hidden");


    document.getElementById(
        "projectId"
    ).textContent =
        data.project_id;


    document.getElementById(
        "problem"
    ).textContent =
        data.startup.problem;


    document.getElementById(
        "solution"
    ).textContent =
        data.startup.solution;


    document.getElementById(
        "customer"
    ).textContent =
        data.startup.target_customer;


    document.getElementById(
        "businessModel"
    ).textContent =
        data.startup.business_model;


    document.getElementById(
        "market"
    ).textContent =
        data.startup.market;


    const assumptions =
        document.getElementById(
            "assumptions"
        );


    assumptions.innerHTML = "";


    data.startup.assumptions.forEach(
        assumption => {

            const li =
                document.createElement("li");

            li.textContent =
                assumption;

            assumptions.appendChild(li);
        }
    );


    result.scrollIntoView({
        behavior: "smooth"
    });
}
// =========================================
// VENTURE X-RAY - REPORT GENERATOR
// DEBUG VERSION
// =========================================

async function generateReport() {

    const status = document.getElementById("status");
    const button = document.querySelector("button");

    // -----------------------------------------
    // GET FORM VALUES
    // -----------------------------------------

    const startupName =
        document.getElementById("startupName").value.trim();

    const problem =
        document.getElementById("problem").value.trim();

    const solution =
        document.getElementById("solution").value.trim();

    const targetMarket =
        document.getElementById("targetMarket").value.trim();

    const businessModel =
        document.getElementById("businessModel").value.trim();

    const score =
        Number(document.getElementById("score").value);

    const decision =
        document.getElementById("decision").value;


    // -----------------------------------------
    // VALIDATION
    // -----------------------------------------

    if (!startupName) {
        showError("Startup name is required.");
        return;
    }

    if (!problem) {
        showError("Problem is required.");
        return;
    }

    if (!solution) {
        showError("Solution is required.");
        return;
    }

    if (!targetMarket) {
        showError("Target market is required.");
        return;
    }

    if (!businessModel) {
        showError("Business model is required.");
        return;
    }

    if (isNaN(score) || score < 0 || score > 100) {
        showError("Defense score must be between 0 and 100.");
        return;
    }


    // -----------------------------------------
    // BUILD PAYLOAD
    // -----------------------------------------

    const data = {

        startup: {
            name: startupName,
            problem: problem,
            solution: solution,
            target_market: targetMarket,
            business_model: businessModel
        },

        refined_idea: {
            name: startupName,
            problem: problem,
            solution: solution,
            target_market: targetMarket,
            business_model: businessModel
        },

        attacker_results: [],

        vulnerabilities: [],

        defense_score: score,

        investor_conversation: [],

        decision: decision
    };


    // -----------------------------------------
    // DEBUG - SHOW EXACT PAYLOAD
    // -----------------------------------------

    console.clear();

    console.log(
        "========================================="
    );

    console.log(
        "VENTURE X-RAY DEBUG"
    );

    console.log(
        "========================================="
    );

    console.log(
        "Payload object:",
        data
    );

    console.log(
        "Payload JSON:"
    );

    console.log(
        JSON.stringify(data, null, 2)
    );

    console.log(
        "========================================="
    );


    // -----------------------------------------
    // SHOW STATUS
    // -----------------------------------------

    status.className = "";

    status.textContent =
        "Sending data to backend...";


    button.disabled = true;

    button.textContent =
        "GENERATING...";


    // -----------------------------------------
    // SEND REQUEST
    // -----------------------------------------

    try {

        const response = await fetch(
            "/generate-report",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify(data)
            }
        );


        // -------------------------------------
        // READ RAW RESPONSE
        // -------------------------------------

        const responseText =
            await response.text();


        console.log(
            "HTTP STATUS:",
            response.status
        );

        console.log(
            "HTTP STATUS TEXT:",
            response.statusText
        );

        console.log(
            "RAW BACKEND RESPONSE:",
            responseText
        );


        // -------------------------------------
        // TRY JSON PARSE
        // -------------------------------------

        let result = null;

        try {

            result =
                JSON.parse(responseText);

        } catch (jsonError) {

            console.error(
                "Response is not valid JSON:",
                jsonError
            );
        }


        // -------------------------------------
        // HANDLE HTTP ERROR
        // -------------------------------------

        if (!response.ok) {

            console.error(
                "========================================="
            );

            console.error(
                "BACKEND ERROR"
            );

            console.error(
                "========================================="
            );

            console.error(
                "Status:",
                response.status
            );

            console.error(
                "Response:",
                result || responseText
            );


            // ---------------------------------
            // DISPLAY FASTAPI VALIDATION ERRORS
            // ---------------------------------

            if (
                result &&
                result.detail &&
                Array.isArray(result.detail)
            ) {

                const errors =
                    result.detail.map(
                        (error, index) => {

                            const location =
                                error.loc
                                    ? error.loc.join(" → ")
                                    : "unknown";

                            const message =
                                error.msg ||
                                "Unknown validation error";

                            const type =
                                error.type ||
                                "unknown";

                            return (
                                `${index + 1}. ` +
                                `Location: ${location}\n` +
                                `Message: ${message}\n` +
                                `Type: ${type}`
                            );
                        }
                    ).join("\n\n");


                console.error(
                    "Pydantic validation errors:"
                );

                console.error(errors);


                showError(
                    "422 VALIDATION ERROR\n\n" +
                    errors
                );

            } else {

                showError(
                    `HTTP ${response.status}\n\n` +
                    responseText
                );
            }


            return;
        }


        // -----------------------------------------
        // SUCCESS
        // -----------------------------------------

        console.log(
            "========================================="
        );

        console.log(
            "SUCCESS"
        );

        console.log(
            "========================================="
        );

        console.log(
            "Backend result:",
            result
        );


        status.textContent =
            "✓ Report and pitch deck generated successfully.";

        status.className =
            "success";


        // -----------------------------------------
        // ENABLE DOWNLOAD LINKS
        // -----------------------------------------

        const reportLink =
            document.querySelector(
                'a[href="/download/report"]'
            );

        const pitchLink =
            document.querySelector(
                'a[href="/download/pitch"]'
            );


        if (reportLink) {

            reportLink.classList.add(
                "active"
            );

            reportLink.style.pointerEvents =
                "auto";

            reportLink.style.opacity =
                "1";
        }


        if (pitchLink) {

            pitchLink.classList.add(
                "active"
            );

            pitchLink.style.pointerEvents =
                "auto";

            pitchLink.style.opacity =
                "1";
        }


    } catch (error) {

        // -------------------------------------
        // NETWORK / JAVASCRIPT ERROR
        // -------------------------------------

        console.error(
            "========================================="
        );

        console.error(
            "REQUEST FAILED"
        );

        console.error(
            "========================================="
        );

        console.error(
            error
        );


        showError(
            "Request failed:\n\n" +
            error.message
        );

    } finally {

        button.disabled = false;

        button.textContent =
            "GENERATE REPORT";
    }
}


// =========================================
// ERROR DISPLAY
// =========================================

function showError(message) {

    const status =
        document.getElementById("status");

    status.textContent =
        "✕ " + message;

    status.className =
        "error";

    console.error(
        message
    );
}
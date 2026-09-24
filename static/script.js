let totalJobs = 0;
let safeJobs = 0;
let suspiciousJobs = 0;
let fakeJobs = 0;


const jobForm = document.getElementById("jobForm");


if (jobForm) {

    jobForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const button = document.getElementById("analyzeButton");

        button.innerHTML =
            '<i class="bi bi-hourglass-split"></i> Analyzing...';

        button.disabled = true;


        const jobData = {

            job_title:
                document.getElementById("job_title").value,

            company:
                document.getElementById("company").value,

            recruiter_email:
                document.getElementById("recruiter_email").value,

            salary:
                document.getElementById("salary").value,

            website:
                document.getElementById("website").value,

            location:
                document.getElementById("location").value,

            description:
                document.getElementById("description").value
        };


        try {

            const response = await fetch("/analyze", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(jobData)

            });


            if (!response.ok) {
                throw new Error("Server error: " + response.status);
            }


            const result = await response.json();


            displayResult(result);


        } catch (error) {

            alert("Unable to analyze the job offer.");

            console.error(error);

        }


        button.innerHTML =
            '<i class="bi bi-rocket-takeoff"></i> Analyze Now';

        button.disabled = false;

    });

}


function displayResult(result) {

    const resultBox =
        document.getElementById("resultBox");

    const prediction =
        document.getElementById("prediction");

    const riskScore =
        document.getElementById("riskScore");

    const reasons =
        document.getElementById("reasons");


    resultBox.style.display = "block";


    prediction.innerText =
        result.prediction;

    riskScore.innerText =
        result.risk_score;


    reasons.innerHTML = "";


    result.reasons.forEach(function (reason) {

        const li = document.createElement("li");

        li.innerText = reason;

        reasons.appendChild(li);

    });


    // Update statistics only if the elements exist

    totalJobs++;


    if (result.prediction === "Genuine") {

        safeJobs++;

    }

    else if (result.prediction === "Suspicious") {

        suspiciousJobs++;

    }

    else {

        fakeJobs++;

    }


    const jobsAnalyzed =
        document.getElementById("jobsAnalyzed");

    const safeJobsElement =
        document.getElementById("safeJobs");

    const suspiciousJobsElement =
        document.getElementById("suspiciousJobs");

    const fakeJobsElement =
        document.getElementById("fakeJobs");


    if (jobsAnalyzed) {
        jobsAnalyzed.innerText = totalJobs;
    }

    if (safeJobsElement) {
        safeJobsElement.innerText = safeJobs;
    }

    if (suspiciousJobsElement) {
        suspiciousJobsElement.innerText = suspiciousJobs;
    }

    if (fakeJobsElement) {
        fakeJobsElement.innerText = fakeJobs;
    }


    resultBox.scrollIntoView({
        behavior: "smooth"
    });

}
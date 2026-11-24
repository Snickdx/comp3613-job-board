(() => {
  const list = document.getElementById("application-list");
  const status = document.getElementById("application-status");

  if (!list || !status) return;

  const labels = {
    applied: "Applied",
    reviewed: "Reviewed",
    shortlisted: "Shortlisted",
    interview: "Interview",
    offered: "Offered",
    hired: "Hired",
    rejected: "Rejected",
    withdrawn: "Withdrawn",
  };

  const feedback = {
    applied: "Your application has been submitted and is awaiting review.",
    reviewed: "An employer has reviewed your application.",
    shortlisted: "Your application has been shortlisted.",
    interview: "Your application is at the interview stage.",
    offered: "An employer has made you an offer.",
    hired: "Congratulations - you have been hired.",
    rejected: "This application was rejected.",
    withdrawn: "You withdrew this application.",
  };

  async function refreshApplications() {
    status.classList.remove("is-error");
    status.textContent = "Refreshing application status...";

    try {
      const response = await fetch("/api/graduates/applications", {
        headers: { Accept: "application/json" },
      });

      if (!response.ok) {
        throw new Error("Unable to load your applications.");
      }

      const data = await response.json();
      if (!Array.isArray(data.applications)) {
        throw new Error("Unable to load your applications.");
      }
      const applications = data.applications;
      list.replaceChildren();

      if (applications.length === 0) {
        const empty = document.createElement("div");
        empty.className = "application-empty";

        const heading = document.createElement("h3");
        heading.textContent = "No applications yet";
        const copy = document.createElement("p");
        copy.textContent = "When you apply to an on-platform listing, its current status will appear here.";
        const browse = document.createElement("a");
        browse.className = "secondary";
        browse.href = "/api/jobs";
        browse.textContent = "Browse jobs";

        empty.append(heading, copy, browse);
        list.appendChild(empty);
        status.textContent = "";
        return;
      }

      applications.forEach((application) => {
        const state = String(application.state || "");
        const card = document.createElement("article");
        card.className = "application-card";
        card.dataset.status = state;

        const main = document.createElement("div");
        main.className = "application-card-main";
        const title = document.createElement("h3");
        title.textContent = application.listing_title || "Listing unavailable";
        main.appendChild(title);
        if (application.listing_company) {
          const company = document.createElement("p");
          company.className = "application-company";
          company.textContent = application.listing_company;
          main.appendChild(company);
        }

        const cardStatus = document.createElement("div");
        cardStatus.className = "application-card-status";
        const badge = document.createElement("span");
        badge.className = `status-badge status-${state}`;
        badge.textContent = labels[state] || state.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
        const copy = document.createElement("p");
        copy.textContent = feedback[state] || "This application has a status reported by the board.";
        cardStatus.append(badge, copy);

        card.append(main, cardStatus);
        list.appendChild(card);
      });
      status.textContent = "";
    } catch (error) {
      status.classList.add("is-error");
      status.textContent = error instanceof Error ? error.message : "Unable to load your applications.";
    }
  }

  refreshApplications();
})();

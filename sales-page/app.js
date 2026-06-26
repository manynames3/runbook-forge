const reportSamples = {
  ecs: {
    type: "ecs-deploy",
    title: "ECS deployment failure triage",
    summary:
      "ECS deployment for checkout-api is not stable. Most likely cause: health check failure.",
    severity: "high",
    system: "prod-shared/checkout-api",
    count: "2",
    evidence: [
      "ECS events failed target health checks",
      "Target group returned HTTP 503",
      "Task exited after startup dependency check",
    ],
    command:
      "aws ecs update-service --cluster prod-shared --service checkout-api --task-definition <previous-task-def>",
  },
  terraform: {
    type: "terraform-plan",
    title: "Terraform plan risk review",
    summary:
      "Runbook Forge found critical risk signals in the plan: public S3 access, world-open ingress, wildcard IAM, RDS replacement, and NAT Gateway cost.",
    severity: "critical",
    system: "terraform-plan",
    count: "1",
    evidence: [
      "S3 bucket policy allows public principal",
      "Security group ingress allows 0.0.0.0/0 on SSH",
      "RDS instance has delete/create replacement action",
    ],
    command: "terraform apply plan.out",
  },
  sqs: {
    type: "sqs-lambda",
    title: "SQS/Lambda backlog triage",
    summary:
      "SQS/Lambda pipeline has backlog pressure. Suspected bottleneck: Lambda throttling and timeout pressure.",
    severity: "critical",
    system: "payments-events -> payments-event-worker",
    count: "1",
    evidence: [
      "Queue depth is 18,234 messages",
      "Oldest message age is 6,120 seconds",
      "DLQ contains 143 messages",
    ],
    command:
      "aws lambda put-function-concurrency --function-name payments-event-worker --reserved-concurrent-executions <value>",
  },
};

function setReport(sampleKey) {
  const sample = reportSamples[sampleKey];
  if (!sample) return;

  document.querySelectorAll(".explorer-tab").forEach((tab) => {
    tab.setAttribute("aria-selected", String(tab.dataset.report === sampleKey));
  });
  document.querySelector("#explorer-type").textContent = sample.type;
  document.querySelector("#explorer-title").textContent = sample.title;
  document.querySelector("#explorer-summary").textContent = sample.summary;
  document.querySelector("#explorer-severity").textContent = sample.severity;
  document.querySelector("#explorer-system").textContent = sample.system;
  document.querySelector("#explorer-count").textContent = sample.count;
  document.querySelector("#explorer-command").textContent = sample.command;

  const evidenceList = document.querySelector("#explorer-evidence");
  evidenceList.replaceChildren(
    ...sample.evidence.map((item) => {
      const element = document.createElement("li");
      element.textContent = item;
      return element;
    }),
  );
}

document.querySelectorAll(".explorer-tab").forEach((tab) => {
  tab.addEventListener("click", () => setReport(tab.dataset.report));
});

import random
import uuid

from locust import HttpUser, between, task


class PRServiceUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8080"

    def on_start(self):
        self.team_name = f"team_{random.randint(0, 99)}"
        self.users = []
        self.prs = []

        response = self.client.get(f"/team/get?team_name={self.team_name}")
        if response.status_code == 200:
            data = response.json()
            if "members" in data:
                self.users = data["members"]

    @task(5)
    def create_pr(self):
        if not self.users:
            return

        author = random.choice(self.users)
        pr_id = f"pr_{uuid.uuid4().hex[:8]}"
        response = self.client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": pr_id,
                "pull_request_name": f"Feature {pr_id}",
                "author_id": author["user_id"],
            },
        )
        if response.status_code == 201:
            data = response.json()
            if "pr" in data:
                self.prs.append(data["pr"])

    @task(3)
    def merge_pr(self):
        open_prs = [pr for pr in self.prs if pr["status"] == "OPEN"]
        if not open_prs:
            return

        pr = random.choice(open_prs)
        response = self.client.post(
            "/pullRequest/merge", json={"pull_request_id": pr["pull_request_id"]}
        )
        if response.status_code == 200:
            pr["status"] = "MERGED"

    @task(2)
    def reassign_reviewer(self):
        open_prs = [
            pr for pr in self.prs if pr["status"] == "OPEN" and pr.get("assigned_reviewers")
        ]
        if not open_prs:
            return

        pr = random.choice(open_prs)
        old_reviewer = random.choice(pr["assigned_reviewers"])

        response = self.client.post(
            "/pullRequest/reassign",
            json={
                "pull_request_id": pr["pull_request_id"],
                "old_user_id": old_reviewer,
            },
        )
        if response.status_code == 200:
            data = response.json()
            if "pr" in data:
                pr["assigned_reviewers"] = data["pr"]["assigned_reviewers"]

    @task(1)
    def toggle_activity(self):
        if not self.users:
            return

        user = random.choice(self.users)
        user["is_active"] = not user["is_active"]

        self.client.post(
            "/users/setIsActive",
            json={"user_id": user["user_id"], "is_active": user["is_active"]},
        )

    @task(1)
    def get_stats(self):
        self.client.get(f"/stats/team/{self.team_name}")

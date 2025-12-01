import random
import uuid
from locust import HttpUser, task, between, events

class ClickFixUser(HttpUser):
    # Simulate a user waiting between 1 and 5 seconds between actions
    wait_time = between(1, 5)

    def on_start(self):
        """
        Generate a unique user ID for each simulated user session.
        This mimics a unique victim clicking a link in a phishing email.
        """
        self.user_id = str(uuid.uuid4())[:8]
        self.scenario = "teams_error" # Default scenario to test

    @task(3)
    def view_lure_page(self):
        """
        Simulate visiting the lure page.
        Weight: 3 (Most common action)
        """
        self.client.get(
            f"/s/{self.scenario}?uid={self.user_id}", 
            name="/s/[scenario]",
            verify=False # Ignore self-signed cert warnings
        )

    @task(1)
    def click_trap_button(self):
        """
        Simulate the user clicking the 'Fix' button.
        Weight: 1 (Not everyone clicks)
        """
        # First visit the page to ensure cookies/session if needed (stateless here, but good practice)
        # Then trigger the click tracking endpoint
        self.client.post(
            f"/track/click/{self.user_id}",
            name="/track/click/[uid]",
            verify=False
        )

    @task(1)
    def execute_payload(self):
        """
        Simulate the full compromise flow:
        1. Request payload (PowerShell script)
        2. Report execution (Beacon back)
        Weight: 1 (Worst case scenario)
        """
        # Step 1: Download Payload
        self.client.get(
            f"/api/v2/config/{self.user_id}",
            name="/api/v2/config/[uid]",
            verify=False
        )
        
        # Step 2: Verify Execution (Beacon)
        # Simulate hostname/username params
        self.client.get(
            f"/verify/{self.user_id}?h=WORKSTATION-01&u=jdoe",
            name="/verify/[uid]",
            verify=False
        )

# Hook to suppress SSL warnings in the console
@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--insecure", action="store_true", default=True, help="Disable SSL verification")

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
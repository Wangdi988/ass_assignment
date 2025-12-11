from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 3)

    fx_datetime = 0 
    code = 0
    data = [
    '2006-05-07 02:55:41.300',
    '2005-12-07 02:55:41.5890',
    '2018-05-16 12:00:54.300',
    '2028-10-08 15:54:32.534'
    ]

    curr_code = [
    'USd',
    'Aud',
    'SGD',
    'CAD'
    ]

    @task
    def post_data(self):
        headers = {
            "Content-Type": "application/json",
            # "X-Gravitee-Api-Key": "gh3ef04e-a0b8-46cb-8ab0-761c8556af7r"
        }

        # Get the current value and wrap around when reaching the end
        ts = self.data[self.fx_datetime]
        alpha_code =self.curr_code[self.code]
        payload = {
            "date_time": ts,
            "alpha_currency_code": alpha_code
        }
        
        self.client.post(
            "http://127.0.0.1:8000/api/fx/read",
            json=payload,
            headers=headers
        )

        # Move to the next index
        self.fx_datetime += 1
        self.code += 1
        if self.fx_datetime >= len(self.data):
            self.fx_datetime = 0 
            self.code = 0

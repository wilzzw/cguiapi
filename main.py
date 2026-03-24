import os
import requests
from getpass import getpass

API_BASE_URL = "https://charmm-gui.org/api"


class QuickBilayer:
    # TODO: Add error handling for failed login and job submission
    def __init__(self, token=None):
        self.token = token
        if self.token is None:
            response = login()
            self.token = response.json().get('token')
            # with open(token_file, 'r') as f:
            #     self.token = f.read().strip()

    # Submit a quick bilayer job with the given parameters; produces a jobid
    def submit(self, pdbreader_jobid, upper_lipids: dict, lower_lipids: dict, **run_params):
        self.pdbreader_jobid = pdbreader_jobid

        # Format the lipid composition into the proper string format for the CHARMM-GUI API
        run_params['upper'] = _format_lipid_composition(upper_lipids)
        run_params['lower'] = _format_lipid_composition(lower_lipids)

        response = quick_bilayer(self.pdbreader_jobid, self.token, **run_params)
        self.jobid = response.json().get('jobid')
        return response

    # Check the job status
    def job_status(self):
        response = job_status(self.jobid, self.token)
        return response
    
    # Download the resulting package when the job is complete
    def download(self, output_path: str, filename="charmm-gui.tgz"):
        filepath = os.path.expanduser(f"{output_path}/{filename}")
        response = job_download(self.jobid, self.token, filepath)
        return response
    
    # Download intermediate results (e.g., step5_assembly.pdb) 
    # This is possible while the job is still running
    # Might come in handy for specific purposes
    def download_intermediate(self, filepath: str, filename="step5_assembly.pdb"):
        response = requests.get(f"https://www.charmm-gui.org/uploaded_pdb/{self.jobid}/{filename}")
        filepath = os.path.expanduser(filepath)
        
        if os.path.exists(filepath):
            print(f"File {filepath} already exists. Please choose a different filename.")
            return
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return response


# Provide credentials for login
# Return the response from authenticated requests, which contains the token
def login():
    headers = {
        "Content-Type": "application/json"
    }

    email = input("Enter email: ")
    password = getpass("Enter password: ")

    login_data = {
        "email": email,
        "password": password
    }

    response = requests.post(f"{API_BASE_URL}/login", json=login_data, headers=headers)
    return response

def job_status(jobid, token):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{API_BASE_URL}/check_status?jobid={jobid}", headers=headers)
    return response

def job_download(jobid, token, filepath):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "jobid": jobid
    }

    response = requests.get(f"{API_BASE_URL}/download", params=params, headers=headers)

    filepath = os.path.expanduser(filepath)
    
    if os.path.exists(filepath):
        print(f"File {filepath} already exists. Please choose a different filename.")
        return
    with open(filepath, 'wb') as f:
        f.write(response.content)
    
    return response

def quick_bilayer(pdbreader_jobid, token, **run_params):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = run_params
    data['jobid'] = pdbreader_jobid
    data['clone_job'] = "1"
    # data = '&'.join([f"{k}={v}" for k,v in data.items()])
    response = requests.post(f"{API_BASE_URL}/quick_bilayer", headers=headers, data=data)

    return response

# Helper function to format lipid composition into the required string format for the API
def _format_lipid_composition(lipid_dict: dict):
    lipid_str = ':'.join(list(lipid_dict.keys()))
    count_str = ':'.join([str(count) for count in lipid_dict.values()])
    formatted_str = f"{lipid_str}={count_str}"
    return formatted_str

# if response.status_code == 200:
#     token = response.json().get("token")
#     print("Login successful!")
#     return token
# else:
#     print("Login failed. Please check your credentials.")
#     return None
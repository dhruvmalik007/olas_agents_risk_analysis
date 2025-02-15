from huggingface_hub import HfApi , ModelCard
from huggingface_hub.hf_api import RepoFile, RepoFolder 
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import os
from gradio_client import Client
from playwright.async_api import async_playwright
"""
This package helps the user to fetch the necessary data from HF hub in order to deploy reliable agents on openAEA / autonomy framework
some of the tasks that can be done using this package are:
- Generate the necessary hf model metadata to be added in the configuration file registered on IPFS.
- fork the given version of the model and defining your own custom version of model.
"""

load_dotenv()


@dataclass
class FileHash:
    fileName: str
    HashValue: str

@dataclass
class FileSecurityScanStatus:
    fileName: str
    scanStatus: Optional[bool]

@dataclass
class ModelDetails:
    current_hashes: List[FileHash] = field(default_factory=list)
    fileSecurityScanStatus: List[FileSecurityScanStatus] = field(default_factory=list)

@dataclass
class ModelOrg:
    model_org: str
    model: ModelDetails = field(default_factory=ModelDetails)
    latest_commit: str = ""
    model_card: Any


@dataclass 
class ModelBenchmark:
    benchmark_params: Dict[str, Any]

@dataclass
class HfMetadata:
    organizations: Dict[str, ModelOrg] = field(default_factory=dict)


class ModelMetadata:
    model_org: str
    model_repo: str
    hf_object: HfApi
    config_file: HfMetadata  ## developing the config file from the given model metadata that is to be stored on IPFS
    gradio_benchmark_comparator = Client("open-llm-leaderboard/comparator")
    params_hf_website = "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard"
    
    def __init__(self, model_org, model_repo):
        self.model_org = model_org
        self.model_repo = model_repo
        self.hf_object = HfApi(token=os.getenv("HF_TOKEN"))
        self.config_file = HfMetadata()
        self.config_file.organizations[model_org] = ModelOrg(model_org=model_org)

    def fetch_model_repo_details(self):
        """
        it fetches the model repo information :
        - current commit hash
        - list of hashes of config.json file along with each of the model tensorfiles 
        - fetch the security scan results (pickle scan/ clamAV and other details)
        - and then finally add them into the json yaml object format with the given model name as root key.
        """
        
        try:
            model_repo_details: List[RepoFile] = self.hf_object.list_repo_tree(repo_id=f"{self.model_org}/{self.model_repo}", expand=True)
            ## now iterate on every file from the list and fetch the parameters
            self.config_file.organizations[self.model_org].latest_commit = self.hf_object.list_repo_refs(repo_id=f"{self.model_org}/{self.model_repo}").branches[0].target_commit ## taking the latest commit hash of default branch
            for hfFile in model_repo_details:
                self.config_file.organizations[self.model_org].model.current_hashes.append(FileHash(fileName=hfFile.name, HashValue=hfFile.lastCommit.oid))
                ## now fetch the security scan status of each file which has the security scan (and is to type lfs)
                if hfFile.type == "lfs":
                    self.config_file.organizations[self.model_org].model.fileSecurityScanStatus.append(FileSecurityScanStatus(fileName=hfFile.name, scanStatus=self.hf_object.get_lfs_file_security_status(repo_id=f"{self.model_org}/{self.model_repo}", file_path=hfFile.path)))
                else:
                    continue
            ## printing the config file as the json 
            print(self.config_file.__dict__)
                
        except Exception as e:
            print(f"Error: {e}")
            return None

    def fetch_model_card(self):
        """
        fetch the model card details from the given model repo
        """
        self.config_file.organizations[self.model_org].model_card = ModelCard.load(f"{self.model_org}/{self.model_repo}")
        return self.config_file.organizations[self.model_org].model_card
    def generate_config_file(self):
        """
        generate the config file of the given model and generates as json file to download
        """
        with open(f"{self.model_org}_config.json", "w") as f:
            f.write(self.config_file.__dict__)
            f.close()
    
    async def fetch_model_benchmark_data(self, regex_search: str=None):
        """
        fetch the benchmark data of the given model 
        - NOTE: Although this could've been optionally taken from the model card (if available).
        - but for more robust evaluation of the models i did write the custom scraper that:
            - fetches the benchmark data from the given model repo
            - and then stores the benchmark data in the given format
        
        inputs:
            - regex_search: its the optional string that fetches the 
        
        """
        
        search_query = f"{self.model_org}/{self.model_repo}"
        if regex_search:
            search_query += f" {regex_search}"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(self.params_hf_website)
                # Click on the "only official Providers" checkbox
                await page.click('text="only official Providers"')

                # Enter the search query into the search bar
                await page.fill('input[aria-label="Search"]', search_query)

                # Wait for the table to load
                await page.wait_for_selector('table.MuiTable-root.css-1d53vco')

                # Extract the table data
                table_data = await page.evaluate('''() => {
                    const rows = document.querySelectorAll('table.MuiTable-root.css-1d53vco tbody tr');
                    return Array.from(rows).map(row => {
                        const cells = row.querySelectorAll('td');
                        return Array.from(cells).map(cell => cell.innerText);
                    });
                }''')

                await browser.close()
                return table_data
        
        except Exception as e:
            print(f"Error: {e}")
            return None
         
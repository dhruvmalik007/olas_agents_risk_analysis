import asyncio
from playwright.async_api import async_playwright
import streamlit as st
import pandas as pd
import plotly.express as px
from fuzzywuzzy import process
import json
import os

class RiskAnalysisFramework:
    def __init__(self):
        self.entries = []

    async def scrape_data(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto("https://registry.olas.network/ethereum/agents")

            progress_bar = st.progress(0)
            page_number = 1

            while True:
                st.info(f"Scraping page {page_number}...")
                await page.wait_for_selector('tbody.ant-table-tbody')
                rows = await page.query_selector_all('tbody.ant-table-tbody tr.ant-table-row')
                
                for row in rows:
                    cells = await row.query_selector_all('td')
                    if len(cells) == 5:
                        id_val = await cells[0].inner_text()
                        name_val = await cells[1].inner_text()

                        # Hover over the owner cell to get the tooltip
                        owner_cell = cells[2]
                        await owner_cell.hover()
                        await page.wait_for_timeout(1000)  # Wait for the tooltip to appear
                        owner_tooltip = await owner_cell.query_selector('.ant-tooltip-inner')
                        owner_val = await owner_tooltip.inner_text() if owner_tooltip else "N/A"

                        # Hover over the hash cell to get the tooltip
                        hash_cell = cells[3]
                        await hash_cell.hover()
                        await page.wait_for_timeout(1000)  # Wait for the tooltip to appear
                        hash_tooltip = await hash_cell.query_selector('.ant-tooltip-inner')
                        hash_val = await hash_tooltip.inner_text() if hash_tooltip else "N/A"

                        entry = {
                            'id': id_val,
                            'name': name_val,
                            'owner': owner_val,
                            'hash': hash_val,
                            'agent_url': f"https://registry.olas.network/ethereum/agents/{id_val}",
                            'owner_link': f"https://etherscan.io/address/{owner_val.strip()}",
                            'hash_link': f"https://gateway.autonolas.tech/ipfs/{hash_val.strip()}"
                        }
                        self.entries.append(entry)

                next_button = await page.query_selector('li.ant-pagination-next:not(.ant-pagination-disabled) button')
                if next_button:
                    await next_button.click()
                    await page.wait_for_load_state('networkidle')
                    page_number += 1
                    progress_bar.progress(page_number * 10)  # Update progress bar
                else:
                    break

            progress_bar.progress(100)  # Complete progress bar
            st.success("Scraping completed!")
            await browser.close()

            # Load existing data from JSON file
            json_file_path = '/workspaces/olas_agents_risk_analysis/example_scrape_info/agent_status.json'
            if os.path.exists(json_file_path) and os.path.getsize(json_file_path) > 0:
                with open(json_file_path, 'r') as file:
                    existing_data = json.load(file)
            else:
                existing_data = []

            # Update existing data with new entries
            existing_ids = {entry['id'] for entry in existing_data}
            new_entries = [entry for entry in self.entries if entry['id'] not in existing_ids]
            updated_data = existing_data + new_entries

            # Save updated data to JSON file
            with open(json_file_path, 'w') as file:
                json.dump(updated_data, file, indent=4)

    def load_data(self):
        json_file_path = '/workspaces/olas_agents_risk_analysis/example_scrape_info/agent_status.json'
        if os.path.exists(json_file_path) and os.path.getsize(json_file_path) > 0:
            with open(json_file_path, 'r') as file:
                self.entries = json.load(file)
        else:
            self.entries = []
            st.warning("agent_status.json not found or is empty. Please scrape the agents first.")

    def search_entries(self, query):
        st.info(f"Searching for agents matching: {query}")
        results = [entry for entry in self.entries if query.lower() in entry['name'].lower()]
        return results

    def render_results(self, results):
        if results:
            st.write("### Search Results")
            for result in results:
                st.write(f"🔍 **Name:** {result['name']}")
                st.write(f"👤 **Owner:** {result['owner']}")
                st.write(f"🔗 **Hash:** {result['hash']}")
                st.write(f"🔗 **Agent URL:** {result['agent_url']}")
                st.write(f"🔗 **Owner Link:** {result['owner_link']}")
                st.write(f"🔗 **Hash Link:** {result['hash_link']}")
                st.write("---")
            
            # Additional sections
            st.write("### Risk Analysis")

            # Define the data for the 5 sections
            data = {
                'Section': ['UX risk', 'Model risk', 'Agentic memory', 'Metadata analysis', 'Unchain-risk'],
                'Status': ['Critical', 'Medium', 'Perfect', 'Medium', 'Perfect'],
                'Details': [
                    'This section requires immediate attention.',
                    'This section needs to be monitored closely.',
                    'This section is in good condition.',
                    'This section needs to be monitored closely.',
                    'This section is in good condition.'
                ]
            }

            df = pd.DataFrame(data)

            # Create a pie chart using Plotly
            fig = px.pie(df, values='Status', names='Section', title='Section Status',
                         color='Status', color_discrete_map={'Critical':'red', 'Medium':'yellow', 'Perfect':'green'},
                         hover_data=['Details'])

            # Display the chart using Streamlit
            st.plotly_chart(fig)
        else:
            st.warning("No results found.")

# Example usage in app.py
# risk_framework = RiskAnalysisFramework()
# risk_framework.load_data()
# query = st.text_input("Search for an agent")
# if st.button("Search"):
#     results = risk_framework.search_entries(query)
#     risk_framework.render_results(results)
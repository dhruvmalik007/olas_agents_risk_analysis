import streamlit as st
from packages.autonomy_framework.risk_analysis_framework import RiskAnalysisFramework
import asyncio

# Initialize the RiskAnalysisFramework
risk_framework = RiskAnalysisFramework()

# Load the data from the JSON file
risk_framework.load_data()

# Sidebar with options
st.sidebar.title("Navigation")
dashboard = st.sidebar.radio("Go to", ("Components", "Registry", "Services", "Agents", "TODO: deploy your own secure agents"))


# Function to create a dashboard with a search bar and buttons
def create_dashboard(dashboard_name):
    st.title(f"Welcome to the AgentBeats {dashboard_name} dashboard")
    st.write("- Write the query that you want to address from the given component")
    st.write("- (optional): add the PDF or other URL from where you want to fetch the additional context")
    st.write("- Wait for the formatted result")
    search_query = st.text_input("Search")
    scrape_button = st.button("Scrape Agents")
    submit_button = st.button("Search")
    
    if scrape_button:
        st.write("Scraping agents...")
        asyncio.run(risk_framework.scrape_data())
        st.write("Scraping completed. Please refresh the page to see the updated data.")
    
    if submit_button:
        st.write(f"Submitting query: {search_query}")
        results = risk_framework.search_entries(search_query)
        risk_framework.render_results(results)

# Display the selected dashboard
if dashboard == "Components":
    create_dashboard("Components")
elif dashboard == "Registry":
    create_dashboard("Registry")
elif dashboard == "Services":
    create_dashboard("Services")
elif dashboard == "Agents":
    create_dashboard("Agents")
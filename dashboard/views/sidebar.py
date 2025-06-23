import streamlit as st

class Sidebar:
    
    PAGE_LIVE_GNSS = "Live GNSS"
    PAGE_GNSS_LOGS_ANALYSIS = "GNSS Logs Analysis"
    
    def __init__(self):
        self.title = "Options"
        self.sidebar_nav_widget = SidebarNavWidget()

    def render(self):
        st.sidebar.title(self.title)
        selected_page = self.sidebar_nav_widget.render()
        st.sidebar.divider()
        return selected_page
        
    
class SidebarNavWidget:
    def __init__(self):
        self.page_names = [
            Sidebar.PAGE_LIVE_GNSS,
            Sidebar.PAGE_GNSS_LOGS_ANALYSIS
        ]

    def render(self):
        selected_page = st.sidebar.radio("Go to", self.page_names)
        st.sidebar.divider()
        
        return selected_page
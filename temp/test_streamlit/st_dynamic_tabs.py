import streamlit as st

class Tab:
    def __init__(self, name, content=""):
        self.name = name
        self.content = content

    def display(self, container):
        """Display the tab's content in the given Streamlit container."""
        container.write(f"Content for {self.name}: {self.content}")

def main():
    # Initialize session state for tabs if not already present
    if 'tabs' not in st.session_state:
        st.session_state.tabs = []

    # Interface for adding a new tab in the main area
    new_tab_name = st.text_input("New tab name")
    new_tab_content = st.text_input("Tab content (optional)")
    if st.button("Add Tab") and new_tab_name:
        st.session_state.tabs.append(Tab(new_tab_name, new_tab_content))

    # Display and manage tabs
    if st.session_state.tabs:
        tab_names = [tab.name for tab in st.session_state.tabs]
        tab_objects = st.tabs(tab_names)
        for i, (tab, tab_instance) in enumerate(zip(tab_objects, st.session_state.tabs)):
            with tab:
                tab_instance.display(tab)
                if st.button(f"Delete {tab_instance.name}", key=f"delete_{i}"):
                    st.session_state.tabs.pop(i)
                    st.rerun()  # Force rerun to update UI
    else:
        st.write("No tabs yet. Add a tab above.")

if __name__ == "__main__":
    main()
